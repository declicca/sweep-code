<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli' && realpath((string) ($_SERVER['SCRIPT_FILENAME'] ?? '')) === realpath(__FILE__)) { http_response_code(404); exit; }
/**
 * Sweep — Gamification V3, step 4: crews (3 to 5 traders) and the accountability buddy (1-to-1).
 *
 * Visible between members only: handle, initial, today's rings, streak, rank, active boss name. Never P&L, trades,
 * amounts or accounts (GameCrew::card() is the only shape returned about another trader).
 * Crew: weekly shared goal = days swept by all members ≥ factor × members (factor 2-5, default 3) → a chest key + 100 XP
 * each, crew streak in weeks. Automatic feed only (sweeps, bosses, ranks, streaks, goal) with emoji reactions: no free chat.
 * Free can join a crew; Pro and Elite can also create one. Everyone can have one buddy.
 */

const GAME_CREW_MAX = 5;
const GAME_CREW_EMOJI = ['👏', '🔥', '💪', '🎯'];

final class GameCrew
{
    private static function q(string $sql, array $a = []): PDOStatement { return GameEngine::q($sql, $a); }

    public static function schema(): void
    {
        static $done = false; if ($done) return; $done = true;
        $pdo = GameEngine::pdo(); $my = $pdo->getAttribute(PDO::ATTR_DRIVER_NAME) === 'mysql';
        $T = $my ? 'VARCHAR(120)' : 'TEXT'; $AI = $my ? 'BIGINT AUTO_INCREMENT PRIMARY KEY' : 'INTEGER PRIMARY KEY AUTOINCREMENT'; $cs = $my ? ' DEFAULT CHARSET=utf8mb4' : '';
        foreach ([
            "CREATE TABLE IF NOT EXISTS crews (id $AI, name VARCHAR(40) NOT NULL, invite_code VARCHAR(12) NOT NULL, owner_id $T NOT NULL, goal_factor INT NOT NULL DEFAULT 3, streak_weeks INT NOT NULL DEFAULT 0, last_goal_week VARCHAR(10) NULL, created_at INT NOT NULL)$cs",
            "CREATE TABLE IF NOT EXISTS crew_members (crew_id BIGINT NOT NULL, user_id $T NOT NULL, joined_at INT NOT NULL, PRIMARY KEY (crew_id, user_id))$cs",
            "CREATE TABLE IF NOT EXISTS crew_events (id $AI, crew_id BIGINT NOT NULL, user_id $T NOT NULL, type VARCHAR(30) NOT NULL, payload_json TEXT NULL, created_at INT NOT NULL)$cs",
            "CREATE TABLE IF NOT EXISTS crew_reactions (event_id BIGINT NOT NULL, user_id $T NOT NULL, emoji VARCHAR(8) NOT NULL, PRIMARY KEY (event_id, user_id))$cs",
            "CREATE TABLE IF NOT EXISTS buddies (user_a $T NOT NULL, user_b $T NOT NULL, status VARCHAR(10) NOT NULL, created_at INT NOT NULL, PRIMARY KEY (user_a, user_b))$cs",
            "CREATE TABLE IF NOT EXISTS buddy_cheers (from_id $T NOT NULL, to_id $T NOT NULL, day VARCHAR(10) NOT NULL, PRIMARY KEY (from_id, day))$cs",
        ] as $s) $pdo->exec($s);
        if ($my) { try { $pdo->exec('ALTER TABLE crews ADD UNIQUE KEY uq_code (invite_code)'); $pdo->exec('ALTER TABLE crew_members ADD UNIQUE KEY uq_member (user_id)'); } catch (Throwable $e) { /* exists */ } }
        else { $pdo->exec('CREATE UNIQUE INDEX IF NOT EXISTS uq_code ON crews (invite_code)'); $pdo->exec('CREATE UNIQUE INDEX IF NOT EXISTS uq_member ON crew_members (user_id)'); }
    }

    private static function handle(string $uid): ?string { return GameSocial::profile($uid)['handle']; }

    /** what one member can see about another: nothing financial */
    public static function card(string $uid, string $me): array
    {
        $d = GameEngine::dayState($uid, GameEngine::today());
        $p = GameEngine::profile($uid, false);
        $streak = $p ? GameEngine::profileState($uid)['streak']['current'] : 0;
        $p = $p ?: ['rank_key' => 'rookie', 'level' => 1];
        $boss = self::q("SELECT boss_id FROM user_bosses WHERE user_id = ? AND status = 'active' LIMIT 1", [$uid])->fetchColumn() ?: null;
        $h = (string) (self::handle($uid) ?? '—');
        return ['handle' => $h, 'initial' => strtoupper(substr($h, 0, 1)), 'me' => $uid === $me, 'rings' => $d['market'] ? $d['rings'] : null, 'swept' => $d['swept'],
                'streak' => $streak, 'rank' => $p['rank_key'], 'level' => (int) $p['level'], 'boss' => $boss];
    }

    /* ───────────── crew ───────────── */

    public static function crewOf(string $uid): ?array
    {
        self::schema();
        return self::q('SELECT c.* FROM crews c JOIN crew_members m ON m.crew_id = c.id WHERE m.user_id = ?', [$uid])->fetch(PDO::FETCH_ASSOC) ?: null;
    }
    private static function members(int $cid): array { return self::q('SELECT user_id FROM crew_members WHERE crew_id = ? ORDER BY joined_at', [$cid])->fetchAll(PDO::FETCH_COLUMN); }
    private static function event(int $cid, string $uid, string $type, array $payload = []): void
    {
        self::q('INSERT INTO crew_events (crew_id, user_id, type, payload_json, created_at) VALUES (?, ?, ?, ?, ?)', [$cid, $uid, $type, $payload ? json_encode($payload) : null, GameEngine::ts()]);
    }

    public static function create(string $uid, string $name): array
    {
        self::schema();
        if (GameV2::plan($uid) === 'free') return ['error' => 'upgrade_required'];
        if (!self::handle($uid)) return ['error' => 'handle_required'];
        if (self::crewOf($uid)) return ['error' => 'already_in_crew'];
        $name = trim(preg_replace('/\s+/', ' ', $name));
        if (strlen($name) < 3 || strlen($name) > 40 || preg_match('/(fuck|shit|nigg|pute|salop|merde)/i', $name)) return ['error' => 'name_invalid'];
        for ($i = 0; $i < 20; $i++) {
            $code = substr(str_replace(['0', 'O', '1', 'I', 'L'], '', strtoupper(bin2hex(random_bytes(6)))), 0, 8);
            if (strlen($code) < 8 || self::q('SELECT 1 FROM crews WHERE invite_code = ?', [$code])->fetchColumn()) continue;
            self::q('INSERT INTO crews (name, invite_code, owner_id, created_at) VALUES (?, ?, ?, ?)', [$name, $code, $uid, GameEngine::ts()]);
            $cid = (int) GameEngine::pdo()->lastInsertId();
            self::q('INSERT INTO crew_members (crew_id, user_id, joined_at) VALUES (?, ?, ?)', [$cid, $uid, GameEngine::ts()]);
            self::event($cid, $uid, 'created');
            GameEngine::track($uid, 'crew_created');
            return ['ok' => true];
        }
        return ['error' => 'retry'];
    }

    public static function join(string $uid, string $code): array
    {
        self::schema();
        if (!self::handle($uid)) return ['error' => 'handle_required'];
        if (self::crewOf($uid)) return ['error' => 'already_in_crew'];
        $c = self::q('SELECT * FROM crews WHERE invite_code = ?', [strtoupper(trim($code))])->fetch(PDO::FETCH_ASSOC);
        if (!$c) return ['error' => 'code_invalid'];
        if (count(self::members((int) $c['id'])) >= GAME_CREW_MAX) return ['error' => 'crew_full'];
        try { self::q('INSERT INTO crew_members (crew_id, user_id, joined_at) VALUES (?, ?, ?)', [$c['id'], $uid, GameEngine::ts()]); } catch (Throwable $e) { return ['error' => 'already_in_crew']; }
        self::event((int) $c['id'], $uid, 'joined');
        GameEngine::track($uid, 'crew_joined');
        return ['ok' => true];
    }

    public static function leave(string $uid): void
    {
        $c = self::crewOf($uid); if (!$c) return;
        self::q('DELETE FROM crew_members WHERE crew_id = ? AND user_id = ?', [$c['id'], $uid]);
        $left = self::members((int) $c['id']);
        if (!$left) { foreach (['crew_events', 'crew_members'] as $t) self::q("DELETE FROM $t WHERE crew_id = ?", [$c['id']]); self::q('DELETE FROM crews WHERE id = ?', [$c['id']]); return; }
        if ($c['owner_id'] === $uid) self::q('UPDATE crews SET owner_id = ? WHERE id = ?', [$left[0], $c['id']]);
        self::event((int) $c['id'], $uid, 'left');
    }

    public static function setGoal(string $uid, int $f): bool
    {
        $c = self::crewOf($uid); if (!$c || $c['owner_id'] !== $uid) return false;
        self::q('UPDATE crews SET goal_factor = ? WHERE id = ?', [max(2, min(5, $f)), $c['id']]);
        return true;
    }

    /** days swept this week by the whole crew; goal met → key + 100 XP each, crew streak in weeks */
    public static function weekProgress(array $c): array
    {
        $mon = GameEngine::monday(GameEngine::today());
        $m = self::members((int) $c['id']);
        $in = implode(',', array_fill(0, count($m), '?'));
        $done = $m ? (int) self::q("SELECT COUNT(*) FROM game_days WHERE user_id IN ($in) AND trading_day BETWEEN ? AND ? AND is_swept = 1", [...$m, $mon, GameEngine::addDays($mon, 4)])->fetchColumn() : 0;
        $goal = (int) $c['goal_factor'] * max(1, count($m));
        if ($done >= $goal && $c['last_goal_week'] !== $mon) {
            $streak = $c['last_goal_week'] === GameEngine::addDays($mon, -7) ? (int) $c['streak_weeks'] + 1 : 1;
            self::q('UPDATE crews SET last_goal_week = ?, streak_weeks = ? WHERE id = ? AND (last_goal_week IS NULL OR last_goal_week <> ?)', [$mon, $streak, $c['id'], $mon]);
            foreach ($m as $u) {
                if (GameEngine::profile($u, false) && GameEngine::awardXp($u, "crew:{$c['id']}:$mon", 100)) {
                    self::q('INSERT INTO user_rewards (user_id, source, reward_type, reward_value, created_at) VALUES (?, ?, ?, ?, ?)', [$u, 'crew', 'key', $mon, GameEngine::ts()]);
                    GameEngine::celebrate($u, 'crew_goal', ['name' => $c['name'], 'xp' => 100]);
                }
            }
            self::event((int) $c['id'], $c['owner_id'], 'goal_met', ['streak' => $streak]);
            GameEngine::track($c['owner_id'], 'crew_goal_met');
        }
        return ['done' => $done, 'goal' => $goal, 'met' => $done >= $goal];
    }

    /** automatic feed: called from GameEngine::celebrate() */
    public static function onCelebrate(string $uid, string $type, array $p): void
    {
        $map = ['sweep' => 'swept', 'boss_defeated' => 'boss', 'streak' => 'streak', 'level' => 'rank'];
        if (!isset($map[$type]) || ($type === 'level' && empty($p['rank_up']))) return;
        $c = self::crewOf($uid);
        if ($c) {
            self::event((int) $c['id'], $uid, $map[$type], array_intersect_key($p, array_flip(['boss', 'n', 'rank'])));
            if ($type === 'sweep') self::weekProgress($c);
        }
        if ($type === 'sweep') self::buddySwept($uid);
    }

    public static function react(string $uid, int $eventId, string $emoji): bool
    {
        if (!in_array($emoji, GAME_CREW_EMOJI, true)) return false;
        $c = self::crewOf($uid); if (!$c) return false;
        if (!self::q('SELECT 1 FROM crew_events WHERE id = ? AND crew_id = ?', [$eventId, $c['id']])->fetchColumn()) return false;
        self::q('DELETE FROM crew_reactions WHERE event_id = ? AND user_id = ?', [$eventId, $uid]);
        self::q('INSERT INTO crew_reactions (event_id, user_id, emoji) VALUES (?, ?, ?)', [$eventId, $uid, $emoji]);
        return true;
    }

    public static function crewState(string $uid): array
    {
        self::schema();
        $c = self::crewOf($uid);
        $out = ['crew' => null, 'can_create' => GameV2::plan($uid) !== 'free', 'has_handle' => (bool) self::handle($uid), 'emoji' => GAME_CREW_EMOJI];
        if (!$c) return $out;
        $m = self::members((int) $c['id']);
        $events = self::q('SELECT * FROM crew_events WHERE crew_id = ? ORDER BY id DESC LIMIT 25', [$c['id']])->fetchAll(PDO::FETCH_ASSOC);
        $feed = [];
        foreach ($events as $e) {
            $rx = []; foreach (self::q('SELECT emoji, COUNT(*) AS n, SUM(CASE WHEN user_id = ? THEN 1 ELSE 0 END) AS mine FROM crew_reactions WHERE event_id = ? GROUP BY emoji', [$uid, $e['id']]) as $r) $rx[$r['emoji']] = ['n' => (int) $r['n'], 'mine' => (bool) $r['mine']];
            $feed[] = ['id' => (int) $e['id'], 'type' => $e['type'], 'handle' => (string) (self::handle($e['user_id']) ?? '—'), 'me' => $e['user_id'] === $uid, 'data' => json_decode((string) $e['payload_json'], true) ?: [], 'at' => (int) $e['created_at'], 'reactions' => $rx];
        }
        $out['crew'] = ['name' => $c['name'], 'code' => $c['invite_code'], 'owner' => $c['owner_id'] === $uid, 'factor' => (int) $c['goal_factor'], 'streak_weeks' => (int) $c['streak_weeks'],
                        'members' => array_map(fn($u) => self::card($u, $uid), $m), 'week' => self::weekProgress($c), 'feed' => $feed, 'max' => GAME_CREW_MAX];
        return $out;
    }

    /* ───────────── buddy (1-to-1, reciprocal) ───────────── */

    private static function buddyRow(string $uid): ?array
    {
        return self::q("SELECT * FROM buddies WHERE (user_a = ? OR user_b = ?) AND status IN ('pending','active') ORDER BY created_at DESC LIMIT 1", [$uid, $uid])->fetch(PDO::FETCH_ASSOC) ?: null;
    }
    public static function invite(string $uid, string $handle): array
    {
        self::schema();
        if (!self::handle($uid)) return ['error' => 'handle_required'];
        if (self::buddyRow($uid)) return ['error' => 'already_buddy'];
        $to = self::q('SELECT user_id FROM social_profile WHERE handle_lc = ?', [strtolower(trim($handle))])->fetchColumn();
        if (!$to || $to === $uid) return ['error' => 'handle_unknown'];
        if (self::buddyRow((string) $to)) return ['error' => 'they_have_buddy'];
        self::q("INSERT INTO buddies (user_a, user_b, status, created_at) VALUES (?, ?, 'pending', ?)", [$uid, $to, GameEngine::ts()]);
        if (class_exists('Notify', false)) Notify::send((string) $to, 'buddy_invite', ['handle' => self::handle($uid)], ['dedupe_key' => 'buddy:inv:' . $uid, 'action_url' => '#dashboard']);
        return ['ok' => true];
    }
    public static function respond(string $uid, bool $accept): void
    {
        $r = self::q("SELECT * FROM buddies WHERE user_b = ? AND status = 'pending'", [$uid])->fetch(PDO::FETCH_ASSOC); if (!$r) return;
        self::q('UPDATE buddies SET status = ? WHERE user_a = ? AND user_b = ?', [$accept ? 'active' : 'ended', $r['user_a'], $r['user_b']]);
        if ($accept) { GameEngine::track($uid, 'buddy_linked'); GameEngine::track($r['user_a'], 'buddy_linked'); }
    }
    public static function end(string $uid): void
    {
        $r = self::buddyRow($uid); if ($r) self::q("UPDATE buddies SET status = 'ended' WHERE user_a = ? AND user_b = ?", [$r['user_a'], $r['user_b']]);
    }
    private static function other(array $r, string $uid): string { return $r['user_a'] === $uid ? $r['user_b'] : $r['user_a']; }
    public static function cheer(string $uid): array
    {
        $r = self::buddyRow($uid); if (!$r || $r['status'] !== 'active') return ['error' => 'no_buddy'];
        try { self::q('INSERT INTO buddy_cheers (from_id, to_id, day) VALUES (?, ?, ?)', [$uid, self::other($r, $uid), GameEngine::today()]); } catch (Throwable $e) { return ['error' => 'once_a_day']; }
        if (class_exists('Notify', false)) Notify::send(self::other($r, $uid), 'buddy_cheer', ['handle' => self::handle($uid)], ['dedupe_key' => 'buddy:cheer:' . $uid . ':' . GameEngine::today(), 'action_url' => '#dashboard']);
        GameEngine::track($uid, 'buddy_encourage');
        return ['ok' => true];
    }
    /** your buddy hears about your sweep; 10 days both swept → buddy_10 */
    private static function buddySwept(string $uid): void
    {
        $r = self::buddyRow($uid); if (!$r || $r['status'] !== 'active') return;
        $o = self::other($r, $uid);
        if (class_exists('Notify', false)) Notify::send($o, 'buddy_swept', ['handle' => self::handle($uid)], ['dedupe_key' => 'buddy:sw:' . $uid . ':' . GameEngine::today(), 'action_url' => '#dashboard']);
        $both = (int) self::q('SELECT COUNT(*) FROM game_days a JOIN game_days b ON b.trading_day = a.trading_day WHERE a.user_id = ? AND b.user_id = ? AND a.is_swept = 1 AND b.is_swept = 1 AND a.trading_day >= ?',
            [$uid, $o, date('Y-m-d', (int) $r['created_at'])])->fetchColumn();
        if ($both >= 10) { GameEngine::unlock($uid, 'buddy_10'); GameEngine::unlock($o, 'buddy_10'); }
    }
    public static function buddyState(string $uid): array
    {
        self::schema();
        $r = self::buddyRow($uid);
        if (!$r) return ['buddy' => null, 'has_handle' => (bool) self::handle($uid)];
        $o = self::other($r, $uid);
        $cheered = (bool) self::q('SELECT 1 FROM buddy_cheers WHERE from_id = ? AND day = ?', [$uid, GameEngine::today()])->fetchColumn();
        return ['buddy' => ['status' => $r['status'], 'incoming' => $r['status'] === 'pending' && $r['user_b'] === $uid, 'card' => $r['status'] === 'active' ? self::card($o, $uid) : ['handle' => self::handle($o)], 'cheered' => $cheered], 'has_handle' => true];
    }
}
