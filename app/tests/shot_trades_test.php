<?php
/** Sweep — several trades from one screenshot: the server-side construction (FIFO, P&L, fees, time zone, session).
 *  php tests/shot_trades_test.php */
declare(strict_types=1);
if (!defined('SAI_INSTRUMENTS')) {   // the contract table (same as ai/ai-stats.php), without loading the AI module
    $src = file_get_contents(__DIR__ . '/../ai/ai-stats.php');
    preg_match('/const SAI_INSTRUMENTS = \[(.*?)\];/s', $src, $m); eval('const SAI_INSTRUMENTS = [' . $m[1] . '];');
}
require __DIR__ . '/../ai/shot-trades.php';
$n = 0; $f = 0; $k = 0;
$id = function ($p) use (&$k) { return $p . (++$k); };
function ok($c, $what) { global $n, $f; $n++; if (!$c) $f++; echo ($c ? 'ok   ' : 'FAIL ') . $what . "\n"; }
$B = fn($rows, $type = 'fills', $o = []) => shot_build(['source_type' => $type, 'rows' => $rows], $o + ['tz' => 'America/New_York', 'date' => '2026-10-07', 'id' => $id]);
// symbols
ok(shot_root('MNQZ6') === 'MNQ' && shot_root('MNQ 12-26') === 'MNQ' && shot_root('/MNQ') === 'MNQ' && shot_root('CME_MINI:NQZ2026') === 'NQ' && shot_root('ESZ6') === 'ES' && shot_root('MES 12-26') === 'MES' && shot_root('XYZ') === null, 'symbols normalized (MNQZ6, MNQ 12-26, /MNQ, CME_MINI:NQZ2026 …), unknown → null');
// 1. scale-in and partial exits → one trade, weighted averages
$r = $B([
  ['symbol' => 'NQZ6', 'side' => 'buy', 'qty' => 1, 'price' => 21000, 'datetime' => '2026-10-07 10:00:00'],
  ['symbol' => 'NQZ6', 'side' => 'buy', 'qty' => 1, 'price' => 20990, 'datetime' => '2026-10-07 10:01:00'],
  ['symbol' => 'NQZ6', 'side' => 'sell', 'qty' => 1, 'price' => 21010, 'datetime' => '2026-10-07 10:05:00'],
  ['symbol' => 'NQZ6', 'side' => 'sell', 'qty' => 1, 'price' => 21020, 'datetime' => '2026-10-07 10:09:00'],
]);
$t = $r['trades'][0] ?? [];
ok(count($r['trades']) === 1 && $t['direction'] === 'long' && $t['contracts'] === 2 && $t['entry'] == 20995 && $t['exit'] == 21015 && count($t['executions']) === 4, 'scale-in + partial exits → ONE trade, 4 executions, average entry 20,995 / exit 21,015');
ok($t['pnl_c'] === 80000 && $t['entry_time'] === '10:00' && $t['exit_time'] === '10:09', 'P&L (21,015 − 20,995) × 2 × $20 = +$800');
// 2. reversal long 2 → short 1 in one fill
$r = $B([
  ['symbol' => 'MNQ', 'side' => 'buy', 'qty' => 2, 'price' => 21000, 'datetime' => '2026-10-07 11:00:00'],
  ['symbol' => 'MNQ', 'side' => 'sell', 'qty' => 3, 'price' => 21010, 'datetime' => '2026-10-07 11:02:00'],
  ['symbol' => 'MNQ', 'side' => 'buy', 'qty' => 1, 'price' => 21005, 'datetime' => '2026-10-07 11:04:00'],
]);
ok(count($r['trades']) === 2 && $r['trades'][0]['direction'] === 'long' && $r['trades'][0]['pnl_c'] === 4000 && $r['trades'][1]['direction'] === 'short' && $r['trades'][1]['contracts'] === 1 && $r['trades'][1]['pnl_c'] === 1000, 'reversal: long 2 closed (+$40), short 1 opened by the same fill (+$10)');
// 3. open at the end
$r = $B([['symbol' => 'ES', 'side' => 'sell', 'qty' => 1, 'price' => 5800, 'datetime' => '2026-10-07 12:00:00']]);
ok(count($r['trades']) === 1 && $r['trades'][0]['open'] && $r['open'] === 1, 'a position still open → « Open — to complete »');
// 4. several symbols mixed, micro vs mini, shorts
$r = $B([
  ['symbol' => 'NQZ6', 'side' => 'sell', 'qty' => 1, 'price' => 21000, 'datetime' => '2026-10-07 09:31:00'],
  ['symbol' => 'MNQZ6', 'side' => 'sell', 'qty' => 5, 'price' => 21000, 'datetime' => '2026-10-07 09:32:00'],
  ['symbol' => 'NQZ6', 'side' => 'buy', 'qty' => 1, 'price' => 20990, 'datetime' => '2026-10-07 09:40:00'],
  ['symbol' => 'MNQZ6', 'side' => 'buy', 'qty' => 5, 'price' => 20990, 'datetime' => '2026-10-07 09:41:00'],
]);
$by = []; foreach ($r['trades'] as $t) $by[$t['instrument']] = $t;
ok(count($r['trades']) === 2 && $by['NQ']['pnl_c'] === 20000 && $by['MNQ']['pnl_c'] === 10000 && $by['NQ']['direction'] === 'short', 'mixed NQ / MNQ shorts: NQ 1 × 10 pts = +$200, MNQ 5 × 10 pts = +$100');
// 5. P&L shown that differs → kept, « To check », both values
$r = $B([['symbol' => 'NQ', 'side' => 'long', 'qty' => 1, 'entry_price' => 21000, 'exit_price' => 21010, 'entry_time' => '2026-10-07 10:00', 'exit_time' => '2026-10-07 10:10', 'pnl_shown' => '250.00']], 'closed_trades');
$t = $r['trades'][0];
ok($t['pnl_c'] === 25000 && $t['pnl_calc_c'] === 20000 && $t['check'], 'P&L shown $250 ≠ computed $200 → the screenshot wins, « To check », both kept');
$r = $B([['symbol' => 'NQ', 'side' => 'long', 'qty' => 1, 'entry_price' => 21000, 'exit_price' => 21010, 'entry_time' => '2026-10-07 10:00', 'exit_time' => '2026-10-07 10:10', 'pnl_shown' => '205']], 'closed_trades');
ok($r['trades'][0]['pnl_c'] === 20000 && !$r['trades'][0]['check'], 'a difference within one tick × qty ($5) → the computed P&L, not to check');
// 6. fees: shown, else the account's commission per contract
$r = $B([['symbol' => 'NQ', 'side' => 'short', 'qty' => 2, 'entry_price' => 21010, 'exit_price' => 21000, 'entry_time' => '10:00', 'exit_time' => '10:05', 'commission_shown' => '8.40']], 'closed_trades');
ok($r['trades'][0]['fees_c'] === 840 && $r['trades'][0]['net_c'] === 40000 - 840, 'commissions shown: $8.40 → net = gross − fees');
$r = $B([['symbol' => 'NQ', 'side' => 'short', 'qty' => 2, 'entry_price' => 21010, 'exit_price' => 21000, 'entry_time' => '10:00', 'exit_time' => '10:05']], 'closed_trades', ['fee_rt_c' => 420]);
ok($r['trades'][0]['fees_c'] === 840 && !empty($r['trades'][0]['fees_auto']), 'no commission shown: the account’s $4.20 per contract × 2');
// 7. time zone CT → ET, session at 18:00 ET
$r = $B([['symbol' => 'ES', 'side' => 'buy', 'qty' => 1, 'price' => 5800, 'datetime' => '2026-10-07 09:00:00'], ['symbol' => 'ES', 'side' => 'sell', 'qty' => 1, 'price' => 5801, 'datetime' => '2026-10-07 09:05:00']], 'fills', ['tz' => 'America/Chicago']);
ok($r['trades'][0]['entry_time'] === '10:00' && $r['trades'][0]['date'] === '2026-10-07', '09:00 CT → 10:00 ET');
$r = $B([['symbol' => 'ES', 'side' => 'buy', 'qty' => 1, 'price' => 5800, 'datetime' => '2026-10-07 17:30:00'], ['symbol' => 'ES', 'side' => 'sell', 'qty' => 1, 'price' => 5801, 'datetime' => '2026-10-07 17:40:00']], 'fills', ['tz' => 'America/Chicago']);
ok($r['trades'][0]['entry_time'] === '18:30' && $r['trades'][0]['date'] === '2026-10-08' && $r['trades'][0]['executions'][0]['t'] === '2026-10-07 18:30:00', '17:30 CT = 18:30 ET → the next day’s session, executions keep the real clock time');
// 8. US formats, unknown symbols
$r = $B([['symbol' => 'MESZ6', 'side' => 'Buy', 'qty' => '1', 'price' => '5,800.25', 'datetime' => '10/07/2026 2:15:00 PM'], ['symbol' => 'MESZ6', 'side' => 'Sell', 'qty' => '1', 'price' => '5,801.25', 'datetime' => '10/07/2026 2:20:00 PM'], ['symbol' => 'ZZZ', 'side' => 'Buy', 'qty' => 1, 'price' => 1, 'datetime' => '10:00']]);
ok(count($r['trades']) === 1 && $r['trades'][0]['entry_time'] === '14:15' && $r['trades'][0]['pnl_c'] === 500 && $r['unknown'] === ['ZZZ'], 'US formats (5,800.25 · 2:15:00 PM), an unknown symbol is reported, never priced as NQ');
// ── tables copied as written (columns + cells) — Lucid / Tradovate-style trade lists ──
$TB = fn($cols, $table, $o = [], $extra = []) => shot_build(['source_type' => 'unknown', 'columns' => $cols, 'table' => $table] + $extra, $o + ['tz' => 'America/New_York', 'date' => '2026-10-07', 'id' => $id]);
$cols = ['Symbol', 'Side', 'Qty', 'Entry Price', 'Exit Price', 'Entry Time', 'Exit Time', 'Duration', 'P&L', 'Commission'];
$lucid = [   // newest first, as most dashboards show it
  ['MNQZ6', 'Short', '3', '21,040.25', '21,030.00', '10/07/2026 10:41:30 AM', '10/07/2026 10:44:02 AM', '2m 32s', '$61.50', '$1.86'],
  ['NQZ6', 'Long', '2', '21,010.25', '21,026.50', '10/07/2026 10:02:11 AM', '10/07/2026 10:09:05 AM', '6m 54s', '$650.00', '$8.40'],
  ['ESZ6', 'Long', '1', '5,812.25', '5,809.00', '10/07/2026 9:31:10 AM', '10/07/2026 9:38:48 AM', '7m 38s', '($162.50)', '$4.20'],
];
$r = $TB($cols, $lucid);
$by = []; foreach ($r['trades'] as $t) $by[$t['instrument']] = $t;
ok(count($r['trades']) === 3 && $r['type'] === 'closed_trades', 'a Lucid-style list (columns + cells) → 3 closed trades');
ok($by['MNQ']['direction'] === 'short' && $by['NQ']['direction'] === 'long' && $by['ES']['direction'] === 'long', 'directions as written (Short / Long)');
ok($by['ES']['entry_time'] === '09:31' && $by['ES']['exit_time'] === '09:38' && $by['NQ']['entry_time'] === '10:02' && $by['MNQ']['exit_time'] === '10:44', 'real entry and exit times (12 h AM, no 09:30 invented)');
ok($by['NQ']['pnl_c'] === 65000 && $by['NQ']['fees_c'] === 840 && $by['ES']['pnl_c'] === -16250 && $by['MNQ']['pnl_c'] === 6150 && !$by['NQ']['check'] && !$by['ES']['check'], 'P&L as computed = as shown (gross), commissions from their column, nothing « to check »');
ok($r['trades'][0]['instrument'] === 'ES', 'newest-first list → trades in time order');
// the side column shows the CLOSING order (Sell for a long): the prices and the P&L decide
$r = $TB(['Contract', 'B/S', 'Qty', 'Entry', 'Exit', 'Entered', 'Exited', 'Net P&L'], [
  ['NQZ6', 'Sell', '1', '21000.00', '21010.00', '2026-10-07 10:00:00', '2026-10-07 10:05:00', '191.60'],
  ['NQZ6', 'Buy', '1', '21020.00', '21005.00', '2026-10-07 11:00:00', '2026-10-07 11:05:00', '291.60'],
  ['NQZ6', 'Sell', '1', '21030.00', '21025.00', '2026-10-07 12:00:00', '2026-10-07 12:05:00', '-108.40'],   // this platform writes the minus of a loss
]);
ok($r['trades'][0]['direction'] === 'long' && $r['trades'][1]['direction'] === 'short' && !empty($r['trades'][0]['side_fixed']), 'a side column that shows the closing order: corrected by the prices and the P&L');
ok($r['trades'][0]['pnl_c'] === 20000 && $r['trades'][0]['fees_c'] === 840 && !empty($r['trades'][0]['fees_from_pnl']) && !$r['trades'][0]['check'], 'a net P&L column without commissions: the difference becomes the fees ($8.40), not « to check »');
// a loss shown only in red
$r = $TB(['Symbol', 'Side', 'Qty', 'Entry Price', 'Exit Price', 'Entry Time', 'Exit Time', 'P&L'], [['ESZ6', 'Long', '1', '5812.25', '5809.00', '09:31:10', '09:38:48', '162.50']], [], ['pnl_colors' => ['red'], 'date_shown' => 'Oct 6, 2026']);
ok($r['trades'][0]['pnl_c'] === -16250 && $r['trades'][0]['direction'] === 'long' && $r['trades'][0]['date'] === '2026-10-06', 'a loss shown only in red counts as a loss; times only + the date written above the table');
// day first (07/10/2026 = 7 October) decided for the whole table
$r = $TB(['Symbol', 'Side', 'Qty', 'Entry Price', 'Exit Price', 'Entry Time', 'Exit Time'], [['MES', 'Short', '2', '5820', '5816.25', '13/10/2026 15:02', '13/10/2026 15:09'], ['MES', 'Long', '1', '5800', '5801', '07/10/2026 14:00', '07/10/2026 14:05']], ['date' => '2026-10-13']);
ok($r['trades'][0]['date'] === '2026-10-07' && $r['trades'][1]['date'] === '2026-10-13', 'dates written day first (13/10, 07/10) read as day first for the whole table');
// unreadable time: never invented
$r = $TB(['Symbol', 'Side', 'Qty', 'Entry Price', 'Exit Price', 'Entry Time', 'Exit Time'], [['NQ', 'Long', '1', '21000', '21010', '', '']]);
ok($r['trades'][0]['entry_time'] === '' && $r['trades'][0]['check'] && in_array('time', $r['trades'][0]['why'], true), 'no time on the screenshot: left empty and « to check » (no 09:30)');
// fills table written as-is (Tradovate Orders)
$r = $TB(['Time', 'Contract', 'B/S', 'Filled Qty', 'Avg Fill Price', 'Status'], [['10/07/2026 10:09:05', 'NQZ6', 'S', '2', '21,026.50', 'Filled'], ['10/07/2026 10:03:40', 'NQZ6', 'B', '1', '21,008.00', 'Filled'], ['10/07/2026 10:02:11', 'NQZ6', 'B', '1', '21,012.25', 'Filled']]);
ok(count($r['trades']) === 1 && $r['type'] === 'fills' && $r['trades'][0]['pnl_c'] === 65500 && $r['trades'][0]['entry_time'] === '10:02', 'a fills table (newest first, B/S letters) → one trade, +$655');
// ISO times with Z, CT written in the cell
$r = $TB(['Symbol', 'Side', 'Qty', 'Entry Price', 'Exit Price', 'Entry Time', 'Exit Time'], [['NQ', 'Long', '1', '21000', '21004', '2026-10-07T14:00:00Z', '2026-10-07T14:03:00Z'], ['NQ', 'Short', '1', '21004', '21000', '10/07/2026 09:10 CT', '10/07/2026 09:12 CT']]);
ok($r['trades'][0]['entry_time'] === '10:00' && $r['trades'][1]['entry_time'] === '10:10', 'times in UTC (Z) or written in CT → New York');
// a Tradesea trade list (the screenshot of 2026-10-08): titles cut (« Instrum… »), « Open time / Close time », « Charges »,
// the date and the time in one cell with a comma, losses only in red, an evening trade
$cols = ['Broker', 'Account Name', 'Instrum…', 'Open time', 'Close time', 'Side', 'Quantity', 'Entry Price', 'Exit Price', 'Net P&L', 'Charges', 'Tags', ''];
$tbl = [
  ['Sandbox', 'Demo Account', 'GC', '2026-10-08, 1:05:31 PM', '2026-10-08, 1:14:00 PM', 'Long', '1', '$4,146.70', '$4,152.80', '$604.00', '$6.00', '', 'Details'],
  ['Sandbox', 'Demo Account', 'GC', '2026-10-08, 11:21:04 AM', '2026-10-08, 11:21:35 AM', 'Long', '1', '$4,143.30', '$4,142.20', '$116.00', '$6.00', '', 'Details'],
  ['Sandbox', 'Demo Account', 'GC', '2026-10-08, 11:05:09 AM', '2026-10-08, 11:08:09 AM', 'Short', '1', '$4,149.90', '$4,149.60', '$24.00', '$6.00', '', 'Details'],
  ['Sandbox', 'Demo Account', 'GC', '2026-10-08, 11:04:23 AM', '2026-10-08, 11:04:32 AM', 'Short', '1', '$4,150.10', '$4,150.40', '$36.00', '$6.00', '', 'Details'],
  ['Sandbox', 'Demo Account', 'GC', '2026-10-07, 8:38:36 PM', '2026-10-07, 9:00:13 PM', 'Short', '1', '$4,130.90', '$4,137.60', '$676.00', '$6.00', '', 'Details'],
];
$r = $TB($cols, $tbl, ['date' => '2026-10-08'], ['pnl_colors' => ['green', 'red', 'green', 'red', 'red']]);
$g = array_map(fn($t) => [$t['date'], $t['entry_time'], $t['exit_time'], $t['direction'], $t['pnl_c'], $t['fees_c'], $t['pnl_c'] - $t['fees_c'], $t['check']], $r['trades']);
ok(count($r['trades']) === 5, 'Tradesea list: 5 trades read (titles cut, Open time / Close time)');
ok($g === [
  ['2026-10-08', '11:04', '11:04', 'short', -3000, 600, -3600, false],
  ['2026-10-08', '11:05', '11:08', 'short', 3000, 600, 2400, false],
  ['2026-10-08', '11:21', '11:21', 'long', -11000, 600, -11600, false],
  ['2026-10-08', '13:05', '13:14', 'long', 61000, 600, 60400, false],
  ['2026-10-08', '20:38', '21:00', 'short', -67000, 600, -67600, false],
], 'every side, time, gross P&L, $6 charges and net P&L as on Tradesea; the 8:38 PM trade belongs to the next session; nothing « to check » (' . json_encode($g) . ')');
// the same list without the colours (a loss copied without its minus): the written side wins, the sign follows the prices
$r = $TB($cols, $tbl, ['date' => '2026-10-08']);
$g2 = array_map(fn($t) => [$t['direction'], $t['pnl_c'] - $t['fees_c'], $t['check']], $r['trades']);
ok($g2 === [['short', -3600, false], ['short', 2400, false], ['long', -11600, false], ['long', 60400, false], ['short', -67600, false]], 'without colours: sides as written, losses still losses (' . json_encode($g2) . ')');
// the symbol written outside the table (chart title, header): a single-trade page and an executions table without a symbol column
ok(shot_root('Gold (GCZ6) · 5 · COMEX') === 'GC' && shot_root('Micro Gold') === 'MGC' && shot_root('E-mini Nasdaq 100') === 'NQ' && shot_root('Micro E-mini Nasdaq-100') === 'MNQ' && shot_root('Crude Oil (CLX6)') === 'CL' && shot_root('MNQ 12-26') === 'MNQ' && shot_root('Demo Account') === null, 'contract names and codes in brackets (Gold (GCZ6) → GC, Micro Gold → MGC…), an account name is not a symbol');
$r = $TB(['Net P&L', 'Side', 'Lots', 'Entry', 'Exit', 'Open time', 'Close time', 'Total Charges'], [['$204.00', 'Long', '1', '$4,149.80', '$4,151.90', '2:51:12 PM', '3:05:05 PM', '$6.00']], [], ['pnl_colors' => ['green'], 'symbol_shown' => 'Gold (GCZ6) · 5 · COMEX', 'date_shown' => 'Thursday, Oct 08, 2026']);
$t = $r['trades'][0] ?? [];
ok(count($r['trades']) === 1 && $t['instrument'] === 'GC' && $t['direction'] === 'long' && $t['date'] === '2026-10-08' && $t['entry_time'] === '14:51' && $t['exit_time'] === '15:05' && $t['pnl_c'] === 21000 && $t['fees_c'] === 600 && $t['net_c'] === 20400 && !$t['check'], 'Tradesea single-trade page (labelled fields, symbol only on the chart): GC long, 14:51 → 15:05, gross $210, charges $6, net $204');
$r = $TB(['Order Time', 'Side', 'Order Type', 'Filled Qty', 'Avg Price', 'Charges', 'Order ID'], [['2026-10-08, 2:51:12 PM', 'Buy', 'Market', '1', '$4,149.80', '$3.00', '28931444'], ['2026-10-08, 3:05:05 PM', 'Sell', 'Market', '1', '$4,151.90', '$3.00', '28931502']], [], ['symbol_shown' => 'Gold (GCZ6) · 5 · COMEX']);
ok(count($r['trades']) === 1 && $r['trades'][0]['instrument'] === 'GC' && $r['trades'][0]['pnl_c'] === 21000 && $r['trades'][0]['fees_c'] === 600, 'Tradesea executions without a symbol column: one GC trade, +$210 gross, $6 charges');
$r = $TB(['Side', 'Qty', 'Entry', 'Exit'], [['Long', '1', '100', '101']]);
ok(!$r['trades'] && $r['no_symbol'] && $r['unknown'] === [], 'no symbol anywhere: « no symbol read », never « ? »');
echo "\n" . ($f ? "$f failed" : "$n/$n passed") . "\n"; exit($f ? 1 : 0);
