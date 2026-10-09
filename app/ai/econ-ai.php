<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli' && realpath((string) ($_SERVER['SCRIPT_FILENAME'] ?? '')) === realpath(__FILE__)) { http_response_code(404); exit; }
/**
 * Sweep AI — economic calendar.
 *
 *  1. Values: after a U.S. release (and for forecasts of the coming days), Gemini with Google Search
 *     looks up actual / forecast / previous / revised and Sweep stores them in econ_events.
 *  2. Market impact report: once the actual is known and the market has had time to react
 *     (30 minutes), Gemini writes a short grounded report, cached for everyone, per language.
 *
 * Report stages: flash at +1 min (the number and what it means), full at +30 min (market reaction), final at +3 h.
 * Cost control: shares the global daily USD budget of ai-config.php, plus its own daily cap
 * ('econ_daily_calls', default 60). Every call is logged in ai_log under user_id 'system:econ'.
 */
require_once __DIR__ . '/ai-core.php';

const EAI_UID = 'system:econ';
const EAI_SEARCH_PRICE = 0.014;      // USD per grounded search query (after Google's monthly free quota; counted conservatively)
const EAI_REPORT_DELAY = 60;         // flash recap 1 minute after the release
const EAI_REPORT_FULL = 1800;        // full report (market reaction) 30 minutes after the release
const EAI_REPORT_REFRESH = 10800;    // one refresh allowed 3 h after the release, for a fuller picture

function eai_enabled(): bool { $c = sai_config(); return (bool) $c['enabled']; }

function eai_schema(PDO $pdo): void
{
    static $done = false; if ($done) return; $done = true;
    sai_init_db($pdo);
    $my = $pdo->getAttribute(PDO::ATTR_DRIVER_NAME) === 'mysql';
    $pdo->exec($my
        ? 'CREATE TABLE IF NOT EXISTS econ_fill (event_id CHAR(40) NOT NULL PRIMARY KEY, kind VARCHAR(10) NOT NULL, tries INT NOT NULL DEFAULT 0, last_try INT NOT NULL DEFAULT 0, status VARCHAR(12) NOT NULL DEFAULT \'pending\', sources TEXT NULL) DEFAULT CHARSET=utf8mb4'
        : 'CREATE TABLE IF NOT EXISTS econ_fill (event_id TEXT PRIMARY KEY, kind TEXT NOT NULL, tries INTEGER NOT NULL DEFAULT 0, last_try INTEGER NOT NULL DEFAULT 0, status TEXT NOT NULL DEFAULT \'pending\', sources TEXT)');
    $pdo->exec($my
        ? 'CREATE TABLE IF NOT EXISTS econ_report (event_id CHAR(40) NOT NULL, lang VARCHAR(2) NOT NULL, data MEDIUMTEXT NOT NULL, sources TEXT NULL, suggest MEDIUMTEXT NULL, created_at INT NOT NULL, PRIMARY KEY (event_id, lang)) DEFAULT CHARSET=utf8mb4'
        : 'CREATE TABLE IF NOT EXISTS econ_report (event_id TEXT NOT NULL, lang TEXT NOT NULL, data TEXT NOT NULL, sources TEXT, suggest TEXT, created_at INTEGER NOT NULL, PRIMARY KEY (event_id, lang))');
}

/** One grounded Gemini call (Google Search tool). Returns data + sources + Google search suggestions. */
function eai_call(PDO $pdo, string $task, string $prompt, int $maxTokens = 1200, string $lang = 'en'): array
{
    $cfg = sai_config();
    if (!$cfg['enabled']) throw new SaiError('disabled', 503);
    if (sai_spent_today($pdo) >= (float) $cfg['global_daily_budget_usd']) throw new SaiError('budget', 503);
    $cap = (int) ($cfg['econ_daily_calls'] ?? 60);
    $n = (int) sai_q($pdo, 'SELECT COUNT(*) FROM ai_log WHERE user_id = ? AND created_at >= ?', [EAI_UID, sai_day_start_utc()])->fetchColumn();
    if ($n >= $cap) throw new SaiError('daily_limit', 429);

    $body = [
        'contents' => [['role' => 'user', 'parts' => [['text' => $prompt]]]],
        'tools' => [['google_search' => (object) []]],
        'systemInstruction' => ['parts' => [['text' => "You are Sweep's economic data desk. You look facts up with Google Search and never invent numbers. "
            . "If you cannot find a figure in a reliable source, return null for it. Answer with JSON only, no prose around it. " . sai_lang_rule($lang)]]],
        'generationConfig' => ['maxOutputTokens' => $maxTokens, 'temperature' => 0.1],
    ];
    if (!empty($cfg['thinking_level'])) $body['generationConfig']['thinkingConfig'] = ['thinkingLevel' => (string) $cfg['thinking_level']];
    [$status, $raw] = sai_http($cfg, $body);
    if ($status === 400 && isset($body['generationConfig']['thinkingConfig']) && stripos((string) $raw, 'thinking') !== false) {
        unset($body['generationConfig']['thinkingConfig']);
        [$status, $raw] = sai_http($cfg, $body);
    }
    if ($status === 0) throw new SaiError('network', 502);
    $res = json_decode((string) $raw, true);
    if ($status !== 200 || !is_array($res)) {
        error_log('[Sweep AI] econ HTTP ' . $status . ' ' . substr((string) $raw, 0, 800));
        throw new SaiError($status === 429 ? 'provider_busy' : 'provider', $status === 429 ? 503 : 502);
    }
    $cand = $res['candidates'][0] ?? [];
    $text = '';
    foreach ($cand['content']['parts'] ?? [] as $p) if (isset($p['text']) && empty($p['thought'])) $text .= $p['text'];
    $gm = $cand['groundingMetadata'] ?? [];
    $queries = count((array) ($gm['webSearchQueries'] ?? []));
    $u = $res['usageMetadata'] ?? [];
    $in = (int) ($u['promptTokenCount'] ?? 0);
    $out = (int) ($u['candidatesTokenCount'] ?? 0) + (int) ($u['thoughtsTokenCount'] ?? 0);
    $cost = $in / 1e6 * (float) $cfg['price_input_per_m'] + $out / 1e6 * (float) $cfg['price_output_per_m'] + $queries * (float) ($cfg['search_price_per_query'] ?? EAI_SEARCH_PRICE);
    sai_q($pdo, 'INSERT INTO ai_log (user_id, task, input_tokens, output_tokens, cost_usd, created_at) VALUES (?, ?, ?, ?, ?, ?)',
        [EAI_UID, substr($task, 0, 40), $in, $out, round($cost, 6), sai_now()]);

    $data = sai_json($text);
    if ($data === null) { error_log('[Sweep AI] econ unparseable answer for ' . $task . ': ' . substr($text, 0, 400)); throw new SaiError('bad_output', 502); }
    $sources = [];
    foreach ((array) ($gm['groundingChunks'] ?? []) as $c) {
        $w = $c['web'] ?? null; if (!$w || empty($w['uri'])) continue;
        $sources[] = ['title' => mb_substr((string) ($w['title'] ?? ''), 0, 120), 'uri' => (string) $w['uri']];
        if (count($sources) >= 6) break;
    }
    $suggest = (string) ($gm['searchEntryPoint']['renderedContent'] ?? '');
    return ['data' => $data, 'sources' => $sources, 'suggest' => $suggest];
}

/** Clean a value the way calendars print it ("0.3%", "142K", "52.1"). */
function eai_val($v): ?string
{
    if ($v === null) return null;
    if (is_float($v) || is_int($v)) $v = (string) $v;
    if (!is_string($v)) return null;
    $v = trim($v);
    if ($v === '' || preg_match('/^(n\/?a|null|none|tbd|-|—)$/i', $v)) return null;
    if (!preg_match('/\d/', $v)) return null;
    return mb_substr($v, 0, 24);
}

/**
 * Fill released values (and upcoming forecasts). Global (one shared calendar), protected by a lock.
 * Returns the number of events updated.
 */
function eai_fill(PDO $pdo, int $maxCalls = 2): int
{
    if (!eai_enabled()) return 0;
    eai_schema($pdo);
    // lock: one refresh at a time for the whole app
    $now = time();
    $lock = (int) (sai_q($pdo, "SELECT v FROM app_settings WHERE k = 'econ_ai_lock'")->fetchColumn() ?: 0);
    if ($lock > $now - 40) return 0;
    $pdo->prepare('DELETE FROM app_settings WHERE k = ?')->execute(['econ_ai_lock']);
    $pdo->prepare('INSERT INTO app_settings (k, v) VALUES (?, ?)')->execute(['econ_ai_lock', (string) $now]);

    $fill = [];
    foreach (sai_q($pdo, 'SELECT event_id, kind, tries, last_try, status FROM econ_fill') as $r) $fill[$r['event_id']] = $r;
    $due = [];
    // 1) released, still no actual (last 3 days)
    foreach (sai_q($pdo, "SELECT id, ts, event, impact, actual, forecast, previous FROM econ_events WHERE country = 'US' AND impact IN ('high','medium') AND ts BETWEEN ? AND ? ORDER BY ts DESC",
        [$now - 3 * 86400, $now - 45]) as $e) {
        if (trim((string) $e['actual']) !== '') continue;
        if (preg_match('/minutes|speech|speaks|testimony|press conference|beige book|statement|remarks/i', (string) $e['event'])) continue;   // text release: no value to fill
        $f = $fill[$e['id']] ?? null;
        if ($f && ($f['status'] === 'done' || ((int) $f['tries'] >= 8 && $now - (int) $f['last_try'] < 3600))) continue;   // after 8 misses: one more try per hour (a past outage no longer blocks the event for good)
        $age = $now - (int) $e['ts'];
        $gap = $age < 900 ? 40 : ($age < 3600 ? 180 : ($age < 6 * 3600 ? 900 : 3600));
        if ($f && $now - (int) $f['last_try'] < $gap) continue;
        $due[] = $e + ['kind' => 'actual'];
    }
    // 2) coming 7 days, no forecast yet (refreshed at most every 12 h)
    foreach (sai_q($pdo, "SELECT id, ts, event, impact, actual, forecast, previous FROM econ_events WHERE country = 'US' AND impact IN ('high','medium') AND ts BETWEEN ? AND ? ORDER BY ts",
        [$now, $now + 7 * 86400]) as $e) {
        if (trim((string) $e['forecast']) !== '') continue;
        $f = $fill[$e['id']] ?? null;
        if ($f && $now - (int) $f['last_try'] < 12 * 3600) continue;
        $due[] = $e + ['kind' => 'forecast'];
    }
    if (!$due) return 0;

    $updated = 0;
    foreach (array_slice(array_chunk($due, 6), 0, $maxCalls) as $batch) {
        $ny = sai_ny();
        $list = array_map(function ($e) use ($ny) {
            $d = (new DateTime('@' . (int) $e['ts']))->setTimezone($ny);
            return ['id' => $e['id'], 'event' => $e['event'], 'release_et' => $d->format('Y-m-d H:i'), 'need' => $e['kind'] === 'actual' ? 'actual, forecast, previous, revised previous' : 'forecast (consensus) and previous'];
        }, $batch);
        $prompt = "Today is " . sai_today_ny() . " (New York). For each U.S. economic release below, search the web and give the figures exactly as published.\n"
            . "Actual and revisions: from the official source (BLS, BEA, Census, Federal Reserve, ISM, Conference Board, U. of Michigan, ADP, Department of Labor, NAR) or major financial news reporting that release.\n"
            . "Forecast: the market consensus reported before the release (Reuters, Bloomberg, MarketWatch, Investing.com, Trading Economics, Forex Factory).\n"
            . "Write values the way economic calendars do: percentages with %, payrolls/claims in thousands with K (e.g. 142K, 227K), indexes as plain numbers (52.1), FOMC rate as the upper bound with % (4.50%).\n"
            . "If the release has not happened yet or you cannot confirm a figure, use null. Never guess.\n"
            . "Releases: " . json_encode($list, JSON_UNESCAPED_UNICODE) . "\n"
            . 'Return JSON: {"events":[{"id":string,"released":true|false,"actual":string|null,"forecast":string|null,"previous":string|null,"revised_previous":string|null,"source":string|null}]}';
        foreach ($batch as $e) {
            $f = $fill[$e['id']] ?? null;
            if ($f) sai_q($pdo, 'UPDATE econ_fill SET tries = tries + 1, last_try = ?, kind = ? WHERE event_id = ?', [$now, $e['kind'], $e['id']]);
            else sai_q($pdo, 'INSERT INTO econ_fill (event_id, kind, tries, last_try, status) VALUES (?, ?, 1, ?, ?)', [$e['id'], $e['kind'], $now, 'pending']);
        }
        try { $r = eai_call($pdo, 'econ_values', $prompt, 1500); }
        catch (SaiError $x) { error_log('[Sweep AI] econ fill: ' . $x->sai); break; }
        $byId = array_column($batch, null, 'id');
        foreach ((array) ($r['data']['events'] ?? []) as $v) {
            $id = (string) ($v['id'] ?? ''); if (!isset($byId[$id])) continue;
            $e = $byId[$id];
            $set = []; $args = [];
            $act = eai_val($v['actual'] ?? null); $fc = eai_val($v['forecast'] ?? null); $pv = eai_val($v['previous'] ?? null); $rv = eai_val($v['revised_previous'] ?? null);
            if ($e['kind'] === 'actual' && $act !== null && !empty($v['released'])) { $set[] = 'actual = ?'; $args[] = $act; }
            if ($fc !== null && trim((string) $e['forecast']) === '') { $set[] = 'forecast = ?'; $args[] = $fc; }
            if ($pv !== null && trim((string) $e['previous']) === '') { $set[] = 'previous = ?'; $args[] = $pv; }
            if ($rv !== null && $rv !== $pv) { $set[] = 'revised = ?'; $args[] = $rv; }
            if (!$set) continue;
            if ($e['kind'] === 'actual' && $act !== null) { $set[] = "source = 'ai'"; }
            $set[] = 'updated_at = ?'; $args[] = $now;
            $args[] = $id;
            sai_q($pdo, 'UPDATE econ_events SET ' . implode(', ', $set) . ' WHERE id = ?', $args);
            if ($e['kind'] === 'actual' && $act !== null) sai_q($pdo, 'UPDATE econ_fill SET status = ?, sources = ? WHERE event_id = ?', ['done', json_encode($r['sources'], JSON_UNESCAPED_SLASHES), $id]);
            elseif ($e['kind'] === 'forecast') sai_q($pdo, 'UPDATE econ_fill SET sources = ? WHERE event_id = ?', [json_encode($r['sources'], JSON_UNESCAPED_SLASHES), $id]);
            $updated++;
        }
    }
    $pdo->prepare('DELETE FROM app_settings WHERE k = ?')->execute(['econ_ai_lock']);
    return $updated;
}

/** Market impact report for one released event, cached per language. */
function eai_report(PDO $pdo, string $id, string $lang, bool $allowCreate = true): array
{
    eai_schema($pdo);
    $lang = sai_lang($lang);
    $e = sai_q($pdo, 'SELECT id, ts, event, impact, actual, forecast, previous, revised FROM econ_events WHERE id = ?', [$id])->fetch(PDO::FETCH_ASSOC);
    if (!$e) throw new SaiError('not_found', 404);
    $now = time(); $ts = (int) $e['ts'];
    $readyAt = $ts + EAI_REPORT_DELAY;
    $sources = json_decode((string) (sai_q($pdo, 'SELECT sources FROM econ_fill WHERE event_id = ?', [$id])->fetchColumn() ?: '[]'), true) ?: [];
    $row = sai_q($pdo, 'SELECT data, sources, suggest, created_at FROM econ_report WHERE event_id = ? AND lang = ?', [$id, $lang])->fetch(PDO::FETCH_ASSOC);
    $stageNow = $now >= $ts + EAI_REPORT_REFRESH ? 'final' : ($now >= $ts + EAI_REPORT_FULL ? 'full' : 'flash');
    $rank = ['flash' => 1, 'full' => 2, 'final' => 3];
    $have = $row ? (string) ((json_decode($row['data'], true) ?: [])['stage'] ?? 'full') : null;
    // a newer stage is due when the stored one is older than what the clock allows (final only if the full one came early)
    $fresh = $row && ($rank[$have] ?? 2) >= ($rank[$stageNow] ?? 1) || ($row && $have === 'full' && $stageNow === 'final' && (int) $row['created_at'] >= $ts + 2 * 3600);
    if ($row && ($fresh || !$allowCreate)) {
        $data = json_decode($row['data'], true);
        return ['state' => 'ready', 'report' => $data, 'stage' => $data['stage'] ?? 'full', 'sources' => json_decode((string) $row['sources'], true) ?: [], 'suggest' => (string) $row['suggest'],
            'created_at' => (int) $row['created_at'], 'next_at' => ($data['stage'] ?? 'full') === 'flash' ? $ts + EAI_REPORT_FULL : null, 'value_sources' => $sources];
    }
    if ($ts > $now) return ['state' => 'upcoming', 'ready_at' => $readyAt, 'value_sources' => $sources];
    $textual = (bool) preg_match('/minutes|speech|speaks|testimony|press conference|beige book|statement|remarks/i', (string) $e['event']);   // no number is published for these
    if (trim((string) $e['actual']) === '' && !$textual) return ['state' => 'awaiting_actual', 'value_sources' => $sources];
    if ($now < $readyAt) return ['state' => 'waiting', 'ready_at' => $readyAt, 'value_sources' => $sources];
    if (!$allowCreate || !eai_enabled()) return ['state' => 'off', 'value_sources' => $sources];

    $ny = sai_ny();
    $rel = (new DateTime('@' . $ts))->setTimezone($ny)->format('Y-m-d H:i');
    $flash = $stageNow === 'flash';
    $prompt = "U.S. release: " . $e['event'] . " on " . $rel . " New York time. " . ($textual && trim((string) $e['actual']) === '' ? "This is a text release (no headline number): summarise what it said and how markets read it. Forecast " . ($e['forecast'] ?: 'n/a') : "Actual " . $e['actual'] . ", forecast " . ($e['forecast'] ?: 'n/a')) . ", previous " . ($e['previous'] ?: 'n/a')
        . ($e['revised'] ? ' (previous revised to ' . $e['revised'] . ')' : '') . ".\n"
        . ($flash ? "This is a FLASH recap written about one minute after the release: explain what the number says versus expectations and the previous reading, and how this indicator is usually read for the Federal Reserve. "
            . "Market reaction may not be reported yet: fill reaction fields only with moves you actually find in sources (first-minute headlines), otherwise null.\n" : "")
        . "Search the news for how markets reacted to this release on " . substr($rel, 0, 10) . ": Nasdaq-100 futures (NQ), S&P 500 futures (ES), the 10-year Treasury yield and the U.S. dollar, in the minutes and hours after "
        . substr($rel, 11) . " ET, and what analysts said it means for the Federal Reserve. Only report moves you find in sources; use null when you don't know. Keep numbers as reported (%, points, basis points).\n"
        . "This is an after-the-fact market recap for traders, not advice: no predictions, no trade ideas.\n"
        . 'Return JSON: {"headline":string (max 12 words),"verdict":"hotter|cooler|stronger|weaker|in_line|mixed","summary":string (2-3 sentences),'
        . '"vs_expectations":string (1 sentence comparing actual, forecast and previous),"reaction":{"nq":string|null,"es":string|null,"yields":string|null,"dollar":string|null},'
        . '"drivers":[string, max 3],"fed_read":string|null (1 sentence),"what_to_watch":string|null (next related release or level, 1 sentence),"confidence":"high|medium|low"}';
    $r = eai_call($pdo, 'econ_report', $prompt, 1400, $lang);
    $d = $r['data'];
    $clean = fn($v, $n = 400) => sai_str($v, $n);
    $rep = [
        'headline' => $clean($d['headline'] ?? null, 120), 'verdict' => in_array($d['verdict'] ?? '', ['hotter', 'cooler', 'stronger', 'weaker', 'in_line', 'mixed'], true) ? $d['verdict'] : 'mixed',
        'summary' => $clean($d['summary'] ?? null, 700), 'vs_expectations' => $clean($d['vs_expectations'] ?? null),
        'reaction' => ['nq' => $clean($d['reaction']['nq'] ?? null, 240), 'es' => $clean($d['reaction']['es'] ?? null, 240), 'yields' => $clean($d['reaction']['yields'] ?? null, 240), 'dollar' => $clean($d['reaction']['dollar'] ?? null, 240)],
        'drivers' => array_values(array_filter(array_map(fn($x) => $clean($x, 240), array_slice((array) ($d['drivers'] ?? []), 0, 3)))),
        'fed_read' => $clean($d['fed_read'] ?? null, 300), 'what_to_watch' => $clean($d['what_to_watch'] ?? null, 300),
        'confidence' => in_array($d['confidence'] ?? '', ['high', 'medium', 'low'], true) ? $d['confidence'] : 'medium',
        'stage' => $stageNow,
    ];
    sai_q($pdo, 'DELETE FROM econ_report WHERE event_id = ? AND lang = ?', [$id, $lang]);
    sai_q($pdo, 'INSERT INTO econ_report (event_id, lang, data, sources, suggest, created_at) VALUES (?, ?, ?, ?, ?, ?)',
        [$id, $lang, json_encode($rep, JSON_UNESCAPED_UNICODE), json_encode($r['sources'], JSON_UNESCAPED_SLASHES), $r['suggest'], $now]);
    return ['state' => 'ready', 'report' => $rep, 'stage' => $stageNow, 'sources' => $r['sources'], 'suggest' => $r['suggest'], 'created_at' => $now,
        'next_at' => $stageNow === 'flash' ? $ts + EAI_REPORT_FULL : null, 'value_sources' => $sources];
}
