<?php
declare(strict_types=1);
/**
 * Sweep — the account guardian's engine (brief « Gardien de compte », step 2, guard/guard.php), on a throwaway SQLite database,
 * the clock pinned (SWEEP_GAME_NOW):
 *   php tests/guard_test.php
 *  - each drawdown type (static, trailing at the end of the day, trailing trade by trade, stopped at the starting balance),
 *    with and without a daily loss limit; an account that touches its floor; a consistency rule; an incomplete preset;
 *  - the levels (calm, watch, danger — by the room or under the usual loss —, breached);
 *  - the session boundary: 17:59 New York is still today, 18:00 is the next session;
 *  - Free: one account with its numbers, the others only named.
 * The numbers checked by hand are written next to each case.
 */
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
$app = dirname(__DIR__);
$tmp = sys_get_temp_dir() . '/sweep-guard-' . bin2hex(random_bytes(4)); mkdir($tmp);
$pdo = new PDO('sqlite:' . $tmp . '/t.db', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC]);
function db() { global $pdo; return $pdo; }
$cfg = ['notifications' => []];
$pdo->exec('CREATE TABLE documents (user_id TEXT NOT NULL, collection TEXT NOT NULL, id TEXT NOT NULL, data TEXT NOT NULL, created_at TEXT, updated_at TEXT, PRIMARY KEY (user_id, collection, id))');
require_once $app . '/notify/notify.php';
require $app . '/game/game.php';
require $app . '/guard/guard.php';
GameEngine::setPdo($pdo);
$pass = 0; $fail = 0;
$ok = function (bool $c, string $what) use (&$pass, &$fail) { echo ($c ? 'ok   ' : 'FAIL ') . $what . "\n"; $c ? $pass++ : $fail++; };
$put = function (string $uid, string $col, array $d) use ($pdo) { $pdo->prepare('INSERT OR REPLACE INTO documents (user_id, collection, id, data) VALUES (?, ?, ?, ?)')->execute([$uid, $col, $d['id'], json_encode($d)]); GameEngine::forget($uid); };
$tr = function (string $acc, string $date, int $net, string $time = '10:00', string $id = '') { static $k = 0; $k++; return ['id' => $id ?: 't' . $k, 'account_id' => $acc, 'date' => $date, 'entry_time' => $time, 'pnl_c' => $net, 'fees_c' => 0, 'created_at' => sprintf('%sT%s:00.%03dZ', $date, $time, $k)]; };
$K = fn(int $d) => $d * 100;   // dollars → cents
$TODAY = '2026-11-04';

// A — static, no daily limit. Start $50,000, drawdown $2,000 → floor $48,000. Before today +$500 (start of day $50,500), today −$300.
//     Balance $50,200; room 50,200 − 48,000 = $2,200; at the start of the day $2,500; 2,200 / 2,500 = 88 % → calm; risk left = room.
$a = ['id' => 'A', 'name' => 'Static', 'phase' => 'eval', 'starting_balance_c' => $K(50000), 'rules' => ['dd_c' => $K(2000), 'dd_type' => 'static', 'target_c' => $K(3000)]];
$g = guard_account($a, [$tr('A', '2026-11-03', $K(500)), $tr('A', $TODAY, $K(-300))], [], ['today' => $TODAY]);
$ok($g['floors']['drawdown_c'] === $K(48000) && $g['floors']['daily_c'] === null && $g['room_c'] === $K(2200) && $g['room_start_c'] === $K(2500) && $g['level'] === 'calm' && $g['left_c'] === $K(2200),
    "A static: floor 48,000, room 2,200 of 2,500, calm (" . json_encode([$g['floors'], $g['room_c'], $g['room_start_c'], $g['level']]) . ')');
$ok($g['goal']['left_c'] === $K(2800) && in_array('dll', $g['missing'], true) && !$g['estimate'], 'A target: $3,000 − $200 profit = $2,800 left; no daily limit listed as missing');

// B — trailing at the end of the day, stopped at the starting balance, daily limit $1,000. Start $50,000, drawdown $2,500.
//     Day 1 +$1,000 (highest close $51,000), day 2 −$400 ($50,600 = start of today), today −$600 ($50,000).
//     Drawdown floor min(51,000 − 2,500, 50,000) = $48,500; daily floor 50,600 − 1,000 = $49,600; the higher: $49,600.
//     Room 50,000 − 49,600 = $400; at the start 50,600 − 49,600 = $1,000; 40 % → watch. Plan $800: 800 − 600 = $200 left (< room).
$b = ['id' => 'B', 'name' => 'EOD', 'phase' => 'eval', 'starting_balance_c' => $K(50000), 'rules' => ['dd_c' => $K(2500), 'dd_type' => 'eod', 'dll_c' => $K(1000)]];
$bt = [$tr('B', '2026-11-02', $K(1000)), $tr('B', '2026-11-03', $K(-400)), $tr('B', $TODAY, $K(-600))];
$g = guard_account($b, $bt, [], ['today' => $TODAY, 'plan_c' => $K(800)]);
$ok($g['floors']['drawdown_c'] === $K(48500) && $g['floors']['daily_c'] === $K(49600) && $g['room_c'] === $K(400) && $g['room_start_c'] === $K(1000) && $g['level'] === 'watch' && $g['left_c'] === $K(200),
    'B end of day + daily limit: floors 48,500 / 49,600, room 400 of 1,000, watch, $200 left of the plan (' . json_encode([$g['floors'], $g['room_c'], $g['left_c'], $g['level']]) . ')');
$g2 = guard_account($b, $bt, [], ['today' => $TODAY]);
$ok($g2['left_c'] === $K(400), 'B without a plan: risk left = the room ($400)');
$g3 = guard_account($b, $bt, [], ['today' => $TODAY, 'usual_loss_c' => $K(450)]);
$ok($g3['level'] === 'danger', 'B with a usual loss of $450 (> $400 of room): danger');
// the same account, no daily limit: only the drawdown floor
$b2 = $b; unset($b2['rules']['dll_c']);
$g = guard_account($b2, $bt, [], ['today' => $TODAY]);
$ok($g['room_c'] === $K(1500) && $g['room_start_c'] === $K(2100) && $g['level'] === 'calm', 'B without a daily limit: room 50,000 − 48,500 = 1,500 of 2,100, calm (' . json_encode([$g['room_c'], $g['room_start_c']]) . ')');

// C — trailing trade by trade, stopped at the start. Start $100,000, drawdown $3,000. Day 1 +2,000 then −1,000 (high $102,000,
//     start of today $101,000, floor $99,000). Today +1,500 ($102,500: floor $99,500) then −2,000 ($100,500).
//     Room 100,500 − 99,500 = $1,000; at the start 101,000 − 99,000 = $2,000; 50 % → watch. Typed account: an estimate.
$c = ['id' => 'C', 'name' => 'Intraday', 'phase' => 'funded', 'starting_balance_c' => $K(100000), 'rules' => ['dd_c' => $K(3000), 'dd_type' => 'trade']];
$ct = [$tr('C', '2026-11-03', $K(2000), '10:00'), $tr('C', '2026-11-03', $K(-1000), '11:00'), $tr('C', $TODAY, $K(1500), '09:40'), $tr('C', $TODAY, $K(-2000), '10:10')];
$g = guard_account($c, $ct, [], ['today' => $TODAY]);
$ok($g['floors']['drawdown_c'] === $K(99500) && $g['room_c'] === $K(1000) && $g['room_start_c'] === $K(2000) && $g['level'] === 'watch' && $g['estimate'] === true && $g['goal'] === null,
    'C trade by trade: floor 99,500, room 1,000 of 2,000, watch, estimate, no target on a funded account (' . json_encode([$g['floors'], $g['room_c'], $g['room_start_c'], $g['level']]) . ')');
$g = guard_account($c, $ct, [], ['today' => $TODAY, 'synced' => true]);
$ok($g['estimate'] === false, 'C synced: not an estimate');
// the stop at the starting balance: a high of $104,000 would put the floor at $101,000 — it stays at $100,000
$g = guard_account($c, [$tr('C', '2026-11-03', $K(4000)), $tr('C', $TODAY, $K(-500))], [], ['today' => $TODAY]);
$ok($g['floors']['drawdown_c'] === $K(100000) && $g['room_c'] === $K(3500), 'C stopped at the starting balance: floor 100,000, room 103,500 − 100,000 = 3,500');
$c2 = $c; $c2['rules']['dd_lock'] = false;
$g = guard_account($c2, [$tr('C', '2026-11-03', $K(4000)), $tr('C', $TODAY, $K(-500))], [], ['today' => $TODAY]);
$ok($g['floors']['drawdown_c'] === $K(101000), 'C without the stop: floor 104,000 − 3,000 = 101,000');

// D — an account that touches its floor (static $48,000): exactly on it, and past it
$d = ['id' => 'D', 'name' => 'Floor', 'phase' => 'eval', 'starting_balance_c' => $K(50000), 'rules' => ['dd_c' => $K(2000), 'dd_type' => 'static']];
$g = guard_account($d, [$tr('D', $TODAY, $K(-2000))], [], ['today' => $TODAY]);
$ok($g['level'] === 'breached' && $g['room_c'] === 0 && $g['left_c'] === 0, 'D on its floor ($48,000): breached, nothing left');
$g = guard_account($d, [$tr('D', $TODAY, $K(-2100))], [], ['today' => $TODAY]);
$ok($g['level'] === 'breached' && $g['room_c'] === $K(-100) && $g['left_c'] === 0, 'D past its floor: breached, room −100, risk left 0');
$g = guard_account($d, [$tr('D', '2026-11-03', $K(-2100)), $tr('D', $TODAY, $K(3000))], [], ['today' => $TODAY]);
$ok($g['level'] === 'breached', 'D breached yesterday, back above today: still breached (the account was lost)');
$g = guard_account($d, [$tr('D', $TODAY, $K(-1700))], [], ['today' => $TODAY]);
$ok($g['level'] === 'danger' && $g['room_pct'] == 15.0, 'D $300 of $2,000 left (15 %): danger');

// E — consistency 40 %: days +1,000, +500, today +300 → best 1,000 / 1,800 = 55.6 % (over the rule). The most today can end at
//     while keeping it: 40 % × 1,500 / 60 % = $1,000 (then 1,000 / 2,500 = 40 %) → $700 more today.
$e = ['id' => 'E', 'name' => 'Cons', 'phase' => 'funded', 'starting_balance_c' => $K(50000), 'rules' => ['dd_c' => $K(2000), 'dd_type' => 'eod', 'consistency_pct' => 40]];
$g = guard_account($e, [$tr('E', '2026-11-02', $K(1000)), $tr('E', '2026-11-03', $K(500)), $tr('E', $TODAY, $K(300))], [], ['today' => $TODAY]);
$ok($g['consistency']['pct'] == 55.6 && $g['consistency']['ok'] === false && $g['consistency']['max_today_c'] === $K(700),
    'E consistency: 55.6 % of 40 %, $700 more today keeps it (' . json_encode($g['consistency']) . ')');

// F — an incomplete preset: only a drawdown. The others are listed, never guessed.
$f = ['id' => 'F', 'name' => 'Part', 'phase' => 'eval', 'starting_balance_c' => $K(25000), 'rules' => ['dd_c' => $K(1500), 'dd_type' => 'static']];
$g = guard_account($f, [], [], ['today' => $TODAY]);
$ok($g['missing'] === ['dll', 'consistency', 'target', 'min_days'] && $g['goal'] === null && $g['consistency'] === null && $g['level'] === 'calm' && $g['room_c'] === $K(1500),
    'F only a drawdown: daily limit, consistency, target and minimum days listed as missing (' . json_encode($g['missing']) . ')');
// a live account without rules: its floor is $0 (as its page), the room is its balance
$lv = ['id' => 'L', 'name' => 'Live', 'money_type' => 'live', 'starting_balance_c' => $K(3000), 'rules' => []];
$g = guard_account($lv, [$tr('L', $TODAY, $K(-200))], [], ['today' => $TODAY]);
$ok($g['floors']['drawdown_c'] === 0 && $g['room_c'] === $K(2800) && $g['floors']['type'] === 'live' && !in_array('dd', $g['missing'], true), 'live without rules: floor $0, room $2,800');

// payouts and adjustments: the same path as the account page (a paid payout lowers the balance, a recalibration moves it)
$p = ['id' => 'P', 'name' => 'Pay', 'phase' => 'funded', 'starting_balance_c' => $K(50000), 'rules' => ['dd_c' => $K(2000), 'dd_type' => 'eod'], 'adjustments' => [['at' => '2026-11-03', 'amount_c' => $K(-100)]]];
$g = guard_account($p, [$tr('P', '2026-11-02', $K(1500)), $tr('P', $TODAY, $K(-200))], [['id' => 'po', 'account_id' => 'P', 'status' => 'paid', 'amount_c' => $K(500), 'payment_date' => '2026-11-03']], ['today' => $TODAY]);
// highest close 51,500 → floor min(49,500, 50,000) = 49,500; balance 50,000 + 1,500 − 200 − 500 − 100 = 50,700; room 1,200
$ok($g['balance_c'] === $K(50700) && $g['floors']['drawdown_c'] === $K(49500) && $g['room_c'] === $K(1200), 'payout and adjustment: balance 50,700, floor 49,500, room 1,200 (' . json_encode([$g['balance_c'], $g['floors']['drawdown_c']]) . ')');

// a balance typed today (step 4): it is the balance now; a trade saved after it wins again
$g = guard_account($b, $bt, [], ['today' => $TODAY, 'live' => ['bal_c' => $K(50300), 'at' => '2026-11-04T23:00:00.000Z']]);
$ok($g['pnl_c'] === $K(-300) && $g['room_c'] === $K(700) && $g['typed'] !== null, 'B typed balance $50,300: today −300, room 700');
$g = guard_account($b, $bt, [], ['today' => $TODAY, 'live' => ['bal_c' => $K(50300), 'at' => '2026-11-04T01:00:00.000Z']]);
$ok($g['pnl_c'] === $K(-600) && $g['typed'] === null, 'B a trade saved after the typed balance: the trades count again');

// a Sunday-evening trade is Monday's session (the app's dayMap): Sunday +1,000 and Monday −400 are one day of +600 —
// the highest close is $50,600, not $51,000 → floor 48,100 (as the account page)
$g = guard_account($b2, [$tr('B', '2026-11-01', $K(1000), '19:00'), $tr('B', '2026-11-02', $K(-400)), $tr('B', $TODAY, $K(-600))], [], ['today' => $TODAY]);
$ok($g['floors']['drawdown_c'] === $K(48100) && $g['room_c'] === $K(1900), 'Sunday evening counts on Monday: floor 48,100, room 1,900 (' . json_encode([$g['floors']['drawdown_c'], $g['room_c']]) . ')');
$g = guard_account($b2, [$tr('B', '2026-11-08', $K(300), '19:00'), $tr('B', '2026-11-09', $K(-100))], [], ['today' => '2026-11-09']);
$ok($g['pnl_c'] === $K(200) && $g['sod_c'] === $K(50000), 'on Monday, Sunday evening\'s trade is in today\'s P&L (+300 − 100 = +200)');

// the session boundary and Free, through the documents
$uid = 'u1';
$put($uid, 'accounts', $b + ['status' => 'active']); $put($uid, 'accounts', $d + ['status' => 'active']);
$put($uid, 'accounts', ['id' => 'X', 'name' => 'Archived', 'status' => 'archived', 'starting_balance_c' => 1, 'rules' => ['dd_c' => 100]]);
foreach ([$tr('B', '2026-11-02', $K(1000)), $tr('B', '2026-11-03', $K(-400)), $tr('B', $TODAY, $K(-600), '16:30')] as $t) $put($uid, 'trades', $t);
$put($uid, 'trades', $tr('D', $TODAY, $K(-1700), '15:00'));
putenv('SWEEP_GAME_NOW=' . $TODAY . ' 17:59');
$s = guard_state($uid, true);
$byId = array_column($s['accounts'], null, 'id');
$ok($s['day'] === $TODAY && count($s['accounts']) === 2 && $s['accounts'][0]['id'] === 'D' && $byId['B']['pnl_c'] === $K(-600),
    '17:59 New York: today\'s session, the most at risk first (D danger, then B), the archived account left out');
putenv('SWEEP_GAME_NOW=' . $TODAY . ' 18:00');
$s = guard_state($uid, true); $byId = array_column($s['accounts'], null, 'id');
$ok($s['day'] === '2026-11-05' && $byId['B']['pnl_c'] === 0 && $byId['B']['sod_c'] === $K(50000) && $byId['B']['room_start_c'] === $K(1000),
    '18:00 New York: the next session — nothing traded yet, the day starts at $50,000 with a daily floor of $49,000 (' . json_encode([$s['day'], $byId['B']['sod_c'], $byId['B']['room_start_c']]) . ')');
putenv('SWEEP_GAME_NOW=' . $TODAY . ' 12:00');
$s = guard_state($uid, false);
$ok(count($s['accounts']) === 2 && isset($s['accounts'][0]['room_c']) && !empty($s['accounts'][1]['locked']) && !isset($s['accounts'][1]['room_c']), 'Free: the most at risk with its numbers, the other only named (locked)');
// the plan's max loss of the day is the planned risk; without a plan, the max loss per day of Settings
$put($uid, 'meta', ['id' => 'settings', 'day_lock' => ['loss_c' => $K(700), 'trades' => 0]]);
$ok(guard_plan_risk($uid, $TODAY) === $K(700), 'planned risk: Settings › max loss per day ($700) without a plan');
$put($uid, 'journals', ['id' => $TODAY, 'pre' => ['bias' => 'bullish', 'max_loss' => 450]]);
$ok(guard_plan_risk($uid, $TODAY) === $K(450), 'planned risk: the day\'s plan ($450) first');
$ok(guard_usual_loss([$tr('A', '2026-11-01', $K(-100)), $tr('A', '2026-11-02', $K(-300)), $tr('A', '2026-11-02', $K(200))]) === $K(200), 'usual loss: the average of the losses ($200)');

echo "\n$pass passed, $fail failed\n";
exit($fail ? 1 : 0);
