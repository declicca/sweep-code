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

// 5. the lock (step 4)
$sheet = fn(array $x = []) => array_replace_recursive(['instrument' => 'MES', 'levels' => ['london_high' => 5820, 'london_low' => 5800],
    'scenarios' => [['id' => 'A', 'direction' => 'long', 'type' => 'breakout', 'level' => 5820, 'stop_estimate' => 5814, 'target' => 5850]], 'limits' => ['max_trades' => 2]], $x);
$day = '2026-10-20'; $before = $ny('2026-10-20 08:00'); $after = $ny('2026-10-20 09:30');
$prev = ['fiche' => Fiche::normalize($sheet(), $day)];
$ok(Fiche::normalize($sheet(), $day)['scenarios'][0]['r_estimate'] === 5.0, '5 R recomputed by the server: 30 / 6 = 5');
$d = Fiche::apply(['fiche' => $sheet(['levels' => ['london_high' => 5830]])], $day, $prev, $before);
$ok($d['fiche']['levels']['london_high'] === 5830.0, '5 before 09:25: the sheet changes');
$d = Fiche::apply(['fiche' => $sheet(['levels' => ['london_high' => 5830], 'scenarios' => [['status' => 'confirmed', 'done' => ['close_15m', 'trigger_5m']]], 'invalidations' => 1])], $day, $prev, $after);
$ok($d['fiche']['levels']['london_high'] === 5820.0 && $d['fiche']['scenarios'][0]['level'] === 5820.0, '5 after 09:25: levels and scenarios stay');
$ok($d['fiche']['scenarios'][0]['status'] === 'confirmed' && $d['fiche']['scenarios'][0]['done'] === ['close_15m'] && $d['fiche']['invalidations'] === 1, '5 … the status, the boxes in order (trigger without retest: not counted), the invalidations follow');
$ok(Fiche::apply(['fiche' => $sheet(['levels' => ['london_high' => 5830]])], $day, $prev, $after, '10:00')['fiche']['levels']['london_high'] === 5830.0, '5 the trader\'s lock time (10:00): still open at 09:30');
$lk = ['fiche' => Fiche::normalize($sheet(['locked_at' => $before]), $day)];
$ok(Fiche::apply(['fiche' => $sheet(['limits' => ['max_trades' => 5], 'locked_at' => null])], $day, $lk, $before)['fiche']['limits']['max_trades'] === 2, '5 locked by hand: limits stay, and it does not unlock');
$ok(Fiche::apply(['pre' => ['bias' => 'bullish']], $day, $prev, $before)['fiche']['levels']['london_high'] === 5820.0, '5 a journal sent without its sheet keeps it');
$ok(!isset(Fiche::apply(['fiche' => null], $day, $prev, $before)['fiche']), '5 before the lock, an explicit null removes it');
$ok(Fiche::apply(['fiche' => null], $day, $prev, $after)['fiche']['levels']['london_high'] === 5820.0, '5 after the lock, it cannot be removed');
$ok(Fiche::apply(['fiche' => $sheet(['scenarios' => [['target' => 5825]], 'locked_at' => $before])], $day, null, $before)['fiche']['locked_at'] === null, '5 under 2R (5 825: 0.8R), the sheet does not lock');
$ok(Fiche::apply(['fiche' => $sheet(['locked_at' => $before])], $day, null, $before)['fiche']['locked_at'] === $before, '5 viable: it locks');

echo "\n$pass passed, $fail failed\n";
exit($fail ? 1 : 0);
