<?php
declare(strict_types=1);
/**
 * Sweep — the app over time (1 Nov., brief dans le temps), the server side, on a throwaway SQLite database, the clock pinned
 * (SWEEP_GAME_NOW):   php tests/life_weeks_test.php
 *  - A1 « A full week inside your plan » only for a week with trades on days that had a plan: never for a week without any trade,
 *    nor for trades taken without a plan (they had no violation only because nothing was planned);
 *  - B1 the 90-day gameplan follows the missions done: a mission Sweep checks itself (a session noted in the journal) is ticked
 *    by a later day too, when the trader reaches it after its calendar date;
 *  - E1 the game state says how many complete days the trader has (« nothing unlocked before 3 complete days », in the app).
 */
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
$app = dirname(__DIR__);
$tmp = sys_get_temp_dir() . '/sweep-life-' . bin2hex(random_bytes(4)); mkdir($tmp);
$pdo = new PDO('sqlite:' . $tmp . '/t.db', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC]);
function db() { global $pdo; return $pdo; }
$cfg = ['notifications' => []];
$pdo->exec('CREATE TABLE documents (user_id TEXT NOT NULL, collection TEXT NOT NULL, id TEXT NOT NULL, data TEXT NOT NULL, created_at TEXT, updated_at TEXT, PRIMARY KEY (user_id, collection, id))');
$pdo->exec('CREATE TABLE users (id TEXT PRIMARY KEY, username TEXT, lang TEXT, email TEXT, first_name TEXT, disabled INT DEFAULT 0)');
require_once $app . '/notify/notify.php';   // (with its listeners: the game recomputes the day on each saved document, as in api.php)
require $app . '/game/game.php';
require_once $app . '/game/wow.php';
require_once $app . '/game/gameplan.php';
GameEngine::setPdo($pdo); GameEngine::schema(); GameV2::schema(); GameV2b::schema(); Notify::schema();
$pass = 0; $fail = 0;
$ok = function (bool $c, string $what) use (&$pass, &$fail) { echo ($c ? 'ok   ' : 'FAIL ') . $what . "\n"; $c ? $pass++ : $fail++; };
$at = function (string $ny) { putenv('SWEEP_GAME_NOW=' . $ny); };
$save = function (string $uid, string $col, array $d) use ($pdo) {
    $prev = $pdo->query('SELECT data FROM documents WHERE user_id = ' . $pdo->quote($uid) . ' AND collection = ' . $pdo->quote($col) . ' AND id = ' . $pdo->quote($d['id']))->fetchColumn();
    $pdo->prepare('INSERT OR REPLACE INTO documents (user_id, collection, id, data, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)')->execute([$uid, $col, $d['id'], json_encode($d), '2026-11-01T14:00:00Z', '2026-11-01T14:00:00Z']);
    nt_doc_event($uid, $col, $d['id'], $d, $prev === false ? null : json_decode((string) $prev, true));
};
$tr = fn(string $id, string $day, int $pnl, string $dir = 'long') => ['id' => $id, 'account_id' => 'a1', 'instrument' => 'NQ', 'direction' => $dir, 'contracts' => 1, 'pnl_c' => $pnl, 'date' => $day, 'entry_time' => '10:20', 'exit_time' => '10:25', 'session_date' => true];
$plan = fn(string $day) => ['id' => $day, 'pre' => ['bias' => 'bullish', 'max_loss' => '500', 'saved_at' => GameEngine::ts()]];
$praise = fn(string $u) => (int) $pdo->query("SELECT COUNT(*) FROM notifications WHERE user_id = " . $pdo->quote($u) . " AND type = 'wow_clean_week'")->fetchColumn();
$week = ['2026-11-02', '2026-11-03', '2026-11-04', '2026-11-05', '2026-11-06'];

// A1. three traders sign up on Sunday 1 Nov.; the first check records the old milestones silently (as in production)
$at('2026-11-01 12:00');
foreach (['sam', 'leo', 'idle'] as $u) { GameEngine::profile($u); $save($u, 'accounts', ['id' => 'a1', 'name' => 'Topstep 50K', 'status' => 'active', 'rules' => ['dd_c' => 200000]]); GameWow::check($u); }
foreach ($week as $d) {
    $at("$d 08:45"); $save('leo', 'journals', $plan($d));
    $at("$d 10:25"); $save('sam', 'trades', $tr("s-$d", $d, 15000)); $save('leo', 'trades', $tr("l-$d", $d, 12000));
}
$at('2026-11-09 08:45');
foreach (['sam', 'leo', 'idle'] as $u) GameWow::check($u);
$ok($praise('idle') === 0, 'A1 a week without any trade: no « A full week inside your plan »');
$ok($praise('sam') === 0, 'A1 a week of trades without a plan (no violation only because nothing was planned): no praise');
$ok($praise('leo') === 1, 'A1 a week of trades, each on a day with a plan, none outside it: the praise, once');
// a week with a plan on some days only: the trades of the days without one are outside the plan
$at('2026-11-01 12:00'); GameEngine::profile('mix'); $save('mix', 'accounts', ['id' => 'a1', 'name' => 'Topstep 50K', 'status' => 'active', 'rules' => ['dd_c' => 200000]]); GameWow::check('mix');
foreach ($week as $i => $d) { if ($i < 2) { $at("$d 08:45"); $save('mix', 'journals', $plan($d)); } $at("$d 10:25"); $save('mix', 'trades', $tr("m-$d", $d, 9000)); }
$at('2026-11-09 08:45'); GameWow::check('mix');
$ok($praise('mix') === 0, 'A1 a plan on 2 days of 5: the 3 trades without a plan count outside it, no praise');

// B1. the gameplan: a session noted in the journal ticks its mission on a later day too
$M = 0; foreach (GP_MISSIONS as $n => $m) if ($m[1] === 'journal') { $M = $n; break; }
$ok($M > 1, "B1 a mission Sweep checks from the journal exists (mission $M)");
if ($M) {
    $at('2026-11-02 08:00'); GameEngine::profile('gp'); $save('gp', 'accounts', ['id' => 'a1', 'name' => 'Topstep 50K', 'status' => 'active', 'rules' => []]); GameGameplan::start('gp', ['track' => 'B']);
    $late = GameEngine::addDays('2026-11-02', $M + 3);   // three days after its calendar date
    $at("$late 10:25"); $save('gp', 'trades', $tr('g1', $late, 5000)); $save('gp', 'journals', ['id' => $late, 'pre' => ['bias' => 'bullish', 'max_loss' => '500'], 'post' => ['well' => 'Patient entry', 'reviewed_at' => GameEngine::ts()]]);
    $at("$late 17:30"); $s = GameGameplan::state('gp');
    $ok(isset(((array) $s['done'])[(string) $M]), "B1 mission $M (a session noted in the journal) ticked by Sweep on $late, 3 days after its date");
    $ok(($s['progress'] ?? -1) === count((array) $s['done']), 'B1 the state says the progress: the number of missions done (' . ($s['progress'] ?? 'none') . ')');
}

// E1. the number of complete days, for the app (nothing « unlocked » before 3)
$at('2026-11-09 18:30'); $ps = GameEngine::profileState('leo');
$ok(array_key_exists('complete_days', $ps) && is_int($ps['complete_days']), 'E1 the game state has the complete days (' . json_encode($ps['complete_days'] ?? null) . ')');

echo "\n$pass passed, $fail failed\n";
array_map('unlink', glob("$tmp/*")); @rmdir($tmp);
exit($fail ? 1 : 0);
