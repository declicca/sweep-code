<?php
declare(strict_types=1);
/**
 * Sweep — the discovery missions (SWEEP.md step 5, section 5): 15 missions over about 3 weeks, each one found by doing it.
 *  - Each mission is ticked by a behaviour Sweep reads (read-only, from the trader's own data), never by opening a page;
 *    the first time it is seen done: 20 XP, once (awardXp « disc:N »).
 *  - One mission a trading day at most (a trader of « More than a year »: two), a late one stays doable.
 *  - A function not yet discovered is not shown (the app hides it): Sweep AI, My money, the guided plan, « My progress » beyond
 *    the level and the streak. The context opens one earlier: My money with a first payout, the guided plan when chosen.
 *  - Existing accounts lose nothing: users.discovery_done = 1 for every account that existed when the missions went live
 *    (set once, the first time this runs, never removed). « Show everything » (Settings › My routine) sets it too.
 *  - Tests: SWEEP_DISC_ALL=1 (tools/run.sh, par.py) treats every account as done except one marked 2 (e2e_discovery).
 */

final class GameDiscovery
{
    /** n => [unlock trading day, the feature it shows (or '')] — the table of SWEEP.md 5.2 */
    const MISSIONS = [
        1 => [1, ''], 2 => [1, ''], 3 => [1, ''], 4 => [1, ''], 5 => [2, ''], 6 => [2, ''], 7 => [3, ''], 8 => [3, ''],
        9 => [4, ''], 10 => [4, ''], 11 => [5, ''], 12 => [6, 'money'], 13 => [7, ''], 14 => [8, 'guided'], 15 => [11, 'game'],
    ];
    const XP = 20;
    const SYNCED = ['ninjatrader', 'quantower'];

    public static function schema(): void
    {
        static $done = false; if ($done) return; $done = true;
        $pdo = GameEngine::pdo();
        $cols = [];
        try {
            $my = $pdo->getAttribute(PDO::ATTR_DRIVER_NAME) === 'mysql';
            $cols = $my ? array_column($pdo->query('SHOW COLUMNS FROM users')->fetchAll(PDO::FETCH_ASSOC), 'Field') : array_column($pdo->query('PRAGMA table_info(users)')->fetchAll(PDO::FETCH_ASSOC), 'name');
            if (!in_array('discovery_done', $cols, true)) {
                $pdo->exec('ALTER TABLE users ADD COLUMN discovery_done INT NOT NULL DEFAULT 0');
                // the missions go live: every account that exists now keeps everything it sees (once, never removed)
                $pdo->exec('UPDATE users SET discovery_done = 1');
            }
        } catch (Throwable $e) { error_log('[Sweep discovery] ' . $e->getMessage()); }
    }

    private static function user(string $uid): array
    {
        self::schema();
        $r = GameEngine::q('SELECT created_at, experience, discovery_done FROM users WHERE id = ?', [$uid])->fetch(PDO::FETCH_ASSOC) ?: [];
        return $r;
    }
    /** true: the trader sees everything (an account from before, « Show everything », or all done) */
    public static function allShown(string $uid, ?array $u = null): bool
    {
        $u ??= self::user($uid); $v = (int) ($u['discovery_done'] ?? 1);
        if (getenv('SWEEP_DISC_ALL')) return $v !== 2;
        return $v === 1;
    }

    /** the trading days since sign-up, the sign-up day being 1 */
    private static function day(array $u): int
    {
        $c = (string) ($u['created_at'] ?? ''); $ts = ctype_digit($c) ? (int) $c : (strtotime($c . (preg_match('/[zZ]|[+-]\d\d:?\d\d$/', $c) ? '' : ' UTC')) ?: time());
        $d0 = (new DateTimeImmutable('@' . ($ts + 6 * 3600)))->setTimezone(new DateTimeZone('America/New_York'))->format('Y-m-d');   // the session of the sign-up
        $today = GameEngine::today(); $n = 0;
        for ($d = $d0; $d <= $today && $n < 400; $d = GameEngine::addDays($d, 1)) if (GameEngine::isMarketDay($d) || $d === $d0) $n++;
        return max(1, $n);
    }

    /** which missions are done, from the trader's data (read-only) */
    public static function doneSet(string $uid): array
    {
        $real = fn(array $l) => array_values(array_filter($l, fn($x) => is_array($x) && empty($x['demo'])));
        $acc = $real(GameEngine::docs($uid, 'accounts')); $tr = array_values(array_filter($real(GameEngine::docs($uid, 'trades')), fn($t) => empty($t['untracked'])));
        $jr = $real(GameEngine::docs($uid, 'journals')); $pay = $real(GameEngine::docs($uid, 'payouts'));
        $set = (GameEngine::docs($uid, 'meta')['settings'] ?? []);
        $done = [];
        if ($acc) $done[1] = true;
        $plans = array_filter($jr, fn($j) => !empty($j['pre']['bias']));
        if ($plans) $done[2] = true;
        if ($tr) $done[3] = true;
        if (array_filter($jr, fn($j) => !empty($j['post']['reviewed_at']))) $done[4] = true;
        try { if ((int) GameEngine::q('SELECT COUNT(*) FROM game_days WHERE user_id = ? AND compliant_count > 0', [$uid])->fetchColumn() > 0) $done[5] = true; } catch (Throwable $e) { /* no game yet */ }
        if (array_filter($tr, fn($t) => trim((string) ($t['setup'] ?? '')) !== '')) $done[6] = true;
        if (array_filter($tr, fn($t) => trim((string) (($t['review'] ?? [])['lesson'] ?? '')) !== '')) $done[7] = true;
        $synced = array_filter($tr, fn($t) => in_array((string) ($t['source'] ?? ''), self::SYNCED, true) || !empty($t['import_key']));
        if (!$synced) { try { $synced = (int) GameEngine::q("SELECT COUNT(*) FROM sync_connections WHERE user_id = ?", [$uid])->fetchColumn() > 0; } catch (Throwable $e) { $synced = false; } }
        if ($synced) $done[8] = true;
        // 9: a closed day whose loss stayed within the morning's risk allowed (the plan's max loss)
        $byDay = []; foreach ($tr as $t) { $d = (string) ($t['date'] ?? ''); $byDay[$d] = ($byDay[$d] ?? 0) + (int) ($t['pnl_c'] ?? 0) - (int) ($t['fees_c'] ?? 0); }
        foreach ($jr as $j) {
            $d = (string) ($j['id'] ?? ''); if (empty($j['post']['reviewed_at']) || !isset($byDay[$d])) continue;
            $ml = (int) round(((float) str_replace([',', '$', ' '], ['.', '', ''], (string) ($j['pre']['max_loss'] ?? '0'))) * 100);
            if ($ml > 0 && $byDay[$d] > -$ml) { $done[9] = true; break; }
        }
        if (!empty(($set['discovery'] ?? [])['device'])) $done[10] = true;   // installed or reminders on: said by the device
        try { if ((int) GameEngine::q('SELECT COUNT(*) FROM weekly_reviews WHERE user_id = ?', [$uid])->fetchColumn() > 0) $done[11] = true; } catch (Throwable $e) { /* no weekly yet */ }
        if ($pay || (($set['realnet'] ?? [])['state'] ?? '') === 'done') $done[12] = true;
        // 13: a plan that takes the rule Stats proposes, or a trade in the plan with a setup (the edge grows from there)
        if (array_filter($jr, fn($j) => trim((string) (($j['pre'] ?? [])['rule'] ?? '')) !== '')) $done[13] = true;
        if (array_filter($jr, fn($j) => !empty($j['fiche']))) $done[14] = true;
        try { $st = GameEngine::q('SELECT streak_best FROM user_game_profile WHERE user_id = ?', [$uid])->fetchColumn(); if ((int) $st >= 3) $done[15] = true; } catch (Throwable $e) { /* no profile yet */ }
        return $done;
    }

    public static function state(string $uid): array
    {
        $u = self::user($uid);
        if (self::allShown($uid, $u)) return ['all' => true, 'shown' => ['money' => true, 'guided' => true, 'game' => true, 'ai' => true]];
        $done = self::doneSet($uid);
        foreach (array_keys($done) as $n) { if (GameEngine::awardXp($uid, 'disc:' . $n, self::XP)) GameEngine::track($uid, 'discovery_done', ['n' => $n]); }
        $day = self::day($u); $fast = ($u['experience'] ?? '') === 'gt1';
        $unlock = fn(int $n) => $fast ? (int) ceil(self::MISSIONS[$n][0] / 2) : self::MISSIONS[$n][0];
        $cur = null; foreach (self::MISSIONS as $n => $m) { if (empty($done[$n])) { $cur = $n; break; } }
        $open = $cur !== null && $unlock($cur) <= $day;
        $set = (GameEngine::docs($uid, 'meta')['settings'] ?? []);
        $pay = array_filter(GameEngine::docs($uid, 'payouts'), fn($x) => is_array($x) && empty($x['demo']));
        $shown = [
            'money' => !empty($done[12]) || ($open && $cur === 12) || (bool) $pay,
            'guided' => !empty($done[14]) || ($open && $cur === 14) || (($set['pm_mode'] ?? '') === 'full'),
            'game' => !empty($done[15]),
            'ai' => !empty($done[15]) || $day >= 11,
        ];
        if (count($done) >= count(self::MISSIONS)) { GameEngine::q('UPDATE users SET discovery_done = 1 WHERE id = ? AND discovery_done <> 1', [$uid]); return ['all' => true, 'shown' => array_fill_keys(array_keys($shown), true)]; }
        return ['all' => false, 'day' => $day, 'done' => array_keys($done), 'current' => $open ? $cur : null, 'next' => $cur, 'of' => count(self::MISSIONS), 'shown' => $shown];
    }

    /** « Show everything »: every mission done, everything shown (never undone) */
    public static function showAll(string $uid): array
    {
        self::schema();
        GameEngine::q('UPDATE users SET discovery_done = 1 WHERE id = ?', [$uid]);
        return self::state($uid);
    }
}

function discovery_route(string $route, string $method, string $uid): void
{
    if ($route === 'api/game/discovery' && $method === 'GET') json_out(200, GameDiscovery::state($uid));
    if ($route === 'api/game/discovery/all' && $method === 'POST') json_out(200, GameDiscovery::showAll($uid));
}
