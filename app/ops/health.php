<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli' && realpath((string) ($_SERVER['SCRIPT_FILENAME'] ?? '')) === realpath(__FILE__)) { http_response_code(404); exit; }
/**
 * Sweep — Admin › Health (brief 02 step 0): the scheduled tasks (ops/cron-lib.php) and whether each outside service is
 * set up. Only yes / no, amounts spent and limits: never a key, a password or any other value of the private folder.
 */
require_once __DIR__ . '/cron-lib.php';

function sweep_health(PDO $pdo, array $cfg, string $app): array
{
    $c = [];
    $sc = (array) ($cfg['smtp'] ?? []);
    $c['smtp'] = !empty($sc['host']) && !empty($sc['user']) && !empty($sc['pass']);   // else PHP mail(): more often in spam
    $c['app_url'] = trim((string) ($cfg['app_url'] ?? '')) !== '';
    try {   // Sweep AI: key, global daily budget, per-trader limit, spent today
        require_once $app . '/ai/ai-core.php';
        $a = sai_config();
        $c['ai'] = !empty($a['enabled']) && trim((string) ($a['api_key'] ?? '')) !== '';
        $c['ai_budget_usd'] = (float) $a['global_daily_budget_usd']; $c['ai_user_limit'] = (int) $a['user_daily_limit'];
        try { $c['ai_spent_usd'] = round(sai_spent_today($pdo), 2); } catch (Throwable $e) { $c['ai_spent_usd'] = 0.0; }   // no AI call yet
    } catch (Throwable $e) { $c['ai'] = false; }
    $c['billing'] = false; $c['webhook'] = false; $c['billing_live'] = false;
    try {
        if (function_exists('billing_on') && billing_on()) {
            $b = sb_config();
            $c['billing'] = trim((string) ($b['stripe_secret_key'] ?? '')) !== '';
            $c['webhook'] = trim((string) ($b['stripe_webhook_secret'] ?? '')) !== '';
            $c['billing_live'] = !empty($b['live']);
        }
    } catch (Throwable $e) { /* no billing config */ }
    $c['chart'] = class_exists('ChartData') && ChartData::enabled();
    $c['backup'] = false; $c['offsite'] = false;
    try {   // the backup settings (ops/backup.php): a passphrase, and an off-site copy if a bucket is set
        $bp = getenv('SWEEP_BACKUP_CONFIG') ?: dirname($app) . '/sweep-private/backup-config.php';
        $bc = is_readable($bp) ? (array) (require $bp) : [];
        $c['backup'] = trim((string) ($bc['passphrase'] ?? '')) !== '';
        $c['offsite'] = !empty(((array) ($bc['s3'] ?? []))['bucket']);
    } catch (Throwable $e) { /* unreadable */ }
    return ['now' => time(), 'tasks' => sweep_cron_status($pdo), 'config' => $c];
}
