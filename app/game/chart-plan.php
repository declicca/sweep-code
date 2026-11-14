<?php
declare(strict_types=1);
/**
 * Sweep — Plan Sync, step 1 (BRIEF_PLAN_SYNC, 13 Nov. 2026): the day's plan made readable by a machine, kept in the day's journal
 * document (journals/{day}.chart = { zones, rules, updated_at }), next to the pre-market sheet but outside it: the sheet locks
 * at the session, the zones stay editable all day. The same model as SweepPlanChart in src/game.js; the add-ons read it (step 2).
 *  - a zone: one price (« level ») or a high and a low (« zone »), on an instrument root (MNQ is NQ, contract month ignored),
 *    with a label, a role, an optional bias and note, and its approach distance in ticks (filled by the app from its one table);
 *  - a rule: one trigger (approach, enter, close above / below, sweep, a New York time) and one action (an alert with the
 *    trader's message, a reminder of the plan, a reminder of a limit Sweep already knows). No nesting, no code.
 * Nothing here reaches an order: Plan Sync reminds, it never trades.
 */
final class ChartPlan
{
    public const MAX_ZONES = 30;
    public const MAX_RULES = 30;
    public const TYPES = ['level', 'zone'];
    public const ROLES = ['support', 'resistance', 'target', 'invalidation', 'neutral'];
    public const BIASES = ['long', 'short'];
    public const TRIGGERS = ['approach', 'enter', 'close_above', 'close_below', 'sweep', 'time'];
    public const TFS = ['1m', '5m', '15m'];
    public const ACTIONS = ['alert', 'plan', 'limit'];
    /** a micro contract reads the levels of its mini (same price) */
    public const MICRO = ['MNQ' => 'NQ', 'MES' => 'ES', 'MYM' => 'YM', 'M2K' => 'RTY', 'MCL' => 'CL', 'MGC' => 'GC', 'SIL' => 'SI', 'M6E' => '6E'];

    /** the tick of each root (the app's INSTR, src/app.js) and its default approach distance in ticks (PC_ROOTS, src/game.js) */
    public const TICKS = ['NQ' => 0.25, 'ES' => 0.25, 'YM' => 1, 'RTY' => 0.1, 'CL' => 0.01, 'GC' => 0.1, 'SI' => 0.005, '6E' => 0.0001, 'NG' => 0.001,
        'HG' => 0.0005, 'ZN' => 0.015625, 'ZB' => 0.03125, 'MBT' => 5, 'MET' => 0.5];
    public const PROX = ['NQ' => 40, 'ES' => 8, 'YM' => 20, 'RTY' => 20, 'CL' => 10, 'GC' => 20, 'SI' => 10, '6E' => 20, 'NG' => 10, 'HG' => 20, 'ZN' => 8, 'ZB' => 8, 'MBT' => 20, 'MET' => 20];

    /** the instrument's root: NQZ6 → NQ, MNQ → NQ, mnq h27 → NQ */
    public static function root(string $s): string
    {
        $s = strtoupper(preg_replace('/[^A-Za-z0-9]/', '', $s) ?? '');
        if (strlen($s) > 3) $s = preg_replace('/[FGHJKMNQUVXZ]\d{1,2}$/', '', $s) ?? $s;
        $s = substr($s, 0, 8);
        return self::MICRO[$s] ?? $s;
    }

    private static function txt($v, int $max): string
    {
        $s = trim(preg_replace('/\s+/u', ' ', strip_tags(is_scalar($v) ? (string) $v : '')) ?? '');
        return mb_substr($s, 0, $max);
    }
    private static function num($v): ?float
    {
        if (is_string($v)) $v = str_replace([' ', "\u{00a0}", ','], ['', '', '.'], $v);
        return is_numeric($v) && is_finite((float) $v) && (float) $v > 0 ? round((float) $v, 6) : null;
    }
    private static function id($v): ?string { return is_string($v) && preg_match('/^[A-Za-z0-9_-]{1,24}$/', $v) ? $v : null; }

    /** known fields only, right types; a zone without a price or an instrument, or a rule without its zone, is left out */
    public static function normalize($c): ?array
    {
        if (!is_array($c)) return null;
        $zones = []; $seen = [];
        foreach (array_slice(is_array($c['zones'] ?? null) ? array_values($c['zones']) : [], 0, self::MAX_ZONES) as $i => $z) {
            if (!is_array($z)) continue;
            $inst = self::root((string) ($z['instrument'] ?? ''));
            if ($inst === '') continue;
            $type = in_array($z['type'] ?? '', self::TYPES, true) ? $z['type'] : 'level';
            $id = self::id($z['id'] ?? null) ?? ('z' . ($i + 1));
            if (isset($seen[$id])) $id .= '_' . ($i + 1);
            $o = ['id' => $id, 'instrument' => $inst, 'type' => $type];
            if ($type === 'level') {
                $p = self::num($z['price'] ?? null); if ($p === null) continue;
                $o['price'] = $p;
            } else {
                $h = self::num($z['high'] ?? null); $l = self::num($z['low'] ?? null);
                if ($h === null || $l === null || $h === $l) continue;
                if ($h < $l) [$h, $l] = [$l, $h];
                $o['high'] = $h; $o['low'] = $l;
            }
            $o['label'] = self::txt($z['label'] ?? '', 40);
            $o['role'] = in_array($z['role'] ?? '', self::ROLES, true) ? $z['role'] : 'neutral';
            $o['bias'] = in_array($z['bias'] ?? null, self::BIASES, true) ? $z['bias'] : null;
            $o['note'] = self::txt($z['note'] ?? '', 200);
            $pt = $z['proximity_ticks'] ?? null;
            $o['proximity_ticks'] = is_numeric($pt) && (int) $pt >= 1 ? min(5000, (int) $pt) : null;
            $zones[] = $o; $seen[$id] = true;
        }
        $rules = []; $rseen = [];
        foreach (array_slice(is_array($c['rules'] ?? null) ? array_values($c['rules']) : [], 0, self::MAX_RULES) as $i => $r) {
            if (!is_array($r)) continue;
            $tr = $r['trigger'] ?? '';
            if (!in_array($tr, self::TRIGGERS, true)) continue;
            $id = self::id($r['id'] ?? null) ?? ('r' . ($i + 1));
            if (isset($rseen[$id])) $id .= '_' . ($i + 1);
            $o = ['id' => $id, 'trigger' => $tr];
            if ($tr === 'time') {
                $t = (string) ($r['time'] ?? '');
                if (!preg_match('/^([01]\d|2[0-3]):[0-5]\d$/', $t)) continue;
                $o['time'] = $t;
            } else {
                $zid = (string) ($r['zone'] ?? '');
                if (!isset($seen[$zid])) continue;   // its zone is gone: the rule goes with it
                $o['zone'] = $zid;
                if (in_array($tr, ['close_above', 'close_below', 'sweep'], true)) $o['tf'] = in_array($r['tf'] ?? '', self::TFS, true) ? $r['tf'] : '5m';
            }
            $o['action'] = in_array($r['action'] ?? '', self::ACTIONS, true) ? $r['action'] : 'alert';
            $o['message'] = self::txt($r['message'] ?? '', 200);
            $rules[] = $o; $rseen[$id] = true;
        }
        $u = $c['updated_at'] ?? null;
        return ['zones' => $zones, 'rules' => $rules, 'updated_at' => is_int($u) && $u > 0 ? $u : time()];
    }

    /**
     * Step 5: was the plan followed? Each trade of the day (copies once, already chosen by the caller) is « in » when its entry
     * price is in a zone of the plan on its instrument (MNQ reads NQ) — a zone between its low and high, a level within its
     * approach distance (its ticks × the instrument's tick) — and in the direction the plan gives there: the zone's own bias,
     * else the day's bias (bullish → long, bearish → short), else either way. Any other trade is « out ». A trade without an
     * entry price or a direction is not counted. null: the day has no zone, nothing to compare with.
     * Returns { n, in, trades: { id: { in, zone } } } (zone: the id of the zone it was in, or null).
     */
    public static function follow($chart, array $pre, array $trades): ?array
    {
        $c = self::normalize($chart);
        if (!$c || !$c['zones']) return null;
        $dayDir = ['bullish' => 'long', 'bearish' => 'short'][$pre['bias'] ?? ''] ?? null;
        $n = 0; $in = 0; $out = [];
        foreach ($trades as $t) {
            if (!is_array($t) || !empty($t['untracked'])) continue;
            $dir = strtolower((string) ($t['direction'] ?? '')); $px = self::num($t['entry'] ?? null);
            if (!in_array($dir, ['long', 'short'], true) || $px === null) continue;
            $root = self::root((string) (($t['instrument'] ?? '') ?: 'NQ'));
            $hit = null;
            foreach ($c['zones'] as $z) {
                if ($z['instrument'] !== $root) continue;
                $tk = self::TICKS[$root] ?? 0.25;
                $inZone = $z['type'] === 'zone'
                    ? $px >= $z['low'] - 1e-9 && $px <= $z['high'] + 1e-9
                    : abs($px - $z['price']) <= ($z['proximity_ticks'] ?? self::PROX[$root] ?? 20) * $tk + 1e-9;
                if (!$inZone) continue;
                $want = $z['bias'] ?? $dayDir;
                if ($want === null || $want === $dir) { $hit = $z['id']; break; }
            }
            $n++; if ($hit !== null) $in++;
            $out[(string) ($t['id'] ?? $n)] = ['in' => $hit !== null, 'zone' => $hit];
        }
        return ['n' => $n, 'in' => $in, 'trades' => $out];
    }

    /**
     * a journal document on its way in (PUT or batch), $prev the stored one: the day's chart plan normalized; never dropped by a
     * document that does not carry it (an older copy of the day); null removes it; no chart plan on a journal that is not a day.
     */
    public static function apply(array $doc, string $id, ?array $prev = null): array
    {
        if (!preg_match('/^\d{4}-\d{2}-\d{2}$/', $id)) { unset($doc['chart']); return $doc; }
        if (!array_key_exists('chart', $doc)) {
            if (is_array($prev['chart'] ?? null)) $doc['chart'] = $prev['chart'];
            return $doc;
        }
        $n = self::normalize($doc['chart']);
        if ($n === null || (!$n['zones'] && !$n['rules'])) unset($doc['chart']); else $doc['chart'] = $n;
        return $doc;
    }
}
