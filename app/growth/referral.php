<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli' && realpath((string) ($_SERVER['SCRIPT_FILENAME'] ?? '')) === realpath(__FILE__)) { http_response_code(404); exit; }
/**
 * Sweep — referral program (ported from the referral module to Sweep's database, sessions and billing).
 *
 * Rules: the friend gets REF_REFEREE_DAYS of Elite (REF_REFEREE_PLAN) at sign-up, on top of the trial everyone gets. The referrer earns a month when the friend,
 * within REF_WINDOW_DAYS, logs REF_TRADES trades on REF_DAYS different days, or pays a first invoice.
 * Paying referrer → credit on the Stripe customer balance (1 month of their plan). Otherwise → 30 days of Pro.
 * Max REF_MAX_YEAR rewards per rolling 12 months. Same IP as the referrer → 'review' (no bonus for the friend).
 * IPs are stored hashed. Codes: first letters of the username + 3 random characters (e.g. MATEOK7Q).
 */
const REF_REFEREE_DAYS = 14, REF_REFEREE_PLAN = 'elite', REF_REWARD_DAYS = 30, REF_BONUS_PLAN = 'pro';   // the friend: 14 days of Elite on top of everyone's Pro trial
const REF_TRADES = 10, REF_DAYS = 3, REF_WINDOW_DAYS = 30, REF_MAX_YEAR = 12, REF_MAX_IP_DAY = 3;
const REF_COOKIE = 'sweep_ref', REF_COOKIE_DAYS = 60;
const REF_ALPHABET = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';

/* multibyte-safe helpers that also work on hosts without the mbstring extension */
function g_sub(string $s, int $start, ?int $len = null): string { return function_exists('mb_substr') ? mb_substr($s, $start, $len) : (preg_match_all('/./us', $s, $m) ? implode('', array_slice($m[0], $start, $len)) : substr($s, $start, $len ?? strlen($s))); }
function g_len(string $s): int { return function_exists('mb_strlen') ? mb_strlen($s) : (int) preg_match_all('/./us', $s); }
function g_upper(string $s): string { return function_exists('mb_strtoupper') ? mb_strtoupper($s) : strtoupper($s); }

function ref_schema(PDO $pdo): void
{
    static $done = false; if ($done) return; $done = true;
    $my = $pdo->getAttribute(PDO::ATTR_DRIVER_NAME) === 'mysql';
    $id = $my ? 'INT UNSIGNED AUTO_INCREMENT PRIMARY KEY' : 'INTEGER PRIMARY KEY AUTOINCREMENT';
    $k = $my ? 'VARCHAR(64)' : 'TEXT'; $tail = $my ? ' DEFAULT CHARSET=utf8mb4' : '';
    $pdo->exec("CREATE TABLE IF NOT EXISTS ref_users (uid $k NOT NULL PRIMARY KEY, code $k NULL, referred_by $k NULL, signup_ip_hash $k NULL)$tail");
    try { $pdo->exec('CREATE UNIQUE INDEX ref_users_code ON ref_users(code)'); } catch (Throwable $e) {}
    $pdo->exec("CREATE TABLE IF NOT EXISTS referrals (id $id, referrer_id $k NOT NULL, referee_id $k NOT NULL, status $k NOT NULL, qualify_reason $k NULL,
        reward_type $k NULL, reward_value INTEGER NULL, ip_hash $k NULL, created_at INTEGER NOT NULL, qualified_at INTEGER NULL, rewarded_at INTEGER NULL)$tail");
    try { $pdo->exec('CREATE UNIQUE INDEX referrals_referee ON referrals(referee_id)'); } catch (Throwable $e) {}
    $pdo->exec("CREATE TABLE IF NOT EXISTS referral_clicks (id $id, referrer_id $k NOT NULL, ip_hash $k NULL, created_at INTEGER NOT NULL)$tail");
}
function ref_q(PDO $pdo, string $sql, array $a = []): PDOStatement { $st = $pdo->prepare($sql); $st->execute($a); return $st; }
function ref_salt(): string { global $cfg; return (string) ($cfg['referral_salt'] ?? ($cfg['password'] ?? 'sweep')) . '|ref'; }
function ref_ip_hash(): string { return hash('sha256', (string) ($_SERVER['HTTP_CF_CONNECTING_IP'] ?? $_SERVER['REMOTE_ADDR'] ?? '') . ref_salt()); }
function ref_row(PDO $pdo, string $uid): array
{
    ref_schema($pdo);
    $r = ref_q($pdo, 'SELECT * FROM ref_users WHERE uid = ?', [$uid])->fetch(PDO::FETCH_ASSOC);
    if ($r) return $r;
    ref_q($pdo, 'INSERT INTO ref_users (uid) VALUES (?)', [$uid]);
    return ['uid' => $uid, 'code' => null, 'referred_by' => null, 'signup_ip_hash' => null];
}
function ref_username(PDO $pdo, string $uid): string { return (string) (ref_q($pdo, 'SELECT username FROM users WHERE id = ?', [$uid])->fetchColumn() ?: ''); }
function ref_find_by_code(PDO $pdo, string $code): ?array
{
    ref_schema($pdo);
    $code = strtoupper(preg_replace('/[^A-Za-z0-9]/', '', $code));
    if ($code === '' || strlen($code) > 16) return null;
    $r = ref_q($pdo, 'SELECT * FROM ref_users WHERE code = ?', [$code])->fetch(PDO::FETCH_ASSOC);
    return $r ?: null;
}
function ref_get_code(PDO $pdo, string $uid): string
{
    $r = ref_row($pdo, $uid);
    if (!empty($r['code'])) return (string) $r['code'];
    $base = ref_username($pdo, $uid);
    if (function_exists('iconv')) $base = (string) @iconv('UTF-8', 'ASCII//TRANSLIT//IGNORE', $base);
    $prefix = substr(strtoupper(preg_replace('/[^A-Za-z]/', '', $base)), 0, 6) ?: 'SWEEP';
    for ($i = 0; $i < 30; $i++) {
        $code = $prefix; for ($j = 0; $j < 3; $j++) $code .= REF_ALPHABET[random_int(0, strlen(REF_ALPHABET) - 1)];
        if (ref_find_by_code($pdo, $code)) continue;
        try { ref_q($pdo, 'UPDATE ref_users SET code = ? WHERE uid = ? AND code IS NULL', [$code, $uid]); } catch (Throwable $e) { continue; }
        $now = ref_row($pdo, $uid); if (!empty($now['code'])) return (string) $now['code'];
    }
    throw new RuntimeException('Could not create a referral code');
}
function ref_cookie_opts(int $expires): array
{
    $host = strtolower((string) ($_SERVER['HTTP_HOST'] ?? ''));
    $o = ['expires' => $expires, 'path' => '/', 'httponly' => true, 'samesite' => 'Lax', 'secure' => !empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off'];
    if (preg_match('/(^|\.)makeitsweep\.com$/', $host)) $o['domain'] = '.makeitsweep.com';   // works on the website and the app
    return $o;
}
/** /r/CODE: remember the code for 60 days (last click wins), count the click, go to sign-up. */
function ref_capture(PDO $pdo, string $code): bool
{
    $r = ref_find_by_code($pdo, $code); if (!$r) return false;
    setcookie(REF_COOKIE, (string) $r['code'], ref_cookie_opts(time() + REF_COOKIE_DAYS * 86400));
    $_COOKIE[REF_COOKIE] = $r['code'];
    ref_q($pdo, 'INSERT INTO referral_clicks (referrer_id, ip_hash, created_at) VALUES (?, ?, ?)', [$r['uid'], ref_ip_hash(), time()]);
    return true;
}
/** For the sign-up screen: ['name' => 'mateo', 'days' => 30] or null. */
function ref_signup_banner(PDO $pdo): ?array
{
    $code = (string) ($_COOKIE[REF_COOKIE] ?? ''); if ($code === '') return null;
    $r = ref_find_by_code($pdo, $code); if (!$r) return null;
    return ['name' => ref_username($pdo, (string) $r['uid']), 'days' => REF_REFEREE_DAYS, 'plan' => REF_REFEREE_PLAN, 'code' => $r['code']];
}
/** Right after a sign-up: link the new trader to the referrer. */
function ref_attach_on_signup(PDO $pdo, string $newUid): ?int
{
    $ip = ref_ip_hash();
    ref_row($pdo, $newUid);
    ref_q($pdo, 'UPDATE ref_users SET signup_ip_hash = ? WHERE uid = ?', [$ip, $newUid]);
    $code = (string) ($_COOKIE[REF_COOKIE] ?? '');
    if ($code !== '') { setcookie(REF_COOKIE, '', ref_cookie_opts(time() - 3600)); unset($_COOKIE[REF_COOKIE]); }
    if ($code === '') return null;
    $ref = ref_find_by_code($pdo, $code);
    if (!$ref || (string) $ref['uid'] === $newUid) return null;
    if ((int) ref_q($pdo, 'SELECT COUNT(*) FROM referrals WHERE ip_hash = ? AND created_at > ?', [$ip, time() - 86400])->fetchColumn() >= REF_MAX_IP_DAY) return null;
    $sameIp = !empty($ref['signup_ip_hash']) && hash_equals((string) $ref['signup_ip_hash'], $ip);
    $status = $sameIp ? 'review' : 'pending';
    try {
        ref_q($pdo, 'INSERT INTO referrals (referrer_id, referee_id, status, ip_hash, created_at) VALUES (?, ?, ?, ?, ?)', [$ref['uid'], $newUid, $status, $ip, time()]);
    } catch (Throwable $e) { return null; }   // already referred
    $id = (int) $pdo->lastInsertId();
    ref_q($pdo, 'UPDATE ref_users SET referred_by = ? WHERE uid = ?', [$ref['uid'], $newUid]);
    if ($status === 'pending' && REF_REFEREE_DAYS > 0) ref_give_days($pdo, $newUid, REF_REFEREE_DAYS, REF_REFEREE_PLAN);
    return $id;
}
/** Free days of Pro through billing grants; consecutive referral months stack end to end. */
function ref_give_days(PDO $pdo, string $uid, int $days, string $plan = REF_BONUS_PLAN): bool
{
    if (!function_exists('billing_on') || !billing_on()) return false;
    sb_schema($pdo);
    $now = function_exists('sb_now') ? sb_now() : time();
    $last = (int) (ref_q($pdo, "SELECT MAX(ends_at) FROM billing_grants WHERE uid = ? AND reason = 'referral' AND ends_at > ?", [$uid, $now])->fetchColumn() ?: 0);
    $start = max($now, $last);
    ref_q($pdo, 'INSERT INTO billing_grants (uid, plan, starts_at, ends_at, reason, created_at) VALUES (?, ?, ?, ?, ?, ?)', [$uid, $plan, $start, $start + $days * 86400, 'referral', $now]);
    return true;
}
function ref_progress(PDO $pdo, array $r): array
{
    $from = (int) $r['created_at']; $to = $from + REF_WINDOW_DAYS * 86400;
    $n = 0; $days = [];
    foreach (ref_q($pdo, "SELECT created_at, data FROM documents WHERE user_id = ? AND collection = 'trades'", [$r['referee_id']]) as $t) {
        $ts = is_numeric($t['created_at']) ? (int) $t['created_at'] : (int) strtotime((string) $t['created_at']);
        if ($ts < $from || $ts >= $to) continue;
        $d = json_decode((string) $t['data'], true) ?: []; if (!empty($d['demo'])) continue;
        $n++; $days[gmdate('Y-m-d', $ts)] = 1;
    }
    return ['trades' => $n, 'days' => count($days), 'days_left' => max(0, REF_WINDOW_DAYS - (int) floor((time() - $from) / 86400))];
}
/** After a trade is added (cheap when nothing is pending). */
function ref_check_user(PDO $pdo, string $refereeId): void
{
    ref_schema($pdo);
    $r = ref_q($pdo, "SELECT * FROM referrals WHERE referee_id = ? AND status = 'pending'", [$refereeId])->fetch(PDO::FETCH_ASSOC);
    if (!$r) return;
    $p = ref_progress($pdo, $r);
    if ($p['trades'] >= REF_TRADES && $p['days'] >= REF_DAYS) ref_reward($pdo, $r, 'activity');
}
/** Stripe webhook: the friend paid a first real invoice. */
function ref_on_first_payment(PDO $pdo, string $refereeId): void
{
    ref_schema($pdo);
    $r = ref_q($pdo, "SELECT * FROM referrals WHERE referee_id = ? AND status = 'pending'", [$refereeId])->fetch(PDO::FETCH_ASSOC);
    if ($r) ref_reward($pdo, $r, 'payment');
}
function ref_reward(PDO $pdo, array $r, string $reason): bool
{
    // claim the row first, so two parallel calls can't both reward
    $now = time();
    $claim = ref_q($pdo, "UPDATE referrals SET status = 'qualified', qualify_reason = ?, qualified_at = ? WHERE id = ? AND status = 'pending'", [$reason, $now, $r['id']]);
    if ($claim->rowCount() !== 1) return false;
    $earned = (int) ref_q($pdo, "SELECT COUNT(*) FROM referrals WHERE referrer_id = ? AND status = 'rewarded' AND rewarded_at > ?", [$r['referrer_id'], $now - 365 * 86400])->fetchColumn();
    if ($earned >= REF_MAX_YEAR) return false;   // qualified, but the yearly cap is reached
    $type = 'bonus_days'; $value = REF_REWARD_DAYS;
    try {
        if (function_exists('billing_on') && billing_on()) {
            require_once dirname(__DIR__) . '/billing/billing-stripe.php';
            $sub = sb_active_sub($pdo, (string) $r['referrer_id']);
            $cus = (string) (ref_q($pdo, 'SELECT stripe_customer FROM billing_users WHERE uid = ?', [$r['referrer_id']])->fetchColumn() ?: '');
            if ($sub && $cus !== '' && in_array($sub['plan'], ['pro', 'elite'], true)) {
                $c = sb_cfg();
                $cents = (int) round(((float) ($c['display_prices'][$sub['plan']]['month'] ?? 0)) * 100);
                if ($cents > 0) {
                    sb_stripe('POST', 'customers/' . rawurlencode($cus) . '/balance_transactions',
                        ['amount' => -$cents, 'currency' => strtolower((string) ($c['currency'] ?? 'usd')), 'description' => 'Sweep: free month (referral #' . $r['id'] . ')'], 'sweep-referral-' . $r['id']);
                    $type = 'stripe_credit'; $value = $cents;
                }
            }
        }
    } catch (Throwable $e) { error_log('[Sweep referral] Stripe credit failed #' . $r['id'] . ': ' . $e->getMessage()); }
    if ($type === 'bonus_days') ref_give_days($pdo, (string) $r['referrer_id'], REF_REWARD_DAYS);
    ref_q($pdo, "UPDATE referrals SET status = 'rewarded', reward_type = ?, reward_value = ?, rewarded_at = ? WHERE id = ?", [$type, $value, $now, $r['id']]);
    return true;
}
/** Catch-up and expiry. Runs at most once a day, triggered by app traffic (no cron needed). */
function ref_cron(PDO $pdo, bool $force = false): array
{
    ref_schema($pdo);
    $k = 'ref_cron_at';
    $last = (int) (ref_q($pdo, 'SELECT v FROM app_settings WHERE k = ?', [$k])->fetchColumn() ?: 0);
    if (!$force && $last > time() - 86400) return ['skipped' => true];
    ref_q($pdo, 'DELETE FROM app_settings WHERE k = ?', [$k]); ref_q($pdo, 'INSERT INTO app_settings (k, v) VALUES (?, ?)', [$k, (string) time()]);
    $rows = ref_q($pdo, "SELECT * FROM referrals WHERE status = 'pending'")->fetchAll(PDO::FETCH_ASSOC);
    $rew = 0; $exp = 0;
    foreach ($rows as $r) {
        $p = ref_progress($pdo, $r);
        if ($p['trades'] >= REF_TRADES && $p['days'] >= REF_DAYS) { if (ref_reward($pdo, $r, 'activity')) $rew++; }
        elseif ((int) $r['created_at'] < time() - REF_WINDOW_DAYS * 86400) { ref_q($pdo, "UPDATE referrals SET status = 'expired' WHERE id = ? AND status = 'pending'", [$r['id']]); $exp++; }
    }
    return ['checked' => count($rows), 'rewarded' => $rew, 'expired' => $exp];
}
function ref_display_name(string $username): string { return g_len($username) > 2 ? g_sub($username, 0, 2) . '•••' . g_sub($username, -1) : $username; }
/** The Referrals tab. */
function ref_dashboard(PDO $pdo, string $uid, string $baseUrl): array
{
    ref_cron($pdo);
    $code = ref_get_code($pdo, $uid);
    $clicks = (int) ref_q($pdo, 'SELECT COUNT(*) FROM referral_clicks WHERE referrer_id = ?', [$uid])->fetchColumn();
    $list = []; $stats = ['invited' => 0, 'pending' => 0, 'validated' => 0, 'earned_year' => 0];
    $rows = ref_q($pdo, "SELECT r.*, u.username FROM referrals r LEFT JOIN users u ON u.id = r.referee_id WHERE r.referrer_id = ? AND r.status <> 'rejected' ORDER BY r.created_at DESC LIMIT 100", [$uid])->fetchAll(PDO::FETCH_ASSOC);
    foreach ($rows as $r) {
        $stats['invited']++;
        $st = $r['status'] === 'review' ? 'pending' : $r['status'];
        if ($st === 'pending') $stats['pending']++;
        if (in_array($st, ['qualified', 'rewarded'], true)) $stats['validated']++;
        if ($st === 'rewarded' && (int) $r['rewarded_at'] > time() - 365 * 86400) $stats['earned_year']++;
        $name = ref_display_name((string) ($r['username'] ?? '?'));
        $item = ['name' => $name, 'initials' => g_upper(g_sub($name, 0, 1)), 'joined' => gmdate('c', (int) $r['created_at']), 'status' => $st, 'reward' => $r['reward_type']];
        if ($r['status'] === 'pending' || $r['status'] === 'review') $item += ref_progress($pdo, $r);
        $list[] = $item;
    }
    $bonus = null;
    if (function_exists('billing_on') && billing_on()) {
        sb_schema($pdo);
        $e = ref_q($pdo, "SELECT MAX(ends_at) FROM billing_grants WHERE uid = ? AND reason = 'referral' AND ends_at > ?", [$uid, time()])->fetchColumn();
        if ($e) $bonus = gmdate('c', (int) $e);
    }
    return ['code' => $code, 'link' => rtrim($baseUrl, '/') . '/r/' . $code, 'clicks' => $clicks, 'stats' => $stats, 'bonus_until' => $bonus, 'referrals' => $list,
        'rules' => ['reward_days' => REF_REWARD_DAYS, 'referee_days' => REF_REFEREE_DAYS, 'trades' => REF_TRADES, 'days' => REF_DAYS, 'window' => REF_WINDOW_DAYS, 'max_year' => REF_MAX_YEAR],
        'billing' => function_exists('billing_on') && billing_on()];
}
/** Administrator view: all referrals, with review actions. */
function ref_admin_list(PDO $pdo): array
{
    ref_schema($pdo);
    return ref_q($pdo, 'SELECT r.id, r.status, r.qualify_reason, r.reward_type, r.reward_value, r.created_at, r.rewarded_at, a.username AS referrer, b.username AS referee
        FROM referrals r LEFT JOIN users a ON a.id = r.referrer_id LEFT JOIN users b ON b.id = r.referee_id ORDER BY r.created_at DESC LIMIT 300')->fetchAll(PDO::FETCH_ASSOC);
}
