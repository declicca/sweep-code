<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli' && realpath((string) ($_SERVER['SCRIPT_FILENAME'] ?? '')) === realpath(__FILE__)) { http_response_code(404); exit; }
/**
 * Sweep — one message, the best channel (brief « Notifications », 5 Nov. 2026). Each automatic message has three outputs: the
 * phone (web push, push/web-push.php), the email (mail/mail-auto.php, same key) and, for an account alert, the bell.
 *  - The phone first when the trader has a device; the email 24 h later, only when the notification was not opened and the
 *    trader did not come back (ml_run asks pa_hold). Without a device, or when the phone cannot take it: the email at once.
 *  - The account and its money: both at once. Long questions (a note from 0 to 10): the email only.
 * Guard rails (the push only; the email keeps its own rules):
 *  - 2 a day at most, with the bell's reminders (notify/notify.php), and 5 a week (account alerts aside);
 *  - quiet hours on the phone's own clock (21:00 to 7:00), never during the session (9:30 to 16:00 ET) except account alerts;
 *  - fatigue: the last 4 of a group ignored → that group 1 a week at most until the trader opens one;
 *  - 30 days without coming back: nothing more (the 30-day email is the last word); everything starts again on return.
 * Each message starts off: Admin › Emails shows its text in EN / FR / ES, switches it on and gives its numbers.
 * Table push_msgs: one line per notification (queued, sent, skipped), its open (the service worker calls api/p/o/<token>),
 * and the email it relays (mail_qid). Sent by mail/send-cron.php (every minute): no new cron line.
 */

const PA_RELAY = 86400;          // the email waits 24 h after the notification
const PA_WEEK = 5;               // automatic notifications in 7 days (account alerts aside)
const PA_DAY_MAX = 2;            // a day, with the bell's reminders
const PA_TIRED = 4;              // ignored in a row → 1 a week for that group
const PA_ABSENT = 30 * 86400;    // no notification after 30 days away
const PA_NEWS_GAP = 28 * 86400;  // Sweep's news: once a month at most
const PA_NY = 'America/New_York';
const PA_GROUPS = ['routine', 'accounts', 'progress', 'news'];

function pa_pdo(): PDO { return db(); }
function pa_q(string $sql, array $a = []): PDOStatement { pa_schema(); $st = pa_pdo()->prepare($sql); $st->execute($a); return $st; }
function pa_now(): int { $e = getenv('SWEEP_PUSH_NOW'); return $e !== false && $e !== '' ? (int) $e : (isset($GLOBALS['SB_NOW']) ? (int) $GLOBALS['SB_NOW'] : time()); }
/** the catalog (push/push-auto-texts.php): channel, group, link, starting text */
function pa_catalog(): array { static $c = null; return $c ?? ($c = (array) require __DIR__ . '/push-auto-texts.php'); }
function pa_def(string $key): ?array { return pa_catalog()[$key] ?? null; }

function pa_schema(): void
{
    static $done = false; if ($done) return; $done = true;
    $pdo = pa_pdo(); $my = $pdo->getAttribute(PDO::ATTR_DRIVER_NAME) === 'mysql';
    $auto = $my ? 'INTEGER PRIMARY KEY AUTO_INCREMENT' : 'INTEGER PRIMARY KEY AUTOINCREMENT'; $K = $my ? 'VARCHAR(120)' : 'TEXT'; $cs = $my ? ' DEFAULT CHARSET=utf8mb4' : '';
    $pdo->exec("CREATE TABLE IF NOT EXISTS push_auto (auto VARCHAR(40) NOT NULL PRIMARY KEY, enabled INT NOT NULL DEFAULT 0, content_json TEXT NULL, updated_at INT NOT NULL)$cs");
    $pdo->exec("CREATE TABLE IF NOT EXISTS push_msgs (id $auto, user_id $K NOT NULL, auto VARCHAR(40) NOT NULL, grp VARCHAR(12) NOT NULL, counted INT NOT NULL DEFAULT 1,
        vars_json TEXT NULL, url VARCHAR(200) NULL, token VARCHAR(24) NOT NULL, state VARCHAR(10) NOT NULL, due_at INT NOT NULL, tries INT NOT NULL DEFAULT 0,
        sent_at INT NULL, opened_at INT NULL, devices INT NOT NULL DEFAULT 0, mail_qid INT NULL, dedupe VARCHAR(120) NULL, why VARCHAR(16) NULL, created_at INT NOT NULL)$cs");
    foreach ($my ? ['ALTER TABLE push_msgs ADD UNIQUE KEY uq_pm_token (token)', 'ALTER TABLE push_msgs ADD KEY ix_pm_due (state, due_at)', 'ALTER TABLE push_msgs ADD KEY ix_pm_user (user_id, sent_at)', 'ALTER TABLE push_msgs ADD KEY ix_pm_mail (mail_qid)', 'ALTER TABLE push_msgs ADD KEY ix_pm_auto (auto, created_at)']
                 : ['CREATE UNIQUE INDEX IF NOT EXISTS uq_pm_token ON push_msgs (token)', 'CREATE INDEX IF NOT EXISTS ix_pm_due ON push_msgs (state, due_at)', 'CREATE INDEX IF NOT EXISTS ix_pm_user ON push_msgs (user_id, sent_at)', 'CREATE INDEX IF NOT EXISTS ix_pm_mail ON push_msgs (mail_qid)', 'CREATE INDEX IF NOT EXISTS ix_pm_auto ON push_msgs (auto, created_at)'] as $sql) {
        try { $pdo->exec($sql); } catch (Throwable $e) { /* exists */ }
    }
}

/* ───────────── the texts and their switch (Admin › Emails) ───────────── */

/** a message's state: on (off until Mateo switches it on) and its text per language (Admin's, else the catalog's) */
function pa_setting(string $key): array
{
    $d = pa_def($key) ?? ['text' => []];
    $r = pa_q('SELECT enabled, content_json FROM push_auto WHERE auto = ?', [$key])->fetch(PDO::FETCH_ASSOC);
    $saved = $r ? (json_decode((string) $r['content_json'], true) ?: []) : [];
    $text = [];
    foreach (['en', 'fr', 'es'] as $l) {
        $t = $saved[$l] ?? $d['text'][$l] ?? ['', ''];
        $text[$l] = [mb_substr(trim((string) ($t[0] ?? '')), 0, 80), mb_substr(trim((string) ($t[1] ?? '')), 0, 160)];
    }
    return ['on' => $r ? (int) $r['enabled'] === 1 : false, 'text' => $text];
}
function pa_save(string $key, array $in): array
{
    if (!pa_def($key)) return ['error' => 'not_found'];
    $cur = pa_setting($key);
    $on = array_key_exists('on', $in) ? (bool) $in['on'] : $cur['on'];
    $text = $cur['text'];
    if (isset($in['text']) && is_array($in['text'])) foreach (['en', 'fr', 'es'] as $l) if (isset($in['text'][$l]) && is_array($in['text'][$l]))
        $text[$l] = [mb_substr(trim((string) ($in['text'][$l][0] ?? '')), 0, 80), mb_substr(trim((string) ($in['text'][$l][1] ?? '')), 0, 160)];
    if ($on && $key !== 'news' && ($text['en'][0] === '' || $text['en'][1] === '')) return ['error' => 'text'];   // never on without an English title and line
    $j = json_encode($text, JSON_UNESCAPED_UNICODE); $t = pa_now();
    if (pa_q('UPDATE push_auto SET enabled = ?, content_json = ?, updated_at = ? WHERE auto = ?', [$on ? 1 : 0, $j, $t, $key])->rowCount() === 0
        && !pa_q('SELECT 1 FROM push_auto WHERE auto = ?', [$key])->fetchColumn())
        pa_q('INSERT INTO push_auto (auto, enabled, content_json, updated_at) VALUES (?, ?, ?, ?)', [$key, $on ? 1 : 0, $j, $t]);
    return ['ok' => true, 'on' => $on, 'text' => $text];
}
/** [title, line] of a message in a language, its values filled ({account}, {milestone}…); an empty language: English */
function pa_text(array $setting, string $lang, array $vars): array
{
    $t = $setting['text'][$lang] ?? ['', ''];
    if ($t[0] === '' || $t[1] === '') $t = $setting['text']['en'];
    $map = []; foreach ($vars as $k => $v) if (is_scalar($v)) $map['{' . $k . '}'] = (string) $v;
    return [strtr($t[0], $map), strtr($t[1], $map)];
}

/* ───────────── who can receive it, and when ───────────── */

/** the trader is in the app right now: his own signed-in request (a trade typed, a plan saved; api.php sets $UID), not the
 *  add-on's (api/sync/push, no session) nor a scheduled task */
function pa_in_app(string $uid): bool
{
    return isset($GLOBALS['UID']) && (string) $GLOBALS['UID'] === $uid;
}
function pa_last_seen(string $uid): int
{
    $u = pa_q('SELECT last_login, created_at FROM users WHERE id = ?', [$uid])->fetch(PDO::FETCH_ASSOC);
    return $u ? (int) (strtotime((string) (($u['last_login'] ?? '') ?: ($u['created_at'] ?? ''))) ?: 0) : 0;
}
/** a device that can receive it: push keys on the server, a device, the group switched on, not 30 days away (except an alert) */
function pa_reachable(string $uid, array $def): bool
{
    if (!function_exists('wp_config') || !wp_config() || !wp_devices(pa_pdo(), $uid)) return false;
    if (empty(wp_groups(wp_prefs(pa_pdo(), $uid))[$def['group']])) return false;
    return $def['ch'] === 'alert' || pa_last_seen($uid) >= pa_now() - PA_ABSENT;
}
/** the zones of the trader's devices (quiet hours on each phone's clock), New York for a device without one */
function pa_tzs(string $uid): array
{
    $out = [];
    foreach (pa_q('SELECT tz FROM push_subscriptions WHERE user_id = ?', [$uid])->fetchAll(PDO::FETCH_COLUMN) as $tz) $out[wp_tz($tz !== null ? (string) $tz : null) ?? PA_NY] = true;
    return $out ? array_keys($out) : [PA_NY];
}
/** the first slot on any of the trader's phones (the others, still at night then, are skipped when it is sent) */
function pa_slot_of(string $uid, int $t, bool $alert): int
{
    return min(array_map(fn($tz) => pa_slot($tz, $t, $alert), pa_tzs($uid)));
}
/**
 * The first moment from $t when this notification may leave: outside the phone's quiet hours (21:00 to 7:00 on its clock),
 * and, except an account alert, outside the session (9:30 to 16:00 ET, Monday to Friday).
 */
function pa_slot(string $tz, int $t, bool $alert): int
{
    for ($i = 0; $i < 4; $i++) {
        $l = (new DateTimeImmutable('@' . $t))->setTimezone(new DateTimeZone($tz)); $h = (int) $l->format('G');
        if ($h >= WP_QUIET[0]) { $t = (new DateTimeImmutable($l->modify('+1 day')->format('Y-m-d') . ' 07:00', new DateTimeZone($tz)))->getTimestamp(); continue; }
        if ($h < WP_QUIET[1]) { $t = (new DateTimeImmutable($l->format('Y-m-d') . ' 07:00', new DateTimeZone($tz)))->getTimestamp(); continue; }
        if ($alert) return $t;
        $ny = (new DateTimeImmutable('@' . $t))->setTimezone(new DateTimeZone(PA_NY)); $hm = $ny->format('H:i');
        if ((int) $ny->format('N') <= 5 && $hm >= '09:30' && $hm < '16:00') { $t = (new DateTimeImmutable($ny->format('Y-m-d') . ' 16:00', new DateTimeZone(PA_NY)))->getTimestamp(); continue; }
        return $t;
    }
    return $t;
}

/* ───────────── queueing ───────────── */

/**
 * One notification of a message in the queue (sent by pa_run within the minute, or at its slot). Null when it cannot reach
 * the trader (off, no device, group off, away, already sent for this $dedupe). $id: the account of an alert ({id} in its link).
 */
function pa_queue(string $uid, string $key, array $vars = [], ?string $dedupe = null): ?int
{
    try {
        $def = pa_def($key); if (!$def || !pa_setting($key)['on'] || !pa_reachable($uid, $def)) return null;
        if ($dedupe !== null && pa_q('SELECT 1 FROM push_msgs WHERE user_id = ? AND dedupe = ?', [$uid, $dedupe])->fetchColumn()) return null;
        $now = pa_now(); $alert = $def['ch'] === 'alert';
        $map = ['{id}' => rawurlencode((string) ($vars['id'] ?? ''))]; foreach ($vars as $k => $v) if (is_scalar($v) && $k !== 'id') $map['{' . $k . '}'] = (string) $v;
        $url = preg_replace('~^https?://[^/#]+/?~', '', strtr((string) $def['url'], $map));   // an in-app link (a value can be a full address: featureDiscover)
        if ($url === '' || $url[0] !== '#') $url = '#dashboard';
        pa_q("INSERT INTO push_msgs (user_id, auto, grp, counted, vars_json, url, token, state, due_at, dedupe, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, 'queued', ?, ?, ?)",
            [$uid, $key, $def['group'], $alert ? 0 : 1, $vars ? json_encode(array_filter($vars, 'is_scalar'), JSON_UNESCAPED_UNICODE) : null, $url, bin2hex(random_bytes(12)), pa_slot_of($uid, $now, $alert), $dedupe, $now]);
        return (int) pa_pdo()->lastInsertId();
    } catch (Throwable $e) { error_log('[Sweep push auto] ' . $key . ' ' . $uid . ': ' . $e->getMessage()); return null; }
}
/**
 * mail/mail-auto.php, before an automatic email is queued: its notification first. Returns the email's delay in seconds
 * (0: at once) and the notification's id to link to the email; ['skip' => true]: no email at all (never: the email stays the
 * relay; kept for the channels to come).
 */
function pa_dispatch(string $uid, string $key, array $vars): array
{
    $def = pa_def($key);
    if (!$def || !in_array($def['ch'], ['push', 'push_away', 'both'], true)) return ['delay' => 0, 'pid' => null];
    if ($def['ch'] === 'push_away' && pa_in_app($uid)) return ['delay' => 0, 'pid' => null];   // he is in the app: the email as before
    $pid = pa_queue($uid, $key, $vars);
    if ($pid === null) return ['delay' => 0, 'pid' => null];
    if ($def['ch'] === 'both') return ['delay' => 0, 'pid' => $pid];
    $due = (int) pa_q('SELECT due_at FROM push_msgs WHERE id = ?', [$pid])->fetchColumn();
    return ['delay' => max(0, $due - pa_now()) + PA_RELAY, 'pid' => $pid];
}
/** the email that relays a notification (its line of mail_queue) */
function pa_link(int $pid, int $qid): void
{
    try { pa_q('UPDATE push_msgs SET mail_qid = ? WHERE id = ?', [$qid, $pid]); } catch (Throwable $e) { error_log('[Sweep push auto] link: ' . $e->getMessage()); }
}
/** a notification that did not leave: its email goes now (instead of 24 h later) */
function pa_release(array $m, string $why): void
{
    pa_q("UPDATE push_msgs SET state = 'skipped', why = ? WHERE id = ?", [$why, $m['id']]);
    if ($m['mail_qid'] !== null) pa_q("UPDATE mail_queue SET next_at = ? WHERE id = ? AND state = 'queued'", [pa_now(), (int) $m['mail_qid']]);
}

/**
 * mail/mail-core.php ml_run, for each email about to leave: null = send it; 'hold' = not needed (its notification was opened,
 * or the trader came back after it); an int = not yet (its notification still waits for its slot: the email waits 24 h after).
 */
function pa_hold(array $q)
{
    try {
        $m = pa_q('SELECT * FROM push_msgs WHERE mail_qid = ? ORDER BY id DESC LIMIT 1', [(int) $q['id']])->fetch(PDO::FETCH_ASSOC);
        if (!$m || (pa_def((string) $m['auto'])['ch'] ?? 'both') === 'both') return null;
        if ($m['state'] === 'queued') return (int) $m['due_at'] + PA_RELAY;
        if ($m['state'] !== 'sent') return null;
        if ($m['opened_at'] !== null) return 'hold';
        $u = pa_q('SELECT last_login FROM users WHERE id = ?', [(string) $m['user_id']])->fetchColumn();
        return $u && (int) strtotime((string) $u) > (int) $m['sent_at'] ? 'hold' : null;
    } catch (Throwable $e) { error_log('[Sweep push auto] hold: ' . $e->getMessage()); return null; }
}

/* ───────────── sending (mail/send-cron.php, every minute) ───────────── */

/** why a counted notification cannot leave now: 'week' (5 in 7 days), 'tired' (its group ignored), 'day' (2 today), or null */
function pa_limit(array $m, int $now): ?string
{
    $uid = (string) $m['user_id'];
    if ((int) pa_q("SELECT COUNT(*) FROM push_msgs WHERE user_id = ? AND state = 'sent' AND counted = 1 AND sent_at > ?", [$uid, $now - 7 * 86400])->fetchColumn() >= PA_WEEK) return 'week';
    $last = pa_q("SELECT opened_at, sent_at FROM push_msgs WHERE user_id = ? AND grp = ? AND state = 'sent' ORDER BY sent_at DESC LIMIT " . PA_TIRED, [$uid, $m['grp']])->fetchAll(PDO::FETCH_ASSOC);
    if (count($last) === PA_TIRED && !array_filter($last, fn($r) => $r['opened_at'] !== null) && (int) $last[0]['sent_at'] > $now - 7 * 86400) return 'tired';
    $from = (new DateTimeImmutable('@' . $now))->setTimezone(new DateTimeZone(PA_NY))->setTime(0, 0)->getTimestamp();
    $bell = class_exists('Notify') ? Notify::alertsToday($uid) : 0;
    if ($bell + (int) pa_q("SELECT COUNT(*) FROM push_msgs WHERE user_id = ? AND state = 'sent' AND counted = 1 AND sent_at >= ?", [$uid, $from])->fetchColumn() >= PA_DAY_MAX) return 'day';
    return null;
}
/** one notification to the trader's devices (each in its language, none in its quiet hours); an alert also in the bell */
function pa_send(array $m, int $now): int
{
    $uid = (string) $m['user_id']; $key = (string) $m['auto']; $def = pa_def($key);
    $set = pa_setting($key); $vars = (array) (json_decode((string) ($m['vars_json'] ?? ''), true) ?: []);
    $alert = $def['ch'] === 'alert';
    if ($alert && class_exists('Notify')) {   // the bell (prop firm alerts: neither capped nor counted), in the trader's language
        $p = []; foreach (['en', 'fr', 'es'] as $l) [$p['t_' . $l], $p['b_' . $l]] = pa_text($set, $l, $vars);
        $p['t'] = $p['t_en']; $p['b'] = $p['b_en'];
        Notify::send($uid, 'pa_alert', $p, ['dedupe_key' => 'pa:' . ($m['dedupe'] ?? $m['id']), 'action_url' => (string) $m['url'], 'icon' => (string) ($def['icon'] ?? 'star'), 'category' => 'prop_alerts']);
    }
    $cfg = wp_config(); if (!$cfg) return 0;
    $n = 0;
    foreach (pa_q('SELECT * FROM push_subscriptions WHERE user_id = ?', [$uid])->fetchAll(PDO::FETCH_ASSOC) as $s) {
        if (wp_quiet($s['tz'] ?? null, $now)) continue;
        [$title, $body] = pa_text($set, in_array($s['lang'], ['en', 'fr', 'es'], true) ? $s['lang'] : 'en', $vars);
        if ($title === '') continue;
        if (wp_deliver(pa_pdo(), $s, ['title' => $title, 'body' => $body, 'url' => (string) $m['url'], 'tag' => 'sweep-' . $key, 'track' => '/api/p/o/' . $m['token']], $key, $cfg)) $n++;
    }
    return $n;
}
/** every notification due: checked again (still on, still reachable, the caps), sent, or held for later, or skipped (its email then goes) */
function pa_run(?int $now = null): array
{
    $now = $now ?? pa_now(); $out = ['sent' => 0, 'skipped' => 0, 'later' => 0];
    foreach (pa_q("SELECT * FROM push_msgs WHERE state = 'queued' AND due_at <= ? ORDER BY due_at, id LIMIT 200", [$now])->fetchAll(PDO::FETCH_ASSOC) as $m) {
        try {
            $def = pa_def((string) $m['auto']); $uid = (string) $m['user_id'];
            if (!$def || ($m['auto'] !== 'news' && !pa_setting((string) $m['auto'])['on'])) { pa_release($m, 'off'); $out['skipped']++; continue; }   // (the news: sent by hand, its switch already back off)
            if (!pa_reachable($uid, $def)) { pa_release($m, 'gone'); $out['skipped']++; continue; }
            if ((int) $m['counted'] === 1 && ($why = pa_limit($m, $now)) !== null) {
                if ($why === 'day' && (int) $m['tries'] < 2) {   // 2 today already: tomorrow, at its slot (twice at most)
                    $next = pa_slot_of($uid, (new DateTimeImmutable('@' . $now))->setTimezone(new DateTimeZone(PA_NY))->modify('+1 day')->setTime(10, 0)->getTimestamp(), false);
                    pa_q('UPDATE push_msgs SET due_at = ?, tries = tries + 1 WHERE id = ?', [$next, $m['id']]); $out['later']++; continue;
                }
                pa_release($m, $why); $out['skipped']++; continue;
            }
            $slot = pa_slot_of($uid, $now, $def['ch'] === 'alert');
            if ($slot > $now) { pa_q('UPDATE push_msgs SET due_at = ? WHERE id = ?', [$slot, $m['id']]); $out['later']++; continue; }   // a device moved to night meanwhile
            if (pa_q("UPDATE push_msgs SET state = 'sending' WHERE id = ? AND state = 'queued'", [$m['id']])->rowCount() !== 1) continue;
            $n = pa_send($m, $now);
            if ($n > 0) { pa_q("UPDATE push_msgs SET state = 'sent', sent_at = ?, devices = ? WHERE id = ?", [$now, $n, $m['id']]); $out['sent']++; }
            else { pa_release($m, 'nodevice'); $out['skipped']++; }
        } catch (Throwable $e) { error_log('[Sweep push auto] run ' . $m['id'] . ': ' . $e->getMessage()); }
    }
    pa_q("UPDATE push_msgs SET state = 'queued' WHERE state = 'sending' AND due_at < ?", [$now - 900]);   // a run that died mid-send
    return $out;
}

/** api/p/o/<token>: the service worker, when the trader taps the notification (no session: the token is the proof) */
function pa_open(string $token): void
{
    try { pa_q('UPDATE push_msgs SET opened_at = ? WHERE token = ? AND opened_at IS NULL', [pa_now(), $token]); } catch (Throwable $e) { error_log('[Sweep push auto] open: ' . $e->getMessage()); }
}
function pa_public_route(string $route, string $method): void
{
    if (!preg_match('#^api/p/o/([a-f0-9]{24})$#', $route, $m)) return;
    if ($method === 'POST') pa_open($m[1]);
    http_response_code(204); exit;
}
/** the trader deleted his account (api.php) */
function pa_forget(string $uid): void
{
    try { pa_q('DELETE FROM push_msgs WHERE user_id = ?', [$uid]); } catch (Throwable $e) { error_log('[Sweep push auto] forget: ' . $e->getMessage()); }
}

/* ───────────── the account's moments (after each trade, typed, copied or synced) ───────────── */

/**
 * A funded account that can ask for a payout (GameV2::payoutStatus, the app's rules): once per payout cycle. An evaluation
 * that reaches its target (net profit after paid payouts): « passed » when its minimum days and its consistency are met too,
 * else « target reached » with what is left (then « passed » later, once). Failed, archived and demo accounts: nothing.
 */
function pa_account_moments(string $uid): void
{
    if (!class_exists('GameV2', false) || !class_exists('GameEngine', false)) return;
    $on = []; foreach (['payoutReady', 'goalReached', 'evalPassed'] as $k) $on[$k] = pa_setting($k)['on'];
    if (!array_filter($on)) return;
    GameEngine::forget($uid);   // the document just saved (this listener may run before the guardian's)
    $trades = GameEngine::docs($uid, 'trades'); $pays = GameEngine::docs($uid, 'payouts');
    $lang = (string) (pa_q('SELECT lang FROM users WHERE id = ?', [$uid])->fetchColumn() ?: 'en');
    foreach (GameEngine::docs($uid, 'accounts') as $a) {
        if (!empty($a['demo']) || in_array($a['status'] ?? '', ['archived', 'closed'], true) || in_array($a['result'] ?? '', ['failed', 'passed'], true)) continue;
        $id = (string) ($a['id'] ?? ''); $name = mb_substr(trim((string) ($a['name'] ?? '')), 0, 40); $r = (array) ($a['rules'] ?? []);
        $phase = (string) (($a['phase'] ?? '') ?: ($a['money_type'] ?? ''));
        if (in_array($phase, ['funded', 'live'], true)) {
            if (!$on['payoutReady']) continue;
            $s = GameV2::payoutStatus($a, $trades, $pays);
            if (!$s || !$s[0]) continue;
            $last = ''; foreach ($pays as $p) if (($p['account_id'] ?? '') === $id && !in_array($p['status'] ?? '', ['rejected', 'planned'], true)) { $d = (string) (($p['request_date'] ?? '') ?: (($p['approval_date'] ?? '') ?: (($p['payment_date'] ?? '') ?: substr((string) ($p['created_at'] ?? ''), 0, 10)))); if ($d > $last) $last = $d; }
            pa_queue($uid, 'payoutReady', ['account' => $name, 'id' => $id], 'payout:' . $id . ':' . ($last ?: 'first'));
            continue;
        }
        $goal = (int) ($r['target_c'] ?? 0); if ($goal <= 0) continue;
        $net = 0; $days = [];
        foreach ($trades as $t) if (($t['account_id'] ?? '') === $id) { $n = GameEngine::net($t); $net += $n; $d = (string) ($t['date'] ?? ''); $days[$d] = ($days[$d] ?? 0) + $n; }
        foreach ($pays as $p) if (($p['account_id'] ?? '') === $id && ($p['status'] ?? '') === 'paid') $net -= (int) ($p['amount_c'] ?? 0);
        if ($net < $goal) continue;
        $left = [];
        $md = (int) ($r['min_days'] ?? 0); if ($md > count($days)) $left[] = ['days', $md - count($days)];
        $cp = (float) ($r['consistency_pct'] ?? 0);
        if ($cp > 0) { $c = GameV2::consPct(array_values($days), isset($r['consistency_base']) ? (string) $r['consistency_base'] : null); if ($c === null || $c > $cp) $left[] = ['cons', $cp]; }
        if (!$left) { if ($on['evalPassed']) pa_queue($uid, 'evalPassed', ['account' => $name, 'id' => $id], 'pass:' . $id); continue; }
        if ($on['goalReached']) pa_queue($uid, 'goalReached', ['account' => $name, 'id' => $id, 'left' => pa_left_text($left, $lang)], 'goal:' . $id);
    }
}
/** what an evaluation still has to meet, in words (the bell shows the trader's language; the phone shows the same words) */
function pa_left_text(array $left, string $lang): string
{
    $L = ['en' => ['days' => ['1 more trading day', '{n} more trading days'], 'cons' => 'consistency (best day ≤ {p} % of the profit)', 'and' => ' and '],
          'fr' => ['days' => ['1 jour de trading de plus', '{n} jours de trading de plus'], 'cons' => 'la consistance (meilleur jour ≤ {p} % du profit)', 'and' => ' et '],
          'es' => ['days' => ['1 día de trading más', '{n} días de trading más'], 'cons' => 'la consistencia (mejor día ≤ {p} % del beneficio)', 'and' => ' y ']][in_array($lang, ['fr', 'es'], true) ? $lang : 'en'];
    $parts = [];
    foreach ($left as [$k, $v]) $parts[] = $k === 'days' ? str_replace('{n}', (string) $v, $L['days'][$v === 1 ? 0 : 1]) : str_replace('{p}', rtrim(rtrim(number_format((float) $v, 1, '.', ''), '0'), '.'), $L['cons']);
    return implode($L['and'], $parts);
}

/* ───────────── Sweep's news (Admin › Emails, by hand) ───────────── */

/** queues the news for every trader who can receive it; refused within 28 days of the last one */
function pa_news_send(array $text): array
{
    $last = (int) pa_q("SELECT MAX(created_at) FROM push_msgs WHERE auto = 'news'")->fetchColumn();
    if ($last && $last > pa_now() - PA_NEWS_GAP) return ['error' => 'too_soon', 'next' => $last + PA_NEWS_GAP];
    $r = pa_save('news', ['on' => true, 'text' => $text]);
    if (isset($r['error']) || $r['text']['en'][0] === '' || $r['text']['en'][1] === '') return ['error' => 'text'];
    $n = 0; $batch = pa_now();
    foreach (pa_q('SELECT DISTINCT user_id FROM push_subscriptions')->fetchAll(PDO::FETCH_COLUMN) as $uid)
        if (pa_queue((string) $uid, 'news', [], 'news:' . $batch) !== null) $n++;
    pa_save('news', ['on' => false]);   // the next one is sent by hand again
    return ['ok' => true, 'queued' => $n];
}

/* ───────────── numbers and Admin › Emails ───────────── */

/** the numbers of a message since $since: notifications sent, opened, emails relayed (sent after an unopened one) and spared */
function pa_stats(string $key, int $since): array
{
    $sent = (int) pa_q("SELECT COUNT(*) FROM push_msgs WHERE auto = ? AND state = 'sent' AND sent_at >= ?", [$key, $since])->fetchColumn();
    $open = (int) pa_q("SELECT COUNT(*) FROM push_msgs WHERE auto = ? AND state = 'sent' AND opened_at IS NOT NULL AND sent_at >= ?", [$key, $since])->fetchColumn();
    $skip = (int) pa_q("SELECT COUNT(*) FROM push_msgs WHERE auto = ? AND state = 'skipped' AND created_at >= ?", [$key, $since])->fetchColumn();
    $relay = $spared = 0;
    try {
        $relay = (int) pa_q("SELECT COUNT(*) FROM push_msgs p JOIN mail_queue q ON q.id = p.mail_qid WHERE p.auto = ? AND p.state = 'sent' AND q.state = 'sent' AND p.sent_at >= ?", [$key, $since])->fetchColumn();
        $spared = (int) pa_q("SELECT COUNT(*) FROM push_msgs p JOIN mail_queue q ON q.id = p.mail_qid WHERE p.auto = ? AND q.state = 'pushed' AND p.sent_at >= ?", [$key, $since])->fetchColumn();
    } catch (Throwable $e) { /* no email queue yet */ }
    return ['sent' => $sent, 'opened' => $open, 'open_rate' => $sent ? round($open * 100 / $sent, 1) : null, 'skipped' => $skip, 'relayed' => $relay, 'spared' => $spared];
}
/** a message as Admin shows it: channel, group, its switch and text, its numbers over 30 days */
function pa_admin_item(string $key): array
{
    $d = pa_def($key); $s = pa_setting($key);
    return ['key' => $key, 'ch' => $d['ch'], 'group' => $d['group'], 'name' => $d['name'] ?? null, 'when' => $d['when'] ?? null, 'on' => $s['on'], 'text' => $s['text'],
        'stats' => pa_stats($key, pa_now() - 30 * 86400), 'vars' => array_values(array_unique(array_merge(...array_map(fn($t) => preg_match_all('/\{(\w+)\}/', $t[0] . ' ' . $t[1], $mm) ? $mm[1] : [], array_values($d['text'] ?? [])))))];
}
/** how many traders the phone reaches: a device, and each group switched on */
function pa_reach(): array
{
    $ids = function_exists('wp_config') && wp_config() ? pa_q('SELECT DISTINCT user_id FROM push_subscriptions')->fetchAll(PDO::FETCH_COLUMN) : [];
    $g = array_fill_keys(PA_GROUPS, 0);
    foreach ($ids as $uid) foreach (wp_groups(wp_prefs(pa_pdo(), (string) $uid)) as $k => $v) if ($v) $g[$k]++;
    return ['devices' => count($ids), 'groups' => $g, 'keys' => function_exists('wp_config') && (bool) wp_config()];
}
/**
 * Admin (administrators only, api.php):
 *   GET  api/admin/push              every message (catalog order), the reach, the last news
 *   POST api/admin/push/<key>        {on, text: {en: [title, line], fr, es}}
 *   POST api/admin/push/news/send    {text}: Sweep's news to every phone (once in 28 days)
 */
function pa_admin_route(string $route, string $method): void
{
    $b = $method === 'POST' ? body_json(65536) : [];
    if ($route === 'api/admin/push' && $method === 'GET') {
        $last = (int) pa_q("SELECT MAX(created_at) FROM push_msgs WHERE auto = 'news'")->fetchColumn();
        json_out(200, ['items' => array_map('pa_admin_item', array_keys(pa_catalog())), 'reach' => pa_reach(), 'news_last' => $last ?: null, 'news_next' => $last ? $last + PA_NEWS_GAP : null]);
    }
    if ($route === 'api/admin/push/news/send' && $method === 'POST') { $r = pa_news_send((array) ($b['text'] ?? [])); json_out(isset($r['error']) ? 409 : 200, $r); }
    if (preg_match('#^api/admin/push/([A-Za-z0-9]{2,40})$#', $route, $m) && $method === 'POST' && $m[1] !== 'news') {
        $r = pa_save($m[1], $b); if (isset($r['error'])) json_out($r['error'] === 'not_found' ? 404 : 400, $r);
        json_out(200, pa_admin_item($m[1]));
    }
    json_out(404, ['error' => 'not_found']);
}

if (class_exists('Notify', false)) Notify::register('pa_alert', ['category' => 'prop_alerts', 'icon' => 'star']);   // an account's moment, its text in the params
if (class_exists('Events', false)) {
    foreach (['trade.created', 'trade.updated', 'payout.recorded', 'payout.updated', 'account.updated'] as $ev)
        Events::on($ev, function (array $p): void { $uid = (string) ($p['uid'] ?? ''); if ($uid !== '') { try { pa_account_moments($uid); } catch (Throwable $e) { error_log('[Sweep push auto] moments: ' . $e->getMessage()); } } });
}
