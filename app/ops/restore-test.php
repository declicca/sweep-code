<?php
declare(strict_types=1);
/**
 * Sweep — restore test (monthly cron) and live integrity check.
 *   /usr/local/bin/php /home/matnsabc/app.makeitsweep.com/ops/restore-test.php
 * Decrypts the latest backup into a temporary file, checks it opens, passes integrity_check and holds the
 * same users as the live database (± sign-ups since the backup). Also runs PRAGMA quick_check on the live
 * database. Prints a short report (cron mails it: that report is your monthly proof that backups restore).
 */
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
require __DIR__ . '/ops-lib.php';
$cfg = ops_cfg(); $bad = false; $out = [];
$all = glob($cfg['dir'] . '/daily/sweep-db-*.enc') ?: []; sort($all);
$last = end($all);
if (!$last) { echo "[Sweep restore test] FAILED: no backup found in {$cfg['dir']}/daily\n"; exit(1); }
$tmp = sys_get_temp_dir() . '/sweep-restore-' . bin2hex(random_bytes(4)) . '.sqlite';
try {
    file_put_contents($tmp, gzdecode(ops_decrypt((string) file_get_contents($last), $cfg['passphrase'])));
    $b = new PDO('sqlite:' . $tmp, null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
    $ok = $b->query('PRAGMA integrity_check')->fetchColumn();
    $bu = (int) $b->query('SELECT COUNT(*) FROM users')->fetchColumn();
    $bd = (int) $b->query('SELECT COUNT(*) FROM documents')->fetchColumn();
    $b = null;
    $l = new PDO('sqlite:' . $cfg['db'], null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
    $lq = $l->query('PRAGMA quick_check')->fetchColumn();
    $lu = (int) $l->query('SELECT COUNT(*) FROM users')->fetchColumn();
    $ld = (int) $l->query('SELECT COUNT(*) FROM documents')->fetchColumn();
    $out[] = 'backup: ' . basename($last) . ' (' . round(filesize($last) / 1048576, 2) . ' MB)';
    $out[] = "restored copy: integrity $ok · $bu users · $bd documents";
    $out[] = "live database: quick_check $lq · $lu users · $ld documents";
    if ($ok !== 'ok' || $lq !== 'ok' || $bu === 0 || $bu > $lu) $bad = true;
    $age = time() - filemtime($last);
    if ($age > 36 * 3600) { $bad = true; $out[] = 'WARNING: latest backup is ' . round($age / 3600) . ' h old (the daily cron may not be running)'; }
} catch (Throwable $e) { $bad = true; $out[] = 'error: ' . $e->getMessage(); }
@unlink($tmp);
echo '[Sweep restore test] ' . ($bad ? 'FAILED' : 'OK') . ' · ' . gmdate('Y-m-d H:i') . " UTC\n  " . implode("\n  ", $out) . "\n";
exit($bad ? 1 : 0);
