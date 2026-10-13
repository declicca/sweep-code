<?php
declare(strict_types=1);
/**
 * Sweep — the JS errors seen on traders' devices (13 Oct.), on a throwaway SQLite database:
 *   php tests/client_errors_test.php
 *  - one error = one message with its numbers taken out (the « Trade page jump » reports of every size are one error);
 *  - the list: counts, traders, first and last time, pages, browsers, versions, the last 3 occurrences, most traders first;
 *  - the Markdown export (Admin › Errors › Export): one block per error, no trader id;
 *  - the email to the support address: the first time an error is seen, not again for 7 days, at most 10 a day, sent
 *    again later when the first try failed.
 */
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
$app = dirname(__DIR__);
$pdo = new PDO('sqlite::memory:', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC]);
require $app . '/ops/client-errors.php';
$pass = 0; $fail = 0;
$ok = function (bool $c, string $what) use (&$pass, &$fail) { echo ($c ? 'ok   ' : 'FAIL ') . $what . "\n"; $c ? $pass++ : $fail++; };
sweep_errors_schema($pdo);
$T = 1791990000;
$add = function (string $uid, string $msg, int $at, string $page = '#trade', string $ua = 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_1 like Mac OS X) AppleWebKit/605.1.15 Version/18.1 Mobile/15E148 Safari/604.1', string $ver = '', string $src = 'nav.js jump report', int $line = 0) use ($pdo) {
    $pdo->prepare('INSERT INTO client_errors (user_id, msg, src, line, page, ua, ver, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)')->execute([$uid, $msg, $src, $line, $page, $ua, $ver, $at]);
};
$add('u1', 'Trade page jump: tapped control moved +25px at 84ms | blocks: surface +25px at 84ms | tapped set | 440x836', $T - 9 * 86400);
$add('u1', 'Trade page jump: tapped control moved +25px at 96ms | blocks: surface +25px at 96ms | tapped set | 440x836', $T - 9 * 86400 + 60);
$add('u2', 'Trade page jump: tapped control moved +25px at 101ms | blocks: surface +25px at 101ms | tapped set | 390x844', $T - 8 * 86400);
for ($i = 0; $i < 12; $i++) $add('u3', "Uncaught TypeError: Cannot read properties of null (reading 'hidden')", $T - 86400 + $i * 60, '#dashboard', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/141.0 Safari/537.36', 'app.e432fafbfd.js', 'https://app.makeitsweep.com/assets/nav.f0dc1d3152.js', 1);
$add('u4', 'Old error', $T - 40 * 86400);

$g = sweep_err_groups($pdo, $T);
$jump = array_values(array_filter($g, fn($x) => strpos($x['msg'], 'Trade page jump') === 0));
$ok(count($g) === 2 && count($jump) === 1 && $jump[0]['n'] === 3 && $jump[0]['traders'] === 2, 'the 3 « Trade page jump » reports (other numbers) are one error: 3 times, 2 traders; nothing older than 30 days (' . count($g) . ' errors)');
$ok($g[0]['traders'] === 2 && strpos($g[1]['msg'], 'hidden') !== false && $g[1]['n'] === 12, 'most traders first, then the 12 « hidden » errors');
$h = $g[1];
$ok($h['where'] === 'https://app.makeitsweep.com/assets/nav.f0dc1d3152.js:1' && $h['pages'] === ['#dashboard'] && $h['browsers'] === ['Chrome macOS'] && $h['versions'] === ['app.e432fafbfd.js'] && $h['first'] === $T - 86400 && $h['last'] === $T - 86400 + 660, 'where, page, browser, version, first and last time');
$ok(count($h['samples']) === 3 && $h['samples'][0]['at'] === $T - 86400 + 660, 'the last 3 occurrences, latest first');
$ok(sweep_err_key('moved -364px at 621ms') === sweep_err_key('moved +25px at 84ms') && sweep_err_key('moved -364px at 621ms') === 'moved #px at #ms', 'the key: numbers and their sign taken out (« moved #px at #ms »)');

$md = sweep_errors_report($pdo, $T);
$ok(strpos($md, '# Sweep — erreurs chez les traders (30 derniers jours)') === 0 && substr_count($md, "\n## ") === 2, 'the export: a title and one block per error');
$ok(strpos($md, "- Où : `https://app.makeitsweep.com/assets/nav.f0dc1d3152.js:1`") !== false && strpos($md, '12 fois, 1 trader') !== false && strpos($md, 'Chrome macOS') !== false && strpos($md, 'app.e432fafbfd.js') !== false, 'each block: where, how often, how many traders, browser, version');
$ok(strpos($md, 'u1') === false && strpos($md, 'u3') === false && strpos($md, 'Old error') === false, 'no trader id, nothing older than 30 days');
$ok(strpos(sweep_errors_report(new PDO('sqlite::memory:'), $T), 'Aucune erreur en 30 jours.') !== false, 'no error: says so');

$sent = [];
$mail = function (string $s, string $t) use (&$sent) { $sent[] = [$s, $t]; return true; };
$ok(sweep_error_alert($pdo, "Uncaught TypeError: Cannot read properties of null (reading 'hidden')", $mail, $T) && count($sent) === 1, 'a new error: one email to the support address');
$ok(strpos($sent[0][0], 'Sweep : nouvelle erreur') === 0 && strpos($sent[0][1], '## 1. Uncaught TypeError') !== false && strpos($sent[0][1], 'colle ce courriel à Claude') !== false, 'the email: its block, and what to do with it');
$ok(!sweep_error_alert($pdo, "Uncaught TypeError: Cannot read properties of null (reading 'hidden')", $mail, $T + 3600) && count($sent) === 1, 'the same error an hour later: no second email');
$ok(sweep_error_alert($pdo, 'Trade page jump: tapped control moved -12px at 22ms | blocks: surface -12px at 22ms | tapped set | 390x844', $mail, $T + 7200) && count($sent) === 2, 'another error (a « Trade page jump »): its own email');
$ok(!sweep_error_alert($pdo, 'Trade page jump: tapped control moved +40px at 70ms | blocks: surface +40px at 70ms | tapped set | 390x844', $mail, $T + 7300) && count($sent) === 2, '… and not one per size of jump');
$n0 = count($sent);
$add('u3', "Uncaught TypeError: Cannot read properties of null (reading 'hidden')", $T + 8 * 86400, '#dashboard');
$ok(sweep_error_alert($pdo, "Uncaught TypeError: Cannot read properties of null (reading 'hidden')", $mail, $T + 8 * 86400 + 10) && count($sent) === $n0 + 1, 'seen again after 7 days: one email again');
// at most 10 a day
$day = $T + 20 * 86400; $before = count($sent);
for ($i = 0; $i < 14; $i++) { $add('u9', "Error number $i x" . str_repeat('y', $i), $day + $i); sweep_error_alert($pdo, "Error number $i x" . str_repeat('y', $i), $mail, $day + $i); }
$ok(count($sent) - $before === 10, 'at most 10 emails a day (' . (count($sent) - $before) . ' for 14 new errors)');
// the mail could not go: tried again next time
$down = function () { return false; };
$add('u9', 'Mail down error', $T + 30 * 86400);
$ok(!sweep_error_alert($pdo, 'Mail down error', $down, $T + 30 * 86400) && sweep_error_alert($pdo, 'Mail down error', $mail, $T + 30 * 86400 + 60), 'an email that could not go is tried again with the next occurrence');

echo "\n$pass/" . ($pass + $fail) . " passed\n";
exit($fail ? 1 : 0);
