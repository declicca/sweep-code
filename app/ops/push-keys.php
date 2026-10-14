<?php
declare(strict_types=1);
/**
 * Sweep — the keys of the notifications on the phone (web push, brief 02 part 10), once, on the server:
 *   /usr/local/bin/php /home/matnsabc/app.makeitsweep.com/ops/push-keys.php
 * Makes a VAPID key pair and writes sweep-private/push-config.php (readable by this user only) if it does not exist yet.
 * Prints the public key only, never the private one. --force makes new keys: every phone must then turn notifications on again.
 */
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
$root = dirname(__DIR__);
require $root . '/push/web-push.php';
$dir = dirname($root) . '/sweep-private';
$file = $dir . '/push-config.php';
if (is_file($file) && !in_array('--force', $argv, true)) {
    fwrite(STDERR, "$file already exists: nothing changed (--force makes new keys; every phone must then turn notifications on again).\n");
    exit(1);
}
if (!is_dir($dir) && !mkdir($dir, 0700, true)) { fwrite(STDERR, "Cannot create $dir\n"); exit(1); }
$k = wp_new_keys();
$tmp = $file . '.' . bin2hex(random_bytes(4));
$old = umask(0077);
$okw = file_put_contents($tmp, "<?php\n// Sweep — web push keys (VAPID), made by ops/push-keys.php on " . gmdate('Y-m-d') . ". Never in git, never by hand.\nreturn " . var_export($k, true) . ";\n");
umask($old);
if ($okw === false || !chmod($tmp, 0600) || !rename($tmp, $file)) { @unlink($tmp); fwrite(STDERR, "Cannot write $file\n"); exit(1); }
echo "Written: $file (readable by this user only)\nPublic key: {$k['public_key']}\n";
