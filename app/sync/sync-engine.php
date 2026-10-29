<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli' && realpath((string) ($_SERVER['SCRIPT_FILENAME'] ?? '')) === realpath(__FILE__)) { http_response_code(404); exit; }
/**
 * Sweep — automatic sync: executions (fills) sent by a platform → trades.
 * Pure functions, no network, no database: the same fills always give the same trades (tests/sync_test.php).
 *  - one position per platform account and contract (MNQ 12-26 and MNQ 03-27 are two positions: a rollover never mixes);
 *  - a trade runs from flat back to flat: scale-ins and partial exits are executions of ONE trade (weighted average
 *    prices); a fill that goes through zero closes the trade and opens the next one with what is left;
 *  - a position still open is not a trade yet: its fills wait (returned in « open »);
 *  - contracts = the largest position held, as in the trade form (positionOf in app.js);
 *  - P&L = (sells − buys) × $ per point, from the platform's point value, else the app's contract table; unknown → « To check »;
 *  - fees = the commissions of the fills, else the account's round-trip commission × contracts bought and sold (fees_auto);
 *  - times arrive in UTC and are kept at New York time; the trade's date is its session (18:00 ET and later = next day);
 *  - the trade id comes from the platform account and the first fill: a second pass rewrites the same trade, never a copy.
 */

require_once __DIR__ . '/../ai/ai-stats.php';      // SAI_INSTRUMENTS: tick size and $ per point of the contracts the app knows
require_once __DIR__ . '/../ai/shot-trades.php';   // shot_root(), shot_session(): one rule for contracts and sessions

/** the fields a sync owns on a trade document; everything else (notes, review, emotions, screenshots…) is the trader's */
const SYNC_TRADE_FIELDS = ['instrument', 'date', 'session_date', 'entry_time', 'exit_time', 'session', 'direction', 'contracts', 'entry', 'exit',
    'pnl_c', 'pnl_manual', 'pnl_check', 'fees_c', 'fees_auto', 'duration_s', 'executions', 'import_key', 'source'];

/** « 09:41 » → the app's session names (sessionFor in app.js) */
function sync_session_name(string $hm): string
{
    if (!preg_match('/^(\d{2}):(\d{2})/', $hm, $m)) return 'other';
    $n = (int) $m[1] * 60 + (int) $m[2];
    if ($n >= 18 * 60 || $n < 2 * 60) return 'asia';
    if ($n < 9 * 60 + 30) return 'london';
    if ($n < 12 * 60) return 'nyam';
    if ($n < 17 * 60) return 'nypm';
    return 'other';
}

/** ProjectX (TopstepX through Quantower) names its contracts with CQG roots: « CON.F.US.ENQ.Z25 » is NQ */
const SYNC_CQG = ['EP' => 'ES', 'ENQ' => 'NQ', 'CLE' => 'CL', 'MCLE' => 'MCL', 'GCE' => 'GC', 'SIE' => 'SI', 'NGE' => 'NG', 'HGE' => 'HG', 'DSX' => '6E'];

/** « MNQ 12-26 », « MNQZ6 », « CON.F.US.MNQ.Z25 » → the app's instrument (MNQ); a contract the app does not know keeps its own root (ZC 12-26 → ZC) */
function sync_root(string $contract): array
{
    // ProjectX: « CON.F.US.MNQ.Z25 », « F.US.ENQ » (the root between the exchange and the month code)
    if (preg_match('/^(?:CON\.)?F\.[A-Z]{2,4}\.([A-Z0-9]+)(?:\.[FGHJKMNQUVXZ]\d{1,2})?$/', strtoupper(trim($contract)), $m)) {
        $r = shot_root(SYNC_CQG[$m[1]] ?? $m[1]);
        if ($r !== null) return [$r, false];
        return [$m[1], true];
    }
    $r = shot_root($contract);
    if ($r !== null) return [$r, false];
    $s = strtoupper(trim($contract));
    $s = preg_replace('/\s+\d{1,2}-\d{2,4}$/', '', $s);          // NinjaTrader « ZC 12-26 »
    $s = preg_replace('/[FGHJKMNQUVXZ]\d{1,2}$/', '', $s);        // « ZCZ6 »
    return [$s !== '' ? $s : '?', true];
}

/** UTC milliseconds → [Y-m-d, H:i:s] at New York time */
function sync_ny(int $ms): array
{
    static $ny = null; $ny ??= new DateTimeZone('America/New_York');
    $d = (new DateTimeImmutable('@' . intdiv($ms, 1000)))->setTimezone($ny);
    return [$d->format('Y-m-d'), $d->format('H:i:s')];
}

/** one fill as sent by a platform → a clean fill, or null when it cannot be used */
function sync_fill(array $f): ?array
{
    $id = trim((string) ($f['id'] ?? '')); $acct = trim((string) ($f['acct'] ?? '')); $contract = strtoupper(trim((string) ($f['contract'] ?? '')));
    $side = $f['side'] ?? null;
    $side = $side === 1 || $side === 'buy' || $side === 'BUY' ? 1 : ($side === -1 || $side === 'sell' || $side === 'SELL' ? -1 : 0);
    $qty = is_numeric($f['qty'] ?? null) ? (int) $f['qty'] : 0;
    $px = is_numeric($f['price'] ?? null) ? (float) $f['price'] : NAN;
    $ts = is_numeric($f['ts'] ?? null) ? (int) $f['ts'] : 0;
    if ($id === '' || $acct === '' || $contract === '' || !$side || $qty <= 0 || (float) $qty != (float) $f['qty'] || !is_finite($px) || $ts <= 0) return null;
    $num = fn($v) => is_numeric($v) && is_finite((float) $v) ? (float) $v : null;
    return ['id' => $id, 'acct' => $acct, 'contract' => $contract, 'side' => $side, 'qty' => $qty, 'price' => $px, 'ts' => $ts,
        'fee' => $num($f['fee'] ?? null), 'pv' => ($pv = $num($f['point_value'] ?? null)) !== null && $pv > 0 ? $pv : null, 'removed' => !empty($f['removed'])];
}

/**
 * fills → trades.
 * $fills: [{id, acct, contract, side (buy|sell or 1|-1), qty, price, ts (UTC ms), fee ($, optional), point_value (optional), removed (optional)}]
 *   - id: the platform's execution id (unique within its account); acct: a stable key of the platform account;
 *   - the same id sent again replaces the earlier one (an amended execution); removed: true withdraws it.
 * $o: accounts => [acct => ['account_id' => Sweep account id, 'fee_rt_c' => round-trip commission per contract]], source => platform.
 * Returns:
 *   trades: closed trades (doc fields of SYNC_TRADE_FIELDS + id, account_id, acct), oldest first;
 *   open: positions not back to flat yet: [acct|contract => {acct, contract, net, fills: [ids]}];
 *   fill_trades: [acct\nfill id => [trade ids]] (a reversal fill belongs to two trades);
 *   skipped: fills that could not be used (missing or invalid fields).
 */
function sync_build(array $fills, array $o = []): array
{
    $accts = (array) ($o['accounts'] ?? []); $source = (string) ($o['source'] ?? 'sync');
    // clean, one per (account, id): the last one sent wins; a removed execution is left out
    $byKey = []; $skipped = 0;
    foreach ($fills as $raw) {
        $f = is_array($raw) ? sync_fill($raw) : null;
        if (!$f) { $skipped++; continue; }
        $byKey[$f['acct'] . "\n" . $f['id']] = $f;
    }
    $clean = array_values(array_filter($byKey, fn($f) => !$f['removed']));
    // time order; same millisecond → the execution id decides, so the order never depends on how the fills arrived
    usort($clean, fn($a, $b) => [$a['acct'], $a['contract'], $a['ts'], $a['id']] <=> [$b['acct'], $b['contract'], $b['ts'], $b['id']]);

    $trades = []; $open = []; $fillTrades = []; $pos = [];
    $start = function (array $f) { return ['acct' => $f['acct'], 'contract' => $f['contract'], 'dir' => $f['side'], 'net' => 0, 'max' => 0,
        'buyN' => 0.0, 'sellN' => 0.0, 'eq' => 0, 'ew' => 0.0, 'xq' => 0, 'xw' => 0.0, 'fee' => 0.0, 'first' => $f, 'last' => $f, 'pv' => null, 'execs' => [], 'ids' => []]; };
    $leg = function (array &$st, array $f, int $q) {
        $px = $f['price'];
        if ($f['side'] > 0) $st['buyN'] += $px * $q; else $st['sellN'] += $px * $q;
        if ($f['side'] === $st['dir']) { $st['eq'] += $q; $st['ew'] += $px * $q; } else { $st['xq'] += $q; $st['xw'] += $px * $q; }
        if ($f['fee'] !== null) $st['fee'] += abs($f['fee']) * ($q / $f['qty']);
        $st['pv'] ??= $f['pv'];
        [$d, $t] = sync_ny($f['ts']);
        $st['execs'][] = ['id' => $f['id'], 'side' => $f['side'] > 0 ? 'buy' : 'sell', 'qty' => $q, 'price' => $px, 't' => $d . ' ' . $t];
        $st['ids'][$f['id']] = true; $st['last'] = $f;
    };
    $close = function (array $st) use (&$trades, &$fillTrades, $accts, $source) {
        [$root] = sync_root($st['contract']);
        $acc = (array) ($accts[$st['acct']] ?? []);
        $pv = $st['pv'] ?? (shot_spec($root)[1] ?? null);
        [$d0, $t0] = sync_ny($st['first']['ts']); [, $t1] = sync_ny($st['last']['ts']);
        $id = 'sy-' . substr(sha1($st['acct'] . "\n" . $st['first']['id']), 0, 24);
        $t = ['id' => $id, 'acct' => $st['acct'], 'account_id' => (string) ($acc['account_id'] ?? ''), 'source' => $source,
            'import_key' => 'sync:' . $st['acct'] . ':' . $st['first']['id'],
            'instrument' => $root, 'date' => shot_session($d0, $t0), 'session_date' => true,
            'entry_time' => substr($t0, 0, 5), 'exit_time' => substr($t1, 0, 5), 'session' => sync_session_name($t0),
            'direction' => $st['dir'] > 0 ? 'long' : 'short', 'contracts' => $st['max'],
            'entry' => round($st['ew'] / $st['eq'], 6), 'exit' => round($st['xw'] / $st['xq'], 6),
            'duration_s' => max(0, (int) round(($st['last']['ts'] - $st['first']['ts']) / 1000)), 'executions' => $st['execs']];
        if ($pv !== null) { $t['pnl_c'] = (int) round(($st['sellN'] - $st['buyN']) * $pv * 100); $t['pnl_manual'] = false; }
        else { $t['pnl_c'] = 0; $t['pnl_manual'] = true; $t['pnl_check'] = true; }   // no point value: the trader types the P&L
        $fees = (int) round($st['fee'] * 100); $feeRt = (int) ($acc['fee_rt_c'] ?? 0);
        if ($fees > 0) $t['fees_c'] = $fees;
        elseif ($feeRt > 0) { $t['fees_c'] = $feeRt * $st['eq']; $t['fees_auto'] = true; }   // a round trip per contract bought and sold
        else $t['fees_c'] = 0;
        $trades[] = [$st['first']['ts'], $t];
        foreach (array_keys($st['ids']) as $fid) $fillTrades[$st['acct'] . "\n" . $fid][] = $id;
    };

    foreach ($clean as $f) {
        $k = $f['acct'] . "\n" . $f['contract'];
        $left = $f['qty'];
        while ($left > 0) {
            $st = $pos[$k] ?? $start($f);
            if ($st['net'] === 0) $st = $start($f);
            if ($f['side'] === $st['dir']) {                       // opening or adding
                $leg($st, $f, $left); $st['net'] += $left; $st['max'] = max($st['max'], $st['net']); $left = 0;
                $pos[$k] = $st; break;
            }
            $q = min($left, $st['net']);                            // reducing or closing
            $leg($st, $f, $q); $st['net'] -= $q; $left -= $q;
            if ($st['net'] === 0) { $close($st); unset($pos[$k]); }   // flat: the trade is done; what is left of the fill opens the next one
            else $pos[$k] = $st;
        }
    }
    foreach ($pos as $st) $open[$st['acct'] . '|' . $st['contract']] = ['acct' => $st['acct'], 'contract' => $st['contract'], 'net' => $st['net'] * $st['dir'], 'fills' => array_keys($st['ids'])];
    usort($trades, fn($a, $b) => [$a[0], $a[1]['acct'], $a[1]['id']] <=> [$b[0], $b[1]['acct'], $b[1]['id']]);   // oldest first (UTC: no DST ambiguity)
    return ['trades' => array_column($trades, 1), 'open' => $open, 'fill_trades' => $fillTrades, 'skipped' => $skipped];
}

/**
 * the same trade taken on several accounts (copy trading) → one copy group, as the CSV import does: same entry minute
 * (New York), instrument and direction, on at least two accounts. The id comes from that signature, so it never changes
 * from one pass to the next. Two such trades on one account in the same minute: the 1st of each account go together,
 * then the 2nd… Returns the trades with copy_group set on the grouped ones.
 */
function sync_copy_groups(array $trades): array
{
    $sig = [];
    foreach ($trades as $i => $t) {
        $s = substr((string) ($t['executions'][0]['t'] ?? ''), 0, 16) . '|' . ($t['instrument'] ?? '') . '|' . ($t['direction'] ?? '');
        $sig[$s][(string) ($t['acct'] ?? '')][] = $i;
    }
    foreach ($sig as $s => $byAcct) {
        if (count($byAcct) < 2) continue;
        foreach ($byAcct as &$list) usort($list, fn($a, $b) => [$trades[$a]['executions'][0]['t'], $trades[$a]['id']] <=> [$trades[$b]['executions'][0]['t'], $trades[$b]['id']]);
        unset($list);
        $depth = max(array_map('count', $byAcct));
        for ($n = 0; $n < $depth; $n++) {
            $grp = []; foreach ($byAcct as $list) if (isset($list[$n])) $grp[] = $list[$n];
            if (count($grp) < 2) continue;
            $cg = 'cg-' . substr(sha1($s . '#' . $n), 0, 20);
            foreach ($grp as $i) $trades[$i]['copy_group'] = $cg;
        }
    }
    return $trades;
}
