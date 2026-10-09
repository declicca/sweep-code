<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli' && realpath((string) ($_SERVER['SCRIPT_FILENAME'] ?? '')) === realpath(__FILE__)) { http_response_code(404); exit; }
/**
 * Sweep — Gamification V3, step 2: monthly seasons with a free and a Pro track.
 *
 * - One season = one calendar month, a name and a ring theme of its own.
 * - Season points = XP earned during the month (season rewards themselves are excluded, so the pass can't feed itself).
 * - 30 tiers of 85 points: about 18 perfect days reach tier 30 (regularity, not volume).
 * - Free track: one reward every 3 tiers. Pro track: every tier (Pro and Elite; upgrading mid-season unlocks what was
 *   already reached, since rewards are claimed). Elite: an exclusive theme at tier 30. Nothing is ever sold per tier.
 */

const GAME_SEASON_TIER = 85;
const GAME_SEASON_TIERS = 30;
const GAME_SEASON_FIRST = '2026-10';   // Season 1
const GAME_SEASON_NAMES = ['Liquidity', 'Momentum', 'Patience', 'Precision', 'Edge', 'Flow', 'Focus', 'Clarity', 'Balance', 'Resolve', 'Discipline', 'Mastery'];

final class GameSeason
{
    private static function q(string $sql, array $a = []): PDOStatement { return GameEngine::q($sql, $a); }

    public static function schema(): void
    {
        static $done = false; if ($done) return; $done = true;
        $my = GameEngine::pdo()->getAttribute(PDO::ATTR_DRIVER_NAME) === 'mysql';
        GameEngine::pdo()->exec('CREATE TABLE IF NOT EXISTS user_season (user_id ' . ($my ? 'VARCHAR(120)' : 'TEXT') . ' NOT NULL, season CHAR(7) NOT NULL, claimed_free TEXT NULL, claimed_premium TEXT NULL, PRIMARY KEY (user_id, season))' . ($my ? ' DEFAULT CHARSET=utf8mb4' : ''));
    }

    public static function current(): array
    {
        $m = substr(GameEngine::today(), 0, 7);
        $n = ((int) substr($m, 0, 4) - (int) substr(GAME_SEASON_FIRST, 0, 4)) * 12 + (int) substr($m, 5, 2) - (int) substr(GAME_SEASON_FIRST, 5, 2) + 1;
        $end = (new DateTimeImmutable($m . '-01 23:59:59', new DateTimeZone('America/New_York')))->modify('last day of this month')->getTimestamp();
        return ['id' => $m, 'number' => max(1, $n), 'name' => GAME_SEASON_NAMES[(max(1, $n) - 1) % 12], 'ends_at' => $end, 'theme' => 'ring_s' . str_replace('-', '', $m)];
    }

    public static function points(string $uid, string $m): int
    {
        $tz = new DateTimeZone('America/New_York');
        $s = (new DateTimeImmutable($m . '-01 00:00', $tz))->getTimestamp();
        $e = (new DateTimeImmutable($m . '-01 00:00', $tz))->modify('first day of next month')->getTimestamp() - 1;
        return (int) self::q("SELECT COALESCE(SUM(xp), 0) FROM xp_events WHERE user_id = ? AND created_at BETWEEN ? AND ? AND event_key NOT LIKE 'season:%'", [$uid, $s, $e])->fetchColumn();
    }

    /** reward of a tier on a track: [type, value] */
    public static function reward(int $tier, string $track, array $season): ?array
    {
        if ($track === 'free') {
            if ($tier % 3) return null;
            return [3 => ['xp', 50], 6 => ['freeze', 1], 9 => ['key', 1], 12 => ['xp', 100], 15 => ['ai_credits', 3], 18 => ['freeze', 1], 21 => ['key', 1], 24 => ['xp', 150], 27 => ['ai_credits', 3], 30 => ['cosmetic', $season['theme']]][$tier];
        }
        if ($tier === 30) return ['badge', 'season_' . str_replace('-', '', $season['id'])];
        if ($tier === 15) return ['cosmetic', ['ring_aurora', 'ring_ember', 'ring_mono', 'ring_violet', 'ring_ocean'][($season['number'] - 1) % 5]];
        return [1 => ['xp', 40], 2 => ['ai_credits', 3], 0 => ['key', 1]][$tier % 3] ?? ['xp', 40];
    }

    public static function state(string $uid): array
    {
        self::schema();
        $s = self::current();
        $pts = self::points($uid, $s['id']);
        $row = self::q('SELECT * FROM user_season WHERE user_id = ? AND season = ?', [$uid, $s['id']])->fetch(PDO::FETCH_ASSOC) ?: [];
        $plan = GameV2::plan($uid);
        $cf = json_decode((string) ($row['claimed_free'] ?? '[]'), true) ?: []; $cp = json_decode((string) ($row['claimed_premium'] ?? '[]'), true) ?: [];
        $tier = min(GAME_SEASON_TIERS, intdiv($pts, GAME_SEASON_TIER));
        $tiers = [];
        for ($i = 1; $i <= GAME_SEASON_TIERS; $i++) {
            $f = self::reward($i, 'free', $s); $p = self::reward($i, 'premium', $s);
            $tiers[] = ['tier' => $i, 'free' => $f ? ['type' => $f[0], 'value' => $f[1], 'claimed' => in_array($i, $cf, true)] : null,
                        'premium' => $p ? ['type' => $p[0], 'value' => $p[1], 'claimed' => in_array($i, $cp, true)] : null];
        }
        return $s + ['points' => $pts, 'tier' => $tier, 'per_tier' => GAME_SEASON_TIER, 'tiers' => $tiers, 'premium' => $plan !== 'free', 'elite' => $plan === 'elite',
                     'claimable' => count(array_filter($tiers, fn($t) => $t['tier'] <= $tier && (($t['free'] && !$t['free']['claimed']) || ($plan !== 'free' && $t['premium'] && !$t['premium']['claimed']))))];
    }

    public static function claim(string $uid, int $tier, string $track): array
    {
        self::schema();
        $s = self::current();
        if ($tier < 1 || $tier > GAME_SEASON_TIERS || !in_array($track, ['free', 'premium'], true)) return ['error' => 'invalid'];
        if (intdiv(self::points($uid, $s['id']), GAME_SEASON_TIER) < $tier) return ['error' => 'not_reached'];
        $plan = GameV2::plan($uid);
        if ($track === 'premium' && $plan === 'free') return ['error' => 'upgrade_required'];
        $rw = self::reward($tier, $track, $s); if (!$rw) return ['error' => 'invalid'];
        // claimed once, recorded through the XP ledger's unique key (race-safe)
        if (!GameEngine::awardXp($uid, "season:{$s['id']}:$track:$tier", $rw[0] === 'xp' ? (int) $rw[1] : 0)) return ['error' => 'claimed'];
        $col = $track === 'free' ? 'claimed_free' : 'claimed_premium';
        $row = self::q('SELECT * FROM user_season WHERE user_id = ? AND season = ?', [$uid, $s['id']])->fetch(PDO::FETCH_ASSOC);
        $list = json_decode((string) ($row[$col] ?? '[]'), true) ?: []; $list[] = $tier;
        if ($row) self::q("UPDATE user_season SET $col = ? WHERE user_id = ? AND season = ?", [json_encode(array_values(array_unique($list))), $uid, $s['id']]);
        else self::q("INSERT INTO user_season (user_id, season, $col) VALUES (?, ?, ?)", [$uid, $s['id'], json_encode($list)]);
        $given = [['type' => $rw[0], 'value' => $rw[1]]];
        self::grant($uid, $rw[0], $rw[1]);
        if ($tier === 30 && $track === 'premium' && $plan === 'elite') { $ex = 'ring_e' . str_replace('-', '', $s['id']); self::grant($uid, 'cosmetic', $ex); $given[] = ['type' => 'cosmetic', 'value' => $ex]; }
        GameEngine::q('INSERT INTO user_rewards (user_id, source, reward_type, reward_value, created_at) VALUES (?, ?, ?, ?, ?)', [$uid, 'season', $rw[0], (string) $rw[1], GameEngine::ts()]);
        GameEngine::track($uid, 'season_tier_claimed', ['tier' => $tier, 'track' => $track]);
        return ['items' => $given];
    }

    private static function grant(string $uid, string $type, $value): void
    {
        if ($type === 'freeze') { $p = GameEngine::profile($uid, false); if ((int) $p['freezes_available'] < GameEngine::freezeQuota($uid) + 1) self::q('UPDATE user_game_profile SET freezes_available = freezes_available + 1 WHERE user_id = ?', [$uid]); }
        elseif ($type === 'key') self::q('INSERT INTO user_rewards (user_id, source, reward_type, reward_value, created_at) VALUES (?, ?, ?, ?, ?)', [$uid, 'season', 'key', 'season', GameEngine::ts()]);
        elseif ($type === 'cosmetic') { GameV2b::schema(); try { self::q('INSERT INTO user_cosmetics (user_id, cosmetic_id, equipped) VALUES (?, ?, 0)', [$uid, (string) $value]); } catch (Throwable $e) { /* owned */ } }
        elseif ($type === 'ai_credits' && function_exists('sb_ai_refund')) { try { for ($i = 0; $i < (int) $value; $i++) sb_ai_refund(GameEngine::pdo(), $uid, 'chat'); } catch (Throwable $e) { /* billing off */ } }
        elseif ($type === 'badge') {
            // one badge per season, created on the fly (not in the static catalog)
            try { self::q('INSERT INTO user_badges (user_id, badge_id, unlocked_at) VALUES (?, ?, ?)', [$uid, (string) $value, GameEngine::ts()]); GameEngine::celebrate($uid, 'badge', ['id' => (string) $value, 'rarity' => 'epic', 'xp' => 0]); } catch (Throwable $e) { /* owned */ }
        }
    }
}
