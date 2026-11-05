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
 *   POST api/admin/mail/campaigns/<id>/auto      {on}: an automation switched on or off (mail/mail-auto.php)
 *   POST api/admin/mail/campaigns/<id>/proposal  {take}: an automation's new text (ma_upgrade) taken, or set aside
 *   POST api/admin/mail/audience                 {audience} → how many traders it reaches, per language
 *   POST api/admin/mail/preview                  {content, lang} → subject and HTML (nothing tracked)
 *   POST api/admin/mail/test                     {content, lang} → to the administrator's own address, at once
 *   POST api/admin/mail/settings                 {address}: the postal address at the bottom (required by anti-spam laws)
 */
require_once __DIR__ . '/mail-core.php';
require_once __DIR__ . '/mail-smtp.php';
require_once __DIR__ . '/mail-auto.php';

/** api/m/o, api/m/c, api/m/u, api/m/r: before the session and the CSRF check (mail apps and the trader's inbox call them) */
function ml_public_route(string $route, string $method): void
{
    if (!preg_match('#^api/m/([ocur])/([a-f0-9]{24})$#', $route, $m)) return;
    if ($m[1] === 'o') ml_open(db(), $m[2]);
    if ($m[1] === 'c') ml_click(db(), $m[2]);
    if ($m[1] === 'r') ml_answer_page(db(), $method, $m[2]);
    ml_unsub_page(db(), $method, $m[2]);
}

/**
 * A one-click answer, as Admin › Feedback keeps it: one line per email and question (a second answer replaces the first;
 * a comment is added to it). The email's « answer » event once. False: not a trader's email (nothing kept).
 */
function ml_answer_save(PDO $pdo, array $q, int $qn, string $a, ?string $comment): bool
{
    if ($q['user_id'] === null || !function_exists('fb_schema')) return false;
    fb_schema($pdo);
    $cid = $q['campaign_id'] !== null ? (int) $q['campaign_id'] : null;
    $c = $cid !== null ? ml_campaign($pdo, $cid) : null;
    $v = $c ? ml_version($c['content'], (string) $q['lang']) : null;
    $Q = $v ? (ml_questions($v['body'], ['{app}' => ml_base()])[$qn] ?? null) : null;
    $i = $Q ? array_search($a, $Q['opts'], true) : false;
    $rating = $Q && $Q['kind'] === 'note' && $Q['opts'] === ['1', '2', '3', '4', '5'] ? (int) $a : null;   // a note from 1 to 5 counts in the experience rating
    $now = time();
    $old = ml_q($pdo, 'SELECT id, message FROM feedback WHERE src_queue = ? AND src_q = ?', [(int) $q['id'], $qn])->fetch(PDO::FETCH_ASSOC);
    $more = $comment !== null && trim($comment) !== '';
    $msg = $more ? mb_substr(trim($comment), 0, 2000) : (string) ($old['message'] ?? '');
    if ($old) ml_q($pdo, 'UPDATE feedback SET answer = ?, answer_i = ?, rating = ?, message = ?, updated_at = ? WHERE id = ?', [$a, $i !== false ? $i : null, $rating, $msg, $now, (int) $old['id']]);
    else ml_q($pdo, 'INSERT INTO feedback (user_id, type, rating, message, page, context, status, created_at, src_queue, src_campaign, src_q, question, answer, answer_i) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
        [(string) $q['user_id'], $rating !== null ? 'experience' : 'answer', $rating, $msg, 'email', json_encode(['lang' => $q['lang'], 'plan' => ml_plan_of($pdo, (string) $q['user_id'])]), 'new', $now,
         (int) $q['id'], $cid, $qn, $Q['question'] ?? null, $a, $i !== false ? $i : null]);
    $fid = $old ? (int) $old['id'] : (int) $pdo->lastInsertId();
    if (!(int) ml_q($pdo, "SELECT COUNT(*) FROM mail_events WHERE queue_id = ? AND type = 'answer'", [(int) $q['id']])->fetchColumn()) ml_event($pdo, (int) $q['id'], $cid, 'answer');
    if ($more && function_exists('fb_notify')) fb_notify($pdo, $fid, 'answer', $rating, $a . ' — ' . $msg, (string) $q['user_id']);   // only a written comment reaches the support box
    return true;
}
/**
 * api/m/r/<token>?q=…&a=…&s=…: the one-click answer (signed: a link changed by hand is refused). The page records it on
 * its own (a script: link scanners, which open every link without running it, never answer for the trader); its form adds a
 * comment, and records the answer too without the script.
 */
function ml_answer_page(PDO $pdo, string $method, string $token): void
{
    $in = $method === 'POST' ? $_POST : $_GET;
    $qn = (int) ($in['q'] ?? -1); $a = mb_substr((string) ($in['a'] ?? ''), 0, 120);
    $q = ml_by_token($pdo, $token);
    $ok = $q && $qn >= 0 && $qn < 10 && $a !== '' && hash_equals(ml_answer_sig($pdo, $token, $qn, $a), (string) ($in['s'] ?? ''));
    $lang = ml_lang($q['lang'] ?? substr((string) ($_SERVER['HTTP_ACCEPT_LANGUAGE'] ?? 'en'), 0, 2));
    $L = ML_T[$lang]; $h = fn($x) => htmlspecialchars((string) $x, ENT_QUOTES, 'UTF-8');
    $nb = fn(string $x) => $lang === 'fr' ? preg_replace('/ ([?:!;])/u', "\u{00A0}$1", $x) : $x;
    if (!$ok) { http_response_code(404); ml_page($lang, 'Sweep', '<h1>Sweep</h1><p>' . $h($L['pg_bad']) . '</p>'); }
    if ($method === 'POST') {
        try { ml_answer_save($pdo, $q, $qn, $a, isset($_POST['more']) ? (string) $_POST['more'] : null); } catch (Throwable $e) { error_log('[Sweep mail] answer: ' . $e->getMessage()); }
        if (!empty($_POST['auto'])) { http_response_code(204); exit; }   // the page's own script
        ml_page($lang, $L['ans_done_t'], '<h1>' . $h($nb($L['ans_done_t'])) . '</h1><p>' . $h($nb($L['ans_done_p'])) . '</p><a class="b p" href="' . $h(ml_base()) . '">' . $h($L['ans_open']) . '</a>');
    }
    $nonce = bin2hex(random_bytes(12));
    $hidden = '<input type="hidden" name="q" value="' . $qn . '"><input type="hidden" name="a" value="' . $h($a) . '"><input type="hidden" name="s" value="' . $h((string) $in['s']) . '">';
    ml_page($lang, $L['ans_t'], '<h1>' . $h($nb($L['ans_t'])) . '</h1><p>' . $h($nb($L['ans_p'])) . ' <span class="a">' . $h($a) . '</span></p>'
        . '<form method="post" action="">' . $hidden . '<label for="more">' . $h($nb($L['ans_more'])) . '</label><textarea id="more" name="more" maxlength="2000"></textarea><button type="submit" class="p">' . $h($L['ans_send']) . '</button></form>',
        $nonce, "(function(){var f=document.querySelector('form'),d=new FormData(f);d.delete('more');d.append('auto','1');fetch(location.pathname,{method:'POST',body:new URLSearchParams(d),credentials:'omit'}).catch(function(){});})();");
}

function ml_admin_route(string $route, string $method, array $me): void
{
    $pdo = db(); ml_schema($pdo); ma_seed($pdo);
    $b = $method === 'POST' ? body_json(262144) : [];
    $err = fn(string $code, int $st = 400) => json_out($st, ['error' => $code]);
    if ($route === 'api/admin/mail' && $method === 'GET') {
        $o = ml_overview($pdo);
        $o['autos'] = array_values(array_filter(array_map(fn($r) => ($i = ma_info($r['auto'])) ? $r + $i : null, $o['autos'])));   // in the catalog's order
        usort($o['autos'], fn($p, $q) => $p['order'] <=> $q['order']);
        json_out(200, $o);
    }
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
        [$s, $t, $h] = ml_render($pdo, $v, $v['lang'], $first, '', false, ['milestone' => 10, 'days' => 10, 'plan' => 'Pro', 'firm' => 'Topstep'] + mu_example($v['lang']));   // an automation's values, as an example
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
    if (preg_match('#^api/admin/mail/campaigns/(\d+)(?:/(send|unschedule|pause|duplicate|auto|proposal))?$#', $route, $m)) {
        $id = (int) $m[1]; $act = $m[2] ?? '';
        $c = ml_campaign($pdo, $id); if (!$c) $err('not_found', 404);
        if ($c['auto'] !== null && !in_array($act, ['', 'auto', 'proposal'], true) || ($c['auto'] !== null && $method === 'DELETE')) $err('auto', 409);   // an automation is switched on or off, never sent by hand nor deleted
        if ($act === 'auto' && $method === 'POST') {
            if ($c['auto'] === null) $err('not_auto', 409);
            ml_q($pdo, 'UPDATE mail_campaigns SET status = ?, updated_at = ? WHERE id = ?', [!empty($b['on']) ? 'active' : 'off', time(), $id]);
            json_out(200, ['ok' => true, 'status' => !empty($b['on']) ? 'active' : 'off']);
        }
        if ($act === 'proposal' && $method === 'POST') { ml_campaign_proposal($pdo, $c, !empty($b['take'])); json_out(200, ['ok' => true]); }
        if ($act === '' && $method === 'GET') json_out(200, ml_campaign_report($pdo, $id) + ['info' => $c['auto'] !== null ? ma_info($c['auto']) : null, 'audience_count' => in_array($c['status'], ['draft', 'scheduled'], true) ? count(ml_audience($pdo, $c['audience'])) : null]);
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
