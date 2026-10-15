<?php
declare(strict_types=1);
/**
 * Sweep — right numbers on the server (brief 00, phase 1, lot 1.2), without network:
 *   php tests/numbers_test.php
 *  d. an instrument outside Sweep's list (ZC, 6J…) is never counted as NQ in « Enter with AI » / screenshot drafts: the symbol
 *     is kept, a dollar result is kept, a result in points or ticks (or prices) is not turned into dollars at NQ's value —
 *     the trader is asked for the P&L; a known instrument is computed as before.
 */
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
$app = dirname(__DIR__);
require $app . '/ai/ai-core.php';
require $app . '/ai/ai-stats.php';
require $app . '/ai/ai-features.php';
$pass = 0; $fail = 0;
$ok = function (bool $c, string $what) use (&$pass, &$fail) { echo ($c ? 'ok   ' : 'FAIL ') . $what . "\n"; $c ? $pass++ : $fail++; };
$ctx = ['accounts' => [['id' => 'a1', 'name' => 'Topstep 50K']], 'setups' => []];
$draft = fn(array $x) => sai_trade_drafts(['trades' => [$x]], $ctx, 'text')['drafts'][0];
$d = $draft(['instrument' => 'ZC', 'direction' => 'long', 'contracts' => 1, 'entry' => 450.25, 'exit' => 452.75, 'result_value' => 125, 'result_unit' => 'usd', 'entry_time' => '10:00', 'exit_time' => '10:10']);
$ok($d['trade']['instrument'] === 'ZC' && $d['trade']['pnl_c'] === 12500 && $d['trade']['pnl_manual'] === true, 'ZC with « +$125 »: kept as ZC, +$125 (before: NQ, P&L from its prices at $20 a point) (' . json_encode([$d['trade']['instrument'], $d['trade']['pnl_c']]) . ')');
$d = $draft(['instrument' => '6J', 'direction' => 'short', 'entry' => 0.006650, 'exit' => 0.006640, 'result_value' => 8, 'result_unit' => 'ticks']);
$ok($d['trade']['instrument'] === '6J' && $d['trade']['pnl_c'] === null && in_array('pnl', $d['missing'], true), '6J with « 8 ticks »: no dollar figure made up, the P&L is asked (' . json_encode([$d['trade']['pnl_c'], $d['missing']]) . ')');
$d = $draft(['instrument' => '6E', 'direction' => 'long', 'entry' => 1.0850, 'exit' => 1.0860]);
$ok($d['trade']['pnl_c'] === 12500 && $d['trade']['pnl_manual'] === false, '6E (in the list), 10 pips: +$125 as before');
$d = $draft(['instrument' => 'NQ', 'direction' => 'long', 'contracts' => 2, 'entry' => 20000, 'exit' => 20010]);
$ok($d['trade']['instrument'] === 'NQ' && $d['trade']['pnl_c'] === 40000, 'NQ, 10 points × 2: +$400 as before');
$d = $draft(['instrument' => 'weird symbol!', 'direction' => 'long', 'result_value' => 50, 'result_unit' => 'usd']);
$ok($d['trade']['instrument'] === '' && $d['trade']['pnl_c'] === 5000, 'an unreadable symbol: left empty for the trader, never « NQ »');
echo "\n$pass passed, $fail failed\n";
exit($fail ? 1 : 0);
