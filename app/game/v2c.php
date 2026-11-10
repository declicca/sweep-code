<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli' && realpath((string) ($_SERVER['SCRIPT_FILENAME'] ?? '')) === realpath(__FILE__)) { http_response_code(404); exit; }
/**
 * Sweep — scheduled reminders (NotificationService) and payout readiness at 100 %.
 * (The monthly Wrapped / « Month in Review » was retired on 10 Nov. 2026, brief « produit final »: its table monthly_wrapped
 * stays, untouched, and goes with a deleted account.)
 * Reminders: in-app notifications through the existing notification center; the plan, the review and the week's recap also
 * reach the phone (push/web-push.php, brief 02 part 10), from the scheduled task only (never while the trader is in the app).
 * Never between 9:30 and the 17:00 ET close, never pushing to take a trade, at most 2 a day (and 2 notifications a day in all,
 * notify/notify.php), each switchable in Settings (category « streaks » for daily reminders, « achievements » for weekly
 * review). The plan, review and recap come at the trader's time (Settings › Notifications, New York time).
 */

final class GameNotifyService
{
    /** the reminders that also reach the phone (push/web-push.php: kind) */
    private const PUSH = ['g_plan' => 'plan', 'g_review' => 'review', 'g_weekly' => 'weekly', 'g_streak' => 'streak', 'g_lock' => 'lock', 'g_guard_watch' => 'guard', 'g_guard_danger' => 'guard'];   // (5 Nov., brief notifications) the streak too   // (3 Nov.) the account guardian (guard/guard.php)   // (1 Nov., brief avance 4) the day's lock, sent by GameEngine::recomputeDay

    /** channels: the bell; and the phone ($push: the scheduled task) for the 3 reminders above. A reminder over the day's 2 waits. */
    public static function send(string $uid, string $type, array $params, string $dedupe, string $url, array $opts = [], bool $push = false): bool
    {
        if (!class_exists('Notify', false)) return false;
        $id = Notify::send($uid, $type, $params, ['dedupe_key' => $dedupe, 'action_url' => $url] + $opts + ['over_cap' => 'skip']);
        if ($id) GameEngine::track($uid, 'notification_sent', ['type' => $type]);
        if ($id && $push && !Notify::$quiet && isset(self::PUSH[$type]) && function_exists('wp_notify')) wp_notify(GameEngine::pdo(), $uid, self::PUSH[$type], $url, array_filter($params, 'is_scalar'));
        return (bool) $id;
    }

    /** one pass for one trader (cron every 15 min with $push, and on app open without: the trader is already in the app) */
    public static function run(string $uid, bool $push = false): void
    {
        if (!class_exists('Notify', false)) return;
        $now = (new DateTimeImmutable('@' . GameEngine::ts()))->setTimezone(new DateTimeZone('America/New_York'));
        $hm = $now->format('H:i'); $date = $now->format('Y-m-d'); $dow = (int) $now->format('N');
        if ($hm >= '09:30' && $hm < '17:00') return;                                   // the session, until the 17:00 close: silence
        // at most 2 game reminders per day
        try { $sent = (int) db()->query("SELECT COUNT(*) FROM notifications WHERE user_id = " . db()->quote($uid) . " AND dedupe_key LIKE " . db()->quote("g:%:$date"))->fetchColumn(); }
        catch (Throwable $e) { $sent = 0; }
        if ($sent >= 2) return;
        $p = GameEngine::profile($uid, false); if (!$p) return;
        // only traders who used Sweep in the last 14 days
        $active = (bool) GameEngine::q('SELECT 1 FROM game_days WHERE user_id = ? AND activity = 1 AND trading_day >= ?', [$uid, GameEngine::addDays($date, -14)])->fetchColumn();
        // the session the reminders speak of: today's in New York (the plan before the open, the review and the streak after
        // the close). From 18:00 GameEngine::today() is already the next session: before 14 Oct. (brief 02 part 11), the evening
        // reminders looked at that next day (no review reminder after 18:00, the streak checked on the wrong day)
        $day = $date;
        $g = GameEngine::q('SELECT * FROM game_days WHERE user_id = ? AND trading_day = ?', [$uid, $day])->fetch(PDO::FETCH_ASSOC) ?: null;
        $market = GameEngine::isMarketDay($day);
        // the trader's times (Settings › Notifications; 8:45, 17:15 and 17:00 New York by default), never after 9:30 / 21:00
        $at = ['plan' => '08:45', 'review' => '17:15', 'weekly' => '17:00'];
        if (function_exists('wp_prefs')) { try { foreach (wp_prefs(GameEngine::pdo(), $uid) as $k => $v) $at[$k] = $v['at']; } catch (Throwable $e) { error_log('[Sweep push] prefs: ' . $e->getMessage()); } }
        $todo = [];
        if ($active && $market && $hm >= $at['plan'] && $hm < '09:30' && !($g && (int) $g['plan_valid'])) $todo[] = ['g_plan', [], '#dashboard'];
        if ($active && $market && $hm >= $at['review'] && $hm < '21:00' && $g && !(int) $g['review_done'] && ((int) $g['trades_count'] > 0 || (int) $g['plan_valid'])) $todo[] = ['g_review', [], '#dashboard'];
        $streak = GameEngine::profileState($uid)['streak'];
        // (5 Nov., brief notifications) from 19:30 (before: 21:00), so it can also reach the phone before its quiet hours
        if ($market && $hm >= '19:30' && !($g && (int) $g['is_valid_streak']) && $streak['current'] >= 3) $todo[] = ['g_streak', ['n' => $streak['current']], '#dashboard'];
        if (class_exists('GameV2b', false)) {
            $w = GameV2b::weeklyState($uid, true);
            // the week's recap (brief 01 step 5): ONE notification when it is ready (review of the last trading day, or its close),
            // never again that week, none once the trader has opened it; every trader with a trade this week
            Notify::schema();   // a fresh database may not have the notifications table yet
            if ($w['open'] && empty($w['seen']) && $hm >= $at['weekly'] && $hm < '21:00' && !GameEngine::q('SELECT 1 FROM notifications WHERE user_id = ? AND dedupe_key LIKE ?', [$uid, 'g:g_weekly:' . $w['week'] . ':%'])->fetchColumn())
                $todo[] = ['g_weekly', [], '#dashboard', 'g:g_weekly:' . $w['week'] . ':' . $date];
            if ($dow === 7 && $hm >= '18:00') {
                $mon = GameEngine::monday($date);
                $row = GameEngine::q('SELECT data_json FROM weekly_reviews WHERE user_id = ? AND week_start = ?', [$uid, $mon])->fetchColumn();
                $int = $row ? ((json_decode((string) $row, true) ?: [])['intention'] ?? '') : '';
                if ($row) $todo[] = ['g_intention', ['intention' => $int !== '' ? $int : '—'], '#dashboard'];
            }
        }
        // end of the free trial: day 50 (10 days left) and day 58 (2 days left), with the paid features the trader really uses
        // (billing-core.php sb_pro_used: the same list as the day-50 card on the dashboard; none → what Free keeps)
        if (function_exists('billing_on')) billing_on();
        if (function_exists('sb_live') && sb_live($uid) && function_exists('sb_active_sub') && !sb_active_sub(GameEngine::pdo(), $uid)) {
            try {
                $t = sb_now();
                $g = GameEngine::q("SELECT plan, ends_at FROM billing_grants WHERE uid = ? AND reason IN ('trial','early_access') AND starts_at <= ? AND ends_at > ? ORDER BY ends_at DESC LIMIT 1", [$uid, $t, $t])->fetch(PDO::FETCH_ASSOC);
                $left = $g ? (int) ceil(((int) $g['ends_at'] - $t) / 86400) : 0;
                if ($g && in_array($left, [10, 2], true)) {
                    $used = sb_pro_used(GameEngine::pdo(), $uid);
                    $p = ['days' => $left, 'plan' => ucfirst((string) $g['plan'])];
                    foreach (['en', 'fr', 'es'] as $l) $p['used_' . $l] = sb_pro_used_text($used, $l);
                    if (self::send($uid, 'trial_ending', $p, "trial:$uid:$left", '#plan', ['body_key' => $used ? 'trial_ending.used' : 'trial_ending.none', 'over_cap' => 'quiet'])) $sent++;   // over the day's 2: in the list, quiet
                }
            } catch (Throwable $e) { error_log('[Sweep notify] trial: ' . $e->getMessage()); }
        }
        foreach ($todo as $x) {
            [$type, $params, $url] = $x;
            if ($sent >= 2) break;
            if (self::send($uid, $type, $params, $x[3] ?? "g:$type:$date", $url, [], $push)) $sent++;   // keys end with :date (2 a day at most)
        }
    }
}

/** the retired Month in Review's table (kept), and the payout readiness check */
final class GameWrapped
{
    public static function schema(): void
    {
        static $done = false; if ($done) return; $done = true;
        $my = GameEngine::pdo()->getAttribute(PDO::ATTR_DRIVER_NAME) === 'mysql';
        GameEngine::pdo()->exec('CREATE TABLE IF NOT EXISTS monthly_wrapped (user_id ' . ($my ? 'VARCHAR(120)' : 'TEXT') . ' NOT NULL, month CHAR(7) NOT NULL, data_json TEXT NOT NULL, created_at INT NOT NULL, viewed_at INT NULL, PRIMARY KEY (user_id, month))' . ($my ? ' DEFAULT CHARSET=utf8mb4' : ''));
        // (1 Nov., brief avance 6) « Month in Review »: seen to its last screen (opened is viewed_at); the Today card stays until then
        try { GameEngine::pdo()->query('SELECT done_at FROM monthly_wrapped LIMIT 0'); }
        catch (Throwable $e) { try { GameEngine::pdo()->exec('ALTER TABLE monthly_wrapped ADD COLUMN done_at INT NULL'); } catch (Throwable $x) { /* added at the same time */ } }
    }

    /** payout readiness reaching 100 %: gold moment + badge, once */
    public static function payoutCheck(string $uid): void
    {
        [$cfg, $ready] = GameV2::payoutReadiness($uid);
        if ($cfg && $ready >= 100 && GameEngine::unlock($uid, 'payout_ready', true)) GameEngine::celebrate($uid, 'payout_ready', []);
    }
}
