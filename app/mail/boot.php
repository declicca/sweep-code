<?php
declare(strict_types=1);
/** Sweep — the database for the email scripts run by cron or by the mail server (send-cron.php, bounce.php). */
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
$root = dirname(__DIR__);
$cfg = require $root . '/config.php';
$DATA = rtrim((string) ($cfg['data_dir'] ?? ($root . '/data')), '/');
if (getenv('SWEEP_TEST_DB')) $DATA = dirname((string) getenv('SWEEP_TEST_DB'));
$c = $cfg['db'] ?? [];
$opts = [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC];
if (($c['driver'] ?? 'sqlite') === 'mysql') {
    $pdo = new PDO('mysql:host=' . $c['host'] . ';dbname=' . $c['name'] . ';charset=utf8mb4', (string) $c['user'], (string) $c['password'], $opts);
} else {
    $pdo = new PDO('sqlite:' . $DATA . '/journal.db', null, null, $opts);
    $pdo->exec('PRAGMA busy_timeout = 5000');
}
function db(): PDO { global $pdo; return $pdo; }
function billing_on(): bool {
    static $on = null; if ($on !== null) return $on;
    global $cfg, $root;
    if (!empty($cfg['billing_config']) && !defined('SWEEP_BILLING_CONFIG')) define('SWEEP_BILLING_CONFIG', (string) $cfg['billing_config']);
    if (!is_file($root . '/billing/billing-core.php')) return $on = false;
    require_once $root . '/billing/billing-core.php';
    try { sb_config(); return $on = true; } catch (Throwable $e) { return $on = false; }
}
require_once __DIR__ . '/mail-core.php';
require_once __DIR__ . '/mail-smtp.php';
