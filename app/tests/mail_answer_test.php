<?php
declare(strict_types=1);
/**
 * Sweep — the one-click answers in the emails (feedback brief, step 1), on a throwaway SQLite database:
 *   php tests/mail_answer_test.php
 *  - the markup: [[?note]] (1 to 5), [[?note|0-10]], [[?choix|A|B|C]]; the question is the paragraph above; a wrong one stays text;
 *  - the email: one signed link per option (api/m/r/…), its legend, the text version; preview and test: the app's feedback page;
 *  - an answer: kept in feedback (its email, question, choice and its place), a second one replaces it, a comment is added
 *    to it; a note from 1 to 5 counts as an experience rating; the email's « answer » event once; not a trader's email: nothing;
 *  - the numbers: answered and its rate, each question in its languages with the counts (EN and FR add up), the last
 *    comments; Admin › Feedback « From an email » lists them with the email's name, the other types never do.
 */
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
$app = dirname(__DIR__);
putenv('SWEEP_TEST_DB');
$pdo = new PDO('sqlite::memory:', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC]);
$pdo->exec('CREATE TABLE users (id TEXT PRIMARY KEY, username TEXT, email TEXT, lang TEXT, first_name TEXT, created_at TEXT, last_login TEXT, disabled INTEGER DEFAULT 0, is_admin INTEGER DEFAULT 0, is_internal INTEGER DEFAULT 0)');
$pdo->exec('CREATE TABLE app_settings (k TEXT PRIMARY KEY, v TEXT NOT NULL)');
function db(): PDO { global $pdo; return $pdo; }
$GLOBALS['cfg'] = $cfg = ['app_url' => 'https://app.test/'];
require $app . '/growth/referral.php';
require $app . '/growth/feedback.php';
require $app . '/mail/mail-core.php';
require $app . '/mail/mail-admin.php';
$pass = 0; $fail = 0;
$ok = function (bool $c, string $what) use (&$pass, &$fail) { echo ($c ? 'ok   ' : 'FAIL ') . $what . "\n"; $c ? $pass++ : $fail++; };
foreach ([['u1', 'ana@t.dev', 'fr', 'Ana'], ['u2', 'ben@t.dev', 'en', 'Ben'], ['u3', 'cruz@t.dev', 'en', 'Cruz']] as [$id, $e, $l, $f])
    $pdo->prepare('INSERT INTO users (id, username, email, lang, first_name, created_at) VALUES (?, ?, ?, ?, ?, ?)')->execute([$id, $id, $e, $l, $f, '2026-10-01T00:00:00Z']);
ml_schema($pdo);

// 1. the markup
$ok(ml_question_of('[[?note]]')['opts'] === ['1', '2', '3', '4', '5'] && ml_question_of('[[?note|0-10]]')['opts'] === array_map('strval', range(0, 10)), '[[?note]] is 1 to 5, [[?note|0-10]] 0 to 10');
$ok(ml_question_of('[[?choix|Les stats| Le plan |]]')['opts'] === ['Les stats', 'Le plan'] && ml_question_of('[[?choice|A|B]]')['kind'] === 'choice', '[[?choix|…]] and [[?choice|…]]: the options, trimmed, empty ones dropped');
$ok(ml_question_of('[[?choix]]') === null && ml_question_of('[[?note|9-2]]')['opts'][0] === '1' && ml_question_of('Rate us [[?note]]') === null, 'no option, a wrong range, a question not alone on its line: not a question (or 1 to 5)');
$fr = "Salut {first},\n\n**Comment** se passe ta première semaine ?\n\n[[?note]]\n\nQu'est-ce qui manque le plus ?\n\n[[?choix|Les stats|La synchro|Autre chose]]\n\n[[Ouvrir Sweep|{app}#dashboard]]";
$en = "Hi {first},\n\nHow is your first week going?\n\n[[?note]]\n\nWhat do you miss the most?\n\n[[?choix|Stats|Sync|Something else]]";
$qs = ml_questions($fr);
$ok(count($qs) === 2 && $qs[0]['question'] === 'Comment se passe ta première semaine ?' && $qs[1]['opts'][1] === 'La synchro', 'the questions of a body: the paragraph above each, plain text');

// 2. the email
$cid = ml_campaign_save($pdo, null, ['name' => 'Semaine 1', 'content' => ['fr' => ['subject' => 'Ta semaine', 'preheader' => '', 'body' => $fr], 'en' => ['subject' => 'Your week', 'preheader' => '', 'body' => $en]], 'audience' => []])['id'];
$tok = ml_token();
[$s, $text, $html] = ml_render($pdo, ['subject' => 'Ta semaine', 'preheader' => '', 'body' => $fr], 'fr', 'Ana', $tok);
preg_match_all('#href="(https://app\.test/api/m/r/' . $tok . '\?[^"]+)"#', $html, $m);
$links = array_map(fn($u) => html_entity_decode($u), $m[1]);
$ok(count($links) === 8, 'the email: one link per option (5 notes + 3 choices): ' . count($links));
parse_str(parse_url($links[3], PHP_URL_QUERY), $p4); parse_str(parse_url($links[6], PHP_URL_QUERY), $pc);
$ok($p4['q'] === '0' && $p4['a'] === '4' && $pc['q'] === '1' && $pc['a'] === 'La synchro' && hash_equals(ml_answer_sig($pdo, $tok, 1, 'La synchro'), $pc['s']), 'each link: its question, its answer, signed');
$ok(!hash_equals(ml_answer_sig($pdo, $tok, 1, 'Autre chose'), $pc['s']) && !hash_equals(ml_answer_sig($pdo, ml_token(), 1, 'La synchro'), $pc['s']), 'a link changed by hand (another answer, another email) fails its signature');
$ok(strpos($html, '1 = pas du tout · 5 = tout à fait') !== false && strpos($text, "4: https://app.test/api/m/r/$tok?q=0&a=4&s=") !== false && strpos($text, 'Autre chose: https://app.test/api/m/r/') !== false, 'the legend under the notes, every option in the text version');
[, , $prev] = ml_render($pdo, ['subject' => 'x', 'preheader' => '', 'body' => $fr], 'fr', 'Ana', '', false);
$ok(strpos($prev, 'api/m/r/') === false && substr_count($prev, 'https://app.test/#feedback') === 8, 'preview and test: the options go to the app\'s feedback page, nothing recorded');

// 3. an answer
$queue = function (string $uid, ?int $cid, string $lang) use ($pdo) {
    $t = ml_token(); ml_q($pdo, "INSERT INTO mail_queue (campaign_id, user_id, email, lang, kind, token, state, next_at, created_at, sent_at) VALUES (?, ?, ?, ?, 'marketing', ?, 'sent', 0, ?, ?)", [$cid, $uid, $uid . '@t.dev', $lang, $t, time(), time() - 3600]);
    return ml_by_token($pdo, $t);
};
$q1 = $queue('u1', $cid, 'fr'); $q2 = $queue('u2', $cid, 'en'); $q3 = $queue('u3', $cid, 'en');
$ok(ml_answer_save($pdo, $q1, 0, '2', null), 'Ana answers 2');
$ok(ml_answer_save($pdo, $q1, 0, '4', null), '… then changes her mind: 4');
$row = fn(array $q, int $n) => ml_q($pdo, 'SELECT * FROM feedback WHERE src_queue = ? AND src_q = ?', [$q['id'], $n])->fetchAll();
$r = $row($q1, 0);
$ok(count($r) === 1 && $r[0]['answer'] === '4' && (int) $r[0]['rating'] === 4 && $r[0]['type'] === 'experience' && $r[0]['user_id'] === 'u1' && (int) $r[0]['src_campaign'] === $cid, 'one line per email and question, the last answer; a note from 1 to 5 is an experience rating');
$ok($r[0]['question'] === 'Comment se passe ta première semaine ?' && $r[0]['message'] === '' && $r[0]['status'] === 'new', 'its question, no comment yet, « new »');
ml_answer_save($pdo, $q1, 1, 'La synchro', "  Il me faut Tradovate.  ");
ml_answer_save($pdo, $q1, 1, 'La synchro', null);
$r = $row($q1, 1);
$ok($r[0]['type'] === 'answer' && $r[0]['rating'] === null && (int) $r[0]['answer_i'] === 1 && $r[0]['message'] === 'Il me faut Tradovate.', 'a choice: its place kept (EN and FR add up), the comment kept when the page records the answer again');
ml_answer_save($pdo, $q2, 1, 'Sync', null); ml_answer_save($pdo, $q3, 1, 'Stats', 'More charts');
$ok((int) ml_q($pdo, "SELECT COUNT(*) FROM mail_events WHERE queue_id = ? AND type = 'answer'", [$q1['id']])->fetchColumn() === 1, 'the email\'s « answer » event once, however many answers');
$raw = $queue('u2', null, 'en'); $raw['user_id'] = null;
$ok(!ml_answer_save($pdo, $raw, 0, '5', null), 'not a trader\'s email: nothing kept');
$q4 = $queue('u2', null, 'en');
$ok(ml_answer_save($pdo, $q4, 0, '5', null) && $row($q4, 0)[0]['question'] === null, 'a ready email (no campaign): the answer kept, no question');

// 4. the numbers
$s = ml_stats($pdo, $cid);
$ok($s['answers'] === 3 && $s['answer_rate'] === 100.0, 'answered: 3 of 3 delivered (' . json_encode([$s['answers'], $s['answer_rate']]) . ')');
$A = ml_answers($pdo, ml_campaign($pdo, $cid));
$c1 = (array) $A['questions'][1]['counts'];
$ok(count($A['questions']) === 2 && $A['questions'][1]['text']['en'] === 'What do you miss the most?' && $A['questions'][1]['opts']['fr'][1] === 'La synchro', 'each question in its languages, with its options');
$ok(($c1[1] ?? 0) === 2 && ($c1[0] ?? 0) === 1 && $A['questions'][1]['total'] === 3 && $A['questions'][0]['total'] === 1, 'the counts by place: « La synchro » and « Sync » are the same answer (2), « Stats » 1');
$ok(count($A['comments']) === 2 && in_array('Il me faut Tradovate.', array_column($A['comments'], 'message'), true), 'the last comments');
$ok(isset(ml_campaign_report($pdo, $cid)['questions']), 'the campaign\'s page has them');

// 5. Admin › Feedback
fb_create($pdo, 'u2', ['type' => 'idea', 'message' => 'Dark charts'], 'free');
$L = fb_admin_list($pdo, null, 'mail');
$ok(count($L['items']) === 5 && count(array_filter($L['items'], fn($i) => ($i['mail']['name']['en'] ?? '') === 'Semaine 1')) === 4, '« From an email »: the 5 answers, 4 with their email\'s name');
$ok(count(fb_admin_list($pdo, null, 'idea')['items']) === 1 && !array_filter(fb_admin_list($pdo, null, 'experience')['items'], fn($i) => isset($i['mail'])), 'the other types never list the email answers');
$ok(fb_admin_list($pdo, null, null)['avg_rating_30d'] === 4.0, 'the note from the email counts in the experience rating');

echo "\n$pass passed, $fail failed\n";
exit($fail ? 1 : 0);
