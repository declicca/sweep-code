<?php
declare(strict_types=1);
/**
 * Sweep — automated tests of the server rules, on a throwaway SQLite database (never the live one).
 *   /usr/local/bin/php /home/matnsabc/app.makeitsweep.com/ops/tests.php
 * Covers: plans over time (trial, campaign bonus, end of trial, nothing deleted), account limits after a downgrade,
 * the write guard, the referral bonus, the progressive reveal of the game. Prints one line per test; exit 1 on failure.
 */
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
$app = dirname(__DIR__);
$db = sys_get_temp_dir() . '/sweep-tests-' . bin2hex(random_bytes(4)) . '.sqlite';
$pdo = new PDO('sqlite:' . $db, null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC]);
$pdo->exec('CREATE TABLE users (id TEXT PRIMARY KEY, username TEXT, created_at TEXT, utm_campaign TEXT)');
$pdo->exec('CREATE TABLE documents (user_id TEXT NOT NULL, collection TEXT NOT NULL, id TEXT NOT NULL, data TEXT NOT NULL, updated_at TEXT, PRIMARY KEY (user_id, collection, id))');
function db() { global $pdo; return $pdo; }
function billing_on() { return true; }

require $app . '/billing/billing-core.php';
$D = 86400; $T0 = strtotime('2026-11-02 15:00:00 UTC');
sb_set_config([
    'live' => true, 'launch_at' => '2026-10-01T00:00:00Z', 'prelaunch_plan' => 'elite', 'comp_users' => [], 'test_users' => [],
    'trial' => ['plan' => 'pro', 'days' => 60], 'early_access_grant' => ['plan' => 'pro', 'days' => 60],
    'campaign_grants' => ['100traders' => ['plan' => 'elite', 'days' => 30]],
    'plans' => ['free' => ['accounts' => 2], 'pro' => ['accounts' => 5], 'elite' => ['accounts' => null]],
    'past_due_grace_days' => 7,
]);
$GLOBALS['SB_NOW'] = $T0;
sb_schema($pdo);

$pass = 0; $fail = 0;
function check(string $name, $got, $want): void {
    global $pass, $fail;
    $ok = $got === $want;
    echo ($ok ? 'ok   ' : 'FAIL ') . $name . ($ok ? '' : '  (got ' . json_encode($got) . ', want ' . json_encode($want) . ')') . "\n";
    $ok ? $pass++ : $fail++;
}
$user = function (string $id, string $camp = '') use ($pdo, $T0) {
    $pdo->prepare('INSERT INTO users (id, username, created_at, utm_campaign) VALUES (?, ?, ?, ?)')->execute([$id, $id, gmdate('Y-m-d\TH:i:s\Z', $T0), $camp]);
    sb_ensure_starting_grant($pdo, $id, $T0);
};

// 1. plans over time
$user('u_trial');
check('trial: Pro on day 0', sb_plan($pdo, 'u_trial'), 'pro');
$GLOBALS['SB_NOW'] = $T0 + 59 * $D; check('trial: still Pro on day 59', sb_plan($pdo, 'u_trial'), 'pro');
$GLOBALS['SB_NOW'] = $T0 + 61 * $D; check('trial: Free on day 61', sb_plan($pdo, 'u_trial'), 'free');
$GLOBALS['SB_NOW'] = $T0;
$user('u_camp', '100-Traders');
check('campaign 100: Elite on day 0', sb_plan($pdo, 'u_camp'), 'elite');
$GLOBALS['SB_NOW'] = $T0 + 31 * $D; check('campaign 100: back to Pro on day 31', sb_plan($pdo, 'u_camp'), 'pro');
$GLOBALS['SB_NOW'] = $T0 + 61 * $D; check('campaign 100: Free on day 61', sb_plan($pdo, 'u_camp'), 'free');
$GLOBALS['SB_NOW'] = $T0;
sb_ensure_starting_grant($pdo, 'u_camp', $T0); sb_campaign_grant($pdo, 'u_camp', $T0);
check('campaign bonus given once only', (int) $pdo->query("SELECT COUNT(*) FROM billing_grants WHERE uid = 'u_camp' AND reason = 'campaign'")->fetchColumn(), 1);
$user('u_other', 'spring-sale');
check('other campaign: no bonus', sb_plan($pdo, 'u_other'), 'pro');

// 2. account limits after the trial: frozen (read-only), never deleted
$GLOBALS['SB_NOW'] = $T0 + 61 * $D;
$acc = sb_accounts($pdo, 'u_trial', ['a1', 'a2', 'a3', 'a4']);
check('downgrade: 2 accounts stay active', $acc['active'], ['a1', 'a2']);
check('downgrade: the others are frozen, not deleted', $acc['frozen'], ['a3', 'a4']);
check('downgrade: the trader is asked to choose', $acc['needs_choice'], true);
$acc = sb_set_active_accounts($pdo, 'u_trial', ['a4', 'a3'], ['a1', 'a2', 'a3', 'a4']);
check('downgrade: the trader picks which stay active', $acc['active'], ['a4', 'a3']);
$g = sb_guard($pdo, 'u_trial', 'create_account', ['account_ids' => ['a1', 'a2', 'a3', 'a4']]);
check('write guard: no new account over the Free limit', $g['code'] ?? null, 'upgrade_required');
$GLOBALS['SB_NOW'] = $T0;
check('write guard: Pro can add accounts', sb_guard($pdo, 'u_trial', 'create_account', ['account_ids' => ['a1', 'a2']]), null);

// 3. referral: the friend gets Elite on top of the trial
if (is_file($app . '/growth/referral.php')) {
    require_once $app . '/growth/referral.php';
    $user('u_friend');
    ref_give_days($pdo, 'u_friend', REF_REFEREE_DAYS, REF_REFEREE_PLAN);
    check('referral: friend on Elite during the bonus', sb_plan($pdo, 'u_friend'), 'elite');
    $GLOBALS['SB_NOW'] = $T0 + (REF_REFEREE_DAYS + 1) * $D;
    check('referral: then the normal Pro trial', sb_plan($pdo, 'u_friend'), 'pro');
    $GLOBALS['SB_NOW'] = $T0;
}

// 4. progressive reveal of the game
putenv('SWEEP_GAME_NOW=2026-11-02 12:00');
require_once $app . '/game/game.php';
GameEngine::setPdo($pdo);
GameEngine::profile('u_g1');
check('reveal: nothing extra on day 1', GameEngine::unlocks('u_g1'), []);
$pdo->prepare("INSERT INTO game_days (user_id, trading_day, ring_plan, ring_execution, ring_review, is_swept, is_valid_streak, activity, updated_at) VALUES (?, '2026-10-30', 100, 100, 100, 1, 1, 1, 1)")->execute(['u_g1']);
check('reveal: missions after the first swept day', GameEngine::unlocks('u_g1'), ['missions']);
check('reveal: one « new » moment per unlock', (int) $pdo->query("SELECT COUNT(*) FROM game_celebrations WHERE user_id = 'u_g1' AND type = 'unlock'")->fetchColumn(), 1);
GameEngine::profile('u_g2');
$pdo->exec("UPDATE user_game_profile SET started_on = '2026-09-01' WHERE user_id = 'u_g2'");
check('reveal: traders already playing keep everything', count(GameEngine::unlocks('u_g2')), count(GAME_UNLOCKS));

$pdo = null; @unlink($db);
echo "\n$pass passed, $fail failed\n";
exit($fail ? 1 : 0);
