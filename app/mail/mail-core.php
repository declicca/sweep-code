<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli' && realpath((string) ($_SERVER['SCRIPT_FILENAME'] ?? '')) === realpath(__FILE__)) { http_response_code(404); exit; }
/**
 * Sweep — our own emailing (brief « Courriels maison », 3 Nov. 2026): campaigns sent from our server, no outside service.
 *  - mail_campaigns: one campaign (EN / FR / ES versions, audience, state); mail_queue: one line per recipient, sent by
 *    mail/send-cron.php (every minute) within an hourly cap that grows week after week (warm-up of the server's address);
 *  - mail_events: opens (a 1×1 image; opens made by Apple Mail's privacy protection or a scanner are kept apart), clicks
 *    (each link goes through api/m/c), bounces and complaints (mail/bounce.php, piped from bounces@), unsubscriptions;
 *  - mail_suppress: addresses never written to again (hard bounce, 3 soft bounces, complaint);
 *  - email_prefs.marketing: 0 = the trader unsubscribed (one click from the email, or the List-Unsubscribe of the mail app).
 * Tables are created on first use (SQLite and MySQL). A dev copy (SWEEP_TEST_DB) never sends: data/mail-sent.jsonl.
 */

const ML_LANGS = ['en', 'fr', 'es'];
const ML_BOUNCE_LIMIT = 0.03;      // a campaign pauses itself above 3 % hard bounces…
const ML_COMPLAINT_LIMIT = 0.002;  // …or 0.2 % complaints (Gmail's limit is 0.3 %), once 100 emails went out
const ML_SOFT_MAX = 3;             // 3 soft bounces in a row: the address is set aside

function ml_my(PDO $pdo): bool { return $pdo->getAttribute(PDO::ATTR_DRIVER_NAME) === 'mysql'; }
function ml_q(PDO $pdo, string $sql, array $a = []): PDOStatement { $st = $pdo->prepare($sql); $st->execute($a); return $st; }

function ml_schema(PDO $pdo): void
{
    static $done = false; if ($done) return;
    $my = ml_my($pdo);
    $auto = $my ? 'INTEGER PRIMARY KEY AUTO_INCREMENT' : 'INTEGER PRIMARY KEY AUTOINCREMENT';
    $K = $my ? 'VARCHAR(191)' : 'TEXT'; $L = $my ? 'LONGTEXT' : 'TEXT'; $cs = $my ? ' DEFAULT CHARSET=utf8mb4' : '';
    $pdo->exec("CREATE TABLE IF NOT EXISTS mail_campaigns (id $auto, name VARCHAR(120) NOT NULL, status VARCHAR(16) NOT NULL, content_json $L NOT NULL,
        audience_json TEXT NOT NULL, recipients INT NOT NULL DEFAULT 0, scheduled_at INT NULL, started_at INT NULL, finished_at INT NULL,
        paused_reason VARCHAR(40) NULL, created_at INT NOT NULL, updated_at INT NOT NULL)$cs");
    $pdo->exec("CREATE TABLE IF NOT EXISTS mail_queue (id $auto, campaign_id INT NULL, user_id $K NULL, email VARCHAR(190) NOT NULL, lang VARCHAR(2) NOT NULL,
        first_name VARCHAR(40) NULL, kind VARCHAR(16) NOT NULL, subject TEXT NULL, text_body $L NULL, html_body $L NULL, token VARCHAR(24) NOT NULL,
        state VARCHAR(12) NOT NULL, attempts INT NOT NULL DEFAULT 0, next_at INT NOT NULL, error VARCHAR(255) NULL, created_at INT NOT NULL, sent_at INT NULL)$cs");
    $pdo->exec("CREATE TABLE IF NOT EXISTS mail_events (id $auto, queue_id INT NOT NULL, campaign_id INT NULL, type VARCHAR(12) NOT NULL, url VARCHAR(500) NULL, at INT NOT NULL)$cs");
    $pdo->exec("CREATE TABLE IF NOT EXISTS mail_suppress (email_lc VARCHAR(190) NOT NULL PRIMARY KEY, reason VARCHAR(16) NOT NULL, soft INT NOT NULL DEFAULT 0, at INT NOT NULL)$cs");
    // the table of the « Your week » email (game/weekly-mail.php): same definition, plus the marketing choice
    $pdo->exec("CREATE TABLE IF NOT EXISTS email_prefs (user_id $K NOT NULL PRIMARY KEY, token VARCHAR(40) NOT NULL, weekly_off INT NOT NULL DEFAULT 0, updated_at INT NOT NULL)$cs");
    foreach (['marketing' => 'INT NULL', 'marketing_at' => 'INT NULL'] as $c => $t) {
        try { $pdo->exec("ALTER TABLE email_prefs ADD COLUMN $c $t"); } catch (Throwable $e) { /* already there */ }
    }
    foreach ($my ? ['ALTER TABLE mail_queue ADD UNIQUE KEY uq_mq_token (token)', 'ALTER TABLE mail_queue ADD KEY ix_mq_send (state, next_at)', 'ALTER TABLE mail_queue ADD KEY ix_mq_camp (campaign_id)',
                    'ALTER TABLE mail_events ADD KEY ix_me_q (queue_id)', 'ALTER TABLE mail_events ADD KEY ix_me_c (campaign_id, type)']
                 : ['CREATE UNIQUE INDEX IF NOT EXISTS uq_mq_token ON mail_queue (token)', 'CREATE INDEX IF NOT EXISTS ix_mq_send ON mail_queue (state, next_at)', 'CREATE INDEX IF NOT EXISTS ix_mq_camp ON mail_queue (campaign_id)',
                    'CREATE INDEX IF NOT EXISTS ix_me_q ON mail_events (queue_id)', 'CREATE INDEX IF NOT EXISTS ix_me_c ON mail_events (campaign_id, type)'] as $sql) {
        try { $pdo->exec($sql); } catch (Throwable $e) { /* exists */ }
    }
    $done = true;
}

/* ───── settings (app_settings) ───── */
function ml_setting(PDO $pdo, string $k, string $def = ''): string
{
    try { $v = ml_q($pdo, 'SELECT v FROM app_settings WHERE k = ?', [$k])->fetchColumn(); } catch (Throwable $e) { $v = false; }
    return $v === false ? $def : (string) $v;
}
function ml_set_setting(PDO $pdo, string $k, string $v): void
{
    $pdo->exec('CREATE TABLE IF NOT EXISTS app_settings (k VARCHAR(64) NOT NULL PRIMARY KEY, v TEXT NOT NULL)');
    if (ml_q($pdo, 'UPDATE app_settings SET v = ? WHERE k = ?', [$v, $k])->rowCount() === 0 && ml_setting($pdo, $k, "\0") === "\0") ml_q($pdo, 'INSERT INTO app_settings (k, v) VALUES (?, ?)', [$k, $v]);
}
/** signs the click links (no open redirect): a random key kept in the database */
function ml_secret(PDO $pdo): string
{
    $s = ml_setting($pdo, 'mail_secret');
    if ($s === '') { $s = bin2hex(random_bytes(32)); ml_set_setting($pdo, 'mail_secret', $s); }
    return $s;
}
function ml_cfg(): array { return (array) ($GLOBALS['cfg'] ?? []); }
function ml_base(): string { $u = trim((string) (ml_cfg()['app_url'] ?? '')); return rtrim($u !== '' ? $u : 'https://app.makeitsweep.com', '/') . '/'; }
function ml_from(): string { return trim((string) (ml_cfg()['mail_from'] ?? '')) ?: 'hello@makeitsweep.com'; }
function ml_bounce_addr(): string { return trim((string) (ml_cfg()['mail_bounce'] ?? '')) ?: 'bounces@makeitsweep.com'; }
function ml_address(PDO $pdo): string { return ml_setting($pdo, 'mail_address', 'Sweep Inc. · Laval (Québec) Canada'); }
function ml_lang($l): string { $l = strtolower(substr((string) $l, 0, 2)); return in_array($l, ML_LANGS, true) ? $l : 'en'; }
function ml_token(): string { return bin2hex(random_bytes(12)); }

/**
 * The hourly cap: config 'mail_per_hour' => ['start' => 100, 'max' => 500]. It doubles every week from the first campaign
 * email (a new sending address earns its reputation slowly), and never goes over 'max' (keep it under WHM's hourly limit).
 */
function ml_cap(PDO $pdo, ?int $now = null): int
{
    $now = $now ?? time(); $c = (array) (ml_cfg()['mail_per_hour'] ?? []);
    $start = max(1, (int) ($c['start'] ?? 100)); $max = max($start, (int) ($c['max'] ?? 500));
    $t0 = (int) ml_setting($pdo, 'mail_warm_start', '0');
    $weeks = $t0 > 0 ? max(0, intdiv($now - $t0, 604800)) : 0;
    return (int) min($max, $start * (2 ** min($weeks, 10)));
}

/* ───── consent and suppression ───── */
function ml_prefs(PDO $pdo, string $uid): array
{
    ml_schema($pdo);
    $r = ml_q($pdo, 'SELECT token, marketing FROM email_prefs WHERE user_id = ?', [$uid])->fetch(PDO::FETCH_ASSOC);
    if ($r) return $r;
    $t = bin2hex(random_bytes(16));
    ml_q($pdo, 'INSERT INTO email_prefs (user_id, token, weekly_off, updated_at) VALUES (?, ?, 0, ?)', [$uid, $t, time()]);
    return ['token' => $t, 'marketing' => null];
}
function ml_set_marketing(PDO $pdo, string $uid, bool $on): void
{
    ml_prefs($pdo, $uid);
    ml_q($pdo, 'UPDATE email_prefs SET marketing = ?, marketing_at = ?, updated_at = ? WHERE user_id = ?', [$on ? 1 : 0, time(), time(), $uid]);
}
function ml_suppressed(PDO $pdo, string $email): bool
{
    return (bool) ml_q($pdo, "SELECT 1 FROM mail_suppress WHERE email_lc = ? AND reason <> 'soft'", [strtolower(trim($email))])->fetchColumn();
}
/** hard / complaint: set aside at once; soft: after ML_SOFT_MAX in a row (a delivered email starts the count again) */
function ml_suppress(PDO $pdo, string $email, string $reason): void
{
    $e = strtolower(trim($email)); $now = time();
    $r = ml_q($pdo, 'SELECT reason, soft FROM mail_suppress WHERE email_lc = ?', [$e])->fetch(PDO::FETCH_ASSOC);
    if ($reason === 'soft') {
        $n = ($r ? (int) $r['soft'] : 0) + 1; $set = $n >= ML_SOFT_MAX ? 'soft_max' : 'soft';
        if ($r && $r['reason'] !== 'soft') return;
        if ($r) ml_q($pdo, 'UPDATE mail_suppress SET soft = ?, reason = ?, at = ? WHERE email_lc = ?', [$n, $set, $now, $e]);
        else ml_q($pdo, 'INSERT INTO mail_suppress (email_lc, reason, soft, at) VALUES (?, ?, ?, ?)', [$e, $set, $n, $now]);
        return;
    }
    if ($r) ml_q($pdo, 'UPDATE mail_suppress SET reason = ?, at = ? WHERE email_lc = ?', [$reason, $now, $e]);
    else ml_q($pdo, 'INSERT INTO mail_suppress (email_lc, reason, soft, at) VALUES (?, ?, 0, ?)', [$e, $reason, $now]);
}

/* ───── audience ───── */
function ml_plan_of(PDO $pdo, string $uid): string
{
    static $on = null;
    if ($on === null) $on = function_exists('billing_on') ? billing_on() : false;
    if (!$on || !function_exists('sb_plan')) return 'free';
    try { return sb_plan($pdo, $uid); } catch (Throwable $e) { return 'free'; }
}
/** filters: lang (en|fr|es|''), plan (free|pro|elite|''), joined (signed up within N days), active (seen within N days), inactive (not seen for N days) */
function ml_clean_audience($a): array
{
    $a = is_array($a) ? $a : [];
    $n = fn($k) => max(0, min(3650, (int) ($a[$k] ?? 0)));
    return ['lang' => in_array($a['lang'] ?? '', ML_LANGS, true) ? $a['lang'] : '', 'plan' => in_array($a['plan'] ?? '', ['free', 'pro', 'elite'], true) ? $a['plan'] : '',
        'joined' => $n('joined'), 'active' => $n('active'), 'inactive' => $n('inactive')];
}
/** every trader the campaign would reach: real accounts with an address, not unsubscribed, not set aside */
function ml_audience(PDO $pdo, array $f, ?int $now = null): array
{
    ml_schema($pdo); $now = $now ?? time(); $f = ml_clean_audience($f);
    $rows = ml_q($pdo, "SELECT u.id, u.email, u.lang, u.first_name, u.created_at, u.last_login, p.marketing FROM users u LEFT JOIN email_prefs p ON p.user_id = u.id
        WHERE u.email IS NOT NULL AND u.email <> '' AND u.disabled = 0 AND u.is_admin = 0 AND COALESCE(u.is_internal, 0) = 0")->fetchAll(PDO::FETCH_ASSOC);
    $sup = []; foreach (ml_q($pdo, "SELECT email_lc FROM mail_suppress WHERE reason <> 'soft'")->fetchAll(PDO::FETCH_COLUMN) as $e) $sup[$e] = true;
    $ts = fn($v) => $v ? (strtotime((string) $v) ?: 0) : 0;
    $out = [];
    foreach ($rows as $r) {
        if ($r['marketing'] !== null && (int) $r['marketing'] === 0) continue;
        if (isset($sup[strtolower(trim((string) $r['email']))])) continue;
        $lang = ml_lang($r['lang']);
        if ($f['lang'] !== '' && $lang !== $f['lang']) continue;
        if ($f['joined'] && $ts($r['created_at']) < $now - $f['joined'] * 86400) continue;
        $seen = $ts($r['last_login']) ?: $ts($r['created_at']);
        if ($f['active'] && $seen < $now - $f['active'] * 86400) continue;
        if ($f['inactive'] && $seen >= $now - $f['inactive'] * 86400) continue;
        if ($f['plan'] !== '' && ml_plan_of($pdo, (string) $r['id']) !== $f['plan']) continue;
        $out[] = ['id' => (string) $r['id'], 'email' => trim((string) $r['email']), 'lang' => $lang, 'first' => trim((string) ($r['first_name'] ?? ''))];
    }
    return $out;
}
/** who is on the list: reachable, unsubscribed, set aside */
function ml_list_health(PDO $pdo): array
{
    ml_schema($pdo);
    $base = "FROM users u LEFT JOIN email_prefs p ON p.user_id = u.id WHERE u.email IS NOT NULL AND u.email <> '' AND u.disabled = 0 AND u.is_admin = 0 AND COALESCE(u.is_internal, 0) = 0";
    $all = (int) ml_q($pdo, "SELECT COUNT(*) $base")->fetchColumn();
    $off = (int) ml_q($pdo, "SELECT COUNT(*) $base AND p.marketing = 0")->fetchColumn();
    $sup = (int) ml_q($pdo, "SELECT COUNT(*) $base AND COALESCE(p.marketing, 1) <> 0 AND LOWER(u.email) IN (SELECT email_lc FROM mail_suppress WHERE reason <> 'soft')")->fetchColumn();
    return ['total' => $all, 'reachable' => $all - $off - $sup, 'unsubscribed' => $off, 'suppressed' => $sup];
}

/* ───── content ───── */
const ML_T = [
    'en' => ['why' => 'You get this email because you have a Sweep account.', 'off' => 'Unsubscribe', 'hi' => 'trader',
        'pg_t' => 'Unsubscribe from Sweep news?', 'pg_p' => 'You will stop getting news and tips by email. Emails about your account (security, billing) still come.', 'pg_b' => 'Unsubscribe',
        'pg_off_t' => 'You are unsubscribed', 'pg_off_p' => 'No more news and tips from Sweep. Changed your mind?', 'pg_off_b' => 'Subscribe again',
        'pg_on_t' => 'You are subscribed again', 'pg_on_p' => 'Sweep news and tips will reach you again.', 'pg_bad' => 'This link is not valid anymore.'],
    'fr' => ['why' => 'Tu reçois ce courriel parce que tu as un compte Sweep.', 'off' => 'Me désinscrire', 'hi' => 'trader',
        'pg_t' => 'Ne plus recevoir les nouvelles de Sweep ?', 'pg_p' => 'Tu ne recevras plus les nouvelles et conseils par courriel. Les courriels sur ton compte (sécurité, facturation) continuent.', 'pg_b' => 'Me désinscrire',
        'pg_off_t' => 'Tu es désinscrit', 'pg_off_p' => 'Plus de nouvelles ni de conseils de Sweep. Tu as changé d’avis ?', 'pg_off_b' => 'Me réinscrire',
        'pg_on_t' => 'Tu es réinscrit', 'pg_on_p' => 'Les nouvelles et conseils de Sweep te parviendront de nouveau.', 'pg_bad' => 'Ce lien n’est plus valide.'],
    'es' => ['why' => 'Recibes este correo porque tienes una cuenta de Sweep.', 'off' => 'Darme de baja', 'hi' => 'trader',
        'pg_t' => '¿Dejar de recibir las novedades de Sweep?', 'pg_p' => 'Dejarás de recibir novedades y consejos por correo. Los correos sobre tu cuenta (seguridad, facturación) siguen llegando.', 'pg_b' => 'Darme de baja',
        'pg_off_t' => 'Te has dado de baja', 'pg_off_p' => 'No más novedades ni consejos de Sweep. ¿Cambiaste de opinión?', 'pg_off_b' => 'Suscribirme de nuevo',
        'pg_on_t' => 'Estás suscrito de nuevo', 'pg_on_p' => 'Las novedades y consejos de Sweep volverán a llegarte.', 'pg_bad' => 'Este enlace ya no es válido.'],
];
/** one campaign's content, cleaned: per language subject, preheader, body (light markup, see ml_render) */
function ml_clean_content($c): array
{
    $c = is_array($c) ? $c : []; $out = [];
    foreach (ML_LANGS as $l) {
        $v = is_array($c[$l] ?? null) ? $c[$l] : [];
        $out[$l] = ['subject' => mb_substr(trim((string) ($v['subject'] ?? '')), 0, 200), 'preheader' => mb_substr(trim((string) ($v['preheader'] ?? '')), 0, 200),
            'body' => mb_substr(str_replace("\r", '', (string) ($v['body'] ?? '')), 0, 20000)];
    }
    return $out;
}
/** the version for a language: its own when it has a subject and a body, else the English one, else the first one written */
function ml_version(array $content, string $lang): ?array
{
    $ok = fn($l) => isset($content[$l]) && $content[$l]['subject'] !== '' && trim($content[$l]['body']) !== '';
    foreach (array_merge([$lang, 'en'], ML_LANGS) as $l) if ($ok($l)) return $content[$l] + ['lang' => $l];
    return null;
}
function ml_link(PDO $pdo, string $token, string $url): string
{
    if ($token === '') return $url;
    return ml_base() . 'api/m/c/' . $token . '?u=' . rtrim(strtr(base64_encode($url), '+/', '-_'), '=') . '&s=' . substr(hash_hmac('sha256', $token . '|' . $url, ml_secret($pdo)), 0, 16);
}
/**
 * The body's light markup, one idea per line:
 *   # A title            a blank line separates paragraphs        **bold**
 *   [text](https://…)    a link                                    [[Button text|https://…]]  a button (alone on its line)
 *   {first}              the trader's first name (« trader » without one), also in the subject
 * Returns [subject, text, html]. $token '' (preview, test): links are not tracked, no open image.
 */
function ml_render(PDO $pdo, array $v, string $lang, string $first, string $token, bool $track = true): array
{
    $L = ML_T[$lang] ?? ML_T['en'];
    $name = $first !== '' ? $first : $L['hi'];
    $sub = str_replace('{first}', $name, $v['subject']);
    $h = fn($x) => htmlspecialchars((string) $x, ENT_QUOTES, 'UTF-8');
    $nb = fn(string $x) => $lang === 'fr' ? preg_replace(['/« /u', '/ »/u', '/ ([?:!;])/u'], ["«\u{00A0}", "\u{00A0}»", "\u{00A0}$1"], $x) : $x;
    $go = fn(string $u) => $track ? ml_link($pdo, $token, $u) : $u;
    $safeUrl = fn(string $u) => preg_match('#^(https?://|mailto:)#i', $u) ? $u : '';
    $inline = function (string $s) use ($h, $go, $safeUrl, $nb): string {
        $s = $h($nb($s));
        $s = preg_replace('/\*\*(.+?)\*\*/u', '<b style="color:#f2f2f3">$1</b>', $s);
        return preg_replace_callback('/\[([^\]]+)\]\(([^)\s]+)\)/u', function ($m) use ($go, $safeUrl, $h) {
            $u = $safeUrl(html_entity_decode($m[2], ENT_QUOTES, 'UTF-8')); if ($u === '') return $m[1];
            return '<a href="' . $h($go($u)) . '" style="color:#4c8dff;text-decoration:underline">' . $m[1] . '</a>';
        }, $s);
    };
    $body = str_replace('{first}', $name, $v['body']);
    $html = ''; $text = '';
    foreach (preg_split('/\n\s*\n/', trim($body)) as $blk) {
        $blk = trim($blk); if ($blk === '') continue;
        if (preg_match('/^\[\[([^|\]]+)\|([^\]\s]+)\]\]$/u', $blk, $m) && ($u = $safeUrl($m[2])) !== '') {
            $html .= '<div style="margin:24px 0"><a href="' . $h($go($u)) . '" style="display:inline-block;background:#4c8dff;color:#0b0b0c;font-weight:600;font-size:15px;text-decoration:none;padding:13px 24px;border-radius:999px">' . $h($nb(trim($m[1]))) . '</a></div>';
            $text .= trim($m[1]) . ': ' . $go($u) . "\n\n"; continue;
        }
        if (preg_match('/^#\s+(.+)$/u', $blk, $m)) {
            $html .= '<h2 style="margin:24px 0 8px;font-size:19px;line-height:1.3;color:#f2f2f3">' . $inline($m[1]) . '</h2>';
            $text .= mb_strtoupper(trim($m[1])) . "\n\n"; continue;
        }
        $html .= '<p style="margin:0 0 16px;font-size:15px;line-height:1.6;color:#b9b9c2">' . implode('<br>', array_map($inline, explode("\n", $blk))) . '</p>';
        $text .= preg_replace_callback('/\[([^\]]+)\]\(([^)\s]+)\)/u', fn($m) => $m[1] . ' (' . (($u = $safeUrl($m[2])) !== '' ? $go($u) : $m[2]) . ')', str_replace('**', '', $blk)) . "\n\n";
    }
    $off = $token !== '' ? ml_base() . 'api/m/u/' . $token : ml_base() . '#settings';
    $addr = ml_address($pdo);
    $text = $nb($text) . "—\n" . $L['why'] . "\n" . $L['off'] . ': ' . $off . "\n" . $addr . "\n";
    $pre = $v['preheader'] !== '' ? '<div style="display:none;max-height:0;overflow:hidden;opacity:0">' . $h($nb(str_replace('{first}', $name, $v['preheader']))) . str_repeat('&#8199;&#847; ', 30) . '</div>' : '';
    $pixel = $track && $token !== '' ? '<img src="' . $h(ml_base() . 'api/m/o/' . $token) . '" width="1" height="1" alt="" style="display:block;width:1px;height:1px;border:0">' : '';
    $html = '<!doctype html><html lang="' . $lang . '"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="dark"><title>' . $h($sub) . '</title></head>'
        . '<body style="margin:0;background:#0b0b0c;padding:32px 16px;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Inter,Arial,sans-serif;color:#f2f2f3">' . $pre
        . '<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td align="center"><table role="presentation" width="100%" style="max-width:520px;background:#141416;border:1px solid #26262a;border-radius:20px" cellpadding="0" cellspacing="0"><tr><td style="padding:32px 28px">'
        . '<div style="font-size:18px;font-weight:700;letter-spacing:-.01em;margin-bottom:24px">sweep</div>' . $html
        . '</td></tr></table><p style="font-size:12px;line-height:1.5;color:#6c6c76;margin:16px 0 0;max-width:520px">' . $h($nb($L['why'])) . ' <a href="' . $h($off) . '" style="color:#8a8a94">' . $h($L['off']) . '</a><br>' . $h($addr) . '</p>'
        . $pixel . '</td></tr></table></body></html>';
    return [$nb($sub), $text, $html];
}

/* ───── campaigns ───── */
function ml_campaign(PDO $pdo, int $id): ?array
{
    ml_schema($pdo);
    $r = ml_q($pdo, 'SELECT * FROM mail_campaigns WHERE id = ?', [$id])->fetch(PDO::FETCH_ASSOC);
    if (!$r) return null;
    $r['id'] = (int) $r['id']; $r['recipients'] = (int) $r['recipients'];
    foreach (['scheduled_at', 'started_at', 'finished_at', 'created_at', 'updated_at'] as $k) $r[$k] = $r[$k] !== null ? (int) $r[$k] : null;
    $r['content'] = ml_clean_content(json_decode((string) $r['content_json'], true)); $r['audience'] = ml_clean_audience(json_decode((string) $r['audience_json'], true));
    unset($r['content_json'], $r['audience_json']);
    return $r;
}
function ml_campaign_save(PDO $pdo, ?int $id, array $b): array
{
    ml_schema($pdo); $now = time();
    $name = mb_substr(trim((string) ($b['name'] ?? '')), 0, 120);
    $content = json_encode(ml_clean_content($b['content'] ?? []), JSON_UNESCAPED_UNICODE); $aud = json_encode(ml_clean_audience($b['audience'] ?? []));
    if ($id === null) {
        ml_q($pdo, "INSERT INTO mail_campaigns (name, status, content_json, audience_json, created_at, updated_at) VALUES (?, 'draft', ?, ?, ?, ?)", [$name, $content, $aud, $now, $now]);
        return ['id' => (int) $pdo->lastInsertId()];
    }
    $c = ml_campaign($pdo, $id);
    if (!$c) return ['error' => 'not_found'];
    if (!in_array($c['status'], ['draft', 'scheduled'], true)) return ['error' => 'sent'];   // what went out is not rewritten
    ml_q($pdo, 'UPDATE mail_campaigns SET name = ?, content_json = ?, audience_json = ?, updated_at = ? WHERE id = ?', [$name, $content, $aud, $now, $id]);
    return ['id' => $id];
}
/** what is missing before it can go: a name, at least the English version or the one of each language targeted */
function ml_campaign_ready(array $c): ?string
{
    if (trim($c['name']) === '') return 'name';
    if (!ml_version($c['content'], $c['audience']['lang'] ?: 'en')) return 'content';
    return null;
}
/** « Send » (now or at a time): the cron takes it from scheduled_at */
function ml_campaign_schedule(PDO $pdo, int $id, ?int $at): array
{
    $c = ml_campaign($pdo, $id); if (!$c) return ['error' => 'not_found'];
    if (!in_array($c['status'], ['draft', 'scheduled'], true)) return ['error' => 'sent'];
    if ($why = ml_campaign_ready($c)) return ['error' => $why];
    ml_q($pdo, "UPDATE mail_campaigns SET status = 'scheduled', scheduled_at = ?, updated_at = ? WHERE id = ?", [$at ?? time(), time(), $id]);
    return ['ok' => true];
}
/** one line per recipient, the audience of the moment it starts (a trader who unsubscribes later is skipped at sending) */
function ml_campaign_start(PDO $pdo, int $id, ?int $now = null): int
{
    $now = $now ?? time(); $c = ml_campaign($pdo, $id); if (!$c || $c['status'] !== 'scheduled') return 0;
    if (ml_q($pdo, "UPDATE mail_campaigns SET status = 'sending', started_at = ?, updated_at = ? WHERE id = ? AND status = 'scheduled'", [$now, $now, $id])->rowCount() !== 1) return 0;   // two runs at once: one only
    $n = 0; $who = ml_audience($pdo, $c['audience'], $now);   // before the transaction: the plan lookup may create billing tables (MySQL commits on CREATE)
    $pdo->beginTransaction();
    try {
        foreach ($who as $r) {
            ml_q($pdo, "INSERT INTO mail_queue (campaign_id, user_id, email, lang, first_name, kind, token, state, next_at, created_at) VALUES (?, ?, ?, ?, ?, 'marketing', ?, 'queued', ?, ?)",
                [$id, $r['id'], $r['email'], $r['lang'], mb_substr($r['first'], 0, 40), ml_token(), $now, $now]);
            $n++;
        }
        $pdo->commit();
    } catch (Throwable $e) { $pdo->rollBack(); ml_q($pdo, "UPDATE mail_campaigns SET status = 'scheduled' WHERE id = ?", [$id]); throw $e; }
    ml_q($pdo, 'UPDATE mail_campaigns SET recipients = ?' . ($n === 0 ? ", status = 'sent', finished_at = ?" : '') . ' WHERE id = ?', $n === 0 ? [$n, $now, $id] : [$n, $id]);
    return $n;
}
function ml_campaign_pause(PDO $pdo, int $id, bool $pause, string $why = 'manual'): bool
{
    return ml_q($pdo, 'UPDATE mail_campaigns SET status = ?, paused_reason = ?, updated_at = ? WHERE id = ? AND status = ?',
        $pause ? ['paused', $why, time(), $id, 'sending'] : ['sending', null, time(), $id, 'paused'])->rowCount() === 1;
}

/* ───── sending ───── */
/** a queued line → [to, subject, text, html, headers] (null: nothing to send any more) */
function ml_compose(PDO $pdo, array $q, array &$camps): ?array
{
    $hdr = ['X-Sweep-Id' => $q['token']];
    if ($q['campaign_id'] !== null) {
        $cid = (int) $q['campaign_id'];
        if (!array_key_exists($cid, $camps)) $camps[$cid] = ml_campaign($pdo, $cid);
        $c = $camps[$cid]; if (!$c) return null;
        $v = ml_version($c['content'], (string) $q['lang']); if (!$v) return null;
        [$s, $t, $h] = ml_render($pdo, $v, $v['lang'], (string) ($q['first_name'] ?? ''), (string) $q['token']);
        $off = ml_base() . 'api/m/u/' . $q['token'];
        $hdr += ['List-Unsubscribe' => '<' . $off . '>, <mailto:' . ml_bounce_addr() . '?subject=unsubscribe-' . $q['token'] . '>', 'List-Unsubscribe-Post' => 'List-Unsubscribe=One-Click',
            'Feedback-ID' => 'c' . $cid . ':campaign:sweep'];
        return [(string) $q['email'], $s, $t, $h, $hdr];
    }
    return [(string) $q['email'], (string) $q['subject'], (string) $q['text_body'], (string) ($q['html_body'] ?? ''), $hdr];
}
/**
 * One run of the sender (mail/send-cron.php, every minute): starts the campaigns that are due, then sends what the hour's
 * cap allows, spread over the hour (cap / 60 per run, a little more to catch up). $send(to, subject, text, html, headers, token)
 * returns true, or a string: « soft: … » (retried 3 times, 10 then 20 min later) or « hard: … » (address set aside).
 */
function ml_run(PDO $pdo, callable $send, ?int $now = null): array
{
    ml_schema($pdo); $now = $now ?? time();
    foreach (ml_q($pdo, "SELECT id FROM mail_campaigns WHERE status = 'scheduled' AND scheduled_at <= ?", [$now])->fetchAll(PDO::FETCH_COLUMN) as $cid) ml_campaign_start($pdo, (int) $cid, $now);
    ml_q($pdo, "UPDATE mail_queue SET state = 'queued' WHERE state = 'sending' AND next_at < ?", [$now - 900]);   // a run that died mid-send
    $cap = ml_cap($pdo, $now);
    $hour = (int) ml_q($pdo, "SELECT COUNT(*) FROM mail_queue WHERE kind = 'marketing' AND sent_at >= ?", [$now - 3600])->fetchColumn();
    $room = max(0, min($cap - $hour, (int) ceil($cap / 60) * 2));
    $out = ['sent' => 0, 'failed' => 0, 'skipped' => 0, 'cap' => $cap, 'hour' => $hour];
    if ($room === 0) return $out + ['left' => ml_left($pdo)];
    $rows = ml_q($pdo, "SELECT q.* FROM mail_queue q LEFT JOIN mail_campaigns c ON c.id = q.campaign_id WHERE q.state = 'queued' AND q.next_at <= ?
        AND (q.campaign_id IS NULL OR c.status = 'sending') ORDER BY CASE WHEN q.kind = 'marketing' THEN 1 ELSE 0 END, q.id LIMIT " . (int) $room, [$now])->fetchAll(PDO::FETCH_ASSOC);
    $camps = [];
    foreach ($rows as $q) {
        if (ml_q($pdo, "UPDATE mail_queue SET state = 'sending', next_at = ? WHERE id = ? AND state = 'queued'", [$now, $q['id']])->rowCount() !== 1) continue;
        $skip = $q['kind'] === 'marketing' && (ml_suppressed($pdo, (string) $q['email'])
            || ($q['user_id'] !== null && (int) ml_q($pdo, 'SELECT COUNT(*) FROM email_prefs WHERE user_id = ? AND marketing = 0', [$q['user_id']])->fetchColumn() > 0));
        $m = $skip ? null : ml_compose($pdo, $q, $camps);
        if ($m === null) { ml_q($pdo, "UPDATE mail_queue SET state = 'skipped' WHERE id = ?", [$q['id']]); $out['skipped']++; continue; }
        $r = $send($m[0], $m[1], $m[2], $m[3], $m[4], (string) $q['token']);
        if ($r === true) {
            ml_q($pdo, "UPDATE mail_queue SET state = 'sent', sent_at = ?, attempts = attempts + 1, error = NULL WHERE id = ?", [time(), $q['id']]);
            ml_q($pdo, "DELETE FROM mail_suppress WHERE email_lc = ? AND reason = 'soft'", [strtolower((string) $q['email'])]);
            if ($q['kind'] === 'marketing' && ml_setting($pdo, 'mail_warm_start') === '') ml_set_setting($pdo, 'mail_warm_start', (string) $now);
            $out['sent']++; continue;
        }
        $err = mb_substr((string) $r, 0, 250); $hard = strpos($err, 'hard:') === 0; $tries = (int) $q['attempts'] + 1;
        if ($hard || $tries >= 3) {
            ml_q($pdo, "UPDATE mail_queue SET state = 'failed', attempts = ?, error = ? WHERE id = ?", [$tries, $err, $q['id']]);
            if ($hard) { ml_suppress($pdo, (string) $q['email'], 'hard'); ml_event($pdo, (int) $q['id'], $q['campaign_id'] !== null ? (int) $q['campaign_id'] : null, 'bounce'); }
            $out['failed']++;
        } else ml_q($pdo, "UPDATE mail_queue SET state = 'queued', attempts = ?, error = ?, next_at = ? WHERE id = ?", [$tries, $err, $now + 600 * $tries, $q['id']]);
    }
    ml_watch($pdo, $now);
    return $out + ['left' => ml_left($pdo)];
}
function ml_left(PDO $pdo): int
{
    return (int) ml_q($pdo, "SELECT COUNT(*) FROM mail_queue q LEFT JOIN mail_campaigns c ON c.id = q.campaign_id WHERE q.state IN ('queued', 'sending') AND (q.campaign_id IS NULL OR c.status = 'sending')")->fetchColumn();
}
/** after a run: a campaign with nothing left is « sent »; one over the bounce or complaint limit pauses itself */
function ml_watch(PDO $pdo, int $now): void
{
    foreach (ml_q($pdo, "SELECT id FROM mail_campaigns WHERE status = 'sending'")->fetchAll(PDO::FETCH_COLUMN) as $cid) {
        $cid = (int) $cid;
        $sent = (int) ml_q($pdo, "SELECT COUNT(*) FROM mail_queue WHERE campaign_id = ? AND state IN ('sent', 'failed')", [$cid])->fetchColumn();
        if ($sent >= 100) {
            $ev = fn($t) => (int) ml_q($pdo, 'SELECT COUNT(DISTINCT queue_id) FROM mail_events WHERE campaign_id = ? AND type = ?', [$cid, $t])->fetchColumn();
            if ($ev('bounce') / $sent > ML_BOUNCE_LIMIT) { ml_campaign_pause($pdo, $cid, true, 'bounces'); continue; }
            if ($ev('complaint') / $sent > ML_COMPLAINT_LIMIT) { ml_campaign_pause($pdo, $cid, true, 'complaints'); continue; }
        }
        if ((int) ml_q($pdo, "SELECT COUNT(*) FROM mail_queue WHERE campaign_id = ? AND state IN ('queued', 'sending')", [$cid])->fetchColumn() === 0)
            ml_q($pdo, "UPDATE mail_campaigns SET status = 'sent', finished_at = ? WHERE id = ? AND status = 'sending'", [$now, $cid]);
    }
}

/* ───── tracking ───── */
function ml_event(PDO $pdo, int $qid, ?int $cid, string $type, ?string $url = null): void
{
    ml_q($pdo, 'INSERT INTO mail_events (queue_id, campaign_id, type, url, at) VALUES (?, ?, ?, ?, ?)', [$qid, $cid, $type, $url !== null ? mb_substr($url, 0, 500) : null, time()]);
}
function ml_by_token(PDO $pdo, string $token): ?array
{
    if (!preg_match('/^[a-f0-9]{24}$/', $token)) return null;
    ml_schema($pdo);
    return ml_q($pdo, 'SELECT id, campaign_id, user_id, email, lang, sent_at FROM mail_queue WHERE token = ?', [$token])->fetch(PDO::FETCH_ASSOC) ?: null;
}
/**
 * An open made by a machine, not a person: Apple Mail's privacy protection (it loads every image when the email arrives,
 * from Apple's addresses, as « Mozilla/5.0 »), security scanners, or an open in the first seconds after sending.
 */
function ml_auto_open(string $ua, string $ip, ?int $sentAt, int $now): bool
{
    if ($sentAt !== null && $now - $sentAt < 20) return true;
    if (trim($ua) === 'Mozilla/5.0' || strpos($ip, '17.') === 0) return true;
    return (bool) preg_match('/bot|crawler|spider|scanner|barracuda|mimecast|proofpoint|safelinks|python|curl|wget|headless/i', $ua);
}
/** api/m/o/<token>: the 1×1 image (never an error: a broken image would show in the email) */
function ml_open(PDO $pdo, string $token): void
{
    try {
        if ($q = ml_by_token($pdo, $token)) ml_event($pdo, (int) $q['id'], $q['campaign_id'] !== null ? (int) $q['campaign_id'] : null,
            ml_auto_open((string) ($_SERVER['HTTP_USER_AGENT'] ?? ''), (string) ($_SERVER['REMOTE_ADDR'] ?? ''), $q['sent_at'] !== null ? (int) $q['sent_at'] : null, time()) ? 'open_auto' : 'open');
    } catch (Throwable $e) { error_log('[Sweep mail] open: ' . $e->getMessage()); }
    header('Content-Type: image/gif'); header('Cache-Control: no-store, no-cache, must-revalidate, max-age=0'); header('X-Robots-Tag: noindex');
    echo base64_decode('R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7'); exit;
}
/** api/m/c/<token>?u=…&s=…: counts the click, then goes to the link (only a link signed by us: no open redirect) */
function ml_click(PDO $pdo, string $token): void
{
    $u = (string) base64_decode(strtr((string) ($_GET['u'] ?? ''), '-_', '+/'), true);
    $ok = $u !== '' && preg_match('#^(https?://|mailto:)#i', $u) && preg_match('/^[a-f0-9]{24}$/', $token)
        && hash_equals(substr(hash_hmac('sha256', $token . '|' . $u, ml_secret($pdo)), 0, 16), (string) ($_GET['s'] ?? ''));
    if (!$ok) { header('Location: ' . ml_base()); http_response_code(302); exit; }
    try {
        $q = ml_by_token($pdo, $token);
        $ua = (string) ($_SERVER['HTTP_USER_AGENT'] ?? '');
        if ($q && !preg_match('/bot|scanner|barracuda|mimecast|proofpoint|safelinks|headless/i', $ua)) ml_event($pdo, (int) $q['id'], $q['campaign_id'] !== null ? (int) $q['campaign_id'] : null, 'click', $u);
    } catch (Throwable $e) { error_log('[Sweep mail] click: ' . $e->getMessage()); }
    header('Cache-Control: no-store'); header('Referrer-Policy: no-referrer'); header('Location: ' . $u); http_response_code(302); exit;
}
function ml_unsubscribe(PDO $pdo, array $q, bool $off): void
{
    if ($q['user_id'] !== null) ml_set_marketing($pdo, (string) $q['user_id'], !$off);
    elseif ($off) ml_suppress($pdo, (string) $q['email'], 'manual');
    if ($off && !(int) ml_q($pdo, "SELECT COUNT(*) FROM mail_events WHERE queue_id = ? AND type = 'unsub'", [$q['id']])->fetchColumn())
        ml_event($pdo, (int) $q['id'], $q['campaign_id'] !== null ? (int) $q['campaign_id'] : null, 'unsub');
    if (!$off) ml_q($pdo, "DELETE FROM mail_events WHERE queue_id = ? AND type = 'unsub'", [$q['id']]);
}
/**
 * api/m/u/<token>: a page with one button. POST without on=1 unsubscribes — also the mail apps' one-click « Unsubscribe »
 * (List-Unsubscribe-Post, RFC 8058: they post « List-Unsubscribe=One-Click », no page); on=1 subscribes again.
 */
function ml_unsub_page(PDO $pdo, string $method, string $token): void
{
    $q = ml_by_token($pdo, $token);
    $lang = ml_lang($q['lang'] ?? substr((string) ($_SERVER['HTTP_ACCEPT_LANGUAGE'] ?? 'en'), 0, 2));
    $L = ML_T[$lang]; $h = fn($x) => htmlspecialchars((string) $x, ENT_QUOTES, 'UTF-8');
    $state = 'ask';
    if ($q && $method === 'POST') { $on = (string) ($_POST['on'] ?? '') === '1'; ml_unsubscribe($pdo, $q, !$on); $state = $on ? 'on' : 'off'; }
    elseif ($q && $q['user_id'] !== null && (int) ml_q($pdo, 'SELECT COUNT(*) FROM email_prefs WHERE user_id = ? AND marketing = 0', [$q['user_id']])->fetchColumn()) $state = 'off';
    [$t, $p, $label, $on] = !$q ? ['Sweep', $L['pg_bad'], '', false] : ($state === 'off' ? [$L['pg_off_t'], $L['pg_off_p'], $L['pg_off_b'], true]
        : ($state === 'on' ? [$L['pg_on_t'], $L['pg_on_p'], '', false] : [$L['pg_t'], $L['pg_p'], $L['pg_b'], false]));
    if ($lang === 'fr') { $t = str_replace(' ?', "\u{00A0}?", $t); $p = str_replace(' ?', "\u{00A0}?", $p); }
    http_response_code($q ? 200 : 404);
    header('Content-Type: text/html; charset=utf-8'); header('Cache-Control: no-store'); header('X-Robots-Tag: noindex'); header('Referrer-Policy: no-referrer');
    header("Content-Security-Policy: default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'");
    $form = $label === '' ? '' : '<form method="post" action="">' . ($on ? '<input type="hidden" name="on" value="1">' : '')
        . '<button type="submit" style="font:inherit;font-size:15px;font-weight:600;border:0;border-radius:999px;padding:13px 24px;cursor:pointer;background:' . ($on ? '#4c8dff;color:#0b0b0c' : '#2a2a30;color:#f2f2f3') . '">' . $h($label) . '</button></form>';
    echo '<!doctype html><html lang="' . $lang . '"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><title>' . $h($t) . ' · Sweep</title></head>'
        . '<body style="margin:0;min-height:100vh;background:#0b0b0c;color:#f2f2f3;font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Inter,Arial,sans-serif;display:flex;align-items:center;justify-content:center;padding:24px 16px;box-sizing:border-box">'
        . '<main style="max-width:420px;width:100%;background:#141416;border:1px solid #26262a;border-radius:26px;padding:32px 28px;box-sizing:border-box">'
        . '<div style="font-size:18px;font-weight:700;margin-bottom:24px">sweep</div><h1 style="font-size:22px;line-height:1.25;margin:0 0 10px">' . $h($t) . '</h1>'
        . '<p style="margin:0 0 24px;font-size:15px;line-height:1.55;color:#b9b9c2">' . $h($p) . '</p>' . $form . '</main></body></html>';
    exit;
}

/* ───── bounces (mail/bounce.php reads what reaches bounces@) ───── */
/**
 * What a message that came back says: ['token' => …, 'type' => bounce|soft_bounce|complaint|unsub] or null (auto-reply,
 * delay warning, or not about one of our emails). Our token is in the X-Sweep-Id header and the Message-ID of every email,
 * which bounce reports quote.
 */
function ml_parse_return(string $raw): ?array
{
    if (preg_match('/^Subject:\s*unsubscribe-([a-f0-9]{24})\s*$/im', $raw, $m)) return ['token' => $m[1], 'type' => 'unsub'];   // List-Unsubscribe by mailto
    if (!preg_match('/X-Sweep-Id:\s*([a-f0-9]{24})/i', $raw, $m) && !preg_match('/Message-ID:\s*<([a-f0-9]{24})\.m@/i', $raw, $m)) return null;
    $tok = $m[1];
    if (preg_match('/Feedback-Type:\s*abuse/i', $raw)) return ['token' => $tok, 'type' => 'complaint'];
    if (preg_match('/^Action:\s*delayed/im', $raw) || preg_match('/has not yet been delivered|message is delayed|delivery (?:has been )?delayed/i', $raw)) return null;
    if (preg_match('/^Status:\s*5\.\d{1,3}\.\d{1,3}/im', $raw) || preg_match('/permanent error|permanently|user unknown|no such user|does not exist|mailbox unavailable|address rejected|\b55[0-4][ -]/i', $raw)) return ['token' => $tok, 'type' => 'bounce'];
    if (preg_match('/^Status:\s*4\.\d{1,3}\.\d{1,3}/im', $raw) || preg_match('/temporary|mailbox (?:is )?full|over quota|\b4[25]\d[ -]/i', $raw)) return ['token' => $tok, 'type' => 'soft_bounce'];
    if (preg_match('/^Auto-Submitted:\s*auto-replied/im', $raw) || preg_match('/out of (?:the )?office|automatic reply|réponse automatique|respuesta automática/i', $raw)) return null;
    return preg_match('/delivery (?:status notification|failure|failed)|undeliver|returned mail|mail delivery/i', $raw) ? ['token' => $tok, 'type' => 'bounce'] : null;
}
function ml_apply_return(PDO $pdo, array $r): bool
{
    $q = ml_by_token($pdo, $r['token']); if (!$q) return false;
    $cid = $q['campaign_id'] !== null ? (int) $q['campaign_id'] : null;
    if ($r['type'] === 'unsub') { ml_unsubscribe($pdo, $q, true); return true; }
    if ((int) ml_q($pdo, 'SELECT COUNT(*) FROM mail_events WHERE queue_id = ? AND type = ?', [$q['id'], $r['type']])->fetchColumn()) return true;   // a report sent twice
    ml_event($pdo, (int) $q['id'], $cid, $r['type']);
    if ($r['type'] === 'complaint') { ml_suppress($pdo, (string) $q['email'], 'complaint'); if ($q['user_id'] !== null) ml_set_marketing($pdo, (string) $q['user_id'], false); }
    else ml_suppress($pdo, (string) $q['email'], $r['type'] === 'bounce' ? 'hard' : 'soft');
    return true;
}

/* ───── statistics ───── */
function ml_rate(int $a, int $b): ?float { return $b > 0 ? round($a * 100 / $b, 1) : null; }
/** the numbers of one campaign (or of every campaign line since $since when $cid is null) */
function ml_stats(PDO $pdo, ?int $cid, int $since = 0): array
{
    ml_schema($pdo);
    [$w, $a] = $cid !== null ? ['q.campaign_id = ?', [$cid]] : ["q.kind = 'marketing' AND q.sent_at >= ?", [$since]];
    $st = []; foreach (ml_q($pdo, "SELECT q.state, COUNT(*) n FROM mail_queue q WHERE $w GROUP BY q.state", $a)->fetchAll(PDO::FETCH_ASSOC) as $r) $st[$r['state']] = (int) $r['n'];
    $ev = []; foreach (ml_q($pdo, "SELECT e.type, COUNT(DISTINCT e.queue_id) n FROM mail_events e JOIN mail_queue q ON q.id = e.queue_id WHERE $w GROUP BY e.type", $a)->fetchAll(PDO::FETCH_ASSOC) as $r) $ev[$r['type']] = (int) $r['n'];
    $real = (int) ml_q($pdo, "SELECT COUNT(DISTINCT e.queue_id) FROM mail_events e JOIN mail_queue q ON q.id = e.queue_id WHERE $w AND e.type IN ('open', 'click')", $a)->fetchColumn();   // a click is an open
    $any = (int) ml_q($pdo, "SELECT COUNT(DISTINCT e.queue_id) FROM mail_events e JOIN mail_queue q ON q.id = e.queue_id WHERE $w AND e.type IN ('open', 'open_auto', 'click')", $a)->fetchColumn();
    $sent = $st['sent'] ?? 0; $bounce = $ev['bounce'] ?? 0;
    // delivered: sent and not bounced afterwards (a refusal at sending is « failed », never « sent »)
    $later = (int) ml_q($pdo, "SELECT COUNT(DISTINCT e.queue_id) FROM mail_events e JOIN mail_queue q ON q.id = e.queue_id WHERE $w AND e.type = 'bounce' AND q.state = 'sent'", $a)->fetchColumn();
    $delivered = max(0, $sent - $later); $clicks = $ev['click'] ?? 0;
    return ['recipients' => array_sum($st), 'queued' => ($st['queued'] ?? 0) + ($st['sending'] ?? 0), 'sent' => $sent, 'failed' => $st['failed'] ?? 0, 'skipped' => $st['skipped'] ?? 0,
        'delivered' => $delivered, 'bounces' => $bounce, 'soft' => $ev['soft_bounce'] ?? 0, 'opens' => $real, 'opens_auto' => max(0, $any - $real), 'clicks' => $clicks,
        'unsubs' => $ev['unsub'] ?? 0, 'complaints' => $ev['complaint'] ?? 0,
        'open_rate' => ml_rate($real, $delivered), 'open_rate_all' => ml_rate($any, $delivered), 'click_rate' => ml_rate($clicks, $delivered), 'click_to_open' => ml_rate($clicks, $real),
        'unsub_rate' => ml_rate($ev['unsub'] ?? 0, $delivered), 'bounce_rate' => ml_rate($bounce, $sent + ($st['failed'] ?? 0))];
}
function ml_campaign_report(PDO $pdo, int $cid): array
{
    $c = ml_campaign($pdo, $cid); if (!$c) return [];
    $s = ml_stats($pdo, $cid);
    $byLang = [];
    foreach (ML_LANGS as $l) {
        $n = (int) ml_q($pdo, "SELECT COUNT(*) FROM mail_queue WHERE campaign_id = ? AND lang = ? AND state = 'sent'", [$cid, $l])->fetchColumn(); if (!$n) continue;
        $o = (int) ml_q($pdo, "SELECT COUNT(DISTINCT e.queue_id) FROM mail_events e JOIN mail_queue q ON q.id = e.queue_id WHERE q.campaign_id = ? AND q.lang = ? AND e.type IN ('open', 'click')", [$cid, $l])->fetchColumn();
        $k = (int) ml_q($pdo, "SELECT COUNT(DISTINCT e.queue_id) FROM mail_events e JOIN mail_queue q ON q.id = e.queue_id WHERE q.campaign_id = ? AND q.lang = ? AND e.type = 'click'", [$cid, $l])->fetchColumn();
        $byLang[] = ['lang' => $l, 'sent' => $n, 'open_rate' => ml_rate($o, $n), 'click_rate' => ml_rate($k, $n)];
    }
    $links = array_map(fn($r) => ['url' => $r['url'], 'clicks' => (int) $r['n']], ml_q($pdo, "SELECT url, COUNT(DISTINCT queue_id) n FROM mail_events WHERE campaign_id = ? AND type = 'click' GROUP BY url ORDER BY n DESC LIMIT 10", [$cid])->fetchAll(PDO::FETCH_ASSOC));
    // the first 48 hours, hour by hour: people who opened (a click counts), and who clicked
    $t0 = $c['started_at'] ?? 0; $hours = array_fill(0, 48, [0, 0]);
    if ($t0) foreach (ml_q($pdo, "SELECT type, queue_id, MIN(at) at FROM mail_events WHERE campaign_id = ? AND type IN ('open', 'click') AND at < ? GROUP BY type, queue_id", [$cid, $t0 + 48 * 3600])->fetchAll(PDO::FETCH_ASSOC) as $r) {
        $h = max(0, min(47, intdiv((int) $r['at'] - $t0, 3600))); $hours[$h][$r['type'] === 'click' ? 1 : 0]++;
    }
    return ['campaign' => $c, 'stats' => $s, 'langs' => $byLang, 'links' => $links, 'hours' => $hours];
}
function ml_overview(PDO $pdo, ?int $now = null): array
{
    ml_schema($pdo); $now = $now ?? time();
    $list = array_map(function ($r) use ($pdo) {
        $s = ml_stats($pdo, (int) $r['id']);
        return ['id' => (int) $r['id'], 'name' => $r['name'], 'status' => $r['status'], 'paused_reason' => $r['paused_reason'], 'recipients' => (int) $r['recipients'],
            'scheduled_at' => $r['scheduled_at'] !== null ? (int) $r['scheduled_at'] : null, 'started_at' => $r['started_at'] !== null ? (int) $r['started_at'] : null,
            'updated_at' => (int) $r['updated_at'], 'sent' => $s['sent'], 'queued' => $s['queued'], 'open_rate' => $s['open_rate'], 'click_rate' => $s['click_rate']];
    }, ml_q($pdo, 'SELECT id, name, status, paused_reason, recipients, scheduled_at, started_at, updated_at FROM mail_campaigns ORDER BY COALESCE(started_at, scheduled_at, updated_at) DESC LIMIT 100')->fetchAll(PDO::FETCH_ASSOC));
    $cap = ml_cap($pdo, $now);
    return ['now' => $now, 'campaigns' => $list, 'month' => ml_stats($pdo, null, $now - 30 * 86400), 'list' => ml_list_health($pdo),
        'sending' => ['cap' => $cap, 'last_hour' => (int) ml_q($pdo, "SELECT COUNT(*) FROM mail_queue WHERE kind = 'marketing' AND sent_at >= ?", [$now - 3600])->fetchColumn(), 'left' => ml_left($pdo),
            'warm_start' => (int) ml_setting($pdo, 'mail_warm_start', '0') ?: null, 'max' => max(1, (int) (((array) (ml_cfg()['mail_per_hour'] ?? []))['max'] ?? 500))],
        'address' => ml_address($pdo), 'from' => ml_from(), 'smtp' => !empty(((array) (ml_cfg()['smtp'] ?? []))['pass'])];
}
