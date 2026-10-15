<?php
declare(strict_types=1);
/**
 * Sweep — backups (brief 00, phase 1.1, 16 Oct.), on a throwaway folder (real data untouched):
 *   php tests/backup_test.php
 *  - a 30 MB database is backed up with only 24 MB of PHP memory (before 16 Oct. the backup held it three times in memory:
 *    read, gzip, encrypted — it failed on a large database);
 *  - the file is streamed (SWB2); ops/restore-test.php says OK; ops/restore.php gives back the same rows;
 *  - one byte changed, or the file cut short: the restore refuses it (never a half database);
 *  - an older one-piece backup (SWB1) still restores;
 *  - the weekly archive also holds the feedback screenshots and the prop firm catalogue.
 */
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
$app = dirname(__DIR__);
require $app . '/ops/ops-lib.php';
$pass = 0; $fail = 0;
$ok = function (bool $c, string $what) use (&$pass, &$fail) { echo ($c ? 'ok   ' : 'FAIL ') . $what . "\n"; $c ? $pass++ : $fail++; };
$tmp = sys_get_temp_dir() . '/sweep-backup-' . bin2hex(random_bytes(4)); mkdir($tmp); foreach (['data', 'data/uploads', 'data/feedback', 'data/presets-history', 'private', 'backups'] as $d) mkdir("$tmp/$d", 0777, true);
$db = "$tmp/data/journal.db";
$pdo = new PDO('sqlite:' . $db, null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
$pdo->exec('CREATE TABLE users (id TEXT PRIMARY KEY, username TEXT)'); $pdo->exec("INSERT INTO users VALUES ('u1', 'mateo')");
$pdo->exec('CREATE TABLE documents (user_id TEXT, collection TEXT, id TEXT, data TEXT, PRIMARY KEY (user_id, collection, id))');
$pdo->beginTransaction(); $st = $pdo->prepare('INSERT INTO documents VALUES (?, ?, ?, ?)');
for ($i = 0; $i < 6000; $i++) $st->execute(['u1', 'trades', "t$i", bin2hex(random_bytes(2400))]);   // ~30 MB, barely compressible
$pdo->commit(); $pdo = null;
clearstatcache(); $ok(filesize($db) > 28 * 1048576, 'a test database of ' . round(filesize($db) / 1048576) . ' MB');
file_put_contents("$tmp/data/uploads/shot1", 'png');
file_put_contents("$tmp/data/feedback/fb1.png", 'png'); file_put_contents("$tmp/data/presets-live.json", '{"version":"x"}'); file_put_contents("$tmp/data/presets-history/2026-10-01.json", '{}');
file_put_contents("$tmp/cfg.php", '<?php return ' . var_export(['db' => $db, 'uploads' => "$tmp/data/uploads", 'private' => "$tmp/private", 'dir' => "$tmp/backups", 'passphrase' => 'test passphrase'], true) . ';');
file_put_contents("$tmp/private/backup-config.php", '<?php return [];');
$php = PHP_BINARY; $env = 'SWEEP_BACKUP_CONFIG=' . escapeshellarg("$tmp/cfg.php");
exec("$env $php -d memory_limit=24M " . escapeshellarg("$app/ops/backup.php") . ' 2>&1', $o1, $rc1);
$daily = glob("$tmp/backups/daily/sweep-db-*.enc") ?: [];
$ok($rc1 === 0 && count($daily) === 1, 'the backup of 30 MB runs with 24 MB of memory (' . $rc1 . ' ' . implode(' ', array_slice($o1, 0, 2)) . ')');
$f = $daily[0] ?? '';
$ok($f && file_get_contents($f, false, null, 0, 4) === 'SWB2', 'streamed format SWB2');
exec("$env $php " . escapeshellarg("$app/ops/restore-test.php") . ' 2>&1', $o2, $rc2);
$ok($rc2 === 0 && strpos(implode(' ', $o2), 'OK') !== false && strpos(implode(' ', $o2), '6000 documents') !== false, 'restore-test: OK, the same 6000 documents (' . implode(' ', array_slice($o2, 0, 3)) . ')');
exec("$env $php " . escapeshellarg("$app/ops/restore.php") . ' ' . escapeshellarg($f) . ' ' . escapeshellarg("$tmp/back.sqlite") . ' 2>&1', $o3, $rc3);
$b = new PDO('sqlite:' . "$tmp/back.sqlite"); $n = (int) $b->query('SELECT COUNT(*) FROM documents')->fetchColumn(); $u = $b->query("SELECT username FROM users WHERE id='u1'")->fetchColumn(); $b = null;
$ok($rc3 === 0 && $n === 6000 && $u === 'mateo', "restore.php: the same rows ($n documents, user $u)");
// a changed byte, a file cut short
$bad = "$tmp/bad.enc"; $raw = (string) file_get_contents($f); $raw[(int) (strlen($raw) / 2)] = chr(ord($raw[(int) (strlen($raw) / 2)]) ^ 1); file_put_contents($bad, $raw);
$e1 = null; try { ops_decrypt_file($bad, "$tmp/x.sqlite", 'test passphrase'); } catch (Throwable $e) { $e1 = $e->getMessage(); }
$ok($e1 !== null && strpos($e1, 'damaged') !== false, "one byte changed: refused ($e1)");
$cut = "$tmp/cut.enc"; file_put_contents($cut, substr((string) file_get_contents($f), 0, (int) (filesize($f) * 0.6)));
$e2 = null; try { ops_decrypt_file($cut, "$tmp/y.sqlite", 'test passphrase'); } catch (Throwable $e) { $e2 = $e->getMessage(); }
$ok($e2 !== null, "a file cut short: refused ($e2)");
$e3 = null; try { ops_decrypt_file($f, "$tmp/z.sqlite", 'wrong'); } catch (Throwable $e) { $e3 = $e->getMessage(); }
$ok($e3 !== null && strpos($e3, 'wrong passphrase') !== false, 'a wrong passphrase: refused');
// an older backup (one piece, SWB1)
$old = "$tmp/old.enc"; file_put_contents($old, ops_encrypt((string) gzencode('legacy content', 6), 'test passphrase'));
ops_decrypt_file($old, "$tmp/old.out", 'test passphrase');
$ok(file_get_contents("$tmp/old.out") === 'legacy content', 'an older backup (SWB1) still restores');
// the weekly archive
$w = glob("$tmp/backups/weekly/sweep-files-*.enc") ?: [];
$names = [];
if ($w) { ops_decrypt_file($w[0], "$tmp/files.tar", 'test passphrase'); foreach (new RecursiveIteratorIterator(new PharData("$tmp/files.tar")) as $x) $names[] = preg_replace('#^.*files\.tar/#', '', (string) $x->getPathname()); }
$ok(in_array('shot1', $names, true) && in_array('feedback/fb1.png', $names, true) && in_array('presets/presets-live.json', $names, true) && in_array('presets/presets-history/2026-10-01.json', $names, true),
    'the weekly archive: screenshots, private config, feedback screenshots, prop firm catalogue (' . implode(', ', $names) . ')');
// clean up
$rm = function (string $d) use (&$rm) { foreach (glob($d . '/{,.}[!.,!..]*', GLOB_BRACE) ?: [] as $x) is_dir($x) ? $rm($x) : @unlink($x); @rmdir($d); };
$rm($tmp);
echo "\n$pass passed, $fail failed\n";
exit($fail ? 1 : 0);
