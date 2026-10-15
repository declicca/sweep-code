<?php
declare(strict_types=1);
/**
 * Sweep — weekly check of the prop firm presets.
 *
 * The work itself is in presets/check.php (shared with Admin → Presets → « Check now »): limits, payout rules and prices
 * read on each firm's own pages, validated, doubtful changes kept « to review », the rest applied, and every trader with
 * an active account at a firm that changed gets a notification. Accounts keep their rules until the trader applies the new ones.
 *
 * cPanel → Cron Jobs → once a week (Monday 05:00):
 *   0 5 * * 1  /usr/local/bin/php /home/matnsabc/app.makeitsweep.com/presets/cron.php >/dev/null 2>&1
 *
 *   php presets/cron.php                 check every firm and apply
 *   php presets/cron.php --dry-run       check and show the changes, apply nothing
 *   php presets/cron.php --firm=lucid    one firm only
 *   php presets/cron.php --rollback      restore the previous version
 */
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }

$root = dirname(__DIR__);
$cfg = require $root . '/config.php';
$DATA = rtrim((string) ($cfg['data_dir'] ?? ($root . '/data')), '/');
$c = $cfg['db'] ?? [];
$opts = [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC];
$pdo = ($c['driver'] ?? 'sqlite') === 'mysql'
    ? new PDO('mysql:host=' . $c['host'] . ';dbname=' . $c['name'] . ';charset=utf8mb4', (string) $c['user'], (string) $c['password'], $opts)
    : new PDO('sqlite:' . $DATA . '/journal.db', null, null, $opts);
if (!function_exists('db')) { function db(): PDO { global $pdo; return $pdo; } }   // notifications use db()
require_once $root . '/presets/check.php';
require_once $root . '/ai/ai-core.php';

$args = array_slice($argv, 1);
$dry = in_array('--dry-run', $args, true);
$only = null; foreach ($args as $a) if (strpos($a, '--firm=') === 0) $only = substr($a, 7);

if (!$dry && !$only && !in_array('--rollback', $args, true)) { require_once $root . '/ops/cron-lib.php'; sweep_cron_start($pdo, 'presets'); }   // Admin › Health (brief 02 step 0)
if (in_array('--rollback', $args, true)) {
    $f = pr_rollback();
    echo $f ? "Restored the version saved as $f\n" : "No previous version to restore\n";
    exit($f ? 0 : 1);
}

$report = pr_run_all($pdo, $dry, $only, 'cron');
if (!$dry && !$only && function_exists('sweep_cron_note')) sweep_cron_note(count($report) . ' firm(s) checked');   // Admin › Health
if (!$dry && !$only && function_exists('sweep_cron_fail') && ($why = pr_run_problem(count($report)))) sweep_cron_fail($why);   // every firm failed: red, not blue
echo ($dry ? "[dry run] " : '') . "Prop firm presets — " . gmdate('Y-m-d H:i') . " UTC\n" . implode("\n", $report) . "\n";
