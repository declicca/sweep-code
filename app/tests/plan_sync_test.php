<?php
declare(strict_types=1);
/**
 * Sweep — Plan Sync step 2, the add-ons' API on a throwaway SQLite database (never the live one):   php tests/plan_sync_test.php
 * The day's plan for one instrument (MNQ reads NQ, time rules for every chart), its version (the ETag), the pre-market plan and
 * its checklist, the trader's language, an empty day; events kept once (a resend ignored), checked (type, id, moment), the
 * day's cap, a heartbeat not stored; the New York trading day at 17:59 / 18:00 and on a weekend; the rate limit; « Synced … ago »
 * in api/sync; a deleted trader's events gone.
 */
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
$app = dirname(__DIR__);
$tmp = sys_get_temp_dir() . '/sweep-ps-' . bin2hex(random_bytes(4)); mkdir($tmp);
$pdo = new PDO('sqlite:' . $tmp . '/t.db', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC]);
$pdo->exec('CREATE TABLE documents (user_id TEXT NOT NULL, collection TEXT NOT NULL, id TEXT NOT NULL, data TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL, PRIMARY KEY (user_id, collection, id))');
$pdo->exec('CREATE TABLE users (id TEXT PRIMARY KEY, disabled INTEGER NOT NULL DEFAULT 0, lang TEXT)');
$pdo->exec("INSERT INTO users (id, lang) VALUES ('u1', 'fr-CA'), ('u2', NULL)");
require $app . '/game/fiche.php';
require $app . '/game/chart-plan.php';
require $app . '/sync/plan-sync.php';

$n = 0; $f = 0;
function ok($c, $what) { global $n, $f; $n++; if (!$c) $f++; echo ($c ? 'ok   ' : 'FAIL ') . $what . "\n"; }
$put = function (string $uid, string $col, string $id, array $d) use ($pdo) {
    $pdo->prepare('INSERT OR REPLACE INTO documents (user_id, collection, id, data, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)')->execute([$uid, $col, $id, json_encode($d, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES), '2026-11-01T00:00:00Z', '2026-11-01T00:00:00Z']);
};
$NY = fn(string $s) => (new DateTimeImmutable($s, new DateTimeZone('America/New_York')))->getTimestamp();
ps_schema($pdo);
$k = sync_new_key($pdo, 'u1', 'quantower'); $conn = sync_auth($pdo, $k['key']);

// 1. the New York trading day (the editor's day, Fiche::dayOf)
ok(Fiche::dayOf($NY('2026-11-12 17:59')) === '2026-11-12' && Fiche::dayOf($NY('2026-11-12 18:00')) === '2026-11-13', '1 17:59 New York is still Thursday\'s plan, 18:00 is Friday\'s');
ok(Fiche::dayOf($NY('2026-11-13 18:00')) === '2026-11-16' && Fiche::dayOf($NY('2026-11-15 18:30')) === '2026-11-16', '1 Friday 18:00 and Sunday evening: Monday\'s plan');

// 2. the day's plan
$day = '2026-11-13';
$chart = ['zones' => [
    ['id' => 'pdh', 'instrument' => 'NQ', 'type' => 'level', 'price' => 21290.25, 'label' => 'PDH', 'role' => 'resistance', 'bias' => 'short', 'note' => 'Sweep then back under', 'proximity_ticks' => 40],
    ['id' => 'buy', 'instrument' => 'NQ', 'type' => 'zone', 'high' => 21200, 'low' => 21180, 'label' => 'Buy zone', 'role' => 'support', 'bias' => 'long', 'proximity_ticks' => 40],
    ['id' => 'es1', 'instrument' => 'ES', 'type' => 'level', 'price' => 5800.25, 'label' => 'ONH', 'role' => 'target', 'proximity_ticks' => 8],
], 'rules' => [
    ['id' => 'r1', 'trigger' => 'sweep', 'zone' => 'pdh', 'tf' => '5m', 'action' => 'plan', 'message' => 'Wait for the reclaim'],
    ['id' => 'r2', 'trigger' => 'enter', 'zone' => 'es1', 'action' => 'alert'],
    ['id' => 'r3', 'trigger' => 'time', 'time' => '11:00', 'action' => 'limit'],
], 'updated_at' => 1794600000];
$put('u1', 'journals', $day, ['id' => $day, 'chart' => $chart, 'pre' => ['bias' => 'bearish', 'scenario' => 'Short the PDH sweep', 'rule' => 'No trade before 9:45', 'setups' => ['ORB', 'Reclaim'], 'max_loss' => '400', 'max_trades' => 3]]);
$put('u1', 'meta', 'settings', ['setup_rules' => ['orb' => [['id' => 'a', 'text' => 'Break of the 15-minute range'], ['id' => 'b', 'text' => 'Volume above average']], 'Reclaim' => [['id' => 'c', 'text' => 'Close back above the level']]]]);
$p = ps_today($pdo, 'u1', $day, 'MNQZ6');
ok($p['instrument'] === 'NQ' && array_column($p['zones'], 'id') === ['pdh', 'buy'], '2 an MNQ chart reads the NQ zones only (the ES level left out)');
ok(array_column($p['rules'], 'id') === ['r1', 'r3'], '2 its rules: those of its zones, and the time rule (every chart)');
ok($p['zones'][0]['price'] === 21290.25 && $p['zones'][0]['proximity_ticks'] === 40 && $p['rules'][0]['tf'] === '5m' && $p['rules'][0]['message'] === 'Wait for the reclaim', '2 a zone and a rule as the editor saved them');
ok($p['plan'] === ['bias' => 'bearish', 'scenario' => 'Short the PDH sweep', 'rule' => 'No trade before 9:45', 'setups' => ['ORB', 'Reclaim'], 'checklist' => ['Break of the 15-minute range', 'Volume above average', 'Close back above the level']], '2 the pre-market plan: bias, scenario, rule, setups, the setups\' own criteria as the checklist');
ok($p['lang'] === 'fr' && $p['day'] === $day && $p['empty'] === false && $p['updated_at'] === 1794600000 && $p['limits'] === null, '2 the trader\'s language, the day, updated_at (limits: read in the app, not loaded here)');
ok(preg_match('/^[0-9a-f]{16}$/', $p['version']) === 1 && ps_today($pdo, 'u1', $day, 'NQ')['version'] === $p['version'], '2 a version (the ETag), the same for the same plan (NQ = MNQ)');
$all = ps_today($pdo, 'u1', $day);
ok($all['instrument'] === null && count($all['zones']) === 3 && count($all['rules']) === 3 && $all['version'] !== $p['version'], '2 no instrument: every zone and rule, its own version');
$c2 = $chart; $c2['zones'][1]['high'] = 21205; $c2['updated_at'] = 1794600100;
$put('u1', 'journals', $day, ['id' => $day, 'chart' => $c2, 'pre' => ['bias' => 'bearish', 'scenario' => 'Short the PDH sweep', 'rule' => 'No trade before 9:45', 'setups' => ['ORB', 'Reclaim']]]);
$p2 = ps_today($pdo, 'u1', $day, 'MNQ');
ok($p2['version'] !== $p['version'] && $p2['zones'][1]['high'] === 21205.0, '2 a zone moved during the session: a new version (the add-on gets it at its next poll)');
ok(ps_today($pdo, 'u1', $day, 'MNQ')['version'] === $p2['version'], '2 nothing changed: the same version (the poll gets a 304)');
$cl = ps_today($pdo, 'u1', $day, 'CL');
ok($cl['empty'] === false && $cl['zones'] === [] && array_column($cl['rules'], 'id') === ['r3'], '2 an instrument without zones: nothing to draw, the time rule still there (so not « no plan »)');
$e = ps_today($pdo, 'u2', $day, 'NQ');
ok($e['empty'] === true && $e['zones'] === [] && $e['rules'] === [] && $e['plan'] === null && $e['lang'] === 'en' && $e['updated_at'] === null, '2 no plan today: empty (the add-on says it once), English by default');
$put('u1', 'journals', $day, ['id' => $day, 'chart' => ['zones' => [['id' => 'x', 'instrument' => 'NQ', 'type' => 'level', 'price' => 'nope']], 'rules' => [['trigger' => 'boom']]]]);
ok(ps_today($pdo, 'u1', $day, 'NQ')['zones'] === [], '2 a stored plan read through the same model (a zone without a price left out)');
$put('u1', 'journals', $day, ['id' => $day, 'chart' => $chart]);

// 3. events
$now = $NY('2026-11-13 10:00');
$ev = fn(string $id, string $type, string $at, array $x = []) => $x + ['id' => $id, 'type' => $type, 'at' => gmdate('Y-m-d\TH:i:s\Z', $NY($at)), 'instrument' => 'MNQZ6', 'price' => 21291.5];
$batch = [
    $ev('ev-00000001', 'zone_approached', '2026-11-13 09:41:10', ['zone' => 'pdh']),
    $ev('ev-00000002', 'zone_entered', '2026-11-13 09:42:00', ['zone' => 'pdh']),
    $ev('ev-00000003', 'rule_triggered', '2026-11-13 09:45:00', ['zone' => 'pdh', 'rule' => 'r1']),
    $ev('ev-00000004', 'addon_heartbeat', '2026-11-13 09:45:30'),
];
$dayOf = fn(int $at) => Fiche::dayOf($at);
$r = ps_events($pdo, $conn, $batch, $now, $dayOf);
ok($r === ['accepted' => 4, 'duplicates' => 0, 'rejected' => 0], '3 a batch of 4 events: all accepted');
$rows = ps_day_events($pdo, 'u1', $day);
ok(count($rows) === 3 && $rows[2]['type'] === 'rule_triggered' && $rows[2]['rule_id'] === 'r1' && $rows[2]['zone_id'] === 'pdh' && $rows[2]['instrument'] === 'NQ' && (float) $rows[2]['price'] === 21291.5 && $rows[2]['platform'] === 'quantower', '3 stored: instrument root, price, zone, rule, platform; the heartbeat not stored');
$r = ps_events($pdo, $conn, $batch, $now + 30, $dayOf);
ok($r === ['accepted' => 1, 'duplicates' => 3, 'rejected' => 0] && count(ps_day_events($pdo, 'u1', $day)) === 3, '3 the same batch sent again (network back): nothing doubled');
$r = ps_events($pdo, $conn, [
    $ev('ev-00000010', 'order_sent', '2026-11-13 09:50:00'), ['type' => 'zone_entered', 'at' => gmdate('Y-m-d\TH:i:s\Z', $now)], $ev('short', 'zone_entered', '2026-11-13 09:50:00'),
    $ev('ev-00000011', 'zone_entered', '2026-11-03 09:50:00'), $ev('ev-00000012', 'zone_entered', '2026-11-13 10:10:00'), ['id' => 'ev-00000013', 'type' => 'zone_entered', 'at' => 'yesterday'], 'x',
], $now, $dayOf);
ok($r === ['accepted' => 0, 'duplicates' => 0, 'rejected' => 7], '3 refused: an unknown type (no order ever), no id, a short id, 10 days old, 10 minutes ahead, a wrong moment, not an object');
ok(ps_events($pdo, $conn, [['id' => 'ev-00000020', 'type' => 'zone_entered', 'at' => ($now - 60) * 1000, 'zone' => 'buy', 'price' => 'NaN']], $now, $dayOf)['accepted'] === 1
   && array_slice(ps_day_events($pdo, 'u1', $day), -1)[0]['price'] === null, '3 a moment in epoch milliseconds accepted; a price that is not a number left empty');
$late = ps_events($pdo, $conn, [$ev('ev-00000030', 'zone_entered', '2026-11-13 18:05:00')], $NY('2026-11-13 18:06'), $dayOf);
ok($late['accepted'] === 1 && count(ps_day_events($pdo, 'u1', '2026-11-16')) === 1, '3 an event at 18:05 New York on a Friday counts on Monday\'s plan');
$many = []; for ($i = 0; $i < PS_MAX_DAY + 5; $i++) $many[] = $ev(sprintf('cap-%08d', $i), 'zone_approached', '2026-11-12 10:00:00');
$r = ps_events($pdo, $conn, $many, $NY('2026-11-12 11:00'), $dayOf);
ok($r['accepted'] === PS_MAX_DAY && $r['rejected'] === 5, '3 the day\'s cap: ' . PS_MAX_DAY . ' events kept per day, the rest dropped');

// 4. « Synced with Quantower · 12 s ago » (api/sync), the rate limit, deletion
$st = sync_status($pdo, 'u1');
ok($st['plan_read_by'] === 'quantower' && $st['plan_read_at'] > 0 && sync_status($pdo, 'u2')['plan_read_at'] === null, '4 api/sync says which add-on read the plan last, and when; nothing for a trader without one');
ps_seen($pdo, $conn, 1794700000);
ok(sync_status($pdo, 'u1')['plan_read_at'] === 1794700000, '4 a read updates it');
$t0 = 1794700020; $okN = 0; for ($i = 0; $i < 61; $i++) if (ps_rate($pdo, 'u1', 'get', $t0)) $okN++;
ok($okN === 60 && !ps_rate($pdo, 'u1', 'get', $t0 + 30) && ps_rate($pdo, 'u1', 'get', $t0 + 60) && ps_rate($pdo, 'u2', 'get', $t0), '4 reads: 60 a minute per trader, the next minute open again, another trader not touched');
$okE = 0; for ($i = 0; $i < 21; $i++) if (ps_rate($pdo, 'u1', 'events', $t0)) $okE++;
ok($okE === 20, '4 event batches: 20 a minute per trader');
ok((int) $pdo->query('SELECT COUNT(*) FROM plan_sync_rate')->fetchColumn() === 3, '4 the limit keeps one row per trader and kind (the table does not grow)');
ps_delete_user($pdo, 'u1');
ok((int) $pdo->query("SELECT COUNT(*) FROM plan_sync_events WHERE user_id = 'u1'")->fetchColumn() === 0 && (int) $pdo->query("SELECT COUNT(*) FROM plan_sync_rate WHERE k LIKE '%:u1'")->fetchColumn() === 0, '4 a deleted trader: events and limits gone');

// 5. nothing reaches an order: the API's code names none of it
$src = (string) file_get_contents($app . '/sync/plan-sync.php');
ok(!preg_match('/\b(place_?order|submit_?order|cancel_?order|close_?position|flatten)\b/i', $src), '5 no order, no position anywhere in the API');

array_map('unlink', glob($tmp . '/*')); @rmdir($tmp);
echo "\n" . ($f ? "$f failed of $n" : "all $n passed") . "\n";
exit($f ? 1 : 0);
