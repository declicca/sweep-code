<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli' && realpath((string) ($_SERVER['SCRIPT_FILENAME'] ?? '')) === realpath(__FILE__)) { http_response_code(404); exit; }
/**
 * Sweep — Gamification V2, step 3: monthly Wrapped, scheduled reminders (NotificationService), payout readiness at 100 %.
 *
 * Wrapped: built on the 1st for the previous month when the trader had 5+ active days. Everything is computed in PHP;
 * no P&L, no amount anywhere (R and counts only). Free sees screens 1, 2, 7 and 8; the others show as a locked preview.
 * Reminders: in-app notifications through the existing notification center (channels ready for web push / native later).
 * Never between 9:30 and 16:00 ET, never pushing to take a trade, at most 2 a day, each switchable in Settings
 * (category « streaks » for daily reminders, « achievements » for weekly review and Wrapped).
 */

final class GameNotifyService
{
    /** channels: in-app today; web push (VAPID) and native (APNs/FCM) plug in here later */
    public static function send(string $uid, string $type, array $params, string $dedupe, string $url): bool
    {
        if (!class_exists('Notify', false)) return false;
        $id = Notify::send($uid, $type, $params, ['dedupe_key' => $dedupe, 'action_url' => $url]);
        if ($id) GameEngine::track($uid, 'notification_sent', ['type' => $type]);
        return (bool) $id;
    }

    /** one pass for one trader (cron every 15 min, and on app open) */
    public static function run(string $uid): void
    {
        if (!class_exists('Notify', false)) return;
        $now = (new DateTimeImmutable('@' . GameEngine::ts()))->setTimezone(new DateTimeZone('America/New_York'));
        $hm = $now->format('H:i'); $date = $now->format('Y-m-d'); $dow = (int) $now->format('N');
        if ($hm >= '09:30' && $hm < '16:00') return;                                   // market hours: silence
        // at most 2 game reminders per day
        try { $sent = (int) db()->query("SELECT COUNT(*) FROM notifications WHERE user_id = " . db()->quote($uid) . " AND dedupe_key LIKE " . db()->quote("g:%:$date"))->fetchColumn(); }
        catch (Throwable $e) { $sent = 0; }
        if ($sent >= 2) return;
        $p = GameEngine::profile($uid, false); if (!$p) return;
        // only traders who used Sweep in the last 14 days
        $active = (bool) GameEngine::q('SELECT 1 FROM game_days WHERE user_id = ? AND activity = 1 AND trading_day >= ?', [$uid, GameEngine::addDays($date, -14)])->fetchColumn();
        $day = GameEngine::today();
        $g = GameEngine::q('SELECT * FROM game_days WHERE user_id = ? AND trading_day = ?', [$uid, $day])->fetch(PDO::FETCH_ASSOC) ?: null;
        $market = GameEngine::isMarketDay($day);
        $todo = [];
        if ($active && $market && $hm >= '08:45' && $hm < '09:30' && !($g && (int) $g['plan_valid'])) $todo[] = ['g_plan', [], '#dashboard'];
        if ($active && $market && $hm >= '16:30' && $hm < '21:00' && $g && !(int) $g['review_done'] && ((int) $g['trades_count'] > 0 || (int) $g['plan_valid'])) $todo[] = ['g_review', [], '#dashboard'];
        $streak = GameEngine::profileState($uid)['streak'];
        if ($market && $hm >= '21:00' && !($g && (int) $g['is_valid_streak']) && $streak['current'] >= 3) $todo[] = ['g_streak', ['n' => $streak['current']], '#dashboard'];
        if (class_exists('GameV2b', false)) {
            $w = GameV2b::weeklyState($uid, true);
            // the week's recap (brief 01 step 5): ONE notification when it is ready (review of the last trading day, or its close),
            // never again that week, none once the trader has opened it; every trader with a trade this week
            Notify::schema();   // a fresh database may not have the notifications table yet
            if ($w['open'] && empty($w['seen']) && !GameEngine::q('SELECT 1 FROM notifications WHERE user_id = ? AND dedupe_key LIKE ?', [$uid, 'g:g_weekly:' . $w['week'] . ':%'])->fetchColumn())
                $todo[] = ['g_weekly', [], '#dashboard', 'g:g_weekly:' . $w['week'] . ':' . $date];
            if ($dow === 7 && $hm >= '18:00') {
                $mon = GameEngine::monday($date);
                $row = GameEngine::q('SELECT data_json FROM weekly_reviews WHERE user_id = ? AND week_start = ?', [$uid, $mon])->fetchColumn();
                $int = $row ? ((json_decode((string) $row, true) ?: [])['intention'] ?? '') : '';
                if ($row) $todo[] = ['g_intention', ['intention' => $int !== '' ? $int : '—'], '#dashboard'];
            }
        }
        if ((int) $now->format('j') === 1 && ($hm >= '16:00' || $hm < '09:30')) {
            $m = (new DateTimeImmutable($date))->modify('first day of last month')->format('Y-m');
            if (GameEngine::q('SELECT 1 FROM monthly_wrapped WHERE user_id = ? AND month = ?', [$uid, $m])->fetchColumn()) $todo[] = ['g_wrapped', ['month' => $m], '#dashboard'];
        }
        // end of the free trial: day 50 (10 days left) and day 58 (2 days left), with what the trader actually used
        if (function_exists('billing_on')) billing_on();
        if (function_exists('sb_live') && sb_live($uid) && function_exists('sb_active_sub') && !sb_active_sub(GameEngine::pdo(), $uid)) {
            try {
                $g = GameEngine::q("SELECT plan, ends_at FROM billing_grants WHERE uid = ? AND reason IN ('trial','early_access') AND starts_at <= ? AND ends_at > ? ORDER BY ends_at DESC LIMIT 1", [$uid, time(), time()])->fetch(PDO::FETCH_ASSOC);
                $left = $g ? (int) ceil(((int) $g['ends_at'] - time()) / 86400) : 0;
                if ($g && in_array($left, [10, 2], true)) {
                    $accounts = count(array_filter(GameEngine::docs($uid, 'accounts'), fn($a) => empty($a['demo'])));
                    $ai = 0; try { $ai = (int) GameEngine::q('SELECT COUNT(*) FROM ai_log WHERE user_id = ?', [$uid])->fetchColumn(); } catch (Throwable $e) { /* no AI log */ }
                    if (self::send($uid, 'trial_ending', ['days' => $left, 'plan' => ucfirst((string) $g['plan']), 'accounts' => $accounts, 'ai' => $ai, 'swept' => (int) GameEngine::counters($uid)['swept']], "trial:$uid:$left", '#plan')) $sent++;
                }
            } catch (Throwable $e) { error_log('[Sweep notify] trial: ' . $e->getMessage()); }
        }
        foreach ($todo as $x) {
            [$type, $params, $url] = $x;
            if ($sent >= 2) break;
            if (self::send($uid, $type, $params, $x[3] ?? "g:$type:$date", $url)) $sent++;   // keys end with :date (2 a day at most)
        }
    }
}

final class GameWrapped
{
    public static function schema(): void
    {
        static $done = false; if ($done) return; $done = true;
        $my = GameEngine::pdo()->getAttribute(PDO::ATTR_DRIVER_NAME) === 'mysql';
        GameEngine::pdo()->exec('CREATE TABLE IF NOT EXISTS monthly_wrapped (user_id ' . ($my ? 'VARCHAR(120)' : 'TEXT') . ' NOT NULL, month CHAR(7) NOT NULL, data_json TEXT NOT NULL, created_at INT NOT NULL, viewed_at INT NULL, PRIMARY KEY (user_id, month))' . ($my ? ' DEFAULT CHARSET=utf8mb4' : ''));
    }

    /** previous month's Wrapped, created once (5+ active days) */
    public static function ensure(string $uid): void
    {
        self::schema();
        $m = (new DateTimeImmutable(GameEngine::today()))->modify('first day of last month')->format('Y-m');
        if (GameEngine::q('SELECT 1 FROM monthly_wrapped WHERE user_id = ? AND month = ?', [$uid, $m])->fetchColumn()) return;
        $data = self::build($uid, $m);
        if (!$data) return;
        try { GameEngine::q('INSERT INTO monthly_wrapped (user_id, month, data_json, created_at) VALUES (?, ?, ?, ?)', [$uid, $m, json_encode($data), GameEngine::ts()]); } catch (Throwable $e) { /* raced */ }
    }

    public static function build(string $uid, string $m): ?array
    {
        $from = "$m-01"; $to = (new DateTimeImmutable($from))->modify('last day of this month')->format('Y-m-d');
        $days = GameEngine::q('SELECT * FROM game_days WHERE user_id = ? AND trading_day BETWEEN ? AND ? ORDER BY trading_day', [$uid, $from, $to])->fetchAll(PDO::FETCH_ASSOC);
        $activeDays = count(array_filter($days, fn($d) => (int) $d['activity'] === 1));
        if ($activeDays < 5) return null;
        $byDay = []; foreach ($days as $d) $byDay[$d['trading_day']] = $d;
        // 1. days swept / market days ; 2. best streak inside the month
        $market = 0; $swept = 0; $run = 0; $best = 0;
        for ($d = $from; $d <= $to; $d = GameEngine::addDays($d, 1)) {
            if (!GameEngine::isMarketDay($d)) continue;
            $market++; $g = $byDay[$d] ?? null;
            if ($g && (int) $g['is_swept']) $swept++;
            $run = $g && (int) $g['is_valid_streak'] ? $run + 1 : 0; $best = max($best, $run);
        }
        // trades of the month with compliance from the scored days
        $okIds = []; foreach ($days as $d) foreach ((json_decode((string) $d['detail_json'], true)['trades'] ?? []) as $x) $okIds[$x['id']] = (bool) $x['ok'];
        $trades = array_values(array_filter(GameEngine::docs($uid, 'trades'), fn($t) => ($t['date'] ?? '') >= $from && ($t['date'] ?? '') <= $to && empty($t['demo'])));
        // 3. signature setup: the setup with the most trades inside the plan
        $setups = [];
        foreach ($trades as $t) { $s = trim((string) ($t['setup'] ?? '')); if ($s === '') continue; $setups[$s][0] = ($setups[$s][0] ?? 0) + 1; $setups[$s][1] = ($setups[$s][1] ?? 0) + (int) ($okIds[(string) $t['id']] ?? false); }
        uasort($setups, fn($a, $b) => $b[1] <=> $a[1] ?: $b[0] <=> $a[0]);
        $sig = $setups ? ['setup' => array_key_first($setups), 'n' => reset($setups)[0], 'pct' => (int) round(reset($setups)[1] / max(1, reset($setups)[0]) * 100)] : null;
        // 4. golden 30-minute slot (R) ; 5. dominant emotion and its effect (R)
        $slots = []; $emo = []; $allR = [];
        foreach ($trades as $t) {
            $r = GameV2b::rOf($t);
            $e = ((array) (($t['emo'] ?? [])['before'] ?? []))[0] ?? null;
            if ($e) { $emo[$e][0] = ($emo[$e][0] ?? 0) + 1; if ($r !== null) $emo[$e][1][] = $r; }
            if ($r === null) continue;
            $allR[] = $r;
            if (preg_match('/^(\d{2}):(\d{2})/', (string) ($t['entry_time'] ?? ''), $x)) { $k = intdiv((int) $x[1] * 60 + (int) $x[2], 30) * 30; $slots[$k][] = $r; }
        }
        $slots = array_filter($slots, fn($v) => count($v) >= 3);
        uasort($slots, fn($a, $b) => array_sum($b) / count($b) <=> array_sum($a) / count($a));
        $gold = $slots ? (function ($k, $v) { return ['start' => sprintf('%02d:%02d', intdiv($k, 60), $k % 60), 'end' => sprintf('%02d:%02d', intdiv($k + 30, 60), ($k + 30) % 60), 'r' => round(array_sum($v) / count($v), 2), 'n' => count($v)]; })(array_key_first($slots), reset($slots)) : null;
        uasort($emo, fn($a, $b) => $b[0] <=> $a[0]);
        $dom = $emo ? (function ($k, $v) { $rs = $v[1] ?? []; return ['emotion' => $k, 'n' => $v[0], 'r' => $rs ? round(array_sum($rs) / count($rs), 2) : null]; })(array_key_first($emo), reset($emo)) : null;
        // 6. badges and journey steps unlocked ; 7. rank and XP of the month
        [$s0, $s1] = [(new DateTimeImmutable($from . ' 00:00', new DateTimeZone('America/New_York')))->getTimestamp(), (new DateTimeImmutable($to . ' 23:59:59', new DateTimeZone('America/New_York')))->getTimestamp()];
        $badges = GameEngine::q('SELECT badge_id FROM user_badges WHERE user_id = ? AND unlocked_at BETWEEN ? AND ?', [$uid, $s0, $s1])->fetchAll(PDO::FETCH_COLUMN);
        $nodes = 0; try { $nodes = (int) GameEngine::q('SELECT COUNT(*) FROM user_map_nodes WHERE user_id = ? AND completed_at BETWEEN ? AND ?', [$uid, $s0, $s1])->fetchColumn(); } catch (Throwable $e) { /* no map yet */ }
        $xp = (int) GameEngine::q('SELECT COALESCE(SUM(xp), 0) FROM xp_events WHERE user_id = ? AND created_at BETWEEN ? AND ?', [$uid, $s0, $s1])->fetchColumn();
        $p = GameEngine::profile($uid, false);
        return ['month' => $m, 'swept' => $swept, 'market_days' => $market, 'active_days' => $activeDays, 'best_streak' => $best, 'signature' => $sig, 'gold_slot' => $gold,
                'emotion' => $dom, 'badges' => array_values($badges), 'nodes' => $nodes, 'xp' => $xp, 'level' => (int) $p['level'], 'rank' => $p['rank_key']];
    }

    public static function state(string $uid): array
    {
        self::schema();
        $rows = GameEngine::q('SELECT month, data_json, created_at, viewed_at FROM monthly_wrapped WHERE user_id = ? ORDER BY month DESC LIMIT 12', [$uid])->fetchAll(PDO::FETCH_ASSOC);
        $plan = GameV2::plan($uid);
        return ['plan' => $plan, 'items' => array_map(fn($r) => ['month' => $r['month'], 'data' => json_decode((string) $r['data_json'], true), 'new' => !$r['viewed_at'], 'fresh' => GameEngine::ts() - (int) $r['created_at'] < 14 * 86400], $rows)];
    }
    public static function viewed(string $uid, string $m): void
    {
        self::schema();
        GameEngine::q('UPDATE monthly_wrapped SET viewed_at = COALESCE(viewed_at, ?) WHERE user_id = ? AND month = ?', [GameEngine::ts(), $uid, $m]);
        GameEngine::track($uid, 'wrapped_viewed', ['month' => $m]);
    }

    /** payout readiness reaching 100 %: gold moment + badge, once */
    public static function payoutCheck(string $uid): void
    {
        [$cfg, $ready] = GameV2::payoutReadiness($uid);
        if ($cfg && $ready >= 100 && GameEngine::unlock($uid, 'payout_ready', true)) GameEngine::celebrate($uid, 'payout_ready', []);
    }
}
