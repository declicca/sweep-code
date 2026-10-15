<?php
declare(strict_types=1);
/**
 * Sweep — decrypt a backup to a usable file (manual restore).
 *   php ops/restore.php /home/matnsabc/sweep-backups/daily/sweep-db-XXXX.sqlite.gz.enc /home/matnsabc/restored.sqlite
 *   php ops/restore.php /home/matnsabc/sweep-backups/weekly/sweep-files-XXXX.tar.gz.enc /home/matnsabc/restored-files.tar.gz
 * To put a database back: put the app in maintenance (rename config.php for a minute), replace data/journal.db by
 * the restored file, delete journal.db-wal and journal.db-shm, then rename config.php back.
 */
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
require __DIR__ . '/ops-lib.php';
[$_, $in, $out] = $argv + [null, null, null];
if (!$in || !$out) { echo "usage: php ops/restore.php <backup.enc> <output file>\n"; exit(1); }
$cfg = ops_cfg();
ops_decrypt_file($in, $out, $cfg['passphrase'], substr($in, -14) === '.sqlite.gz.enc');   // a database comes out as .sqlite, the files archive as .tar.gz
echo "restored to $out (" . round(filesize($out) / 1048576, 2) . " MB)\n";
