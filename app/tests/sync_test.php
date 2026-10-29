<?php
/** Sweep — automatic sync: executions → trades (flat to flat, P&L, fees, New York sessions, ids, copy groups).
 *  php tests/sync_test.php */
declare(strict_types=1);
require __DIR__ . '/../sync/sync-engine.php';
$n = 0; $f = 0;
function ok($c, $what) { global $n, $f; $n++; if (!$c) $f++; echo ($c ? 'ok   ' : 'FAIL ') . $what . "\n"; }
// a New York wall clock → UTC milliseconds (what the platforms send)
$T = fn(string $ny, int $ms = 0) => (new DateTimeImmutable($ny, new DateTimeZone('America/New_York')))->getTimestamp() * 1000 + $ms;
$U = fn(string $utc) => (new DateTimeImmutable($utc, new DateTimeZone('UTC')))->getTimestamp() * 1000;
$F = fn(string $id, string $side, int $qty, float $px, int $ts, array $x = []) => $x + ['id' => $id, 'acct' => 'APEX-1', 'contract' => 'NQ 12-26', 'side' => $side, 'qty' => $qty, 'price' => $px, 'ts' => $ts];
$B = fn(array $fills, array $o = []) => sync_build($fills, $o + ['source' => 'ninjatrader']);

// contracts → the app's instruments
ok(sync_root('MNQ 12-26') === ['MNQ', false] && sync_root('MNQZ6') === ['MNQ', false] && sync_root('ES 03-27') === ['ES', false] && sync_root('MGC 02-27') === ['MGC', false], 'contracts: « MNQ 12-26 », « MNQZ6 », « ES 03-27 », « MGC 02-27 » → MNQ, MNQ, ES, MGC');
ok(sync_root('ZC 12-26') === ['ZC', true] && sync_root('ZCZ6') === ['ZC', true], 'a contract the app does not know keeps its root (ZC), marked unknown');
// ProjectX (TopstepX through Quantower, 29 Oct.): CQG roots in « CON.F.US.<root>.<month> »
ok(sync_root('CON.F.US.MNQ.Z25') === ['MNQ', false] && sync_root('CON.F.US.ENQ.H26') === ['NQ', false] && sync_root('CON.F.US.EP.Z25') === ['ES', false] && sync_root('F.US.MES') === ['MES', false] && sync_root('CON.F.US.GCE.Z25') === ['GC', false],
   'ProjectX names: « CON.F.US.MNQ.Z25 » → MNQ, ENQ → NQ, EP → ES, « F.US.MES » → MES, GCE → GC');
ok(sync_root('CON.F.US.ZZZ.Z25') === ['ZZZ', true], 'a ProjectX root the app does not know: its root, marked unknown (Admin › Sync lists it)');

// 1. scale-in and partial exits → ONE trade
$r = $B([
    $F('e1', 'buy', 1, 21000, $T('2026-10-07 10:00:00')), $F('e2', 'buy', 1, 20990, $T('2026-10-07 10:01:00')),
    $F('e3', 'sell', 1, 21010, $T('2026-10-07 10:05:00')), $F('e4', 'sell', 1, 21020, $T('2026-10-07 10:09:00')),
]);
$t = $r['trades'][0] ?? [];
ok(count($r['trades']) === 1 && $t['direction'] === 'long' && $t['contracts'] === 2 && $t['entry'] == 20995 && $t['exit'] == 21015 && count($t['executions']) === 4 && !$r['open'], 'scale-in + partial exits → one long trade of 2 contracts, average entry 20,995 / exit 21,015, 4 executions');
ok($t['pnl_c'] === 80000 && $t['pnl_manual'] === false && empty($t['pnl_check']) && $t['fees_c'] === 0 && empty($t['fees_auto']), 'P&L (21,015 − 20,995) × 2 × $20 = +$800, computed (not typed), no fees known');
ok($t['date'] === '2026-10-07' && $t['session_date'] === true && $t['entry_time'] === '10:00' && $t['exit_time'] === '10:09' && $t['session'] === 'nyam' && $t['duration_s'] === 540 && $t['instrument'] === 'NQ', 'New York times 10:00 → 10:09, session NY AM, 9 min, instrument NQ');
ok($t['executions'][0] === ['id' => 'e1', 'side' => 'buy', 'qty' => 1, 'price' => 21000.0, 't' => '2026-10-07 10:00:00'] && $t['executions'][3]['side'] === 'sell', 'executions in the app\'s format (id, side, qty, price, New York time)');
ok($t['id'] === 'sy-' . substr(sha1("APEX-1\ne1"), 0, 24) && $t['import_key'] === 'sync:APEX-1:e1' && $t['source'] === 'ninjatrader' && $t['acct'] === 'APEX-1', 'id and import key from the account and the first fill; source = the platform');
ok(preg_match('/^[A-Za-z0-9_.:@+~-]{1,120}$/', $t['id']) === 1, 'the id is a valid document id for the API');

// 2. in, out, in again before flat → still one trade; contracts = the largest position; fees on every contract bought and sold
$r = $B([
    $F('a', 'buy', 2, 100, $T('2026-10-07 11:00:00')), $F('b', 'sell', 1, 102, $T('2026-10-07 11:01:00')),
    $F('c', 'buy', 1, 101, $T('2026-10-07 11:02:00')), $F('d', 'sell', 2, 104, $T('2026-10-07 11:03:00')),
], ['accounts' => ['APEX-1' => ['account_id' => 'acc9', 'fee_rt_c' => 400]]]);
$t = $r['trades'][0] ?? [];
ok(count($r['trades']) === 1 && $t['contracts'] === 2 && abs($t['entry'] - 301 / 3) < 1e-6 && abs($t['exit'] - 310 / 3) < 1e-6, 'buy 2, sell 1, buy 1, sell 2 → one trade, contracts 2 (largest position), weighted averages');
ok($t['pnl_c'] === (int) round(((102 + 208) - (200 + 101)) * 20 * 100) && $t['fees_c'] === 1200 && $t['fees_auto'] === true && $t['account_id'] === 'acc9', 'P&L = sells − buys; no commission in the fills → $4 × 3 contracts round trip = $12 (fees_auto); Sweep account from the map');

// 3. reversal: long 2 → short 1 in one fill
$r = $B([
    $F('r1', 'buy', 2, 21000, $T('2026-10-07 11:00:00'), ['contract' => 'MNQ 12-26', 'fee' => 1.0]),
    $F('r2', 'sell', 3, 21010, $T('2026-10-07 11:02:00'), ['contract' => 'MNQ 12-26', 'fee' => 1.5]),
    $F('r3', 'buy', 1, 21005, $T('2026-10-07 11:04:00'), ['contract' => 'MNQ 12-26', 'fee' => 0.5]),
]);
[$a, $b] = $r['trades'] + [null, null];
ok(count($r['trades']) === 2 && $a['direction'] === 'long' && $a['contracts'] === 2 && $a['pnl_c'] === 4000 && $b['direction'] === 'short' && $b['contracts'] === 1 && $b['pnl_c'] === 1000, 'reversal: long 2 closed (+$40), short 1 opened by the same fill and closed (+$10)');
ok($a['executions'][1]['qty'] === 2 && $b['executions'][0]['qty'] === 1 && $b['executions'][0]['id'] === 'r2' && $a['id'] !== $b['id'] && $r['fill_trades']["APEX-1\nr2"] === [$a['id'], $b['id']], 'the reversal fill is split 2 / 1 and belongs to both trades');
ok($a['fees_c'] === 200 && $b['fees_c'] === 100 && empty($a['fees_auto']), 'commissions from the fills, the reversal fill\'s split in proportion ($1 + $1 / $0.50 + $0.50)');

// 4. a position still open is not a trade
$r = $B([$F('o1', 'sell', 1, 5800, $T('2026-10-07 12:00:00'), ['contract' => 'ES 12-26']), $F('o2', 'sell', 1, 5801, $T('2026-10-07 12:01:00'), ['contract' => 'ES 12-26'])]);
ok(!$r['trades'] && ($r['open']['APEX-1|ES 12-26']['net'] ?? 0) === -2 && $r['open']['APEX-1|ES 12-26']['fills'] === ['o1', 'o2'], 'short 2 still open → no trade; the open position keeps its fills');

// 5. the same fills, sent twice or in another order → exactly the same trades
$set = [
    $F('x1', 'buy', 1, 21000, $T('2026-10-07 09:31:00')), $F('x2', 'sell', 1, 21004, $T('2026-10-07 09:33:00')),
    $F('x3', 'sell', 2, 21002, $T('2026-10-07 09:40:00')), $F('x4', 'buy', 2, 20998, $T('2026-10-07 09:45:00')),
];
$one = $B($set); $rev = $B(array_reverse($set)); $dup = $B(array_merge($set, $set, [$set[1]]));
ok(json_encode($one) === json_encode($rev) && json_encode($one) === json_encode($dup) && count($one['trades']) === 2, 'replayed, duplicated or out-of-order fills → the same 2 trades, same ids');

// 6. same millisecond: the execution id decides, never the arrival order
$same = [$F('m1', 'buy', 1, 100, $T('2026-10-07 10:00:00')), $F('m2', 'sell', 1, 101, $T('2026-10-07 10:00:00'))];
ok(json_encode($B($same)) === json_encode($B(array_reverse($same))) && count($B($same)['trades']) === 1, 'two fills in the same millisecond: same result whatever the order they arrive in');

// 7. an amended execution replaces the first one; a removed one is left out
$r = $B([$F('k1', 'buy', 1, 100, $T('2026-10-07 10:00:00')), $F('k2', 'sell', 1, 101, $T('2026-10-07 10:05:00')), $F('k2', 'sell', 1, 103, $T('2026-10-07 10:05:00'))]);
ok(count($r['trades']) === 1 && $r['trades'][0]['exit'] == 103 && $r['trades'][0]['pnl_c'] === 6000 && count($r['trades'][0]['executions']) === 2, 'amended execution (same id sent again) → the new price wins, no extra execution');
$r = $B([$F('k1', 'buy', 1, 100, $T('2026-10-07 10:00:00')), $F('k2', 'sell', 1, 101, $T('2026-10-07 10:05:00')), $F('k2', 'sell', 1, 101, $T('2026-10-07 10:05:00'), ['removed' => true])]);
ok(!$r['trades'] && ($r['open']['APEX-1|NQ 12-26']['net'] ?? 0) === 1, 'removed execution → the exit is gone, the position is open again (no trade)');

// 8. the 18:00 ET rule, the Sunday open and the clock changes
$day = fn(string $utcIn, string $utcOut) => $B([$F('s1', 'buy', 1, 100, $U($utcIn)), $F('s2', 'sell', 1, 101, $U($utcOut))])['trades'][0];
$t = $day('2026-10-07 21:59:00', '2026-10-07 22:10:00');   // 17:59 EDT
ok($t['date'] === '2026-10-07' && $t['entry_time'] === '17:59' && $t['session'] === 'other', '17:59 ET → still the session of the 7th');
$t = $day('2026-10-07 22:01:00', '2026-10-07 22:30:00');   // 18:01 EDT
ok($t['date'] === '2026-10-08' && $t['entry_time'] === '18:01' && $t['session'] === 'asia' && $t['executions'][0]['t'] === '2026-10-07 18:01:00', '18:01 ET → session of the 8th, the execution keeps its real time (7th, 18:01)');
$t = $day('2026-10-11 22:05:00', '2026-10-11 22:20:00');   // Sunday 18:05 EDT
ok($t['date'] === '2026-10-12', 'Sunday 18:05 ET (market open) → Monday\'s session');
$t = $day('2026-03-08 22:00:00', '2026-03-08 22:15:00');   // the day the clocks spring forward: 18:00 EDT (17:00 if read as EST)
ok($t['date'] === '2026-03-09' && $t['entry_time'] === '18:00', 'clocks forward (8 Mar 2026): 22:00 UTC = 18:00 ET → next session');
$t = $day('2026-11-02 14:30:00', '2026-11-02 14:45:00');   // Monday after the clocks fall back: 09:30 EST
$t2 = $day('2026-10-30 13:30:00', '2026-10-30 13:45:00');  // Friday before: 09:30 EDT
ok($t['entry_time'] === '09:30' && $t2['entry_time'] === '09:30' && $t['date'] === '2026-11-02' && $t2['date'] === '2026-10-30', 'clocks back (1 Nov 2026): the open is 09:30 ET before and after');
$r = $B([$F('d1', 'buy', 1, 100, $U('2026-11-01 05:30:00')), $F('d2', 'sell', 1, 101, $U('2026-11-01 06:10:00')), $F('d3', 'buy', 1, 100, $U('2026-11-01 06:20:00')), $F('d4', 'sell', 1, 102, $U('2026-11-01 06:25:00'))]);
ok(count($r['trades']) === 2 && $r['trades'][0]['id'] === 'sy-' . substr(sha1("APEX-1\nd1"), 0, 24) && $r['trades'][0]['entry_time'] === '01:30' && $r['trades'][1]['entry_time'] === '01:20', 'the hour that happens twice (1 Nov, 01:00-02:00 ET): trades stay in real order (01:30 EDT before 01:20 EST)');

// 9. P&L: short, the platform's point value, unknown contracts
$r = $B([$F('p1', 'sell', 3, 5800.25, $T('2026-10-07 10:00:00'), ['contract' => 'MES 12-26']), $F('p2', 'buy', 3, 5797.75, $T('2026-10-07 10:20:00'), ['contract' => 'MES 12-26'])]);
ok($r['trades'][0]['direction'] === 'short' && $r['trades'][0]['pnl_c'] === 3750, 'short MES 3 × 2.5 points × $5 = +$37.50');
$r = $B([$F('p3', 'buy', 1, 450.25, $T('2026-10-07 10:00:00'), ['contract' => 'ZC 12-26']), $F('p4', 'sell', 1, 451, $T('2026-10-07 10:20:00'), ['contract' => 'ZC 12-26'])]);
ok($r['trades'][0]['instrument'] === 'ZC' && $r['trades'][0]['pnl_c'] === 0 && $r['trades'][0]['pnl_check'] === true && $r['trades'][0]['pnl_manual'] === true, 'unknown contract with no point value → P&L $0 « To check », never priced as NQ');
$r = $B([$F('p5', 'buy', 1, 450.25, $T('2026-10-07 10:00:00'), ['contract' => 'ZC 12-26', 'point_value' => 50]), $F('p6', 'sell', 1, 451, $T('2026-10-07 10:20:00'), ['contract' => 'ZC 12-26', 'point_value' => 50])]);
ok($r['trades'][0]['pnl_c'] === 3750 && empty($r['trades'][0]['pnl_check']), 'unknown to the app but the platform sends $50/point → P&L computed (+$37.50)');
$r = $B([$F('p7', 'buy', 1, 1.08525, $T('2026-10-07 10:00:00'), ['contract' => '6E 12-26']), $F('p8', 'sell', 1, 1.0855, $T('2026-10-07 10:20:00'), ['contract' => '6E 12-26'])]);
ok($r['trades'][0]['entry'] == 1.08525 && $r['trades'][0]['pnl_c'] === 3125, '6E keeps its 5 decimals; 0.00025 × $125,000 = +$31.25');

// 10. fees: commissions in the fills win; all zero → the account's commission (same rule as the CSV import)
$r = $B([$F('f1', 'buy', 2, 100, $T('2026-10-07 10:00:00'), ['fee' => 1.24]), $F('f2', 'sell', 2, 101, $T('2026-10-07 10:05:00'), ['fee' => 1.24])], ['accounts' => ['APEX-1' => ['fee_rt_c' => 400]]]);
ok($r['trades'][0]['fees_c'] === 248 && empty($r['trades'][0]['fees_auto']), 'commissions sent by the platform ($1.24 + $1.24) win over the account\'s rate');
$r = $B([$F('f3', 'buy', 2, 100, $T('2026-10-07 10:00:00'), ['fee' => 0]), $F('f4', 'sell', 2, 101, $T('2026-10-07 10:05:00'), ['fee' => 0])], ['accounts' => ['APEX-1' => ['fee_rt_c' => 400]]]);
ok($r['trades'][0]['fees_c'] === 800 && $r['trades'][0]['fees_auto'] === true, 'commissions all $0 → the account\'s $4 round trip × 2 = $8 (fees_auto)');

// 11. positions are per account and per contract month
$r = $B([$F('g1', 'buy', 1, 21000, $T('2026-10-07 10:00:00'), ['contract' => 'MNQ 12-26']), $F('g2', 'sell', 1, 21100, $T('2026-10-07 10:01:00'), ['contract' => 'MNQ 03-27'])]);
ok(!$r['trades'] && count($r['open']) === 2, 'rollover: buy MNQ 12-26 and sell MNQ 03-27 are two open positions, never one trade');
$r = $B([$F('h1', 'buy', 1, 100, $T('2026-10-07 10:00:00')), $F('h2', 'sell', 1, 101, $T('2026-10-07 10:01:00'), ['acct' => 'APEX-2'])]);
ok(!$r['trades'] && count($r['open']) === 2, 'two accounts never close each other\'s positions');

// 12. copy trading: the same trade on several accounts → one copy group
$cp = [];
foreach (['APEX-1', 'APEX-2', 'LUCID-7'] as $k => $acct) {
    $cp[] = $F("c$k-in", 'buy', 1, 21000, $T('2026-10-07 10:00:05', 40 * $k), ['acct' => $acct]);
    $cp[] = $F("c$k-out", 'sell', 1, 21010, $T('2026-10-07 10:03:00', 40 * $k), ['acct' => $acct]);
}
$cp[] = $F('lone-in', 'buy', 1, 21000, $T('2026-10-07 10:07:00'), ['acct' => 'APEX-2']); $cp[] = $F('lone-out', 'sell', 1, 21003, $T('2026-10-07 10:09:00'), ['acct' => 'APEX-2']);
$g = sync_copy_groups($B($cp)['trades']);
$groups = array_values(array_unique(array_filter(array_column($g, 'copy_group'))));
$lone = array_values(array_filter($g, fn($t) => $t['executions'][0]['id'] === 'lone-in'))[0];
ok(count($groups) === 1 && count(array_filter($g, fn($t) => ($t['copy_group'] ?? '') === $groups[0])) === 3 && !isset($lone['copy_group']), 'same minute, instrument and side on 3 accounts → one copy group of 3; the trade alone stays alone');
ok($groups[0] === array_values(array_unique(array_filter(array_column(sync_copy_groups($B(array_reverse($cp))['trades']), 'copy_group'))))[0], 'the copy group id is the same on every pass');
$two = [];
foreach (['APEX-1', 'APEX-2'] as $acct) foreach ([0, 1] as $i) {
    $two[] = $F("$acct-$i-in", 'buy', 1, 100, $T('2026-10-07 10:00:10', $i * 20000), ['acct' => $acct]);
    $two[] = $F("$acct-$i-out", 'sell', 1, 101, $T('2026-10-07 10:00:15', $i * 20000), ['acct' => $acct]);
}
$g = sync_copy_groups($B($two)['trades']);
$byGroup = []; foreach ($g as $t) $byGroup[$t['copy_group'] ?? ''][] = $t['acct'];
ok(count($byGroup) === 2 && !isset($byGroup['']) && array_map(fn($a) => count(array_unique($a)), array_values($byGroup)) === [2, 2], 'two trades per account in the same minute → two groups, one trade per account in each');

// 13. unusable fills are skipped, never guessed
$r = $B([
    ['acct' => 'A', 'contract' => 'NQ 12-26', 'side' => 'buy', 'qty' => 1, 'price' => 1, 'ts' => 1],   // no id
    $F('v2', 'buy', 0, 100, $T('2026-10-07 10:00:00')), $F('v3', 'buy', 1, 100, $T('2026-10-07 10:00:00'), ['qty' => 1.5]),
    $F('v4', 'hold', 1, 100, $T('2026-10-07 10:00:00')), $F('v5', 'buy', 1, 100, 0), $F('v6', 'buy', 1, 100, $T('2026-10-07 10:00:00'), ['price' => 'abc']),
    'not a fill',
]);
ok($r['skipped'] === 7 && !$r['trades'] && !$r['open'], 'fills with no id, no quantity, half a contract, an unknown side, no time, no price or not an object → skipped (7)');

echo "\n" . ($f ? "$f failed" : "$n/$n passed") . "\n"; exit($f ? 1 : 0);
