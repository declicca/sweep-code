<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli' && realpath((string) ($_SERVER['SCRIPT_FILENAME'] ?? '')) === realpath(__FILE__)) { http_response_code(404); exit; }
/**
 * Ask Sweep — the chat assistant.
 * One Gemini call per message. The AI sees compact summaries of the trader's own data (computed here),
 * today's economic calendar, and a short app guide. When an exact filtered figure is needed it returns a
 * query spec and PHP computes the number (the AI never does the math).
 */
require_once __DIR__ . '/ai-core.php';
require_once __DIR__ . '/ai-stats.php';
require_once __DIR__ . '/ai-features.php';

const ASK_GUIDE = "Sweep app guide (for how-to questions):\n"
    . "- Today: the day's routine (Plan, Execution, Review rings), the coach, the news of the day, your accounts.\n"
    . "- Add a trade: the + button: by hand (symbol, buy/sell, time, contracts, entry, stop, exit) or from a screenshot of your platform. Copy it to your other accounts there or later from the trade's page (« Copy to my group »).\n"
    . "- Trade page: the coach's verdict, « Answer your coach », the full review (checklist, psychology, notes, screenshots), the chart, AI feedback.\n"
    . "- Stats: net P&L, win rate, profit factor (from 5 trades), « What works for you », trends, deep dives (discipline, behavior, recovery, sessions, time of day, setups, news).\n"
    . "- Calendar: P&L by day with U.S. news. Journal: the day's plan and review, the weekly review.\n"
    . "- Accounts: prop firm accounts with their firm's rules (drawdown, target, daily limit, payout conditions); « Ready for a payout » on an account's page says what is missing, « Record my request » fills the payout.\n"
    . "- My money (payouts and expenses): « + Add payout » / « + Add expense »; net = payouts - expenses.\n"
    . "- Import: CSV from Tradovate, Rithmic R|Trader Pro, TopstepX or TradingView; automatic sync from NinjaTrader 8 and Quantower (Settings > Data > Connections).\n"
    . "- Settings: profile, checklist, risk rules, notifications, plan, data (export everything as a ZIP, delete the account). Help: the avatar menu > Help.";

function ask_money($c): ?string { if ($c === null) return null; $v = $c / 100; return ($v < 0 ? '-' : '') . '$' . number_format(abs($v), 2); }

function ask_fmt($v, string $kind, string $lang): string
{
    if ($v === null) return '—';
    $dec = $lang === 'en' ? '.' : ',';
    $n = fn($x, $d) => number_format((float) $x, $d, $dec, $lang === 'en' ? ',' : ' ');
    return match ($kind) {
        'money' => ($v < 0 ? '-' : '') . ($lang === 'en' ? '$' . $n(abs($v) / 100, 2) : $n(abs($v) / 100, 2) . ' $'),
        'pct' => $n($v * 100, 1) . ($lang === 'en' ? '%' : ' %'),
        'ratio' => $n($v, 2),
        'r' => ($v >= 0 ? '+' : '') . $n($v, 2) . 'R',
        'min' => $n($v, 0) . ' min',
        default => (string) (is_float($v) ? $n($v, 1) : $v),
    };
}

function ask_econ(PDO $pdo, string $lang): array
{
    $ny = sai_ny();
    $d0 = new DateTime('today', $ny); $t0 = $d0->getTimestamp(); $t1 = $t0 + 2 * 86400;
    $out = [];
    try {
        foreach (sai_q($pdo, "SELECT id, ts, event, impact, actual, forecast, previous FROM econ_events WHERE country = 'US' AND impact IN ('high','medium') AND ts BETWEEN ? AND ? ORDER BY ts", [$t0 - 86400, $t1]) as $e) {
            $row = ['time_et' => (new DateTime('@' . $e['ts']))->setTimezone($ny)->format('D H:i'), 'event' => $e['event'], 'impact' => $e['impact'],
                'actual' => $e['actual'] ?: null, 'forecast' => $e['forecast'] ?: null, 'previous' => $e['previous'] ?: null];
            try {
                $r = sai_q($pdo, 'SELECT data FROM econ_report WHERE event_id = ? AND lang = ?', [$e['id'], $lang])->fetchColumn();
                if ($r) { $d = json_decode($r, true); $row['report'] = ['headline' => $d['headline'] ?? null, 'summary' => $d['summary'] ?? null, 'nq' => $d['reaction']['nq'] ?? null]; }
            } catch (Throwable $x) { /* report table not created yet */ }
            $out[] = $row;
        }
    } catch (Throwable $x) { /* calendar not loaded yet */ }
    return $out;
}

function sweep_chat(PDO $pdo, string $uid, array $b, string $lang): array
{
    $msg = trim((string) ($b['message'] ?? ''));
    if ($msg === '' || mb_strlen($msg) > 600) throw new SaiError('bad_input', 400);
    $hist = [];
    foreach (array_slice((array) ($b['history'] ?? []), -8) as $h) {
        $role = ($h['role'] ?? '') === 'user' ? 'Trader' : 'Ask Sweep';
        $text = sai_str($h['text'] ?? null, 600);
        if ($text !== null) $hist[] = $role . ': ' . $text;
    }
    $all = array_values(array_filter(sai_trades($pdo, $uid), fn($t) => !$t['demo']));
    $accounts = sai_accounts($pdo, $uid);
    $today = sai_today_ny();
    $since = fn($days) => array_values(array_filter($all, fn($t) => $t['date'] >= (new DateTime($today))->modify("-$days days")->format('Y-m-d')));
    $vals = function (string $k) use ($all) { $c = []; foreach ($all as $t) foreach ((array) ($k === 'tags' ? $t['tags'] : [$t[$k]]) as $v) if ($v !== '' && $v !== null) $c[$v] = ($c[$v] ?? 0) + 1; arsort($c); return array_slice(array_keys($c), 0, 20); };
    $pay = 0; $exp = 0;
    foreach (sai_docs($pdo, $uid, 'payouts') as $p) if (($p['status'] ?? '') === 'paid') $pay += (int) ($p['amount_c'] ?? 0);
    foreach (sai_docs($pdo, $uid, 'expenses') as $e) $exp += (int) ($e['amount_c'] ?? 0);
    $ctx = [
        'today' => $today,
        'all_time' => sai_brief($all),
        'last_30_days' => sai_brief($since(30), false),
        'last_7_days' => sai_brief($since(7), false),
        'today_trades' => sai_brief(array_values(array_filter($all, fn($t) => $t['date'] === $today)), false),
        'accounts' => array_map(fn($a) => $a['name'], $accounts),
        'payouts_paid_usd' => round($pay / 100, 2), 'expenses_usd' => round($exp / 100, 2),
        'labels' => ['setups' => $vals('setup'), 'sessions' => $vals('session'), 'instruments' => $vals('instrument'), 'tags' => $vals('tags')],
        'us_economic_calendar' => ask_econ($pdo, $lang),
    ];
    $prompt = "You are Ask Sweep, the friendly assistant in the Sweep trading journal. Answer the trader's latest message.\n"
        . ASK_GUIDE . "\n\n"
        . "Trader data (computed by Sweep, money in USD, by_* rows are [label, trades, net_usd, win_rate_pct]): " . json_encode($ctx, JSON_UNESCAPED_UNICODE) . "\n\n"
        . "Rules:\n"
        . "- Use only this data. If a precise figure needs a filter or grouping not given above, fill \"query\" and write {value} (and {count}, {best}, {worst}) in the reply where the computed result goes.\n"
        . "  query.metric: one of " . json_encode(SAI_METRICS) . "; query.group_by: one of " . json_encode(SAI_GROUPS) . "; query.filters (optional): date_from, date_to (YYYY-MM-DD), instrument, direction (long|short), session, setup, tag, grade, account, weekdays (1-7), time_from, time_to (HH:MM ET), outcome (win|loss).\n"
        . "- About markets: you may describe today's U.S. economic releases and their reports above. Never predict prices, never give trade signals, entries or financial advice; say so kindly if asked.\n"
        . "- Be warm and brief (max 110 words). Numbers first. Plain text, no markdown tables.\n"
        . "- action (optional) lets the app open a screen: new_trade, ai_log, ai_review, ai_scan, insights, calendar, news, journal, accounts, payouts, settings, import.\n"
        . "- followups: 2-3 short questions the trader might ask next.\n"
        . "- data: when the reply uses the trader's own numbers without a query, the window they come from: all_time, last_30_days, last_7_days or today (else null). Say the period and the number of trades in the reply.\n\n"
        . ($hist ? "Conversation so far:\n" . implode("\n", $hist) . "\n\n" : '')
        . "Trader: " . $msg . "\n\n"
        . 'Return JSON: {"reply":string,"query":null|{"metric":string,"group_by":string,"filters":{}},"data":null|string,"action":null|string,"followups":[string]}';
    $r = sai_call($pdo, $uid, 'chat', $prompt, ['system' => sai_system($lang), 'max_tokens' => 700, 'cache' => false]);
    $d = $r['data'];
    $reply = sai_str($d['reply'] ?? null, 1200) ?? '';
    $q = is_array($d['query'] ?? null) ? $d['query'] : null;
    // the trades an answer about the trader's data comes from, counted here (never by the model): « Based on your 48 trades … »
    $span = function (array $l): ?array { if (!$l) return null; $ds = array_column($l, 'date'); sort($ds); return ['trades' => count($l), 'from' => $ds[0], 'to' => end($ds)]; };
    $win = ['all_time' => $all, 'last_30_days' => $since(30), 'last_7_days' => $since(7), 'today' => array_values(array_filter($all, fn($t) => $t['date'] === $today))];
    $basis = !$q && is_string($d['data'] ?? null) && isset($win[$d['data']]) ? $span($win[$d['data']]) : null;
    if ($q) {
        $metric = in_array($q['metric'] ?? '', SAI_METRICS, true) ? $q['metric'] : 'net_pnl';
        $by = in_array($q['group_by'] ?? '', SAI_GROUPS, true) ? $q['group_by'] : 'none';
        $f = is_array($q['filters'] ?? null) ? $q['filters'] : [];
        $clean = [];
        foreach (['date_from', 'date_to'] as $k) if (is_string($f[$k] ?? null) && preg_match('/^\d{4}-\d{2}-\d{2}$/', $f[$k])) $clean[$k] = $f[$k];
        foreach (['instrument', 'session', 'setup', 'tag', 'grade', 'account', 'time_from', 'time_to'] as $k) if (($v = sai_str($f[$k] ?? null, 60)) !== null) $clean[$k] = $v;
        if (in_array($f['direction'] ?? null, ['long', 'short'], true)) $clean['direction'] = $f['direction'];
        if (in_array($f['outcome'] ?? null, ['win', 'loss'], true)) $clean['outcome'] = $f['outcome'];
        if (is_array($f['weekdays'] ?? null)) $clean['weekdays'] = array_values(array_filter(array_map('intval', $f['weekdays']), fn($x) => $x >= 1 && $x <= 7));
        $trades = sai_filter($all, $clean, $accounts);
        $m = sai_metrics($trades);
        $basis = $span($trades);
        [$value, $kind] = sai_metric_value($metric, $m);
        $rows = $by !== 'none' ? sai_grouped($trades, $by, $metric, $accounts) : [];
        $ranked = array_values(array_filter($rows, fn($x) => $x['value'] !== null && $x['trades'] >= 1));
        usort($ranked, fn($a, $b) => $b['value'] <=> $a['value']);
        $reply = strtr($reply, ['{value}' => ask_fmt($value, $kind, $lang), '{count}' => (string) $m['trades'],
            '{best}' => (string) ($ranked[0]['label'] ?? '—'), '{worst}' => (string) ($ranked ? end($ranked)['label'] : '—')]);
    }
    $reply = preg_replace('/\{(value|count|best|worst)\}/', '—', $reply);
    $actions = ['new_trade', 'ai_log', 'ai_review', 'ai_scan', 'insights', 'calendar', 'news', 'journal', 'accounts', 'payouts', 'settings', 'import'];
    return [
        'reply' => $reply,
        'action' => in_array($d['action'] ?? null, $actions, true) ? $d['action'] : null,
        'followups' => array_values(array_filter(array_map(fn($x) => sai_str($x, 90), array_slice((array) ($d['followups'] ?? []), 0, 3)))),
        'basis' => $basis,   // {trades, from, to} when the answer speaks about the trader's data
        'cached' => $r['cached'], 'usage' => sai_usage($pdo, $uid),
    ];
}
