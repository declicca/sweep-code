<?php
declare(strict_types=1);
/**
 * Sweep — automatic backups (CLI only, cPanel cron).
 *
 *   Daily:  /usr/local/bin/php /home/matnsabc/app.makeitsweep.com/ops/backup.php
 *   Test:   /usr/local/bin/php /home/matnsabc/app.makeitsweep.com/ops/restore-test.php   (monthly)
 *
 * 1. Hot copy of the SQLite database with `VACUUM INTO` (never a raw file copy while it is in use),
 *    then `PRAGMA integrity_check` on the copy.
 * 2. Compressed (gzip) and encrypted (AES-256-GCM, key derived from the passphrase in the private config), streamed by
 *    chunks of 1 MB since 16 Oct. (format SWB2, ops-lib.php): the database is never held in memory.
 * 3. Kept locally outside the web root: 7 daily, 4 weekly (Sunday), 12 monthly (1st of the month).
 * 4. Uploaded screenshots + private config + feedback screenshots + prop firm catalogue: a weekly encrypted archive (same
 *    rotation folders).
 * 5. Optional off-site copy to any S3-compatible storage (Backblaze B2, Cloudflare R2, AWS S3, Wasabi):
 *    set the retention there with a bucket lifecycle rule.
 * Prints nothing when everything is fine (cron mails only on problems); exit code 1 on failure.
 *
 * Config: /home/<user>/sweep-private/backup-config.php (template: ops/backup-config.sample.php).
 */
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
require __DIR__ . '/ops-lib.php';

$cfg = ops_cfg();
$fail = function (string $m) { fwrite(STDERR, '[Sweep backup] ' . $m . "\n"); error_log('[Sweep backup] ' . $m); if (function_exists('sweep_cron_fail')) sweep_cron_fail($m); exit(1); };
if (is_file($cfg['db'])) { try { require_once __DIR__ . '/cron-lib.php'; sweep_cron_start(new PDO('sqlite:' . $cfg['db'], null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]), 'backup'); } catch (Throwable $e) { error_log('[Sweep backup] health: ' . $e->getMessage()); } }   // Admin › Health (brief 02 step 0)
if ($cfg['passphrase'] === '') $fail('no passphrase in backup-config.php: refusing to write unencrypted backups');
if (!is_file($cfg['db'])) $fail('database not found: ' . $cfg['db']);
foreach (['daily', 'weekly', 'monthly'] as $d) if (!is_dir($cfg['dir'] . "/$d") && !@mkdir($cfg['dir'] . "/$d", 0700, true)) $fail('cannot create ' . $cfg['dir'] . "/$d");

$stamp = gmdate('Ymd-His');
$tmp = sys_get_temp_dir() . "/sweep-$stamp-" . bin2hex(random_bytes(4)) . '.sqlite';

// 1. hot copy + integrity
try {
    $pdo = new PDO('sqlite:' . $cfg['db'], null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
    $pdo->exec('PRAGMA busy_timeout = 15000');
    $pdo->exec('VACUUM INTO ' . $pdo->quote($tmp));
    $pdo = null;
    $chk = new PDO('sqlite:' . $tmp, null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
    $ok = $chk->query('PRAGMA integrity_check')->fetchColumn();
    $users = (int) $chk->query('SELECT COUNT(*) FROM users')->fetchColumn();
    $chk = null;
    if ($ok !== 'ok') { @unlink($tmp); $fail('integrity_check failed on the copy: ' . $ok); }
} catch (Throwable $e) { @unlink($tmp); $fail('copy failed: ' . $e->getMessage()); }

// 2. compress + encrypt
$name = "sweep-db-$stamp-u$users.sqlite.gz.enc";
$daily = $cfg['dir'] . "/daily/$name";
try { ops_encrypt_file($tmp, $daily, $cfg['passphrase']); }   // streamed: never the whole database in memory (16 Oct.)
catch (Throwable $e) { @unlink($tmp); @unlink($daily); $fail('cannot write ' . $daily . ': ' . $e->getMessage()); }
@unlink($tmp);
@chmod($daily, 0600);
$files = [$daily];

// 3. weekly / monthly copies
$dow = (int) gmdate('N'); $dom = (int) gmdate('j');
if ($dow === 7) { copy($daily, $cfg['dir'] . "/weekly/$name"); $files[] = $cfg['dir'] . "/weekly/$name"; }
if ($dom === 1) { copy($daily, $cfg['dir'] . "/monthly/$name"); $files[] = $cfg['dir'] . "/monthly/$name"; }

// 4. weekly: uploaded screenshots + private config
if ($dow === 7 || !glob($cfg['dir'] . '/weekly/sweep-files-*')) {
    try {
        $tar = sys_get_temp_dir() . "/sweep-files-$stamp.tar";
        $phar = new PharData($tar);
        if (is_dir($cfg['uploads'])) $phar->buildFromDirectory($cfg['uploads']);
        foreach (glob($cfg['private'] . '/*.php') ?: [] as $f) $phar->addFile($f, 'sweep-private/' . basename($f));
        // and since 16 Oct.: the feedback screenshots and the prop firm catalogue (the checked rules, their status, their history)
        $data = dirname($cfg['db']);
        foreach (glob($data . '/feedback/*') ?: [] as $f) if (is_file($f)) $phar->addFile($f, 'feedback/' . basename($f));
        foreach (array_merge([$data . '/presets-live.json', $data . '/presets-status.json'], glob($data . '/presets-history/*') ?: []) as $f) if (is_file($f)) $phar->addFile($f, 'presets/' . (strpos($f, '/presets-history/') !== false ? 'presets-history/' : '') . basename($f));
        $fname = "sweep-files-$stamp.tar.gz.enc";
        ops_encrypt_file($tar, $cfg['dir'] . "/weekly/$fname", $cfg['passphrase']);
        @chmod($cfg['dir'] . "/weekly/$fname", 0600);
        @unlink($tar);
        $files[] = $cfg['dir'] . "/weekly/$fname";
    } catch (Throwable $e) { fwrite(STDERR, '[Sweep backup] files archive skipped: ' . $e->getMessage() . "\n"); }
}

// rotation
foreach (['daily' => 7, 'weekly' => 4, 'monthly' => 12] as $d => $keep) {
    foreach (['sweep-db-', 'sweep-files-'] as $prefix) {
        $all = glob($cfg['dir'] . "/$d/$prefix*") ?: []; sort($all);
        foreach (array_slice($all, 0, max(0, count($all) - $keep)) as $old) @unlink($old);
    }
}

// 5. off-site
if (!empty($cfg['s3']['bucket'])) {
    foreach ($files as $f) {
        $key = trim((string) ($cfg['s3']['prefix'] ?? 'sweep'), '/') . '/' . basename(dirname($f)) . '/' . basename($f);
        $r = ops_s3_put_file($cfg['s3'], $key, $f);   // read from the file, not copied in memory
        if ($r !== true) $fail('off-site upload failed for ' . basename($f) . ': ' . $r);
    }
}
file_put_contents($cfg['dir'] . '/last-success.txt', gmdate('c') . " $name\n");
if (function_exists('sweep_cron_note')) sweep_cron_note($name . (!empty($cfg['s3']['bucket']) ? ' + off-site copy' : ' (no off-site copy)'));
exit(0);
