<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli' && realpath((string) ($_SERVER['SCRIPT_FILENAME'] ?? '')) === realpath(__FILE__)) { http_response_code(404); exit; }
/**
 * Sweep billing: Stripe. Plain cURL, no Composer, no SDK.
 * Stripe Checkout (hosted payment page) + Customer Portal (cancel, change card, switch plan) + webhooks.
 * Webhooks are the only thing that changes a subscription in the database. The redirect after payment is never trusted.
 */

require_once __DIR__ . '/billing-core.php';

function sb_stripe(string $method, string $path, array $params = [], string $idem = ''): array
{
    if (isset($GLOBALS['SB_STRIPE_MOCK'])) return ($GLOBALS['SB_STRIPE_MOCK'])($method, $path, $params);
    $key = (string) sb_cfg()['stripe_secret_key'];
    if ($key === '' || strpos($key, 'sk_') !== 0) throw new RuntimeException('Stripe secret key missing in billing-config.php');
    $url = rtrim((string) (sb_cfg()['stripe_api_base'] ?? 'https://api.stripe.com/v1'), '/') . '/' . ltrim($path, '/');
    $body = http_build_query($params, '', '&');
    if (!function_exists('curl_init')) {   // hosts without the cURL extension: PHP streams
        $ctx = stream_context_create(['http' => ['method' => $method, 'ignore_errors' => true, 'timeout' => 20,
            'header' => "Authorization: Basic " . base64_encode($key . ':') . "\r\nStripe-Version: 2024-06-20\r\nContent-Type: application/x-www-form-urlencoded\r\n" . ($idem !== '' ? "Idempotency-Key: $idem\r\n" : ''),
            'content' => $method === 'GET' ? '' : $body]]);
        $raw = @file_get_contents($method === 'GET' && $body !== '' ? "$url?$body" : $url, false, $ctx);
        $code = 0; foreach (($http_response_header ?? []) as $h) if (preg_match('#^HTTP/\S+\s+(\d{3})#', $h, $mm)) $code = (int) $mm[1];
        if ($raw === false) throw new RuntimeException('Stripe unreachable');
        $json = json_decode((string) $raw, true) ?: [];
        if ($code >= 400) throw new RuntimeException('Stripe ' . $code . ': ' . ($json['error']['message'] ?? 'error'));
        return $json;
    }
    $ch = curl_init($method === 'GET' && $body !== '' ? "$url?$body" : $url);
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT        => 20,
        CURLOPT_USERPWD        => $key . ':',
        CURLOPT_CUSTOMREQUEST  => $method,
        CURLOPT_HTTPHEADER     => array_merge(['Stripe-Version: 2024-06-20'], $idem !== '' ? ['Idempotency-Key: ' . $idem] : []),
    ]);
    if ($method !== 'GET') curl_setopt($ch, CURLOPT_POSTFIELDS, $body);
    $raw = curl_exec($ch);
    $code = (int) curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $err = curl_error($ch);
    curl_close($ch);
    if ($raw === false) throw new RuntimeException('Stripe unreachable: ' . $err);
    $json = json_decode((string) $raw, true) ?: [];
    if ($code >= 400) throw new RuntimeException('Stripe ' . $code . ': ' . ($json['error']['message'] ?? 'error'));
    return $json;
}

function sb_price_map(): array
{
    $map = [];
    foreach ((array) sb_cfg()['stripe_prices'] as $plan => $iv) foreach ((array) $iv as $interval => $id) $map[(string) $id] = [$plan, $interval];
    return $map;
}

function sb_customer(PDO $pdo, string $uid): string
{
    $row = sb_q($pdo, 'SELECT stripe_customer, email FROM billing_users WHERE uid = ?', [$uid])->fetch(PDO::FETCH_ASSOC) ?: [];
    if (!empty($row['stripe_customer'])) return (string) $row['stripe_customer'];
    $params = ['metadata' => ['uid' => $uid]];
    if (!empty($row['email']) && filter_var($row['email'], FILTER_VALIDATE_EMAIL)) $params['email'] = $row['email'];
    $c = sb_stripe('POST', 'customers', $params);
    sb_q($pdo, 'UPDATE billing_users SET stripe_customer = ? WHERE uid = ?', [$c['id'], $uid]);
    return (string) $c['id'];
}

/** Returns ['url' => stripe page]. Founding price is applied automatically when the user is eligible. */
function sb_checkout(PDO $pdo, string $uid, string $plan, string $interval, string $trigger = '', array $user = []): array
{
    $cfg = sb_cfg();
    if (!sb_live($uid)) return ['error' => 'Billing is not live yet', 'code' => 'not_live'];
    $price = $cfg['stripe_prices'][$plan][$interval] ?? '';
    if (!in_array($plan, ['pro', 'elite'], true) || !in_array($interval, ['month', 'year'], true) || $price === '') {
        return ['error' => 'Unknown plan', 'code' => 'bad_plan'];
    }
    $state = sb_state($pdo, $uid, $user);
    // Already paying: plan switches happen in the portal (prorated, keeps the founding discount).
    if ($state['subscription']) return sb_portal($pdo, $uid);

    $base = rtrim((string) $cfg['app_url'], '/') . '/';
    $founding = $state['founding']['eligible'];
    $p = [
        'mode' => 'subscription',
        'customer' => sb_customer($pdo, $uid),
        'client_reference_id' => $uid,
        'line_items' => [['price' => $price, 'quantity' => 1]],
        'success_url' => $base . '?billing=success&plan=' . $plan,
        'cancel_url'  => $base . '?billing=cancel',
        'metadata' => ['uid' => $uid, 'trigger' => substr($trigger, 0, 48), 'founding' => $founding ? '1' : '0'],
        'subscription_data' => ['metadata' => ['uid' => $uid, 'founding' => $founding ? '1' : '0']],
    ];
    if ($founding) $p['discounts'] = [['coupon' => (string) $cfg['stripe_founding_coupon']]];
    else $p['allow_promotion_codes'] = 'true';
    if (!empty($cfg['stripe_automatic_tax'])) {
        $p['automatic_tax'] = ['enabled' => 'true'];
        $p['customer_update'] = ['address' => 'auto', 'name' => 'auto'];
        $p['billing_address_collection'] = 'required';
    }
    $s = sb_stripe('POST', 'checkout/sessions', $p);
    sb_log_upsell($pdo, $uid, $trigger ?: 'plans_page', 'checkout', false);
    return ['url' => (string) $s['url']];
}

function sb_portal(PDO $pdo, string $uid): array
{
    if (!sb_live($uid)) return ['error' => 'Billing is not live yet', 'code' => 'not_live'];
    $s = sb_stripe('POST', 'billing_portal/sessions', [
        'customer' => sb_customer($pdo, $uid),
        'return_url' => rtrim((string) sb_cfg()['app_url'], '/') . '/?billing=portal',
    ]);
    return ['url' => (string) $s['url']];
}

/* ───────────────────────────── webhooks ───────────────────────────── */

function sb_verify_signature(string $payload, string $header, string $secret, int $tolerance = 300): bool
{
    if ($secret === '' || $header === '') return false;
    $t = null; $sigs = [];
    foreach (explode(',', $header) as $part) {
        [$k, $v] = array_pad(explode('=', trim($part), 2), 2, '');
        if ($k === 't') $t = (int) $v;
        if ($k === 'v1') $sigs[] = $v;
    }
    if (!$t || !$sigs || abs(sb_now() - $t) > $tolerance) return false;
    $expected = hash_hmac('sha256', $t . '.' . $payload, $secret);
    foreach ($sigs as $s) if (hash_equals($expected, $s)) return true;
    return false;
}

/** Writes a Stripe subscription object into billing_subs. Returns the uid it belongs to (or null). */
function sb_sync_subscription(PDO $pdo, array $sub, ?string $uidHint = null): ?string
{
    $uid = (string) ($sub['metadata']['uid'] ?? '') ?: $uidHint;
    $customer = is_array($sub['customer'] ?? null) ? ($sub['customer']['id'] ?? '') : (string) ($sub['customer'] ?? '');
    if (!$uid && $customer) $uid = (string) (sb_q($pdo, 'SELECT uid FROM billing_users WHERE stripe_customer = ?', [$customer])->fetchColumn() ?: '');
    if (!$uid) { error_log('[Sweep billing] subscription ' . ($sub['id'] ?? '?') . ' has no user'); return null; }

    $item = $sub['items']['data'][0] ?? [];
    $priceId = (string) ($item['price']['id'] ?? $sub['plan']['id'] ?? '');
    [$plan, $interval] = sb_price_map()[$priceId] ?? [null, null];
    if (!$plan) { error_log('[Sweep billing] unknown price ' . $priceId); return null; }

    $coupon = (string) sb_cfg()['stripe_founding_coupon'];
    $founding = ($sub['metadata']['founding'] ?? '') === '1'
        || ($coupon !== '' && (($sub['discount']['coupon']['id'] ?? '') === $coupon));
    foreach ((array) ($sub['discounts'] ?? []) as $d) if (is_array($d) && (($d['coupon']['id'] ?? '') === $coupon)) $founding = true;

    $status = (string) ($sub['status'] ?? 'incomplete');
    $periodEnd = $sub['current_period_end'] ?? $item['current_period_end'] ?? null;
    $now = sb_now();
    $prev = sb_q($pdo, 'SELECT past_due_since, founding FROM billing_subs WHERE id = ?', [$sub['id']])->fetch(PDO::FETCH_ASSOC);
    if ($prev && (int) $prev['founding'] === 1) $founding = true;   // founding price is for life on this subscription
    $pastDueSince = $status === 'past_due' ? (int) (($prev['past_due_since'] ?? null) ?: $now) : null;

    $vals = [$uid, 'stripe', $plan, $interval, $status, $founding ? 1 : 0, $priceId, $periodEnd ? (int) $periodEnd : null,
             !empty($sub['cancel_at_period_end']) ? 1 : 0, $pastDueSince, $now];
    if ($prev !== false) {
        sb_q($pdo, 'UPDATE billing_subs SET uid=?, source=?, plan=?, billing_interval=?, status=?, founding=?, price_id=?, period_end=?, cancel_at_period_end=?, past_due_since=?, updated_at=? WHERE id = ?', [...$vals, $sub['id']]);
    } else {
        sb_q($pdo, 'INSERT INTO billing_subs (uid, source, plan, billing_interval, status, founding, price_id, period_end, cancel_at_period_end, past_due_since, updated_at, id) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)', [...$vals, $sub['id']]);
    }
    if ($customer) sb_q($pdo, 'UPDATE billing_users SET stripe_customer = ? WHERE uid = ? AND (stripe_customer IS NULL OR stripe_customer = \'\')', [$customer, $uid]);
    return $uid;
}

/** Handles one verified event. Returns a short description (for the log / tests). */
function sb_handle_event(PDO $pdo, array $event): string
{
    sb_schema($pdo);
    $id = (string) ($event['id'] ?? '');
    $type = (string) ($event['type'] ?? '');
    $obj = (array) ($event['data']['object'] ?? []);
    if ($id === '') return 'ignored: no id';
    if (sb_q($pdo, 'SELECT 1 FROM billing_webhooks WHERE event_id = ?', [$id])->fetchColumn()) return 'duplicate';

    $result = 'ignored';
    switch ($type) {
        case 'checkout.session.completed':
            if (($obj['mode'] ?? '') === 'subscription' && !empty($obj['subscription'])) {
                $uid = (string) ($obj['client_reference_id'] ?? $obj['metadata']['uid'] ?? '');
                $sub = is_array($obj['subscription']) ? $obj['subscription'] : sb_stripe('GET', 'subscriptions/' . $obj['subscription']);
                $uid = sb_sync_subscription($pdo, $sub, $uid ?: null);
                if ($uid) sb_log_upsell($pdo, $uid, (string) ($obj['metadata']['trigger'] ?? '') ?: 'plans_page', 'converted', false);
                $result = 'subscribed ' . ($uid ?? '?');
            }
            break;
        case 'customer.subscription.created':
        case 'customer.subscription.updated':
        case 'customer.subscription.deleted':
        case 'customer.subscription.paused':
        case 'customer.subscription.resumed':
            $uid = sb_sync_subscription($pdo, $obj);
            $result = 'synced ' . ($obj['status'] ?? '') . ' ' . ($uid ?? '?');
            break;
        case 'invoice.paid':
        case 'invoice.payment_failed':
            $subId = $obj['subscription'] ?? ($obj['parent']['subscription_details']['subscription'] ?? null);
            if (is_array($subId)) $subId = $subId['id'] ?? null;
            if ($subId) {
                $uid = sb_sync_subscription($pdo, sb_stripe('GET', 'subscriptions/' . $subId));
                $result = 'invoice synced ' . ($uid ?? '?');
                // referrals: a friend's first real payment qualifies the referral
                if ($type === 'invoice.paid' && $uid && (int) ($obj['amount_paid'] ?? 0) > 0 && function_exists('ref_on_first_payment')) {
                    try { ref_on_first_payment($pdo, (string) $uid); } catch (Throwable $e) { error_log('[Sweep referral] payment hook: ' . $e->getMessage()); }
                }
            }
            break;
    }
    sb_q($pdo, 'INSERT INTO billing_webhooks (event_id, type, at) VALUES (?, ?, ?)', [$id, $type, sb_now()]);
    return $result;
}

/** Entry point for Stripe. Must be routed BEFORE the sign-in check. */
function sweep_billing_webhook_route(PDO $pdo): void
{
    $payload = (string) file_get_contents('php://input');
    $sig = (string) ($_SERVER['HTTP_STRIPE_SIGNATURE'] ?? '');
    if (!sb_verify_signature($payload, $sig, (string) sb_cfg()['stripe_webhook_secret'])) sb_out(400, ['error' => 'bad signature']);
    $event = json_decode($payload, true);
    if (!is_array($event)) sb_out(400, ['error' => 'bad payload']);
    try {
        sb_out(200, ['ok' => true, 'result' => sb_handle_event($pdo, $event)]);
    } catch (Throwable $e) {
        error_log('[Sweep billing] webhook: ' . $e->getMessage());
        sb_out(500, ['error' => 'webhook failed']);   // Stripe retries automatically
    }
}

function sb_out(int $code, array $data): void
{
    if (isset($GLOBALS['SB_OUT_CAPTURE'])) { throw new SbOut($code, $data); }
    http_response_code($code);
    header('Content-Type: application/json; charset=utf-8');
    header('Cache-Control: no-store');
    echo json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    exit;
}

final class SbOut extends Exception
{
    public int $status; public array $data;
    public function __construct(int $status, array $data) { parent::__construct('out'); $this->status = $status; $this->data = $data; }
}
