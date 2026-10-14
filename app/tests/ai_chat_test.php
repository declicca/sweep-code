<?php
declare(strict_types=1);
/**
 * Sweep — « Ask Sweep », the chat (brief 02 part 9), on a throwaway SQLite database, the model replaced by a stand-in
 * (SWEEP_AI_CHAT_MOCK: no call to Google, no key):
 *   php tests/ai_chat_test.php
 *  - a how-to question: an answer and the screen to open, no « based on » line (no data used);
 *  - a question about the trader's month: « based on » the trades of the last 30 days, counted by the server, with their dates;
 *  - a question that needs an exact figure (worst hour): the server computes it, and says on how many trades;
 *  - the plan's quota (Free: 3 a day): the 4th question is refused with « upgrade_required », its reset at New York's midnight;
 *  - a provider failure gives the question back (the quota is not used); the day's budget reached → « budget »; AI turned off → « disabled »;
 *  - Admin › Health shows the plans' daily limits (the ones that apply with billing).
 */
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
$app = dirname(__DIR__);
$tmp = getenv('AI_TEST_DIR') ?: sys_get_temp_dir() . '/sweep-ai-' . bin2hex(random_bytes(4));
@mkdir($tmp);
$scenario = $argv[1] ?? 'main';
$pdo = new PDO('sqlite:' . $tmp . '/t.db', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC]);
function db() { global $pdo; return $pdo; }
function billing_on() { return true; }
// the AI's test settings: a fake key (never used: the stand-in answers), no pause between questions, a $0.05 budget for the day
file_put_contents($tmp . '/ai-config.php', "<?php return ['enabled' => " . ($scenario === 'disabled' ? 'false' : 'true') . ", 'api_key' => 'local-test-only', 'min_seconds_between_calls' => 0, 'global_daily_budget_usd' => 0.05];\n");
define('SWEEP_AI_CONFIG', $tmp . '/ai-config.php');
file_put_contents($tmp . '/mock.json', json_encode([
    'rules' => [
        ['match' => 'payout', 'out' => ['reply' => 'My money > + Add a payout.', 'action' => 'payouts', 'followups' => ['And an expense?'], 'data' => null]],
        ['match' => 'my month', 'out' => ['reply' => 'This month: +$450 over 4 trades.', 'data' => 'last_30_days', 'followups' => []]],
        ['match' => 'worst hour', 'out' => ['reply' => 'Your worst hour: {worst} ({count} trades).', 'query' => ['metric' => 'net_pnl', 'group_by' => 'hour', 'filters' => []]]],
        ['match' => 'outage', 'error' => 'provider'],
        ['match' => 'expensive', 'out' => ['reply' => 'OK'], 'cost' => 0.06],
    ],
    'default' => ['reply' => 'OK'],
]));
putenv('SWEEP_AI_CHAT_MOCK=' . $tmp . '/mock.json');
if ($scenario === 'main') {
    $pdo->exec('CREATE TABLE users (id TEXT PRIMARY KEY, username TEXT, created_at TEXT, utm_campaign TEXT, email TEXT)');
    $pdo->exec('CREATE TABLE documents (user_id TEXT NOT NULL, collection TEXT NOT NULL, id TEXT NOT NULL, data TEXT NOT NULL, created_at TEXT, updated_at TEXT, PRIMARY KEY (user_id, collection, id))');
}
require $app . '/billing/billing-core.php';
require $app . '/ai/chat.php';
sb_set_config(['live' => true, 'launch_at' => '2026-01-01T00:00:00Z', 'prelaunch_plan' => 'elite', 'comp_users' => [], 'test_users' => [], 'campaign_grants' => [],
    'trial' => ['plan' => 'pro', 'days' => 0], 'early_access_grant' => ['plan' => 'pro', 'days' => 0], 'past_due_grace_days' => 7, 'ai_reviews_fair_use_monthly' => 200,
    'founding_deadline' => '2000-01-01T00:00:00Z', 'founding_for' => 'early_access', 'founding_percent_off' => 50, 'stripe_founding_coupon' => '', 'paywall_max_blocking_per_week' => 3, 'currency' => 'USD',
    'plans' => ['free' => ['ai_daily' => 3, 'ai_import' => false, 'ai_reviews' => 0], 'pro' => ['ai_daily' => 50], 'elite' => ['ai_daily' => 200]]]);
$ask = function (string $q) use ($pdo) {
    try { return [200, sweep_chat($pdo, 'u1', ['message' => $q, 'history' => []], 'en')]; }
    catch (SaiError $e) { return [$e->http, ['code' => $e->sai] + $e->extra]; }
};
if ($scenario === 'disabled') { echo json_encode($ask('Hello')); exit; }

$pass = 0; $fail = 0;
$ok = function (bool $c, string $what) use (&$pass, &$fail) { echo ($c ? 'ok   ' : 'FAIL ') . $what . "\n"; $c ? $pass++ : $fail++; };
$pdo->prepare('INSERT INTO users (id, username, created_at, email) VALUES (?, ?, ?, ?)')->execute(['u1', 'u1', '2026-09-01T12:00:00Z', 'u1@t.dev']);
$today = sai_today_ny();
$day = fn(int $k) => (new DateTime($today))->modify("-$k days")->format('Y-m-d');
$put = function (string $id, string $date, string $time, int $pnl) use ($pdo) {
    $pdo->prepare('INSERT INTO documents (user_id, collection, id, data, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)')->execute(['u1', 'trades', $id, json_encode(['id' => $id, 'account_id' => 'a', 'instrument' => 'NQ', 'direction' => 'long', 'contracts' => 1, 'date' => $date, 'entry_time' => $time, 'pnl_c' => $pnl, 'fees_c' => 0]), $date, $date]);
};
// 4 trades in the last 30 days, 2 older ones
$put('t1', $day(3), '09:45:00', 30000); $put('t2', $day(5), '11:15:00', -10000); $put('t3', $day(10), '09:40:00', 20000); $put('t4', $day(20), '11:30:00', 5000);
$put('t5', $day(60), '10:05:00', -20000); $put('t6', $day(90), '09:50:00', 15000);

[$c, $r] = $ask('How do I add a payout?');
$ok($c === 200 && $r['reply'] === 'My money > + Add a payout.' && $r['action'] === 'payouts' && $r['basis'] === null, 'a how-to question: the answer, the screen to open, no « based on » (no data)');
[$c, $r] = $ask('How was my month?');
$ok($c === 200 && $r['basis'] === ['trades' => 4, 'from' => $day(20), 'to' => $day(3)], 'my month: « based on » the 4 trades of the last 30 days, from ' . $day(20) . ' to ' . $day(3) . ' (' . json_encode($r['basis']) . ')');
[$c, $r] = $ask('What is my worst hour?');
$ok($c === 200 && $r['reply'] === 'Your worst hour: 10:00 (6 trades).' && ($r['basis']['trades'] ?? 0) === 6 && $r['basis']['from'] === $day(90), 'an exact figure: computed by the server (worst hour 10:00), « based on » its 6 trades (' . $r['reply'] . ')');
[$c, $r] = $ask('Hello');
$ok($c === 402 && ($r['code'] ?? '') === 'upgrade_required' && ($r['feature'] ?? '') === 'ai_daily' && ($r['limit'] ?? 0) === 3, 'Free: the 4th question of the day is refused (402, upgrade_required, 3 a day)');
$reset = new DateTime($r['reset_at'] ?? 'now'); $reset->setTimezone(sai_ny());
$ok($reset->format('H:i') === '00:00' && $reset->format('Y-m-d') === (new DateTime($today))->modify('+1 day')->format('Y-m-d'), 'its reset: midnight in New York (' . ($r['reset_at'] ?? '') . ')');
// tomorrow the allowance is back (the New York day changed)
$pdo->exec("UPDATE billing_usage SET period = '2000-01-01' WHERE uid = 'u1'");
$used = fn() => (int) $pdo->query("SELECT COALESCE(SUM(count), 0) FROM billing_usage WHERE uid = 'u1' AND period = " . $pdo->quote(sb_period('ai_daily')))->fetchColumn();
[$c, $r] = $ask('Is there an outage?');
$ok($c === 502 && ($r['code'] ?? '') === 'provider' && $used() === 0, 'a provider failure: an error with its code, the question given back (0 used)');
[$c, $r] = $ask('An expensive question');
$ok($c === 200 && $used() === 1, 'answered: 1 used');
[$c, $r] = $ask('Hello again');
$ok($c === 503 && ($r['code'] ?? '') === 'budget', 'the day\'s budget reached ($0.06 of $0.05): « budget » (503), the AI pauses for the day');
$off = json_decode((string) shell_exec('AI_TEST_DIR=' . escapeshellarg($tmp) . ' ' . escapeshellarg(PHP_BINARY) . ' ' . escapeshellarg(__FILE__) . ' disabled 2>/dev/null'), true);   // (the AI's settings are read once per process)
$ok(($off[0] ?? 0) === 503 && ($off[1]['code'] ?? '') === 'disabled', 'AI turned off: « disabled » (503)');
require_once $app . '/ops/health.php';   // Admin › Health: with billing, the per-trader limit shown is each plan's (not ai-config's)
$h = sweep_health($pdo, [], $app)['config'];
$ok(($h['ai_plan_limits'] ?? null) === ['free' => 3, 'pro' => 50, 'elite' => 200], 'Admin › Health: Sweep AI per trader and per day, by plan (' . json_encode($h['ai_plan_limits'] ?? null) . ')');

$pdo = null; array_map('unlink', glob($tmp . '/*') ?: []); @rmdir($tmp);
echo "\n$pass passed, $fail failed\n";
exit($fail ? 1 : 0);
