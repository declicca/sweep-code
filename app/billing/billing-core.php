<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli' && realpath((string) ($_SERVER['SCRIPT_FILENAME'] ?? '')) === realpath(__FILE__)) { http_response_code(404); exit; }
/**
 * Sweep billing: core.
 *
 * One rule for the whole app: never check a plan name. Ask this module instead.
 *   sb_can($pdo, $uid, 'payouts')        → bool
 *   sb_limit($pdo, $uid, 'ai_daily')     → int|null (null = unlimited)
 *   sb_state($pdo, $uid)                 → everything the UI needs
 *   sb_guard($pdo, $uid, $action, $ctx)  → null (allowed) or an "upgrade_required" error
 *
 * Effective plan = best of: comp access › paid subscription › trial / early-access grant › free.
 * Downgrades never delete anything: extra accounts are frozen (read-only), locked data stays stored.
 */

const SB_RANK = ['free' => 0, 'pro' => 1, 'elite' => 2];
const SB_DAY  = 86400;

/* ───────────────────────────── config ───────────────────────────── */

function sb_config(): array
{
    static $cfg = null;
    if ($cfg !== null) return $cfg;
    $candidates = [];
    if (defined('SWEEP_BILLING_CONFIG')) $candidates[] = SWEEP_BILLING_CONFIG;
    $candidates[] = dirname(__DIR__, 2) . '/sweep-private/billing-config.php';   // /home/USER/<app>/billing → /home/USER/sweep-private
    $candidates[] = dirname(__DIR__, 3) . '/sweep-private/billing-config.php';   // one level deeper, just in case
    foreach ($candidates as $p) {
        if (is_file($p)) { $cfg = (array) require $p; break; }
    }
    if ($cfg === null) throw new RuntimeException('Billing config file not found (sweep-private/billing-config.php)');
    $cfg += [
        'live' => false, 'prelaunch_plan' => 'elite', 'launch_at' => '2100-01-01T00:00:00Z',
        'founding_deadline' => '2000-01-01T00:00:00Z', 'early_access_grant' => ['plan' => 'pro', 'days' => 30],
        'trial' => ['plan' => 'pro', 'days' => 14],
        // campaign bonus on top of the trial, by utm_campaign (normalised: lowercase, letters and digits only)
        'campaign_grants' => ['100' => ['plan' => 'elite', 'days' => 30], '100traders' => ['plan' => 'elite', 'days' => 30], '100futurestraders' => ['plan' => 'elite', 'days' => 30],
                              'lookingfor100' => ['plan' => 'elite', 'days' => 30], 'lookingfor100futurestraders' => ['plan' => 'elite', 'days' => 30], 'founding100' => ['plan' => 'elite', 'days' => 30]], 'founding_for' => 'early_access', 'past_due_grace_days' => 7,
        'ai_reviews_fair_use_monthly' => 200, 'paywall_max_blocking_per_week' => 3, 'currency' => 'USD',
        'display_prices' => [], 'founding_percent_off' => 50, 'stripe_prices' => [], 'stripe_founding_coupon' => '',
        'stripe_automatic_tax' => false, 'app_url' => '/', 'comp_users' => [],
    ];
    return $cfg;
}

/** Tests only. */
function sb_set_config(array $cfg): void
{
    $GLOBALS['SB_CONFIG_OVERRIDE'] = $cfg;
}

function sb_cfg(): array
{
    return $GLOBALS['SB_CONFIG_OVERRIDE'] ?? sb_config();
}

/** Billing is live for everyone when 'live' is true, or only for the ids listed in 'test_users' (test before launch without locking anyone else). */
function sb_live(string $uid = ''): bool
{
    $cfg = sb_cfg();
    if (!empty($cfg['live'])) return true;
    return $uid !== '' && in_array($uid, array_map('strval', (array) ($cfg['test_users'] ?? [])), true);
}

function sb_now(): int
{
    return isset($GLOBALS['SB_NOW']) ? (int) $GLOBALS['SB_NOW'] : time();
}

function sb_ts($v): ?int
{
    if ($v === null || $v === '') return null;
    if (is_int($v) || (is_string($v) && ctype_digit($v))) {
        $n = (int) $v;
        return $n > 100000000000 ? intdiv($n, 1000) : $n;   // accept milliseconds too
    }
    $t = strtotime((string) $v);
    return $t === false ? null : $t;
}

function sb_plan_limits(string $plan): array
{
    $plans = sb_cfg()['plans'] ?? [];
    return (array) ($plans[$plan] ?? $plans['free'] ?? []);
}

/* ───────────────────────────── schema ───────────────────────────── */

function sb_schema(PDO $pdo): void
{
    static $done = false;
    if ($done) return;
    $mysql = $pdo->getAttribute(PDO::ATTR_DRIVER_NAME) === 'mysql';
    $auto  = $mysql ? 'INTEGER PRIMARY KEY AUTO_INCREMENT' : 'INTEGER PRIMARY KEY AUTOINCREMENT';
    $key   = $mysql ? 'VARCHAR(191)' : 'TEXT';
    $pdo->exec("CREATE TABLE IF NOT EXISTS billing_users (
        uid $key PRIMARY KEY, created_at INTEGER, first_seen INTEGER, stripe_customer $key NULL,
        active_accounts TEXT NULL, email TEXT NULL)");
    $pdo->exec("CREATE TABLE IF NOT EXISTS billing_subs (
        id $key PRIMARY KEY, uid $key NOT NULL, source VARCHAR(16) NOT NULL, plan VARCHAR(16) NOT NULL,
        billing_interval VARCHAR(8) NULL, status VARCHAR(24) NOT NULL, founding INTEGER DEFAULT 0, price_id TEXT NULL,
        period_end INTEGER NULL, cancel_at_period_end INTEGER DEFAULT 0, past_due_since INTEGER NULL, updated_at INTEGER NOT NULL)");
    $pdo->exec("CREATE TABLE IF NOT EXISTS billing_grants (
        id $auto, uid $key NOT NULL, plan VARCHAR(16) NOT NULL, starts_at INTEGER NOT NULL, ends_at INTEGER NOT NULL,
        reason VARCHAR(24) NOT NULL, created_at INTEGER NOT NULL)");
    $pdo->exec("CREATE TABLE IF NOT EXISTS billing_usage (
        uid $key NOT NULL, metric VARCHAR(32) NOT NULL, period VARCHAR(10) NOT NULL, count INTEGER NOT NULL DEFAULT 0,
        PRIMARY KEY (uid, metric, period))");
    $pdo->exec("CREATE TABLE IF NOT EXISTS billing_upsell (
        id $auto, uid $key NOT NULL, trig VARCHAR(48) NOT NULL, action VARCHAR(16) NOT NULL, blocking INTEGER DEFAULT 0,
        plan VARCHAR(16) NULL, at INTEGER NOT NULL)");
    $pdo->exec("CREATE TABLE IF NOT EXISTS billing_webhooks (
        event_id $key PRIMARY KEY, type VARCHAR(64) NOT NULL, at INTEGER NOT NULL)");
    foreach (['CREATE INDEX IF NOT EXISTS billing_subs_uid ON billing_subs (uid)',
              'CREATE INDEX IF NOT EXISTS billing_grants_uid ON billing_grants (uid)',
              'CREATE INDEX IF NOT EXISTS billing_upsell_uid ON billing_upsell (uid, at)'] as $sql) {
        try { $pdo->exec($mysql ? str_replace('IF NOT EXISTS ', '', $sql) : $sql); } catch (Throwable $e) { /* index exists */ }
    }
    $done = true;
}

function sb_q(PDO $pdo, string $sql, array $args = []): PDOStatement
{
    $st = $pdo->prepare($sql);
    $st->execute($args);
    return $st;
}

/* ───────────────────────────── users & grants ───────────────────────────── */

/**
 * Registers the user on first contact and gives the right starting access:
 *   created before launch → early-access grant (free Pro for N days from launch day)
 *   created after launch  → reverse trial (free Pro for N days from signup)
 */
function sb_user(PDO $pdo, string $uid, $createdAt = null, ?string $email = null): array
{
    sb_schema($pdo);
    $row = sb_q($pdo, 'SELECT * FROM billing_users WHERE uid = ?', [$uid])->fetch(PDO::FETCH_ASSOC);
    $now = sb_now();
    $created = sb_ts($createdAt);
    if (!$row) {
        $c = $created ?? $now;
        sb_q($pdo, 'INSERT INTO billing_users (uid, created_at, first_seen, email) VALUES (?, ?, ?, ?)', [$uid, $c, $now, $email]);
        $row = ['uid' => $uid, 'created_at' => $c, 'first_seen' => $now, 'stripe_customer' => null, 'active_accounts' => null, 'email' => $email];
    } else {
        if ($created !== null && (int) $row['created_at'] !== $created) {
            sb_q($pdo, 'UPDATE billing_users SET created_at = ? WHERE uid = ?', [$created, $uid]);
            $row['created_at'] = $created;
        }
        if ($email && $email !== ($row['email'] ?? null)) {
            sb_q($pdo, 'UPDATE billing_users SET email = ? WHERE uid = ?', [$email, $uid]);
            $row['email'] = $email;
        }
    }
    sb_ensure_starting_grant($pdo, $uid, (int) $row['created_at']);
    return $row;
}

function sb_is_early_access(int $createdAt): bool
{
    return $createdAt < (int) sb_ts(sb_cfg()['launch_at']);
}

function sb_ensure_starting_grant(PDO $pdo, string $uid, int $createdAt): void
{
    $cfg = sb_cfg();
    if (!sb_live($uid)) return;                       // nothing is granted before launch: everyone has prelaunch access
    $has = sb_q($pdo, "SELECT 1 FROM billing_grants WHERE uid = ? AND reason IN ('trial','early_access') LIMIT 1", [$uid])->fetchColumn();
    if ($has) return;
    $launch = (int) sb_ts($cfg['launch_at']);
    if (sb_is_early_access($createdAt)) {
        $g = $cfg['early_access_grant'];
        $start = $launch;
        $reason = 'early_access';
    } else {
        $g = $cfg['trial'];
        $start = max($createdAt, $launch);
        $reason = 'trial';
    }
    if (empty($g['days']) || empty($g['plan'])) return;
    sb_q($pdo, 'INSERT INTO billing_grants (uid, plan, starts_at, ends_at, reason, created_at) VALUES (?, ?, ?, ?, ?, ?)',
        [$uid, (string) $g['plan'], $start, $start + (int) $g['days'] * SB_DAY, $reason, sb_now()]);
    sb_campaign_grant($pdo, $uid, $start);
}

/** Campaign recruits (e.g. the « 100 futures traders » cohort) get a bonus on top of everyone's trial, once. */
function sb_campaign_grant(PDO $pdo, string $uid, int $start): void
{
    try {
        $camp = strtolower(preg_replace('/[^a-z0-9]/i', '', (string) sb_q($pdo, 'SELECT utm_campaign FROM users WHERE id = ?', [$uid])->fetchColumn()));
        $g = (sb_cfg()['campaign_grants'] ?? [])[$camp] ?? null;
        if (!$g || empty($g['plan']) || empty($g['days'])) return;
        if (sb_q($pdo, "SELECT 1 FROM billing_grants WHERE uid = ? AND reason = 'campaign' LIMIT 1", [$uid])->fetchColumn()) return;
        sb_q($pdo, 'INSERT INTO billing_grants (uid, plan, starts_at, ends_at, reason, created_at) VALUES (?, ?, ?, ?, ?, ?)',
            [$uid, (string) $g['plan'], $start, $start + (int) $g['days'] * SB_DAY, 'campaign', sb_now()]);
    } catch (Throwable $e) { error_log('[Sweep billing] campaign grant: ' . $e->getMessage()); }
}

/** Give someone access manually (support gesture, contest prize, partner…). */
function sb_grant(PDO $pdo, string $uid, string $plan, int $days, string $reason = 'comp'): void
{
    sb_schema($pdo);
    $now = sb_now();
    sb_q($pdo, 'INSERT INTO billing_grants (uid, plan, starts_at, ends_at, reason, created_at) VALUES (?, ?, ?, ?, ?, ?)',
        [$uid, $plan, $now, $now + $days * SB_DAY, $reason, $now]);
}

/* ───────────────────────────── effective plan ───────────────────────────── */

function sb_active_sub(PDO $pdo, string $uid): ?array
{
    $cfg = sb_cfg();
    $now = sb_now();
    $best = null;
    foreach (sb_q($pdo, 'SELECT * FROM billing_subs WHERE uid = ?', [$uid])->fetchAll(PDO::FETCH_ASSOC) as $s) {
        $ok = in_array($s['status'], ['active', 'trialing'], true)
            || ($s['status'] === 'past_due' && $s['past_due_since'] !== null
                && $now < (int) $s['past_due_since'] + (int) $cfg['past_due_grace_days'] * SB_DAY);
        if (!$ok) continue;
        if ($best === null || SB_RANK[$s['plan']] > SB_RANK[$best['plan']]) $best = $s;
    }
    return $best;
}

function sb_active_grant(PDO $pdo, string $uid): ?array
{
    $now = sb_now();
    $best = null;
    foreach (sb_q($pdo, 'SELECT * FROM billing_grants WHERE uid = ? AND starts_at <= ? AND ends_at > ?', [$uid, $now, $now])->fetchAll(PDO::FETCH_ASSOC) as $g) {
        if (!isset(SB_RANK[$g['plan']])) continue;
        if ($best === null || SB_RANK[$g['plan']] > SB_RANK[$best['plan']]
            || (SB_RANK[$g['plan']] === SB_RANK[$best['plan']] && $g['ends_at'] > $best['ends_at'])) $best = $g;
    }
    return $best;
}

/** ['plan' => free|pro|elite, 'source' => prelaunch|comp|subscription|early_access|trial|comp_grant|free, 'sub' => ?, 'grant' => ?] */
function sb_effective(PDO $pdo, string $uid): array
{
    $cfg = sb_cfg();
    if (!sb_live($uid)) return ['plan' => (string) $cfg['prelaunch_plan'], 'source' => 'prelaunch', 'sub' => null, 'grant' => null];
    $comp = $cfg['comp_users'][$uid] ?? null;
    if ($comp && isset(SB_RANK[$comp])) return ['plan' => $comp, 'source' => 'comp', 'sub' => null, 'grant' => null];

    $sub = sb_active_sub($pdo, $uid);
    $grant = sb_active_grant($pdo, $uid);
    $plan = 'free'; $source = 'free';
    if ($grant) { $plan = $grant['plan']; $source = $grant['reason'] === 'comp' ? 'comp_grant' : $grant['reason']; }
    if ($sub && SB_RANK[$sub['plan']] >= SB_RANK[$plan]) { $plan = $sub['plan']; $source = 'subscription'; }
    return ['plan' => $plan, 'source' => $source, 'sub' => $sub, 'grant' => $grant];
}

function sb_plan(PDO $pdo, string $uid): string
{
    sb_schema($pdo);
    return sb_effective($pdo, $uid)['plan'];
}

function sb_limit(PDO $pdo, string $uid, string $key)
{
    return sb_plan_limits(sb_plan($pdo, $uid))[$key] ?? null;
}

function sb_can(PDO $pdo, string $uid, string $feature): bool
{
    $v = sb_limit($pdo, $uid, $feature);
    if (is_bool($v)) return $v;
    if ($v === null) return true;
    if (is_int($v)) return $v > 0;
    return $v === 'full';
}

/** Cheapest plan that unlocks a feature (for the paywall). */
function sb_plan_for(string $feature): string
{
    foreach (['pro', 'elite'] as $p) {
        $v = sb_plan_limits($p)[$feature] ?? null;
        if ($v === true || $v === null || $v === 'full' || (is_int($v) && $v > (sb_plan_limits('free')[$feature] ?? 0))) return $p;
    }
    return 'elite';
}

/* ───────────────────────────── founding ───────────────────────────── */

function sb_founding(PDO $pdo, string $uid, array $user, array $eff): array
{
    $cfg = sb_cfg();
    $deadline = (int) sb_ts($cfg['founding_deadline']);
    $locked = $eff['sub'] && (int) $eff['sub']['founding'] === 1;
    $who = $cfg['founding_for'] === 'everyone' || sb_is_early_access((int) $user['created_at']);
    $paid = $eff['sub'] !== null;
    return [
        // nothing to buy for a comped account (admin, partner) or a permanent Elite: no founding banner then
        'eligible' => sb_live($uid) && $who && !$paid && sb_now() < $deadline && !empty($cfg['stripe_founding_coupon'])
            && !in_array($eff['source'] ?? '', ['comp', 'comp_grant'], true) && !(($eff['plan'] ?? '') === 'elite' && empty($eff['grant'])),
        'locked'   => $locked,
        'deadline' => gmdate('c', $deadline),
        'percent'  => (int) $cfg['founding_percent_off'],
    ];
}

/* ───────────────────────────── usage & quotas ───────────────────────────── */

function sb_period(string $metric): string
{
    return $metric === 'ai_reviews' ? gmdate('Y-m', sb_now()) : gmdate('Y-m-d', sb_now());
}

function sb_usage(PDO $pdo, string $uid, string $metric): int
{
    sb_schema($pdo);
    return (int) (sb_q($pdo, 'SELECT count FROM billing_usage WHERE uid = ? AND metric = ? AND period = ?', [$uid, $metric, sb_period($metric)])->fetchColumn() ?: 0);
}

function sb_usage_inc(PDO $pdo, string $uid, string $metric, int $by = 1): void
{
    $p = sb_period($metric);
    $st = sb_q($pdo, 'UPDATE billing_usage SET count = count + ? WHERE uid = ? AND metric = ? AND period = ?', [$by, $uid, $metric, $p]);
    if ($st->rowCount() === 0) {
        try { sb_q($pdo, 'INSERT INTO billing_usage (uid, metric, period, count) VALUES (?, ?, ?, ?)', [$uid, $metric, $p, $by]); }
        catch (Throwable $e) { sb_q($pdo, 'UPDATE billing_usage SET count = count + ? WHERE uid = ? AND metric = ? AND period = ?', [$by, $uid, $metric, $p]); }
    }
}

function sb_reset_at(string $metric): string
{
    $n = sb_now();
    $t = $metric === 'ai_reviews' ? gmmktime(0, 0, 0, (int) gmdate('n', $n) + 1, 1, (int) gmdate('Y', $n)) : gmmktime(0, 0, 0, (int) gmdate('n', $n), (int) gmdate('j', $n) + 1, (int) gmdate('Y', $n));
    return gmdate('c', $t);
}

/**
 * Call this BEFORE every AI call. $kind: 'review' (AI trade review), 'import' (AI import), anything else = daily AI quota.
 * On success the use is counted. On failure nothing is counted.
 * Returns ['ok' => true, ...] or ['ok' => false, 'code' => 'upgrade_required'|'quota', 'feature', 'used', 'limit', 'reset_at', 'upgrade_to'].
 */
function sb_ai_consume(PDO $pdo, string $uid, string $kind = 'chat', bool $count = true): array
{
    sb_schema($pdo);
    $plan = sb_plan($pdo, $uid);
    $L = sb_plan_limits($plan);
    if ($kind === 'import' && empty($L['ai_import'])) {
        return ['ok' => false, 'code' => 'upgrade_required', 'feature' => 'ai_import', 'plan' => $plan, 'upgrade_to' => sb_plan_for('ai_import')];
    }
    $metric = $kind === 'review' ? 'ai_reviews' : 'ai_daily';
    $limit = $L[$metric] ?? null;
    if ($metric === 'ai_reviews' && $limit === null) $limit = (int) sb_cfg()['ai_reviews_fair_use_monthly'];
    $used = sb_usage($pdo, $uid, $metric);
    if ($limit !== null && $used >= (int) $limit) {
        $next = $plan === 'elite' ? null : ($plan === 'pro' ? 'elite' : 'pro');
        return ['ok' => false, 'code' => $next ? 'upgrade_required' : 'quota', 'feature' => $metric, 'plan' => $plan,
                'used' => $used, 'limit' => (int) $limit, 'reset_at' => sb_reset_at($metric), 'upgrade_to' => $next];
    }
    if ($count) sb_usage_inc($pdo, $uid, $metric);
    return ['ok' => true, 'plan' => $plan, 'feature' => $metric, 'used' => $used + ($count ? 1 : 0), 'limit' => $limit === null ? null : (int) $limit];
}

/** Give a use back when the AI call itself failed (so users don't pay quota for errors). */
function sb_ai_refund(PDO $pdo, string $uid, string $kind = 'chat'): void
{
    $metric = $kind === 'review' ? 'ai_reviews' : 'ai_daily';
    sb_q($pdo, 'UPDATE billing_usage SET count = CASE WHEN count > 0 THEN count - 1 ELSE 0 END WHERE uid = ? AND metric = ? AND period = ?', [$uid, $metric, sb_period($metric)]);
}

/* ───────────────────────────── accounts (freeze, never delete) ───────────────────────────── */

/**
 * $accountIds: ALL the user's trading account ids, oldest first.
 * Returns ['limit' => ?int, 'active' => [...], 'frozen' => [...], 'needs_choice' => bool]
 */
function sb_accounts(PDO $pdo, string $uid, array $accountIds): array
{
    $accountIds = array_values(array_map('strval', $accountIds));
    $limit = sb_limit($pdo, $uid, 'accounts');
    if ($limit === null || count($accountIds) <= $limit) {
        return ['limit' => $limit, 'active' => $accountIds, 'frozen' => [], 'needs_choice' => false];
    }
    $saved = json_decode((string) (sb_q($pdo, 'SELECT active_accounts FROM billing_users WHERE uid = ?', [$uid])->fetchColumn() ?: '[]'), true) ?: [];
    $active = array_values(array_intersect(array_map('strval', $saved), $accountIds));
    $chosen = count($active) > 0;
    foreach ($accountIds as $id) {                   // fill up to the limit, oldest first
        if (count($active) >= $limit) break;
        if (!in_array($id, $active, true)) $active[] = $id;
    }
    $active = array_slice($active, 0, (int) $limit);
    return ['limit' => (int) $limit, 'active' => $active, 'frozen' => array_values(array_diff($accountIds, $active)), 'needs_choice' => !$chosen];
}

function sb_set_active_accounts(PDO $pdo, string $uid, array $ids, array $allIds): array
{
    $ids = array_values(array_intersect(array_map('strval', $ids), array_map('strval', $allIds)));
    $limit = sb_limit($pdo, $uid, 'accounts');
    if ($limit !== null) $ids = array_slice($ids, 0, (int) $limit);
    // upsert: the choice must stick even if the billing row was not created yet
    if (!sb_q($pdo, 'SELECT 1 FROM billing_users WHERE uid = ?', [$uid])->fetchColumn()) sb_q($pdo, 'INSERT INTO billing_users (uid, created_at, first_seen) VALUES (?, ?, ?)', [$uid, sb_now(), sb_now()]);
    sb_q($pdo, 'UPDATE billing_users SET active_accounts = ? WHERE uid = ?', [json_encode($ids), $uid]);
    return sb_accounts($pdo, $uid, $allIds);
}

/* ───────────────────────────── write guard ───────────────────────────── */

/**
 * Call before saving. Returns null when allowed, otherwise an error to send back with HTTP 402.
 *   'create_account' ctx: ['account_ids' => [...existing ids]]
 *   'write_trade'    ctx: ['account_id' => id, 'account_ids' => [...all ids]]   (trades, journals tied to an account)
 *   'write_payouts'  ctx: []                                                    (payouts and expenses)
 * Deleting is always allowed: it's the user's data.
 */
function sb_guard(PDO $pdo, string $uid, string $action, array $ctx = []): ?array
{
    sb_schema($pdo);
    if (!sb_live($uid)) return null;
    $plan = sb_plan($pdo, $uid);
    $err = fn(string $feature, string $trigger) => [
        'error' => 'upgrade_required', 'code' => 'upgrade_required', 'feature' => $feature,
        'trigger' => $trigger, 'plan' => $plan, 'upgrade_to' => sb_plan_for($feature),
    ];
    switch ($action) {
        case 'create_account':
            $limit = sb_plan_limits($plan)['accounts'] ?? null;
            if ($limit !== null && count($ctx['account_ids'] ?? []) >= $limit) return $err('accounts', 'add_account');
            return null;
        case 'write_trade':
            $id = (string) ($ctx['account_id'] ?? '');
            if ($id === '') return null;
            $acc = sb_accounts($pdo, $uid, (array) ($ctx['account_ids'] ?? []));
            if (in_array($id, $acc['frozen'], true)) return $err('accounts', 'frozen_account');
            return null;
        case 'write_payouts':
            return sb_can($pdo, $uid, 'payouts') ? null : $err('payouts', 'payouts');
    }
    return null;
}

/* ───────────────────────────── paywall pacing & analytics ───────────────────────────── */

function sb_paywall_left(PDO $pdo, string $uid): int
{
    $n = (int) sb_q($pdo, "SELECT COUNT(*) FROM billing_upsell WHERE uid = ? AND action = 'shown' AND blocking = 1 AND at > ?", [$uid, sb_now() - 7 * SB_DAY])->fetchColumn();
    return max(0, (int) sb_cfg()['paywall_max_blocking_per_week'] - $n);
}

function sb_log_upsell(PDO $pdo, string $uid, string $trigger, string $action, bool $blocking): void
{
    $action = in_array($action, ['shown', 'dismissed', 'clicked', 'checkout', 'converted'], true) ? $action : 'shown';
    $trigger = substr(preg_replace('/[^a-z0-9_:-]/i', '', $trigger) ?: 'unknown', 0, 48);
    sb_q($pdo, 'INSERT INTO billing_upsell (uid, trig, action, blocking, plan, at) VALUES (?, ?, ?, ?, ?, ?)',
        [$uid, $trigger, $action, $blocking ? 1 : 0, sb_plan($pdo, $uid), sb_now()]);
}

/** Conversion by trigger over the last N days: which paywall moments actually sell. */
function sb_funnel(PDO $pdo, int $days = 30): array
{
    sb_schema($pdo);
    $rows = sb_q($pdo, 'SELECT trig, action, COUNT(*) n FROM billing_upsell WHERE at > ? GROUP BY trig, action', [sb_now() - $days * SB_DAY])->fetchAll(PDO::FETCH_ASSOC);
    $out = [];
    foreach ($rows as $r) $out[$r['trig']][$r['action']] = (int) $r['n'];
    foreach ($out as $t => $a) {
        $shown = $a['shown'] ?? 0;
        $out[$t]['conversion_pct'] = $shown ? round(100 * ($a['converted'] ?? 0) / $shown, 1) : null;
    }
    return $out;
}

/* ───────────────────────────── full state for the UI ───────────────────────────── */

function sb_state(PDO $pdo, string $uid, array $user = []): array
{
    $cfg = sb_cfg();
    $u = sb_user($pdo, $uid, $user['created_at'] ?? null, $user['email'] ?? null);
    $eff = sb_effective($pdo, $uid);
    $plan = $eff['plan'];
    $L = sb_plan_limits($plan);
    $now = sb_now();

    $trial = null;
    if ($eff['grant'] && in_array($eff['source'], ['trial', 'early_access', 'comp_grant'], true)) {
        $ends = (int) $eff['grant']['ends_at'];
        $trial = ['kind' => $eff['source'], 'plan' => $eff['grant']['plan'], 'ends_at' => gmdate('c', $ends), 'days_left' => (int) ceil(($ends - $now) / SB_DAY)];
    }
    $sub = null;
    if ($eff['sub']) {
        $s = $eff['sub'];
        $sub = ['plan' => $s['plan'], 'interval' => $s['billing_interval'], 'status' => $s['status'], 'founding' => (bool) $s['founding'],
                'cancel_at_period_end' => (bool) $s['cancel_at_period_end'], 'period_end' => $s['period_end'] ? gmdate('c', (int) $s['period_end']) : null,
                'grace_ends' => $s['status'] === 'past_due' ? gmdate('c', (int) $s['past_due_since'] + (int) $cfg['past_due_grace_days'] * SB_DAY) : null];
    }
    // last trial that already ended, for the "your trial ended" moment
    $ended = sb_q($pdo, "SELECT plan, ends_at, reason FROM billing_grants WHERE uid = ? AND reason IN ('trial','early_access') AND ends_at <= ? ORDER BY ends_at DESC LIMIT 1", [$uid, $now])->fetch(PDO::FETCH_ASSOC);

    $founding = sb_founding($pdo, $uid, $u, $eff);
    $prices = [];
    foreach ((array) $cfg['display_prices'] as $p => $iv) {
        foreach ((array) $iv as $i => $amount) {
            $prices[$p][$i] = ['amount' => (float) $amount,
                'founding' => $founding['eligible'] ? round($amount * (100 - $founding['percent']) / 100, 2) : null];
        }
    }
    $accounts = isset($user['account_ids']) ? sb_accounts($pdo, $uid, (array) $user['account_ids']) : null;

    $reviewLimit = $L['ai_reviews'] ?? null;
    return [
        'live'      => sb_live($uid),
        'plan'      => $plan,
        'source'    => $eff['source'],
        'limits'    => $L,
        'plans'     => $cfg['plans'],
        'usage'     => [
            'ai_daily'   => ['used' => sb_usage($pdo, $uid, 'ai_daily'), 'limit' => $L['ai_daily'] ?? null, 'reset_at' => sb_reset_at('ai_daily')],
            'ai_reviews' => ['used' => sb_usage($pdo, $uid, 'ai_reviews'), 'limit' => $reviewLimit, 'reset_at' => sb_reset_at('ai_reviews')],
        ],
        'trial'        => $trial,
        'trial_ended'  => (!$trial && !$sub && $ended && $plan === 'free') ? ['plan' => $ended['plan'], 'ended_at' => gmdate('c', (int) $ended['ends_at']), 'kind' => $ended['reason']] : null,
        'subscription' => $sub,
        'founding'     => $founding,
        'early_access' => sb_is_early_access((int) $u['created_at']),
        'launch_at'    => gmdate('c', (int) sb_ts($cfg['launch_at'])),
        'prices'       => $prices,
        'currency'     => $cfg['currency'],
        'accounts'     => $accounts,
        'paywall'      => ['blocking_left' => sb_live($uid) ? sb_paywall_left($pdo, $uid) : 0],
        'can_manage'   => !empty($u['stripe_customer']),
    ];
}
