<?php
declare(strict_types=1);
/**
 * Sweep — the week's recap on Friday (brief 01 step 5), on a throwaway SQLite database (never the live one):
 *   php tests/weekly_test.php
 * The clock is pinned (SWEEP_GAME_NOW, New York time) for each scenario of the brief:
 *  - Friday review done at 16:30 ET → the recap is ready at once; no review → ready at the 17:00 close, not before;
 *  - Friday a market holiday → Thursday's review / close; no trade in the week → no recap, no notification;
 *  - the trader's own time zone (Paris, Tokyo) changes nothing; ONE notification a week, none once the recap is opened;
 *  - the « Your week » email (lot 3): from 17:30 ET on the last trading day, once, not if opened in the app, not without a
 *    trade, not once stopped from its link; the recap's numbers (same rules as weekBrief() in src/game.js), no P&L.
 */
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
$app = dirname(__DIR__);
$tmp = sys_get_temp_dir() . '/sweep-weekly-' . bin2hex(random_bytes(4)); mkdir($tmp);
$pdo = new PDO('sqlite:' . $tmp . '/t.db', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC]);
function db() { global $pdo; return $pdo; }
$pdo->exec('CREATE TABLE documents (user_id TEXT NOT NULL, collection TEXT NOT NULL, id TEXT NOT NULL, data TEXT NOT NULL, updated_at TEXT, PRIMARY KEY (user_id, collection, id))');
$pdo->exec('CREATE TABLE users (id TEXT PRIMARY KEY, username TEXT, lang TEXT, email TEXT, first_name TEXT, disabled INT DEFAULT 0)');
require $app . '/notify/notify.php';
require $app . '/game/game.php';
GameEngine::setPdo($pdo); GameEngine::schema(); GameV2::schema(); GameV2b::schema(); if (class_exists('GameV2c')) GameV2c::schema();
$pass = 0; $fail = 0;
$ok = function (bool $c, string $what) use (&$pass, &$fail) { echo ($c ? 'ok   ' : 'FAIL ') . $what . "\n"; $c ? $pass++ : $fail++; };
$at = function (string $ny) { putenv('SWEEP_GAME_NOW=' . $ny); };
$day = fn(string $uid, string $d, int $trades, int $review) => $pdo->prepare('INSERT OR REPLACE INTO game_days (user_id, trading_day, trades_count, review_done, activity, updated_at) VALUES (?, ?, ?, ?, 1, ?)')->execute([$uid, $d, $trades, $review, time()]);
foreach (['u1', 'u2', 'u3'] as $u) { $at('2026-10-05 08:00'); GameEngine::profile($u); }

// week of Monday 2026-10-05: u1 traded on Tuesday; Friday review not done yet. u2: no trade this week.
$day('u1', '2026-10-06', 2, 1);
$W = '2026-10-05';
$at('2026-10-08 20:00'); $ok(GameV2b::openWeek('u1') === null, 'Thursday evening: the week is not over, no recap');
$at('2026-10-09 16:29'); $ok(GameV2b::openWeek('u1') === null, 'Friday 16:29, no review yet: no recap');
$at('2026-10-09 17:00'); $ok(GameV2b::openWeek('u1') === $W, 'no review: the recap is ready at the 17:00 ET close');
$ok(GameV2b::openWeek('u2') === null, 'no trade in the week: no recap at all');
$at('2026-10-10 11:00'); $ok(GameV2b::openWeek('u1') === $W, 'Saturday: still ready, waiting for the next opening of the app');
$at('2026-10-11 23:30'); $ok(GameV2b::openWeek('u1') === $W, 'Sunday 23:30: still ready');
$at('2026-10-12 09:00'); $ok(GameV2b::openWeek('u1') === null, 'Monday: the new week has no recap yet');
// u3: trades Friday and finishes Friday's review at 16:30 → ready at once
$day('u3', '2026-10-09', 1, 0);
$at('2026-10-09 16:30'); $ok(GameV2b::openWeek('u3') === null, 'Friday 16:30, review not done: not yet');
$day('u3', '2026-10-09', 1, 1);
$ok(GameV2b::openWeek('u3') === $W, 'Friday review done at 16:30 ET: the recap is ready at once');
// Good Friday 2027-03-26 (market holiday): Thursday 2027-03-25 is the last trading day
$day('u1', '2027-03-23', 1, 0);
$at('2027-03-25 16:59'); $ok(GameV2b::openWeek('u1') === null, 'Friday is a holiday: Thursday 16:59 without review, not yet');
$at('2027-03-25 17:00'); $ok(GameV2b::openWeek('u1') === '2027-03-22', 'Friday is a holiday: ready at Thursday\'s 17:00 close');
$day('u3', '2027-03-25', 1, 1);
$at('2027-03-25 15:00'); $ok(GameV2b::openWeek('u3') === '2027-03-22', 'Friday is a holiday: Thursday\'s review done → ready at once');
// the trader's time zone changes nothing (the rule is New York time)
foreach (['Europe/Paris', 'Asia/Tokyo'] as $tz) {
    date_default_timezone_set($tz);
    $at('2026-10-09 16:59'); $a = GameV2b::openWeek('u1'); $at('2026-10-09 17:00'); $b = GameV2b::openWeek('u1');
    $ok($a === null && $b === $W, "time zone $tz: same moment (17:00 New York)");
}
date_default_timezone_set('UTC');
// the light state seen by the app: open, not seen; opening the recap marks it seen
$at('2026-10-09 17:05'); $w = GameV2b::weeklyState('u1', true);
$ok($w['open'] && $w['week'] === $W && $w['seen'] === false, 'the app gets: ready, not seen yet');
// ONE notification a week, none after the recap is opened
$count = fn(string $u) => (int) $pdo->query("SELECT COUNT(*) FROM notifications WHERE user_id = " . $pdo->quote($u) . " AND type = 'g_weekly'")->fetchColumn();
$at('2026-10-09 17:15'); GameNotifyService::run('u1');
$ok($count('u1') === 1, 'Friday 17:15: « Your week is ready » sent once');
$at('2026-10-10 10:00'); GameNotifyService::run('u1');
$at('2026-10-11 19:00'); GameNotifyService::run('u1');
$ok($count('u1') === 1, 'no second notification on Saturday or Sunday');
$at('2026-10-09 17:15'); GameNotifyService::run('u2');
$ok($count('u2') === 0, 'no trade in the week: no notification');
$at('2026-10-09 16:45'); GameV2b::markSeen('u3', $W); GameNotifyService::run('u3');
$ok($count('u3') === 0, 'recap already opened in the app: no notification');
$ok(GameV2b::weeklyState('u3', true)['seen'] === true, 'opened → seen (the routine card stops offering it)');

// ───── the « Your week » email (lot 3) ─────
$mails = []; GameWeeklyMail::$mailer = function (string $to, string $subject, string $text, string $html, array $h) use (&$mails) { $mails[] = compact('to', 'subject', 'text', 'html', 'h'); return true; };
$user = fn(string $id, string $lang, string $email, string $first = '', int $disabled = 0) => $pdo->prepare('INSERT OR REPLACE INTO users (id, username, lang, email, first_name, disabled) VALUES (?, ?, ?, ?, ?, ?)')->execute([$id, $id, $lang, $email, $first, $disabled]);
$doc = fn(string $uid, string $col, array $d) => $pdo->prepare('INSERT OR REPLACE INTO documents (user_id, collection, id, data) VALUES (?, ?, ?, ?)')->execute([$uid, $col, $d['id'], json_encode($d)]);
$user('u1', 'fr-CA', 'uma@t.dev', 'Uma'); $user('u2', 'fr', 'u2@t.dev'); $user('u3', 'en', 'u3@t.dev');
// u1's week: 3 trades on 2 days with checklist answers; a demo trade and a Saturday trade are left out
foreach ([['t1', '2026-10-06', ['plan' => 'y', 'stop' => 'n']], ['t2', '2026-10-06', ['plan' => 'y', 'stop' => 'n']], ['t3', '2026-10-07', ['plan' => 'y', 'stop' => 'y', 'size' => 'na']],
          ['t4', '2026-10-08', ['plan' => 'n', 'stop' => 'n'], true], ['t5', '2026-10-10', ['plan' => 'n']]] as $t)
    $doc('u1', 'trades', ['id' => $t[0], 'date' => $t[1], 'pnl_c' => 250000, 'discipline' => $t[2]] + (!empty($t[3]) ? ['demo' => true] : []));
foreach ([['p1', 'paid', '2026-10-07', 50000, null], ['p2', 'paid', '2026-10-11', null, 20000], ['p3', 'requested', '2026-10-08', 90000, null], ['p4', 'paid', '2026-10-12', 90000, null], ['p5', 'rejected', '2026-10-07', 90000, null]] as $q)
    $doc('u1', 'payouts', array_filter(['id' => $q[0], 'status' => $q[1], 'paid_on' => $q[2], 'net_c' => $q[3], 'amount_c' => $q[4]], fn($v) => $v !== null));
$b = GameWeeklyMail::brief('u1', $W, 'fr');
$ok($b['traded'] === 2 && $b['disc'] === 67, "brief: 2 days traded (demo and Saturday left out), discipline (50 + 50 + 100) / 3 = 67 ({$b['traded']}, {$b['disc']})");
$ok(($b['best']['q'] ?? '') === 'Ce trade faisait-il partie de mon plan de trading ?' && $b['best']['y'] === 3 && $b['best']['n'] === 3, 'brief: best habit, the default question in French, yes 3 times out of 3');
$ok(($b['work']['q'] ?? '') === 'Ai-je respecté mon stop ?', 'brief: point to work on, the question answered « yes » least often (1 of 3)');
$ok($b['payouts'] === 70000, "brief: payouts paid Monday-Sunday only (net, else amount): 500 + 200 = 700 \$ ({$b['payouts']})");
$ok(GameWeeklyMail::brief('u1', $W, 'es')['best']['q'] === '¿Esta operación formaba parte de mi plan?' && GameWeeklyMail::brief('u1', $W, 'en')['best']['q'] === 'Was this trade part of my trading plan?', 'brief: the default question in Spanish and English');
// a checklist of the trader's own: its words as written; a tie is broken the same way as in the app (question id)
$doc('u3', 'meta', ['id' => 'settings', 'questions' => [['id' => 'plan', 'text' => 'Was this trade part of my trading plan?'], ['id' => 'aplus', 'text' => 'Only my A+ setup?']]]);
foreach ([['v1', ['plan' => 'y', 'aplus' => 'y']], ['v2', ['plan' => 'y', 'aplus' => 'y']]] as $t) $doc('u3', 'trades', ['id' => $t[0], 'date' => '2026-10-09', 'discipline' => $t[1]]);
$b3 = GameWeeklyMail::brief('u3', $W, 'fr');
$ok(($b3['best']['q'] ?? '') === 'Only my A+ setup?' && $b3['work'] === null, 'brief: own question kept as written; tie (2 of 2 each) → the first id; nothing to work on');

$sent = function (string $u) use (&$mails) { return count(array_filter($mails, fn($m) => $m['to'] === $u)); };
$at('2026-10-09 17:29'); GameWeeklyMail::run('u1');
$ok($sent('uma@t.dev') === 0, 'email: Friday 17:29, not yet');
$at('2026-10-09 17:30'); GameWeeklyMail::run('u1');
$ok($sent('uma@t.dev') === 1, 'email: Friday 17:30 ET, « Ta semaine » sent');
$at('2026-10-09 17:45'); GameWeeklyMail::run('u1'); $at('2026-10-10 09:00'); GameWeeklyMail::run('u1'); $at('2026-10-11 20:00'); GameWeeklyMail::run('u1');
$ok($sent('uma@t.dev') === 1, 'email: once a week (not again on Friday evening, Saturday or Sunday)');
$m = $mails[0] ?? ['subject' => '', 'text' => '', 'html' => '', 'h' => []];
$ok($m['subject'] === 'Ta semaine du 5 au 9 octobre', "email: French subject ({$m['subject']})");
$want = ['Salut Uma,', "Streak de journées balayées\u{00A0}: 0 jours d’affilée", "Discipline de la semaine\u{00A0}: 67\u{202F}%", "Journées balayées\u{00A0}: 0 sur 2 jours tradés",
         'Ta meilleure habitude' . "\u{00A0}: « Ce trade faisait-il partie de mon plan de trading ? » — oui 3 fois sur 3", "Vise un « oui » à « Ai-je respecté mon stop ? » sur chaque trade.",
         "Payouts reçus cette semaine\u{00A0}: 700\u{00A0}$", 'Voir mon bilan'];
$sp = fn(string $x) => str_replace("\u{00A0}", ' ', $x);   // French no-break spaces (« », ? :) compared as spaces
$miss = array_values(array_filter($want, fn($w) => strpos($sp($m['text']), $sp($w)) === false));
$ok(!$miss, 'email: streak, discipline, swept days of days traded, best habit, point to work on, payouts' . ($miss ? ' — missing: ' . implode(' | ', $miss) : ''));
preg_match_all('/\d[\d\x{202F}\x{00A0},.]*\x{00A0}\$|\$\d/u', $m['text'] . ' ' . strip_tags($m['html']), $dl);
$ok(count(array_unique($dl[0])) === 1, 'email: the payouts are the only dollar amount (no P&L, no simulated money): ' . json_encode(array_unique($dl[0]), JSON_UNESCAPED_UNICODE));
$tok = GameWeeklyMail::token('u1');
$ok(strpos($m['html'], 'api/email/weekly?t=' . $tok) !== false && ($m['h']['List-Unsubscribe'] ?? '') === '<https://app.makeitsweep.com/api/email/weekly?t=' . $tok . '>' && ($m['h']['List-Unsubscribe-Post'] ?? '') === 'List-Unsubscribe=One-Click',
    'email: a link to stop it (and the mail apps\' one-click « Unsubscribe »)');
$ok(strpos($m['html'], "Ce trade faisait-il partie de mon plan de trading\u{00A0}?\u{00A0}»") !== false && strpos($m['html'], '<script') === false, 'email: the HTML version has the same content, French no-break spaces (« ?\u{00A0}» » never alone on a line)');
$at('2026-10-09 17:30'); GameWeeklyMail::run('u2'); GameWeeklyMail::run('u3');
$ok($sent('u2@t.dev') === 0, 'email: no trade in the week, no email');
$ok($sent('u3@t.dev') === 0, 'email: recap already opened in the app (u3 at 16:45), no email');
// Good Friday 2027: Thursday is the last trading day → Thursday 17:30
$at('2027-03-25 17:29'); GameWeeklyMail::run('u1'); $ok($sent('uma@t.dev') === 1, 'email: Friday is a holiday, Thursday 17:29: not yet');
$at('2027-03-25 17:30'); GameWeeklyMail::run('u1'); $ok($sent('uma@t.dev') === 2 && end($mails)['subject'] === 'Ta semaine du 22 au 25 mars', 'email: Friday is a holiday, Thursday 17:30 ET (« ' . end($mails)['subject'] . ' »)');
// stopped from its link → no more emails; started again → next week's
$ok(GameWeeklyMail::setOff($tok, true) && !GameWeeklyMail::setOff(str_repeat('0', 32), true), 'link: stops the email (an unknown link does nothing)');
$day('u1', '2026-10-13', 1, 0); $at('2026-10-16 17:30'); GameWeeklyMail::run('u1');
$ok($sent('uma@t.dev') === 2, 'email stopped: none the next week');
GameWeeklyMail::setOff($tok, false); GameWeeklyMail::run('u1');
$ok($sent('uma@t.dev') === 3, 'started again from the page: sent');
// no email address, disabled account: nothing; English subject for an English trader
$user('u4', 'en', '', 'Ann'); $user('u5', 'en', 'u5@t.dev', 'Bo', 1); $user('u6', 'en', 'u6@t.dev', 'Cy');
foreach (['u4', 'u5', 'u6'] as $u) { $at('2026-10-05 08:00'); GameEngine::profile($u); $day($u, '2026-10-06', 1, 0); }
$at('2026-10-09 17:30'); foreach (['u4', 'u5', 'u6'] as $u) GameWeeklyMail::run($u);
$ok($sent('u5@t.dev') === 0 && count(array_filter($mails, fn($x) => $x['to'] === '')) === 0, 'email: none without an email address or for a disabled account');
$e6 = array_values(array_filter($mails, fn($x) => $x['to'] === 'u6@t.dev'))[0] ?? ['subject' => '', 'text' => ''];
$ok($e6['subject'] === 'Your week: October 5–9' && strpos($e6['text'], 'Hi Cy,') === 0 && strpos($e6['text'], 'Answer the checklist on your trades') !== false, "email: English, no checklist answered → how to get a score ({$e6['subject']})");
// a failed send is not retried every 15 minutes (never a double email)
GameWeeklyMail::$mailer = fn() => false; $user('u7', 'es', 'u7@t.dev'); $at('2026-10-05 08:00'); GameEngine::profile('u7'); $day('u7', '2026-10-06', 1, 0);
$at('2026-10-09 17:30'); $r1 = GameWeeklyMail::run('u7'); GameWeeklyMail::$mailer = function () use (&$mails) { $mails[] = ['to' => 'u7@t.dev']; return true; }; $at('2026-10-09 17:45'); GameWeeklyMail::run('u7');
$ok($r1 === false && $sent('u7@t.dev') === 0, 'email: a failed send is logged, not sent twice later');

foreach (glob($tmp . '/*') as $x) @unlink($x); @rmdir($tmp);
echo "\n$pass passed, $fail failed\n";
exit($fail ? 1 : 0);
