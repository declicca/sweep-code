<?php
declare(strict_types=1);
/**
 * Sweep — the week's recap on Friday (brief 01 step 5), on a throwaway SQLite database (never the live one):
 *   php tests/weekly_test.php
 * The clock is pinned (SWEEP_GAME_NOW, New York time) for each scenario of the brief:
 *  - Friday review done at 16:30 ET → the recap is ready at once; no review → ready at the 17:00 close, not before;
 *  - Friday a market holiday → Thursday's review / close; no trade in the week → no recap, no notification;
 *  - the trader's own time zone (Paris, Tokyo) changes nothing; ONE notification a week, none once the recap is opened.
 */
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
$app = dirname(__DIR__);
$tmp = sys_get_temp_dir() . '/sweep-weekly-' . bin2hex(random_bytes(4)); mkdir($tmp);
$pdo = new PDO('sqlite:' . $tmp . '/t.db', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC]);
function db() { global $pdo; return $pdo; }
$pdo->exec('CREATE TABLE documents (user_id TEXT NOT NULL, collection TEXT NOT NULL, id TEXT NOT NULL, data TEXT NOT NULL, updated_at TEXT, PRIMARY KEY (user_id, collection, id))');
$pdo->exec('CREATE TABLE users (id TEXT PRIMARY KEY, username TEXT, lang TEXT)');
require $app . '/notify/notify.php';
require $app . '/game/game.php';
GameEngine::setPdo($pdo); GameEngine::schema(); GameV2::schema(); GameV2b::schema(); if (class_exists('GameV2c')) GameV2c::schema();
$pass = 0; $fail = 0;
$ok = function (bool $c, string $what) use (&$pass, &$fail) { echo ($c ? 'ok   ' : 'FAIL ') . $what . "\n"; $c ? $pass++ : $fail++; };
$at = function (string $ny) { putenv('SWEEP_GAME_NOW=' . $ny); };
$day = fn(string $uid, string $d, int $trades, int $review) => $pdo->prepare('INSERT OR REPLACE INTO game_days (user_id, trading_day, trades_count, review_done, activity, updated_at) VALUES (?, ?, ?, ?, 1, ?)')->execute([$uid, $d, $trades, $review, time()]);
foreach (['u1', 'u2', 'u3'] as $u) { $at('2026-10-05 08:00'); GameEngine::profile($u); }

// week of Monday 2026-10-05: u1 traded on Tuesday; Friday review not done yet. u2: no trade this week.
$day('u1', '2026-10-06', 2, 1);
$W = '2026-10-05';
$at('2026-10-08 20:00'); $ok(GameV2b::openWeek('u1') === null, 'Thursday evening: the week is not over, no recap');
$at('2026-10-09 16:29'); $ok(GameV2b::openWeek('u1') === null, 'Friday 16:29, no review yet: no recap');
$at('2026-10-09 17:00'); $ok(GameV2b::openWeek('u1') === $W, 'no review: the recap is ready at the 17:00 ET close');
$ok(GameV2b::openWeek('u2') === null, 'no trade in the week: no recap at all');
$at('2026-10-10 11:00'); $ok(GameV2b::openWeek('u1') === $W, 'Saturday: still ready, waiting for the next opening of the app');
$at('2026-10-11 23:30'); $ok(GameV2b::openWeek('u1') === $W, 'Sunday 23:30: still ready');
$at('2026-10-12 09:00'); $ok(GameV2b::openWeek('u1') === null, 'Monday: the new week has no recap yet');
// u3: trades Friday and finishes Friday's review at 16:30 → ready at once
$day('u3', '2026-10-09', 1, 0);
$at('2026-10-09 16:30'); $ok(GameV2b::openWeek('u3') === null, 'Friday 16:30, review not done: not yet');
$day('u3', '2026-10-09', 1, 1);
$ok(GameV2b::openWeek('u3') === $W, 'Friday review done at 16:30 ET: the recap is ready at once');
// Good Friday 2027-03-26 (market holiday): Thursday 2027-03-25 is the last trading day
$day('u1', '2027-03-23', 1, 0);
$at('2027-03-25 16:59'); $ok(GameV2b::openWeek('u1') === null, 'Friday is a holiday: Thursday 16:59 without review, not yet');
$at('2027-03-25 17:00'); $ok(GameV2b::openWeek('u1') === '2027-03-22', 'Friday is a holiday: ready at Thursday\'s 17:00 close');
$day('u3', '2027-03-25', 1, 1);
$at('2027-03-25 15:00'); $ok(GameV2b::openWeek('u3') === '2027-03-22', 'Friday is a holiday: Thursday\'s review done → ready at once');
// the trader's time zone changes nothing (the rule is New York time)
foreach (['Europe/Paris', 'Asia/Tokyo'] as $tz) {
    date_default_timezone_set($tz);
    $at('2026-10-09 16:59'); $a = GameV2b::openWeek('u1'); $at('2026-10-09 17:00'); $b = GameV2b::openWeek('u1');
    $ok($a === null && $b === $W, "time zone $tz: same moment (17:00 New York)");
}
date_default_timezone_set('UTC');
// the light state seen by the app: open, not seen; opening the recap marks it seen
$at('2026-10-09 17:05'); $w = GameV2b::weeklyState('u1', true);
$ok($w['open'] && $w['week'] === $W && $w['seen'] === false, 'the app gets: ready, not seen yet');
// ONE notification a week, none after the recap is opened
$count = fn(string $u) => (int) $pdo->query("SELECT COUNT(*) FROM notifications WHERE user_id = " . $pdo->quote($u) . " AND type = 'g_weekly'")->fetchColumn();
$at('2026-10-09 17:15'); GameNotifyService::run('u1');
$ok($count('u1') === 1, 'Friday 17:15: « Your week is ready » sent once');
$at('2026-10-10 10:00'); GameNotifyService::run('u1');
$at('2026-10-11 19:00'); GameNotifyService::run('u1');
$ok($count('u1') === 1, 'no second notification on Saturday or Sunday');
$at('2026-10-09 17:15'); GameNotifyService::run('u2');
$ok($count('u2') === 0, 'no trade in the week: no notification');
$at('2026-10-09 16:45'); GameV2b::markSeen('u3', $W); GameNotifyService::run('u3');
$ok($count('u3') === 0, 'recap already opened in the app: no notification');
$ok(GameV2b::weeklyState('u3', true)['seen'] === true, 'opened → seen (the routine card stops offering it)');

foreach (glob($tmp . '/*') as $x) @unlink($x); @rmdir($tmp);
echo "\n$pass passed, $fail failed\n";
exit($fail ? 1 : 0);
