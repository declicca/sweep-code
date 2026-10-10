<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli' && realpath((string) ($_SERVER['SCRIPT_FILENAME'] ?? '')) === realpath(__FILE__)) { http_response_code(404); exit; }
/**
 * Sweep — real money on the server, for « The reality of the month » (sent on the 1st of each month by game/cron.php).
 * Same rules as moneyOf() in src/ux.js (section 24) — tests/e2e_money_parity.py checks both give the same numbers:
 *  - simulated profit = P&L of evaluation and funded accounts (a copied trade counts once: its earliest copy);
 *  - money received   = net of the payouts paid in the period (net_c, else amount_c);
 *  - expenses         = sum of the expenses of the period (a refund is negative);
 *  - net real         = money received + realized P&L of live and personal accounts − expenses.
 */
final class SweepMoneyServer
{
    public static function typeOf(array $a): ?string
    {
        if (function_exists('sweep_money_type_of')) return sweep_money_type_of($a);
        if (in_array($a['money_type'] ?? '', ['eval', 'funded', 'live', 'personal'], true)) return $a['money_type'];
        $ph = (string) ($a['phase'] ?? ''); if (in_array($ph, ['eval', 'funded', 'live', 'personal'], true)) return $ph;
        $r = (array) ($a['rules'] ?? []);
        if (!empty($r['target_c'])) return 'eval';
        foreach (['payout_win_days', 'payout_min_c', 'payout_max_c', 'payout_min_bal_c', 'payout_trade_days'] as $k) if (!empty($r[$k])) return 'funded';
        if (empty($a['firm_id']) && empty($a['preset'])) return 'personal';
        return null;
    }
    private static function docs(PDO $pdo, string $uid, string $col): array
    {
        $st = $pdo->prepare('SELECT id, data FROM documents WHERE user_id = ? AND collection = ?'); $st->execute([$uid, $col]);
        $out = []; foreach ($st->fetchAll(PDO::FETCH_ASSOC) as $r) { $d = json_decode((string) $r['data'], true); if (is_array($d)) { $d['id'] = $d['id'] ?? $r['id']; $out[] = $d; } }
        return $out;
    }
    /** the month's numbers, in cents: [sim, received, expenses, live, net] */
    public static function period(PDO $pdo, string $uid, string $from, string $to): array
    {
        $in = fn($d) => is_string($d) && $d !== '' && $d >= $from && $d <= $to;
        $types = []; foreach (self::docs($pdo, $uid, 'accounts') as $a) $types[$a['id']] = self::typeOf($a);
        $trades = array_values(array_filter(self::docs($pdo, $uid, 'trades'), fn($t) => $in($t['date'] ?? '')));
        if (array_filter($trades, fn($t) => empty($t['demo']))) $trades = array_values(array_filter($trades, fn($t) => empty($t['demo'])));
        $net = fn($t) => (int) ($t['pnl_c'] ?? 0) - (int) ($t['fees_c'] ?? 0);
        $first = [];   // copy group → its earliest copy
        foreach ($trades as $t) { $g = $t['copy_group'] ?? ''; if ($g === '') continue; $k = (string) ($t['created_at'] ?? $t['id']); if (!isset($first[$g]) || $k < $first[$g][0]) $first[$g] = [$k, $t['id']]; }
        $sim = 0; $live = 0;
        foreach ($trades as $t) {
            $ty = $types[$t['account_id'] ?? ''] ?? null;
            if (($ty === 'live' || $ty === 'personal')) $live += $net($t);
            $g = $t['copy_group'] ?? '';
            if (($ty === 'eval' || $ty === 'funded') && ($g === '' || $first[$g][1] === $t['id'])) $sim += $net($t);
        }
        $recv = 0;
        foreach (self::docs($pdo, $uid, 'payouts') as $p) {
            if (($p['status'] ?? '') !== 'paid') continue;
            $d = $p['paid_on'] ?? '' ?: ($p['payment_date'] ?? '' ?: ($p['approval_date'] ?? '' ?: ($p['request_date'] ?? '')));
            if ($in($d)) $recv += (int) ($p['net_c'] ?? $p['amount_c'] ?? 0);
        }
        $exp = 0; foreach (self::docs($pdo, $uid, 'expenses') as $e) if ($in($e['date'] ?? '')) $exp += (int) ($e['amount_c'] ?? 0);
        return ['sim' => $sim, 'received' => $recv, 'expenses' => $exp, 'live' => $live, 'net' => $recv + $live - $exp];
    }
    /** on the 1st (New York), once per trader: « The reality of last month » */
    /** whole dollars in the language's format, the same grouping as the app (tests/e2e_rule_parity.py): en 1,688 · fr 1 688 · es 1.688 */
    public static function dollars(int $c, string $lang): string
    {
        $sign = $c < 0 ? '−' : ''; $v = abs($c) / 100;
        return $sign . ($lang === 'fr' ? number_format($v, 0, ',', "\u{202F}") : ($lang === 'es' ? number_format($v, 0, ',', '.') : number_format($v, 0, '.', ',')));
    }
    public static function monthly(PDO $pdo, string $uid, ?DateTimeImmutable $now = null): bool
    {
        if (!class_exists('Notify')) return false;
        $now = $now ?? new DateTimeImmutable('now', new DateTimeZone('America/New_York'));
        if ((int) $now->format('j') !== 1 || (int) $now->format('G') < 8) return false;
        $first = $now->modify('first day of last month'); $from = $first->format('Y-m-01'); $to = $first->format('Y-m-t');
        $m = self::period($pdo, $uid, $from, $to);
        if (!$m['sim'] && !$m['received'] && !$m['expenses'] && !$m['live']) return false;   // nothing happened
        $fmt = fn(int $c) => number_format($c / 100, 0, '.', ',');
        $mon = (int) $first->format('n') - 1;
        $names = ['en' => ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'], 'fr' => ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'], 'es' => ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']];
        $p = ['month' => $names['en'][$mon], 'month_fr' => $names['fr'][$mon], 'month_es' => $names['es'][$mon], 'from' => $from, 'to' => $to];
        foreach (['sim' => $m['sim'], 'received' => $m['received'], 'expenses' => $m['expenses'], 'net' => $m['net']] as $k => $c) {   // amounts in each language's format (1,688 · 1 688 · 1.688)
            $p[$k] = self::dollars($c, 'en'); $p[$k . '_fr'] = self::dollars($c, 'fr'); $p[$k . '_es'] = self::dollars($c, 'es');
        }
        return (bool) Notify::send($uid, 'money_month', $p,
            ['dedupe_key' => 'money_month:' . $first->format('Y-m'), 'action_url' => '#payouts', 'category' => 'product_updates', 'priority' => 'celebration']   /* shown large once (the session's window), then in the bell */);
    }
}
