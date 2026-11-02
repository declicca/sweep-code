<?php
declare(strict_types=1);
/**
 * Sweep — a trade from one sentence (brief avance, step 3; ai/ai-entry.php), on a throwaway SQLite database, Sweep AI
 * replaced by a stand-in (SWEEP_AI_ENTRY_MOCK: never Google, no key):
 *   php tests/ai_entry_test.php
 *  - plain sentences (EN, FR, ES) read without AI: side, symbol, contracts, P&L, time, prices, the account named;
 *    no AI call and no quota used; a doubtful value (no sign, « at 2:15 ») has a low confidence;
 *  - several accounts and none named: the account is asked; one account: that one;
 *  - other sentences: one Sweep AI call, its JSON checked field by field (a wrong type is dropped, a missing confidence is
 *    « to check »), a list or text is refused (bad_output) and the use given back;
 *  - the plan's quota per New York month: Free 10, Pro 150, Elite unlimited within the day's budget; the 11th on Free →
 *    « upgrade_required » (entry_quota, Pro), reset on the 1st at midnight New York; a plain sentence still works then;
 *  - the screenshot reader's task counts as a screenshot (Free: 3 a day), not as AI messages.
 */
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
$app = dirname(__DIR__);
$tmp = getenv('AI_TEST_DIR') ?: sys_get_temp_dir() . '/sweep-entry-' . bin2hex(random_bytes(4));
@mkdir($tmp);
$scenario = $argv[1] ?? 'main';
$pdo = new PDO('sqlite:' . $tmp . '/t.db', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC]);
function db() { global $pdo; return $pdo; }
function billing_on() { return true; }
file_put_contents($tmp . '/ai-config.php', "<?php return ['enabled' => " . ($scenario === 'disabled' ? 'false' : 'true') . ", 'api_key' => 'local-test-only', 'min_seconds_between_calls' => 0, 'global_daily_budget_usd' => 1.00];\n");
define('SWEEP_AI_CONFIG', $tmp . '/ai-config.php');
file_put_contents($tmp . '/mock.json', json_encode([
    'rules' => [
        ['match' => 'nasdaq this morning', 'out' => ['account' => null, 'instrument' => 'NQZ6', 'direction' => 'long', 'contracts' => 2, 'entry' => null, 'exit' => null, 'pnl_usd' => 400, 'time' => '09:35', 'date' => null,
            'confidence' => ['account' => 0, 'instrument' => 0.95, 'direction' => 0.9, 'contracts' => 0.5, 'entry' => 0, 'exit' => 0, 'pnl_usd' => 0.95, 'time' => 0.6, 'date' => 0]]],
        ['match' => 'messy', 'raw' => '```json {"account":"Topstep 50K","instrument":"zzz!!","direction":"up","contracts":"two","entry":"21000","exit":-5,"pnl_usd":"lots","time":"9.42","date":"2026-02-30","confidence":{"account":95,"entry":"high"}} ```'],
        ['match' => 'as a list', 'out' => [['instrument' => 'NQ']]],
        ['match' => 'not json', 'raw' => 'Sorry, I cannot help.'],
        ['match' => 'expensive', 'out' => ['direction' => 'short', 'pnl_usd' => -100, 'confidence' => ['direction' => 1, 'pnl_usd' => 1]], 'cost' => 2.0],
    ],
    'default' => ['account' => null, 'instrument' => 'ES', 'direction' => 'short', 'contracts' => 1, 'entry' => null, 'exit' => null, 'pnl_usd' => -50, 'time' => null, 'date' => null,
        'confidence' => ['account' => 0, 'instrument' => 1, 'direction' => 1, 'contracts' => 1, 'entry' => 0, 'exit' => 0, 'pnl_usd' => 1, 'time' => 0, 'date' => 0]],
]));
putenv('SWEEP_AI_ENTRY_MOCK=' . $tmp . '/mock.json');
if ($scenario === 'main') {
    $pdo->exec('CREATE TABLE users (id TEXT PRIMARY KEY, username TEXT, created_at TEXT, utm_campaign TEXT, email TEXT)');
    $pdo->exec('CREATE TABLE documents (user_id TEXT NOT NULL, collection TEXT NOT NULL, id TEXT NOT NULL, data TEXT NOT NULL, created_at TEXT, updated_at TEXT, PRIMARY KEY (user_id, collection, id))');
}
require $app . '/billing/billing-core.php';
require_once $app . '/ai/ai-core.php';
require_once $app . '/ai/ai-stats.php';
require_once $app . '/ai/ai-features.php';
require_once $app . '/ai/ai-entry.php';
sb_set_config(['live' => true, 'launch_at' => '2026-01-01T00:00:00Z', 'prelaunch_plan' => 'elite', 'comp_users' => [], 'test_users' => [], 'campaign_grants' => [],
    'trial' => ['plan' => 'pro', 'days' => 0], 'early_access_grant' => ['plan' => 'pro', 'days' => 0], 'past_due_grace_days' => 7, 'ai_reviews_fair_use_monthly' => 200,
    'founding_deadline' => '2000-01-01T00:00:00Z', 'founding_for' => 'early_access', 'founding_percent_off' => 50, 'stripe_founding_coupon' => '', 'paywall_max_blocking_per_week' => 3, 'currency' => 'USD', 'display_prices' => [],
    'plans' => ['free' => ['ai_daily' => 3, 'ai_import' => false, 'ai_reviews' => 0], 'pro' => ['ai_daily' => 50, 'ai_import' => true], 'elite' => ['ai_daily' => 200, 'ai_import' => true]]]);
$run = function (string $uid, string $text, string $lang = 'en') use ($pdo) {
    try { return [200, sai_entry($pdo, $uid, $text, $lang)]; }
    catch (SaiError $e) { return [$e->http, ['code' => $e->sai] + $e->extra]; }
};
if ($scenario === 'disabled') { echo json_encode([$run('u1', 'long NQ +$400 on Topstep 50K yesterday'), $run('u1', 'what a day')]); exit; }

$pass = 0; $fail = 0;
$ok = function (bool $c, string $what) use (&$pass, &$fail) { echo ($c ? 'ok   ' : 'FAIL ') . $what . "\n"; $c ? $pass++ : $fail++; };
$acc = function (string $uid, string $id, string $name) use ($pdo) {
    $pdo->prepare('INSERT INTO documents (user_id, collection, id, data, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)')->execute([$uid, 'accounts', $id, json_encode(['id' => $id, 'name' => $name, 'status' => 'active']), '2026-09-01', '2026-09-01']);
};
$grant = function (string $uid, string $plan) use ($pdo) {
    sb_schema($pdo);
    $pdo->prepare('INSERT INTO billing_grants (uid, plan, starts_at, ends_at, reason, created_at) VALUES (?, ?, ?, ?, ?, ?)')->execute([$uid, $plan, time() - 3600, time() + 86400 * 30, 'comp', time()]);
};
foreach (['u1', 'u2', 'pro', 'elite'] as $u) $pdo->prepare('INSERT INTO users (id, username, created_at, email) VALUES (?, ?, ?, ?)')->execute([$u, $u, '2026-09-01T12:00:00Z', $u . '@t.dev']);
$acc('u1', 'a1', 'Topstep 50K'); $acc('u1', 'a2', 'Apex 2');   // two accounts
$acc('u2', 'b1', 'Lucid 25K');   // one account
$acc('pro', 'p1', 'P1'); $acc('pro', 'p2', 'P2'); $acc('elite', 'e1', 'E1');
$grant('pro', 'pro'); $grant('elite', 'elite');
$aiCalls = fn(string $uid) => (int) $pdo->query("SELECT COUNT(*) FROM ai_log WHERE user_id = " . $pdo->quote($uid))->fetchColumn();
$used = fn(string $uid) => sb_usage($pdo, $uid, 'ai_entry');
sai_init_db($pdo);

/* 1. plain sentences: read here, no AI, no quota */
[$c, $r] = $run('u1', 'long NQ 2 contracts +$400');
$t = $r['trade'] ?? [];
$ok($c === 200 && $r['source'] === 'local' && $t['direction'] === 'long' && $t['instrument'] === 'NQ' && $t['contracts'] === 2 && $t['pnl_c'] === 40000 && $r['low'] === [] && $r['missing'] === [],
    '« long NQ 2 contracts +$400 »: long, NQ, 2, +$400, all sure, read without AI (' . json_encode($t) . ')');
$ok($t['account_id'] === null && $r['ask_account'] === true, 'two accounts, none named: the account is asked');
[$c, $r] = $run('u1', 'short ES 1 lot stopped -$250 at 9:42');
$t = $r['trade'] ?? [];
$ok($c === 200 && $r['source'] === 'local' && $t['direction'] === 'short' && $t['instrument'] === 'ES' && $t['contracts'] === 1 && $t['pnl_c'] === -25000 && $t['time'] === '09:42' && $r['low'] === [],
    '« short ES 1 lot stopped -$250 at 9:42 »: short, ES, 1, −$250, 09:42 (' . json_encode($t) . ')');
[$c, $r] = $run('u1', 'long 2 MNQZ6 from 21000 to 21012.5 on Apex 2');
$t = $r['trade'] ?? [];
$ok($c === 200 && $r['source'] === 'local' && $t['instrument'] === 'MNQ' && $t['contracts'] === 2 && $t['entry'] === 21000.0 && $t['exit'] === 21012.5 && $t['pnl_c'] === null && $r['missing'] === [] && $t['account_id'] === 'a2' && $r['ask_account'] === false,
    'the contract month dropped (MNQZ6 → MNQ), « 2 » before the symbol, the prices, the account named « Apex 2 » (' . json_encode($t) . ')');
[$c, $r] = $run('u1', 'short NQ stopped $300');
$ok($c === 200 && ($r['trade']['pnl_c'] ?? 0) === -30000 && $r['confidence']['pnl_c'] === 0.9 && $r['low'] === [], '« stopped $300 » without a sign: a loss (−$300)');
[$c, $r] = $run('u1', 'long NQ 400$ at 2:15');
$ok($c === 200 && $r['source'] === 'local' && ($r['trade']['pnl_c'] ?? 0) === 40000 && in_array('pnl_c', $r['low'], true) && in_array('time', $r['low'], true),
    'no sign and no word for it, « at 2:15 » (2:15 or 14:15?): read, both highlighted (' . json_encode($r['low'] ?? null) . ')');
[$c, $r] = $run('u2', 'achat NQ 2 contrats +400 $ à 9h42', 'fr');
$t = $r['trade'] ?? [];
$ok($c === 200 && $r['source'] === 'local' && $t['direction'] === 'long' && $t['contracts'] === 2 && $t['pnl_c'] === 40000 && $t['time'] === '09:42' && $t['account_id'] === 'b1' && $r['ask_account'] === false,
    'French « achat NQ 2 contrats +400 $ à 9h42 », one account: that account (' . json_encode($t) . ')');
[$c, $r] = $run('u2', 'venta ES 1 contrato -250$ a las 10:05', 'es');
$t = $r['trade'] ?? [];
$ok($c === 200 && $r['source'] === 'local' && $t['direction'] === 'short' && $t['instrument'] === 'ES' && $t['pnl_c'] === -25000 && $t['time'] === '10:05', 'Spanish « venta ES 1 contrato -250$ a las 10:05 » (' . json_encode($t) . ')');
[$c, $r] = $run('u1', 'long NQ +$1,200.50');
$ok($c === 200 && ($r['trade']['pnl_c'] ?? 0) === 120050, 'a thousands comma: +$1,200.50');
$ok($aiCalls('u1') === 0 && $aiCalls('u2') === 0 && $used('u1') === 0, 'no AI call and no quota used for plain sentences');

/* 2. the rest: one Sweep AI call, checked field by field */
[$c, $r] = $run('u1', 'took a long on nasdaq this morning, made 4 hundred with 2');
$t = $r['trade'] ?? [];
$ok($c === 200 && $r['source'] === 'ai' && $t['instrument'] === 'NQ' && $t['direction'] === 'long' && $t['contracts'] === 2 && $t['pnl_c'] === 40000 && $t['time'] === '09:35',
    'a free sentence: Sweep AI reads it (NQZ6 → NQ, long, 2, +$400, 09:35) (' . json_encode($t) . ')');
$ok($r['low'] === ['contracts', 'time'] && $r['ask_account'] === true && $aiCalls('u1') === 1 && $used('u1') === 1, 'its low confidences highlighted (contracts 0.5, time 0.6), the account asked, 1 use counted (' . json_encode($r['low']) . ')');
[$c, $r] = $run('u1', 'a messy one');
$t = $r['trade'] ?? [];
$ok($c === 200 && $t['account_id'] === 'a1' && $r['confidence']['account_id'] === 0.95 && $t['instrument'] === 'ZZZ' && in_array('instrument', $r['low'], true) && $t['direction'] === null && $t['contracts'] === null
    && $t['entry'] === 21000.0 && $t['exit'] === null && $t['pnl_c'] === null && $t['time'] === null && $t['date'] === null && in_array('entry', $r['low'], true) && $r['missing'] === ['direction', 'pnl_c'],
    'strict JSON: the fence removed, wrong types dropped (side « up », « two », −5, « lots », « 9.42 », 30 Feb.), 95 → 0.95, an unknown symbol and a value without confidence to check (' . json_encode([$t, $r['low']]) . ')');
$before = $used('u1');
[$c, $r] = $run('u1', 'answer as a list');
$ok($c === 502 && $r['code'] === 'bad_output' && $used('u1') === $before, 'an answer that is a list: refused (bad_output), the use given back');
[$c, $r] = $run('u1', 'this is not json');
$ok($c === 502 && $r['code'] === 'bad_output' && $used('u1') === $before, 'an answer that is not JSON: refused, the use given back');

/* 3. the plan's quota per month (u1 is on Free: no trial in this config) */
$ok(sb_plan($pdo, 'u1') === 'free' && sb_plan_limits('free')['ai_entry_monthly'] === 10 && sb_plan_limits('pro')['ai_entry_monthly'] === 150 && sb_plan_limits('elite')['ai_entry_monthly'] === null, 'the plans: Free 10 a month, Pro 150, Elite unlimited');
for ($i = $used('u1'); $i < 10; $i++) $run('u1', 'entry number ' . $i);
$ok($used('u1') === 10, 'Free: 10 AI entries used this month');
[$c, $r] = $run('u1', 'one more please');
$ok($c === 402 && $r['code'] === 'upgrade_required' && $r['feature'] === 'ai_entry_monthly' && $r['trigger'] === 'entry_quota' && $r['limit'] === 10 && $r['upgrade_to'] === 'pro', 'the 11th on Free: refused (402, entry_quota, go Pro)');
$reset = new DateTime($r['reset_at'] ?? 'now'); $reset->setTimezone(sai_ny());
$first = (new DateTime('first day of next month', sai_ny()))->format('Y-m-d');
$ok($reset->format('H:i') === '00:00' && $reset->format('Y-m-d') === $first, 'its reset: the 1st of next month, midnight New York (' . ($r['reset_at'] ?? '') . ')');
[$c, $r] = $run('u1', 'long NQ 2 contracts +$400');
$ok($c === 200 && $r['source'] === 'local', 'a plain sentence still works with the quota used (no AI)');
$ok(sb_usage($pdo, 'u1', 'ai_daily') === 0, 'the AI messages of the day are not touched');
$pdo->exec("UPDATE billing_usage SET period = '2000-01' WHERE uid = 'u1' AND metric = 'ai_entry'");
[$c, $r] = $run('u1', 'next month');
$ok($c === 200 && $used('u1') === 1, 'a new month: the allowance is back');
for ($i = 0; $i < 150; $i++) $run('pro', 'pro entry ' . $i);
[$c, $r] = $run('pro', 'pro entry 151');
$ok($used('pro') === 150 && $c === 402 && $r['upgrade_to'] === 'elite' && $r['limit'] === 150, 'Pro: 150 a month, the 151st → Elite');
for ($i = 0; $i < 200; $i++) $run('elite', 'elite entry ' . $i);
[$c, $r] = $run('elite', 'elite entry 201');
$ok($c === 200 && $used('elite') === 201, 'Elite: unlimited (201 this month)');
[$c, $r] = $run('elite', 'an expensive one');
[$c, $r] = $run('elite', 'after the budget');
$ok($c === 503 && $r['code'] === 'budget', 'Elite within the day\'s budget: once spent, « budget » (503)');

/* 4. the screenshot reader counts as a screenshot */
$ok(sai_kind('trade_shot2') === 'shot' && sai_kind('trade_import') === 'shot' && sai_kind('trade_entry') === 'entry', 'the screenshot reader (trade_shot2) uses the screenshot quota, the sentence its own');
$st = sb_state($pdo, 'u1');
$ok(($st['plans']['free']['ai_entry_monthly'] ?? 'x') === 10 && array_key_exists('ai_entry_monthly', $st['plans']['elite'] ?? []) && $st['plans']['elite']['ai_entry_monthly'] === null && ($st['usage']['ai_entry']['limit'] ?? 0) === 10, 'the plans page gets the monthly AI entries of each plan');

/* 5. Sweep AI turned off: a plain sentence still fills the sheet, the rest says « disabled » */
$off = json_decode((string) shell_exec('AI_TEST_DIR=' . escapeshellarg($tmp) . ' ' . escapeshellarg(PHP_BINARY) . ' ' . escapeshellarg(__FILE__) . ' disabled 2>/dev/null'), true);
$ok(($off[0][0] ?? 0) === 200 && ($off[0][1]['source'] ?? '') === 'partial' && ($off[0][1]['trade']['account_id'] ?? '') === 'a1' && in_array('pnl_c', $off[0][1]['low'] ?? [], true) && ($off[1][0] ?? 0) === 503 && ($off[1][1]['code'] ?? '') === 'disabled',
    'AI off: what the sentence plainly says (all to check), else « disabled » (' . json_encode($off) . ')');

$pdo = null; array_map('unlink', glob($tmp . '/*') ?: []); @rmdir($tmp);
echo "\n$pass passed, $fail failed\n";
exit($fail ? 1 : 0);
