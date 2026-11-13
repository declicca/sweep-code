<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli' && realpath((string) ($_SERVER['SCRIPT_FILENAME'] ?? '')) === realpath(__FILE__)) { http_response_code(404); exit; }
/**
 * Sweep — Admin › « To look at » (13 Nov., brief « Admin lisible sur téléphone », 2.1): only what asks for an action, one line each.
 * Every line reads what its own section of Admin already shows (nothing is measured twice):
 *   task     a scheduled task red or late (ops/cron-lib.php, the Health block)
 *   error    a JS error (by message) or a PHP error first seen in the last 7 days (client_errors; the tail of error_log)
 *   rules    firm rules read but not applied at the last check (« not confirmed by a second reading », presets/check.php), or no check for 8 days
 *   sync     traders (the team aside) with accounts found but none linked, or an add-on downloaded and never seen (sync_admin)
 *   signups  sign-ups started and not finished in the last 7 days (signup_leads)
 *   backup   no backup, or backups with no copy outside the server (the Health block)
 * Returns ['now' => ts, 'items' => [['k' => kind, 'n' => count, …]]]; no item = nothing to look at. A part that cannot be read
 * (a table that does not exist yet) is skipped, never an error.
 */
function sweep_watch(PDO $pdo, array $cfg, string $app, ?int $now = null, ?string $log = null): array
{
    $now = $now ?? time(); $d7 = $now - 7 * 86400; $items = [];
    $try = function (callable $f) { try { return $f(); } catch (Throwable $e) { return null; } };

    $health = $try(function () use ($pdo, $cfg, $app) { require_once __DIR__ . '/health.php'; return sweep_health($pdo, $cfg, $app); });
    if ($health) {
        $bad = array_values(array_filter((array) $health['tasks'], fn($t) => ($t['color'] ?? 'green') !== 'green'));
        if ($bad) $items[] = ['k' => 'task', 'n' => count($bad), 'red' => count(array_filter($bad, fn($t) => $t['color'] === 'red')), 'tasks' => array_slice(array_column($bad, 'task'), 0, 3)];
    }

    $js = (int) ($try(fn() => count($pdo->query('SELECT msg FROM client_errors GROUP BY msg HAVING MIN(created_at) > ' . (int) $d7)->fetchAll())) ?? 0);
    $php = 0; $log = $log ?? $app . '/error_log';   // (the tests give a log of their own)
    if (is_file($log) && filesize($log) < 50 * 1048576 && ($fh = @fopen($log, 'r'))) {   // as the dashboard reads it: its last 2 MB
        fseek($fh, max(0, filesize($log) - 2 * 1048576)); $old = []; $new = [];
        while (($line = fgets($fh)) !== false) {
            if (!preg_match('/^\[(\d{2}-[A-Za-z]{3}-\d{4} [\d:]+)[^\]]*\] (.*)$/', rtrim($line), $m)) continue;
            $ts = strtotime($m[1] . ' UTC') ?: 0; $msg = substr(preg_replace('/\d+/', '#', $m[2]) ?? '', 0, 160);
            if ($ts > $d7) $new[$msg] = true; else $old[$msg] = true;
        }
        fclose($fh); $php = count(array_diff_key($new, $old));
    }
    if ($js + $php) $items[] = ['k' => 'error', 'n' => $js + $php, 'js' => $js, 'php' => $php];

    $pr = $try(function () { require_once dirname(__DIR__) . '/presets/check.php'; return pr_admin_summary(); });
    if ($pr) {
        $held = array_values(array_filter((array) $pr['firms'], fn($f) => (bool) array_filter((array) ($f['errors'] ?? []), fn($e) => strpos((string) $e, 'not applied') === 0)));
        if ($held || !empty($pr['stale'])) $items[] = ['k' => 'rules', 'n' => count($held), 'firms' => array_slice(array_column($held, 'name'), 0, 4), 'stale' => !empty($pr['stale']), 'days' => $pr['days_since'] ?? null];
    }

    $sy = $try(function () use ($pdo, $now) { require_once dirname(__DIR__) . '/sync/sync-store.php'; return sync_admin($pdo, $now); });
    if ($sy) {
        $who = ['to_link' => [], 'downloaded' => []];
        foreach ((array) $sy['rows'] as $r) if (empty($r['team']) && isset($who[$r['state']])) $who[$r['state']][$r['user_id']] = true;
        if ($who['to_link'] || $who['downloaded']) $items[] = ['k' => 'sync', 'n' => count($who['to_link'] + $who['downloaded']), 'to_link' => count($who['to_link']), 'downloaded' => count($who['downloaded'])];
    }

    $leads = (int) ($try(fn() => $pdo->query('SELECT COUNT(*) FROM signup_leads WHERE completed_at IS NULL AND created_at > ' . (int) $d7)->fetchColumn()) ?? 0);
    if ($leads) $items[] = ['k' => 'signups', 'n' => $leads];

    if ($health && (empty($health['config']['backup']) || empty($health['config']['offsite']))) $items[] = ['k' => 'backup', 'n' => 1, 'none' => empty($health['config']['backup'])];

    return ['now' => $now, 'items' => $items];
}
