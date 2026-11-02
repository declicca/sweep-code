<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli' && realpath((string) ($_SERVER['SCRIPT_FILENAME'] ?? '')) === realpath(__FILE__)) { http_response_code(404); exit; }
/**
 * Sweep — creator program (brief « avance concurrentielle », step 5). Builds on the referral program (growth/referral.php).
 *
 * - The Creator status is given by Sweep only, from Admin (no self sign-up). Giving it creates, through the existing Stripe
 *   helper (sb_stripe), a coupon (CR_PROMO_PERCENT % off for CR_PROMO_MONTHS months) and a promotion code equal to the
 *   creator's code. If Stripe refuses, the status is not given and Admin sees Stripe's reason.
 * - The creator's link: makeitsweep.com/?ref=CODE (the app also takes /?ref=CODE and /r/CODE: same cookie, same click count).
 * - Commission: CR_RATE_BP / 100 % of each invoice really paid by a trader the creator brought, for CR_MONTHS months from that
 *   trader's first paid invoice. A refund reverses the commission of that payment (in proportion when partial). A cancelled
 *   subscription stops future commissions. Everything comes from Stripe's webhooks (billing/billing-stripe.php). Amounts in cents.
 * - Payouts stay manual: Admin marks a month as paid (nothing moves money) and exports the statement (CSV).
 * - Everyone else keeps the referral program as it is (a free month); a creator earns the commission instead of free months.
 * Tables (created on first use, SQLite and MySQL): creators, creator_refs, creator_ledger, creator_payouts.
 */
const CR_RATE_BP = 3000, CR_MONTHS = 12, CR_PROMO_PERCENT = 20, CR_PROMO_MONTHS = 3;
const CR_SITE = 'https://makeitsweep.com/';

function cr_schema(PDO $pdo): void
{
    static $done = false; if ($done) return; $done = true;
    $my = $pdo->getAttribute(PDO::ATTR_DRIVER_NAME) === 'mysql';
    $id = $my ? 'INT UNSIGNED AUTO_INCREMENT PRIMARY KEY' : 'INTEGER PRIMARY KEY AUTOINCREMENT';
    $k = $my ? 'VARCHAR(120)' : 'TEXT'; $tail = $my ? ' DEFAULT CHARSET=utf8mb4' : '';
    $pdo->exec("CREATE TABLE IF NOT EXISTS creators (uid $k NOT NULL PRIMARY KEY, code $k NOT NULL, coupon_id $k NULL, promo_id $k NULL,
        rate_bp INTEGER NOT NULL, months INTEGER NOT NULL, created_at INTEGER NOT NULL, created_by $k NULL)$tail");
    // one row per trader a creator brought who paid: when the 12 months start, and when the subscription was cancelled
    $pdo->exec("CREATE TABLE IF NOT EXISTS creator_refs (referee_id $k NOT NULL PRIMARY KEY, creator_id $k NOT NULL, first_paid_at INTEGER NOT NULL, canceled_at INTEGER NULL)$tail");
    // one row per paid invoice (kind 'payment') or refund (kind 'refund', negative); source_id makes each webhook count once
    $pdo->exec("CREATE TABLE IF NOT EXISTS creator_ledger (id $id, creator_id $k NOT NULL, referee_id $k NOT NULL, kind VARCHAR(10) NOT NULL, source_id $k NOT NULL,
        invoice_id $k NULL, charge_id $k NULL, pi_id $k NULL, amount_c INTEGER NOT NULL, commission_c INTEGER NOT NULL, currency VARCHAR(8) NOT NULL,
        at INTEGER NOT NULL, month VARCHAR(7) NOT NULL)$tail");
    try { $pdo->exec('CREATE UNIQUE INDEX creator_ledger_src ON creator_ledger(source_id)'); } catch (Throwable $e) {}
    try { $pdo->exec('CREATE INDEX creator_ledger_cm ON creator_ledger(creator_id, month)'); } catch (Throwable $e) {}
    $pdo->exec("CREATE TABLE IF NOT EXISTS creator_payouts (id $id, creator_id $k NOT NULL, month VARCHAR(7) NOT NULL, amount_c INTEGER NOT NULL,
        paid_at INTEGER NOT NULL, paid_by $k NULL)$tail");
    try { $pdo->exec('CREATE UNIQUE INDEX creator_payouts_cm ON creator_payouts(creator_id, month)'); } catch (Throwable $e) {}
}
function cr_q(PDO $pdo, string $sql, array $a = []): PDOStatement { $st = $pdo->prepare($sql); $st->execute($a); return $st; }
function cr_now(): int { return function_exists('sb_now') ? sb_now() : time(); }
/** The statement month, New York time (Sweep's trading day is New York's). */
function cr_month(int $ts): string { return (new DateTimeImmutable('@' . $ts))->setTimezone(new DateTimeZone('America/New_York'))->format('Y-m'); }
function cr_get(PDO $pdo, string $uid): ?array
{
    cr_schema($pdo);
    $r = cr_q($pdo, 'SELECT * FROM creators WHERE uid = ?', [$uid])->fetch(PDO::FETCH_ASSOC);
    return $r ?: null;
}
function cr_link(string $code): string { return CR_SITE . '?ref=' . rawurlencode($code); }

/**
 * Admin › Creators › « Make creator ». $code: optional, replaces the trader's referral code (letters and digits, 3 to 16).
 * Returns ['ok' => true, 'creator' => row] or ['error' => reason]. Nothing is saved unless Stripe created the promotion code.
 */
function cr_make(PDO $pdo, string $uid, string $code = '', string $by = ''): array
{
    cr_schema($pdo); ref_schema($pdo);
    if ($uid === '' || !cr_q($pdo, 'SELECT 1 FROM users WHERE id = ?', [$uid])->fetchColumn()) return ['error' => 'No trader with this username or email.'];
    if (cr_get($pdo, $uid)) return ['error' => 'This trader is already a creator.'];
    if (!function_exists('billing_on') || !billing_on()) return ['error' => 'Billing is off: Stripe cannot create the promo code.'];
    $code = strtoupper(trim($code));
    if ($code !== '') {
        if (!preg_match('/^[A-Z0-9]{3,16}$/', $code)) return ['error' => 'The code must be 3 to 16 letters or digits.'];
        $own = ref_find_by_code($pdo, $code);
        if ($own && (string) $own['uid'] !== $uid) return ['error' => 'This code is already used by another trader.'];
    } else $code = ref_get_code($pdo, $uid);
    require_once dirname(__DIR__) . '/billing/billing-stripe.php';
    try {
        $coupon = sb_stripe('POST', 'coupons', ['percent_off' => CR_PROMO_PERCENT, 'duration' => 'repeating', 'duration_in_months' => CR_PROMO_MONTHS,
            'name' => 'Sweep creator ' . $code, 'metadata' => ['creator_uid' => $uid]], 'sweep-creator-coupon-' . $uid . '-' . $code);
        if (empty($coupon['id'])) throw new RuntimeException('Stripe did not return a coupon');
        $promo = sb_stripe('POST', 'promotion_codes', ['coupon' => (string) $coupon['id'], 'code' => $code, 'metadata' => ['creator_uid' => $uid],
            'restrictions' => ['first_time_transaction' => 'true']], 'sweep-creator-promo-' . $uid . '-' . $code);
        if (empty($promo['id'])) throw new RuntimeException('Stripe did not return a promotion code');
    } catch (Throwable $e) {
        error_log('[Sweep creators] make ' . $uid . ': ' . $e->getMessage());
        return ['error' => 'Stripe refused: ' . $e->getMessage()];
    }
    ref_row($pdo, $uid);
    cr_q($pdo, 'UPDATE ref_users SET code = ? WHERE uid = ?', [$code, $uid]);
    cr_q($pdo, 'INSERT INTO creators (uid, code, coupon_id, promo_id, rate_bp, months, created_at, created_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
        [$uid, $code, (string) $coupon['id'], (string) $promo['id'], CR_RATE_BP, CR_MONTHS, cr_now(), $by]);
    return ['ok' => true, 'creator' => cr_get($pdo, $uid)];
}

/** The creator who brought this trader (a referral that was not rejected), or null. */
function cr_creator_of(PDO $pdo, string $refereeId): ?array
{
    cr_schema($pdo); ref_schema($pdo);
    $r = cr_q($pdo, "SELECT c.* FROM referrals r JOIN creators c ON c.uid = r.referrer_id WHERE r.referee_id = ? AND r.status <> 'rejected'", [$refereeId])->fetch(PDO::FETCH_ASSOC);
    return $r ?: null;
}
/** Checkout: the creator's promotion code for a trader the creator brought, until the trader has paid once. */
function cr_checkout_promo(PDO $pdo, string $uid): ?string
{
    $c = cr_creator_of($pdo, $uid);
    if (!$c || empty($c['promo_id'])) return null;
    if (cr_q($pdo, 'SELECT 1 FROM creator_refs WHERE referee_id = ?', [$uid])->fetchColumn()) return null;
    return (string) $c['promo_id'];
}
/** The promotion codes an invoice used (Stripe's shapes: discount, discounts[] as objects). */
function cr_invoice_promos(array $inv): array
{
    $out = [];
    $d = $inv['discount'] ?? null; if (is_array($d) && !empty($d['promotion_code'])) $out[] = is_array($d['promotion_code']) ? (string) ($d['promotion_code']['id'] ?? '') : (string) $d['promotion_code'];
    foreach ((array) ($inv['discounts'] ?? []) as $d) if (is_array($d) && !empty($d['promotion_code'])) $out[] = is_array($d['promotion_code']) ? (string) ($d['promotion_code']['id'] ?? '') : (string) $d['promotion_code'];
    return array_values(array_filter(array_unique($out)));
}
function cr_id($v): string { return is_array($v) ? (string) ($v['id'] ?? '') : (string) ($v ?? ''); }

/** Webhook invoice.paid: 30 % of what was paid, within 12 months of the trader's first paid invoice, unless cancelled. */
function cr_on_invoice_paid(PDO $pdo, string $uid, array $inv): string
{
    cr_schema($pdo); ref_schema($pdo);
    $paid = (int) ($inv['amount_paid'] ?? 0);
    $invId = (string) ($inv['id'] ?? '');
    if ($paid <= 0 || $invId === '') return 'no amount';
    $c = cr_creator_of($pdo, $uid);
    if (!$c) {
        // a trader who typed a creator's code at checkout, without the link: the code brings him to that creator
        $promos = cr_invoice_promos($inv);
        if (!$promos) return 'no creator';
        $c = cr_q($pdo, 'SELECT * FROM creators WHERE promo_id IN (' . implode(',', array_fill(0, count($promos), '?')) . ')', $promos)->fetch(PDO::FETCH_ASSOC) ?: null;
        if (!$c || (string) $c['uid'] === $uid) return 'no creator';
        if (cr_q($pdo, 'SELECT 1 FROM referrals WHERE referee_id = ?', [$uid])->fetchColumn()) return 'referred by someone else';
        ref_row($pdo, $uid);
        cr_q($pdo, "INSERT INTO referrals (referrer_id, referee_id, status, qualify_reason, ip_hash, created_at) VALUES (?, ?, 'pending', 'promo_code', NULL, ?)", [$c['uid'], $uid, cr_now()]);
        cr_q($pdo, 'UPDATE ref_users SET referred_by = ? WHERE uid = ?', [$c['uid'], $uid]);
    }
    $at = (int) ($inv['status_transitions']['paid_at'] ?? 0) ?: cr_now();
    $ref = cr_q($pdo, 'SELECT * FROM creator_refs WHERE referee_id = ?', [$uid])->fetch(PDO::FETCH_ASSOC);
    if (!$ref) {
        cr_q($pdo, 'INSERT INTO creator_refs (referee_id, creator_id, first_paid_at, canceled_at) VALUES (?, ?, ?, NULL)', [$uid, $c['uid'], $at]);
        $ref = ['referee_id' => $uid, 'creator_id' => $c['uid'], 'first_paid_at' => $at, 'canceled_at' => null];
    }
    if ($ref['canceled_at'] !== null && $at >= (int) $ref['canceled_at']) return 'cancelled';
    $end = (new DateTimeImmutable('@' . (int) $ref['first_paid_at']))->modify('+' . (int) $c['months'] . ' months')->getTimestamp();
    if ($at >= $end) return 'after the window';
    $commission = (int) round($paid * (int) $c['rate_bp'] / 10000);
    try {
        cr_q($pdo, 'INSERT INTO creator_ledger (creator_id, referee_id, kind, source_id, invoice_id, charge_id, pi_id, amount_c, commission_c, currency, at, month) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
            [$ref['creator_id'], $uid, 'payment', 'inv:' . $invId, $invId, cr_id($inv['charge'] ?? null) ?: null, cr_id($inv['payment_intent'] ?? null) ?: null,
             $paid, $commission, strtolower((string) ($inv['currency'] ?? 'usd')), $at, cr_month($at)]);
    } catch (Throwable $e) { return 'duplicate'; }
    return 'commission ' . $commission;
}

/** Webhook charge.refunded: the commission of that payment goes back, in proportion to what was refunded so far. */
function cr_on_refund(PDO $pdo, array $ch): string
{
    cr_schema($pdo);
    $inv = cr_id($ch['invoice'] ?? null); $chId = cr_id($ch['id'] ?? null); $pi = cr_id($ch['payment_intent'] ?? null);
    $conds = []; $args = [];
    foreach (['invoice_id' => $inv, 'charge_id' => $chId, 'pi_id' => $pi] as $col => $v) if ($v !== '') { $conds[] = "$col = ?"; $args[] = $v; }
    if (!$conds) return 'no payment';
    $p = cr_q($pdo, "SELECT * FROM creator_ledger WHERE kind = 'payment' AND (" . implode(' OR ', $conds) . ')', $args)->fetch(PDO::FETCH_ASSOC);
    if (!$p) return 'no commission';
    $refunded = min((int) ($ch['amount_refunded'] ?? 0), (int) $p['amount_c']);
    if ($refunded <= 0) return 'nothing refunded';
    $target = -(int) round((int) $p['commission_c'] * $refunded / max(1, (int) $p['amount_c']));
    $done = (int) cr_q($pdo, "SELECT COALESCE(SUM(commission_c), 0) FROM creator_ledger WHERE kind = 'refund' AND invoice_id = ?", [$p['invoice_id']])->fetchColumn();
    $doneAmt = (int) cr_q($pdo, "SELECT COALESCE(SUM(amount_c), 0) FROM creator_ledger WHERE kind = 'refund' AND invoice_id = ?", [$p['invoice_id']])->fetchColumn();
    $delta = $target - $done;
    if ($delta === 0) return 'already reversed';
    $at = cr_now();
    try {
        cr_q($pdo, 'INSERT INTO creator_ledger (creator_id, referee_id, kind, source_id, invoice_id, charge_id, pi_id, amount_c, commission_c, currency, at, month) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
            [$p['creator_id'], $p['referee_id'], 'refund', 'ref:' . ($chId ?: $p['invoice_id']) . ':' . $refunded, $p['invoice_id'], $chId ?: $p['charge_id'], $pi ?: $p['pi_id'],
             -($refunded + $doneAmt), $delta, $p['currency'], $at, cr_month($at)]);
    } catch (Throwable $e) { return 'duplicate'; }
    return 'reversed ' . $delta;
}

/** Webhook customer.subscription.deleted: no commission on anything this trader pays afterwards. */
function cr_on_cancel(PDO $pdo, string $uid): void
{
    cr_schema($pdo);
    cr_q($pdo, 'UPDATE creator_refs SET canceled_at = ? WHERE referee_id = ? AND canceled_at IS NULL', [cr_now(), $uid]);
}

/** Totals of one creator (cents). */
function cr_totals(PDO $pdo, string $uid): array
{
    cr_schema($pdo); ref_schema($pdo);
    $month = cr_month(cr_now());
    $earned = (int) cr_q($pdo, 'SELECT COALESCE(SUM(commission_c), 0) FROM creator_ledger WHERE creator_id = ?', [$uid])->fetchColumn();
    $paid = (int) cr_q($pdo, 'SELECT COALESCE(SUM(amount_c), 0) FROM creator_payouts WHERE creator_id = ?', [$uid])->fetchColumn();
    $paying = 0;
    try {
        $paying = (int) cr_q($pdo, "SELECT COUNT(DISTINCT s.uid) FROM billing_subs s JOIN referrals r ON r.referee_id = s.uid
            WHERE r.referrer_id = ? AND r.status <> 'rejected' AND s.source = 'stripe' AND s.status IN ('active', 'past_due')", [$uid])->fetchColumn();
    } catch (Throwable $e) { /* billing tables not created yet */ }
    return [
        'clicks' => (int) cr_q($pdo, 'SELECT COUNT(*) FROM referral_clicks WHERE referrer_id = ?', [$uid])->fetchColumn(),
        'signups' => (int) cr_q($pdo, "SELECT COUNT(*) FROM referrals WHERE referrer_id = ? AND status <> 'rejected'", [$uid])->fetchColumn(),
        'paying' => $paying,
        'month_c' => (int) cr_q($pdo, 'SELECT COALESCE(SUM(commission_c), 0) FROM creator_ledger WHERE creator_id = ? AND month = ?', [$uid, $month])->fetchColumn(),
        'earned_c' => $earned, 'paid_c' => $paid, 'to_pay_c' => $earned - $paid, 'month' => $month,
    ];
}
/** The Creator section of the Referrals tab (only for creators). */
function cr_dashboard(PDO $pdo, string $uid): ?array
{
    $c = cr_get($pdo, $uid); if (!$c) return null;
    return ['code' => $c['code'], 'link' => cr_link((string) $c['code']), 'rate' => (int) $c['rate_bp'] / 100, 'months' => (int) $c['months'],
        'promo' => ['percent' => CR_PROMO_PERCENT, 'months' => CR_PROMO_MONTHS], 'currency' => 'usd'] + cr_totals($pdo, $uid);
}
/** Each month of one creator: payments, refunds, commission, paid or not. */
function cr_months(PDO $pdo, string $uid): array
{
    $out = [];
    foreach (cr_q($pdo, "SELECT month, SUM(CASE WHEN kind = 'payment' THEN amount_c ELSE 0 END) AS paid_c, SUM(CASE WHEN kind = 'refund' THEN amount_c ELSE 0 END) AS refunded_c,
        SUM(commission_c) AS commission_c, COUNT(*) AS n FROM creator_ledger WHERE creator_id = ? GROUP BY month ORDER BY month DESC", [$uid]) as $r) {
        $out[$r['month']] = ['month' => $r['month'], 'payments_c' => (int) $r['paid_c'], 'refunds_c' => (int) $r['refunded_c'], 'commission_c' => (int) $r['commission_c'], 'paid_at' => null, 'paid_c' => null];
    }
    foreach (cr_q($pdo, 'SELECT month, amount_c, paid_at FROM creator_payouts WHERE creator_id = ?', [$uid]) as $p) {
        $out[$p['month']] = $out[$p['month']] ?? ['month' => $p['month'], 'payments_c' => 0, 'refunds_c' => 0, 'commission_c' => 0];
        $out[$p['month']]['paid_at'] = (int) $p['paid_at']; $out[$p['month']]['paid_c'] = (int) $p['amount_c'];
    }
    krsort($out);
    return array_values($out);
}
/** Admin › Creators: every creator with the numbers the creator sees, and the months to pay. */
function cr_admin_list(PDO $pdo): array
{
    cr_schema($pdo);
    $items = [];
    foreach (cr_q($pdo, 'SELECT c.*, u.username, u.email FROM creators c LEFT JOIN users u ON u.id = c.uid ORDER BY c.created_at')->fetchAll(PDO::FETCH_ASSOC) as $c) {
        $items[] = ['uid' => $c['uid'], 'username' => $c['username'], 'email' => $c['email'], 'code' => $c['code'], 'link' => cr_link((string) $c['code']),
            'promo_id' => $c['promo_id'], 'since' => (int) $c['created_at'], 'months' => cr_months($pdo, (string) $c['uid'])] + cr_totals($pdo, (string) $c['uid']);
    }
    return ['items' => $items, 'month' => cr_month(cr_now()), 'rate' => CR_RATE_BP / 100, 'window' => CR_MONTHS];
}
/** Admin marks a finished month as paid to one creator (the money itself is sent by hand, outside Sweep). */
function cr_mark_paid(PDO $pdo, string $uid, string $month, string $by = ''): array
{
    cr_schema($pdo);
    if (!cr_get($pdo, $uid)) return ['error' => 'Not a creator.'];
    if (!preg_match('/^\d{4}-\d{2}$/', $month)) return ['error' => 'Bad month.'];
    if ($month >= cr_month(cr_now())) return ['error' => 'This month is not over yet.'];
    $amt = (int) cr_q($pdo, 'SELECT COALESCE(SUM(commission_c), 0) FROM creator_ledger WHERE creator_id = ? AND month = ?', [$uid, $month])->fetchColumn();
    try { cr_q($pdo, 'INSERT INTO creator_payouts (creator_id, month, amount_c, paid_at, paid_by) VALUES (?, ?, ?, ?, ?)', [$uid, $month, $amt, cr_now(), $by]); }
    catch (Throwable $e) { return ['error' => 'This month is already marked as paid.']; }
    return ['ok' => true, 'amount_c' => $amt];
}
/** The statement of one month for every creator: one line per payment or refund, then one total per creator (CSV rows). */
function cr_statement(PDO $pdo, string $month): array
{
    cr_schema($pdo);
    $rows = [['month', 'creator', 'creator_email', 'code', 'trader', 'type', 'date_utc', 'invoice', 'amount', 'commission', 'currency', 'status']];
    $tot = [];
    foreach (cr_q($pdo, 'SELECT l.*, c.code, a.username AS creator, a.email AS creator_email, b.username AS trader FROM creator_ledger l JOIN creators c ON c.uid = l.creator_id
        LEFT JOIN users a ON a.id = l.creator_id LEFT JOIN users b ON b.id = l.referee_id WHERE l.month = ? ORDER BY a.username, l.at, l.id', [$month]) as $r) {
        $rows[] = [$month, (string) $r['creator'], (string) $r['creator_email'], (string) $r['code'], (string) ($r['trader'] ?? 'deleted'), (string) $r['kind'], gmdate('Y-m-d H:i', (int) $r['at']),
            (string) $r['invoice_id'], number_format((int) $r['amount_c'] / 100, 2, '.', ''), number_format((int) $r['commission_c'] / 100, 2, '.', ''), strtoupper((string) $r['currency']), ''];
        $t = &$tot[(string) $r['creator_id']];
        if (!$t) $t = ['creator' => (string) $r['creator'], 'email' => (string) $r['creator_email'], 'code' => (string) $r['code'], 'amount' => 0, 'commission' => 0, 'currency' => strtoupper((string) $r['currency'])];
        $t['amount'] += (int) $r['amount_c']; $t['commission'] += (int) $r['commission_c'];
        unset($t);
    }
    foreach ($tot as $cid => $t) {
        $p = cr_q($pdo, 'SELECT paid_at FROM creator_payouts WHERE creator_id = ? AND month = ?', [$cid, $month])->fetchColumn();
        $rows[] = [$month, $t['creator'], $t['email'], $t['code'], '', 'total', '', '', number_format($t['amount'] / 100, 2, '.', ''), number_format($t['commission'] / 100, 2, '.', ''), $t['currency'],
            $p ? 'paid ' . gmdate('Y-m-d', (int) $p) : 'to pay'];
    }
    return $rows;
}
/** Account deleted: a creator's own rows go; a trader a creator brought stays in the ledger without his id (the money was real). */
function cr_delete_user(PDO $pdo, string $uid): void
{
    cr_schema($pdo);
    foreach (['DELETE FROM creators WHERE uid = ?', 'DELETE FROM creator_payouts WHERE creator_id = ?', 'DELETE FROM creator_ledger WHERE creator_id = ?',
              'DELETE FROM creator_refs WHERE referee_id = ? OR creator_id = ?'] as $sql) cr_q($pdo, $sql, substr_count($sql, '?') === 2 ? [$uid, $uid] : [$uid]);
    cr_q($pdo, "UPDATE creator_ledger SET referee_id = 'deleted' WHERE referee_id = ?", [$uid]);
}
