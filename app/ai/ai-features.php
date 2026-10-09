<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli' && realpath((string) ($_SERVER['SCRIPT_FILENAME'] ?? '')) === realpath(__FILE__)) { http_response_code(404); exit; }
/**
 * Sweep AI — features.
 * Each feature: gather data (PHP, free) → one small AI call (JSON) → validate → return.
 * The AI never writes to the database: it only proposes drafts the trader confirms.
 */

function sai_system(string $lang): string
{
    return "You are the assistant inside Sweep, a trading journal for futures traders who mostly trade prop firm accounts.\n"
        . "Rules: be concise, concrete and numbers-first. Use ONLY the data provided; never invent numbers, trades or facts. "
        . "Judge process (plan, rules, discipline), not just outcome. No market predictions, no trade signals, no financial advice. "
        . "Answer with a single JSON object matching the requested shape, nothing else. Money is in US dollars. Weekdays: 1=Monday … 7=Sunday. "
        . sai_lang_rule($lang);
}

/* =====================================================================
   1) Natural-language trade entry  +  2) screenshot import (trades)
   ===================================================================== */

const SAI_TRADE_SHAPE = '{"trades":[{"instrument":"NQ|MNQ|ES|MES|YM|MYM|RTY|M2K|CL|MCL|GC|MGC|null","direction":"long|short|null",'
    . '"contracts":integer|null,"date":"YYYY-MM-DD|null","entry_time":"HH:MM|null","exit_time":"HH:MM|null","entry":number|null,"exit":number|null,'
    . '"result_value":number|null,"result_unit":"usd|points|ticks|r|null","fees_usd":number|null,"stop":number|null,"target":number|null,'
    . '"setup":string|null,"tags":[string],"account":string|null,"notes":string|null}],"warnings":[string]}';

function sai_trade_context(PDO $pdo, string $uid): array
{
    $settings = sai_settings($pdo, $uid);
    $accounts = array_values(array_filter(sai_accounts($pdo, $uid), fn($a) => $a['active'] && !$a['demo']));
    if (!$accounts) $accounts = array_values(array_filter(sai_accounts($pdo, $uid), fn($a) => $a['active']));
    $setups = array_values(array_unique(array_filter(array_map('strval', (array) ($settings['setups'] ?? [])))));
    return ['accounts' => $accounts, 'setups' => array_slice($setups, 0, 40)];
}

function sai_trade_rules(array $ctx): string
{
    return "Today (New York trading day) is " . sai_today_ny() . ". Resolve relative dates (\"yesterday\", \"Monday\") from it. Times are 24h New York time.\n"
        . "Known setups (use the exact spelling when one matches, else null): " . json_encode($ctx['setups'], JSON_UNESCAPED_UNICODE) . "\n"
        . "Known accounts (put the matching name in \"account\" only if the trader names one): " . json_encode(array_map(fn($a) => trim($a['name'] . ($a['firm'] ? ' (' . $a['firm'] . ')' : '')), $ctx['accounts']), JSON_UNESCAPED_UNICODE) . "\n"
        . "Rules: one object per round-trip trade. \"2 NQ longs\" = two trades; \"long 2 NQ\" = one trade with 2 contracts. "
        . "A loss has a negative result_value. \"Stopped at -12 ticks\" → result_value -12, result_unit \"ticks\". "
        . "If a value is not stated, use null — do not guess prices, times or results. Put anything else useful (reason, emotion) in notes. "
        . "Add a short warning for each trade where direction, contracts or result is missing.";
}

function sai_parse_trades(PDO $pdo, string $uid, string $text, string $lang): array
{
    $text = trim($text);
    if ($text === '' || mb_strlen($text) > 2000) throw new SaiError('bad_input', 400);
    $ctx = sai_trade_context($pdo, $uid);
    $prompt = "Extract the trades described in this trader note.\n" . sai_trade_rules($ctx)
        . "\nReturn JSON exactly shaped like: " . SAI_TRADE_SHAPE . "\n\nTrader note:\n\"\"\"\n" . $text . "\n\"\"\"";
    $r = sai_call($pdo, $uid, 'trade_parse', $prompt, ['system' => sai_system($lang), 'max_tokens' => 1200]);
    return sai_trade_drafts($r['data'], $ctx, 'text') + ['cached' => $r['cached']];
}

function sai_import_trades_image(PDO $pdo, string $uid, array $image, string $lang): array
{
    $ctx = sai_trade_context($pdo, $uid);
    $prompt = "This image is a screenshot from a trading platform or a prop firm dashboard (fills, orders, trade history or performance).\n"
        . "Extract every CLOSED trade you can read. Pair entry and exit fills into round-trip trades when the screenshot shows fills. "
        . "Use the P&L shown on screen as result_value with result_unit \"usd\" when visible. Use fees/commissions if shown. "
        . "If the image is not a trading screenshot, return no trades and one warning saying so.\n"
        . sai_trade_rules($ctx) . "\nReturn JSON exactly shaped like: " . SAI_TRADE_SHAPE;
    $r = sai_call($pdo, $uid, 'trade_import', $prompt, ['system' => sai_system($lang), 'image' => $image, 'max_tokens' => 2500]);
    return sai_trade_drafts($r['data'], $ctx, 'image') + ['cached' => $r['cached']];
}

/** Turn the AI's raw extraction into draft Sweep trade documents (same fields the app saves). */
function sai_trade_drafts(array $data, array $ctx, string $source): array
{
    $drafts = [];
    $defaultAcc = $ctx['accounts'][0] ?? null;
    foreach (array_slice((array) ($data['trades'] ?? []), 0, 50) as $x) {
        if (!is_array($x)) continue;
        $instr = strtoupper((string) ($x['instrument'] ?? ''));
        if (!isset(SAI_INSTRUMENTS[$instr])) $instr = 'NQ';
        $dir = in_array($x['direction'] ?? null, ['long', 'short'], true) ? $x['direction'] : null;
        $date = is_string($x['date'] ?? null) && preg_match('/^\d{4}-\d{2}-\d{2}$/', $x['date']) ? $x['date'] : sai_today_ny();
        $time = fn($v) => is_string($v) && preg_match('/^([01]?\d|2[0-3]):[0-5]\d$/', $v) ? str_pad($v, 5, '0', STR_PAD_LEFT) : '';
        $unit = in_array($x['result_unit'] ?? null, ['usd', 'points', 'ticks', 'r'], true) ? $x['result_unit'] : null;
        $acc = $defaultAcc;
        if (!empty($x['account'])) {
            $h = mb_strtolower((string) $x['account']);
            foreach ($ctx['accounts'] as $a) {
                if (str_contains($h, mb_strtolower($a['name'])) || str_contains(mb_strtolower($a['name']), $h)) { $acc = $a; break; }
            }
        }
        $setup = sai_str($x['setup'] ?? null, 60);
        if ($setup !== null) {
            $match = null;
            foreach ($ctx['setups'] as $s) if (mb_strtolower($s) === mb_strtolower($setup)) $match = $s;
            $setup = $match ?? $setup;
        }
        $t = [
            'id' => sai_id('t'), 'instrument' => $instr, 'account_id' => $acc['id'] ?? '', 'date' => $date, 'direction' => $dir,
            'contracts' => max(1, (int) ($x['contracts'] ?? 1)), 'entry' => sai_num($x['entry'] ?? null), 'exit' => sai_num($x['exit'] ?? null),
            'entry_time' => $time($x['entry_time'] ?? null), 'exit_time' => $time($x['exit_time'] ?? null), 'session' => '',
            'stop' => sai_num($x['stop'] ?? null), 'target' => sai_num($x['target'] ?? null),
            'fees_c' => ($f = sai_num($x['fees_usd'] ?? null)) !== null ? (int) round(abs($f) * 100) : 0,
            'setup' => $setup ?? '', 'grade' => '', 'risk_c' => null, 'planned_rr' => '',
            'r_mult' => $unit === 'r' ? sai_num($x['result_value'] ?? null) : null,
            'tags' => array_values(array_slice(array_filter(array_map(fn($v) => sai_str($v, 30), (array) ($x['tags'] ?? []))), 0, 6)),
            'notes' => sai_str($x['notes'] ?? null, 1000) ?? '', 'discipline' => (object) [], 'emo' => (object) [], 'review' => (object) [], 'shots' => [],
            '_result_value' => sai_num($x['result_value'] ?? null), '_result_unit' => $unit,
        ];
        $pnl = sai_pnl_c($t);
        $t['pnl_c'] = $pnl;
        $t['pnl_manual'] = !($t['entry'] !== null && $t['exit'] !== null);
        $t['ai_source'] = $source;
        unset($t['_result_value'], $t['_result_unit']);
        $missing = [];
        if (!$t['direction']) $missing[] = 'direction';
        if ($t['pnl_c'] === null) $missing[] = 'pnl';
        if ($t['entry_time'] === '') $missing[] = 'entry_time';
        if ($t['exit_time'] === '') $missing[] = 'exit_time';
        if ($t['account_id'] === '') $missing[] = 'account';
        $drafts[] = ['trade' => $t, 'missing' => $missing];
    }
    $warnings = array_values(array_slice(array_filter(array_map(fn($w) => sai_str($w, 200), (array) ($data['warnings'] ?? []))), 0, 10));
    return ['drafts' => $drafts, 'warnings' => $warnings, 'accounts' => $ctx['accounts'], 'setups' => $ctx['setups']];
}

/* =====================================================================
   3) Receipt / payout screenshot scan → expense & payout drafts
   ===================================================================== */

const SAI_EXPENSE_CATS = ['evaluation', 'activation', 'reset', 'data', 'platform', 'other'];
const SAI_PAYOUT_STATUS = ['requested', 'approved', 'paid', 'rejected'];

function sai_scan_receipt(PDO $pdo, string $uid, array $image, string $lang): array
{
    $firms = sai_firms($pdo, $uid);
    $accounts = array_values(array_filter(sai_accounts($pdo, $uid), fn($a) => !$a['demo']));
    $prompt = "This image is a receipt, invoice, order confirmation, payout email or payout dashboard from a prop firm or trading service.\n"
        . "Today is " . sai_today_ny() . ". Known prop firms: " . json_encode(array_column($firms, 'name'), JSON_UNESCAPED_UNICODE) . "\n"
        . "Extract each money item. kind = \"expense\" for money the trader paid (evaluation/challenge = evaluation, activation/funded fee = activation, "
        . "reset = reset, market data = data, platform/software = platform, anything else = other) or \"payout\" for money the trader receives from a firm.\n"
        . "Return JSON exactly shaped like: {\"items\":[{\"kind\":\"expense|payout\",\"date\":\"YYYY-MM-DD|null\",\"amount_usd\":number|null,"
        . "\"category\":\"evaluation|activation|reset|data|platform|other|null\",\"status\":\"requested|approved|paid|rejected|null\","
        . "\"firm\":string|null,\"account_ref\":string|null,\"notes\":string|null}],\"warnings\":[string]}\n"
        . "Amounts are positive numbers. If the currency is not USD, keep the number and add a warning. If the image is unrelated, return no items and a warning.";
    $r = sai_call($pdo, $uid, 'receipt_scan', $prompt, ['system' => sai_system($lang), 'image' => $image, 'max_tokens' => 1000]);

    $items = [];
    foreach (array_slice((array) ($r['data']['items'] ?? []), 0, 20) as $x) {
        if (!is_array($x)) continue;
        $kind = ($x['kind'] ?? '') === 'payout' ? 'payout' : 'expense';
        $amt = sai_num($x['amount_usd'] ?? null);
        $date = is_string($x['date'] ?? null) && preg_match('/^\d{4}-\d{2}-\d{2}$/', $x['date']) ? $x['date'] : sai_today_ny();
        $firmId = '';
        if (!empty($x['firm'])) {
            $h = mb_strtolower((string) $x['firm']);
            foreach ($firms as $f) if ($f['name'] !== '' && (str_contains($h, mb_strtolower($f['name'])) || str_contains(mb_strtolower($f['name']), $h))) { $firmId = $f['id']; break; }
        }
        $accId = '';
        if (!empty($x['account_ref'])) {
            $h = mb_strtolower((string) $x['account_ref']);
            foreach ($accounts as $a) if (str_contains($h, mb_strtolower($a['name'])) || str_contains(mb_strtolower($a['name']), $h)) { $accId = $a['id']; $firmId = $firmId ?: $a['firm_id']; break; }
        }
        $notes = sai_str($x['notes'] ?? null, 300) ?? '';
        if ($kind === 'expense') {
            $cat = in_array($x['category'] ?? null, SAI_EXPENSE_CATS, true) ? $x['category'] : 'other';
            $doc = ['id' => sai_id('e'), 'date' => $date, 'firm_id' => $firmId, 'account_id' => $accId, 'category' => $cat,
                'amount_c' => $amt !== null ? (int) round(abs($amt) * 100) : null, 'notes' => $notes, 'ai_source' => 'image'];
        } else {
            $st = in_array($x['status'] ?? null, SAI_PAYOUT_STATUS, true) ? $x['status'] : 'requested';
            $doc = ['id' => sai_id('p'), 'account_id' => $accId, 'firm_id' => $firmId, 'amount_c' => $amt !== null ? (int) round(abs($amt) * 100) : null,
                'status' => $st, 'request_date' => $date, 'approval_date' => in_array($st, ['approved', 'paid'], true) ? $date : '',
                'payment_date' => $st === 'paid' ? $date : '', 'notes' => $notes, 'ai_source' => 'image'];
        }
        $missing = [];
        if ($doc['amount_c'] === null) $missing[] = 'amount';
        if ($kind === 'payout' && $accId === '') $missing[] = 'account';
        $items[] = ['kind' => $kind, 'doc' => $doc, 'missing' => $missing];
    }
    return ['items' => $items, 'warnings' => array_values(array_filter(array_map(fn($w) => sai_str($w, 200), (array) ($r['data']['warnings'] ?? [])))),
        'firms' => $firms, 'accounts' => $accounts, 'categories' => SAI_EXPENSE_CATS, 'cached' => $r['cached']];
}

/* =====================================================================
   4) Ask your journal — AI turns the question into a safe query; PHP computes the answer.
   ===================================================================== */

function sai_ask(PDO $pdo, string $uid, string $question, string $lang): array
{
    $question = trim($question);
    if ($question === '' || mb_strlen($question) > 400) throw new SaiError('bad_input', 400);
    $all = sai_trades($pdo, $uid);
    $accounts = sai_accounts($pdo, $uid);
    $vals = function (string $k) use ($all) {
        $c = [];
        foreach ($all as $t) foreach ((array) ($k === 'tags' ? $t['tags'] : [$t[$k]]) as $v) if ($v !== '' && $v !== null) $c[$v] = ($c[$v] ?? 0) + 1;
        arsort($c);
        return array_slice(array_keys($c), 0, 30);
    };
    $ctxt = [
        'today' => sai_today_ny(),
        'setups' => $vals('setup'), 'sessions' => $vals('session'), 'instruments' => $vals('instrument'), 'tags' => $vals('tags'),
        'grades' => $vals('grade'), 'accounts' => array_column($accounts, 'name'),
    ];
    // The spec depends on the question + the user's labels only, so it is cached and re-used for free.
    $prompt = "Translate the trader's question about THEIR OWN trade history into a query spec. You do not see the trades; the app computes the answer.\n"
        . "Context (the trader's own labels): " . json_encode($ctxt, JSON_UNESCAPED_UNICODE) . "\n"
        . "metric: one of " . json_encode(SAI_METRICS) . "\n"
        . "group_by: one of " . json_encode(SAI_GROUPS) . " (use one when the question compares or asks \"which/best/worst\").\n"
        . "filters (all optional, use null when not asked): date_from, date_to (YYYY-MM-DD; resolve \"last month\", \"this week\" from today), instrument, "
        . "direction (long|short), session, setup, tag, grade, account (use the trader's labels exactly), weekdays (array of 1-7), "
        . "time_from, time_to (HH:MM New York time of entry), outcome (win|loss).\n"
        . "answer_template: one short sentence answering the question in the trader's language, using {value} for the computed number and {count} for the number of trades "
        . "(and {best} / {worst} for the top/bottom group label when grouped). title: 3-6 word title.\n"
        . "If the question is not about their trading data, set supported=false and put a one-sentence helpful reply in \"reply\".\n"
        . "Return JSON: {\"supported\":true|false,\"reply\":string|null,\"title\":string,\"metric\":string,\"group_by\":string,\"filters\":{...},\"answer_template\":string}\n\n"
        . "Question: \"" . $question . "\"";
    $r = sai_call($pdo, $uid, 'ask', $prompt, ['system' => sai_system($lang), 'max_tokens' => 500]);
    $s = $r['data'];

    if (empty($s['supported'])) {
        return ['supported' => false, 'reply' => sai_str($s['reply'] ?? null, 400) ?? '', 'cached' => $r['cached']];
    }
    $metric = in_array($s['metric'] ?? '', SAI_METRICS, true) ? $s['metric'] : 'net_pnl';
    $by = in_array($s['group_by'] ?? '', SAI_GROUPS, true) ? $s['group_by'] : 'none';
    $f = is_array($s['filters'] ?? null) ? $s['filters'] : [];
    $clean = [];
    foreach (['date_from', 'date_to'] as $k) if (is_string($f[$k] ?? null) && preg_match('/^\d{4}-\d{2}-\d{2}$/', $f[$k])) $clean[$k] = $f[$k];
    foreach (['instrument', 'session', 'setup', 'tag', 'grade', 'account', 'time_from', 'time_to'] as $k) if (($v = sai_str($f[$k] ?? null, 60)) !== null) $clean[$k] = $v;
    if (in_array($f['direction'] ?? null, ['long', 'short'], true)) $clean['direction'] = $f['direction'];
    if (in_array($f['outcome'] ?? null, ['win', 'loss'], true)) $clean['outcome'] = $f['outcome'];
    if (is_array($f['weekdays'] ?? null)) $clean['weekdays'] = array_values(array_filter(array_map('intval', $f['weekdays']), fn($d) => $d >= 1 && $d <= 7));

    $trades = sai_filter($all, $clean, $accounts);
    $m = sai_metrics($trades);
    [$value, $kind] = sai_metric_value($metric, $m);
    $rows = $by !== 'none' ? sai_grouped($trades, $by, $metric, $accounts) : [];
    $ranked = array_values(array_filter($rows, fn($x) => $x['value'] !== null && $x['trades'] >= 1));
    usort($ranked, fn($a, $b) => $b['value'] <=> $a['value']);

    return [
        'supported' => true, 'title' => sai_str($s['title'] ?? null, 80) ?? '', 'metric' => $metric, 'group_by' => $by, 'filters' => $clean,
        'template' => sai_str($s['answer_template'] ?? null, 300) ?? '{value}', 'value' => $value, 'kind' => $kind, 'count' => $m['trades'],
        'best' => $ranked[0]['label'] ?? null, 'worst' => $ranked ? end($ranked)['label'] : null, 'rows' => $rows, 'cached' => $r['cached'],
    ];
}

/* =====================================================================
   5) Weekly review
   ===================================================================== */

function sai_week_bounds(?string $start): array
{
    $d = ($start && preg_match('/^\d{4}-\d{2}-\d{2}$/', $start)) ? new DateTime($start, sai_ny()) : new DateTime('today', sai_ny());
    $d->modify('monday this week');
    $from = $d->format('Y-m-d');
    $to = (clone $d)->modify('+6 days')->format('Y-m-d');
    $prev = (clone $d)->modify('-7 days')->format('Y-m-d');
    return [$from, $to, $prev];
}

function sai_weekly_review(PDO $pdo, string $uid, ?string $weekStart, string $lang): array
{
    [$from, $to, $prevFrom] = sai_week_bounds($weekStart);
    $all = array_values(array_filter(sai_trades($pdo, $uid), fn($t) => !$t['demo']));
    $week = sai_filter($all, ['date_from' => $from, 'date_to' => $to, 'include_demo' => true]);
    $prev = sai_filter($all, ['date_from' => $prevFrom, 'date_to' => date('Y-m-d', strtotime($from . ' -1 day')), 'include_demo' => true]);
    $hist = sai_filter($all, ['date_from' => date('Y-m-d', strtotime($from . ' -56 days')), 'date_to' => $to, 'include_demo' => true]);
    $stats = sai_metrics($week);
    $days = [];
    foreach ($week as $t) { $days[$t['date']]['net_c'] = ($days[$t['date']]['net_c'] ?? 0) + $t['net_c']; $days[$t['date']]['trades'] = ($days[$t['date']]['trades'] ?? 0) + 1; }
    ksort($days);
    $base = ['week_start' => $from, 'week_end' => $to, 'stats' => $stats, 'prev_stats' => sai_metrics($prev), 'days' => $days];
    if (!$week) return $base + ['review' => null, 'reason' => 'no_trades', 'cached' => false];

    $journals = [];
    foreach (sai_docs($pdo, $uid, 'journals') as $j) {
        $d = (string) ($j['date'] ?? $j['id']);
        if ($d >= $from && $d <= $to && empty($j['demo']) && ($b = sai_journal_brief($j))) $journals[$d] = $b;
    }
    ksort($journals);
    $prompt = "Write the trader's weekly review for $from to $to.\n"
        . "THIS WEEK: " . json_encode(sai_brief($week), JSON_UNESCAPED_UNICODE) . "\n"
        . "PREVIOUS WEEK: " . json_encode(sai_brief($prev, false), JSON_UNESCAPED_UNICODE) . "\n"
        . "LAST 8 WEEKS (baseline): " . json_encode(sai_brief($hist, false), JSON_UNESCAPED_UNICODE) . "\n"
        . "DAILY JOURNALS (pre-market plan and post-market notes, may be empty): " . json_encode($journals, JSON_UNESCAPED_UNICODE) . "\n"
        . "Find what actually drove the result: best/worst setup, session, time, day; behavior after losses; plan vs execution (max loss, max trades) when journals exist. "
        . "Each point must cite a number from the data. Be direct and encouraging, never generic.\n"
        . "Return JSON: {\"headline\":string (max 12 words),\"score\":integer 1-10 (process quality, not P&L),\"summary\":string (2-3 sentences),"
        . "\"went_well\":[string, max 3],\"to_fix\":[string, max 3],\"plan_vs_execution\":string|null,\"focus_next_week\":string (one concrete focus),"
        . "\"rule_for_next_week\":string (one simple, measurable rule)}";
    $r = sai_call($pdo, $uid, 'weekly_review', $prompt, ['system' => sai_system($lang), 'max_tokens' => 1200]);
    $d = $r['data'];
    $list = fn($v) => array_values(array_slice(array_filter(array_map(fn($x) => sai_str($x, 300), (array) $v)), 0, 3));
    $review = [
        'headline' => sai_str($d['headline'] ?? null, 120) ?? '', 'score' => max(1, min(10, (int) ($d['score'] ?? 5))),
        'summary' => sai_str($d['summary'] ?? null, 600) ?? '', 'went_well' => $list($d['went_well'] ?? []), 'to_fix' => $list($d['to_fix'] ?? []),
        'plan_vs_execution' => sai_str($d['plan_vs_execution'] ?? null, 400), 'focus_next_week' => sai_str($d['focus_next_week'] ?? null, 300) ?? '',
        'rule_for_next_week' => sai_str($d['rule_for_next_week'] ?? null, 200) ?? '',
    ];
    return $base + ['review' => $review, 'cached' => $r['cached']];
}

/* =====================================================================
   6) Day debrief — plan vs execution for one day
   ===================================================================== */

function sai_day_debrief(PDO $pdo, string $uid, string $date, string $lang): array
{
    if (!preg_match('/^\d{4}-\d{2}-\d{2}$/', $date)) $date = sai_today_ny();
    $all = sai_trades($pdo, $uid);
    $day = sai_filter($all, ['date_from' => $date, 'date_to' => $date, 'include_demo' => true]);
    $journal = sai_journal_brief(sai_journal_for($pdo, $uid, $date));
    $stats = sai_metrics($day);
    if (!$day && !$journal) return ['date' => $date, 'stats' => $stats, 'debrief' => null, 'reason' => 'no_data', 'cached' => false];

    $list = array_map(fn($t) => [
        'time' => trim(($t['entry_time'] ?? '') . '-' . ($t['exit_time'] ?? ''), '-'), 'instrument' => $t['instrument'], 'direction' => $t['direction'],
        'contracts' => $t['contracts'], 'net_usd' => round($t['net_c'] / 100, 2), 'setup' => $t['setup'], 'grade' => $t['grade'], 'r' => $t['r_mult'],
    ], $day);
    $prompt = "Debrief the trader's day $date: compare the PLAN with what they DID.\n"
        . "PLAN AND NOTES (journal, may be empty): " . json_encode($journal, JSON_UNESCAPED_UNICODE) . "\n"
        . "TRADES IN ORDER: " . json_encode($list, JSON_UNESCAPED_UNICODE) . "\n"
        . "DAY TOTALS: " . json_encode(sai_brief($day, false), JSON_UNESCAPED_UNICODE) . "\n"
        . "Check explicitly: max loss respected? max trades respected? bias followed? focus respected? If there is no plan, say so and suggest what to plan tomorrow.\n"
        . "Return JSON: {\"verdict\":\"followed|partly|broke|no_plan\",\"summary\":string (2 sentences),\"checks\":[{\"label\":string,\"ok\":true|false|null,\"detail\":string}] (max 5),"
        . "\"lesson\":string,\"tomorrow\":string (one concrete action)}";
    $r = sai_call($pdo, $uid, 'day_debrief', $prompt, ['system' => sai_system($lang), 'max_tokens' => 900]);
    $d = $r['data'];
    $checks = [];
    foreach (array_slice((array) ($d['checks'] ?? []), 0, 5) as $c) {
        if (!is_array($c) || ($l = sai_str($c['label'] ?? null, 80)) === null) continue;
        $checks[] = ['label' => $l, 'ok' => is_bool($c['ok'] ?? null) ? $c['ok'] : null, 'detail' => sai_str($c['detail'] ?? null, 240) ?? ''];
    }
    return ['date' => $date, 'stats' => $stats, 'debrief' => [
        'verdict' => in_array($d['verdict'] ?? '', ['followed', 'partly', 'broke', 'no_plan'], true) ? $d['verdict'] : 'partly',
        'summary' => sai_str($d['summary'] ?? null, 500) ?? '', 'checks' => $checks,
        'lesson' => sai_str($d['lesson'] ?? null, 300) ?? '', 'tomorrow' => sai_str($d['tomorrow'] ?? null, 300) ?? '',
    ], 'cached' => $r['cached']];
}

/* =====================================================================
   7) Trade feedback (single trade, process-focused)  +  8) setup/tag suggestion
   ===================================================================== */

function sai_trade_payload(array $doc): array
{
    $keep = ['instrument', 'date', 'direction', 'contracts', 'entry', 'exit', 'entry_time', 'exit_time', 'session', 'stop', 'target',
        'setup', 'grade', 'planned_rr', 'r_mult', 'tags', 'notes', 'discipline', 'emo', 'review'];
    $out = [];
    foreach ($keep as $k) if (isset($doc[$k]) && $doc[$k] !== '' && $doc[$k] !== [] && $doc[$k] !== null) $out[$k] = $doc[$k];
    $out['net_usd'] = round(((float) ($doc['pnl_c'] ?? 0) - abs((float) ($doc['fees_c'] ?? 0))) / 100, 2);
    $json = json_encode($out, JSON_UNESCAPED_UNICODE);
    if (strlen($json) > 6000) { unset($out['review']); $out['notes'] = mb_substr((string) ($out['notes'] ?? ''), 0, 800); }
    return $out;
}

function sai_trade_feedback(PDO $pdo, string $uid, string $tradeId, ?array $image, string $lang): array
{
    $doc = sai_doc($pdo, $uid, 'trades', $tradeId);
    if (!$doc) throw new SaiError('not_found', 404);
    $all = array_values(array_filter(sai_trades($pdo, $uid), fn($t) => !$t['demo']));
    $setup = (string) ($doc['setup'] ?? '');
    $same = $setup !== '' ? sai_filter($all, ['setup' => $setup, 'include_demo' => true]) : [];
    $prompt = "Give feedback on this single trade. Focus on process (plan, entry, stop, management, rules, emotions), not on whether it won.\n"
        . "TRADE: " . json_encode(sai_trade_payload($doc), JSON_UNESCAPED_UNICODE) . "\n"
        . "SAME SETUP HISTORY: " . json_encode($same ? sai_brief($same, false) : null, JSON_UNESCAPED_UNICODE) . "\n"
        . "ALL TRADES BASELINE: " . json_encode(sai_brief($all, false), JSON_UNESCAPED_UNICODE) . "\n"
        . ($image ? "A chart screenshot of the trade is attached; use it for context only.\n" : '')
        . "Return JSON: {\"verdict\":\"good_process|mixed|poor_process\",\"went_well\":string,\"improve\":string,\"next_time\":string (one concrete action),"
        . "\"setup_context\":string|null (how this setup usually performs for them, with a number)}";
    $r = sai_call($pdo, $uid, 'trade_feedback', $prompt, ['system' => sai_system($lang), 'image' => $image, 'max_tokens' => 700]);
    $d = $r['data'];
    return ['trade_id' => $tradeId, 'feedback' => [
        'verdict' => in_array($d['verdict'] ?? '', ['good_process', 'mixed', 'poor_process'], true) ? $d['verdict'] : 'mixed',
        'went_well' => sai_str($d['went_well'] ?? null, 400) ?? '', 'improve' => sai_str($d['improve'] ?? null, 400) ?? '',
        'next_time' => sai_str($d['next_time'] ?? null, 300) ?? '', 'setup_context' => sai_str($d['setup_context'] ?? null, 300),
    ], 'cached' => $r['cached']];
}

function sai_suggest_tags(PDO $pdo, string $uid, string $tradeId, ?array $image, string $lang): array
{
    $doc = sai_doc($pdo, $uid, 'trades', $tradeId);
    if (!$doc) throw new SaiError('not_found', 404);
    $ctx = sai_trade_context($pdo, $uid);
    $tags = [];
    foreach (sai_trades($pdo, $uid) as $t) foreach ($t['tags'] as $g) $tags[$g] = ($tags[$g] ?? 0) + 1;
    arsort($tags);
    $prompt = "Suggest how to label this trade in the trader's journal.\n"
        . "TRADE: " . json_encode(sai_trade_payload($doc), JSON_UNESCAPED_UNICODE) . "\n"
        . "THE TRADER'S SETUPS (prefer one of these, exact spelling): " . json_encode($ctx['setups'], JSON_UNESCAPED_UNICODE) . "\n"
        . "THE TRADER'S TAGS (prefer these): " . json_encode(array_slice(array_keys($tags), 0, 40), JSON_UNESCAPED_UNICODE) . "\n"
        . ($image ? "A chart screenshot is attached: read the price action (liquidity sweep, FVG, break of structure, retest, range, trend…).\n" : '')
        . "Return JSON: {\"setup\":string|null (one of the trader's setups),\"new_setup\":string|null (only if none fits),\"tags\":[string, max 4],"
        . "\"reason\":string (one sentence)}";
    $r = sai_call($pdo, $uid, 'suggest_tags', $prompt, ['system' => sai_system($lang), 'image' => $image, 'max_tokens' => 400]);
    $d = $r['data'];
    $setup = sai_str($d['setup'] ?? null, 60);
    if ($setup !== null && !in_array(mb_strtolower($setup), array_map('mb_strtolower', $ctx['setups']), true)) { $d['new_setup'] = $d['new_setup'] ?? $setup; $setup = null; }
    return ['trade_id' => $tradeId, 'setup' => $setup, 'new_setup' => sai_str($d['new_setup'] ?? null, 60),
        'tags' => array_values(array_slice(array_filter(array_map(fn($v) => sai_str($v, 30), (array) ($d['tags'] ?? []))), 0, 4)),
        'reason' => sai_str($d['reason'] ?? null, 300) ?? '', 'cached' => $r['cached']];
}

/* ───────────── several trades from one screenshot ─────────────
 * Gemini only copies the rows it can read (no pairing, no math); ai/shot-trades.php builds the trades.
 * One call per screenshot (one credit). SWEEP_AI_MOCK (env): a JSON file of mocked answers for tests
 * ({ "<sha1 of the image>": {...}, "default": {...} }), so the tests spend no credits. */
const SAI_SHOT_SHAPE = '{"source_type":"closed_trades"|"fills"|"chart"|"unknown","platform_guess":"tradovate"|"rithmic"|"ninjatrader"|"topstepx"|"projectx"|"other","timezone_shown":"ET"|"CT"|"local"|"unknown","account_label":string|null,"rows":[{"symbol":string,"side":"buy"|"sell"|"long"|"short","qty":number,"price":number|null,"entry_price":number|null,"exit_price":number|null,"datetime":string|null,"entry_time":string|null,"exit_time":string|null,"pnl_shown":number|null,"commission_shown":number|null,"confidence":number}]}';
function sai_shot_read(PDO $pdo, string $uid, array $image, string $lang): array
{
    $mock = getenv('SWEEP_AI_MOCK');
    if ($mock && is_file($mock)) {
        $all = json_decode((string) file_get_contents($mock), true) ?: [];
        $key = sha1((string) ($image['data'] ?? ''));
        return ['data' => $all[$key] ?? $all['default'] ?? ['source_type' => 'unknown', 'rows' => []], 'cached' => false];
    }
    // Gemini copies the table AS WRITTEN (titles and cells, character for character); the server reads the columns.
    // Copying text is what a vision model does best; interpreting (sides, times, pairing, math) is done by the server.
    $prompt = "This image is a screenshot from a futures trading platform or prop firm dashboard (Tradovate, Rithmic R|Trader, NinjaTrader, TopstepX, ProjectX, Lucid, Apex…): a list of trades, an order/fill history, or a performance table.\n"
        . "Your only job is to COPY THE TABLE EXACTLY AS WRITTEN. Do not interpret, convert, round, pair, compute or reorder anything.\n"
        . "- columns: the column titles, left to right, exactly as written (e.g. \"Symbol\", \"Side\", \"Qty\", \"Entry Price\", \"Exit Price\", \"Entry Time\", \"Exit Time\", \"P&L\", \"Commission\").\n"
        . "- table: one array per visible row, top to bottom, with one string per column in the SAME order as columns, copied character for character (keep $, commas, minus signs, parentheses, AM/PM, dates and seconds as shown). Use \"\" for an empty cell. Never skip a column, never merge rows.\n"
        . "- pnl_colors: for each row, the colour of its P&L / profit cell: \"red\", \"green\" or null (losses are often only shown in red).\n"
        . "- source_type: \"closed_trades\" when each row is a whole trade (entry and exit), \"fills\" when each row is one execution, \"chart\" for a chart, \"unknown\" if there is no trade.\n"
        . "- symbol_shown: the instrument written ANYWHERE on the screenshot (chart title, header, breadcrumb, account line), exactly as written, e.g. \"Gold (GCZ6) · 5 · COMEX\" or \"MNQZ6\" — needed when the table itself has no symbol column. Else null.\n"
        . "- When the screenshot shows ONE trade as labelled fields (e.g. \"Net P&L $204.00 · Side Long · Lots 1 · Entry $4,149.80 · Exit $4,151.90 · Open time 2:51:12 PM · Close time 3:05:05 PM · Total Charges $6.00\"), return those labels as columns and their values as ONE row of table.\n"
        . "- When it shows both a trade summary (or a list of trades) and its executions, copy the trade summary / list, not the executions.\n"
        . "- timezone_shown: a time zone written on screen (\"ET\", \"CT\", \"UTC\") or \"local\" if the platform says local time, else \"unknown\". date_shown: a date written above or near the table (filter, title) when the rows themselves show only times, else null. account_label: an account number or name shown, else null.\n"
        . "- If the image has no table but a chart with trades, use source_type \"chart\" and put what you can read in rows (symbol, side, qty, entry_price, exit_price, entry_time, exit_time, pnl_shown) with confidence 0-1.\n"
        . "Skip cancelled, rejected or working orders, totals and summary rows. If you cannot read the image, return an empty table.\n"
        . "Return only JSON shaped like: {\"source_type\":string,\"platform_guess\":string,\"timezone_shown\":string,\"date_shown\":string|null,\"symbol_shown\":string|null,\"account_label\":string|null,\"columns\":[string],\"table\":[[string]],\"pnl_colors\":[string|null],\"rows\":[]}";
    $cfg = function_exists('sai_config') ? sai_config() : [];
    return sai_call($pdo, $uid, 'trade_shot2', $prompt, ['system' => sai_system($lang), 'image' => $image, 'max_tokens' => 8000, 'temperature' => 0, 'model' => (string) ($cfg['model_vision'] ?? '')]);
}
/** the read rows → trades for one account, with the time zone resolved (screen, else the account's platform zone, else ask) */
function sai_shot_trades(PDO $pdo, string $uid, array $data, array $b): array
{
    require_once __DIR__ . '/shot-trades.php';
    $ctx = sai_trade_context($pdo, $uid);
    $accId = (string) ($b['account_id'] ?? '');
    $label = mb_strtolower(trim((string) ($data['account_label'] ?? '')));
    $suggest = null;
    if ($label !== '') foreach ($ctx['accounts'] as $a) { $n = mb_strtolower((string) $a['name']); if ($n !== '' && (str_contains($label, $n) || str_contains($n, $label))) { $suggest = $a['id']; break; } }
    $acc = null; foreach (sai_accounts($pdo, $uid) as $a) if ($a['id'] === ($accId ?: $suggest)) $acc = $a;
    $raw = $acc ? (json_decode((string) q("SELECT data FROM documents WHERE user_id = ? AND collection = 'accounts' AND id = ?", [$uid, $acc['id']])->fetchColumn(), true) ?: []) : [];
    $shown = strtoupper((string) ($data['timezone_shown'] ?? 'unknown'));
    $tzChosen = (string) ($b['tz'] ?? '');
    $tz = null; $needs = false;
    if (in_array($tzChosen, ['America/New_York', 'America/Chicago', 'UTC'], true) || ($tzChosen && in_array($tzChosen, timezone_identifiers_list(), true))) $tz = $tzChosen;
    elseif (isset(SHOT_TZ[$shown])) $tz = SHOT_TZ[$shown];
    elseif ($shown === 'LOCAL' && !empty($b['local_tz']) && in_array($b['local_tz'], timezone_identifiers_list(), true)) $tz = (string) $b['local_tz'];
    elseif (!empty($raw['platform_tz']) && in_array($raw['platform_tz'], timezone_identifiers_list(), true)) $tz = (string) $raw['platform_tz'];
    else { $tz = 'America/New_York'; $needs = true; }
    $built = shot_build($data, ['tz' => $tz, 'date' => sai_today_ny(), 'fee_rt_c' => (int) ($raw['fee_rt_c'] ?? 0)]);
    return ['source_type' => (string) ($data['source_type'] ?? 'unknown'), 'platform_guess' => (string) ($data['platform_guess'] ?? 'other'), 'timezone_shown' => $shown,
        'tz' => $tz, 'needs_tz' => $needs, 'account_suggest' => $suggest, 'account_label' => $data['account_label'] ?? null, 'rows' => $data['rows'] ?? [], 'columns' => $data['columns'] ?? [], 'table' => $data['table'] ?? [], 'pnl_colors' => $data['pnl_colors'] ?? [], 'date_shown' => $data['date_shown'] ?? null, 'symbol_shown' => $data['symbol_shown'] ?? null, 'no_symbol' => $built['no_symbol'] ?? false, 'meta' => array_diff_key($data, ['rows' => 1, 'table' => 1]),
        'trades' => $built['trades'], 'open' => $built['open'], 'unknown' => $built['unknown'], 'skipped' => $built['skipped'] ?? 0];
}
