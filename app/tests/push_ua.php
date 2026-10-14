<?php
declare(strict_types=1);
/**
 * Sweep — the phone's side of a web push, for the tests only (tests/push_test.php, tests/e2e_push.py):
 *   php tests/push_ua.php keys                          a browser's key pair: {"p256dh","auth","pem"}
 *   php tests/push_ua.php open <file> <pem> <auth> <ep>  the messages SWEEP_PUSH_MOCK wrote for that endpoint, decrypted (JSON lines);
 *                                                        <pem>: the key itself or a file holding it
 *   php tests/push_ua.php run <uid> <HH:MM>             the scheduled task's reminders for one trader (SWEEP_TEST_DB), on the
 *                                                        next market day at that New York time; the trader used Sweep the day before
 */
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
require_once dirname(__DIR__) . '/push/web-push.php';

/** a browser's key pair (P-256) and its auth secret */
function ua_keys(): array
{
    $k = openssl_pkey_new(['private_key_type' => OPENSSL_KEYTYPE_EC, 'curve_name' => 'prime256v1']);
    openssl_pkey_export($k, $pem);
    return ['p256dh' => wp_b64u(wp_pub_raw($k)), 'auth' => wp_b64u(random_bytes(16)), 'pem' => $pem];
}

/** RFC 8291 from the browser's side: the clear message, or null */
function ua_decrypt(string $body, string $pem, string $auth): ?string
{
    if (strlen($body) < 16 + 4 + 1 + 65 + 17) return null;
    $salt = substr($body, 0, 16); $idlen = ord($body[20]); $as = substr($body, 21, $idlen); $ct = substr($body, 21 + $idlen);
    $ua = openssl_pkey_get_private($pem); $uaPub = wp_pub_raw($ua);
    $secret = openssl_pkey_derive(openssl_pkey_get_public(wp_pub_pem($as)), $ua);
    $ikm = hash_hkdf('sha256', $secret, 32, "WebPush: info\0" . $uaPub . $as, $auth);
    $cek = hash_hkdf('sha256', $ikm, 16, "Content-Encoding: aes128gcm\0", $salt);
    $nonce = hash_hkdf('sha256', $ikm, 12, "Content-Encoding: nonce\0", $salt);
    $p = openssl_decrypt(substr($ct, 0, -16), 'aes-128-gcm', $cek, OPENSSL_RAW_DATA, $nonce, substr($ct, -16));
    if (!is_string($p)) return null;
    $p = rtrim($p, "\0");
    return substr($p, -1) === "\x02" ? substr($p, 0, -1) : null;   // the last record's delimiter
}

/** what the mock push service received for one endpoint: [{headers, msg (decoded JSON), raw}] */
function ua_open(string $file, string $pem, string $auth, string $endpoint): array
{
    $out = [];
    foreach (is_file($file) ? file($file, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES) : [] as $line) {
        $x = json_decode($line, true);
        if (($x['endpoint'] ?? '') !== $endpoint) continue;
        $clear = ua_decrypt((string) base64_decode((string) $x['body']), $pem, wp_b64u_d($auth));
        $out[] = ['headers' => $x['headers'], 'msg' => $clear !== null ? json_decode($clear, true) : null];
    }
    return $out;
}

if (realpath((string) ($_SERVER['SCRIPT_FILENAME'] ?? '')) !== realpath(__FILE__)) return;   // required by another test
$mode = $argv[1] ?? '';
if ($mode === 'keys') { echo json_encode(ua_keys()), "\n"; exit; }
if ($mode === 'open') { foreach (ua_open($argv[2], is_file($argv[3]) ? (string) file_get_contents($argv[3]) : $argv[3], $argv[4], $argv[5]) as $m) echo json_encode($m, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES), "\n"; exit; }
if ($mode === 'run') {
    $root = dirname(__DIR__);
    $cfg = [];
    $dbf = (string) getenv('SWEEP_TEST_DB');   // the dev server's database (tools/run.sh, tools/par.py)
    if ($dbf === '' || !is_file($dbf)) { fwrite(STDERR, "SWEEP_TEST_DB: the dev server's database\n"); exit(2); }
    $pdo = new PDO('sqlite:' . $dbf, null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC]);
    $pdo->exec('PRAGMA busy_timeout = 5000');
    function db(): PDO { global $pdo; return $pdo; }
    function billing_on(): bool { return false; }
    foreach (['/notify/notify.php', '/notify/listeners.php'] as $f) require_once $root . $f;
    require_once $root . '/game/game.php';
    GameEngine::setPdo($pdo); GameEngine::schema();
    $uid = $argv[2]; $hm = $argv[3] ?? '09:00';
    $d = (new DateTimeImmutable('tomorrow', new DateTimeZone('America/New_York')))->format('Y-m-d');
    while (!GameEngine::isMarketDay($d)) $d = GameEngine::addDays($d, 1);
    putenv("SWEEP_GAME_NOW=$d $hm");
    GameEngine::profile($uid);
    $pdo->prepare('INSERT OR REPLACE INTO game_days (user_id, trading_day, activity, updated_at) VALUES (?, ?, 1, ?)')->execute([$uid, GameEngine::addDays($d, -1), time()]);
    GameNotifyService::run($uid, true);
    echo json_encode(['day' => $d, 'at' => $hm, 'bell' => $pdo->query('SELECT type FROM notifications WHERE user_id = ' . $pdo->quote($uid) . ' ORDER BY id')->fetchAll(PDO::FETCH_COLUMN)]), "\n";
    exit;
}
fwrite(STDERR, "usage: php tests/push_ua.php keys | open <file> <pem> <auth> <endpoint> | run <uid> <HH:MM>\n");
exit(2);
