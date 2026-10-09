<?php
/*
 * Sweep (app.makeitsweep.com) — PHP backend, multi-user.
 * Accounts with username + password, session cookies, per-trader data isolation,
 * invite-code registration and a small admin panel. No Node.js needed.
 */
declare(strict_types=1);
ini_set('display_errors', '0');

if (!is_file(__DIR__ . '/config.php')) {   // never a blank 500: say exactly what is missing
    http_response_code(503); header('Content-Type: text/html; charset=utf-8'); header('Retry-After: 120');
    echo '<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Sweep</title>'
       . '<body style="font:15px/1.5 system-ui,sans-serif;max-width:560px;margin:60px auto;padding:0 20px">'
       . '<h1 style="font-size:18px">Sweep is being updated</h1><p>Back in a minute.</p>'
       . '<!-- Administrator: config.php is missing from the app folder. Put it back (it is never part of an update zip). --></body>';
    error_log('Sweep: config.php is missing in ' . __DIR__);
    exit;
}
$cfg  = require __DIR__ . '/config.php';
$DATA = rtrim((string)($cfg['data_dir'] ?? (__DIR__ . '/data')), '/');
// Defaults from config.php; the admin can change them from the Traders page (stored in the database).
$CFG_INVITE = trim((string)($cfg['invite_code'] ?? ''));
$CFG_REGISTRATION = (string)($cfg['registration'] ?? 'open');   // Sweep is public: anyone can create an account
$APP_URL   = rtrim((string)($cfg['app_url'] ?? ''), '/') . '/';
$MAIL_FROM = trim((string)($cfg['mail_from'] ?? ''));
$SUPPORT   = trim((string)($cfg['support_email'] ?? '')) ?: 'hello@makeitsweep.com';
if ($MAIL_FROM === '') $MAIL_FROM = 'hello@makeitsweep.com';
$MAX_USERS   = (int)($cfg['max_users'] ?? 200);
$UPLOAD_QUOTA = (int)($cfg['upload_quota_mb'] ?? 500) * 1048576;
$MAX_DOCS    = (int)($cfg['max_records_per_user'] ?? 50000);
// Market context providers (see README). Economic calendar: manual | fmp | finnhub. Market data: none | databento.
$ECON_PROVIDER   = strtolower((string)($cfg['econ_provider'] ?? 'manual'));
$ECON_KEY        = trim((string)(getenv('ECONOMIC_DATA_API_KEY') ?: ($cfg['econ_api_key'] ?? $cfg['ECONOMIC_DATA_API_KEY'] ?? '')));
$MARKET_PROVIDER = strtolower((string)($cfg['market_provider'] ?? 'none'));
$MARKET_KEY      = trim((string)(getenv('MARKET_DATA_API_KEY') ?: ($cfg['market_api_key'] ?? $cfg['MARKET_DATA_API_KEY'] ?? '')));
$MARKET_SYMBOL   = trim((string)($cfg['market_symbol'] ?? 'NQ.v.0'));
require_once __DIR__ . '/econ.php';
const COOKIE = 'tj_session';
const SESSION_TTL = 30 * 86400;
const COLLECTIONS = ['firms', 'accounts', 'trades', 'journals', 'weekly', 'payouts', 'expenses', 'meta'];
const ID_RE = '/^[A-Za-z0-9_.:@+~-]{1,120}$/';
const USERNAME_RE = '/^[A-Za-z0-9_.-]{3,32}$/';
const INVITE_RE = '/^[A-Za-z0-9_-]{4,64}$/';
const CODE_ALPHABET = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
const IMAGE_TYPES = ['image/png', 'image/jpeg', 'image/gif', 'image/webp'];

$route  = trim((string)($_GET['r'] ?? 'app'), '/');
$method = $_SERVER['REQUEST_METHOD'] ?? 'GET';
if ($method === 'POST' && isset($_GET['_method'])) $method = strtoupper((string)$_GET['_method']);
$HTTPS = (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off') || (($_SERVER['HTTP_X_FORWARDED_PROTO'] ?? '') === 'https');

header('X-Content-Type-Options: nosniff');
header('Referrer-Policy: same-origin');
header('X-Frame-Options: DENY');

/* ================= helpers ================= */
function json_out(int $code, $data): void {
    http_response_code($code);
    header('Content-Type: application/json; charset=utf-8');
    header('Cache-Control: no-store');
    echo json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    exit;
}
function html_out(int $code, string $title, string $msg): void {
    http_response_code($code);
    header('Content-Type: text/html; charset=utf-8');
    header('Cache-Control: no-store');
    echo '<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>' . $title
       . '</title><body style="font:15px/1.5 system-ui,sans-serif;max-width:560px;margin:60px auto;padding:0 20px;color:#222">'
       . '<h1 style="font-size:18px">' . $title . '</h1><p>' . $msg . '</p></body>';
    exit;
}
function body_json(int $max = 1048576): array {
    $raw = file_get_contents('php://input');
    if ($raw === false || strlen($raw) > $max) json_out(413, ['error' => 'Request too large.']);
    $d = json_decode($raw === '' ? '{}' : $raw, true);
    if (!is_array($d) || ($d !== [] && array_keys($d) === range(0, count($d) - 1))) json_out(400, ['error' => 'Body must be a JSON object.']);
    return $d;
}
function now(): string { return gmdate('Y-m-d\TH:i:s\Z'); }
/**
 * One session-date rule (2026-10): a trade's « date » IS its trading session. Trades not yet marked session_date: true
 * are moved once (same rule as GameEngine::hasSessionDate: an older trade entered at 18:00 ET or later was dated by the
 * calendar → the next day; one already moved by the app keeps its date) and marked, so nothing is ever moved twice.
 */
/** money_type of an account (eval / funded = simulated, live / personal = real), deduced once; null = « to classify » */
function sweep_money_type_of(array $a): ?string
{
    if (in_array($a['money_type'] ?? '', ['eval', 'funded', 'live', 'personal'], true)) return $a['money_type'];
    $ph = (string) ($a['phase'] ?? '');
    if (in_array($ph, ['eval', 'funded', 'live', 'personal'], true)) return $ph;
    $r = (array) ($a['rules'] ?? []);
    if (!empty($r['target_c'])) return 'eval';
    foreach (['payout_win_days', 'payout_min_c', 'payout_max_c', 'payout_min_bal_c', 'payout_trade_days'] as $k) if (!empty($r[$k])) return 'funded';
    if (empty($a['firm_id']) && empty($a['preset'])) return 'personal';
    return null;
}
function sweep_money_types(string $uid): int
{
    $n = 0;
    foreach (q("SELECT id, data FROM documents WHERE user_id = ? AND collection = 'accounts' AND data NOT LIKE '%\"money_type\":%'", [$uid])->fetchAll() as $r) {
        $a = json_decode((string) $r['data'], true); if (!is_array($a)) continue;
        $t = sweep_money_type_of($a); if (!$t) continue;   // left for the « Classify your accounts » window
        $a['money_type'] = $t;
        q('UPDATE documents SET data = ?, updated_at = ? WHERE user_id = ? AND collection = ? AND id = ?', [json_encode($a, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES), now(), $uid, 'accounts', $r['id']]);
        $n++;
    }
    return $n;
}
/** monthly subscriptions (expenses with recurring = monthly): one expense per month on the anniversary day, until the
 *  linked account is passed, failed, closed or archived (then recurring_end is set and nothing more is created) */
function sweep_recurring_expenses(string $uid): int
{
    $rows = q("SELECT id, data FROM documents WHERE user_id = ? AND collection = 'expenses' AND data LIKE '%\"recurring\":\"monthly\"%'", [$uid])->fetchAll();
    if (!$rows) return 0;
    $today = (new DateTimeImmutable('now', new DateTimeZone('America/New_York')))->modify('+6 hours')->format('Y-m-d');
    $have = [];
    foreach (q("SELECT id FROM documents WHERE user_id = ? AND collection = 'expenses'", [$uid])->fetchAll() as $x) $have[$x['id']] = true;
    $n = 0;
    foreach ($rows as $r) {
        $e = json_decode((string) $r['data'], true); if (!is_array($e) || !empty($e['recurring_of']) || empty($e['date'])) continue;
        $end = (string) ($e['recurring_end'] ?? '');
        if ($end === '' && !empty($e['account_id'])) {
            $ad = q("SELECT data FROM documents WHERE user_id = ? AND collection = 'accounts' AND id = ?", [$uid, $e['account_id']])->fetchColumn();
            $a = $ad ? json_decode((string) $ad, true) : null;
            $passed = (bool) q("SELECT 1 FROM documents WHERE user_id = ? AND collection = 'accounts' AND data LIKE ?", [$uid, '%"from_eval":"' . $e['account_id'] . '"%'])->fetchColumn();
            if (!$a || $passed || in_array($a['status'] ?? '', ['archived', 'closed'], true) || in_array($a['result'] ?? '', ['passed', 'failed'], true) || in_array($a['outcome'] ?? '', ['passed', 'failed'], true)) {
                $end = (string) ($a['failed_on'] ?? '') ?: $today;
                $e['recurring_end'] = $end;
                q('UPDATE documents SET data = ?, updated_at = ? WHERE user_id = ? AND collection = ? AND id = ?', [json_encode($e, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES), now(), $uid, 'expenses', $r['id']]);
            }
        }
        $limit = $end !== '' && $end < $today ? $end : $today;
        $d0 = new DateTimeImmutable($e['date'] . ' 12:00:00'); $day = (int) $d0->format('j');
        for ($k = 1; $k < 120; $k++) {
            $m = $d0->modify('first day of +' . $k . ' month'); $dd = min($day, (int) $m->format('t'));
            $date = $m->format('Y-m-') . str_pad((string) $dd, 2, '0', STR_PAD_LEFT);
            if ($date > $limit) break;
            $id = $r['id'] . '-m' . $k; if (isset($have[$id])) continue;
            $doc = ['id' => $id, 'date' => $date, 'category' => $e['category'] ?? 'subscription', 'amount_c' => (int) ($e['amount_c'] ?? 0), 'firm_id' => $e['firm_id'] ?? '', 'account_id' => $e['account_id'] ?? '', 'recurring_of' => $r['id']];
            if (!empty($e['demo'])) $doc['demo'] = true;
            q('INSERT INTO documents (user_id, collection, id, data, updated_at, created_at) VALUES (?, ?, ?, ?, ?, ?)', [$uid, 'expenses', $id, json_encode($doc, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES), now(), now()]);
            $have[$id] = true; $n++;
        }
    }
    return $n;
}
function sweep_session_dates(string $uid): int
{
    $rows = q("SELECT id, data FROM documents WHERE user_id = ? AND collection = 'trades' AND data NOT LIKE '%\"session_date\":true%'", [$uid])->fetchAll();
    if (!$rows) return 0;
    $n = 0; $pdo = db(); $pdo->beginTransaction();
    try {
        foreach ($rows as $r) {
            $t = json_decode((string) $r['data'], true); if (!is_array($t) || !empty($t['session_date'])) continue;
            $d = (string) ($t['date'] ?? ''); $tm = substr((string) ($t['entry_time'] ?? ''), 0, 5);
            if (preg_match('/^\d{4}-\d{2}-\d{2}$/', $d) && $tm !== '' && $tm >= '18:00') {
                $x = $t['executions'][0]['t'] ?? null;
                $already = is_string($x) && substr($x, 0, 10) !== '' && substr($x, 0, 10) < $d;
                if (!$already) $t['date'] = (new DateTimeImmutable($d . ' 12:00:00'))->modify('+1 day')->format('Y-m-d');
            }
            $t['session_date'] = true;
            q('UPDATE documents SET data = ?, updated_at = ? WHERE user_id = ? AND collection = ? AND id = ?', [json_encode($t, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES), now(), $uid, 'trades', $r['id']]);
            $n++;
        }
        $pdo->commit();
    } catch (Throwable $e) { $pdo->rollBack(); error_log('Sweep session dates: ' . $e->getMessage()); return 0; }
    // the game is unchanged: it already put those older evening trades on the next day (GameEngine::tradeDay)
    return $n;
}
function uuid(): string { $b = bin2hex(random_bytes(16)); return substr($b,0,8).'-'.substr($b,8,4).'-'.substr($b,12,4).'-'.substr($b,16,4).'-'.substr($b,20); }
function client_ip(): string { return (string)($_SERVER['REMOTE_ADDR'] ?? '0.0.0.0'); }
function cookie_path(): string {
    $sn = str_replace('\\', '/', (string)($_SERVER['SCRIPT_NAME'] ?? ''));
    return substr($sn, -8) === '/api.php' ? substr($sn, 0, -7) : '/';   // folder that contains api.php
}
function temp_password(): string {
    $a = 'abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789'; $s = '';
    for ($i = 0; $i < 14; $i++) $s .= $a[random_int(0, strlen($a) - 1)];
    return $s;
}

function new_recovery_code(): string {
    $c = '';
    for ($i = 0; $i < 16; $i++) { if ($i && $i % 4 === 0) $c .= '-'; $c .= CODE_ALPHABET[random_int(0, 31)]; }
    return $c;   // 80 bits, e.g. K7QM-2XWP-9RTD-H4NC
}
function norm_code($v): string { return strtoupper(preg_replace('/[^A-Za-z0-9]/', '', (string)$v)); }
function set_recovery_code(string $uid): string {
    $code = new_recovery_code();
    q('UPDATE users SET recovery_hash = ?, recovery_created = ? WHERE id = ?', [password_hash(norm_code($code), PASSWORD_DEFAULT), now(), $uid]);
    return $code;
}

/* ================= database ================= */
function ensure_data_dir(string $dir): void {
    if (!is_dir($dir) && !@mkdir($dir, 0750, true)) json_out(500, ['error' => 'Cannot create the data folder. Check data_dir in config.php.']);
    if (!is_dir($dir . '/uploads')) @mkdir($dir . '/uploads', 0750, true);
    if (!is_file($dir . '/.htaccess')) @file_put_contents($dir . '/.htaccess', "<IfModule mod_authz_core.c>\n  Require all denied\n</IfModule>\n<IfModule !mod_authz_core.c>\n  Deny from all\n</IfModule>\n");
    if (!is_file($dir . '/index.html')) @file_put_contents($dir . '/index.html', '');
    if (!is_writable($dir)) json_out(500, ['error' => 'The data folder is not writable.']);
}
function db(): PDO {
    static $pdo = null;
    global $cfg, $DATA;
    if ($pdo) return $pdo;
    $c = $cfg['db'] ?? [];
    $opts = [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC];
    ensure_data_dir($DATA);
    if (($c['driver'] ?? 'sqlite') === 'mysql') {
        if (defined('PDO::MYSQL_ATTR_FOUND_ROWS')) $opts[PDO::MYSQL_ATTR_FOUND_ROWS] = true;
        $pdo = new PDO('mysql:host=' . $c['host'] . ';dbname=' . $c['name'] . ';charset=utf8mb4', (string)$c['user'], (string)$c['password'], $opts);
        foreach ([
            'CREATE TABLE IF NOT EXISTS documents (user_id VARCHAR(120) NOT NULL, collection VARCHAR(32) NOT NULL, id VARCHAR(120) NOT NULL,
               data LONGTEXT NOT NULL, created_at VARCHAR(32) NOT NULL, updated_at VARCHAR(32) NOT NULL, PRIMARY KEY (user_id, collection, id)) DEFAULT CHARSET=utf8mb4',
            'CREATE TABLE IF NOT EXISTS uploads (id VARCHAR(64) NOT NULL PRIMARY KEY, user_id VARCHAR(120) NOT NULL, content_type VARCHAR(40) NOT NULL,
               size INT NOT NULL, created_at VARCHAR(32) NOT NULL, INDEX (user_id)) DEFAULT CHARSET=utf8mb4',
            'CREATE TABLE IF NOT EXISTS users (id VARCHAR(120) NOT NULL PRIMARY KEY, username VARCHAR(32) NOT NULL, username_lc VARCHAR(32) NOT NULL UNIQUE,
               password_hash VARCHAR(255) NOT NULL, is_admin TINYINT NOT NULL DEFAULT 0, disabled TINYINT NOT NULL DEFAULT 0,
               created_at VARCHAR(32) NOT NULL, last_login VARCHAR(32) NULL) DEFAULT CHARSET=utf8mb4',
            'CREATE TABLE IF NOT EXISTS sessions (token_hash CHAR(64) NOT NULL PRIMARY KEY, user_id VARCHAR(120) NOT NULL,
               created_at INT NOT NULL, expires_at INT NOT NULL, INDEX (user_id)) DEFAULT CHARSET=utf8mb4',
            'CREATE TABLE IF NOT EXISTS attempts (k VARCHAR(190) NOT NULL, at INT NOT NULL, INDEX (k, at)) DEFAULT CHARSET=utf8mb4',
            'CREATE TABLE IF NOT EXISTS app_settings (k VARCHAR(64) NOT NULL PRIMARY KEY, v TEXT NOT NULL) DEFAULT CHARSET=utf8mb4',
            'CREATE TABLE IF NOT EXISTS econ_events (id CHAR(40) NOT NULL PRIMARY KEY, ts INT NOT NULL, country VARCHAR(8) NOT NULL, event VARCHAR(255) NOT NULL,
               impact VARCHAR(10) NOT NULL, actual VARCHAR(40) NULL, forecast VARCHAR(40) NULL, previous VARCHAR(40) NULL, source VARCHAR(20) NOT NULL, updated_at INT NOT NULL, INDEX (ts)) DEFAULT CHARSET=utf8mb4',
            'CREATE TABLE IF NOT EXISTS econ_sync (day CHAR(10) NOT NULL PRIMARY KEY, fetched_at INT NOT NULL) DEFAULT CHARSET=utf8mb4',
            'CREATE TABLE IF NOT EXISTS candles (symbol VARCHAR(20) NOT NULL, t INT NOT NULL, o DOUBLE NOT NULL, h DOUBLE NOT NULL, l DOUBLE NOT NULL, c DOUBLE NOT NULL, v INT NOT NULL, PRIMARY KEY (symbol, t)) DEFAULT CHARSET=utf8mb4',
            'CREATE TABLE IF NOT EXISTS candle_sync (symbol VARCHAR(20) NOT NULL, day CHAR(10) NOT NULL, fetched_at INT NOT NULL, PRIMARY KEY (symbol, day)) DEFAULT CHARSET=utf8mb4',
        ] as $sql) $pdo->exec($sql);
        $pdo->exec('CREATE TABLE IF NOT EXISTS reset_tokens (token_hash CHAR(64) NOT NULL PRIMARY KEY, user_id VARCHAR(40) NOT NULL, expires_at INT NOT NULL, used INT NOT NULL DEFAULT 0) DEFAULT CHARSET=utf8mb4');
        foreach (['full_name' => 'VARCHAR(80) NULL', 'first_name' => 'VARCHAR(40) NULL', 'last_name' => 'VARCHAR(40) NULL', 'recovery_hash' => 'VARCHAR(255) NULL', 'recovery_created' => 'VARCHAR(32) NULL', 'email' => 'VARCHAR(190) NULL', 'email_lc' => 'VARCHAR(190) NULL', 'terms_accepted_at' => 'VARCHAR(32) NULL', 'utm_source' => 'VARCHAR(30) NULL', 'utm_medium' => 'VARCHAR(30) NULL', 'utm_campaign' => 'VARCHAR(50) NULL', 'utm_content' => 'VARCHAR(50) NULL', 'found_via' => 'VARCHAR(20) NULL', 'found_video' => 'VARCHAR(120) NULL', 'accounts_info' => 'VARCHAR(160) NULL', 'experience' => 'VARCHAR(10) NULL', 'is_internal' => 'TINYINT NOT NULL DEFAULT 0', 'lang' => 'VARCHAR(5) NULL'] as $col => $type) {
            if (!$pdo->query("SHOW COLUMNS FROM users LIKE '$col'")->fetch()) $pdo->exec("ALTER TABLE users ADD COLUMN $col $type");
        }
        if (!$pdo->query("SHOW COLUMNS FROM econ_events LIKE 'status'")->fetch()) $pdo->exec("ALTER TABLE econ_events ADD COLUMN status VARCHAR(20) NULL");
    } else {
        if (!in_array('sqlite', PDO::getAvailableDrivers(), true)) {
            json_out(500, ['error' => 'PDO SQLite is not enabled on this PHP version. Enable pdo_sqlite in cPanel or switch config.php to MySQL.']);
        }
        $pdo = new PDO('sqlite:' . $DATA . '/journal.db', null, null, $opts);
        $pdo->exec('PRAGMA busy_timeout = 5000');
        $pdo->exec('PRAGMA journal_mode = WAL');
        foreach ([
            'CREATE TABLE IF NOT EXISTS documents (user_id TEXT NOT NULL, collection TEXT NOT NULL, id TEXT NOT NULL, data TEXT NOT NULL,
               created_at TEXT NOT NULL, updated_at TEXT NOT NULL, PRIMARY KEY (user_id, collection, id))',
            'CREATE TABLE IF NOT EXISTS uploads (id TEXT PRIMARY KEY, user_id TEXT NOT NULL, content_type TEXT NOT NULL, size INTEGER NOT NULL, created_at TEXT NOT NULL)',
            'CREATE INDEX IF NOT EXISTS uploads_user ON uploads(user_id)',
            'CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, username TEXT NOT NULL, username_lc TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL,
               is_admin INTEGER NOT NULL DEFAULT 0, disabled INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL, last_login TEXT)',
            'CREATE TABLE IF NOT EXISTS sessions (token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL, created_at INTEGER NOT NULL, expires_at INTEGER NOT NULL)',
            'CREATE INDEX IF NOT EXISTS sessions_user ON sessions(user_id)',
            'CREATE TABLE IF NOT EXISTS attempts (k TEXT NOT NULL, at INTEGER NOT NULL)',
            'CREATE INDEX IF NOT EXISTS attempts_k ON attempts(k, at)',
            'CREATE TABLE IF NOT EXISTS app_settings (k TEXT PRIMARY KEY, v TEXT NOT NULL)',
            'CREATE TABLE IF NOT EXISTS econ_events (id TEXT PRIMARY KEY, ts INTEGER NOT NULL, country TEXT NOT NULL, event TEXT NOT NULL, impact TEXT NOT NULL,
               actual TEXT, forecast TEXT, previous TEXT, source TEXT NOT NULL, updated_at INTEGER NOT NULL)',
            'CREATE INDEX IF NOT EXISTS econ_ts ON econ_events(ts)',
            'CREATE TABLE IF NOT EXISTS econ_sync (day TEXT PRIMARY KEY, fetched_at INTEGER NOT NULL)',
            'CREATE TABLE IF NOT EXISTS candles (symbol TEXT NOT NULL, t INTEGER NOT NULL, o REAL NOT NULL, h REAL NOT NULL, l REAL NOT NULL, c REAL NOT NULL, v INTEGER NOT NULL, PRIMARY KEY (symbol, t))',
            'CREATE TABLE IF NOT EXISTS candle_sync (symbol TEXT NOT NULL, day TEXT NOT NULL, fetched_at INTEGER NOT NULL, PRIMARY KEY (symbol, day))',
        ] as $sql) $pdo->exec($sql);
        $cols = [];
        foreach ($pdo->query('PRAGMA table_info(users)') as $col) $cols[] = $col['name'];
        foreach (['full_name', 'first_name', 'last_name', 'recovery_hash', 'recovery_created', 'email', 'email_lc', 'terms_accepted_at', 'lang', 'utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'found_via', 'found_video', 'accounts_info', 'experience'] as $col) if (!in_array($col, $cols, true)) { try { $pdo->exec("ALTER TABLE users ADD COLUMN $col TEXT"); } catch (Throwable $e) { /* added by a request running at the same time */ } }
        if (!in_array('is_internal', $cols, true)) $pdo->exec('ALTER TABLE users ADD COLUMN is_internal INTEGER NOT NULL DEFAULT 0');
        $pdo->exec('CREATE TABLE IF NOT EXISTS reset_tokens (token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL, expires_at INTEGER NOT NULL, used INTEGER NOT NULL DEFAULT 0)');
        // an older reset_tokens table (created before « used » existed) is brought up to date; reset links are short-lived, so an unusable old table is simply rebuilt
        $rcols = [];
        foreach ($pdo->query('PRAGMA table_info(reset_tokens)') as $col) $rcols[] = $col['name'];
        if (array_diff(['token_hash', 'user_id', 'expires_at'], $rcols)) {
            $pdo->exec('DROP TABLE IF EXISTS reset_tokens');
            $pdo->exec('CREATE TABLE reset_tokens (token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL, expires_at INTEGER NOT NULL, used INTEGER NOT NULL DEFAULT 0)');
        } elseif (!in_array('used', $rcols, true)) {
            try { $pdo->exec('ALTER TABLE reset_tokens ADD COLUMN used INTEGER NOT NULL DEFAULT 0'); } catch (Throwable $e) { /* added by a request running at the same time */ }
        }
        $pdo->exec('CREATE UNIQUE INDEX IF NOT EXISTS users_email ON users(email_lc)');
        $ecols = [];
        foreach ($pdo->query('PRAGMA table_info(econ_events)') as $col) $ecols[] = $col['name'];
        if (!in_array('status', $ecols, true)) $pdo->exec('ALTER TABLE econ_events ADD COLUMN status TEXT');
    }
    return $pdo;
}
function q(string $sql, array $args = []): PDOStatement { $st = db()->prepare($sql); $st->execute($args); return $st; }
function setting(string $k, string $default): string {
    $v = q('SELECT v FROM app_settings WHERE k = ?', [$k])->fetchColumn();
    return $v === false ? $default : (string)$v;
}
function save_setting(string $k, string $v): void {
    if (q('UPDATE app_settings SET v = ? WHERE k = ?', [$v, $k])->rowCount() === 0 && setting($k, "\0") === "\0") q('INSERT INTO app_settings (k, v) VALUES (?, ?)', [$k, $v]);
}
/** Effective access settings: database first, then config.php defaults. */
function access(): array {
    global $CFG_INVITE, $CFG_REGISTRATION;
    $invite = setting('invite_code', $CFG_INVITE);
    $reg = setting('registration', $CFG_REGISTRATION);
    if (!in_array($reg, ['open', 'invite', 'closed'], true)) $reg = 'closed';
    if ($reg === 'invite' && $invite === '') $reg = 'closed';
    $reset = setting('reset_method', 'recovery');
    if (!in_array($reset, ['recovery', 'invite', 'off'], true)) $reset = 'recovery';
    if ($reset === 'invite' && $invite === '') $reset = 'recovery';
    return ['registration' => $reg, 'invite' => $invite, 'reset' => $reset];
}

/* ================= market context: HTTP, economic calendar, candles ================= */
function http_get(string $url, array $headers = [], ?string $basicUser = null): array {
    if (function_exists('curl_init')) {
        $ch = curl_init($url);
        curl_setopt_array($ch, [CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => 25, CURLOPT_CONNECTTIMEOUT => 8, CURLOPT_HTTPHEADER => $headers, CURLOPT_FOLLOWLOCATION => true]);
        if ($basicUser !== null) curl_setopt($ch, CURLOPT_USERPWD, $basicUser . ':');
        $body = curl_exec($ch); $code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE); curl_close($ch);
        return [$code, $body === false ? '' : (string)$body];
    }
    if ($basicUser !== null) $headers[] = 'Authorization: Basic ' . base64_encode($basicUser . ':');
    $ctx = stream_context_create(['http' => ['timeout' => 25, 'header' => implode("\r\n", $headers), 'ignore_errors' => true]]);
    $body = @file_get_contents($url, false, $ctx); $code = 0;
    foreach ($http_response_header ?? [] as $h) if (preg_match('#^HTTP/\S+ (\d{3})#', $h, $m)) $code = (int)$m[1];
    return [$code, $body === false ? '' : (string)$body];
}
function fmt_val($v, $unit = ''): ?string {
    if ($v === null || $v === '') return null;
    if (is_numeric($v)) { $v = rtrim(rtrim(number_format((float)$v, 3, '.', ''), '0'), '.'); }
    return (string)$v . ($unit && !preg_match('/[a-z%]$/i', (string)$v) ? $unit : '');
}
/** Economic calendar provider abstraction: returns normalized US high/medium events. */
function econ_fetch(string $from, string $to): array {
    global $ECON_PROVIDER, $ECON_KEY;
    if ($ECON_KEY === '' || !in_array($ECON_PROVIDER, ['tradingeconomics', 'fmp', 'finnhub'], true)) return [];
    $out = [];
    if ($ECON_PROVIDER === 'tradingeconomics') {
        [$code, $body] = http_get('https://api.tradingeconomics.com/calendar/country/united%20states/' . $from . '/' . $to . '?c=' . urlencode($ECON_KEY) . '&f=json');
        $rows = $code === 200 ? json_decode($body, true) : null;
        if (!is_array($rows)) { error_log('Trading Journal: economic calendar (Trading Economics) HTTP ' . $code); throw new RuntimeException('econ provider unavailable'); }
        return array_values(array_filter(array_map('te_row', $rows)));
    }
    if ($ECON_PROVIDER === 'fmp') {
        [$code, $body] = http_get('https://financialmodelingprep.com/stable/economic-calendar?from=' . $from . '&to=' . $to . '&apikey=' . urlencode($ECON_KEY));
        if ($code !== 200) [$code, $body] = http_get('https://financialmodelingprep.com/api/v3/economic_calendar?from=' . $from . '&to=' . $to . '&apikey=' . urlencode($ECON_KEY));
        $rows = $code === 200 ? json_decode($body, true) : null;
        if (!is_array($rows)) { error_log('Trading Journal: economic calendar (FMP) HTTP ' . $code); return []; }
        foreach ($rows as $r) {
            $out[] = ['country' => strtoupper((string)($r['country'] ?? '')), 'time' => (string)($r['date'] ?? ''), 'event' => (string)($r['event'] ?? ''),
                      'impact' => strtolower((string)($r['impact'] ?? '')), 'unit' => (string)($r['unit'] ?? ''),
                      'actual' => $r['actual'] ?? null, 'forecast' => $r['estimate'] ?? null, 'previous' => $r['previous'] ?? null];
        }
    } else {
        [$code, $body] = http_get('https://finnhub.io/api/v1/calendar/economic?from=' . $from . '&to=' . $to . '&token=' . urlencode($ECON_KEY));
        $d = $code === 200 ? json_decode($body, true) : null;
        if (!is_array($d)) { error_log('Trading Journal: economic calendar (Finnhub) HTTP ' . $code); return []; }
        foreach (($d['economicCalendar'] ?? []) as $r) {
            $out[] = ['country' => strtoupper((string)($r['country'] ?? '')), 'time' => (string)($r['time'] ?? ''), 'event' => (string)($r['event'] ?? ''),
                      'impact' => strtolower((string)($r['impact'] ?? '')), 'unit' => (string)($r['unit'] ?? ''),
                      'actual' => $r['actual'] ?? null, 'forecast' => $r['estimate'] ?? null, 'previous' => $r['prev'] ?? null];
        }
    }
    return array_values(array_filter($out, fn($e) => $e['country'] === 'US' && in_array($e['impact'], ['high', 'medium'], true) && $e['event'] !== '' && $e['time'] !== ''));
}
function econ_store(array $events, string $source): void {
    econ_schema();
    foreach ($events as $e) {
        $ts = strtotime($e['time'] . ' UTC'); if (!$ts) continue;   // providers report UTC
        // provider events keep one id even if the provider reschedules them
        $id = !empty($e['provider_event_id']) ? sha1($source . '|' . $e['provider_event_id']) : sha1('US|' . $ts . '|' . strtolower(trim($e['event'])));
        $raw = !empty($e['raw']);   // values already formatted by the provider (e.g. "0.3%", "220K")
        $fv = fn($k) => $raw ? (($e[$k] ?? null) !== null ? (string)$e[$k] : null) : fmt_val($e[$k] ?? null, $e['unit'] ?? '');
        $a = $fv('actual'); $f = $fv('forecast'); $p = $fv('previous'); $rv = $fv('revised');
        $row = q('SELECT actual FROM econ_events WHERE id = ?', [$id])->fetch();
        if (!$row) {
            q('INSERT INTO econ_events (id, ts, country, event, impact, actual, forecast, previous, source, updated_at, status, revised, unit, ticker, provider_event_id, provider_updated, reference) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
              [$id, $ts, 'US', $e['event'], $e['impact'], $a, $f, $p, $source, time(), 'official', $rv, $e['unit'] ?? null, $e['ticker'] ?? null, $e['provider_event_id'] ?? null, $e['provider_updated'] ?? null, $e['reference'] ?? null]);
        } else {
            // the first published actual is kept: later revisions never overwrite history
            q('UPDATE econ_events SET ts = ?, event = ? WHERE id = ?', [$ts, $e['event'], $id]);
            q('UPDATE econ_events SET impact = ?, forecast = COALESCE(?, forecast), previous = COALESCE(?, previous), actual = COALESCE(actual, ?), revised = COALESCE(?, revised),
               ticker = COALESCE(?, ticker), provider_event_id = COALESCE(?, provider_event_id), provider_updated = COALESCE(?, provider_updated), reference = COALESCE(?, reference), updated_at = ? WHERE id = ?',
              [$e['impact'], $f, $p, $a, $rv, $e['ticker'] ?? null, $e['provider_event_id'] ?? null, $e['provider_updated'] ?? null, $e['reference'] ?? null, time(), $id]);
        }
    }
}
/** Import a schedule file: {events:[{date, time (ET), event, impact, status, actual?, forecast?, previous?}]}. Existing events keep their values. */
function econ_import(array $data): int {
    $tz = new DateTimeZone('America/New_York'); $n = 0;
    foreach (($data['events'] ?? []) as $e) {
        $date = (string)($e['date'] ?? ''); $time = (string)($e['time'] ?? ''); $name = trim((string)($e['event'] ?? '')); $impact = strtolower((string)($e['impact'] ?? ''));
        if (!preg_match('/^\d{4}-\d{2}-\d{2}$/', $date) || !preg_match('/^\d{1,2}:\d{2}$/', $time) || $name === '' || !in_array($impact, ['high', 'medium'], true)) continue;
        $ts = (new DateTime($date . ' ' . $time . ':00', $tz))->getTimestamp();
        $id = sha1('US|' . $ts . '|' . strtolower($name));
        if (q('SELECT 1 FROM econ_events WHERE id = ?', [$id])->fetch()) continue;
        q('INSERT INTO econ_events (id, ts, country, event, impact, actual, forecast, previous, source, updated_at, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
          [$id, $ts, 'US', substr($name, 0, 200), $impact, ($e['actual'] ?? null) ?: null, ($e['forecast'] ?? null) ?: null, ($e['previous'] ?? null) ?: null, 'schedule', time(), substr((string)($e['status'] ?? 'estimated'), 0, 20)]);
        $n++;
    }
    return $n;
}
/** Bundled schedule file(s) are imported once, when the calendar runs in manual mode. */
function econ_seed(): void {
    global $ECON_PROVIDER, $ECON_KEY;
    if ($ECON_KEY !== '' && in_array($ECON_PROVIDER, ['tradingeconomics', 'fmp', 'finnhub'], true)) return;
    foreach (glob(__DIR__ . '/econ-us-*.json') ?: [] as $file) {
        $key = 'econ_seed:' . basename($file) . ':' . filesize($file);
        if (setting($key, '') !== '') continue;
        $data = json_decode((string)file_get_contents($file), true);
        if (is_array($data)) { $n = econ_import($data); save_setting($key, (string)$n); }
    }
}
function econ_sync(string $from, string $to): void {
    global $ECON_PROVIDER, $ECON_KEY;
    if ($ECON_KEY === '' || !in_array($ECON_PROVIDER, ['tradingeconomics', 'fmp', 'finnhub'], true)) return;
    $today = gmdate('Y-m-d'); $need = [];
    econ_schema();
    $hot = (bool)q("SELECT 1 FROM econ_events WHERE ts BETWEEN ? AND ? AND (actual IS NULL OR actual = '') AND source <> 'schedule' LIMIT 1", [time() - 1200, time() + 90])->fetch();
    for ($d = $from; $d <= $to; $d = date('Y-m-d', strtotime($d . ' +1 day'))) {
        $f = q('SELECT fetched_at FROM econ_sync WHERE day = ?', [$d])->fetchColumn();
        $stale = $d >= date('Y-m-d', strtotime($today . ' -2 day')) ? 600 : ($d > $today ? 21600 : PHP_INT_MAX);
        if ($hot && $d === $today) $stale = 20;   // a release is due or just out and the actual is missing: poll closely
        if ($f === false || time() - (int)$f > $stale) $need[] = $d;
    }
    if (!$need) return;
    try { $ev = econ_fetch(min($need), max($need)); } catch (Throwable $x) { return; }
    econ_store($ev, $ECON_PROVIDER);
    foreach ($need as $d) {
        if (q('UPDATE econ_sync SET fetched_at = ? WHERE day = ?', [time(), $d])->rowCount() === 0) q('INSERT INTO econ_sync (day, fetched_at) VALUES (?, ?)', [$d, time()]);
    }
}
/** Market data provider abstraction: 1-minute candles, cached per UTC day. */
function candles_sync(int $from, int $to, ?string $symbol = null): void {
    global $MARKET_PROVIDER, $MARKET_KEY, $MARKET_SYMBOL;
    $SYM = $symbol ?: $MARKET_SYMBOL;
    if ($MARKET_PROVIDER !== 'databento' || $MARKET_KEY === '') return;
    for ($day = gmdate('Y-m-d', $from); $day <= gmdate('Y-m-d', $to); $day = gmdate('Y-m-d', strtotime($day . ' +1 day UTC'))) {
        $f = q('SELECT fetched_at FROM candle_sync WHERE symbol = ? AND day = ?', [$SYM, $day])->fetchColumn();
        $isToday = $day === gmdate('Y-m-d');
        if ($f !== false && (!$isToday || time() - (int)$f < 180)) continue;
        $start = $day . 'T00:00:00Z'; $endTs = min(strtotime($day . ' +1 day UTC'), time() - 900, class_exists('ChartData', false) ? ChartData::horizon() : time() - 86400);   // licence delay (chart_data_min_age_hours)
        if ($endTs <= strtotime($start)) continue;
        $url = 'https://hist.databento.com/v0/timeseries.get_range?' . http_build_query([
            'dataset' => 'GLBX.MDP3', 'symbols' => $SYM, 'stype_in' => 'continuous', 'schema' => 'ohlcv-1m',
            'start' => $start, 'end' => gmdate('Y-m-d\TH:i:s\Z', $endTs), 'encoding' => 'json', 'pretty_px' => 'true', 'pretty_ts' => 'true', 'map_symbols' => 'false']);
        [$code, $body] = http_get($url, [], $MARKET_KEY);
        if ($code !== 200) { error_log('Trading Journal: market data (Databento) HTTP ' . $code . ' ' . substr($body, 0, 200)); continue; }
        $pdo = db(); $pdo->beginTransaction();
        foreach (preg_split('/\r?\n/', $body) as $line) {
            $r = json_decode($line, true); if (!is_array($r)) continue;
            $ts = $r['hd']['ts_event'] ?? null; $t = is_numeric($ts) ? intdiv((int)$ts, 1000000000) : strtotime((string)$ts);
            if (!$t) continue;
            $vals = [(float)$r['open'], (float)$r['high'], (float)$r['low'], (float)$r['close'], (int)($r['volume'] ?? 0)];
            if (q('UPDATE candles SET o = ?, h = ?, l = ?, c = ?, v = ? WHERE symbol = ? AND t = ?', [...$vals, $SYM, $t])->rowCount() === 0)
                q('INSERT INTO candles (symbol, t, o, h, l, c, v) VALUES (?, ?, ?, ?, ?, ?, ?)', [$SYM, $t, ...$vals]);
        }
        $pdo->commit();
        if (q('UPDATE candle_sync SET fetched_at = ? WHERE symbol = ? AND day = ?', [time(), $SYM, $day])->rowCount() === 0)
            q('INSERT INTO candle_sync (symbol, day, fetched_at) VALUES (?, ?, ?)', [$SYM, $day, time()]);
    }
}

/* ================= accounts & sessions ================= */
function bootstrap_admin(): void {
    global $cfg;
    if ((int)q('SELECT COUNT(*) FROM users')->fetchColumn() > 0) return;
    $u = trim((string)($cfg['user'] ?? ''));
    $p = (string)($cfg['password'] ?? '');
    if (!preg_match(USERNAME_RE, $u) || strlen($p) < 10 || $p === 'change-me-to-a-long-random-password') {
        html_out(500, 'Setup required', 'Open <code>config.php</code> and set <code>user</code> (3–32 letters, digits, <code>_ . -</code>) and <code>password</code> (10+ characters). They create the first administrator account.');
    }
    // Keeps the existing single-user data: documents were stored under this same id.
    q('INSERT INTO users (id, username, username_lc, password_hash, is_admin, created_at) VALUES (?, ?, ?, ?, 1, ?)',
      [$u, $u, strtolower($u), password_hash($p, PASSWORD_DEFAULT), now()]);
}
function set_session_cookie(string $token, int $expires): void {
    global $HTTPS;
    setcookie(COOKIE, $token, ['expires' => $expires, 'path' => cookie_path(), 'secure' => $HTTPS, 'httponly' => true, 'samesite' => 'Lax']);
}
function create_session(string $userId): void {
    $token = bin2hex(random_bytes(32));
    $exp = time() + SESSION_TTL;
    q('INSERT INTO sessions (token_hash, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)', [hash('sha256', $token), $userId, time(), $exp]);
    q('UPDATE users SET last_login = ? WHERE id = ?', [now(), $userId]);
    set_session_cookie($token, $exp);
    if (random_int(1, 20) === 1) {
        q('DELETE FROM sessions WHERE expires_at < ?', [time()]);
        q('DELETE FROM attempts WHERE at < ?', [time() - 86400]);
    }
}
/** sign-up step 1 emails (marketing follow-up of unfinished sign-ups) */
function lead_table(PDO $pdo): void {
    static $done = false; if ($done) return;
    $pdo->exec('CREATE TABLE IF NOT EXISTS signup_leads (email_lc VARCHAR(190) NOT NULL PRIMARY KEY, lang VARCHAR(5) NULL, ref VARCHAR(32) NULL, utm VARCHAR(190) NULL, created_at INT NOT NULL, updated_at INT NOT NULL, attempts INT NOT NULL DEFAULT 1, completed_at INT NULL, user_id VARCHAR(120) NULL)');
    $done = true;
}
function current_user(): ?array {
    $t = (string)($_COOKIE[COOKIE] ?? '');
    if (!preg_match('/^[a-f0-9]{64}$/', $t)) return null;
    $row = q('SELECT s.expires_at, u.id, u.username, u.full_name, u.first_name, u.last_name, u.email, u.created_at, u.is_admin, u.disabled, u.recovery_hash, u.recovery_created, u.experience FROM sessions s JOIN users u ON u.id = s.user_id WHERE s.token_hash = ?',
             [hash('sha256', $t)])->fetch();
    if (!$row || (int)$row['disabled'] === 1 || (int)$row['expires_at'] < time()) return null;
    if ((int)$row['expires_at'] - time() < SESSION_TTL - 86400) { // slide the expiry at most once a day
        $exp = time() + SESSION_TTL;
        q('UPDATE sessions SET expires_at = ? WHERE token_hash = ?', [$exp, hash('sha256', $t)]);
        set_session_cookie($t, $exp);
    }
    return ['id' => $row['id'], 'username' => $row['username'], 'full_name' => $row['full_name'] ?? null, 'first_name' => $row['first_name'] ?? null, 'last_name' => $row['last_name'] ?? null, 'email' => $row['email'] ?? null, 'created_at' => $row['created_at'] ?? null, 'is_admin' => (int)$row['is_admin'] === 1,
            'has_recovery' => !empty($row['recovery_hash']), 'recovery_created' => $row['recovery_created'], 'experience' => $row['experience'] ?? null];
}
function end_session(): void {
    $t = (string)($_COOKIE[COOKIE] ?? '');
    if (preg_match('/^[a-f0-9]{64}$/', $t)) q('DELETE FROM sessions WHERE token_hash = ?', [hash('sha256', $t)]);
    set_session_cookie('', time() - 3600);
}
function lang_code($l): string { $l = strtolower(substr((string)$l, 0, 2)); return in_array($l, ['en', 'fr', 'es'], true) ? $l : 'en'; }
/**
 * Emails from hello@makeitsweep.com.
 * With config 'smtp' => ['host' => 'mail.makeitsweep.com', 'port' => 465, 'user' => 'hello@makeitsweep.com', 'pass' => '…']
 * the email is sent through the mailbox (SMTP over SSL, authenticated: best delivery, lands in « Sent »).
 * Without it, PHP mail() is used from the same address.
 */
function sweep_mail(string $to, string $subject, string $text, string $html = ''): bool {
    global $cfg, $MAIL_FROM, $SUPPORT;
    $from = $MAIL_FROM; $sc = (array)($cfg['smtp'] ?? []);
    $bnd = 'sw' . bin2hex(random_bytes(8));
    $subj = '=?UTF-8?B?' . base64_encode($subject) . '?=';
    $body = $html === '' ? $text
        : "--$bnd\r\nContent-Type: text/plain; charset=UTF-8\r\nContent-Transfer-Encoding: base64\r\n\r\n" . chunk_split(base64_encode($text))
        . "--$bnd\r\nContent-Type: text/html; charset=UTF-8\r\nContent-Transfer-Encoding: base64\r\n\r\n" . chunk_split(base64_encode($html)) . "--$bnd--\r\n";
    $ctype = $html === '' ? "Content-Type: text/plain; charset=UTF-8\r\nContent-Transfer-Encoding: 8bit" : "Content-Type: multipart/alternative; boundary=\"$bnd\"";
    $hdr = "From: Sweep <$from>\r\nReply-To: " . ($SUPPORT ?: $from) . "\r\nMIME-Version: 1.0\r\n" . $ctype;
    if (!empty($sc['host']) && !empty($sc['user']) && !empty($sc['pass'])) {
        try {
            $port = (int)($sc['port'] ?? 465);
            $fp = @stream_socket_client(($port === 465 ? 'ssl://' : 'tcp://') . $sc['host'] . ':' . $port, $en, $es, 15);
            if (!$fp) throw new RuntimeException("connect $es");
            stream_set_timeout($fp, 15);
            $rd = function () use ($fp) { $o = ''; while (($l = fgets($fp, 515)) !== false) { $o .= $l; if (isset($l[3]) && $l[3] === ' ') break; } return $o; };
            $cmd = function (string $c, array $ok) use ($fp, $rd) { fwrite($fp, $c . "\r\n"); $r = $rd(); if (!in_array((int)substr($r, 0, 3), $ok, true)) throw new RuntimeException(trim($r)); return $r; };
            $rd();
            $cmd('EHLO makeitsweep.com', [250]);
            if ($port === 587) { $cmd('STARTTLS', [220]); stream_socket_enable_crypto($fp, true, STREAM_CRYPTO_METHOD_TLS_CLIENT); $cmd('EHLO makeitsweep.com', [250]); }
            $cmd('AUTH LOGIN', [334]); $cmd(base64_encode($sc['user']), [334]); $cmd(base64_encode($sc['pass']), [235]);
            $cmd('MAIL FROM:<' . $from . '>', [250]); $cmd('RCPT TO:<' . $to . '>', [250, 251]); $cmd('DATA', [354]);
            $msg = "To: <$to>\r\nSubject: $subj\r\nDate: " . date('r') . "\r\nMessage-ID: <" . bin2hex(random_bytes(12)) . "@makeitsweep.com>\r\n" . $hdr . "\r\n\r\n" . $body;
            $msg = preg_replace('/^\./m', '..', str_replace(["\r\n", "\n"], ["\n", "\r\n"], $msg));
            $cmd($msg . "\r\n.", [250]); @fwrite($fp, "QUIT\r\n"); fclose($fp);
            return true;
        } catch (Throwable $e) { error_log('Sweep: SMTP failed (' . $e->getMessage() . '), falling back to mail()'); }
    }
    $ok = function_exists('mail') && @mail($to, $subj, $body, $hdr, '-f' . $from);
    if (!$ok) error_log('Sweep: email could not be sent to ' . $to);
    return $ok;
}

/** Password reset email, in the trader's language (text + a clean HTML version). */
function send_reset_email(string $to, string $username, string $token, string $lang): bool {
    global $APP_URL, $SUPPORT;
    $base = $APP_URL !== '/' ? $APP_URL : ((isset($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off' ? 'https://' : 'http://') . ($_SERVER['HTTP_HOST'] ?? 'localhost') . '/');
    $link = $base . '?reset=' . $token;
    $first = $username;
    try { $fn = q('SELECT first_name FROM users WHERE email_lc = ?', [strtolower($to)])->fetchColumn(); if ($fn) $first = (string)$fn; } catch (Throwable $e) { /* older base */ }
    $L = ['en' => ['s' => 'Reset your Sweep password', 'hi' => "Hi $first,", 'p1' => 'Someone asked to reset the password of your Sweep account. Choose a new one with the button below. The link works for one hour.', 'btn' => 'Choose a new password', 'p2' => "If it wasn't you, ignore this email: your password stays the same.", 'help' => 'A question? Reply to this email or write to', 'sig' => 'The Sweep team'],
          'fr' => ['s' => 'Réinitialise ton mot de passe Sweep', 'hi' => "Salut $first,", 'p1' => 'Quelqu’un a demandé à réinitialiser le mot de passe de ton compte Sweep. Choisis-en un nouveau avec le bouton ci-dessous. Le lien est valide une heure.', 'btn' => 'Choisir un nouveau mot de passe', 'p2' => 'Si ce n’était pas toi, ignore cet email : ton mot de passe reste le même.', 'help' => 'Une question ? Réponds à cet email ou écris à', 'sig' => 'L’équipe Sweep'],
          'es' => ['s' => 'Restablece tu contraseña de Sweep', 'hi' => "Hola $first,", 'p1' => 'Alguien pidió restablecer la contraseña de tu cuenta de Sweep. Elige una nueva con el botón de abajo. El enlace vale una hora.', 'btn' => 'Elegir una nueva contraseña', 'p2' => 'Si no fuiste tú, ignora este correo: tu contraseña no cambia.', 'help' => '¿Una pregunta? Responde a este correo o escribe a', 'sig' => 'El equipo de Sweep']][$lang] ?? null;
    if (!$L) $L = ['s' => 'Reset your Sweep password', 'hi' => "Hi $first,", 'p1' => 'Someone asked to reset the password of your Sweep account. Choose a new one with the button below. The link works for one hour.', 'btn' => 'Choose a new password', 'p2' => "If it wasn't you, ignore this email: your password stays the same.", 'help' => 'A question? Reply to this email or write to', 'sig' => 'The Sweep team'];
    $sup = $SUPPORT ?: 'hello@makeitsweep.com';
    $text = $L['hi'] . "\n\n" . $L['p1'] . "\n\n" . $link . "\n\n" . $L['p2'] . "\n\n" . $L['help'] . " $sup\n\n— " . $L['sig'];
    $h = fn($x) => htmlspecialchars($x, ENT_QUOTES, 'UTF-8');
    $html = '<!doctype html><html><body style="margin:0;background:#0b0b0c;padding:32px 16px;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Inter,Arial,sans-serif;color:#e9e9ee">'
      . '<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td align="center"><table role="presentation" width="100%" style="max-width:520px;background:#141416;border:1px solid #26262a;border-radius:18px" cellpadding="0" cellspacing="0"><tr><td style="padding:32px 32px 28px">'
      . '<div style="font-size:18px;font-weight:700;letter-spacing:-.01em;margin-bottom:24px">sweep</div>'
      . '<p style="margin:0 0 12px;font-size:16px">' . $h($L['hi']) . '</p><p style="margin:0 0 24px;font-size:15px;line-height:1.55;color:#b9b9c2">' . $h($L['p1']) . '</p>'
      . '<a href="' . $h($link) . '" style="display:inline-block;background:#4c8dff;color:#0b0b0c;font-weight:600;font-size:15px;text-decoration:none;padding:13px 24px;border-radius:999px">' . $h($L['btn']) . '</a>'
      . '<p style="margin:24px 0 0;font-size:13px;line-height:1.55;color:#8a8a94">' . $h($L['p2']) . '</p>'
      . '<p style="margin:16px 0 0;font-size:13px;color:#8a8a94">' . $h($L['help']) . ' <a href="mailto:' . $h($sup) . '" style="color:#4c8dff">' . $h($sup) . '</a></p>'
      . '</td></tr></table><p style="font-size:12px;color:#5c5c66;margin:16px 0 0">' . $h($L['sig']) . ' · makeitsweep.com</p></td></tr></table></body></html>';
    return sweep_mail($to, $L['s'], $text, $html);
}
/** Campaign attribution: UTM tags from the website's sweep_utm cookie (first touch) + the two optional sign-up answers. */
function save_signup_attribution(string $uid, array $b): void {
    $utm = [];
    if (!empty($_COOKIE['sweep_utm'])) { $d = json_decode((string)$_COOKIE['sweep_utm'], true); if (is_array($d)) $utm = $d; }
    $tag = function ($v, int $max) { $v = preg_replace('/[^A-Za-z0-9_\-\.]/', '', trim((string)($v ?? ''))); return $v === '' ? null : substr($v, 0, $max); };
    $txt = function ($v, int $max) { $v = trim(preg_replace('/[\x00-\x1F\x7F]+/u', ' ', (string)($v ?? ''))); if ($v === '') return null; return function_exists('mb_substr') ? mb_substr($v, 0, $max) : substr($v, 0, $max); };
    $via = in_array($b['found_via'] ?? '', ['tiktok', 'instagram', 'discord', 'friend', 'other'], true) ? (string)$b['found_via'] : null;
    q('UPDATE users SET utm_source = ?, utm_medium = ?, utm_campaign = ?, utm_content = ?, found_via = ?, found_video = ?, accounts_info = ? WHERE id = ?', [
        $tag($utm['utm_source'] ?? null, 30), $tag($utm['utm_medium'] ?? null, 30), $tag($utm['utm_campaign'] ?? null, 50), $tag($utm['utm_content'] ?? null, 50),
        $via, in_array($via, ['tiktok', 'instagram'], true) ? $txt($b['found_video'] ?? null, 120) : null, $txt($b['accounts_info'] ?? null, 160), $uid]);
}
/** /100 page counter: traders who joined since the campaign start (internal/test accounts and administrators excluded). */
function cohort_count(): array {
    global $cfg, $DATA;
    $c = (array)($cfg['cohort'] ?? []);
    $start = (string)($c['start'] ?? '2026-10-11T04:00:00Z');   // Oct 11, 2026, midnight New York
    $total = (int)($c['total'] ?? 100);
    $mode = (string)($c['count'] ?? 'signups');                  // 'signups' or 'activated' (account + first trade)
    $file = $DATA . '/cohort-count.json';
    if (is_file($file) && time() - filemtime($file) < 60) { $j = json_decode((string)file_get_contents($file), true); if (is_array($j)) return $j; }
    $startIso = gmdate('Y-m-d\TH:i:s\Z', (int)strtotime($start));
    $ids = q('SELECT id FROM users WHERE created_at >= ? AND is_admin = 0 AND COALESCE(is_internal, 0) = 0 AND disabled = 0', [$startIso])->fetchAll(PDO::FETCH_COLUMN);
    $taken = count($ids);
    if ($mode === 'activated' && $ids) {
        $taken = 0;
        foreach ($ids as $id) {
            $has = ['accounts' => false, 'trades' => false];
            foreach (q("SELECT collection, data FROM documents WHERE user_id = ? AND collection IN ('accounts','trades')", [$id]) as $r) {
                $d = json_decode((string)$r['data'], true) ?: []; if (empty($d['demo'])) $has[$r['collection']] = true;
            }
            if ($has['accounts'] && $has['trades']) $taken++;
        }
    }
    $out = ['taken' => min($taken, $total), 'total' => $total];
    @file_put_contents($file, json_encode($out));
    return $out;
}
/** Billing module (billing/) + private config (sweep-private/billing-config.php). Off when either is missing: the app works as before. */
function billing_on(): bool {
    static $on = null; if ($on !== null) return $on;
    global $cfg;
    if (!empty($cfg['billing_config']) && !defined('SWEEP_BILLING_CONFIG')) define('SWEEP_BILLING_CONFIG', (string)$cfg['billing_config']);
    if (!is_file(__DIR__ . '/billing/billing-core.php')) return $on = false;
    require_once __DIR__ . '/billing/billing-core.php';
    try { sb_config(); return $on = true; } catch (Throwable $e) { return $on = false; }
}
/** What a trader has, for the Traders page: plan, where it comes from, and when it ends. */
function billing_admin_plan(string $uid): ?array {
    if (!billing_on()) return null;
    try {
        sb_schema(db());
        $e = sb_effective(db(), $uid);
        $g = $e['grant']; $sub = $e['sub'];
        $src = $e['source'];
        if ($g && ($g['reason'] ?? '') === 'comp' && (int)$g['ends_at'] - time() > 3650 * 86400) $src = 'permanent';
        return ['plan' => $e['plan'], 'source' => $src, 'ends_at' => $g && $src !== 'permanent' && $src !== 'subscription' ? (int)$g['ends_at'] : null,
            'sub' => $sub ? ['plan' => $sub['plan'], 'status' => $sub['status']] : null, 'live' => sb_live($uid)];
    } catch (Throwable $x) { return null; }
}
/** The trader's real trading account ids (sample data excluded), oldest first. */
function billing_account_ids(string $uid): array {
    $out = [];
    foreach (q("SELECT id, data FROM documents WHERE user_id = ? AND collection = 'accounts' ORDER BY created_at, id", [$uid]) as $r) {
        $d = json_decode((string)$r['data'], true) ?: [];
        if (!empty($d['demo'])) continue;
        $out[] = (string)$r['id'];
    }
    return $out;
}
/** Count recent attempts for each key; refuse when any key is over its limit. */
function throttle(array $keys, int $max, int $window): void {
    foreach ($keys as $k) {
        if ((int)q('SELECT COUNT(*) FROM attempts WHERE k = ? AND at > ?', [$k, time() - $window])->fetchColumn() >= $max) {
            json_out(429, ['error' => 'Too many attempts. Wait a few minutes and try again.']);
        }
    }
}
function record_attempt(array $keys): void { foreach ($keys as $k) q('INSERT INTO attempts (k, at) VALUES (?, ?)', [$k, time()]); }
function delete_user_everything(string $uid): void {
    global $DATA;
    foreach (q('SELECT id FROM uploads WHERE user_id = ?', [$uid])->fetchAll() as $r) @unlink($DATA . '/uploads/' . $r['id']);
    q('DELETE FROM uploads WHERE user_id = ?', [$uid]);
    q('DELETE FROM documents WHERE user_id = ?', [$uid]);
    growth_delete_user(db(), $uid);
    if (class_exists('GameCrew', false)) { try { GameCrew::schema(); GameCrew::leave($uid); GameCrew::end($uid); if (class_exists('GameDiscord', false)) GameDiscord::unlink($uid); } catch (Throwable $e) { error_log('[Sweep crew] delete: ' . $e->getMessage()); } }
    if (class_exists('GameEngine', false)) { try { foreach (['user_game_profile', 'game_days', 'xp_events', 'user_badges', 'game_celebrations', 'game_analytics', 'user_map_nodes', 'user_missions', 'user_rewards', 'user_bosses', 'weekly_reviews', 'edge_reveals', 'user_cosmetics', 'user_quests', 'monthly_wrapped', 'user_season', 'social_profile', 'league_members', 'crew_reactions'] as $tb) db()->prepare("DELETE FROM $tb WHERE user_id = ?")->execute([$uid]); } catch (Throwable $e) { error_log('[Sweep game] delete: ' . $e->getMessage()); } }
    if (class_exists('Notify', false)) { try { Notify::deleteUser($uid); } catch (Throwable $e) { error_log('[Sweep notify] delete: ' . $e->getMessage()); } }
    foreach (['ai_cache', 'ai_log'] as $t) { try { q("DELETE FROM $t WHERE user_id = ?", [$uid]); } catch (Throwable $e) { /* AI tables not created yet */ } }
    if (billing_on()) {
        try {
            require_once __DIR__ . '/billing/billing-stripe.php';
            if (!empty(sb_cfg()['live'])) foreach (q("SELECT id FROM billing_subs WHERE uid = ? AND source = 'stripe' AND status IN ('active','trialing','past_due')", [$uid]) as $r) {
                try { sb_stripe('DELETE', 'subscriptions/' . $r['id']); } catch (Throwable $e) { error_log('[Sweep billing] cancel on delete: ' . $e->getMessage()); }
            }
            foreach (['billing_usage', 'billing_upsell', 'billing_grants', 'billing_subs', 'billing_users'] as $t) { try { q("DELETE FROM $t WHERE uid = ?", [$uid]); } catch (Throwable $e) {} }
        } catch (Throwable $e) { error_log('[Sweep billing] delete: ' . $e->getMessage()); }
    }
    q('DELETE FROM sessions WHERE user_id = ?', [$uid]);
    q('DELETE FROM users WHERE id = ?', [$uid]);
}
/** product analytics, kept in Sweep's own database (no third-party tool): activation, retention, AI cost… */
function product_event(string $uid, string $event, array $meta = []): void {
    try {
        static $ready = false;
        if (!$ready) { db()->exec("CREATE TABLE IF NOT EXISTS game_analytics (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL, event VARCHAR(40) NOT NULL, meta_json TEXT NULL, created_at INT NOT NULL)"); $ready = true; }
        q('INSERT INTO game_analytics (user_id, event, meta_json, created_at) VALUES (?, ?, ?, ?)', [$uid, substr($event, 0, 40), $meta ? json_encode($meta) : null, now()]);
    } catch (Throwable $e) { error_log('[Sweep event] ' . $e->getMessage()); }
}

function require_csrf(): void {
    // Cross-site forms cannot set custom headers, and browsers always send Origin on cross-site POSTs.
    if (($_SERVER['HTTP_X_REQUESTED_WITH'] ?? '') !== 'fetch') json_out(403, ['error' => 'Missing request header.']);
    $origin = (string)($_SERVER['HTTP_ORIGIN'] ?? '');
    if ($origin !== '' && strcasecmp((string)parse_url($origin, PHP_URL_HOST), (string)preg_replace('/:\d+$/', '', (string)($_SERVER['HTTP_HOST'] ?? ''))) !== 0) {
        json_out(403, ['error' => 'Cross-site request refused.']);
    }
}

/* ================= routes ================= */
try {
    bootstrap_admin();
    // prop firm presets: no full check for 8 days → email to the support address (looked at once an hour, after the response)
    register_shutdown_function(function () {
        global $SUPPORT;
        try {
            if (!is_file(__DIR__ . '/presets/check.php')) return;
            $w = rtrim((string)($GLOBALS['DATA'] ?? ''), '/') . '/presets-watchdog.json';
            if (is_file($w) && filemtime($w) > time() - 3600) return;   // cheap: one file stat per request
            if (function_exists('fastcgi_finish_request')) @fastcgi_finish_request();
            require_once __DIR__ . '/presets/check.php';
            pr_watchdog(fn(string $subj, string $text) => sweep_mail($SUPPORT ?: 'hello@makeitsweep.com', $subj, $text));
        } catch (Throwable $e) { error_log('Sweep presets watchdog: ' . $e->getMessage()); }
    });
    require_once __DIR__ . '/growth/referral.php';
    require_once __DIR__ . '/growth/feedback.php';
    if (is_file(__DIR__ . '/notify/notify.php')) require_once __DIR__ . '/notify/notify.php';   // notification center + events (Feature 0)
    if (is_file(__DIR__ . '/game/game.php')) require_once __DIR__ . '/game/game.php';
    if (!empty($cfg['chart_config']) && !defined('SWEEP_CHART_CONFIG')) define('SWEEP_CHART_CONFIG', (string)$cfg['chart_config']);
    if (is_file(__DIR__ . '/chart/chart.php')) require_once __DIR__ . '/chart/chart.php';     // real candle charts (Databento)         // gamification V1 « Sweep the day »
    // /100 page counter, public: no personal data, cached 60 s, readable from makeitsweep.com only
    if (in_array($route, ['api/cohort-count.php', 'api/cohort-count'], true)) {
        $origin = (string)($_SERVER['HTTP_ORIGIN'] ?? '');
        if (in_array($origin, ['https://makeitsweep.com', 'https://www.makeitsweep.com'], true)) { header('Access-Control-Allow-Origin: ' . $origin); header('Vary: Origin'); }
        if ($method === 'OPTIONS') { header('Access-Control-Allow-Methods: GET'); http_response_code(204); exit; }
        $out = json_encode(cohort_count());
        http_response_code(200); header('Content-Type: application/json; charset=utf-8'); header('Cache-Control: public, max-age=60');
        echo $out; exit;
    }
    // /r/CODE (referral link): remember the code, then go to sign-up
    if (preg_match('#^ref/([A-Za-z0-9]{3,16})$#', $route, $rm)) {
        try { ref_capture(db(), $rm[1]); } catch (Throwable $e) { error_log('[Sweep referral] capture: ' . $e->getMessage()); }
        header('Location: /?signup=1', true, 302); exit;
    }
    // /s/ID (public share link) and /s/ID.png (its image): a snapshot of one card, nothing else of the account
    if (preg_match('#^s/([A-Za-z0-9]{10,24})(\.png)?$#', $route, $sm)) {
        require_once __DIR__ . '/growth/share-links.php';
        sl_public(db(), $sm[1], !empty($sm[2]));
    }
    // sign-up step 1: keep the email (never the password) so an unfinished sign-up can be followed up
    if ($route === 'api/auth/lead' && $method === 'POST') {
        require_csrf();
        $b = json_decode((string) file_get_contents('php://input'), true) ?: [];
        if (!empty($b['website'])) json_out(200, ['ok' => true]);   // bots fill the hidden field
        $em = strtolower(trim((string) ($b['email'] ?? '')));
        if (!filter_var($em, FILTER_VALIDATE_EMAIL) || strlen($em) > 190) json_out(400, ['error' => 'Enter a valid email.']);
        $ip = 'lead:' . hash('sha256', (string) ($_SERVER['REMOTE_ADDR'] ?? ''));
        throttle([$ip], 20, 3600); record_attempt([$ip]);
        lead_table(db());
        $ex = q('SELECT 1 FROM signup_leads WHERE email_lc = ?', [$em])->fetch();
        if ($ex) q('UPDATE signup_leads SET updated_at = ?, attempts = attempts + 1 WHERE email_lc = ?', [time(), $em]);
        else q('INSERT INTO signup_leads (email_lc, lang, ref, utm, created_at, updated_at, attempts) VALUES (?, ?, ?, ?, ?, ?, 1)', [$em, substr((string) ($b['lang'] ?? ''), 0, 5), substr((string) ($b['ref'] ?? ''), 0, 32), substr((string) ($b['utm'] ?? ''), 0, 190), time(), time()]);
        json_out(200, ['ok' => true]);
    }
    // Stripe webhook: public, raw body, verified by its signature (no session, no CSRF header)
    if ($route === 'api/billing/webhook' && $method === 'POST') {
        if (!billing_on()) json_out(404, ['error' => 'billing not configured']);
        require_once __DIR__ . '/billing/billing-routes.php';
        sweep_billing_webhook_route(db());
    }
    $ACCESS = access();
    if ($method !== 'GET' && $method !== 'HEAD') require_csrf();

    /* ---------- public ---------- */
    if ($route === 'api/auth/config' && $method === 'GET') {
        $trial = null;   // the sign-up screen shows the free trial when billing is live
        if (billing_on()) { try { $bc = sb_cfg(); if (!empty($bc['live']) && !empty($bc['trial']['days'])) $trial = ['days' => (int)$bc['trial']['days'], 'plan' => (string)$bc['trial']['plan']]; } catch (Throwable $e) {} }
        $invite = null; try { $invite = ref_signup_banner(db()); } catch (Throwable $e) {}
        json_out(200, ['registration' => $ACCESS['registration'], 'reset' => $ACCESS['reset'], 'trial' => $trial, 'invite' => $invite]);
    }

    if ($route === 'api/auth/login' && $method === 'POST') {
        $b = body_json(4096);
        $name = strtolower(trim((string)($b['username'] ?? '')));
        $pass = (string)($b['password'] ?? '');
        $keys = ['ip:' . client_ip(), 'u:' . $name];
        throttle($keys, 10, 900);
        $u = q('SELECT id, password_hash, disabled FROM users WHERE ' . (strpos($name, '@') !== false ? 'email_lc' : 'username_lc') . ' = ?', [$name])->fetch();
        $valid = password_verify($pass, $u ? $u['password_hash'] : '$2y$10$usesomesillystringfore7hnbRJHxXVLeakoG8K30oukPsA.ztMG');
        if (!$u || !$valid) { record_attempt($keys); json_out(401, ['error' => 'Incorrect username, email or password.']); }
        if ((int)$u['disabled'] === 1) json_out(403, ['error' => 'This account is disabled. Contact Sweep support.']);
        if (password_needs_rehash($u['password_hash'], PASSWORD_DEFAULT)) q('UPDATE users SET password_hash = ? WHERE id = ?', [password_hash($pass, PASSWORD_DEFAULT), $u['id']]);
        q('DELETE FROM attempts WHERE k = ?', ['u:' . $name]);
        create_session($u['id']);
        if (function_exists('nt_fire')) nt_fire('user.signed_in', ['uid' => (string)$u['id']]);
        json_out(200, ['ok' => true]);
    }

    if ($route === 'api/auth/register' && $method === 'POST') {
        if ($ACCESS['registration'] === 'closed') json_out(403, ['error' => 'Registration is closed for now.']);
        $b = body_json(4096);
        $name = trim((string)($b['username'] ?? ''));
        $pass = (string)($b['password'] ?? '');
        $email = strtolower(trim((string)($b['email'] ?? '')));
        $keys = ['reg:' . client_ip()];
        throttle($keys, 5, 3600);
        // basic anti-bot: a hidden field humans never fill, and a form filled in under 2 seconds
        if (trim((string)($b['website'] ?? '')) !== '' || (int)($b['elapsed'] ?? 9999) < 2000) { record_attempt($keys); json_out(400, ['error' => 'Please try again.']); }
        if (empty($b['consent'])) json_out(400, ['error' => 'Please confirm you are 18 or older and accept the Terms and Privacy policy.']);
        if (!filter_var($email, FILTER_VALIDATE_EMAIL) || strlen($email) > 190) json_out(400, ['error' => 'Enter a valid email.']);
        if ($ACCESS['registration'] === 'invite' && !hash_equals(strtolower($ACCESS['invite']), strtolower(trim((string)($b['invite'] ?? ''))))) { record_attempt($keys); json_out(403, ['error' => 'Invalid invite code.']); }
        if ($name === '') {   // one-screen sign-up: a username from the email (editable when the profile is completed)
            $base = substr(preg_replace('/[^a-z0-9_.-]/', '', strtolower(strstr($email, '@', true) ?: 'trader')) ?: 'trader', 0, 24);
            if (strlen($base) < 3) $base .= 'trader';
            $name = $base; $k = 1;
            while (q('SELECT 1 FROM users WHERE username_lc = ?', [strtolower($name)])->fetch()) $name = $base . (++$k);
        }
        if (!preg_match(USERNAME_RE, $name)) json_out(400, ['error' => 'Username: 3–32 characters, letters, digits, _ . - only.']);
        if (strlen($pass) < 10 || strlen($pass) > 200) json_out(400, ['error' => 'Password: at least 10 characters.']);
        if (strcasecmp($pass, $name) === 0) json_out(400, ['error' => 'The password cannot be your username.']);
        if ((int)q('SELECT COUNT(*) FROM users')->fetchColumn() >= $MAX_USERS) json_out(403, ['error' => 'Sweep is full for now. Try again later.']);
        if (q('SELECT 1 FROM users WHERE username_lc = ?', [strtolower($name)])->fetch()) json_out(409, ['error' => 'This username is taken.']);
        if (q('SELECT 1 FROM users WHERE email_lc = ?', [$email])->fetch()) json_out(409, ['error' => 'An account already uses this email.']);
        $id = 'u_' . bin2hex(random_bytes(8));
        q('INSERT INTO users (id, username, username_lc, password_hash, is_admin, created_at, email, email_lc, terms_accepted_at, lang) VALUES (?, ?, ?, ?, 0, ?, ?, ?, ?, ?)',
          [$id, $name, strtolower($name), password_hash($pass, PASSWORD_DEFAULT), now(), $email, $email, now(), lang_code($b['lang'] ?? 'en')]);
        record_attempt($keys);
        $fn = trim(preg_replace('/\s+/u', ' ', strip_tags((string)($b['full_name'] ?? ''))) ?? '');
        if ($fn !== '') q('UPDATE users SET full_name = ? WHERE id = ?', [mb_substr($fn, 0, 80), $id]);
        try { lead_table(db()); q('UPDATE signup_leads SET completed_at = ?, user_id = ? WHERE email_lc = ?', [time(), $id, $email]); } catch (Throwable $e) { /* never blocks a sign-up */ }
        try { save_signup_attribution($id, $b); } catch (Throwable $e) { error_log('[Sweep] attribution: ' . $e->getMessage()); }
        try { ref_attach_on_signup(db(), $id); } catch (Throwable $e) { error_log('[Sweep referral] signup: ' . $e->getMessage()); }
        product_event($id, 'signup_completed', ['lang' => lang_code($b['lang'] ?? 'en'), 'utm_source' => substr((string)($b['utm_source'] ?? ''), 0, 60), 'utm_campaign' => substr((string)($b['utm_campaign'] ?? ''), 0, 60),
            'device' => preg_match('/iPhone|Android|Mobile/i', (string)($_SERVER['HTTP_USER_AGENT'] ?? '')) ? 'mobile' : 'desktop']);
        create_session($id);
        json_out(201, ['ok' => true]);
    }

    if ($route === 'api/auth/logout' && $method === 'POST') { end_session(); json_out(200, ['ok' => true]); }

    if ($route === 'api/auth/forgot' && $method === 'POST') {
        // Always answers the same way, whether or not the email exists.
        $b = body_json(2048);
        $email = strtolower(trim((string)($b['email'] ?? '')));
        throttle(['fg:' . client_ip()], 8, 3600);
        record_attempt(['fg:' . client_ip()]);
        if (filter_var($email, FILTER_VALIDATE_EMAIL)) {
            throttle(['fge:' . $email], 3, 3600);
            $u = q('SELECT id, username, disabled, lang FROM users WHERE email_lc = ?', [$email])->fetch();
            if ($u && (int)$u['disabled'] === 0) {
                record_attempt(['fge:' . $email]);
                $token = bin2hex(random_bytes(32));
                q('DELETE FROM reset_tokens WHERE user_id = ? OR expires_at < ?', [$u['id'], time()]);
                q('INSERT INTO reset_tokens (token_hash, user_id, expires_at, used) VALUES (?, ?, ?, 0)', [hash('sha256', $token), $u['id'], time() + 3600]);
                send_reset_email($email, (string)$u['username'], $token, lang_code($b['lang'] ?? ($u['lang'] ?? 'en')));
            }
        }
        json_out(200, ['ok' => true]);
    }

    if ($route === 'api/auth/reset' && $method === 'POST') {
        $b = body_json(2048);
        $token = (string)($b['token'] ?? '');
        $pass = (string)($b['password'] ?? '');
        throttle(['rt:' . client_ip()], 10, 900);
        if (!preg_match('/^[a-f0-9]{64}$/', $token)) json_out(400, ['error' => 'This reset link is invalid or has expired.']);
        $row = q('SELECT t.user_id, t.expires_at, t.used, u.username, u.disabled FROM reset_tokens t JOIN users u ON u.id = t.user_id WHERE t.token_hash = ?', [hash('sha256', $token)])->fetch();
        if (!$row || (int)$row['used'] === 1 || (int)$row['expires_at'] < time() || (int)$row['disabled'] === 1) { record_attempt(['rt:' . client_ip()]); json_out(400, ['error' => 'This reset link is invalid or has expired.']); }
        if (strlen($pass) < 10 || strlen($pass) > 200) json_out(400, ['error' => 'New password: at least 10 characters.']);
        if (strcasecmp($pass, (string)$row['username']) === 0) json_out(400, ['error' => 'The password cannot be your username.']);
        q('UPDATE users SET password_hash = ? WHERE id = ?', [password_hash($pass, PASSWORD_DEFAULT), $row['user_id']]);
        q('UPDATE reset_tokens SET used = 1 WHERE user_id = ?', [$row['user_id']]);
        q('DELETE FROM sessions WHERE user_id = ?', [$row['user_id']]);
        create_session($row['user_id']);
        json_out(200, ['ok' => true]);
    }

    if ($route === 'api/auth/recover' && $method === 'POST') {
        // Reset a forgotten password with username + code. The code is the trader's personal
        // recovery code, or — only if the admin chose it — the shared invite code.
        if ($ACCESS['reset'] === 'off') json_out(403, ['error' => 'Password reset is turned off. Contact Sweep support.']);
        $b = body_json(4096);
        $name = strtolower(trim((string)($b['username'] ?? '')));
        $code = (string)($b['code'] ?? '');
        $pass = (string)($b['password'] ?? '');
        $keys = ['rec:' . client_ip(), 'recu:' . $name];
        throttle(['rec:' . client_ip()], 10, 900);
        throttle(['recu:' . $name], 5, 900);
        $u = q('SELECT id, username, is_admin, disabled, recovery_hash FROM users WHERE username_lc = ?', [$name])->fetch();
        $fail = function () use ($keys) { record_attempt($keys); json_out(403, ['error' => 'Incorrect username or code.']); };
        if (!$u || (int)$u['disabled'] === 1) { password_verify('x', '$2y$10$usesomesillystringfore7hnbRJHxXVLeakoG8K30oukPsA.ztMG'); $fail(); }
        $viaInvite = false;
        if ($u['recovery_hash'] && password_verify(norm_code($code), $u['recovery_hash'])) {
            // personal recovery code: always accepted
        } elseif ($ACCESS['reset'] === 'invite' && (int)$u['is_admin'] === 0 && hash_equals(strtolower($ACCESS['invite']), strtolower(trim($code)))) {
            $viaInvite = true;   // never allowed for administrator accounts
        } else {
            $fail();
        }
        if (strlen($pass) < 10 || strlen($pass) > 200) json_out(400, ['error' => 'New password: at least 10 characters.']);
        if (strcasecmp($pass, (string)$u['username']) === 0) json_out(400, ['error' => 'The password cannot be your username.']);
        q('UPDATE users SET password_hash = ? WHERE id = ?', [password_hash($pass, PASSWORD_DEFAULT), $u['id']]);
        q('DELETE FROM sessions WHERE user_id = ?', [$u['id']]);   // sign out everywhere
        q('DELETE FROM attempts WHERE k = ?', ['recu:' . $name]);
        $newCode = $viaInvite ? null : set_recovery_code($u['id']);   // a used recovery code is replaced
        create_session($u['id']);
        json_out(200, ['ok' => true, 'recovery_code' => $newCode]);
    }

    $me = current_user();
    // share links: create, list and revoke (the trader's own)
    if (strpos($route, 'api/share/') === 0) {
        if (!$me) json_out(401, ['error' => 'Sign in first.']);
        require_once __DIR__ . '/growth/share-links.php';
        $rawIn = (string) file_get_contents('php://input');
        if ($method === 'POST' && $rawIn === '' && (int) ($_SERVER['CONTENT_LENGTH'] ?? 0) > 0) json_out(413, ['error' => 'too_large']);   // over PHP's post_max_size
        $b = json_decode($rawIn, true) ?: [];
        if ($route === 'api/share/create' && $method === 'POST') { $r = sl_create(db(), $me, $b); if (isset($r['error'])) json_out($r['error'] === 'slow_down' ? 429 : 400, $r); json_out(200, $r + ['url' => '/s/' . $r['id']]); }
        if ($route === 'api/share/list' && $method === 'GET') json_out(200, ['links' => sl_list(db(), $me)]);
        if ($route === 'api/share/delete' && $method === 'POST') json_out(200, ['ok' => sl_delete(db(), $me, (string) ($b['id'] ?? ''))]);
        json_out(404, ['error' => 'not found']);
    }
    // prop firm presets (firm → account type → size → rules), kept up to date by presets/cron.php
    if ($route === 'api/presets') {
        require_once __DIR__ . '/presets/presets-lib.php';
        header('Content-Type: application/json; charset=utf-8'); header('Cache-Control: private, max-age=3600');
        $c = pr_current();
        echo json_encode(['version' => $c['version'] ?? '', 'checked_at' => $c['checked_at'] ?? null, 'origin' => strpos((string) ($c['origin'] ?? ''), 'seed') === 0 ? 'seed' : 'checked', 'firms' => array_values(array_filter($c['firms'], fn($f) => !empty($f['programs'])))], JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
        exit;
    }
    // current version of the app (checked by open tabs to update themselves after a deploy)
    if ($route === 'api/version') {
        header('Content-Type: application/json; charset=utf-8'); header('Cache-Control: no-store');
        $f = __DIR__ . '/app.html';
        echo json_encode(['build' => substr(md5((string) file_get_contents($f)), 0, 12), 'at' => gmdate('c', (int) filemtime($f))]);
        exit;
    }
    if ($route === 'app' || $route === '' || $route === 'index.html') {
        header('Content-Type: text/html; charset=utf-8');
        header('Cache-Control: no-store');
        header("Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: blob:; connect-src 'self'; frame-src https://s.tradingview.com https://www.tradingview-widget.com; frame-ancestors 'none'; base-uri 'self'; form-action 'self'");
        header('X-Content-Type-Options: nosniff');
        header('Referrer-Policy: strict-origin-when-cross-origin');
        header('Permissions-Policy: camera=(), microphone=(), geolocation=()');
        // the page carries its version: the app compares it with the server's and updates itself when a new one is deployed
        $file = __DIR__ . ($me ? '/app.html' : '/auth.html');
        $html = (string) file_get_contents($file);
        $build = substr(md5($html), 0, 12);
        echo str_replace('</head>', '<meta name="sweep-build" content="' . $build . '" data-at="' . gmdate('c', (int) filemtime($file)) . '">' . "\n</head>", $html);
        exit;
    }
    if (!$me) {
        if (strpos($route, 'api/') === 0) json_out(401, ['error' => 'Signed out.']);
        http_response_code(401); exit;
    }
    $UID = $me['id'];

    // Referrals and feedback (growth/)
    if ($route === 'api/referral' && $method === 'GET') {
        $base = $APP_URL !== '/' ? $APP_URL : ((isset($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off' ? 'https://' : 'http://') . ($_SERVER['HTTP_HOST'] ?? 'localhost') . '/');
        json_out(200, ref_dashboard(db(), (string)$UID, $base));
    }
    if ($route === 'api/feedback' && $method === 'GET') json_out(200, ['items' => fb_list_mine(db(), (string)$UID)]);
    if ($route === 'api/feedback' && $method === 'POST') {
        $plan = null; if (billing_on()) { try { $plan = sb_plan(db(), (string)$UID); } catch (Throwable $e) {} }
        $r = fb_create(db(), (string)$UID, body_json(8 * 1048576), $plan);
        json_out(isset($r['error']) ? ($r['error'] === 'limit' ? 429 : 400) : 201, $r);
    }
    if (preg_match('#^api/feedback/shot/(\d+)$#', $route, $fm) && $method === 'GET') fb_serve_shot(db(), (int)$fm[1], (string)$UID, !empty($me['is_admin']));

    // Real charts (chart/): bars for your own trades or an 8-hour window, never newer than the licence delay
    if (strpos($route, 'api/chart/') === 0 && function_exists('chart_route')) chart_route($route, $method, (string)$UID);

    // Complete export in one tap (ZIP: backup JSON + CSV + screenshots)
    if ($route === 'api/export/full' && $method === 'GET') {
        throttle(['exp:' . $UID], 6, 3600); record_attempt(['exp:' . $UID]);
        require_once __DIR__ . '/export/export.php';
        export_full(db(), (string)$UID, $DATA);
    }

    // Gamification (game/)
    if (strpos($route, 'api/game/') === 0 && function_exists('game_route')) game_route($route, $method, (string)$UID);

    // Notification center (notify/)
    if (strpos($route, 'api/notifications') === 0 && function_exists('nt_route')) nt_route($route, $method, (string)$UID, !empty($me['is_admin']));

    // Billing (plans, Stripe checkout and portal, account chooser)
    if (strpos($route, 'api/billing/') === 0) {
        if (!billing_on()) json_out(200, ['live' => false, 'off' => true]);
        require_once __DIR__ . '/billing/billing-routes.php';
        sweep_billing_route($route, $method, (string)$UID, db(), [
            'created_at' => $me['created_at'] ?? null, 'email' => $me['email'] ?? null, 'is_admin' => !empty($me['is_admin']),
            'account_ids' => fn() => billing_account_ids((string)$UID),
        ]);
    }

    // Sweep AI module (ai/): only runs when the trader taps an AI action
    if (strpos($route, 'api/ai/') === 0) {
        if (!empty($cfg['ai_config']) && !defined('SWEEP_AI_CONFIG')) define('SWEEP_AI_CONFIG', (string)$cfg['ai_config']);
        if ($route === 'api/ai/chat' && $method === 'POST') {   // Ask Sweep (chat bubble)
            require_once __DIR__ . '/ai/chat.php';
            try { $b = body_json(65536); json_out(200, sweep_chat(db(), (string)$UID, $b, sai_lang($b['lang'] ?? 'en'))); }
            catch (SaiError $x) { json_out($x->http, $x->extra + ['error' => 'AI error', 'code' => $x->sai, 'usage' => isset($UID) ? sai_usage(db(), (string)$UID) : null]); }
        }
        require_once __DIR__ . '/ai/ai-routes.php';
        sweep_ai_route($route, $method, (string)$UID, db());
    }

    // admin: sign-ups started (email + password) but not finished, for the marketing follow-up; ?format=csv to download
    if ($route === 'api/admin/leads' && $method === 'GET') {
        if (empty($me['is_admin'])) json_out(403, ['error' => 'Admins only.']);
        lead_table(db());
        $rows = q('SELECT email_lc AS email, lang, ref, utm, created_at, updated_at, attempts FROM signup_leads WHERE completed_at IS NULL ORDER BY created_at DESC LIMIT 5000')->fetchAll();
        if (($_GET['format'] ?? '') === 'csv') {
            header('Content-Type: text/csv; charset=utf-8'); header('Content-Disposition: attachment; filename="sweep-unfinished-signups.csv"');
            $o = fopen('php://output', 'w'); fputcsv($o, ['email', 'lang', 'ref', 'utm', 'started_utc', 'last_try_utc', 'tries']);
            foreach ($rows as $r) fputcsv($o, [$r['email'], $r['lang'], $r['ref'], $r['utm'], gmdate('Y-m-d H:i', (int) $r['created_at']), gmdate('Y-m-d H:i', (int) $r['updated_at']), $r['attempts']]);
            exit;
        }
        $done = (int) q('SELECT COUNT(*) FROM signup_leads WHERE completed_at IS NOT NULL')->fetchColumn();
        json_out(200, ['unfinished' => $rows, 'finished' => $done]);
    }
    if ($route === 'api/me/profile' && $method === 'POST') {
        $b = body_json(4096);
        $clean = fn($v, $n) => mb_substr(trim(preg_replace('/\s+/u', ' ', strip_tags((string)$v)) ?? ''), 0, $n);
        $fn = $clean($b['first_name'] ?? '', 40); $ln = $clean($b['last_name'] ?? '', 40);
        if ($fn === '' || $ln === '') json_out(400, ['error' => 'Enter your first and last name.']);
        $set = ['first_name = ?' => $fn, 'last_name = ?' => $ln, 'full_name = ?' => trim($fn . ' ' . $ln)];
        if (isset($b['username']) && trim((string)$b['username']) !== '' && strcasecmp(trim((string)$b['username']), (string)$me['username']) !== 0) {
            $un = trim((string)$b['username']);
            if (!preg_match(USERNAME_RE, $un)) json_out(400, ['error' => 'Username: 3–32 characters, letters, digits, _ . - only.']);
            if (q('SELECT 1 FROM users WHERE username_lc = ? AND id <> ?', [strtolower($un), $UID])->fetch()) json_out(409, ['error' => 'This username is taken.']);
            $set['username = ?'] = $un; $set['username_lc = ?'] = strtolower($un);
        }
        foreach (['found_via' => 40, 'found_video' => 120, 'accounts_info' => 160] as $k => $n) if (isset($b[$k])) $set[$k . ' = ?'] = $clean($b[$k], $n);
        if (isset($b['experience'])) $set['experience = ?'] = in_array($b['experience'], ['new', 'lt1', 'gt1'], true) ? $b['experience'] : null;   // « How long have you been trading? » (onboarding)
        q('UPDATE users SET ' . implode(', ', array_keys($set)) . ' WHERE id = ?', array_merge(array_values($set), [$UID]));
        json_out(200, ['ok' => true, 'first_name' => $fn, 'last_name' => $ln, 'full_name' => trim($fn . ' ' . $ln), 'username' => $set['username = ?'] ?? $me['username'], 'experience' => array_key_exists('experience = ?', $set) ? $set['experience = ?'] : ($me['experience'] ?? null)]);
    }
    if ($route === 'api/me/name' && $method === 'POST') {
        $b = body_json(1024);
        $fn = trim(preg_replace('/\s+/u', ' ', strip_tags((string)($b['full_name'] ?? ''))) ?? '');
        q('UPDATE users SET full_name = ? WHERE id = ?', [$fn === '' ? null : mb_substr($fn, 0, 80), $UID]);
        json_out(200, ['ok' => true, 'full_name' => $fn]);
    }
    if ($route === 'api/me/email' && $method === 'POST') {
        $b = body_json(2048);
        $email = strtolower(trim((string)($b['email'] ?? '')));
        throttle(['em:' . $UID], 10, 3600); record_attempt(['em:' . $UID]);
        $h = q('SELECT password_hash FROM users WHERE id = ?', [$UID])->fetchColumn();
        if (!password_verify((string)($b['password'] ?? ''), (string)$h)) json_out(403, ['error' => 'Your current password is incorrect.']);
        if (!filter_var($email, FILTER_VALIDATE_EMAIL) || strlen($email) > 190) json_out(400, ['error' => 'Enter a valid email.']);
        if (q('SELECT 1 FROM users WHERE email_lc = ? AND id <> ?', [$email, $UID])->fetch()) json_out(409, ['error' => 'An account already uses this email.']);
        q('UPDATE users SET email = ?, email_lc = ? WHERE id = ?', [$email, $email, $UID]);
        json_out(200, ['ok' => true, 'email' => $email]);
    }
    if ($route === 'api/health') json_out(200, ['ok' => true, 'php' => PHP_VERSION, 'drivers' => PDO::getAvailableDrivers()]);

    if ($route === 'api/data' && $method === 'GET') {
        sweep_session_dates($UID);   // one rule: a trade's date is its session (older evening trades move once, then marked)
        sweep_money_types($UID);     // every account gets its money type once (eval, funded, live, personal)
        sweep_recurring_expenses($UID);   // monthly subscriptions: this month's expense, until the linked account ends
        $out = ['user' => $me, 'reset_method' => $ACCESS['reset'], 'support' => $SUPPORT];
        foreach (COLLECTIONS as $c) $out[$c] = [];
        foreach (q('SELECT collection, id, data FROM documents WHERE user_id = ?', [$UID]) as $row) {
            if (!isset($out[$row['collection']])) continue;
            // decoded as objects: an empty {} (emotions, checklist answers…) must reach the app as {}, not [] —
            // an array there makes every later emotion / score / answer on that trade silently lost
            $d = json_decode($row['data']);
            if (!($d instanceof stdClass)) continue;
            $d->id = $row['id'];
            if ($row['collection'] === 'trades') foreach (['review', 'discipline', 'emo'] as $k) if (isset($d->$k) && is_array($d->$k) && !$d->$k) $d->$k = new stdClass();
            $out[$row['collection']][] = $d;
        }
        $out['settings'] = null;
        foreach ($out['meta'] as $m) if (($m->id ?? '') === 'settings') $out['settings'] = $m;
        unset($out['meta']);
        json_out(200, $out);
    }

    /* several trades at once (a screenshot with several trades): all or nothing, in ONE transaction. Each trade carries the
       import_batch_id; « Undo » removes the whole batch the same way (del). The game, missions and notifications run once
       per trading day touched (on its last trade), so a batch of 8 gives one celebration, not 8. */
    if ($route === 'api/docs/batch' && $method === 'POST') {
        $b = body_json(4 * 1048576);
        $col = (string) ($b['col'] ?? 'trades');
        if (!in_array($col, COLLECTIONS, true)) json_out(400, ['error' => 'invalid collection']);
        $puts = array_values(array_filter((array) ($b['put'] ?? []), 'is_array')); $dels = array_values(array_filter((array) ($b['del'] ?? []), 'is_string'));
        if (count($puts) + count($dels) === 0 || count($puts) + count($dels) > 300) json_out(400, ['error' => 'empty or too large batch']);
        foreach ($puts as $d) if (!preg_match(ID_RE, (string) ($d['id'] ?? ''))) json_out(400, ['error' => 'invalid id']);
        foreach ($dels as $id) if (!preg_match(ID_RE, $id)) json_out(400, ['error' => 'invalid id']);
        if (billing_on() && $col === 'trades') foreach ($puts as $d) if (empty($d['demo']) && !empty($d['account_id'])) {
            $deny = sb_guard(db(), (string) $UID, 'write_trade', ['account_id' => (string) $d['account_id'], 'account_ids' => billing_account_ids((string) $UID)]);
            if ($deny) json_out(402, $deny);
        }
        if ((int) q('SELECT COUNT(*) FROM documents WHERE user_id = ?', [$UID])->fetchColumn() + count($puts) > $MAX_DOCS) json_out(507, ['error' => 'Record limit reached.']);
        $events = [];
        $pdo = db(); $pdo->beginTransaction();
        try {
            foreach ($puts as $d) {
                $d['user_id'] = $UID; $id = (string) $d['id'];
                $json = json_encode($d, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
                $prev = q('SELECT data FROM documents WHERE user_id = ? AND collection = ? AND id = ?', [$UID, $col, $id])->fetchColumn();
                if ($prev !== false) q('UPDATE documents SET data = ?, updated_at = ? WHERE user_id = ? AND collection = ? AND id = ?', [$json, now(), $UID, $col, $id]);
                else q('INSERT INTO documents (user_id, collection, id, data, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)', [$UID, $col, $id, $json, now(), now()]);
                $events[] = [$id, $d, $prev !== false ? (json_decode((string) $prev, true) ?: []) : null];
            }
            foreach ($dels as $id) {
                $prev = q('SELECT data FROM documents WHERE user_id = ? AND collection = ? AND id = ?', [$UID, $col, $id])->fetchColumn();
                if ($prev === false) continue;
                q('DELETE FROM documents WHERE user_id = ? AND collection = ? AND id = ?', [$UID, $col, $id]);
                $events[] = [$id, null, json_decode((string) $prev, true) ?: []];
            }
            $pdo->commit();
        } catch (Throwable $e) { $pdo->rollBack(); error_log('[Sweep batch] ' . $e->getMessage()); json_out(500, ['error' => 'The batch was not saved.']); }
        // events: one per trading day touched (the game recomputes the whole day from the documents)
        if (function_exists('nt_doc_event')) {
            $byDay = [];
            foreach ($events as $ev) { $t = $ev[1] ?? $ev[2] ?? []; $day = (string) ($t['date'] ?? '') . '|' . (string) ($t['account_id'] ?? ''); $byDay[$day] = $ev; }
            foreach ($byDay as $ev) { try { nt_doc_event((string) $UID, $col, $ev[0], $ev[1], $ev[2]); } catch (Throwable $e) { error_log('[Sweep batch] event: ' . $e->getMessage()); } }
        }
        if ($col === 'trades' && $puts) { try { ref_check_user(db(), (string) $UID); } catch (Throwable $e) { /* referral check next time */ } }
        json_out(200, ['ok' => true, 'put' => count($puts), 'del' => count($dels)]);
    }
    if (preg_match('#^api/docs/([a-z]+)/([^/]+)$#', $route, $m)) {
        [, $col, $id] = $m;
        if (!in_array($col, COLLECTIONS, true) || !preg_match(ID_RE, $id)) json_out(400, ['error' => 'invalid path']);
        if ($method === 'PUT') {
            $doc = body_json();
            $doc['id'] = $id;
            $doc['user_id'] = $UID;
            if (billing_on() && empty($doc['demo'])) {   // the plan decides; sample data and deletes are never blocked
                $deny = null;
                if (in_array($col, ['payouts', 'expenses'], true)) $deny = sb_guard(db(), (string)$UID, 'write_payouts');
                elseif ($col === 'accounts') {
                    $isNew = !q("SELECT 1 FROM documents WHERE user_id = ? AND collection = 'accounts' AND id = ?", [$UID, $id])->fetchColumn();
                    if ($isNew) $deny = sb_guard(db(), (string)$UID, 'create_account', ['account_ids' => billing_account_ids((string)$UID)]);
                } elseif ($col === 'trades' && !empty($doc['account_id'])) {
                    $deny = sb_guard(db(), (string)$UID, 'write_trade', ['account_id' => (string)$doc['account_id'], 'account_ids' => billing_account_ids((string)$UID)]);
                }
                if ($deny) json_out(402, $deny);
            }
            $obj = json_decode((string) file_get_contents('php://input'));
            if ($obj instanceof stdClass) { $obj->id = $id; $obj->user_id = $UID; $json = json_encode($obj, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES); }
            else $json = json_encode($doc, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
            $prevRaw = q('SELECT data FROM documents WHERE user_id = ? AND collection = ? AND id = ?', [$UID, $col, $id])->fetchColumn();   // for events
            $up = q('UPDATE documents SET data = ?, updated_at = ? WHERE user_id = ? AND collection = ? AND id = ?', [$json, now(), $UID, $col, $id]);
            if ($up->rowCount() === 0) {
                if ((int)q('SELECT COUNT(*) FROM documents WHERE user_id = ?', [$UID])->fetchColumn() >= $MAX_DOCS) json_out(507, ['error' => 'Record limit reached.']);
                q('INSERT INTO documents (user_id, collection, id, data, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)', [$UID, $col, $id, $json, now(), now()]);
                if ($col === 'trades' && empty($doc['demo'])) { try { ref_check_user(db(), (string)$UID); } catch (Throwable $e) { error_log('[Sweep referral] check: ' . $e->getMessage()); } }
            }
            if (function_exists('nt_doc_event')) { try { nt_doc_event((string)$UID, $col, $id, $doc, $prevRaw !== false ? (json_decode((string)$prevRaw, true) ?: []) : null); } catch (Throwable $e) { error_log('[Sweep events] ' . $e->getMessage()); } }
            json_out(200, ['ok' => true]);
        }
        if ($method === 'DELETE') {
            $prevRaw = q('SELECT data FROM documents WHERE user_id = ? AND collection = ? AND id = ?', [$UID, $col, $id])->fetchColumn();
            q('DELETE FROM documents WHERE user_id = ? AND collection = ? AND id = ?', [$UID, $col, $id]);
            if ($prevRaw !== false && function_exists('nt_doc_event')) { try { nt_doc_event((string)$UID, $col, $id, null, json_decode((string)$prevRaw, true) ?: []); } catch (Throwable $e) { error_log('[Sweep events] ' . $e->getMessage()); } }
            json_out(200, ['ok' => true]);
        }
        json_out(405, ['error' => 'method not allowed']);
    }

    // browser errors (message, page, app version, device), so problems on traders' phones are seen
    // searches that found nothing (text + language): the admin dashboard lists the top 20
    if ($route === 'api/search-miss' && $method === 'POST') {
        throttle(['sm:' . $UID], 60, 3600); record_attempt(['sm:' . $UID]);
        $b = body_json(1024);
        $q = trim((function_exists('mb_strtolower') ? 'mb_strtolower' : 'strtolower')(substr((string)($b['q'] ?? ''), 0, 80)));
        if ($q !== '') product_event((string)$UID, 'search_no_result', ['q' => $q, 'lang' => lang_code((string)($b['lang'] ?? 'en'))]);
        json_out(200, ['ok' => true]);
    }

    if ($route === 'api/client-error' && $method === 'POST') {
        throttle(['ce:' . $UID], 30, 3600); record_attempt(['ce:' . $UID]);
        $b = body_json(4096);
        db()->exec("CREATE TABLE IF NOT EXISTS client_errors (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, msg TEXT, src TEXT, line INT, page TEXT, ua TEXT, ver TEXT, created_at INT NOT NULL)");
        q('INSERT INTO client_errors (user_id, msg, src, line, page, ua, ver, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', [(string)$UID, substr((string)($b['msg'] ?? ''), 0, 500), substr((string)($b['src'] ?? ''), 0, 200),
            (int)($b['line'] ?? 0), substr((string)($b['page'] ?? ''), 0, 80), substr((string)($_SERVER['HTTP_USER_AGENT'] ?? ''), 0, 200), substr((string)($b['ver'] ?? ''), 0, 40), time()]);
        json_out(200, ['ok' => true]);
    }

    if ($route === 'api/uploads' && $method === 'POST') {
        $len = (int)($_SERVER['CONTENT_LENGTH'] ?? 0);
        $raw = file_get_contents('php://input');
        if ($raw === false || $raw === '') json_out($len > 0 ? 413 : 415, ['error' => $len > 0 ? 'image larger than the PHP upload limit' : 'empty upload']);
        if (strlen($raw) > 20 * 1048576) json_out(413, ['error' => 'image larger than 20 MB']);
        $info = @getimagesizefromstring($raw);
        $type = $info['mime'] ?? '';
        if (!in_array($type, IMAGE_TYPES, true)) json_out(415, ['error' => 'PNG, JPEG, GIF or WebP only']);
        $used = (int)q('SELECT COALESCE(SUM(size), 0) FROM uploads WHERE user_id = ?', [$UID])->fetchColumn();
        if ($used + strlen($raw) > $UPLOAD_QUOTA) json_out(507, ['error' => 'Screenshot storage is full for this account.']);
        $id = uuid();
        if (file_put_contents($DATA . '/uploads/' . $id, $raw) === false) json_out(500, ['error' => 'could not store the image']);
        q('INSERT INTO uploads (id, user_id, content_type, size, created_at) VALUES (?, ?, ?, ?, ?)', [$id, $UID, $type, strlen($raw), now()]);
        json_out(201, ['id' => $id, 'url' => 'uploads/' . $id]);
    }

    if (preg_match('#^(api/)?uploads/([A-Za-z0-9-]{1,64})$#', $route, $m)) {
        $id = $m[2];
        $row = q('SELECT * FROM uploads WHERE id = ? AND user_id = ?', [$id, $UID])->fetch();
        if ($m[1] === '' && $method === 'GET') {
            if (!$row || !is_file($DATA . '/uploads/' . $id)) { http_response_code(404); exit; }
            header('Content-Type: ' . $row['content_type']);
            header('Content-Length: ' . filesize($DATA . '/uploads/' . $id));
            header('Cache-Control: private, max-age=31536000, immutable');
            readfile($DATA . '/uploads/' . $id);
            exit;
        }
        if ($m[1] === 'api/' && $method === 'DELETE') {
            if ($row) { q('DELETE FROM uploads WHERE id = ? AND user_id = ?', [$id, $UID]); @unlink($DATA . '/uploads/' . $id); }
            json_out(200, ['ok' => true]);
        }
    }

    /* ---------- market context ---------- */
    if ($route === 'api/econ' && $method === 'GET') {
        $from = (string)($_GET['from'] ?? ''); $to = (string)($_GET['to'] ?? '');
        if (!preg_match('/^\d{4}-\d{2}-\d{2}$/', $from) || !preg_match('/^\d{4}-\d{2}-\d{2}$/', $to) || $to < $from) json_out(400, ['error' => 'from/to must be YYYY-MM-DD']);
        if ((strtotime($to) - strtotime($from)) / 86400 > 92) json_out(400, ['error' => 'Range too large (max 92 days).']);
        try { econ_seed(); econ_sync($from, $to); } catch (Throwable $e) { error_log('Trading Journal econ sync: ' . $e->getMessage()); }
        $tz = new DateTimeZone('America/New_York');
        $t0 = (new DateTime($from . ' 00:00:00', $tz))->getTimestamp(); $t1 = (new DateTime($to . ' 23:59:59', $tz))->getTimestamp();
        econ_schema();
        $rows = q("SELECT id, ts, event, impact, actual, forecast, previous, revised, source, status FROM econ_events WHERE country = 'US' AND impact IN ('high','medium') AND ts BETWEEN ? AND ? ORDER BY ts", [$t0, $t1])->fetchAll();
        foreach ($rows as &$r) $r['ts'] = (int)$r['ts'];
        json_out(200, ['events' => $rows, 'provider' => $ECON_KEY !== '' && in_array($ECON_PROVIDER, ['tradingeconomics', 'fmp', 'finnhub'], true) ? $ECON_PROVIDER : 'manual']);
    }
    if (preg_match('#^api/econ/event/([a-f0-9]{40})$#', $route, $m) && $method === 'GET') {
        $d = econ_detail($m[1]); if (!$d) json_out(404, ['error' => 'Event not found.']);
        json_out(200, $d);
    }
    // Sweep AI fills the economic calendar and writes market impact reports (ai/econ-ai.php)
    if (($route === 'api/econ/ai-refresh' || preg_match('#^api/econ/event/([a-f0-9]{40})/report$#', $route, $em)) && $method === 'POST') {
        if (!is_file(__DIR__ . '/ai/econ-ai.php')) json_out(200, ['enabled' => false]);
        if (!empty($cfg['ai_config']) && !defined('SWEEP_AI_CONFIG')) define('SWEEP_AI_CONFIG', (string)$cfg['ai_config']);
        require_once __DIR__ . '/ai/econ-ai.php';
        econ_schema();
        try {
            if (!eai_enabled()) { static $w = false; if (!$w && (int) gmdate('i') % 30 === 0) { $w = true; error_log('[Sweep AI] econ: AI is disabled (ai-config), the calendar cannot fill released values or write impact reports'); } json_out(200, ['enabled' => false]); }
            if ($route === 'api/econ/ai-refresh') json_out(200, ['enabled' => true, 'updated' => eai_fill(db())]);
            $b = body_json(2048);
            $rep = eai_report(db(), $em[1], (string)($b['lang'] ?? 'en'));
            // plans without full calendar notes see the headline and the first sentence (the report is still written once, for everyone)
            if (($rep['state'] ?? '') === 'ready' && billing_on() && sb_limit(db(), (string)$UID, 'calendar_notes') !== 'full') {
                $r = $rep['report']; $first = preg_split('/(?<=[.!?])\s+/u', (string)($r['summary'] ?? ''))[0] ?? '';
                $rep['report'] = ['headline' => $r['headline'] ?? null, 'verdict' => $r['verdict'] ?? 'mixed', 'summary' => $first, 'stage' => $r['stage'] ?? null, 'confidence' => $r['confidence'] ?? 'medium', 'reaction' => [], 'drivers' => []];
                $rep['locked'] = true; $rep['sources'] = [];
            }
            json_out(200, $rep);
        } catch (SaiError $x) {
            json_out($x->http, ['error' => 'AI error', 'code' => $x->sai]);
        }
    }
    if ($route === 'api/market/candles' && $method === 'GET') {
        $from = (int)($_GET['from'] ?? 0); $to = (int)($_GET['to'] ?? 0);
        if ($from <= 0 || $to <= $from || $to - $from > 3 * 86400) json_out(400, ['error' => 'Invalid range (max 3 days).']);
        $active = $MARKET_PROVIDER === 'databento' && $MARKET_KEY !== '';
        // instrument root → continuous front contract (NQ keeps the configured symbol)
        $root = strtoupper((string)($_GET['symbol'] ?? 'NQ'));
        $full = ['MNQ' => 'NQ', 'MES' => 'ES', 'MYM' => 'YM', 'M2K' => 'RTY', 'MCL' => 'CL', 'MGC' => 'GC'][$root] ?? $root;   // micros trade at the same price
        $sym = $full === 'NQ' ? $MARKET_SYMBOL : (in_array($full, ['ES', 'YM', 'RTY', 'CL', 'GC'], true) ? $full . '.v.0' : $MARKET_SYMBOL);
        if ($active) { try { candles_sync($from, $to, $sym); } catch (Throwable $e) { error_log('Trading Journal candles: ' . $e->getMessage()); } }
        $rows = $active ? q('SELECT t, o, h, l, c, v FROM candles WHERE symbol = ? AND t BETWEEN ? AND ? ORDER BY t', [$sym, $from, $to])->fetchAll(PDO::FETCH_NUM) : [];
        $rows = array_map(fn($r) => [(int)$r[0], (float)$r[1], (float)$r[2], (float)$r[3], (float)$r[4], (int)$r[5]], $rows);
        $hz = class_exists('ChartData', false) ? ChartData::horizon() : time() - 86400;
        $rows = array_values(array_filter($rows, fn($r) => $r[0] + 60 <= $hz));   // never newer than the licence delay
        json_out(200, ['candles' => $rows, 'provider' => $active ? 'databento' : 'none']);
    }

    /* ---------- own account ---------- */
    if ($route === 'api/account/password' && $method === 'POST') {
        $b = body_json(4096);
        $cur = q('SELECT password_hash FROM users WHERE id = ?', [$UID])->fetchColumn();
        throttle(['pw:' . $UID], 10, 900);
        if (!password_verify((string)($b['current'] ?? ''), (string)$cur)) { record_attempt(['pw:' . $UID]); json_out(403, ['error' => 'Your current password is incorrect.']); }
        $new = (string)($b['new'] ?? '');
        if (strlen($new) < 10 || strlen($new) > 200) json_out(400, ['error' => 'New password: at least 10 characters.']);
        q('UPDATE users SET password_hash = ? WHERE id = ?', [password_hash($new, PASSWORD_DEFAULT), $UID]);
        q('DELETE FROM sessions WHERE user_id = ?', [$UID]);   // sign out every other device
        create_session($UID);
        json_out(200, ['ok' => true]);
    }
    if ($route === 'api/account/recovery' && $method === 'POST') {
        $b = body_json(4096);
        $cur = q('SELECT password_hash FROM users WHERE id = ?', [$UID])->fetchColumn();
        throttle(['pw:' . $UID], 10, 900);
        if (!password_verify((string)($b['password'] ?? ''), (string)$cur)) { record_attempt(['pw:' . $UID]); json_out(403, ['error' => 'Your current password is incorrect.']); }
        json_out(200, ['recovery_code' => set_recovery_code($UID)]);
    }
    if ($route === 'api/account' && $method === 'DELETE') {
        $b = body_json(4096);
        $cur = q('SELECT password_hash FROM users WHERE id = ?', [$UID])->fetchColumn();
        if (!password_verify((string)($b['password'] ?? ''), (string)$cur)) json_out(403, ['error' => 'Incorrect password.']);
        if ($me['is_admin'] && (int)q('SELECT COUNT(*) FROM users WHERE is_admin = 1 AND disabled = 0')->fetchColumn() <= 1) {
            json_out(409, ['error' => 'You are the only administrator. The administrator account cannot be deleted.']);
        }
        delete_user_everything($UID);
        set_session_cookie('', time() - 3600);
        json_out(200, ['ok' => true]);
    }

    /* ---------- administration ---------- */
    if (strpos($route, 'api/admin/') === 0) {
        if (!$me['is_admin']) json_out(403, ['error' => 'Administrators only.']);
        // campaign attribution report: per post, sign-ups, activated, 3+ trading days, still logging on day 7 and day 14
        if ($route === 'api/admin/attribution' && $method === 'GET') {
            $since = preg_match('/^\d{4}-\d{2}-\d{2}$/', (string)($_GET['since'] ?? '')) ? $_GET['since'] : '2026-10-05';
            $groups = [];
            foreach (q('SELECT id, created_at, utm_source, utm_content, found_via FROM users WHERE created_at >= ? AND COALESCE(is_internal, 0) = 0 AND is_admin = 0', [$since])->fetchAll() as $u) {
                $post = $u['utm_content'] ?: 'no-tag:' . ($u['found_via'] ?: 'unknown'); $src = $u['utm_source'] ?: '-';
                $k = $post . '|' . $src;
                $g = &$groups[$k]; if (!$g) $g = ['post_id' => $post, 'source' => $src, 'signups' => 0, 'activated' => 0, 'three_days' => 0, 'd7' => 0, 'd14' => 0];
                $g['signups']++;
                $acc = false; $dates = [];
                foreach (q("SELECT collection, data FROM documents WHERE user_id = ? AND collection IN ('accounts','trades')", [$u['id']]) as $r) {
                    $d = json_decode((string)$r['data'], true) ?: []; if (!empty($d['demo'])) continue;
                    if ($r['collection'] === 'accounts') $acc = true; elseif (!empty($d['date'])) $dates[(string)$d['date']] = 1;
                }
                if ($acc && $dates) $g['activated']++;
                if (count($dates) >= 3) $g['three_days']++;
                $s0 = strtotime(substr((string)$u['created_at'], 0, 10));
                $in = function (int $a, int $b) use ($dates, $s0) { foreach (array_keys($dates) as $dd) { $x = (int)floor((strtotime($dd) - $s0) / 86400); if ($x >= $a && $x < $b) return true; } return false; };
                if ($in(7, 14)) $g['d7']++;
                if ($in(14, 21)) $g['d14']++;
                unset($g);
            }
            $rows = array_values($groups);
            usort($rows, fn($a, $b) => [$b['activated'], $b['signups']] <=> [$a['activated'], $a['signups']]);
            json_out(200, ['since' => $since, 'rows' => $rows]);
        }
        if (preg_match('#^api/admin/users/([A-Za-z0-9_.-]{1,120})/internal$#', $route, $m) && $method === 'POST') {
            q('UPDATE users SET is_internal = ? WHERE id = ?', [!empty(body_json(1024)['internal']) ? 1 : 0, $m[1]]);
            @unlink($DATA . '/cohort-count.json');
            json_out(200, ['ok' => true]);
        }
        // prop firm presets: last check, status per firm, « Check now » (one firm per request, then « finish »)
        if (strpos($route, 'api/admin/presets') === 0) {
            require_once __DIR__ . '/presets/check.php';
            if ($route === 'api/admin/presets' && $method === 'GET') json_out(200, pr_admin_summary());
            if ($route === 'api/admin/presets/check' && $method === 'POST') {
                $b = body_json(2048); @set_time_limit(240); @ignore_user_abort(true);
                if (!empty($b['finish'])) { pr_finish_run('admin'); json_out(200, pr_admin_summary()); }
                $fid = (string)($b['firm'] ?? ''); $firm = null;
                foreach (pr_current()['firms'] as $f) if ($f['id'] === $fid) $firm = $f;
                if (!$firm) json_out(404, ['error' => 'Unknown firm.']);
                [$st, $new] = pr_check_firm(db(), $firm);
                json_out(200, ['firm' => $fid, 'result' => pr_apply(db(), $fid, $st, $new)]);
            }
            json_out(404, ['error' => 'not found']);
        }
        if ($route === 'api/admin/metrics' && $method === 'GET') { require_once __DIR__ . '/ops/metrics.php'; json_out(200, sweep_metrics(db(), __DIR__)); }
        if ($route === 'api/admin/feedback' && $method === 'GET') json_out(200, fb_admin_list(db(), $_GET['status'] ?? null, $_GET['type'] ?? null));
        if (preg_match('#^api/admin/feedback/(\d+)$#', $route, $fm) && $method === 'POST') {
            $b = body_json(65536);
            $before = q('SELECT user_id, status FROM feedback WHERE id = ?', [(int)$fm[1]])->fetch();
            $okFb = fb_update(db(), (int)$fm[1], (string)($b['status'] ?? ''), isset($b['reply']) ? (string)$b['reply'] : null);
            if ($okFb && $before && $before['status'] !== (string)($b['status'] ?? '') && function_exists('nt_fire')) {
                nt_fire('feedback.status_changed', ['uid' => (string)$before['user_id'], 'item_id' => (int)$fm[1], 'from' => (string)$before['status'], 'to' => (string)$b['status'], 'reply' => isset($b['reply']) ? (string)$b['reply'] : null, 'admin_id' => (string)$UID]);
            }
            json_out($okFb ? 200 : 400, ['ok' => true]);
        }
        if ($route === 'api/admin/referrals' && $method === 'GET') json_out(200, ['items' => ref_admin_list(db())]);
        if (preg_match('#^api/admin/referrals/(\d+)$#', $route, $fm) && $method === 'POST') {
            $b = body_json(1024); $act = (string)($b['action'] ?? '');
            $r = q('SELECT * FROM referrals WHERE id = ?', [(int)$fm[1]])->fetch();
            if (!$r) json_out(404, ['error' => 'not found']);
            if ($act === 'approve' && $r['status'] === 'review') { q("UPDATE referrals SET status = 'pending' WHERE id = ?", [$r['id']]); ref_give_days(db(), (string)$r['referee_id'], REF_REFEREE_DAYS); ref_check_user(db(), (string)$r['referee_id']); }
            elseif ($act === 'reject' && in_array($r['status'], ['review', 'pending'], true)) q("UPDATE referrals SET status = 'rejected' WHERE id = ?", [$r['id']]);
            else json_out(400, ['error' => 'Nothing to do.']);
            json_out(200, ['ok' => true]);
        }
        if ($route === 'api/admin/ai-usage' && $method === 'GET') {
            try {
                $days = q('SELECT SUBSTR(created_at, 1, 10) AS day, COUNT(*) AS calls, COUNT(DISTINCT user_id) AS users, SUM(input_tokens + output_tokens) AS tokens, ROUND(SUM(cost_usd), 4) AS usd FROM ai_log GROUP BY day ORDER BY day DESC LIMIT 14')->fetchAll();
            } catch (Throwable $e) { $days = []; }
            json_out(200, ['days' => $days]);
        }
        if ($route === 'api/admin/users' && $method === 'GET') {
            $users = q('SELECT id, username, is_admin, disabled, created_at, last_login, recovery_hash, utm_source, utm_medium, utm_campaign, utm_content, found_via, found_video, accounts_info, is_internal FROM users ORDER BY created_at')->fetchAll();
            $trades = []; foreach (q("SELECT user_id, COUNT(*) n FROM documents WHERE collection = 'trades' GROUP BY user_id") as $r) $trades[$r['user_id']] = (int)$r['n'];
            $bytes = [];  foreach (q('SELECT user_id, SUM(size) b FROM uploads GROUP BY user_id') as $r) $bytes[$r['user_id']] = (int)$r['b'];
            foreach ($users as &$u) {
                $u['is_admin'] = (int)$u['is_admin'] === 1; $u['disabled'] = (int)$u['disabled'] === 1;
                $u['trades'] = $trades[$u['id']] ?? 0; $u['upload_bytes'] = $bytes[$u['id']] ?? 0;
                $u['has_recovery'] = !empty($u['recovery_hash']); unset($u['recovery_hash']);
                $u['plan'] = billing_admin_plan((string)$u['id']);
            }
            json_out(200, ['users' => $users, 'registration' => $ACCESS['registration'], 'invite_code' => $ACCESS['invite'], 'reset_method' => $ACCESS['reset'], 'max_users' => $MAX_USERS,
                'providers' => ['econ' => $ECON_KEY !== '' && in_array($ECON_PROVIDER, ['tradingeconomics', 'fmp', 'finnhub'], true) ? $ECON_PROVIDER : 'manual', 'market' => $MARKET_PROVIDER === 'databento' && $MARKET_KEY !== '' ? 'databento' : 'none']]);
        }
        if ($route === 'api/admin/econ' && $method === 'POST') {
            $b = body_json(4096);
            $date = (string)($b['date'] ?? ''); $time = (string)($b['time'] ?? ''); $name = trim((string)($b['event'] ?? ''));
            $impact = (string)($b['impact'] ?? 'high');
            if (!preg_match('/^\d{4}-\d{2}-\d{2}$/', $date) || !preg_match('/^\d{1,2}:\d{2}$/', $time) || $name === '' || !in_array($impact, ['high', 'medium'], true)) json_out(400, ['error' => 'Date, time (HH:MM ET), name and impact are required.']);
            $ts = (new DateTime($date . ' ' . $time . ':00', new DateTimeZone('America/New_York')))->getTimestamp();
            $id = sha1('US|' . $ts . '|' . strtolower($name));
            q('DELETE FROM econ_events WHERE id = ?', [$id]);
            q('INSERT INTO econ_events (id, ts, country, event, impact, actual, forecast, previous, source, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
              [$id, $ts, 'US', substr($name, 0, 200), $impact, trim((string)($b['actual'] ?? '')) ?: null, trim((string)($b['forecast'] ?? '')) ?: null, trim((string)($b['previous'] ?? '')) ?: null, 'manual', time()]);
            q('UPDATE econ_events SET status = ? WHERE id = ?', ['official', $id]);
            json_out(201, ['id' => $id]);
        }
        if ($route === 'api/admin/econ/import' && $method === 'POST') {
            $b = body_json(4 * 1048576);
            json_out(200, ['imported' => econ_import($b)]);
        }
        if (preg_match('#^api/admin/econ/([a-f0-9]{40})$#', $route, $m) && $method === 'DELETE') { q('DELETE FROM econ_events WHERE id = ?', [$m[1]]); json_out(200, ['ok' => true]); }
        if ($route === 'api/admin/settings' && $method === 'POST') {
            $b = body_json(4096);
            $reg = (string)($b['registration'] ?? $ACCESS['registration']);
            $inv = trim((string)($b['invite_code'] ?? $ACCESS['invite']));
            $rst = (string)($b['reset_method'] ?? $ACCESS['reset']);
            if (!in_array($reg, ['open', 'invite', 'closed'], true) || !in_array($rst, ['recovery', 'invite', 'off'], true)) json_out(400, ['error' => 'Invalid setting.']);
            if ($inv !== '' && !preg_match(INVITE_RE, $inv)) json_out(400, ['error' => 'Invite code: 4–64 characters, letters, digits, _ or - only.']);
            if (($reg === 'invite' || $rst === 'invite') && $inv === '') json_out(400, ['error' => 'Set an invite code first.']);
            save_setting('registration', $reg); save_setting('invite_code', $inv); save_setting('reset_method', $rst);
            json_out(200, ['ok' => true]);
        }
        // plan given by the administrator: a trial for N days, permanent access, or removal of what was given
        if (preg_match('#^api/admin/users/([A-Za-z0-9_.-]{1,120})/plan$#', $route, $m) && $method === 'POST') {
            if (!billing_on()) json_out(409, ['error' => 'Billing is not set up.']);
            $tid = $m[1];
            if (!q('SELECT 1 FROM users WHERE id = ?', [$tid])->fetchColumn()) json_out(404, ['error' => 'Trader not found.']);
            $b = body_json(2048);
            $action = (string)($b['action'] ?? ''); $plan = (string)($b['plan'] ?? '');
            $now = time();
            sb_schema(db());
            // whatever the administrator gave before is replaced, so the latest choice is the one that counts
            q("UPDATE billing_grants SET ends_at = ? WHERE uid = ? AND reason IN ('comp','admin_trial') AND ends_at > ?", [$now, $tid, $now]);
            if ($action === 'trial' || $action === 'permanent') {
                if (!in_array($plan, ['pro', 'elite'], true)) json_out(400, ['error' => 'Choose Pro or Elite.']);
                $days = $action === 'permanent' ? 36500 : max(1, min(365, (int)($b['days'] ?? 14)));
                sb_grant(db(), $tid, $plan, $days, $action === 'permanent' ? 'comp' : 'admin_trial');
            } elseif ($action !== 'remove') json_out(400, ['error' => 'Unknown action.']);
            json_out(200, ['ok' => true, 'plan' => billing_admin_plan($tid)]);
        }
        if (preg_match('#^api/admin/users/([A-Za-z0-9_.-]{1,120})/role$#', $route, $m) && $method === 'POST') {
            $tid = $m[1];
            $t = q('SELECT id, is_admin FROM users WHERE id = ?', [$tid])->fetch();
            if (!$t) json_out(404, ['error' => 'Trader not found.']);
            if ($tid === $UID) json_out(409, ['error' => 'You cannot change your own role.']);
            $admin = !empty(body_json(1024)['admin']);
            q('UPDATE users SET is_admin = ? WHERE id = ?', [$admin ? 1 : 0, $tid]);
            json_out(200, ['ok' => true, 'is_admin' => $admin]);
        }
        if (preg_match('#^api/admin/users/([A-Za-z0-9_.-]{1,120})(?:/(reset|disable|enable))?$#', $route, $m)) {
            $tid = $m[1]; $action = $m[2] ?? '';
            $t = q('SELECT id, is_admin FROM users WHERE id = ?', [$tid])->fetch();
            if (!$t) json_out(404, ['error' => 'Trader not found.']);
            if ($tid === $UID) json_out(409, ['error' => 'Use your own Settings to manage your account.']);
            if ((int)$t['is_admin'] === 1) json_out(409, ['error' => 'Other administrators cannot be changed here.']);
            if ($action === 'reset' && $method === 'POST') {
                $pw = temp_password();
                q('UPDATE users SET password_hash = ? WHERE id = ?', [password_hash($pw, PASSWORD_DEFAULT), $tid]);
                q('DELETE FROM sessions WHERE user_id = ?', [$tid]);
                json_out(200, ['password' => $pw]);
            }
            if (($action === 'disable' || $action === 'enable') && $method === 'POST') {
                q('UPDATE users SET disabled = ? WHERE id = ?', [$action === 'disable' ? 1 : 0, $tid]);
                if ($action === 'disable') q('DELETE FROM sessions WHERE user_id = ?', [$tid]);
                json_out(200, ['ok' => true]);
            }
            if ($action === '' && $method === 'DELETE') { delete_user_everything($tid); json_out(200, ['ok' => true]); }
        }
        json_out(404, ['error' => 'not found']);
    }

    json_out(404, ['error' => 'not found']);
} catch (Throwable $e) {
    error_log('Trading Journal: ' . $e->getMessage() . ' @ ' . $e->getFile() . ':' . $e->getLine());
    json_out(500, ['error' => 'Server error — see the error_log file in the journal folder.']);
}
