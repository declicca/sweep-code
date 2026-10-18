<?php
declare(strict_types=1);
/**
 * « Your edge » (brief edge T2, 17 Oct.): one profile of what works for the trader, used everywhere (the coach, Edge Reveal…).
 * Twin of SweepEdge.profile() in src/coach.js — same inputs, same steps, same order (tests/e2e_edge_parity.py locks them):
 *  - the real trades of the last 8 weeks (56 sessions back from the day), a copied trade once (the first saved);
 *  - the result of a trade: R when its risk is known (risk_c) on at least 80 % of them, else $ per contract;
 *  - a mean weighted ×2 on the last 4 weeks; conditions of 1 or 2 dimensions with 5 trades at least;
 *  - a winning condition: positive, and above the trader's mean by a quarter of their mean absolute result at least;
 *    scored gap × √n; 3 at most, never two on almost the same trades (80 % in common); 1 leak (the costliest);
 *  - level: lead (5), trend (10), confirmed (20 and positive on both halves of the 8 weeks);
 *    « new » (under 5 trades a week ago), « fading » (the last 4 weeks under half of the 4 before, 5 trades on each side).
 * Not financial advice: it describes the trader's past, nothing more.
 */
final class GameEdge
{
    public const DIMS = ['setup', 'slot', 'session', 'weekday', 'side', 'plan', 'emo', 'nth', 'after', 'inst'];

    private static function addDays(string $d, int $k): string { return (new DateTimeImmutable($d . ' 12:00:00', new DateTimeZone('UTC')))->modify(($k >= 0 ? '+' : '') . $k . ' days')->format('Y-m-d'); }
    private static function net(array $t): int { return (int) ($t['pnl_c'] ?? 0) - (int) ($t['fees_c'] ?? 0); }
    private static function low($s): string { return mb_strtolower(trim((string) $s)); }
    private static function cents($v): int { $n = (float) preg_replace('/[^0-9.]/', '', (string) ($v ?? '')); return $n > 0 ? (int) round($n * 100) : 0; }
    private static function r2(float $x): float { return ($x < 0 ? -1 : 1) * round(abs($x) * 100) / 100; }
    private static function hasSessionDate(array $t): bool { return class_exists('GameEngine') ? GameEngine::hasSessionDate($t) : !empty($t['session_date']); }

    /** the dimensions of each trade (in the day's real order: nth and after) */
    private static function dimsOf(array $list, array $pre): array
    {
        $out = []; $day = null; $i = 0; $prev = null;
        foreach ($list as $t) {
            if ($t['date'] !== $day) { $day = $t['date']; $i = 0; $prev = null; }
            $d = [];
            $s = trim((string) ($t['setup'] ?? '')); if ($s !== '') $d['setup'] = $s;
            if (preg_match('/^(\d{1,2}):(\d{2})/', (string) ($t['entry_time'] ?? ''), $m)) { $x = intdiv((int) $m[1] * 60 + (int) $m[2], 30) * 30; $d['slot'] = sprintf('%02d:%02d', intdiv($x, 60), $x % 60); }
            if ((string) ($t['session'] ?? '') !== '') $d['session'] = (string) $t['session'];
            $d['weekday'] = (new DateTimeImmutable($t['date'] . ' 12:00:00', new DateTimeZone('UTC')))->format('N');
            if (in_array($t['direction'] ?? '', ['long', 'short'], true)) $d['side'] = $t['direction'];
            $p = $pre[$t['date']] ?? null;
            if (is_array($p)) {
                $bias = in_array($p['bias'] ?? '', ['bullish', 'bearish', 'neutral', 'no_trade'], true) ? $p['bias'] : null;
                if ($bias && ($bias === 'no_trade' || self::cents($p['max_loss'] ?? '') > 0)) {
                    $ps = array_values(array_filter(array_map([self::class, 'low'], (array) ($p['setups'] ?? [])), fn($x) => $x !== ''));
                    $in = $bias !== 'no_trade' && ($bias === 'neutral' || (($bias === 'bullish') === (($t['direction'] ?? '') === 'long')))
                        && (!$ps || in_array(self::low($t['setup'] ?? ''), $ps, true));
                    $d['plan'] = $in ? 'in' : 'out';
                }
            }
            $e = ((array) (($t['emo'] ?? [])['before'] ?? []))[0] ?? null; if (is_string($e) && $e !== '') $d['emo'] = $e;
            if ($i < 2) $d['nth'] = (string) ($i + 1);
            if ($prev !== null) { $pn = self::net($prev); if ($pn !== 0) $d['after'] = $pn > 0 ? 'win' : 'loss'; }
            if ((string) ($t['instrument'] ?? '') !== '') $d['inst'] = strtoupper((string) $t['instrument']);
            $out[] = $d; $prev = $t; $i++;
        }
        return $out;
    }

    /** @param array $trades all the trader's trades; @param array $journals journals (id = session day, pre = the plan); @param string $day the session */
    public static function profile(array $trades, array $journals, string $day): array
    {
        $from = self::addDays($day, -55); $mid = self::addDays($day, -27); $wk = self::addDays($day, -6);
        // a copied trade once: the first saved of its group (as GameEngine::onePerCopyGroup)
        $list = []; $at = [];
        foreach ($trades as $t) {
            if (!is_array($t) || !empty($t['demo']) || !isset($t['date']) || $t['date'] < $from || $t['date'] > $day) continue;
            $g = (string) ($t['copy_group'] ?? '');
            if ($g === '') { $list[] = $t; continue; }
            $k = (string) (($t['created_at'] ?? '') ?: ($t['id'] ?? ''));
            if (!isset($at[$g])) { $at[$g] = [count($list), $k]; $list[] = $t; }
            elseif (strcmp($k, $at[$g][1]) < 0) { $list[$at[$g][0]] = $t; $at[$g][1] = $k; }
        }
        // the real order: by session, an evening trade (18:00 or later) before that session's morning, then saved time, then id
        $rk = function (array $t): string { $x = substr((string) ($t['entry_time'] ?? ''), 0, 5); return (self::hasSessionDate($t) && $x !== '' && $x >= '18' ? '0' : '1') . ($x !== '' ? $x : '99:99'); };
        usort($list, function ($a, $b) use ($rk) {
            return strcmp($a['date'], $b['date']) ?: strcmp($rk($a), $rk($b)) ?: strcmp((string) ($a['created_at'] ?? ''), (string) ($b['created_at'] ?? '')) ?: strcmp((string) ($a['id'] ?? ''), (string) ($b['id'] ?? ''));
        });
        $pre = []; foreach ($journals as $j) if (is_array($j) && isset($j['id'])) $pre[(string) $j['id']] = $j['pre'] ?? null;
        $dims = self::dimsOf($list, $pre);
        $withR = 0; foreach ($list as $t) if ((int) ($t['risk_c'] ?? 0) > 0) $withR++;
        $unit = $list && $withR >= 0.8 * count($list) ? 'R' : '$';
        $rows = [];
        foreach ($list as $i => $t) {
            $risk = (int) ($t['risk_c'] ?? 0);
            if ($unit === 'R') { if ($risk <= 0) continue; $v = self::net($t) / $risk; }
            else $v = self::net($t) / 100 / max(1, (int) round((float) ($t['contracts'] ?? 1)));
            $rows[] = ['t' => $t, 'v' => $v, 'w' => $t['date'] >= $mid ? 2 : 1, 'd' => $dims[$i]];
        }
        $n = count($rows);
        $base = ['n' => $n, 'unit' => $unit, 'avg' => 0.0, 'enough' => $n >= 5, 'wins' => [], 'leak' => null];
        if (!$n) return $base;
        $sw = 0; $s = 0.0; $sa = 0.0;
        foreach ($rows as $r) { $sw += $r['w']; $s += $r['w'] * $r['v']; $sa += $r['w'] * abs($r['v']); }
        $M = $s / $sw; $A = $sa / $sw; $base['avg'] = self::r2($M);
        // every condition of 1 or 2 dimensions
        $C = [];
        foreach ($rows as $k => $r) {
            $keys = [];
            $ds = array_values(array_filter(self::DIMS, fn($x) => isset($r['d'][$x])));
            foreach ($ds as $a) $keys[] = [[$a, $r['d'][$a]]];
            for ($x = 0; $x < count($ds); $x++) for ($y = $x + 1; $y < count($ds); $y++) $keys[] = [[$ds[$x], $r['d'][$ds[$x]]], [$ds[$y], $r['d'][$ds[$y]]]];
            foreach ($keys as $pairs) {
                $key = implode('|', array_map(fn($p) => $p[0] . '=' . ($p[0] === 'setup' ? self::low($p[1]) : $p[1]), $pairs));
                if (!isset($C[$key])) $C[$key] = ['key' => $key, 'dims' => $pairs, 'n' => 0, 'w' => 0, 's' => 0.0, 'wins' => 0, 'no' => 0, 'so' => 0.0, 'nr' => 0, 'sr' => 0.0, 'nw' => 0, 'last' => '', 'ids' => []];
                $c = &$C[$key];
                $c['dims'] = $pairs;   // the setup as last written
                $c['n']++; $c['w'] += $r['w']; $c['s'] += $r['w'] * $r['v'];
                if (self::net($r['t']) > 0) $c['wins']++;
                if ($r['t']['date'] >= $mid) { $c['nr']++; $c['sr'] += $r['v']; } else { $c['no']++; $c['so'] += $r['v']; }
                if ($r['t']['date'] < $wk) $c['nw']++;
                if (strcmp($r['t']['date'], $c['last']) > 0) $c['last'] = $r['t']['date'];
                $c['ids'][$k] = true;
                unset($c);
            }
        }
        $win = []; $loss = [];
        foreach ($C as $c) {
            if ($c['n'] < 5) continue;
            $m = $c['s'] / $c['w'];
            if ($m > 0 && $m - $M >= 0.25 * $A && $A > 0) $win[] = $c + ['m' => $m, 'score' => ($m - $M) * sqrt($c['n'])];
            elseif ($m < 0 && $M - $m >= 0.25 * $A && $A > 0) $loss[] = $c + ['m' => $m, 'score' => ($M - $m) * sqrt($c['n'])];
        }
        // the same score (often the same trades): the simplest first (1 dimension), then in the order of DIMS (the setup first)
        $rank = fn($c) => count($c['dims']) . ':' . implode(',', array_map(fn($p) => (string) array_search($p[0], self::DIMS, true), $c['dims']));
        $order = fn($a, $b) => ($b['score'] <=> $a['score']) ?: ($b['n'] <=> $a['n']) ?: strcmp($rank($a), $rank($b)) ?: strcmp($a['key'], $b['key']);
        usort($win, $order); usort($loss, $order);
        $picked = [];
        foreach ($win as $c) {
            if (count($picked) >= 3) break;
            foreach ($picked as $p) { $both = count(array_intersect_key($c['ids'], $p['ids'])); if ($both / (count($c['ids']) + count($p['ids']) - $both) >= 0.8) continue 2; }
            $picked[] = $c;
        }
        $out = function (array $c) {
            $mo = $c['no'] ? $c['so'] / $c['no'] : null; $mr = $c['nr'] ? $c['sr'] / $c['nr'] : null;
            $level = $c['n'] >= 20 && $c['no'] && $c['nr'] && $mo > 0 && $mr > 0 ? 'confirmed' : ($c['n'] >= 10 ? 'trend' : 'lead');
            return ['key' => $c['key'], 'dims' => $c['dims'], 'n' => $c['n'], 'win' => (int) round($c['wins'] / $c['n'] * 100), 'avg' => self::r2($c['m']), 'level' => $level, 'last' => $c['last'],
                'new' => $c['nw'] < 5, 'fading' => $c['nr'] >= 5 && $c['no'] >= 5 && $mo > 0 && $mr < $mo / 2];
        };
        $base['wins'] = array_map($out, $picked);
        $base['leak'] = $loss ? $out($loss[0]) : null;
        return $base;
    }

    /** the trader's profile as the server reads it (Edge Reveal, the weekly recap) */
    public static function forUser(string $uid, ?string $day = null): array
    {
        return self::profile(GameEngine::docs($uid, 'trades'), GameEngine::docs($uid, 'journals'), $day ?? GameEngine::today());
    }
}
