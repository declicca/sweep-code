<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli' && realpath((string) ($_SERVER['SCRIPT_FILENAME'] ?? '')) === realpath(__FILE__)) { http_response_code(404); exit; }
/**
 * Sweep — Admin › Emails (administrators only, api/admin/mail…) and the links in the emails (api/m/…, no session).
 *   GET  api/admin/mail                          overview: campaigns, last 30 days, the list, the sending pace
 *   POST api/admin/mail/campaigns                a new draft {name, content, audience}
 *   GET  api/admin/mail/campaigns/<id>           the campaign and its numbers
 *   POST api/admin/mail/campaigns/<id>           save a draft · DELETE: delete a draft
 *   POST api/admin/mail/campaigns/<id>/send      {at: unix time, or none for now} · …/unschedule · …/pause {pause} · …/duplicate
 *   POST api/admin/mail/audience                 {audience} → how many traders it reaches, per language
 *   POST api/admin/mail/preview                  {content, lang} → subject and HTML (nothing tracked)
 *   POST api/admin/mail/test                     {content, lang} → to the administrator's own address, at once
 *   POST api/admin/mail/settings                 {address}: the postal address at the bottom (required by anti-spam laws)
 */
require_once __DIR__ . '/mail-core.php';
require_once __DIR__ . '/mail-smtp.php';

/** api/m/o, api/m/c, api/m/u: before the session and the CSRF check (mail apps and the trader's inbox call them) */
function ml_public_route(string $route, string $method): void
{
    if (!preg_match('#^api/m/([ocu])/([a-f0-9]{24})$#', $route, $m)) return;
    if ($m[1] === 'o') ml_open(db(), $m[2]);
    if ($m[1] === 'c') ml_click(db(), $m[2]);
    ml_unsub_page(db(), $method, $m[2]);
}

function ml_admin_route(string $route, string $method, array $me): void
{
    $pdo = db(); ml_schema($pdo);
    $b = $method === 'POST' ? body_json(262144) : [];
    $err = fn(string $code, int $st = 400) => json_out($st, ['error' => $code]);
    if ($route === 'api/admin/mail' && $method === 'GET') json_out(200, ml_overview($pdo));
    if ($route === 'api/admin/mail/campaigns' && $method === 'POST') json_out(200, ml_campaign_save($pdo, null, $b));
    if ($route === 'api/admin/mail/audience' && $method === 'POST') {
        $who = ml_audience($pdo, (array) ($b['audience'] ?? []));
        $by = array_fill_keys(ML_LANGS, 0); foreach ($who as $r) $by[$r['lang']]++;
        json_out(200, ['count' => count($who), 'langs' => $by]);
    }
    if (($route === 'api/admin/mail/preview' || $route === 'api/admin/mail/test') && $method === 'POST') {
        $content = ml_clean_content($b['content'] ?? []); $lang = ml_lang($b['lang'] ?? 'en');
        $v = ml_version($content, $lang);
        if (!$v) $err('content');
        $first = trim((string) ($me['first_name'] ?? '')) ?: (string) ($me['username'] ?? '');
        [$s, $t, $h] = ml_render($pdo, $v, $v['lang'], $first, '', false);
        if ($route === 'api/admin/mail/preview') json_out(200, ['subject' => $s, 'html' => $h, 'lang' => $v['lang']]);
        $to = trim((string) ($me['email'] ?? ''));
        if ($to === '') $err('no_email');
        $smtp = new MlSmtp((array) ($GLOBALS['cfg']['smtp'] ?? []));
        $r = $smtp->send($to, '[Test] ' . $s, $t, $h, [], ml_token()); $smtp->close();
        $r === true ? json_out(200, ['ok' => true, 'to' => $to]) : json_out(502, ['error' => 'send', 'detail' => $r]);
    }
    if ($route === 'api/admin/mail/settings' && $method === 'POST') {
        $a = mb_substr(trim((string) ($b['address'] ?? '')), 0, 200);
        if (mb_strlen($a) < 10) $err('address');
        ml_set_setting($pdo, 'mail_address', $a); json_out(200, ['ok' => true]);
    }
    if (preg_match('#^api/admin/mail/campaigns/(\d+)(?:/(send|unschedule|pause|duplicate))?$#', $route, $m)) {
        $id = (int) $m[1]; $act = $m[2] ?? '';
        $c = ml_campaign($pdo, $id); if (!$c) $err('not_found', 404);
        if ($act === '' && $method === 'GET') json_out(200, ml_campaign_report($pdo, $id) + ['audience_count' => in_array($c['status'], ['draft', 'scheduled'], true) ? count(ml_audience($pdo, $c['audience'])) : null]);
        if ($act === '' && $method === 'POST') { $r = ml_campaign_save($pdo, $id, $b); isset($r['error']) ? $err($r['error'], 409) : json_out(200, $r); }
        if ($act === '' && $method === 'DELETE') {
            if (!in_array($c['status'], ['draft', 'scheduled'], true)) $err('sent', 409);
            ml_q($pdo, 'DELETE FROM mail_campaigns WHERE id = ?', [$id]); json_out(200, ['ok' => true]);
        }
        if ($method !== 'POST') $err('method', 405);
        if ($act === 'send') {
            $at = isset($b['at']) ? (int) $b['at'] : null;
            if ($at !== null && ($at < time() - 60 || $at > time() + 90 * 86400)) $err('at');
            $r = ml_campaign_schedule($pdo, $id, $at); isset($r['error']) ? $err($r['error'], 409) : json_out(200, $r);
        }
        if ($act === 'unschedule') {
            ml_q($pdo, "UPDATE mail_campaigns SET status = 'draft', scheduled_at = NULL, updated_at = ? WHERE id = ? AND status = 'scheduled'", [time(), $id]);
            json_out(200, ['ok' => true]);
        }
        if ($act === 'pause') json_out(200, ['ok' => ml_campaign_pause($pdo, $id, !empty($b['pause']))]);
        if ($act === 'duplicate') {
            $L = ['en' => ' (copy)', 'fr' => ' (copie)', 'es' => ' (copia)'][ml_lang($b['lang'] ?? 'en')] ?? ' (copy)';
            json_out(200, ml_campaign_save($pdo, null, ['name' => mb_substr($c['name'], 0, 110) . $L, 'content' => $c['content'], 'audience' => $c['audience']]));
        }
    }
    $err('not_found', 404);
}
