<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli' && realpath((string) ($_SERVER['SCRIPT_FILENAME'] ?? '')) === realpath(__FILE__)) { http_response_code(404); exit; }
/**
 * Sweep billing: routes. Wire into the app's router like this:
 *
 * BEFORE the sign-in check (Stripe calls it, no session):
 *     if ($route === 'api/billing/webhook') { require_once __DIR__ . '/billing/billing-routes.php'; sweep_billing_webhook_route(db()); }
 *
 * AFTER the signed-in user is known:
 *     if (strpos($route, 'api/billing/') === 0) {
 *         require_once __DIR__ . '/billing/billing-routes.php';
 *         sweep_billing_route($route, $method, (string) $UID, db(), [
 *             'created_at'  => $me['created_at'],          // signup date (unix or ISO) — decides early access vs trial
 *             'email'       => $me['email'] ?? null,       // prefills Stripe checkout (optional)
 *             'account_ids' => $accountIds,                  // the user's trading account ids, oldest first (array or callable)
 *         ]);
 *     }
 *
 * Routes (JSON):
 *   GET  api/billing/me               → plan, limits, usage, trial, founding, prices, frozen accounts…
 *   POST api/billing/checkout         {plan: pro|elite, interval: month|year, trigger} → {url}
 *   POST api/billing/portal           → {url}   (manage / cancel / switch plan / change card)
 *   POST api/billing/active-accounts  {ids: [...]} → choose which accounts stay active on Free
 *   POST api/billing/upsell           {trigger, action: shown|dismissed|clicked, blocking: bool}
 *   GET  api/billing/funnel           → conversion by paywall trigger (only for user ids listed in admin_users)
 */

require_once __DIR__ . '/billing-core.php';
require_once __DIR__ . '/billing-stripe.php';

function sb_is_admin(string $uid): bool
{
    try { $c = sb_cfg(); } catch (Throwable $e) { return false; }
    return in_array($uid, array_map('strval', array_merge((array) ($c['admin_users'] ?? []), (array) ($c['test_users'] ?? []))), true);
}

function sweep_billing_route(string $route, string $method, string $uid, PDO $pdo, array $user = []): void
{
    $post = strtoupper($method) === 'POST';
    $b = [];
    if ($post) $b = json_decode((string) file_get_contents('php://input'), true) ?: $_POST;
    if (isset($user['account_ids']) && is_callable($user['account_ids'])) $user['account_ids'] = (array) ($user['account_ids'])();

    try {
        sb_schema($pdo);
        sb_user($pdo, $uid, $user['created_at'] ?? null, $user['email'] ?? null);
        switch ($route) {
            case 'api/billing/me':
                sb_out(200, sb_state($pdo, $uid, $user));

            case 'api/billing/checkout':
                if (!$post) break;
                $r = sb_checkout($pdo, $uid, (string) ($b['plan'] ?? ''), (string) ($b['interval'] ?? 'year'), (string) ($b['trigger'] ?? ''), $user);
                if (isset($r['error'])) error_log('[Sweep billing] api/billing/checkout: ' . $r['error'] . ' (' . ($r['code'] ?? '') . ')');
                sb_out(isset($r['error']) ? 400 : 200, $r + (isset($r['error']) && (sb_is_admin($uid) || !empty($user['is_admin'])) ? ['detail' => $r['error']] : []));

            case 'api/billing/portal':
                if (!$post) break;
                $r = sb_portal($pdo, $uid);
                if (isset($r['error'])) error_log('[Sweep billing] api/billing/portal: ' . $r['error'] . ' (' . ($r['code'] ?? '') . ')');
                sb_out(isset($r['error']) ? 400 : 200, $r + (isset($r['error']) && (sb_is_admin($uid) || !empty($user['is_admin'])) ? ['detail' => $r['error']] : []));

            case 'api/billing/active-accounts':
                if (!$post) break;
                sb_out(200, sb_set_active_accounts($pdo, $uid, (array) ($b['ids'] ?? []), (array) ($user['account_ids'] ?? [])));

            case 'api/billing/upsell':
                if (!$post) break;
                sb_log_upsell($pdo, $uid, (string) ($b['trigger'] ?? ''), (string) ($b['action'] ?? 'shown'), !empty($b['blocking']));
                sb_out(200, ['ok' => true, 'blocking_left' => sb_paywall_left($pdo, $uid)]);

            case 'api/billing/diag':   // setup checklist for the owner (app administrators, admin_users, test_users)
                if (!sb_is_admin($uid) && empty($user['is_admin'])) sb_out(403, ['error' => 'forbidden']);
                sb_out(200, ['checks' => sb_diag()]);

            case 'api/billing/funnel':
                if (!in_array($uid, array_map('strval', (array) (sb_cfg()['admin_users'] ?? [])), true)) sb_out(403, ['error' => 'forbidden']);
                sb_out(200, ['days' => 30, 'triggers' => sb_funnel($pdo, (int) ($_GET['days'] ?? 30))]);
        }
        sb_out(404, ['error' => 'not found']);
    } catch (SbOut $o) {
        throw $o;
    } catch (Throwable $e) {
        error_log('[Sweep billing] ' . $route . ': ' . $e->getMessage() . ' @ ' . $e->getFile() . ':' . $e->getLine());
        // the owner (admin_users / test_users) sees Stripe's exact reason under the button; traders see a generic message
        sb_out(500, ['error' => 'Billing is temporarily unavailable', 'code' => 'server'] + (sb_is_admin($uid) || !empty($user['is_admin']) ? ['detail' => $e->getMessage()] : []));
    }
}

/** Checks billing-config.php and Stripe one item at a time, so a setup problem names itself. */
function sb_diag(): array
{
    $c = sb_cfg(); $out = [];
    $add = function (string $label, bool $ok, string $detail = '') use (&$out) { $out[] = ['label' => $label, 'ok' => $ok, 'detail' => $detail]; };
    $add('Billing switch', true, !empty($c['live']) ? "live = true (billing is on for everyone)" : ('live = false' . (count((array) ($c['test_users'] ?? [])) ? ' · test users: ' . implode(', ', (array) $c['test_users']) : ' · no test users')));
    $add('Server can call Stripe', function_exists('curl_init') || ini_get('allow_url_fopen'), function_exists('curl_init') ? 'cURL available' : (ini_get('allow_url_fopen') ? 'PHP streams (no cURL)' : 'Neither cURL nor allow_url_fopen: ask your host'));
    $key = (string) ($c['stripe_secret_key'] ?? '');
    $mode = strpos($key, 'sk_live_') === 0 ? 'live' : (strpos($key, 'sk_test_') === 0 ? 'test' : null);
    $add('Stripe secret key', $mode !== null, $mode ? "$mode mode key" : 'Missing or not a secret key (must start with sk_test_ or sk_live_; rk_ restricted keys and pk_ publishable keys do not work)');
    $wh = (string) ($c['stripe_webhook_secret'] ?? '');
    $add('Webhook signing secret', strpos($wh, 'whsec_') === 0, strpos($wh, 'whsec_') === 0 ? 'Set' : 'Missing (Developers → Webhooks → your endpoint → Signing secret, starts with whsec_)');
    if ($mode === null) return $out;
    try { $acct = sb_stripe('GET', 'balance'); $add('Stripe accepts the key', true, 'Connected'); }
    catch (Throwable $e) { $add('Stripe accepts the key', false, $e->getMessage()); return $out; }
    foreach ((array) ($c['stripe_prices'] ?? []) as $plan => $iv) foreach ((array) $iv as $interval => $id) {
        $label = ucfirst((string) $plan) . ' · ' . ($interval === 'year' ? 'yearly' : 'monthly') . ' price';
        if (strpos((string) $id, 'price_') !== 0 || preg_match('/^price_(PRO|ELITE)_/', (string) $id)) { $add($label, false, "Still a placeholder ($id): copy the real price_… id from Stripe"); continue; }
        try {
            $p = sb_stripe('GET', 'prices/' . $id);
            $amt = isset($p['unit_amount']) ? number_format($p['unit_amount'] / 100, 2) . ' ' . strtoupper((string) ($p['currency'] ?? '')) : '?';
            $rec = $p['recurring']['interval'] ?? null;
            $ok = !empty($p['active']) && $rec === $interval && (bool) ($p['livemode'] ?? false) === ($mode === 'live');
            $add($label, $ok, $ok ? "$amt / $rec" : trim((empty($p['active']) ? 'Price is archived. ' : '') . ($rec !== $interval ? "Billing period is '$rec', expected '$interval'. " : '') . (((bool) ($p['livemode'] ?? false)) !== ($mode === 'live') ? 'Price and key are not in the same mode (test vs live).' : '')));
        } catch (Throwable $e) { $add($label, false, $e->getMessage()); }
    }
    $cp = (string) ($c['stripe_founding_coupon'] ?? '');
    if ($cp === '') $add('Founding coupon', false, 'No coupon id in the config');
    else {
        try { $k = sb_stripe('GET', 'coupons/' . rawurlencode($cp)); $ok = !empty($k['valid']);
            $add('Founding coupon', $ok, $ok ? ($k['percent_off'] ?? '?') . '% off · ' . ($k['duration'] ?? '') : 'Coupon exists but is no longer valid'); }
        catch (Throwable $e) { $add('Founding coupon', false, $e->getMessage() . " — create a coupon whose ID is exactly '$cp'"); }
    }
    $add('Return address after payment', strpos((string) ($c['app_url'] ?? ''), 'https://') === 0, (string) ($c['app_url'] ?? ''));
    return $out;
}
