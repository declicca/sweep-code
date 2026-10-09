<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli' && realpath((string) ($_SERVER['SCRIPT_FILENAME'] ?? '')) === realpath(__FILE__)) { http_response_code(404); exit; }
/**
 * Sweep — prop firm presets catalogue (firm → account type → size → evaluation / funded rules).
 *
 *  - presets/seed.json            the catalogue shipped with the app (starting point)
 *  - data/presets-live.json       the catalogue kept up to date by ops/presets-refresh.php (weekly cron); wins over the seed
 *  - data/presets-history/        every previous version (rollback: php ops/presets-refresh.php --rollback)
 *  - data/presets-status.json     what the last check did, firm by firm (shown in the admin dashboard)
 *
 * Amounts are in dollars. dd_type: eod = trailing at end of day, trade = trailing in real time (intraday), static.
 */

const PR_DD_TYPES = ['eod', 'trade', 'static'];

function pr_data_dir(): string
{
    global $DATA;
    if (!empty($DATA)) return rtrim((string) $DATA, '/');
    $cfgFile = dirname(__DIR__, 2) . '/sweep-private/config.php';
    $cfg = is_file($cfgFile) ? (array) (include $cfgFile) : (is_file(dirname(__DIR__) . '/config.php') ? (array) (include dirname(__DIR__) . '/config.php') : []);
    return rtrim((string) ($cfg['data_dir'] ?? (dirname(__DIR__) . '/data')), '/');
}
function pr_seed_path(): string { return __DIR__ . '/seed.json'; }
function pr_live_path(): string { return pr_data_dir() . '/presets-live.json'; }
function pr_status_path(): string { return pr_data_dir() . '/presets-status.json'; }
function pr_history_dir(): string { return pr_data_dir() . '/presets-history'; }

function pr_read(string $path): ?array
{
    if (!is_file($path)) return null;
    $d = json_decode((string) file_get_contents($path), true);
    return is_array($d) && isset($d['firms']) && is_array($d['firms']) ? $d : null;
}

/** The catalogue the app uses: the live (checked) version when valid and built on the shipped seed, else the seed.
 *  A new seed shipped in an update (corrections checked by hand) always wins over an older live file. */
function pr_current(): array
{
    $seed = pr_read(pr_seed_path()) ?? ['schema' => 1, 'version' => 'none', 'firms' => []];
    $live = pr_read(pr_live_path());
    if ($live && ($live['seed_version'] ?? null) === ($seed['version'] ?? null) && !pr_validate_catalogue($live)) return pr_with_payouts($live, $seed);
    return $seed;
}

/** payout rules come from the shipped catalogue when the weekly check has none for a program/size (it reads limits, not payouts) */
function pr_with_payouts(array $live, array $seed): array
{
    $idx = []; $liveIdx = []; $priceIdx = [];
    foreach ((array) ($seed['firms'] ?? []) as $f) foreach ((array) ($f['programs'] ?? []) as $p) foreach ((array) ($p['sizes'] ?? []) as $sz) if (!empty($sz['price'])) $priceIdx[$f['id'] . '|' . $p['id'] . '|' . $sz['size']] = $sz['price'];
    foreach ((array) ($seed['firms'] ?? []) as $f) foreach ((array) ($f['programs'] ?? []) as $p) foreach ((array) ($p['sizes'] ?? []) as $sz) if (!empty($sz['live'])) $liveIdx[$f['id'] . '|' . $p['id'] . '|' . $sz['size']] = $sz['live'];
    foreach ((array) ($seed['firms'] ?? []) as $f) foreach ((array) ($f['programs'] ?? []) as $p) foreach ((array) ($p['sizes'] ?? []) as $sz)
        if (!empty($sz['funded']['payout'])) $idx[$f['id'] . '|' . $p['id'] . '|' . $sz['size']] = [$sz['funded']['payout'], $sz['funded']['consistency'] ?? null, $sz['funded']['payout_live'] ?? null];
    foreach ($live['firms'] as &$f) foreach ($f['programs'] as &$p) foreach ($p['sizes'] as &$sz) {
        $k = ($f['id'] ?? '') . '|' . ($p['id'] ?? '') . '|' . ($sz['size'] ?? '');
        if (isset($idx[$k]) && empty($sz['funded']['payout'])) { $sz['funded']['payout'] = $idx[$k][0]; if (!isset($sz['funded']['consistency']) && $idx[$k][1] !== null) $sz['funded']['consistency'] = $idx[$k][1]; }
        if (isset($idx[$k]) && $idx[$k][2] && empty($sz['funded']['payout_live'])) $sz['funded']['payout_live'] = $idx[$k][2];
        if (!empty($liveIdx[$k]) && empty($sz['live'])) $sz['live'] = $liveIdx[$k];
        if (!empty($priceIdx[$k]) && empty($sz['price'])) $sz['price'] = $priceIdx[$k];   // the catalogue's prices survive the weekly check
    }
    return $live;
}

function pr_status(): array
{
    $s = is_file(pr_status_path()) ? json_decode((string) file_get_contents(pr_status_path()), true) : null;
    return is_array($s) ? $s : ['last_run' => null, 'firms' => []];
}

/* ───────────── validation: impossible numbers never reach a trader ───────────── */

/** Errors for one phase of one size (empty = fine). */
function pr_check_phase(array $p, int $size, string $phase): array
{
    $e = [];
    $pct = fn($v) => $v / max(1, $size) * 100;
    $dd = $p['dd'] ?? null;
    if (!is_numeric($dd) || $dd <= 0) $e[] = "$phase: max loss missing";
    elseif ($pct($dd) < 0.8 || $pct($dd) > 10) $e[] = "$phase: max loss {$dd} is " . round($pct($dd), 1) . '% of the account (expected 0.8–10%)';
    if (!in_array($p['dd_type'] ?? '', PR_DD_TYPES, true)) $e[] = "$phase: drawdown type must be eod, trade or static";
    if ($phase === 'eval') {
        $t = $p['target'] ?? null;
        if (!is_numeric($t) || $t <= 0) $e[] = 'eval: profit target missing';
        elseif ($pct($t) < 2 || $pct($t) > 15) $e[] = "eval: profit target {$t} is " . round($pct($t), 1) . '% of the account (expected 2–15%)';
    }
    if (isset($p['dll'])) { if (!is_numeric($p['dll']) || $p['dll'] <= 0 || (is_numeric($dd) && $p['dll'] > $dd)) $e[] = "$phase: daily loss limit must be positive and not above the max loss"; }
    if (isset($p['consistency']) && (!is_numeric($p['consistency']) || $p['consistency'] < 10 || $p['consistency'] > 80)) $e[] = "$phase: consistency must be 10–80%";
    if (isset($p['min_days']) && (!is_numeric($p['min_days']) || $p['min_days'] < 0 || $p['min_days'] > 30)) $e[] = "$phase: minimum days must be 0–30";
    if (isset($p['max_minis']) && (!is_numeric($p['max_minis']) || $p['max_minis'] < 1 || $p['max_minis'] > 60)) $e[] = "$phase: max contracts must be 1–60";
    if (isset($p['payout'])) {
        $po = (array) $p['payout'];
        if (isset($po['win_days']) && (!is_numeric($po['win_days']) || $po['win_days'] < 0 || $po['win_days'] > 30)) $e[] = "$phase: payout winning days must be 0–30";
        if (isset($po['win_min']) && (!is_numeric($po['win_min']) || $po['win_min'] < 0 || $po['win_min'] > $size * 0.05)) $e[] = "$phase: payout minimum day profit looks wrong";
        if (isset($po['min_bal']) && (!is_numeric($po['min_bal']) || $po['min_bal'] < $size || $po['min_bal'] > $size * 1.2)) $e[] = "$phase: payout minimum balance must be between the size and +20%";
        foreach (['min', 'max', 'max_dll', 'cycle_min'] as $k) if (isset($po[$k]) && (!is_numeric($po[$k]) || $po[$k] < 0 || $po[$k] > $size)) $e[] = "$phase: payout $k looks wrong";
        if (isset($po['max_pct']) && (!is_numeric($po['max_pct']) || $po['max_pct'] <= 0 || $po['max_pct'] > 100)) $e[] = "$phase: payout max % must be 1–100";
        if (isset($p['dd_lock_offset']) && (!is_numeric($p['dd_lock_offset']) || $p['dd_lock_offset'] < 0 || $p['dd_lock_offset'] > 1000)) $e[] = "$phase: drawdown lock offset looks wrong";
        if (isset($po['split_pct']) && (!is_numeric($po['split_pct']) || $po['split_pct'] <= 0 || $po['split_pct'] > 100)) $e[] = "$phase: payout split must be 1–100 %";
        if (isset($po['trade_days']) && (!is_numeric($po['trade_days']) || $po['trade_days'] < 0 || $po['trade_days'] > 30)) $e[] = "$phase: payout trading days must be 0–30";
        if (isset($po['max_payouts']) && (!is_numeric($po['max_payouts']) || $po['max_payouts'] < 1 || $po['max_payouts'] > 50)) $e[] = "$phase: max number of payouts must be 1–50";
        if (isset($po['ladder'])) { if (!is_array($po['ladder']) || count($po['ladder']) > 20) $e[] = "$phase: payout ladder looks wrong"; else foreach ($po['ladder'] as $v) if ($v !== null && (!is_numeric($v) || $v <= 0 || $v > $size)) { $e[] = "$phase: payout ladder step looks wrong"; break; } }
    }
    return $e;
}

function pr_validate_firm(array $f): array
{
    $e = [];
    if (empty($f['id']) || empty($f['name'])) $e[] = 'firm id/name missing';
    foreach ((array) ($f['programs'] ?? []) as $pi => $p) {
        $label = ($p['name'] ?? "program $pi");
        if (empty($p['id']) || empty($p['name'])) $e[] = "$label: id/name missing";
        if (empty($p['sizes']) || !is_array($p['sizes'])) { $e[] = "$label: no sizes"; continue; }
        $seen = [];
        foreach ($p['sizes'] as $s) {
            $size = (int) ($s['size'] ?? 0);
            if ($size < 5000 || $size > 500000) { $e[] = "$label: size {$size} out of range"; continue; }
            if (isset($seen[$size])) $e[] = "$label: size {$size} listed twice"; $seen[$size] = 1;
            if (empty($s['eval']) && empty($s['funded'])) { $e[] = "$label {$size}: no rules"; continue; }
            if (!empty($s['eval'])) foreach (pr_check_phase((array) $s['eval'], $size, 'eval') as $x) $e[] = "$label {$size} $x";
            if (!empty($s['funded'])) foreach (pr_check_phase((array) $s['funded'], $size, 'funded') as $x) $e[] = "$label {$size} $x";
            foreach ((array) ($s['variants'] ?? []) as $vid => $v) foreach (['eval', 'funded'] as $ph) if (!empty($v[$ph]) && !empty($s[$ph]))
                foreach (pr_check_phase(pr_merge_phase((array) $s[$ph], (array) $v[$ph]), $size, $ph) as $x) $e[] = "$label {$size} ($vid) $x";
            if (!empty($s['price'])) foreach (pr_check_price((array) $s['price'], $size) as $x) $e[] = "$label {$size} $x";
        }
    }
    return $e;
}

function pr_validate_catalogue(array $c): array
{
    $e = [];
    foreach ((array) ($c['firms'] ?? []) as $f) foreach (pr_validate_firm((array) $f) as $x) $e[] = ($f['name'] ?? '?') . ': ' . $x;
    return $e;
}

/** A firm's fee: evaluation (per month or once) and activation, in dollars. */
function pr_check_price(array $p, int $size): array
{
    $e = [];
    foreach (['eval', 'activation'] as $k) if (isset($p[$k]) && (!is_numeric($p[$k]) || $p[$k] < 0 || $p[$k] > max(3000, $size * 0.03))) $e[] = "price: $k {$p[$k]} looks wrong";
    if (isset($p['eval_period']) && !in_array($p['eval_period'], ['month', 'once'], true)) $e[] = 'price: period must be month or once';
    return $e;
}

/** A variant (an option chosen at purchase, e.g. Topstep « Consistency ») over the base rules: null removes a field. */
function pr_merge_phase(array $base, array $over): array
{
    foreach ($over as $k => $v) { if ($v === null) unset($base[$k]); else $base[$k] = $v; }
    return $base;
}

/* ───────────── the rules an account gets from a preset (same maths as the app: presets in ux.js) ───────────── */

/** « firm|program|size|phase|opt+opt » → [size, program, firm, rules] or null. */
function pr_find(array $cat, string $value): ?array
{
    $v = explode('|', $value) + ['', '', '', '', ''];
    foreach ((array) $cat['firms'] as $f) if (($f['id'] ?? '') === $v[0]) foreach ((array) $f['programs'] as $p) if (($p['id'] ?? '') === $v[1])
        foreach ((array) $p['sizes'] as $s) if ((string) $s['size'] === $v[2]) return [$s, $p, $f, $v[3], array_values(array_filter(explode('+', (string) $v[4])))];
    return null;
}

function pr_phase_rules(array $s, string $phase, array $opts): ?array
{
    if ($phase === 'live') {
        if (!empty($s['live'])) return $s['live'];
        if (empty($s['funded'])) return null;
        $r = $s['funded'];
        $r['payout'] = $r['payout_live'] ?? (isset($r['payout']) ? array_diff_key($r['payout'], ['max' => 1, 'max_dll' => 1, 'ladder' => 1, 'max_payouts' => 1]) : null);
        return $r;
    }
    if (empty($s[$phase])) return null;
    $r = $s[$phase];
    foreach ($opts as $o) if (!empty($s['variants'][$o][$phase])) $r = pr_merge_phase($r, $s['variants'][$o][$phase]);
    return $r;
}

/** The account rules (amounts in cents, as the app stores them) for a preset value. */
function pr_rules_of(array $cat, string $value): ?array
{
    $hit = pr_find($cat, $value); if (!$hit) return null;
    [$s, $p, $f, $phase, $opts] = $hit;
    $r = pr_phase_rules($s, $phase, $opts) ?? (!empty($s['eval']) ? $s['eval'] : ($s['funded'] ?? null));
    if (!$r) return null;
    $c = fn($x) => $x === null ? null : (int) round($x * 100);
    $dll = in_array('dll', $opts, true);
    $liveStart = $phase === 'live' && !empty($r['start_pct']) ? (int) round($s['size'] * $r['start_pct'] / 100) : null;
    $liveDd = $liveStart !== null && isset($r['floor']) ? $liveStart - $r['floor'] : null;
    $out = ['target_c' => $phase === 'eval' ? $c($r['target'] ?? null) : null, 'dd_c' => $liveDd !== null ? $c($liveDd) : $c($r['dd'] ?? null),
        'dd_floor_c' => $phase === 'live' && isset($r['floor']) ? $c($r['floor']) : null, 'dd_type' => $r['dd_type'] ?? 'eod', 'dd_lock_offset_c' => isset($r['dd_lock_offset']) ? $c($r['dd_lock_offset']) : null,
        'dll_c' => !empty($r['dll_optional']) && !$dll ? null : $c($r['dll'] ?? null), 'consistency_pct' => $r['consistency'] ?? null,
        'min_days' => $phase === 'eval' ? ($r['min_days'] ?? null) : null];
    $po = $phase === 'eval' ? null : ($r['payout'] ?? null);
    $out += [
        'payout_win_days' => $po['win_days'] ?? null, 'payout_win_min_c' => !empty($po['win_days']) ? $c($po['win_min'] ?? 0) : null,
        'payout_trade_days' => $po['trade_days'] ?? null, 'payout_min_c' => $c($po['min'] ?? null),
        'payout_max_c' => $c($dll && !empty($po['max_dll']) ? $po['max_dll'] : ($po['max'] ?? null)), 'payout_max_pct' => $po['max_pct'] ?? null,
        'payout_min_bal_c' => $c($po['min_bal'] ?? null), 'payout_cycle_pos' => !empty($po['cycle_pos']) ? true : null,
        'payout_cycle_min_c' => $c($po['cycle_min'] ?? null), 'payout_ladder_c' => isset($po['ladder']) && is_array($po['ladder']) ? array_map($c, $po['ladder']) : null,
        'payout_max_n' => $po['max_payouts'] ?? null, 'payout_split_pct' => $po['split_pct'] ?? null,
    ];
    return ['rules' => $out, 'name' => $p['name'] . ' ' . ($s['size'] / 1000) . 'K', 'firm' => $f['name'], 'price' => $s['price'] ?? null];
}

/** What differs between two sets of account rules: [field => [old, new]]. */
function pr_rules_diff(array $a, array $b): array
{
    $d = [];
    foreach (array_unique(array_merge(array_keys($a), array_keys($b))) as $k) {
        $x = $a[$k] ?? null; $y = $b[$k] ?? null;
        if (is_array($x) || is_array($y)) { if (json_encode($x) !== json_encode($y)) $d[$k] = [$x, $y]; }
        elseif ($x != $y) $d[$k] = [$x, $y];
    }
    return $d;
}

/** The differences in plain words, in the trader's language (en / fr / es). At most 4 lines, then « +N ». */
function pr_describe(array $diff, string $lang): string
{
    $L = [
        'en' => ['target_c' => 'Profit target', 'dd_c' => 'Max loss', 'dd_type' => 'Drawdown type', 'dll_c' => 'Daily loss limit', 'consistency_pct' => 'Consistency', 'min_days' => 'Minimum days',
            'payout_win_days' => 'Winning days for a payout', 'payout_win_min_c' => 'Minimum per winning day', 'payout_trade_days' => 'Trading days for a payout', 'payout_min_c' => 'Minimum payout',
            'payout_max_c' => 'Maximum per payout', 'payout_max_pct' => 'Max % of the profit', 'payout_min_bal_c' => 'Balance to keep', 'payout_cycle_min_c' => 'Profit since the last payout',
            'payout_ladder_c' => 'Payout caps', 'payout_max_n' => 'Max number of payouts', 'payout_cycle_pos' => 'Profitable since the last payout', 'dd_floor_c' => 'Balance to stay above',
            '_none' => 'none', '_yes' => 'yes', '_more' => '+{n} more', 'eod' => 'end of day', 'trade' => 'real time', 'static' => 'static'],
        'fr' => ['target_c' => 'Objectif de profit', 'dd_c' => 'Perte max', 'dd_type' => 'Type de drawdown', 'dll_c' => 'Limite de perte du jour', 'consistency_pct' => 'Consistance', 'min_days' => 'Jours minimum',
            'payout_win_days' => 'Jours gagnants pour un payout', 'payout_win_min_c' => 'Minimum par jour gagnant', 'payout_trade_days' => 'Jours tradés pour un payout', 'payout_min_c' => 'Payout minimum',
            'payout_max_c' => 'Maximum par payout', 'payout_max_pct' => 'Max % du profit', 'payout_min_bal_c' => 'Solde à garder', 'payout_cycle_min_c' => 'Profit depuis le dernier payout',
            'payout_ladder_c' => 'Plafonds de payout', 'payout_max_n' => 'Nombre max de payouts', 'payout_cycle_pos' => 'Profitable depuis le dernier payout', 'dd_floor_c' => 'Solde à garder au-dessus de',
            '_none' => 'aucune', '_yes' => 'oui', '_more' => '+{n} autres', 'eod' => 'fin de journée', 'trade' => 'temps réel', 'static' => 'fixe'],
        'es' => ['target_c' => 'Objetivo de beneficio', 'dd_c' => 'Pérdida máx.', 'dd_type' => 'Tipo de drawdown', 'dll_c' => 'Límite de pérdida diaria', 'consistency_pct' => 'Consistencia', 'min_days' => 'Días mínimos',
            'payout_win_days' => 'Días ganadores para un payout', 'payout_win_min_c' => 'Mínimo por día ganador', 'payout_trade_days' => 'Días operados para un payout', 'payout_min_c' => 'Payout mínimo',
            'payout_max_c' => 'Máximo por payout', 'payout_max_pct' => 'Máx. % del beneficio', 'payout_min_bal_c' => 'Saldo a mantener', 'payout_cycle_min_c' => 'Beneficio desde el último payout',
            'payout_ladder_c' => 'Topes de payout', 'payout_max_n' => 'Número máx. de payouts', 'payout_cycle_pos' => 'Rentable desde el último payout', 'dd_floor_c' => 'Saldo mínimo',
            '_none' => 'ninguno', '_yes' => 'sí', '_more' => '+{n} más', 'eod' => 'al cierre', 'trade' => 'tiempo real', 'static' => 'fijo'],
    ][$lang] ?? null;
    if (!$L) return pr_describe($diff, 'en');
    $fmt = function ($k, $v) use ($L) {
        if ($v === null || $v === false) return $L['_none'];
        if ($v === true) return $L['_yes'];
        if (is_array($v)) return implode(' / ', array_map(fn($x) => $x === null ? '∞' : '$' . number_format($x / 100), $v));
        if (substr($k, -2) === '_c') return '$' . number_format($v / 100);
        if (in_array($k, ['consistency_pct', 'payout_max_pct'], true)) return $v . ' %';
        return $L[$v] ?? (string) $v;
    };
    $lines = [];
    foreach ($diff as $k => [$a, $b]) { if (!isset($L[$k])) continue; $lines[] = $L[$k] . ' : ' . $fmt($k, $a) . ' → ' . $fmt($k, $b); }
    if ($lang === 'en') $lines = array_map(fn($x) => str_replace(' : ', ': ', $x), $lines);
    $more = count($lines) - 4;
    return implode(' · ', array_slice($lines, 0, 4)) . ($more > 0 ? ' · ' . str_replace('{n}', (string) $more, $L['_more']) : '');
}

/* ───────────── differences, in words (for the admin and the history) ───────────── */

function pr_diff_firm(array $old, array $new): array
{
    $d = [];
    $idx = function (array $f) { $o = []; foreach ((array) ($f['programs'] ?? []) as $p) foreach ((array) ($p['sizes'] ?? []) as $s) $o[$p['name'] . ' ' . ((int) $s['size'] / 1000) . 'K'] = $s; return $o; };
    $a = $idx($old); $b = $idx($new);
    foreach ($b as $k => $s) if (!isset($a[$k])) $d[] = "new: $k";
    foreach ($a as $k => $s) if (!isset($b[$k])) $d[] = "removed: $k";
    foreach ($b as $k => $s) {
        if (!isset($a[$k])) continue;
        foreach (['eval', 'funded'] as $ph) foreach (['target', 'dd', 'dd_type', 'dll', 'dll_optional', 'consistency', 'min_days', 'max_minis'] as $f) {
            $x = $a[$k][$ph][$f] ?? null; $y = $s[$ph][$f] ?? null;
            if ($x != $y) $d[] = "$k $ph $f: " . ($x === null ? '—' : var_export($x, true)) . ' → ' . ($y === null ? '—' : var_export($y, true));
        }
        foreach (array_unique(array_merge(array_keys((array) ($a[$k]['funded']['payout'] ?? [])), array_keys((array) ($s['funded']['payout'] ?? [])))) as $f) {
            $x = $a[$k]['funded']['payout'][$f] ?? null; $y = $s['funded']['payout'][$f] ?? null; if (is_array($x)) $x = json_encode($x); if (is_array($y)) $y = json_encode($y);
            if ($x != $y) $d[] = "$k payout $f: " . ($x === null ? '—' : $x) . ' → ' . ($y === null ? '—' : $y);
        }
        foreach (['eval', 'eval_period', 'activation'] as $f) {
            $x = $a[$k]['price'][$f] ?? null; $y = $s['price'][$f] ?? null;
            if ($x != $y) $d[] = "$k price $f: " . ($x === null ? '—' : $x) . ' → ' . ($y === null ? '—' : $y);
        }
    }
    return $d;
}

/* ───────────── saving (each version kept, newest 40) ───────────── */

function pr_save(array $catalogue): void
{
    $dir = pr_history_dir();
    if (!is_dir($dir)) @mkdir($dir, 0750, true);
    // the version being replaced goes to the history (the shipped seed the first time)
    @copy(is_file(pr_live_path()) ? pr_live_path() : pr_seed_path(), $dir . '/' . gmdate('Y-m-d-His') . '.json');
    $files = glob($dir . '/*.json') ?: [];
    sort($files);
    while (count($files) > 40) @unlink(array_shift($files));
    $tmp = pr_live_path() . '.tmp';
    file_put_contents($tmp, json_encode($catalogue, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_PRETTY_PRINT));
    rename($tmp, pr_live_path());
}

function pr_save_status(array $status): void
{
    $tmp = pr_status_path() . '.tmp';
    file_put_contents($tmp, json_encode($status, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_PRETTY_PRINT));
    rename($tmp, pr_status_path());
}

/** Restore the version before the current one. */
function pr_rollback(): ?string
{
    $files = glob(pr_history_dir() . '/*.json') ?: [];
    sort($files);
    $last = array_pop($files);
    if (!$last || !pr_read($last)) return null;
    copy($last, pr_live_path());
    @unlink($last);
    return basename($last);
}
