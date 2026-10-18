<?php
declare(strict_types=1);
/**
 * Sweep — « Your edge » (brief edge T2): the profile on sets of trades written for the test:
 *   php tests/edge_test.php
 * Under 5 trades: not enough; an ORB of the morning that wins: found, with its level and number of trades; copies once,
 * example data out; $ per contract when the risk is unknown; « confirmed » only positive on both halves; « fading »; « new »;
 * a leak; never two conditions on the same trades.
 */
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
require dirname(__DIR__) . '/game/edge.php';
$pass = 0; $fail = 0;
$ok = function (bool $c, string $what) use (&$pass, &$fail) { echo ($c ? 'ok   ' : 'FAIL ') . $what . "\n"; $c ? $pass++ : $fail++; };
$day = '2026-10-16';   // a Friday
$d = fn(int $k) => (new DateTimeImmutable($day))->modify(($k >= 0 ? '-' : '+') . abs($k) . ' days')->format('Y-m-d');
$n = 0;
$tr = function (int $back, string $time, int $pnl, array $x = []) use ($d, &$n) {
    $n++;
    return $x + ['id' => sprintf('t%04d', $n), 'date' => $d($back), 'entry_time' => $time . ':00', 'session_date' => true, 'direction' => 'long', 'contracts' => 1, 'instrument' => 'NQ',
        'pnl_c' => $pnl, 'fees_c' => 0, 'risk_c' => 10000, 'setup' => '', 'created_at' => $d($back) . 'T' . $time . ':00.000Z'];
};
$find = fn(array $p, string $key) => array_values(array_filter($p['wins'], fn($c) => $c['key'] === $key))[0] ?? null;

// 1. under 5 trades
$p = GameEdge::profile([$tr(1, '09:40', 5000), $tr(2, '09:40', -2000), $tr(3, '10:10', 3000), $tr(4, '11:00', 1000)], [], $day);
$ok(!$p['enough'] && $p['n'] === 4 && !$p['wins'], '4 trades: not enough yet, nothing shown (' . $p['n'] . ')');

// 2. ORB of the morning wins, the rest loses a little; trades on market days only
$T = []; $days = [1, 2, 3, 4, 7, 8, 9, 10, 11, 14, 15, 16, 17, 18];
foreach ($days as $i => $b) { $T[] = $tr($b, '09:45', $i % 5 === 4 ? -10000 : 20000, ['setup' => 'Opening Range Breakout']); $T[] = $tr($b, '13:15', -5000, ['setup' => 'Reversal']); }
$p = GameEdge::profile($T, [], $day);
$top = $p['wins'][0] ?? null;
$ok($p['unit'] === 'R' && $p['n'] === 28, 'risk known on every trade: in R, 28 trades (' . $p['unit'] . ', ' . $p['n'] . ')');
$ok($top && $top['key'] === 'setup=opening range breakout' && $top['dims'] === [['setup', 'Opening Range Breakout']] && $top['n'] === 14 && $top['level'] === 'trend' && abs($top['avg'] - 1.57) < 0.01,
    'the morning ORB first, by its setup (same trades as its slot: the simplest, the setup first): 14 trades, « trend », +1.57 R (' . json_encode($top) . ')');
$ok(count($p['wins']) === 1, 'the ORB, its 9:30 slot and « 1st trade of the day » are the same 14 trades: shown once (' . count($p['wins']) . ')');
$ok($p['leak'] && $p['leak']['avg'] < 0 && $p['leak']['n'] === 14, 'the leak: the afternoon reversal (' . json_encode($p['leak'] ? [$p['leak']['key'], $p['leak']['avg']] : null) . ')');
$ok($top && $top['win'] === 86 && $top['last'] === $d(1), 'its win rate (12 of 14 = 86 %) and the day of its last trade (' . ($top['win'] ?? '') . ', ' . ($top['last'] ?? '') . ')');

// 3. copies once, example data out
$C = $T;
foreach ([1, 2] as $k) $C[] = $tr(1, '09:45', 20000, ['setup' => 'Opening Range Breakout', 'copy_group' => 'g1', 'account_id' => 'b' . $k, 'created_at' => $d(1) . 'T09:45:00.900Z']);
$C[0]['copy_group'] = 'g1';   // the original of the group: the first ORB (saved before its copies)
for ($k = 0; $k < 6; $k++) $C[] = $tr(2, '15:00', 90000, ['demo' => true, 'setup' => 'Demo']);
$p2 = GameEdge::profile($C, [], $day);
$ok($p2['n'] === 28, 'a trade copied on 2 more accounts counts once, the example trades not at all (' . $p2['n'] . ')');

// 4. $ per contract when the risk is unknown
$U = array_map(fn($t) => ['risk_c' => 0, 'contracts' => 2] + $t, $T);
$p3 = GameEdge::profile($U, [], $day);
$ok($p3['unit'] === '$' && $p3['wins'] && abs($p3['wins'][0]['avg'] - 78.57) < 0.01, 'no risk: $ per contract (the ORB: ($200 × 12 − $100 × 2) / 14 / 2 contracts) (' . $p3['unit'] . ', ' . ($p3['wins'][0]['avg'] ?? '') . ')');

// 5. confirmed: 20 trades or more, positive on both halves of the 8 weeks
$V = [];
foreach ([1, 2, 3, 4, 7, 8, 9, 10, 11, 14, 30, 31, 32, 35, 36, 37, 38, 39, 42, 43, 44] as $i => $b) { $V[] = $tr($b, '09:40', $i % 4 === 3 ? -8000 : 15000, ['setup' => 'VWAP reclaim']); $V[] = $tr($b, '11:30', -4000); }
$p4 = GameEdge::profile($V, [], $day); $c4 = $find($p4, 'setup=vwap reclaim');
$ok($c4 && $c4['n'] === 21 && $c4['level'] === 'confirmed' && !$c4['fading'], '21 VWAP reclaims, positive in both halves: « confirmed » (' . json_encode($c4 ? [$c4['n'], $c4['level']] : null) . ')');

// 6. fading: strong before, weak in the last 4 weeks
$F = [];
foreach ([30, 31, 32, 35, 36, 37] as $b) { $F[] = $tr($b, '09:40', 30000, ['setup' => 'Break & retest']); $F[] = $tr($b, '12:00', -6000); }
foreach ([1, 2, 3, 4, 7, 8] as $i => $b) { $F[] = $tr($b, '09:40', $i % 2 ? 2000 : 1000, ['setup' => 'Break & retest']); $F[] = $tr($b, '12:00', -6000); }
$p5 = GameEdge::profile($F, [], $day); $c5 = $find($p5, 'setup=break & retest');
$ok($c5 && $c5['fading'] && $c5['level'] === 'trend', '+3 R before, +0.15 R in the last 4 weeks: « fading », still shown (' . json_encode($c5 ? [$c5['n'], $c5['avg'], $c5['fading']] : null) . ')');

// 7. new: under 5 trades a week ago
$N = [];
foreach ([0, 1, 2, 3, 4, 5] as $b) { $N[] = $tr($b, '09:35', 18000, ['setup' => 'Fair value gap']); $N[] = $tr($b, '14:00', -5000); }
$p6 = GameEdge::profile($N, [], $day); $c6 = $find($p6, 'setup=fair value gap');
$ok($c6 && $c6['new'] && $c6['level'] === 'lead', '6 FVG in the last 6 days: a new lead (' . json_encode($c6 ? [$c6['n'], $c6['level'], $c6['new']] : null) . ')');

// 8. the plan: « in your plan » from the day's bias and setups
$P = []; $J = [];
foreach ([1, 2, 3, 4, 7, 8, 9] as $b) {
    $J[] = ['id' => $d($b), 'pre' => ['bias' => 'bullish', 'max_loss' => '500', 'setups' => ['ORB']]];
    $P[] = $tr($b, '10:05', 12000, ['setup' => 'ORB']); $P[] = $tr($b, '11:05', -7000, ['setup' => 'Chase', 'direction' => 'short']);
}
$p7 = GameEdge::profile($P, $J, $day);
$keys = array_column($p7['wins'], 'key');
$ok(array_intersect($keys, ['plan=in', 'setup=orb', 'side=long']) && $p7['leak'] && preg_match('/plan=out|side=short|setup=chase/', $p7['leak']['key']), 'in the plan (bullish, ORB) wins, off the plan loses (' . json_encode([$keys, $p7['leak']['key'] ?? null]) . ')');

// 9. the 8 weeks only, nothing after the day
$O = $T; $O[] = $tr(80, '09:45', 900000, ['setup' => 'Old']); $O[] = $tr(-2, '09:45', 900000, ['setup' => 'Future']);
$ok(GameEdge::profile($O, [], $day)['n'] === 28, 'a trade older than 8 weeks or after the day is not read');

echo $fail ? "$fail failed\n" : "all passed\n";
exit($fail ? 1 : 0);
