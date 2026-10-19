<?php
declare(strict_types=1);
/**
 * Sweep — plans, billing, referrals and feedback (brief 02 part 13), on a throwaway SQLite database (never the live one),
 * Stripe replaced by a recorder (no network call), webhooks signed with a test secret:
 *   php tests/billing_test.php
 *  - the whole subscription: sign-up → 60-day Pro trial (given at the first contact) → day 50 and day 58: the reminder lists
 *    the paid features really used, once each → day 61: Free, accounts over the limit frozen (read-only), nothing deleted,
 *    the trader picks which stay active → Pro through Stripe Checkout and its webhook (signature checked, replays ignored,
 *    the redirect never trusted) → cancellation at the end of the period → Free again; a failed payment keeps the plan 7 days;
 *  - the referral: the friend's 14 days of Elite; the free month once, to the referrer, only when the friend really uses
 *    Sweep (10 real trades on 3 days within 30 days) or pays a first invoice; a Stripe credit when the referrer pays;
 *  - the feedback page: a message reaches Admin and the support mailbox (sweep_mail), its status changes, a wrong one is refused.
 */
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
ob_start();   // the referral cookie (setcookie) must not meet output already sent
$app = dirname(__DIR__);
$tmp = sys_get_temp_dir() . '/sweep-billing-' . bin2hex(random_bytes(4)); mkdir($tmp);
$pdo = new PDO('sqlite:' . $tmp . '/t.db', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC]);
function db() { global $pdo; return $pdo; }
function billing_on() { return true; }
$MAILS = [];
function sweep_mail(string $to, string $subject, string $text, string $html = '', array $headers = []): bool { $GLOBALS['MAILS'][] = [$to, $subject, $text]; return true; }
$cfg = ['password' => 'local-test-only'];   // the referral salt
$SUPPORT = 'support@sweep.test'; $APP_URL = 'https://app.sweep.test/'; $DATA = $tmp;
$pdo->exec('CREATE TABLE users (id TEXT PRIMARY KEY, username TEXT, created_at TEXT, utm_campaign TEXT, lang TEXT, email TEXT, first_name TEXT, disabled INT DEFAULT 0)');
$pdo->exec('CREATE TABLE documents (user_id TEXT NOT NULL, collection TEXT NOT NULL, id TEXT NOT NULL, data TEXT NOT NULL, created_at TEXT, updated_at TEXT, PRIMARY KEY (user_id, collection, id))');
$pdo->exec('CREATE TABLE app_settings (k TEXT PRIMARY KEY, v TEXT NOT NULL)');
require $app . '/billing/billing-routes.php';
require $app . '/growth/referral.php';
require $app . '/growth/feedback.php';
require $app . '/notify/notify.php';
require $app . '/game/game.php';
GameEngine::setPdo($pdo); GameEngine::schema(); GameV2::schema(); GameV2b::schema(); if (class_exists('GameV2c')) GameV2c::schema();

const SECRET = 'whsec_local_test_only';
sb_set_config([
    'live' => true, 'launch_at' => '2026-01-01T00:00:00Z', 'prelaunch_plan' => 'elite', 'comp_users' => [], 'test_users' => [], 'admin_users' => [],
    'trial' => ['plan' => 'pro', 'days' => 60], 'early_access_grant' => ['plan' => 'pro', 'days' => 60], 'campaign_grants' => [],
    'founding_deadline' => '2000-01-01T00:00:00Z', 'founding_for' => 'early_access', 'founding_percent_off' => 50, 'stripe_founding_coupon' => '',
    'past_due_grace_days' => 7, 'ai_reviews_fair_use_monthly' => 200, 'paywall_max_blocking_per_week' => 3, 'currency' => 'USD',
    'plans' => [
        'free'  => ['accounts' => 2, 'analytics_days' => 30, 'payouts' => false, 'ai_import' => false, 'ai_daily' => 3, 'ai_reviews' => 0],
        'pro'   => ['accounts' => 5, 'analytics_days' => null, 'payouts' => true, 'ai_import' => true, 'ai_daily' => 50, 'ai_reviews' => 3],
        'elite' => ['accounts' => null, 'analytics_days' => null, 'payouts' => true, 'ai_import' => true, 'ai_daily' => 200, 'ai_reviews' => null],
    ],
    'display_prices' => ['pro' => ['month' => 29, 'year' => 290], 'elite' => ['month' => 59, 'year' => 590]],
    'stripe_prices' => ['pro' => ['month' => 'price_test_pro_m', 'year' => 'price_test_pro_y'], 'elite' => ['month' => 'price_test_elite_m', 'year' => 'price_test_elite_y']],
    'stripe_secret_key' => 'sk_test_local_only', 'stripe_webhook_secret' => SECRET, 'stripe_automatic_tax' => false, 'app_url' => 'https://app.sweep.test/',
]);
sb_schema($pdo);

$pass = 0; $fail = 0;
$ok = function (bool $c, string $what) use (&$pass, &$fail) { echo ($c ? 'ok   ' : 'FAIL ') . $what . "\n"; $c ? $pass++ : $fail++; };
// Stripe: every call recorded, the subscriptions it knows
$STRIPE = []; $SUBS = [];
$GLOBALS['SB_STRIPE_MOCK'] = function (string $m, string $path, array $p) {
    global $STRIPE, $SUBS;
    $STRIPE[] = [$m, $path, $p];
    if ($m === 'POST' && $path === 'customers') return ['id' => 'cus_' . (count($STRIPE) + 100)];
    if ($m === 'POST' && $path === 'checkout/sessions') return ['id' => 'cs_' . count($STRIPE), 'url' => 'https://checkout.stripe.test/cs_' . count($STRIPE)];
    if ($m === 'POST' && $path === 'billing_portal/sessions') return ['url' => 'https://billing.stripe.test/portal'];
    if ($m === 'GET' && preg_match('#^subscriptions/(.+)$#', $path, $mm) && isset($SUBS[$mm[1]])) return $SUBS[$mm[1]];
    if ($m === 'POST' && preg_match('#^customers/[^/]+/balance_transactions$#', $path)) return ['id' => 'cbtxn_' . count($STRIPE)];
    throw new RuntimeException("unexpected Stripe call $m $path");
};
$calls = fn(string $m, string $path) => array_values(array_filter($GLOBALS['STRIPE'], fn($c) => $c[0] === $m && $c[1] === $path));
// the clock: New York time, the same moment for billing (SB_NOW) and the game's reminders (SWEEP_GAME_NOW)
$at = function (string $ny): int { $t = (new DateTimeImmutable($ny, new DateTimeZone('America/New_York')))->getTimestamp(); $GLOBALS['SB_NOW'] = $t; putenv('SWEEP_GAME_NOW=' . $ny); return $t; };
$signup = function (string $uid) use ($pdo) {
    $pdo->prepare('INSERT INTO users (id, username, created_at, lang, email) VALUES (?, ?, ?, ?, ?)')->execute([$uid, $uid, gmdate('Y-m-d\TH:i:s\Z', sb_now()), 'fr', $uid . '@sweep.test']);
};
$doc = function (string $uid, string $col, string $id, array $d, ?int $created = null) use ($pdo) {
    $c = gmdate('Y-m-d\TH:i:s\Z', $created ?? sb_now());
    $pdo->prepare('INSERT OR REPLACE INTO documents (user_id, collection, id, data, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)')->execute([$uid, $col, $id, json_encode($d + ['id' => $id]), $c, $c]);
};
$ids = fn(string $uid) => array_values(array_map(fn($r) => (string) $r['id'], array_filter($pdo->query("SELECT id, data FROM documents WHERE user_id = " . $pdo->quote($uid) . " AND collection = 'accounts' ORDER BY created_at, id")->fetchAll(),
    fn($r) => empty(json_decode($r['data'], true)['demo']))));
$count = fn(string $uid, string $col) => (int) $pdo->query("SELECT COUNT(*) FROM documents WHERE user_id = " . $pdo->quote($uid) . " AND collection = " . $pdo->quote($col))->fetchColumn();
// api/billing/* the way api.php calls it (the trader's sign-up date, email and real accounts)
$route = function (string $uid, string $r, ?array $post = null) use ($pdo, $ids) {
    $GLOBALS['SB_OUT_CAPTURE'] = true; $_POST = $post ?? [];
    $u = $pdo->query('SELECT created_at, email FROM users WHERE id = ' . $pdo->quote($uid))->fetch();
    try { sweep_billing_route($r, $post === null ? 'GET' : 'POST', $uid, $pdo, ['created_at' => $u['created_at'], 'email' => $u['email'], 'account_ids' => fn() => $ids($uid)]); }
    catch (SbOut $o) { return [$o->status, $o->data]; }
    return [0, []];
};
// a Stripe webhook: signed like Stripe does (t=…,v1=HMAC-SHA256 of « t.payload »), then verified and handled like the public route
$sign = fn(string $payload, string $secret, int $t) => 't=' . $t . ',v1=' . hash_hmac('sha256', $t . '.' . $payload, $secret);
$hook = function (string $id, string $type, array $obj, string $secret = SECRET, ?int $t = null) use ($pdo, $sign) {
    $payload = json_encode(['id' => $id, 'object' => 'event', 'type' => $type, 'data' => ['object' => $obj]]);
    if (!sb_verify_signature($payload, $sign($payload, $secret, $t ?? sb_now()), (string) sb_cfg()['stripe_webhook_secret'])) return 'bad signature';
    return sb_handle_event($pdo, json_decode($payload, true));
};
$sub = fn(string $id, string $uid, string $cus, string $price, string $status, int $end, bool $cancel = false) => ['id' => $id, 'object' => 'subscription', 'customer' => $cus,
    'status' => $status, 'cancel_at_period_end' => $cancel, 'current_period_end' => $end, 'metadata' => ['uid' => $uid, 'founding' => '0'], 'items' => ['data' => [['price' => ['id' => $price], 'current_period_end' => $end]]]];
$notes = fn(string $uid) => $pdo->query("SELECT * FROM notifications WHERE user_id = " . $pdo->quote($uid) . " AND type = 'trial_ending' ORDER BY id")->fetchAll();
$D = 86400;

/* ───────── 1. the whole subscription ───────── */
$at('2026-10-15 10:00'); $signup('ana'); GameEngine::profile('ana');
$ok((int) $pdo->query("SELECT COUNT(*) FROM billing_grants WHERE uid = 'ana'")->fetchColumn() === 0, 'sign-up: nothing granted before the first contact with billing');
[$c, $s] = $route('ana', 'api/billing/me');
$ok($c === 200 && $s['plan'] === 'pro' && $s['source'] === 'trial' && ($s['trial']['days_left'] ?? 0) === 60 && $s['trial']['plan'] === 'pro', 'sign-up: Pro trial of 60 days (' . json_encode($s['trial']) . ')');
$ok((int) $pdo->query("SELECT COUNT(*) FROM billing_grants WHERE uid = 'ana' AND reason = 'trial'")->fetchColumn() === 1, 'sign-up: one trial, given at the first contact');
$route('ana', 'api/billing/me');
$ok((int) $pdo->query("SELECT COUNT(*) FROM billing_grants WHERE uid = 'ana'")->fetchColumn() === 1, 'sign-up: the trial is never given twice');
// during the trial: 4 accounts (and the sample one), payouts and an expense, screenshot trades, trades from the first days, AI over the Free quota
foreach (['a1', 'a2', 'a3', 'a4'] as $i => $a) $doc('ana', 'accounts', $a, ['name' => strtoupper($a), 'status' => 'active'], sb_now() + $i);
$doc('ana', 'accounts', 'demo-a', ['name' => 'Sample', 'demo' => true], sb_now() - 10);
$doc('ana', 'payouts', 'p1', ['amount_c' => 150000, 'status' => 'paid']); $doc('ana', 'payouts', 'p2', ['amount_c' => 90000, 'status' => 'paid']); $doc('ana', 'expenses', 'e1', ['amount_c' => 15000]);
for ($i = 1; $i <= 5; $i++) $doc('ana', 'trades', "t$i", ['account_id' => 'a1', 'date' => '2026-10-16', 'pnl_c' => 1000]);
for ($i = 1; $i <= 3; $i++) $doc('ana', 'trades', "s$i", ['account_id' => 'a3', 'date' => '2026-12-01', 'source' => 'screenshot']);
$doc('ana', 'trades', 'demo-t', ['account_id' => 'demo-a', 'date' => '2026-10-16', 'source' => 'screenshot', 'demo' => true]);
$pdo->exec("INSERT INTO billing_usage (uid, metric, period, count) VALUES ('ana', 'ai_daily', '2026-11-20', 5)");
$before = ['accounts' => $count('ana', 'accounts'), 'trades' => $count('ana', 'trades'), 'payouts' => $count('ana', 'payouts'), 'expenses' => $count('ana', 'expenses')];
// a second trader who uses nothing Free lacks
$at('2026-10-15 10:00'); $signup('ben'); GameEngine::profile('ben'); $route('ben', 'api/billing/me');
$doc('ben', 'accounts', 'b1', ['name' => 'B1']); $doc('ben', 'trades', 'bt1', ['account_id' => 'b1', 'date' => '2026-12-01']);

// day 50: 10 days left → the reminder lists what Ana really uses of Pro (the same list as the dashboard card)
$at('2026-12-04 20:00');
[, $s] = $route('ana', 'api/billing/me');
$ok(($s['trial']['days_left'] ?? 0) === 10, 'day 50: 10 days left');
$used = array_column(sb_pro_used($pdo, 'ana'), null, 'k');
$ok(($used['accounts']['n'] ?? 0) === 4 && ($used['accounts']['free'] ?? 0) === 2, 'day 50: 4 accounts, Free keeps 2 (the sample account does not count)');
$ok(($used['money']['payouts'] ?? 0) === 2 && ($used['money']['expenses'] ?? 0) === 1, 'day 50: My money, 2 payouts and 1 expense');
$ok(($used['shots']['n'] ?? 0) === 3, 'day 50: 3 trades read from a screenshot (not the sample one)');
$ok(($used['history']['n'] ?? 0) === 5 && ($used['history']['days'] ?? 0) === 30, 'day 50: 5 trades older than the 30 days Free shows');
$ok(isset($used['ai']), 'day 50: Sweep AI over the Free daily quota once');
$ok(sb_pro_used($pdo, 'ben') === [], 'day 50: nothing for a trader who uses nothing Free lacks');
$ok(array_column($s['pro_used'] ?? [], 'k') === ['accounts', 'money', 'shots', 'history', 'ai'], 'day 50: the app gets the same list (api/billing/me pro_used)');
GameNotifyService::run('ana'); GameNotifyService::run('ana'); GameNotifyService::run('ben');
$n = $notes('ana'); $p = json_decode((string) ($n[0]['params'] ?? '{}'), true) ?: [];
$ok(count($n) === 1 && (int) ($p['days'] ?? 0) === 10 && $n[0]['body_key'] === 'trial_ending.used' && $n[0]['action_url'] === '#plan', 'day 50: one reminder, once (' . count($n) . ')');
$ok(($p['used_fr'] ?? '') === '4 comptes (Free en garde 2 actifs), Mon argent (2 payouts, 1 dépense), la lecture des captures sans limite (3 trades ; Free : 3 par jour), ton historique complet (5 trades de plus de 30 jours) et Sweep AI au-delà de la limite de Free',
    'day 50: the reminder names them, in French: ' . ($p['used_fr'] ?? ''));
$ok(strpos($p['used_en'] ?? '', '4 accounts (Free keeps 2 active), My money (2 payouts, 1 expense)') === 0 && strpos($p['used_es'] ?? '', '4 cuentas (Free mantiene 2 activas), Mi dinero (2 payouts, 1 gasto)') === 0, 'day 50: and in English and Spanish');
$nb = $notes('ben');
$ok(count($nb) === 1 && $nb[0]['body_key'] === 'trial_ending.none', 'day 50: nothing used → the reminder says what Free keeps');
$at('2026-12-12 20:00'); GameNotifyService::run('ana');
$n = $notes('ana');
$ok(count($n) === 2 && (int) (json_decode((string) $n[1]['params'], true)['days'] ?? 0) === 2, 'day 58: the second reminder, 2 days left');
$at('2026-12-13 20:00'); GameNotifyService::run('ana');
$ok(count($notes('ana')) === 2, 'day 59: no third reminder');
$at('2026-12-14 08:59');   // signed up at 10:00 EDT: the 60 days end at 09:00 EST
[, $s] = $route('ana', 'api/billing/me');
$ok($s['plan'] === 'pro' && ($s['trial']['days_left'] ?? 0) === 1, 'day 60, 08:59: still Pro');
$at('2026-12-14 09:00');
$ok($route('ana', 'api/billing/me')[1]['plan'] === 'free', 'day 60, 09:00: the 60 days are over, Free');

// day 61: back to Free — frozen, never deleted
$at('2026-12-15 20:00');
[, $s] = $route('ana', 'api/billing/me');
$ok($s['plan'] === 'free' && $s['trial'] === null && ($s['trial_ended']['plan'] ?? '') === 'pro', 'day 61: Free, the trial ended (' . json_encode($s['trial_ended']) . ')');
// screenshots read by Sweep AI on Free (Mateo, 18 Oct.): 3 a day on their own count, a 4th asks for Pro; a receipt scan stays
// Pro and Elite; a read that failed is given back; New York's midnight gives 3 more; the plans page shows « 3 a day »
$d0 = sb_usage($pdo, 'ana', 'ai_daily');
$r = [sb_ai_consume($pdo, 'ana', 'shot'), sb_ai_consume($pdo, 'ana', 'shot'), sb_ai_consume($pdo, 'ana', 'shot'), sb_ai_consume($pdo, 'ana', 'shot')];
$ok($r[0]['ok'] && $r[2]['ok'] && $r[2]['used'] === 3 && !$r[3]['ok'] && $r[3]['code'] === 'upgrade_required' && $r[3]['feature'] === 'ai_import_daily' && $r[3]['trigger'] === 'shot_quota' && $r[3]['limit'] === 3 && !empty($r[3]['reset_at']) && $r[3]['upgrade_to'] === 'pro', 'Free: 3 screenshots a day, the 4th opens « Pro » (' . json_encode($r[3]) . ')');
$ok(sb_usage($pdo, 'ana', 'ai_daily') === $d0, 'Free: the screenshots do not use the AI messages');
sb_ai_refund($pdo, 'ana', 'shot');
$ok(sb_ai_consume($pdo, 'ana', 'shot')['ok'] && !sb_ai_consume($pdo, 'ana', 'shot')['ok'], 'Free: a failed read is given back (one more, then the limit again)');
$rc = sb_ai_consume($pdo, 'ana', 'import');
$ok(!$rc['ok'] && $rc['code'] === 'upgrade_required' && $rc['feature'] === 'ai_import', 'Free: a receipt scan stays Pro and Elite (' . ($rc['feature'] ?? '') . ')');
$me = $route('ana', 'api/billing/me')[1];
$ok(($me['plans']['free']['ai_import_daily'] ?? null) === 3 && array_key_exists('ai_import_daily', $me['plans']['pro'] ?? []) && $me['plans']['pro']['ai_import_daily'] === null && ($me['usage']['ai_import_daily']['used'] ?? null) === 3, 'the app gets 3 a day for Free, unlimited for Pro, and what is used today');
$keep = $GLOBALS['SB_NOW']; $GLOBALS['SB_NOW'] = (new DateTimeImmutable('@' . $keep))->setTimezone(new DateTimeZone('America/New_York'))->modify('tomorrow 00:05')->getTimestamp();
$ok(sb_ai_consume($pdo, 'ana', 'shot')['ok'], 'Free: 3 more after midnight, New York');
$GLOBALS['SB_NOW'] = $keep;
$ok($s['accounts']['limit'] === 2 && $s['accounts']['active'] === ['a1', 'a2'] && $s['accounts']['frozen'] === ['a3', 'a4'] && $s['accounts']['needs_choice'] === true,
    'day 61: the 2 oldest accounts stay active, the 2 others frozen, the trader is asked to choose');
$ok($before === ['accounts' => $count('ana', 'accounts'), 'trades' => $count('ana', 'trades'), 'payouts' => $count('ana', 'payouts'), 'expenses' => $count('ana', 'expenses')], 'day 61: nothing deleted (accounts, trades, payouts, expenses)');
$g = sb_guard($pdo, 'ana', 'write_trade', ['account_id' => 'a3', 'account_ids' => $ids('ana')]);
$ok(($g['code'] ?? '') === 'upgrade_required' && $g['trigger'] === 'frozen_account', 'day 61: a frozen account takes no new trade');
$ok(sb_guard($pdo, 'ana', 'write_trade', ['account_id' => 'a1', 'account_ids' => $ids('ana')]) === null, 'day 61: an active account still does');
$ok((sb_guard($pdo, 'ana', 'write_payouts')['code'] ?? '') === 'upgrade_required', 'day 61: My money is read-only on Free');
$ok((sb_guard($pdo, 'ana', 'create_account', ['account_ids' => $ids('ana')])['code'] ?? '') === 'upgrade_required', 'day 61: no new account over the Free limit');
[$c, $a] = $route('ana', 'api/billing/active-accounts', ['ids' => ['a4', 'a3', 'a1']]);
$ok($c === 200 && $a['active'] === ['a4', 'a3'] && $a['frozen'] === ['a1', 'a2'] && $a['needs_choice'] === false, 'day 61: the trader picks the 2 that stay active (a third one is ignored)');
[, $s] = $route('ana', 'api/billing/me');
$ok($s['accounts']['active'] === ['a4', 'a3'], 'day 61: the choice sticks');

// passage à Pro: Stripe Checkout, then only the webhook changes the plan
$STRIPE = [];
[$c, $r] = $route('ana', 'api/billing/checkout', ['plan' => 'pro', 'interval' => 'year', 'trigger' => 'trial_ended']);
$cs = $calls('POST', 'checkout/sessions')[0][2] ?? [];
$cu = $calls('POST', 'customers')[0][2] ?? [];
$ok($c === 200 && strpos((string) ($r['url'] ?? ''), 'https://checkout.stripe.test/') === 0, 'checkout: the secure Stripe page opens');
$ok(($cu['email'] ?? '') === 'ana@sweep.test' && ($cu['metadata']['uid'] ?? '') === 'ana', 'checkout: the Stripe customer carries the trader');
$ok(($cs['mode'] ?? '') === 'subscription' && ($cs['line_items'][0]['price'] ?? '') === 'price_test_pro_y' && ($cs['client_reference_id'] ?? '') === 'ana'
    && ($cs['metadata']['trigger'] ?? '') === 'trial_ended' && ($cs['success_url'] ?? '') === 'https://app.sweep.test/?billing=success&plan=pro', 'checkout: Pro yearly, for this trader, back to the app');
$cus = (string) $pdo->query("SELECT stripe_customer FROM billing_users WHERE uid = 'ana'")->fetchColumn();
$route('ana', 'api/billing/checkout', ['plan' => 'pro', 'interval' => 'month']);
$ok($cus !== '' && count($calls('POST', 'customers')) === 1, 'checkout: the same Stripe customer next time');
$ok($route('ana', 'api/billing/me')[1]['plan'] === 'free', 'checkout: coming back from Stripe changes nothing until the webhook');
$t = sb_now(); $SUBS['sub_ana'] = $sub('sub_ana', 'ana', $cus, 'price_test_pro_y', 'active', $t + 365 * $D);
$ev = ['id' => 'cs_x', 'object' => 'checkout.session', 'mode' => 'subscription', 'subscription' => 'sub_ana', 'client_reference_id' => 'ana', 'metadata' => ['uid' => 'ana', 'trigger' => 'trial_ended']];
$ok($hook('evt_1', 'checkout.session.completed', $ev, 'whsec_someone_else') === 'bad signature', 'webhook: a wrong signature is refused');
$ok($hook('evt_1', 'checkout.session.completed', $ev, SECRET, $t - 600) === 'bad signature', 'webhook: a signature older than 5 minutes is refused');
$ok($route('ana', 'api/billing/me')[1]['plan'] === 'free', 'webhook: nothing changed after a refused one');
$ok($hook('evt_1', 'checkout.session.completed', $ev) === 'subscribed ana', 'webhook: checkout completed');
[, $s] = $route('ana', 'api/billing/me');
$ok($s['plan'] === 'pro' && $s['source'] === 'subscription' && $s['subscription']['interval'] === 'year' && $s['trial_ended'] === null, 'Pro: paid yearly');
$ok($s['accounts']['frozen'] === [] && sb_guard($pdo, 'ana', 'write_trade', ['account_id' => 'a1', 'account_ids' => $ids('ana')]) === null && sb_guard($pdo, 'ana', 'write_payouts') === null,
    'Pro: every account and My money open again');
$ok($hook('evt_1', 'checkout.session.completed', $ev) === 'duplicate', 'webhook: the same event twice is handled once');
$ok((int) $pdo->query("SELECT COUNT(*) FROM billing_upsell WHERE uid = 'ana' AND action = 'converted' AND trig = 'trial_ended'")->fetchColumn() === 1, 'Pro: the sale is counted once, on the moment that sold it');
$ok(str_starts_with($hook('evt_2', 'invoice.paid', ['id' => 'in_1', 'subscription' => 'sub_ana', 'amount_paid' => 29000]), 'invoice synced ana'), 'webhook: the paid invoice');
[$c, $r] = $route('ana', 'api/billing/checkout', ['plan' => 'elite', 'interval' => 'year']);
$ok(($r['url'] ?? '') === 'https://billing.stripe.test/portal', 'Pro: changing plan goes through the Stripe portal (no second subscription)');
// cancellation: Pro until the end of the paid period, then Free (the accounts chosen earlier stay active)
$end = $t + 30 * $D;
$SUBS['sub_ana'] = $sub('sub_ana', 'ana', $cus, 'price_test_pro_y', 'active', $end, true);
$hook('evt_3', 'customer.subscription.updated', $SUBS['sub_ana']);
[, $s] = $route('ana', 'api/billing/me');
$ok($s['plan'] === 'pro' && $s['subscription']['cancel_at_period_end'] === true && $s['subscription']['period_end'] === gmdate('c', $end), 'cancellation: still Pro until the end of the period');
$GLOBALS['SB_NOW'] = $end + 60;
$SUBS['sub_ana'] = $sub('sub_ana', 'ana', $cus, 'price_test_pro_y', 'canceled', $end, true);
$hook('evt_4', 'customer.subscription.deleted', $SUBS['sub_ana']);
[, $s] = $route('ana', 'api/billing/me');
$ok($s['plan'] === 'free' && $s['subscription'] === null && $s['accounts']['active'] === ['a4', 'a3'] && $s['accounts']['frozen'] === ['a1', 'a2'], 'cancellation: Free again, the same accounts active');
$ok($before === ['accounts' => $count('ana', 'accounts'), 'trades' => $count('ana', 'trades'), 'payouts' => $count('ana', 'payouts'), 'expenses' => $count('ana', 'expenses')], 'cancellation: still nothing deleted');
// a failed payment: the plan stays 7 days (the card can be updated), then Free
$at('2026-12-20 20:00'); $signup('cy'); $route('cy', 'api/billing/me');
$pdo->exec("UPDATE billing_users SET stripe_customer = 'cus_cy' WHERE uid = 'cy'");
$SUBS['sub_cy'] = $sub('sub_cy', 'cy', 'cus_cy', 'price_test_elite_m', 'active', sb_now() + 30 * $D);
$hook('evt_5', 'customer.subscription.created', $SUBS['sub_cy']);
$ok($route('cy', 'api/billing/me')[1]['plan'] === 'elite', 'past due: Elite while paid');
$SUBS['sub_cy']['status'] = 'past_due';
$hook('evt_6', 'invoice.payment_failed', ['id' => 'in_2', 'subscription' => 'sub_cy', 'amount_paid' => 0]);
[, $s] = $route('cy', 'api/billing/me');
$ok($s['plan'] === 'elite' && $s['subscription']['status'] === 'past_due' && $s['subscription']['grace_ends'] === gmdate('c', sb_now() + 7 * $D), 'past due: still Elite, 7 days to update the card');
$GLOBALS['SB_NOW'] += 7 * $D + 60;
$ok($route('cy', 'api/billing/me')[1]['plan'] === 'pro', 'past due: after 7 days, the plan of the trial still running (Pro)');
$GLOBALS['SB_NOW'] += 60 * $D;
$ok($route('cy', 'api/billing/me')[1]['plan'] === 'free', 'past due: and Free once the trial is over');

/* ───────── 2. the referral (the real clock: the referral module counts with time()) ───────── */
unset($GLOBALS['SB_NOW']); putenv('SWEEP_GAME_NOW');
$_SERVER['REMOTE_ADDR'] = '10.0.0.1'; $signup('rita'); ref_attach_on_signup($pdo, 'rita'); $route('rita', 'api/billing/me');
$code = ref_get_code($pdo, 'rita');
$ok((bool) preg_match('/^RITA[A-Z2-9]{3}$/', $code), "referral: Rita's code ($code)");
$_COOKIE[REF_COOKIE] = $code; $_SERVER['REMOTE_ADDR'] = '10.0.0.2'; $signup('fred');
$rid = ref_attach_on_signup($pdo, 'fred'); $route('fred', 'api/billing/me');
$ok($rid !== null && $pdo->query("SELECT status FROM referrals WHERE referee_id = 'fred'")->fetchColumn() === 'pending', 'referral: Fred signs up with the link');
$ok(sb_plan($pdo, 'fred') === 'elite' && (int) $pdo->query("SELECT COUNT(*) FROM billing_grants WHERE uid = 'fred' AND reason = 'referral' AND plan = 'elite'")->fetchColumn() === 1, 'referral: Fred gets 14 days of Elite on top of his trial');
$_COOKIE[REF_COOKIE] = $code; $_SERVER['REMOTE_ADDR'] = '10.0.0.1'; $signup('fake');
ref_attach_on_signup($pdo, 'fake'); $route('fake', 'api/billing/me');
$ok($pdo->query("SELECT status FROM referrals WHERE referee_id = 'fake'")->fetchColumn() === 'review' && sb_plan($pdo, 'fake') === 'pro', 'referral: same connection as Rita → to review in Admin, no Elite yet');
$rewards = fn(string $uid) => (int) $pdo->query("SELECT COUNT(*) FROM billing_grants WHERE uid = " . $pdo->quote($uid) . " AND reason = 'referral'")->fetchColumn();
$now = time();
for ($i = 1; $i <= 10; $i++) $doc('fred', 'trades', "f$i", ['account_id' => 'fa', 'date' => gmdate('Y-m-d', $now)], $now + ($i <= 5 ? 3600 : $D + 3600));   // 10 trades on 2 days
for ($i = 1; $i <= 10; $i++) $doc('fred', 'trades', "fd$i", ['account_id' => 'fa', 'demo' => true], $now + 2 * $D + 3600);                                  // sample data on a third day
ref_check_user($pdo, 'fred'); ref_cron($pdo, true);
$ok($pdo->query("SELECT status FROM referrals WHERE referee_id = 'fred'")->fetchColumn() === 'pending' && $rewards('rita') === 0, 'referral: 10 trades on 2 days (and sample data) are not enough yet');
$doc('fred', 'trades', 'f11', ['account_id' => 'fa', 'date' => gmdate('Y-m-d', $now)], $now + 2 * $D + 3600);
ref_check_user($pdo, 'fred');
$r = $pdo->query("SELECT * FROM referrals WHERE referee_id = 'fred'")->fetch();
$ok($r['status'] === 'rewarded' && $r['qualify_reason'] === 'activity' && $r['reward_type'] === 'bonus_days' && $rewards('rita') === 1, 'referral: 11 real trades on 3 days → Rita gets her free month');
$g = $pdo->query("SELECT * FROM billing_grants WHERE uid = 'rita' AND reason = 'referral'")->fetch();
$ok($g['plan'] === 'pro' && (int) $g['ends_at'] - (int) $g['starts_at'] === 30 * $D, 'referral: the month is 30 days of Pro, on Rita');
$ok((int) $pdo->query("SELECT COUNT(*) FROM billing_grants WHERE uid = 'fred' AND reason = 'referral'")->fetchColumn() === 1, 'referral: nothing more for Fred');
$doc('fred', 'trades', 'f12', ['account_id' => 'fa'], $now + 3 * $D);
ref_check_user($pdo, 'fred'); ref_cron($pdo, true); ref_on_first_payment($pdo, 'fred');
$ok($rewards('rita') === 1, 'referral: the month is given once only (more trades, the daily check, a payment)');
// a paying referrer: a credit of one month on her Stripe balance, once
$_SERVER['REMOTE_ADDR'] = '10.0.0.3'; $signup('paula'); ref_attach_on_signup($pdo, 'paula'); $route('paula', 'api/billing/me');
$pdo->exec("UPDATE billing_users SET stripe_customer = 'cus_paula' WHERE uid = 'paula'");
$SUBS['sub_paula'] = $sub('sub_paula', 'paula', 'cus_paula', 'price_test_pro_m', 'active', time() + 30 * $D);
$hook('evt_7', 'customer.subscription.created', $SUBS['sub_paula']);
$_COOKIE[REF_COOKIE] = ref_get_code($pdo, 'paula'); $_SERVER['REMOTE_ADDR'] = '10.0.0.4'; $signup('gus'); ref_attach_on_signup($pdo, 'gus'); $route('gus', 'api/billing/me');
$pdo->exec("UPDATE billing_users SET stripe_customer = 'cus_gus' WHERE uid = 'gus'");
$SUBS['sub_gus'] = $sub('sub_gus', 'gus', 'cus_gus', 'price_test_pro_m', 'active', time() + 30 * $D);
$STRIPE = [];
$hook('evt_8', 'invoice.paid', ['id' => 'in_3', 'subscription' => 'sub_gus', 'amount_paid' => 2900]);
$hook('evt_9', 'invoice.paid', ['id' => 'in_4', 'subscription' => 'sub_gus', 'amount_paid' => 2900]);
$cr = $calls('POST', 'customers/cus_paula/balance_transactions');
$r = $pdo->query("SELECT * FROM referrals WHERE referee_id = 'gus'")->fetch();
$ok(count($cr) === 1 && (int) $cr[0][2]['amount'] === -2900 && $cr[0][2]['currency'] === 'usd', "referral: Gus's first payment → one month of Pro credited to Paula's Stripe balance, once");
$ok($r['status'] === 'rewarded' && $r['qualify_reason'] === 'payment' && $r['reward_type'] === 'stripe_credit' && $rewards('paula') === 0, 'referral: a credit, not free days, for a paying referrer');
$ok(count($calls('POST', 'customers/cus_gus/balance_transactions')) === 0, 'referral: never on the friend');

/* ───────── 3. the feedback page ───────── */
$MAILS = [];
$r1 = fb_create($pdo, 'ana', ['type' => 'idea', 'message' => 'Un graphique par setup', 'page' => '#analytics', 'lang' => 'fr'], 'free');
$ok(!empty($r1['ok']) && count($MAILS) === 1 && $MAILS[0][0] === 'support@sweep.test' && strpos($MAILS[0][1], 'Feedback idea #' . $r1['id']) !== false
    && strpos($MAILS[0][2], 'ana <ana@sweep.test>') !== false && strpos($MAILS[0][2], 'Un graphique par setup') !== false, 'feedback: sent, and the support mailbox gets it (sweep_mail, with who and what)');
$adm = fb_admin_list($pdo, null, null);
$it = $adm['items'][0] ?? [];
$ok($adm['new'] === 1 && ($it['message'] ?? '') === 'Un graphique par setup' && ($it['user'] ?? '') === 'ana' && ($it['context']['plan'] ?? '') === 'free' && ($it['page'] ?? '') === '#analytics', 'feedback: it is in Admin, with the trader, the page and the plan');
$ok(fb_update($pdo, (int) $r1['id'], 'planned', 'Bonne idée, c’est prévu.') && (fb_list_mine($pdo, 'ana')[0]['status'] ?? '') === 'planned' && (fb_list_mine($pdo, 'ana')[0]['reply'] ?? '') === 'Bonne idée, c’est prévu.', 'feedback: Admin sets « planned » with a reply, the trader sees both');
$ok(!fb_update($pdo, (int) $r1['id'], 'bogus', null) && fb_list_mine($pdo, 'ana')[0]['status'] === 'planned', 'feedback: an unknown status is refused, nothing changes');
$ok((fb_create($pdo, 'ana', ['type' => 'rant', 'message' => 'x'], 'free')['error'] ?? '') === 'invalid' && (fb_create($pdo, 'ana', ['type' => 'bug', 'message' => '  '], 'free')['error'] ?? '') === 'invalid', 'feedback: a wrong type or an empty message is refused');
$r2 = fb_create($pdo, 'ana', ['type' => 'experience', 'rating' => 4, 'message' => 'Simple et clair'], 'free');
$ok(($adm = fb_admin_list($pdo, null, null)) && $adm['avg_rating_30d'] === 4.0 && fb_admin_list($pdo, 'new', 'experience')['items'][0]['id'] === $r2['id'], 'feedback: the rating counts in the 30-day average, filters work');
for ($i = 0; $i < 8; $i++) fb_create($pdo, 'ana', ['type' => 'bug', 'message' => "bug $i"], 'free');
$ok((fb_create($pdo, 'ana', ['type' => 'bug', 'message' => 'one too many'], 'free')['error'] ?? '') === 'limit', 'feedback: 10 a day at most');

$pdo = null; array_map('unlink', glob($tmp . '/*') ?: []); @rmdir($tmp);
echo "\n$pass passed, $fail failed\n";
exit($fail ? 1 : 0);
