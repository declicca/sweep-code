<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli' && realpath((string) ($_SERVER['SCRIPT_FILENAME'] ?? '')) === realpath(__FILE__)) { http_response_code(404); exit; }
/**
 * Sweep — automatic « wow » moments: milestones of discipline (never P&L), sent once each through the notification
 * center (category « achievements »; the big ones open as a celebration). On the first check, milestones the trader
 * already passed are recorded silently, so nobody gets ten notifications at once.
 */

final class GameWow
{
    private const STEPS = [
        'journal' => [10, 50, 100, 250, 500, 1000],
        'plans' => [10, 50, 100, 250],
        'reviews' => [10, 50, 100, 250],
        'days' => [30, 100, 365],
    ];
    private const BIG = ['journal' => 100, 'plans' => 100, 'reviews' => 100, 'days' => 100];

    private static function counts(string $uid): array
    {
        $journaled = 0; foreach (GameEngine::docs($uid, 'trades') as $t) if (GameEngine::journaled($t)) $journaled++;
        $c = GameEngine::counters($uid);
        $p = GameEngine::profile($uid, false);
        $days = (int) floor((GameEngine::ts() - (new DateTimeImmutable((string) $p['started_on']))->getTimestamp()) / 86400);
        return ['journal' => $journaled, 'plans' => $c['plans'], 'reviews' => $c['reviews'], 'days' => $days];
    }

    public static function check(string $uid): void
    {
        if (!class_exists('Notify', false)) return;
        $p = GameEngine::profile($uid, false); if (!$p) return;
        $o = GameEngine::onboarding($p);
        $seen = (array) ($o['wow'] ?? []);
        $init = empty($o['wow_init']);
        $send = [];
        foreach (self::counts($uid) as $k => $v) foreach (self::STEPS[$k] as $n) {
            $key = "$k:$n";
            if ($v < $n || in_array($key, $seen, true)) continue;
            $seen[] = $key;
            if (!$init) $send[] = ['wow_' . $k, ['n' => $n], $n >= self::BIG[$k]];
        }
        // first week (Mon-Fri, locked) with 3+ trades and none outside the plan
        if (!in_array('clean_week', $seen, true)) {
            $mon = GameEngine::addDays(GameEngine::monday(GameEngine::today()), -7);
            for ($w = 0; $w < 8; $w++, $mon = GameEngine::addDays($mon, -7)) {
                $rows = GameEngine::q('SELECT detail_json, plan_valid FROM game_days WHERE user_id = ? AND trading_day BETWEEN ? AND ?', [$uid, $mon, GameEngine::addDays($mon, 4)])->fetchAll(PDO::FETCH_ASSOC);
                $n = 0; $off = 0;
                foreach ($rows as $r) foreach ((json_decode((string) $r['detail_json'], true)['trades'] ?? []) as $x) { $n++; if (!empty($x['v'])) $off++; }
                if ($n >= 3 && $off === 0) { $seen[] = 'clean_week'; if (!$init) $send[] = ['wow_clean_week', [], true]; break; }
            }
        }
        // best month of discipline (share of valid market days), told on the 1st, once per month
        $prevM = (new DateTimeImmutable(GameEngine::today()))->modify('first day of last month')->format('Y-m');
        if (!in_array("month:$prevM", $seen, true)) {
            $by = [];
            foreach (GameEngine::q('SELECT trading_day, is_valid_streak FROM game_days WHERE user_id = ? AND trading_day < ?', [$uid, substr(GameEngine::today(), 0, 7) . '-01']) as $r) {
                if (!GameEngine::isMarketDay($r['trading_day'])) continue;
                $m = substr($r['trading_day'], 0, 7); $by[$m][0] = ($by[$m][0] ?? 0) + 1; $by[$m][1] = ($by[$m][1] ?? 0) + (int) $r['is_valid_streak'];
            }
            $by = array_filter($by, fn($x) => $x[0] >= 10);
            if (isset($by[$prevM]) && count($by) >= 2) {
                $pct = fn($x) => $x[1] / $x[0];
                $best = max(array_map($pct, array_diff_key($by, [$prevM => 1])));
                $seen[] = "month:$prevM";
                if ($pct($by[$prevM]) > $best && !$init) $mi = (int) substr($prevM, 5) - 1; $send[] = ['wow_best_month', ['pct' => (int) round($pct($by[$prevM]) * 100), 'month' => ['January','February','March','April','May','June','July','August','September','October','November','December'][$mi],
                    'month_fr' => ['janvier','février','mars','avril','mai','juin','juillet','août','septembre','octobre','novembre','décembre'][$mi], 'month_es' => ['enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre'][$mi]], true];
            }
        }
        $o['wow'] = array_values(array_unique($seen)); $o['wow_init'] = true;
        GameEngine::q('UPDATE user_game_profile SET onboarding_json = ? WHERE user_id = ?', [json_encode($o), $uid]);
        foreach ($send as [$type, $params, $big]) {
            Notify::send($uid, $type, $params, ['dedupe_key' => $type . ':' . json_encode($params), 'action_url' => '#analytics', 'priority' => $big ? 'celebration' : 'normal']);
            GameEngine::track($uid, 'wow_moment', ['type' => $type]);
        }
    }
}
