<?php
declare(strict_types=1);
/**
 * Sweep — the pre-market sheet's model (brief « Plan pre-market adaptatif », step 1):   php tests/fiche_test.php
 * Trading day: 17:59 NY is still the day, 18:00 the next one; Friday evening, Saturday and Sunday go to Monday. Lock: 09:25 NY
 * of the sheet's own date by default, the trader's time otherwise, summer and winter time. Normalize: known fields only, right
 * types, limits bounded, the checklist from the scenario's type, checked boxes kept in their order; no sheet on a non-day.
 */
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
require dirname(__DIR__) . '/game/fiche.php';
$pass = 0; $fail = 0;
$ok = function (bool $c, string $what) use (&$pass, &$fail) { echo ($c ? 'ok   ' : 'FAIL ') . $what . "\n"; $c ? $pass++ : $fail++; };
$ny = fn(string $s) => (new DateTimeImmutable($s, new DateTimeZone('America/New_York')))->getTimestamp();

// 1. the trading day
foreach ([['2026-10-19 17:59', '2026-10-19'], ['2026-10-19 18:00', '2026-10-20'], ['2026-10-20 09:25', '2026-10-20'], ['2026-10-20 00:30', '2026-10-20'],
          ['2026-10-23 17:59', '2026-10-23'], ['2026-10-23 18:00', '2026-10-26'], ['2026-10-24 12:00', '2026-10-26'], ['2026-10-25 18:05', '2026-10-26'],
          ['2026-11-01 01:30', '2026-11-02'], ['2026-03-08 18:00', '2026-03-09']] as [$at, $want]) {
    $ok(Fiche::dayOf($ny($at)) === $want, "1 $at NY → trading day $want (" . Fiche::dayOf($ny($at)) . ')');
}
// 2. the lock time
$ok(Fiche::lockEpoch('2026-10-20') === $ny('2026-10-20 09:25'), '2 default lock: 09:25 NY on the sheet\'s own date (summer time)');
$ok(Fiche::lockEpoch('2026-12-14') === $ny('2026-12-14 09:25'), '2 default lock in winter time too');
$ok(Fiche::lockEpoch('2026-10-20', '09:00') === $ny('2026-10-20 09:00'), '2 the trader\'s lock time');
$ok(Fiche::lockEpoch('2026-10-20', '25:00') === $ny('2026-10-20 09:25'), '2 a wrong time: the default');
// 3. normalize
$f = Fiche::normalize(['instrument' => 'MES<script>', 'junk' => 1, 'levels' => ['london_high' => '5820.5', 'pdl' => 'x', 'source' => 'robot'],
    'scenarios' => [['id' => 'A', 'direction' => 'short', 'type' => 'breakdown', 'level' => 5820, 'target' => 5790, 'done' => ['retest_5m', 'close_15m', 'vwap'], 'status' => 'odd'],
                    ['type' => 'reclaim'], ['type' => 'breakout']],
    'limits' => ['risk_pct' => 3, 'max_trades' => 99, 'time_limit' => '11:30'], 'no_trade_conditions' => ['two_invalidations', 'hack'], 'locked_at' => '1'], '2026-10-20');
$ok(!isset($f['junk']) && $f['v'] === 1 && $f['trading_day'] === '2026-10-20', '3 unknown fields dropped, version and day set');
$ok($f['instrument'] === 'MESscript', '3 instrument: letters and digits only (' . $f['instrument'] . ')');
$ok($f['levels']['london_high'] === 5820.5 && $f['levels']['pdl'] === null && $f['levels']['source'] === 'manual', '3 levels: numbers or null, source manual unless auto');
$ok(count($f['scenarios']) === 2 && $f['scenarios'][1]['id'] === 'B', '3 two scenarios at most, A then B');
$ok($f['scenarios'][0]['conditions'] === ['close_15m', 'retest_5m', 'trigger_5m', 'risk_checked'] && $f['scenarios'][1]['conditions'][3] === 'vwap', '3 the checklist comes from the type (VWAP for a reclaim)');
$ok($f['scenarios'][0]['done'] === ['close_15m', 'retest_5m'] && $f['scenarios'][0]['status'] === 'waiting', '3 checked boxes kept in the checklist\'s order, unknown status → waiting');
$ok($f['limits'] === ['risk_pct' => 0.5, 'max_trades' => 20, 'time_limit' => '11:30'], '3 limits bounded (risk 0.5 or 0.25, 1 to 20 trades)');
$ok($f['no_trade_conditions'] === ['two_invalidations'] && $f['locked_at'] === null && $f['mode'] === 'full', '3 no-trade conditions from the list, locked_at an integer or null, mode full');
$ok(json_encode($f['answers']) === '{}', '3 answers stay an object');
// 4. apply
$ok(!isset(Fiche::apply(['fiche' => ['instrument' => 'NQ']], 'notes')['fiche']), '4 no sheet on a journal that is not a day');
$ok(Fiche::apply(['fiche' => ['instrument' => 'NQ']], '2026-10-20')['fiche']['instrument'] === 'NQ', '4 a day\'s sheet normalized');
$ok(Fiche::apply(['pre' => ['bias' => 'bullish']], '2026-10-20') === ['pre' => ['bias' => 'bullish']], '4 a journal without a sheet is untouched');

echo "\n$pass passed, $fail failed\n";
exit($fail ? 1 : 0);
