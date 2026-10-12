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

const SYNC_PLATFORMS = ['ninjatrader'];
const SYNC_MAX_FILLS = 500;      // executions per push
const SYNC_MAX_ACCOUNTS = 50;    // accounts described per push
const SYNC_MATCH_MIN = 2;        // minutes between a synced entry and a trade typed by hand
const SYNC_ADDON = __DIR__ . '/addon/SweepSync.zip';   // the NinjaTrader 8 add-on (step 4), downloaded through api/sync/addon

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
    ];
    foreach ($sql as $s) $pdo->exec($s);
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

/** a new key for a platform, shown once; the previous one stops working at once */
function sync_new_key(PDO $pdo, string $uid, string $platform): array
{
    sync_schema($pdo);
    $key = 'swk_' . bin2hex(random_bytes(20)); $now = time(); $id = 'sc_' . bin2hex(random_bytes(8));
    sync_q($pdo, "UPDATE sync_connections SET status = 'revoked', revoked_at = ? WHERE user_id = ? AND platform = ? AND status = 'active'", [$now, $uid, $platform]);
    sync_q($pdo, 'INSERT INTO sync_connections (id, user_id, platform, key_hash, key_hint, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
        [$id, $uid, $platform, hash('sha256', $key), substr($key, -4), 'active', $now]);
    return ['id' => $id, 'platform' => $platform, 'key' => $key, 'hint' => substr($key, -4)];
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
function sync_guess(string $name): array
{
    $u = strtoupper($name);
    if (str_starts_with($u, 'PA-APEX')) return ['firm' => 'apex', 'phase' => 'funded'];
    if (str_starts_with($u, 'APEX-')) return ['firm' => 'apex', 'phase' => 'eval'];
    if (preg_match('/^(SIM\d*|PLAYBACK\d*|BACKTEST)$/', $u)) return ['sim' => true];
    return [];
}
function sync_account_row(PDO $pdo, string $uid, string $platform, string $name, ?array $info, int $now): array
{
    $row = sync_q($pdo, 'SELECT * FROM sync_accounts WHERE user_id = ? AND platform = ? AND ext_id = ?', [$uid, $platform, $name])->fetch();
    $js = $info !== null ? json_encode($info, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES) : null;
    if (!$row) {
        $id = 'sa_' . bin2hex(random_bytes(8));
        try {
            // NinjaTrader's own simulation accounts (Sim101, Playback101) start « ignored »: one tap in the list links them
            sync_q($pdo, 'INSERT INTO sync_accounts (id, user_id, platform, ext_id, info, state, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)', [$id, $uid, $platform, $name, $js, empty(sync_guess($name)['sim']) ? 'new' : 'ignored', $now, $now]);
        } catch (Throwable $e) { /* added by a push running at the same time */ }
        return sync_q($pdo, 'SELECT * FROM sync_accounts WHERE user_id = ? AND platform = ? AND ext_id = ?', [$uid, $platform, $name])->fetch();
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
        $rows = []; foreach ($names as $n => $info) $rows[$n] = sync_account_row($pdo, $uid, $platform, $n, $info, $now);
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
    $states = []; foreach ($rows as $n => $r) $states[] = ['name' => $n, 'state' => $r['state']];
    return ['ok' => true, 'received' => count($fills)] + $stats + ['trades' => $written, 'accounts' => $states];
}

/* ---------------- building and writing the trades ---------------- */

/** a trade typed by hand that is the same trade: same instrument, side and contracts, entry within SYNC_MATCH_MIN minutes */
function sync_match(array $t, array &$manual): ?string
{
    $at = strtotime($t['executions'][0]['t'] . ' America/New_York');
    $best = null; $bestD = PHP_INT_MAX;
    foreach ($manual as $id => $m) {
        if (($m['instrument'] ?? '') !== $t['instrument'] || ($m['direction'] ?? '') !== $t['direction'] || (int) ($m['contracts'] ?? 0) !== (int) $t['contracts'] || $m['_at'] === null) continue;
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
        $now = time(); $iso = sync_iso(); $creates = 0;
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
        }
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
        $byDay = []; foreach ($events as $ev) $byDay[($ev[1]['date'] ?? '') . '|' . $accountId] = $ev;
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
    $conns = [];
    foreach (sync_q($pdo, "SELECT platform, key_hint, status, client, last_seen_at, last_push_at, created_at FROM sync_connections WHERE user_id = ? AND status = 'active' ORDER BY created_at", [$uid]) as $c)
        $conns[] = ['platform' => $c['platform'], 'hint' => $c['key_hint'], 'client' => $c['client'], 'last_seen_at' => $c['last_seen_at'] === null ? null : (int) $c['last_seen_at'], 'last_push_at' => $c['last_push_at'] === null ? null : (int) $c['last_push_at'], 'created_at' => (int) $c['created_at']];
    $n = []; foreach (sync_q($pdo, 'SELECT sync_account_id, COUNT(*) n FROM sync_trades WHERE user_id = ? GROUP BY sync_account_id', [$uid]) as $r) $n[$r['sync_account_id']] = (int) $r['n'];
    $accts = [];
    foreach (sync_q($pdo, 'SELECT * FROM sync_accounts WHERE user_id = ? ORDER BY created_at, ext_id', [$uid]) as $a)
        $accts[] = ['id' => $a['id'], 'platform' => $a['platform'], 'name' => $a['ext_id'], 'info' => json_decode((string) $a['info'], true) ?: null, 'guess' => sync_guess((string) $a['ext_id']) ?: null,
            'state' => $a['state'], 'account_id' => $a['account_id'], 'trades' => $n[$a['id']] ?? 0, 'last_fill_at' => $a['last_fill_at'] === null ? null : (int) $a['last_fill_at'], 'error' => $a['last_error']];
    return ['connections' => $conns, 'accounts' => $accts, 'addon' => is_file(SYNC_ADDON) ? ['url' => 'api/sync/addon', 'size' => filesize(SYNC_ADDON)] : null];
}
/** a trader deletes their Sweep account: everything of the sync goes too */
function sync_delete_user(PDO $pdo, string $uid): void
{
    foreach (['sync_fills', 'sync_trades', 'sync_accounts', 'sync_connections'] as $t) { try { sync_q($pdo, "DELETE FROM $t WHERE user_id = ?", [$uid]); } catch (Throwable $e) { /* tables not created yet */ } }
}
