<?php
declare(strict_types=1);
/**
 * Sweep — what the trade charts cost and cover (brief 02 part 8), read only, on the server:
 *   /usr/local/bin/php /home/matnsabc/app.makeitsweep.com/ops/chart-check.php
 * The cost: Databento's own price of each download, as chart/chart.php logged it before running it (chart_fetch_log,
 * metadata.get_cost), by month, with the requests the daily budget stopped. The coverage: the real trades of the last 30
 * days (example data aside) whose chart exists, those not yet old enough (24 h), not downloaded yet, or on an instrument
 * without a chart. The cost per active trader (a trade in the last 30 days). Never prints a key.
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
require_once $root . '/chart/chart.php';
ChartData::schema();
$cc = ChartData::cfg();
printf("Charts: %s · daily budget $%.2f · data after %d h\n\n", ChartData::enabled() ? 'on (Databento key set)' : 'OFF (no Databento key)', (float) $cc['chart_daily_budget_usd'], (int) $cc['chart_data_min_age_hours']);

// 1. the cost, month by month (Databento's price of each download)
echo "Cost by month (Databento's price, before each download):\n";
$rows = $pdo->query("SELECT substr(created_at, 1, 7) AS m, status, COUNT(*) AS n, COALESCE(SUM(cost_usd), 0) AS usd, COALESCE(SUM(bytes), 0) AS b FROM chart_fetch_log GROUP BY substr(created_at, 1, 7), status ORDER BY m")->fetchAll();
if (!$rows) echo "  no download yet\n";
$byM = [];
foreach ($rows as $r) $byM[$r['m']][$r['status']] = $r;
foreach ($byM as $m => $st) {
    $ok = $st['ok'] ?? ['n' => 0, 'usd' => 0, 'b' => 0];
    printf("  %s  $%8.4f  %4d download(s)  %6.1f MB%s%s\n", $m, (float) $ok['usd'], (int) $ok['n'], (int) $ok['b'] / 1048576,
        isset($st['budget']) ? '  · ' . $st['budget']['n'] . ' stopped by the daily budget' : '', isset($st['error']) ? '  · ' . $st['error']['n'] . ' errors' : '');
}
$t30 = gmdate('Y-m-d H:i:s', time() - 30 * 86400);
$spent30 = (float) $pdo->query("SELECT COALESCE(SUM(cost_usd), 0) FROM chart_fetch_log WHERE status = 'ok' AND created_at >= '$t30'")->fetchColumn();

// 2. the coverage: the real trades of the last 30 days
$recent = gmdate('Y-m-d', time() - 30 * 86400);
$n = 0; $covered = 0; $young = 0; $missing = 0; $noInst = []; $noTime = 0; $users = [];
foreach ($pdo->query("SELECT user_id, data FROM documents WHERE collection = 'trades'") as $r) {
    $t = json_decode((string) $r['data'], true);
    if (!is_array($t) || !empty($t['demo']) || (string) ($t['date'] ?? '') < $recent) continue;
    $n++; $users[$r['user_id']] = true;
    $typed = (string) ($t['contract'] ?? '') ?: (string) ($t['instrument'] ?? 'NQ');
    $inst = ChartData::instrument($typed);
    if (!$inst) { $k = strtoupper($typed) ?: '?'; $noInst[$k] = ($noInst[$k] ?? 0) + 1; continue; }
    $span = ChartData::tradeSpan($t);
    if (!$span) { $noTime++; continue; }
    $day = ChartData::sessionDay($span[0]);
    if (ChartData::cached($inst[0], $day, $inst[1] ?? null)) $covered++;
    elseif (time() < ChartData::availableAt($day)) $young++;
    else $missing++;
}
$active = count($users);
echo "\nReal trades of the last 30 days: $n, by $active active trader(s)\n";
if ($n) {
    $line = fn(string $label, int $v, string $more = '') => printf("  %-30s %5d%s\n", $label, $v, $more);
    $line('with their chart:', $covered, '  (' . round($covered / $n * 100) . ' %)');
    $line('too recent (under ' . (int) $cc['chart_data_min_age_hours'] . ' h):', $young);
    printf("  %-30s %5d%s\n", 'not downloaded yet:', $missing, $missing ? '  (the hourly task catches up, 40 days a run, inside the budget)' : '');
    $line('no entry time:', $noTime);
    arsort($noInst);
    printf("  %-30s %5d%s\n", 'instrument without a chart:', array_sum($noInst), $noInst ? '  (' . implode(', ', array_map(fn($k, $v) => "$k $v", array_keys(array_slice($noInst, 0, 8, true)), array_slice($noInst, 0, 8, true))) . ')' : '');
}
printf("\nCost of the last 30 days: $%.2f · per active trader: %s\n", $spent30, $active ? '$' . number_format($spent30 / $active, 3) : '—');
$bars = (string) $cc['chart_cache_dir']; $size = 0; $files = 0;
if (is_dir($bars)) foreach (new RecursiveIteratorIterator(new RecursiveDirectoryIterator($bars, FilesystemIterator::SKIP_DOTS)) as $f) { $size += $f->getSize(); $files++; }
printf("Charts kept on the server: %d file(s), %.1f MB\n", $files, $size / 1048576);
