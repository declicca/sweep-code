<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli' && realpath((string) ($_SERVER['SCRIPT_FILENAME'] ?? '')) === realpath(__FILE__)) { http_response_code(404); exit; }
/**
 * Sweep — Gamification V3, step 3: public handle + weekly leagues.
 *
 * Privacy first: every social feature is opt-in and shows only a chosen handle, an initial, the week's XP and a rank.
 * No P&L, trade, amount or account ever leaves this file (GameSocial::member() is the only shape returned to others).
 * Leagues: groups formed on Monday from opted-in traders who were active the week before, by tier (Bronze → Diamond),
 * 20-30 per group; when a tier has fewer than 10 people, tiers are merged into a single league. Never fake players.
 * Ranking = XP earned in the week (chest and season rewards excluded: they are luck, not process).
 * Top 20 % promoted, bottom 15 % relegated (never below Bronze; no relegation after a freeze or a short holiday week).
 */

const GAME_LEAGUE_TIERS = [1 => 'bronze', 2 => 'silver', 3 => 'gold', 4 => 'platinum', 5 => 'diamond'];
const GAME_LEAGUE_MIN = 10;
const GAME_LEAGUE_SIZE = 30;

final class GameSocial
{
    private static function q(string $sql, array $a = []): PDOStatement { return GameEngine::q($sql, $a); }

    public static function schema(): void
    {
        static $done = false; if ($done) return; $done = true;
        $pdo = GameEngine::pdo(); $my = $pdo->getAttribute(PDO::ATTR_DRIVER_NAME) === 'mysql';
        $T = $my ? 'VARCHAR(120)' : 'TEXT'; $AI = $my ? 'BIGINT AUTO_INCREMENT PRIMARY KEY' : 'INTEGER PRIMARY KEY AUTOINCREMENT'; $cs = $my ? ' DEFAULT CHARSET=utf8mb4' : '';
        foreach ([
            "CREATE TABLE IF NOT EXISTS social_profile (user_id $T NOT NULL PRIMARY KEY, handle VARCHAR(20) NULL, handle_lc VARCHAR(20) NULL, league_opt_in INT NOT NULL DEFAULT 0, league_tier INT NOT NULL DEFAULT 1, updated_at INT NOT NULL)$cs",
            "CREATE TABLE IF NOT EXISTS league_groups (id $AI, week_start VARCHAR(10) NOT NULL, tier INT NOT NULL, finalized_at INT NULL, created_at INT NOT NULL)$cs",
            "CREATE TABLE IF NOT EXISTS league_members (group_id BIGINT NOT NULL, user_id $T NOT NULL, week_xp INT NOT NULL DEFAULT 0, final_rank INT NULL, outcome VARCHAR(10) NULL, PRIMARY KEY (group_id, user_id))$cs",
            "CREATE TABLE IF NOT EXISTS moderation_reports (id $AI, reporter_id $T NOT NULL, target_type VARCHAR(20) NOT NULL, target_id VARCHAR(120) NOT NULL, reason VARCHAR(200) NULL, created_at INT NOT NULL, resolved_at INT NULL)$cs",
        ] as $s) $pdo->exec($s);
        if ($my) { try { $pdo->exec('ALTER TABLE social_profile ADD UNIQUE KEY uq_handle (handle_lc)'); } catch (Throwable $e) { /* exists */ } }
        else $pdo->exec('CREATE UNIQUE INDEX IF NOT EXISTS uq_handle ON social_profile (handle_lc)');
    }

    public static function profile(string $uid): array
    {
        self::schema();
        $r = self::q('SELECT * FROM social_profile WHERE user_id = ?', [$uid])->fetch(PDO::FETCH_ASSOC);
        return $r ? ['handle' => $r['handle'], 'league_opt_in' => (bool) $r['league_opt_in'], 'league_tier' => (int) $r['league_tier']] : ['handle' => null, 'league_opt_in' => false, 'league_tier' => 1];
    }

    /** handle: 3-20 letters, digits, _ . - ; unique (case-insensitive); a few words refused */
    public static function save(string $uid, array $b): array
    {
        self::schema();
        $cur = self::profile($uid);
        $handle = array_key_exists('handle', $b) ? trim((string) $b['handle']) : $cur['handle'];
        if ($handle !== null && $handle !== '') {
            if (!preg_match('/^[A-Za-z0-9_.\-]{3,20}$/', $handle)) return ['error' => 'handle_format'];
            if (preg_match('/(admin|sweep|support|moderat|fuck|shit|nigg|pute|salop|merde)/i', $handle) && strcasecmp($handle, (string) $cur['handle']) !== 0) return ['error' => 'handle_refused'];
            $taken = self::q('SELECT user_id FROM social_profile WHERE handle_lc = ? AND user_id <> ?', [strtolower($handle), $uid])->fetchColumn();
            if ($taken) return ['error' => 'handle_taken'];
        } else $handle = null;
        $opt = array_key_exists('league_opt_in', $b) ? (bool) $b['league_opt_in'] : $cur['league_opt_in'];
        if ($opt && !$handle) return ['error' => 'handle_required'];
        $row = [$handle, $handle ? strtolower($handle) : null, $opt ? 1 : 0, GameEngine::ts(), $uid];
        if (self::q('SELECT 1 FROM social_profile WHERE user_id = ?', [$uid])->fetchColumn()) self::q('UPDATE social_profile SET handle = ?, handle_lc = ?, league_opt_in = ?, updated_at = ? WHERE user_id = ?', $row);
        else self::q('INSERT INTO social_profile (handle, handle_lc, league_opt_in, updated_at, user_id) VALUES (?, ?, ?, ?, ?)', $row);
        if ($opt && !$cur['league_opt_in']) { GameEngine::track($uid, 'league_joined'); self::joinLate($uid); }
        if (!$opt) self::leave($uid);
        return ['ok' => true, 'profile' => self::profile($uid)];
    }

    public static function report(string $uid, string $type, string $id, string $reason = ''): void
    {
        self::schema();
        self::q('INSERT INTO moderation_reports (reporter_id, target_type, target_id, reason, created_at) VALUES (?, ?, ?, ?, ?)', [$uid, substr($type, 0, 20), substr($id, 0, 120), substr($reason, 0, 200), GameEngine::ts()]);
    }

    /* ───────────── weeks and XP ───────────── */

    private static function weekBounds(string $mon): array
    {
        $tz = new DateTimeZone('America/New_York');
        return [(new DateTimeImmutable($mon . ' 00:00', $tz))->getTimestamp(), (new DateTimeImmutable($mon . ' 00:00', $tz))->modify('+7 days')->getTimestamp() - 1];
    }
    public static function weekXp(string $uid, string $mon): int
    {
        [$s, $e] = self::weekBounds($mon);
        return (int) self::q("SELECT COALESCE(SUM(xp), 0) FROM xp_events WHERE user_id = ? AND created_at BETWEEN ? AND ? AND event_key NOT LIKE 'season:%' AND event_key NOT LIKE 'chest:%'", [$uid, $s, $e])->fetchColumn();
    }
    private static function thisWeek(): string { return GameEngine::monday(substr((new DateTimeImmutable('@' . GameEngine::ts()))->setTimezone(new DateTimeZone('America/New_York'))->format('Y-m-d'), 0, 10)); }

    /* ───────────── formation and results ───────────── */

    /** form this week's groups once (and close last week's first) */
    public static function ensureWeek(): void
    {
        self::schema();
        $mon = self::thisWeek();
        if (self::q('SELECT 1 FROM league_groups WHERE week_start = ? LIMIT 1', [$mon])->fetchColumn()) return;
        $prev = GameEngine::addDays($mon, -7);
        self::finalize($prev);
        // a sentinel group row makes formation happen once even if two requests race
        $pdo = GameEngine::pdo();
        $pdo->beginTransaction();
        try {
            if (self::q('SELECT 1 FROM league_groups WHERE week_start = ? LIMIT 1', [$mon])->fetchColumn()) { $pdo->commit(); return; }
            [$ps, $pe] = self::weekBounds($prev);
            $rows = self::q("SELECT sp.user_id, sp.league_tier FROM social_profile sp WHERE sp.league_opt_in = 1 AND sp.handle IS NOT NULL
                AND EXISTS (SELECT 1 FROM xp_events x WHERE x.user_id = sp.user_id AND x.created_at BETWEEN ? AND ?)", [$ps, $pe])->fetchAll(PDO::FETCH_ASSOC);
            $byTier = []; foreach ($rows as $r) $byTier[(int) $r['league_tier']][] = $r['user_id'];
            $small = array_filter($byTier, fn($u) => count($u) < GAME_LEAGUE_MIN);
            $groups = [];
            if ($small) {   // any tier under 10 → one single league for everybody (never fake players)
                $all = array_merge(...array_values($byTier ?: [[]]));
                if ($all) $groups[] = [max(array_keys($byTier)), $all];
            } else {
                foreach ($byTier as $tier => $users) { shuffle($users); $n = max(1, (int) ceil(count($users) / GAME_LEAGUE_SIZE)); foreach (array_chunk($users, (int) ceil(count($users) / $n)) as $chunk) $groups[] = [$tier, $chunk]; }
            }
            if (!$groups) $groups[] = [1, []];   // empty marker: late joiners land here
            foreach ($groups as [$tier, $users]) {
                self::q('INSERT INTO league_groups (week_start, tier, created_at) VALUES (?, ?, ?)', [$mon, $tier, GameEngine::ts()]);
                $gid = (int) $pdo->lastInsertId();
                foreach ($users as $u) self::q('INSERT INTO league_members (group_id, user_id) VALUES (?, ?)', [$gid, $u]);
            }
            $pdo->commit();
        } catch (Throwable $e) { $pdo->rollBack(); throw $e; }
    }

    /** someone who opts in mid-week (or was inactive last week) joins the smallest group of the week */
    public static function joinLate(string $uid): void
    {
        self::ensureWeek();
        $mon = self::thisWeek();
        if (self::q('SELECT 1 FROM league_members m JOIN league_groups g ON g.id = m.group_id WHERE g.week_start = ? AND m.user_id = ?', [$mon, $uid])->fetchColumn()) return;
        $gid = self::q('SELECT g.id FROM league_groups g LEFT JOIN league_members m ON m.group_id = g.id WHERE g.week_start = ? GROUP BY g.id ORDER BY COUNT(m.user_id) ASC LIMIT 1', [$mon])->fetchColumn();
        if ($gid) self::q('INSERT INTO league_members (group_id, user_id) VALUES (?, ?)', [$gid, $uid]);
    }
    private static function leave(string $uid): void
    {
        $mon = self::thisWeek();
        self::q('DELETE FROM league_members WHERE user_id = ? AND group_id IN (SELECT id FROM league_groups WHERE week_start = ? AND finalized_at IS NULL)', [$uid, $mon]);
    }

    /** close a week: ranks, promotions, relegations, top-3 rewards, one celebration each */
    public static function finalize(string $mon): void
    {
        $groups = self::q('SELECT * FROM league_groups WHERE week_start = ? AND finalized_at IS NULL', [$mon])->fetchAll(PDO::FETCH_ASSOC);
        $marketDays = 0; for ($i = 0; $i < 5; $i++) if (GameEngine::isMarketDay(GameEngine::addDays($mon, $i))) $marketDays++;
        foreach ($groups as $g) {
            self::q('UPDATE league_groups SET finalized_at = ? WHERE id = ? AND finalized_at IS NULL', [GameEngine::ts(), $g['id']]);
            $members = self::q('SELECT user_id FROM league_members WHERE group_id = ?', [$g['id']])->fetchAll(PDO::FETCH_COLUMN);
            $scores = []; foreach ($members as $u) $scores[$u] = self::weekXp($u, $mon);
            arsort($scores);
            $n = count($scores); $up = (int) floor($n * 0.2); $down = (int) floor($n * 0.15);
            $rank = 0;
            foreach ($scores as $u => $xp) {
                $rank++;
                $p = self::profile($u); $tier = $p['league_tier'];
                $froze = (bool) GameEngine::q('SELECT 1 FROM game_days WHERE user_id = ? AND trading_day BETWEEN ? AND ? AND freeze_used = 1', [$u, $mon, GameEngine::addDays($mon, 4)])->fetchColumn();
                $outcome = 'stayed';
                if ($n >= 3 && $rank <= $up && $xp > 0 && $tier < 5) { $outcome = 'promoted'; $tier++; }
                elseif ($n >= 3 && $rank > $n - $down && $tier > 1 && !$froze && $marketDays >= 5) { $outcome = 'relegated'; $tier--; }
                self::q('UPDATE league_members SET week_xp = ?, final_rank = ?, outcome = ? WHERE group_id = ? AND user_id = ?', [$xp, $rank, $outcome, $g['id'], $u]);
                self::q('UPDATE social_profile SET league_tier = ? WHERE user_id = ?', [$tier, $u]);
                if (!GameEngine::profile($u, false)) continue;   // no game profile: rank and tier only
                if ($rank <= 3 && $xp > 0) GameEngine::awardXp($u, "league:$mon", [1 => 150, 2 => 100, 3 => 75][$rank]);
                if ($outcome === 'promoted') { GameEngine::unlock($u, 'league_promoted', true); GameEngine::track($u, 'league_promoted', ['tier' => $tier]); }
                GameEngine::celebrate($u, 'league_result', ['rank' => $rank, 'of' => $n, 'outcome' => $outcome, 'tier' => $tier, 'xp' => $rank <= 3 && $xp > 0 ? [1 => 150, 2 => 100, 3 => 75][$rank] : 0]);
            }
        }
    }

    /* ───────────── read model (the only shape others ever see) ───────────── */

    private static function member(array $r, string $me): array
    {
        $h = (string) $r['handle'];
        return ['handle' => $h, 'initial' => strtoupper(substr($h, 0, 1)), 'xp' => (int) $r['xp'], 'me' => $r['user_id'] === $me, 'ref' => substr(sha1('m' . $r['user_id']), 0, 12)];
    }

    public static function league(string $uid): array
    {
        self::schema();
        $p = self::profile($uid);
        $out = ['profile' => $p, 'tiers' => GAME_LEAGUE_TIERS, 'group' => null];
        if (!$p['league_opt_in']) return $out;
        self::ensureWeek(); self::joinLate($uid);
        $mon = self::thisWeek();
        $g = self::q('SELECT g.* FROM league_groups g JOIN league_members m ON m.group_id = g.id WHERE g.week_start = ? AND m.user_id = ?', [$mon, $uid])->fetch(PDO::FETCH_ASSOC);
        if (!$g) return $out;
        $rows = self::q('SELECT m.user_id, sp.handle FROM league_members m JOIN social_profile sp ON sp.user_id = m.user_id WHERE m.group_id = ? AND sp.league_opt_in = 1 AND sp.handle IS NOT NULL', [$g['id']])->fetchAll(PDO::FETCH_ASSOC);
        foreach ($rows as &$r) $r['xp'] = self::weekXp($r['user_id'], $mon);
        unset($r);
        usort($rows, fn($a, $b) => $b['xp'] <=> $a['xp'] ?: strcmp((string) $a['handle'], (string) $b['handle']));
        $n = count($rows);
        $end = (new DateTimeImmutable($mon . ' 00:00', new DateTimeZone('America/New_York')))->modify('+7 days')->getTimestamp();
        $out['group'] = ['tier' => (int) $g['tier'], 'members' => array_map(fn($r) => self::member($r, $uid), $rows), 'promote' => (int) floor($n * 0.2), 'relegate' => (int) floor($n * 0.15), 'ends_at' => $end, 'single' => true];
        return $out;
    }
}
