<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli' && realpath((string) ($_SERVER['SCRIPT_FILENAME'] ?? '')) === realpath(__FILE__)) { http_response_code(404); exit; }
/**
 * Sweep — the account guardian (brief « Gardien de compte », 3 Nov., SWEEP.md section 8): how much an account can still lose
 * today without being put at risk, and when to stop. The one source of truth for its numbers (the card on Today, its sheet,
 * api/guardian for the future widgets).
 *  - guard_path(): the drawdown path of an account, the same as the app's acctState (src/app.js) with its adjustments
 *    (src/nav.js, « Recalibrate »): static, trailing at the end of the day, trailing trade by trade, stopped at the starting
 *    balance (+ offset), paid payouts and dated adjustments, a live account without rules (its limit is $0). Checked against
 *    acctState by tests/e2e_guard_parity.py: the account page and the guardian show one drawdown room.
 *  - guard_compute(): the brief's numbers from the brief's inputs (floors, room, risk left today, level, consistency, target).
 *  - guard_account(): an account's inputs from its documents, then guard_compute().
 *  - guard_state(): every active account of a trader, the most at risk first, by plan (Free: one account).
 * Amounts in cents. A rule missing from the account's firm rules is never guessed: its indicator is listed in `missing`.
 */

const GUARD_LEVELS = ['calm' => 0, 'watch' => 1, 'danger' => 2, 'stopped' => 3, 'breached' => 4];

/** the order of an account's trades, as acctState sorts them (tkey, src/app.js): the date, an evening trade of the session
 *  first, the entry time, then when it was created */
function guard_tkey(array $t): string
{
    $tm = (string) ($t['entry_time'] ?? '');
    return ($t['date'] ?? '') . ' ' . (GameEngine::hasSessionDate($t) && $tm >= '18' ? '0' : '1') . ($tm !== '' ? $tm : '99:99') . ' ' . ($t['created_at'] ?? '');
}

/**
 * The drawdown path (acctState, src/app.js, with the adjustments of src/nav.js): balance, limit, breached, the highest balance
 * the limit follows. $trades: the account's own trades (any order). $pays: the trader's payouts (only this account's paid ones count).
 * Returns ['bal', 'thr' (null: no drawdown rule), 'breached', 'peak', 'net', 'days' (date => net, in date order)].
 */
function guard_path(array $a, array $trades, array $pays): array
{
    $r = (array) ($a['rules'] ?? []); $id = (string) ($a['id'] ?? '');
    $start = (int) ($a['starting_balance_c'] ?? 0);
    $n = array_values(array_filter($trades, fn($t) => ($t['account_id'] ?? '') === $id));
    usort($n, fn($x, $y) => strcmp(guard_tkey($x), guard_tkey($y)));
    $net = 0; foreach ($n as $t) $net += GameEngine::net($t);
    $PW = [];
    foreach ($pays as $p) if (($p['account_id'] ?? '') === $id && ($p['status'] ?? '') === 'paid') $PW[] = ['d' => (string) (($p['payment_date'] ?? '') ?: (($p['approval_date'] ?? '') ?: (($p['request_date'] ?? '') ?: ($p['date'] ?? '')))), 'a' => (int) ($p['amount_c'] ?? 0)];
    usort($PW, fn($x, $y) => strcmp($x['d'] !== '' ? $x['d'] : '9999', $y['d'] !== '' ? $y['d'] : '9999'));   // a payout without a date: last
    $paid = array_sum(array_column($PW, 'a'));
    $AW = [];
    foreach ((array) ($a['adjustments'] ?? []) as $x) if (is_array($x) && (int) ($x['amount_c'] ?? 0)) $AW[] = ['d' => (string) ($x['at'] ?? ''), 'a' => (int) $x['amount_c']];
    usort($AW, fn($x, $y) => strcmp($x['d'], $y['d']));
    $adj = array_sum(array_column($AW, 'a'));

    $peak = $start; $c = $start; $l = null; $br = false; $PI = 0; $AI = 0;
    $u = (int) ($r['dd_c'] ?? 0); $type = (string) ($r['dd_type'] ?? 'eod');
    $lockOn = ($r['dd_lock'] ?? true) !== false;
    $cap = fn(int $h): int => $lockOn && $type !== 'static' ? min($h, $start + (int) ($r['dd_lock_offset_c'] ?? 0)) : $h;
    $live = !$u && ((($a['money_type'] ?? '') ?: ($a['phase'] ?? '')) === 'live');
    if ($live) $l = 0;
    $AS = function () use (&$c, &$l, &$br) { if ($l !== null && $c <= $l) $br = true; };
    $AT = function () use (&$c, &$l, &$br, &$peak, $u, $cap) { if ($l !== null && $c <= $l) $br = true; $peak = max($peak, $c); $l = $cap($peak - $u); };
    $PAY = function (string $h) use (&$PI, $PW, &$c, &$l, &$br) {
        while ($PI < count($PW) && $PW[$PI]['d'] !== '' && $PW[$PI]['d'] < $h) { $c -= $PW[$PI]['a']; $PI++; if ($l !== null && $c <= $l) $br = true; }
    };
    $ADJ = function (?string $h, callable $f) use (&$AI, $AW, &$c) {
        while ($AI < count($AW) && ($h === null || $AW[$AI]['d'] <= $h)) {
            $d = $AW[$AI]['d'];
            while ($AI < count($AW) && $AW[$AI]['d'] === $d) $c += $AW[$AI++]['a'];
            $f();
        }
    };
    $FIN = function (callable $f) use (&$PI, &$AI, $PW, $AW, &$c, &$l, &$br, $ADJ) {
        while ($PI < count($PW) || $AI < count($AW)) {
            if ($AI < count($AW) && ($PI >= count($PW) || $AW[$AI]['d'] <= ($PW[$PI]['d'] !== '' ? $PW[$PI]['d'] : '9999'))) $ADJ($AW[$AI]['d'], $f);
            else { $c -= $PW[$PI++]['a']; if ($l !== null && $c <= $l) $br = true; }
        }
    };
    $days = [];
    foreach ($n as $t) { $d = (string) ($t['date'] ?? ''); $days[$d] = ($days[$d] ?? 0) + GameEngine::net($t); }
    if ($u) {
        $l = $start - $u;
        if ($type === 'static') {
            foreach ($n as $t) { $ADJ((string) $t['date'], $AS); $PAY((string) $t['date']); $c += GameEngine::net($t); if ($c <= $l) $br = true; }
            $FIN($AS);
        } elseif ($type === 'trade') {
            foreach ($n as $t) { $ADJ((string) $t['date'], $AT); $PAY((string) $t['date']); $c += GameEngine::net($t); if ($c <= $l) $br = true; $peak = max($peak, $c); $l = $cap($peak - $u); }
            $FIN($AT);
        } else {   // trailing at the end of the day (the default type, as acctState)
            $byDay = []; foreach ($n as $t) $byDay[(string) $t['date']][] = $t;
            foreach ($byDay as $d => $list) {
                $ADJ((string) $d, $AT); $PAY((string) $d);
                foreach ($list as $t) { $c += GameEngine::net($t); if ($c <= $l) $br = true; }
                $peak = max($peak, $c); $l = $cap($peak - $u);
            }
            $FIN($AT);
        }
    }
    $bal = $start + $net - $paid + $adj;
    if ($l !== null && $bal <= $l) $br = true;
    return ['bal' => $bal, 'thr' => $l, 'breached' => $br, 'peak' => $peak, 'net' => $net + $adj, 'days' => $days];
}

/**
 * The brief's numbers (section 3, step 2), from the brief's inputs:
 *  rules            the account's firm rules (dd_c, dd_type, dd_lock, dd_lock_offset_c, dll_c, target_c, consistency_pct,
 *                   consistency_base, min_days)
 *  start_c          the account's starting balance          sod_c        the balance at the start of the day
 *  peak_c           the highest balance known               peak_eod_c   the highest end-of-day balance
 *  pnl_c            today's P&L                              plan_c       the trader's planned risk for the day (0: none)
 *  live             a live account without firm rules (its floor is $0, as its page says)
 *  synced           its trades come from the platform (NinjaTrader, Quantower)
 *  breached         the account already went past its limit (its history)
 *  usual_loss_c     the average of the trader's last 20 losses (0: unknown)
 *  stopped          the stop rule was reached (step 5)
 *  days             date => net of every trading day (today included), for the consistency
 *  phase            eval / funded / live;  net_c the account's net profit;  traded_days the days traded
 * Returns the guardian's object (see SWEEP.md 8.4).
 */
function guard_compute(array $in): array
{
    $r = (array) ($in['rules'] ?? []);
    $start = (int) ($in['start_c'] ?? 0); $sod = (int) ($in['sod_c'] ?? $start); $pnl = (int) ($in['pnl_c'] ?? 0); $bal = $sod + $pnl;
    $dd = (int) ($r['dd_c'] ?? 0); $dll = (int) ($r['dll_c'] ?? 0); $type = (string) ($r['dd_type'] ?? 'eod');
    $lockOn = ($r['dd_lock'] ?? true) !== false; $lockAt = $start + (int) ($r['dd_lock_offset_c'] ?? 0);
    $missing = [];
    // the drawdown floor: now, and at the start of the day (the room the day started with)
    $ddFloor = null; $ddFloorSod = null; $estimate = false;
    if ($dd > 0) {
        if ($type === 'static') { $ddFloor = $ddFloorSod = $start - $dd; }
        else {
            $hi = (int) ($type === 'trade' ? ($in['peak_c'] ?? $start) : ($in['peak_eod_c'] ?? $start));
            $hiSod = (int) ($in['peak_sod_c'] ?? $hi);
            $ddFloor = $lockOn ? min($hi - $dd, $lockAt) : $hi - $dd;
            $ddFloorSod = $lockOn ? min($hiSod - $dd, $lockAt) : $hiSod - $dd;
            $estimate = $type === 'trade' && empty($in['synced']);   // Sweep does not see the open (unrealized) highs of a typed account
        }
    } elseif (!empty($in['live'])) { $ddFloor = $ddFloorSod = 0; }
    else $missing[] = 'dd';
    $dayFloor = $dll > 0 ? $sod - $dll : null;
    if ($dll <= 0) $missing[] = 'dll';
    $floors = array_values(array_filter([$ddFloor, $dayFloor], fn($v) => $v !== null));
    $floor = $floors ? max($floors) : null;
    $floorsSod = array_values(array_filter([$ddFloorSod, $dayFloor], fn($v) => $v !== null));
    $room = $floor !== null ? $bal - $floor : null;
    $roomSod = $floorsSod ? $sod - max($floorsSod) : null;
    $plan = (int) ($in['plan_c'] ?? 0);
    $left = $room === null ? null : max(0, $plan > 0 ? min($room, $plan + $pnl) : $room);
    // the level
    $breached = !empty($in['breached']) || ($floor !== null && $bal <= $floor);
    $usual = (int) ($in['usual_loss_c'] ?? 0);
    $pct = $room !== null && $roomSod !== null && $roomSod > 0 ? $room / $roomSod : null;
    if ($breached) $level = 'breached';
    elseif (!empty($in['stopped'])) $level = 'stopped';
    elseif ($room === null) $level = 'calm';
    elseif ($pct === null || $pct < 0.25 || ($usual > 0 && $room < $usual)) $level = 'danger';
    elseif ($pct <= 0.5) $level = 'watch';
    else $level = 'calm';
    // consistency: the best day's share of the profit, and the most today can make while keeping the rule
    $cons = null; $cp = (float) ($r['consistency_pct'] ?? 0);
    if ($cp > 0) {
        $days = array_map('intval', (array) ($in['days'] ?? [])); $today = (string) ($in['today'] ?? '');
        $base = isset($r['consistency_base']) ? (string) $r['consistency_base'] : null;
        $now = GameV2::consPct(array_values($days), $base);
        $other = $days; unset($other[$today]);
        $so = array_sum($base === 'win' ? array_filter($other, fn($v) => $v > 0) : $other);
        $p = $cp / 100; $maxDay = $p < 1 && $so > 0 ? (int) floor($p * $so / (1 - $p)) : null;
        $bo = $other ? max(0, max($other)) : 0;
        $cons = ['pct' => $now === null ? null : round($now, 1), 'limit' => $cp, 'ok' => $now === null || $now <= $cp,
            'max_today_c' => $maxDay !== null && $maxDay >= $bo ? max(0, $maxDay - (int) ($days[$today] ?? 0)) : null];
    } else $missing[] = 'consistency';
    // the target (an evaluation)
    $goal = null; $phase = (string) ($in['phase'] ?? '');
    if (!in_array($phase, ['funded', 'live'], true)) {
        $tg = (int) ($r['target_c'] ?? 0); $md = (int) ($r['min_days'] ?? 0);
        if ($tg > 0) $goal = ['left_c' => max(0, $tg - (int) ($in['net_c'] ?? 0)), 'target_c' => $tg]; else $missing[] = 'target';
        if ($md > 0) $goal = ($goal ?? []) + ['days_left' => max(0, $md - (int) ($in['traded_days'] ?? 0)), 'min_days' => $md]; else $missing[] = 'min_days';
    }
    return [
        'room_c' => $room, 'room_start_c' => $roomSod, 'room_pct' => $pct === null ? null : round(max(0, $pct) * 100, 1), 'left_c' => $left,
        'level' => $level, 'balance_c' => $bal, 'sod_c' => $sod, 'pnl_c' => $pnl, 'plan_c' => $plan ?: null,
        'floors' => ['drawdown_c' => $ddFloor, 'daily_c' => $dayFloor, 'type' => $dd > 0 ? $type : (!empty($in['live']) ? 'live' : null)],
        'consistency' => $cons, 'goal' => $goal, 'estimate' => $estimate, 'missing' => $missing,
    ];
}

/** an active account the guardian watches: not a demo, not archived or closed, with a drawdown or daily limit (or live) */
function guard_watched(array $a): bool
{
    if (!empty($a['demo']) || in_array($a['status'] ?? '', ['archived', 'closed'], true)) return false;
    $r = (array) ($a['rules'] ?? []);
    return (int) ($r['dd_c'] ?? 0) > 0 || (int) ($r['dll_c'] ?? 0) > 0 || ((($a['money_type'] ?? '') ?: ($a['phase'] ?? '')) === 'live');
}

/**
 * An account's inputs from its documents, then guard_compute(). $ctx: today (the session), plan_c, usual_loss_c, synced (bool),
 * stopped (bool), live_c (a balance the trader typed today, step 4: ['bal_c', 'at'] or null).
 */
function guard_account(array $a, array $trades, array $pays, array $ctx): array
{
    $today = (string) $ctx['today']; $id = (string) ($a['id'] ?? '');
    $mine = array_values(array_filter($trades, fn($t) => ($t['account_id'] ?? '') === $id));
    $before = array_values(array_filter($mine, fn($t) => (string) ($t['date'] ?? '') !== $today));
    $now = guard_path($a, $mine, $pays); $sod = guard_path($a, $before, $pays);
    $pnl = $now['bal'] - $sod['bal'];
    // a balance typed today (an account without sync, step 4) is the balance now while no trade of the day came after it
    $lv = $ctx['live'] ?? null; $typed = false;
    if (is_array($lv) && isset($lv['bal_c'])) {
        $typed = true;
        foreach ($mine as $t) if ((string) ($t['date'] ?? '') === $today && strcmp((string) (($t['updated_at'] ?? '') ?: ($t['created_at'] ?? '')), (string) ($lv['at'] ?? '')) > 0) $typed = false;
        if ($typed) $pnl = (int) $lv['bal_c'] - $sod['bal'];
    }
    $r = (array) ($a['rules'] ?? []); $bal = $sod['bal'] + $pnl;
    // the highest balance the trailing limit follows: the path's own; a typed balance moves it as the day's last trade would
    $peak = $typed ? max(((string) ($r['dd_type'] ?? 'eod')) === 'trade' ? $now['peak'] : $sod['peak'], $bal) : $now['peak'];
    $days = $sod['days']; if ($pnl !== 0 || isset($now['days'][$today])) $days[$today] = $pnl;
    $live = !(int) ($r['dd_c'] ?? 0) && ((($a['money_type'] ?? '') ?: ($a['phase'] ?? '')) === 'live');
    $g = guard_compute([
        'rules' => $r, 'start_c' => (int) ($a['starting_balance_c'] ?? 0), 'sod_c' => $sod['bal'], 'pnl_c' => $pnl,
        'peak_c' => $peak, 'peak_eod_c' => $peak, 'peak_sod_c' => $sod['peak'],
        'plan_c' => (int) ($ctx['plan_c'] ?? 0), 'live' => $live, 'synced' => !empty($ctx['synced']),
        'breached' => $typed ? $sod['breached'] : $now['breached'],
        'usual_loss_c' => (int) ($ctx['usual_loss_c'] ?? 0), 'stopped' => !empty($ctx['stopped']),
        'days' => $days, 'today' => $today, 'phase' => (string) (($a['phase'] ?? '') ?: ($a['money_type'] ?? '')),
        'net_c' => $sod['net'] + $pnl, 'traded_days' => count($days),
    ]);
    $g['typed'] = $typed ? (string) ($lv['at'] ?? '') : null;
    return ['id' => $id, 'name' => (string) ($a['name'] ?? ''), 'phase' => (string) (($a['phase'] ?? '') ?: ($a['money_type'] ?? '')), 'synced' => !empty($ctx['synced'])] + $g;
}

/** the average of the trader's last 20 losing trades (cents, positive), 0 without any */
function guard_usual_loss(array $trades): int
{
    $l = array_values(array_filter($trades, fn($t) => empty($t['untracked']) && GameEngine::net($t) < 0));
    usort($l, fn($x, $y) => strcmp(guard_tkey($y), guard_tkey($x)));
    $l = array_slice($l, 0, 20);
    return $l ? (int) round(-array_sum(array_map([GameEngine::class, 'net'], $l)) / count($l)) : 0;
}

/** the trader's planned risk for the day: the day's plan (its max loss), else his own max loss per day (Settings › My routine) */
function guard_plan_risk(string $uid, string $day): int
{
    $pre = (array) ((GameEngine::docs($uid, 'journals')[$day] ?? [])['pre'] ?? []);
    if (in_array($pre['bias'] ?? '', ['bullish', 'bearish', 'neutral'], true)) {
        $v = $pre['max_loss'] ?? null;
        $c = is_numeric($v) ? (int) round((float) $v * 100) : 0;
        if ($c > 0) return $c;
    }
    return GameEngine::standingLimits(GameEngine::docs($uid, 'meta')['settings'] ?? [], $day)['loss_c'];
}

/** the trader's accounts linked to a sync add-on (their trades come from the platform) */
function guard_synced_ids(string $uid): array
{
    try { return array_flip(array_map('strval', GameEngine::q("SELECT account_id FROM sync_accounts WHERE user_id = ? AND account_id IS NOT NULL AND account_id <> ''", [$uid])->fetchAll(PDO::FETCH_COLUMN))); }
    catch (Throwable $e) { return []; }   // no sync table yet
}

/**
 * Every watched account of a trader, the most at risk first (the highest level, then the smallest room). $all: the plan lets the
 * guardian watch every account (Pro, Elite); otherwise (Free) only the first one has its numbers, the others only their name.
 */
function guard_state(string $uid, bool $all, array $opts = []): array
{
    $day = GameEngine::today();
    $accounts = array_values(array_filter(GameEngine::docs($uid, 'accounts'), 'guard_watched'));
    $trades = array_values(GameEngine::docs($uid, 'trades')); $pays = array_values(GameEngine::docs($uid, 'payouts'));
    $j = GameEngine::docs($uid, 'journals')[$day] ?? [];
    $liveBy = (array) (((array) ($j['guard'] ?? []))['live'] ?? []);
    $ctx = ['today' => $day, 'plan_c' => guard_plan_risk($uid, $day), 'usual_loss_c' => guard_usual_loss($trades)];
    $synced = guard_synced_ids($uid); $stopped = (array) ($opts['stopped'] ?? []);
    $out = [];
    foreach ($accounts as $a) {
        $id = (string) $a['id'];
        $out[] = guard_account($a, $trades, $pays, $ctx + ['synced' => isset($synced[$id]), 'stopped' => !empty($stopped[$id]) || !empty($stopped['*']), 'live' => is_array($liveBy[$id] ?? null) ? $liveBy[$id] : null]);
    }
    usort($out, fn($x, $y) => GUARD_LEVELS[$y['level']] <=> GUARD_LEVELS[$x['level']] ?: (($x['room_c'] ?? PHP_INT_MAX) <=> ($y['room_c'] ?? PHP_INT_MAX)) ?: strcmp($x['name'], $y['name']));
    if (!$all) foreach ($out as $k => $g) if ($k > 0) $out[$k] = ['id' => $g['id'], 'name' => $g['name'], 'locked' => true];
    return ['day' => $day, 'all' => $all, 'accounts' => $out];
}
