<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli' && realpath((string) ($_SERVER['SCRIPT_FILENAME'] ?? '')) === realpath(__FILE__)) { http_response_code(404); exit; }
/**
 * Sweep — Gamification V2, step 2: weekly review + chest, cosmetics, Edge Reveal, comeback quest.
 *
 * - Weekly review: Friday 17:00 ET → Sunday 23:59 ET. 50 XP, badges weekly_4 / weekly_12, an intention shown all next week.
 * - Chest: opened once per weekly review, richer with a key (3 missions done). Never sold, odds shown to the trader.
 * - Edge Reveal: statistics in PHP (R and %, never dollars), wording by Sweep AI (cached, not counted in the trader's
 *   allowance, within the global daily budget) or a translated template. Free: first week of the month; Pro/Elite weekly;
 *   Elite can open a second candidate.
 * - Comeback quest: after a lost streak of 5+ or 7+ quiet market days: review, plan before the open, sweep a day within
 *   5 market days → half of the lost streak back (once per 30 days) + the comeback badge.
 */

const GAME_CHEST = [   // reward => [normal %, with key %]
    'freeze' => [20, 40], 'cosmetic' => [15, 30], 'ai_credits' => [15, 25], 'pro_days' => [5, 10], 'lucky' => [3, 6],
];
const GAME_COSMETICS = ['ring_default', 'ring_aurora', 'ring_ember', 'ring_mono', 'ring_violet', 'ring_ocean'];
/** points per 1.00 of price, to express a typed stop as risk (R) when risk_c is missing */
const GAME_POINT_VALUE = ['NQ' => 20, 'MNQ' => 2, 'ES' => 50, 'MES' => 5, 'YM' => 5, 'MYM' => 0.5, 'RTY' => 50, 'M2K' => 5, 'CL' => 1000, 'MCL' => 100, 'GC' => 100, 'MGC' => 10, 'SI' => 5000, '6E' => 125000];

final class GameV2b
{
    private static function q(string $sql, array $a = []): PDOStatement { return GameEngine::q($sql, $a); }

    public static function schema(): void
    {
        static $done = false; if ($done) return; $done = true;
        $pdo = GameEngine::pdo(); $my = $pdo->getAttribute(PDO::ATTR_DRIVER_NAME) === 'mysql';
        $T = $my ? 'VARCHAR(120)' : 'TEXT'; $AI = $my ? 'BIGINT AUTO_INCREMENT PRIMARY KEY' : 'INTEGER PRIMARY KEY AUTOINCREMENT'; $cs = $my ? ' DEFAULT CHARSET=utf8mb4' : '';
        foreach ([
            "CREATE TABLE IF NOT EXISTS weekly_reviews (user_id $T NOT NULL, week_start VARCHAR(10) NOT NULL, data_json TEXT NOT NULL, completed_at INT NOT NULL, chest_opened_at INT NULL, PRIMARY KEY (user_id, week_start))$cs",
            "CREATE TABLE IF NOT EXISTS edge_reveals (id $AI, user_id $T NOT NULL, week_start VARCHAR(10) NOT NULL, slot INT NOT NULL DEFAULT 1, insight_key VARCHAR(40) NOT NULL, data_json TEXT NOT NULL, text_json TEXT NULL, ai_used INT NOT NULL DEFAULT 0, revealed_at INT NULL)$cs",
            "CREATE TABLE IF NOT EXISTS user_cosmetics (user_id $T NOT NULL, cosmetic_id VARCHAR(40) NOT NULL, equipped INT NOT NULL DEFAULT 0, PRIMARY KEY (user_id, cosmetic_id))$cs",
            "CREATE TABLE IF NOT EXISTS user_quests (id $AI, user_id $T NOT NULL, kind VARCHAR(20) NOT NULL, started_on VARCHAR(10) NOT NULL, ends_on VARCHAR(10) NOT NULL, lost_streak INT NOT NULL DEFAULT 0, completed_at INT NULL, created_at INT NOT NULL)$cs",
        ] as $s) $pdo->exec($s);
        if ($my) { try { $pdo->exec('ALTER TABLE edge_reveals ADD UNIQUE KEY uq_reveal (user_id, week_start, slot)'); } catch (Throwable $e) { /* exists */ } }
        else $pdo->exec('CREATE UNIQUE INDEX IF NOT EXISTS uq_reveal ON edge_reveals (user_id, week_start, slot)');
    }

    /* ───────────── weekly review window ───────────── */

    /**
     * The week whose recap is ready right now (its Monday), or null — brief 01 step 5. The recap of a week is ready from the
     * end of its last trading day (Friday, or Thursday when Friday is a market holiday): as soon as that day's review is
     * done, or at its 17:00 ET close otherwise, until Sunday 23:59 ET. New York time, whatever the trader's own time zone.
     * For a trader ($uid): only a week with at least one trade has a recap. Without $uid: the time rule only.
     */
    public static function openWeek(?string $uid = null): ?string
    {
        $now = (new DateTimeImmutable('@' . GameEngine::ts()))->setTimezone(new DateTimeZone('America/New_York'));
        $today = $now->format('Y-m-d'); $mon = GameEngine::monday($today); $last = null;
        for ($i = 4; $i >= 0; $i--) { $d = GameEngine::addDays($mon, $i); if (GameEngine::isMarketDay($d)) { $last = $d; break; } }
        if ($last === null || $today < $last) return null;
        $closed = $today > $last || $now->format('H:i') >= '17:00';
        if ($uid === null) return $closed ? $mon : null;
        $w = self::q('SELECT SUM(trades_count) AS n, MAX(CASE WHEN trading_day = ? THEN review_done ELSE 0 END) AS r FROM game_days WHERE user_id = ? AND trading_day >= ? AND trading_day <= ?',
            [$last, $uid, $mon, GameEngine::addDays($mon, 4)])->fetch(PDO::FETCH_ASSOC) ?: [];
        if ((int) ($w['n'] ?? 0) < 1) return null;   // no trade this week: no recap, no reminder
        return ($closed || (int) ($w['r'] ?? 0) === 1) ? $mon : null;
    }
    /** the trader opened this week's recap in the app (no reminder, no « Your week » email after that) */
    public static function seen(string $uid, string $mon): bool
    {
        return (bool) self::q("SELECT 1 FROM game_analytics WHERE user_id = ? AND event = 'weekly_opened' AND meta_json = ?", [$uid, json_encode(['week' => $mon])])->fetchColumn();
    }
    public static function markSeen(string $uid, string $mon): void { if (!self::seen($uid, $mon)) GameEngine::track($uid, 'weekly_opened', ['week' => $mon]); }

    public static function weekSummary(string $uid, string $mon): array
    {
        $days = [];
        for ($i = 0; $i < 5; $i++) {
            $d = GameEngine::addDays($mon, $i);
            $g = self::q('SELECT ring_plan, ring_execution, ring_review, is_swept, day_off FROM game_days WHERE user_id = ? AND trading_day = ?', [$uid, $d])->fetch(PDO::FETCH_ASSOC) ?: null;
            $days[] = ['day' => $d, 'market' => GameEngine::isMarketDay($d), 'rings' => $g ? ['plan' => (int) $g['ring_plan'], 'execution' => (int) $g['ring_execution'], 'review' => (int) $g['ring_review']] : null, 'swept' => $g && (int) $g['is_swept'] === 1];
        }
        $m = self::q('SELECT COUNT(*) AS n, SUM(CASE WHEN completed_at IS NOT NULL THEN 1 ELSE 0 END) AS done FROM user_missions WHERE user_id = ? AND week_start = ?', [$uid, $mon])->fetch(PDO::FETCH_ASSOC) ?: [];
        $p = GameEngine::profileState($uid);
        return ['days' => $days, 'swept' => count(array_filter($days, fn($d) => $d['swept'])), 'streak' => $p['streak']['current'], 'missions' => ['done' => (int) ($m['done'] ?? 0), 'total' => (int) ($m['n'] ?? 0)]];
    }

    public static function weeklyState(string $uid, bool $light = false): array
    {
        self::schema();
        $mon = self::openWeek($uid);
        $last = self::q('SELECT week_start, data_json, chest_opened_at FROM weekly_reviews WHERE user_id = ? ORDER BY week_start DESC LIMIT 1', [$uid])->fetch(PDO::FETCH_ASSOC) ?: null;
        $intention = null;
        if ($last && $last['week_start'] === GameEngine::addDays(GameEngine::monday(GameEngine::today()), -7)) $intention = (json_decode((string) $last['data_json'], true) ?: [])['intention'] ?? null;
        $keys = (int) self::q("SELECT COUNT(*) FROM user_rewards WHERE user_id = ? AND reward_type = 'key' AND used_at IS NULL", [$uid])->fetchColumn();
        if (!$mon) return ['open' => false, 'intention' => $intention, 'keys' => $keys];
        $row = self::q('SELECT * FROM weekly_reviews WHERE user_id = ? AND week_start = ?', [$uid, $mon])->fetch(PDO::FETCH_ASSOC) ?: null;
        if ($light) return ['open' => true, 'week' => $mon, 'seen' => self::seen($uid, $mon), 'done' => (bool) $row, 'chest_opened' => (bool) ($row['chest_opened_at'] ?? false), 'intention' => $intention, 'keys' => $keys];
        return ['open' => true, 'week' => $mon, 'seen' => self::seen($uid, $mon), 'done' => (bool) $row, 'chest_opened' => $row && $row['chest_opened_at'], 'intention' => $intention, 'keys' => $keys,
                'answers' => $row ? (json_decode((string) $row['data_json'], true) ?: (object) []) : (object) [],
                'summary' => self::weekSummary($uid, $mon), 'reveal' => self::reveal($uid, $mon, 1), 'can_second' => GameV2::plan($uid) === 'elite', 'odds' => GAME_CHEST];
    }

    public static function saveWeekly(string $uid, array $b): array
    {
        self::schema();
        $mon = self::openWeek($uid);
        if (!$mon) return ['error' => 'closed'];
        $clean = fn($k) => mb_substr_safe(trim((string) ($b[$k] ?? '')), 300);
        $g = (int) ($b['grade'] ?? 0);
        $data = ['best' => $clean('best'), 'worst' => $clean('worst'), 'fix' => $clean('fix'), 'rule' => $clean('rule'), 'intention' => $clean('intention'), 'grade' => $g >= 1 && $g <= 5 ? $g : null];
        try { self::q('INSERT INTO weekly_reviews (user_id, week_start, data_json, completed_at) VALUES (?, ?, ?, ?)', [$uid, $mon, json_encode($data), GameEngine::ts()]); }
        catch (Throwable $e) { self::q('UPDATE weekly_reviews SET data_json = ? WHERE user_id = ? AND week_start = ?', [json_encode($data), $uid, $mon]); }
        if (GameEngine::awardXp($uid, "weekly:$mon", 50)) GameEngine::track($uid, 'weekly_review_done');
        $run = self::weeklyRun($uid);
        if ($run >= 4) GameEngine::unlock($uid, 'weekly_4');
        if ($run >= 12) GameEngine::unlock($uid, 'weekly_12');
        GameV2::evaluateMap($uid);
        return ['ok' => true];
    }

    /** consecutive weeks with a weekly review, ending with the latest one */
    public static function weeklyRun(string $uid): int
    {
        try { $weeks = self::q('SELECT week_start FROM weekly_reviews WHERE user_id = ? ORDER BY week_start DESC', [$uid])->fetchAll(PDO::FETCH_COLUMN); } catch (Throwable $e) { return 0; }
        $run = 0; $expect = null;
        foreach ($weeks as $w) { if ($expect !== null && $w !== $expect) break; $run++; $expect = GameEngine::addDays($w, -7); }
        return $run;
    }

    /* ───────────── chest ───────────── */

    public static function openChest(string $uid): array
    {
        self::schema();
        $mon = self::openWeek($uid);
        $row = $mon ? self::q('SELECT * FROM weekly_reviews WHERE user_id = ? AND week_start = ?', [$uid, $mon])->fetch(PDO::FETCH_ASSOC) : null;
        if (!$row) return ['error' => 'review_first'];
        if ($row['chest_opened_at']) return ['error' => 'opened'];
        self::q('UPDATE weekly_reviews SET chest_opened_at = ? WHERE user_id = ? AND week_start = ? AND chest_opened_at IS NULL', [GameEngine::ts(), $uid, $mon]);
        $key = self::q("SELECT id FROM user_rewards WHERE user_id = ? AND reward_type = 'key' AND used_at IS NULL ORDER BY id LIMIT 1", [$uid])->fetchColumn();
        if ($key) self::q('UPDATE user_rewards SET used_at = ? WHERE id = ?', [GameEngine::ts(), $key]);
        $k = $key ? 1 : 0;
        $items = [];
        $xp = $key ? random_int(60, 150) : random_int(25, 90);
        GameEngine::awardXp($uid, "chest:$mon", $xp); $items[] = ['type' => 'xp', 'value' => $xp];
        $roll = fn(string $r) => random_int(1, 100) <= GAME_CHEST[$r][$k];
        $plan = GameV2::plan($uid);
        if ($roll('freeze')) {
            $p = GameEngine::profile($uid, false); $cap = GameEngine::freezeQuota($uid) + 1;
            if ((int) $p['freezes_available'] < $cap) { self::q('UPDATE user_game_profile SET freezes_available = freezes_available + 1 WHERE user_id = ?', [$uid]); $items[] = ['type' => 'freeze', 'value' => 1]; }
        }
        if ($roll('cosmetic')) {
            $have = self::q('SELECT cosmetic_id FROM user_cosmetics WHERE user_id = ?', [$uid])->fetchAll(PDO::FETCH_COLUMN);
            $left = array_values(array_diff(array_slice(GAME_COSMETICS, 1), $have));
            if ($left) { $c = $left[random_int(0, count($left) - 1)]; self::q('INSERT INTO user_cosmetics (user_id, cosmetic_id, equipped) VALUES (?, ?, 0)', [$uid, $c]); $items[] = ['type' => 'cosmetic', 'value' => $c]; }
        }
        if ($roll('ai_credits') && function_exists('sb_ai_refund')) { try { for ($i = 0; $i < 3; $i++) sb_ai_refund(GameEngine::pdo(), $uid, 'chat'); $items[] = ['type' => 'ai_credits', 'value' => 3]; } catch (Throwable $e) { /* billing off */ } }
        if ($plan === 'free' && $roll('pro_days') && function_exists('sb_grant')) { try { sb_grant(GameEngine::pdo(), $uid, 'pro', 3, 'chest'); $items[] = ['type' => 'pro_days', 'value' => 3]; } catch (Throwable $e) { /* billing off */ } }
        if ($roll('lucky') && GameEngine::unlock($uid, 'lucky', true)) $items[] = ['type' => 'badge', 'value' => 'lucky'];
        foreach ($items as $it) self::q('INSERT INTO user_rewards (user_id, source, reward_type, reward_value, created_at) VALUES (?, ?, ?, ?, ?)', [$uid, 'chest', $it['type'], (string) $it['value'], GameEngine::ts()]);
        GameEngine::track($uid, 'chest_opened', ['key' => (bool) $key, 'items' => count($items)]);
        return ['items' => $items, 'key' => (bool) $key];
    }

    /* ───────────── cosmetics ───────────── */

    public static function cosmetics(string $uid): array
    {
        self::schema();
        $rows = self::q('SELECT cosmetic_id, equipped FROM user_cosmetics WHERE user_id = ?', [$uid])->fetchAll(PDO::FETCH_ASSOC);
        $owned = ['ring_default' => true]; $eq = 'ring_default';
        foreach ($rows as $r) { $owned[$r['cosmetic_id']] = true; if ((int) $r['equipped']) $eq = $r['cosmetic_id']; }
        return ['all' => array_values(array_unique(array_merge(GAME_COSMETICS, array_keys($owned)))), 'owned' => array_keys($owned), 'equipped' => $eq];
    }
    public static function equip(string $uid, string $id): bool
    {
        self::schema();
        if ($id !== 'ring_default' && !self::q('SELECT 1 FROM user_cosmetics WHERE user_id = ? AND cosmetic_id = ?', [$uid, $id])->fetchColumn()) return false;
        self::q('UPDATE user_cosmetics SET equipped = 0 WHERE user_id = ?', [$uid]);
        if ($id !== 'ring_default') self::q('UPDATE user_cosmetics SET equipped = 1 WHERE user_id = ? AND cosmetic_id = ?', [$uid, $id]);
        return true;
    }

    /* ───────────── Edge Reveal ───────────── */

    public static function rOf(array $t): ?float
    {
        $net = GameEngine::net($t);
        if (($risk = (int) ($t['risk_c'] ?? 0)) > 0) return $net / $risk;
        $pv = GAME_POINT_VALUE[strtoupper((string) ($t['instrument'] ?? 'NQ'))] ?? null;
        if ($pv && isset($t['entry'], $t['stop']) && $t['stop'] !== '' && (float) $t['entry'] !== (float) $t['stop']) {
            $risk = abs((float) $t['entry'] - (float) $t['stop']) * $pv * max(1, (float) ($t['contracts'] ?? 1)) * 100;
            return $risk > 0 ? $net / $risk : null;
        }
        return null;
    }
    private static function avg(array $a): ?float { return $a ? array_sum($a) / count($a) : null; }

    /** statistical candidates on the last 4-8 weeks, best first */
    public static function candidates(string $uid): array
    {
        $from = GameEngine::addDays(GameEngine::today(), -56);
        $trades = array_values(array_filter(GameEngine::docs($uid, 'trades'), fn($t) => ($t['date'] ?? '') >= $from && empty($t['demo'])));
        $rows = [];
        foreach ($trades as $t) { $r = self::rOf($t); if ($r !== null) $rows[] = ['t' => $t, 'r' => $r]; }
        $out = [];
        if (count($rows) < 20) {
            // beginner reveal: habits, not results
            $c = GameEngine::counters($uid);
            return [['key' => 'beginner', 'score' => 1, 'data' => ['trades' => count($trades), 'reviews' => $c['reviews'], 'plans' => $c['plans'], 'swept' => $c['swept']]]];
        }
        $all = self::avg(array_column($rows, 'r'));
        $group = function (callable $key, int $min) use ($rows): array { $g = []; foreach ($rows as $x) { $k = $key($x['t']); if ($k !== null && $k !== '') $g[$k][] = $x['r']; } return array_filter($g, fn($v) => count($v) >= $min); };
        $add = function (string $key, array $data, float $gap, int $n) use (&$out) { if ($n > 0) $out[] = ['key' => $key, 'score' => abs($gap) * sqrt($n), 'data' => $data]; };
        // best 30-minute slot
        $slots = $group(function ($t) { $m = preg_match('/^(\d{2}):(\d{2})/', (string) ($t['entry_time'] ?? ''), $x) ? (int) $x[1] * 60 + (int) $x[2] : null; return $m === null ? null : (string) (intdiv($m, 30) * 30); }, 5);
        if ($slots) { uasort($slots, fn($a, $b) => self::avg($b) <=> self::avg($a)); $k = (int) array_key_first($slots); $v = $slots[$k];
            $add('best_slot', ['start' => sprintf('%02d:%02d', intdiv($k, 60), $k % 60), 'end' => sprintf('%02d:%02d', intdiv($k + 30, 60), ($k + 30) % 60), 'r' => round(self::avg($v), 2), 'n' => count($v), 'all' => round($all, 2)], self::avg($v) - $all, count($v)); }
        // best setup
        $setups = $group(fn($t) => trim((string) ($t['setup'] ?? '')), 5);
        if (count($setups) >= 2) { uasort($setups, fn($a, $b) => self::avg($b) <=> self::avg($a)); $k = array_key_first($setups); $v = $setups[$k];
            $add('best_setup', ['setup' => $k, 'r' => round(self::avg($v), 2), 'n' => count($v), 'all' => round($all, 2)], self::avg($v) - $all, count($v)); }
        // emotion
        $emo = $group(fn($t) => ((array) (($t['emo'] ?? [])['before'] ?? []))[0] ?? null, 5);
        if (count($emo) >= 2) { uasort($emo, fn($a, $b) => self::avg($a) <=> self::avg($b)); $k = array_key_first($emo); $v = $emo[$k];
            $add('emotion', ['emotion' => $k, 'r' => round(self::avg($v), 2), 'n' => count($v), 'all' => round($all, 2)], self::avg($v) - $all, count($v)); }
        // weekday
        $wd = $group(fn($t) => (string) (new DateTimeImmutable((string) $t['date']))->format('N'), 5);
        if (count($wd) >= 3) { uasort($wd, fn($a, $b) => self::avg($b) <=> self::avg($a)); $k = (int) array_key_first($wd); $v = $wd[$k];
            $add('best_day', ['weekday' => $k, 'r' => round(self::avg($v), 2), 'n' => count($v), 'all' => round($all, 2)], self::avg($v) - $all, count($v)); }
        // plan before the open vs not (scored days)
        $days = self::q("SELECT trading_day, plan_at, plan_valid, detail_json FROM game_days WHERE user_id = ? AND trading_day >= ?", [$uid, $from])->fetchAll(PDO::FETCH_ASSOC);
        $byId = []; foreach ($rows as $x) $byId[(string) $x['t']['id']] = $x['r'];
        $withP = []; $noP = []; $ok = []; $bad = [];
        foreach ($days as $d) {
            $early = (int) $d['plan_valid'] && $d['plan_at'] && (int) $d['plan_at'] < GameEngine::epochEt($d['trading_day'], '09:30');
            foreach ((json_decode((string) $d['detail_json'], true)['trades'] ?? []) as $x) {
                if (!isset($byId[$x['id']])) continue;
                if ($early) $withP[] = $byId[$x['id']]; else $noP[] = $byId[$x['id']];
                if ($x['ok']) $ok[] = $byId[$x['id']]; else $bad[] = $byId[$x['id']];
            }
        }
        if (count($withP) >= 5 && count($noP) >= 5) $add('plan_effect', ['with' => round(self::avg($withP), 2), 'without' => round(self::avg($noP), 2), 'n' => count($withP) + count($noP)], self::avg($withP) - self::avg($noP), min(count($withP), count($noP)));
        if (count($ok) >= 5 && count($bad) >= 5) $add('compliance', ['in_plan' => round(self::avg($ok), 2), 'off_plan' => round(self::avg($bad), 2), 'pct' => (int) round(count($ok) / (count($ok) + count($bad)) * 100)], self::avg($ok) - self::avg($bad), min(count($ok), count($bad)));
        usort($out, fn($a, $b) => $b['score'] <=> $a['score']);
        // not something revealed in the last 4 weeks
        $recent = self::q('SELECT insight_key FROM edge_reveals WHERE user_id = ? AND week_start >= ?', [$uid, GameEngine::addDays(GameEngine::monday(GameEngine::today()), -28)])->fetchAll(PDO::FETCH_COLUMN);
        $fresh = array_values(array_filter($out, fn($c) => !in_array($c['key'], $recent, true)));
        return $fresh ?: $out;
    }

    /** this week's reveal (slot 1, or the Elite second one), created once, gated by plan */
    public static function reveal(string $uid, string $mon, int $slot): ?array
    {
        $plan = GameV2::plan($uid);
        if ($slot === 2 && $plan !== 'elite') return null;
        $firstWeekOfMonth = (int) (new DateTimeImmutable($mon))->format('j') <= 7;
        if ($plan === 'free' && !$firstWeekOfMonth) return ['locked' => true];
        $row = self::q('SELECT * FROM edge_reveals WHERE user_id = ? AND week_start = ? AND slot = ?', [$uid, $mon, $slot])->fetch(PDO::FETCH_ASSOC) ?: null;
        if (!$row) {
            $c = self::candidates($uid);
            $pickC = $c[$slot - 1] ?? null;
            if (!$pickC) return null;
            try { self::q('INSERT INTO edge_reveals (user_id, week_start, slot, insight_key, data_json) VALUES (?, ?, ?, ?, ?)', [$uid, $mon, $slot, $pickC['key'], json_encode($pickC['data'])]); } catch (Throwable $e) { /* raced */ }
            $row = self::q('SELECT * FROM edge_reveals WHERE user_id = ? AND week_start = ? AND slot = ?', [$uid, $mon, $slot])->fetch(PDO::FETCH_ASSOC);
        }
        $texts = json_decode((string) ($row['text_json'] ?? ''), true) ?: [];
        return ['id' => (int) $row['id'], 'key' => $row['insight_key'], 'data' => json_decode((string) $row['data_json'], true) ?: [], 'texts' => $texts, 'revealed' => (bool) $row['revealed_at']];
    }

    /** flip the card: Sweep AI words it once per language (2 sentences, no dollars), else the client template */
    public static function flip(string $uid, int $id, string $lang): array
    {
        $row = self::q('SELECT * FROM edge_reveals WHERE id = ? AND user_id = ?', [$id, $uid])->fetch(PDO::FETCH_ASSOC);
        if (!$row) return ['error' => 'not_found'];
        if (!$row['revealed_at']) { self::q('UPDATE edge_reveals SET revealed_at = ? WHERE id = ?', [GameEngine::ts(), $id]); GameEngine::track($uid, 'edge_reveal_viewed', ['key' => $row['insight_key']]); GameV2::evaluateMap($uid); }
        $texts = json_decode((string) ($row['text_json'] ?? ''), true) ?: [];
        if (!isset($texts[$lang]) && $row['insight_key'] !== 'beginner' && GameV2::plan($uid) !== 'free') {
            try {
                global $cfg;
                if (!empty($cfg['ai_config']) && !defined('SWEEP_AI_CONFIG')) define('SWEEP_AI_CONFIG', (string) $cfg['ai_config']);
                $core = dirname(__DIR__) . '/ai/ai-core.php';
                if (is_file($core)) {
                    require_once $core;
                    $name = ['en' => 'English', 'fr' => 'Canadian French (tutoiement)', 'es' => 'Spanish'][$lang] ?? 'English';
                    $prompt = 'A trading-discipline app shows a trader one weekly discovery about their edge, computed from their own trades. Insight: ' . $row['insight_key']
                        . '. Numbers (R = multiple of the risk taken): ' . $row['data_json'] . ". Write it in $name: at most 2 short sentences, positive and actionable, using R and percentages only."
                        . ' No dollar amounts, no financial advice, no predictions. Return JSON {"text": "..."}.';
                    $r = sai_call(GameEngine::pdo(), $uid, 'game_edge_reveal', $prompt, ['max_tokens' => 220, 'temperature' => .5]);
                    $txt = trim((string) (($r['data'] ?? [])['text'] ?? ''));
                    if ($txt !== '' && strlen($txt) <= 600 && !preg_match('/\$\s?\d/', $txt)) {
                        $texts[$lang] = $txt;
                        self::q('UPDATE edge_reveals SET text_json = ?, ai_used = 1 WHERE id = ?', [json_encode($texts), $id]);
                    }
                }
            } catch (Throwable $e) { /* template on the client */ }
        }
        return ['texts' => $texts];
    }

    /* ───────────── comeback quest ───────────── */

    public static function startQuest(string $uid, string $kind, int $lost): void
    {
        self::schema();
        if (self::q('SELECT 1 FROM user_quests WHERE user_id = ? AND completed_at IS NULL AND ends_on >= ?', [$uid, GameEngine::today()])->fetchColumn()) return;
        $d = GameEngine::today(); $n = 0; $end = $d;
        while ($n < 5) { $end = GameEngine::addDays($end, 1); if (GameEngine::isMarketDay($end)) $n++; }
        self::q('INSERT INTO user_quests (user_id, kind, started_on, ends_on, lost_streak, created_at) VALUES (?, ?, ?, ?, ?, ?)', [$uid, $kind, $d, $end, $lost, GameEngine::ts()]);
        GameEngine::celebrate($uid, 'quest_start', ['kind' => $kind, 'lost' => $lost]);
        GameEngine::track($uid, 'comeback_started', ['kind' => $kind]);
    }

    /** steps done inside the quest window; completion restores half the lost streak (once per 30 days) */
    public static function questState(string $uid): ?array
    {
        self::schema();
        $q = self::q('SELECT * FROM user_quests WHERE user_id = ? ORDER BY id DESC LIMIT 1', [$uid])->fetch(PDO::FETCH_ASSOC);
        if (!$q || ($q['completed_at'] === null && $q['ends_on'] < GameEngine::today()) || ($q['completed_at'] && (int) $q['completed_at'] < GameEngine::ts() - 86400)) return null;
        $days = self::q('SELECT trading_day, plan_valid, plan_at, review_done, is_swept FROM game_days WHERE user_id = ? AND trading_day BETWEEN ? AND ?', [$uid, $q['started_on'], $q['ends_on']])->fetchAll(PDO::FETCH_ASSOC);
        $steps = ['review' => false, 'plan' => false, 'sweep' => false];
        foreach ($days as $d) {
            if ((int) $d['review_done']) $steps['review'] = true;
            if ((int) $d['plan_valid'] && $d['plan_at'] && (int) $d['plan_at'] < GameEngine::epochEt($d['trading_day'], '09:30')) $steps['plan'] = true;
            if ((int) $d['is_swept']) $steps['sweep'] = true;
        }
        if (!$q['completed_at'] && !in_array(false, $steps, true)) {
            self::q('UPDATE user_quests SET completed_at = ? WHERE id = ?', [GameEngine::ts(), $q['id']]);
            $restore = 0;
            $recent = (int) self::q('SELECT COUNT(*) FROM user_quests WHERE user_id = ? AND completed_at IS NOT NULL AND completed_at > ? AND id <> ? AND lost_streak > 0', [$uid, GameEngine::ts() - 30 * 86400, $q['id']])->fetchColumn();
            if ((int) $q['lost_streak'] >= 5 && !$recent) {
                $restore = intdiv((int) $q['lost_streak'], 2);
                $p = GameEngine::profile($uid, false); $cur = (int) $p['streak_current'] + $restore;
                self::q('UPDATE user_game_profile SET streak_current = ?, streak_best = ? WHERE user_id = ?', [$cur, max((int) $p['streak_best'], $cur), $uid]);
            }
            GameEngine::awardXp($uid, 'quest:' . $q['id'], 100);
            GameEngine::unlock($uid, 'comeback', true);
            GameEngine::celebrate($uid, 'quest_done', ['restore' => $restore, 'xp' => 100]);
            GameEngine::track($uid, 'comeback_completed', ['restore' => $restore]);
            $q['completed_at'] = GameEngine::ts();
        }
        return ['kind' => $q['kind'], 'ends_on' => $q['ends_on'], 'lost' => (int) $q['lost_streak'], 'steps' => $steps, 'done' => (bool) $q['completed_at']];
    }

    /** 7+ quiet market days → a comeback quest the next time the trader opens the app */
    public static function checkAbsence(string $uid): void
    {
        $last = self::q('SELECT MAX(trading_day) FROM game_days WHERE user_id = ? AND activity = 1', [$uid])->fetchColumn();
        if (!$last) return;
        $n = 0; for ($d = GameEngine::addDays((string) $last, 1); $d < GameEngine::today(); $d = GameEngine::addDays($d, 1)) if (GameEngine::isMarketDay($d)) $n++;
        if ($n >= 7) self::startQuest($uid, 'absence', 0);
    }
}

function mb_substr_safe(string $s, int $n): string { return function_exists('mb_substr') ? mb_substr($s, 0, $n) : substr($s, 0, $n); }
