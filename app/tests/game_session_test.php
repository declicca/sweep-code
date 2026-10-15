<?php
declare(strict_types=1);
/**
 * Sweep — the game counts the right session (brief 02 part 11), on a throwaway SQLite database, the clock pinned (SWEEP_GAME_NOW):
 *   php tests/game_session_test.php
 *  - a trade entered at 19:05 ET belongs to the next session (with or without « session_date »); the day's rings and XP
 *    (plan, review, swept day) go to the day of the plan and the review, once each;
 *  - from 18:00 ET « today » is the next session, yet the review written at 18:30 still closes the day that closed;
 *  - a day locks after the next day's 23:59:59 ET; then the streak counts it; the next session stays provisional;
 *  - the missions' week starts Sunday 18:00 ET (the session of Monday);
 *  - the evening reminders (review, streak) speak of the day that closed, not of the session that began at 18:00.
 */
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
$app = dirname(__DIR__);
$tmp = sys_get_temp_dir() . '/sweep-game-' . bin2hex(random_bytes(4)); mkdir($tmp);
$pdo = new PDO('sqlite:' . $tmp . '/t.db', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC]);
function db() { global $pdo; return $pdo; }
$pdo->exec('CREATE TABLE documents (user_id TEXT NOT NULL, collection TEXT NOT NULL, id TEXT NOT NULL, data TEXT NOT NULL, updated_at TEXT, PRIMARY KEY (user_id, collection, id))');
$pdo->exec('CREATE TABLE users (id TEXT PRIMARY KEY, username TEXT, lang TEXT, email TEXT, first_name TEXT, disabled INT DEFAULT 0)');
require_once $app . '/notify/notify.php';
require_once $app . '/game/game.php';
GameEngine::setPdo($pdo); GameEngine::schema(); GameV2::schema(); GameV2b::schema();
$pass = 0; $fail = 0;
$ok = function (bool $c, string $what) use (&$pass, &$fail) { echo ($c ? 'ok   ' : 'FAIL ') . $what . "\n"; $c ? $pass++ : $fail++; };
$at = function (string $ny) { putenv('SWEEP_GAME_NOW=' . $ny); };
$doc = function (string $col, array $d) use ($pdo) { $pdo->prepare("INSERT OR REPLACE INTO documents (user_id, collection, id, data) VALUES ('g1', ?, ?, ?)")->execute([$col, $d['id'], json_encode($d)]); GameEngine::forget('g1'); };   // (the engine keeps the documents of a pass)
$day = fn(string $d) => $pdo->query("SELECT * FROM game_days WHERE user_id = 'g1' AND trading_day = " . $pdo->quote($d))->fetch() ?: [];
$xp = fn() => $pdo->query("SELECT event_key FROM xp_events WHERE user_id = 'g1' ORDER BY event_key")->fetchAll(PDO::FETCH_COLUMN);
$D = '2026-10-13'; $D1 = '2026-10-14';   // Tuesday, Wednesday

// 1. which session a trade belongs to
$ok(GameEngine::tradeDay(['date' => $D1, 'entry_time' => '19:05:00', 'session_date' => true]) === $D1 && GameEngine::tradeDay(['date' => $D, 'entry_time' => '19:05:00']) === $D1
    && GameEngine::tradeDay(['date' => $D, 'entry_time' => '10:00:00']) === $D, 'a 19:05 ET entry: the next session (saved as the session or as the calendar day); 10:00: the same day');
$at("$D 08:00"); GameEngine::profile('g1');
$at("$D 08:10"); $ok(GameEngine::today() === $D, '8:10 ET: today is the session of the day');
$doc('journals', ['id' => $D, 'pre' => ['bias' => 'bullish', 'max_loss' => '500', 'saved_at' => GameEngine::ts()]]);
$doc('trades', ['id' => 't1', 'date' => $D, 'entry_time' => '10:00:00', 'session_date' => true, 'direction' => 'long', 'pnl_c' => 20000, 'stop' => 1, 'discipline' => ['plan' => 'y']]);
$at("$D 17:30"); GameEngine::recomputeDay('g1', $D);
$g = $day($D);
$ok((int) ($g['ring_plan'] ?? 0) === 100 && (int) ($g['ring_execution'] ?? 0) === 100 && (int) ($g['ring_review'] ?? 0) < 100 && (int) ($g['trades_count'] ?? 0) === 1, '17:30: the plan and the trade close their rings for the day, the review not yet');
// 2. from 18:00 ET « today » is the next session; the review written at 18:30 still closes the day that closed
$at("$D 18:30"); $ok(GameEngine::today() === $D1, '18:30 ET: today is already the next session (Wednesday)');
$doc('journals', ['id' => $D, 'pre' => ['bias' => 'bullish', 'max_loss' => '500'], 'post' => ['well' => 'Waited for my setup', 'reviewed_at' => GameEngine::ts()]]);
$doc('trades', ['id' => 't2', 'date' => $D1, 'entry_time' => '19:05:00', 'session_date' => true, 'direction' => 'long', 'pnl_c' => -5000, 'stop' => 1]);
GameEngine::recomputeDay('g1', $D); GameEngine::recomputeDay('g1', $D1);
$g = $day($D); $g1 = $day($D1);
$ok((int) $g['ring_review'] === 100 && (int) $g['is_swept'] === 1 && (int) $g['trades_count'] === 1, 'the review at 18:30 sweeps Tuesday (its 3 rings), with its one trade');
$ok((int) ($g1['trades_count'] ?? 0) === 1 && (int) ($g1['is_swept'] ?? 0) === 0, 'the 19:05 trade counts for Wednesday, not Tuesday');
$keys = $xp();
$ok(in_array("plan:$D", $keys, true) && in_array("review:$D", $keys, true) && in_array("sweep:$D", $keys, true) && !in_array("sweep:$D1", $keys, true), 'XP: plan, review and swept day of Tuesday, none of them on Wednesday (' . implode(', ', $keys) . ')');
GameEngine::recomputeDay('g1', $D);
$ok($xp() === $keys, 'computing Tuesday again: no XP twice');
// 3. the lock and the streak
$at("$D1 23:59"); GameEngine::catchUp('g1');
$ok(empty($day($D)['locked_at']), 'Wednesday 23:59 ET: Tuesday is not locked yet (grace until the next day 23:59:59)');
$at('2026-10-15 00:05'); GameEngine::catchUp('g1');
$p = GameEngine::profile('g1', false); $st = GameEngine::profileState('g1')['streak'];
$ok(!empty($day($D)['locked_at']) && (int) $p['streak_current'] === 1 && empty($day($D1)['locked_at']) && $st['current'] >= 1, 'Thursday 0:05 ET: Tuesday locked, the streak counts it (1); Wednesday stays open (' . json_encode($st) . ')');
// 4. the missions' week
$at('2026-10-18 17:59'); $a = GameV2::weekStart();
$at('2026-10-18 18:01'); $b = GameV2::weekStart();
$ok($a === '2026-10-12' && $b === '2026-10-19', "the missions' week: Sunday 17:59 ET still this week ($a), 18:01 the next ($b)");
// 5. the evening reminders: the day that closed
$pdo->exec("UPDATE game_days SET review_done = 0, ring_review = 0, is_valid_streak = 0 WHERE user_id = 'g1' AND trading_day = '2026-10-19'");
$doc('trades', ['id' => 't3', 'date' => '2026-10-19', 'entry_time' => '10:00:00', 'session_date' => true, 'direction' => 'long', 'pnl_c' => 1000, 'stop' => 1]);
$at('2026-10-19 12:00'); GameEngine::recomputeDay('g1', '2026-10-19');
$at('2026-10-19 18:45'); GameNotifyService::run('g1');
$types = $pdo->query("SELECT type FROM notifications WHERE user_id = 'g1'")->fetchAll(PDO::FETCH_COLUMN);
$ok(in_array('g_review', $types, true), 'Monday 18:45 ET, a trade and no review: « 60 seconds to sweep your day » (before 14 Oct.: nothing after 18:00) (' . implode(', ', $types) . ')');

$pdo = null; array_map('unlink', glob($tmp . '/*') ?: []); @rmdir($tmp);
echo "\n$pass passed, $fail failed\n";
exit($fail ? 1 : 0);
