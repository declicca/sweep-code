<?php
declare(strict_types=1);
/**
 * Sweep — our own emailing (mail/mail-core.php), on a throwaway SQLite database (never the live one):
 *   php tests/mail_test.php
 *  - audience: real traders with an address only; filters (language, signed up, seen, not seen); unsubscribed and set-aside skipped;
 *  - the email: {first}, French no-break spaces, signed tracked links, the open image, the unsubscribe link and headers (one click);
 *  - sending: the hourly cap spread over the hour, doubled each week from the first email, never over the maximum;
 *    unsubscribed after the start → skipped; hard refusal → set aside; soft → retried, then failed; the campaign ends « sent »;
 *  - opens by a machine (Apple Mail's privacy protection, scanners, the first seconds) apart from real ones; clicks;
 *  - what comes back to bounces@: bounce reports (Exim and DSN), soft, complaints, unsubscribe by email; auto-replies and delays ignored;
 *  - the numbers (delivered, open and click rates, per language, the 48 hours) and the automatic pause above 3 % bounces.
 */
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
$app = dirname(__DIR__);
putenv('SWEEP_TEST_DB');   // the real sender is never called here: every send goes through the fake below
$pdo = new PDO('sqlite::memory:', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC]);
$pdo->exec('CREATE TABLE users (id TEXT PRIMARY KEY, username TEXT, email TEXT, lang TEXT, first_name TEXT, created_at TEXT, last_login TEXT, disabled INTEGER DEFAULT 0, is_admin INTEGER DEFAULT 0, is_internal INTEGER DEFAULT 0)');
$pdo->exec('CREATE TABLE app_settings (k TEXT PRIMARY KEY, v TEXT NOT NULL)');
$cfg = ['app_url' => 'https://app.test/', 'mail_per_hour' => ['start' => 100, 'max' => 500]];
require $app . '/mail/mail-core.php';
$pass = 0; $fail = 0;
$ok = function (bool $c, string $what) use (&$pass, &$fail) { echo ($c ? 'ok   ' : 'FAIL ') . $what . "\n"; $c ? $pass++ : $fail++; };
$now = strtotime('2026-11-03 12:00:00 UTC');
$iso = fn(int $days) => gmdate('Y-m-d\TH:i:s\Z', $now - $days * 86400);
$add = function (string $id, string $email, string $lang, string $first, int $joined, ?int $seen, array $x = []) use ($pdo, $iso) {
    $pdo->prepare('INSERT INTO users (id, username, email, lang, first_name, created_at, last_login, disabled, is_admin, is_internal) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)')
        ->execute([$id, $id, $email, $lang, $first, $iso($joined), $seen === null ? null : $iso($seen), $x['disabled'] ?? 0, $x['admin'] ?? 0, $x['internal'] ?? 0]);
};
$add('u1', 'ana@t.dev', 'fr', 'Ana', 3, 1);
$add('u2', 'ben@t.dev', 'en', 'Ben', 40, 2);
$add('u3', 'cruz@t.dev', 'es', '', 100, 60);
$add('u4', 'dan@t.dev', 'en', 'Dan', 200, null);
$add('u5', 'off@t.dev', 'en', 'Off', 10, 1);
$add('u6', 'gone@t.dev', 'en', 'Gone', 10, 1);
$add('a1', 'admin@t.dev', 'fr', 'Mateo', 300, 0, ['admin' => 1]);
$add('i1', 'qa@t.dev', 'en', 'QA', 5, 0, ['internal' => 1]);
$add('d1', 'dis@t.dev', 'en', 'Dis', 5, 0, ['disabled' => 1]);
$add('n1', '', 'en', 'NoMail', 5, 0);
ml_schema($pdo);
ml_set_marketing($pdo, 'u5', false);
ml_suppress($pdo, 'GONE@t.dev', 'hard');
$ids = fn(array $a) => implode(',', array_map(fn($r) => $r['id'], ml_audience($pdo, $a, $now)));

/* ── audience ── */
$ok($ids([]) === 'u1,u2,u3,u4', 'audience: real traders with an address, minus unsubscribed and set aside (' . $ids([]) . ')');
$ok($ids(['lang' => 'fr']) === 'u1' && $ids(['lang' => 'es']) === 'u3', 'audience: by language');
$ok($ids(['joined' => 30]) === 'u1', 'audience: signed up within 30 days');
$ok($ids(['active' => 7]) === 'u1,u2', 'audience: seen within 7 days');
$ok($ids(['inactive' => 30]) === 'u3,u4', 'audience: not seen for 30 days (never logged in again: since sign-up)');
$ok($ids(['lang' => 'xx', 'plan' => 'gold']) === 'u1,u2,u3,u4', 'audience: unknown filters ignored');
$h = ml_list_health($pdo);
$ok($h === ['total' => 6, 'reachable' => 4, 'unsubscribed' => 1, 'suppressed' => 1], 'the list: 6 traders, 4 reachable, 1 unsubscribed, 1 set aside (' . json_encode($h) . ')');

/* ── the email ── */
$content = ['en' => ['subject' => 'News for {first}', 'preheader' => 'Two minutes', 'body' => "# What is new\n\nHello {first}, read **this** [guide](https://makeitsweep.com/guide).\n\n[[Open Sweep|https://app.makeitsweep.com/#dashboard]]\n\nBad [link](javascript:alert(1))."],
    'fr' => ['subject' => 'Du nouveau, {first} ?', 'preheader' => '', 'body' => "Salut {first} : voici « la suite » !"], 'es' => ['subject' => '', 'preheader' => '', 'body' => '']];
$c = ml_clean_content($content);
$ok(ml_version($c, 'es')['lang'] === 'en' && ml_version($c, 'fr')['lang'] === 'fr', 'an empty version (ES): the English one is sent');
[$s, $t, $hh] = ml_render($pdo, ml_version($c, 'en'), 'en', 'Ben', 'abcdefabcdefabcdefabcdef');
$ok($s === 'News for Ben' && strpos($t, 'Hello Ben') !== false, 'the email: {first} in the subject and the body');
[, , $h3] = ml_render($pdo, ml_version($c, 'en'), 'en', '', 'abcdefabcdefabcdefabcdef');
$ok(strpos($h3, 'Hello trader') !== false, 'the email: « trader » without a first name');
preg_match_all('#href="(https://app\.test/api/m/c/abcdefabcdefabcdefabcdef\?u=([^&"]+)&amp;s=([0-9a-f]{16}))"#', $hh, $mm);
$urls = array_map(fn($u) => base64_decode(strtr($u, '-_', '+/')), $mm[2]);
$ok($urls === ['https://makeitsweep.com/guide', 'https://app.makeitsweep.com/#dashboard'], 'the email: the link and the button go through api/m/c (' . implode(' ', $urls) . ')');
$ok($mm[3][0] === substr(hash_hmac('sha256', 'abcdefabcdefabcdefabcdef|https://makeitsweep.com/guide', ml_secret($pdo)), 0, 16), 'the email: each tracked link is signed (no open redirect)');
$ok(strpos($hh, 'javascript:') === false && strpos($hh, 'Bad link') !== false, 'the email: a link that is not http(s) or mailto stays plain text');
$ok(strpos($hh, 'api/m/o/abcdefabcdefabcdefabcdef') !== false && strpos($hh, 'api/m/u/abcdefabcdefabcdefabcdef') !== false && strpos($hh, 'Laval') !== false, 'the email: open image, unsubscribe link, postal address');
$ok(strpos($hh, '<h2') !== false && strpos($hh, '<b style') !== false && strpos($hh, 'Two minutes') !== false, 'the email: title, bold, hidden preheader');
$ok(strpos($t, 'Open Sweep: https://app.test/api/m/c/') !== false && strpos($t, 'Unsubscribe: https://app.test/api/m/u/') !== false, 'the text version: button and unsubscribe as plain links');
[$sf, $tf] = ml_render($pdo, ml_version($c, 'fr'), 'fr', 'Ana', 'abcdefabcdefabcdefabcdef');
$ok($sf === "Du nouveau, Ana\u{00A0}?" && strpos($tf, "Ana\u{00A0}: voici «\u{00A0}la suite\u{00A0}»\u{00A0}!") !== false && strpos($tf, 'Me désinscrire') !== false, 'French: no-break spaces, French footer');
[, , $hp] = ml_render($pdo, ml_version($c, 'en'), 'en', 'Ben', '', false);
$ok(strpos($hp, 'api/m/') === false && strpos($hp, 'href="https://makeitsweep.com/guide"') !== false, 'preview and test: nothing tracked');

/* ── campaign → queue → sending ── */
$id = ml_campaign_save($pdo, null, ['name' => 'Launch', 'content' => $content, 'audience' => []])['id'];
$ok(ml_campaign_schedule($pdo, $id, $now + 3600) === ['ok' => true], 'send at a time: scheduled');
$sent = []; $fake = function ($to, $s, $t, $h, $hd, $tok) use (&$sent) { $sent[] = compact('to', 's', 'hd', 'tok'); return $to === 'dan@t.dev' ? 'hard: 550 5.1.1 no such user' : true; };
$r = ml_run($pdo, $fake, $now);
$ok($r['sent'] === 0 && ml_campaign($pdo, $id)['status'] === 'scheduled', 'before its time: nothing goes');
ml_set_marketing($pdo, 'u3', false);   // unsubscribes between the start and the sending… (set after the start below)
ml_set_marketing($pdo, 'u3', true);
$r = ml_run($pdo, $fake, $now + 3600);
$cc = ml_campaign($pdo, $id);
$ok($cc['recipients'] === 4 && $r['cap'] === 100, 'at its time: 4 recipients queued, cap 100 an hour');
$ok($r['sent'] === 3 && $r['failed'] === 1, 'one run: 4 tried (cap 100 / 60 × 2 = 4), 3 sent, 1 refused (' . json_encode($r) . ')');
$ok(ml_suppressed($pdo, 'dan@t.dev') && (int) ml_q($pdo, "SELECT COUNT(*) FROM mail_events WHERE type = 'bounce'")->fetchColumn() === 1, 'hard refusal: address set aside, counted as a bounce');
$one = $sent[0];
$ok($one['hd']['List-Unsubscribe-Post'] === 'List-Unsubscribe=One-Click' && strpos($one['hd']['List-Unsubscribe'], '<https://app.test/api/m/u/' . $one['tok'] . '>') === 0
    && strpos($one['hd']['List-Unsubscribe'], 'mailto:bounces@makeitsweep.com?subject=unsubscribe-' . $one['tok']) !== false && $one['hd']['X-Sweep-Id'] === $one['tok'], 'headers: one-click unsubscribe (link + mailto), our token');
$byTo = []; foreach ($sent as $x) $byTo[$x['to']] = $x['s'];
$ok(($byTo['ana@t.dev'] ?? '') === "Du nouveau, Ana\u{00A0}?" && ($byTo['cruz@t.dev'] ?? '') === 'News for trader', 'each trader gets their language (Spanish: the English version)');
$ok(ml_campaign($pdo, $id)['status'] === 'sent', 'nothing left: « sent »');
$ok(ml_setting($pdo, 'mail_warm_start') === (string) ($now + 3600), 'the warm-up starts with the first email');

/* ── pace ── */
$ok(ml_cap($pdo, $now + 3600 + 6 * 86400) === 100 && ml_cap($pdo, $now + 3600 + 7 * 86400) === 200 && ml_cap($pdo, $now + 3600 + 14 * 86400) === 400 && ml_cap($pdo, $now + 3600 + 21 * 86400) === 500, 'cap: 100, 200 after a week, 400, then the maximum (500)');
for ($i = 0; $i < 30; $i++) $add("b$i", "b$i@t.dev", 'en', '', 1, 0);
$id2 = ml_campaign_save($pdo, null, ['name' => 'Big', 'content' => $content, 'audience' => ['joined' => 2]])['id'];
$t2 = $now + 7200; ml_campaign_schedule($pdo, $id2, $t2); $n = 0; $runs = 0;
while ($runs < 40) { $r = ml_run($pdo, fn() => true, $t2 + $runs * 60); $n += $r['sent']; $runs++; if ($r['left'] === 0) break; }
$ok(ml_campaign($pdo, $id2)['recipients'] === 30 && $n === 30 && $runs === 8, "30 emails at 4 a minute: 8 runs ($runs, " . ml_campaign($pdo, $id2)["recipients"] . " recipients, $n sent)");
$hourly = (int) ml_q($pdo, "SELECT COUNT(*) FROM mail_queue WHERE kind = 'marketing' AND sent_at >= ?", [$t2 - 3600 + 600])->fetchColumn();
$ok($hourly <= 100, "never more than the cap in an hour ($hourly)");

/* ── skipped, soft, retried ── */
$add('s1', 'bounce-soft@t.dev', 'en', '', -3, -3); $add('s2', 'late@t.dev', 'en', '', -3, -3);   // signed up 3 days from now
$id3 = ml_campaign_save($pdo, null, ['name' => 'Soft', 'content' => $content, 'audience' => ['joined' => 1]])['id'];
ml_campaign_schedule($pdo, $id3, null);
$t3 = $now + 3 * 86400; ml_campaign_start($pdo, $id3, $t3);
ml_set_marketing($pdo, 's2', false);   // unsubscribed after the start
$soft = fn($to) => $to === 'bounce-soft@t.dev' ? 'soft: 451 try later' : true;
$r = ml_run($pdo, $soft, $t3);
$ok($r['skipped'] >= 1 && ml_q($pdo, "SELECT state FROM mail_queue WHERE campaign_id = ? AND email = 'late@t.dev'", [$id3])->fetchColumn() === 'skipped', 'unsubscribed after the start: skipped');
$st = fn() => ml_q($pdo, "SELECT state, attempts FROM mail_queue WHERE campaign_id = ? AND email = 'bounce-soft@t.dev'", [$id3])->fetch();
$ok($st()['state'] === 'queued' && (int) $st()['attempts'] === 1, 'soft refusal: queued again');
ml_run($pdo, $soft, $t3 + 60); $ok((int) $st()['attempts'] === 1, 'not before 10 minutes');
ml_run($pdo, $soft, $t3 + 601); ml_run($pdo, $soft, $t3 + 601 + 1201);
$ok($st()['state'] === 'failed' && (int) $st()['attempts'] === 3 && !ml_suppressed($pdo, 'bounce-soft@t.dev'), 'third soft refusal: failed, address kept');

/* ── opens and clicks ── */
$q = fn($email, $cid) => ml_q($pdo, 'SELECT * FROM mail_queue WHERE email = ? AND campaign_id = ?', [$email, $cid])->fetch();
$ok(ml_auto_open('Mozilla/5.0', '17.58.1.2', $now - 3600, $now) && ml_auto_open('Mozilla/5.0 (iPhone)', '8.8.8.8', $now - 5, $now) && ml_auto_open('Barracuda scanner', '1.1.1.1', null, $now), 'machine opens: Apple Mail (Apple address, bare user agent), first seconds, scanners');
$ok(!ml_auto_open('Mozilla/5.0 (iPhone; CPU iPhone OS 18_0) AppleWebKit', '24.48.1.1', $now - 600, $now) && !ml_auto_open('Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome GoogleImageProxy', '66.249.1.1', $now - 600, $now), 'real opens: a phone, Gmail');
$qa = $q('ana@t.dev', $id); $qb = $q('ben@t.dev', $id); $qc = $q('cruz@t.dev', $id);
ml_event($pdo, (int) $qa['id'], $id, 'open'); ml_event($pdo, (int) $qa['id'], $id, 'open');
ml_event($pdo, (int) $qb['id'], $id, 'open_auto'); ml_event($pdo, (int) $qc['id'], $id, 'click', 'https://makeitsweep.com/guide');
$s = ml_stats($pdo, $id);
$ok($s['sent'] === 3 && $s['failed'] === 1 && $s['delivered'] === 3 && $s['opens'] === 2 && $s['opens_auto'] === 1 && $s['clicks'] === 1, 'numbers: 3 delivered, 2 real opens (a click counts), 1 machine open apart, 1 click (' . json_encode($s) . ')');
$ok($s['open_rate'] === 66.7 && $s['open_rate_all'] === 100.0 && $s['click_rate'] === 33.3 && $s['click_to_open'] === 50.0 && $s['bounce_rate'] === 25.0, 'rates: opens 66.7 % (100 % with machines), clicks 33.3 %, 50 % of openers, bounces 25 %');

/* ── what comes back ── */
$tok = $qb['token'];
$exim = "From: Mail Delivery System <Mailer-Daemon@vsrv223.armadaservers.com>\nSubject: Mail delivery failed: returning message to sender\n\nThis message was created automatically by mail delivery software.\n\nA message that you sent could not be delivered to one or more of its recipients. This is a permanent error. The following address(es) failed:\n\n  ben@t.dev\n    host gmail-smtp-in.l.google.com said: 550-5.1.1 The email account that you tried to reach does not exist.\n\n------ This is a copy of the message, including all the headers. ------\nMessage-ID: <$tok.m@makeitsweep.com>\nX-Sweep-Id: $tok\n";
$ok(ml_parse_return($exim) === ['token' => $tok, 'type' => 'bounce'], 'Exim report (permanent error): hard bounce');
$dsn = "Content-Type: multipart/report; report-type=delivery-status\n\nReporting-MTA: dns; mx.t.dev\nFinal-Recipient: rfc822; x@t.dev\nAction: failed\nStatus: 4.2.2\nDiagnostic-Code: smtp; 452 mailbox full\n\nX-Sweep-Id: $tok\n";
$ok(ml_parse_return($dsn) === ['token' => $tok, 'type' => 'soft_bounce'], 'DSN 4.2.2 (mailbox full): soft bounce');
$ok(ml_parse_return("Subject: Warning: message delayed\nAction: delayed\nStatus: 4.4.7\nX-Sweep-Id: $tok\n") === null, 'delay warning: ignored');
$ok(ml_parse_return("Auto-Submitted: auto-replied\nSubject: Out of office\n\nI am away.\nIn-Reply-To: <$tok.m@makeitsweep.com>\nMessage-ID: <$tok.m@makeitsweep.com>") === null, 'out of office: ignored');
$ok(ml_parse_return("Content-Type: multipart/report; report-type=feedback-report\n\nFeedback-Type: abuse\nUser-Agent: Yahoo!-Mail-Feedback/2.0\n\nX-Sweep-Id: $tok\n") === ['token' => $tok, 'type' => 'complaint'], 'complaint (feedback loop)');
$ok(ml_parse_return("To: bounces@makeitsweep.com\nSubject: unsubscribe-$tok\n\n") === ['token' => $tok, 'type' => 'unsub'], 'unsubscribe by email (List-Unsubscribe mailto)');
$ok(ml_parse_return("Subject: hello\n\nnothing of ours") === null, 'not about one of our emails: ignored');
ml_apply_return($pdo, ml_parse_return($exim)); ml_apply_return($pdo, ml_parse_return($exim));
$ok(ml_suppressed($pdo, 'ben@t.dev') && ml_stats($pdo, $id)['delivered'] === 2 && ml_stats($pdo, $id)['bounces'] === 2, 'bounce after sending: set aside, once (a report sent twice), no longer delivered');
ml_apply_return($pdo, ['token' => $qa['token'], 'type' => 'unsub']);
$ok((int) ml_q($pdo, "SELECT marketing FROM email_prefs WHERE user_id = 'u1'")->fetchColumn() === 0 && ml_stats($pdo, $id)['unsubs'] === 1 && $ids(['lang' => 'fr']) === '', 'unsubscribe: counted, out of every next audience');
ml_unsubscribe($pdo, ml_by_token($pdo, $qa['token']), false);
$ok($ids(['lang' => 'fr']) === 'u1' && ml_stats($pdo, $id)['unsubs'] === 0, 'subscribe again from the same page: back on the list');
ml_apply_return($pdo, ['token' => $qc['token'], 'type' => 'complaint']);
$ok(ml_suppressed($pdo, 'cruz@t.dev') && ml_stats($pdo, $id)['complaints'] === 1, 'complaint: never written to again');

/* ── report and automatic pause ── */
$rep = ml_campaign_report($pdo, $id);
$ok(count($rep['hours']) === 48 && array_sum(array_column($rep['hours'], 0)) === 1 && array_sum(array_column($rep['hours'], 1)) === 1, 'report: 48 hours (first open, first click per person)');
$ok($rep['links'] === [['url' => 'https://makeitsweep.com/guide', 'clicks' => 1]] && count($rep['langs']) === 3, 'report: top links, per language');
for ($i = 0; $i < 120; $i++) $add("p$i", ($i < 5 ? 'bounce-hard' . $i : "p$i") . '@t.dev', 'en', '', 0, 0);
$pdo->exec("UPDATE users SET created_at = '" . gmdate('Y-m-d\TH:i:s\Z', $now + 5 * 86400) . "' WHERE id LIKE 'p%'");
$id4 = ml_campaign_save($pdo, null, ['name' => 'Pause', 'content' => $content, 'audience' => ['joined' => 1]])['id'];
ml_campaign_schedule($pdo, $id4, $now + 5 * 86400);
$pdo->exec('DELETE FROM app_settings WHERE k = \'mail_warm_start\''); $cfg['mail_per_hour'] = ['start' => 3000, 'max' => 3000];
$r = ml_run($pdo, fn($to) => strpos($to, 'bounce-hard') === 0 ? 'hard: 550' : true, $now + 5 * 86400 + 60);
$c4 = ml_campaign($pdo, $id4);
$ok($c4['status'] === 'paused' && $c4['paused_reason'] === 'bounces', 'over 3 % bounces after 100 emails: the campaign pauses itself (' . $c4['status'] . ')');
$ok(ml_campaign_pause($pdo, $id4, false) && ml_campaign($pdo, $id4)['status'] === 'sending', 'resume');
$ok(ml_campaign_save($pdo, $id4, ['name' => 'x'])['error'] === 'sent', 'a campaign that went out is never rewritten');
$ov = ml_overview($pdo, $now + 5 * 86400 + 60);
$ok(count($ov['campaigns']) === 4 && $ov['month']['sent'] > 0 && $ov['sending']['max'] === 3000, 'overview: campaigns, 30 days, the pace');

echo "\n$pass passed, $fail failed\n";
exit($fail ? 1 : 0);
