<?php
declare(strict_types=1);
/**
 * Sweep — the 90-day gameplan's model (brief « Parcours de 90 jours », step 1), throwaway SQLite, the clock pinned:
 *   php tests/gameplan_test.php
 *  - it starts on the next Monday (today if it is one); before it, nothing opens but the first account Sweep sees;
 *  - mission N opens on its date; a late one can still be done; each pays its minutes in XP once;
 *  - past day 30 (60), nothing of the next month opens until the gate is passed; a gate is decided, not ticked;
 *  - « again »: Weeks 3 and 4 of the month from the next Monday, their missions open again;
 *  - Free is locked (402), Pro and Elite not; stop removes the plan.
 */
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
$app = dirname(__DIR__);
$tmp = sys_get_temp_dir() . '/sweep-gp-' . bin2hex(random_bytes(4)); mkdir($tmp);
$pdo = new PDO('sqlite:' . $tmp . '/t.db', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC]);
function db() { global $pdo; return $pdo; }
// billing as live, the plan from the trader's id
function billing_on(): bool { return true; }
function sb_live(string $uid): bool { return true; }
function sb_can(PDO $pdo, string $uid, string $f): bool { return $f === 'gameplan' && $uid !== 'free1'; }
$pdo->exec('CREATE TABLE documents (user_id TEXT NOT NULL, collection TEXT NOT NULL, id TEXT NOT NULL, data TEXT NOT NULL, updated_at TEXT, PRIMARY KEY (user_id, collection, id))');
$pdo->exec('CREATE TABLE users (id TEXT PRIMARY KEY, username TEXT, lang TEXT, email TEXT, first_name TEXT, disabled INT DEFAULT 0)');
require_once $app . '/notify/notify.php';
require_once $app . '/game/game.php';
GameEngine::setPdo($pdo); GameEngine::schema();
$pass = 0; $fail = 0;
$ok = function (bool $c, string $what) use (&$pass, &$fail) { echo ($c ? 'ok   ' : 'FAIL ') . $what . "\n"; $c ? $pass++ : $fail++; };
$at = function (string $ny) { putenv('SWEEP_GAME_NOW=' . $ny); };
$xp = fn(string $u) => $pdo->query("SELECT event_key, xp FROM xp_events WHERE user_id = " . $pdo->quote($u) . " AND event_key LIKE 'gp:%' ORDER BY event_key")->fetchAll(PDO::FETCH_KEY_PAIR);
$U = 'g1'; GameEngine::profile($U);
$doc = function (string $col, array $d, string $u = 'g1') use ($pdo) { $pdo->prepare('INSERT OR REPLACE INTO documents (user_id, collection, id, data) VALUES (?, ?, ?, ?)')->execute([$u, $col, $d['id'], json_encode($d)]); GameEngine::forget($u); };

// 1. the start
$ok(count(GP_MISSIONS) === 90 && GP_MISSIONS[30][2] === 1 && GP_MISSIONS[60][2] === 2 && GP_MISSIONS[90][2] === 3, '1 90 missions, gates on days 30, 60, 90');
$at('2026-10-21 10:00');   // a Wednesday: the day the account is made
$Z = 'g0'; GameEngine::profile($Z);
$ok(GameGameplan::state($Z)['access'] && !GameGameplan::state($Z)['started'], '1 not started');
$s = GameGameplan::start($Z, ['track' => 'B']);
$ok($s['started'] && $s['start'] === '2026-10-21' && $s['track'] === 'B' && $s['day'] === 1 && $s['open_to'] === 1, '1 started on a Wednesday: day 1 is that very day (20 Oct., Mateo), track B');
$ok((GameGameplan::done($Z, 2)['error'] ?? '') === 'not_open', '1 day 2 is tomorrow: not open');
$ok(!isset(((array) GameGameplan::state($Z)['done'])['1']), '1 no account yet: mission 1 waits');
$doc('accounts', ['id' => 'a1', 'name' => 'Topstep 50K', 'status' => 'active', 'rules' => []], 'g0');
$ok((((array) GameGameplan::state($Z)['done'])['1']['by'] ?? '') === 'sweep' && ($xp($Z)['gp:1'] ?? 0) === 20, '1 the first account: Sweep ticks mission 1, 20 XP');
// the main trader, from Monday 26 Oct.
$at('2026-10-26 08:00'); GameGameplan::start($U, []); $doc('accounts', ['id' => 'a1', 'name' => 'Topstep 50K', 'status' => 'active', 'rules' => []]);
$ok(GameGameplan::state($U)['day'] === 1 && GameGameplan::state($U)['open_to'] === 1 && ($xp($U)['gp:1'] ?? 0) === 20, '1 Monday: day 1, mission 1 by Sweep');
$at('2026-10-27 09:00');   // Tuesday: day 2
// 2. one mission a day, its XP once, late ones still open
$s = GameGameplan::done($U, 2); GameGameplan::done($U, 2);
$ok(isset(((array) $s['done'])['2']) && ($xp($U)['gp:2'] ?? 0) === 30 && count($xp($U)) === 2, '2 day 2 done: 30 XP, once');
$ok((GameGameplan::done($U, 3)['error'] ?? '') === 'not_open', '2 day 3 is tomorrow: not open');
$at('2026-11-03 09:00');   // day 9
$ok(!isset(GameGameplan::done($U, 4)['error']) && !isset(GameGameplan::done($U, 9)['error']), '2 day 9: a late mission (4) and today\'s (9) can be done');
$ok((GameGameplan::done($U, 999)['error'] ?? '') === 'bad_mission', '2 an unknown mission: refused');
// 2b. what Sweep sees: the trade with stop and target (day 2 done by hand above), the day's review, the weekly recap
$W = 'g3'; GameEngine::profile($W); $at('2026-10-26 09:00'); GameGameplan::start($W, []);
$at('2026-10-27 15:00');   // day 2
$doc('trades', ['id' => 't0', 'account_id' => 'a', 'date' => '2026-10-27', 'entry_time' => '10:00', 'instrument' => 'MES', 'direction' => 'long', 'contracts' => 1, 'entry' => 5800, 'exit' => 5810, 'stop' => 5795], $W);
$ok(!isset(((array) GameGameplan::state($W)['done'])['2']), '2b a trade without its target: mission 2 waits');
$doc('trades', ['id' => 't1', 'account_id' => 'a', 'date' => '2026-10-27', 'entry_time' => '10:30', 'instrument' => 'MES', 'direction' => 'long', 'contracts' => 1, 'entry' => 5800, 'exit' => 5810, 'stop' => 5795, 'target' => 5810], $W);
$ok((((array) GameGameplan::state($W)['done'])['2']['by'] ?? '') === 'sweep', '2b with its stop and target: Sweep ticks mission 2');
$at('2026-11-23 15:00');   // day 29, « Final session » (session journaled)
$pdo->prepare('INSERT INTO game_days (user_id, trading_day, review_done, updated_at) VALUES (?, ?, 1, ?)')->execute([$W, '2026-11-23', time()]);
$st = (array) GameGameplan::state($W)['done'];
$ok((($st['29'] ?? [])['by'] ?? '') === 'sweep', '2b the day reviewed in the journal: Sweep ticks « Final session » (29)');
$ok(!isset($st['28']) && !isset($st['26']), '2b « 3 + 3 » (28) is the trader\'s to tick; the weekly recap (26) not done yet');
GameV2b::schema(); $pdo->prepare('INSERT INTO weekly_reviews (user_id, week_start, data_json, completed_at) VALUES (?, ?, ?, ?)')->execute([$W, '2026-11-16', '{}', time()]);
$ok(((((array) GameGameplan::state($W)['done'])['26'] ?? [])['by'] ?? '') === 'sweep', '2b the weekly recap of that week: Sweep ticks mission 26');

// 3. the gate of month 1
$at('2026-11-30 09:00');   // day 36
$s = GameGameplan::state($U);
$ok($s['day'] === 36 && $s['open_to'] === 30, '3 day 36, gate 1 not passed: nothing past day 30 opens (' . $s['open_to'] . ')');
$ok((GameGameplan::done($U, 30)['error'] ?? '') === 'gate' && (GameGameplan::done($U, 31)['error'] ?? '') === 'not_open', '3 the gate is decided, not ticked; day 31 waits for it');
$s = GameGameplan::gate($U, 1, 'pass');
$ok(($s['open_to'] ?? 0) === 36 && (((array) $s['gates'])['1'] ?? '') === 'pass' && ($xp($U)['gp:gate1'] ?? 0) === GP_GATE_XP, '3 gate 1 passed: month 2 open, ' . GP_GATE_XP . ' XP');
$ok((GameGameplan::gate($U, 2, 'pass')['error'] ?? '') === 'not_open', '3 gate 2 before day 60: not open');
// 4. again: Weeks 3 and 4
$V = 'g2'; GameEngine::profile($V); $at('2026-10-26 09:00'); GameGameplan::start($V, []);
$at('2026-11-10 09:00'); GameGameplan::done($V, 14); GameGameplan::done($V, 15); GameGameplan::done($V, 16);
$at('2026-11-25 09:00');   // a Wednesday, day 31
$s = GameGameplan::gate($V, 1, 'repeat');
$ok($s['track'] === 'A' && GameGameplan::dayOf($s['start'], '2026-11-25') === 15, '4 again: day 15 is today, 25 Nov. (start ' . $s['start'] . ')');
$d = array_map('strval', array_keys((array) $s['done']));
$ok(in_array('14', $d, true) && !in_array('15', $d, true) && !in_array('16', $d, true) && $s['open_to'] === 15, '4 Weeks 3 and 4 open again (14 kept, 15 and 16 to redo), from day 15 today');
// 4b. the track, never asked: from the accounts
$T1 = 'g4'; GameEngine::profile($T1); $at('2026-10-21 10:00');
$doc('accounts', ['id' => 's1', 'name' => 'Sim', 'status' => 'active', 'money_type' => 'simulation', 'phase' => 'simulation'], $T1);
$ok(GameGameplan::start($T1, [])['track'] === 'A', '4b only a simulation account: track A');
$doc('accounts', ['id' => 'e1', 'name' => 'Eval', 'status' => 'active', 'money_type' => 'eval', 'phase' => 'eval', 'firm_id' => 'f'], $T1);
$ok(GameGameplan::start($T1, [])['track'] === 'B', '4b an evaluation too: track B');

// 5. Free, stop
$at('2026-10-21 10:00');
$ok(!GameGameplan::state('free1')['access'] && (GameGameplan::start('free1', [])['error'] ?? '') === 'locked' && (GameGameplan::done('free1', 1)['error'] ?? '') === 'locked', '5 Free: locked');
$s = GameGameplan::stop($U);
$ok(!$s['started'] && ($xp($U)['gp:2'] ?? 0) === 30, '5 stop: the plan is gone, the XP stays');

echo "\n$pass passed, $fail failed\n";
exit($fail ? 1 : 0);
