<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli' && realpath((string) ($_SERVER['SCRIPT_FILENAME'] ?? '')) === realpath(__FILE__)) { http_response_code(404); exit; }
/**
 * Sweep — Plan Sync, step 2 (BRIEF_PLAN_SYNC, 13 Nov. 2026): the API the chart add-ons (Quantower, NinjaTrader 8) poll.
 * Same key as the trade sync (X-Sweep-Key, sync/sync-store.php: sync_auth), so the same access: whoever can sync can read
 * the plan. No session, no CSRF header.
 *   GET  api/plan-sync/today?instrument=NQ   the day's plan for one instrument root (MNQ reads NQ; contract month ignored):
 *                                            zones, rules, the pre-market plan (bias, scenario, rule, checklist), the limits
 *                                            Sweep already knows (read, never copied), the trader's language, `version`.
 *                                            ETag = version; If-None-Match equal → 304, no body.
 *   POST api/plan-sync/events {events: [...]} what the add-on saw: rule_triggered, zone_approached, zone_entered,
 *                                            addon_heartbeat. Each one: id (made by the add-on: a resend is ignored), at
 *                                            (UTC), instrument, price, zone / rule. A heartbeat is not stored.
 * The trading day follows New York (18:00 starts the next one; a weekend belongs to Monday: Fiche::dayOf), as the app's editor.
 * Rate limited per trader. Nothing here reaches an order, and no market data is stored outside the events.
 */
require_once __DIR__ . '/sync-store.php';

const PS_EVENT_TYPES = ['rule_triggered', 'zone_approached', 'zone_entered', 'addon_heartbeat'];
const PS_MAX_BATCH = 100;          // events per request
const PS_MAX_DAY = 500;            // events stored per trader and trading day
const PS_RATE = ['get' => [60, 60], 'events' => [20, 60]];   // requests per window (seconds), per trader
// the add-on shows this when its key no longer opens anything (brief, section 8: a clear message and the way back)
const PS_KEY_MSG = [
    'en' => 'Your Sweep key no longer works. In Sweep: Settings › Connections, download the add-on again or create a new key.',
    'fr' => 'Ta clé Sweep ne fonctionne plus. Dans Sweep : Réglages › Connexions, télécharge l’add-on de nouveau ou crée une nouvelle clé.',
    'es' => 'Tu clave de Sweep ya no funciona. En Sweep: Ajustes › Conexiones, descarga el add-on de nuevo o crea una clave nueva.',
];

function ps_schema(PDO $pdo): void
{
    static $done = []; $k = spl_object_id($pdo); if (isset($done[$k])) return; $done[$k] = true;
    sync_schema($pdo);
    $pdo->exec(sync_mysql($pdo)
        ? 'CREATE TABLE IF NOT EXISTS plan_sync_events (user_id VARCHAR(120) NOT NULL, id VARCHAR(64) NOT NULL, type VARCHAR(20) NOT NULL, day CHAR(10) NOT NULL,
             at INT NOT NULL, platform VARCHAR(20) NOT NULL, instrument VARCHAR(8) NULL, price DOUBLE NULL, zone_id VARCHAR(30) NULL, rule_id VARCHAR(30) NULL,
             received_at INT NOT NULL, PRIMARY KEY (user_id, id), INDEX ps_ev_day (user_id, day)) DEFAULT CHARSET=utf8mb4'
        : 'CREATE TABLE IF NOT EXISTS plan_sync_events (user_id TEXT NOT NULL, id TEXT NOT NULL, type TEXT NOT NULL, day TEXT NOT NULL, at INTEGER NOT NULL,
             platform TEXT NOT NULL, instrument TEXT, price REAL, zone_id TEXT, rule_id TEXT, received_at INTEGER NOT NULL, PRIMARY KEY (user_id, id))');
    if (!sync_mysql($pdo)) $pdo->exec('CREATE INDEX IF NOT EXISTS plan_sync_events_day ON plan_sync_events(user_id, day)');
    $pdo->exec(sync_mysql($pdo)
        ? 'CREATE TABLE IF NOT EXISTS plan_sync_rate (k VARCHAR(160) NOT NULL PRIMARY KEY, win INT NOT NULL, n INT NOT NULL) DEFAULT CHARSET=utf8mb4'
        : 'CREATE TABLE IF NOT EXISTS plan_sync_rate (k TEXT PRIMARY KEY, win INTEGER NOT NULL, n INTEGER NOT NULL)');
    // when an add-on last read the plan (the editor's « Synced with Quantower · 12 s ago », api/sync: plan_read_at)
    try { $pdo->query('SELECT plan_read_at FROM sync_connections LIMIT 0'); } catch (Throwable $e) { $pdo->exec('ALTER TABLE sync_connections ADD COLUMN plan_read_at INT NULL'); }
}

/** one fixed window per trader and kind: false once the window is full (one row per key, no growing table) */
function ps_rate(PDO $pdo, string $uid, string $kind, int $now): bool
{
    [$max, $len] = PS_RATE[$kind]; $k = $kind . ':' . $uid; $win = intdiv($now, $len) * $len;
    $r = sync_q($pdo, 'SELECT win, n FROM plan_sync_rate WHERE k = ?', [$k])->fetch();
    if (!$r) { try { sync_q($pdo, 'INSERT INTO plan_sync_rate (k, win, n) VALUES (?, ?, 1)', [$k, $win]); return true; } catch (Throwable $e) { $r = ['win' => $win, 'n' => 1]; } }
    if ((int) $r['win'] !== $win) { sync_q($pdo, 'UPDATE plan_sync_rate SET win = ?, n = 1 WHERE k = ?', [$win, $k]); return true; }
    if ((int) $r['n'] >= $max) return false;
    sync_q($pdo, 'UPDATE plan_sync_rate SET n = n + 1 WHERE k = ?', [$k]);
    return true;
}

/** a document of the trader (decoded), or [] */
function ps_doc(PDO $pdo, string $uid, string $col, string $id): array
{
    $d = json_decode((string) sync_doc($pdo, $uid, $col, $id), true);
    return is_array($d) ? $d : [];
}

/** the day's pre-market plan, as the add-on reminds it: bias, scenario, the day's rule, the planned setups and their criteria */
function ps_plan(array $pre, array $settings): ?array
{
    $bias = in_array($pre['bias'] ?? '', ['bullish', 'bearish', 'neutral', 'no_trade'], true) ? $pre['bias'] : null;
    $txt = fn($v, int $n) => mb_substr(trim(preg_replace('/\s+/u', ' ', strip_tags(is_scalar($v) ? (string) $v : '')) ?? ''), 0, $n);
    $setups = array_values(array_filter(array_map(fn($s) => $txt($s, 60), array_slice((array) ($pre['setups'] ?? []), 0, 10)), 'strlen'));
    // the checklist: each planned setup's own entry criteria (Settings › Setups, settings.setup_rules), read, never copied back
    $ck = []; $rules = [];
    foreach (is_array($settings['setup_rules'] ?? null) ? $settings['setup_rules'] : [] as $k => $v) $rules[mb_strtolower(trim((string) $k))] = $v;
    foreach ($setups as $s) foreach ((array) ($rules[mb_strtolower($s)] ?? []) as $c) {
        $t = $txt(is_array($c) ? ($c['text'] ?? '') : $c, 120);
        if ($t !== '' && !in_array($t, $ck, true) && count($ck) < 10) $ck[] = $t;
    }
    $o = ['bias' => $bias, 'scenario' => $txt($pre['scenario'] ?? '', 300), 'rule' => $txt($pre['rule'] ?? '', 200), 'setups' => $setups, 'checklist' => $ck];
    return $bias === null && $o['scenario'] === '' && $o['rule'] === '' && !$setups ? null : $o;
}

/** the limits Sweep already knows for the day (the day's plan, Settings › My routine, the accounts' daily limits, the account
 *  guardian), read where they live; null where api.php's game and guardian are not loaded (tests of the store) */
function ps_limits(string $uid, string $day, array $pre): ?array
{
    if (!class_exists('GameEngine', false)) return null;
    try {
        $ml = $pre['max_loss'] ?? null; $planLoss = is_numeric($ml) ? (int) round((float) $ml * 100) : 0;
        $planTrades = isset($pre['max_trades']) && is_numeric($pre['max_trades']) ? (int) $pre['max_trades'] : 0;
        $l = GameEngine::dayLimits($uid, $day, max(0, $planLoss), max(0, $planTrades));
        $o = ['max_loss_c' => $l['loss_c'] ?: null, 'max_trades' => $l['trades'] ?: null, 'losses_in_row' => $l['losses'] ?: null, 'stopped' => null, 'accounts' => []];
        if (function_exists('guard_state')) {
            $lock = guard_stop_on($uid) ? guard_lock($uid) : null;
            $o['stopped'] = $lock ? (string) $lock['why'] : null;
            $g = guard_state($uid, guard_allowed($uid, 'guard_all'), ['stopped' => $lock ? ['*' => true] : []]);
            foreach ($g['accounts'] as $a) if (empty($a['locked'])) $o['accounts'][] = ['name' => mb_substr((string) $a['name'], 0, 60), 'level' => $a['level'], 'left_c' => $a['left_c']];
        }
        return $o;
    } catch (Throwable $e) { error_log('[Sweep plan-sync] limits: ' . $e->getMessage()); return null; }
}

/**
 * The day's plan for the add-on. $inst: an instrument as the chart names it ('' = every instrument). `version` changes when
 * anything in it changes (it is the ETag); `empty` when there is nothing to draw (the add-on says it once).
 */
function ps_today(PDO $pdo, string $uid, string $day, string $inst = ''): array
{
    $j = ps_doc($pdo, $uid, 'journals', $day);
    $c = class_exists('ChartPlan') && is_array($j['chart'] ?? null) ? (ChartPlan::normalize($j['chart']) ?? ['zones' => [], 'rules' => [], 'updated_at' => 0]) : ['zones' => [], 'rules' => [], 'updated_at' => 0];
    $root = $inst !== '' && class_exists('ChartPlan') ? ChartPlan::root($inst) : '';
    $zones = array_values(array_filter($c['zones'], fn($z) => $root === '' || $z['instrument'] === $root));
    $ids = array_flip(array_column($zones, 'id'));
    $rules = array_values(array_filter($c['rules'], fn($r) => $r['trigger'] === 'time' || isset($ids[$r['zone'] ?? ''])));
    $pre = is_array($j['pre'] ?? null) ? $j['pre'] : [];
    $settings = (array) (ps_doc($pdo, $uid, 'meta', 'settings'));
    $lang = 'en';
    try { $l = sync_q($pdo, 'SELECT lang FROM users WHERE id = ?', [$uid])->fetchColumn(); $l = strtolower(substr((string) $l, 0, 2)); if (in_array($l, ['en', 'fr', 'es'], true)) $lang = $l; } catch (Throwable $e) { /* no lang column (tests) */ }
    $o = ['day' => $day, 'instrument' => $root !== '' ? $root : null, 'lang' => $lang, 'empty' => !$zones && !$rules,
        'zones' => $zones, 'rules' => $rules, 'plan' => ps_plan($pre, $settings), 'limits' => ps_limits($uid, $day, $pre), 'updated_at' => $zones || $rules ? (int) $c['updated_at'] : null];
    $o['version'] = substr(hash('sha256', json_encode($o, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES)), 0, 16);
    return $o;
}

/** an add-on read the plan (or said it is alive): the editor's « Synced … ago » */
function ps_seen(PDO $pdo, array $conn, int $now): void
{
    sync_q($pdo, 'UPDATE sync_connections SET plan_read_at = ?, last_seen_at = ? WHERE id = ?', [$now, $now, $conn['id']]);
}

/** a moment the add-on sends: ISO 8601 UTC ('2026-11-13T14:42:05Z', '…05.123Z') or epoch milliseconds; null otherwise */
function ps_at($v): ?int
{
    if (is_int($v) || (is_string($v) && ctype_digit($v))) { $n = (int) $v; return $n > 1000000000000 ? intdiv($n, 1000) : null; }
    if (is_string($v) && preg_match('/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,6})?Z$/', $v)) { $t = strtotime($v); return $t === false ? null : $t; }
    return null;
}

/**
 * The events of one request: each one checked, kept once (its id), heartbeats only mark the add-on as seen. Returns
 * {accepted, duplicates, rejected} — a rejected event (unknown type, no id, a moment more than 7 days old or 5 minutes ahead,
 * the day's cap reached) is dropped, never retried by the add-on.
 */
function ps_events(PDO $pdo, array $conn, array $events, int $now, callable $dayOf): array
{
    $uid = (string) $conn['user_id']; $acc = 0; $dup = 0; $bad = 0; $per = [];
    foreach ($events as $e) {
        if (!is_array($e)) { $bad++; continue; }
        $type = (string) ($e['type'] ?? ''); $id = (string) ($e['id'] ?? ''); $at = ps_at($e['at'] ?? null);
        if (!in_array($type, PS_EVENT_TYPES, true) || !preg_match('/^[A-Za-z0-9_.:-]{8,64}$/', $id) || $at === null || $at < $now - 7 * 86400 || $at > $now + 300) { $bad++; continue; }
        if ($type === 'addon_heartbeat') { $acc++; continue; }
        $day = $dayOf($at);
        $per[$day] ??= (int) sync_q($pdo, 'SELECT COUNT(*) FROM plan_sync_events WHERE user_id = ? AND day = ?', [$uid, $day])->fetchColumn();
        if (sync_q($pdo, 'SELECT 1 FROM plan_sync_events WHERE user_id = ? AND id = ?', [$uid, $id])->fetchColumn()) { $dup++; continue; }
        if ($per[$day] >= PS_MAX_DAY) { $bad++; continue; }
        $inst = (string) ($e['instrument'] ?? ''); $inst = $inst !== '' && class_exists('ChartPlan') ? ChartPlan::root($inst) : mb_substr(strtoupper($inst), 0, 8);
        $px = $e['price'] ?? null; $px = is_numeric($px) && is_finite((float) $px) ? (float) $px : null;
        $ref = fn($v) => is_string($v) && preg_match('/^[A-Za-z0-9_-]{1,30}$/', $v) ? $v : null;
        try {
            sync_q($pdo, 'INSERT INTO plan_sync_events (user_id, id, type, day, at, platform, instrument, price, zone_id, rule_id, received_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                [$uid, $id, $type, $day, $at, (string) $conn['platform'], $inst !== '' ? $inst : null, $px, $ref($e['zone'] ?? null), $ref($e['rule'] ?? null), $now]);
            $acc++; $per[$day]++;
        } catch (PDOException $x) { $dup++; }   // the same id sent twice at the same moment
    }
    if ($acc || $dup) ps_seen($pdo, $conn, $now);
    return ['accepted' => $acc, 'duplicates' => $dup, 'rejected' => $bad];
}

/** the trader's events of a day, oldest first (step 5 shows them) */
function ps_day_events(PDO $pdo, string $uid, string $day): array
{
    ps_schema($pdo);
    return sync_q($pdo, 'SELECT id, type, at, platform, instrument, price, zone_id, rule_id FROM plan_sync_events WHERE user_id = ? AND day = ? ORDER BY at, id', [$uid, $day])->fetchAll();
}

function ps_delete_user(PDO $pdo, string $uid): void
{
    try { sync_q($pdo, 'DELETE FROM plan_sync_events WHERE user_id = ?', [$uid]); sync_q($pdo, 'DELETE FROM plan_sync_rate WHERE k IN (?, ?)', ['get:' . $uid, 'events:' . $uid]); }
    catch (Throwable $e) { /* tables not created yet */ }
}

/* ---------------- HTTP ---------------- */

/** the connection behind the request's key, or a 401 with the way back (in the add-on's three languages) */
function ps_conn(PDO $pdo): array
{
    $ip = 'syncip:' . hash('sha256', client_ip());
    throttle([$ip], 20, 900);   // wrong keys from one address, as api/sync/push
    $conn = sync_auth($pdo, trim((string) ($_SERVER['HTTP_X_SWEEP_KEY'] ?? '')));
    if (!$conn) { record_attempt([$ip]); json_out(401, ['error' => PS_KEY_MSG['en'], 'code' => 'key', 'messages' => PS_KEY_MSG]); }
    $cp = sync_client_platform((string) ($_SERVER['HTTP_X_SWEEP_CLIENT'] ?? ''));
    if ($cp !== null && $cp !== $conn['platform']) json_out(401, ['error' => 'This key is for ' . SYNC_NAMES[$conn['platform']] . '. Create a ' . SYNC_NAMES[$cp] . ' key in Sweep: Settings, Connections.', 'code' => 'platform', 'messages' => PS_KEY_MSG]);
    ps_schema($pdo);
    return $conn;
}

function ps_route(string $route, string $method): void
{
    $pdo = db();
    $kind = $route === 'api/plan-sync/today' ? 'get' : ($route === 'api/plan-sync/events' ? 'events' : null);
    if ($kind === null) json_out(404, ['error' => 'not found']);
    if (($kind === 'get' && $method !== 'GET') || ($kind === 'events' && $method !== 'POST')) json_out(405, ['error' => 'method not allowed']);
    $conn = ps_conn($pdo);
    $now = class_exists('GameEngine', false) ? GameEngine::ts() : time();
    if (!ps_rate($pdo, (string) $conn['user_id'], $kind, time())) { header('Retry-After: ' . PS_RATE[$kind][1]); json_out(429, ['error' => 'Too many requests. Wait a minute.', 'code' => 'rate']); }
    if ($kind === 'get') {
        $p = ps_today($pdo, (string) $conn['user_id'], Fiche::dayOf($now), substr((string) ($_GET['instrument'] ?? ''), 0, 20));
        ps_seen($pdo, $conn, time());
        $tag = '"' . $p['version'] . '"';
        header('ETag: ' . $tag); header('Cache-Control: private, no-cache');
        // W/ and Apache's « -gzip » (mod_deflate changes the ETag of a compressed answer) are the same version
        $inm = array_map(fn($x) => preg_replace(['#^W/#', '#-(gzip|br)"$#'], ['', '"'], trim($x)), explode(',', (string) ($_SERVER['HTTP_IF_NONE_MATCH'] ?? '')));
        if (in_array($tag, $inm, true)) { http_response_code(304); exit; }
        http_response_code(200); header('Content-Type: application/json; charset=utf-8');
        echo json_encode($p, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES); exit;
    }
    $b = body_json(262144);
    $ev = $b['events'] ?? null;
    if (!is_array($ev) || ($ev !== [] && array_keys($ev) !== range(0, count($ev) - 1))) json_out(400, ['error' => 'events must be a list.']);
    if (count($ev) > PS_MAX_BATCH) json_out(413, ['error' => 'Too many events in one request.', 'max' => PS_MAX_BATCH]);
    try { $r = sync_tx($pdo, fn() => ps_events($pdo, $conn, $ev, time(), fn(int $at) => Fiche::dayOf($at))); }
    catch (Throwable $e) { error_log('[Sweep plan-sync] events: ' . $e->getMessage()); json_out(503, ['error' => 'Not saved. Send again.', 'code' => 'retry']); }
    json_out(200, ['ok' => true] + $r);
}
