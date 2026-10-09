<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli' && realpath((string) ($_SERVER['SCRIPT_FILENAME'] ?? '')) === realpath(__FILE__)) { http_response_code(404); exit; }
/**
 * Sweep — Gamification V3, step 1: bosses (your bad habits, with a health bar).
 *
 * Detection is pure PHP on the last 20 market days (at least 15 trades). A clean day hits the boss (-1 HP),
 * a relapse heals it (+1 HP, never above its start). A relapse never costs XP or streak. Hits are written when
 * a day locks (same moment as the streak), so they never flip-flop; today's status is shown live.
 * Evidence is shown in % and R, never in dollars. Sweep AI only words the intro (Pro/Elite), cached in the row,
 * with a translated template as fallback; it never uses the trader's AI allowance.
 */

const GAME_BOSSES = ['revenge', 'fomo_open', 'cursed_day', 'oversize', 'moving_stop', 'overtrader', 'offplan', 'no_plan'];
const GAME_BOSS_HP = 10;
const GAME_BOSS_REMATCH_HP = 6;
const GAME_BOSS_XP = 500;

final class GameBoss
{
    private static function q(string $sql, array $a = []): PDOStatement { return GameEngine::q($sql, $a); }

    public static function schema(): void
    {
        static $done = false;
        if ($done) return;
        $done = true;
        $pdo = GameEngine::pdo();
        $my = $pdo->getAttribute(PDO::ATTR_DRIVER_NAME) === 'mysql';
        $T = $my ? 'VARCHAR(120)' : 'TEXT'; $AI = $my ? 'BIGINT AUTO_INCREMENT PRIMARY KEY' : 'INTEGER PRIMARY KEY AUTOINCREMENT'; $cs = $my ? ' DEFAULT CHARSET=utf8mb4' : '';
        $pdo->exec("CREATE TABLE IF NOT EXISTS user_bosses (id $AI, user_id $T NOT NULL, boss_id VARCHAR(30) NOT NULL, variant VARCHAR(20) NOT NULL DEFAULT 'normal',
            hp_max INT NOT NULL, hp INT NOT NULL, evidence_json TEXT NOT NULL, intro_text TEXT NULL, intro_lang VARCHAR(2) NULL, status VARCHAR(10) NOT NULL,
            started_at INT NOT NULL, defeated_at INT NULL, checked_at INT NULL)$cs");
        $pdo->exec("CREATE TABLE IF NOT EXISTS boss_hits (boss_row_id BIGINT NOT NULL, trading_day VARCHAR(10) NOT NULL, delta INT NOT NULL, PRIMARY KEY (boss_row_id, trading_day))$cs");
    }

    /* ───────────── data helpers ───────────── */

    private static function r(array $t): ?float
    {
        $risk = (int) ($t['risk_c'] ?? 0);
        return $risk > 0 ? GameEngine::net($t) / $risk : null;
    }
    private static function mins(?string $hm): ?int { return preg_match('/^(\d{2}):(\d{2})/', (string) $hm, $m) ? (int) $m[1] * 60 + (int) $m[2] : null; }
    private static function marketDaysBack(int $n): array
    {
        $out = []; $d = GameEngine::addDays(GameEngine::today(), -1);
        while (count($out) < $n && $d > '2000-01-01') { if (GameEngine::isMarketDay($d)) $out[] = $d; $d = GameEngine::addDays($d, -1); }
        return array_reverse($out);
    }
    /** trades of the window grouped by trading day, copies counted once, in entry order */
    private static function window(string $uid, array $days): array
    {
        $set = array_flip($days); $by = []; $seen = [];
        foreach (GameEngine::docs($uid, 'trades') as $t) {
            $d = GameEngine::tradeDay($t);
            if ($d === null || !isset($set[$d])) continue;
            $g = (string) ($t['copy_group'] ?? ''); if ($g !== '') { if (isset($seen[$g])) continue; $seen[$g] = true; }
            $by[$d][] = $t;
        }
        foreach ($by as &$list) usort($list, fn($a, $b) => strcmp((string) ($a['entry_time'] ?? ''), (string) ($b['entry_time'] ?? '')));
        return $by;
    }
    private static function gameDays(string $uid, array $days): array
    {
        if (!$days) return [];
        $st = self::q('SELECT * FROM game_days WHERE user_id = ? AND trading_day BETWEEN ? AND ?', [$uid, $days[0], end($days)]);
        $out = []; foreach ($st as $r) $out[$r['trading_day']] = $r; return $out;
    }

    /* ───────────── per-day pattern checks (shared by detection and daily hits) ───────────── */

    /** @return array{0: bool, 1: bool} [pattern happened, day counts as a clean hit] */
    public static function dayCheck(string $boss, array $trades, ?array $g, string $day, array $ev = []): array
    {
        $n = count($trades);
        $det = $g ? (json_decode((string) $g['detail_json'], true)['trades'] ?? []) : [];
        switch ($boss) {
            case 'revenge':
                $bad = false;
                for ($i = 1; $i < $n; $i++) {
                    if (GameEngine::net($trades[$i - 1]) >= 0) continue;
                    $out = self::mins($trades[$i - 1]['exit_time'] ?? $trades[$i - 1]['entry_time'] ?? null); $in = self::mins($trades[$i]['entry_time'] ?? null);
                    if ($out !== null && $in !== null && $in - $out >= 0 && $in - $out < 10) { $bad = true; break; }
                }
                return [$bad, $n > 0 && !$bad];
            case 'fomo_open':
                $open = array_filter($trades, fn($t) => ($m = self::mins($t['entry_time'] ?? null)) !== null && $m >= 570 && $m < 575);
                $offOpen = array_filter($det, fn($x) => !$x['ok'] && in_array($x['id'], array_map(fn($t) => (string) $t['id'], $open), true));
                $bad = (bool) ($g && (int) $g['plan_valid'] ? $offOpen : $open);
                return [$bad, $n > 0 && !$bad];
            case 'cursed_day':
                if ((int) (new DateTimeImmutable($day))->format('N') !== (int) ($ev['weekday'] ?? 0)) return [false, false];
                $clean = $g && (int) $g['plan_valid'] && (int) $g['ring_execution'] === 100;
                return [$n > 0 && !$clean, $clean];
            case 'oversize':
                $bad = false; $wins = 0;
                for ($i = 0; $i < $n; $i++) {
                    if ($i > 0 && $wins >= 2 && (float) ($trades[$i]['contracts'] ?? 0) > (float) ($trades[$i - 1]['contracts'] ?? 0)) { $bad = true; break; }
                    $wins = GameEngine::net($trades[$i]) > 0 ? $wins + 1 : 0;
                }
                $constant = $n > 0 && count(array_unique(array_map(fn($t) => (string) ($t['contracts'] ?? ''), $trades))) === 1;
                return [$bad, $constant];
            case 'moving_stop':
                $bad = false;
                foreach ($trades as $t) {
                    $d = (array) ($t['discipline'] ?? []);
                    if (in_array('stop', (array) ($t['auto_flags'] ?? []), true) || ($d['stop'] ?? '') === 'n' || ($d['widen'] ?? '') === 'n' || ($t['rules_followed'] ?? '') === 'partial') { $bad = true; break; }
                }
                return [$bad, $n > 0 && !$bad];
            case 'overtrader':
                $over = array_filter($det, fn($x) => in_array('over_max_trades', $x['v'] ?? [], true));
                $hasMax = (bool) ($ev['has_max'][$day] ?? false);
                return [(bool) $over, $n > 0 && $hasMax && !$over];
            case 'offplan':
                $off = array_filter($det, fn($x) => in_array('setup_not_in_plan', $x['v'] ?? [], true) || in_array('plan_no_trade', $x['v'] ?? [], true));
                return [(bool) $off, $n > 0 && $g && (int) $g['plan_valid'] && !$off];
            case 'no_plan':
                $early = $g && (int) $g['plan_valid'] && $g['plan_at'] && (int) $g['plan_at'] < GameEngine::epochEt($day, '09:30');
                return [!$early, (bool) $early];
        }
        return [false, false];
    }

    /* ───────────── detection (last 20 market days, min 15 trades) ───────────── */

    public static function detect(string $uid): array
    {
        $days = self::marketDaysBack(20);
        $by = self::window($uid, $days);
        $gd = self::gameDays($uid, $days);
        $all = array_merge(...array_values($by ?: [[]]));
        $n = count($all);
        $found = [];
        if ($n >= 15) {
            // revenge: >= 25 % of losses followed by a trade within 10 min
            $losses = 0; $quick = 0;
            foreach ($by as $list) for ($i = 0; $i < count($list); $i++) {
                if (GameEngine::net($list[$i]) >= 0) continue;
                $losses++;
                if (isset($list[$i + 1])) { $o = self::mins($list[$i]['exit_time'] ?? $list[$i]['entry_time'] ?? null); $e = self::mins($list[$i + 1]['entry_time'] ?? null); if ($o !== null && $e !== null && $e - $o >= 0 && $e - $o < 10) $quick++; }
            }
            if ($losses >= 4 && $quick / $losses >= .25) $found['revenge'] = ['score' => $quick / $losses / .25, 'pct' => round($quick / $losses * 100), 'losses' => $losses, 'quick' => $quick];
            // fomo at the open: >= 20 % of trades in 9:30-9:35 with average R < -0.3
            $open = array_filter($all, fn($t) => ($m = self::mins($t['entry_time'] ?? null)) !== null && $m >= 570 && $m < 575);
            $rs = array_values(array_filter(array_map([self::class, 'r'], $open), fn($x) => $x !== null));
            if (count($open) / $n >= .2 && count($rs) >= 3 && array_sum($rs) / count($rs) < -.3) $found['fomo_open'] = ['score' => count($open) / $n / .2 + abs(array_sum($rs) / count($rs)), 'pct' => round(count($open) / $n * 100), 'r' => round(array_sum($rs) / count($rs), 2)];
            // cursed day: one weekday with average R clearly below the others
            $wd = [];
            foreach ($all as $t) { $r = self::r($t); if ($r === null) continue; $w = (int) (new DateTimeImmutable((string) GameEngine::tradeDay($t)))->format('N'); $wd[$w][] = $r; }
            $allR = array_merge(...array_values($wd ?: [[]]));
            if (count($allR) >= 15) {
                $avg = array_sum($allR) / count($allR);
                foreach ($wd as $w => $list) {
                    if (count($list) < 4) continue;
                    $a = array_sum($list) / count($list);
                    $others = array_merge(...array_values(array_diff_key($wd, [$w => 1])));
                    $o = $others ? array_sum($others) / count($others) : $avg;
                    if ($a < $o - .5 && $a < 0 && (!isset($found['cursed_day']) || $a < $found['cursed_day']['r'])) $found['cursed_day'] = ['score' => ($o - $a) * 2, 'weekday' => $w, 'r' => round($a, 2), 'others' => round($o, 2)];
                }
            }
            // oversize: size up after 2+ wins in a row, at least 3 times
            $times = 0;
            foreach ($by as $list) { $wins = 0; for ($i = 0; $i < count($list); $i++) { if ($i > 0 && $wins >= 2 && (float) ($list[$i]['contracts'] ?? 0) > (float) ($list[$i - 1]['contracts'] ?? 0)) $times++; $wins = GameEngine::net($list[$i]) > 0 ? $wins + 1 : 0; } }
            if ($times >= 3) $found['oversize'] = ['score' => $times / 3, 'times' => $times];
            // moving stop: stop not respected / widened / rules partly followed on >= 20 % of trades
            $ms = 0; foreach ($all as $t) { $d = (array) ($t['discipline'] ?? []); if (in_array('stop', (array) ($t['auto_flags'] ?? []), true) || ($d['stop'] ?? '') === 'n' || ($d['widen'] ?? '') === 'n' || ($t['rules_followed'] ?? '') === 'partial') $ms++; }
            if ($ms >= 3 && $ms / $n >= .2) $found['moving_stop'] = ['score' => $ms / $n / .2, 'pct' => round($ms / $n * 100), 'times' => $ms];
        }
        // plan-based bosses read the scored days (needs 10 market days of game data)
        $scored = array_filter($gd, fn($g) => $g['trading_day'] >= ($days[0] ?? ''));
        if (count($scored) >= 10) {
            $planDays = 0; $noEarly = 0; $withMax = 0; $over = 0; $tot = 0; $off = 0;
            foreach ($scored as $d => $g) {
                [$happened] = self::dayCheck('no_plan', [], $g, $d); if ($happened) $noEarly++;
                $det = json_decode((string) $g['detail_json'], true)['trades'] ?? [];
                foreach ($det as $x) { $tot++; if (in_array('setup_not_in_plan', $x['v'] ?? [], true)) $off++; }
                if (array_filter($det, fn($x) => in_array('over_max_trades', $x['v'] ?? [], true))) $over++;
                $j = GameEngine::docs($uid, 'journals')[$d] ?? []; if (!empty(($j['pre'] ?? [])['max_trades'])) $withMax++;
            }
            $c = count($scored);
            if ($noEarly / $c >= .5) $found['no_plan'] = ['score' => $noEarly / $c / .5, 'pct' => round($noEarly / $c * 100), 'days' => $c];
            if ($withMax >= 5 && $over / $withMax >= .3) $found['overtrader'] = ['score' => $over / $withMax / .3, 'pct' => round($over / $withMax * 100)];
            if ($tot >= 15 && $off / $tot >= .3) $found['offplan'] = ['score' => $off / $tot / .3, 'pct' => round($off / $tot * 100)];
        }
        uasort($found, fn($a, $b) => $b['score'] <=> $a['score']);
        return $found;
    }

    /* ───────────── lifecycle ───────────── */

    private static function slots(string $uid): int { return GameV2::plan($uid) === 'elite' ? 2 : 1; }

    /** spawn the most costly detected pattern(s); handles the 30-day « for good » check */
    public static function refresh(string $uid): void
    {
        self::schema();
        $now = GameEngine::ts();
        // 30 days after a victory: did the habit stay gone?
        foreach (self::q("SELECT * FROM user_bosses WHERE user_id = ? AND status = 'defeated' AND checked_at IS NULL AND defeated_at < ?", [$uid, $now - 30 * 86400])->fetchAll(PDO::FETCH_ASSOC) as $b) {
            $back = isset(self::detect($uid)[$b['boss_id']]);
            self::q("UPDATE user_bosses SET checked_at = ?, status = ? WHERE id = ?", [$now, $back ? 'dormant' : 'defeated', $b['id']]);
            if (!$back) { GameEngine::unlock($uid, 'boss_for_good'); }
            elseif (GameV2::plan($uid) === 'elite') { self::spawn($uid, $b['boss_id'], json_decode((string) $b['evidence_json'], true) ?: [], 'rematch'); }   // « Revanche » is an Elite feature; otherwise normal detection can bring it back
        }
        $active = self::q("SELECT boss_id FROM user_bosses WHERE user_id = ? AND status = 'active'", [$uid])->fetchAll(PDO::FETCH_COLUMN);
        if (count($active) >= self::slots($uid)) return;
        // detection at most once a day
        $p = GameEngine::profile($uid, false); $o = GameEngine::onboarding($p);
        if (($o['boss_checked'] ?? '') === GameEngine::today()) return;
        $o['boss_checked'] = GameEngine::today();
        self::q('UPDATE user_game_profile SET onboarding_json = ? WHERE user_id = ?', [json_encode($o), $uid]);
        $recent = self::q("SELECT boss_id FROM user_bosses WHERE user_id = ? AND (status = 'active' OR (defeated_at IS NOT NULL AND defeated_at > ?))", [$uid, $now - 30 * 86400])->fetchAll(PDO::FETCH_COLUMN);
        foreach (self::detect($uid) as $id => $ev) {
            if (in_array($id, $recent, true) || in_array($id, $active, true)) continue;
            self::spawn($uid, $id, $ev, 'normal');
            $active[] = $id;
            if (count($active) >= self::slots($uid)) break;
        }
    }

    private static function spawn(string $uid, string $id, array $ev, string $variant): void
    {
        $hp = $variant === 'rematch' ? GAME_BOSS_REMATCH_HP : GAME_BOSS_HP;
        self::q("INSERT INTO user_bosses (user_id, boss_id, variant, hp_max, hp, evidence_json, status, started_at) VALUES (?, ?, ?, ?, ?, ?, 'active', ?)",
            [$uid, $id, $variant, $hp, $hp, json_encode($ev), GameEngine::ts()]);
        GameEngine::celebrate($uid, 'boss_spawn', ['boss' => $id, 'variant' => $variant]);
        GameEngine::track($uid, 'boss_spawned', ['boss' => $id, 'variant' => $variant]);
    }

    /** called when a market day locks: one hit or one relapse per active boss */
    public static function onLock(string $uid, string $day): void
    {
        self::schema();
        $bosses = self::q("SELECT * FROM user_bosses WHERE user_id = ? AND status = 'active' AND started_at <= ?", [$uid, GameEngine::deadline($day)])->fetchAll(PDO::FETCH_ASSOC);
        if (!$bosses) return;
        $by = self::window($uid, [$day]); $gd = self::gameDays($uid, [$day]);
        $max = !empty(((GameEngine::docs($uid, 'journals')[$day] ?? [])['pre'] ?? [])['max_trades']);
        foreach ($bosses as $b) {
            $startDay = (new DateTimeImmutable('@' . (int) $b['started_at']))->setTimezone(new DateTimeZone('America/New_York'))->modify('+6 hours')->format('Y-m-d');
            if ($day < $startDay) continue;   // only days after the boss appeared
            $ev = (json_decode((string) $b['evidence_json'], true) ?: []) + ['has_max' => [$day => $max]];
            [$bad, $clean] = self::dayCheck($b['boss_id'], $by[$day] ?? [], $gd[$day] ?? null, $day, $ev);
            $delta = $bad ? 1 : ($clean ? -1 : 0);
            if ($delta === 0) continue;
            try { self::q('INSERT INTO boss_hits (boss_row_id, trading_day, delta) VALUES (?, ?, ?)', [$b['id'], $day, $delta]); } catch (Throwable $e) { continue; }   // once per day
            $hp = max(0, min((int) $b['hp_max'], (int) $b['hp'] + $delta));
            self::q('UPDATE user_bosses SET hp = ? WHERE id = ?', [$hp, $b['id']]);
            GameEngine::track($uid, $delta < 0 ? 'boss_hit' : 'boss_relapse', ['boss' => $b['boss_id']]);
            if ($hp === 0) {
                self::q("UPDATE user_bosses SET status = 'defeated', defeated_at = ? WHERE id = ?", [GameEngine::ts(), $b['id']]);
                GameEngine::awardXp($uid, 'boss:' . $b['id'], GAME_BOSS_XP);
                GameEngine::unlock($uid, 'boss_' . $b['boss_id'], true);
                GameEngine::celebrate($uid, 'boss_defeated', ['boss' => $b['boss_id'], 'xp' => GAME_BOSS_XP, 'variant' => $b['variant']]);
                GameEngine::track($uid, 'boss_defeated', ['boss' => $b['boss_id']]);
            }
        }
    }

    /* ───────────── intro text (Sweep AI wording only, Pro/Elite, cached in the row) ───────────── */

    private static function intro(string $uid, array $b, string $lang): ?string
    {
        if ($b['intro_text'] && $b['intro_lang'] === $lang) return $b['intro_text'];
        if (GameV2::plan($uid) === 'free') return null;
        try {
            global $cfg;
            if (!empty($cfg['ai_config']) && !defined('SWEEP_AI_CONFIG')) define('SWEEP_AI_CONFIG', (string) $cfg['ai_config']);
            $core = dirname(__DIR__) . '/ai/ai-core.php';
            if (!is_file($core)) return null;
            require_once $core;
            if (!function_exists('sai_call')) return null;
            $ev = json_decode((string) $b['evidence_json'], true) ?: [];
            $name = ['en' => 'English', 'fr' => 'Canadian French (tutoiement)', 'es' => 'Spanish'][$lang] ?? 'English';
            $prompt = "A trading-discipline app turns a trader's bad habit into a playful boss to defeat. Boss: {$b['boss_id']}. Evidence (computed, last 20 market days): " . json_encode($ev)
                . ". Write the boss introduction in $name: exactly 2 short sentences, teasing but kind, about the habit and that clean days hit it. No dollar amounts, no financial advice, no predictions."
                . ' Return JSON {"text": "..."}.';
            $r = sai_call(GameEngine::pdo(), $uid, 'game_boss_intro', $prompt, ['max_tokens' => 200, 'temperature' => .6]);
            $text = trim((string) (($r['data'] ?? [])['text'] ?? ''));
            if ($text === '' || strlen($text) > 600 || preg_match('/\$\s?\d/', $text)) return null;
            self::q('UPDATE user_bosses SET intro_text = ?, intro_lang = ? WHERE id = ?', [$text, $lang, $b['id']]);
            return $text;
        } catch (Throwable $e) { return null; }   // translated template on the client
    }

    /* ───────────── read model ───────────── */

    public static function state(string $uid, string $lang = 'en'): array
    {
        self::schema();
        self::refresh($uid);
        $rows = self::q("SELECT * FROM user_bosses WHERE user_id = ? AND status = 'active' ORDER BY started_at", [$uid])->fetchAll(PDO::FETCH_ASSOC);
        $today = GameEngine::today();
        $out = [];
        foreach ($rows as $b) {
            $ev = json_decode((string) $b['evidence_json'], true) ?: [];
            $by = self::window($uid, [$today]); $gd = self::gameDays($uid, [$today]);
            $max = !empty(((GameEngine::docs($uid, 'journals')[$today] ?? [])['pre'] ?? [])['max_trades']);
            [$bad, $clean] = GameEngine::isMarketDay($today) ? self::dayCheck($b['boss_id'], $by[$today] ?? [], $gd[$today] ?? null, $today, $ev + ['has_max' => [$today => $max]]) : [false, false];
            $hits = self::q('SELECT trading_day, delta FROM boss_hits WHERE boss_row_id = ? ORDER BY trading_day DESC LIMIT 20', [$b['id']])->fetchAll(PDO::FETCH_ASSOC);
            $out[] = ['row' => (int) $b['id'], 'boss' => $b['boss_id'], 'variant' => $b['variant'], 'hp' => (int) $b['hp'], 'hp_max' => (int) $b['hp_max'], 'evidence' => $ev,
                      'intro' => self::intro($uid, $b, $lang), 'today' => $bad ? 'relapse' : ($clean ? 'hit' : 'pending'),
                      'hits' => array_map(fn($h) => ['day' => $h['trading_day'], 'delta' => (int) $h['delta']], array_reverse($hits))];
        }
        $won = self::q("SELECT boss_id, defeated_at FROM user_bosses WHERE user_id = ? AND defeated_at IS NOT NULL ORDER BY defeated_at DESC", [$uid])->fetchAll(PDO::FETCH_ASSOC);
        return ['active' => $out, 'defeated' => array_map(fn($w) => ['boss' => $w['boss_id'], 'at' => (int) $w['defeated_at']], $won), 'slots' => self::slots($uid)];
    }
}
