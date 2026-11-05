<?php
declare(strict_types=1);
/**
 * Sweep — the automatic emails (mail/mail-auto.php), on a throwaway SQLite database, nothing sent for real:
 *   php tests/mail_auto_test.php
 *  - nothing before the first run, which marks what existing traders already did (a trader with 12 trades never gets
 *    « first trade »); after Loops, its marks are kept and the past is not marked again;
 *  - the 24 automations are seeded once with their EN / FR / ES text, never overwritten; the 4 first steps of day one and the
 *    5 feedback emails (tests/mail_feedback_test.php) and « Sweep on your phone » (5 Nov.) off;
 *  - each event « once » is queued once: sign-up, profile, first account ({firm}), first trade, 10th / 50th / 100th trade,
 *    first payout, first plan, even after a delete and a new add; copies once, sample data never; an import: the highest milestone;
 *  - Stripe: subscriptionStarted, subscriptionCanceled (asked, or stopped right away), paymentFailed {plan}; referralRewarded;
 *  - the daily steps, run after run at 7:30 New York time: absences of 3 / 7 / 14 / 30 days once per absence, the Pro trial
 *    30 / 10 / 3 days before its end and its end, never for the Discord crew, a permanent access or a trader who pays;
 *    missed days caught up without sending twice; the evening of day one at 18:30 New York, not after a plan, given up late;
 *  - an automation switched off: claimed, nothing queued; switched off after queueing: not sent;
 *  - the queue: the text in the trader's language with its values, the unsubscribe respected for news, never for an
 *    email about the account; « Your week » and the password reset as ready emails; mail/send-cron.php runs it all;
 *  - an account deleted: its lines go.
 */
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
$app = dirname(__DIR__);
$tmp = sys_get_temp_dir() . '/sweep-mail-auto-' . bin2hex(random_bytes(4)); mkdir($tmp);
ini_set('error_log', $tmp . '/php.log'); putenv('SWEEP_TEST_DB=' . $tmp . '/t.db');
$pdo = new PDO('sqlite:' . $tmp . '/t.db', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC]);
$pdo->exec('CREATE TABLE users (id TEXT PRIMARY KEY, username TEXT, email TEXT, first_name TEXT, last_name TEXT, lang TEXT, created_at TEXT, last_login TEXT, disabled INTEGER NOT NULL DEFAULT 0, is_admin INTEGER NOT NULL DEFAULT 0, is_internal INTEGER NOT NULL DEFAULT 0, utm_campaign TEXT)');
$pdo->exec('CREATE TABLE documents (user_id TEXT NOT NULL, collection TEXT NOT NULL, id TEXT NOT NULL, data TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL, PRIMARY KEY (user_id, collection, id))');
$pdo->exec('CREATE TABLE app_settings (k TEXT PRIMARY KEY, v TEXT NOT NULL)');
function db(): PDO { global $pdo; return $pdo; }
function billing_on(): bool { return true; }
$GLOBALS['cfg'] = ['app_url' => 'https://app.makeitsweep.com'];
require $app . '/billing/billing-core.php';
require $app . '/billing/billing-stripe.php';
require $app . '/notify/notify.php';          // Events, nt_doc_event (the app's document events)
require $app . '/growth/referral.php';
require $app . '/mail/mail-core.php';
require $app . '/mail/mail-auto.php';
$D = 86400; $NY = new DateTimeZone('America/New_York');
$T0 = strtotime('2026-11-02T12:00:00Z');      // Monday Nov 2, 7:00 in New York (winter time)
sb_set_config(['live' => true, 'launch_at' => '2026-10-01T00:00:00Z', 'prelaunch_plan' => 'elite', 'comp_users' => ['u_cfg' => 'elite'], 'test_users' => [],
    'trial' => ['plan' => 'pro', 'days' => 60], 'early_access_grant' => ['plan' => 'pro', 'days' => 60], 'campaign_grants' => [], 'past_due_grace_days' => 7,
    'stripe_prices' => ['pro' => ['month' => 'price_pm', 'year' => 'price_py'], 'elite' => ['month' => 'price_em', 'year' => 'price_ey']], 'stripe_founding_coupon' => '',
    'display_prices' => ['pro' => ['month' => 19], 'elite' => ['month' => 39]], 'currency' => 'USD']);
$GLOBALS['SB_NOW'] = $T0;
sb_schema($pdo); ml_schema($pdo);

$pass = 0; $fail = 0;
$ok = function (bool $c, string $what) use (&$pass, &$fail) { echo ($c ? 'ok   ' : 'FAIL ') . $what . "\n"; $c ? $pass++ : $fail++; };
// what went into the queue for an automation (and a trader): its values
$events = function (?string $name = null, ?string $uid = null) use ($pdo): array {
    $r = $pdo->query('SELECT q.user_id, q.kind, q.vars_json, q.lang, c.auto FROM mail_queue q JOIN mail_campaigns c ON c.id = q.campaign_id WHERE c.auto IS NOT NULL ORDER BY q.id')->fetchAll();
    return array_values(array_map(fn($x) => ['uid' => $x['user_id'], 'name' => $x['auto'], 'kind' => $x['kind'], 'lang' => $x['lang'], 'vars' => json_decode((string) $x['vars_json'], true) ?: []],
        array_filter($r, fn($x) => ($name === null || $x['auto'] === $name) && ($uid === null || $x['user_id'] === $uid))));
};
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
$autoSet = fn(string $key, bool $on) => $pdo->prepare('UPDATE mail_campaigns SET status = ? WHERE auto = ?')->execute([$on ? 'active' : 'off', $key]);

// 1. the automations, seeded once
ma_seed($pdo);
$a = $pdo->query('SELECT auto, status, content_json FROM mail_campaigns WHERE auto IS NOT NULL')->fetchAll();
$st = array_column($a, 'status', 'auto');
$ok(count($a) === 24 && count(array_filter($a, fn($r) => array_map(fn($v) => $v['subject'] !== '' && $v['body'] !== '', json_decode($r['content_json'], true)) === ['en' => true, 'fr' => true, 'es' => true])) === 24,
    '24 automations, each with a subject and a body in EN, FR and ES');
$ok(array_keys(array_filter($st, fn($s) => $s === 'off')) === ['profileCompleted', 'firstAccountAdded', 'firstPlanSaved', 'firstTradeLogged', 'weekOne', 'nps30', 'featureDiscover', 'feedbackShipped', 'months3', 'phoneInstall'], 'the 4 first steps of day one and the 5 feedback emails start off, the 14 others on');
$pdo->exec("UPDATE mail_campaigns SET content_json = '{\"en\":{\"subject\":\"Mine\",\"preheader\":\"\",\"body\":\"Edited\"}}' WHERE auto = 'inactive30d'");
ma_seed($pdo);
$ok(strpos((string) $pdo->query("SELECT content_json FROM mail_campaigns WHERE auto = 'inactive30d'")->fetchColumn(), 'Edited') !== false && (int) $pdo->query('SELECT COUNT(*) FROM mail_campaigns WHERE auto IS NOT NULL')->fetchColumn() === 24,
    'a text edited in Admin is never overwritten, nothing added twice');
foreach (['profileCompleted', 'firstAccountAdded', 'firstPlanSaved', 'firstTradeLogged'] as $k) $autoSet($k, true);   // all on for the steps below

// 2. before the first run: nothing
$user('u_off');
$ok(!ma_ready() && !ma_once('u_off', 'signedUp') && $events() === [], 'before the first run: nothing queued');

// 3. the first run: what existing traders already did
$user('u_old', ['first' => 'Max']);
$doc('u_old', 'accounts', 'a1', ['name' => 'Topstep 50K', 'firm_id' => 'f1'], false);
for ($i = 1; $i <= 12; $i++) $doc('u_old', 'trades', "t$i", $trade($i), false);
$doc('u_old', 'payouts', 'p1', ['net_c' => 50000, 'status' => 'paid'], false);
$doc('u_old', 'trades', 'demo1', $trade(0, ['demo' => true]), false);
ma_init();
$ok(ma_ready(), 'first run: ready');
$ok($rows('u_old') === ['day1Evening', 'firstAccountAdded', 'firstPayoutLogged', 'firstTradeLogged', 'profileCompleted', 'signedUp', 'tradesMilestone:10'], 'first run: what u_old already did is marked (' . implode(', ', $rows('u_old')) . ')');
$ok($events() === [], 'first run: nothing queued for the past');
$doc('u_old', 'trades', 't13', $trade(13));
$ok($events(null, 'u_old') === [], 'u_old adds his 13th trade: no « first trade », no milestone');

// 4. a new trader, step by step
$GLOBALS['SB_NOW'] = $T0 + 3600;
$user('u_new', ['lang' => 'fr', 'created' => $T0 + 3600]);
sb_user($pdo, 'u_new', $T0 + 3600, 'u_new@t.dev');
$ok(ma_once('u_new', 'signedUp') && !ma_once('u_new', 'signedUp'), 'signedUp: claimed once, the second time refused');
$e = $events('signedUp', 'u_new');
$ok(count($e) === 1 && $e[0]['lang'] === 'fr' && $e[0]['kind'] === 'marketing', 'signedUp queued once, in the trader’s language, as news');
$pdo->exec("UPDATE users SET first_name = 'Léa', last_name = 'Roy' WHERE id = 'u_new'");
$ok(ma_once('u_new', 'profileCompleted') && !ma_once('u_new', 'profileCompleted') && count($events('profileCompleted', 'u_new')) === 1, 'profileCompleted: once');
$doc('u_new', 'accounts', 'n1', ['name' => 'Apex 50K', 'firm_id' => 'nf1', 'preset' => 'apex|eod|50000|eval|']);
$doc('u_new', 'accounts', 'n2', ['name' => 'Topstep 50K', 'firm_id' => 'nf2']);
$e = $events('firstAccountAdded', 'u_new');
$ok(count($e) === 1 && $e[0]['vars'] === ['firm' => 'Apex Trader Funding'], 'firstAccountAdded once; {firm} from the preset while the firm is not saved yet (' . json_encode($e[0]['vars'] ?? null) . ')');
$user('u_firm'); $doc('u_firm', 'firms', 'ff', ['name' => 'Lucid Trading'], false); $doc('u_firm', 'accounts', 'fa', ['name' => 'Lucid 25K', 'firm_id' => 'ff']);
$user('u_perso'); $doc('u_perso', 'accounts', 'pa', ['name' => 'IBKR']);
$doc('u_new', 'accounts', 'demoA', ['name' => 'Sample', 'demo' => true]);
$ok(($events('firstAccountAdded', 'u_firm')[0]['vars']['firm'] ?? '') === 'Lucid Trading' && ($events('firstAccountAdded', 'u_perso')[0]['vars']['firm'] ?? null) === '', '{firm}: the firm saved in Sweep; empty for a personal account');
$doc('u_new', 'trades', 'demoT', $trade(0, ['demo' => true]));
$ok($events('firstTradeLogged', 'u_new') === [], 'a sample trade never counts');
$doc('u_new', 'trades', 'n-t1', $trade(1));
$del('u_new', 'trades', 'n-t1');
$doc('u_new', 'trades', 'n-t1b', $trade(1));
$ok(count($events('firstTradeLogged', 'u_new')) === 1, 'firstTradeLogged once, not again after the first trade is deleted and added again');
for ($i = 2; $i <= 9; $i++) { $doc('u_new', 'trades', "n-c$i-a", $trade($i, ['copy_group' => "g$i", 'account_id' => 'n1'])); $doc('u_new', 'trades', "n-c$i-b", $trade($i, ['copy_group' => "g$i", 'account_id' => 'n2'])); }
$ok($events('tradesMilestone', 'u_new') === [] && ma_trade_count('u_new') === 9, '9 trades, 8 of them copied on 2 accounts (17 documents): no milestone yet');
$doc('u_new', 'trades', 'n-t10', $trade(10));
$e = $events('tradesMilestone', 'u_new');
$ok(count($e) === 1 && $e[0]['vars'] === ['milestone' => '10'], 'the 10th trade: tradesMilestone {milestone} 10');
$doc('u_new', 'trades', 'n-t10', $trade(10, ['note' => 'edited']));
$del('u_new', 'trades', 'n-t10'); $doc('u_new', 'trades', 'n-t10c', $trade(10));
$ok(count($events('tradesMilestone', 'u_new')) === 1, 'an edit, then the 10th deleted and added again: not twice');
for ($i = 11; $i <= 120; $i++) $doc('u_new', 'trades', "n-i$i", $trade($i), $i === 120);
$e = array_map(fn($x) => $x['vars']['milestone'], $events('tradesMilestone', 'u_new'));
$ok($e === ['10', '100'] && in_array('tradesMilestone:50', $rows('u_new'), true), 'an import from 10 to 120 trades: 100 only, 50 marked as passed (' . json_encode($e) . ')');
$user('u_imp'); for ($i = 1; $i <= 60; $i++) $doc('u_imp', 'trades', "i$i", $trade($i), $i === 60);
$ok(count($events('firstTradeLogged', 'u_imp')) === 1 && array_map(fn($x) => $x['vars']['milestone'], $events('tradesMilestone', 'u_imp')) === ['50'], 'a first import of 60 trades: firstTradeLogged and tradesMilestone 50');
$doc('u_new', 'payouts', 'est-payouts', ['net_c' => 100000, 'status' => 'paid', 'estimated' => true]);
$ok($events('firstPayoutLogged', 'u_new') === [], 'the estimated payout of « Your real net »: no firstPayoutLogged');
$doc('u_new', 'payouts', 'np1', ['net_c' => 80000, 'status' => 'requested']);
$doc('u_new', 'payouts', 'np2', ['net_c' => 80000, 'status' => 'paid']);
$ok(count($events('firstPayoutLogged', 'u_new')) === 1, 'firstPayoutLogged once (a payout entered, whatever its status)');
$doc('u_new', 'journals', '2026-10-20', ['post' => ['followed' => 'yes']]);
$ok($events('firstPlanSaved', 'u_new') === [], 'a review only: no firstPlanSaved');
$doc('u_new', 'journals', '2026-10-21', ['pre' => ['bias' => 'bullish', 'max_loss' => '500']]);
$doc('u_new', 'journals', '2026-10-22', ['pre' => ['bias' => 'bearish']]);
$ok(count($events('firstPlanSaved', 'u_new')) === 1, 'firstPlanSaved once, at the first plan');
$doc('u_imp', 'journals', 'j1', ['pre' => ['bias' => 'bullish']], false); $doc('u_imp', 'journals', 'j2', ['pre' => ['bias' => 'bullish']]);
$ok($events('firstPlanSaved', 'u_imp') === [] && in_array('firstPlanSaved', $rows('u_imp'), true), 'plans before the event existed: marked, not sent');
$ok(ma_claim('u_x', 'k', 1) && !ma_claim('u_x', 'k', 2), 'a claim is taken once (one statement)');

// 5. Stripe and referral
$user('u_pay'); sb_user($pdo, 'u_pay', $T0, 'u_pay@t.dev');
$sub = ['id' => 'sub_1', 'customer' => 'cus_1', 'metadata' => ['uid' => 'u_pay'], 'items' => ['data' => [['price' => ['id' => 'price_pm']]]], 'status' => 'active', 'cancel_at_period_end' => false, 'current_period_end' => $T0 + 30 * $D];
sb_handle_event($pdo, ['id' => 'evt_1', 'type' => 'customer.subscription.created', 'data' => ['object' => $sub]]);
$ok($events(null, 'u_pay') === [], 'subscription created: nothing yet');
ma_stripe($pdo, 'invoice.paid', ['subscription' => 'sub_1', 'billing_reason' => 'subscription_create'], [], 'u_pay');
$e = $events('subscriptionStarted', 'u_pay');
$ok(count($e) === 1 && $e[0]['vars'] === ['plan' => 'Pro'] && $e[0]['kind'] === 'transactional', 'first invoice paid: subscriptionStarted {plan} Pro, an email about the account');
ma_stripe($pdo, 'invoice.paid', ['subscription' => 'sub_1', 'billing_reason' => 'subscription_cycle'], [], 'u_pay');
$ok(count($events('subscriptionStarted', 'u_pay')) === 1, 'a renewal: no new subscriptionStarted');
ma_stripe($pdo, 'invoice.payment_failed', ['parent' => ['subscription_details' => ['subscription' => 'sub_1']]], [], 'u_pay');
$ok(($events('paymentFailed', 'u_pay')[0]['vars'] ?? null) === ['plan' => 'Pro'], 'payment failed: paymentFailed (Pro)');
sb_handle_event($pdo, ['id' => 'evt_2', 'type' => 'customer.subscription.updated', 'data' => ['object' => ['cancel_at_period_end' => true] + $sub, 'previous_attributes' => ['cancel_at_period_end' => false]]]);
$ok(($events('subscriptionCanceled', 'u_pay')[0]['vars'] ?? null) === ['plan' => 'Pro'], 'cancellation asked (end of the period): subscriptionCanceled (Pro)');
sb_handle_event($pdo, ['id' => 'evt_3', 'type' => 'customer.subscription.updated', 'data' => ['object' => ['cancel_at_period_end' => true, 'current_period_end' => $T0 + 31 * $D] + $sub, 'previous_attributes' => ['current_period_end' => $T0 + 30 * $D]]]);
sb_handle_event($pdo, ['id' => 'evt_4', 'type' => 'customer.subscription.deleted', 'data' => ['object' => ['cancel_at_period_end' => true, 'status' => 'canceled'] + $sub]]);
$ok(count($events('subscriptionCanceled', 'u_pay')) === 1, 'another change, then the end of the period: not announced twice');
$sub2 = ['id' => 'sub_2', 'items' => ['data' => [['price' => ['id' => 'price_ey']]]], 'status' => 'canceled', 'cancel_at_period_end' => false] + $sub;
sb_handle_event($pdo, ['id' => 'evt_5', 'type' => 'customer.subscription.deleted', 'data' => ['object' => $sub2]]);
$ok(($events('subscriptionCanceled', 'u_pay')[1]['vars'] ?? null) === ['plan' => 'Elite'], 'a subscription stopped right away: subscriptionCanceled (Elite)');
sb_handle_event($pdo, ['id' => 'evt_5', 'type' => 'customer.subscription.deleted', 'data' => ['object' => $sub2]]);
$ok(count($events('subscriptionCanceled', 'u_pay')) === 2, 'the same Stripe event twice: once');
$user('u_ref'); $user('u_friend');
ref_schema($pdo); $pdo->exec("INSERT INTO referrals (referrer_id, referee_id, status, created_at) VALUES ('u_ref', 'u_friend', 'pending', $T0)");
ref_reward($pdo, $pdo->query("SELECT * FROM referrals WHERE referee_id = 'u_friend'")->fetch(), 'activity');
$ok(count($events('referralRewarded', 'u_ref')) === 1 && $events(null, 'u_friend') === [], 'referral rewarded: referralRewarded to the referrer');

// 6. the queue: the email itself
$sent = []; $send = function ($to, $s, $t, $h, $hd, $tok) use (&$sent) { $sent[] = compact('to', 's', 't', 'h', 'hd'); return true; };
$drain = function (int $at) use ($pdo, &$send) { for ($i = 0; $i < 40 && ml_left($pdo) > 0; $i++) ml_run($pdo, $send, $at + $i * 60); };   // 4 news a minute at the start of the warm-up
$drain(time());
$m = array_values(array_filter($sent, fn($x) => $x['to'] === 'u_new@t.dev' && strpos($x['s'], '100') !== false));
$ok(count($m) === 1 && $m[0]['s'] === '100 trades dans ton journal' && strpos($m[0]['t'], 'Salut Léa') !== false && strpos($m[0]['h'], 'https://app.makeitsweep.com/api/m/c/') !== false && isset($m[0]['hd']['List-Unsubscribe']),
    'sent in French with its values: « 100 trades dans ton journal », « Salut Léa », tracked links, one-click unsubscribe (' . ($m[0]['s'] ?? '-') . ')');
$ok(count(array_filter($sent, fn($x) => strpos($x['hd']['Feedback-ID'] ?? '', ':auto:sweep') !== false)) === count($sent) && count($sent) === count($events()), 'every automatic email queued so far went out once (' . count($sent) . ')');
// unsubscribed: news skipped, the account emails still come
ml_set_marketing($pdo, 'u_pay', false); $sent = [];
ma_stripe($pdo, 'invoice.payment_failed', ['parent' => ['subscription_details' => ['subscription' => 'sub_1']]], [], 'u_pay');
ma_send('u_pay', 'inactive7d');
$drain(time() + 3000);
$ok(array_column($sent, 's') === ['Your payment did not go through'], 'unsubscribed: « payment failed » still sent, the news (7 days away) skipped (' . json_encode(array_column($sent, 's')) . ')');
// an automation off: claimed, nothing queued; switched off after queueing: not sent
$autoSet('firstPayoutLogged', false); $user('u_po'); $n = count($events());
$doc('u_po', 'payouts', 'x', ['net_c' => 100, 'status' => 'paid']);
$ok(count($events()) === $n && in_array('firstPayoutLogged', $rows('u_po'), true), 'an automation switched off: the moment passes (claimed), nothing queued');
$autoSet('firstPayoutLogged', true); $user('u_po2'); $doc('u_po2', 'payouts', 'x', ['net_c' => 100, 'status' => 'paid']); $autoSet('firstPayoutLogged', false); $sent = [];
$drain(time() + 3000);
$ok($sent === [] && $pdo->query("SELECT state FROM mail_queue WHERE user_id = 'u_po2'")->fetchColumn() === 'skipped', 'switched off after it was queued: not sent (skipped)');
$autoSet('firstPayoutLogged', true);
// ready emails: « Your week » (its own stop link), the password reset sent at once
[$wid] = ml_enqueue($pdo, 'u_new', 'u_new@t.dev', 'fr', 'weekly', 'Ta semaine', 'texte', '<p>html</p>', ['List-Unsubscribe' => '<https://x/stop>']);
[$rid] = ml_enqueue($pdo, 'u_new', 'u_new@t.dev', 'fr', 'transactional', 'Réinitialise', 'lien', '');
$sent = [];
$ok(ml_send_now($pdo, $rid, $send) && $pdo->query("SELECT state FROM mail_queue WHERE id = $rid")->fetchColumn() === 'sent' && ($sent[0]['s'] ?? '') === 'Réinitialise', 'the password reset: queued and sent at once');
$fails = fn() => 'soft: 451 later';
[$rid2] = ml_enqueue($pdo, 'u_new', 'u_new@t.dev', 'fr', 'transactional', 'Réinitialise 2', 'lien', '');
$ok(!ml_send_now($pdo, $rid2, $fails) && $pdo->query("SELECT state FROM mail_queue WHERE id = $rid2")->fetchColumn() === 'queued', 'not sent at once: back in the queue, the cron tries again');
$sent = []; $drain(time() + 3200);
$w = array_values(array_filter($sent, fn($x) => $x['s'] === 'Ta semaine'));
$ok(count($w) === 1 && ($w[0]['hd']['List-Unsubscribe'] ?? '') === '<https://x/stop>' && in_array('Réinitialise 2', array_column($sent, 's'), true), '« Your week » sent with its own stop link; the reset retried by the next run');
$ok(ml_hour($pdo, time() + 7200) === 0 && ml_hour($pdo, time() + 3300) === (int) $pdo->query("SELECT COUNT(*) FROM mail_queue WHERE kind IN ('marketing', 'weekly') AND state = 'sent'")->fetchColumn(), 'the hourly cap counts news and « Your week », never the account emails');

// 7. the daily steps, run after run at 7:30 in New York
$pdo->exec('DELETE FROM users'); $pdo->exec('DELETE FROM email_events_log'); $pdo->exec('DELETE FROM mail_queue');
$GLOBALS['SB_NOW'] = $T0;
$seen = strtotime('2026-11-02T20:00:00Z');   // last visit: Monday 15:00 in New York
foreach (['u_abs', 'u_trial', 'u_paying', 'u_crew', 'u_cfg', 'u_comp', 'u_gap', 'u_gap2', 'u_ea'] as $id) { $user($id, ['seen' => $id === 'u_trial' ? $T0 + 400 * $D : $seen]); sb_user($pdo, $id, $T0, "$id@t.dev"); }
$pdo->exec("UPDATE billing_grants SET reason = 'early_access' WHERE uid = 'u_ea'");
$pdo->exec("INSERT INTO billing_subs (id, uid, source, plan, billing_interval, status, updated_at) VALUES ('sub_p', 'u_paying', 'stripe', 'pro', 'year', 'active', $T0)");
sb_grant($pdo, 'u_crew', 'elite', 36500, 'comp'); sb_grant($pdo, 'u_comp', 'pro', 36500, 'comp'); sb_grant($pdo, 'u_abs', 'elite', 30, 'comp');
$b = ma_billing('u_crew', ['created_at' => $iso($T0), 'email' => 'x']);
$ok($b['crew'] && $b['permanent'] && !ma_billing('u_comp', ['created_at' => $iso($T0)])['crew'] && ma_billing('u_cfg', ['created_at' => $iso($T0)])['crew'] && !ma_billing('u_abs', ['created_at' => $iso($T0)])['crew'],
    'Discord crew = Elite for life (Admin « Permanent » or config); a permanent Pro or a 30-day Elite is not');
$runs = []; $prevOf = [];
for ($d = 0; $d <= 64; $d++) {
    $day = (new DateTimeImmutable('2026-11-03 07:30', $NY))->modify("+$d days");
    $now = $day->getTimestamp(); $GLOBALS['SB_NOW'] = $now;
    $k = $day->format('Y-m-d');
    if ($d === 33) $pdo->exec("UPDATE users SET last_login = '" . $iso(strtotime('2026-12-05T15:00:00Z')) . "' WHERE id = 'u_abs'");   // came back on Dec 5
    $n = count($events());
    foreach (['u_abs', 'u_trial', 'u_paying', 'u_crew', 'u_cfg', 'u_comp', 'u_ea', 'u_gap', 'u_gap2'] as $id) {
        if ($id === 'u_gap' && $k >= '2026-11-08' && $k <= '2026-11-10') continue;    // server down 3 days
        if ($id === 'u_gap2' && $k >= '2026-11-09' && $k <= '2026-11-16') continue;   // server down 8 days
        $r = ma_daily_run([$id], $prevOf[$id] ?? $now - $D, $now);
        if ($r['failed']) echo "  $k $id failed: {$r['error']}\n";
        $prevOf[$id] = $now;
    }
    foreach (array_slice($events(), $n) as $x) $runs[$k][] = $x['uid'] . ':' . $x['name'] . ($x['vars']['days'] ?? '');
}
$when = function (string $what) use ($runs): array { $o = []; foreach ($runs as $k => $l) foreach ($l as $x) if ($x === $what) $o[] = $k; return $o; };
$ok($when('u_abs:inactive3d') === ['2026-11-06', '2026-12-09'] && $when('u_abs:inactive7d') === ['2026-11-10', '2026-12-13'] && $when('u_abs:inactive14d') === ['2026-11-17', '2026-12-20'] && $when('u_abs:inactive30d') === ['2026-12-03', '2027-01-05'],
    'absence: 3 days (Nov 6), 7 (Nov 10), 14 (Nov 17), 30 (Dec 3) after Monday 15:00; back on Dec 5, a new absence: Dec 9, Dec 13, Dec 20, Jan 5');
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
$GLOBALS['SB_NOW'] = (new DateTimeImmutable('2027-01-01 07:30', $NY))->getTimestamp(); $n = count($events());
ma_daily_run(['u_trial'], $GLOBALS['SB_NOW'] - $D, $GLOBALS['SB_NOW']);
$ok(count($events()) === $n, 'the same run again: nothing sent twice');
$GLOBALS['SB_NOW'] = (new DateTimeImmutable('2027-02-01 07:30', $NY))->getTimestamp(); $said = [];
$pdo->exec("UPDATE users SET last_login = '" . $iso($GLOBALS['SB_NOW'] - 7 * $D - 3600) . "' WHERE id = 'u_trial'");
ma_daily_run(['u_trial'], $GLOBALS['SB_NOW'] - $D, $GLOBALS['SB_NOW'], true, function (string $s) use (&$said) { $said[] = $s; });
$ok($said === ['would send: inactive7d → u_trial'] && count($events()) === $n && !ma_logged('u_trial', 'inactive7d', $GLOBALS['SB_NOW'] - 8 * $D), 'dry run: says what would leave, queues and writes nothing');

// 8. the evening of day one (18:30 New York), through the cron's entry ma_cron
$GLOBALS['SB_NOW'] = null; unset($GLOBALS['SB_NOW']);
$pdo->exec('DELETE FROM mail_queue');
$at = fn(string $s) => (new DateTimeImmutable($s, $NY))->getTimestamp();
$user('e_am', ['created' => $at('2027-03-02 09:00')]); $user('e_late', ['created' => $at('2027-03-02 19:10')]); $user('e_plan', ['created' => $at('2027-03-02 10:00')]); $user('e_gone', ['created' => $at('2027-03-02 11:00')]);
$doc('e_plan', 'journals', '2027-03-03', ['pre' => ['bias' => 'bullish']], false);
ma_cron($pdo, $at('2027-03-02 18:29'));
$ok($events('day1Evening') === [], '18:29 New York: not yet');
ma_cron($pdo, $at('2027-03-02 18:31'));
$ok(array_column($events('day1Evening'), 'uid') === ['e_am', 'e_gone'] && in_array('day1Evening', $rows('e_plan'), true), '18:31: the two traders of the day without a plan; the one with a plan marked, nothing sent');
ma_cron($pdo, $at('2027-03-02 19:00'));
$ok(count($events('day1Evening')) === 2, 'the next runs: not twice');
ma_cron($pdo, $at('2027-03-03 18:32'));
$ok(array_column($events('day1Evening'), 'uid') === ['e_am', 'e_gone', 'e_late'], 'signed up at 19:10: the evening of the next day');
$user('e_miss', ['created' => $at('2027-03-04 08:00')]);
ma_cron($pdo, $at('2027-03-05 02:00'));
$ok(count($events('day1Evening')) === 3 && in_array('day1Evening', $rows('e_miss'), true), 'more than 6 hours late (the server was down): given up, never sent at night');
// the daily pass through ma_cron: from 7:30, once a New York day
$pdo->exec("UPDATE users SET last_login = '" . $iso($at('2027-03-02 07:00')) . "' WHERE id = 'e_am'");
ma_cron($pdo, $at('2027-03-05 07:29'));
$ok($events('inactive3d', 'e_am') === [], 'before 7:30 New York: no daily pass');
ma_cron($pdo, $at('2027-03-05 07:31')); ma_cron($pdo, $at('2027-03-05 12:00'));
$ok(count($events('inactive3d', 'e_am')) === 1 && ma_setting('mail_auto_day') === '2027-03-05', 'from 7:30: the 3-day absence, once that day');

// 9. after Loops: its marks kept, the past not marked again, its daily window goes on
$tmp2 = $tmp . '/b.db'; $p2 = new PDO('sqlite:' . $tmp2, null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC]);
$keep = $pdo; $pdo = $p2;
$pdo->exec('CREATE TABLE users (id TEXT PRIMARY KEY, username TEXT, email TEXT, first_name TEXT, last_name TEXT, lang TEXT, created_at TEXT, last_login TEXT, disabled INTEGER NOT NULL DEFAULT 0, is_admin INTEGER NOT NULL DEFAULT 0, is_internal INTEGER NOT NULL DEFAULT 0, utm_campaign TEXT)');
$pdo->exec('CREATE TABLE documents (user_id TEXT NOT NULL, collection TEXT NOT NULL, id TEXT NOT NULL, data TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL, PRIMARY KEY (user_id, collection, id))');
$pdo->exec("CREATE TABLE app_settings (k TEXT PRIMARY KEY, v TEXT NOT NULL)");
$pdo->exec("INSERT INTO app_settings (k, v) VALUES ('loops_since', '1700000000'), ('loops_daily_at', '1799990000'), ('loops_daily_day', '2027-01-15')");
$pdo->exec("CREATE TABLE email_events_log (user_id TEXT NOT NULL, event_name TEXT NOT NULL, sent_at INT NOT NULL)");
$pdo->exec("INSERT INTO email_events_log VALUES ('L1', 'signedUp', 1700000001)");
$pdo->exec("INSERT INTO users (id, username, email, first_name, lang, created_at) VALUES ('L1', 'L1', 'l1@t.dev', 'Ana', 'en', '2026-10-01T00:00:00Z'), ('L2', 'L2', 'l2@t.dev', NULL, 'en', '2026-10-01T00:00:00Z')");
for ($i = 1; $i <= 3; $i++) $pdo->exec("INSERT INTO documents VALUES ('L2', 'trades', 't$i', '{}', '', '')");
$rows2 = fn(string $uid) => $pdo->query("SELECT event_name FROM email_events_log WHERE user_id = '$uid' ORDER BY event_name")->fetchAll(PDO::FETCH_COLUMN);
ma_ready(true);
$m = ma_init();
$ok($m === 2 && $rows2('L1') === ['day1Evening', 'signedUp'] && $rows2('L2') === ['day1Evening'] && ma_setting('mail_auto_daily_at') === '1799990000' && ma_setting('mail_auto_day') === '2027-01-15',
    'after Loops: what Loops sent stays, only the evening of day one is marked, the daily window goes on from Loops’ last run');
$pdo = $keep; ma_ready(true); ma_ready();

// 10. account deleted: its lines go
$pdo->exec("INSERT INTO email_events_log (user_id, event_name, sent_at) VALUES ('u_trial', 'signedUp', 1)");
ma_forget('u_trial');
$ok($rows('u_trial') === [], 'account deleted: its lines of email_events_log gone');

foreach (glob($tmp . '/*') as $x) @unlink($x); @rmdir($tmp);
echo "\n$pass passed, $fail failed\n";
exit($fail ? 1 : 0);
