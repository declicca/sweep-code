<?php
declare(strict_types=1);
/**
 * Sweep — copy the live database to the staging site (e.g. trade.agencedeclic.ca), anonymised.
 *   php ops/staging-copy.php /home/matnsabc/trade.agencedeclic.ca/data/journal.db
 * Hot copy (VACUUM INTO), then: e-mails replaced, passwords of non-admin traders replaced by a random hash (admins keep
 * theirs so you can sign in), recovery codes, sessions, Stripe ids and Discord links removed. Screenshots are not copied.
 * Refuses to write over the live database.
 */
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
require __DIR__ . '/ops-lib.php';
$cfg = ops_cfg();
$to = $argv[1] ?? '';
if ($to === '') { echo "usage: php ops/staging-copy.php <staging journal.db>\n"; exit(1); }
if (realpath(dirname($to)) && realpath($cfg['db']) === realpath($to)) { echo "refused: this is the live database\n"; exit(1); }
$tmp = $to . '.tmp';
@unlink($tmp);
$live = new PDO('sqlite:' . $cfg['db'], null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
$live->exec('PRAGMA busy_timeout = 15000');
$live->exec('VACUUM INTO ' . $live->quote($tmp));
$live = null;
$s = new PDO('sqlite:' . $tmp, null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
$has = fn(string $t) => (bool) $s->query("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = " . $s->quote($t))->fetchColumn();
$s->exec("UPDATE users SET email = 'user-' || id || '@example.invalid', email_lc = 'user-' || id || '@example.invalid', recovery_hash = NULL");
$h = $s->prepare('UPDATE users SET password_hash = ? WHERE id = ? AND is_admin = 0');
foreach ($s->query('SELECT id FROM users WHERE is_admin = 0')->fetchAll(PDO::FETCH_COLUMN) as $id) $h->execute([password_hash(bin2hex(random_bytes(16)), PASSWORD_DEFAULT), $id]);
foreach (['sessions', 'attempts', 'notifications', 'discord_queue', 'client_errors'] as $t) if ($has($t)) $s->exec("DELETE FROM $t");
if ($has('billing_users')) $s->exec('UPDATE billing_users SET stripe_customer = NULL, email = NULL');
if ($has('social_profile')) { try { $s->exec('UPDATE social_profile SET discord_user_id = NULL, discord_name = NULL'); } catch (Throwable $e) { /* no Discord columns */ } }
$n = (int) $s->query('SELECT COUNT(*) FROM users')->fetchColumn();
$s = null;
foreach (['', '-wal', '-shm'] as $x) @unlink($to . $x);
rename($tmp, $to);
echo "staging database ready: $to ($n users, anonymised)\n";
