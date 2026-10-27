<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli' && realpath((string) ($_SERVER['SCRIPT_FILENAME'] ?? '')) === realpath(__FILE__)) { http_response_code(404); exit; }
/**
 * Sweep — the automatic emails go through Loops (loops.so): welcome, follow-ups, end of the Pro trial, win-back.
 * Sweep only sends signals, at the right moment and once: who the trader is now (the Loops contact) and what just
 * happened (an event). The emails themselves are written and switched on in Loops.
 *
 * Step 0: the client (server side only), its private config sweep-private/loops-config.php (template:
 * loops/loops-config.sample.php; no key = off, the app works exactly as before) and the contact, kept up to date: sign-up,
 * each return to the app (last visit, at most once an hour), profile, email, plan (Stripe, Admin), account deleted.
 * Contact properties: LOOPS_PROPS (created in Loops by the first run of loops/cron.php).
 *
 * Step 1: the events. In the app, in real time (this file): signedUp, profileCompleted, firstAccountAdded, firstPlanSaved, firstTradeLogged,
 * tradesMilestone (10th, 50th, 100th trade), firstPayoutLogged (once each), subscriptionStarted, subscriptionCanceled,
 * paymentFailed (Stripe webhook), referralRewarded. Once a day from 7:30 New York time (loops/cron.php): inactive7d,
 * inactive14d, inactive30d, proTrialDaysLeft (30, 10, 3), proTrialEnded.
 *
 * Rules:
 *  - Loops never blocks a trader: 3 s at most, the error goes to the PHP error log (« [Sweep loops] »), the request carries
 *    on. In the app the calls leave after the response (loops_later); in the crons, right away.
 *  - An event « once » leaves once per trader, even after a delete and a new add: it is claimed in email_events_log before
 *    it is sent (one statement: two requests at the same time cannot both claim it); a failed send gives the claim back,
 *    so the next occasion sends it. Trades count copies once and never sample data.
 *  - Every event carries the contact properties of the moment.
 *  - Nothing is sent before the first run of loops/cron.php (loops_init): it creates the contact properties in Loops and
 *    marks what existing traders have already done, so a trader with 300 trades never gets « first trade ».
 */

const LOOPS_PROPS = ['language' => 'string', 'plan' => 'string', 'isPaying' => 'boolean', 'isDiscordCrew' => 'boolean',
                     'proTrialEndsAt' => 'date', 'lastLoginAt' => 'date'];
const LOOPS_MILESTONES = [10, 50, 100];   // tradesMilestone
const LOOPS_INACTIVE = [3, 7, 14, 30];    // inactive3d, inactive7d, inactive14d, inactive30d: days without coming back (3: brief 02 part 10, the soft come-back)
const LOOPS_TRIAL_LEFT = [3, 10, 30];     // proTrialDaysLeft: days before the end of the Pro trial

function loops_pdo(): PDO { return db(); }   // api.php, the crons and the tests each define db()
function loops_q(string $sql, array $args = []): PDOStatement { $st = loops_pdo()->prepare($sql); $st->execute($args); return $st; }
function loops_now(): int { return isset($GLOBALS['SB_NOW']) ? (int) $GLOBALS['SB_NOW'] : time(); }   // a test date (loops/cron.php --now) moves billing too
function loops_setting(string $k): ?string { $v = loops_q('SELECT v FROM app_settings WHERE k = ?', [$k])->fetchColumn(); return $v === false ? null : (string) $v; }
function loops_save_setting(string $k, string $v): void { loops_q('DELETE FROM app_settings WHERE k = ?', [$k]); loops_q('INSERT INTO app_settings (k, v) VALUES (?, ?)', [$k, $v]); }

/* ───────────── config and client ───────────── */

/** The private config: SWEEP_LOOPS_CONFIG (tests), else sweep-private/loops-config.php next to the app folder. $set: tests only. */
function loops_cfg(?array $set = null): array
{
    static $c = null;
    if ($set === null && $c !== null) return $c;
    if ($set === null) {
        $set = [];
        foreach (array_filter([(string) getenv('SWEEP_LOOPS_CONFIG'), dirname(__DIR__, 2) . '/sweep-private/loops-config.php', dirname(__DIR__, 3) . '/sweep-private/loops-config.php']) as $p) {
            if (is_file($p)) { $set = (array) require $p; break; }
        }
    }
    $c = $set + ['api_key' => '', 'api_url' => 'https://app.loops.so/api/v1', 'timeout' => 3];
    $c['api_key'] = trim((string) $c['api_key']);
    loops_ready(true);
    return $c;
}
function loops_on(): bool { return loops_cfg()['api_key'] !== ''; }
/** Sending starts once the first run of loops/cron.php has prepared Loops (loops_since). $reset: after that run, and in tests. */
function loops_ready(bool $reset = false): bool
{
    static $r = null;
    if ($reset) { $r = null; return false; }
    if ($r !== null) return $r;
    if (!loops_on()) return $r = false;
    try { return $r = loops_setting('loops_since') !== null; } catch (Throwable $e) { return $r = false; }
}

/** One HTTP call to Loops: [status (0 = no answer), decoded body]. Never throws. */
function loops_http(string $method, string $path, ?array $body = null): array
{
    $c = loops_cfg();
    $t = max(1, (int) $c['timeout']);
    $url = rtrim((string) $c['api_url'], '/') . '/' . ltrim($path, '/');
    $head = ['Authorization: Bearer ' . $c['api_key'], 'Accept: application/json'];
    $data = $body === null ? null : (string) json_encode($body, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    if ($data !== null) $head[] = 'Content-Type: application/json';
    if (function_exists('curl_init')) {
        $ch = curl_init($url);
        curl_setopt_array($ch, [CURLOPT_CUSTOMREQUEST => $method, CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => $t, CURLOPT_CONNECTTIMEOUT => min(2, $t), CURLOPT_HTTPHEADER => $head]);
        if ($data !== null) curl_setopt($ch, CURLOPT_POSTFIELDS, $data);
        $raw = curl_exec($ch); $code = (int) curl_getinfo($ch, CURLINFO_RESPONSE_CODE);
        if ($raw === false) return [0, ['message' => curl_error($ch) ?: 'no answer']];
    } else {
        $raw = @file_get_contents($url, false, stream_context_create(['http' => ['method' => $method, 'header' => implode("\r\n", $head), 'content' => $data ?? '', 'timeout' => $t, 'ignore_errors' => true]]));
        if ($raw === false) return [0, ['message' => 'no answer']];
        $h = function_exists('http_get_last_response_headers') ? (array) http_get_last_response_headers() : [];
        $code = preg_match('#^HTTP/\S+ (\d{3})#', (string) ($h[0] ?? ''), $m) ? (int) $m[1] : 200;
    }
    $j = json_decode((string) $raw, true);
    return [$code, is_array($j) ? $j : ['message' => substr(trim(strip_tags((string) $raw)), 0, 160)]];
}
/** One call, true when Loops took it. A refusal or no answer is logged, never thrown. Crons wait and retry on « too many requests ». */
function loops_call(string $method, string $path, array $body, string $what): bool
{
    for ($try = 0; ; $try++) {
        [$code, $j] = loops_http($method, $path, $body);
        if ($code === 429 && PHP_SAPI === 'cli' && $try < 3) { usleep(1000000 * ($try + 1)); continue; }
        break;
    }
    if ($code >= 200 && $code < 300 && ($j['success'] ?? true) !== false) return true;
    $GLOBALS['LOOPS_ERROR'] = $what . ': ' . ($code ?: 'no answer') . ' ' . substr((string) ($j['message'] ?? ''), 0, 160);
    error_log('[Sweep loops] ' . $GLOBALS['LOOPS_ERROR']);
    return false;
}

/* ───────────── the contact ───────────── */

function loops_lang($l): string { $l = strtolower(substr((string) $l, 0, 2)); return in_array($l, ['en', 'fr', 'es'], true) ? $l : 'en'; }
/** Last visit: users.last_login (sign-in, and each return to the app at most once an hour), else the sign-up. */
function loops_last_seen(array $u): int { return (int) (strtotime((string) (($u['last_login'] ?? '') ?: ($u['created_at'] ?? ''))) ?: 0); }

/** plan (free / pro / elite), pays (Stripe), Discord crew (Elite for life, given in Admin), permanent access, end of the Pro trial. */
function loops_billing(string $uid, array $u): array
{
    $out = ['plan' => 'elite', 'paying' => false, 'crew' => false, 'permanent' => false, 'trial_end' => null, 'live' => false];   // billing off: nothing is limited
    if (!function_exists('billing_on') || !billing_on()) return $out;
    try {
        $pdo = loops_pdo(); sb_schema($pdo);
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
    } catch (Throwable $e) { error_log('[Sweep loops] plan of ' . $uid . ': ' . $e->getMessage()); }
    return $out;
}

/** The Loops contact of a trader right now: userId, email, names, then LOOPS_PROPS (dates in ms). Null without an email: nothing to send to. */
function loops_contact(string $uid): ?array
{
    $u = loops_q('SELECT id, email, first_name, last_name, lang, created_at, last_login FROM users WHERE id = ?', [$uid])->fetch(PDO::FETCH_ASSOC);
    if (!$u || trim((string) $u['email']) === '') return null;
    $b = loops_billing($uid, $u);
    $c = ['userId' => $uid, 'email' => trim((string) $u['email'])];
    foreach (['firstName' => 'first_name', 'lastName' => 'last_name'] as $k => $col) if (trim((string) $u[$col]) !== '') $c[$k] = trim((string) $u[$col]);
    $c += ['language' => loops_lang($u['lang'] ?? ''), 'plan' => $b['plan'], 'isPaying' => $b['paying'], 'isDiscordCrew' => $b['crew']];
    if ($b['trial_end']) $c['proTrialEndsAt'] = $b['trial_end'] * 1000;
    if ($seen = loops_last_seen($u)) $c['lastLoginAt'] = $seen * 1000;
    return $c;
}

/* ───────────── what was sent: email_events_log ───────────── */

function loops_schema(): void
{
    static $done = false; if ($done) return;
    $my = loops_pdo()->getAttribute(PDO::ATTR_DRIVER_NAME) === 'mysql';
    loops_pdo()->exec('CREATE TABLE IF NOT EXISTS email_events_log (user_id ' . ($my ? 'VARCHAR(120)' : 'TEXT') . ' NOT NULL, event_name ' . ($my ? 'VARCHAR(64)' : 'TEXT')
        . ' NOT NULL, sent_at INT NOT NULL)' . ($my ? ' DEFAULT CHARSET=utf8mb4' : ''));
    try { loops_pdo()->exec($my ? 'ALTER TABLE email_events_log ADD INDEX email_events_log_user (user_id, event_name)' : 'CREATE INDEX IF NOT EXISTS email_events_log_user ON email_events_log (user_id, event_name)'); } catch (Throwable $e) { /* exists */ }
    $done = true;
}
/** The events « once » already sent to a trader (tradesMilestone and proTrialDaysLeft carry their step: « tradesMilestone:10 »). */
function loops_done(string $uid): array { loops_schema(); return loops_q('SELECT DISTINCT event_name FROM email_events_log WHERE user_id = ?', [$uid])->fetchAll(PDO::FETCH_COLUMN); }
function loops_logged(string $uid, string $key, int $since = 0): bool { loops_schema(); return (bool) loops_q('SELECT 1 FROM email_events_log WHERE user_id = ? AND event_name = ? AND sent_at >= ?', [$uid, $key, $since])->fetchColumn(); }
/** Claims an event « once »: true when this call wrote the line (and so sends it). $since: only a line from then on counts (absences). */
function loops_claim(string $uid, string $key, int $at, int $since = 0): bool
{
    loops_schema();
    $mysql = loops_pdo()->getAttribute(PDO::ATTR_DRIVER_NAME) === 'mysql';
    try {
        return loops_q('INSERT INTO email_events_log (user_id, event_name, sent_at) SELECT ?, ?, ?' . ($mysql ? ' FROM DUAL' : '')
            . ' WHERE NOT EXISTS (SELECT 1 FROM email_events_log WHERE user_id = ? AND event_name = ? AND sent_at >= ?)', [$uid, $key, $at, $uid, $key, $since])->rowCount() === 1;
    } catch (Throwable $e) { error_log('[Sweep loops] claim ' . $key . ' ' . $uid . ': ' . $e->getMessage()); return false; }
}
function loops_unclaim(string $uid, string $key, int $at): void
{
    try { loops_q('DELETE FROM email_events_log WHERE user_id = ? AND event_name = ? AND sent_at = ?', [$uid, $key, $at]); }
    catch (Throwable $e) { error_log('[Sweep loops] unclaim ' . $key . ' ' . $uid . ': ' . $e->getMessage()); }
}

/* ───────────── sending ───────────── */

/** Sends an event now, with the contact of the moment. $props: the event's properties, or a Closure of the contact. */
function loops_send(string $uid, string $name, $props = []): bool
{
    $c = loops_contact($uid);
    if (!$c) return true;   // no email (the very first administrator): no contact, nothing to send
    $p = $props instanceof Closure ? $props($c) : $props;
    return loops_call('POST', 'events/send', $c + ['eventName' => $name] + ($p ? ['eventProperties' => $p] : []), $name . ' ' . $uid);
}
/** In the app: after the response, so the trader never waits for Loops. In the crons and tests: right away. */
function loops_later(string $key, callable $fn): void
{
    if (PHP_SAPI === 'cli') { $fn(); return; }
    if (!isset($GLOBALS['LOOPS_QUEUE'])) {
        $GLOBALS['LOOPS_QUEUE'] = [];
        register_shutdown_function(function (): void {
            $q = $GLOBALS['LOOPS_QUEUE']; $GLOBALS['LOOPS_QUEUE'] = [];
            if (!$q) return;
            if (function_exists('fastcgi_finish_request')) @fastcgi_finish_request(); elseif (function_exists('litespeed_finish_request')) @litespeed_finish_request();
            foreach ($q as $k => $fn) { try { $fn(); } catch (Throwable $e) { error_log('[Sweep loops] ' . $k . ': ' . $e->getMessage()); } }
        });
    }
    $GLOBALS['LOOPS_QUEUE'][$key] = $fn;
}
/** An event that can happen again (Stripe, referral). */
function loops_event(string $uid, string $name, $props = []): void
{
    static $n = 0;
    if (!loops_ready()) return;
    unset($GLOBALS['LOOPS_QUEUE']["sync:$uid"]);   // the event brings the contact
    loops_later("event:$uid:" . (++$n), fn() => loops_send($uid, $name, $props));
}
/** An event « once » ($key: its line in email_events_log, « tradesMilestone:10 »). True when claimed (it leaves after the response). */
function loops_once(string $uid, string $name, $props = [], ?string $key = null): bool
{
    static $n = 0;
    if (!loops_ready()) return false;
    $key = $key ?? $name; $at = loops_now();
    if (!loops_claim($uid, $key, $at)) return false;
    unset($GLOBALS['LOOPS_QUEUE']["sync:$uid"]);
    loops_later("event:$uid:o" . (++$n), function () use ($uid, $name, $props, $key, $at): void { if (!loops_send($uid, $name, $props)) loops_unclaim($uid, $key, $at); });
    return true;
}
/** The contact only (plan, last visit, name or email changed): skipped when an event of the same request already brings it. */
function loops_sync(string $uid): void
{
    if (!loops_ready()) return;
    foreach (array_keys($GLOBALS['LOOPS_QUEUE'] ?? []) as $k) if (strpos($k, "event:$uid:") === 0) return;
    loops_later("sync:$uid", function () use ($uid): void { if ($c = loops_contact($uid)) loops_call('PUT', 'contacts/update', $c, 'contact ' . $uid); });
}
/** The trader deleted their account (called before the users row goes): their Loops contact and their lines of email_events_log go too. */
function loops_forget(string $uid): void
{
    try { loops_schema(); loops_q('DELETE FROM email_events_log WHERE user_id = ?', [$uid]); } catch (Throwable $e) { error_log('[Sweep loops] forget ' . $uid . ': ' . $e->getMessage()); }
    if (!loops_on()) return;
    $em = trim((string) (loops_q('SELECT email FROM users WHERE id = ?', [$uid])->fetchColumn() ?: ''));
    foreach (array_keys($GLOBALS['LOOPS_QUEUE'] ?? []) as $k) if (strpos($k, "event:$uid:") === 0 || $k === "sync:$uid") unset($GLOBALS['LOOPS_QUEUE'][$k]);
    loops_later("forget:$uid", function () use ($uid, $em): void {
        [$code, $j] = loops_http('POST', 'contacts/delete', $em !== '' ? ['email' => $em] : ['userId' => $uid]);
        if ($code !== 200 && $code !== 404) error_log('[Sweep loops] delete contact ' . $uid . ': ' . ($code ?: 'no answer') . ' ' . substr((string) ($j['message'] ?? ''), 0, 160));
    });
}

/* ───────────── the app's events (part A) ───────────── */

/** Real trades of a trader: copies once (a trade copied on 3 accounts is one trade), never sample data. */
function loops_trade_count(string $uid): int
{
    $n = 0; $seen = [];
    foreach (loops_q("SELECT data FROM documents WHERE user_id = ? AND collection = 'trades'", [$uid])->fetchAll(PDO::FETCH_COLUMN) as $raw) {
        $d = json_decode((string) $raw, true);
        if (!is_array($d) || !empty($d['demo'])) continue;
        $g = (string) ($d['copy_group'] ?? '');
        if ($g !== '') { if (isset($seen[$g])) continue; $seen[$g] = true; }
        $n++;
    }
    return $n;
}
/** Has the trader a real document of this collection (sample data never counts)? */
function loops_has(string $uid, string $col, ?callable $keep = null): bool
{
    foreach (loops_q('SELECT data FROM documents WHERE user_id = ? AND collection = ?', [$uid, $col])->fetchAll(PDO::FETCH_COLUMN) as $raw) {
        $d = json_decode((string) $raw, true);
        if (is_array($d) && empty($d['demo']) && (!$keep || $keep($d))) return true;
    }
    return false;
}
/** firstAccountAdded's propFirm: the account's firm in Sweep, else its preset's firm in the catalog (the firm may arrive a moment after the account), else ''. */
function loops_firm_of(string $uid, array $a): string
{
    $fid = (string) ($a['firm_id'] ?? '');
    if ($fid !== '') {
        $raw = loops_q("SELECT data FROM documents WHERE user_id = ? AND collection = 'firms' AND id = ?", [$uid, $fid])->fetchColumn();
        $name = $raw ? trim((string) ((json_decode((string) $raw, true) ?: [])['name'] ?? '')) : '';
        if ($name !== '') return $name;
    }
    $pid = explode('|', (string) ($a['preset'] ?? ''))[0];
    if ($pid !== '') foreach ((array) ((json_decode((string) @file_get_contents(dirname(__DIR__) . '/presets/seed.json'), true) ?: [])['firms'] ?? []) as $f)
        if (($f['id'] ?? '') === $pid) return (string) ($f['name'] ?? '');
    return '';
}
/** The first account: claimed and sent after the response, when the firm (saved by its own request at the same time) is there. */
function loops_on_account(array $p): void
{
    $uid = (string) ($p['uid'] ?? ''); $a = (array) ($p['doc'] ?? []);
    if ($uid === '' || !empty($a['demo']) || !loops_ready() || in_array('firstAccountAdded', loops_done($uid), true)) return;
    unset($GLOBALS['LOOPS_QUEUE']["sync:$uid"]);   // the event brings the contact
    loops_later("event:$uid:account", function () use ($uid, $a): void {
        $firm = loops_firm_of($uid, $a);
        if ($firm === '' && !empty($a['firm_id']) && PHP_SAPI !== 'cli') { usleep(1000000); $firm = loops_firm_of($uid, $a); }   // its firm a moment late
        $at = loops_now();
        if (loops_claim($uid, 'firstAccountAdded', $at) && !loops_send($uid, 'firstAccountAdded', ['propFirm' => $firm])) loops_unclaim($uid, 'firstAccountAdded', $at);
    });
}
/** A trade saved: the first one, then the 10th, 50th and 100th. Several steps passed in one go (an import): only the highest leaves. */
function loops_on_trade(array $p): void
{
    $uid = (string) ($p['uid'] ?? '');
    if ($uid === '' || !empty(($p['doc'] ?? [])['demo']) || !loops_ready()) return;
    $left = array_diff(array_merge(['firstTradeLogged'], array_map(fn($m) => "tradesMilestone:$m", LOOPS_MILESTONES)), loops_done($uid));
    if (!$left) return;   // after the 100th trade: one small query per save
    $n = loops_trade_count($uid);
    if ($n >= 1 && in_array('firstTradeLogged', $left, true)) loops_once($uid, 'firstTradeLogged');
    $reached = array_values(array_filter(LOOPS_MILESTONES, fn($m) => $n >= $m && in_array("tradesMilestone:$m", $left, true)));
    if (!$reached) return;
    $top = max($reached);
    foreach ($reached as $m) if ($m !== $top) loops_claim($uid, "tradesMilestone:$m", loops_now());   // passed: never sent later
    loops_once($uid, 'tradesMilestone', ['milestone' => $top], "tradesMilestone:$top");
}
/** (27 Oct., brief activation step E) the first plan saved (a bias in the journal's pre-market): once. A trader who had plans before
 *  this event existed is marked, never sent « first plan » for his tenth one. */
function loops_on_journal(array $p): void
{
    $uid = (string) ($p['uid'] ?? ''); $d = (array) ($p['doc'] ?? []);
    if ($uid === '' || !empty($d['demo']) || empty(($d['pre'] ?? [])['bias']) || !loops_ready() || in_array('firstPlanSaved', loops_done($uid), true)) return;
    $n = 0;
    foreach (loops_q("SELECT data FROM documents WHERE user_id = ? AND collection = 'journals'", [$uid])->fetchAll(PDO::FETCH_COLUMN) as $raw) {
        $j = json_decode((string) $raw, true); if (is_array($j) && empty($j['demo']) && !empty(($j['pre'] ?? [])['bias'])) $n++;
    }
    if ($n > 1) { loops_claim($uid, 'firstPlanSaved', loops_now()); return; }
    loops_once($uid, 'firstPlanSaved');
}
function loops_on_payout(array $p): void
{
    $uid = (string) ($p['uid'] ?? ''); $d = (array) ($p['doc'] ?? []);
    if ($uid === '' || !empty($d['demo']) || !empty($d['estimated'])) return;   // a payout the trader entered, not the estimate of « Your real net »
    loops_once($uid, 'firstPayoutLogged');
}

/**
 * After a verified Stripe event (billing/billing-stripe.php, sb_handle_event), the trader known:
 *   invoice.paid, first invoice of a new subscription      → subscriptionStarted (plan, interval)
 *   invoice.payment_failed                                  → paymentFailed (plan)
 *   customer.subscription.updated, a cancellation just asked (it ends with the period) → subscriptionCanceled (plan)
 *   customer.subscription.deleted, no cancellation asked before (stopped right away)    → subscriptionCanceled (plan)
 *   any other change of a subscription, a renewal          → the contact (plan, isPaying)
 * $before: the event's previous_attributes (what an update changed, with the old values).
 */
function loops_stripe(PDO $pdo, string $type, array $obj, array $before, string $uid): void
{
    if (!loops_ready() || $uid === '') return;
    $planOf = function ($subId) use ($pdo): array {
        $r = is_string($subId) && $subId !== '' ? sb_q($pdo, 'SELECT plan, billing_interval FROM billing_subs WHERE id = ?', [$subId])->fetch(PDO::FETCH_ASSOC) : null;
        return [(string) ($r['plan'] ?? ''), (string) ($r['billing_interval'] ?? '')];
    };
    if ($type === 'invoice.paid' || $type === 'invoice.payment_failed') {
        $sub = $obj['subscription'] ?? ($obj['parent']['subscription_details']['subscription'] ?? null);
        [$plan, $interval] = $planOf(is_array($sub) ? ($sub['id'] ?? null) : $sub);
        if ($type === 'invoice.payment_failed') loops_event($uid, 'paymentFailed', ['plan' => $plan]);
        elseif (($obj['billing_reason'] ?? '') === 'subscription_create') loops_event($uid, 'subscriptionStarted', ['plan' => $plan, 'interval' => $interval]);
        else loops_sync($uid);
        return;
    }
    if (strpos($type, 'customer.subscription.') !== 0) return;
    [$plan] = $planOf($obj['id'] ?? null);
    $asked = fn(array $s): bool => !empty($s['cancel_at_period_end']) || !empty($s['cancel_at']);
    if (($type === 'customer.subscription.updated' && $asked($obj) && !$asked(array_merge($obj, $before)))
        || ($type === 'customer.subscription.deleted' && !$asked($obj))) { loops_event($uid, 'subscriptionCanceled', ['plan' => $plan]); return; }
    loops_sync($uid);
}

/* ───────────── first run and the daily events (part B, loops/cron.php) ───────────── */

/**
 * First run (loops/cron.php): the contact properties in Loops (LOOPS_PROPS, the missing ones), then what existing traders
 * have already done is marked in email_events_log without sending (sign-up, profile, first account, first trade, milestones
 * reached, first payout); then the app starts sending. ['error' => null|why, 'created' => [...], 'marked' => n].
 */
function loops_init(): array
{
    [$code, $have] = loops_http('GET', 'contacts/properties?list=custom');
    if ($code !== 200) return ['error' => 'contact properties: ' . ($code ?: 'no answer') . ' ' . substr((string) ($have['message'] ?? ''), 0, 160), 'created' => [], 'marked' => 0];
    $keys = array_column(array_filter($have, 'is_array'), 'key'); $created = [];
    foreach (LOOPS_PROPS as $name => $type) if (!in_array($name, $keys, true)) {
        if (!loops_call('POST', 'contacts/properties', ['name' => $name, 'type' => $type], "property $name")) return ['error' => $GLOBALS['LOOPS_ERROR'], 'created' => $created, 'marked' => 0];
        $created[] = $name;
    }
    $now = loops_now(); $marked = 0;
    foreach (loops_q('SELECT id, first_name FROM users')->fetchAll(PDO::FETCH_ASSOC) as $u) {
        $uid = (string) $u['id']; $n = loops_trade_count($uid);
        $done = ['signedUp'];
        if (trim((string) $u['first_name']) !== '') $done[] = 'profileCompleted';
        if (loops_has($uid, 'accounts')) $done[] = 'firstAccountAdded';
        if ($n >= 1) $done[] = 'firstTradeLogged';
        foreach (LOOPS_MILESTONES as $m) if ($n >= $m) $done[] = "tradesMilestone:$m";
        if (loops_has($uid, 'payouts', fn($d) => empty($d['estimated']))) $done[] = 'firstPayoutLogged';
        if (loops_has($uid, 'journals', fn($d) => !empty(($d['pre'] ?? [])['bias']))) $done[] = 'firstPlanSaved';
        foreach ($done as $k) if (loops_claim($uid, $k, $now)) $marked++;
    }
    loops_save_setting('loops_since', (string) $now);
    loops_ready(true);
    return ['error' => null, 'created' => $created, 'marked' => $marked];
}

/**
 * The daily steps of a trader that came due in ($from, $now]: [line in email_events_log, event, properties, since].
 * One step of each kind at most, the latest (several come due together only after the server missed days):
 *  - absence: 7, 14 and 30 days after the last visit; « since » = that visit, so a new absence starts over;
 *  - Pro trial: 30, 10 and 3 days before its end, then its end; never for the Discord crew (or another access for life)
 *    nor a trader who pays. $b: loops_billing().
 */
function loops_daily_due(array $u, array $b, int $from, int $now): array
{
    $out = [];
    $seen = loops_last_seen($u);
    if ($seen) foreach (array_reverse(LOOPS_INACTIVE) as $d) {
        $due = $seen + $d * 86400;
        if ($due > $from && $due <= $now) { $out[] = ["inactive{$d}d", "inactive{$d}d", [], $seen]; break; }
    }
    if ($b['live'] && $b['trial_end'] && !$b['paying'] && !$b['crew'] && !$b['permanent']) {
        $end = (int) $b['trial_end'];
        $steps = [['proTrialEnded', 'proTrialEnded', [], $end]];
        foreach (LOOPS_TRIAL_LEFT as $d) $steps[] = ["proTrialDaysLeft:$d", 'proTrialDaysLeft', ['daysLeft' => $d], $end - $d * 86400];
        foreach ($steps as [$key, $name, $props, $due]) if ($due > $from && $due <= $now) { $out[] = [$key, $name, $props, 0]; break; }
    }
    return $out;
}

/**
 * The daily run over these traders (loops/cron.php): each step due in ($from, $now] is claimed, then sent; a refused one
 * gives its claim back (tried again at the next run). $dry: only says what would leave. $say: one line per step.
 * ['sent' => [event => n], 'failed' => n, 'error' => last refusal].
 */
function loops_daily_run(array $ids, int $from, int $now, bool $dry = false, ?callable $say = null): array
{
    $say = $say ?? function (string $s): void {};
    $sent = []; $failed = 0; $err = '';
    foreach ($ids as $uid) {
        $uid = (string) $uid;
        $u = loops_q('SELECT id, email, created_at, last_login, disabled FROM users WHERE id = ?', [$uid])->fetch(PDO::FETCH_ASSOC);
        if (!$u || (int) $u['disabled'] === 1 || trim((string) $u['email']) === '') continue;
        try {
            foreach (loops_daily_due($u, loops_billing($uid, $u), $from, $now) as [$key, $name, $props, $since]) {
                $what = $name . ($props ? ' ' . json_encode($props) : '') . " → $uid";
                if ($dry) { $say((loops_logged($uid, $key, $since) ? 'already sent: ' : 'would send: ') . $what); continue; }
                if (!loops_claim($uid, $key, $now, $since)) { $say("already sent: $what"); continue; }
                if (loops_send($uid, $name, $props)) { $sent[$name] = ($sent[$name] ?? 0) + 1; $say("sent: $what"); }
                else { loops_unclaim($uid, $key, $now); $failed++; $err = (string) ($GLOBALS['LOOPS_ERROR'] ?? ''); $say("NOT sent: $what ($err)"); }
                if (PHP_SAPI === 'cli' && !getenv('SWEEP_TEST_DB')) usleep(120000);   // Loops takes 10 requests a second
            }
        } catch (Throwable $e) { $failed++; $err = $uid . ': ' . $e->getMessage(); error_log('[Sweep loops] daily ' . $err); }
    }
    return ['sent' => $sent, 'failed' => $failed, 'error' => $err];
}

if (class_exists('Events', false)) {
    Events::on('account.created', 'loops_on_account');
    Events::on('trade.created', 'loops_on_trade');
    Events::on('trade.updated', 'loops_on_trade');   // a batch fires one event per trading day: it can be an update
    Events::on('payout.recorded', 'loops_on_payout');
    Events::on('journal.saved', 'loops_on_journal');
}
