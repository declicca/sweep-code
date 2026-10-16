<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli' && realpath((string) ($_SERVER['SCRIPT_FILENAME'] ?? '')) === realpath(__FILE__)) { http_response_code(404); exit; }
/**
 * Sweep — Gamification V2, step 1: chapter map (« Parcours ») and weekly missions.
 * Built on the V1 engine (GameEngine): same XP ledger, badges, celebrations, game_days.
 * Discipline only: no node and no mission counts trades to take, amounts or win rate.
 * The payout chapter shows readiness as a percentage only, never an amount.
 */

/* ───────────── catalog: chapters and nodes ───────────── */
/** node id => [chapter, target, xp, metric]; nodes marked 'soon' unlock with step 2 (weekly review, Edge Reveal) */
const GAME_MAP = [
    1 => ['c1_goal' => [1, 30, 'goal'], 'c1_rules' => [1, 30, 'rules'], 'c1_plan' => [1, 40, 'plans'], 'c1_journal' => [1, 40, 'journaled'],
          'c1_review' => [1, 40, 'reviews'], 'c1_journal10' => [10, 60, 'journaled'], 'c1_sweep' => [1, 80, 'swept']],
    2 => ['c2_setups' => [3, 50, 'setups'], 'c2_journal30' => [30, 60, 'journaled'], 'c2_edge' => [1, 60, 'edge_reveals'],
          'c2_sweep5' => [5, 70, 'swept'], 'c2_weekly' => [1, 60, 'weekly_reviews'], 'c2_journal50' => [50, 100, 'journaled_full']],
    3 => ['c3_streak10' => [10, 80, 'best_streak'], 'c3_window' => [10, 100, 'swept_15'], 'c3_week' => [1, 100, 'perfect_week'],
          'c3_weekly4' => [4, 90, 'weekly_run'], 'c3_compliant20' => [20, 100, 'compliant_best']],
    4 => ['c4_setup' => [1, 40, 'payout_config'], 'c4_half' => [50, 70, 'payout_ready'], 'c4_ready' => [100, 100, 'payout_ready'], 'c4_payout' => [1, 100, 'payouts']],
    5 => ['c5_accounts' => [2, 50, 'accounts'], 'c5_expenses' => [1, 40, 'expenses'], 'c5_payouts3' => [3, 90, 'payouts'], 'c5_net' => [1, 100, 'net_positive'],
          'c5_streak60' => [60, 100, 'best_streak']],
];
/** chapter 4 for traders without a prop firm: months with 70 % valid market days */
const GAME_MAP_C4_PERSONAL = ['c4p_month1' => [1, 60, 'months_70'], 'c4p_month2' => [2, 80, 'months_70'], 'c4p_month3' => [3, 100, 'months_70']];
const GAME_MAP_SOON = [];   // weekly review and Edge Reveal are live (step 2)
const GAME_CHAPTER_XP = 300;
const GAME_CHAPTER_FREE = 2;   // Free: chapters 1-2, Pro/Elite: everything

/* ───────────── catalog: weekly missions ───────────── */
/** id => [difficulty 1-3, target, metric]; difficulty pays 50 / 100 / 150 XP */
const GAME_MISSIONS = [
    'm_review_3'     => [1, 3, 'review_days'],
    'm_plan_3'       => [1, 3, 'plan_days'],
    'm_emotion_5'    => [1, 5, 'emotion_trades'],
    'm_plan_early'   => [2, 3, 'plan_early_days'],
    'm_screens'      => [2, 5, 'screen_trades'],
    'm_sweep_2'      => [2, 2, 'swept_days'],
    'm_no_offplan'   => [2, 4, 'clean_days'],
    'm_review_all'   => [3, 5, 'review_days'],
    'm_sweep_3'      => [3, 3, 'swept_days'],
    'm_emotion_all'  => [3, 4, 'emotion_days'],
    'm_maxloss'      => [3, 3, 'maxloss_days'],
];
const GAME_MISSION_XP = [1 => 50, 2 => 100, 3 => 150];

final class GameV2
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
        $pdo->exec("CREATE TABLE IF NOT EXISTS user_map_nodes (user_id $T NOT NULL, node_id VARCHAR(40) NOT NULL, progress INT NOT NULL DEFAULT 0, target INT NOT NULL,
            completed_at INT NULL, PRIMARY KEY (user_id, node_id))$cs");
        $pdo->exec("CREATE TABLE IF NOT EXISTS user_missions (id $AI, user_id $T NOT NULL, week_start VARCHAR(10) NOT NULL, mission_id VARCHAR(40) NOT NULL,
            difficulty INT NOT NULL, progress INT NOT NULL DEFAULT 0, target INT NOT NULL, completed_at INT NULL, rerolled INT NOT NULL DEFAULT 0)$cs");
        $pdo->exec("CREATE TABLE IF NOT EXISTS user_rewards (id $AI, user_id $T NOT NULL, source VARCHAR(30) NOT NULL, reward_type VARCHAR(30) NOT NULL,
            reward_value VARCHAR(80) NOT NULL, created_at INT NOT NULL, used_at INT NULL)$cs");
        if ($my) { try { $pdo->exec('ALTER TABLE user_missions ADD UNIQUE KEY uq_mission (user_id, week_start, mission_id)'); } catch (Throwable $e) { /* exists */ } }
        else $pdo->exec('CREATE UNIQUE INDEX IF NOT EXISTS uq_mission ON user_missions (user_id, week_start, mission_id)');
    }

    public static function plan(string $uid): string
    {
        try { if (function_exists('billing_on') && billing_on() && function_exists('sb_plan')) return sb_plan(GameEngine::pdo(), $uid); } catch (Throwable $e) { /* billing off */ }
        return 'pro';   // early access / first 60 days: Pro
    }

    /* ───────────── metrics (computed in PHP from real data) ───────────── */

    public static function metrics(string $uid): array
    {
        $trades = array_values(GameEngine::docs($uid, 'trades'));
        $journaled = 0; $full = 0; $setups = [];
        foreach ($trades as $t) {
            if (GameEngine::journaled($t)) $journaled++;
            if (GameEngine::journaled($t) && !empty(($t['emo'] ?? [])['before'])) $full++;
            $s = strtolower(trim((string) ($t['setup'] ?? ''))); if ($s !== '') $setups[$s] = true;
        }
        $c = GameEngine::counters($uid);
        $p = GameEngine::profile($uid, false);
        $prog = GameEngine::badgeProgress($uid, $c);
        $accounts = array_filter(GameEngine::docs($uid, 'accounts'), fn($a) => ($a['status'] ?? '') !== 'archived');
        $paid = array_filter(GameEngine::docs($uid, 'payouts'), fn($x) => ($x['status'] ?? '') === 'paid');
        $exp = GameEngine::docs($uid, 'expenses');
        $paidSum = array_sum(array_map(fn($x) => (int) ($x['amount_c'] ?? 0), $paid));
        $expSum = array_sum(array_map(fn($x) => (int) ($x['amount_c'] ?? 0), $exp));
        [$cfg, $ready] = self::payoutReadiness($uid);
        $start = GameEngine::startProgress($uid);
        // 10 swept days inside any 15 consecutive market days
        $days = self::q('SELECT trading_day, is_swept, is_valid_streak FROM game_days WHERE user_id = ? ORDER BY trading_day', [$uid])->fetchAll(PDO::FETCH_ASSOC);
        $flags = array_map(fn($d) => (int) $d['is_swept'], array_values(array_filter($days, fn($d) => GameEngine::isMarketDay($d['trading_day']))));
        $win = 0; for ($i = 0; $i < count($flags); $i++) $win = max($win, array_sum(array_slice($flags, max(0, $i - 14), min(15, $i + 1))));
        return [
            'goal' => !empty($p['goal']) ? 1 : 0, 'rules' => $start['steps']['rules'] ? 1 : 0, 'plans' => $c['plans'], 'journaled' => $journaled,
            'reviews' => $c['reviews'], 'swept' => $c['swept'], 'setups' => count($setups), 'journaled_full' => $full,
            'edge_reveals' => self::countIf('edge_reveals', $uid, 'revealed_at IS NOT NULL'), 'weekly_reviews' => self::countIf('weekly_reviews', $uid, '1 = 1'),
            'weekly_run' => self::weeklyRun($uid), 'best_streak' => max((int) $p['streak_best'], (int) $p['streak_current']), 'swept_15' => $win,
            'perfect_week' => $prog['full_week'][0], 'compliant_best' => $c['compliant_best'],
            'payout_config' => $cfg ? 1 : 0, 'payout_ready' => $ready, 'payouts' => count($paid), 'accounts' => count($accounts), 'expenses' => count($exp),
            'net_positive' => ($paidSum > 0 && $paidSum > $expSum) ? 1 : 0, 'months_70' => self::months70($days),
        ];
    }
    private static function countIf(string $table, string $uid, string $where): int
    {
        try { return (int) self::q("SELECT COUNT(*) FROM $table WHERE user_id = ? AND $where", [$uid])->fetchColumn(); } catch (Throwable $e) { return 0; }   // table arrives in step 2
    }
    private static function weeklyRun(string $uid): int { return class_exists('GameV2b', false) ? GameV2b::weeklyRun($uid) : 0; }

    /** consecutive calendar months (latest run) with >= 70 % valid market days */
    private static function months70(array $days): int
    {
        $by = [];
        foreach ($days as $d) { if (!GameEngine::isMarketDay($d['trading_day'])) continue; $m = substr($d['trading_day'], 0, 7); $by[$m][0] = ($by[$m][0] ?? 0) + 1; $by[$m][1] = ($by[$m][1] ?? 0) + (int) $d['is_valid_streak']; }
        ksort($by); $run = 0; $best = 0;
        foreach ($by as $m => [$n, $v]) { if ($m >= substr(GameEngine::today(), 0, 7)) continue; $run = ($n >= 10 && $v / $n >= .7) ? $run + 1 : 0; $best = max($best, $run); }
        return $best;
    }

    /**
     * One funded account's next payout, with the same rules as the app's payout counter (src/nav.js SweepPayout.status, brief 02
     * part 3): winning and traded days since the last request, profit since the last payout, consistency, the balance to keep,
     * the amount that can be asked for (cap, ladder step), the firm's number of payouts. The app also knows when an account is
     * breached; here a failed or archived account is skipped. Returns [ready, 0-100 (100 only when ready)] or null without payout rules.
     */
    /** consistency, the app's one rule (consPct, src/app.js; brief 00, Q4): the best day as a % of the total net profit, or of
     *  the winning days when the firm's catalogue says « consistency_base: win »; null without a profit */
    public static function consPct(array $days, ?string $base = null): ?float
    {
        $pos = array_filter($days, fn($v) => $v > 0); $best = $pos ? max($pos) : 0; $sum = array_sum($base === 'win' ? $pos : $days);
        return $best > 0 && $sum > 0 ? $best / $sum * 100 : null;
    }

    public static function payoutStatus(array $a, array $trades, array $pays): ?array
    {
        $r = (array) ($a['rules'] ?? []);
        $has = false; foreach (['payout_win_days', 'payout_trade_days', 'payout_min_bal_c', 'payout_min_c', 'payout_max_c', 'payout_cycle_pos', 'payout_first_min_c'] as $k) if (!empty($r[$k])) $has = true;
        if (!$has) return null;
        $id = (string) ($a['id'] ?? ''); $start = (int) ($a['starting_balance_c'] ?? 0);
        // requested, approved or paid: each one restarts the count and is one step of the ladder (a planned one is not asked yet)
        $mine = array_values(array_filter($pays, fn($p) => ($p['account_id'] ?? '') === $id && !in_array($p['status'] ?? '', ['rejected', 'planned'], true)));
        $last = '';
        foreach ($mine as $p) { $d = (string) ((($p['request_date'] ?? '') ?: (($p['approval_date'] ?? '') ?: ($p['payment_date'] ?? ''))) ?: substr((string) ($p['created_at'] ?? ''), 0, 10)); if ($d > $last) $last = $d; }
        $days = []; $net = 0;
        foreach ($trades as $t) { if (($t['account_id'] ?? '') !== $id) continue; $n = GameEngine::net($t); $net += $n; $d = (string) ($t['date'] ?? ''); if ($last === '' || $d > $last) $days[$d] = ($days[$d] ?? 0) + $n; }
        $paid = 0; foreach ($pays as $p) if (($p['account_id'] ?? '') === $id && ($p['status'] ?? '') === 'paid') $paid += (int) ($p['amount_c'] ?? 0);
        $adj = 0; foreach ((array) ($a['adjustments'] ?? []) as $x) $adj += (int) ($x['amount_c'] ?? 0);
        $bal = $start + $net - $paid + $adj; $cycle = array_sum($days);
        $c = [];   // [ok, frac]
        $clamp = fn($v) => max(0, min(1, $v));
        if (!empty($r['payout_win_days'])) { $m = (int) ($r['payout_win_min_c'] ?? 0); $n = count(array_filter($days, fn($v) => $m ? $v >= $m : $v > 0)); $c[] = [$n >= (int) $r['payout_win_days'], min(1, $n / (int) $r['payout_win_days'])]; }
        if (!empty($r['payout_trade_days'])) { $n = count($days); $c[] = [$n >= (int) $r['payout_trade_days'], min(1, $n / (int) $r['payout_trade_days'])]; }
        if (!empty($r['payout_cycle_pos']) && $last !== '') $c[] = [$cycle > 0, $cycle > 0 ? 1 : 0];
        if (!empty($r['payout_first_min_c']) && $last === '') $c[] = [$cycle >= (int) $r['payout_first_min_c'], $clamp($cycle / (int) $r['payout_first_min_c'])];
        if (!empty($r['payout_cycle_min_c']) && $last !== '') $c[] = [$cycle >= (int) $r['payout_cycle_min_c'], $clamp($cycle / (int) $r['payout_cycle_min_c'])];
        if (!empty($r['consistency_pct']) && empty($r['target_c'])) { $cp = self::consPct(array_values($days), $r['consistency_base'] ?? null); $okc = $cp !== null && $cp <= (float) $r['consistency_pct']; $c[] = [$okc, $okc ? 1 : 0]; }
        $min = (int) ($r['payout_min_c'] ?? 0); $mb = (int) ($r['payout_min_bal_c'] ?? 0);
        if ($mb) $c[] = [$bal >= $mb + $min, $clamp(($bal - $start) / max(1, $mb + $min - $start))];
        $avail = $mb ? $bal - $mb : $bal - $start;
        if (!empty($r['payout_max_pct'])) $avail = min($avail, (int) floor(($bal - $start) * (float) $r['payout_max_pct'] / 100));
        $lad = is_array($r['payout_ladder_c'] ?? null) && $r['payout_ladder_c'] ? array_values($r['payout_ladder_c']) : null;
        $cap = $lad ? $lad[min(count($mine), count($lad) - 1)] : ($r['payout_max_c'] ?? null);
        if ($cap) $avail = min($avail, (int) $cap);
        $avail = max(0, $avail);
        $c[] = [$avail >= max(1, $min), $min ? $clamp($avail / $min) : ($avail > 0 ? 1 : 0)];
        if (!empty($r['payout_max_n'])) { $okn = count($mine) < (int) $r['payout_max_n']; $c[] = [$okn, $okn ? 1 : 0]; }
        $ready = !in_array(false, array_column($c, 0), true);
        return [$ready, $ready ? 100 : min(99, (int) round(min(array_column($c, 1)) * 100))];
    }

    /**
     * « Prêt pour le payout » : funded accounts with payout rules → payoutStatus (the app's rules); evaluations with a target →
     * the weakest of profit progress, trading days and consistency. Returned as a percentage only.
     * @return array{0: bool, 1: int} [configured, best readiness 0-100]
     */
    public static function payoutReadiness(string $uid): array
    {
        $cfg = false; $best = 0;
        $trades = GameEngine::docs($uid, 'trades');
        $paid = GameEngine::docs($uid, 'payouts');
        foreach (GameEngine::docs($uid, 'accounts') as $a) {
            if (($a['status'] ?? '') === 'archived' || ($a['result'] ?? '') === 'failed' || !empty($a['demo'])) continue;   // (« Mark as failed »: result failed)
            $r = (array) ($a['rules'] ?? []);
            $s = self::payoutStatus($a, $trades, $paid);
            if ($s !== null) { $cfg = true; $best = max($best, $s[1]); continue; }
            $goal = (int) ($r['target_c'] ?? 0);
            if ($goal <= 0) continue;
            $cfg = true;
            $net = 0; $byDay = [];
            foreach ($trades as $t) if (($t['account_id'] ?? '') === $a['id']) { $n = GameEngine::net($t); $net += $n; $d = (string) ($t['date'] ?? ''); $byDay[$d] = ($byDay[$d] ?? 0) + $n; }
            foreach ($paid as $x) if (($x['account_id'] ?? '') === $a['id'] && ($x['status'] ?? '') === 'paid') $net -= (int) ($x['amount_c'] ?? 0);
            $parts = [max(0, min(1, $net / $goal))];
            if (!empty($r['min_days'])) $parts[] = min(1, count($byDay) / (int) $r['min_days']);
            if (!empty($r['consistency_pct']) && $net > 0 && $byDay && ($cp = self::consPct(array_values($byDay), $r['consistency_base'] ?? null)) !== null) { $parts[] = $cp <= (int) $r['consistency_pct'] ? 1 : max(0, (int) $r['consistency_pct'] / $cp); }
            $best = max($best, (int) floor(min($parts) * 100));
        }
        return [$cfg, $best];
    }

    private static function personal(string $uid): bool
    {
        $firms = GameEngine::docs($uid, 'firms');
        foreach (GameEngine::docs($uid, 'accounts') as $a) {
            $f = $firms[$a['firm_id'] ?? ''] ?? null;
            if ($f && stripos((string) ($f['name'] ?? ''), 'personal') === false && stripos((string) ($f['name'] ?? ''), 'perso') === false) return false;
        }
        return true;
    }

    /** chapters in display order (goal « first payout » brings chapter 4 before 3) */
    public static function chapters(string $uid): array
    {
        $p = GameEngine::profile($uid, false);
        $map = GAME_MAP;
        if (self::personal($uid)) $map[4] = GAME_MAP_C4_PERSONAL;
        $order = ($p['goal'] ?? '') === 'payout' ? [1, 2, 4, 3, 5] : [1, 2, 3, 4, 5];
        $out = []; foreach ($order as $i => $c) $out[] = ['n' => $c, 'pos' => $i + 1, 'nodes' => $map[$c]];
        return $out;
    }

    /* ───────────── map evaluation ───────────── */

    public static function evaluateMap(string $uid, bool $quiet = false): array
    {
        self::schema();
        $m = self::metrics($uid);
        $plan = self::plan($uid);
        $done = [];
        foreach (self::q('SELECT node_id, completed_at FROM user_map_nodes WHERE user_id = ?', [$uid]) as $r) $done[$r['node_id']] = $r['completed_at'];
        $newNodes = [];
        foreach (self::chapters($uid) as $ch) {
            $locked = $plan === 'free' && $ch['pos'] > GAME_CHAPTER_FREE;
            $all = true;
            foreach ($ch['nodes'] as $id => [$target, $xp, $metric]) {
                $v = (int) ($m[$metric] ?? 0);
                $complete = !$locked && $v >= $target;
                if (isset($done[$id]) && $done[$id]) { continue; }
                if (!$complete) $all = false;
                $at = $complete ? GameEngine::ts() : null;
                if (array_key_exists($id, $done)) self::q('UPDATE user_map_nodes SET progress = ?, target = ?, completed_at = ? WHERE user_id = ? AND node_id = ?', [min($v, $target), $target, $at, $uid, $id]);
                else self::q('INSERT INTO user_map_nodes (user_id, node_id, progress, target, completed_at) VALUES (?, ?, ?, ?, ?)', [$uid, $id, min($v, $target), $target, $at]);
                if ($complete) {
                    $done[$id] = $at;
                    if (GameEngine::awardXp($uid, "map:$id", $xp)) { $newNodes[] = $id; GameEngine::track($uid, 'map_node_completed', ['node' => $id]); }
                }
            }
            if ($all && !$locked && GameEngine::awardXp($uid, 'chapter:' . $ch['n'], GAME_CHAPTER_XP)) {
                GameEngine::track($uid, 'chapter_completed', ['chapter' => $ch['n']]);
                if (!$quiet) GameEngine::celebrate($uid, 'chapter', ['chapter' => $ch['n'], 'pos' => $ch['pos'], 'xp' => GAME_CHAPTER_XP]);
            }
        }
        if ($newNodes && !$quiet) GameEngine::celebrate($uid, 'node', ['nodes' => $newNodes]);
        if (class_exists('GameWrapped', false) && !$quiet) { try { GameWrapped::payoutCheck($uid); } catch (Throwable $e) { /* never blocks */ } }
        return $newNodes;
    }

    /** first look at the map: what the history already completed, paid quietly, one message. Idempotent. */
    public static function backfillMap(string $uid): void
    {
        $p = GameEngine::profile($uid, false);
        $o = GameEngine::onboarding($p);
        if (!empty($o['map_init'])) return;
        $before = (int) $p['xp_total'];
        $nodes = self::evaluateMap($uid, true);
        $o['map_init'] = true;
        self::q('UPDATE user_game_profile SET onboarding_json = ? WHERE user_id = ?', [json_encode($o), $uid]);
        if ($nodes) GameEngine::celebrate($uid, 'map_backfill', ['nodes' => count($nodes), 'xp' => (int) GameEngine::profile($uid, false)['xp_total'] - $before]);
    }

    public static function mapState(string $uid): array
    {
        $plan = self::plan($uid);
        $m = self::metrics($uid);
        $rows = [];
        foreach (self::q('SELECT node_id, progress, target, completed_at FROM user_map_nodes WHERE user_id = ?', [$uid]) as $r) $rows[$r['node_id']] = $r;
        $chapters = []; $next = null;
        foreach (self::chapters($uid) as $ch) {
            $locked = $plan === 'free' && $ch['pos'] > GAME_CHAPTER_FREE;
            $nodes = [];
            foreach ($ch['nodes'] as $id => [$target, $xp, $metric]) {
                $r = $rows[$id] ?? null;
                $done = $r && $r['completed_at'];
                $v = $done ? $target : min($target, (int) ($m[$metric] ?? 0));
                $soon = in_array($metric, GAME_MAP_SOON, true) && !$done;
                $node = ['id' => $id, 'progress' => $v, 'target' => $target, 'xp' => $xp, 'done' => (bool) $done, 'at' => $done ? (int) $r['completed_at'] : null, 'soon' => $soon, 'metric' => $metric];
                if (!$done && !$soon && !$locked && $next === null) { $next = $node + ['chapter' => $ch['n'], 'pos' => $ch['pos']]; }
                $nodes[] = $node;
            }
            $chapters[] = ['n' => $ch['n'], 'pos' => $ch['pos'], 'locked' => $locked, 'done' => !$locked && !array_filter($nodes, fn($x) => !$x['done']), 'nodes' => $nodes];
        }
        $cur = null; foreach ($chapters as $c) if (!$c['done']) { $cur = $c; break; }
        $cur ??= end($chapters);
        [$cfg, $ready] = self::payoutReadiness($uid);
        return ['chapters' => $chapters, 'next' => $next, 'current' => ['n' => $cur['n'], 'pos' => $cur['pos'], 'done' => count(array_filter($cur['nodes'], fn($x) => $x['done'])), 'total' => count($cur['nodes']), 'locked' => $cur['locked']],
                'payout' => ['configured' => $cfg, 'ready' => $ready], 'plan' => $plan];
    }

    /* ───────────── weekly missions ───────────── */

    public static function weekStart(?string $day = null): string { return GameEngine::monday($day ?? GameEngine::today()); }
    /** missions expire at the end of Friday's grace period (Saturday 23:59 ET) */
    public static function weekOpen(string $mon): bool { return GameEngine::ts() <= GameEngine::deadline(GameEngine::addDays($mon, 4)); }

    /** weaknesses of the last 2 weeks → weights (higher = more likely) */
    private static function weights(string $uid, string $mon): array
    {
        $from = GameEngine::addDays($mon, -14); $to = GameEngine::addDays($mon, -1);
        $days = self::q('SELECT * FROM game_days WHERE user_id = ? AND trading_day BETWEEN ? AND ?', [$uid, $from, $to])->fetchAll(PDO::FETCH_ASSOC);
        $n = max(1, count(array_filter($days, fn($d) => GameEngine::isMarketDay($d['trading_day']))));
        $plans = 0; $early = 0; $rev = 0; $trades = 0; $emo = 0; $shots = 0; $off = 0;
        foreach ($days as $d) {
            $plans += (int) ($d['ring_plan'] > 0); $rev += (int) $d['review_done'];
            if ($d['plan_at'] && (int) $d['plan_at'] < GameEngine::epochEt($d['trading_day'], '09:30')) $early++;
            foreach ((json_decode((string) $d['detail_json'], true)['trades'] ?? []) as $t) { $trades++; $emo += !empty($t['e']); $shots += !empty($t['s']); $off += !empty($t['v']); }
        }
        $T = max(1, $trades);
        return [
            'review_days' => 1 + 3 * (1 - $rev / $n), 'plan_days' => 1 + 3 * (1 - $plans / $n), 'plan_early_days' => 1 + 3 * (1 - $early / $n),
            'emotion_trades' => 1 + 3 * (1 - $emo / $T), 'emotion_days' => 1 + 2 * (1 - $emo / $T), 'screen_trades' => 1 + 3 * (1 - $shots / $T),
            'swept_days' => 2, 'clean_days' => 1 + 3 * ($off / $T), 'maxloss_days' => 1.5,
        ];
    }

    private static function pick(array $pool, array $w, array $exclude = []): ?string
    {
        $pool = array_values(array_filter($pool, fn($id) => !in_array($id, $exclude, true)));
        if (!$pool) return null;
        $tot = 0; foreach ($pool as $id) $tot += $w[GAME_MISSIONS[$id][2]] ?? 1;
        $r = mt_rand() / mt_getrandmax() * $tot;
        foreach ($pool as $id) { $r -= $w[GAME_MISSIONS[$id][2]] ?? 1; if ($r <= 0) return $id; }
        return end($pool);
    }

    /** 3 missions per week (easy, medium, hard); Free gets the easy one. Created once, Monday 00:00 ET or at first open. */
    public static function ensureMissions(string $uid, ?string $mon = null): array
    {
        self::schema();
        $mon ??= self::weekStart();
        $have = self::q('SELECT * FROM user_missions WHERE user_id = ? AND week_start = ? ORDER BY difficulty', [$uid, $mon])->fetchAll(PDO::FETCH_ASSOC);
        if ($have || !self::weekOpen($mon)) return $have;
        mt_srand(crc32($uid . $mon));   // same draw if two requests race
        $w = self::weights($uid, $mon);
        $picked = [];
        foreach ([1, 2, 3] as $diff) {
            $id = self::pick(array_keys(array_filter(GAME_MISSIONS, fn($m) => $m[0] === $diff)), $w, $picked);
            if (!$id) continue;
            $picked[] = $id;
            try { self::q('INSERT INTO user_missions (user_id, week_start, mission_id, difficulty, target) VALUES (?, ?, ?, ?, ?)', [$uid, $mon, $id, $diff, GAME_MISSIONS[$id][1]]); } catch (Throwable $e) { /* raced */ }
        }
        mt_srand();
        self::updateMissions($uid, $mon);
        return self::q('SELECT * FROM user_missions WHERE user_id = ? AND week_start = ? ORDER BY difficulty', [$uid, $mon])->fetchAll(PDO::FETCH_ASSOC);
    }

    /** progress of the week's missions from game_days (Mon-Fri) */
    public static function updateMissions(string $uid, string $mon): void
    {
        if (!self::weekOpen($mon)) return;
        $rows = self::q('SELECT * FROM user_missions WHERE user_id = ? AND week_start = ?', [$uid, $mon])->fetchAll(PDO::FETCH_ASSOC);
        if (!$rows) return;
        $days = self::q('SELECT * FROM game_days WHERE user_id = ? AND trading_day BETWEEN ? AND ?', [$uid, $mon, GameEngine::addDays($mon, 4)])->fetchAll(PDO::FETCH_ASSOC);
        $v = ['review_days' => 0, 'plan_days' => 0, 'plan_early_days' => 0, 'emotion_trades' => 0, 'screen_trades' => 0, 'swept_days' => 0, 'clean_days' => 0, 'emotion_days' => 0, 'maxloss_days' => 0];
        foreach ($days as $d) {
            $det = json_decode((string) $d['detail_json'], true) ?: []; $tr = $det['trades'] ?? [];
            $v['review_days'] += (int) $d['review_done'];
            $v['plan_days'] += (int) ((int) $d['ring_plan'] === 100);
            $v['plan_early_days'] += (int) ($d['plan_valid'] && $d['plan_at'] && (int) $d['ring_plan'] > 0 && (int) $d['plan_at'] < GameEngine::epochEt($d['trading_day'], '09:30'));
            foreach ($tr as $t) { $v['emotion_trades'] += !empty($t['e']); $v['screen_trades'] += !empty($t['s']); }
            $v['swept_days'] += (int) $d['is_swept'];
            $active = $tr || (int) $d['plan_valid'];
            $v['clean_days'] += (int) ($active && (int) $d['plan_valid'] && !array_filter($tr, fn($t) => !empty($t['v'])));
            $v['emotion_days'] += (int) ($tr && !array_filter($tr, fn($t) => empty($t['e'])));
            $v['maxloss_days'] += (int) ((int) $d['plan_valid'] && $d['plan_bias'] !== 'no_trade' && !array_filter($tr, fn($t) => in_array('over_max_loss', $t['v'] ?? [], true)));
        }
        $all = true;
        $limit = self::plan($uid) === 'free' ? 1 : 3;
        usort($rows, fn($a, $b) => (int) $a['difficulty'] <=> (int) $b['difficulty']);
        foreach ($rows as $i => $r) {
            $p = min((int) $r['target'], $v[GAME_MISSIONS[$r['mission_id']][2] ?? ''] ?? 0);
            if ($i >= $limit) { $all = false; if ((int) $r['progress'] !== $p) self::q('UPDATE user_missions SET progress = ? WHERE id = ?', [$p, $r['id']]); continue; }   // locked: visible, never paid
            $done = $p >= (int) $r['target'];
            if (!$done) $all = false;
            if ((int) $r['progress'] !== $p || ($done && !$r['completed_at'])) {
                self::q('UPDATE user_missions SET progress = ?, completed_at = COALESCE(completed_at, ?) WHERE id = ?', [$p, $done ? GameEngine::ts() : null, $r['id']]);
            }
            if ($done && GameEngine::awardXp($uid, "mission:$mon:" . $r['mission_id'], GAME_MISSION_XP[(int) $r['difficulty']] ?? 50)) {
                GameEngine::celebrate($uid, 'mission', ['id' => $r['mission_id'], 'xp' => GAME_MISSION_XP[(int) $r['difficulty']] ?? 50]);
                GameEngine::track($uid, 'mission_completed', ['id' => $r['mission_id'], 'difficulty' => (int) $r['difficulty']]);
            }
        }
        // the three missions of the week → one chest key (the chest arrives in step 2)
        if ($all && count($rows) === 3 && GameEngine::awardXp($uid, "missions_all:$mon", 0)) {
            self::q('INSERT INTO user_rewards (user_id, source, reward_type, reward_value, created_at) VALUES (?, ?, ?, ?, ?)', [$uid, 'mission', 'key', $mon, GameEngine::ts()]);
            GameEngine::celebrate($uid, 'key', ['week' => $mon]);
        }
    }

    /** Elite: swap one unfinished mission once a week (same difficulty) */
    public static function reroll(string $uid, int $missionId): bool
    {
        if (self::plan($uid) !== 'elite') return false;
        $mon = self::weekStart();
        $r = self::q('SELECT * FROM user_missions WHERE id = ? AND user_id = ? AND week_start = ?', [$missionId, $uid, $mon])->fetch(PDO::FETCH_ASSOC);
        if (!$r || $r['completed_at'] || self::q('SELECT 1 FROM user_missions WHERE user_id = ? AND week_start = ? AND rerolled = 1', [$uid, $mon])->fetchColumn()) return false;
        $taken = self::q('SELECT mission_id FROM user_missions WHERE user_id = ? AND week_start = ?', [$uid, $mon])->fetchAll(PDO::FETCH_COLUMN);
        $id = self::pick(array_keys(array_filter(GAME_MISSIONS, fn($m) => $m[0] === (int) $r['difficulty'])), self::weights($uid, $mon), $taken);
        if (!$id) return false;
        self::q('UPDATE user_missions SET mission_id = ?, target = ?, progress = 0, rerolled = 1 WHERE id = ?', [$id, GAME_MISSIONS[$id][1], $r['id']]);
        self::updateMissions($uid, $mon);
        GameEngine::track($uid, 'mission_rerolled', ['mission' => $id]);   // Admin › Metrics: the game's use (brief 02 part 11)
        return true;
    }

    public static function missionsState(string $uid): array
    {
        $mon = self::weekStart();
        $rows = self::ensureMissions($uid, $mon);
        $plan = self::plan($uid);
        $limit = $plan === 'free' ? 1 : 3;
        $rerolled = (bool) array_filter($rows, fn($r) => (int) $r['rerolled'] === 1);
        return ['week' => $mon, 'ends' => GameEngine::deadline(GameEngine::addDays($mon, 4)), 'plan' => $plan, 'can_reroll' => $plan === 'elite' && !$rerolled,
                'keys' => (int) self::q("SELECT COUNT(*) FROM user_rewards WHERE user_id = ? AND reward_type = 'key' AND used_at IS NULL", [$uid])->fetchColumn(),
                'missions' => array_map(fn($r, $i) => ['id' => (int) $r['id'], 'mission' => $r['mission_id'], 'difficulty' => (int) $r['difficulty'], 'progress' => (int) $r['progress'],
                    'target' => (int) $r['target'], 'done' => (bool) $r['completed_at'], 'xp' => GAME_MISSION_XP[(int) $r['difficulty']] ?? 50, 'locked' => $i >= $limit], $rows, array_keys($rows))];
    }

    /* ───────────── hooks ───────────── */

    /** called by GameEngine::recomputeDay after every save */
    public static function onDay(string $uid, string $day): void
    {
        self::schema();
        $mon = self::weekStart($day);
        self::updateMissions($uid, $mon);
        $o = GameEngine::onboarding(GameEngine::profile($uid, false));
        if (empty($o['map_init'])) self::backfillMap($uid); else self::evaluateMap($uid);
        if (class_exists('GameWow', false)) { try { GameWow::check($uid); } catch (Throwable $e) { error_log('[Sweep wow] ' . $e->getMessage()); } }
    }
}


/* the map also moves when accounts, rules or payouts change (not only on trades and journal pages) */
if (class_exists('Events', false)) {
    foreach (['account.created', 'account.updated', 'payout.recorded', 'payout.updated', 'payout.paid'] as $ev) {
        Events::on($ev, function (array $p): void {
            $uid = (string) ($p['uid'] ?? '');
            if ($uid === '' || !GameEngine::profile($uid, false)) return;
            GameEngine::forget($uid);
            GameV2::schema();
            GameV2::evaluateMap($uid);
        });
    }
}
