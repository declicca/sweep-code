<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli' && realpath((string) ($_SERVER['SCRIPT_FILENAME'] ?? '')) === realpath(__FILE__)) { http_response_code(404); exit; }
/**
 * Sweep — the check of the prop firm presets, firm by firm. Used by presets/cron.php (weekly) and by the
 * « Check now » button of the admin dashboard (api/admin/presets/check, one firm per request).
 *
 * For every firm, Gemini (with Google Search) reads the firm's own pages and lists every account type sold today:
 * evaluation and funded limits, PAYOUT rules (winning days and minimum per day, cap per request or ladder, payout
 * consistency, safety net / buffer, max number of payouts) and PRICES (evaluation, activation). Then Sweep:
 *   1. validates every number (impossible values never reach a trader);
 *   2. refuses doubtful changes: half the accounts gone, a price or a payout cap that moves by more than half, a ladder
 *      that changes length… The firm goes « to review » and keeps its previous rules — never applied automatically;
 *   3. applies what passes (previous version kept in data/presets-history/) and tells every trader with an active
 *      account at that firm what changes for THEIR account. Their account keeps its rules until they apply the new ones.
 */
require_once __DIR__ . '/presets-lib.php';

const PR_UID = 'system:presets';
const PR_STALE_DAYS = 8;

/** Plain text of a page (for the prompt): scripts, styles and tags removed, whitespace squeezed. */
function pr_fetch_text(string $url): string
{
    if (getenv('SWEEP_PRESETS_MOCK')) return '';
    $ch = curl_init($url);
    curl_setopt_array($ch, [CURLOPT_RETURNTRANSFER => true, CURLOPT_FOLLOWLOCATION => true, CURLOPT_MAXREDIRS => 4, CURLOPT_CONNECTTIMEOUT => 8, CURLOPT_TIMEOUT => 20,
        CURLOPT_USERAGENT => 'Mozilla/5.0 (compatible; SweepPresetsBot/1.0; +https://makeitsweep.com)', CURLOPT_HTTPHEADER => ['Accept-Language: en-US,en;q=0.8']]);
    $html = (string) curl_exec($ch);
    curl_close($ch);
    $html = preg_replace('#<(script|style|noscript|svg)[^>]*>.*?</\1>#is', ' ', $html) ?? '';
    $text = html_entity_decode(strip_tags(preg_replace('#<(br|/p|/li|/tr|/h\d)>#i', "\n", $html) ?? ''), ENT_QUOTES | ENT_HTML5, 'UTF-8');
    return trim(preg_replace("/[ \t]+/", ' ', preg_replace("/\n\s*\n+/", "\n", $text) ?? '') ?? '');
}

/** One grounded Gemini call (Google Search) that returns the firm's catalogue as JSON. */
function pr_ask(PDO $pdo, array $firm, string $pages): array
{
    // tests: SWEEP_PRESETS_MOCK=file.json answers instead of Gemini ({"firm-id": {"programs": [...]}})
    if ($mock = getenv('SWEEP_PRESETS_MOCK')) { $m = json_decode((string) file_get_contents($mock), true); if (!isset($m[$firm['id']])) throw new RuntimeException('no mock answer'); return [$m[$firm['id']], ['mock']]; }
    if (!function_exists('sai_config')) require_once dirname(__DIR__) . '/ai/ai-core.php';
    $cfg = sai_config();
    if (!$cfg['enabled']) throw new RuntimeException('AI is disabled in ai-config.php');
    if (sai_spent_today($pdo) >= (float) $cfg['global_daily_budget_usd']) throw new RuntimeException('daily AI budget reached');
    $current = json_encode(['programs' => array_values(array_filter($firm['programs'], fn($p) => empty($p['legacy'])))], JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    $prompt = "Prop firm: {$firm['name']} (also known as: " . implode(', ', (array) ($firm['aliases'] ?? [])) . ").\n"
        . "Official sites: " . implode(' ', (array) $firm['sources']) . "\n\n"
        . "Task: list EVERY futures account type this firm sells TODAY, with every account size, and for each size the rules of the evaluation, of the funded account, the PAYOUT rules of the funded account and the PRICES.\n"
        . "Use ONLY the firm's own pages (its website, help center, rules, payout policy or pricing pages) found with Google Search or given below. Ignore review, coupon and affiliate sites. "
        . "If a number is not on an official page, use null. Never guess. Amounts in US dollars. Prices are the list prices before any coupon.\n\n"
        . "Return JSON only, exactly this shape:\n"
        . '{"programs":[{"id":"short-slug","name":"Account type name as the firm writes it","direct":false,"sizes":[{"size":50000,'
        . '"eval":{"target":3000,"dd":2000,"dd_type":"eod","dll":1000,"dll_optional":true,"consistency":50,"min_days":2,"max_minis":5},'
        . '"funded":{"dd":2000,"dd_type":"eod","dll":null,"consistency":null,"max_minis":5,'
        . '"payout":{"win_days":5,"win_min":150,"trade_days":null,"split_pct":90,"min":500,"max":2000,"max_dll":null,"max_pct":50,"ladder":null,"min_bal":52100,"max_payouts":null,"cycle_pos":true}},'
        . '"price":{"eval":49,"eval_period":"month","activation":149}}],'
        . '"evidence":[{"url":"https://…official page…","quote":"short sentence from that page"}]}]}' . "\n"
        . "Rules of the fields: dd = maximum loss / drawdown amount; dd_type = \"eod\" (trails the end-of-day balance), \"trade\" (trails in real time / intraday) or \"static\"; "
        . "dll = daily loss limit (null if none); dll_optional = true when the trader chooses at purchase whether the account has that daily loss limit; consistency = the best-day percentage rule (e.g. 50 for 50%), null if none (in \"funded\" it is the payout consistency); min_days = minimum trading days to pass; "
        . "max_minis = maximum mini contracts. For an account sold already funded (no evaluation), set \"direct\": true and \"eval\": null.\n"
        . "Payout fields: win_days = number of winning days required per payout and win_min = the minimum profit for a day to count; trade_days = number of traded days required (any result) when the firm counts days that way; "
        . "min = minimum payout; max = maximum per request; max_dll = maximum per request when the daily loss limit option was taken (null if the same); max_pct = maximum % of the profit or balance per request; "
        . "ladder = list of caps for the 1st, 2nd, 3rd… payout when the cap changes from one payout to the next (null otherwise; null inside the list = no cap); min_bal = the balance that must stay in the account (safety net, buffer zone) minus the minimum payout; "
        . "max_payouts = maximum number of payouts before the account closes or changes; split_pct = the trader's share of a payout in % (e.g. 90); cycle_pos = true when the account must be profitable since the last payout.\n"
        . "Price fields: eval = evaluation price; eval_period = \"month\" (subscription) or \"once\"; activation = fee to activate the funded account (0 when none).\n"
        . "Keep the same \"id\" as today's catalogue when it is the same account type.\n\n"
        . "Today's catalogue in Sweep (to compare, not to copy):\n$current\n\n"
        . ($pages !== '' ? "Text of the official pages (may be partial):\n" . mb_substr($pages, 0, 60000) : '');
    $body = [
        'contents' => [['role' => 'user', 'parts' => [['text' => $prompt]]]],
        'tools' => [['google_search' => (object) []]],
        'systemInstruction' => ['parts' => [['text' => 'You are a careful analyst of futures prop firm rules. You only report what the firm itself publishes, you cite the page, and you answer with JSON only.']]],
        'generationConfig' => ['maxOutputTokens' => 12000, 'temperature' => 0.1],
    ];
    [$status, $raw] = sai_http($cfg, $body);
    if ($status !== 200) throw new RuntimeException("Gemini HTTP $status " . substr((string) $raw, 0, 300));
    $res = json_decode((string) $raw, true);
    $cand = $res['candidates'][0] ?? [];
    $text = '';
    foreach ($cand['content']['parts'] ?? [] as $p) if (isset($p['text']) && empty($p['thought'])) $text .= $p['text'];
    $u = $res['usageMetadata'] ?? [];
    $queries = count((array) ($cand['groundingMetadata']['webSearchQueries'] ?? []));
    $cost = (int) ($u['promptTokenCount'] ?? 0) / 1e6 * (float) $cfg['price_input_per_m'] + ((int) ($u['candidatesTokenCount'] ?? 0) + (int) ($u['thoughtsTokenCount'] ?? 0)) / 1e6 * (float) $cfg['price_output_per_m'] + $queries * (float) ($cfg['search_price_per_query'] ?? 0.014);
    sai_q($pdo, 'INSERT INTO ai_log (user_id, task, input_tokens, output_tokens, cost_usd, created_at) VALUES (?, ?, ?, ?, ?, ?)',
        [PR_UID, 'presets_' . substr($firm['id'], 0, 30), (int) ($u['promptTokenCount'] ?? 0), (int) ($u['candidatesTokenCount'] ?? 0), round($cost, 6), sai_now()]);
    $data = sai_json($text);
    if (!$data || !isset($data['programs']) || !is_array($data['programs'])) throw new RuntimeException('unreadable answer');
    $sources = [];
    foreach ((array) ($cand['groundingMetadata']['groundingChunks'] ?? []) as $ch) if (!empty($ch['web']['uri'])) $sources[] = (string) $ch['web']['uri'];
    return [$data, array_values(array_unique($sources))];
}

/** Clean the answer into the catalogue shape (numbers as numbers, unknown fields dropped). */
function pr_clean_programs(array $programs): array
{
    $num = fn($v) => is_numeric($v) ? 0 + $v : null;
    $payout = function ($po) use ($num) {
        if (!is_array($po)) return null;
        $o = [];
        foreach (['win_days', 'win_min', 'trade_days', 'min', 'max', 'max_dll', 'max_pct', 'min_bal', 'max_payouts', 'cycle_min', 'split_pct'] as $k) if ($num($po[$k] ?? null) !== null) $o[$k] = $num($po[$k]);
        if (isset($po['ladder']) && is_array($po['ladder']) && $po['ladder']) $o['ladder'] = array_map(fn($v) => $num($v), array_slice(array_values($po['ladder']), 0, 20));
        if (!empty($po['cycle_pos'])) $o['cycle_pos'] = true;
        return $o ?: null;
    };
    $phase = function ($p, bool $eval) use ($num, $payout) {
        if (!is_array($p)) return null;
        $o = ['dd' => $num($p['dd'] ?? null), 'dd_type' => in_array($p['dd_type'] ?? '', PR_DD_TYPES, true) ? $p['dd_type'] : null];
        if ($eval) $o['target'] = $num($p['target'] ?? null);
        foreach (['dll', 'consistency', 'max_minis'] as $k) if ($num($p[$k] ?? null) !== null) $o[$k] = $num($p[$k]);
        if (!empty($p['dll_optional']) && isset($o['dll'])) $o['dll_optional'] = true;
        if ($eval && $num($p['min_days'] ?? null) !== null) $o['min_days'] = $num($p['min_days']);
        if (!$eval && ($po = $payout($p['payout'] ?? null))) $o['payout'] = $po;
        return array_filter($o, fn($v) => $v !== null);
    };
    $out = [];
    foreach ($programs as $p) {
        if (!is_array($p) || empty($p['name'])) continue;
        $sizes = [];
        foreach ((array) ($p['sizes'] ?? []) as $s) {
            $size = (int) ($s['size'] ?? 0); if ($size <= 0) continue;
            $row = ['size' => $size];
            if (!empty($s['eval'])) $row['eval'] = $phase($s['eval'], true);
            if (!empty($s['funded'])) $row['funded'] = $phase($s['funded'], false);
            if (!empty($s['price']) && is_array($s['price'])) {
                $pr = array_filter(['eval' => $num($s['price']['eval'] ?? null), 'activation' => $num($s['price']['activation'] ?? null),
                    'eval_period' => in_array($s['price']['eval_period'] ?? '', ['month', 'once'], true) ? $s['price']['eval_period'] : null], fn($v) => $v !== null);
                if (isset($pr['eval']) || isset($pr['activation'])) $row['price'] = $pr + ['checked' => gmdate('Y-m-d')];
            }
            $sizes[] = $row;
        }
        usort($sizes, fn($a, $b) => $a['size'] <=> $b['size']);
        $id = preg_replace('/[^a-z0-9-]+/', '-', strtolower((string) ($p['id'] ?? $p['name']))) ?: 'program';
        $out[] = array_filter(['id' => trim($id, '-'), 'name' => (string) $p['name'], 'direct' => !empty($p['direct']) ?: null, 'sizes' => $sizes,
            'evidence' => array_slice(array_values(array_filter((array) ($p['evidence'] ?? []), fn($e) => is_array($e) && !empty($e['url']))), 0, 4)], fn($v) => $v !== null);
    }
    return $out;
}

/**
 * What the check does not read is carried over from the current catalogue: translated notes, options chosen at
 * purchase and their variants (Topstep « Consistency »), live rules, Legacy account types (no longer sold, so never on
 * today's pages), sources checked by hand. A payout rule or a price the answer does not mention keeps its value
 * (« not found on the page » is not « removed »).
 */
function pr_carry_over(array $old, array $new): array
{
    $byId = []; foreach ($old['programs'] as $p) $byId[$p['id']] = $p;
    foreach ($new['programs'] as &$p) {
        $o = $byId[$p['id']] ?? null; if (!$o) continue;
        foreach (['note', 'label', 'options', 'verified', 'payout_sources'] as $k) if (isset($o[$k])) $p[$k] = $o[$k];
        $oSizes = []; foreach ($o['sizes'] as $s) $oSizes[$s['size']] = $s;
        foreach ($p['sizes'] as &$s) {
            $os = $oSizes[$s['size']] ?? null; if (!$os) continue;
            foreach (['variants', 'live'] as $k) if (isset($os[$k])) $s[$k] = $os[$k];
            if (isset($os['funded']['payout_live']) && isset($s['funded'])) $s['funded']['payout_live'] = $os['funded']['payout_live'];
            if (isset($os['funded']['dd_lock']) && isset($s['funded'])) $s['funded']['dd_lock'] = $os['funded']['dd_lock'];
            if (isset($os['funded']['dd_lock_offset']) && isset($s['funded'])) $s['funded']['dd_lock_offset'] = $os['funded']['dd_lock_offset'];   // Apex: the threshold stops at start + $100
            if (!empty($os['funded']['payout']) && isset($s['funded'])) $s['funded']['payout'] = ($s['funded']['payout'] ?? []) + $os['funded']['payout'];
            if (!empty($os['price'])) $s['price'] = isset($s['price']) ? $s['price'] + $os['price'] : $os['price'];
        }
        unset($s);
    }
    unset($p);
    foreach ($old['programs'] as $p) if (!empty($p['legacy'])) $new['programs'][] = $p;   // never sold any more: kept as is
    return $new;
}

/** Changes too big to be trusted from one reading: the firm goes « to review », nothing is applied. */
function pr_doubtful(array $old, array $new): array
{
    $e = [];
    $idx = function (array $f) { $o = []; foreach ((array) $f['programs'] as $p) foreach ((array) $p['sizes'] as $s) $o[$p['id'] . ' ' . ((int) $s['size'] / 1000) . 'K'] = $s; return $o; };
    $a = $idx($old); $b = $idx($new);
    $jump = fn($x, $y) => is_numeric($x) && is_numeric($y) && $x > 0 && abs($y - $x) / $x > 0.5;
    foreach ($b as $k => $s) {
        if (!isset($a[$k])) continue;
        $po = (array) ($a[$k]['funded']['payout'] ?? []); $pn = (array) ($s['funded']['payout'] ?? []);
        foreach (['min', 'max', 'max_dll', 'min_bal', 'win_min'] as $f) if ($jump($po[$f] ?? null, $pn[$f] ?? null)) $e[] = "$k payout $f {$po[$f]} → {$pn[$f]} (more than half): to review";
        foreach (['win_days', 'trade_days', 'max_payouts'] as $f) if (isset($po[$f], $pn[$f]) && abs($pn[$f] - $po[$f]) > 3) $e[] = "$k payout $f {$po[$f]} → {$pn[$f]}: to review";
        if (isset($po['ladder'], $pn['ladder']) && count((array) $po['ladder']) !== count((array) $pn['ladder'])) $e[] = "$k payout ladder changes length: to review";
        foreach (['eval', 'funded'] as $ph) { $x = $a[$k][$ph]['consistency'] ?? null; $y = $s[$ph]['consistency'] ?? null; if (is_numeric($x) && is_numeric($y) && abs($y - $x) > 20) $e[] = "$k $ph consistency $x → $y: to review"; }
        foreach (['eval', 'activation'] as $f) { $x = $a[$k]['price'][$f] ?? null; $y = $s['price'][$f] ?? null; if ($jump($x, $y)) $e[] = "$k price $f $x → $y (more than half): to review"; }
    }
    return $e;
}

/** Check one firm. Returns the status line and the new firm (null when nothing is to be applied). */
function pr_check_firm(PDO $pdo, array $firm): array
{
    $st = ['checked_at' => gmdate('c'), 'status' => 'unchanged', 'changes' => [], 'errors' => [], 'sources' => [], 'name' => $firm['name']];
    try {
        $pages = '';
        foreach (array_slice((array) $firm['sources'], 0, 3) as $u) { $t = pr_fetch_text($u); if ($t !== '') $pages .= "\n--- $u ---\n" . mb_substr($t, 0, 25000); }
        [$answer, $sources] = pr_ask($pdo, $firm, $pages);
        $st['sources'] = array_slice($sources, 0, 8);
        $new = $firm; $new['programs'] = pr_clean_programs((array) $answer['programs']);
        $read = count($new['programs']);
        $new = pr_carry_over($firm, $new);
        $errors = pr_validate_firm($new);
        $oldCount = array_sum(array_map(fn($p) => empty($p['legacy']) ? count($p['sizes'] ?? []) : 0, $firm['programs']));
        $newCount = array_sum(array_map(fn($p) => empty($p['legacy']) ? count($p['sizes'] ?? []) : 0, $new['programs']));
        if (!$read) $errors[] = 'no account found on the official pages';
        if ($oldCount > 0 && $newCount < $oldCount / 2) $errors[] = "only $newCount accounts found (was $oldCount): kept the previous rules, to review";
        $errors = array_merge($errors, pr_doubtful($firm, $new));
        $diff = pr_diff_firm($firm, $new);
        if ($errors) { $st['status'] = 'review'; $st['errors'] = array_slice($errors, 0, 12); $st['changes'] = array_slice($diff, 0, 40); return [$st, null]; }
        if ($diff) { $st['status'] = 'updated'; $st['changes'] = array_slice($diff, 0, 40); return [$st, $new]; }
    } catch (Throwable $e) {
        $st['status'] = 'error'; $st['errors'] = [$e->getMessage()];
    }
    return [$st, null];
}

/**
 * The firm changed: every trader with an active account at that firm (made from its preset) gets one notification
 * that says what changes for THEIR account. The account itself is not touched: « Apply the new rules » on its page.
 * Returns the number of notifications sent.
 */
function pr_notify_changes(PDO $pdo, array $oldCat, array $newCat, string $firmId): int
{
    if (!class_exists('Notify')) {
        $root = dirname(__DIR__);
        foreach (['/notify/notify.php', '/notify/listeners.php'] as $f) if (is_file($root . $f)) require_once $root . $f;
        if (!class_exists('Notify')) return 0;
    }
    $sent = 0; $firmName = $firmId;
    foreach ((array) $newCat['firms'] as $f) if ($f['id'] === $firmId) $firmName = $f['name'];
    $st = $pdo->prepare("SELECT user_id, id, data FROM documents WHERE collection = 'accounts' AND data LIKE ?");
    $st->execute(['%"preset":"' . str_replace(['%', '_'], ['\%', '\_'], $firmId) . '|%']);
    foreach ($st->fetchAll(PDO::FETCH_ASSOC) as $r) {
        $a = json_decode((string) $r['data'], true);
        if (!is_array($a) || !empty($a['demo']) || in_array($a['status'] ?? 'active', ['archived', 'closed', 'breached'], true)) continue;
        $pv = (string) ($a['preset'] ?? ''); if (strpos($pv, $firmId . '|') !== 0) continue;
        $before = pr_rules_of($oldCat, $pv); $after = pr_rules_of($newCat, $pv);
        if (!$before || !$after) continue;
        $diff = pr_rules_diff($before['rules'], $after['rules']);
        if (!$diff) continue;
        $params = ['firm' => $firmName, 'account' => (string) ($a['name'] ?? $after['name']), 'n' => count($diff),
            'changes' => pr_describe($diff, 'en'), 'changes_fr' => pr_describe($diff, 'fr'), 'changes_es' => pr_describe($diff, 'es')];
        if (Notify::send((string) $r['user_id'], 'rules_changed', $params, ['dedupe_key' => 'rules:' . $r['id'] . ':' . ($newCat['version'] ?? gmdate('Y-m-d')) . ':' . substr(md5(json_encode($after['rules'])), 0, 8),
            'action_url' => '#account/' . $r['id'], 'category' => 'prop_alerts'])) $sent++;
    }
    return $sent;
}

/** Apply one firm's result to the catalogue and the status (saved at once). */
function pr_apply(PDO $pdo, string $firmId, array $st, ?array $new, bool $dry = false): array
{
    $cat = pr_current(); $status = pr_status();
    $seed = pr_read(pr_seed_path());
    if ($new && !$dry) {
        $old = $cat;
        foreach ($cat['firms'] as $i => $f) if ($f['id'] === $firmId) $cat['firms'][$i] = $new;
        $cat['version'] = gmdate('Y-m-d-His'); $cat['checked_at'] = gmdate('c');
        $cat['origin'] = 'weekly check of the official pages'; $cat['seed_version'] = $seed['version'] ?? null;
        pr_save($cat);
        try { $st['notified'] = pr_notify_changes($pdo, $old, pr_current(), $firmId); }
        catch (Throwable $e) { $st['notified'] = 0; $st['errors'][] = 'notifications not sent: ' . $e->getMessage(); error_log('Sweep presets notify: ' . $e->getMessage()); }
    }
    if (!$dry) { $status['firms'][$firmId] = $st; pr_save_status($status); }
    return $st;
}

/** End of a full run (cron, or the last firm of « Check now »): the date the admin sees and the 8-day alert rely on. */
function pr_finish_run(string $by = 'cron'): void
{
    $status = pr_status(); $status['last_run'] = gmdate('c'); $status['last_run_by'] = $by; pr_save_status($status);
    $cat = pr_current();
    if (is_file(pr_live_path()) && ($cat['origin'] ?? '') !== '' && strpos((string) $cat['origin'], 'seed') !== 0) { $cat['checked_at'] = gmdate('c'); pr_save($cat); }
}

/* ───────────── admin view + 8-day alert ───────────── */

function pr_watch_path(): string { return pr_data_dir() . '/presets-watchdog.json'; }

/** For the admin block: last check, per-firm status, whether it is late (no full check for 8 days). */
function pr_admin_summary(?int $now = null): array
{
    $now = $now ?? time();
    $status = pr_status(); $cat = pr_current();
    $last = $status['last_run'] ?? null; $ts = $last ? strtotime((string) $last) : 0;
    $days = $ts ? (int) floor(($now - $ts) / 86400) : null;
    $w = is_file(pr_watch_path()) ? (json_decode((string) file_get_contents(pr_watch_path()), true) ?: []) : [];
    $firms = [];
    foreach ((array) $cat['firms'] as $f) {
        $s = $status['firms'][$f['id']] ?? null;
        $firms[] = ['id' => $f['id'], 'name' => $f['name'], 'programs' => count($f['programs'] ?? []), 'status' => $s['status'] ?? 'never', 'checked_at' => $s['checked_at'] ?? null,
            'changes' => array_slice((array) ($s['changes'] ?? []), 0, 12), 'errors' => array_slice((array) ($s['errors'] ?? []), 0, 6), 'notified' => $s['notified'] ?? null];
    }
    return ['last_run' => $last, 'last_run_by' => $status['last_run_by'] ?? null, 'days_since' => $days, 'stale' => !$ts || ($now - $ts) > PR_STALE_DAYS * 86400,
        'stale_days' => PR_STALE_DAYS, 'version' => $cat['version'] ?? '', 'origin' => $cat['origin'] ?? '', 'alert_mailed_at' => $w['mailed_at'] ?? null, 'firms' => $firms];
}

/**
 * No full check for 8 days → an email to the support address (at most once a day). Called by the app itself
 * (api.php, throttled to once an hour), so it works even when the cron job is the thing that stopped.
 * $send(subject, text) returns true when the email left.
 */
function pr_watchdog(callable $send, ?int $now = null): ?string
{
    $now = $now ?? time();
    $p = pr_watch_path();
    $w = is_file($p) ? (json_decode((string) file_get_contents($p), true) ?: []) : [];
    if (($w['looked_at'] ?? 0) > $now - 3600) return null;
    $w['looked_at'] = $now;
    $sum = pr_admin_summary($now);
    $out = null;
    if ($sum['stale'] && (strtotime((string) ($w['mailed_at'] ?? '')) ?: 0) < $now - 86400) {
        $since = $sum['last_run'] ? gmdate('Y-m-d H:i', strtotime($sum['last_run'])) . ' UTC' : 'never';
        $text = "The weekly check of the prop firm presets has not run for more than " . PR_STALE_DAYS . " days (last full check: $since).\n\n"
            . "Traders may be using outdated rules.\n\n"
            . "1. cPanel → Cron Jobs: check the line  0 5 * * 1  /usr/local/bin/php /home/matnsabc/app.makeitsweep.com/presets/cron.php\n"
            . "2. Run it once in the cPanel terminal and read what it prints.\n"
            . "3. Or open the app → Admin → Presets → « Check now ».\n\n— Sweep";
        if ($send('Sweep — prop firm presets not checked for ' . PR_STALE_DAYS . ' days', $text)) { $w['mailed_at'] = gmdate('c', $now); $out = 'mailed'; } else $out = 'mail_failed';
    }
    @file_put_contents($p, json_encode($w));
    return $out;
}
