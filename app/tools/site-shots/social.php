<?php
declare(strict_types=1);
/**
 * Sweep — the site's captures: the people around Alex (local capture copy only, never a real database). The league never
 * shows fake players to a real trader; these fictional traders exist only in the capture copy, so the league and the crew
 * screens have someone in them. For each Alex (one per language): his public handle, a Bronze league of the week with
 * him and 13 traders, a crew of 4 with its week's activity.
 *   php /tmp/gs/tools/site-shots/social.php <today> <uid_en> <handle_en> [<uid_fr> <handle_fr> …]
 */
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
$root = dirname(__DIR__, 2);
$cfg = require $root . '/config.php';
$DATA = rtrim((string) ($cfg['data_dir'] ?? ($root . '/data')), '/');
if (!str_contains($DATA, '/tmp/')) { fwrite(STDERR, "not a capture copy: $DATA\n"); exit(1); }
$pdo = new PDO('sqlite:' . $DATA . '/journal.db', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC]);
$pdo->exec('PRAGMA busy_timeout = 5000');
function db(): PDO { global $pdo; return $pdo; }
function billing_on(): bool { return false; }
foreach (['/notify/notify.php', '/notify/listeners.php'] as $f) if (is_file($root . $f)) require_once $root . $f;
require_once $root . '/game/game.php';
$today = $argv[1];
putenv("SWEEP_GAME_NOW=$today 11:05"); $_SERVER['REQUEST_TIME'] = time();
GameEngine::schema(); GameSocial::schema(); GameCrew::schema();
$mon = GameEngine::monday($today);
$at = fn(string $d, string $hm) => GameEngine::epochEt($d, $hm);
mt_srand(9);

// 13 traders (handle, level, streak, week XP, days swept this week)
$people = [['NQ_Nomad', 18, 41, 1180, 4], ['RiskFirst', 14, 22, 1060, 4], ['TapeReader', 12, 15, 540, 3], ['LondonLow', 9, 9, 470, 3], ['OpeningBell', 11, 12, 455, 3],
    ['Mika.T', 8, 7, 390, 3], ['SamTrades', 7, 5, 350, 2], ['PatientPete', 10, 11, 330, 2], ['Delta.Dan', 6, 4, 280, 2], ['ES_Ellie', 5, 3, 240, 2],
    ['Kai_Futures', 4, 2, 180, 1], ['Noor.Trades', 3, 1, 120, 1], ['Rio.Scalps', 2, 0, 60, 0]];
$ids = [];
foreach ($people as $i => [$h, $lvl, $streak, $wxp, $swept]) {
    $uid = 'u_shots_' . strtolower(preg_replace('/[^A-Za-z]/', '', $h));
    $ids[$h] = $uid;
    GameEngine::q('DELETE FROM users WHERE id = ?', [$uid]);
    GameEngine::q("INSERT INTO users (id, username, username_lc, password_hash, is_admin, disabled, created_at, first_name, is_internal) VALUES (?, ?, ?, ?, 0, 1, ?, ?, 1)",
        [$uid, strtolower($h), strtolower($h), '!', '2026-08-01 12:00:00', explode('_', str_replace('.', '_', $h))[0]]);
    foreach (['user_game_profile', 'game_days', 'xp_events', 'social_profile'] as $t) GameEngine::q("DELETE FROM $t WHERE user_id = ?", [$uid]);
    $xp = GameEngine::xpFor($lvl) + mt_rand(20, 400);
    GameEngine::q('INSERT INTO user_game_profile (user_id, xp_total, level, rank_key, streak_current, streak_best, started_on, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
        [$uid, $xp, $lvl, GameEngine::rankFor($lvl), $streak, max($streak, $streak + mt_rand(0, 9)), '2026-08-03', GameEngine::ts()]);
    GameEngine::q('INSERT INTO social_profile (user_id, handle, handle_lc, league_opt_in, league_tier, updated_at) VALUES (?, ?, ?, 1, 1, ?)', [$uid, $h, strtolower($h), GameEngine::ts()]);
    for ($k = 0; $k < 4; $k++) {   // Monday to Thursday morning
        $d = GameEngine::addDays($mon, $k); if ($d > $today) break;
        $sw = $k < $swept && $d < $today ? 1 : 0;
        GameEngine::q('INSERT INTO game_days (user_id, trading_day, ring_plan, ring_execution, ring_review, trades_count, is_swept, is_valid_streak, review_done, plan_valid, activity, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 1, ?)',
            [$uid, $d, 100, $d < $today || $k % 2 ? 100 : 0, $sw ? 100 : ($d < $today ? 60 : 0), mt_rand(1, 3), $sw, $sw, $sw, GameEngine::ts()]);
    }
    // the week's XP, spread from Monday to this morning
    $parts = max(1, min(6, intdiv($wxp, 60)));
    for ($k = 0; $k < $parts; $k++) GameEngine::q('INSERT INTO xp_events (user_id, event_key, xp, created_at) VALUES (?, ?, ?, ?)',
        [$uid, "shots:$k", intdiv($wxp, $parts), $at(GameEngine::addDays($mon, min(3, $k % 4)), '09:' . str_pad((string) (20 + $k * 5), 2, '0', STR_PAD_LEFT))]);
}

foreach (['crew_reactions', 'crew_events', 'crew_members', 'crews', 'league_members', 'league_groups'] as $t) GameEngine::q("DELETE FROM $t");   // (capture copy: run again from scratch)
$crewNames = ['en' => 'NQ Open Club', 'fr' => 'Club de l’ouverture', 'es' => 'Club de la apertura'];
$langs = ['en', 'fr', 'es'];
for ($a = 2, $n = 0; $a + 1 < count($argv); $a += 2, $n++) {
    [$uid, $handle] = [$argv[$a], $argv[$a + 1]]; $lang = $langs[$n] ?? 'en';
    GameEngine::q('DELETE FROM social_profile WHERE user_id = ?', [$uid]);
    GameEngine::q('INSERT INTO social_profile (user_id, handle, handle_lc, league_opt_in, league_tier, updated_at) VALUES (?, ?, ?, 1, 1, ?)', [$uid, $handle, strtolower($handle), GameEngine::ts()]);
    // his league of the week: him and the 13 (formed as on Monday, Bronze)
    GameEngine::q('INSERT INTO league_groups (week_start, tier, created_at) VALUES (?, 1, ?)', [$mon, $at($mon, '00:05')]);
    $gid = (int) GameEngine::pdo()->lastInsertId();
    foreach (array_merge([$uid], array_values($ids)) as $u) GameEngine::q('INSERT INTO league_members (group_id, user_id) VALUES (?, ?)', [$gid, $u]);
    // his crew: him (owner) and 3 of them (a trader is in one crew only: other mates for each language)
    $mates = array_map(fn($h) => $ids[$h], [['NQ_Nomad', 'LondonLow', 'Mika.T'], ['RiskFirst', 'OpeningBell', 'SamTrades'], ['TapeReader', 'PatientPete', 'Delta.Dan']][$n]);
    GameEngine::q('INSERT INTO crews (name, invite_code, owner_id, goal_factor, streak_weeks, last_goal_week, created_at) VALUES (?, ?, ?, 3, 3, ?, ?)',
        [$crewNames[$lang], 'SWP' . strtoupper(substr(md5($uid), 0, 5)), $uid, GameEngine::addDays($mon, -7), $at('2026-09-21', '18:30')]);
    $cid = (int) GameEngine::pdo()->lastInsertId();
    foreach (array_merge([$uid], $mates) as $k => $u) GameEngine::q('INSERT INTO crew_members (crew_id, user_id, joined_at) VALUES (?, ?, ?)', [$cid, $u, $at('2026-09-21', '18:3' . $k)]);
    [$m1, $m2, $m3] = $mates;
    $feed = [[$m3, 'swept', null, $mon, '16:42'], [$uid, 'swept', null, $mon, '16:58'], [$m1, 'streak', ['n' => 20], GameEngine::addDays($mon, 1), '16:20'],
             [$m2, 'swept', null, GameEngine::addDays($mon, 1), '17:05'], [$uid, 'swept', null, GameEngine::addDays($mon, 1), '17:11'],
             [$m1, 'swept', null, GameEngine::addDays($mon, 2), '16:31'], [$uid, 'swept', null, GameEngine::addDays($mon, 2), '16:49'], [$m2, 'rank', ['rank' => 'disciplined'], GameEngine::addDays($mon, 2), '17:40']];
    foreach ($feed as [$u, $type, $p, $d, $hm]) {
        if ($d > $today) continue;
        GameEngine::q('INSERT INTO crew_events (crew_id, user_id, type, payload_json, created_at) VALUES (?, ?, ?, ?, ?)', [$cid, $u, $type, $p ? json_encode($p) : null, $at($d, $hm)]);
        $eid = (int) GameEngine::pdo()->lastInsertId();
        foreach (array_slice(array_merge([$uid], $mates), 0, mt_rand(1, 3)) as $r) if ($r !== $u) GameEngine::q('INSERT INTO crew_reactions (event_id, user_id, emoji) VALUES (?, ?, ?)', [$eid, $r, GAME_CREW_EMOJI[mt_rand(0, 3)]]);
    }
}
echo json_encode(['people' => count($ids), 'alex' => (count($argv) - 2) / 2, 'week' => $mon]), "\n";
