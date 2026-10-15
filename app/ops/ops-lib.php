<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }

/** settings: private config overrides the defaults */
function ops_cfg(): array
{
    $app = dirname(__DIR__);
    $home = dirname($app);
    $c = [];
    $load = static fn(string $f) => require $f;   // its own scope: a config file's variables never overwrite these ($c in the app's config did)
    foreach ([getenv('SWEEP_BACKUP_CONFIG') ?: '', $home . '/sweep-private/backup-config.php'] as $p) {
        if ($p && is_readable($p)) { $x = $load($p); if (is_array($x)) { $c = $x; break; } }
    }
    $appCfg = is_readable($app . '/config.php') ? $load($app . '/config.php') : [];
    $data = is_array($appCfg) && !empty($appCfg['data_dir']) ? rtrim((string) $appCfg['data_dir'], '/') : $app . '/data';
    return $c + [
        'db' => $data . '/journal.db',
        'uploads' => $data . '/uploads',
        'private' => $home . '/sweep-private',
        'dir' => $home . '/sweep-backups',
        'passphrase' => '',
        's3' => ['endpoint' => '', 'region' => 'auto', 'bucket' => '', 'key' => '', 'secret' => '', 'prefix' => 'sweep'],
    ];
}

/** AES-256-GCM; file = "SWB1" + salt(16) + iv(12) + tag(16) + ciphertext. Key = PBKDF2-SHA256(passphrase, salt, 200k). */
function ops_encrypt(string $plain, string $pass): string
{
    $salt = random_bytes(16); $iv = random_bytes(12); $tag = '';
    $key = hash_pbkdf2('sha256', $pass, $salt, 200000, 32, true);
    $ct = openssl_encrypt($plain, 'aes-256-gcm', $key, OPENSSL_RAW_DATA, $iv, $tag);
    if ($ct === false) throw new RuntimeException('encryption failed');
    return 'SWB1' . $salt . $iv . $tag . $ct;
}
function ops_decrypt(string $blob, string $pass): string
{
    if (substr($blob, 0, 4) !== 'SWB1') throw new RuntimeException('not a Sweep backup');
    $salt = substr($blob, 4, 16); $iv = substr($blob, 20, 12); $tag = substr($blob, 32, 16); $ct = substr($blob, 48);
    $key = hash_pbkdf2('sha256', $pass, $salt, 200000, 32, true);
    $pt = openssl_decrypt($ct, 'aes-256-gcm', $key, OPENSSL_RAW_DATA, $iv, $tag);
    if ($pt === false) throw new RuntimeException('wrong passphrase or damaged file');
    return $pt;
}

/**
 * The same, streamed (16 Oct., brief 00 phase 1.1): the backup never holds the database in memory (it held it three times:
 * read, gzip, encrypted). File = "SWB2" + salt(16), then chunks: length(4, big-endian) + last(1) + iv(12) + tag(16) +
 * ciphertext of up to 1 MB of gzip data. Each chunk's number and « last » flag are authenticated with it (AES-GCM AAD):
 * a chunk dropped, moved or a file cut short fails the decryption.
 */
const OPS_CHUNK = 1048576;
function ops_encrypt_file(string $src, string $dst, string $pass): void
{
    $in = fopen($src, 'rb'); $out = fopen($dst, 'wb'); if (!$in || !$out) throw new RuntimeException('cannot open ' . (!$in ? $src : $dst));
    $salt = random_bytes(16); $key = hash_pbkdf2('sha256', $pass, $salt, 200000, 32, true);
    fwrite($out, 'SWB2' . $salt);
    $z = deflate_init(ZLIB_ENCODING_GZIP, ['level' => 6]); $buf = ''; $n = 0;
    $emit = function (string $pt, bool $last) use ($out, $key, &$n) {
        $iv = random_bytes(12); $tag = '';
        $ct = openssl_encrypt($pt, 'aes-256-gcm', $key, OPENSSL_RAW_DATA, $iv, $tag, pack('N', $n) . ($last ? "\x01" : "\x00"));
        if ($ct === false) throw new RuntimeException('encryption failed');
        fwrite($out, pack('N', strlen($ct)) . ($last ? "\x01" : "\x00") . $iv . $tag . $ct); $n++;
    };
    while (!feof($in)) {
        $buf .= deflate_add($z, (string) fread($in, OPS_CHUNK), ZLIB_NO_FLUSH);
        while (strlen($buf) > OPS_CHUNK) { $emit(substr($buf, 0, OPS_CHUNK), false); $buf = substr($buf, OPS_CHUNK); }
    }
    $buf .= deflate_add($z, '', ZLIB_FINISH);
    while (strlen($buf) > OPS_CHUNK) { $emit(substr($buf, 0, OPS_CHUNK), false); $buf = substr($buf, OPS_CHUNK); }
    $emit($buf, true);
    fclose($in); if (!fclose($out)) throw new RuntimeException('cannot write ' . $dst);
}
/** Reads SWB2 (streamed) and SWB1 (older backups, one piece). $gunzip false keeps the gzip data (the files archive: .tar.gz). */
function ops_decrypt_file(string $src, string $dst, string $pass, bool $gunzip = true): void
{
    $in = fopen($src, 'rb'); if (!$in) throw new RuntimeException('cannot open ' . $src);
    $magic = (string) fread($in, 4);
    if ($magic === 'SWB1') { fclose($in); $pt = ops_decrypt((string) file_get_contents($src), $pass); if (file_put_contents($dst, $gunzip ? (string) gzdecode($pt) : $pt) === false) throw new RuntimeException('cannot write ' . $dst); return; }
    if ($magic !== 'SWB2') throw new RuntimeException('not a Sweep backup');
    $salt = (string) fread($in, 16); $key = hash_pbkdf2('sha256', $pass, $salt, 200000, 32, true);
    $out = fopen($dst, 'wb'); if (!$out) throw new RuntimeException('cannot write ' . $dst);
    $z = $gunzip ? inflate_init(ZLIB_ENCODING_GZIP) : null; $n = 0; $last = false;
    while (!$last) {
        $h = (string) fread($in, 33); if (strlen($h) < 33) throw new RuntimeException('damaged file (cut short)');
        $len = unpack('N', substr($h, 0, 4))[1]; $last = $h[4] === "\x01"; $iv = substr($h, 5, 12); $tag = substr($h, 17, 16);
        $ct = ''; while (strlen($ct) < $len && !feof($in)) $ct .= (string) fread($in, $len - strlen($ct));
        $pt = openssl_decrypt($ct, 'aes-256-gcm', $key, OPENSSL_RAW_DATA, $iv, $tag, pack('N', $n) . ($last ? "\x01" : "\x00"));
        if ($pt === false) throw new RuntimeException('wrong passphrase or damaged file');
        fwrite($out, $z ? (string) inflate_add($z, $pt, $last ? ZLIB_FINISH : ZLIB_SYNC_FLUSH) : $pt); $n++;
    }
    if (fread($in, 1) !== '') throw new RuntimeException('damaged file (data after the end)');
    fclose($in); fclose($out);
}
/** The same upload, read from the file (no copy of it in memory). */
function ops_s3_put_file(array $s3, string $key, string $file)
{
    return ops_s3_put($s3, $key, '', $file);
}

/** PUT one object to S3-compatible storage (AWS Signature V4). Returns true or an error string. */
function ops_s3_put(array $s3, string $key, string $body, ?string $file = null)
{
    $endpoint = rtrim((string) $s3['endpoint'], '/');           // e.g. https://s3.us-west-004.backblazeb2.com
    $host = (string) parse_url($endpoint, PHP_URL_HOST);
    $region = (string) ($s3['region'] ?: 'auto');
    $path = '/' . rawurlencode((string) $s3['bucket']) . '/' . implode('/', array_map('rawurlencode', explode('/', $key)));
    $now = gmdate('Ymd\THis\Z'); $date = substr($now, 0, 8);
    $hash = $file !== null ? (string) hash_file('sha256', $file) : hash('sha256', $body);
    $headers = ['content-type' => 'application/octet-stream', 'host' => $host, 'x-amz-content-sha256' => $hash, 'x-amz-date' => $now];
    ksort($headers);
    $canonHeaders = ''; foreach ($headers as $k => $v) $canonHeaders .= "$k:$v\n";
    $signed = implode(';', array_keys($headers));
    $canon = "PUT\n$path\n\n$canonHeaders\n$signed\n$hash";
    $scope = "$date/$region/s3/aws4_request";
    $sts = "AWS4-HMAC-SHA256\n$now\n$scope\n" . hash('sha256', $canon);
    $k = hash_hmac('sha256', $date, 'AWS4' . $s3['secret'], true);
    foreach ([$region, 's3', 'aws4_request'] as $part) $k = hash_hmac('sha256', $part, $k, true);
    $sig = hash_hmac('sha256', $sts, $k);
    $auth = "AWS4-HMAC-SHA256 Credential={$s3['key']}/$scope, SignedHeaders=$signed, Signature=$sig";
    $ch = curl_init($endpoint . $path);
    $h = []; foreach ($headers as $hk => $hv) if ($hk !== 'host') $h[] = "$hk: $hv";
    $h[] = 'Authorization: ' . $auth;
    if ($file !== null) { $fh = fopen($file, 'rb'); curl_setopt_array($ch, [CURLOPT_UPLOAD => true, CURLOPT_INFILE => $fh, CURLOPT_INFILESIZE => (int) filesize($file), CURLOPT_HTTPHEADER => $h, CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => 900]); }
    else curl_setopt_array($ch, [CURLOPT_CUSTOMREQUEST => 'PUT', CURLOPT_POSTFIELDS => $body, CURLOPT_HTTPHEADER => $h, CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => 300]);
    $out = (string) curl_exec($ch); $code = (int) curl_getinfo($ch, CURLINFO_HTTP_CODE); $err = curl_error($ch); curl_close($ch); if (isset($fh) && is_resource($fh)) fclose($fh);
    return ($code >= 200 && $code < 300) ? true : ('HTTP ' . $code . ' ' . ($err ?: substr(strip_tags($out), 0, 200)));
}
