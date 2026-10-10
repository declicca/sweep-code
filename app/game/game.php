<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli' && realpath((string) ($_SERVER['SCRIPT_FILENAME'] ?? '')) === realpath(__FILE__)) { http_response_code(404); exit; }
/**
 * Sweep — Gamification V1 « Sweep the day ».
 *
 * Adapted to Sweep's real data model (see README → Gamification):
 *  - Trades, journals and settings are JSON documents (table `documents`). The engine reads them; it never edits them.
 *  - Plan du jour  = journal document of the day, field `pre`  (bias, setups, max_loss, max_trades, levels, day_off).
 *  - Revue du jour = journal document of the day, field `post` (well, tomorrow, discipline 1-5, reviewed_at).
 *  - A trade is journaled when it has a setup, an emotion (emo.before) and a rules answer (rules_followed or the checklist).
 *  - Copied trades (same copy_group on several accounts) count once. Sample data never counts.
 *  - Only market days from the day the trader first opens the game are scored: no past streak, no past Sweep.
 *  - Days are locked lazily (each time the trader opens the app) and by the optional hourly cron: same code, same result.
 *
 * Every XP grant goes through xp_events with a unique key: the same action never pays twice, XP is never taken back.
 */

require_once __DIR__ . '/catalog.php';
require_once __DIR__ . '/v2.php';
require_once __DIR__ . '/boss.php';
require_once __DIR__ . '/v2b.php';
require_once __DIR__ . '/v2c.php';
require_once __DIR__ . '/weekly-mail.php';   // « Your week » email (brief 01 step 5)
require_once __DIR__ . '/v3s.php';
require_once __DIR__ . '/v3l.php';
require_once __DIR__ . '/v3c.php';
require_once __DIR__ . '/v3d.php';
require_once __DIR__ . '/wow.php';

final class GameEngine
{
    private static ?PDO $pdo = null;
    private static array $docCache = [];
    /** celebrations created during this request, per user */
    private static array $made = [];

    public static function setPdo(PDO $pdo): void { self::$pdo = $pdo; }
    public static function pdo(): PDO { return self::$pdo ?? db(); }
    public static function q(string $sql, array $a = []): PDOStatement { $st = self::pdo()->prepare($sql); $st->execute($a); return $st; }
    private static function mysql(): bool { return self::pdo()->getAttribute(PDO::ATTR_DRIVER_NAME) === 'mysql'; }

    /* ───────────── schema ───────────── */

    public static function schema(): void
    {
        static $done = false;
        if ($done) return;
        $done = true;
        $my = self::mysql();
        $T = $my ? 'VARCHAR(120)' : 'TEXT';
        $D = $my ? 'CHAR(10)' : 'TEXT';
        $AI = $my ? 'BIGINT AUTO_INCREMENT PRIMARY KEY' : 'INTEGER PRIMARY KEY AUTOINCREMENT';
        $cs = $my ? ' DEFAULT CHARSET=utf8mb4' : '';
        $sql = [
            "CREATE TABLE IF NOT EXISTS user_game_profile (user_id $T NOT NULL PRIMARY KEY, xp_total INT NOT NULL DEFAULT 0, level INT NOT NULL DEFAULT 1,
              rank_key VARCHAR(20) NOT NULL DEFAULT 'rookie', streak_current INT NOT NULL DEFAULT 0, streak_best INT NOT NULL DEFAULT 0, streak_start $D NULL,
              streak_last_day $D NULL, freezes_available INT NOT NULL DEFAULT 1, freezes_reset_on $D NULL, last_locked_day $D NULL, started_on $D NOT NULL,
              goal VARCHAR(30) NULL, trading_style VARCHAR(20) NULL, instruments VARCHAR(255) NULL, onboarding_json TEXT NULL, sound_enabled INT NOT NULL DEFAULT 0,
              default_max_loss INT NULL, updated_at INT NOT NULL)$cs",
            "CREATE TABLE IF NOT EXISTS game_days (user_id $T NOT NULL, trading_day $D NOT NULL, ring_plan INT NOT NULL DEFAULT 0, ring_execution INT NOT NULL DEFAULT 0,
              ring_review INT NOT NULL DEFAULT 0, trades_count INT NOT NULL DEFAULT 0, compliant_count INT NOT NULL DEFAULT 0, journaled_count INT NOT NULL DEFAULT 0,
              is_swept INT NOT NULL DEFAULT 0, is_valid_streak INT NOT NULL DEFAULT 0, review_done INT NOT NULL DEFAULT 0, day_off INT NOT NULL DEFAULT 0,
              plan_valid INT NOT NULL DEFAULT 0, plan_at INT NULL, plan_bias VARCHAR(12) NULL, guardrail INT NOT NULL DEFAULT 0, freeze_used INT NOT NULL DEFAULT 0,
              activity INT NOT NULL DEFAULT 0, net_c INT NOT NULL DEFAULT 0, detail_json TEXT NULL, locked_at INT NULL, updated_at INT NOT NULL,
              PRIMARY KEY (user_id, trading_day))$cs",
            "CREATE TABLE IF NOT EXISTS xp_events (id $AI, user_id $T NOT NULL, event_key VARCHAR(120) NOT NULL, xp INT NOT NULL, meta_json TEXT NULL, created_at INT NOT NULL)$cs",
            "CREATE TABLE IF NOT EXISTS user_badges (user_id $T NOT NULL, badge_id VARCHAR(40) NOT NULL, unlocked_at INT NOT NULL, PRIMARY KEY (user_id, badge_id))$cs",
            "CREATE TABLE IF NOT EXISTS game_celebrations (id $AI, user_id $T NOT NULL, type VARCHAR(30) NOT NULL, payload_json TEXT NOT NULL, created_at INT NOT NULL, seen_at INT NULL)$cs",
            "CREATE TABLE IF NOT EXISTS market_holidays (day $D NOT NULL PRIMARY KEY, label VARCHAR(80) NULL)$cs",
            "CREATE TABLE IF NOT EXISTS game_analytics (id $AI, user_id $T NOT NULL, event VARCHAR(40) NOT NULL, meta_json TEXT NULL, created_at INT NOT NULL)$cs",
        ];
        foreach ($sql as $s) self::pdo()->exec($s);
        $idx = [
            'CREATE UNIQUE INDEX IF NOT EXISTS uq_xp ON xp_events (user_id, event_key)',
            'CREATE INDEX IF NOT EXISTS idx_celeb_unseen ON game_celebrations (user_id, seen_at)',
            'CREATE INDEX IF NOT EXISTS idx_game_an ON game_analytics (user_id, event)',
        ];
        if ($my) {
            foreach (['ALTER TABLE xp_events ADD UNIQUE KEY uq_xp (user_id, event_key)', 'ALTER TABLE game_celebrations ADD KEY idx_celeb_unseen (user_id, seen_at)',
                      'ALTER TABLE game_analytics ADD KEY idx_game_an (user_id, event)'] as $s) { try { self::pdo()->exec($s); } catch (Throwable $e) { /* exists */ } }
        } else {
            foreach ($idx as $s) self::pdo()->exec($s);
        }
        // CME / U.S. market holidays (full closures and abbreviated sessions counted as neutral days). Edit the table for later years.
        if (!self::q('SELECT 1 FROM market_holidays LIMIT 1')->fetchColumn()) {
            foreach (GAME_HOLIDAYS as $d => $label) self::q('INSERT INTO market_holidays (day, label) VALUES (?, ?)', [$d, $label]);
        }
    }

    /* ───────────── time ───────────── */

    private static function tz(): DateTimeZone { static $z = null; return $z ??= new DateTimeZone('America/New_York'); }
    /** current time; SWEEP_GAME_NOW (environment, tests only) can pin it, e.g. "2026-10-05 08:15" New York time */
    public static function ts(): int { $e = getenv('SWEEP_GAME_NOW'); return $e ? (new DateTimeImmutable($e, self::tz()))->getTimestamp() + (time() - (int) ($_SERVER['REQUEST_TIME'] ?? time())) : time(); }
    public static function nowEt(): DateTimeImmutable { return (new DateTimeImmutable('@' . self::ts()))->setTimezone(self::tz()); }
    /** trading day of "now": NY time + 6 h (the CME session that starts at 18:00 belongs to the next day) */
    public static function today(): string { return self::nowEt()->modify('+6 hours')->format('Y-m-d'); }
    public static function addDays(string $d, int $n): string { return (new DateTimeImmutable($d . ' 12:00', self::tz()))->modify(($n >= 0 ? '+' : '') . $n . ' days')->format('Y-m-d'); }
    public static function epochEt(string $d, string $hm): int { return (new DateTimeImmutable($d . ' ' . $hm, self::tz()))->getTimestamp(); }
    /** grace ends D+1 23:59:59 ET */
    public static function deadline(string $d): int { return self::epochEt(self::addDays($d, 1), '23:59:59'); }
    public static function isLocked(string $d): bool { return self::ts() > self::deadline($d); }
    private static function weekday(string $d): int { return (int) (new DateTimeImmutable($d . ' 12:00'))->format('N'); }
    public static function monday(string $d): string { return self::addDays($d, 1 - self::weekday($d)); }

    public static function isMarketDay(string $d): bool
    {
        if (self::weekday($d) > 5) return false;
        static $h = null;
        if ($h === null) { $h = []; foreach (self::q('SELECT day FROM market_holidays') as $r) $h[$r['day']] = true; }
        return !isset($h[$d]);
    }

    /**
     * Is the trade's date already its session (trading day)? One rule for the whole app:
     *  - session_date: true (every trade saved or imported by the app since this version) → yes;
     *  - otherwise, a trade entered before 18:00 ET → yes (same day either way);
     *  - a trade entered at 18:00 or later whose first execution happened the day BEFORE its date → yes
     *    (saved by the app between the 18:00 rule and the session_date mark: already moved, never moved twice);
     *  - any other trade entered at 18:00 or later (older trades, dated by the calendar) → no: its session is the next day.
     */
    public static function hasSessionDate(array $t): bool
    {
        if (!empty($t['session_date'])) return true;
        $tm = substr((string) ($t['entry_time'] ?? ''), 0, 5);
        if ($tm === '' || $tm < '18:00') return true;
        $x = $t['executions'][0]['t'] ?? null; $d = (string) ($t['date'] ?? '');
        return is_string($x) && substr($x, 0, 10) !== '' && substr($x, 0, 10) < $d;
    }
    /** trade → its trading day (the date field IS the session; older evening trades → the next day) */
    public static function tradeDay(array $t): ?string
    {
        $d = (string) ($t['date'] ?? '');
        if (!preg_match('/^\d{4}-\d{2}-\d{2}$/', $d)) return null;
        return self::hasSessionDate($t) ? $d : self::addDays($d, 1);
    }
    /** the clock time of the entry (New York): an evening trade of session D was entered on D-1 */
    public static function tradeEpoch(array $t): ?int
    {
        $d = (string) ($t['date'] ?? ''); $tm = substr((string) ($t['entry_time'] ?? ''), 0, 5);
        if (!preg_match('/^\d{4}-\d{2}-\d{2}$/', $d)) return null;
        $tm = preg_match('/^\d{2}:\d{2}$/', $tm) ? $tm : '09:30';
        if ($tm >= '18:00' && self::hasSessionDate($t)) $d = self::addDays($d, -1);
        return self::epochEt($d, $tm);
    }

    /* ───────────── documents (read-only) ───────────── */

    public static function docs(string $uid, string $col): array
    {
        $k = $uid . '|' . $col;
        if (isset(self::$docCache[$k])) return self::$docCache[$k];
        $out = [];
        foreach (self::q('SELECT id, data FROM documents WHERE user_id = ? AND collection = ?', [$uid, $col]) as $r) {
            $d = json_decode((string) $r['data'], true);
            if (is_array($d) && empty($d['demo'])) { $d['id'] = $r['id']; $out[$r['id']] = $d; }
        }
        return self::$docCache[$k] = $out;
    }
    public static function forget(string $uid): void { foreach (array_keys(self::$docCache) as $k) if (str_starts_with($k, $uid . '|')) unset(self::$docCache[$k]); }

    /** trades of a trading day, copies counted once, in entry order */
    private static function dayTrades(string $uid, string $day): array
    {
        $seen = []; $out = [];
        foreach (self::docs($uid, 'trades') as $t) {
            if (self::tradeDay($t) !== $day) continue;
            $g = (string) ($t['copy_group'] ?? '');
            if ($g !== '') { if (isset($seen[$g])) continue; $seen[$g] = true; }
            $out[] = $t;
        }
        usort($out, fn($a, $b) => (self::tradeEpoch($a) ?? 0) <=> (self::tradeEpoch($b) ?? 0) ?: strcmp((string) ($a['id'] ?? ''), (string) ($b['id'] ?? '')));
        return $out;
    }
    private static function allTradesChrono(string $uid): array
    {
        $seen = []; $out = [];
        foreach (self::docs($uid, 'trades') as $t) {
            $g = (string) ($t['copy_group'] ?? '');
            if ($g !== '') { if (isset($seen[$g])) continue; $seen[$g] = true; }
            if (self::tradeDay($t) === null) continue;
            $out[] = $t;
        }
        usort($out, fn($a, $b) => (self::tradeEpoch($a) ?? 0) <=> (self::tradeEpoch($b) ?? 0));
        return $out;
    }
    private static function money($v): ?int
    {
        if ($v === null || $v === '') return null;
        if (is_int($v) || is_float($v)) return (int) round($v * 100);
        $s = preg_replace('/[^0-9.\-]/', '', str_replace('−', '-', (string) $v));
        return ($s === '' || $s === '-' || !is_numeric($s)) ? null : (int) round((float) $s * 100);
    }
    private static function low(string $s): string { return function_exists('mb_strtolower') ? mb_strtolower($s) : strtolower($s); }
    public static function net(array $t): int { return (int) ($t['pnl_c'] ?? 0) - (int) ($t['fees_c'] ?? 0); }
    /** a defined risk: a stop price, a risk in $ (screenshot trades), or « I respected my stop / defined my risk » answered yes */
    /** the stop rule is broken only when the trader says so (« no » to the stop / risk questions) */
    public static function stopBroken(array $t): bool
    {
        $d = (array) ($t['discipline'] ?? []);
        foreach (['stop', 'risk', 'defined_risk', 'stop_respected'] as $k) if (($d[$k] ?? '') === 'n') return true;
        return false;
    }
    public static function hasStop(array $t): bool
    {
        if (isset($t['stop']) && $t['stop'] !== '' && $t['stop'] !== null) return true;
        if ((int) ($t['risk_c'] ?? 0) > 0 || (int) ($t['stop_c'] ?? 0) !== 0) return true;
        $d = (array) ($t['discipline'] ?? []);
        foreach (['stop', 'risk', 'defined_risk', 'stop_respected'] as $k) if (($d[$k] ?? '') === 'y') return true;
        return false;
    }
    /** yes / partial / no / null from the explicit answer or the discipline checklist */
    private static function rules(array $t): ?string
    {
        $r = $t['rules_followed'] ?? null;
        if (in_array($r, ['yes', 'partial', 'no'], true)) return $r;
        $ans = array_filter(array_values((array) ($t['discipline'] ?? [])), fn($v) => $v === 'y' || $v === 'n');
        if (!$ans) return null;
        $n = count(array_filter($ans, fn($v) => $v === 'n'));
        return $n === 0 ? 'yes' : ($n * 2 < count($ans) ? 'partial' : 'no');
    }
    public static function journaled(array $t): bool
    {
        return trim((string) ($t['setup'] ?? '')) !== '' && !empty(($t['emo'] ?? [])['before']) && self::rules($t) !== null;
    }

    /* ───────────── profile ───────────── */

    public static function profile(string $uid, bool $create = true): ?array
    {
        self::schema();
        $p = self::q('SELECT * FROM user_game_profile WHERE user_id = ?', [$uid])->fetch(PDO::FETCH_ASSOC);
        if ($p || !$create) return $p ?: null;
        $today = self::today();
        self::q('INSERT INTO user_game_profile (user_id, started_on, freezes_available, freezes_reset_on, onboarding_json, updated_at) VALUES (?, ?, ?, ?, ?, ?)',
            [$uid, $today, self::freezeQuota($uid), self::monday($today), json_encode(['existing' => count(self::docs($uid, 'trades')) > 0]), self::ts()]);
        self::backfill($uid);
        return self::q('SELECT * FROM user_game_profile WHERE user_id = ?', [$uid])->fetch(PDO::FETCH_ASSOC);
    }
    private static function setProfile(string $uid, array $f): void
    {
        $f['updated_at'] = self::ts();
        self::q('UPDATE user_game_profile SET ' . implode(', ', array_map(fn($k) => "$k = ?", array_keys($f))) . ' WHERE user_id = ?', [...array_values($f), $uid]);
    }
    public static function onboarding(array $p): array { $o = json_decode((string) ($p['onboarding_json'] ?? ''), true); return is_array($o) ? $o : []; }

    public static function freezeQuota(string $uid): int
    {
        $plan = 'pro';   // early access and the first 60 days: Pro quota
        try {
            if (function_exists('billing_on') && billing_on() && function_exists('sb_plan')) $plan = sb_plan(self::pdo(), $uid);
        } catch (Throwable $e) { /* billing unavailable: keep Pro quota */ }
        return GAME_FREEZES[$plan] ?? 2;
    }

    public static function levelFor(int $xp): int { $n = 1; while (50 * ($n + 1) * $n <= $xp) $n++; return $n; }
    public static function xpFor(int $level): int { return 50 * $level * ($level - 1); }
    public static function rankFor(int $level): string { $r = 'rookie'; foreach (GAME_RANKS as [$min, $k]) if ($level >= $min) $r = $k; return $r; }
    private static function nextRank(int $level): ?array { foreach (GAME_RANKS as [$min, $k]) if ($min > $level) return [$min, $k]; return null; }

    /* ───────────── XP, badges, celebrations ───────────── */

    /** @return bool true when this key paid for the first time */
    public static function awardXp(string $uid, string $key, int $xp, array $meta = []): bool
    {
        try {
            self::q('INSERT INTO xp_events (user_id, event_key, xp, meta_json, created_at) VALUES (?, ?, ?, ?, ?)', [$uid, substr($key, 0, 120), $xp, $meta ? json_encode($meta) : null, self::ts()]);
        } catch (Throwable $e) {
            return false;   // unique key: already paid
        }
        if ($xp <= 0) return true;
        $p = self::profile($uid, false);
        $total = (int) $p['xp_total'] + $xp;
        $lvl = self::levelFor($total); $rank = self::rankFor($lvl);
        self::setProfile($uid, ['xp_total' => $total, 'level' => $lvl, 'rank_key' => $rank]);
        if ($lvl > (int) $p['level']) {
            self::celebrate($uid, 'level', ['level' => $lvl, 'rank' => $rank, 'rank_up' => $rank !== $p['rank_key']]);
            self::track($uid, 'level_up', ['level' => $lvl]);
            if ($rank !== $p['rank_key']) self::track($uid, 'rank_up', ['rank' => $rank]);
        }
        return true;
    }

    public static function celebrate(string $uid, string $type, array $payload): void
    {
        self::q('INSERT INTO game_celebrations (user_id, type, payload_json, created_at) VALUES (?, ?, ?, ?)', [$uid, $type, json_encode($payload), self::ts()]);
        self::$made[$uid][] = $type;
        if (class_exists('GameDiscord', false)) { try { GameDiscord::onCelebrate($uid, $type, $payload); } catch (Throwable $e) { error_log('[Sweep discord] ' . $e->getMessage()); } }
        if (class_exists('GameCrew', false)) { try { GameCrew::schema(); GameCrew::onCelebrate($uid, $type, $payload); } catch (Throwable $e) { error_log('[Sweep crew] ' . $e->getMessage()); } }
    }
    public static function track(string $uid, string $event, array $meta = []): void
    {
        try { self::q('INSERT INTO game_analytics (user_id, event, meta_json, created_at) VALUES (?, ?, ?, ?)', [$uid, substr($event, 0, 40), $meta ? json_encode($meta) : null, self::ts()]); }
        catch (Throwable $e) { /* analytics never blocks */ }
    }

    private static function hasBadge(string $uid, string $id): bool { return (bool) self::q('SELECT 1 FROM user_badges WHERE user_id = ? AND badge_id = ?', [$uid, $id])->fetchColumn(); }
    public static function unlock(string $uid, string $id, bool $quiet = false): bool
    {
        if (!isset(GAME_BADGES[$id]) || self::hasBadge($uid, $id)) return false;
        try { self::q('INSERT INTO user_badges (user_id, badge_id, unlocked_at) VALUES (?, ?, ?)', [$uid, $id, self::ts()]); } catch (Throwable $e) { return false; }
        $b = GAME_BADGES[$id];
        if ($b['xp'] > 0) self::awardXp($uid, 'badge:' . $id, $b['xp']); else self::awardXp($uid, 'badge:' . $id, 0);
        if (!$quiet) self::celebrate($uid, 'badge', ['id' => $id, 'rarity' => $b['rarity'], 'xp' => $b['xp']]);
        self::track($uid, 'badge_unlocked', ['id' => $id]);
        return true;
    }

    /** counters used by badges and the Progression screen */
    public static function counters(string $uid): array
    {
        $r = self::q('SELECT COUNT(*) AS days, SUM(is_swept) AS swept, SUM(review_done) AS reviews, SUM(CASE WHEN plan_valid = 1 AND ring_plan > 0 THEN 1 ELSE 0 END) AS plans,
            SUM(guardrail) AS guardrails FROM game_days WHERE user_id = ?', [$uid])->fetch(PDO::FETCH_ASSOC) ?: [];
        $early = 0;
        foreach (self::q('SELECT trading_day, plan_at FROM game_days WHERE user_id = ? AND plan_valid = 1 AND ring_plan > 0 AND plan_at IS NOT NULL', [$uid]) as $d) {
            if ((int) $d['plan_at'] < self::epochEt($d['trading_day'], '09:00')) $early++;
        }
        // consecutive compliant trades (current run and best run), from the scored days
        $run = 0; $bestRun = 0;
        foreach (self::q('SELECT detail_json FROM game_days WHERE user_id = ? ORDER BY trading_day', [$uid]) as $d) {
            foreach ((json_decode((string) $d['detail_json'], true)['trades'] ?? []) as $t) { $run = $t['ok'] ? $run + 1 : 0; $bestRun = max($bestRun, $run); }
        }
        // consecutive trades with a stop, from the whole history
        $stopRun = 0; $stopBest = 0; $journaledAny = false;
        foreach (self::allTradesChrono($uid) as $t) {
            $stopRun = self::hasStop($t) ? $stopRun + 1 : 0; $stopBest = max($stopBest, $stopRun);
            $journaledAny = $journaledAny || self::journaled($t);
        }
        $guardPaid = (int) self::q("SELECT COUNT(*) FROM xp_events WHERE user_id = ? AND event_key LIKE 'guardrail:%'", [$uid])->fetchColumn();   // only once confirmed (review or lock)
        return ['days' => (int) ($r['days'] ?? 0), 'swept' => (int) ($r['swept'] ?? 0), 'reviews' => (int) ($r['reviews'] ?? 0), 'plans' => (int) ($r['plans'] ?? 0),
            'guardrails' => $guardPaid, 'early_plans' => $early, 'compliant_run' => $run, 'compliant_best' => $bestRun,
            'stop_run' => $stopRun, 'stop_best' => $stopBest, 'journaled_any' => $journaledAny];
    }

    /** progress toward each badge: [value, target] */
    public static function badgeProgress(string $uid, ?array $c = null): array
    {
        $c ??= self::counters($uid);
        $p = self::profile($uid, false) ?: [];
        $o = self::onboarding($p);
        $days = self::q('SELECT * FROM game_days WHERE user_id = ? ORDER BY trading_day', [$uid])->fetchAll(PDO::FETCH_ASSOC);
        $byDay = []; foreach ($days as $d) $byDay[$d['trading_day']] = $d;

        // full week: every market day of one Mon-Fri week swept (at least 4 market days that week)
        $fullWeek = 0; $weeks = [];
        foreach ($days as $d) $weeks[self::monday($d['trading_day'])][] = $d;
        foreach ($weeks as $mon => $ds) {
            $market = array_filter(array_map(fn($i) => self::addDays($mon, $i), range(0, 4)), fn($x) => self::isMarketDay($x));
            if (count($market) < 4) continue;
            $ok = true; foreach ($market as $m) if (empty($byDay[$m]['is_swept'])) { $ok = false; break; }
            if ($ok) { $fullWeek = 1; break; }
        }
        $patience = 0; $resilience = 0; $comeback = 0; $zen = 0; $perfRun = 0; $perfBest = 0; $offRun = 0; $idle = 0; $prevNet = null;
        $first = $days ? $days[0]['trading_day'] : null;
        if ($first) {
            for ($d = $first; $d <= self::today(); $d = self::addDays($d, 1)) {
                if (!self::isMarketDay($d)) continue;
                $g = $byDay[$d] ?? null;
                $swept = $g && (int) $g['is_swept'] === 1;
                if ($swept && $g['plan_bias'] === 'no_trade') $patience = 1;
                if ($swept && $prevNet !== null && $prevNet < 0) $resilience = 1;
                if ($swept && $idle >= 7) $comeback = 1;
                if ($swept && $offRun >= 3 && (int) $g['day_off'] === 0) $zen = 1;
                $det = $g ? (json_decode((string) $g['detail_json'], true) ?: []) : [];
                if ($g && (int) $g['trades_count'] > 0) { $perfRun = !empty($det['perfect_docs']) ? $perfRun + 1 : 0; $perfBest = max($perfBest, $perfRun); }
                $offRun = ($g && (int) $g['day_off'] === 1 && (int) $g['plan_valid'] === 1) ? $offRun + 1 : ($swept ? 0 : $offRun);
                if ($g && (int) $g['day_off'] === 0 && (int) $g['activity'] === 1) $offRun = $swept ? 0 : $offRun;
                $idle = ($g && (int) $g['activity'] === 1) ? 0 : $idle + 1;
                if ($g && (int) $g['trades_count'] > 0) $prevNet = (int) $g['net_c'];
            }
        }
        $streakBest = max((int) ($p['streak_best'] ?? 0), (int) ($p['streak_current'] ?? 0));
        return [
            'welcome' => [!empty($o['done']) ? 1 : 0, 1], 'first_plan' => [min(1, $c['plans']), 1], 'first_journal' => [$c['journaled_any'] ? 1 : 0, 1],
            'first_sweep' => [min(1, $c['swept']), 1], 'sweep_5' => [min(5, $c['swept']), 5], 'sweep_25' => [min(25, $c['swept']), 25], 'sweep_100' => [min(100, $c['swept']), 100],
            'streak_7' => [min(7, $streakBest), 7], 'streak_30' => [min(30, $streakBest), 30], 'streak_100' => [min(100, $streakBest), 100],
            'full_week' => [$fullWeek, 1], 'patience' => [$patience, 1], 'guardrail' => [min(1, $c['guardrails']), 1], 'early_plan' => [min(10, $c['early_plans']), 10],
            'sniper' => [min(10, $c['compliant_best']), 10], 'sacred_stop' => [min(50, $c['stop_best']), 50], 'reviewer_20' => [min(20, $c['reviews']), 20],
            'resilience' => [$resilience, 1], 'comeback' => [$comeback, 1], 'perfectionist' => [min(5, $perfBest), 5], 'zen' => [$zen, 1],
        ];
    }

    public static function evaluateBadges(string $uid, bool $quiet = false): array
    {
        $won = [];
        foreach (self::badgeProgress($uid) as $id => [$v, $target]) {
            if ($v >= $target && self::unlock($uid, $id, $quiet)) $won[] = $id;
        }
        return $won;
    }

    /* ───────────── one day ───────────── */

    /** Recompute rings for one trading day, pay what is due, store the result. Idempotent. */
    public static function recomputeDay(string $uid, string $day): ?array
    {
        $p = self::profile($uid, false);
        if (!$p || $day < $p['started_on'] || $day > self::today() || !self::isMarketDay($day)) return null;
        $prev = self::q('SELECT * FROM game_days WHERE user_id = ? AND trading_day = ?', [$uid, $day])->fetch(PDO::FETCH_ASSOC) ?: null;
        if ($prev && $prev['locked_at']) return $prev;

        $j = self::docs($uid, 'journals')[$day] ?? [];
        $pre = (array) ($j['pre'] ?? []); $post = (array) ($j['post'] ?? []);
        $settings = self::docs($uid, 'meta')['settings'] ?? [];
        $userSetups = array_values(array_filter((array) ($settings['setups'] ?? [])));
        $trades = self::dayTrades($uid, $day);
        $n = count($trades);

        // plan
        $bias = in_array($pre['bias'] ?? '', ['bullish', 'bearish', 'neutral', 'no_trade'], true) ? $pre['bias'] : null;
        $maxLoss = self::money($pre['max_loss'] ?? null);
        $planSetups = array_map(fn($s) => self::low(trim((string) $s)), array_values(array_filter((array) ($pre['setups'] ?? []))));
        $maxTrades = isset($pre['max_trades']) && $pre['max_trades'] !== '' ? (int) $pre['max_trades'] : 0;
        $dayOff = !empty($pre['day_off']) && $bias === 'no_trade';
        $planValid = $bias !== null && ($bias === 'no_trade' || ($maxLoss ?? 0) > 0);   // setups are optional in the plan
        $planAt = $prev['plan_at'] ?? null;
        $planPast = !empty((json_decode((string) ($prev['detail_json'] ?? ''), true) ?: [])['plan_past']);
        if ($planValid && $planAt === null) {
            $planAt = self::ts();
            $planPast = $day < self::today();                    // a plan cannot be created for a past day
        }
        // the time the trader saved the plan (sent by the app); the server may only see it later, at its next check
        $savedAt = isset($pre['saved_at']) && is_numeric($pre['saved_at']) ? (int) $pre['saved_at'] : null;
        $savedEarly = false;
        if ($planValid && $savedAt && $savedAt > self::epochEt($day, '00:00') - 86400 && $savedAt <= self::ts() && ($planAt === null || $savedAt < (int) $planAt)) { $planAt = $savedAt; $savedEarly = true; }
        $firstEpoch = $n ? self::tradeEpoch($trades[0]) : null;
        $ringPlan = 0;
        if ($planValid && !$planPast) $ringPlan = 100;   // a plan made for the day closes the ring (made late or not: that shows in the discipline score)
        $planLate = $planValid && !$planPast && $firstEpoch !== null && (int) $planAt > $firstEpoch;

        // execution
        $cum = 0; $ok = 0; $jn = 0; $det = []; $guardIdx = null; $perfect = $n > 0;
        foreach ($trades as $i => $t) {
            $v = [];
            if (self::stopBroken($t)) $v[] = 'no_stop';
            if ($planValid) {
                if ($bias === 'no_trade') $v[] = 'plan_no_trade';
                $dir = strtolower((string) ($t['direction'] ?? ''));
                if (($bias === 'bullish' && $dir === 'short') || ($bias === 'bearish' && $dir === 'long')) $v[] = 'against_bias';
                $st = self::low(trim((string) ($t['setup'] ?? '')));
                if ($planSetups && $st !== '' && !in_array($st, $planSetups, true)) $v[] = 'setup_not_in_plan';
                if ($maxLoss && $cum <= -$maxLoss) $v[] = 'over_max_loss';
                if ($maxTrades && $i >= $maxTrades) $v[] = 'over_max_trades';
            }
            $r = self::rules($t);
            // in your plan = nothing broken: no violation and the checklist not mostly « no »; one « no » counts half
            $good = !$v && $r !== 'no';
            if ($good) $ok += $r === 'partial' ? 0.5 : 1;
            $isJ = self::journaled($t);
            if ($isJ) $jn++;
            if (empty($t['shots']) || trim((string) ($t['notes'] ?? '')) === '') $perfect = false;
            $cum += self::net($t);
            if ($maxLoss && $guardIdx === null && $cum <= -$maxLoss) $guardIdx = $i;
            $det[] = ['id' => (string) $t['id'], 'ok' => $good, 'v' => $v, 'j' => $isJ, 'rules' => $r, 'e' => !empty(($t['emo'] ?? [])['before']), 's' => !empty($t['shots'])];
        }
        $execScore = $n ? (int) round(100 * $ok / $n) : null;   // trades in the plan: for the discipline score
        $ringExec = $n ? 100 : ($planValid ? 100 : 0);   // trading (or keeping to « no trade ») closes the ring
        $ok = (int) floor($ok);

        // review
        // the day's review is done once it is written somewhere: the « Daily review » sheet, the Journal page's
        // post-market fields, or a written review on every trade of the day (what went well / wrong / lesson)
        $txt = fn($v) => trim((string) ($v ?? '')) !== '';
        $postWritten = $txt($post['well'] ?? null) || $txt($post['tomorrow'] ?? null) || $txt($post['lesson'] ?? null) || $txt($post['wrong'] ?? null);
        $tradesReviewed = $n > 0;
        foreach ($trades as $t) { $rv = (array) ($t['review'] ?? []); if (!($txt($rv['well'] ?? null) || $txt($rv['wrong'] ?? null) || $txt($rv['lesson'] ?? null))) { $tradesReviewed = false; break; } }
        $reviewDone = !empty($post['reviewed_at']) || $postWritten || $tradesReviewed || $dayOff;
        $ringReview = $reviewDone ? 100 : ($n ? (int) round(60 * $jn / $n) : 0);   // the day's review closes the ring

        $swept = $ringPlan === 100 && $ringExec === 100 && $ringReview === 100;
        $guard = $planValid && $maxLoss && $guardIdx !== null && $guardIdx === $n - 1 && $n > 0;
        $activity = $n > 0 || $pre || $post;
        $row = [
            'ring_plan' => $ringPlan, 'ring_execution' => $ringExec, 'ring_review' => $ringReview, 'trades_count' => $n, 'compliant_count' => $ok, 'journaled_count' => $jn,
            'is_swept' => $swept ? 1 : 0, 'is_valid_streak' => ($ringReview === 100 || $dayOff) ? 1 : 0, 'review_done' => $reviewDone ? 1 : 0, 'day_off' => $dayOff ? 1 : 0,
            'plan_valid' => $planValid ? 1 : 0, 'plan_at' => $planAt, 'plan_bias' => $bias, 'guardrail' => $guard ? 1 : 0, 'activity' => $activity ? 1 : 0, 'net_c' => $cum,
            'detail_json' => json_encode(['trades' => $det, 'perfect_docs' => $perfect && $n > 0, 'plan_past' => $planPast, 'plan_late' => $planLate ?? false, 'exec_score' => $execScore ?? null]), 'updated_at' => self::ts(),
        ];
        if ($prev) {
            self::q('UPDATE game_days SET ' . implode(', ', array_map(fn($k) => "$k = ?", array_keys($row))) . ' WHERE user_id = ? AND trading_day = ?', [...array_values($row), $uid, $day]);
        } else {
            self::q('INSERT INTO game_days (user_id, trading_day, ' . implode(', ', array_keys($row)) . ') VALUES (?, ?, ' . implode(', ', array_fill(0, count($row), '?')) . ')', [$uid, $day, ...array_values($row)]);
        }

        // rewards (each key pays once)
        $gained = []; $pay = function (string $key, int $xp, string $label) use ($uid, &$gained): bool { if (!self::awardXp($uid, $key, $xp, [])) return false; $gained[] = [$label, $xp]; return true; };
        if ($ringPlan > 0 && $pay("plan:$day", $ringPlan === 100 ? GAME_XP['plan'] : GAME_XP['plan_late'], $ringPlan === 100 ? 'plan' : 'plan_late')) {
            self::track($uid, 'plan_saved', ['when' => $ringPlan === 100 ? 'early' : 'late']);
        }
        $paidJ = (int) self::q("SELECT COUNT(*) FROM xp_events WHERE user_id = ? AND event_key LIKE ?", [$uid, "journal:$day:%"])->fetchColumn();
        foreach ($det as $t) {
            if (!$t['j'] || $paidJ >= GAME_XP['journal_cap']) continue;
            if (self::awardXp($uid, "journal:$day:" . $t['id'], GAME_XP['journal'])) { $paidJ++; $gained[] = ['journal', GAME_XP['journal']]; self::track($uid, 'trade_journaled'); }
        }
        if ($dayOff) { if ($pay("dayoff:$day", GAME_XP['dayoff'], 'dayoff')) self::track($uid, 'dayoff'); }
        elseif ($reviewDone) { if (self::awardXp($uid, "review:$day", GAME_XP['review'])) { $gained[] = ['review', GAME_XP['review']]; self::track($uid, 'review_saved'); } }
        foreach (['plan' => $ringPlan, 'execution' => $ringExec, 'review' => $ringReview] as $ring => $v) {
            if ($v === 100 && self::awardXp($uid, "ring:$ring:$day", GAME_XP['ring'])) { $gained[] = ["ring_$ring", GAME_XP['ring']]; self::track($uid, 'ring_closed', ['ring' => $ring]); }
        }
        if ($swept && self::awardXp($uid, "sweep:$day", GAME_XP['sweep'])) {
            self::celebrate($uid, 'sweep', ['day' => $day, 'xp' => GAME_XP['sweep'] + array_sum(array_column($gained, 1)), 'day_off' => $dayOff]);
            self::track($uid, 'day_swept', ['day_off' => $dayOff]);
            $gained = [];
        }
        if ($guard && $reviewDone) self::guardrail($uid, $day);
        if ($gained) self::celebrate($uid, 'xp', ['xp' => array_sum(array_column($gained, 1)), 'items' => array_column($gained, 0)]);

        self::evaluateBadges($uid);
        self::startProgress($uid);
        if (class_exists('GameV2', false)) { try { GameV2::onDay($uid, $day); } catch (Throwable $e) { error_log('[Sweep game v2] ' . $e->getMessage()); } }
        return self::q('SELECT * FROM game_days WHERE user_id = ? AND trading_day = ?', [$uid, $day])->fetch(PDO::FETCH_ASSOC);
    }

    private static function guardrail(string $uid, string $day): void
    {
        if (self::awardXp($uid, "guardrail:$day", GAME_XP['guardrail'])) {
            self::celebrate($uid, 'guardrail', ['day' => $day, 'xp' => GAME_XP['guardrail']]);
            self::track($uid, 'guardrail', ['day' => $day]);
        }
    }

    /* ───────────── locking + streak ───────────── */

    /** Lock every day whose grace has ended and evaluate the streak. Same result whether run by the cron or on app open. */
    public static function catchUp(string $uid): void
    {
        $p = self::profile($uid, false);
        if (!$p) return;
        $start = $p['last_locked_day'] ? self::addDays($p['last_locked_day'], 1) : $p['started_on'];
        $today = self::today();
        $quota = null;
        for ($d = $start; $d < $today; $d = self::addDays($d, 1)) {
            if (!self::isLocked($d)) break;
            if (self::isMarketDay($d)) {
                self::recomputeDay($uid, $d);
                $p = self::profile($uid, false);
                $f = [];
                // weekly freeze refill (every Monday, never above the quota)
                $mon = self::monday($d);
                if ($p['freezes_reset_on'] === null || $mon > $p['freezes_reset_on']) {
                    $quota ??= self::freezeQuota($uid);
                    $f['freezes_available'] = $quota; $f['freezes_reset_on'] = $mon; $p['freezes_available'] = $quota;
                }
                $g = self::q('SELECT * FROM game_days WHERE user_id = ? AND trading_day = ?', [$uid, $d])->fetch(PDO::FETCH_ASSOC);
                $valid = $g && (int) $g['is_valid_streak'] === 1;
                if ($g && (int) $g['guardrail'] === 1) self::guardrail($uid, $d);
                $cur = (int) $p['streak_current']; $best = (int) $p['streak_best'];
                if ($valid) {
                    $cur++; $best = max($best, $cur);
                    $f += ['streak_current' => $cur, 'streak_best' => $best, 'streak_last_day' => $d, 'streak_start' => $cur === 1 ? $d : ($p['streak_start'] ?: $d)];
                    if (isset(GAME_STREAK_MILESTONES[$cur])) {
                        $startDay = $f['streak_start'];
                        if (self::awardXp($uid, "streak:$cur:$startDay", GAME_STREAK_MILESTONES[$cur])) {
                            self::celebrate($uid, 'streak', ['n' => $cur, 'xp' => GAME_STREAK_MILESTONES[$cur]]);
                            self::track($uid, 'streak_milestone', ['n' => $cur]);
                        }
                    }
                } elseif ($cur > 0) {   // nothing to protect before the first valid day
                    if ((int) $p['freezes_available'] > 0) {
                        $f['freezes_available'] = (int) $p['freezes_available'] - 1;
                        self::q('UPDATE game_days SET freeze_used = 1 WHERE user_id = ? AND trading_day = ?', [$uid, $d]);
                        if (!$g) self::q('INSERT INTO game_days (user_id, trading_day, freeze_used, updated_at) VALUES (?, ?, 1, ?)', [$uid, $d, self::ts()]);
                        if ($cur > 0) { self::celebrate($uid, 'freeze_used', ['day' => $d, 'left' => $f['freezes_available']]); self::track($uid, 'freeze_used'); }
                    } else {
                        $f += ['streak_current' => 0, 'streak_start' => null];
                        if ($cur >= 5 && class_exists('GameV2b', false)) { try { GameV2b::startQuest($uid, 'streak', $cur); } catch (Throwable $e) { error_log('[Sweep quest] ' . $e->getMessage()); } }
                        self::celebrate($uid, 'streak_lost', ['best' => $best]);
                        self::track($uid, 'streak_lost', ['was' => $cur]);
                    }
                }
                if ($g) self::q('UPDATE game_days SET locked_at = ? WHERE user_id = ? AND trading_day = ?', [self::ts(), $uid, $d]);
                if (class_exists('GameBoss', false)) { try { GameBoss::onLock($uid, $d); } catch (Throwable $e) { error_log('[Sweep boss] ' . $e->getMessage()); } }
                if ($f) self::setProfile($uid, $f);
            }
            self::setProfile($uid, ['last_locked_day' => $d]);
        }
        // the weekly refill happens on Monday even before Monday is locked
        $p = self::profile($uid, false);
        $mon = self::monday($today);
        if ($p['freezes_reset_on'] === null || $mon > $p['freezes_reset_on']) self::setProfile($uid, ['freezes_available' => self::freezeQuota($uid), 'freezes_reset_on' => $mon]);
        self::evaluateBadges($uid);
    }

    /* ───────────── onboarding / « Démarrage » ───────────── */

    public static function startProgress(string $uid): array
    {
        $p = self::profile($uid, false);
        $o = self::onboarding($p);
        $hasRules = (int) ($p['default_max_loss'] ?? 0) > 0;
        foreach (self::docs($uid, 'accounts') as $a) if (!empty(($a['rules'] ?? [])['dll_c'])) { $hasRules = true; break; }
        $c = self::q('SELECT SUM(CASE WHEN ring_plan > 0 THEN 1 ELSE 0 END) AS plans, SUM(review_done) AS reviews FROM game_days WHERE user_id = ?', [$uid])->fetch(PDO::FETCH_ASSOC) ?: [];
        $journaled = false; foreach (self::docs($uid, 'trades') as $t) if (self::journaled($t)) { $journaled = true; break; }
        $steps = ['goal' => !empty($p['goal']), 'style' => !empty($p['trading_style']), 'rules' => $hasRules, 'journal' => $journaled,
                  'plan' => (int) ($c['plans'] ?? 0) > 0, 'review' => (int) ($c['reviews'] ?? 0) > 0];
        $pct = 20;
        foreach (GAME_START_STEPS as $k => $w) if ($steps[$k]) { $pct += $w; if (self::awardXp($uid, "onboarding:$k", GAME_XP['onboarding'])) self::track($uid, 'onboarding_step', ['step' => $k]); }
        if ($pct >= 100 && empty($o['done'])) {
            $o['done'] = true;
            self::setProfile($uid, ['onboarding_json' => json_encode($o)]);
            self::unlock($uid, 'welcome');
            self::track($uid, 'onboarding_complete');
        }
        return ['percent' => min(100, $pct), 'steps' => $steps, 'done' => !empty($o['done'])];
    }

    /** First open: badges the existing history already earned (no past streak, no past Sweep). Idempotent. */
    public static function backfill(string $uid): array
    {
        $before = (int) (self::profile($uid, false)['xp_total'] ?? 0);
        $won = self::evaluateBadges($uid, true);
        $p = self::profile($uid, false);
        $xp = (int) $p['xp_total'] - $before;
        if ($won) { self::celebrate($uid, 'backfill', ['xp' => $xp, 'badges' => $won]); self::track($uid, 'backfill', ['xp' => $xp, 'n' => count($won)]); }
        return ['xp' => $xp, 'badges' => $won];
    }

    /* ───────────── read models for the app ───────────── */

    public static function dayState(string $uid, string $day): array
    {
        $g = self::q('SELECT * FROM game_days WHERE user_id = ? AND trading_day = ?', [$uid, $day])->fetch(PDO::FETCH_ASSOC) ?: null;
        $det = $g ? (json_decode((string) $g['detail_json'], true) ?: []) : [];
        return [
            'day' => $day, 'market' => self::isMarketDay($day), 'locked' => $g && $g['locked_at'] ? true : self::isLocked($day), 'deadline' => self::deadline($day),
            'rings' => ['plan' => (int) ($g['ring_plan'] ?? 0), 'execution' => (int) ($g['ring_execution'] ?? 0), 'review' => (int) ($g['ring_review'] ?? 0)],
            'trades' => (int) ($g['trades_count'] ?? 0), 'journaled' => (int) ($g['journaled_count'] ?? 0), 'compliant' => (int) ($g['compliant_count'] ?? 0),
            'swept' => (bool) ($g['is_swept'] ?? 0), 'valid' => (bool) ($g['is_valid_streak'] ?? 0), 'review_done' => (bool) ($g['review_done'] ?? 0),
            'day_off' => (bool) ($g['day_off'] ?? 0), 'plan_valid' => (bool) ($g['plan_valid'] ?? 0), 'plan_past' => !empty($det['plan_past']), 'plan_late' => !empty($det['plan_late']), 'exec_score' => $det['exec_score'] ?? null,
            'guardrail' => (bool) ($g['guardrail'] ?? 0), 'freeze_used' => (bool) ($g['freeze_used'] ?? 0), 'detail' => $det['trades'] ?? [],
        ];
    }

    /** progressive reveal: unlocked features (persisted), with a one-time « new » moment for each */
    public static function unlocks(string $uid): array
    {
        $p = self::profile($uid, false); if (!$p) return array_keys(GAME_UNLOCKS);
        $o = self::onboarding($p);
        $have = array_values(array_intersect((array) ($o['unlocked'] ?? []), array_keys(GAME_UNLOCKS)));
        $legacy = empty($o['unlock_init']) && (string) $p['started_on'] < self::addDays(self::today(), -3);   // already playing: keep everything
        $c = null; $days = (int) floor((self::ts() - (new DateTimeImmutable((string) $p['started_on']))->getTimestamp()) / 86400);
        $new = [];
        foreach (GAME_UNLOCKS as $f => $cond) {
            if (in_array($f, $have, true)) continue;
            if ($legacy) { $have[] = $f; continue; }
            $c = $c ?? self::counters($uid) + ['journaled' => (int) self::q("SELECT COALESCE(SUM(journaled_count), 0) FROM game_days WHERE user_id = ?", [$uid])->fetchColumn()];
            $met = function (array $req) use ($c, $p, $days): bool {
                foreach ($req as $k => $v) {
                    if ($k === 'or') continue;
                    $val = $k === 'swept' ? (int) $c['swept'] : ($k === 'level' ? (int) $p['level'] : ($k === 'trades' ? (int) $c['journaled'] : ($k === 'days' ? $days : 0)));
                    if ($val < (int) $v) return false;
                }
                return true;
            };
            if ($met($cond) || (isset($cond['or']) && $met($cond['or']))) { $have[] = $f; $new[] = $f; }
        }
        if ($new || empty($o['unlock_init'])) {
            $o['unlocked'] = array_values(array_unique($have)); $o['unlock_init'] = true;
            self::q('UPDATE user_game_profile SET onboarding_json = ? WHERE user_id = ?', [json_encode($o), $uid]);
            foreach ($new as $f) { self::celebrate($uid, 'unlock', ['feature' => $f]); self::track($uid, 'feature_unlocked', ['feature' => $f]); }
        }
        return $have;
    }

    public static function profileState(string $uid): array
    {
        $p = self::profile($uid, false);
        $xp = (int) $p['xp_total']; $lvl = (int) $p['level'];
        $nr = self::nextRank($lvl);
        // provisional streak: locked streak + valid days still in their grace window
        $streak = (int) $p['streak_current']; $todayValid = false; $broken = false;
        $from = $p['last_locked_day'] ? self::addDays($p['last_locked_day'], 1) : $p['started_on'];
        for ($d = $from; $d <= self::today(); $d = self::addDays($d, 1)) {
            if (!self::isMarketDay($d)) continue;
            $v = (int) self::q('SELECT is_valid_streak FROM game_days WHERE user_id = ? AND trading_day = ?', [$uid, $d])->fetchColumn();
            if ($d === self::today()) $todayValid = (bool) $v;
            if ($v && !$broken) $streak++; elseif (!$v && $d !== self::today()) $broken = true;
        }
        $o = self::onboarding($p);
        return [
            'xp' => $xp, 'level' => $lvl, 'rank' => $p['rank_key'], 'level_xp' => self::xpFor($lvl), 'next_level_xp' => self::xpFor($lvl + 1),
            'next_rank' => $nr ? ['rank' => $nr[1], 'level' => $nr[0], 'xp' => self::xpFor($nr[0]) - $xp] : null,
            'streak' => ['current' => $streak, 'best' => max((int) $p['streak_best'], $streak), 'today_valid' => $todayValid,
                         'freezes' => (int) $p['freezes_available'], 'quota' => self::freezeQuota($uid)],
            'sound' => (bool) $p['sound_enabled'], 'started_on' => $p['started_on'],
            'onboarding' => ['whats_new_due' => empty($o['whats_new']) && (string) ($p['started_on'] ?? '') !== '' && (string) $p['started_on'] < GAME_RELEASE_DATE && (bool) self::q('SELECT 1 FROM game_days WHERE user_id = ? AND trading_day < ? AND (activity = 1 OR trades_count > 0 OR plan_valid = 1 OR review_done = 1) LIMIT 1', [$uid, GAME_RELEASE_DATE])->fetchColumn(), 'seen' => !empty($o['seen']), 'existing' => !empty($o['existing']), 'done' => !empty($o['done']),
                             'goal' => $p['goal'], 'style' => $p['trading_style'], 'instruments' => $p['instruments'] ? explode(',', (string) $p['instruments']) : [],
                             'max_loss' => $p['default_max_loss'] !== null ? (int) $p['default_max_loss'] : null],
        ];
    }

    public static function pendingCelebrations(string $uid): array
    {
        $out = [];
        foreach (self::q('SELECT id, type, payload_json, created_at FROM game_celebrations WHERE user_id = ? AND seen_at IS NULL ORDER BY id LIMIT 20', [$uid]) as $r) {
            $out[] = ['id' => (int) $r['id'], 'type' => $r['type'], 'data' => json_decode((string) $r['payload_json'], true) ?: [], 'at' => (int) $r['created_at']];
        }
        return $out;
    }

    public static function badgesState(string $uid): array
    {
        $have = [];
        foreach (self::q('SELECT badge_id, unlocked_at FROM user_badges WHERE user_id = ?', [$uid]) as $r) $have[$r['badge_id']] = (int) $r['unlocked_at'];
        $prog = self::badgeProgress($uid);
        $out = [];
        foreach (GAME_BADGES as $id => $b) {
            $got = isset($have[$id]);
            $out[] = ['id' => $id, 'rarity' => $b['rarity'], 'secret' => $b['secret'] && !$got, 'xp' => $b['xp'], 'unlocked' => $got, 'unlocked_at' => $have[$id] ?? null,
                      'progress' => $b['secret'] && !$got ? null : ($prog[$id] ?? [$got ? 1 : 0, 1])];
        }
        return $out;
    }

    /* ───────────── event hooks (documents saved by the app) ───────────── */

    public static function onDoc(array $p, string $name): void
    {
        $uid = (string) ($p['uid'] ?? '');
        if ($uid === '' || !self::profile($uid, false)) return;
        self::forget($uid);
        $days = [];
        if (str_starts_with($name, 'trade.')) {
            foreach ([$p['doc'] ?? null, $p['prev'] ?? null] as $t) if (is_array($t) && ($d = self::tradeDay($t))) $days[$d] = true;
        } elseif (str_starts_with($name, 'journal.')) {
            if (preg_match('/^\d{4}-\d{2}-\d{2}$/', (string) ($p['id'] ?? ''))) $days[$p['id']] = true;
        }
        foreach (array_keys($days) as $d) self::recomputeDay($uid, $d);
    }
}

/** U.S. market holidays, 12 months ahead (NYSE closures; CME equity futures close early or halt on these days). */
const GAME_HOLIDAYS = [
    '2026-11-26' => 'Thanksgiving', '2026-12-25' => 'Christmas', '2027-01-01' => "New Year's Day", '2027-01-18' => 'Martin Luther King Jr. Day',
    '2027-02-15' => "Presidents' Day", '2027-03-26' => 'Good Friday', '2027-05-31' => 'Memorial Day', '2027-06-18' => 'Juneteenth (observed)',
    '2027-07-05' => 'Independence Day (observed)', '2027-09-06' => 'Labor Day',
];

/* ───────────── routes: api/game/* ───────────── */

function game_route(string $route, string $method, string $uid): void
{
    GameEngine::schema();
    $p = GameEngine::profile($uid);           // first open creates the profile + history backfill

    if ($route === 'api/game/today' && $method === 'GET') {
        GameEngine::catchUp($uid);
        $today = GameEngine::today();
        GameEngine::recomputeDay($uid, $today);
        $y = GameEngine::addDays($today, -1);
        while (!GameEngine::isMarketDay($y) && $y > GameEngine::addDays($today, -5)) $y = GameEngine::addDays($y, -1);
        if (!GameEngine::isLocked($y)) GameEngine::recomputeDay($uid, $y);
        json_out(200, [
            'today' => GameEngine::dayState($uid, $today),
            'unlocked' => GameEngine::unlocks($uid),
            'yesterday' => GameEngine::isLocked($y) ? null : GameEngine::dayState($uid, $y),
            'profile' => GameEngine::profileState($uid),
            'start' => GameEngine::startProgress($uid),
            'map' => (function () use ($uid) { GameV2::backfillMap($uid); GameV2::evaluateMap($uid); $m = GameV2::mapState($uid); return ['next' => $m['next'], 'current' => $m['current'], 'payout' => $m['payout']]; })(),
            'missions' => GameV2::missionsState($uid),
            'weekly' => GameV2b::weeklyState($uid, true),
            'quest' => (function () use ($uid) { GameV2b::schema(); GameV2b::checkAbsence($uid); return GameV2b::questState($uid); })(),
            'cosmetic' => GameV2b::cosmetics($uid)['equipped'],
            'crew' => (function () use ($uid) { try { $c = GameCrew::crewOf($uid); if (!$c) return null; $w = GameCrew::weekProgress($c); return ['name' => $c['name'], 'done' => $w['done'], 'goal' => $w['goal']]; } catch (Throwable $e) { return null; } })(),
            'buddy' => (function () use ($uid) { try { $b = GameCrew::buddyState($uid)['buddy']; return $b ? ['status' => $b['status'], 'incoming' => $b['incoming'], 'handle' => $b['card']['handle'] ?? null] : null; } catch (Throwable $e) { return null; } })(),
            'league' => (function () use ($uid) { try { $l = GameSocial::league($uid); } catch (Throwable $e) { return null; } if (!$l['group']) return null;
                $rank = 0; foreach ($l['group']['members'] as $i => $m) if ($m['me']) $rank = $i + 1; return ['tier' => $l['profile']['league_tier'], 'rank' => $rank, 'of' => count($l['group']['members'])]; })(),
            'season' => (function () use ($uid) { $s = GameSeason::state($uid); return ['id' => $s['id'], 'number' => $s['number'], 'name' => $s['name'], 'tier' => $s['tier'], 'claimable' => $s['claimable'], 'points' => $s['points'], 'per_tier' => $s['per_tier']]; })(),
            'wrapped' => (function () use ($uid) { GameWrapped::ensure($uid); try { GameWrappedYear::ensure($uid); } catch (Throwable $e) { error_log('[Sweep wrapped year] ' . $e->getMessage()); } try { GameNotifyService::run($uid); } catch (Throwable $e) { error_log('[Sweep notify] ' . $e->getMessage()); }
                $w = GameWrapped::state($uid)['items'][0] ?? null; return $w && $w['fresh'] ? ['month' => $w['month'], 'new' => $w['new']] : null; })(),
            'celebrations' => GameEngine::pendingCelebrations($uid),
        ]);
    }
    if ($route === 'api/game/profile' && $method === 'GET') {
        GameEngine::catchUp($uid);
        $c = GameEngine::counters($uid);
        $ref = null;
        try { if (function_exists('ref_get_code')) $ref = ref_get_code(db(), $uid); } catch (Throwable $e) { $ref = null; }
        json_out(200, ['profile' => GameEngine::profileState($uid), 'counters' => $c, 'badges' => GameEngine::badgesState($uid), 'ref' => $ref]);
    }
    if ($route === 'api/game/discord' && $method === 'GET') json_out(200, GameDiscord::state_($uid));
    if ($route === 'api/game/discord/start' && $method === 'GET') { $u = GameDiscord::authorizeUrl($uid); if (!$u) json_out(404, ['error' => 'discord_off']); header('Location: ' . $u, true, 302); exit; }
    if ($route === 'api/game/discord/callback' && $method === 'GET') {
        $ok = GameDiscord::callback($uid, (string) ($_GET['code'] ?? ''), (string) ($_GET['state'] ?? ''));
        $base = rtrim(str_replace('\\', '/', dirname((string) ($_SERVER['SCRIPT_NAME'] ?? '/'))), '/');
        header('Location: ' . $base . '/' . ($ok ? '?discord=linked' : '?discord=error') . '#settings', true, 302); exit;
    }
    if ($route === 'api/game/discord/unlink' && $method === 'POST') { GameDiscord::unlink($uid); json_out(200, GameDiscord::state_($uid)); }
    if ($route === 'api/game/discord/share' && $method === 'POST') { $b = body_json(256); GameDiscord::setShare($uid, !empty($b['on'])); json_out(200, GameDiscord::state_($uid)); }
    if ($route === 'api/game/crew' && $method === 'GET') json_out(200, GameCrew::crewState($uid) + ['buddy' => GameCrew::buddyState($uid)['buddy']]);
    if (strpos($route, 'api/game/crew/') === 0 && $method === 'POST') {
        $b = body_json(1024); $a = substr($route, 14);
        $r = match ($a) { 'create' => GameCrew::create($uid, (string) ($b['name'] ?? '')), 'join' => GameCrew::join($uid, (string) ($b['code'] ?? '')),
            'leave' => (GameCrew::leave($uid) ?? ['ok' => true]), 'goal' => ['ok' => GameCrew::setGoal($uid, (int) ($b['factor'] ?? 3))],
            'react' => ['ok' => GameCrew::react($uid, (int) ($b['id'] ?? 0), (string) ($b['emoji'] ?? ''))], default => ['error' => 'not_found'] };
        json_out(isset($r['error']) ? 400 : 200, $r + GameCrew::crewState($uid) + ['buddy' => GameCrew::buddyState($uid)['buddy']]);
    }
    if (strpos($route, 'api/game/buddy/') === 0 && $method === 'POST') {
        $b = body_json(1024); $a = substr($route, 15);
        $r = match ($a) { 'invite' => GameCrew::invite($uid, (string) ($b['handle'] ?? '')), 'respond' => (GameCrew::respond($uid, !empty($b['accept'])) ?? ['ok' => true]),
            'end' => (GameCrew::end($uid) ?? ['ok' => true]), 'cheer' => GameCrew::cheer($uid), default => ['error' => 'not_found'] };
        json_out(isset($r['error']) ? 400 : 200, $r + ['buddy' => GameCrew::buddyState($uid)['buddy']]);
    }
    if ($route === 'api/game/league' && $method === 'GET') json_out(200, GameSocial::league($uid));
    if ($route === 'api/game/social' && $method === 'GET') json_out(200, GameSocial::profile($uid));
    if ($route === 'api/game/social' && $method === 'POST') { $r = GameSocial::save($uid, body_json(1024)); json_out(isset($r['error']) ? 400 : 200, $r); }
    if ($route === 'api/game/report' && $method === 'POST') { $b = body_json(1024); GameSocial::report($uid, (string) ($b['type'] ?? 'handle'), (string) ($b['id'] ?? ''), (string) ($b['reason'] ?? '')); json_out(200, ['ok' => true]); }
    if ($route === 'api/game/season' && $method === 'GET') json_out(200, GameSeason::state($uid));
    if ($route === 'api/game/season/claim' && $method === 'POST') { $b = body_json(256); $r = GameSeason::claim($uid, (int) ($b['tier'] ?? 0), (string) ($b['track'] ?? '')); json_out(isset($r['error']) ? 400 : 200, $r + ['season' => GameSeason::state($uid)]); }
    if ($route === 'api/game/wrapped' && $method === 'GET') json_out(200, GameWrapped::state($uid));
    if ($route === 'api/game/wrapped/viewed' && $method === 'POST') { $b = body_json(256); if (preg_match('/^\d{4}-\d{2}$/', (string) ($b['month'] ?? ''))) GameWrapped::viewed($uid, $b['month']); json_out(200, ['ok' => true]); }
    if ($route === 'api/game/weekly' && $method === 'GET') { $w = GameV2b::weeklyState($uid); if (!empty($w['open'])) GameV2b::markSeen($uid, (string) $w['week']); json_out(200, $w); }   // opening the recap = seen (no reminder, no email after)
    if ($route === 'api/game/weekly' && $method === 'POST') { $r = GameV2b::saveWeekly($uid, body_json(4096)); json_out(isset($r['error']) ? 400 : 200, $r + ['celebrations' => GameEngine::pendingCelebrations($uid)]); }
    if ($route === 'api/game/chest' && $method === 'POST') { $r = GameV2b::openChest($uid); json_out(isset($r['error']) ? 400 : 200, $r + ['cosmetics' => GameV2b::cosmetics($uid)]); }
    if ($route === 'api/game/reveal/flip' && $method === 'POST') { $b = body_json(1024); json_out(200, GameV2b::flip($uid, (int) ($b['id'] ?? 0), in_array($b['lang'] ?? '', ['fr', 'es'], true) ? $b['lang'] : 'en')); }
    if ($route === 'api/game/reveal/second' && $method === 'GET') { $w = GameV2b::openWeek($uid); json_out(200, ['reveal' => $w ? GameV2b::reveal($uid, $w, 2) : null]); }
    if ($route === 'api/game/cosmetics' && $method === 'GET') json_out(200, GameV2b::cosmetics($uid));
    if ($route === 'api/game/cosmetics' && $method === 'POST') { $b = body_json(512); GameV2b::equip($uid, (string) ($b['id'] ?? '')); json_out(200, GameV2b::cosmetics($uid)); }
    if ($route === 'api/game/boss' && $method === 'GET') { GameEngine::catchUp($uid); json_out(200, GameBoss::state($uid, in_array($_GET['lang'] ?? '', ['fr', 'es'], true) ? $_GET['lang'] : 'en')); }
    if ($route === 'api/game/map' && $method === 'GET') { GameV2::backfillMap($uid); GameV2::evaluateMap($uid); json_out(200, GameV2::mapState($uid)); }
    if ($route === 'api/game/missions/reroll' && $method === 'POST') {
        $b = body_json(1024);
        $ok = GameV2::reroll($uid, (int) ($b['id'] ?? 0));
        json_out($ok ? 200 : 400, ['ok' => $ok, 'missions' => GameV2::missionsState($uid)]);
    }
    if ($route === 'api/game/badges' && $method === 'GET') json_out(200, ['badges' => GameEngine::badgesState($uid)]);
    if ($route === 'api/game/history' && $method === 'GET') {
        $from = preg_match('/^\d{4}-\d{2}-\d{2}$/', (string) ($_GET['from'] ?? '')) ? $_GET['from'] : GameEngine::addDays(GameEngine::today(), -40);
        $to = preg_match('/^\d{4}-\d{2}-\d{2}$/', (string) ($_GET['to'] ?? '')) ? $_GET['to'] : GameEngine::today();
        $st = db()->prepare('SELECT trading_day, ring_plan, ring_execution, ring_review, is_swept, is_valid_streak, day_off, freeze_used FROM game_days WHERE user_id = ? AND trading_day BETWEEN ? AND ? ORDER BY trading_day');
        $st->execute([$uid, $from, $to]);
        $hol = db()->prepare('SELECT day FROM market_holidays WHERE day BETWEEN ? AND ?'); $hol->execute([$from, $to]);
        json_out(200, ['days' => $st->fetchAll(PDO::FETCH_ASSOC), 'holidays' => array_column($hol->fetchAll(PDO::FETCH_ASSOC), 'day'), 'started_on' => $p['started_on'], 'today' => GameEngine::today()]);
    }
    if ($route === 'api/game/celebrations/seen' && $method === 'POST') {
        $b = body_json(8192);
        $ids = array_slice(array_map('intval', (array) ($b['ids'] ?? [])), 0, 50);
        if ($ids) {
            $st = db()->prepare('UPDATE game_celebrations SET seen_at = ? WHERE user_id = ? AND id IN (' . implode(',', array_fill(0, count($ids), '?')) . ') AND seen_at IS NULL');
            $st->execute([GameEngine::ts(), $uid, ...$ids]);
        }
        json_out(200, ['ok' => true]);
    }
    if ($route === 'api/game/onboarding' && $method === 'POST') {
        $b = body_json(8192);
        $o = GameEngine::onboarding($p);
        $f = [];
        if (isset($b['goal']) && in_array($b['goal'], ['evaluation', 'payout', 'consistency', 'edge'], true)) $f['goal'] = $b['goal'];
        if (isset($b['style']) && in_array($b['style'], ['scalp', 'intraday', 'swing'], true)) $f['trading_style'] = $b['style'];
        if (isset($b['instruments']) && is_array($b['instruments'])) $f['instruments'] = implode(',', array_slice(array_filter(array_map(fn($s) => preg_replace('/[^A-Z0-9]/', '', strtoupper((string) $s)), $b['instruments'])), 0, 10));
        if (isset($b['max_loss'])) { $v = (int) round((float) $b['max_loss'] * 100); if ($v > 0 && $v < 100000000) $f['default_max_loss'] = $v; }
        if (!empty($b['seen'])) $o['seen'] = true;
        if (!empty($b['whats_new'])) $o['whats_new'] = true;
        $f['onboarding_json'] = json_encode($o);
        $st = db()->prepare('UPDATE user_game_profile SET ' . implode(', ', array_map(fn($k) => "$k = ?", array_keys($f))) . ', updated_at = ? WHERE user_id = ?');
        $st->execute([...array_values($f), GameEngine::ts(), $uid]);
        json_out(200, ['start' => GameEngine::startProgress($uid), 'profile' => GameEngine::profileState($uid), 'celebrations' => GameEngine::pendingCelebrations($uid)]);
    }
    if ($route === 'api/game/sound' && $method === 'POST') {
        $b = body_json(1024);
        db()->prepare('UPDATE user_game_profile SET sound_enabled = ?, updated_at = ? WHERE user_id = ?')->execute([!empty($b['on']) ? 1 : 0, GameEngine::ts(), $uid]);
        json_out(200, ['ok' => true]);
    }
    if ($route === 'api/game/share' && $method === 'POST') {
        $b = body_json(2048);
        if (($b['kind'] ?? '') === 'locked_tap') GameEngine::track($uid, 'locked_feature_tapped');
        else GameEngine::track($uid, !empty($b['shared']) ? 'share_card_shared' : 'share_card_created', ['kind' => substr((string) ($b['kind'] ?? ''), 0, 20)]);
        json_out(200, ['ok' => true]);
    }
    json_out(404, ['error' => 'not found']);
}

/* recompute when the app saves a trade or a journal page */
if (class_exists('Events', false)) {
    foreach (['trade.created', 'trade.updated', 'trade.deleted', 'journal.saved', 'journal.deleted'] as $ev) {
        Events::on($ev, [GameEngine::class, 'onDoc']);
    }
    // activation analytics: every real trade logged (sample data excluded), with how it was entered
    Events::on('trade.created', function (array $p): void {
        $d = (array) ($p['doc'] ?? []);
        if (!empty($d['demo']) || empty($p['uid'])) return;
        $method = !empty($d['ai']) || !empty($d['ai_source']) ? 'ai' : (!empty($d['executions']) ? 'executions' : 'manual');
        GameEngine::track((string) $p['uid'], 'trade_logged', ['method' => $method, 'instrument' => (string) ($d['instrument'] ?? ''), 'copies' => !empty($d['copy_group'])]);
    });
}
