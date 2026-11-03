<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli' && realpath((string) ($_SERVER['SCRIPT_FILENAME'] ?? '')) === realpath(__FILE__)) { http_response_code(404); exit; }
/**
 * Sweep — automatic sync, server side: the trader's personal key, the executions a platform sends (kept as received in
 * sync_fills), the platform accounts found and their link to Sweep accounts, and the trades written from them
 * (sync-engine.php). Works on the PDO it is given: the app's database, or a throwaway one in tests/sync_store_test.php.
 *  - an account found is « new » until the trader links it to a Sweep account (or ignores it): nothing is written before;
 *  - the trades of a contract are rebuilt from all its executions each time one changes, then compared with what was
 *    written (sync_trades): unchanged → nothing; changed → only the platform's fields (SYNC_TRADE_FIELDS) are rewritten;
 *  - what the trader wrote (notes, review, emotions, checklist, screenshots, tags, setup, grade, stop, target) is never touched;
 *  - a synced trade the trader deleted is never written again (its row stays in sync_trades, its document is gone);
 *  - a trade already typed by hand (same Sweep account, instrument, side and contracts, entry within 2 minutes) is
 *    completed instead of doubled; its notes, screenshots and review stay;
 *  - the same rules as api/docs/batch: the plan's write guard, the record limit, one game event per trading day touched.
 */
require_once __DIR__ . '/sync-engine.php';

const SYNC_PLATFORMS = ['ninjatrader', 'quantower'];
const SYNC_MAX_FILLS = 500;      // executions per push
const SYNC_MAX_ACCOUNTS = 50;    // accounts described per push
const SYNC_MATCH_MIN = 2;        // minutes between a synced entry and a trade typed by hand
// each platform's add-on, downloaded through api/sync/addon?platform=…; a platform shows in Connections once its add-on is here
const SYNC_ADDONS = ['ninjatrader' => __DIR__ . '/addon/SweepSync.zip', 'quantower' => __DIR__ . '/addon/SweepSync-Quantower.zip'];
const SYNC_CLIENTS = ['Sweep NT8' => 'ninjatrader', 'Sweep Quantower' => 'quantower'];   // how each add-on names itself (« client »)
const SYNC_NAMES = ['ninjatrader' => 'NinjaTrader 8', 'quantower' => 'Quantower'];

function sync_q(PDO $pdo, string $sql, array $args = []): PDOStatement { $st = $pdo->prepare($sql); $st->execute($args); return $st; }
function sync_iso(): string { return gmdate('Y-m-d\TH:i:s\Z'); }   // the documents' date format (now() in api.php)
function sync_mysql(PDO $pdo): bool { return $pdo->getAttribute(PDO::ATTR_DRIVER_NAME) === 'mysql'; }

/** the tables, created once per database */
function sync_schema(PDO $pdo): void
{
    static $done = []; $k = spl_object_id($pdo); if (isset($done[$k])) return; $done[$k] = true;
    $sql = sync_mysql($pdo) ? [
        'CREATE TABLE IF NOT EXISTS sync_connections (id VARCHAR(40) NOT NULL PRIMARY KEY, user_id VARCHAR(120) NOT NULL, platform VARCHAR(20) NOT NULL,
           key_hash CHAR(64) NOT NULL UNIQUE, key_hint VARCHAR(8) NOT NULL, status VARCHAR(10) NOT NULL, client VARCHAR(120) NULL, last_seen_at INT NULL,
           last_push_at INT NULL, created_at INT NOT NULL, revoked_at INT NULL, INDEX (user_id)) DEFAULT CHARSET=utf8mb4',
        'CREATE TABLE IF NOT EXISTS sync_accounts (id VARCHAR(40) NOT NULL PRIMARY KEY, user_id VARCHAR(120) NOT NULL, platform VARCHAR(20) NOT NULL,
           ext_id VARCHAR(120) NOT NULL, info TEXT NULL, account_id VARCHAR(120) NULL, state VARCHAR(10) NOT NULL, last_fill_at BIGINT NULL, last_error VARCHAR(40) NULL,
           created_at INT NOT NULL, updated_at INT NOT NULL, UNIQUE KEY sync_acct_ext (user_id, platform, ext_id), UNIQUE KEY sync_acct_link (user_id, account_id)) DEFAULT CHARSET=utf8mb4',
        'CREATE TABLE IF NOT EXISTS sync_fills (id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY, user_id VARCHAR(120) NOT NULL, sync_account_id VARCHAR(40) NOT NULL,
           ext_id VARCHAR(120) NOT NULL, contract VARCHAR(40) NOT NULL, side TINYINT NOT NULL, qty INT NOT NULL, price DOUBLE NOT NULL, ts BIGINT NOT NULL,
           fee DOUBLE NULL, point_value DOUBLE NULL, removed TINYINT NOT NULL DEFAULT 0, received_at INT NOT NULL,
           UNIQUE KEY sync_fill_ext (sync_account_id, ext_id), INDEX sync_fill_c (sync_account_id, contract, ts)) DEFAULT CHARSET=utf8mb4',
        'CREATE TABLE IF NOT EXISTS sync_trades (user_id VARCHAR(120) NOT NULL, trade_id VARCHAR(40) NOT NULL, doc_id VARCHAR(120) NOT NULL, sync_account_id VARCHAR(40) NOT NULL,
           sig CHAR(40) NOT NULL, fills TEXT NOT NULL, entry_at VARCHAR(19) NOT NULL, inst VARCHAR(20) NOT NULL, dir VARCHAR(5) NOT NULL, copy_group VARCHAR(40) NULL,
           created_at INT NOT NULL, updated_at INT NOT NULL, PRIMARY KEY (user_id, trade_id), INDEX sync_tr_doc (user_id, doc_id), INDEX sync_tr_acct (sync_account_id),
           INDEX sync_tr_at (user_id, entry_at)) DEFAULT CHARSET=utf8mb4',
        'CREATE TABLE IF NOT EXISTS sync_copies (user_id VARCHAR(120) NOT NULL, src_doc VARCHAR(120) NOT NULL, account_id VARCHAR(120) NOT NULL, doc_id VARCHAR(120) NOT NULL,
           created_at INT NOT NULL, PRIMARY KEY (user_id, src_doc, account_id)) DEFAULT CHARSET=utf8mb4',
    ] : [
        'CREATE TABLE IF NOT EXISTS sync_connections (id TEXT PRIMARY KEY, user_id TEXT NOT NULL, platform TEXT NOT NULL, key_hash TEXT NOT NULL UNIQUE,
           key_hint TEXT NOT NULL, status TEXT NOT NULL, client TEXT, last_seen_at INTEGER, last_push_at INTEGER, created_at INTEGER NOT NULL, revoked_at INTEGER)',
        'CREATE INDEX IF NOT EXISTS sync_connections_user ON sync_connections(user_id)',
        'CREATE TABLE IF NOT EXISTS sync_accounts (id TEXT PRIMARY KEY, user_id TEXT NOT NULL, platform TEXT NOT NULL, ext_id TEXT NOT NULL, info TEXT, account_id TEXT,
           state TEXT NOT NULL, last_fill_at INTEGER, last_error TEXT, created_at INTEGER NOT NULL, updated_at INTEGER NOT NULL,
           UNIQUE (user_id, platform, ext_id), UNIQUE (user_id, account_id))',
        'CREATE TABLE IF NOT EXISTS sync_fills (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL, sync_account_id TEXT NOT NULL, ext_id TEXT NOT NULL,
           contract TEXT NOT NULL, side INTEGER NOT NULL, qty INTEGER NOT NULL, price REAL NOT NULL, ts INTEGER NOT NULL, fee REAL, point_value REAL,
           removed INTEGER NOT NULL DEFAULT 0, received_at INTEGER NOT NULL, UNIQUE (sync_account_id, ext_id))',
        'CREATE INDEX IF NOT EXISTS sync_fills_contract ON sync_fills(sync_account_id, contract, ts)',
        'CREATE TABLE IF NOT EXISTS sync_trades (user_id TEXT NOT NULL, trade_id TEXT NOT NULL, doc_id TEXT NOT NULL, sync_account_id TEXT NOT NULL, sig TEXT NOT NULL,
           fills TEXT NOT NULL, entry_at TEXT NOT NULL, inst TEXT NOT NULL, dir TEXT NOT NULL, copy_group TEXT, created_at INTEGER NOT NULL, updated_at INTEGER NOT NULL,
           PRIMARY KEY (user_id, trade_id))',
        'CREATE INDEX IF NOT EXISTS sync_trades_doc ON sync_trades(user_id, doc_id)',
        'CREATE INDEX IF NOT EXISTS sync_trades_acct ON sync_trades(sync_account_id)',
        'CREATE INDEX IF NOT EXISTS sync_trades_at ON sync_trades(user_id, entry_at)',
        'CREATE TABLE IF NOT EXISTS sync_copies (user_id TEXT NOT NULL, src_doc TEXT NOT NULL, account_id TEXT NOT NULL, doc_id TEXT NOT NULL, created_at INTEGER NOT NULL,
           PRIMARY KEY (user_id, src_doc, account_id))',
    ];
    foreach ($sql as $s) $pdo->exec($s);
    // (3 Nov.) when the add-on was downloaded with this key in it (null: a key made to be pasted, before 1.3.0 or without ZipArchive)
    try { $pdo->query('SELECT downloaded_at FROM sync_connections LIMIT 0'); } catch (Throwable $e) { $pdo->exec('ALTER TABLE sync_connections ADD COLUMN downloaded_at INT NULL'); }
}

/** one write at a time (SQLite: the lock is taken at the start, so two pushes never build the same trade twice) */
function sync_tx(PDO $pdo, callable $fn)
{
    $my = sync_mysql($pdo);
    if ($my) $pdo->beginTransaction(); else $pdo->exec('BEGIN IMMEDIATE');
    try { $r = $fn(); if ($my) $pdo->commit(); else $pdo->exec('COMMIT'); return $r; }
    catch (Throwable $e) { try { if ($my) $pdo->rollBack(); else $pdo->exec('ROLLBACK'); } catch (Throwable $x) { /* already closed */ } throw $e; }
}

/* ---------------- the personal key ---------------- */

/**
 * a new key for a platform. To paste (« New key »): shown once, the previous ones stop working at once. In a download
 * ($download): written in the add-on, the previous ones keep working (a 2nd download, a 2nd computer) until « Stop the sync »
 */
function sync_new_key(PDO $pdo, string $uid, string $platform, bool $download = false): array
{
    sync_schema($pdo);
    $key = 'swk_' . bin2hex(random_bytes(20)); $now = time(); $id = 'sc_' . bin2hex(random_bytes(8));
    if (!$download) sync_q($pdo, "UPDATE sync_connections SET status = 'revoked', revoked_at = ? WHERE user_id = ? AND platform = ? AND status = 'active'", [$now, $uid, $platform]);
    sync_q($pdo, 'INSERT INTO sync_connections (id, user_id, platform, key_hash, key_hint, status, created_at, downloaded_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
        [$id, $uid, $platform, hash('sha256', $key), substr($key, -4), 'active', $now, $download ? $now : null]);
    return ['id' => $id, 'platform' => $platform, 'key' => $key, 'hint' => substr($key, -4)];
}
/** the add-ons that carry the trader's key in their download (NinjaTrader 8, 1.3.0); without ZipArchive: the key to paste, as before */
function sync_can_embed(string $platform): bool
{
    return $platform === 'ninjatrader' && class_exists('ZipArchive') && !defined('SYNC_NO_EMBED') && is_file(SYNC_ADDONS[$platform]);
}
/**
 * the NinjaTrader 8 add-on with a new key of the trader in it (EmbeddedKey in AddOns/SweepSync.cs): a zip in a temporary file,
 * or null when it cannot be made (then nothing was created)
 */
function sync_addon_zip(PDO $pdo, string $uid, string $platform): ?string
{
    if (!sync_can_embed($platform)) return null;
    $src = new ZipArchive(); if ($src->open(SYNC_ADDONS[$platform]) !== true) return null;
    $files = []; for ($i = 0; $i < $src->numFiles; $i++) { $nm = (string) $src->getNameIndex($i); $files[$nm] = (string) $src->getFromIndex($i); }
    $src->close();
    $cs = $files['AddOns/SweepSync.cs'] ?? '';
    if (!isset($files['Info.xml']) || substr_count($cs, 'public const string EmbeddedKey = "";') !== 1) return null;
    $tmp = tempnam(sys_get_temp_dir(), 'swz'); if ($tmp === false) return null;
    $k = sync_new_key($pdo, $uid, $platform, true);
    $files['AddOns/SweepSync.cs'] = str_replace('public const string EmbeddedKey = "";', 'public const string EmbeddedKey = "' . $k['key'] . '";', $cs);
    $z = new ZipArchive();
    if ($z->open($tmp, ZipArchive::OVERWRITE) !== true) { sync_q($pdo, 'DELETE FROM sync_connections WHERE id = ?', [$k['id']]); @unlink($tmp); return null; }
    foreach ($files as $nm => $data) $z->addFromString($nm, $data);
    $z->close();
    return $tmp;
}
function sync_revoke(PDO $pdo, string $uid, string $platform): int
{
    sync_schema($pdo);
    return sync_q($pdo, "UPDATE sync_connections SET status = 'revoked', revoked_at = ? WHERE user_id = ? AND platform = ? AND status = 'active'", [time(), $uid, $platform])->rowCount();
}
/** the connection behind a key (only an active key of an enabled trader); only its hash is stored */
function sync_auth(PDO $pdo, string $key): ?array
{
    if (!preg_match('/^swk_[0-9a-f]{40}$/', $key)) return null;
    sync_schema($pdo);
    $c = sync_q($pdo, "SELECT * FROM sync_connections WHERE key_hash = ? AND status = 'active'", [hash('sha256', $key)])->fetch();
    if (!$c) return null;
    try { if ((int) sync_q($pdo, 'SELECT disabled FROM users WHERE id = ?', [$c['user_id']])->fetchColumn() === 1) return null; } catch (Throwable $e) { /* no users table (tests) */ }
    return $c;
}

/* ---------------- documents ---------------- */

function sync_doc(PDO $pdo, string $uid, string $col, string $id): ?string
{
    $d = sync_q($pdo, 'SELECT data FROM documents WHERE user_id = ? AND collection = ? AND id = ?', [$uid, $col, $id])->fetchColumn();
    return $d === false ? null : (string) $d;
}
/** the plan decides, as for a trade typed in the app: a frozen account (Free plan) receives nothing, its executions wait */
function sync_guard(PDO $pdo, string $uid, string $accountId): ?array
{
    if (!function_exists('billing_on') || !function_exists('sb_guard') || !billing_on()) return null;
    return sb_guard($pdo, $uid, 'write_trade', ['account_id' => $accountId, 'account_ids' => function_exists('billing_account_ids') ? billing_account_ids($uid) : []]);
}

/* ---------------- accounts found ---------------- */

function sync_name($v): string { return mb_substr(trim(preg_replace('/[\x00-\x1F\x7F]/u', '', (string) $v)), 0, 120); }
/** what the account's name says, when a firm documents it (Apex: « APEX-… » evaluation, « PA-APEX… » funded); NinjaTrader's own simulation accounts */
function sync_guess(string $name, string $platform = 'ninjatrader'): array
{
    $u = strtoupper($name);
    if (str_starts_with($u, 'PA-APEX')) return ['firm' => 'apex', 'phase' => 'funded'];
    if (str_starts_with($u, 'APEX-')) return ['firm' => 'apex', 'phase' => 'eval'];
    if ($platform === 'ninjatrader' && preg_match('/^(SIM\d*|PLAYBACK\d*|BACKTEST)$/', $u)) return ['sim' => true];
    return [];
}
/** the platform an add-on says it is (its « client »), or null when it does not say */
function sync_client_platform(string $client): ?string
{
    foreach (SYNC_CLIENTS as $prefix => $platform) if (str_starts_with($client, $prefix)) return $platform;
    return null;
}
function sync_account_row(PDO $pdo, string $uid, string $platform, string $name, ?array $info, int $now): array
{
    $row = sync_q($pdo, 'SELECT * FROM sync_accounts WHERE user_id = ? AND platform = ? AND ext_id = ?', [$uid, $platform, $name])->fetch();
    $js = $info !== null ? json_encode($info, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES) : null;
    if (!$row) {
        $id = 'sa_' . bin2hex(random_bytes(8));
        try {
            // NinjaTrader's own simulation accounts (Sim101, Playback101) start « ignored »: one tap in the list links them
            sync_q($pdo, 'INSERT INTO sync_accounts (id, user_id, platform, ext_id, info, state, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', [$id, $uid, $platform, $name, $js, empty(sync_guess($name, $platform)['sim']) ? 'new' : 'ignored', $now, $now]);
            $made = true;
        } catch (Throwable $e) { /* added by a push running at the same time */ }
        $row = sync_q($pdo, 'SELECT * FROM sync_accounts WHERE user_id = ? AND platform = ? AND ext_id = ?', [$uid, $platform, $name])->fetch();
        if ($row && !empty($made)) $row['_found'] = true;   // found by this push (the trader is told once, sync_receive)
        return $row;
    }
    if ($js !== null && $js !== $row['info']) { sync_q($pdo, 'UPDATE sync_accounts SET info = ?, updated_at = ? WHERE id = ?', [$js, $now, $row['id']]); $row['info'] = $js; }
    return $row;
}

/* ---------------- receiving executions ---------------- */

/**
 * A push from a platform: {client, accounts: [{name, connection, provider, currency, cash}], fills: [{id, account, contract,
 * side, qty, price, ts (UTC ms), fee, point_value, removed}]}. New executions are kept, the same ones skipped, amended ones
 * updated; then the trades of the linked accounts whose executions changed are rebuilt and written.
 */
function sync_receive(PDO $pdo, array $conn, array $p): array
{
    sync_schema($pdo);
    $uid = (string) $conn['user_id']; $platform = (string) $conn['platform']; $now = time();
    $fills = array_values((array) ($p['fills'] ?? []));
    if (count($fills) > SYNC_MAX_FILLS) return ['error' => 'too_many', 'max' => SYNC_MAX_FILLS];
    $names = [];
    foreach (array_slice(array_values((array) ($p['accounts'] ?? [])), 0, SYNC_MAX_ACCOUNTS) as $a) {
        if (!is_array($a) || ($n = sync_name($a['name'] ?? '')) === '') continue;
        $names[$n] = ['connection' => sync_name($a['connection'] ?? ''), 'provider' => sync_name($a['provider'] ?? ''), 'currency' => strtoupper(substr(sync_name($a['currency'] ?? ''), 0, 3)),
            'cash' => is_numeric($a['cash'] ?? null) && is_finite((float) $a['cash']) ? round((float) $a['cash'], 2) : null];
    }
    foreach ($fills as $f) if (is_array($f) && ($n = sync_name($f['account'] ?? '')) !== '' && !array_key_exists($n, $names)) $names[$n] = null;
    if (count($names) > SYNC_MAX_ACCOUNTS) return ['error' => 'too_many_accounts', 'max' => SYNC_MAX_ACCOUNTS];
    $min = 1577836800000; $max = ($now + 86400) * 1000;   // 2020-01-01 … tomorrow
    $stats = ['new' => 0, 'changed' => 0, 'skipped' => 0];
    $client = sync_name($p['client'] ?? '') ?: null; $cid = (string) $conn['id'];
    [$rows, $touched] = sync_tx($pdo, function () use ($pdo, $uid, $platform, $names, $fills, $now, $min, $max, $client, $cid, &$stats) {
        // (string): PHP turns a key of digits only (an account « 1234567 ») into an int
        $rows = []; foreach ($names as $n => $info) $rows[$n] = sync_account_row($pdo, $uid, $platform, (string) $n, $info, $now);
        $touched = [];
        foreach ($fills as $raw) {
            $acct = is_array($raw) ? sync_name($raw['account'] ?? '') : '';
            $f = $acct !== '' ? sync_fill(['acct' => $acct] + $raw) : null;
            if (!$f || $f['ts'] < $min || $f['ts'] > $max || strlen($f['id']) > 120 || strlen($f['contract']) > 40) { $stats['skipped']++; continue; }
            $sa = $rows[$acct];
            $vals = [$f['contract'], $f['side'], $f['qty'], $f['price'], $f['ts'], $f['fee'], $f['pv'], $f['removed'] ? 1 : 0];
            $old = sync_q($pdo, 'SELECT contract, side, qty, price, ts, fee, point_value, removed FROM sync_fills WHERE sync_account_id = ? AND ext_id = ?', [$sa['id'], $f['id']])->fetch(PDO::FETCH_NUM);
            if ($old === false) {
                sync_q($pdo, 'INSERT INTO sync_fills (user_id, sync_account_id, ext_id, contract, side, qty, price, ts, fee, point_value, removed, received_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                    array_merge([$uid, $sa['id'], $f['id']], $vals, [$now]));
                $stats['new']++;
            } else {
                $same = true; foreach ($vals as $i => $v) { $o = $old[$i]; if ($v === null || $o === null ? $v !== $o : (is_float($v) ? abs((float) $o - $v) > 1e-9 : (string) $o !== (string) $v)) { $same = false; break; } }
                if ($same) continue;
                sync_q($pdo, 'UPDATE sync_fills SET contract = ?, side = ?, qty = ?, price = ?, ts = ?, fee = ?, point_value = ?, removed = ?, received_at = ? WHERE sync_account_id = ? AND ext_id = ?',
                    array_merge($vals, [$now, $sa['id'], $f['id']]));
                $stats['changed']++;
                $touched[$sa['id']][(string) $old[0]] = true;   // an execution moved to another contract: the old one is rebuilt too
            }
            $touched[$sa['id']][$f['contract']] = true;
            sync_q($pdo, 'UPDATE sync_accounts SET last_fill_at = ? WHERE id = ? AND (last_fill_at IS NULL OR last_fill_at < ?)', [$f['ts'], $sa['id'], $f['ts']]);
        }
        sync_q($pdo, 'UPDATE sync_connections SET last_seen_at = ?, last_push_at = CASE WHEN ? > 0 THEN ? ELSE last_push_at END, client = ? WHERE id = ?',
            [$now, count($fills), $now, $client, $cid]);
        return [$rows, $touched];
    });
    $written = ['created' => 0, 'updated' => 0, 'merged' => 0];
    foreach ($touched as $sid => $contracts) {
        $sa = null; foreach ($rows as $r) if ($r['id'] === $sid) $sa = $r;
        if (!$sa || $sa['state'] !== 'linked') continue;
        $r = sync_apply($pdo, $uid, $sa, array_keys($contracts));
        foreach ($written as $k => $v) $written[$k] += $r[$k] ?? 0;
    }
    $states = []; foreach ($rows as $n => $r) $states[] = ['name' => (string) $n, 'state' => $r['state']];
    // new accounts to link: the trader hears it in the app (bell), wherever they are; one notification per platform and day at most
    $fresh = 0; foreach ($rows as $r) if ($r['state'] === 'new' && !empty($r['_found'])) $fresh++;
    if ($fresh && class_exists('Notify')) {
        $n = (int) sync_q($pdo, "SELECT COUNT(*) FROM sync_accounts WHERE user_id = ? AND platform = ? AND state = 'new'", [$uid, $platform])->fetchColumn();
        Notify::send($uid, 'sync_found', ['n' => $n, 'platform' => SYNC_NAMES[$platform] ?? $platform], ['dedupe_key' => 'sync_found:' . $platform . ':' . gmdate('Y-m-d', $now), 'action_url' => '#settings/sync']);
    }
    return ['ok' => true, 'received' => count($fills)] + $stats + ['trades' => $written, 'accounts' => $states];
}

/* ---------------- building and writing the trades ---------------- */

/** a trade typed by hand that is the same trade: same instrument, side and contracts, entry within SYNC_MATCH_MIN minutes */
function sync_match(array $t, array &$manual): ?string
{
    $at = strtotime($t['executions'][0]['t'] . ' America/New_York');
    $best = null; $bestD = PHP_INT_MAX;
    foreach ($manual as $id => $m) {
        // a copy made by Sweep (copy_src) is that trade whatever its size: the synced trade wins over the copy (copy groups, brief « avance concurrentielle », step 2)
        if (($m['instrument'] ?? '') !== $t['instrument'] || ($m['direction'] ?? '') !== $t['direction'] || (empty($m['copy_src']) && (int) ($m['contracts'] ?? 0) !== (int) $t['contracts']) || $m['_at'] === null) continue;
        $d = abs(intdiv($m['_at'], 60) - intdiv($at, 60));
        if ($d <= SYNC_MATCH_MIN && ($d < $bestD || ($d === $bestD && strcmp((string) $id, (string) $best) < 0))) { $best = (string) $id; $bestD = $d; }
    }
    if ($best !== null) unset($manual[$best]);
    return $best;
}
/** trades typed by hand on a Sweep account during some sessions (by their date), not written by a sync, with their entry time */
function sync_manual(PDO $pdo, string $uid, string $accountId, array $days, array $skip): array
{
    $out = []; if (!$days) return $out;
    $acc = '%"account_id":' . json_encode($accountId, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES) . '%';
    foreach (array_chunk($days, 50) as $part) {
        $or = implode(' OR ', array_fill(0, count($part), 'data LIKE ?'));
        $args = array_merge([$uid, $acc], array_map(fn($d) => '%"date":"' . $d . '"%', $part));
        foreach (sync_q($pdo, "SELECT id, data FROM documents WHERE user_id = ? AND collection = 'trades' AND data LIKE ? AND ($or)", $args) as $r) {
            if (isset($skip[$r['id']])) continue;
            $d = json_decode((string) $r['data'], true) ?: [];
            if (($d['account_id'] ?? '') !== $accountId || !empty($d['demo']) || !in_array($d['date'] ?? '', $part, true)) continue;
            $d['_at'] = sync_doc_at($d); $out[(string) $r['id']] = $d;
        }
    }
    if ($out) foreach (array_chunk(array_keys($out), 200) as $part)
        foreach (sync_q($pdo, 'SELECT doc_id FROM sync_trades WHERE user_id = ? AND doc_id IN (' . implode(',', array_fill(0, count($part), '?')) . ')', array_merge([$uid], $part)) as $r) unset($out[$r['doc_id']]);
    return $out;
}
/** the entry time of a trade document (New York): its first execution, else date + entry time (an evening entry belongs to the day before its session) */
function sync_doc_at(array $d): ?int
{
    $x = $d['executions'][0]['t'] ?? null;
    if (is_string($x) && preg_match('/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}/', $x)) return strtotime(substr($x, 0, 19) . ' America/New_York') ?: null;
    $date = (string) ($d['date'] ?? ''); $tm = substr((string) ($d['entry_time'] ?? ''), 0, 5);
    if (!preg_match('/^\d{4}-\d{2}-\d{2}$/', $date) || !preg_match('/^\d{2}:\d{2}$/', $tm)) return null;
    if ($tm >= '18:00' && !empty($d['session_date'])) $date = (new DateTimeImmutable($date . ' 12:00:00'))->modify('-1 day')->format('Y-m-d');
    return strtotime("$date $tm:00 America/New_York") ?: null;
}

/**
 * Rebuild the trades of one linked account (only $contracts when given) and write what changed.
 * $accountId / $dry: the preview before linking (counts only, nothing written).
 * Returns counts: created, updated, merged (typed by hand, completed), deleted (removed by the trader, left out), open
 * positions, manual (typed by hand in the same days with no synced equivalent; preview only), error (account, plan).
 */
function sync_apply(PDO $pdo, string $uid, array $sa, ?array $contracts = null, ?string $accountId = null, bool $dry = false): array
{
    sync_schema($pdo);
    $accountId ??= (string) ($sa['account_id'] ?? '');
    $out = ['created' => 0, 'updated' => 0, 'merged' => 0, 'deleted' => 0, 'open' => 0];
    $accRaw = $accountId !== '' ? sync_doc($pdo, $uid, 'accounts', $accountId) : null;
    $acc = $accRaw !== null ? (json_decode($accRaw, true) ?: []) : null;
    if (!$acc || !empty($acc['demo'])) {
        if (!$dry && ($sa['state'] ?? '') === 'linked') sync_q($pdo, "UPDATE sync_accounts SET state = 'new', account_id = NULL, last_error = 'account_gone', updated_at = ? WHERE id = ?", [time(), $sa['id']]);
        return $out + ['error' => 'account'];
    }
    if (!$dry && ($deny = sync_guard($pdo, $uid, $accountId))) {
        sync_q($pdo, "UPDATE sync_accounts SET last_error = 'plan', updated_at = ? WHERE id = ?", [time(), $sa['id']]);
        return $out + ['error' => 'plan', 'plan' => $deny];
    }
    $key = $sa['platform'] . ':' . $sa['ext_id'];   // stable key of the platform account → stable trade ids
    $events = [];
    $work = function () use ($pdo, $uid, $sa, $contracts, $accountId, $acc, $key, $dry, &$out, &$events) {
        // every execution of the contracts concerned (a trade is always rebuilt from flat)
        $args = [$sa['id']]; $where = '';
        if ($contracts) { $where = ' AND contract IN (' . implode(',', array_fill(0, count($contracts), '?')) . ')'; $args = array_merge($args, array_values($contracts)); }
        $fills = [];
        foreach (sync_q($pdo, 'SELECT ext_id, contract, side, qty, price, ts, fee, point_value, removed FROM sync_fills WHERE sync_account_id = ?' . $where, $args) as $r)
            $fills[] = ['id' => (string) $r['ext_id'], 'acct' => $key, 'contract' => (string) $r['contract'], 'side' => (int) $r['side'], 'qty' => (int) $r['qty'], 'price' => (float) $r['price'],
                'ts' => (int) $r['ts'], 'fee' => $r['fee'] === null ? null : (float) $r['fee'], 'point_value' => $r['point_value'] === null ? null : (float) $r['point_value'], 'removed' => (int) $r['removed'] === 1];
        $b = sync_build($fills, ['accounts' => [$key => ['account_id' => $accountId, 'fee_rt_c' => (int) ($acc['fee_rt_c'] ?? 0)]], 'source' => $sa['platform']]);
        $out['open'] = count($b['open']);
        // what was written before for this account, and which documents already belong to a sync (never matched again)
        $rows = []; $owner = [];
        foreach (sync_q($pdo, 'SELECT * FROM sync_trades WHERE user_id = ? AND sync_account_id = ?', [$uid, $sa['id']]) as $r) {
            $r['fills'] = json_decode((string) $r['fills'], true) ?: []; $rows[$r['trade_id']] = $r;
            foreach ($r['fills'] as $fid) $owner[$fid] = $r['trade_id'];
        }
        $built = []; foreach ($b['trades'] as $t) $built[$t['id']] = true;
        // trades typed by hand on this Sweep account, the days of the synced trades not written yet (never a document a sync already wrote)
        $days = []; foreach ($b['trades'] as $t) if (!isset($rows[$t['id']])) $days[$t['date']] = true;
        $manual = sync_manual($pdo, $uid, $accountId, array_keys($days), $built);
        // each built trade → the document it goes to
        $plan = [];
        foreach ($b['trades'] as $t) {
            $fids = array_values(array_unique(array_column($t['executions'], 'id')));
            if (isset($rows[$t['id']])) { $plan[] = [$t, $rows[$t['id']]['doc_id'], 'update', null, $fids]; continue; }
            $prev = null; foreach ($fids as $fid) if (isset($owner[$fid]) && !isset($built[$owner[$fid]])) { $prev = $owner[$fid]; break; }
            if ($prev !== null) { $plan[] = [$t, $rows[$prev]['doc_id'], 'takeover', $prev, $fids]; continue; }   // an earlier execution arrived late: same document, new id
            $m = sync_match($t, $manual);
            $plan[] = $m !== null ? [$t, $m, 'merge', null, $fids] : [$t, $t['id'], 'create', null, $fids];
        }
        $out['manual'] = count($manual);
        // copy groups with the synced trades of the trader's other accounts at the same minutes
        $groups = sync_groups($pdo, $uid, $sa['id'], array_column($plan, 0), $dry);
        $now = time(); $iso = sync_iso(); $creates = 0; $written = [];
        foreach ($plan as [$t, $docId, $kind, $prevTid, $fids]) {
            $t['copy_group'] = $groups[$t['id']] ?? null;
            $sig = sha1(json_encode([array_intersect_key($t, array_flip(SYNC_TRADE_FIELDS)), $accountId, $t['copy_group']]));
            $raw = sync_doc($pdo, $uid, 'trades', $docId);
            $row = ['trade_id' => $t['id'], 'doc_id' => $docId, 'sig' => $sig, 'fills' => json_encode($fids), 'entry_at' => $t['executions'][0]['t'], 'inst' => $t['instrument'], 'dir' => $t['direction'], 'copy_group' => $t['copy_group']];
            if ($kind === 'update' || $kind === 'takeover') {
                if ($raw === null) {   // the trader deleted it: never written again
                    $out['deleted']++;
                    if (!$dry && $kind === 'takeover') sync_row($pdo, $uid, $sa['id'], ['sig' => ''] + $row, $prevTid, $now);
                    continue;
                }
                if ($kind === 'update' && $rows[$t['id']]['sig'] === $sig) continue;   // nothing changed
            }
            $out[$kind === 'create' ? 'created' : ($kind === 'merge' ? 'merged' : 'updated')]++;
            if ($dry) continue;
            if ($raw === null) $creates++;
            $doc = sync_doc_fields($raw, $t, $docId, $uid, $accountId, $iso);
            $json = sync_put($pdo, $uid, $docId, $doc, $raw !== null, $iso);
            $events[] = [$docId, json_decode($json, true), $raw === null ? null : (json_decode($raw, true) ?: [])];
            sync_row($pdo, $uid, $sa['id'], $row, $prevTid, $now);
            $written[] = [$docId, $kind];
        }
        if (!$dry) $creates += sync_follow($pdo, $uid, $accountId, $written, $events);   // a master account's trades on its followers
        if (!$dry && $creates > 0) {
            $max = (int) ($GLOBALS['MAX_DOCS'] ?? 50000);
            if ((int) sync_q($pdo, 'SELECT COUNT(*) FROM documents WHERE user_id = ?', [$uid])->fetchColumn() > $max) throw new SyncLimit();
        }
        if (!$dry) sync_q($pdo, 'UPDATE sync_accounts SET last_error = NULL, updated_at = ? WHERE id = ?', [$now, $sa['id']]);
    };
    if ($dry) { $work(); return $out; }
    try { sync_tx($pdo, $work); }
    catch (SyncLimit $e) {
        sync_q($pdo, "UPDATE sync_accounts SET last_error = 'limit', updated_at = ? WHERE id = ?", [time(), $sa['id']]);
        return ['created' => 0, 'updated' => 0, 'merged' => 0, 'deleted' => 0, 'open' => $out['open'], 'error' => 'limit'];
    }
    // after the commit, as api/docs/batch: the game and the notifications once per trading day touched, the referral check once
    if (function_exists('nt_doc_event')) {
        $byDay = []; foreach ($events as $ev) $byDay[($ev[1]['date'] ?? '') . '|' . ($ev[1]['account_id'] ?? $accountId)] = $ev;
        foreach ($byDay as $ev) { try { nt_doc_event($uid, 'trades', $ev[0], $ev[1], $ev[2]); } catch (Throwable $e) { error_log('[Sweep sync] event: ' . $e->getMessage()); } }
    }
    if ($out['created'] > 0 && function_exists('ref_check_user')) { try { ref_check_user($pdo, $uid); } catch (Throwable $e) { /* referral check next time */ } }
    return $out;
}
final class SyncLimit extends RuntimeException {}

/** the trade's document: the platform's fields replaced, everything the trader wrote kept (read as objects: an empty {} stays {}) */
function sync_doc_fields(?string $raw, array $t, string $docId, string $uid, string $accountId, string $iso): stdClass
{
    $d = $raw !== null ? json_decode($raw) : null;
    if (!($d instanceof stdClass)) $d = (object) ['discipline' => new stdClass(), 'emo' => new stdClass(), 'review' => new stdClass(), 'tags' => [], 'shots' => [], 'setup' => '', 'notes' => '', 'created_at' => $iso];
    foreach (SYNC_TRADE_FIELDS as $k) {
        if ($k === 'import_key' && !empty($d->import_key) && !str_starts_with((string) $d->import_key, 'sync:')) continue;   // a CSV import's key stays (no double on a re-import)
        if (array_key_exists($k, $t)) $d->$k = $t[$k]; else unset($d->$k);
    }
    $own = empty($d->copy_group) || str_starts_with((string) $d->copy_group, 'cg-');   // a copy group the trader made stays
    if ($own) { if ($t['copy_group']) $d->copy_group = $t['copy_group']; else unset($d->copy_group); }
    $d->id = $docId; $d->account_id = $accountId; $d->user_id = $uid;
    return $d;
}
/** writes a trade document, returns its JSON */
function sync_put(PDO $pdo, string $uid, string $id, stdClass $doc, bool $exists, string $iso): string
{
    $json = json_encode($doc, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    if ($exists) sync_q($pdo, "UPDATE documents SET data = ?, updated_at = ? WHERE user_id = ? AND collection = 'trades' AND id = ?", [$json, $iso, $uid, $id]);
    else sync_q($pdo, "INSERT INTO documents (user_id, collection, id, data, created_at, updated_at) VALUES (?, 'trades', ?, ?, ?, ?)", [$uid, $id, $json, $iso, $iso]);
    return $json;
}
function sync_row(PDO $pdo, string $uid, string $sid, array $r, ?string $prevTid, int $now): void
{
    if ($prevTid !== null) sync_q($pdo, 'DELETE FROM sync_trades WHERE user_id = ? AND trade_id = ?', [$uid, $prevTid]);
    $up = sync_q($pdo, 'UPDATE sync_trades SET doc_id = ?, sig = ?, fills = ?, entry_at = ?, inst = ?, dir = ?, copy_group = ?, updated_at = ? WHERE user_id = ? AND trade_id = ?',
        [$r['doc_id'], $r['sig'], $r['fills'], $r['entry_at'], $r['inst'], $r['dir'], $r['copy_group'], $now, $uid, $r['trade_id']]);
    if ($up->rowCount() === 0) sync_q($pdo, 'INSERT INTO sync_trades (user_id, trade_id, doc_id, sync_account_id, sig, fills, entry_at, inst, dir, copy_group, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
        [$uid, $r['trade_id'], $r['doc_id'], $sid, $r['sig'], $r['fills'], $r['entry_at'], $r['inst'], $r['dir'], $r['copy_group'], $now, $now]);
}

/**
 * copy groups (sync_copy_groups) over the trades built for one account and the synced trades of the trader's other
 * accounts at the same minutes. A trade of another account whose group changes gets it on its document too.
 * Returns trade id → copy group for the trades built.
 */
function sync_groups(PDO $pdo, string $uid, string $sid, array $trades, bool $dry): array
{
    if (!$trades) return [];
    $mins = array_values(array_unique(array_map(fn($t) => substr($t['executions'][0]['t'], 0, 16), $trades)));
    $all = array_map(fn($t) => ['acct' => $sid] + $t, $trades); $other = [];
    foreach (array_chunk($mins, 200) as $part) {
        $rs = sync_q($pdo, 'SELECT trade_id, doc_id, sync_account_id, entry_at, inst, dir, copy_group FROM sync_trades WHERE user_id = ? AND sync_account_id <> ? AND SUBSTR(entry_at, 1, 16) IN (' . implode(',', array_fill(0, count($part), '?')) . ')', array_merge([$uid, $sid], $part));
        foreach ($rs as $r) { $other[$r['trade_id']] = $r; $all[] = ['id' => $r['trade_id'], 'acct' => $r['sync_account_id'], 'instrument' => $r['inst'], 'direction' => $r['dir'], 'executions' => [['t' => $r['entry_at']]]]; }
    }
    $out = [];
    foreach (sync_copy_groups($all) as $t) {
        $g = $t['copy_group'] ?? null;
        if (!isset($other[$t['id']])) { $out[$t['id']] = $g; continue; }
        $r = $other[$t['id']];
        if ($dry || (string) $r['copy_group'] === (string) $g) continue;
        sync_q($pdo, 'UPDATE sync_trades SET copy_group = ? WHERE user_id = ? AND trade_id = ?', [$g, $uid, $r['trade_id']]);
        $raw = sync_doc($pdo, $uid, 'trades', $r['doc_id']); if ($raw === null) continue;
        $d = json_decode($raw); if (!($d instanceof stdClass)) continue;
        if (!empty($d->copy_group) && !str_starts_with((string) $d->copy_group, 'cg-')) continue;   // grouped by the trader
        if ($g) $d->copy_group = $g; else unset($d->copy_group);
        sync_put($pdo, $uid, $r['doc_id'], $d, true, sync_iso());
    }
    return $out;
}

/* ---------------- copy groups with a master account (brief « avance concurrentielle », step 2, 2 Nov.) ----------------
 * Accounts › « Copy group »: a master account (copy_lead) and its followers (same group_id), each with a contract
 * multiplier (copy_pct ÷ 100, ×1 by default). A trade the sync writes for the first time on the master is copied on each
 * follower, the way the app copies (SweepCopy.make, nav.js): its size × the multiplier (at least 1 contract), its P&L for
 * that size, the follower's commission; the setup, grade, emotions and notes of the moment. Later platform corrections of
 * the master's trade move its copies (platform fields only); a copy the trader deleted is never written again.
 * A follower synced itself is never copied: its own synced trade joins the master trade's group (no double).
 * Pro and Elite (limit copy_groups). */

/** the copy group of a Sweep account when the group has a master: ['group', 'lead', 'followers'], else null */
function sync_lead_group(PDO $pdo, string $uid, string $accountId): ?array
{
    $all = [];
    foreach (sync_q($pdo, "SELECT id, data FROM documents WHERE user_id = ? AND collection = 'accounts'", [$uid]) as $r) {
        $d = json_decode((string) $r['data'], true); if (is_array($d)) $all[(string) $r['id']] = ['id' => (string) $r['id']] + $d;
    }
    $g = (string) ($all[$accountId]['group_id'] ?? ''); if ($g === '') return null;
    $ok = fn(array $a) => empty($a['demo']) && !in_array($a['status'] ?? 'active', ['archived', 'closed'], true);
    $lead = null; $fol = [];
    foreach ($all as $a) if ((string) ($a['group_id'] ?? '') === $g && $ok($a)) { if ($lead === null && !empty($a['copy_lead'])) $lead = $a; else $fol[] = $a; }
    if ($lead) $fol = array_values(array_filter($fol, fn($a) => $a['id'] !== $lead['id']));
    return $lead && $fol ? ['group' => $g, 'lead' => $lead, 'followers' => $fol] : null;
}
/** the plan decides (Pro and Elite); without billing, or before it is live for this trader, everyone */
function sync_copy_allowed(PDO $pdo, string $uid): bool
{
    if (!function_exists('billing_on') || !billing_on() || !function_exists('sb_can')) return true;
    if (function_exists('sb_live') && !sb_live($uid)) return true;
    return sb_can($pdo, $uid, 'copy_groups');
}
/** the trade of an account taken at the same moment as $m (instrument, side, entry within SYNC_MATCH_MIN minutes); with $grp, in no other group */
function sync_twin(PDO $pdo, string $uid, string $accountId, array $m, ?string $grp): ?array
{
    $at = sync_doc_at($m); if ($at === null || empty($m['date'])) return null;
    $acc = '%"account_id":' . json_encode($accountId, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES) . '%';
    $best = null; $bestD = PHP_INT_MAX;
    foreach (sync_q($pdo, "SELECT id, data FROM documents WHERE user_id = ? AND collection = 'trades' AND data LIKE ? AND data LIKE ?", [$uid, $acc, '%"date":"' . $m['date'] . '"%']) as $r) {
        $d = json_decode((string) $r['data'], true); if (!is_array($d) || ($d['account_id'] ?? '') !== $accountId || !empty($d['demo'])) continue;
        if (($d['instrument'] ?? '') !== ($m['instrument'] ?? '') || ($d['direction'] ?? '') !== ($m['direction'] ?? '')) continue;
        $cg = (string) ($d['copy_group'] ?? ''); if ($grp !== null && $cg !== '' && $cg !== $grp && !str_starts_with($cg, 'cg-')) continue;
        $x = sync_doc_at($d); if ($x === null) continue;
        $dd = abs(intdiv($x, 60) - intdiv($at, 60));
        if ($dd <= SYNC_MATCH_MIN && $dd < $bestD) { $best = ['id' => (string) $r['id']] + $d; $bestD = $dd; }
    }
    return $best;
}
/** a trade document's copy group, and nothing else the trader wrote */
function sync_set_group(PDO $pdo, string $uid, string $docId, string $grp): void
{
    $raw = sync_doc($pdo, $uid, 'trades', $docId); if ($raw === null) return;
    $d = json_decode($raw); if (!($d instanceof stdClass) || (string) ($d->copy_group ?? '') === $grp) return;
    $d->copy_group = $grp; sync_put($pdo, $uid, $docId, $d, true, sync_iso());
}
function sync_ts_of($v): int { $t = is_string($v) && $v !== '' ? strtotime($v) : false; return $t === false ? 0 : $t; }
/** a copy of the master's trade $m on follower $f (its size, P&L, commission); $prev: the copy already written (platform fields only) */
function sync_copy_doc(array $m, array $f, string $grp, string $cid, int $k, ?array $prev): array
{
    $n0 = max(1, (int) ($m['contracts'] ?? 1)); $p = (float) ($f['copy_pct'] ?? 0); if ($p <= 0) $p = 100;
    $n = max(1, (int) round($n0 * $p / 100)); $x = $n / $n0;
    if ($prev === null) {
        $d = $m; unset($d['real_pnl_c'], $d['pnl_real']);
        // the original stays the earliest: a group counts as its original (Stats, Journal, My money, the coach, the server)
        $d['created_at'] = gmdate('Y-m-d\TH:i:s\Z', max(time(), sync_ts_of($m['created_at'] ?? null)) + 1 + $k);
        if ($x != 1 && isset($m['risk_c']) && is_numeric($m['risk_c'])) $d['risk_c'] = (int) round($m['risk_c'] * $x);
    } else {
        $d = $prev;
        foreach (SYNC_TRADE_FIELDS as $q) { if (array_key_exists($q, $m)) $d[$q] = $m[$q]; else unset($d[$q]); }
    }
    unset($d['import_key'], $d['source']);   // a copy made by Sweep is not the platform's trade
    $d['id'] = $cid; $d['account_id'] = (string) $f['id']; $d['copy_group'] = $grp; $d['copy_src'] = (string) $m['id'];
    $d['contracts'] = $n;
    $ex = is_array($m['executions'] ?? null) ? $m['executions'] : [];
    if ($x != 1) {
        $ex = array_map(fn($e) => ['qty' => max(1, (int) round(((float) ($e['qty'] ?? 0)) * $x))] + $e, $ex);
        if (isset($m['pnl_c']) && is_numeric($m['pnl_c'])) $d['pnl_c'] = (int) round($m['pnl_c'] * $x);
    }
    $d['executions'] = $ex;
    $fee = (int) ($f['fee_rt_c'] ?? 0);
    if ($fee > 0) {   // its own commission, one round trip per contract bought or sold (turnsOf in nav.js)
        $side = $ex[0]['side'] ?? null; $q = 0; foreach ($ex as $e) if (($e['side'] ?? null) === $side) $q += (int) ($e['qty'] ?? 0);
        $d['fees_c'] = (int) round($fee * ($q > 0 ? $q : $n)); $d['fees_auto'] = true;
    } elseif (isset($m['fees_c']) && is_numeric($m['fees_c'])) { $d['fees_c'] = (int) round($m['fees_c'] * $x); unset($d['fees_auto']); }
    return sync_objs($d);
}
/** read as arrays, an empty {} came back as []: the trader's maps stay maps (a checklist answer added later must keep its key) */
function sync_objs(array $d): array { foreach (['discipline', 'emo', 'review'] as $q) if (array_key_exists($q, $d) && $d[$q] === []) $d[$q] = new stdClass(); return $d; }
/**
 * After a sync wrote trades on $accountId: on a master, its new trades are copied on its followers (a synced follower's own
 * trade joins the group instead) and its corrected trades move their copies; on a synced follower, each trade joins the group
 * of the master's trade taken at the same moment. Returns the number of documents created (the record limit).
 */
function sync_follow(PDO $pdo, string $uid, string $accountId, array $written, array &$events): int
{
    if (!$written) return 0;
    $G = sync_lead_group($pdo, $uid, $accountId); if (!$G || !sync_copy_allowed($pdo, $uid)) return 0;
    $linked = [];
    foreach (sync_q($pdo, "SELECT account_id FROM sync_accounts WHERE user_id = ? AND state = 'linked' AND account_id IS NOT NULL", [$uid]) as $r) $linked[(string) $r['account_id']] = true;
    $iso = sync_iso(); $made = 0;
    $groupOf = function (string $docId, array &$m) use ($pdo, $uid): string {
        $g = (string) ($m['copy_group'] ?? '');
        if ($g === '') { $g = 'mg-' . substr(sha1($uid . '|' . $docId), 0, 20); sync_set_group($pdo, $uid, $docId, $g); $m['copy_group'] = $g; }
        return $g;
    };
    if ((string) $G['lead']['id'] !== $accountId) {
        // a follower synced with its platform: its trade joins the master's trade of the same moment (never a copy of it)
        if (!isset($linked[$accountId])) return 0;
        foreach ($written as [$docId]) {
            $raw = sync_doc($pdo, $uid, 'trades', $docId); $d = $raw === null ? null : json_decode($raw, true); if (!is_array($d)) continue;
            $cur = (string) ($d['copy_group'] ?? ''); if ($cur !== '' && !str_starts_with($cur, 'cg-')) continue;   // grouped by the trader
            $m = sync_twin($pdo, $uid, (string) $G['lead']['id'], $d, null); if (!$m) continue;   // the master's trade, whatever its group
            $g = $groupOf((string) $m['id'], $m);
            if ($cur !== $g) sync_set_group($pdo, $uid, $docId, $g);
        }
        return 0;
    }
    foreach ($written as [$docId, $kind]) {
        $raw = sync_doc($pdo, $uid, 'trades', $docId); $m = $raw === null ? null : json_decode($raw, true);
        if (!is_array($m) || !empty($m['demo'])) continue;
        $m['id'] = $docId; $k = 0; $grp = null;
        foreach ($G['followers'] as $f) {
            $fid = (string) $f['id'];
            if (isset($linked[$fid])) {   // synced itself: its own trade wins, in the same group
                $tw = sync_twin($pdo, $uid, $fid, $m, (string) ($m['copy_group'] ?? ''));
                if ($tw) { $grp ??= $groupOf($docId, $m); if ((string) ($tw['copy_group'] ?? '') !== $grp) sync_set_group($pdo, $uid, (string) $tw['id'], $grp); }
                continue;
            }
            $cid = sync_q($pdo, 'SELECT doc_id FROM sync_copies WHERE user_id = ? AND src_doc = ? AND account_id = ?', [$uid, $docId, $fid])->fetchColumn();
            if ($cid === false) {
                // only a trade new to Sweep: one typed in the app (then completed by the sync) had its copies chosen in the form
                if ($kind !== 'create' || sync_guard($pdo, $uid, $fid)) continue;
                $grp ??= $groupOf($docId, $m);
                $cid = 'cp-' . substr(sha1($uid . '|' . $docId . '|' . $fid), 0, 20);
                if (sync_doc($pdo, $uid, 'trades', $cid) !== null) continue;
                $c = sync_copy_doc($m, $f, $grp, $cid, $k++, null);
                $json = sync_put($pdo, $uid, $cid, json_decode(json_encode($c, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES)), false, $iso);
                sync_q($pdo, 'INSERT INTO sync_copies (user_id, src_doc, account_id, doc_id, created_at) VALUES (?, ?, ?, ?, ?)', [$uid, $docId, $fid, $cid, time()]);
                $events[] = [$cid, json_decode($json, true), null]; $made++;
                continue;
            }
            $cid = (string) $cid; $craw = sync_doc($pdo, $uid, 'trades', $cid);
            if ($craw === null) continue;   // the trader deleted this copy: never written again
            if (sync_q($pdo, 'SELECT 1 FROM sync_trades WHERE user_id = ? AND doc_id = ?', [$uid, $cid])->fetchColumn()) continue;   // now the platform's own trade
            $prev = json_decode($craw, true); if (!is_array($prev)) continue; $prev = sync_objs($prev);
            $grp ??= $groupOf($docId, $m);
            $c = sync_copy_doc($m, $f, $grp, $cid, 0, $prev);
            if ($c == $prev) continue;
            $json = sync_put($pdo, $uid, $cid, json_decode(json_encode($c, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES)), true, $iso);
            $events[] = [$cid, json_decode($json, true), $prev];
        }
    }
    return $made;
}

/* ---------------- what the trader does ---------------- */

function sync_account_of(PDO $pdo, string $uid, string $id): ?array
{
    sync_schema($pdo);
    $r = sync_q($pdo, 'SELECT * FROM sync_accounts WHERE user_id = ? AND id = ?', [$uid, $id])->fetch();
    return $r ?: null;
}
/** before linking: what linking would do (counts only) */
function sync_preview(PDO $pdo, string $uid, string $sid, string $accountId): array
{
    $sa = sync_account_of($pdo, $uid, $sid); if (!$sa) return ['error' => 'not_found'];
    $r = sync_apply($pdo, $uid, $sa, null, $accountId, true);
    return isset($r['error']) ? $r : ['add' => $r['created'], 'complete' => $r['merged'], 'manual' => $r['manual'] ?? 0, 'open' => $r['open']];
}
/** link a platform account to a Sweep account, then write its trades */
function sync_link(PDO $pdo, string $uid, string $sid, string $accountId): array
{
    $sa = sync_account_of($pdo, $uid, $sid); if (!$sa) return ['error' => 'not_found'];
    $raw = $accountId !== '' ? sync_doc($pdo, $uid, 'accounts', $accountId) : null;
    if ($raw === null || !empty((json_decode($raw, true) ?: [])['demo'])) return ['error' => 'account'];
    $other = sync_q($pdo, 'SELECT id FROM sync_accounts WHERE user_id = ? AND account_id = ? AND id <> ?', [$uid, $accountId, $sid])->fetchColumn();
    if ($other !== false) return ['error' => 'taken'];
    sync_q($pdo, "UPDATE sync_accounts SET state = 'linked', account_id = ?, last_error = NULL, updated_at = ? WHERE id = ?", [$accountId, time(), $sid]);
    $sa = sync_account_of($pdo, $uid, $sid);
    return ['ok' => true] + sync_apply($pdo, $uid, $sa);
}
/** ignore a platform account, or undo a link (the trades already written stay: they are the trader's) */
function sync_set_state(PDO $pdo, string $uid, string $sid, string $state): array
{
    $sa = sync_account_of($pdo, $uid, $sid); if (!$sa) return ['error' => 'not_found'];
    sync_q($pdo, 'UPDATE sync_accounts SET state = ?, account_id = NULL, last_error = NULL, updated_at = ? WHERE id = ?', [$state, time(), $sid]);
    return ['ok' => true, 'state' => $state];
}
/** connections and accounts found, for the Connections screen */
function sync_status(PDO $pdo, string $uid): array
{
    sync_schema($pdo);
    $conns = [];   // one per platform: the key last seen, else the newest (several keys live after several downloads)
    foreach (sync_q($pdo, "SELECT platform, key_hint, status, client, last_seen_at, last_push_at, created_at, downloaded_at FROM sync_connections WHERE user_id = ? AND status = 'active' ORDER BY created_at", [$uid]) as $c) {
        $row = ['platform' => $c['platform'], 'hint' => $c['key_hint'], 'client' => $c['client'], 'last_seen_at' => $c['last_seen_at'] === null ? null : (int) $c['last_seen_at'], 'last_push_at' => $c['last_push_at'] === null ? null : (int) $c['last_push_at'], 'created_at' => (int) $c['created_at'], 'downloaded_at' => $c['downloaded_at'] === null ? null : (int) $c['downloaded_at']];
        $o = $conns[$c['platform']] ?? null;
        if ($o === null || [(int) $row['last_seen_at'], $row['created_at']] >= [(int) $o['last_seen_at'], $o['created_at']]) $conns[$c['platform']] = $row;
    }
    $conns = array_values($conns);
    $n = []; foreach (sync_q($pdo, 'SELECT sync_account_id, COUNT(*) n FROM sync_trades WHERE user_id = ? GROUP BY sync_account_id', [$uid]) as $r) $n[$r['sync_account_id']] = (int) $r['n'];
    $accts = [];
    foreach (sync_q($pdo, 'SELECT * FROM sync_accounts WHERE user_id = ? ORDER BY created_at, ext_id', [$uid]) as $a)
        $accts[] = ['id' => $a['id'], 'platform' => $a['platform'], 'name' => $a['ext_id'], 'info' => json_decode((string) $a['info'], true) ?: null, 'guess' => sync_guess((string) $a['ext_id'], (string) $a['platform']) ?: null,
            'state' => $a['state'], 'account_id' => $a['account_id'], 'trades' => $n[$a['id']] ?? 0, 'last_fill_at' => $a['last_fill_at'] === null ? null : (int) $a['last_fill_at'], 'error' => $a['last_error']];
    $addons = []; foreach (SYNC_ADDONS as $pl => $f) $addons[$pl] = is_file($f) ? ['url' => 'api/sync/addon?platform=' . $pl, 'size' => filesize($f), 'embed' => sync_can_embed($pl)] : null;
    return ['connections' => $conns, 'accounts' => $accts, 'addons' => $addons];
}
/**
 * Admin › Sync: per platform (traders with a key, add-on seen within 24 h, accounts linked, trades written in 7 days), then one
 * row per trader and platform (their active keys together), most recently seen first, with where the trader is: key_only (a key
 * made to be pasted, add-on never seen), downloaded (the add-on downloaded with its key, never seen; downloaded_at), no_accounts
 * (add-on seen, no account found), to_link (accounts found, none linked), error (an account in error: plan, limit,
 * account_gone), ok (linked); and the contracts received in 30 days with the instrument Sweep reads in each (a contract Sweep does
 * not recognize keeps its P&L, from the platform's point value, but not its instrument: listed apart, « unknown »).
 * Read-only; names and emails as in Admin › Users, never a key or an execution.
 */
function sync_admin(PDO $pdo, int $now = 0): array
{
    sync_schema($pdo); $now = $now ?: time();
    $acc = [];
    foreach (sync_q($pdo, 'SELECT user_id, platform, state, last_error FROM sync_accounts') as $r) {
        $a = &$acc[$r['user_id'] . '|' . $r['platform']]; $a ??= ['new' => 0, 'linked' => 0, 'ignored' => 0, 'errors' => []];
        if (isset($a[$r['state']])) $a[$r['state']]++;
        if ($r['last_error'] !== null && $r['last_error'] !== '' && !in_array($r['last_error'], $a['errors'], true)) $a['errors'][] = (string) $r['last_error'];
        unset($a);
    }
    $tr = [];
    foreach (sync_q($pdo, 'SELECT a.user_id, a.platform, COUNT(*) n, SUM(CASE WHEN t.created_at >= ? THEN 1 ELSE 0 END) n7 FROM sync_trades t JOIN sync_accounts a ON a.id = t.sync_account_id GROUP BY a.user_id, a.platform', [$now - 7 * 86400]) as $r)
        $tr[$r['user_id'] . '|' . $r['platform']] = ['n' => (int) $r['n'], 'n7' => (int) $r['n7']];
    $ctr = []; $unknown = [];
    foreach (sync_q($pdo, 'SELECT a.user_id, a.platform, f.contract, COUNT(*) n, MAX(f.received_at) last FROM sync_fills f JOIN sync_accounts a ON a.id = f.sync_account_id WHERE f.received_at >= ? GROUP BY a.user_id, a.platform, f.contract ORDER BY last DESC', [$now - 30 * 86400]) as $r) {
        [$inst, $odd] = sync_root((string) $r['contract']);
        $k = $r['user_id'] . '|' . $r['platform'];
        if (count($ctr[$k] ?? []) < 12) $ctr[$k][] = ['contract' => (string) $r['contract'], 'instrument' => $inst, 'known' => !$odd, 'n' => (int) $r['n']];
        if ($odd) $unknown[$r['platform'] . '|' . $r['contract']] = ['platform' => (string) $r['platform'], 'contract' => (string) $r['contract'], 'instrument' => $inst];
    }
    // a trader's active keys of a platform, together: the last seen (its add-on), the newest key, the last download
    $conns = [];
    foreach (sync_q($pdo, "SELECT user_id, platform, client, last_seen_at, last_push_at, created_at, downloaded_at FROM sync_connections WHERE status = 'active' ORDER BY created_at") as $c) {
        $k = $c['user_id'] . '|' . $c['platform']; $o = $conns[$k] ?? null;
        if ($o === null) { $conns[$k] = $c; continue; }
        if ((int) $c['last_seen_at'] > (int) $o['last_seen_at']) { $o['last_seen_at'] = $c['last_seen_at']; $o['client'] = $c['client']; }
        if ((int) $c['last_push_at'] > (int) $o['last_push_at']) $o['last_push_at'] = $c['last_push_at'];
        if ((int) $c['downloaded_at'] > (int) $o['downloaded_at']) $o['downloaded_at'] = $c['downloaded_at'];
        $o['created_at'] = max((int) $o['created_at'], (int) $c['created_at']);
        $conns[$k] = $o;
    }
    $conns = array_values($conns);
    $users = [];
    if ($conns) {
        $ids = array_values(array_unique(array_column($conns, 'user_id')));
        try {
            foreach (sync_q($pdo, 'SELECT * FROM users WHERE id IN (' . implode(',', array_fill(0, count($ids), '?')) . ')', $ids) as $u) $users[$u['id']] = $u;
        } catch (Throwable $e) { /* no users table (tests) */ }
    }
    $plat = []; foreach (SYNC_PLATFORMS as $p) $plat[$p] = ['traders' => 0, 'seen_24h' => 0, 'linked' => 0, 'trades_7d' => 0];
    $rows = [];
    foreach ($conns as $c) {
        $k = $c['user_id'] . '|' . $c['platform'];
        $a = $acc[$k] ?? ['new' => 0, 'linked' => 0, 'ignored' => 0, 'errors' => []]; $t = $tr[$k] ?? ['n' => 0, 'n7' => 0];
        $seen = $c['last_seen_at'] === null ? null : (int) $c['last_seen_at'];
        $dl = $c['downloaded_at'] === null ? null : (int) $c['downloaded_at'];
        $state = $seen === null ? ($dl !== null ? 'downloaded' : 'key_only') : ($a['errors'] ? 'error' : (!($a['new'] + $a['linked'] + $a['ignored']) ? 'no_accounts' : (!$a['linked'] ? 'to_link' : 'ok')));
        $u = $users[$c['user_id']] ?? [];
        $name = trim(((string) ($u['first_name'] ?? '')) . ' ' . ((string) ($u['last_name'] ?? '')));
        $rows[] = ['user_id' => (string) $c['user_id'], 'name' => $name !== '' ? $name : (string) ($u['username'] ?? $c['user_id']), 'email' => (string) ($u['email'] ?? ''),
            'team' => !empty($u['is_admin']) || !empty($u['is_internal']), 'platform' => (string) $c['platform'], 'client' => $c['client'],
            'created_at' => (int) $c['created_at'], 'downloaded_at' => $dl, 'last_seen_at' => $seen, 'last_push_at' => $c['last_push_at'] === null ? null : (int) $c['last_push_at'],
            'accounts' => ['new' => $a['new'], 'linked' => $a['linked'], 'ignored' => $a['ignored']], 'errors' => $a['errors'],
            'trades' => $t['n'], 'trades_7d' => $t['n7'], 'contracts' => $ctr[$k] ?? [], 'state' => $state];
        if (isset($plat[$c['platform']])) {
            $x = &$plat[$c['platform']]; $x['traders']++; if ($seen !== null && $now - $seen < 86400) $x['seen_24h']++; $x['linked'] += $a['linked']; $x['trades_7d'] += $t['n7']; unset($x);
        }
    }
    usort($rows, fn($x, $y) => [$y['last_seen_at'] ?? 0, $y['created_at']] <=> [$x['last_seen_at'] ?? 0, $x['created_at']]);
    return ['now' => $now, 'platforms' => $plat, 'unknown' => array_values($unknown), 'rows' => array_slice($rows, 0, 300)];
}
/** a trader deletes their Sweep account: everything of the sync goes too */
function sync_delete_user(PDO $pdo, string $uid): void
{
    foreach (['sync_fills', 'sync_trades', 'sync_accounts', 'sync_connections', 'sync_copies'] as $t) { try { sync_q($pdo, "DELETE FROM $t WHERE user_id = ?", [$uid]); } catch (Throwable $e) { /* tables not created yet */ } }
}
