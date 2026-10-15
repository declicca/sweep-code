<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli' && realpath((string) ($_SERVER['SCRIPT_FILENAME'] ?? '')) === realpath(__FILE__)) { http_response_code(404); exit; }
/**
 * Sweep — what runs in the background (brief 02 step 0). Every scheduled task records its last run in `cron_runs`
 * (start, end, duration, success or the error that stopped it); Admin › Health shows one line per task (green, orange
 * when late, red when it failed, is stuck or never ran); the support address gets ONE email per incident when a task
 * stays red for more than one cycle. The tasks, their schedule and the exact cPanel command: ops/CRON.md.
 * Tracking never stops a task: any error here is logged and the task carries on.
 */
const SWEEP_CRON_PHP = '/usr/local/bin/php';
/** name => [script, cron schedule, expected interval in seconds, output kept for cPanel's « Cron Email »] */
const SWEEP_CRON_TASKS = [
    'game'         => ['game/cron.php', '*/15 * * * *', 900, false],
    'chart'        => ['chart/cron.php', '0 * * * *', 3600, false],
    'presets'      => ['presets/cron.php', '0 5 * * 1', 604800, false],
    'backup'       => ['ops/backup.php', '30 3 * * *', 86400, true],         // prints only when something goes wrong
    'restore_test' => ['ops/restore-test.php', '0 6 * * 1', 604800, true],   // its report is the weekly proof that backups restore
    'emails'       => ['loops/cron.php', '30 * * * *', 3600, false],      // Loops: the daily events from 7:30 New York time (the other runs catch up)
];

function sweep_cron_schema(PDO $pdo): void
{
    static $done = false; if ($done) return;
    $T = $pdo->getAttribute(PDO::ATTR_DRIVER_NAME) === 'mysql' ? 'VARCHAR(40)' : 'TEXT';
    $pdo->exec("CREATE TABLE IF NOT EXISTS cron_runs (task $T NOT NULL PRIMARY KEY, started_at INT NULL, finished_at INT NULL, duration_ms INT NULL,
        ok INT NULL, error TEXT NULL, note TEXT NULL, last_ok_at INT NULL, red_since INT NULL, alerted_at INT NULL)");
    $done = true;
}
function sweep_cron_row(PDO $pdo, string $task): void
{
    $st = $pdo->prepare('SELECT 1 FROM cron_runs WHERE task = ?'); $st->execute([$task]);
    if (!$st->fetchColumn()) $pdo->prepare('INSERT INTO cron_runs (task) VALUES (?)')->execute([$task]);
}
/** the exact line for cPanel → Cron Jobs (schedule + command) */
function sweep_cron_command(string $task): string
{
    [$script, , , $mail] = SWEEP_CRON_TASKS[$task];
    return SWEEP_CRON_PHP . ' ' . dirname(__DIR__) . '/' . $script . ($mail ? '' : ' >/dev/null 2>&1');
}

/** at the top of a task: records its start; its end is recorded when the script stops (success, or what stopped it) */
function sweep_cron_start(PDO $pdo, string $task): void
{
    global $SWEEP_CRON;
    try {
        sweep_cron_schema($pdo); sweep_cron_row($pdo, $task);
        $pdo->prepare('UPDATE cron_runs SET started_at = ? WHERE task = ?')->execute([time(), $task]);
    } catch (Throwable $e) { error_log('[Sweep cron] ' . $task . ' start not recorded: ' . $e->getMessage()); return; }
    $SWEEP_CRON = ['pdo' => $pdo, 'task' => $task, 't0' => microtime(true), 'done' => false, 'err' => null, 'note' => ''];
    register_shutdown_function('sweep_cron_finish');
}
/** a task that fails records why (call it before exit(1)) */
function sweep_cron_fail(string $msg): void { global $SWEEP_CRON; if ($SWEEP_CRON) $SWEEP_CRON['err'] = mb_substr(trim($msg), 0, 500); }
/** a short summary of a successful run (« 42 players ») */
function sweep_cron_note(string $note): void { global $SWEEP_CRON; if ($SWEEP_CRON) $SWEEP_CRON['note'] = mb_substr(trim($note), 0, 200); }
function sweep_cron_finish(): void
{
    global $SWEEP_CRON;
    if (!$SWEEP_CRON || $SWEEP_CRON['done']) return;
    $SWEEP_CRON['done'] = true;
    $e = error_get_last();
    $fatal = $e && in_array($e['type'], [E_ERROR, E_PARSE, E_CORE_ERROR, E_COMPILE_ERROR, E_USER_ERROR], true);
    $err = $SWEEP_CRON['err'] ?? ($fatal ? trim(strtok((string) $e['message'], "\n")) . ' (' . basename((string) $e['file']) . ':' . $e['line'] . ')' : null);   // first line: no stack trace
    $now = time();
    try {
        $SWEEP_CRON['pdo']->prepare('UPDATE cron_runs SET finished_at = ?, duration_ms = ?, ok = ?, error = ?, note = ?, last_ok_at = ' . ($err === null ? '?' : 'last_ok_at') . ' WHERE task = ?')
            ->execute(array_merge([$now, (int) round((microtime(true) - $SWEEP_CRON['t0']) * 1000), $err === null ? 1 : 0, $err !== null ? mb_substr($err, 0, 500) : null, $SWEEP_CRON['note'] ?: null],
                $err === null ? [$now] : [], [$SWEEP_CRON['task']]));
    } catch (Throwable $x) { error_log('[Sweep cron] ' . $SWEEP_CRON['task'] . ' end not recorded: ' . $x->getMessage()); }
}

/**
 * One line per task. green: last run fine and on time (or running) · orange: no successful run for two cycles (+10 min)
 * · red: the last run failed, a run is stuck (started, never ended, for over an hour or a cycle), or it never ran.
 */
function sweep_cron_status(PDO $pdo, ?int $now = null): array
{
    $now = $now ?? time(); sweep_cron_schema($pdo);
    $rows = []; foreach ($pdo->query('SELECT * FROM cron_runs')->fetchAll(PDO::FETCH_ASSOC) as $r) $rows[$r['task']] = $r;
    $out = [];
    foreach (SWEEP_CRON_TASKS as $task => [$script, $when, $every]) {
        $r = $rows[$task] ?? []; $i = fn(string $k) => isset($r[$k]) ? (int) $r[$k] : null;
        $started = $i('started_at'); $finished = $i('finished_at'); $lastOk = $i('last_ok_at');
        if ($started === null) $s = ['red', 'never'];
        elseif ($finished === null || $finished < $started) $s = $now - $started > max(3600, $every) ? ['red', 'stuck'] : ['green', 'running'];
        elseif ($i('ok') !== 1) $s = ['red', 'failed'];
        elseif ($lastOk === null || $now - $lastOk > 2 * $every + 600) $s = ['orange', 'late'];
        else $s = ['green', 'ok'];
        $out[] = ['task' => $task, 'script' => $script, 'schedule' => $when, 'every' => $every, 'command' => sweep_cron_command($task),
            'color' => $s[0], 'state' => $s[1], 'started_at' => $started, 'finished_at' => $finished, 'duration_ms' => $i('duration_ms'),
            'last_ok_at' => $lastOk, 'error' => $r['error'] ?? null, 'note' => $r['note'] ?? null, 'red_since' => $i('red_since'), 'alerted_at' => $i('alerted_at')];
    }
    return $out;
}

/**
 * Run every 15 minutes (end of game/cron.php) and at most once an hour by the app itself (in case the 15-minute task is the
 * one that stopped). A task red for more than one cycle, or late (orange) at once → one email to the support address; none
 * again until it is back to normal (green). $mail(subject, text) returns true when sent. Returns the number of emails sent.
 */
function sweep_cron_watch(PDO $pdo, callable $mail, ?int $now = null): int
{
    $now = $now ?? time(); $sent = 0;
    foreach (sweep_cron_status($pdo, $now) as $s) {
        $task = $s['task']; sweep_cron_row($pdo, $task);
        if ($s['color'] === 'green') {
            if ($s['red_since'] !== null) $pdo->prepare('UPDATE cron_runs SET red_since = NULL, alerted_at = NULL WHERE task = ?')->execute([$task]);
            continue;
        }
        // late (orange: no successful run for two cycles) alerts too, at once: a task that silently stopped running is the
        // incident that matters most (before 16 Oct. only red alerted; a stopped backup could wait ~13 days)
        $late = $s['state'] === 'late';
        if ($s['red_since'] === null) { $pdo->prepare('UPDATE cron_runs SET red_since = ? WHERE task = ?')->execute([$now, $task]); if (!$late) continue; $s['red_since'] = $now; }
        if ($s['alerted_at'] !== null || (!$late && $now - $s['red_since'] < $s['every'])) continue;
        $what = ['never' => "n'a jamais tourné", 'failed' => 'a échoué', 'stuck' => "a démarré sans jamais finir", 'late' => "ne tourne plus (aucun passage réussi depuis deux cycles)"][$s['state']] ?? $s['state'];
        $when = fn(?int $t) => $t ? gmdate('Y-m-d H:i', $t) . ' UTC' : '—';
        $text = "La tâche planifiée « $task » ($s[script]) $what.\n\n"
            . 'Dernier démarrage : ' . $when($s['started_at']) . "\nDernière fin : " . $when($s['finished_at']) . "\nDernier succès : " . $when($s['last_ok_at']) . "\n"
            . ($s['error'] ? "Erreur : $s[error]\n" : '')
            . "\nDans cPanel → Cron Jobs, la ligne attendue :\n$s[schedule]  $s[command]\n\nDétail : Admin › Santé de l'app. Aucun autre courriel tant qu'elle n'est pas revenue à la normale.";
        try { $ok = (bool) $mail("Sweep : tâche planifiée « $task » " . ($late ? 'en retard' : 'en échec'), $text); } catch (Throwable $e) { $ok = false; error_log('[Sweep cron] alert: ' . $e->getMessage()); }
        if ($ok) { $pdo->prepare('UPDATE cron_runs SET alerted_at = ? WHERE task = ?')->execute([$now, $task]); $sent++; }
    }
    return $sent;
}
