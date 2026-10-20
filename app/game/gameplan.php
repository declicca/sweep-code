<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli' && realpath((string) ($_SERVER['SCRIPT_FILENAME'] ?? '')) === realpath(__FILE__)) { http_response_code(404); exit; }
/**
 * Sweep — the 90-day gameplan (brief « Parcours de 90 jours », 20 Oct.): Mateo's three « Learning Edition » PDFs as a game.
 *
 * - 90 missions over 12 weeks, from a Monday: mission N is dated start + N − 1; a late one can still be done, never a penalty.
 * - Some missions Sweep checks on its own (step 4, 'a' below); the others the trader ticks, facing its « Done when ».
 * - Each mission pays its minutes in XP once (xp_events key gp:N); a gate (days 30, 60, 90) decides: on to the next
 *   month, or Weeks 3 and 4 again (the plan moves, nothing is lost).
 * - Pro and Elite (the trial too); Free sees it locked. Billing not live yet: everyone, like the rest of the app.
 * The texts live in the app (src/gameplan.js, built from the site's website/src/pages21.py); here only what the server needs.
 */

/** N => [XP (the mission's minutes), what Sweep checks itself ('' = the trader ticks it), gate of month (0 = none)] */
const GP_MISSIONS = [1=>[20,'account',0],2=>[30,'trade',0],3=>[20,'',0],4=>[20,'',0],5=>[25,'weekly',0],6=>[20,'',0],7=>[15,'',0],8=>[20,'',0],9=>[20,'',0],10=>[30,'',0],11=>[30,'',0],12=>[30,'weekly',0],13=>[25,'',0],14=>[15,'',0],15=>[30,'',0],16=>[30,'',0],17=>[30,'',0],18=>[30,'',0],19=>[30,'',0],20=>[25,'',0],21=>[10,'',0],22=>[30,'journal',0],23=>[30,'zero',0],24=>[30,'zero',0],25=>[30,'zero',0],26=>[30,'weekly',0],27=>[25,'',0],28=>[20,'',0],29=>[30,'journal',0],30=>[20,'',1],31=>[20,'',0],32=>[30,'',0],33=>[30,'weekly',0],34=>[25,'',0],35=>[10,'',0],36=>[30,'',0],37=>[30,'',0],38=>[30,'',0],39=>[30,'',0],40=>[30,'weekly',0],41=>[30,'',0],42=>[15,'',0],43=>[30,'',0],44=>[30,'journal',0],45=>[30,'journal',0],46=>[30,'zero',0],47=>[30,'weekly',0],48=>[25,'',0],49=>[15,'',0],50=>[30,'journal',0],51=>[30,'journal',0],52=>[20,'limits',0],53=>[30,'',0],54=>[30,'weekly',0],55=>[25,'',0],56=>[15,'',0],57=>[30,'journal',0],58=>[30,'journal',0],59=>[25,'',0],60=>[20,'',2],61=>[30,'',0],62=>[25,'',0],63=>[20,'',0],64=>[30,'',0],65=>[30,'',0],66=>[30,'',0],67=>[30,'journal',0],68=>[30,'',0],69=>[25,'',0],70=>[15,'',0],71=>[30,'journal',0],72=>[30,'',0],73=>[30,'journal',0],74=>[30,'zero',0],75=>[30,'weekly',0],76=>[25,'',0],77=>[20,'',0],78=>[30,'journal',0],79=>[30,'',0],80=>[30,'journal',0],81=>[30,'zero',0],82=>[30,'weekly',0],83=>[30,'',0],84=>[25,'',0],85=>[30,'journal',0],86=>[30,'journal',0],87=>[30,'journal',0],88=>[30,'zero',0],89=>[30,'',0],90=>[20,'',3]];
const GP_GATE_XP = 150;

final class GameGameplan
{
    private static function q(string $sql, array $a = []): PDOStatement { return GameEngine::q($sql, $a); }

    public static function schema(): void
    {
        static $done = false; if ($done) return; $done = true;
        $my = GameEngine::pdo()->getAttribute(PDO::ATTR_DRIVER_NAME) === 'mysql';
        GameEngine::pdo()->exec('CREATE TABLE IF NOT EXISTS game_gameplan (user_id ' . ($my ? 'VARCHAR(120)' : 'TEXT') . ' NOT NULL PRIMARY KEY, start_day CHAR(10) NOT NULL, track CHAR(1) NOT NULL, done_json TEXT NULL, gates_json TEXT NULL, created_at INTEGER NOT NULL, updated_at INTEGER NOT NULL)');
    }

    /** Pro and Elite, the trial too; Free not. Billing off or not live for this trader: everyone (as the rest of the app). */
    public static function access(string $uid): bool
    {
        try {
            if (!function_exists('billing_on') || !billing_on() || !function_exists('sb_can')) return true;
            if (function_exists('sb_live') && !sb_live($uid)) return true;
            return sb_can(GameEngine::pdo(), $uid, 'gameplan');
        } catch (Throwable $e) { return true; }   // billing unavailable: never lock a trader out of his plan
    }

    /** The next Monday (today if it is one), the trading day of New York as the rest of the game. */
    public static function nextMonday(string $today): string
    {
        $dow = (int) (new DateTimeImmutable($today . ' 12:00'))->format('N');
        return $dow === 1 ? $today : GameEngine::addDays($today, 8 - $dow);
    }

    private static function row(string $uid): ?array
    {
        self::schema();
        $r = self::q('SELECT * FROM game_gameplan WHERE user_id = ?', [$uid])->fetch(PDO::FETCH_ASSOC);
        return $r ?: null;
    }

    /** Day N of the plan for a date (1 = the start), 0 before it. */
    public static function dayOf(string $start, string $day): int
    {
        if ($day < $start) return 0;
        return (int) (new DateTimeImmutable($start . ' 12:00'))->diff(new DateTimeImmutable($day . ' 12:00'))->days + 1;
    }

    /** What Sweep can see on its own (read only: nothing of the trader's data is changed). $date = the mission's date. */
    private static function met(string $uid, string $kind, string $date): bool
    {
        $live = fn($a) => !in_array((string) ($a['status'] ?? 'active'), ['archived', 'closed'], true);
        switch ($kind) {
            case 'account': foreach (GameEngine::docs($uid, 'accounts') as $a) if ($live($a)) return true; return false;
            case 'limits':
                foreach (GameEngine::docs($uid, 'accounts') as $a) { $r = (array) ($a['rules'] ?? []); if ($live($a) && ((int) ($r['dll_c'] ?? 0) > 0 || (int) ($r['dd_c'] ?? 0) > 0)) return true; }
                return false;
            case 'trade':   // a trade journaled with its stop and its target, on the mission's day or after
                foreach (GameEngine::docs($uid, 'trades') as $t) { $d = GameEngine::tradeDay($t); if ($d !== null && $d >= $date && GameEngine::hasStop($t) && ($t['target'] ?? '') !== '' && $t['target'] !== null) return true; }
                return false;
            case 'journal': return (bool) self::q('SELECT review_done FROM game_days WHERE user_id = ? AND trading_day = ?', [$uid, $date])->fetchColumn();
            case 'zero':    // the day reviewed and kept to its rules (the game's guardrail of that day)
                return self::met($uid, 'journal', $date) && (bool) self::q('SELECT 1 FROM xp_events WHERE user_id = ? AND event_key = ?', [$uid, 'guardrail:' . $date])->fetchColumn();
            case 'weekly':
                try { return (bool) self::q('SELECT 1 FROM weekly_reviews WHERE user_id = ? AND week_start = ?', [$uid, GameEngine::monday($date)])->fetchColumn(); }
                catch (Throwable $e) { return false; }
        }
        return false;
    }

    /** Sweep ticks the open missions it can measure (and the first account, even before the Monday). */
    private static function autoCheck(string $uid, array $r): void
    {
        $done = json_decode((string) $r['done_json'], true) ?: []; $gates = json_decode((string) $r['gates_json'], true) ?: [];
        $to = max(1, self::openTo(self::dayOf($r['start_day'], GameEngine::today()), $gates));
        for ($n = 1; $n <= $to; $n++) {
            $kind = GP_MISSIONS[$n][1] ?? ''; if ($kind === '' || isset($done[(string) $n])) continue;
            if (self::met($uid, $kind, GameEngine::addDays($r['start_day'], $n - 1))) self::done($uid, $n, 'sweep');
        }
    }

    public static function state(string $uid, bool $check = true): array
    {
        $today = GameEngine::today();
        if ($check && self::access($uid) && ($r0 = self::row($uid))) { try { self::autoCheck($uid, $r0); } catch (Throwable $e) { error_log('[Sweep gameplan] ' . $e->getMessage()); } }
        $out = ['access' => self::access($uid), 'today' => $today, 'started' => false, 'next_monday' => self::nextMonday($today)];
        $r = self::row($uid); if (!$r) return $out;
        $done = json_decode((string) $r['done_json'], true) ?: []; $gates = json_decode((string) $r['gates_json'], true) ?: [];
        $day = self::dayOf($r['start_day'], $today);
        return array_merge($out, ['started' => true, 'start' => $r['start_day'], 'track' => $r['track'], 'day' => min($day, 999),
            'done' => (object) $done, 'gates' => (object) $gates, 'open_to' => self::openTo($day, $gates)]);
    }

    /** The last mission that can be done today: its date reached, and not past a gate that is not passed. */
    private static function openTo(int $day, array $gates): int
    {
        $n = max(0, min(90, $day));
        foreach ([30 => '1', 60 => '2'] as $g => $m) if ($n > $g && ($gates[$m] ?? '') !== 'pass') $n = $g;
        return $n;
    }

    public static function start(string $uid, array $b): array
    {
        if (!self::access($uid)) return ['error' => 'locked'];
        $track = ($b['track'] ?? 'A') === 'B' ? 'B' : 'A';
        $start = self::nextMonday(GameEngine::today());
        if (self::row($uid)) self::q('UPDATE game_gameplan SET start_day = ?, track = ?, done_json = NULL, gates_json = NULL, updated_at = ? WHERE user_id = ?', [$start, $track, time(), $uid]);
        else self::q('INSERT INTO game_gameplan (user_id, start_day, track, done_json, gates_json, created_at, updated_at) VALUES (?, ?, ?, NULL, NULL, ?, ?)', [$uid, $start, $track, time(), time()]);
        GameEngine::track($uid, 'gameplan_start', ['track' => $track]);
        return self::state($uid);
    }

    public static function stop(string $uid): array
    {
        self::schema(); self::q('DELETE FROM game_gameplan WHERE user_id = ?', [$uid]);
        GameEngine::track($uid, 'gameplan_stop');
        return self::state($uid);
    }

    /** A mission ticked (by the trader, or by Sweep with $by = 'sweep'): its XP once. */
    public static function done(string $uid, int $n, string $by = 'trader'): array
    {
        if (!self::access($uid)) return ['error' => 'locked'];
        $r = self::row($uid); if (!$r) return ['error' => 'not_started'];
        if (!isset(GP_MISSIONS[$n])) return ['error' => 'bad_mission'];
        $gates = json_decode((string) $r['gates_json'], true) ?: [];
        $early = $n === 1 && $by === 'sweep';   // the first account, often added before the Monday
        if (!$early && $n > self::openTo(self::dayOf($r['start_day'], GameEngine::today()), $gates)) return ['error' => 'not_open'];
        if (GP_MISSIONS[$n][2]) return ['error' => 'gate'];   // a gate is decided, not ticked
        $done = json_decode((string) $r['done_json'], true) ?: [];
        if (isset($done[(string) $n])) return self::state($uid, $by !== 'sweep');
        $done[(string) $n] = ['at' => time(), 'by' => $by === 'sweep' ? 'sweep' : 'trader'];
        self::q('UPDATE game_gameplan SET done_json = ?, updated_at = ? WHERE user_id = ?', [json_encode($done), time(), $uid]);
        $xp = GP_MISSIONS[$n][0];
        if (GameEngine::awardXp($uid, 'gp:' . $n, $xp, ['by' => $by]) && $by === 'sweep') GameEngine::celebrate($uid, 'gameplan', ['n' => $n, 'xp' => $xp]);   // ticked by the trader: the app shows it there and then
        return $by === 'sweep' ? [] : self::state($uid);
    }

    /** A gate: 'pass' opens the next month; 'repeat' gives Weeks 3 and 4 of that month again, from the next Monday. */
    public static function gate(string $uid, int $m, string $choice): array
    {
        if (!self::access($uid)) return ['error' => 'locked'];
        $r = self::row($uid); if (!$r) return ['error' => 'not_started'];
        if ($m < 1 || $m > 3 || !in_array($choice, ['pass', 'repeat'], true)) return ['error' => 'bad_gate'];
        $g = $m * 30;
        if (self::dayOf($r['start_day'], GameEngine::today()) < $g) return ['error' => 'not_open'];
        $gates = json_decode((string) $r['gates_json'], true) ?: []; $done = json_decode((string) $r['done_json'], true) ?: [];
        if ($choice === 'pass') {
            $gates[(string) $m] = 'pass'; $done[(string) $g] = ['at' => time(), 'by' => 'trader'];
            GameEngine::awardXp($uid, 'gp:gate' . $m, GP_GATE_XP);   // the gate sheet celebrates it
            self::q('UPDATE game_gameplan SET done_json = ?, gates_json = ?, updated_at = ? WHERE user_id = ?', [json_encode($done), json_encode($gates), time(), $uid]);
        } else {
            // Weeks 3 and 4 of month m again: their first day (15 of the month) on the next Monday, their missions open again
            $first = $g - 15;   // day 15, 45 or 75
            $start = GameEngine::addDays(self::nextMonday(GameEngine::today()), -($first - 1));
            foreach (array_keys($done) as $k) if ((int) $k >= $first) unset($done[$k]);
            unset($gates[(string) $m]);
            self::q('UPDATE game_gameplan SET start_day = ?, done_json = ?, gates_json = ?, updated_at = ? WHERE user_id = ?', [$start, json_encode($done), json_encode($gates), time(), $uid]);
        }
        GameEngine::track($uid, 'gameplan_gate', ['month' => $m, 'choice' => $choice]);
        return self::state($uid);
    }
}

function gameplan_route(string $route, string $method, string $uid): bool
{
    if ($route === 'api/game/gameplan' && $method === 'GET') { json_out(200, GameGameplan::state($uid)); }
    if ($method !== 'POST' || strpos($route, 'api/game/gameplan/') !== 0) return false;
    $b = body_json(1024); $a = substr($route, strlen('api/game/gameplan/'));
    $r = $a === 'start' ? GameGameplan::start($uid, $b) : ($a === 'stop' ? GameGameplan::stop($uid)
       : ($a === 'done' ? GameGameplan::done($uid, (int) ($b['n'] ?? 0)) : ($a === 'gate' ? GameGameplan::gate($uid, (int) ($b['month'] ?? 0), (string) ($b['choice'] ?? '')) : ['error' => 'not_found'])));
    json_out(isset($r['error']) ? ($r['error'] === 'locked' ? 402 : ($r['error'] === 'not_found' ? 404 : 400)) : 200, $r);
    return true;
}
