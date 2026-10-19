<?php
declare(strict_types=1);
/**
 * Sweep — the pre-market sheet (« fiche », brief « Plan pre-market adaptatif », step 1): one per trading day and trader,
 * kept in the day's journal document (journals/{day}.fiche). The same model as SweepFiche in src/game.js.
 * A trading day follows New York: it starts at 18:00 the evening before (NY + 6 h, like GameEngine::today()); a Saturday or
 * a Sunday belongs to the Monday. The sheet locks at the trader's time (09:25 NY by default).
 */
final class Fiche
{
    public const VERSION = 1;
    public const LOCK_HM = '09:25';
    public const SCENARIO_TYPES = ['breakdown', 'breakout', 'continuation', 'reclaim', 'rejection'];
    public const STATUSES = ['waiting', 'confirmed', 'invalidated', 'taken', 'expired'];
    public const NO_TRADE = ['narrow_range', 'two_invalidations', 'time_limit', 'other'];
    public const RULES = ['no_retest', 'off_plan', 'max_trades', 'news_window', 'moved_stop', 'other'];

    private static function tz(): DateTimeZone { static $z = null; return $z ??= new DateTimeZone('America/New_York'); }

    /** the trading day of a moment (epoch seconds) */
    public static function dayOf(int $ts): string
    {
        $d = (new DateTimeImmutable('@' . $ts))->setTimezone(self::tz())->modify('+6 hours');
        while ((int) $d->format('N') > 5) $d = $d->modify('+1 day');
        return $d->format('Y-m-d');
    }

    /** the moment the sheet of a trading day locks (its own date, NY wall time) */
    public static function lockEpoch(string $day, ?string $hm = null): int
    {
        $hm = self::hm($hm) ?? self::LOCK_HM;
        return (new DateTimeImmutable($day . ' ' . $hm, self::tz()))->getTimestamp();
    }

    public static function hm($v): ?string
    {
        return is_string($v) && preg_match('/^([01]\d|2[0-3]):[0-5]\d$/', $v) ? $v : null;
    }

    /** the checklist of a scenario, in its order (a reclaim adds VWAP) */
    public static function conditions(string $type, bool $news = false): array
    {
        return array_merge($news ? ['news_15m'] : [],  $type === 'reclaim' ? ['close_15m', 'retest_5m', 'trigger_5m', 'vwap', 'risk_checked'] : ['close_15m', 'retest_5m', 'trigger_5m', 'risk_checked']);   // B2: the first full 15m after a news comes first
    }

    private static function num($v): ?float { return is_numeric($v) ? (float) $v : null; }
    /** checked boxes: a box only counts when the one before it is checked (the checklist's order) */
    public static function prefix(array $conds, array $done): array { $o = []; foreach ($conds as $c) { if (!in_array($c, $done, true)) break; $o[] = $c; } return $o; }
    /** estimated R: |target − entry| / |entry − stop|, the entry being the scenario's level; one decimal */
    public static function r(?float $level, ?float $stop, ?float $target): ?float
    {
        if ($level === null || $stop === null || $target === null || $level == $stop) return null;
        return round(abs($target - $level) / abs($level - $stop), 1);
    }
    public static function viable(array $f): bool
    {
        if (!$f['scenarios']) return false;
        foreach ($f['scenarios'] as $s) if ($s['r_estimate'] === null || $s['r_estimate'] < 2) return false;
        return true;
    }
    /** now (SWEEP_GAME_NOW, New York time, pins it in tests — like GameEngine::ts()) */
    public static function now(): int
    {
        $e = getenv('SWEEP_GAME_NOW');
        return $e ? (new DateTimeImmutable($e, self::tz()))->getTimestamp() + (time() - (int) ($_SERVER['REQUEST_TIME'] ?? time())) : time();
    }
    /** locked: by the trader (locked_at) or by the clock (the lock time of its day is past) */
    public static function isLocked(array $f, int $now, ?string $hm = null): bool
    {
        return !empty($f['locked_at']) || $now >= self::lockEpoch((string) $f['trading_day'], $hm);
    }

    /** a sheet as the server keeps it: known fields only, the right types; what the client sent beyond that is dropped */
    public static function normalize(array $f, string $day): array
    {
        $lv = is_array($f['levels'] ?? null) ? $f['levels'] : [];
        $sc = []; $an = is_array($f['answers'] ?? null) ? $f['answers'] : []; $news = ($an['B2'] ?? '') === 'yes' && ($an['B1'] ?? '') === 'yes';
        foreach (array_slice(is_array($f['scenarios'] ?? null) ? $f['scenarios'] : [], 0, 2) as $s) {
            if (!is_array($s)) continue;
            $type = in_array($s['type'] ?? '', self::SCENARIO_TYPES, true) ? $s['type'] : 'breakout';
            $sc[] = [
                'id' => in_array($s['id'] ?? '', ['A', 'B'], true) ? $s['id'] : (count($sc) ? 'B' : 'A'),
                'direction' => ($s['direction'] ?? '') === 'short' ? 'short' : 'long',
                'type' => $type,
                'level' => self::num($s['level'] ?? null), 'stop_estimate' => self::num($s['stop_estimate'] ?? null),
                'target' => self::num($s['target'] ?? null), 'r_estimate' => self::r(self::num($s['level'] ?? null), self::num($s['stop_estimate'] ?? null), self::num($s['target'] ?? null)),
                'conditions' => self::conditions($type, $news),
                'done' => self::prefix(self::conditions($type, $news), is_array($s['done'] ?? null) ? $s['done'] : []),
                'status' => in_array($s['status'] ?? '', self::STATUSES, true) ? $s['status'] : 'waiting',
                'source' => ($s['source'] ?? '') === 'auto' ? 'auto' : 'manual',
            ];
        }
        $win = [];
        foreach (is_array($f['news_windows'] ?? null) ? $f['news_windows'] : [] as $w) {
            if (is_array($w) && self::hm($w['start'] ?? null) && self::hm($w['end'] ?? null)) $win[] = ['start' => $w['start'], 'end' => $w['end'], 'event' => mb_substr((string) ($w['event'] ?? ''), 0, 80)];
        }
        $lim = is_array($f['limits'] ?? null) ? $f['limits'] : [];
        return [
            'v' => self::VERSION,
            'trading_day' => $day,
            'instrument' => mb_substr(preg_replace('/[^A-Za-z0-9!._-]/', '', (string) ($f['instrument'] ?? '')), 0, 16),
            'levels' => ['london_high' => self::num($lv['london_high'] ?? null), 'london_low' => self::num($lv['london_low'] ?? null),
                'pdh' => self::num($lv['pdh'] ?? null), 'pdl' => self::num($lv['pdl'] ?? null), 'price' => self::num($lv['price'] ?? null),
                'source' => ($lv['source'] ?? '') === 'auto' ? 'auto' : 'manual'],
            'answers' => (object) (is_array($f['answers'] ?? null) ? array_slice($f['answers'], 0, 40, true) : []),
            'scenarios' => $sc,
            'news_windows' => array_slice($win, 0, 8),
            'no_trade_conditions' => array_values(array_intersect(self::NO_TRADE, is_array($f['no_trade_conditions'] ?? null) ? $f['no_trade_conditions'] : [])),
            'no_trade_other' => mb_substr((string) ($f['no_trade_other'] ?? ''), 0, 120),
            'limits' => ['risk_pct' => in_array(self::num($lim['risk_pct'] ?? null), [0.25, 0.5], true) ? (float) $lim['risk_pct'] : 0.5,
                'max_trades' => max(1, min(20, (int) ($lim['max_trades'] ?? 2))), 'time_limit' => self::hm($lim['time_limit'] ?? null)],
            'reminder' => mb_substr((string) ($f['reminder'] ?? ''), 0, 200),
            'mode' => ($f['mode'] ?? '') === 'express' ? 'express' : 'full',
            'invalidations' => max(0, min(9, (int) ($f['invalidations'] ?? 0))),
            'locked_at' => is_int($f['locked_at'] ?? null) ? $f['locked_at'] : null,
        ];
    }

    /**
     * a journal document on its way in (PUT or batch), $prev the stored one: its sheet normalized; a locked sheet keeps its
     * plan (levels, scenarios, limits…), only the scenarios' status and checked boxes and the invalidations follow; a sheet
     * is never dropped by a document that does not carry it; it locks only with every scenario viable (2R or more).
     */
    public static function apply(array $doc, string $id, ?array $prev = null, ?int $now = null, ?string $hm = null): array
    {
        $isDay = (bool) preg_match('/^\d{4}-\d{2}-\d{2}$/', $id);
        $old = $isDay && is_array($prev['fiche'] ?? null) ? self::normalize($prev['fiche'], $id) : null;
        $now ??= self::now();
        if (!$isDay) { unset($doc['fiche']); return $doc; }
        if (!array_key_exists('fiche', $doc)) { if ($old) $doc['fiche'] = $old; return $doc; }
        if ($old && self::isLocked($old, $now, $hm)) {
            $new = is_array($doc['fiche']) ? self::normalize($doc['fiche'], $id) : null;
            if ($new) {
                foreach ($old['scenarios'] as $i => $s) {
                    foreach ($new['scenarios'] as $n) if ($n['id'] === $s['id']) { $old['scenarios'][$i]['status'] = $n['status']; $old['scenarios'][$i]['done'] = self::prefix($s['conditions'], $n['done']); }
                }
                $old['invalidations'] = $new['invalidations'];
            }
            $doc['fiche'] = $old;
            return $doc;
        }
        if ($doc['fiche'] === null || !is_array($doc['fiche'])) { unset($doc['fiche']); return $doc; }
        $f = self::normalize($doc['fiche'], $id);
        if ($f['locked_at'] !== null && !self::viable($f)) $f['locked_at'] = null;   // under 2R: no lock
        $doc['fiche'] = $f;
        return $doc;
    }
}
