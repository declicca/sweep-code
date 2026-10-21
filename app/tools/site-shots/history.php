<?php
declare(strict_types=1);
/**
 * Sweep — the site's captures: Alex's days replayed in the game, as if he had used the app every day (local capture copy
 * only, never a real database). For each market day from his first one: the plan at 8:45, the day recomputed after the
 * close (review), then the day locked the next morning — the engine's own rules (GameEngine::recomputeDay, catchUp).
 *   SWEEP_TEST_DB=/tmp/gs/data/journal.db php /tmp/gs/tools/site-shots/history.php <uid> <first_day> <today> [HH:MM, now]
 */
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
[$uid, $first, $today, $now] = [$argv[1], $argv[2], $argv[3], $argv[4] ?? '11:05'];
$root = dirname(__DIR__, 2);
$cfg = require $root . '/config.php';
$DATA = rtrim((string) ($cfg['data_dir'] ?? ($root . '/data')), '/');
$pdo = new PDO('sqlite:' . $DATA . '/journal.db', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC]);
$pdo->exec('PRAGMA busy_timeout = 5000');
if (!str_contains($DATA, '/tmp/')) { fwrite(STDERR, "not a capture copy: $DATA\n"); exit(1); }
function db(): PDO { global $pdo; return $pdo; }
function billing_on(): bool { return false; }
foreach (['/notify/notify.php', '/notify/listeners.php'] as $f) if (is_file($root . $f)) require_once $root . $f;
require_once $root . '/game/game.php';
$at = function (string $day, string $hm): void { putenv("SWEEP_GAME_NOW=$day $hm"); $_SERVER['REQUEST_TIME'] = time(); };
GameEngine::schema();
// a fresh game profile that starts on his first day
foreach (['user_game_profile', 'game_days', 'xp_events', 'user_badges', 'game_celebrations'] as $t) GameEngine::q("DELETE FROM $t WHERE user_id = ?", [$uid]);
$at($first, '08:30'); GameEngine::forget($uid); GameEngine::profile($uid);
for ($d = $first; $d <= $today; $d = GameEngine::addDays($d, 1)) {
    if (!GameEngine::isMarketDay($d)) continue;
    $at($d, '08:50'); GameEngine::forget($uid); GameEngine::catchUp($uid); GameEngine::recomputeDay($uid, $d);
    if ($d < $today || $now >= '16:40') { $at($d, '16:40'); GameEngine::forget($uid); GameEngine::recomputeDay($uid, $d); }
}
$at($today, $now); GameEngine::forget($uid); GameEngine::catchUp($uid); GameEngine::recomputeDay($uid, $today);
// the journey's steps evaluated in one go (first opening of the map) get the day he actually reached them
GameV2::backfillMap($uid); GameV2::evaluateMap($uid);
$md = []; for ($d = $first; count($md) < 40; $d = GameEngine::addDays($d, 1)) if (GameEngine::isMarketDay($d)) $md[] = $d;   // his market days
$when = ['c1_rules' => [0, '08:31'], 'c1_plan' => [0, '08:46'], 'c1_journal' => [0, '10:05'], 'c2_setups' => [1, '09:12'], 'c1_journal10' => [4, '11:20'], 'c2_journal30' => [13, '10:40'], 'c2_journal50' => [22, '11:02']];
foreach ($when as $node => [$k, $hm]) GameEngine::q('UPDATE user_map_nodes SET completed_at = ? WHERE user_id = ? AND node_id = ? AND completed_at IS NOT NULL', [GameEngine::epochEt($md[$k], $hm), $uid, $node]);
GameEngine::q('DELETE FROM game_celebrations WHERE user_id = ?', [$uid]);   // nothing pops up on the captures
$p = GameEngine::profile($uid, false);
echo json_encode(['xp' => $p['xp_total'], 'level' => $p['level'], 'streak' => $p['streak_current'], 'best' => $p['streak_best'], 'rank' => $p['rank_key']]), "\n";
