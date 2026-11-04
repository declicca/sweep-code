<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli' && realpath((string) ($_SERVER['SCRIPT_FILENAME'] ?? '')) === realpath(__FILE__)) { http_response_code(404); exit; }
/**
 * Sweep — the automatic emails, sent by our own server (replaces Loops, 4 Nov. 2026): welcome, day one, follow-ups,
 * milestones, absences, the end of the Pro trial, Stripe, referral. Each one is an automation of Admin › Emails
 * (mail_campaigns.auto = its key): its text in EN / FR / ES, switched on or off there, with its numbers. An event puts one
 * line in mail_queue (mail/mail-core.php); mail/send-cron.php sends it within the minute.
 *
 * The events (same moments as under Loops, same table email_events_log: what Loops already sent is never sent again):
 *  - in the app, right away: signedUp, profileCompleted, firstAccountAdded, firstPlanSaved, firstTradeLogged,
 *    tradesMilestone (10th, 50th, 100th trade), firstPayoutLogged (once each), subscriptionStarted, subscriptionCanceled,
 *    paymentFailed (Stripe webhook), referralRewarded;
 *  - by mail/send-cron.php: once a New York day from 7:30, inactive3d / 7d / 14d / 30d and proTrialDaysLeft (30, 10, 3),
 *    proTrialEnded; every run, day1Evening (18:30 New York on the day of sign-up, or the next day after 18:00, when no plan
 *    is saved yet; given up 6 hours later).
 * Rules:
 *  - an event « once » leaves once per trader, even after a delete and a new add: it is claimed in email_events_log before
 *    it is queued (one statement); trades count copies once and never sample data;
 *  - nothing before the first run (ma_init): what existing traders already did is marked, so a trader with 300 trades never
 *    gets « first trade »; after Loops, its marks are kept as they are;
 *  - an automation switched off: the moment passes (claimed, nothing queued);
 *  - the queue respects the unsubscribe (marketing) and the addresses set aside, at sending time.
 */

const MA_MILESTONES = [10, 50, 100];   // tradesMilestone
const MA_INACTIVE = [3, 7, 14, 30];    // inactive3d … inactive30d: days without coming back
const MA_TRIAL_LEFT = [3, 10, 30];     // proTrialDaysLeft: days before the end of the Pro trial
const MA_NY = 'America/New_York';

function ma_pdo(): PDO { return db(); }
function ma_q(string $sql, array $args = []): PDOStatement { $st = ma_pdo()->prepare($sql); $st->execute($args); return $st; }
function ma_now(): int { return isset($GLOBALS['SB_NOW']) ? (int) $GLOBALS['SB_NOW'] : time(); }   // a test date moves billing too
function ma_setting(string $k): ?string { $v = ma_q('SELECT v FROM app_settings WHERE k = ?', [$k])->fetchColumn(); return $v === false ? null : (string) $v; }

/** the texts as they start (mail/mail-auto-texts.php) */
function ma_catalog(): array { static $c = null; return $c ?? ($c = (array) require __DIR__ . '/mail-auto-texts.php'); }

/** Each automation of the catalog that is not in mail_campaigns yet: added once, with its starting text (never overwritten). */
function ma_seed(PDO $pdo): void
{
    static $done = false; if ($done) return;
    ml_schema($pdo); $now = time();
    $have = array_flip(ml_q($pdo, 'SELECT auto FROM mail_campaigns WHERE auto IS NOT NULL')->fetchAll(PDO::FETCH_COLUMN));
    foreach (ma_catalog() as $key => $a) {
        if (isset($have[$key])) continue;
        ml_q($pdo, 'INSERT INTO mail_campaigns (name, status, content_json, audience_json, auto, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
            [$a['name']['en'], $a['on'] ? 'active' : 'off', json_encode(ml_clean_content($a['content']), JSON_UNESCAPED_UNICODE), '{}', $key, $now, $now]);
    }
    $done = true;
}
/** What Admin shows of an automation: its name and trigger in the three languages, its kind, its own variables, its place in the list */
function ma_info(string $key): ?array
{
    $c = ma_catalog(); if (!isset($c[$key])) return null;
    return ['name' => $c[$key]['name'], 'when' => $c[$key]['when'], 'kind' => ma_kind($key), 'vars' => $c[$key]['vars'] ?? [], 'order' => array_search($key, array_keys($c), true)];
}
function ma_kind(string $key): string { return (ma_catalog()[$key]['kind'] ?? 'marketing') === 'transactional' ? 'transactional' : 'marketing'; }

/** ready once ma_init() marked what existing traders already did (after Loops: its own mark counts) */
function ma_ready(bool $reset = false): bool
{
    static $r = null;
    if ($reset) { $r = null; return false; }
    if ($r !== null) return $r;
    try { return $r = ma_setting('mail_auto_since') !== null; } catch (Throwable $e) { return $r = false; }
}

/* ───────────── what was sent: email_events_log (the table Loops used) ───────────── */

function ma_schema(): void
{
    static $done = false; if ($done) return;
    $my = ma_pdo()->getAttribute(PDO::ATTR_DRIVER_NAME) === 'mysql';
    ma_pdo()->exec('CREATE TABLE IF NOT EXISTS email_events_log (user_id ' . ($my ? 'VARCHAR(120)' : 'TEXT') . ' NOT NULL, event_name ' . ($my ? 'VARCHAR(64)' : 'TEXT')
        . ' NOT NULL, sent_at INT NOT NULL)' . ($my ? ' DEFAULT CHARSET=utf8mb4' : ''));
    try { ma_pdo()->exec($my ? 'ALTER TABLE email_events_log ADD INDEX email_events_log_user (user_id, event_name)' : 'CREATE INDEX IF NOT EXISTS email_events_log_user ON email_events_log (user_id, event_name)'); } catch (Throwable $e) { /* exists */ }
    $done = true;
}
/** The events « once » already sent to a trader (tradesMilestone and proTrialDaysLeft carry their step: « tradesMilestone:10 »). */
function ma_done(string $uid): array { ma_schema(); return ma_q('SELECT DISTINCT event_name FROM email_events_log WHERE user_id = ?', [$uid])->fetchAll(PDO::FETCH_COLUMN); }
function ma_logged(string $uid, string $key, int $since = 0): bool { ma_schema(); return (bool) ma_q('SELECT 1 FROM email_events_log WHERE user_id = ? AND event_name = ? AND sent_at >= ?', [$uid, $key, $since])->fetchColumn(); }
/** Claims an event « once »: true when this call wrote the line (and so sends it). $since: only a line from then on counts (absences). */
function ma_claim(string $uid, string $key, int $at, int $since = 0): bool
{
    ma_schema();
    $mysql = ma_pdo()->getAttribute(PDO::ATTR_DRIVER_NAME) === 'mysql';
    try {
        return ma_q('INSERT INTO email_events_log (user_id, event_name, sent_at) SELECT ?, ?, ?' . ($mysql ? ' FROM DUAL' : '')
            . ' WHERE NOT EXISTS (SELECT 1 FROM email_events_log WHERE user_id = ? AND event_name = ? AND sent_at >= ?)', [$uid, $key, $at, $uid, $key, $since])->rowCount() === 1;
    } catch (Throwable $e) { error_log('[Sweep mail auto] claim ' . $key . ' ' . $uid . ': ' . $e->getMessage()); return false; }
}
function ma_unclaim(string $uid, string $key, int $at): void
{
    try { ma_q('DELETE FROM email_events_log WHERE user_id = ? AND event_name = ? AND sent_at = ?', [$uid, $key, $at]); }
    catch (Throwable $e) { error_log('[Sweep mail auto] unclaim ' . $key . ' ' . $uid . ': ' . $e->getMessage()); }
}

/* ───────────── queueing ───────────── */

/**
 * One email of an automation for a trader, in the queue now. True when there is nothing more to do (queued, the
 * automation off, or no address); false only when the database refused (the claim is then given back).
 * $vars: the event's values ({firm}, {milestone}, {days}, {plan}).
 */
function ma_send(string $uid, string $key, array $vars = []): bool
{
    $pdo = ma_pdo();
    try {
        ma_seed($pdo);
        $c = ml_q($pdo, 'SELECT id, status FROM mail_campaigns WHERE auto = ?', [$key])->fetch(PDO::FETCH_ASSOC);
        if (!$c || $c['status'] !== 'active') return true;
        $u = ma_q('SELECT email, first_name, lang, disabled FROM users WHERE id = ?', [$uid])->fetch(PDO::FETCH_ASSOC);
        if (!$u || (int) ($u['disabled'] ?? 0) === 1 || !filter_var(trim((string) $u['email']), FILTER_VALIDATE_EMAIL)) return true;
        if (isset($vars['plan'])) $vars['plan'] = ucfirst((string) $vars['plan']);
        $now = time();
        ml_q($pdo, "INSERT INTO mail_queue (campaign_id, user_id, email, lang, first_name, kind, vars_json, token, state, next_at, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'queued', ?, ?)",
            [(int) $c['id'], $uid, trim((string) $u['email']), ml_lang($u['lang'] ?? ''), mb_substr(trim((string) ($u['first_name'] ?? '')), 0, 40), ma_kind($key),
             $vars ? json_encode(array_map('strval', $vars), JSON_UNESCAPED_UNICODE) : null, ml_token(), $now, $now]);
        ml_q($pdo, 'UPDATE mail_campaigns SET recipients = recipients + 1 WHERE id = ?', [(int) $c['id']]);
        return true;
    } catch (Throwable $e) { error_log('[Sweep mail auto] ' . $key . ' ' . $uid . ': ' . $e->getMessage()); return false; }
}
/** In the app: after the response (the first account waits a moment for its firm). In the crons and tests: right away. */
function ma_later(string $key, callable $fn): void
{
    if (PHP_SAPI === 'cli') { $fn(); return; }
    if (!isset($GLOBALS['MA_LATER'])) {
        $GLOBALS['MA_LATER'] = [];
        register_shutdown_function(function (): void {
            $q = $GLOBALS['MA_LATER']; $GLOBALS['MA_LATER'] = [];
            if (!$q) return;
            if (function_exists('fastcgi_finish_request')) @fastcgi_finish_request(); elseif (function_exists('litespeed_finish_request')) @litespeed_finish_request();
            foreach ($q as $k => $fn) { try { $fn(); } catch (Throwable $e) { error_log('[Sweep mail auto] ' . $k . ': ' . $e->getMessage()); } }
        });
    }
    $GLOBALS['MA_LATER'][$key] = $fn;
}
/** An event that can happen again (Stripe, referral). */
function ma_event(string $uid, string $name, array $vars = []): void
{
    if (ma_ready()) ma_send($uid, $name, $vars);
}
/** An event « once » ($key: its line in email_events_log, « tradesMilestone:10 »). True when claimed. */
function ma_once(string $uid, string $name, array $vars = [], ?string $key = null): bool
{
    if (!ma_ready()) return false;
    $key = $key ?? $name; $at = ma_now();
    if (!ma_claim($uid, $key, $at)) return false;
    if (!ma_send($uid, $name, $vars)) ma_unclaim($uid, $key, $at);
    return true;
}
/** The trader deleted their account (called before the users row goes): their lines of email_events_log go. */
function ma_forget(string $uid): void
{
    try { ma_schema(); ma_q('DELETE FROM email_events_log WHERE user_id = ?', [$uid]); } catch (Throwable $e) { error_log('[Sweep mail auto] forget ' . $uid . ': ' . $e->getMessage()); }
}

/* ───────────── the app's events ───────────── */

/** Real trades of a trader: copies once (a trade copied on 3 accounts is one trade), never sample data. */
function ma_trade_count(string $uid): int
{
    $n = 0; $seen = [];
    foreach (ma_q("SELECT data FROM documents WHERE user_id = ? AND collection = 'trades'", [$uid])->fetchAll(PDO::FETCH_COLUMN) as $raw) {
        $d = json_decode((string) $raw, true);
        if (!is_array($d) || !empty($d['demo'])) continue;
        $g = (string) ($d['copy_group'] ?? '');
        if ($g !== '') { if (isset($seen[$g])) continue; $seen[$g] = true; }
        $n++;
    }
    return $n;
}
/** Has the trader a real document of this collection (sample data never counts)? */
function ma_has(string $uid, string $col, ?callable $keep = null): bool
{
    foreach (ma_q('SELECT data FROM documents WHERE user_id = ? AND collection = ?', [$uid, $col])->fetchAll(PDO::FETCH_COLUMN) as $raw) {
        $d = json_decode((string) $raw, true);
        if (is_array($d) && empty($d['demo']) && (!$keep || $keep($d))) return true;
    }
    return false;
}
/** {firm} of firstAccountAdded: the account's firm in Sweep, else its preset's firm in the catalog, else ''. */
function ma_firm_of(string $uid, array $a): string
{
    $fid = (string) ($a['firm_id'] ?? '');
    if ($fid !== '') {
        $raw = ma_q("SELECT data FROM documents WHERE user_id = ? AND collection = 'firms' AND id = ?", [$uid, $fid])->fetchColumn();
        $name = $raw ? trim((string) ((json_decode((string) $raw, true) ?: [])['name'] ?? '')) : '';
        if ($name !== '') return $name;
    }
    $pid = explode('|', (string) ($a['preset'] ?? ''))[0];
    if ($pid !== '') foreach ((array) ((json_decode((string) @file_get_contents(dirname(__DIR__) . '/presets/seed.json'), true) ?: [])['firms'] ?? []) as $f)
        if (($f['id'] ?? '') === $pid) return (string) ($f['name'] ?? '');
    return '';
}
/** The first account: claimed and queued after the response, when the firm (saved by its own request at the same time) is there. */
function ma_on_account(array $p): void
{
    $uid = (string) ($p['uid'] ?? ''); $a = (array) ($p['doc'] ?? []);
    if ($uid === '' || !empty($a['demo']) || !ma_ready() || in_array('firstAccountAdded', ma_done($uid), true)) return;
    ma_later("account:$uid", function () use ($uid, $a): void {
        $firm = ma_firm_of($uid, $a);
        if ($firm === '' && !empty($a['firm_id']) && PHP_SAPI !== 'cli') { usleep(1000000); $firm = ma_firm_of($uid, $a); }   // its firm a moment late
        $at = ma_now();
        if (ma_claim($uid, 'firstAccountAdded', $at) && !ma_send($uid, 'firstAccountAdded', ['firm' => $firm])) ma_unclaim($uid, 'firstAccountAdded', $at);
    });
}
/** A trade saved: the first one, then the 10th, 50th and 100th. Several steps passed in one go (an import): only the highest leaves. */
function ma_on_trade(array $p): void
{
    $uid = (string) ($p['uid'] ?? '');
    if ($uid === '' || !empty(($p['doc'] ?? [])['demo']) || !ma_ready()) return;
    $left = array_diff(array_merge(['firstTradeLogged'], array_map(fn($m) => "tradesMilestone:$m", MA_MILESTONES)), ma_done($uid));
    if (!$left) return;   // after the 100th trade: one small query per save
    $n = ma_trade_count($uid);
    if ($n >= 1 && in_array('firstTradeLogged', $left, true)) ma_once($uid, 'firstTradeLogged');
    $reached = array_values(array_filter(MA_MILESTONES, fn($m) => $n >= $m && in_array("tradesMilestone:$m", $left, true)));
    if (!$reached) return;
    $top = max($reached);
    foreach ($reached as $m) if ($m !== $top) ma_claim($uid, "tradesMilestone:$m", ma_now());   // passed: never sent later
    ma_once($uid, 'tradesMilestone', ['milestone' => $top], "tradesMilestone:$top");
}
/** The first plan saved (a bias in the journal's pre-market): once. A trader who had plans before is marked, never told « first plan ». */
function ma_on_journal(array $p): void
{
    $uid = (string) ($p['uid'] ?? ''); $d = (array) ($p['doc'] ?? []);
    if ($uid === '' || !empty($d['demo']) || empty(($d['pre'] ?? [])['bias']) || !ma_ready() || in_array('firstPlanSaved', ma_done($uid), true)) return;
    $n = 0;
    foreach (ma_q("SELECT data FROM documents WHERE user_id = ? AND collection = 'journals'", [$uid])->fetchAll(PDO::FETCH_COLUMN) as $raw) {
        $j = json_decode((string) $raw, true); if (is_array($j) && empty($j['demo']) && !empty(($j['pre'] ?? [])['bias'])) $n++;
    }
    if ($n > 1) { ma_claim($uid, 'firstPlanSaved', ma_now()); return; }
    ma_once($uid, 'firstPlanSaved');
}
function ma_on_payout(array $p): void
{
    $uid = (string) ($p['uid'] ?? ''); $d = (array) ($p['doc'] ?? []);
    if ($uid === '' || !empty($d['demo']) || !empty($d['estimated'])) return;   // a payout the trader entered, not the estimate of « Your real net »
    ma_once($uid, 'firstPayoutLogged');
}

/**
 * After a verified Stripe event (billing/billing-stripe.php, sb_handle_event), the trader known:
 *   invoice.paid, first invoice of a new subscription      → subscriptionStarted {plan}
 *   invoice.payment_failed                                  → paymentFailed {plan}
 *   customer.subscription.updated, a cancellation just asked (it ends with the period) → subscriptionCanceled {plan}
 *   customer.subscription.deleted, no cancellation asked before (stopped right away)    → subscriptionCanceled {plan}
 * $before: the event's previous_attributes (what an update changed, with the old values).
 */
function ma_stripe(PDO $pdo, string $type, array $obj, array $before, string $uid): void
{
    if (!ma_ready() || $uid === '') return;
    $planOf = function ($subId) use ($pdo): string {
        $r = is_string($subId) && $subId !== '' ? sb_q($pdo, 'SELECT plan FROM billing_subs WHERE id = ?', [$subId])->fetch(PDO::FETCH_ASSOC) : null;
        return (string) ($r['plan'] ?? '');
    };
    if ($type === 'invoice.paid' || $type === 'invoice.payment_failed') {
        $sub = $obj['subscription'] ?? ($obj['parent']['subscription_details']['subscription'] ?? null);
        $plan = $planOf(is_array($sub) ? ($sub['id'] ?? null) : $sub);
        if ($type === 'invoice.payment_failed') ma_event($uid, 'paymentFailed', ['plan' => $plan]);
        elseif (($obj['billing_reason'] ?? '') === 'subscription_create') ma_event($uid, 'subscriptionStarted', ['plan' => $plan]);
        return;
    }
    if (strpos($type, 'customer.subscription.') !== 0) return;
    $asked = fn(array $s): bool => !empty($s['cancel_at_period_end']) || !empty($s['cancel_at']);
    if (($type === 'customer.subscription.updated' && $asked($obj) && !$asked(array_merge($obj, $before)))
        || ($type === 'customer.subscription.deleted' && !$asked($obj))) ma_event($uid, 'subscriptionCanceled', ['plan' => $planOf($obj['id'] ?? null)]);
}

/* ───────────── first run and the timed events (mail/send-cron.php) ───────────── */

/** Last visit: users.last_login (sign-in, and each return to the app at most once an hour), else the sign-up. */
function ma_last_seen(array $u): int { return (int) (strtotime((string) (($u['last_login'] ?? '') ?: ($u['created_at'] ?? ''))) ?: 0); }

/** plan, pays (Stripe), Discord crew (Elite for life, given in Admin), permanent access, end of the Pro trial. */
function ma_billing(string $uid, array $u): array
{
    $out = ['plan' => 'elite', 'paying' => false, 'crew' => false, 'permanent' => false, 'trial_end' => null, 'live' => false];   // billing off: nothing is limited
    if (!function_exists('billing_on') || !billing_on()) return $out;
    try {
        $pdo = ma_pdo(); sb_schema($pdo);
        sb_user($pdo, $uid, $u['created_at'] ?? null, $u['email'] ?? null);   // the starting grant (trial) exists from the first contact, as on api/billing/me
        $now = sb_now();
        $out['plan'] = sb_effective($pdo, $uid)['plan'];
        $out['live'] = sb_live($uid);
        $out['paying'] = $out['live'] && sb_active_sub($pdo, $uid) !== null;
        $perm = (sb_cfg()['comp_users'] ?? [])[$uid] ?? null;   // access for life: config, or « Permanent » in Admin › Traders (comp, 100 years)
        if ($perm !== null && !isset(SB_RANK[$perm])) $perm = null;
        foreach (sb_q($pdo, "SELECT plan FROM billing_grants WHERE uid = ? AND reason = 'comp' AND starts_at <= ? AND ends_at > ?", [$uid, $now, $now + 3650 * 86400])->fetchAll(PDO::FETCH_COLUMN) as $p)
            if (isset(SB_RANK[$p]) && ($perm === null || SB_RANK[$p] > SB_RANK[$perm])) $perm = (string) $p;
        $out['permanent'] = $perm !== null;
        $out['crew'] = $perm === 'elite';
        $end = sb_q($pdo, "SELECT MAX(ends_at) FROM billing_grants WHERE uid = ? AND reason IN ('trial','early_access')", [$uid])->fetchColumn();
        $out['trial_end'] = $end ? (int) $end : null;
    } catch (Throwable $e) { error_log('[Sweep mail auto] plan of ' . $uid . ': ' . $e->getMessage()); }
    return $out;
}

/**
 * First run: what existing traders have already done is marked in email_events_log without sending (sign-up, profile,
 * first account, first trade, milestones reached, first payout, first plan, the evening of day one); after Loops
 * (loops_since set), its marks are what was sent: only the evening of day one is marked. Returns how many lines were written.
 */
function ma_init(): int
{
    $now = ma_now(); $marked = 0; $after = ma_setting('loops_since') !== null;
    foreach (ma_q('SELECT id, first_name FROM users')->fetchAll(PDO::FETCH_ASSOC) as $u) {
        $uid = (string) $u['id']; $done = ['day1Evening'];
        if (!$after) {
            $n = ma_trade_count($uid);
            $done[] = 'signedUp';
            if (trim((string) $u['first_name']) !== '') $done[] = 'profileCompleted';
            if (ma_has($uid, 'accounts')) $done[] = 'firstAccountAdded';
            if ($n >= 1) $done[] = 'firstTradeLogged';
            foreach (MA_MILESTONES as $m) if ($n >= $m) $done[] = "tradesMilestone:$m";
            if (ma_has($uid, 'payouts', fn($d) => empty($d['estimated']))) $done[] = 'firstPayoutLogged';
            if (ma_has($uid, 'journals', fn($d) => !empty(($d['pre'] ?? [])['bias']))) $done[] = 'firstPlanSaved';
        }
        foreach ($done as $k) if (ma_claim($uid, $k, $now)) $marked++;
    }
    ml_set_setting(ma_pdo(), 'mail_auto_since', (string) $now);
    if ($after) foreach (['loops_daily_at' => 'mail_auto_daily_at', 'loops_daily_day' => 'mail_auto_day'] as $from => $to)   // the daily window goes on from Loops' last run
        if (($d = ma_setting($from)) !== null) ml_set_setting(ma_pdo(), $to, $d);
    ma_ready(true);
    return $marked;
}

/**
 * The daily steps of a trader that came due in ($from, $now]: [line in email_events_log, automation, values, since].
 * One step of each kind at most, the latest (several come due together only after the server missed days):
 *  - absence: 3, 7, 14 and 30 days after the last visit; « since » = that visit, so a new absence starts over;
 *  - Pro trial: 30, 10 and 3 days before its end, then its end; never for the Discord crew (or another access for life)
 *    nor a trader who pays. $b: ma_billing().
 */
function ma_daily_due(array $u, array $b, int $from, int $now): array
{
    $out = [];
    $seen = ma_last_seen($u);
    if ($seen) foreach (array_reverse(MA_INACTIVE) as $d) {
        $due = $seen + $d * 86400;
        if ($due > $from && $due <= $now) { $out[] = ["inactive{$d}d", "inactive{$d}d", [], $seen]; break; }
    }
    if ($b['live'] && $b['trial_end'] && !$b['paying'] && !$b['crew'] && !$b['permanent']) {
        $end = (int) $b['trial_end'];
        $steps = [['proTrialEnded', 'proTrialEnded', [], $end]];
        foreach (MA_TRIAL_LEFT as $d) $steps[] = ["proTrialDaysLeft:$d", 'proTrialDaysLeft', ['days' => $d], $end - $d * 86400];
        foreach ($steps as [$key, $name, $vars, $due]) if ($due > $from && $due <= $now) { $out[] = [$key, $name, $vars, 0]; break; }
    }
    return $out;
}

/**
 * The daily run over these traders: each step due in ($from, $now] is claimed, then queued; a refused one gives its claim
 * back (tried again at the next run). $dry: only says what would leave. $say: one line per step.
 * ['sent' => [automation => n], 'failed' => n, 'error' => last refusal].
 */
function ma_daily_run(array $ids, int $from, int $now, bool $dry = false, ?callable $say = null): array
{
    $say = $say ?? function (string $s): void {};
    $sent = []; $failed = 0; $err = '';
    foreach ($ids as $uid) {
        $uid = (string) $uid;
        $u = ma_q('SELECT id, email, created_at, last_login, disabled FROM users WHERE id = ?', [$uid])->fetch(PDO::FETCH_ASSOC);
        if (!$u || (int) $u['disabled'] === 1 || trim((string) $u['email']) === '') continue;
        try {
            foreach (ma_daily_due($u, ma_billing($uid, $u), $from, $now) as [$key, $name, $vars, $since]) {
                $what = $name . ($vars ? ' ' . json_encode($vars) : '') . " → $uid";
                if ($dry) { $say((ma_logged($uid, $key, $since) ? 'already sent: ' : 'would send: ') . $what); continue; }
                if (!ma_claim($uid, $key, $now, $since)) { $say("already sent: $what"); continue; }
                if (ma_send($uid, $name, $vars)) { $sent[$name] = ($sent[$name] ?? 0) + 1; $say("sent: $what"); }
                else { ma_unclaim($uid, $key, $now); $failed++; $err = "$name $uid"; $say("NOT sent: $what"); }
            }
        } catch (Throwable $e) { $failed++; $err = $uid . ': ' . $e->getMessage(); error_log('[Sweep mail auto] daily ' . $err); }
    }
    return ['sent' => $sent, 'failed' => $failed, 'error' => $err];
}

/** 18:30 New York on the trader's day of sign-up, or the next day when they signed up from 18:00 */
function ma_evening_due(int $signup): int
{
    $l = (new DateTimeImmutable('@' . $signup))->setTimezone(new DateTimeZone(MA_NY));
    $d = new DateTimeImmutable($l->format('Y-m-d') . ' 18:30', new DateTimeZone(MA_NY));
    return ($l->format('H:i') >= '18:00' ? $d->modify('+1 day') : $d)->getTimestamp();
}
/** day1Evening for the traders who signed up in the last 3 days: due, no plan saved yet; given up 6 hours after its time. */
function ma_evening_run(int $now): int
{
    $n = 0;
    foreach (ma_q('SELECT id, created_at FROM users WHERE disabled = 0 AND created_at >= ?', [gmdate('Y-m-d\TH:i:s\Z', $now - 3 * 86400)])->fetchAll(PDO::FETCH_ASSOC) as $u) {
        $uid = (string) $u['id']; $t = strtotime((string) $u['created_at']); if (!$t) continue;
        $due = ma_evening_due($t);
        if ($now < $due || ma_logged($uid, 'day1Evening')) continue;
        if ($now > $due + 6 * 3600 || ma_logged($uid, 'firstPlanSaved') || ma_has($uid, 'journals', fn($d) => !empty(($d['pre'] ?? [])['bias']))) { ma_claim($uid, 'day1Evening', $now); continue; }
        if (ma_once($uid, 'day1Evening')) $n++;
    }
    return $n;
}

/**
 * Every run of mail/send-cron.php: the first run marks the past; the evening of day one; from 7:30 New York, once a day,
 * the absences and the trial (what came due since the previous daily run, a whole day the first time). A short note.
 */
function ma_cron(PDO $pdo, ?int $now = null): string
{
    $now = $now ?? time(); ma_seed($pdo); ma_schema();
    if (!ma_ready()) ma_init();
    $note = [];
    if ($e = ma_evening_run($now)) $note[] = "$e day-one evening";
    $local = (new DateTimeImmutable('@' . $now))->setTimezone(new DateTimeZone(MA_NY)); $day = $local->format('Y-m-d');
    if ($local->format('H:i') >= '07:30' && ma_setting('mail_auto_day') !== $day) {
        $prev = (int) (ma_setting('mail_auto_daily_at') ?? 0);
        $from = $prev > 0 && $prev < $now ? $prev : $now - 86400;
        $r = ma_daily_run(ma_q('SELECT id FROM users WHERE disabled = 0 ORDER BY created_at')->fetchAll(PDO::FETCH_COLUMN), $from, $now);
        if ($r['failed'] === 0) { ml_set_setting($pdo, 'mail_auto_daily_at', (string) $now); ml_set_setting($pdo, 'mail_auto_day', $day); }
        $note[] = $r['sent'] ? array_sum($r['sent']) . ' daily' : 'daily: nothing due';
        if ($r['failed']) $note[] = $r['failed'] . ' daily not queued (' . $r['error'] . ')';
    }
    return implode(', ', $note);
}

if (class_exists('Events', false)) {
    Events::on('account.created', 'ma_on_account');
    Events::on('trade.created', 'ma_on_trade');
    Events::on('trade.updated', 'ma_on_trade');   // a batch fires one event per trading day: it can be an update
    Events::on('payout.recorded', 'ma_on_payout');
    Events::on('journal.saved', 'ma_on_journal');
}
