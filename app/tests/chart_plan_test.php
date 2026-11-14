<?php
declare(strict_types=1);
/**
 * Sweep — Plan Sync step 1, the chart plan's model (journals/{day}.chart):   php tests/chart_plan_test.php
 * Roots (MNQ is NQ, the contract month ignored), zones and rules normalized (known fields, right types, a reversed zone put
 * right, a rule without its zone left out), kept when a document does not carry it, removed when emptied, never on a non-day.
 */
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
require dirname(__DIR__) . '/game/chart-plan.php';
$pass = 0; $fail = 0;
$ok = function (bool $c, string $what) use (&$pass, &$fail) { echo ($c ? 'ok   ' : 'FAIL ') . $what . "\n"; $c ? $pass++ : $fail++; };

// 1. the instrument's root
foreach ([['NQ', 'NQ'], ['MNQ', 'NQ'], ['NQZ6', 'NQ'], ['MNQH27', 'NQ'], ['mes z6', 'ES'], ['MGC', 'GC'], ['MCL', 'CL'], ['CL', 'CL'], ['M2K', 'RTY'], ['GC', 'GC'], ['ES', 'ES']] as [$in, $want]) {
    $ok(ChartPlan::root($in) === $want, "1 root of $in is $want (" . ChartPlan::root($in) . ')');
}
// 2. normalize
$c = ChartPlan::normalize(['junk' => 1, 'zones' => [
    ['id' => 'pdh', 'instrument' => 'MNQZ6', 'type' => 'level', 'price' => '21290.25', 'label' => '<b>PDH</b>', 'role' => 'resistance', 'bias' => 'short', 'note' => 'Sweep then back under', 'proximity_ticks' => 40, 'x' => 2],
    ['id' => 'buy', 'instrument' => 'NQ', 'type' => 'zone', 'high' => 21180, 'low' => 21200, 'label' => 'Buy zone', 'role' => 'odd', 'bias' => 'up'],
    ['id' => 'bad', 'instrument' => 'NQ', 'type' => 'level', 'price' => 'x'],
    ['id' => 'noinst', 'instrument' => '', 'type' => 'level', 'price' => 100],
    ['id' => 'flat', 'instrument' => 'ES', 'type' => 'zone', 'high' => 5800, 'low' => 5800],
], 'rules' => [
    ['id' => 'r1', 'trigger' => 'sweep', 'zone' => 'pdh', 'tf' => '5m', 'action' => 'plan', 'message' => 'Wait for the reclaim'],
    ['id' => 'r2', 'trigger' => 'close_above', 'zone' => 'buy', 'tf' => '4h', 'action' => 'nope'],
    ['id' => 'r3', 'trigger' => 'enter', 'zone' => 'gone'],
    ['id' => 'r4', 'trigger' => 'time', 'time' => '09:30', 'action' => 'limit', 'tf' => '5m'],
    ['id' => 'r5', 'trigger' => 'time', 'time' => '9h30'],
    ['id' => 'r6', 'trigger' => 'explode', 'zone' => 'pdh'],
], 'updated_at' => 1792000000]);
$ok(count($c['zones']) === 2 && count($c['rules']) === 3, '2 two zones and three rules kept (no price, no instrument, a flat zone, no zone, a wrong time, an unknown trigger left out)');
$z = $c['zones'][0];
$ok($z['instrument'] === 'NQ' && $z['price'] === 21290.25 && $z['label'] === 'PDH' && $z['role'] === 'resistance' && $z['bias'] === 'short' && $z['proximity_ticks'] === 40 && !isset($z['x']), '2 a level: root NQ, the price a number, tags stripped, known fields only');
$z = $c['zones'][1];
$ok($z['high'] === 21200.0 && $z['low'] === 21180.0 && $z['role'] === 'neutral' && $z['bias'] === null && $z['proximity_ticks'] === null, '2 a reversed zone put right, an unknown role neutral, an unknown bias none');
$ok($c['rules'][0] === ['id' => 'r1', 'trigger' => 'sweep', 'zone' => 'pdh', 'tf' => '5m', 'action' => 'plan', 'message' => 'Wait for the reclaim'], '2 a sweep rule kept as it is');
$ok($c['rules'][1]['tf'] === '5m' && $c['rules'][1]['action'] === 'alert', '2 a wrong time frame: 5m; a wrong action: the alert');
$ok($c['rules'][2] === ['id' => 'r4', 'trigger' => 'time', 'time' => '09:30', 'action' => 'limit', 'message' => ''], '2 a time rule: its New York time, no zone, no time frame');
$ok($c['updated_at'] === 1792000000 && !isset($c['junk']), '2 updated_at kept, unknown keys dropped');
$ok(ChartPlan::normalize('x') === null, '2 not an object: nothing');
$many = ChartPlan::normalize(['zones' => array_map(fn($i) => ['id' => "z$i", 'instrument' => 'NQ', 'price' => 20000 + $i], range(1, 40))]);
$ok(count($many['zones']) === ChartPlan::MAX_ZONES, '2 at most ' . ChartPlan::MAX_ZONES . ' zones');
// 3. apply
$day = '2026-11-13'; $stored = ['chart' => $c];
$ok(ChartPlan::apply(['pre' => ['bias' => 'bullish']], $day, $stored)['chart'] === $c, '3 a document without its chart plan keeps the stored one');
$ok(!isset(ChartPlan::apply(['chart' => ['zones' => [], 'rules' => []]], $day, $stored)['chart']), '3 emptied: removed');
$ok(!isset(ChartPlan::apply(['chart' => null], $day, $stored)['chart']), '3 null: removed');
$ok(!isset(ChartPlan::apply(['chart' => $c], 'notes', null)['chart']), '3 no chart plan on a journal that is not a day');
$ok(ChartPlan::apply(['pre' => ['bias' => 'bullish']], $day, null) === ['pre' => ['bias' => 'bullish']], '3 a journal without a chart plan is untouched');
$d = ChartPlan::apply(['chart' => ['zones' => [['id' => 'a', 'instrument' => 'MES', 'price' => 5810.5, 'label' => 'PDL', 'role' => 'support']]]], $day, $stored);
$ok($d['chart']['zones'][0]['instrument'] === 'ES' && !$d['chart']['rules'], '3 a new chart plan replaces the stored one (its rules gone with their zones)');

echo "\n$pass passed, $fail failed\n";
exit($fail ? 1 : 0);
