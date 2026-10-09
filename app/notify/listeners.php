<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli' && realpath((string) ($_SERVER['SCRIPT_FILENAME'] ?? '')) === realpath(__FILE__)) { http_response_code(404); exit; }
/**
 * Sweep — notification types and event listeners.
 * Each later feature adds its types and listeners here (feedback loop, prop alerts, payout readiness, wow moments, streaks).
 *
 * Events fired by api.php (payload: uid, id, doc, prev — doc is null on delete, prev is null on create):
 *   trade.created  trade.updated  trade.deleted
 *   account.created  account.updated  account.deleted
 *   journal.saved  journal.deleted
 *   payout.recorded (new payout)  payout.updated  payout.paid (status became "paid")  payout.deleted
 *   feedback.status_changed (payload: uid = author, item_id, from, to, reply)
 *   user.signed_in (payload: uid)
 *
 * Listeners run synchronously, inside a try/catch: a failing listener is logged and never blocks the save.
 * Keep them fast; anything heavy or time-based belongs in a cron job.
 */

// Types: category, priority, icon. Text lives in the app's i18n dictionary under "<type>.title" / "<type>.body".
Notify::register('welcome', ['category' => 'system', 'icon' => 'bell']);
Notify::register('test_normal', ['category' => 'system', 'icon' => 'info']);
Notify::register('test_celebration', ['category' => 'achievements', 'priority' => 'celebration', 'icon' => 'star']);

// Gamification reminders (game/v2c.php, sent by the game cron every 15 min; never 9:30-16:00 ET, 2 a day at most)
foreach (['g_plan' => 'streaks', 'g_review' => 'streaks', 'g_streak' => 'streaks', 'g_weekly' => 'achievements', 'g_intention' => 'achievements', 'g_wrapped' => 'achievements'] as $type => $cat) {
    Notify::register($type, ['category' => $cat, 'icon' => $cat === 'streaks' ? 'flame' : 'star']);
}

// Listeners: none yet. Example for a later feature:
// Events::on('trade.created', function (array $p): void {
//     Notify::send($p['uid'], 'first_trade', [], ['dedupe_key' => 'ach:first_trade', 'action_url' => '#trades']);
// });

// Feedback loop (Feature 1): the author hears about every step of their idea or bug, « You asked, we built it » when it ships
foreach (['fb_planned' => 'normal', 'fb_in_progress' => 'normal', 'fb_shipped' => 'celebration', 'fb_declined' => 'normal'] as $type => $prio) {
    Notify::register($type, ['category' => 'product_updates', 'priority' => $prio, 'icon' => $prio === 'celebration' ? 'star' : 'message']);
}
Events::on('feedback.status_changed', function (array $p): void {
    $to = (string) ($p['to'] ?? '');
    if (!in_array($to, ['planned', 'in_progress', 'shipped', 'declined'], true) || empty($p['uid'])) return;
    $reply = trim((string) ($p['reply'] ?? ''));
    Notify::send((string) $p['uid'], 'fb_' . $to, ['reply' => $reply !== '' ? mb_strimwidth_safe($reply, 160) : ''],
        ['dedupe_key' => 'fb:' . (int) ($p['item_id'] ?? 0) . ':' . $to, 'action_url' => '#feedback']);
});
function mb_strimwidth_safe(string $s, int $n): string { return strlen($s) <= $n ? $s : rtrim(function_exists('mb_substr') ? mb_substr($s, 0, $n) : substr($s, 0, $n)) . '…'; }

// Crews & buddy (game/v3c.php)
Notify::register('buddy_invite', ['category' => 'achievements', 'icon' => 'user']);
Notify::register('buddy_cheer', ['category' => 'achievements', 'icon' => 'star']);
Notify::register('buddy_swept', ['category' => 'achievements', 'icon' => 'star']);

// « Wow » moments (game/wow.php): discipline milestones, never P&L
foreach (['wow_journal', 'wow_plans', 'wow_reviews', 'wow_days', 'wow_clean_week', 'wow_best_month'] as $type) Notify::register($type, ['category' => 'achievements', 'icon' => 'star']);

// « Your chart is ready » (chart/cron.php) and end-of-trial reminders (game/v2c.php)
Notify::register('chart_ready', ['category' => 'product_updates', 'icon' => 'chart']);
// a firm changed its rules (presets/check.php): what changes for this account, « Apply the new rules » on its page
Notify::register('rules_changed', ['category' => 'prop_alerts', 'icon' => 'info']);
// the 1st of each month: simulated profit, money really received, expenses, net real money (money/money.php)
Notify::register('money_month', ['category' => 'product_updates', 'icon' => 'info']);
Notify::register('trial_ending', ['category' => 'system', 'icon' => 'star']);
