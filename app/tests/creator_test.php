<?php
declare(strict_types=1);
/**
 * Sweep — creator program (brief « avance concurrentielle », step 5), on a throwaway SQLite database (never the live one),
 * Stripe replaced by a recorder (no network call), webhooks signed with a test secret like billing_test.php:
 *   php tests/creator_test.php
 *  - Admin gives the status: the coupon (20 % for 3 months) and the promotion code (the creator's code) asked to Stripe;
 *    Stripe refuses → no status, the reason comes back; billing off → no status;
 *  - the ledger: a paid invoice → 30 %; a refund takes it back (in proportion when partial); after 12 months from the first
 *    paid invoice, nothing; a cancelled subscription stops the commission; two creators kept apart; a creator's code typed
 *    at checkout without the link brings the trader to that creator; replays count once;
 *  - checkout: the creator's code applied by itself until the trader's first payment;
 *  - a normal trader's referral is unchanged (the free month), and a creator gets no free month;
 *  - the totals of the Referrals tab, a month marked paid, the month's statement, a deleted account.
 */
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
ob_start();   // the referral cookie (setcookie) must not meet output already sent
$app = dirname(__DIR__);
$tmp = sys_get_temp_dir() . '/sweep-creator-' . bin2hex(random_bytes(4)); mkdir($tmp);
$pdo = new PDO('sqlite:' . $tmp . '/t.db', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC]);
function db() { global $pdo; return $pdo; }
$BILLING = true;
function billing_on() { return $GLOBALS['BILLING']; }
$cfg = ['password' => 'local-test-only'];   // the referral salt
$pdo->exec('CREATE TABLE users (id TEXT PRIMARY KEY, username TEXT, created_at TEXT, lang TEXT, email TEXT, disabled INT DEFAULT 0)');
$pdo->exec('CREATE TABLE documents (user_id TEXT NOT NULL, collection TEXT NOT NULL, id TEXT NOT NULL, data TEXT NOT NULL, created_at TEXT, updated_at TEXT, PRIMARY KEY (user_id, collection, id))');
$pdo->exec('CREATE TABLE app_settings (k TEXT PRIMARY KEY, v TEXT NOT NULL)');
require $app . '/billing/billing-routes.php';
require $app . '/growth/referral.php';
require $app . '/growth/creators.php';
require $app . '/growth/feedback.php';

const SECRET = 'whsec_local_test_only';
sb_set_config([
    'live' => true, 'launch_at' => '2026-01-01T00:00:00Z', 'prelaunch_plan' => 'elite', 'comp_users' => [], 'test_users' => [], 'admin_users' => [],
    'trial' => ['plan' => 'pro', 'days' => 60], 'early_access_grant' => ['plan' => 'pro', 'days' => 60], 'campaign_grants' => [],
    'founding_deadline' => '2000-01-01T00:00:00Z', 'founding_for' => 'early_access', 'founding_percent_off' => 50, 'stripe_founding_coupon' => '',
    'past_due_grace_days' => 7, 'ai_reviews_fair_use_monthly' => 200, 'paywall_max_blocking_per_week' => 3, 'currency' => 'USD',
    'plans' => [
        'free'  => ['accounts' => 2, 'analytics_days' => 30, 'payouts' => false, 'ai_import' => false, 'ai_daily' => 3, 'ai_reviews' => 0],
        'pro'   => ['accounts' => null, 'analytics_days' => null, 'payouts' => true, 'ai_import' => true, 'ai_daily' => 50, 'ai_reviews' => 3],
        'elite' => ['accounts' => null, 'analytics_days' => null, 'payouts' => true, 'ai_import' => true, 'ai_daily' => 200, 'ai_reviews' => null],
    ],
    'display_prices' => ['pro' => ['month' => 19, 'year' => 159], 'elite' => ['month' => 39, 'year' => 329]],
    'stripe_prices' => ['pro' => ['month' => 'price_test_pro_m', 'year' => 'price_test_pro_y'], 'elite' => ['month' => 'price_test_elite_m', 'year' => 'price_test_elite_y']],
    'stripe_secret_key' => 'sk_test_local_only', 'stripe_webhook_secret' => SECRET, 'stripe_automatic_tax' => false, 'app_url' => 'https://app.sweep.test/',
]);
sb_schema($pdo); ref_schema($pdo); cr_schema($pdo);

$pass = 0; $fail = 0;
$ok = function (bool $c, string $what) use (&$pass, &$fail) { echo ($c ? 'ok   ' : 'FAIL ') . $what . "\n"; $c ? $pass++ : $fail++; };
$STRIPE = []; $SUBS = [];
$GLOBALS['SB_STRIPE_MOCK'] = function (string $m, string $path, array $p) {
    global $STRIPE, $SUBS;
    $STRIPE[] = [$m, $path, $p];
    if ($m === 'POST' && $path === 'customers') return ['id' => 'cus_' . (count($STRIPE) + 100)];
    if ($m === 'POST' && $path === 'checkout/sessions') return ['id' => 'cs_' . count($STRIPE), 'url' => 'https://checkout.stripe.test/cs_' . count($STRIPE)];
    if ($m === 'POST' && $path === 'coupons') return ['id' => 'co_' . count($STRIPE)] + $p;
    if ($m === 'POST' && $path === 'promotion_codes') {
        if (strpos((string) $p['code'], 'FAIL') === 0) throw new RuntimeException('Stripe 400: A promotion code with this code already exists');
        return ['id' => 'promo_' . $p['code'], 'code' => $p['code']];
    }
    if ($m === 'GET' && preg_match('#^subscriptions/(.+)$#', $path, $mm) && isset($SUBS[$mm[1]])) return $SUBS[$mm[1]];
    if ($m === 'POST' && preg_match('#^customers/[^/]+/balance_transactions$#', $path)) return ['id' => 'cbtxn_' . count($STRIPE)];
    throw new RuntimeException("unexpected Stripe call $m $path");
};
$calls = fn(string $m, string $path) => array_values(array_filter($GLOBALS['STRIPE'], fn($c) => $c[0] === $m && $c[1] === $path));
$at = function (string $ny): int { $t = (new DateTimeImmutable($ny, new DateTimeZone('America/New_York')))->getTimestamp(); $GLOBALS['SB_NOW'] = $t; return $t; };
$n = 0;
$signup = function (string $uid, string $code = '') use ($pdo, &$n) {
    $pdo->prepare('INSERT INTO users (id, username, created_at, lang, email) VALUES (?, ?, ?, ?, ?)')->execute([$uid, $uid, gmdate('Y-m-d\TH:i:s\Z', sb_now()), 'fr', $uid . '@sweep.test']);
    $_SERVER['REMOTE_ADDR'] = '10.0.0.' . (++$n);   // each trader from his own connection
    if ($code !== '') $_COOKIE[REF_COOKIE] = $code; else unset($_COOKIE[REF_COOKIE]);
    ref_attach_on_signup($pdo, $uid);
};
$route = function (string $uid, string $r, ?array $post = null) use ($pdo) {
    $GLOBALS['SB_OUT_CAPTURE'] = true; $_POST = $post ?? [];
    $u = $pdo->query('SELECT created_at, email FROM users WHERE id = ' . $pdo->quote($uid))->fetch();
    try { sweep_billing_route($r, $post === null ? 'GET' : 'POST', $uid, $pdo, ['created_at' => $u['created_at'], 'email' => $u['email'], 'account_ids' => []]); }
    catch (SbOut $o) { return [$o->status, $o->data]; }
    return [0, []];
};
$sign = fn(string $payload, string $secret, int $t) => 't=' . $t . ',v1=' . hash_hmac('sha256', $t . '.' . $payload, $secret);
$hook = function (string $id, string $type, array $obj, string $secret = SECRET) use ($pdo, $sign) {
    $payload = json_encode(['id' => $id, 'object' => 'event', 'type' => $type, 'data' => ['object' => $obj]]);
    if (!sb_verify_signature($payload, $sign($payload, $secret, sb_now()), (string) sb_cfg()['stripe_webhook_secret'])) return 'bad signature';
    return sb_handle_event($pdo, json_decode($payload, true));
};
$sub = function (string $uid, string $status = 'active') {
    $s = ['id' => 'sub_' . $uid, 'object' => 'subscription', 'customer' => 'cus_' . $uid, 'status' => $status, 'cancel_at_period_end' => false, 'current_period_end' => sb_now() + 30 * 86400,
        'metadata' => ['uid' => $uid, 'founding' => '0'], 'items' => ['data' => [['price' => ['id' => 'price_test_pro_m'], 'current_period_end' => sb_now() + 30 * 86400]]]];
    $GLOBALS['SUBS'][$s['id']] = $s; return $s;
};
$inv = 0;
$pay = function (string $uid, int $cents, array $extra = []) use ($hook, $sub, &$inv) {
    $sub($uid); $id = 'in_' . (++$inv);
    $r = $hook('evt_pay_' . $id, 'invoice.paid', ['id' => $id, 'object' => 'invoice', 'customer' => 'cus_' . $uid, 'subscription' => 'sub_' . $uid, 'amount_paid' => $cents, 'currency' => 'usd',
        'charge' => 'ch_' . $id, 'payment_intent' => 'pi_' . $id, 'status_transitions' => ['paid_at' => sb_now()]] + $extra);
    return [$id, $r];
};
$refund = fn(string $invId, int $refunded, int $amount) => $hook('evt_rf_' . $invId . '_' . $refunded, 'charge.refunded', ['id' => 'ch_' . $invId, 'object' => 'charge', 'invoice' => $invId,
    'payment_intent' => 'pi_' . $invId, 'amount' => $amount, 'amount_refunded' => $refunded, 'currency' => 'usd', 'refunded' => $refunded >= $amount]);
$ledger = fn(string $creator) => array_map(fn($r) => [$r['kind'], (int) $r['amount_c'], (int) $r['commission_c']], $pdo->query('SELECT * FROM creator_ledger WHERE creator_id = ' . $pdo->quote($creator) . ' ORDER BY id')->fetchAll());
$earned = fn(string $creator) => (int) $pdo->query('SELECT COALESCE(SUM(commission_c), 0) FROM creator_ledger WHERE creator_id = ' . $pdo->quote($creator))->fetchColumn();

/* ───────── 1. Admin gives the status ───────── */
$at('2026-11-02 10:00');
foreach (['cleo', 'dax', 'eve'] as $u) $signup($u);
$r = cr_make($pdo, 'cleo', 'cleo', 'admin1');
$co = $calls('POST', 'coupons'); $pc = $calls('POST', 'promotion_codes');
$ok(!empty($r['ok']) && $r['creator']['code'] === 'CLEO' && $r['creator']['promo_id'] === 'promo_CLEO' && (int) $r['creator']['rate_bp'] === 3000 && (int) $r['creator']['months'] === 12, 'make creator: status given, code CLEO, 30 %, 12 months');
$ok(count($co) === 1 && (int) $co[0][2]['percent_off'] === 20 && $co[0][2]['duration'] === 'repeating' && (int) $co[0][2]['duration_in_months'] === 3, 'make creator: Stripe coupon asked with 20 % for 3 months ' . json_encode($co[0][2] ?? null));
$ok(count($pc) === 1 && $pc[0][2]['code'] === 'CLEO' && $pc[0][2]['coupon'] === 'co_1' && $pc[0][2]['restrictions']['first_time_transaction'] === 'true', 'make creator: promotion code CLEO on that coupon, first payment only');
$ok((string) $pdo->query("SELECT code FROM ref_users WHERE uid = 'cleo'")->fetchColumn() === 'CLEO', 'make creator: the referral code becomes CLEO (link makeitsweep.com/?ref=CLEO)');
$ok(cr_link('CLEO') === 'https://makeitsweep.com/?ref=CLEO', 'the creator link is makeitsweep.com/?ref=CODE');
$ok(isset(cr_make($pdo, 'cleo')['error']), 'make creator: twice → refused');
$r = cr_make($pdo, 'dax', 'FAILDAX');
$ok(($r['error'] ?? '') === 'Stripe refused: Stripe 400: A promotion code with this code already exists' && !cr_get($pdo, 'dax'), 'Stripe refuses → no status, Admin sees Stripe\'s reason (' . ($r['error'] ?? '') . ')');
$r = cr_make($pdo, 'dax', ref_get_code($pdo, 'eve'));
$ok(($r['error'] ?? '') === 'This code is already used by another trader.', 'make creator: another trader\'s code → refused');
$ok(isset(cr_make($pdo, 'nobody')['error']), 'make creator: unknown trader → refused');
$GLOBALS['BILLING'] = false; $c0 = count($STRIPE);
$r = cr_make($pdo, 'dax');
$ok(isset($r['error']) && !cr_get($pdo, 'dax') && count($STRIPE) === $c0, 'billing off → no status, Stripe not called');
$GLOBALS['BILLING'] = true;
$r = cr_make($pdo, 'dax', '');
$daxCode = (string) ($r['creator']['code'] ?? '');
$ok(!empty($r['ok']) && $daxCode !== '' && $r['creator']['promo_id'] === 'promo_' . $daxCode, 'make creator without a code: his referral code is the promo code (' . $daxCode . ')');

/* ───────── 2. traders brought by creators ───────── */
$signup('tom', 'CLEO'); $signup('una', 'CLEO'); $signup('vic', $daxCode);
$signup('fay', (string) ref_get_code($pdo, 'eve'));   // a normal referral
$signup('gil');                                          // no link: types DAX's code at checkout
$ok((string) $pdo->query("SELECT referrer_id FROM referrals WHERE referee_id = 'tom'")->fetchColumn() === 'cleo', 'sign-up with the creator\'s link: linked to the creator');
$ok((int) $pdo->query("SELECT COUNT(*) FROM billing_grants WHERE uid = 'tom' AND reason = 'referral' AND plan = 'elite'")->fetchColumn() === 1, 'the trader keeps the friend\'s 14 days of Elite');
// checkout: the creator's code by itself
[$c, $s] = $route('tom', 'api/billing/checkout', ['plan' => 'pro', 'interval' => 'month']);
$cs = $calls('POST', 'checkout/sessions'); $last = end($cs)[2];
$ok($c === 200 && ($last['discounts'][0]['promotion_code'] ?? '') === 'promo_CLEO' && !isset($last['allow_promotion_codes']), 'checkout: the creator\'s promo code applied by itself');
[$c, $s] = $route('gil', 'api/billing/checkout', ['plan' => 'pro', 'interval' => 'month']);
$cs = $calls('POST', 'checkout/sessions'); $last = end($cs)[2];
$ok($c === 200 && !isset($last['discounts']) && ($last['allow_promotion_codes'] ?? '') === 'true', 'checkout: a trader without a creator can type a code');

/* ───────── 3. the ledger ───────── */
$ok($hook('evt_bad', 'invoice.paid', ['id' => 'in_bad', 'subscription' => 'sub_tom', 'amount_paid' => 1900], 'whsec_wrong') === 'bad signature', 'webhook: a wrong signature is refused');
$at('2026-11-03 09:00');
[$i1, $r] = $pay('tom', 1900);
$ok(strpos((string) $r, 'creator: commission 570') !== false && $ledger('cleo') === [['payment', 1900, 570]], 'payment of 19.00 → 30 % = 5.70 (' . $r . ')');
$ok($hook('evt_pay_' . $i1, 'invoice.paid', ['id' => $i1, 'subscription' => 'sub_tom', 'amount_paid' => 1900]) === 'duplicate', 'the same event again → ignored');
$r = $hook('evt_pay_again_' . $i1, 'invoice.paid', ['id' => $i1, 'object' => 'invoice', 'subscription' => 'sub_tom', 'amount_paid' => 1900, 'currency' => 'usd']);
$ok(strpos((string) $r, 'creator: duplicate') !== false && count($ledger('cleo')) === 1, 'the same invoice in another event → counted once');
$rf = $pdo->query("SELECT status, reward_type FROM referrals WHERE referee_id = 'tom'")->fetch();
$ok($rf['status'] === 'qualified' && $rf['reward_type'] === 'commission' && count($calls('POST', 'customers/cus_cleo/balance_transactions')) === 0
    && (int) $pdo->query("SELECT COUNT(*) FROM billing_grants WHERE uid = 'cleo' AND reason = 'referral'")->fetchColumn() === 0, 'a creator gets the commission, not the free month');
[$c, $s] = $route('tom', 'api/billing/checkout', ['plan' => 'pro', 'interval' => 'month']);
$ok(cr_checkout_promo($pdo, 'tom') === null, 'after his first payment, the creator\'s code is no longer applied by itself');
// refund: whole, then partial
$r = $refund($i1, 1900, 1900);
$ok($r === 'refund: reversed -570' && $earned('cleo') === 0 && $ledger('cleo')[1] === ['refund', -1900, -570], 'full refund → the commission goes back (' . $r . ')');
$ok($refund($i1, 1900, 1900) === 'duplicate', 'the same refund event again → ignored');
$at('2026-12-03 09:00');
[$i2, $r] = $pay('tom', 1900);
$ok($refund($i2, 950, 1900) === 'refund: reversed -285' && $earned('cleo') === 285, 'half refunded → half the commission goes back');
$ok($hook('evt_rf_late', 'charge.refunded', ['id' => 'ch_' . $i2, 'invoice' => $i2, 'amount' => 1900, 'amount_refunded' => 1900]) === 'refund: reversed -285' && $earned('cleo') === 0, 'then the rest → the rest of the commission');
$ok($hook('evt_rf_none', 'charge.refunded', ['id' => 'ch_x', 'invoice' => 'in_other', 'amount' => 1000, 'amount_refunded' => 1000]) === 'refund: no commission', 'a refund of a payment without commission → nothing');
// 12 months from the first paid invoice (3 Nov. 2026)
$at('2027-10-03 09:00'); [$i3, $r] = $pay('tom', 1900);
$ok(strpos((string) $r, 'commission 570') !== false, 'month 11 → still 30 %');
$at('2027-11-04 09:00'); [$i4, $r] = $pay('tom', 1900);
$ok(strpos((string) $r, 'creator: after the window') !== false && count($ledger('cleo')) === 6, 'after 12 months → nothing (' . $r . ')');
// cancellation
$at('2026-11-05 09:00'); [$iu, $r] = $pay('una', 3900);
$ok(strpos((string) $r, 'commission 1170') !== false, 'second trader of the same creator: 39.00 → 11.70');
$r = $hook('evt_del_una', 'customer.subscription.deleted', $sub('una', 'canceled'));
$at('2026-12-05 09:00'); [$iu2, $r] = $pay('una', 3900);
$ok(strpos((string) $r, 'creator: cancelled') !== false, 'after a cancellation → no commission on what he pays later (' . $r . ')');
// two creators kept apart
$at('2026-11-10 09:00'); [$iv, $r] = $pay('vic', 15900);
$ok(strpos((string) $r, 'commission 4770') !== false && $earned('dax') === 4770 && $ledger('dax') === [['payment', 15900, 4770]], 'another creator: yearly 159.00 → 47.70, on his own ledger');
// a creator's code typed at checkout, without the link
[$ig, $r] = $pay('gil', 1520, ['discount' => ['coupon' => ['id' => 'co_x'], 'promotion_code' => 'promo_' . $daxCode]]);
$ok(strpos((string) $r, 'commission 456') !== false && (string) $pdo->query("SELECT referrer_id FROM referrals WHERE referee_id = 'gil'")->fetchColumn() === 'dax', 'code typed at checkout → the trader goes to that creator, 30 % of 15.20 (' . $r . ')');
// a normal trader's referral: unchanged
$c0 = count($calls('POST', 'customers/cus_eve/balance_transactions'));
[$if, $r] = $pay('fay', 1900);
$rf = $pdo->query("SELECT status, reward_type, reward_value FROM referrals WHERE referee_id = 'fay'")->fetch();
$ok(strpos((string) $r, 'creator: no creator') !== false && $rf['status'] === 'rewarded' && $rf['reward_type'] === 'bonus_days' && (int) $rf['reward_value'] === 30
    && (int) $pdo->query("SELECT COUNT(*) FROM creator_ledger WHERE referee_id = 'fay'")->fetchColumn() === 0, 'a normal referral: the free month as before, no commission (' . json_encode($rf) . ')');
$ok(cr_dashboard($pdo, 'eve') === null, 'a normal trader has no Creator section');

/* ───────── 4. the Referrals tab, a month marked paid, the statement ───────── */
$at('2026-12-15 12:00');
ref_q($pdo, 'INSERT INTO referral_clicks (referrer_id, ip_hash, created_at) VALUES (?, ?, ?), (?, ?, ?), (?, ?, ?)', ['cleo', 'a', time(), 'cleo', 'b', time(), 'dax', 'c', time()]);
$pdo->exec("UPDATE billing_subs SET status = 'active' WHERE uid IN ('tom')");
$d = cr_dashboard($pdo, 'cleo');
// cleo: Nov. +570 −570 +1170 = 1170 ; Dec. +570 −285 −285 = 0 (+ 2027) → earned 1170 + 570 (Oct. 2027)
$ok($d['code'] === 'CLEO' && $d['link'] === 'https://makeitsweep.com/?ref=CLEO' && $d['clicks'] === 2 && $d['signups'] === 2 && $d['paying'] === 2, 'Referrals tab: clicks 2, sign-ups 2, paying 2 (' . json_encode(array_intersect_key($d, array_flip(['clicks', 'signups', 'paying']))) . ')');
$ok($d['month_c'] === 0 && $d['earned_c'] === 1740 && $d['to_pay_c'] === 1740 && $d['rate'] == 30 && $d['promo'] === ['percent' => 20, 'months' => 3], 'Referrals tab: this month 0.00, to pay 17.40 (' . $d['earned_c'] . ')');
$ok(isset(cr_mark_paid($pdo, 'cleo', '2026-12')['error']), 'the month in progress cannot be marked paid');
$r = cr_mark_paid($pdo, 'cleo', '2026-11', 'admin1');
$ok(($r['amount_c'] ?? null) === 1170 && cr_dashboard($pdo, 'cleo')['to_pay_c'] === 570 && cr_dashboard($pdo, 'cleo')['paid_c'] === 1170, 'November marked paid: 11.70, 5.70 left to pay');
$ok(isset(cr_mark_paid($pdo, 'cleo', '2026-11')['error']), 'the same month twice → refused');
$ok(isset(cr_mark_paid($pdo, 'eve', '2026-10')['error']), 'not a creator → refused');
$adm = cr_admin_list($pdo);
$cl = array_values(array_filter($adm['items'], fn($i) => $i['uid'] === 'cleo'))[0] ?? [];
$nov = array_values(array_filter($cl['months'] ?? [], fn($m) => $m['month'] === '2026-11'))[0] ?? [];
$ok(count($adm['items']) === 2 && $nov['payments_c'] === 1900 + 3900 && $nov['refunds_c'] === -1900 && $nov['commission_c'] === 1170 && $nov['paid_c'] === 1170, 'Admin: each creator, his months with payments, refunds, commission, paid');
$csv = cr_statement($pdo, '2026-11');
$tot = array_values(array_filter($csv, fn($r) => $r[5] === 'total'));
$ok($csv[0][0] === 'month' && count($csv) === 1 + 5 + 2 && $tot[0][1] === 'cleo' && $tot[0][9] === '11.70' && strpos($tot[0][11], 'paid') === 0 && $tot[1][1] === 'dax' && $tot[1][9] === '52.26' && $tot[1][11] === 'to pay',
    'statement of November: one line per payment or refund, a total per creator, paid or to pay');
// a deleted account
growth_delete_user($pdo, 'una');
$ok((int) $pdo->query("SELECT COUNT(*) FROM creator_ledger WHERE referee_id = 'una'")->fetchColumn() === 0 && $earned('cleo') === 1740, 'a trader deletes his account: his id leaves the ledger, the commission stays');
growth_delete_user($pdo, 'dax');
$ok(!cr_get($pdo, 'dax') && (int) $pdo->query("SELECT COUNT(*) FROM creator_ledger WHERE creator_id = 'dax'")->fetchColumn() === 0, 'a creator deletes his account: his rows go');

ob_end_flush();
echo "\n$pass passed, $fail failed\n";
exit($fail ? 1 : 0);
