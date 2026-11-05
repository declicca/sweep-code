<?php
declare(strict_types=1);
/**
 * Sweep — monetization at 100 traders (brief of 5 Nov., steps 2 to 4), on a throwaway SQLite database, Stripe replaced by a
 * recorder (no network call):
 *   php tests/monetize_test.php
 *  - step 2: a new trader gets the trial of the config (30 days); a trial already given keeps its end when the config changes;
 *    the end-of-trial emails come at 10 and 3 days left (no more « 30 left »);
 *  - step 3: the founding offer for the first N subscribers (founding_cap): places left, gone at 0 or after the deadline, a
 *    founder keeps his price;
 *  - step 4: « Pause 1 month »: Stripe's pause_collection (resumes in 30 days), Free during the pause (nothing deleted, no
 *    founding offer, no second subscription), « Resume now », one pause per 6 months, none on a subscription ending; the
 *    « resumes in 3 days » email once per pause; Stripe's webhook ending the pause.
 */
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
$app = dirname(__DIR__);
$tmp = sys_get_temp_dir() . '/sweep-monetize-' . bin2hex(random_bytes(4)); mkdir($tmp);
$pdo = new PDO('sqlite:' . $tmp . '/t.db', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC]);
function db() { global $pdo; return $pdo; }
function billing_on() { return true; }
$pdo->exec('CREATE TABLE users (id TEXT PRIMARY KEY, username TEXT, created_at TEXT, utm_campaign TEXT, lang TEXT, email TEXT, first_name TEXT, last_login TEXT, disabled INT DEFAULT 0)');
$pdo->exec('CREATE TABLE documents (user_id TEXT NOT NULL, collection TEXT NOT NULL, id TEXT NOT NULL, data TEXT NOT NULL, created_at TEXT, updated_at TEXT, PRIMARY KEY (user_id, collection, id))');
$pdo->exec('CREATE TABLE app_settings (k TEXT PRIMARY KEY, v TEXT NOT NULL)');
require $app . '/billing/billing-routes.php';
require $app . '/mail/mail-core.php';
require $app . '/mail/mail-auto.php';

$base = [
    'live' => true, 'launch_at' => '2026-01-01T00:00:00Z', 'prelaunch_plan' => 'elite', 'comp_users' => [], 'test_users' => [], 'admin_users' => [],
    'trial' => ['plan' => 'pro', 'days' => 30], 'early_access_grant' => ['plan' => 'pro', 'days' => 60], 'campaign_grants' => [],
    'founding_deadline' => '2026-12-02T04:59:59Z', 'founding_for' => 'everyone', 'founding_percent_off' => 50, 'founding_cap' => 3, 'stripe_founding_coupon' => 'FOUNDING50',
    'past_due_grace_days' => 7, 'ai_reviews_fair_use_monthly' => 200, 'paywall_max_blocking_per_week' => 3, 'currency' => 'USD',
    'plans' => [
        'free'  => ['accounts' => 2, 'analytics_days' => 30, 'payouts' => false, 'ai_import' => false, 'ai_daily' => 3, 'ai_reviews' => 0],
        'pro'   => ['accounts' => null, 'analytics_days' => null, 'payouts' => true, 'ai_import' => true, 'ai_daily' => 50, 'ai_reviews' => 3],
        'elite' => ['accounts' => null, 'analytics_days' => null, 'payouts' => true, 'ai_import' => true, 'ai_daily' => 200, 'ai_reviews' => null],
    ],
    'display_prices' => ['pro' => ['month' => 19, 'year' => 159], 'elite' => ['month' => 39, 'year' => 329]],
    'stripe_prices' => ['pro' => ['month' => 'price_test_pro_m', 'year' => 'price_test_pro_y'], 'elite' => ['month' => 'price_test_elite_m', 'year' => 'price_test_elite_y']],
    'stripe_secret_key' => 'sk_test_local_only', 'stripe_webhook_secret' => 'whsec_local_test_only', 'stripe_automatic_tax' => false, 'app_url' => 'https://app.sweep.test/',
];
sb_set_config($base);
sb_schema($pdo);

$pass = 0; $fail = 0;
$ok = function (bool $c, string $what) use (&$pass, &$fail) { echo ($c ? 'ok   ' : 'FAIL ') . $what . "\n"; $c ? $pass++ : $fail++; };
$STRIPE = []; $SUBS = [];
$GLOBALS['SB_STRIPE_MOCK'] = function (string $m, string $path, array $p) {
    global $STRIPE, $SUBS;
    $STRIPE[] = [$m, $path, $p];
    if ($m === 'POST' && $path === 'customers') return ['id' => 'cus_' . count($STRIPE)];
    if ($m === 'POST' && $path === 'checkout/sessions') return ['id' => 'cs_' . count($STRIPE), 'url' => 'https://checkout.stripe.test/cs_' . count($STRIPE)];
    if ($m === 'POST' && $path === 'billing_portal/sessions') return ['url' => 'https://billing.stripe.test/portal'];
    if (preg_match('#^subscriptions/(.+)$#', $path, $mm) && isset($SUBS[$mm[1]])) {
        if ($m === 'POST' && array_key_exists('pause_collection', $p)) $SUBS[$mm[1]]['pause_collection'] = is_array($p['pause_collection']) ? $p['pause_collection'] : null;
        return $SUBS[$mm[1]];
    }
    throw new RuntimeException("unexpected Stripe call $m $path");
};
$calls = fn(string $m, string $path) => array_values(array_filter($GLOBALS['STRIPE'], fn($c) => $c[0] === $m && $c[1] === $path));
$at = function (string $ny): int { $t = (new DateTimeImmutable($ny, new DateTimeZone('America/New_York')))->getTimestamp(); $GLOBALS['SB_NOW'] = $t; return $t; };
$signup = function (string $uid) use ($pdo) {
    $pdo->prepare('INSERT INTO users (id, username, created_at, lang, email) VALUES (?, ?, ?, ?, ?)')->execute([$uid, $uid, gmdate('Y-m-d\TH:i:s\Z', sb_now()), 'fr', $uid . '@sweep.test']);
    sb_user($pdo, $uid, gmdate('c', sb_now()), $uid . '@sweep.test');
};
// a Stripe subscription as its webhook gives it (customer.subscription.created / updated)
$sub = function (string $id, string $uid, string $status = 'active', bool $founding = false, array $more = []) {
    return array_merge(['id' => $id, 'object' => 'subscription', 'customer' => 'cus_' . $uid, 'status' => $status, 'cancel_at_period_end' => false,
        'current_period_end' => sb_now() + 30 * 86400, 'metadata' => ['uid' => $uid, 'founding' => $founding ? '1' : '0'],
        'items' => ['data' => [['price' => ['id' => 'price_test_pro_m']]]], 'pause_collection' => null], $more);
};
$subscribe = function (string $id, string $uid, bool $founding) use ($pdo, $sub) {
    $GLOBALS['SUBS'][$id] = $sub($id, $uid, 'active', $founding);
    sb_handle_event($pdo, ['id' => 'evt_' . $id, 'type' => 'customer.subscription.created', 'data' => ['object' => $GLOBALS['SUBS'][$id]]]);
};

/* ───────────── step 2: the 30-day trial ───────────── */
$at('2026-11-05 10:00');
sb_set_config(['trial' => ['plan' => 'pro', 'days' => 60]] + $base);
$signup('old');                                        // signed up under the 60-day trial
$oldEnd = (int) $pdo->query("SELECT ends_at FROM billing_grants WHERE uid = 'old' AND reason = 'trial'")->fetchColumn();
sb_set_config($base);                                  // Mateo sets trial.days = 30
$signup('new');
$newEnd = (int) $pdo->query("SELECT ends_at FROM billing_grants WHERE uid = 'new' AND reason = 'trial'")->fetchColumn();
$ok($newEnd === sb_now() + 30 * 86400 && sb_state($pdo, 'new')['trial']['days_left'] === 30, 'trial: a new trader gets 30 days of Pro, no card');
$at('2026-11-20 10:00');
sb_user($pdo, 'old', null, 'old@sweep.test'); sb_state($pdo, 'old');
$ok((int) $pdo->query("SELECT ends_at FROM billing_grants WHERE uid = 'old' AND reason = 'trial'")->fetchColumn() === $oldEnd
    && (int) $pdo->query("SELECT COUNT(*) FROM billing_grants WHERE uid = 'old'")->fetchColumn() === 1 && sb_state($pdo, 'old')['trial']['days_left'] === 45,
    'trial: a trial already given keeps its 60 days (never recalculated, no second grant)');
$due = function (int $end, int $daysLeft): array {   // the daily steps on the day a trial has $daysLeft days left
    $now = $end - $daysLeft * 86400 + 3600;
    return array_column(ma_daily_due(['id' => 'x', 'created_at' => '2026-01-01T00:00:00Z', 'last_login' => gmdate('c', $now)], ['live' => true, 'trial_end' => $end, 'paying' => false, 'crew' => false, 'permanent' => false, 'pause' => null], $now - 86400, $now), 0);
};
$ok($due($newEnd, 30) === [] && $due($newEnd, 10) === ['proTrialDaysLeft:10'] && $due($newEnd, 3) === ['proTrialDaysLeft:3'] && $due($newEnd, 0) === ['proTrialEnded'],
    'trial: the end-of-trial emails at 10 and 3 days left, then the end; none at 30 days left');
$texts = (array) require $app . '/mail/mail-auto-texts.php';
$ok(!preg_match('/\b60\b/', json_encode($texts['proTrialEnded']['content'], JSON_UNESCAPED_UNICODE)) && !preg_match('/\b30\b/', json_encode($texts['proTrialDaysLeft']['when'], JSON_UNESCAPED_UNICODE)),
    'trial: no « 60 days » nor « 30 days left » in the emails (EN, FR, ES)');
$before = (array) require $app . '/mail/mail-auto-texts-before.php';
$ok(MA_TEXTS_V === 3 && isset($before[2]['proTrialEnded']), 'trial: the earlier « 60 days » text is replaced where Mateo did not change it (MA_TEXTS_V 3)');

/* ───────────── step 3: the founding offer for the first N subscribers ───────────── */
$f = sb_state($pdo, 'new')['founding'];
$ok($f['eligible'] && $f['left'] === 3 && $f['cap'] === 3 && $f['percent'] === 50, 'founding: 3 places of 3 left, 50 % for life, open to every trader');
$ok(sb_state($pdo, 'new')['prices']['pro']['month']['founding'] === 9.5, 'founding: Pro at 9.50 instead of 19');
sb_checkout($pdo, 'new', 'pro', 'month');
$cs = $calls('POST', 'checkout/sessions');
$ok(($cs[0][2]['discounts'][0]['coupon'] ?? '') === 'FOUNDING50' && ($cs[0][2]['subscription_data']['metadata']['founding'] ?? '') === '1', 'founding: the checkout carries the coupon and marks the subscription founding');
foreach (['a', 'b'] as $u) { $signup($u); $subscribe("sub_$u", $u, true); }
$GLOBALS['SUBS']['sub_z'] = $sub('sub_z', 'z', 'incomplete', true); $signup('z');
sb_handle_event($pdo, ['id' => 'evt_z', 'type' => 'customer.subscription.created', 'data' => ['object' => $GLOBALS['SUBS']['sub_z']]]);
$f = sb_state($pdo, 'new')['founding'];
$ok($f['eligible'] && $f['left'] === 1, 'founding: 2 founders → 1 place left (a payment never completed takes no place)');
$subscribe('sub_new', 'new', true);
$signup('late');
$f = sb_state($pdo, 'late')['founding'];
$ok(!$f['eligible'] && $f['left'] === 0 && sb_state($pdo, 'late')['prices']['pro']['month']['founding'] === null, 'founding: at the 3rd founder the offer is gone for everyone else (no founding price shown)');
$ok(sb_state($pdo, 'new')['subscription']['founding'] === true, 'founding: the founder keeps his price');
$GLOBALS['SUBS']['sub_a']['status'] = 'canceled';
sb_handle_event($pdo, ['id' => 'evt_a_cancel', 'type' => 'customer.subscription.deleted', 'data' => ['object' => $GLOBALS['SUBS']['sub_a']]]);
$ok(sb_state($pdo, 'late')['founding']['left'] === 0, 'founding: a founder who cancels does not give his place back (the first 100 subscribers)');
sb_set_config(['founding_cap' => 100] + $base);
$ok(sb_state($pdo, 'late')['founding']['eligible'] && sb_state($pdo, 'late')['founding']['left'] === 97, 'founding: cap 100 → 97 places left');
$at('2026-12-01 23:58'); $ok(sb_state($pdo, 'late')['founding']['eligible'], 'founding: still open on Dec. 1 at 23:58 (New York)');
$at('2026-12-02 00:00'); $ok(!sb_state($pdo, 'late')['founding']['eligible'], 'founding: closed on Dec. 2 at midnight (New York)');

/* ───────────── step 4: « Pause 1 month » before « Cancel » ───────────── */
$at('2026-11-21 10:00');
$signup('p'); $subscribe('sub_p', 'p', false);
$pdo->exec("UPDATE billing_grants SET ends_at = " . (sb_now() - 1) . " WHERE uid = 'p'");   // his trial is over: he pays
$st = sb_state($pdo, 'p');
$ok($st['plan'] === 'pro' && $st['pause']['can'] && !$st['pause']['paused'], 'pause: a running subscription can be paused');
$STRIPE = [];
$r = sb_pause($pdo, 'p');
$c = $calls('POST', 'subscriptions/sub_p')[0][2] ?? [];
$ok(!empty($r['ok']) && ($c['pause_collection']['behavior'] ?? '') === 'void' && (int) ($c['pause_collection']['resumes_at'] ?? 0) === sb_now() + 30 * 86400,
    'pause: Stripe holds the payments (pause_collection void) and resumes in 30 days');
$st = sb_state($pdo, 'p');
$ok($st['plan'] === 'free' && $st['source'] === 'free' && $st['pause']['paused'] && $st['pause']['plan'] === 'pro' && $st['pause']['until'] === gmdate('c', sb_now() + 30 * 86400) && $st['subscription'] === null,
    'pause: Free during the pause, the plan and the date it resumes are known');
$ok(!$st['founding']['eligible'] && (sb_checkout($pdo, 'p', 'elite', 'month')['code'] ?? '') === 'paused', 'pause: no founding offer and no second subscription during the pause');
$ok(sb_q($pdo, "SELECT COUNT(*) FROM billing_subs WHERE uid = 'p'")->fetchColumn() == 1 && (sb_pause($pdo, 'p')['code'] ?? '') === 'no_pause', 'pause: nothing deleted; no second pause while paused');
// the « resumes in 3 days » email: once per pause, 3 days before
$until = (int) sb_paused_sub($pdo, 'p')['paused_until'];
$pz = function (int $now) use ($until): array {
    return array_values(array_filter(ma_daily_due(['id' => 'p', 'created_at' => '2026-11-21T15:00:00Z', 'last_login' => gmdate('c', $now)], ['live' => true, 'trial_end' => null, 'paying' => false, 'crew' => false, 'permanent' => false, 'pause' => ['until' => $until, 'plan' => 'Pro']], $now - 86400, $now), fn($x) => $x[1] === 'pauseEnding'));
};
$hit = $pz($until - 3 * 86400 + 60);
$ok($pz($until - 5 * 86400) === [] && count($hit) === 1 && $hit[0][0] === "pauseEnding:$until" && $hit[0][2] === ['plan' => 'Pro'] && $pz($until - 2 * 86400 + 60) === [],
    'pause: « resumes in 3 days » due once, 3 days before (its line carries the pause, so the next pause has its own)');
$texts = (array) require $app . '/mail/mail-auto-texts.php'; $push = (array) require $app . '/push/push-auto-texts.php';
$ok(isset($texts['pauseEnding']) && $texts['pauseEnding']['kind'] === 'transactional' && count(array_filter($texts['pauseEnding']['content'], fn($v) => strpos($v['subject'], '3') !== false)) === 3
    && ($push['pauseEnding']['ch'] ?? '') === 'both' && count($push['pauseEnding']['text']) === 3, 'pause: the email and the phone notification exist in EN, FR, ES');
// Resume now
$STRIPE = [];
$ok(!empty(sb_resume($pdo, 'p')['ok']) && array_key_exists('pause_collection', $calls('POST', 'subscriptions/sub_p')[0][2] ?? []) && ($calls('POST', 'subscriptions/sub_p')[0][2]['pause_collection'] ?? 'x') === '',
    'pause: « Resume now » clears the pause at Stripe');
$st = sb_state($pdo, 'p');
$ok($st['plan'] === 'pro' && !$st['pause']['paused'] && !$st['pause']['can'] && $st['pause']['next'] === gmdate('c', sb_now() + SB_PAUSE_EVERY * 86400), 'pause: back on Pro; the next pause in 6 months');
$at('2027-05-24 10:00');
$ok(sb_state($pdo, 'p')['pause']['can'], 'pause: possible again after 6 months');
// the pause ends at Stripe by itself: its webhook clears it
sb_pause($pdo, 'p');
$GLOBALS['SUBS']['sub_p']['pause_collection'] = null;
sb_handle_event($pdo, ['id' => 'evt_p_resumed', 'type' => 'customer.subscription.updated', 'data' => ['object' => $GLOBALS['SUBS']['sub_p']]]);
$ok(sb_state($pdo, 'p')['plan'] === 'pro' && !sb_state($pdo, 'p')['pause']['paused'], 'pause: Stripe\'s webhook at the end of the pause gives Pro back');
// a pause reaching its date without a webhook: Pro again from that date
$at('2027-12-01 10:00'); sb_pause($pdo, 'p'); $at('2028-01-01 10:00');
$ok(sb_state($pdo, 'p')['plan'] === 'pro', 'pause: past its date the subscription counts again, even before the webhook');
// none on a subscription ending, nor on Free
$signup('c'); $subscribe('sub_c', 'c', false);
$GLOBALS['SUBS']['sub_c']['cancel_at_period_end'] = true;
sb_handle_event($pdo, ['id' => 'evt_c_end', 'type' => 'customer.subscription.updated', 'data' => ['object' => $GLOBALS['SUBS']['sub_c']]]);
$ok(!sb_state($pdo, 'c')['pause']['can'] && (sb_pause($pdo, 'c')['code'] ?? '') === 'no_pause' && !sb_state($pdo, 'late')['pause']['can'], 'pause: not on a subscription already ending, nor without a subscription');

$pdo = null; array_map('unlink', glob($tmp . '/*') ?: []); @rmdir($tmp);
echo "\n$pass passed, $fail failed\n";
exit($fail ? 1 : 0);
