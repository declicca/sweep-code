<?php
declare(strict_types=1);
/**
 * Sweep — Admin › Feedback « What traders say » (brief « Courriels de feedback », step 5), on a throwaway SQLite database:
 *   php tests/mail_insights_test.php
 *  - the NPS of the « Day 30 » email: share of 9-10 minus share of 0-6 over 90 days, the 90 days before, each of 6 months;
 *  - the one-click answers of each email that got some (the NPS aside), how many chose each option;
 *  - what the active traders use (Sweep's own accounts aside), the last 10 comments, newest first;
 *  - the list's filters: an email's option, an NPS group, the lines with a comment.
 */
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
$app = dirname(__DIR__);
$tmp = sys_get_temp_dir() . '/sweep-mail-insights-' . bin2hex(random_bytes(4)); mkdir($tmp);
ini_set('error_log', $tmp . '/php.log'); putenv('SWEEP_TEST_DB=' . $tmp . '/t.db');
$pdo = new PDO('sqlite:' . $tmp . '/t.db', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC]);
$pdo->exec('CREATE TABLE users (id TEXT PRIMARY KEY, username TEXT, email TEXT, first_name TEXT, lang TEXT, created_at TEXT, last_login TEXT, disabled INTEGER NOT NULL DEFAULT 0, is_admin INTEGER NOT NULL DEFAULT 0, is_internal INTEGER NOT NULL DEFAULT 0)');
$pdo->exec('CREATE TABLE app_settings (k TEXT PRIMARY KEY, v TEXT NOT NULL)');
function db(): PDO { global $pdo; return $pdo; }
$GLOBALS['cfg'] = ['app_url' => 'https://app.test/'];
require $app . '/mail/mail-core.php';
require $app . '/mail/mail-auto.php';
require $app . '/growth/feedback.php';
$pass = 0; $fail = 0;
$ok = function (bool $c, string $what) use (&$pass, &$fail) { echo ($c ? 'ok   ' : 'FAIL ') . $what . "\n"; $c ? $pass++ : $fail++; };
ml_schema($pdo); ma_seed($pdo); mu_schema($pdo); fb_schema($pdo);
$D = 86400; $now = time();

// nothing yet: an empty card, no error
$I = ml_insights($pdo, $now);
$ok($I['nps']['score'] === null && $I['nps']['n'] === 0 && $I['emails'] === [] && $I['notes'] === [] && count($I['nps']['months']) === 6, 'nothing yet: no score, no answer, no comment, 6 empty months');

foreach (['a' => 0, 'b' => 0, 'c' => 0, 'boss' => 1] as $id => $adm)
    $pdo->prepare('INSERT INTO users (id, username, email, lang, created_at, last_login, is_admin) VALUES (?, ?, ?, ?, ?, ?, ?)')->execute([$id, $id, "$id@x.test", 'en', '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z', $adm]);
$camp = fn(string $auto) => (int) $pdo->query("SELECT id FROM mail_campaigns WHERE auto = '$auto'")->fetchColumn();
$nps = $camp('nps30'); $week = $camp('weekOne');
$fb = function (string $uid, ?int $c, ?int $i, string $msg, int $ago, string $answer = '') use ($pdo, $now, $D) {
    $pdo->prepare("INSERT INTO feedback (user_id, type, message, status, created_at, src_queue, src_campaign, src_q, answer, answer_i) VALUES (?, ?, ?, 'new', ?, ?, ?, ?, ?, ?)")
        ->execute([$uid, $c ? 'answer' : 'idea', $msg, $now - $ago * $D, $c ? 1 : null, $c, $c ? 0 : null, $answer ?: ($i !== null ? (string) $i : null), $i]);
};
// the last 90 days: 10, 9 (promoters), 8 (passive), 3 (detractor) → 25; the 90 days before: 10 and 2 → 0; 300 days ago: left out
$fb('a', $nps, 10, 'Love the plan', 2); $fb('b', $nps, 9, '', 5); $fb('c', $nps, 8, '', 20); $fb('a', $nps, 3, 'Too slow', 60);
$fb('b', $nps, 10, '', 100); $fb('c', $nps, 2, '', 120); $fb('a', $nps, 0, '', 300);
$I = ml_insights($pdo, $now); $P = $I['nps'];
$ok($P['score'] === 25 && $P['n'] === 4 && [$P['p'], $P['pa'], $P['d']] === [2, 1, 1], 'NPS of the last 90 days: 2 promoters, 1 passive, 1 detractor → +25');
$ok($P['prev'] === 0 && $P['campaign'] === $nps && $P['days'] === 90, 'the 90 days before: 0 (one 10, one 2); the answer of 300 days ago left out');
$last = end($P['months']);
$ok($last['m'] === gmdate('Y-m', $now) && array_sum(array_column($P['months'], 'n')) >= 4, 'the trend: 6 months, the current one last');

// one-click answers: weekOne, first option twice, second once; the NPS has its own box
$fb('a', $week, 0, '', 1, 'Import from my platform'); $fb('b', $week, 0, 'Tradovate please', 1, 'Import from my platform'); $fb('c', $week, 1, '', 1, 'More stats');
$I = ml_insights($pdo, $now);
$ok(count($I['emails']) === 1 && $I['emails'][0]['id'] === $week && $I['emails'][0]['name']['fr'] === 'Une semaine de Sweep', 'the answers: weekOne only (the NPS apart), its name in 3 languages');
$Q = $I['emails'][0]['questions'][0] ?? null;
$ok($Q && $Q['total'] === 3 && (array) $Q['counts'] === [0 => 2, 1 => 1] && count($Q['opts']['es']) === 6, 'its question: 2 chose the first option, 1 the second; options in EN, FR, ES');

// what they use: the admin aside
foreach (['a' => ['journal' => 4, 'plan' => 2], 'b' => ['journal' => 1], 'boss' => ['journal' => 9, 'stats' => 9]] as $u => $d)
    $pdo->prepare('REPLACE INTO mail_usage (user_id, data_json, updated_at) VALUES (?, ?, ?)')->execute([$u, json_encode(['days' => $d, 'ever' => array_keys($d)]), $now]);
$U = ml_insights($pdo, $now)['usage']; $by = array_column($U['features'], 'pct', 'key');
$ok($U['active'] === 2 && $by['journal'] === 100 && $by['plan'] === 50 && $by['stats'] === 0 && $U['features'][0]['key'] === 'journal', 'what they use: 2 active traders (the admin aside), journal 100 %, plan 50 %, stats 0 %');

// the last 10 comments, newest first
for ($k = 0; $k < 12; $k++) $fb('c', null, null, "Idea $k", 30 + $k);
$N = ml_insights($pdo, $now)['notes'];
$ok(count($N) === 10 && $N[0]['message'] === 'Tradovate please' && $N[0]['user'] === 'b' && $N[1]['message'] === 'Love the plan', 'the last 10 comments, newest first, with the trader');

// the list, filtered by a click
$L = fn(array $f) => array_map(fn($o) => $o['message'] . '|' . ($o['mail']['answer'] ?? ''), fb_admin_list($pdo, null, null, $f)['items']);
$ok(count($L(['camp' => (string) $week, 'q' => '0', 'a' => '0'])) === 2 && count($L(['camp' => (string) $week, 'q' => '0', 'a' => '1'])) === 1, 'an option clicked: its answers only (2, then 1)');
$ok(count($L(['nps' => 'p'])) === 3 && count($L(['nps' => 'pa'])) === 1 && count($L(['nps' => 'd'])) === 3, 'an NPS group clicked: 9-10, 7-8, 0-6 (all time)');
$ok(count($L(['notes' => '1'])) === 15 && count($L([])) === 22 && count($L(['nps' => 'x'])) === 22, 'with a comment: 15 of 22; an unknown group filters nothing');

echo "\n$pass ok, $fail failed\n";
array_map('unlink', glob($tmp . '/*')); @rmdir($tmp);
exit($fail ? 1 : 0);
