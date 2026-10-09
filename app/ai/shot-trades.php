<?php
declare(strict_types=1);
/**
 * Sweep — several trades from one screenshot.
 * Gemini only copies what the screenshot shows (rows); everything is computed here, the same way every time:
 *  - closed_trades: one row = one trade;
 *  - fills: per symbol, in time order, FIFO; a trade runs from flat back to flat (scale-ins and partial exits are the
 *    executions of ONE trade, weighted average prices); a reversal closes the trade and opens the next one; a position
 *    still open at the end is « Open — to complete » (unchecked);
 *  - P&L = (exit − entry) × qty × $ per point (sign by direction); the P&L shown on screen wins when it differs by more
 *    than one tick × qty (the trade is then « To check »);
 *  - fees: the commissions shown, else the account's commission per contract;
 *  - times → New York; the trade's date is its session (18:00 ET and later = next day).
 * Pure functions: tests/shot_trades_test.php checks them without the network.
 */

const SHOT_ROOTS = ['MNQ', 'NQ', 'MES', 'ES', 'MYM', 'YM', 'M2K', 'RTY', 'MCL', 'CL', 'MGC', 'GC', 'SIL', 'SI', 'M6E', '6E', 'ZN', 'ZB', 'NG', 'HG', 'MBT', 'MET'];
const SHOT_TZ = ['ET' => 'America/New_York', 'CT' => 'America/Chicago', 'UTC' => 'UTC'];

function shot_spec(string $root): ?array
{
    $t = defined('SAI_INSTRUMENTS') ? SAI_INSTRUMENTS : [];
    return $t[$root] ?? null;   // [tick size, $ per point]
}
/** contract names written in full on charts and dashboards → root (longest names first) */
const SHOT_NAMES = [
    'micro e-mini nasdaq' => 'MNQ', 'micro nasdaq' => 'MNQ', 'e-mini nasdaq' => 'NQ', 'nasdaq 100' => 'NQ', 'nasdaq' => 'NQ',
    'micro e-mini s&p' => 'MES', 'micro s&p' => 'MES', 'e-mini s&p' => 'ES', 's&p 500' => 'ES',
    'micro e-mini dow' => 'MYM', 'micro dow' => 'MYM', 'e-mini dow' => 'YM', 'dow' => 'YM',
    'micro e-mini russell' => 'M2K', 'micro russell' => 'M2K', 'e-mini russell' => 'RTY', 'russell' => 'RTY',
    'micro gold' => 'MGC', 'gold' => 'GC', 'oro' => 'GC', 'micro silver' => 'SIL', 'silver' => 'SI',
    'micro crude' => 'MCL', 'micro wti' => 'MCL', 'crude oil' => 'CL', 'crude' => 'CL', 'wti' => 'CL', 'natural gas' => 'NG', 'copper' => 'HG',
    'micro euro' => 'M6E', 'euro fx' => '6E', '10-year' => 'ZN', '10 year' => 'ZN', 't-bond' => 'ZB', '30-year' => 'ZB', 'micro bitcoin' => 'MBT', 'micro ether' => 'MET',
];
/**
 * « MNQZ6 », « MNQ 12-26 », « /MNQ », « CME_MINI:MNQZ2026 », « MNQ1! », « Gold (GCZ6) · 5 · COMEX », « Micro E-mini Nasdaq »
 * → the contract's root (null when unknown). A code in brackets wins over the name; the name is read last.
 */
function shot_root(string $sym): ?string
{
    $raw = trim($sym); if ($raw === '') return null;
    $try = function (string $s): ?string {
        $s = strtoupper(trim($s));
        $s = preg_replace('/^[A-Z0-9_]+:/', '', $s); $s = ltrim($s, '/ '); $s = preg_replace('/\s+.*/', '', $s);
        if ($s === '') return null;
        foreach (SHOT_ROOTS as $r) if (str_starts_with($s, $r)) {
            $rest = substr($s, strlen($r));
            if ($rest === '' || preg_match('/^([FGHJKMNQUVXZ]\d{1,4}|\d!?|\d{1,2}-\d{2,4}|!)$/', $rest)) return $r;   // the root, then a month/year code
        }
        return null;
    };
    if (preg_match_all('/\(([^)]+)\)/', $raw, $m)) foreach ($m[1] as $in) if ($r = $try($in)) return $r;   // « Gold (GCZ6) »
    if ($r = $try($raw)) return $r;
    foreach (preg_split('/[\s·•|,]+/u', $raw) as $tok) if ($tok !== '' && ($r = $try($tok))) return $r;
    $low = mb_strtolower($raw);
    foreach (SHOT_NAMES as $name => $r) if (preg_match('/(^|[^a-z])' . preg_quote($name, '/') . '([^a-z]|$)/u', $low)) return $r;
    return null;
}
function shot_num($v): ?float
{
    if ($v === null || $v === '') return null;
    if (is_numeric($v)) return (float) $v;
    $s = str_replace(['$', ' ', "\u{202F}", "\u{00A0}"], '', (string) $v);
    $neg = str_starts_with($s, '(') && str_ends_with($s, ')') || str_starts_with($s, '-') || str_starts_with($s, '−');
    $s = trim(str_replace(['(', ')', '−', '-'], '', $s));
    if (preg_match('/^\d{1,3}(\.\d{3})+,\d+$/', $s)) $s = str_replace(['.', ','], ['', '.'], $s);   // 1.234,50
    else $s = str_replace(',', '', $s);
    if (!is_numeric($s)) return null;
    return $neg ? -(float) $s : (float) $s;
}
/**
 * a date/time written on the screenshot → [Y-m-d, H:i:s] at New York time (null if unreadable).
 * Reads: 2026-10-07 14:32:10 · 2026-10-07T18:32:10.123Z / +02:00 (the written offset wins) · 10/07/2026 2:32:10 PM ·
 * 07/10/2026 14:32 (day first when the first number is > 12) · Oct 7, 2026 2:32:10 PM · 7 oct. 2026 14:32 ·
 * 14:32:10.250 (time only: the day comes from $fallbackDate). $tz = zone of the times when no offset is written.
 */
function shot_time(?string $raw, string $tz, string $fallbackDate, ?bool $dayFirst = null): ?array
{
    $raw = trim((string) $raw); if ($raw === '') return null;
    $raw = preg_replace('/\s+/', ' ', str_replace(["\u{202F}", "\u{00A0}", ','], [' ', ' ', ' '], $raw));
    $zone = $tz;
    if (preg_match('/\s*\b(ET|EST|EDT)\b\.?$/i', $raw)) { $zone = 'America/New_York'; $raw = trim(preg_replace('/\s*\b(ET|EST|EDT)\b\.?$/i', '', $raw)); }
    elseif (preg_match('/\s*\b(CT|CST|CDT)\b\.?$/i', $raw)) { $zone = 'America/Chicago'; $raw = trim(preg_replace('/\s*\b(CT|CST|CDT)\b\.?$/i', '', $raw)); }
    elseif (preg_match('/\s*\b(UTC|GMT)\b$/i', $raw)) { $zone = 'UTC'; $raw = trim(preg_replace('/\s*\b(UTC|GMT)\b$/i', '', $raw)); }
    $off = null;
    if (preg_match('/(Z|[+-]\d{2}:?\d{2})$/', $raw, $om) && preg_match('/\d{1,2}:\d{2}/', $raw)) { $off = $om[1] === 'Z' ? '+00:00' : $om[1]; $raw = trim(substr($raw, 0, -strlen($om[1]))); }
    $months = ['jan' => 1, 'feb' => 2, 'fév' => 2, 'fev' => 2, 'mar' => 3, 'apr' => 4, 'avr' => 4, 'abr' => 4, 'may' => 5, 'mai' => 5, 'jun' => 6, 'juin' => 6, 'jul' => 7, 'juil' => 7, 'aug' => 8, 'aoû' => 8, 'aou' => 8, 'ago' => 8, 'sep' => 9, 'oct' => 10, 'nov' => 11, 'dec' => 12, 'déc' => 12, 'dic' => 12, 'ene' => 1, 'enero' => 1];
    $y = $mo = $d = null;
    $rest = $raw;
    if (preg_match('/(\d{4})[-\/.](\d{1,2})[-\/.](\d{1,2})[T ]?/', $raw, $m)) { [$y, $mo, $d] = [(int) $m[1], (int) $m[2], (int) $m[3]]; $rest = substr($raw, strpos($raw, $m[0]) + strlen($m[0])); }
    elseif (preg_match('/(\d{1,2})[\/.\-](\d{1,2})[\/.\-](\d{2,4})/', $raw, $m)) {
        $a = (int) $m[1]; $b = (int) $m[2]; $y = strlen($m[3]) === 2 ? 2000 + (int) $m[3] : (int) $m[3];
        if ($a > 12 || ($dayFirst === true && $b <= 12)) [$d, $mo] = [$a, $b]; else [$mo, $d] = [$a, $b];   // US month/day unless the table writes day first
        $rest = substr($raw, strpos($raw, $m[0]) + strlen($m[0]));
    } elseif (preg_match('/\b([A-Za-zéûÉ]{3,5})\.?\s+(\d{1,2})(?:st|nd|rd|th)?\s+(\d{4})\b/u', $raw, $m) && shot_month($m[1], $months)) {
        $mo = shot_month($m[1], $months); $d = (int) $m[2]; $y = (int) $m[3];
        $rest = substr($raw, strpos($raw, $m[0]) + strlen($m[0]));
    } elseif (preg_match('/\b(\d{1,2})\s+([A-Za-zéûÉ]{3,5})\.?\s+(\d{4})\b/u', $raw, $m) && shot_month($m[2], $months)) {
        $mo = shot_month($m[2], $months); $d = (int) $m[1]; $y = (int) $m[3];
        $rest = substr($raw, strpos($raw, $m[0]) + strlen($m[0]));
    }
    if (!preg_match('/(\d{1,2}):(\d{2})(?::(\d{2}))?(?:[.,]\d+)?\s*([AaPp]\.?[Mm]\.?)?/', $rest !== '' ? $rest : $raw, $tm) && !preg_match('/(\d{1,2}):(\d{2})(?::(\d{2}))?(?:[.,]\d+)?\s*([AaPp]\.?[Mm]\.?)?/', $raw, $tm)) return null;
    $h = (int) $tm[1]; $mi = (int) $tm[2]; $se = (int) ($tm[3] ?? 0);
    if (!empty($tm[4])) { $h %= 12; if (strtolower($tm[4][0]) === 'p') $h += 12; }
    if ($h > 23 || $mi > 59) return null;
    if (!$y || !$mo || !$d) { $fb = explode('-', $fallbackDate); [$y, $mo, $d] = [(int) $fb[0], (int) $fb[1], (int) $fb[2]]; }
    if (!checkdate((int) $mo, (int) $d, (int) $y)) return null;
    try {
        $str = sprintf('%04d-%02d-%02d %02d:%02d:%02d', $y, $mo, $d, $h, $mi, $se);
        $dt = $off !== null ? new DateTimeImmutable($str . ' ' . $off) : new DateTimeImmutable($str, new DateTimeZone($zone));
        $ny = $dt->setTimezone(new DateTimeZone('America/New_York'));
        return [$ny->format('Y-m-d'), $ny->format('H:i:s')];
    } catch (Throwable $e) { return null; }
}
function shot_month(string $w, array $months): ?int { $k = mb_strtolower($w); return $months[mb_substr($k, 0, 4)] ?? $months[mb_substr($k, 0, 3)] ?? null; }

/** day first (07/10 = 7 October) or month first, decided once for the whole table from all its dates */
function shot_dayfirst(array $strings, string $today): ?bool
{
    $first = $second = false; $cands = [];
    foreach ($strings as $x) if (preg_match('/\b(\d{1,2})[\/.\-](\d{1,2})[\/.\-](\d{2,4})\b/', (string) $x, $m)) {
        if ((int) $m[1] > 12) $first = true; if ((int) $m[2] > 12) $second = true; $cands[] = $m;
    }
    if ($first && !$second) return true;
    if ($second && !$first) return false;
    if (!$cands) return null;
    // still ambiguous: the reading that puts the trades closest to today (and not in the future)
    $score = function (bool $df) use ($cands, $today) { $s = 0; foreach ($cands as $m) { $y = strlen($m[3]) === 2 ? 2000 + (int) $m[3] : (int) $m[3]; [$mo, $d] = $df ? [(int) $m[2], (int) $m[1]] : [(int) $m[1], (int) $m[2]]; if (!checkdate($mo, $d, $y)) return PHP_INT_MAX; $diff = (strtotime($today) - strtotime(sprintf('%04d-%02d-%02d', $y, $mo, $d))) / 86400; $s += $diff < -1 ? 10000 : abs($diff); } return $s; };
    return $score(true) < $score(false);
}
/**
 * the table as written (column titles + cells, copied by Gemini) → rows with known fields. Columns are recognised by
 * their title, in English, French or Spanish; the order on screen does not matter.
 */
function shot_table_rows(array $columns, array $table): array
{
    // a column title → its field, by the words it contains (titles are often cut: « Instrum… », « Open ti… »)
    $field = function (string $title): ?string {
        $k = mb_strtolower(trim(preg_replace('/[\s ]+/u', ' ', $title)));
        $k = trim(preg_replace('/(\.{2,}|…)$/u', '', $k), " .:*\t");
        if ($k === '') return null;
        $has = fn(string $re) => (bool) preg_match('/' . $re . '/u', $k);
        $time = $has('time|date|heure|hora|fecha|\bat\b|timestamp|when|^(entered|exited|opened|closed)$');
        $price = $has('price|prix|precio|avg|fill');
        if ($has('^(net |gross |realized |réalisé )?(p ?& ?l|pnl|p\/l|profit|résultat|resultat|gain|ganancia|result)') || $has('p&l|pnl|profit') && !$has('%|factor')) return 'pnl_shown';
        if ($has('commission|charge|fee|frais|comisi|^comm')) return 'commission_shown';
        if ($has('^(instrum|symbol|symbole|contract|contrat|ticker|product|produit|market|march|sym|contractname|s[ií]mbolo)')) return 'symbol';
        if ($has('^(side|sens|direction|dir$|b\/s|buy\/sell|long\/short|action|position|lado|type$|trade side)')) return 'side';
        if ($has('^(qty|quant|size|taille|contracts?$|contrats?$|lots?$|filled qty|qty filled|cantidad|amount$)')) return 'qty';
        if ($time && $has('entry|entr|open|opened|entered|start|in$|time in|ouverture|apertura')) return 'entry_time';
        if ($time && $has('exit|sortie|close|closed|exited|end|out$|time out|fermeture|cierre')) return 'exit_time';
        if ($has('entry|entr[ée]e|open price|buy price|opening|apertura') && !$time) return 'entry_price';
        if ($has('exit|sortie|close price|sell price|closing|cierre') && !$time) return 'exit_price';
        if ($price && !$time) return 'price';
        if ($time) return 'datetime';
        return null;
    };
    $map = [];
    foreach ($columns as $i => $c) { $f = $field((string) $c); if ($f && !isset($map[$f])) $map[$f] = $i; }
    // no symbol column recognised: the column whose cells look like contracts (NQZ6, MGC, /ES…)
    if (!isset($map['symbol'])) {
        $best = null; $bestN = 0;
        foreach ($columns as $i => $c) { if (in_array($i, $map, true)) continue; $n = 0; foreach ($table as $cells) if (is_array($cells) && shot_root((string) ($cells[$i] ?? ''))) $n++; if ($n > $bestN) { $best = $i; $bestN = $n; } }
        if ($best !== null && $bestN >= max(1, (int) floor(count($table) / 2))) $map['symbol'] = $best;
    }
    $gross = isset($map['pnl_shown']) && preg_match('/gross|brut/i', (string) ($columns[$map['pnl_shown']] ?? ''));
    $rows = [];
    foreach ($table as $cells) {
        if (!is_array($cells)) continue;
        $r = ['confidence' => 0.95];
        foreach ($map as $field => $i) $r[$field] = isset($cells[$i]) ? trim((string) $cells[$i]) : null;
        if ($gross) $r['pnl_is_gross'] = true;
        $rows[] = $r;
    }
    return ['rows' => $rows, 'map' => $map];
}
/** the session of a New York clock time: 18:00 and later belong to the next day */
function shot_session(string $date, string $time): string
{
    return substr($time, 0, 5) >= '18:00' ? (new DateTimeImmutable($date . ' 12:00:00'))->modify('+1 day')->format('Y-m-d') : $date;
}
function shot_pnl_c(string $root, string $dir, float $entry, float $exit, float $qty): ?int
{
    $sp = shot_spec($root); if (!$sp) return null;
    return (int) round(($exit - $entry) * ($dir === 'long' ? 1 : -1) * $qty * $sp[1] * 100);
}
/** « Buy », « Long », « Achat », « B », « Buy to open »… → +1 ; « Sell », « Short », « Vente »… → −1 ; else 0 */
function shot_side($v): int
{
    $x = mb_strtolower(trim((string) $v));
    if ($x === '') return 0;
    if (preg_match('/\b(short|sell|sold|vente|vendu|venta|corto)\b|^s$|^sl$|^ss$/u', $x)) return -1;
    if (preg_match('/\b(long|buy|bought|achat|acheté|compra|largo)\b|^b$|^l$|^bt$/u', $x)) return 1;
    return 0;
}
/** a P&L as written: « $1,234.50 », « (120.00) », « -$45 », with the colour when only the colour says it is a loss */
function shot_pnl_cents($v, $color = null): ?int
{
    $n = shot_num($v); if ($n === null) return null;
    $c = (int) round($n * 100);
    if ($c > 0 && in_array(strtolower((string) $color), ['red', 'rouge', 'rojo', 'loss', 'negative'], true)) $c = -$c;
    return $c;
}
/**
 * rows (from Gemini) → trades. $o: tz (zone of the screenshot), date (fallback day), fee_rt_c (account commission per
 * contract), id (function for new ids). Returns ['trades' => [...], 'open' => n, 'unknown' => [symbols]].
 * When Gemini sends the table as written (columns + table), the rows come from shot_table_rows().
 */
function shot_build(array $data, array $o): array
{
    $tz = $o['tz'] ?? 'America/New_York'; $day = $o['date'] ?? date('Y-m-d'); $feeRt = (int) ($o['fee_rt_c'] ?? 0);
    $nid = $o['id'] ?? fn($p) => $p . bin2hex(random_bytes(6));
    $type = (string) ($data['source_type'] ?? 'unknown');
    $rows = array_values(array_filter((array) ($data['rows'] ?? []), 'is_array'));
    if (!empty($data['columns']) && !empty($data['table'])) {
        $tb = shot_table_rows((array) $data['columns'], (array) $data['table']);
        $colors = (array) ($data['pnl_colors'] ?? []);
        foreach ($tb['rows'] as $k => &$r) { if (isset($colors[$k])) $r['pnl_color'] = $colors[$k]; } unset($r);
        $rows = $tb['rows']; $m = $tb['map'];
        if ((isset($m['entry_price']) && isset($m['exit_price'])) || (isset($m['entry_time']) && isset($m['exit_time']))) $type = 'closed_trades';
        elseif (isset($m['price']) && isset($m['side'])) $type = 'fills';
    }
    if (!empty($data['date_shown']) && ($ds = shot_time((string) $data['date_shown'] . ' 12:00', 'America/New_York', $day))) $day = $ds[0];
    $symAll = trim((string) ($data['symbol_shown'] ?? ''));
    if ($symAll !== '') foreach ($rows as &$r) { if (trim((string) ($r['symbol'] ?? '')) === '' || !shot_root((string) $r['symbol'])) $r['symbol'] = shot_root((string) ($r['symbol'] ?? '')) ? $r['symbol'] : $symAll; } unset($r);
    $strs = []; foreach ($rows as $r) foreach (['datetime', 'entry_time', 'exit_time'] as $f) if (!empty($r[$f])) $strs[] = (string) $r[$f];
    $df = shot_dayfirst($strs, $day);
    $T = fn($raw, $fallback) => shot_time($raw, $tz, $fallback, $df);
    $out = []; $unknown = [];
    $finish = function (array $t) use (&$out, $feeRt) {
        $t['contracts'] = max(1, (int) round($t['contracts']));
        $calc = ($t['entry'] !== null && $t['exit'] !== null) ? shot_pnl_c($t['instrument'], $t['direction'], $t['entry'], $t['exit'], $t['contracts']) : null;
        $shown = $t['_shown']; $feesShown = $t['_fees'] !== null ? (int) round(abs($t['_fees']) * 100) : null;
        $sp = shot_spec($t['instrument']); $tol = $sp ? max(1, (int) round($sp[0] * $sp[1] * $t['contracts'] * 100)) : 0;
        $t['pnl_calc_c'] = $calc; $t['pnl_shown_c'] = $shown;
        $fees = $feesShown ?? ($feeRt > 0 ? $feeRt * $t['contracts'] : 0);
        if ($calc !== null && $shown !== null && empty($t['_gross'])) {
            if (abs($shown - $calc) <= $tol) { $t['pnl_c'] = $calc; }                                    // the platform shows the gross P&L
            elseif ($feesShown !== null && abs($shown - ($calc - $feesShown)) <= $tol) { $t['pnl_c'] = $calc; }   // it shows the net P&L
            elseif ($feesShown === null && $calc - $shown > 0 && $calc - $shown <= 1500 * $t['contracts']) { $t['pnl_c'] = $calc; $fees = $calc - $shown; $t['fees_from_pnl'] = true; }   // net P&L: the difference is the fees
            else { $t['pnl_c'] = $shown; $t['pnl_manual'] = true; $t['check'] = true; $t['why'][] = 'pnl'; }
        } elseif ($calc !== null) { $t['pnl_c'] = $calc; }
        elseif ($shown !== null) { $t['pnl_c'] = $shown; $t['pnl_manual'] = true; }
        else { $t['pnl_c'] = 0; $t['pnl_manual'] = true; if (empty($t['open'])) { $t['check'] = true; $t['why'][] = 'pnl'; } }
        $t['pnl_manual'] = $t['pnl_manual'] ?? false;
        $t['fees_c'] = $fees; if ($feesShown === null && $fees > 0 && empty($t['fees_from_pnl'])) $t['fees_auto'] = true;
        $t['net_c'] = $t['pnl_c'] - $t['fees_c'];
        $t['why'] = array_values(array_unique($t['why']));
        unset($t['_shown'], $t['_fees'], $t['_gross']);
        $out[] = $t;
    };
    $base = fn(string $root, string $dir, ?array $tm, string $fallbackDay) => ['id' => $nid('t'), 'instrument' => $root, 'direction' => $dir, 'date' => $tm ? shot_session($tm[0], $tm[1]) : $fallbackDay, 'session_date' => true,
        'entry_time' => $tm ? substr($tm[1], 0, 5) : '', 'exit_time' => '', 'contracts' => 0, 'entry' => null, 'exit' => null, 'executions' => [], 'check' => false, 'open' => false, 'why' => [], '_shown' => null, '_fees' => null, '_gross' => false];
    if ($type === 'closed_trades' || $type === 'chart') {
        // does this platform write the minus of a loss? (some only colour it red: then an unsigned number says nothing)
        $signsWritten = false; foreach ($rows as $r) if (preg_match('/[-−(]/u', (string) ($r['pnl_shown'] ?? ''))) { $signsWritten = true; break; }
        foreach ($rows as $r) {
            $root = shot_root((string) ($r['symbol'] ?? '')); if (!$root) { $unknown[] = trim((string) ($r['symbol'] ?? '')) !== '' ? (string) $r['symbol'] : ''; continue; }
            $tin = $T($r['entry_time'] ?? $r['datetime'] ?? null, $day);
            $tout = $T($r['exit_time'] ?? null, $tin ? $tin[0] : $day);
            if ($tin && $tout && $tout[0] . $tout[1] < $tin[0] . $tin[1]) [$tin, $tout] = [$tout, $tin];   // columns read the other way round
            $q = abs(shot_num($r['qty'] ?? 1) ?? 1) ?: 1;
            $en = shot_num($r['entry_price'] ?? $r['price'] ?? null); $ex = shot_num($r['exit_price'] ?? null);
            $shown = shot_pnl_cents($r['pnl_shown'] ?? null, $r['pnl_color'] ?? null);
            // the direction: written on the screenshot, checked against the prices and the P&L (the math wins)
            $sd = shot_side($r['side'] ?? '');
            // is the P&L's sign really written (minus, parentheses or a colour)? Otherwise it cannot correct the side.
            $explicit = $signsWritten || preg_match('/[-−(]/u', (string) ($r['pnl_shown'] ?? '')) || in_array(strtolower((string) ($r['pnl_color'] ?? '')), ['red', 'green', 'rouge', 'vert', 'rojo', 'verde'], true);
            $math = ($en !== null && $ex !== null && $ex != $en && $shown && $explicit) ? ((($ex - $en) * $shown) > 0 ? 1 : -1) : 0;
            if ($shown && !$explicit && $sd && $en !== null && $ex !== null && $ex != $en) $shown = abs($shown) * ((($ex - $en) * $sd) > 0 ? 1 : -1);   // sign from the side and the prices
            $fixed = false;
            if ($math && $sd && $math !== $sd) { $sd = $math; $fixed = true; } elseif (!$sd) $sd = $math;
            $t = $base($root, $sd >= 0 ? 'long' : 'short', $tin, $tin ? shot_session($tin[0], $tin[1]) : $day);
            if (!$sd) { $t['check'] = true; $t['why'][] = 'side'; }
            if ($fixed) $t['side_fixed'] = true;
            if (!$tin) { $t['check'] = true; $t['why'][] = 'time'; }
            $t['contracts'] = $q; $t['entry'] = $en; $t['exit'] = $ex;
            $t['exit_time'] = $tout ? substr($tout[1], 0, 5) : '';
            $t['_shown'] = $shown; $t['_fees'] = shot_num($r['commission_shown'] ?? null); $t['_gross'] = !empty($r['pnl_is_gross']) && false;
            $bs = fn(int $sgn) => $sgn > 0 ? 'buy' : 'sell';
            if ($en !== null && $tin) $t['executions'][] = ['id' => $nid('x'), 'side' => $bs($sd >= 0 ? 1 : -1), 'qty' => $q, 'price' => $en, 't' => $tin[0] . ' ' . $tin[1]];
            if ($ex !== null && ($tout || $tin)) $t['executions'][] = ['id' => $nid('x'), 'side' => $bs($sd >= 0 ? -1 : 1), 'qty' => $q, 'price' => $ex, 't' => ($tout ?? $tin)[0] . ' ' . ($tout ?? $tin)[1]];
            if ((float) ($r['confidence'] ?? 1) < 0.6) { $t['check'] = true; $t['why'][] = 'read'; }
            if ($ex === null && $shown === null) $t['open'] = true;
            $finish($t);
        }
    } elseif ($type === 'fills') {
        $fills = []; $skipped = 0;
        foreach ($rows as $i => $r) {
            $root = shot_root((string) ($r['symbol'] ?? '')); if (!$root) { $unknown[] = trim((string) ($r['symbol'] ?? '')) !== '' ? (string) $r['symbol'] : ''; continue; }
            $sd = shot_side($r['side'] ?? ''); $q = abs(shot_num($r['qty'] ?? null) ?? 0); $px = shot_num($r['price'] ?? $r['entry_price'] ?? null);
            $tm = $T($r['datetime'] ?? $r['entry_time'] ?? null, $day);
            if (!$sd || !$q || $px === null || !$tm) { $skipped++; continue; }
            $fills[] = ['root' => $root, 'side' => $sd, 'qty' => $q, 'price' => $px, 'tm' => $tm, 'k' => $tm[0] . ' ' . $tm[1] . sprintf(' %04d', $i), 'fee' => shot_num($r['commission_shown'] ?? null), 'conf' => (float) ($r['confidence'] ?? 1)];
        }
        // a list written newest first: same time order once sorted (the original row order breaks ties, reversed if the list is newest first)
        $desc = count($fills) > 1 && strcmp($fills[0]['k'], $fills[count($fills) - 1]['k']) > 0;
        if ($desc) foreach ($fills as $n => &$f) $f['k'] = substr($f['k'], 0, -5) . sprintf(' %04d', 9999 - $n); unset($f);
        usort($fills, fn($a, $b) => strcmp($a['k'], $b['k']));
        $pos = [];
        foreach ($fills as $f) {
            $left = $f['qty'];
            while ($left > 1e-9) {
                $st = $pos[$f['root']] ?? null;
                if (!$st) $st = ['t' => $base($f['root'], $f['side'] > 0 ? 'long' : 'short', $f['tm'], $day), 'dir' => $f['side'], 'net' => 0.0, 'ew' => 0.0, 'eq' => 0.0, 'xw' => 0.0, 'xq' => 0.0, 'fee' => null, 'last' => $f['tm']];
                if ($f['side'] === $st['dir']) {
                    $st['net'] += $left; $st['ew'] += $f['price'] * $left; $st['eq'] += $left;
                    $st['t']['executions'][] = ['id' => $nid('x'), 'side' => $f['side'] > 0 ? 'buy' : 'sell', 'qty' => $left, 'price' => $f['price'], 't' => $f['tm'][0] . ' ' . $f['tm'][1]];
                    if ($f['fee'] !== null) $st['fee'] = ($st['fee'] ?? 0) + abs($f['fee']) * ($left / $f['qty']);
                    if ($f['conf'] < 0.6) { $st['t']['check'] = true; $st['t']['why'][] = 'read'; }
                    $left = 0; $pos[$f['root']] = $st; break;
                }
                $close = min($left, $st['net']);
                $st['net'] -= $close; $st['xw'] += $f['price'] * $close; $st['xq'] += $close; $left -= $close; $st['last'] = $f['tm'];
                $st['t']['executions'][] = ['id' => $nid('x'), 'side' => $f['side'] > 0 ? 'buy' : 'sell', 'qty' => $close, 'price' => $f['price'], 't' => $f['tm'][0] . ' ' . $f['tm'][1]];
                if ($f['fee'] !== null) $st['fee'] = ($st['fee'] ?? 0) + abs($f['fee']) * ($close / $f['qty']);
                if ($f['conf'] < 0.6) { $st['t']['check'] = true; $st['t']['why'][] = 'read'; }
                if ($st['net'] <= 1e-9) {
                    $t = $st['t']; $t['contracts'] = $st['eq']; $t['entry'] = round($st['ew'] / $st['eq'], 6); $t['exit'] = round($st['xw'] / $st['xq'], 6);
                    $t['exit_time'] = substr($st['last'][1], 0, 5); $t['_fees'] = $st['fee'];
                    $finish($t); unset($pos[$f['root']]);
                } else $pos[$f['root']] = $st;
            }
        }
        foreach ($pos as $st) {
            $t = $st['t']; $t['contracts'] = $st['eq']; $t['entry'] = round($st['ew'] / $st['eq'], 6);
            $t['open'] = true; $t['check'] = true; $t['why'][] = 'open'; $t['_fees'] = $st['fee']; $t['exit'] = null; $finish($t);
        }
        if ($skipped) $o['skipped'] = $skipped;
    }
    usort($out, fn($a, $b) => strcmp($a['date'] . $a['entry_time'], $b['date'] . $b['entry_time']));
    return ['trades' => $out, 'open' => count(array_filter($out, fn($t) => $t['open'])), 'unknown' => array_values(array_unique(array_filter($unknown, fn($u) => $u !== ''))), 'no_symbol' => in_array('', $unknown, true), 'type' => $type, 'skipped' => $o['skipped'] ?? 0];
}
