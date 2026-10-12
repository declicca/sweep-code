<?php
declare(strict_types=1);
/**
 * Sweep — what runs in the background (brief 02 step 0), on a throwaway SQLite database (never the live one):
 *   php tests/cron_health_test.php
 *  - a task records its last run: success (duration, summary), failure (its message) and a fatal error (what stopped it),
 *    each in a real separate PHP process, like cron;
 *  - one line per task: OK, running, late after two cycles, failed, stuck, never ran;
 *  - ONE email to the support address when a task stays red for more than one cycle, none again until it is back to normal;
 *  - the exact cPanel line of each task.
 */
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
$app = dirname(__DIR__);
$tmp = sys_get_temp_dir() . '/sweep-cron-' . bin2hex(random_bytes(4)); mkdir($tmp);
$db = $tmp . '/t.db';
$pdo = new PDO('sqlite:' . $db, null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC]);
require $app . '/ops/cron-lib.php';
$pass = 0; $fail = 0;
$ok = function (bool $c, string $what) use (&$pass, &$fail) { echo ($c ? 'ok   ' : 'FAIL ') . $what . "\n"; $c ? $pass++ : $fail++; };
// a task run the way cron runs it: its own PHP process
$run = function (string $task, string $body) use ($app, $db, $tmp): int {
    $f = $tmp . "/$task.php";
    file_put_contents($f, "<?php\nrequire " . var_export($app . '/ops/cron-lib.php', true) . ";\n\$pdo = new PDO('sqlite:' . " . var_export($db, true) . ", null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);\nsweep_cron_start(\$pdo, " . var_export($task, true) . ");\n$body\n");
    exec(escapeshellarg(PHP_BINARY) . ' ' . escapeshellarg($f) . ' 2>/dev/null', $o, $code); return $code;
};
$row = fn(string $t) => $pdo->query('SELECT * FROM cron_runs WHERE task = ' . $pdo->quote($t))->fetch() ?: [];

$c = $run('game', "usleep(120000); sweep_cron_note('3 player(s)');");
$r = $row('game');
$ok($c === 0 && (int) $r['ok'] === 1 && $r['error'] === null && $r['note'] === '3 player(s)' && (int) $r['last_ok_at'] === (int) $r['finished_at'], 'success: recorded, with its summary');
$ok((int) $r['duration_ms'] >= 100 && (int) $r['finished_at'] >= (int) $r['started_at'], "success: duration ({$r['duration_ms']} ms)");
$c = $run('backup', "sweep_cron_fail('no passphrase in backup-config.php'); exit(1);");
$r = $row('backup');
$ok($c === 1 && (int) $r['ok'] === 0 && $r['error'] === 'no passphrase in backup-config.php' && $r['last_ok_at'] === null, 'failure: recorded with its message, exit code kept (cron mail)');
$c = $run('chart', "sweep_cron_note('half done'); undefined_function_here();");
$r = $row('chart');
$ok($c !== 0 && (int) $r['ok'] === 0 && strpos((string) $r['error'], 'undefined_function_here') !== false, 'fatal error: what stopped the task is recorded (' . $r['error'] . ')');
$run('presets', "sweep_cron_note('7 firm(s) checked');");
$okAt = (int) $row('presets')['last_ok_at'];
$run('presets', "exit(1);");   // an exit without a message: nothing says it failed, the run is fine
$ok((int) $row('presets')['ok'] === 1, 'a plain exit without a recorded failure counts as a normal end');

// the lines, at different moments
$st = fn(int $now) => array_column(sweep_cron_status($pdo, $now), null, 'task');
$t0 = (int) $row('game')['finished_at'];
$s = $st($t0 + 60);
$ok($s['game']['color'] === 'green' && $s['game']['state'] === 'ok', 'game: OK just after its run');
$ok($s['backup']['color'] === 'red' && $s['backup']['state'] === 'failed', 'backup: red, failed');
$ok($s['chart']['color'] === 'red' && $s['chart']['state'] === 'failed', 'chart: red after a fatal error');
$ok($s['restore_test']['color'] === 'red' && $s['restore_test']['state'] === 'never', 'restore test: red, never ran');
$ok($st($t0 + 2 * 900 + 590)['game']['color'] === 'green' && $st($t0 + 2 * 900 + 610)['game']['state'] === 'late' && $st($t0 + 2 * 900 + 610)['game']['color'] === 'orange',
    'game: orange (late) after two cycles + 10 min without a successful run');
$pdo->prepare('UPDATE cron_runs SET started_at = ? WHERE task = ?')->execute([$t0 + 100, 'game']);   // a run that started and has not ended
$ok($st($t0 + 160)['game']['state'] === 'running' && $st($t0 + 160)['game']['color'] === 'green', 'a run in progress: green, running');
$ok($st($t0 + 100 + 3700)['game']['state'] === 'stuck' && $st($t0 + 100 + 3700)['game']['color'] === 'red', 'started more than an hour ago and never ended: red, stuck');
$pdo->prepare('UPDATE cron_runs SET started_at = ? WHERE task = ?')->execute([$t0 - 1, 'game']);
$ok($s['game']['command'] === '/usr/local/bin/php ' . $app . '/game/cron.php >/dev/null 2>&1' && $s['backup']['command'] === '/usr/local/bin/php ' . $app . '/ops/backup.php'
    && $s['presets']['schedule'] === '0 5 * * 1', 'the cPanel line of each task (the backup keeps its output for « Cron Email »)');

// alerts: one email per incident, after one cycle in red
$mails = []; $mail = function (string $subj, string $text) use (&$mails) { $mails[] = [$subj, $text]; return true; };
$n = function () use (&$mails) { return count($mails); };
$T = $t0 + 60;
sweep_cron_watch($pdo, $mail, $T);
$ok($n() === 0, 'red just noticed: no email yet');
sweep_cron_watch($pdo, $mail, $T + 3600);
$ok($n() === 1 && strpos($mails[0][0], 'chart') !== false, 'chart red for one cycle (1 h): one email (' . ($mails[0][0] ?? '') . ')');
$ok(strpos($mails[0][1] ?? '', '0 * * * *  /usr/local/bin/php ' . $app . '/chart/cron.php') !== false && strpos($mails[0][1] ?? '', 'undefined_function_here') !== false, 'the email gives the error and the cPanel line');
sweep_cron_watch($pdo, $mail, $T + 7200);
$ok($n() === 1, 'no second email for the same incident');
sweep_cron_watch($pdo, $mail, $T + 86400);
$ok($n() === 2 && strpos($mails[1][0], 'backup') !== false, 'backup red for one cycle (1 day): one email');
$run('chart', "sweep_cron_note('ok again');"); $back = (int) $row('chart')['finished_at'];
sweep_cron_watch($pdo, $mail, $back + 60);
$ok($row('chart')['red_since'] === null && $row('chart')['alerted_at'] === null, 'chart back to normal: the incident is closed');
$pdo->prepare('UPDATE cron_runs SET ok = 0, error = ? WHERE task = ?')->execute(['Databento 401', 'chart']);
sweep_cron_watch($pdo, $mail, $back + 120); sweep_cron_watch($pdo, $mail, $back + 120 + 3600);
$ok($n() === 3 && strpos($mails[2][1], 'Databento 401') !== false, 'a new incident later: a new email');
$ok(count(array_filter($mails, fn($m) => strpos($m[0], 'restore_test') !== false)) === 0 && $n() === 3, 'never ran for less than one cycle (1 week): no email yet');
sweep_cron_watch($pdo, $mail, $T + 7 * 86400 + 60);
$ok(count(array_filter($mails, fn($m) => strpos($m[0], 'restore_test') !== false)) === 1, 'never ran for a whole week: one email');
$nope = fn() => false; $before = $n();
$pdo->exec("UPDATE cron_runs SET alerted_at = NULL WHERE task = 'backup'");
sweep_cron_watch($pdo, $nope, $T + 8 * 86400);
$ok($row('backup')['alerted_at'] === null, 'an email that could not be sent is tried again at the next check');

foreach (glob($tmp . '/*') as $x) @unlink($x); @rmdir($tmp);
echo "\n$pass passed, $fail failed\n";
exit($fail ? 1 : 0);
