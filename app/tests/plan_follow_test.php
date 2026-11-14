<?php
declare(strict_types=1);
/**
 * Sweep — Plan Sync step 5, was the plan followed?   php tests/plan_follow_test.php
 * ChartPlan::follow: a trade is « in the plan » when its entry is in a zone of its instrument (MNQ reads NQ; a zone between
 * its bounds, a level within its approach distance in ticks) and in the direction planned there (the zone's bias, else the
 * day's, else either way); otherwise « off plan »; no zone → nothing to say; a trade without entry or direction not counted.
 * ps_day (api/sync/plan-day) on a throwaway SQLite database: the day's events in order, the trades of that day only, demo
 * trades left out, another trader's events never shown.
 */
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
$app = dirname(__DIR__);
require $app . '/game/fiche.php';
require $app . '/game/chart-plan.php';
require $app . '/sync/plan-sync.php';
$pass = 0; $fail = 0;
$ok = function (bool $c, string $what) use (&$pass, &$fail) { echo ($c ? 'ok   ' : 'FAIL ') . $what . "\n"; $c ? $pass++ : $fail++; };

$chart = ['zones' => [
    ['id' => 'pdh', 'instrument' => 'NQ', 'type' => 'level', 'price' => 21290.25, 'label' => 'PDH', 'role' => 'resistance', 'bias' => 'short', 'proximity_ticks' => 40],
    ['id' => 'buy', 'instrument' => 'NQ', 'type' => 'zone', 'high' => 21200, 'low' => 21180, 'label' => 'Buy zone', 'role' => 'support'],
    ['id' => 'onh', 'instrument' => 'ES', 'type' => 'level', 'price' => 5800.25, 'label' => 'ONH', 'role' => 'target'],
], 'rules' => []];
$T = fn(string $id, string $dir, $entry, string $inst = 'NQ', array $x = []) => ['id' => $id, 'direction' => $dir, 'entry' => $entry, 'instrument' => $inst] + $x;

// 1. the zones and the direction
$f = ChartPlan::follow($chart, ['bias' => 'bullish'], [
    $T('a', 'long', 21190),                 // in the buy zone, long, the day bullish (the zone has no bias)
    $T('b', 'short', 21285.5, 'MNQZ6'),     // 19 ticks from PDH on MNQ (its bias: short)
    $T('c', 'long', 21280),                 // at PDH but long: against the zone's own bias
    $T('d', 'short', 21190),                // in the buy zone but short, the day bullish
    $T('e', 'long', 21240),                 // between the zones
    $T('f', 'long', 21280.25),              // 40 ticks under PDH exactly, long: against its bias
]);
$ok($f['n'] === 6 && $f['in'] === 2, "1 2 of 6 trades in the plan ({$f['in']} of {$f['n']})");
$ok($f['trades']['a'] === ['in' => true, 'zone' => 'buy'], '1 in the zone, in the day\'s direction: in (buy)');
$ok($f['trades']['b'] === ['in' => true, 'zone' => 'pdh'], '1 MNQ reads NQ\'s levels, within the approach distance, the zone\'s bias: in (pdh)');
$ok(!$f['trades']['c']['in'] && !$f['trades']['d']['in'] && !$f['trades']['e']['in'], '1 against the zone\'s bias, against the day\'s bias, between the zones: off plan');
$z = ChartPlan::follow($chart, [], [$T('g', 'short', 21190), $T('h', 'long', 21190)]);
$ok($z['in'] === 2, '1 a zone without a bias on a day without one: either direction is in the plan');
$n = ChartPlan::follow($chart, ['bias' => 'neutral'], [$T('i', 'short', 21180)]);
$ok($n['in'] === 1, '1 a neutral day: the zone\'s bounds are in (21180 = its low)');
// 2. a level's distance: its own ticks, else the instrument's default (ES 8 ticks = 2 points)
$d = ChartPlan::follow($chart, [], [$T('j', 'long', 5802.25, 'MES'), $T('k', 'long', 5802.5, 'ES')]);
$ok($d['trades']['j']['in'] && !$d['trades']['k']['in'], '2 ES level without its own distance: 8 ticks (2 points) by default — 5802.25 in, 5802.50 out');
$w = ChartPlan::follow(['zones' => [['id' => 'x', 'instrument' => 'NQ', 'type' => 'level', 'price' => 21000, 'label' => 'X', 'proximity_ticks' => 4]]], [], [$T('l', 'long', 21001), $T('m', 'long', 21001.25)]);
$ok($w['trades']['l']['in'] && !$w['trades']['m']['in'], '2 a level\'s own distance: 4 ticks = 1 point on NQ');
// 3. what is not counted, and no zone
$e = ChartPlan::follow($chart, [], [$T('n', '', 21190), $T('o', 'long', null), ['id' => 'p', 'direction' => 'long', 'entry' => 21190, 'untracked' => true], $T('q', 'long', 'x'), $T('r', 'long', 21190, 'GC')]);
$ok($e['n'] === 1 && $e['in'] === 0, "3 no direction, no entry, « trades not detailed », a bad price: not counted; a gold trade with NQ zones: off plan ({$e['in']} of {$e['n']})");
$ok(ChartPlan::follow(['zones' => [], 'rules' => [['id' => 'r', 'trigger' => 'time', 'time' => '09:30']]], [], [$T('s', 'long', 1)]) === null, '3 no zone that day: nothing to compare (null)');
$ok(ChartPlan::follow(null, [], []) === null, '3 no chart plan: null');
$ok(ChartPlan::follow($chart, [], []) === ['n' => 0, 'in' => 0, 'trades' => []], '3 zones but no trade yet: 0 of 0');

// 4. ps_day: the app's read of a day
$tmp = sys_get_temp_dir() . '/sweep-pf-' . bin2hex(random_bytes(4)); mkdir($tmp);
$pdo = new PDO('sqlite:' . $tmp . '/t.db', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC]);
$pdo->exec('CREATE TABLE documents (user_id TEXT NOT NULL, collection TEXT NOT NULL, id TEXT NOT NULL, data TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL, PRIMARY KEY (user_id, collection, id))');
$pdo->exec('CREATE TABLE users (id TEXT PRIMARY KEY, disabled INTEGER NOT NULL DEFAULT 0, lang TEXT)');
$pdo->exec("INSERT INTO users (id, lang) VALUES ('u1', 'fr'), ('u2', 'en')");
$put = function (string $uid, string $col, string $id, array $d) use ($pdo) {
    $pdo->prepare('INSERT OR REPLACE INTO documents (user_id, collection, id, data, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)')->execute([$uid, $col, $id, json_encode($d), '2026-11-01T00:00:00Z', '2026-11-01T00:00:00Z']);
};
ps_schema($pdo);
$day = '2026-11-13';
$put('u1', 'journals', $day, ['id' => $day, 'chart' => $chart + ['updated_at' => 1794600000], 'pre' => ['bias' => 'bullish']]);
$put('u1', 'trades', 't1', ['date' => $day, 'entry_time' => '09:50', 'direction' => 'long', 'entry' => 21190, 'instrument' => 'MNQ']);
$put('u1', 'trades', 't2', ['date' => $day, 'entry_time' => '10:30', 'direction' => 'short', 'entry' => 21240, 'instrument' => 'NQ']);
$put('u1', 'trades', 't3', ['date' => '2026-11-12', 'direction' => 'long', 'entry' => 21190, 'instrument' => 'NQ']);
$put('u1', 'trades', 't4', ['date' => $day, 'direction' => 'long', 'entry' => 21190, 'instrument' => 'NQ', 'demo' => true]);
$NY = fn(string $s) => (new DateTimeImmutable($s, new DateTimeZone('America/New_York')))->getTimestamp();
$k = sync_new_key($pdo, 'u1', 'quantower'); $conn = sync_auth($pdo, $k['key']);
$k2 = sync_new_key($pdo, 'u2', 'ninjatrader'); $conn2 = sync_auth($pdo, $k2['key']);
$now = $NY('2026-11-13 12:00');
ps_events($pdo, $conn, [
    ['type' => 'zone_entered', 'id' => 'ev-entered-1', 'at' => gmdate('Y-m-d\TH:i:s\Z', $NY('2026-11-13 09:45')), 'instrument' => 'MNQZ6', 'price' => 21199.75, 'zone' => 'buy'],
    ['type' => 'zone_approached', 'id' => 'ev-approach-1', 'at' => gmdate('Y-m-d\TH:i:s\Z', $NY('2026-11-13 09:42')), 'instrument' => 'NQ', 'price' => 21209, 'zone' => 'buy'],
    ['type' => 'addon_heartbeat', 'id' => 'ev-heartbeat-1', 'at' => gmdate('Y-m-d\TH:i:s\Z', $NY('2026-11-13 09:46'))],
], $now, fn(int $at) => Fiche::dayOf($at));
ps_events($pdo, $conn2, [['type' => 'zone_entered', 'id' => 'ev-other-trader', 'at' => gmdate('Y-m-d\TH:i:s\Z', $NY('2026-11-13 09:30')), 'instrument' => 'NQ', 'zone' => 'buy']], $now, fn(int $at) => Fiche::dayOf($at));
$r = ps_day($pdo, 'u1', $day);
$ok(array_column($r['events'], 'type') === ['zone_approached', 'zone_entered'], '4 the day\'s events, oldest first, the heartbeat not kept (' . implode(', ', array_column($r['events'], 'type')) . ')');
$ok($r['events'][0]['zone'] === 'buy' && $r['events'][1]['instrument'] === 'NQ' && $r['events'][0]['platform'] === 'quantower', '4 each event: its zone, its root, its platform');
$ok($r['follow']['n'] === 2 && $r['follow']['in'] === 1 && $r['follow']['trades']['t1']['in'] && !$r['follow']['trades']['t2']['in'], '4 the day\'s trades only, the sample data left out: 1 of 2 in the plan');
$ok(count(ps_day($pdo, 'u2', $day)['events']) === 1 && ps_day($pdo, 'u2', $day)['follow'] === null, '4 another trader sees only their own events (and has no zone)');
$ok(ps_day($pdo, 'u1', 'x') === ['day' => null, 'events' => [], 'follow' => null], '4 a day that is not a date: nothing');
$ok(ps_day($pdo, 'u1', '2026-11-12')['events'] === [] && ps_day($pdo, 'u1', '2026-11-12')['follow'] === null, '4 a day without zones or events: nothing to show');
array_map('unlink', glob($tmp . '/*')); @rmdir($tmp);

echo "\n$pass passed, $fail failed\n";
exit($fail ? 1 : 0);
