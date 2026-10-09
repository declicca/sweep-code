<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli' && realpath((string) ($_SERVER['SCRIPT_FILENAME'] ?? '')) === realpath(__FILE__)) { http_response_code(404); exit; }
/**
 * Sweep AI — stats engine.
 * All the math happens HERE, in PHP, for free. The AI only receives small summaries.
 * Reads the app's existing `documents` table (collections: trades, accounts, firms, journals, meta...).
 */

const SAI_INSTRUMENTS = [
    // symbol => [tick size, $ per point]
    'NQ' => [0.25, 20], 'MNQ' => [0.25, 2], 'ES' => [0.25, 50], 'MES' => [0.25, 5],
    'YM' => [1, 5], 'MYM' => [1, 0.5], 'RTY' => [0.1, 50], 'M2K' => [0.1, 5],
    'CL' => [0.01, 1000], 'MCL' => [0.01, 100], 'GC' => [0.1, 100], 'MGC' => [0.1, 10],
    '6E' => [0.00005, 125000], 'M6E' => [0.0001, 12500], 'ZN' => [0.015625, 1000], 'ZB' => [0.03125, 1000],
    'SI' => [0.005, 5000], 'SIL' => [0.005, 1000], 'NG' => [0.001, 10000], 'HG' => [0.0005, 25000], 'MBT' => [5, 0.1], 'MET' => [0.5, 0.1],
];

/* ---------------- loading ---------------- */

function sai_docs(PDO $pdo, string $uid, string $col): array
{
    $out = [];
    foreach (sai_q($pdo, 'SELECT id, data FROM documents WHERE user_id = ? AND collection = ?', [$uid, $col]) as $r) {
        $d = json_decode((string) $r['data'], true);
        if (!is_array($d)) continue;
        $d['id'] = $r['id'];
        $out[] = $d;
    }
    return $out;
}

function sai_doc(PDO $pdo, string $uid, string $col, string $id): ?array
{
    $v = sai_q($pdo, 'SELECT data FROM documents WHERE user_id = ? AND collection = ? AND id = ?', [$uid, $col, $id])->fetchColumn();
    if (!is_string($v)) return null;
    $d = json_decode($v, true);
    if (!is_array($d)) return null;
    $d['id'] = $id;
    return $d;
}

function sai_settings(PDO $pdo, string $uid): array
{
    return sai_doc($pdo, $uid, 'meta', 'settings') ?? [];
}

/** Active accounts (id, name, firm_id, firm name) — used to pre-fill drafts. */
function sai_accounts(PDO $pdo, string $uid): array
{
    $firms = [];
    foreach (sai_docs($pdo, $uid, 'firms') as $f) $firms[$f['id']] = (string) ($f['name'] ?? '');
    $out = [];
    foreach (sai_docs($pdo, $uid, 'accounts') as $a) {
        $status = (string) ($a['status'] ?? 'active');
        $out[] = [
            'id' => $a['id'], 'name' => (string) ($a['name'] ?? $a['id']), 'firm_id' => (string) ($a['firm_id'] ?? ''),
            'firm' => $firms[$a['firm_id'] ?? ''] ?? '', 'active' => $status === 'active', 'demo' => !empty($a['demo']),
        ];
    }
    usort($out, fn($a, $b) => [$b['active'], $a['name']] <=> [$a['active'], $b['name']]);
    return $out;
}

function sai_firms(PDO $pdo, string $uid): array
{
    return array_map(fn($f) => ['id' => $f['id'], 'name' => (string) ($f['name'] ?? '')], sai_docs($pdo, $uid, 'firms'));
}

/**
 * Normalized trades, sorted oldest → newest.
 * Trades copied across accounts (same copy_group) count once, with P&L/fees/contracts added up — same rule as the app.
 */
function sai_trades(PDO $pdo, string $uid): array
{
    $groups = [];
    foreach (sai_docs($pdo, $uid, 'trades') as $t) {
        $k = !empty($t['copy_group']) ? 'g:' . $t['copy_group'] : 'i:' . $t['id'];
        $n = sai_norm_trade($t);
        if (!isset($groups[$k])) { $groups[$k] = $n; continue; }
        foreach (['pnl_c', 'fees_c', 'net_c', 'contracts', 'risk_c'] as $f) $groups[$k][$f] = ($groups[$k][$f] ?? 0) + ($n[$f] ?? 0);
        $groups[$k]['accounts']++;
    }
    $list = array_values($groups);
    usort($list, fn($a, $b) => [$a['date'], $a['entry_time'] ?? ''] <=> [$b['date'], $b['entry_time'] ?? '']);
    return $list;
}

function sai_norm_trade(array $t): array
{
    $pnl = (int) round((float) ($t['pnl_c'] ?? 0));
    $fees = (int) round(abs((float) ($t['fees_c'] ?? 0)));
    $et = sai_min($t['entry_time'] ?? null);
    $xt = sai_min($t['exit_time'] ?? null);
    $hold = ($et !== null && $xt !== null) ? (($xt - $et + 1440) % 1440) : null;
    $date = (string) ($t['date'] ?? '');
    return [
        'id' => (string) $t['id'], 'date' => $date, 'weekday' => $date ? (int) date('N', strtotime($date)) : null,
        'instrument' => strtoupper((string) ($t['instrument'] ?? 'NQ')), 'direction' => (string) ($t['direction'] ?? ''),
        'contracts' => (int) ($t['contracts'] ?? 0), 'entry_time' => $t['entry_time'] ?? null, 'exit_time' => $t['exit_time'] ?? null,
        'hour' => $et !== null ? intdiv($et, 60) : null, 'hold_min' => $hold,
        'session' => (string) ($t['session'] ?? ''), 'setup' => (string) ($t['setup'] ?? ''), 'grade' => (string) ($t['grade'] ?? ''),
        'tags' => array_values(array_filter(array_map('strval', (array) ($t['tags'] ?? [])))), 'account_id' => (string) ($t['account_id'] ?? ''),
        'pnl_c' => $pnl, 'fees_c' => $fees, 'net_c' => $pnl - $fees, 'risk_c' => isset($t['risk_c']) ? (int) $t['risk_c'] : null,
        'r_mult' => isset($t['r_mult']) && is_numeric($t['r_mult']) ? (float) $t['r_mult'] : null, 'demo' => !empty($t['demo']), 'accounts' => 1,
    ];
}

function sai_min($hhmm): ?int
{
    if (!is_string($hhmm) || !preg_match('/^(\d{1,2}):(\d{2})/', $hhmm, $m)) return null;
    return ((int) $m[1]) * 60 + (int) $m[2];
}

/* ---------------- metrics ---------------- */

function sai_metrics(array $trades): array
{
    $n = count($trades);
    $wins = $losses = 0; $gw = $gl = $net = $fees = 0; $big = $worst = 0; $rs = []; $hw = $hl = [];
    $days = [];
    foreach ($trades as $t) {
        $v = $t['net_c']; $net += $v; $fees += $t['fees_c']; $days[$t['date']] = ($days[$t['date']] ?? 0) + $v;
        if ($v > 0) { $wins++; $gw += $v; $big = max($big, $v); if ($t['hold_min'] !== null) $hw[] = $t['hold_min']; }
        elseif ($v < 0) { $losses++; $gl += -$v; $worst = min($worst, $v); if ($t['hold_min'] !== null) $hl[] = $t['hold_min']; }
        if ($t['r_mult'] !== null) $rs[] = $t['r_mult'];
    }
    $greenDays = count(array_filter($days, fn($x) => $x > 0));
    return [
        'trades' => $n, 'wins' => $wins, 'losses' => $losses,
        'win_rate' => $n ? round($wins / $n, 4) : null,
        'net_c' => $net, 'fees_c' => $fees,
        'profit_factor' => $gl > 0 ? round($gw / $gl, 2) : ($gw > 0 ? null : 0),
        'avg_win_c' => $wins ? (int) round($gw / $wins) : null,
        'avg_loss_c' => $losses ? (int) round(-$gl / $losses) : null,
        'expectancy_c' => $n ? (int) round($net / $n) : null,
        'avg_r' => $rs ? round(array_sum($rs) / count($rs), 2) : null,
        'largest_win_c' => $big ?: null, 'largest_loss_c' => $worst ?: null,
        'avg_hold_win_min' => $hw ? (int) round(array_sum($hw) / count($hw)) : null,
        'avg_hold_loss_min' => $hl ? (int) round(array_sum($hl) / count($hl)) : null,
        'days' => count($days), 'green_days' => $greenDays,
    ];
}

/* ---------------- query engine (used by "Ask your journal") ---------------- */

const SAI_METRICS = ['net_pnl', 'win_rate', 'trade_count', 'avg_win', 'avg_loss', 'profit_factor', 'expectancy', 'avg_r',
    'largest_win', 'largest_loss', 'fees', 'avg_hold_winners', 'avg_hold_losers', 'green_days'];
const SAI_GROUPS = ['none', 'weekday', 'session', 'setup', 'hour', 'month', 'instrument', 'direction', 'account', 'grade', 'tag'];

function sai_filter(array $trades, array $f, array $accounts = []): array
{
    $acc = null;
    if (!empty($f['account'])) {
        $needle = mb_strtolower((string) $f['account']);
        foreach ($accounts as $a) if (mb_strtolower($a['name']) === $needle || $a['id'] === $f['account'] || ($a['firm'] && mb_strtolower($a['firm']) === $needle)) $acc[] = $a['id'];
        $acc = $acc ?? ['__none__'];
    }
    $wd = array_map('intval', (array) ($f['weekdays'] ?? []));
    $hf = sai_min($f['time_from'] ?? null); $ht = sai_min($f['time_to'] ?? null);
    $out = [];
    foreach ($trades as $t) {
        if (!empty($f['date_from']) && $t['date'] < $f['date_from']) continue;
        if (!empty($f['date_to']) && $t['date'] > $f['date_to']) continue;
        if (!empty($f['instrument']) && $t['instrument'] !== strtoupper((string) $f['instrument'])) continue;
        if (!empty($f['direction']) && $t['direction'] !== $f['direction']) continue;
        if (!empty($f['session']) && mb_strtolower($t['session']) !== mb_strtolower((string) $f['session'])) continue;
        if (!empty($f['setup']) && mb_strtolower($t['setup']) !== mb_strtolower((string) $f['setup'])) continue;
        if (!empty($f['grade']) && strtoupper($t['grade']) !== strtoupper((string) $f['grade'])) continue;
        if (!empty($f['tag']) && !in_array(mb_strtolower((string) $f['tag']), array_map('mb_strtolower', $t['tags']), true)) continue;
        if ($wd && !in_array($t['weekday'], $wd, true)) continue;
        if ($hf !== null || $ht !== null) {
            $m = sai_min($t['entry_time']);
            if ($m === null || ($hf !== null && $m < $hf) || ($ht !== null && $m > $ht)) continue;
        }
        if (!empty($f['outcome'])) {
            if ($f['outcome'] === 'win' && $t['net_c'] <= 0) continue;
            if ($f['outcome'] === 'loss' && $t['net_c'] >= 0) continue;
        }
        if ($acc !== null && !in_array($t['account_id'], $acc, true)) continue;
        if (empty($f['include_demo']) && $t['demo']) continue;
        $out[] = $t;
    }
    return $out;
}

/** Value of one metric for a list of trades: [raw value, kind] where kind is money|pct|num|min|ratio. */
function sai_metric_value(string $metric, array $m): array
{
    return match ($metric) {
        'net_pnl' => [$m['net_c'], 'money'],
        'win_rate' => [$m['win_rate'], 'pct'],
        'trade_count' => [$m['trades'], 'num'],
        'avg_win' => [$m['avg_win_c'], 'money'],
        'avg_loss' => [$m['avg_loss_c'], 'money'],
        'profit_factor' => [$m['profit_factor'], 'ratio'],
        'expectancy' => [$m['expectancy_c'], 'money'],
        'avg_r' => [$m['avg_r'], 'r'],
        'largest_win' => [$m['largest_win_c'], 'money'],
        'largest_loss' => [$m['largest_loss_c'], 'money'],
        'fees' => [$m['fees_c'], 'money'],
        'avg_hold_winners' => [$m['avg_hold_win_min'], 'min'],
        'avg_hold_losers' => [$m['avg_hold_loss_min'], 'min'],
        'green_days' => [$m['green_days'], 'num'],
        default => [null, 'num'],
    };
}

function sai_group_key(array $t, string $by, array $accNames): array
{
    return match ($by) {
        'weekday' => [[(string) $t['weekday']], fn($k) => $k],
        'session' => [[$t['session'] ?: '—'], fn($k) => $k],
        'setup' => [[$t['setup'] ?: '—'], fn($k) => $k],
        'hour' => [[$t['hour'] === null ? '—' : sprintf('%02d:00', $t['hour'])], fn($k) => $k],
        'month' => [[substr($t['date'], 0, 7)], fn($k) => $k],
        'instrument' => [[$t['instrument']], fn($k) => $k],
        'direction' => [[$t['direction'] ?: '—'], fn($k) => $k],
        'account' => [[$t['account_id']], fn($k) => $accNames[$k] ?? $k],
        'grade' => [[$t['grade'] ?: '—'], fn($k) => $k],
        'tag' => [$t['tags'] ?: ['—'], fn($k) => $k],
        default => [['all'], fn($k) => $k],
    };
}

function sai_grouped(array $trades, string $by, string $metric, array $accounts = []): array
{
    $accNames = [];
    foreach ($accounts as $a) $accNames[$a['id']] = $a['name'];
    $buckets = []; $label = null;
    foreach ($trades as $t) {
        [$keys, $label] = sai_group_key($t, $by, $accNames);
        foreach ($keys as $k) $buckets[$k][] = $t;
    }
    $rows = [];
    foreach ($buckets as $k => $list) {
        $m = sai_metrics($list);
        [$v, $kind] = sai_metric_value($metric, $m);
        $rows[] = ['key' => (string) $k, 'label' => $label ? $label((string) $k) : (string) $k, 'value' => $v, 'kind' => $kind,
            'trades' => $m['trades'], 'net_c' => $m['net_c'], 'win_rate' => $m['win_rate']];
    }
    if (in_array($by, ['weekday', 'hour', 'month'], true)) usort($rows, fn($a, $b) => strcmp($a['key'], $b['key']));
    else usort($rows, fn($a, $b) => ($b['value'] ?? -INF) <=> ($a['value'] ?? -INF));
    return array_slice($rows, 0, 24);
}

/* ---------------- compact summaries sent to the AI ---------------- */

/** Small, numbers-only summary of a set of trades (money in dollars to save tokens and avoid confusion). */
function sai_brief(array $trades, bool $withBreakdowns = true): array
{
    $m = sai_metrics($trades);
    $d = fn($c) => $c === null ? null : round($c / 100, 2);
    $out = [
        'trades' => $m['trades'], 'win_rate_pct' => $m['win_rate'] === null ? null : round($m['win_rate'] * 100, 1),
        'net_usd' => $d($m['net_c']), 'fees_usd' => $d($m['fees_c']), 'profit_factor' => $m['profit_factor'],
        'avg_win_usd' => $d($m['avg_win_c']), 'avg_loss_usd' => $d($m['avg_loss_c']), 'expectancy_usd' => $d($m['expectancy_c']),
        'avg_r' => $m['avg_r'], 'avg_hold_win_min' => $m['avg_hold_win_min'], 'avg_hold_loss_min' => $m['avg_hold_loss_min'],
        'trading_days' => $m['days'], 'green_days' => $m['green_days'],
    ];
    if ($withBreakdowns && $trades) {
        foreach (['setup', 'session', 'weekday', 'hour'] as $by) {
            $rows = sai_grouped($trades, $by, 'net_pnl');
            $out['by_' . $by] = array_map(fn($r) => [$r['label'], $r['trades'], $d($r['net_c']), $r['win_rate'] === null ? null : round($r['win_rate'] * 100)], array_slice($rows, 0, 8));
        }
        $out['by_columns'] = ['label', 'trades', 'net_usd', 'win_rate_pct'];
        $out['behavior'] = sai_behavior($trades);
    }
    return $out;
}

/** Behavior facts the AI can't see from totals: revenge trades, overtrading, sizing after losses. */
function sai_behavior(array $trades): array
{
    $byDay = [];
    foreach ($trades as $t) $byDay[$t['date']][] = $t;
    $after = []; $sizeUp = 0; $sizeAfterLoss = 0; $counts = [];
    foreach ($byDay as $list) {
        $counts[] = count($list);
        for ($i = 1; $i < count($list); $i++) {
            $p = $list[$i - 1]; $c = $list[$i];
            if ($p['net_c'] < 0) {
                $sizeAfterLoss++;
                if ($c['contracts'] > $p['contracts']) $sizeUp++;
                $pe = sai_min($p['exit_time']) ?? sai_min($p['entry_time']); $ce = sai_min($c['entry_time']);
                if ($pe !== null && $ce !== null && $ce - $pe >= 0 && $ce - $pe <= 15) $after[] = $c;
            }
        }
    }
    sort($counts);
    $am = sai_metrics($after);
    return [
        'trades_within_15min_after_a_loss' => $am['trades'],
        'their_win_rate_pct' => $am['win_rate'] === null ? null : round($am['win_rate'] * 100, 1),
        'their_net_usd' => round($am['net_c'] / 100, 2),
        'size_increased_after_loss_pct' => $sizeAfterLoss ? round($sizeUp / $sizeAfterLoss * 100) : null,
        'max_trades_in_a_day' => $counts ? end($counts) : 0,
        'median_trades_per_day' => $counts ? $counts[intdiv(count($counts), 2)] : 0,
    ];
}

/** Trim a journal doc to what matters (plan + post-market), capped in size. */
function sai_journal_brief(?array $j): ?array
{
    if (!$j) return null;
    $keep = [];
    foreach (['pre', 'post'] as $part) {
        if (!is_array($j[$part] ?? null)) continue;
        foreach ($j[$part] as $k => $v) {
            if (is_array($v)) $v = implode(', ', array_map(fn($x) => is_scalar($x) ? (string) $x : '', $v));
            if (!is_scalar($v)) continue;
            $v = trim((string) $v);
            if ($v !== '') $keep[$part][$k] = mb_substr($v, 0, 300);
        }
    }
    return $keep ?: null;
}

function sai_journal_for(PDO $pdo, string $uid, string $date): ?array
{
    $j = sai_doc($pdo, $uid, 'journals', $date);
    if ($j) return $j;
    foreach (sai_docs($pdo, $uid, 'journals') as $d) if (($d['date'] ?? '') === $date) return $d;
    return null;
}

/** P&L in cents for a draft trade, from prices or from a stated result. */
function sai_pnl_c(array $t): ?int
{
    $spec = SAI_INSTRUMENTS[$t['instrument']] ?? SAI_INSTRUMENTS['NQ'];
    [$tick, $pv] = $spec;
    $q = max(1, (int) ($t['contracts'] ?? 1));
    if ($t['entry'] !== null && $t['exit'] !== null && in_array($t['direction'], ['long', 'short'], true)) {
        $pts = ($t['exit'] - $t['entry']) * ($t['direction'] === 'long' ? 1 : -1);
        return (int) round($pts * $pv * $q * 100);
    }
    $v = $t['_result_value'] ?? null; $u = $t['_result_unit'] ?? null;
    if ($v === null) return null;
    return match ($u) {
        'usd' => (int) round($v * 100),
        'points' => (int) round($v * $pv * $q * 100),
        'ticks' => (int) round($v * $tick * $pv * $q * 100),
        default => null,
    };
}
