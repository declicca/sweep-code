<?php
declare(strict_types=1);
/**
 * Sweep — chart preload (cPanel cron, every hour). Downloads, once for everybody, the session days of the trades of the
 * last 30 days that are old enough (chart_data_min_age_hours) and not cached yet; on the first runs it also catches up
 * older history, in batches, always inside the daily budget.
 *
 *   /usr/local/bin/php /home/matnsabc/app.makeitsweep.com/chart/cron.php >/dev/null 2>&1
 */
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
$root = dirname(__DIR__);
$cfg = require $root . '/config.php';
if (!empty($cfg['chart_config']) && !defined('SWEEP_CHART_CONFIG')) define('SWEEP_CHART_CONFIG', (string) $cfg['chart_config']);
$DATA = rtrim((string) ($cfg['data_dir'] ?? ($root . '/data')), '/');
$c = $cfg['db'] ?? [];
$opts = [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC];
$pdo = ($c['driver'] ?? 'sqlite') === 'mysql'
    ? new PDO('mysql:host=' . $c['host'] . ';dbname=' . $c['name'] . ';charset=utf8mb4', (string) $c['user'], (string) $c['password'], $opts)
    : new PDO('sqlite:' . $DATA . '/journal.db', null, null, $opts);
function db(): PDO { global $pdo; return $pdo; }
require_once __DIR__ . '/chart.php';
foreach (['/notify/notify.php', '/notify/listeners.php'] as $f) if (is_file($root . $f)) require_once $root . $f;   // « your chart is ready »

if (!ChartData::enabled()) { echo "Sweep chart: disabled or no Databento key\n"; exit; }
$perRun = 40;
$recent = gmdate('Y-m-d', time() - 30 * 86400);
$jobs = [];   // root|day|contract => [recent?, …]
foreach ($pdo->query("SELECT data FROM documents WHERE collection = 'trades'") as $r) {
    $t = json_decode((string) $r['data'], true);
    if (!is_array($t) || !empty($t['demo'])) continue;
    $inst = ChartData::instrument((string) ($t['contract'] ?? '') ?: (string) ($t['instrument'] ?? 'NQ'));
    $span = ChartData::tradeSpan($t);
    if (!$inst || !$span) continue;
    $day = ChartData::sessionDay($span[0]);
    $key = $inst[0] . '|' . $day . '|' . ($inst[1] ?? '');
    $jobs[$key] = $day >= $recent ? 1 : 0;
}
arsort($jobs);   // the last 30 days first, then the older history (catch-up)
$done = 0; $skipped = 0;
foreach ($jobs as $key => $isRecent) {
    if ($done >= $perRun) break;
    [$root, $day, $con] = explode('|', $key);
    if (ChartData::cached($root, $day, $con ?: null)) { $skipped++; continue; }
    if (time() < ChartData::availableAt($day)) continue;
    $r = ChartData::day($root, $day, $con ?: null);
    if ($r['status'] === 'soon') { echo "Sweep chart: daily budget reached, stopping\n"; break; }
    if ($r['status'] === 'ok') $done++;
}
echo date('c') . " Sweep chart: $done day(s) downloaded, $skipped already cached, " . count($jobs) . " total\n";

// « Your NQ chart is ready »: once per trader and session day, when the day's chart becomes available
// (within 48 h of it, never during market hours: a later run sends it after 4 pm ET).
if (class_exists('Notify', false)) {
    $et = new DateTimeImmutable('now', new DateTimeZone('America/New_York')); $hm = $et->format('H:i');
    if (!($hm >= '09:30' && $hm < '16:00' && (int) $et->format('N') <= 5)) {
        $sent = 0; $seen = [];
        foreach ($pdo->query("SELECT user_id, data FROM documents WHERE collection = 'trades'") as $r) {
            $t = json_decode((string) $r['data'], true);
            if (!is_array($t) || !empty($t['demo'])) continue;
            $inst = ChartData::instrument((string) ($t['contract'] ?? '') ?: (string) ($t['instrument'] ?? 'NQ'));
            $span = ChartData::tradeSpan($t);
            if (!$inst || !$span) continue;
            $day = ChartData::sessionDay($span[0]); $at = ChartData::availableAt($day);
            $k = $r['user_id'] . '|' . $day;
            if (isset($seen[$k]) || time() < $at || time() - $at > 48 * 3600 || !ChartData::cached($inst[0], $day, $inst[1] ?? null)) continue;
            $seen[$k] = 1;
            if (Notify::send((string) $r['user_id'], 'chart_ready', ['inst' => (string) ($t['instrument'] ?? $inst[0])], ['dedupe_key' => "chart:{$r['user_id']}:$day", 'action_url' => '#trade/' . $t['id']])) $sent++;
        }
        if ($sent) echo date('c') . " Sweep chart: $sent « chart ready » notification(s)\n";
    }
}
