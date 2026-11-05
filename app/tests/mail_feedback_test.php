<?php
declare(strict_types=1);
/**
 * Sweep — the feedback emails (brief « Courriels de feedback », step 4), on a throwaway SQLite database, nothing sent:
 *   php tests/mail_feedback_test.php
 *  - switched off: nothing queued, nothing claimed (switched on later, the traders due get them);
 *  - the daily run (ma_feedback_run): weekOne (days 7 to 21), nps30 (30 days, seen in 30), months3 (90 days, used Sweep in
 *    30), featureDiscover (from 14 days, seen in 30: the first of plan, review, stats, sync never tried nor presented, one a
 *    week, never the same twice); one per trader and day; the unsubscribed never claimed;
 *  - never within 3 days of an automatic news email, nor a question within 30 days of another request for an opinion;
 *  - featureDiscover's text in the trader's language, with its button and page; the preview's example values;
 *  - feedbackShipped: a feedback set to « shipped » sends the author « You asked for it » with the request and the reply,
 *    once per feedback; not for another status nor a one-click answer without a comment.
 */
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
$app = dirname(__DIR__);
$tmp = sys_get_temp_dir() . '/sweep-mail-feedback-' . bin2hex(random_bytes(4)); mkdir($tmp);
ini_set('error_log', $tmp . '/php.log'); putenv('SWEEP_TEST_DB=' . $tmp . '/t.db');
$pdo = new PDO('sqlite:' . $tmp . '/t.db', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC]);
$pdo->exec('CREATE TABLE users (id TEXT PRIMARY KEY, username TEXT, email TEXT, first_name TEXT, lang TEXT, created_at TEXT, last_login TEXT, disabled INTEGER NOT NULL DEFAULT 0, is_admin INTEGER NOT NULL DEFAULT 0, is_internal INTEGER NOT NULL DEFAULT 0)');
$pdo->exec('CREATE TABLE app_settings (k TEXT PRIMARY KEY, v TEXT NOT NULL)');
$pdo->exec('CREATE TABLE feedback (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, message TEXT, reply TEXT, status TEXT)');
function db(): PDO { global $pdo; return $pdo; }
$GLOBALS['cfg'] = ['app_url' => 'https://app.test/'];
require $app . '/mail/mail-core.php';
require $app . '/mail/mail-auto.php';
$pass = 0; $fail = 0;
$ok = function (bool $c, string $what) use (&$pass, &$fail) { echo ($c ? 'ok   ' : 'FAIL ') . $what . "\n"; $c ? $pass++ : $fail++; };
ml_schema($pdo); ma_seed($pdo); ma_schema(); mu_schema($pdo);
ml_set_setting($pdo, 'mail_auto_since', '1');   // past the first run (ma_init)
$D = 86400; $now = time();
$iso = fn(int $t) => gmdate('Y-m-d\TH:i:s\Z', $t);
$user = function (string $id, string $lang, int $age, int $seenAgo, array $profile = []) use ($pdo, $iso, $now, $D) {
    $pdo->prepare('INSERT INTO users (id, username, email, first_name, lang, created_at, last_login) VALUES (?, ?, ?, ?, ?, ?, ?)')->execute([$id, $id, "$id@x.test", ucfirst($id), $lang, $iso($now - $age * $D), $iso($now - $seenAgo * $D)]);
    $pdo->prepare('INSERT INTO mail_usage (user_id, data_json, updated_at) VALUES (?, ?, ?)')->execute([$id, json_encode($profile + ['days' => [], 'ever' => []]), $now]);
};
$user('w', 'en', 8, 1);                                                 // week one
$user('wold', 'fr', 25, 1);                                              // past week one, before day 30: a feature
$user('n', 'en', 40, 2, ['ever' => ['plan', 'journal'], 'days' => ['journal' => 3]]);   // day 30
$user('naway', 'en', 40, 60);                                            // not seen for 60 days: nothing
$user('m', 'es', 100, 1, ['ever' => ['journal'], 'days' => ['journal' => 5]]);          // three months, active
$user('midle', 'en', 100, 3, ['days' => ['rules' => 1]]);                // seen, but only the firm rules (passive): not « used »
$user('unsub', 'en', 8, 1);
$pdo->exec("INSERT INTO email_prefs (user_id, token, weekly_off, marketing, updated_at) VALUES ('unsub', 't', 0, 0, 1)");
$ids = ['w', 'wold', 'n', 'naway', 'm', 'midle', 'unsub'];
$q = fn() => $pdo->query("SELECT q.user_id, c.auto, q.vars_json, q.lang FROM mail_queue q JOIN mail_campaigns c ON c.id = q.campaign_id ORDER BY q.id")->fetchAll();
$pairs = fn() => array_map(fn($r) => $r['user_id'] . ':' . $r['auto'], $q());
$logged = fn(string $k) => (int) $pdo->query("SELECT COUNT(*) FROM email_events_log WHERE event_name LIKE '$k%'")->fetchColumn();
$on = fn(array $ks, bool $v) => array_map(fn($k) => $pdo->prepare('UPDATE mail_campaigns SET status = ? WHERE auto = ?')->execute([$v ? 'active' : 'off', $k]), $ks);
$age = function (int $days) use ($pdo, $D) {   // everything sent so far, $days earlier (sent: an email that asks marks itself, as ml_compose does)
    $pdo->prepare("UPDATE mail_queue SET created_at = created_at - ?, state = 'sent', sent_at = created_at - ?, asked = CASE WHEN campaign_id IN (SELECT id FROM mail_campaigns WHERE auto IN ('weekOne', 'nps30', 'months3')) THEN 1 ELSE asked END")->execute([$days * $D, $days * $D]);
    $pdo->prepare('UPDATE email_events_log SET sent_at = sent_at - ?')->execute([$days * $D]);
};
$F = ['weekOne', 'nps30', 'featureDiscover', 'months3'];

// 1. off at the start: nothing queued, nothing claimed
$st = $pdo->query("SELECT status FROM mail_campaigns WHERE auto IN ('weekOne', 'nps30', 'featureDiscover', 'feedbackShipped', 'months3')")->fetchAll(PDO::FETCH_COLUMN);
$ok($st === array_fill(0, 5, 'off'), 'the 5 feedback emails are created off');
$ok(ma_feedback_run($ids, $now) === [] && $q() === [] && $logged('') === 0, 'switched off: nothing queued, nothing claimed');

// 2. switched on: one each, the right one
$on($F, true);
$r = ma_feedback_run($ids, $now);
$ok($pairs() === ['w:weekOne', 'wold:featureDiscover', 'n:nps30', 'm:months3', 'midle:nps30'], 'switched on: week one, a feature (25 days), day 30 ×2, three months; not the absent one nor the unsubscribed (' . implode(', ', $pairs()) . ')');
$ok($logged('featureDiscover:plan') === 1 && $logged('weekOne') === 1 && $logged('nps30') === 2 && $logged('months3') === 1, 'each claimed in email_events_log (featureDiscover:plan: never tried)');
$fv = json_decode($q()[1]['vars_json'], true);
$ok($q()[1]['lang'] === 'fr' && $fv['feature'] === 'le plan du matin' && $fv['feature_button'] === 'Faire mon plan' && $fv['feature_link'] === 'https://app.test/#dashboard' && strpos($fv['feature_pitch'], 'ton biais (tu t’attends') !== false,
    'featureDiscover in French: the feature, its pitch (bias explained), its button and page');
$camps = []; $row = $pdo->query("SELECT q.* FROM mail_queue q WHERE user_id = 'wold'")->fetch(); $m = ml_compose($pdo, $row, $camps);
$ok(str_replace("\u{00A0}", ' ', $m[1]) === 'As-tu essayé le plan du matin ?' && strpos($m[2], 'Faire mon plan: https://app.test/api/m/c/') !== false && strpos($m[2], '{feature') === false, 'rendered: « As-tu essayé le plan du matin ? », its button tracked, no value left');
$ok(ma_feedback_run($ids, $now) === [] && count($q()) === 5, 'the same day again: nothing more');

// 3. 4 days later: past the 3 days, but a question waits 30 days after another
$age(4);
ma_feedback_run($ids, $now);
$new = array_slice($pairs(), 5);
$ok($new === ['n:featureDiscover', 'm:featureDiscover', 'midle:featureDiscover'] && $logged('featureDiscover:review') === 1 && $logged('featureDiscover:plan') === 3,
    '4 days later: day 30 done, the 3-month trader asked 4 days ago gets no question, a feature instead (the plan, or the review when the plan is tried) (' . implode(', ', $new) . ')');
$ok(!in_array('w:featureDiscover', $new, true) && !in_array('wold:featureDiscover', $new, true), 'week one is not 14 days old; a feature 4 days ago: not this week');

// 4. a week later: the next feature, never the same twice; a trader asked 11 days ago still waits for a question
$age(8);
ma_feedback_run($ids, $now);
$new = array_slice($pairs(), 8);
$wold = $pdo->query("SELECT event_name FROM email_events_log WHERE user_id = 'wold' ORDER BY sent_at")->fetchAll(PDO::FETCH_COLUMN);
$ok(in_array('wold:featureDiscover', $new, true) && $wold === ['featureDiscover:plan', 'featureDiscover:review'], 'a week later: the next feature (the review), never the plan again (' . implode(', ', $wold) . ')');
foreach (range(1, 6) as $i) { $age(8); ma_feedback_run($ids, $now); }
$per = $pdo->query("SELECT user_id, COUNT(*) n, COUNT(DISTINCT event_name) d FROM email_events_log WHERE event_name LIKE 'featureDiscover:%' GROUP BY user_id")->fetchAll();
$ok(array_column($per, 'n', 'user_id') === array_column($per, 'd', 'user_id') && max(array_column($per, 'n')) <= 4, 'weeks later: each feature at most once per trader, 4 at most');
$at = fn(string $u, string $k) => (int) $pdo->query("SELECT sent_at FROM email_events_log WHERE user_id = '$u' AND event_name = '$k'")->fetchColumn();
$ok(!in_array('w:nps30', $pairs(), true) && in_array('m:nps30', $pairs(), true) && $at('m', 'nps30') - $at('m', 'months3') >= 30 * $D, 'm asked « three months »: its day 30 waited 30 days after it; w is still 8 days old: no day 30');

// 5. the 3-day rule against any automatic news email
$pdo->exec("DELETE FROM mail_queue"); $pdo->exec("DELETE FROM email_events_log");
$user('w2', 'en', 9, 1);
ma_send('w2', 'inactive3d');
ma_feedback_run(['w2'], $now);
$ok($pairs() === ['w2:inactive3d'], 'an absence email queued today: week one waits');
$age(3); ma_feedback_run(['w2'], $now);
$ok($pairs() === ['w2:inactive3d', 'w2:weekOne'], '3 days later: week one leaves');

// 6. switched off again: not claimed, the traders due get it once switched on
$pdo->exec("DELETE FROM mail_queue"); $pdo->exec("DELETE FROM email_events_log");
$on($F, false); ma_feedback_run($ids, $now);
$ok($q() === [] && $logged('') === 0, 'off: the moment does not pass');
$on(['weekOne'], true); ma_feedback_run(array_merge($ids, ['w2']), $now);
$ok($pairs() === ['w:weekOne', 'w2:weekOne'], 'week one on: the traders in their first weeks');

// 7. « You asked for it, it is done »
$on(['feedbackShipped'], true); $pdo->exec("DELETE FROM mail_queue");
$pdo->exec("INSERT INTO feedback (user_id, message, reply, status) VALUES ('n', 'Please add a calendar   view\nof my trades', 'Under Calendar.', 'planned'), ('n', '', NULL, 'new')");
ma_on_feedback(['uid' => 'n', 'item_id' => 1, 'from' => 'planned', 'to' => 'in_progress', 'reply' => '']);
$ok($q() === [], 'another status: nothing');
ma_on_feedback(['uid' => 'n', 'item_id' => 1, 'from' => 'in_progress', 'to' => 'shipped', 'reply' => 'You will find it under Calendar.']);
ma_on_feedback(['uid' => 'n', 'item_id' => 1, 'from' => 'planned', 'to' => 'shipped', 'reply' => 'Again']);
$sv = json_decode((string) ($q()[0]['vars_json'] ?? ''), true);
$ok(count($q()) === 1 && $q()[0]['auto'] === 'feedbackShipped' && $sv === ['request' => 'Please add a calendar view of my trades', 'reply' => 'You will find it under Calendar.'], 'shipped: the author gets it once, with the request (one line) and the reply');
$row = $pdo->query('SELECT * FROM mail_queue LIMIT 1')->fetch(); $camps = []; $m = ml_compose($pdo, $row, $camps);
$ok($m[1] === 'You asked for it, it is done' && strpos($m[2], '“Please add a calendar view of my trades”') !== false && strpos($m[2], 'It is in Sweep now. You will find it under Calendar.') !== false, 'rendered: the request quoted, the reply after « It is in Sweep now. »');
ma_on_feedback(['uid' => 'n', 'item_id' => 2, 'from' => 'new', 'to' => 'shipped', 'reply' => '']);
ma_on_feedback(['uid' => 'w', 'item_id' => 1, 'from' => 'new', 'to' => 'shipped', 'reply' => '']);
$ok(count($q()) === 1, 'a feedback without words, or someone else’s: nothing');

// 8. the preview's example values
$ex = ma_example('fr');
$ok($ex['feature'] === 'les stats' && $ex['feature_link'] === 'https://app.test/#analytics' && $ex['request'] !== '' && $ex['reply'] !== '' && ma_example('es')['feature_button'] === 'Ver mis estadísticas', 'the preview: an example of each value, in its language');

foreach (glob($tmp . '/*') as $x) @unlink($x); @rmdir($tmp);
echo "\n$pass passed, $fail failed\n";
exit($fail ? 1 : 0);
