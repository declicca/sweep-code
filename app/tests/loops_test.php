<?php
declare(strict_types=1);
/**
 * Sweep — automatic emails through Loops (loops/loops.php), on a throwaway SQLite database and a stand-in Loops
 * (tests/loops_mock.php on a free port, never the real Loops):
 *   php tests/loops_test.php
 *  - off without a key; nothing before the first run, which creates the contact properties and marks what existing
 *    traders already did (a trader with 12 trades never gets « first trade »);
 *  - each event « once » leaves once: sign-up, profile, first account (its firm), first trade, 10th / 50th / 100th trade,
 *    first payout, even after a delete and a new add; copies once, sample data never; an import: the highest milestone;
 *  - every event carries the contact: userId, email, names, language, plan, isPaying, isDiscordCrew, proTrialEndsAt, lastLoginAt;
 *  - Stripe: subscriptionStarted (plan, interval), subscriptionCanceled (asked, or stopped right away), paymentFailed;
 *    referralRewarded;
 *  - the daily steps, run after run at 7:30 New York time: absences of 7 / 14 / 30 days once per absence, the Pro trial
 *    30 / 10 / 3 days before its end and its end, never for the Discord crew, a permanent access or a trader who pays;
 *    missed days caught up without sending twice;
 *  - a wrong key, no answer or a slow Loops: nothing breaks, the error is logged, the claim is given back;
 *  - an account deleted: its Loops contact and its lines go.
 */
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
$app = dirname(__DIR__);
$tmp = sys_get_temp_dir() . '/sweep-loops-' . bin2hex(random_bytes(4)); mkdir($tmp);
ini_set('error_log', $tmp . '/php.log'); putenv('SWEEP_TEST_DB=' . $tmp . '/t.db');
$pdo = new PDO('sqlite:' . $tmp . '/t.db', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC]);
$pdo->exec('CREATE TABLE users (id TEXT PRIMARY KEY, username TEXT, email TEXT, first_name TEXT, last_name TEXT, lang TEXT, created_at TEXT, last_login TEXT, disabled INTEGER NOT NULL DEFAULT 0, utm_campaign TEXT)');
$pdo->exec('CREATE TABLE documents (user_id TEXT NOT NULL, collection TEXT NOT NULL, id TEXT NOT NULL, data TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL, PRIMARY KEY (user_id, collection, id))');
$pdo->exec('CREATE TABLE app_settings (k TEXT PRIMARY KEY, v TEXT NOT NULL)');
function db(): PDO { global $pdo; return $pdo; }
function billing_on(): bool { return true; }
require $app . '/billing/billing-core.php';
require $app . '/billing/billing-stripe.php';
require $app . '/notify/notify.php';          // Events, nt_doc_event (the app's document events)
require $app . '/growth/referral.php';
require $app . '/loops/loops.php';
$D = 86400; $NY = new DateTimeZone('America/New_York');
$T0 = strtotime('2026-11-02T12:00:00Z');      // Monday Nov 2, 7:00 in New York (winter time)
sb_set_config(['live' => true, 'launch_at' => '2026-10-01T00:00:00Z', 'prelaunch_plan' => 'elite', 'comp_users' => ['u_cfg' => 'elite'], 'test_users' => [],
    'trial' => ['plan' => 'pro', 'days' => 60], 'early_access_grant' => ['plan' => 'pro', 'days' => 60], 'campaign_grants' => [], 'past_due_grace_days' => 7,
    'stripe_prices' => ['pro' => ['month' => 'price_pm', 'year' => 'price_py'], 'elite' => ['month' => 'price_em', 'year' => 'price_ey']], 'stripe_founding_coupon' => '',
    'display_prices' => ['pro' => ['month' => 19], 'elite' => ['month' => 39]], 'currency' => 'USD']);
$GLOBALS['SB_NOW'] = $T0;
sb_schema($pdo);

$pass = 0; $fail = 0;
$ok = function (bool $c, string $what) use (&$pass, &$fail) { echo ($c ? 'ok   ' : 'FAIL ') . $what . "\n"; $c ? $pass++ : $fail++; };

// the stand-in Loops
$sock = stream_socket_server('tcp://127.0.0.1:0'); $port = (int) substr(strrchr(stream_socket_get_name($sock, false), ':'), 1); fclose($sock);
$mock = proc_open([PHP_BINARY, '-S', "127.0.0.1:$port", $app . '/tests/loops_mock.php'], [['file', '/dev/null', 'r'], ['file', '/dev/null', 'w'], ['file', '/dev/null', 'w']], $pp, null, ['LOOPS_MOCK_DIR' => $tmp, 'PHP_CLI_SERVER_WORKERS' => '4']);
for ($i = 0; $i < 50 && !@fsockopen('127.0.0.1', $port); $i++) usleep(100000);
$URL = "http://127.0.0.1:$port/api/v1";
$calls = function () use ($tmp): array { return is_file("$tmp/calls.jsonl") ? array_map(fn($l) => json_decode($l, true), file("$tmp/calls.jsonl", FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES)) : []; };
$events = function (?string $name = null, ?string $uid = null) use ($calls): array {
    return array_values(array_filter($calls(), fn($c) => $c['path'] === '/api/v1/events/send' && $c['key'] === 'test-key' && ($name === null || ($c['body']['eventName'] ?? '') === $name) && ($uid === null || ($c['body']['userId'] ?? '') === $uid)));
};
$puts = fn(string $uid) => count(array_filter($calls(), fn($c) => $c['path'] === '/api/v1/contacts/update' && ($c['body']['userId'] ?? '') === $uid));
$iso = fn(int $t) => gmdate('Y-m-d\TH:i:s\Z', $t);
$user = function (string $id, array $x = []) use ($pdo, $iso, $T0) {
    $pdo->prepare('INSERT INTO users (id, username, email, first_name, last_name, lang, created_at, last_login) VALUES (?, ?, ?, ?, ?, ?, ?, ?)')
        ->execute([$id, $id, $x['email'] ?? "$id@t.dev", $x['first'] ?? null, $x['last'] ?? null, $x['lang'] ?? 'en', $iso($x['created'] ?? $T0), $iso($x['seen'] ?? ($x['created'] ?? $T0))]);
};
$doc = function (string $uid, string $col, string $id, array $d, bool $event = true) use ($pdo, $iso) {
    $prev = $pdo->prepare('SELECT data FROM documents WHERE user_id = ? AND collection = ? AND id = ?'); $prev->execute([$uid, $col, $id]); $p = $prev->fetchColumn();
    $pdo->prepare('INSERT OR REPLACE INTO documents (user_id, collection, id, data, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)')->execute([$uid, $col, $id, json_encode($d), $iso(time()), $iso(time())]);
    if ($event) nt_doc_event($uid, $col, $id, $d, $p !== false ? json_decode((string) $p, true) : null);
};
$del = function (string $uid, string $col, string $id) use ($pdo) {
    $prev = $pdo->prepare('SELECT data FROM documents WHERE user_id = ? AND collection = ? AND id = ?'); $prev->execute([$uid, $col, $id]); $p = $prev->fetchColumn();
    $pdo->prepare('DELETE FROM documents WHERE user_id = ? AND collection = ? AND id = ?')->execute([$uid, $col, $id]);
    nt_doc_event($uid, $col, $id, null, json_decode((string) $p, true));
};
$trade = fn(int $i, array $x = []) => $x + ['account_id' => 'a1', 'instrument' => 'NQ', 'direction' => 'long', 'contracts' => 1, 'pnl_c' => 1000, 'date' => '2026-11-02'];
$rows = fn(string $uid) => $pdo->query('SELECT event_name FROM email_events_log WHERE user_id = ' . $pdo->quote($uid) . ' ORDER BY event_name')->fetchAll(PDO::FETCH_COLUMN);

// 1. off without a key: nothing sent, nothing written, nothing breaks
loops_cfg(['api_key' => '', 'api_url' => $URL]);
$user('u_off');
$ok(!loops_on() && !loops_once('u_off', 'signedUp') && $calls() === [] && !$pdo->query("SELECT name FROM sqlite_master WHERE name = 'email_events_log'")->fetchColumn(), 'no key: off, no call, no table');
// 2. a key, but before the first run: nothing either
loops_cfg(['api_key' => 'test-key', 'api_url' => $URL, 'timeout' => 2]);
$ok(loops_on() && !loops_ready() && !loops_once('u_off', 'signedUp') && $calls() === [], 'a key but no first run yet: nothing sent');

// 3. the first run: contact properties, then what existing traders already did
$user('u_old', ['first' => 'Max']);
$doc('u_old', 'accounts', 'a1', ['name' => 'Topstep 50K', 'firm_id' => 'f1'], false);
for ($i = 1; $i <= 12; $i++) $doc('u_old', 'trades', "t$i", $trade($i), false);
$doc('u_old', 'payouts', 'p1', ['net_c' => 50000, 'status' => 'paid'], false);
$doc('u_old', 'trades', 'demo1', $trade(0, ['demo' => true]), false);
$r = loops_init();
$created = array_column(array_filter($calls(), fn($c) => $c['method'] === 'POST' && $c['path'] === '/api/v1/contacts/properties'), 'body');
$ok($r['error'] === null && loops_ready(), 'first run: Loops ready');
$ok(array_column($created, 'type', 'name') === LOOPS_PROPS, 'first run: the 6 contact properties created with their type (' . json_encode(array_column($created, 'type', 'name')) . ')');
$ok($rows('u_old') === ['firstAccountAdded', 'firstPayoutLogged', 'firstTradeLogged', 'profileCompleted', 'signedUp', 'tradesMilestone:10'], 'first run: what u_old already did is marked (' . implode(', ', $rows('u_old')) . ')');
$ok($events() === [], 'first run: no event sent for the past');
$ok(loops_init()['created'] === [], 'a second first run creates nothing again');
$doc('u_old', 'trades', 't13', $trade(13));
$ok($events(null, 'u_old') === [], 'u_old adds his 13th trade: no « first trade », no milestone');

// 4. a new trader, step by step
$GLOBALS['SB_NOW'] = $T0 + 3600;
$user('u_new', ['lang' => 'fr', 'created' => $T0 + 3600]);
sb_user($pdo, 'u_new', $T0 + 3600, 'u_new@t.dev');
$ok(loops_once('u_new', 'signedUp', fn(array $c) => ['language' => $c['language'], 'plan' => $c['plan']]) && !loops_once('u_new', 'signedUp'), 'signedUp: claimed once, the second time refused');
$e = $events('signedUp', 'u_new');
$b = $e[0]['body'] ?? [];
$ok(count($e) === 1 && $b['eventProperties'] === ['language' => 'fr', 'plan' => 'pro'], 'signedUp sent once, with language and plan (' . json_encode($b['eventProperties'] ?? null) . ')');
$ok($b['userId'] === 'u_new' && $b['email'] === 'u_new@t.dev' && $b['language'] === 'fr' && $b['plan'] === 'pro' && $b['isPaying'] === false && $b['isDiscordCrew'] === false
    && $b['proTrialEndsAt'] === ($T0 + 3600 + 60 * $D) * 1000 && $b['lastLoginAt'] === ($T0 + 3600) * 1000 && !isset($b['firstName']), 'the event carries the contact: language, plan, isPaying, isDiscordCrew, proTrialEndsAt and lastLoginAt in ms');
$pdo->exec("UPDATE users SET first_name = 'Léa', last_name = 'Roy' WHERE id = 'u_new'");
$ok(loops_once('u_new', 'profileCompleted') && !loops_once('u_new', 'profileCompleted'), 'profileCompleted: once');
$b = $events('profileCompleted', 'u_new')[0]['body'] ?? [];
$ok(($b['firstName'] ?? '') === 'Léa' && ($b['lastName'] ?? '') === 'Roy' && !isset($b['eventProperties']), 'profileCompleted carries the first and last name');
loops_sync('u_new');
$ok($puts('u_new') === 1, 'a later change of the profile: the contact is updated (PUT contacts/update)');
// first account: its firm, or its preset's firm when the firm arrives after the account
$doc('u_new', 'accounts', 'n1', ['name' => 'Apex 50K', 'firm_id' => 'nf1', 'preset' => 'apex|eod|50000|eval|']);
$doc('u_new', 'accounts', 'n2', ['name' => 'Topstep 50K', 'firm_id' => 'nf2']);
$e = $events('firstAccountAdded', 'u_new');
$ok(count($e) === 1 && $e[0]['body']['eventProperties'] === ['propFirm' => 'Apex Trader Funding'], 'firstAccountAdded once; the firm from the preset while the firm is not saved yet (' . json_encode($e[0]['body']['eventProperties'] ?? null) . ')');
$user('u_firm'); $doc('u_firm', 'firms', 'ff', ['name' => 'Lucid Trading'], false); $doc('u_firm', 'accounts', 'fa', ['name' => 'Lucid 25K', 'firm_id' => 'ff']);
$user('u_perso'); $doc('u_perso', 'accounts', 'pa', ['name' => 'IBKR']);
$doc('u_new', 'accounts', 'demoA', ['name' => 'Sample', 'demo' => true]);
$ok(($events('firstAccountAdded', 'u_firm')[0]['body']['eventProperties']['propFirm'] ?? '') === 'Lucid Trading' && ($events('firstAccountAdded', 'u_perso')[0]['body']['eventProperties']['propFirm'] ?? null) === '',
    'propFirm: the firm saved in Sweep; empty for a personal account');
// trades: sample data never, the first one, copies once, delete and add again
$doc('u_new', 'trades', 'demoT', $trade(0, ['demo' => true]));
$ok($events('firstTradeLogged', 'u_new') === [], 'a sample trade never counts');
$doc('u_new', 'trades', 'n-t1', $trade(1));
$del('u_new', 'trades', 'n-t1');
$doc('u_new', 'trades', 'n-t1b', $trade(1));
$ok(count($events('firstTradeLogged', 'u_new')) === 1, 'firstTradeLogged once, not again after the first trade is deleted and added again');
for ($i = 2; $i <= 9; $i++) { $doc('u_new', 'trades', "n-c$i-a", $trade($i, ['copy_group' => "g$i", 'account_id' => 'n1'])); $doc('u_new', 'trades', "n-c$i-b", $trade($i, ['copy_group' => "g$i", 'account_id' => 'n2'])); }
$ok($events('tradesMilestone', 'u_new') === [] && loops_trade_count('u_new') === 9, '9 trades, 8 of them copied on 2 accounts (17 documents): no milestone yet');
$doc('u_new', 'trades', 'n-t10', $trade(10));
$e = $events('tradesMilestone', 'u_new');
$ok(count($e) === 1 && $e[0]['body']['eventProperties'] === ['milestone' => 10], 'the 10th trade: tradesMilestone 10');
$doc('u_new', 'trades', 'n-t10', $trade(10, ['note' => 'edited']));
$del('u_new', 'trades', 'n-t10'); $doc('u_new', 'trades', 'n-t10c', $trade(10));
$ok(count($events('tradesMilestone', 'u_new')) === 1, 'an edit, then the 10th deleted and added again: not twice');
// an import that jumps from 10 to 120: only the highest step left (50 is marked, never sent later)
for ($i = 11; $i <= 120; $i++) $doc('u_new', 'trades', "n-i$i", $trade($i), $i === 120);
$e = array_map(fn($x) => $x['body']['eventProperties']['milestone'], $events('tradesMilestone', 'u_new'));
$ok($e === [10, 100] && in_array('tradesMilestone:50', $rows('u_new'), true), 'an import from 10 to 120 trades: tradesMilestone 100 only, 50 marked as passed (' . json_encode($e) . ')');
$user('u_imp'); for ($i = 1; $i <= 60; $i++) $doc('u_imp', 'trades', "i$i", $trade($i), $i === 60);
$ok(count($events('firstTradeLogged', 'u_imp')) === 1 && array_map(fn($x) => $x['body']['eventProperties']['milestone'], $events('tradesMilestone', 'u_imp')) === [50], 'a first import of 60 trades: firstTradeLogged and tradesMilestone 50');
// payouts: the estimate of « Your real net » is not a payout
$doc('u_new', 'payouts', 'est-payouts', ['net_c' => 100000, 'status' => 'paid', 'estimated' => true]);
$ok($events('firstPayoutLogged', 'u_new') === [], 'the estimated payout of « Your real net »: no firstPayoutLogged');
$doc('u_new', 'payouts', 'np1', ['net_c' => 80000, 'status' => 'requested']);
$doc('u_new', 'payouts', 'np2', ['net_c' => 80000, 'status' => 'paid']);
$ok(count($events('firstPayoutLogged', 'u_new')) === 1, 'firstPayoutLogged once (a payout entered, whatever its status)');
$ok(loops_claim('u_x', 'k', 1) && !loops_claim('u_x', 'k', 2), 'a claim is taken once (one statement)');

// 5. Stripe
$user('u_pay'); sb_user($pdo, 'u_pay', $T0, 'u_pay@t.dev');
$sub = ['id' => 'sub_1', 'customer' => 'cus_1', 'metadata' => ['uid' => 'u_pay'], 'items' => ['data' => [['price' => ['id' => 'price_pm']]]], 'status' => 'active', 'cancel_at_period_end' => false, 'current_period_end' => $T0 + 30 * $D];
$n0 = $puts('u_pay');
sb_handle_event($pdo, ['id' => 'evt_1', 'type' => 'customer.subscription.created', 'data' => ['object' => $sub]]);
$ok($puts('u_pay') === $n0 + 1 && $events(null, 'u_pay') === [], 'subscription created: the contact (plan) is updated, no event yet');
loops_stripe($pdo, 'invoice.paid', ['subscription' => 'sub_1', 'billing_reason' => 'subscription_create'], [], 'u_pay');
$e = $events('subscriptionStarted', 'u_pay');
$ok(count($e) === 1 && $e[0]['body']['eventProperties'] === ['plan' => 'pro', 'interval' => 'month'] && $e[0]['body']['isPaying'] === true && $e[0]['body']['plan'] === 'pro', 'first invoice paid: subscriptionStarted (pro, month), isPaying');
loops_stripe($pdo, 'invoice.paid', ['subscription' => 'sub_1', 'billing_reason' => 'subscription_cycle'], [], 'u_pay');
$ok(count($events('subscriptionStarted', 'u_pay')) === 1, 'a renewal: no new subscriptionStarted');
loops_stripe($pdo, 'invoice.payment_failed', ['parent' => ['subscription_details' => ['subscription' => 'sub_1']]], [], 'u_pay');
$ok(($events('paymentFailed', 'u_pay')[0]['body']['eventProperties'] ?? null) === ['plan' => 'pro'], 'payment failed: paymentFailed (pro)');
sb_handle_event($pdo, ['id' => 'evt_2', 'type' => 'customer.subscription.updated', 'data' => ['object' => ['cancel_at_period_end' => true] + $sub, 'previous_attributes' => ['cancel_at_period_end' => false]]]);
$ok(($events('subscriptionCanceled', 'u_pay')[0]['body']['eventProperties'] ?? null) === ['plan' => 'pro'], 'cancellation asked (end of the period): subscriptionCanceled (pro)');
sb_handle_event($pdo, ['id' => 'evt_3', 'type' => 'customer.subscription.updated', 'data' => ['object' => ['cancel_at_period_end' => true, 'current_period_end' => $T0 + 31 * $D] + $sub, 'previous_attributes' => ['current_period_end' => $T0 + 30 * $D]]]);
sb_handle_event($pdo, ['id' => 'evt_4', 'type' => 'customer.subscription.deleted', 'data' => ['object' => ['cancel_at_period_end' => true, 'status' => 'canceled'] + $sub]]);
$ok(count($events('subscriptionCanceled', 'u_pay')) === 1, 'another change, then the end of the period: not announced twice');
$sub2 = ['id' => 'sub_2', 'items' => ['data' => [['price' => ['id' => 'price_ey']]]], 'status' => 'canceled', 'cancel_at_period_end' => false] + $sub;
sb_handle_event($pdo, ['id' => 'evt_5', 'type' => 'customer.subscription.deleted', 'data' => ['object' => $sub2]]);
$ok(($events('subscriptionCanceled', 'u_pay')[1]['body']['eventProperties'] ?? null) === ['plan' => 'elite'], 'a subscription stopped right away: subscriptionCanceled (elite)');
sb_handle_event($pdo, ['id' => 'evt_5', 'type' => 'customer.subscription.deleted', 'data' => ['object' => $sub2]]);
$ok(count($events('subscriptionCanceled', 'u_pay')) === 2, 'the same Stripe event twice: once');
// referral: the referrer earns a month
$user('u_ref'); $user('u_friend');
ref_schema($pdo); $pdo->exec("INSERT INTO referrals (referrer_id, referee_id, status, created_at) VALUES ('u_ref', 'u_friend', 'pending', $T0)");
ref_reward($pdo, $pdo->query("SELECT * FROM referrals WHERE referee_id = 'u_friend'")->fetch(), 'activity');
$ok(count($events('referralRewarded', 'u_ref')) === 1 && $events(null, 'u_friend') === [], 'referral rewarded: referralRewarded to the referrer');

// 6. the daily steps, run after run at 7:30 in New York
$pdo->exec('DELETE FROM users'); $pdo->exec('DELETE FROM email_events_log'); @unlink("$tmp/calls.jsonl");
$GLOBALS['SB_NOW'] = $T0;
$seen = strtotime('2026-11-02T20:00:00Z');   // last visit: Monday 15:00 in New York
foreach (['u_abs', 'u_trial', 'u_paying', 'u_crew', 'u_cfg', 'u_comp', 'u_gap', 'u_gap2', 'u_ea'] as $id) { $user($id, ['seen' => $id === 'u_trial' ? $T0 + 400 * $D : $seen]); sb_user($pdo, $id, $T0, "$id@t.dev"); }
$pdo->exec("UPDATE billing_grants SET reason = 'early_access' WHERE uid = 'u_ea'");
$pdo->exec("INSERT INTO billing_subs (id, uid, source, plan, billing_interval, status, updated_at) VALUES ('sub_p', 'u_paying', 'stripe', 'pro', 'year', 'active', $T0)");
sb_grant($pdo, 'u_crew', 'elite', 36500, 'comp'); sb_grant($pdo, 'u_comp', 'pro', 36500, 'comp'); sb_grant($pdo, 'u_abs', 'elite', 30, 'comp');
$b = loops_billing('u_crew', ['created_at' => $iso($T0), 'email' => 'x']);
$ok($b['crew'] && $b['permanent'] && !loops_billing('u_comp', ['created_at' => $iso($T0)])['crew'] && loops_billing('u_cfg', ['created_at' => $iso($T0)])['crew'] && !loops_billing('u_abs', ['created_at' => $iso($T0)])['crew'],
    'Discord crew = Elite for life (Admin « Permanent » or config); a permanent Pro or a 30-day Elite is not');
$runs = [];   // day => [uid:event…]
$prevOf = [];   // each trader's previous run (the cron's window: since its previous successful run)
for ($d = 0; $d <= 64; $d++) {
    $day = (new DateTimeImmutable('2026-11-03 07:30', $NY))->modify("+$d days");
    $now = $day->getTimestamp(); $GLOBALS['SB_NOW'] = $now;
    $k = $day->format('Y-m-d');
    if ($d === 33) $pdo->exec("UPDATE users SET last_login = '" . $iso(strtotime('2026-12-05T15:00:00Z')) . "' WHERE id = 'u_abs'");   // came back on Dec 5
    $n = count($events());
    foreach (['u_abs', 'u_trial', 'u_paying', 'u_crew', 'u_cfg', 'u_comp', 'u_ea', 'u_gap', 'u_gap2'] as $id) {
        if ($id === 'u_gap' && $k >= '2026-11-08' && $k <= '2026-11-10') continue;    // server down 3 days
        if ($id === 'u_gap2' && $k >= '2026-11-09' && $k <= '2026-11-16') continue;   // server down 8 days
        $r = loops_daily_run([$id], $prevOf[$id] ?? $now - $D, $now);
        if ($r['failed']) echo "  $k $id failed: {$r['error']}\n";
        $prevOf[$id] = $now;
    }
    foreach (array_slice($events(), $n) as $x) $runs[$k][] = $x['body']['userId'] . ':' . $x['body']['eventName'] . ($x['body']['eventProperties']['daysLeft'] ?? '');
}
$when = function (string $what) use ($runs): array { $o = []; foreach ($runs as $k => $l) foreach ($l as $x) if ($x === $what) $o[] = $k; return $o; };
$ok($when('u_abs:inactive3d') === ['2026-11-06', '2026-12-09'] && $when('u_abs:inactive7d') === ['2026-11-10', '2026-12-13'] && $when('u_abs:inactive14d') === ['2026-11-17', '2026-12-20'] && $when('u_abs:inactive30d') === ['2026-12-03', '2027-01-05'],
    'absence: 3 days (Nov 6), 7 (Nov 10), 14 (Nov 17), 30 (Dec 3) after Monday 15:00; back on Dec 5, a new absence: Dec 9, Dec 13, Dec 20, Jan 5 (' . json_encode([$when('u_abs:inactive3d'), $when('u_abs:inactive7d'), $when('u_abs:inactive14d'), $when('u_abs:inactive30d')]) . ')');
$ok($when('u_trial:proTrialDaysLeft30') === ['2026-12-02'] && $when('u_trial:proTrialDaysLeft10') === ['2026-12-22'] && $when('u_trial:proTrialDaysLeft3') === ['2026-12-29'] && $when('u_trial:proTrialEnded') === ['2027-01-01'],
    'Pro trial (ends Jan 1, 7:00 New York): 30 days left Dec 2, 10 Dec 22, 3 Dec 29, ended Jan 1');
$ok($when('u_ea:proTrialEnded') === ['2027-01-01'], 'an early-access Pro (free Pro from the launch) counts as the trial');
foreach (['u_paying' => 'a trader who pays', 'u_crew' => 'the Discord crew (Admin)', 'u_cfg' => 'the Discord crew (config)', 'u_comp' => 'a permanent Pro'] as $id => $who)
    $ok(array_filter(array_merge(...array_values($runs)), fn($x) => strpos($x, "$id:proTrial") === 0) === [] && $when("$id:inactive7d") === ['2026-11-10'], "never the trial steps for $who (the absences yes)");
$ok($when('u_gap:inactive7d') === ['2026-11-11'], 'server down Nov 8-10: the 7-day absence (due Nov 9) is caught up on Nov 11, once');
$ok($when('u_gap2:inactive7d') === [] && $when('u_gap2:inactive14d') === ['2026-11-17'], 'down Nov 9-16: 7 and 14 days came due together, only the 14-day one is sent');
$ok($when('u_trial:inactive7d') === [], 'a trader seen recently: no absence');
$twice = array_keys(array_filter(array_count_values(array_merge(...array_values($runs))), fn($n) => $n > 1));
$ok($twice === ['u_abs:inactive3d', 'u_abs:inactive7d', 'u_abs:inactive14d', 'u_abs:inactive30d'], 'no step sent twice, except the absences of u_abs: once per absence (' . json_encode($twice) . ')');
$e = $events('proTrialDaysLeft', 'u_trial')[0]['body'] ?? [];
$ok(($e['eventProperties'] ?? null) === ['daysLeft' => 30] && $e['plan'] === 'pro', 'proTrialDaysLeft carries daysLeft and the contact');
$ok(($events('proTrialEnded', 'u_trial')[0]['body']['plan'] ?? '') === 'free', 'proTrialEnded: the contact says plan free');
// a manual run the same moment again: nothing twice
$GLOBALS['SB_NOW'] = (new DateTimeImmutable('2027-01-01 07:30', $NY))->getTimestamp(); $n = count($events());
loops_daily_run(['u_trial'], $GLOBALS['SB_NOW'] - $D, $GLOBALS['SB_NOW']);
$ok(count($events()) === $n, 'the same run again: nothing sent twice');
// dry run
$GLOBALS['SB_NOW'] = (new DateTimeImmutable('2027-02-01 07:30', $NY))->getTimestamp(); $said = [];
$pdo->exec("UPDATE users SET last_login = '" . $iso($GLOBALS['SB_NOW'] - 7 * $D - 3600) . "' WHERE id = 'u_trial'");
loops_daily_run(['u_trial'], $GLOBALS['SB_NOW'] - $D, $GLOBALS['SB_NOW'], true, function (string $s) use (&$said) { $said[] = $s; });
$ok($said === ['would send: inactive7d → u_trial'] && count($events()) === $n && !loops_logged('u_trial', 'inactive7d', $GLOBALS['SB_NOW'] - 8 * $D), 'dry run: says what would leave, sends and writes nothing');

// 7. Loops refuses or does not answer: nothing breaks, logged, the claim given back
loops_cfg(['api_key' => 'wrong-key', 'api_url' => $URL, 'timeout' => 2]);
$user('u_err');
$ok(loops_once('u_err', 'signedUp') && $rows('u_err') === [], 'wrong key: the app carries on, the claim is given back (sent at the next occasion)');
$r = loops_daily_run(['u_trial'], $GLOBALS['SB_NOW'] - $D, $GLOBALS['SB_NOW']);
$ok($r['failed'] === 1 && strpos($r['error'], '401') !== false && !loops_logged('u_trial', 'inactive7d', $GLOBALS['SB_NOW'] - 8 * $D), 'wrong key in the daily run: counted as failed (' . $r['error'] . '), not marked as sent');
$log = (string) @file_get_contents("$tmp/php.log");
$ok(strpos($log, '[Sweep loops] signedUp u_err: 401 Invalid API key') !== false, 'the refusal is in the PHP error log');
loops_cfg(['api_key' => 'test-key', 'api_url' => $URL, 'timeout' => 2]);
$r = loops_daily_run(['u_trial'], $GLOBALS['SB_NOW'] - $D, $GLOBALS['SB_NOW']);
$ok($r['failed'] === 0 && ($r['sent']['inactive7d'] ?? 0) === 1, 'the next run with the right key sends it');
loops_cfg(['api_key' => 'test-key', 'api_url' => 'http://127.0.0.1:1/api/v1', 'timeout' => 2]);
$t = microtime(true);
$ok(loops_once('u_err', 'signedUp') && $rows('u_err') === [] && microtime(true) - $t < 3, 'no answer (nothing listening): fails fast, claim given back');
loops_cfg(['api_key' => 'test-key', 'api_url' => $URL, 'timeout' => 1]);
$t = microtime(true);
$ok(!loops_call('POST', 'events/send', ['userId' => 'u_err', 'eventName' => 'x', 'slow' => true], 'slow') && microtime(true) - $t < 2.5, sprintf('a Loops that hangs: given up after the timeout (%.1f s)', microtime(true) - $t));

// 8. account deleted: its contact and its lines go
loops_cfg(['api_key' => 'test-key', 'api_url' => $URL, 'timeout' => 2]);
$pdo->exec("INSERT INTO email_events_log (user_id, event_name, sent_at) VALUES ('u_trial', 'signedUp', 1)");
loops_forget('u_trial');
$last = array_values(array_filter($calls(), fn($c) => $c['path'] === '/api/v1/contacts/delete'));
$ok(count($last) === 1 && $last[0]['body'] === ['email' => 'u_trial@t.dev'] && $rows('u_trial') === [], 'account deleted: contact deleted in Loops, its lines of email_events_log gone');

$mp = (int) (proc_get_status($mock)['pid'] ?? 0); if ($mp) exec('pkill -TERM -P ' . $mp);   // php -S with workers: its children first (proc_terminate stops only the parent)
proc_terminate($mock); proc_close($mock);
usleep(500000); exec('pgrep -f ' . escapeshellarg("[1]27.0.0.1:$port"), $left);   // [1]: the sh -c running pgrep has the text in its own command line (Linux counted it)
$ok(!$left, 'the mock Loops server is stopped, its workers too (' . count($left) . ' left; before 16 Oct.: 4 every run)');
foreach (glob($tmp . '/*') as $x) @unlink($x); @rmdir($tmp);
echo "\n$pass passed, $fail failed\n";
exit($fail ? 1 : 0);
