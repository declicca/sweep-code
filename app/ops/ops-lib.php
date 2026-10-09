<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }

/** settings: private config overrides the defaults */
function ops_cfg(): array
{
    $app = dirname(__DIR__);
    $home = dirname($app);
    $c = [];
    foreach ([getenv('SWEEP_BACKUP_CONFIG') ?: '', $home . '/sweep-private/backup-config.php'] as $p) {
        if ($p && is_readable($p)) { $x = require $p; if (is_array($x)) { $c = $x; break; } }
    }
    $appCfg = is_readable($app . '/config.php') ? (require $app . '/config.php') : [];
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

/** PUT one object to S3-compatible storage (AWS Signature V4). Returns true or an error string. */
function ops_s3_put(array $s3, string $key, string $body)
{
    $endpoint = rtrim((string) $s3['endpoint'], '/');           // e.g. https://s3.us-west-004.backblazeb2.com
    $host = (string) parse_url($endpoint, PHP_URL_HOST);
    $region = (string) ($s3['region'] ?: 'auto');
    $path = '/' . rawurlencode((string) $s3['bucket']) . '/' . implode('/', array_map('rawurlencode', explode('/', $key)));
    $now = gmdate('Ymd\THis\Z'); $date = substr($now, 0, 8);
    $hash = hash('sha256', $body);
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
    curl_setopt_array($ch, [CURLOPT_CUSTOMREQUEST => 'PUT', CURLOPT_POSTFIELDS => $body, CURLOPT_HTTPHEADER => $h, CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => 300]);
    $out = (string) curl_exec($ch); $code = (int) curl_getinfo($ch, CURLINFO_HTTP_CODE); $err = curl_error($ch); curl_close($ch);
    return ($code >= 200 && $code < 300) ? true : ('HTTP ' . $code . ' ' . ($err ?: substr(strip_tags($out), 0, 200)));
}
