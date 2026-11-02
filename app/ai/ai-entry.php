<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli' && realpath((string) ($_SERVER['SCRIPT_FILENAME'] ?? '')) === realpath(__FILE__)) { http_response_code(404); exit; }
/**
 * Sweep AI — a trade from one sentence (brief « avance », step 3: log a trade in under 10 seconds).
 *   « long NQ 2 contracts +$400 », « short ES 1 lot stopped -$250 at 9:42 »
 * 1. A plain sentence is read here, without AI (no call, no quota): every word must be understood, else step 2.
 * 2. Otherwise one Sweep AI call (task « trade_entry ») with a strict JSON answer: account, instrument, side, contracts,
 *    entry, exit, P&L, time, date, and a confidence per field. The answer is checked field by field (sai_entry_clean):
 *    a wrong type is dropped, never guessed.
 * Nothing is saved here: the result only fills the add-trade sheet; the trader checks it and taps « Save ».
 * The screenshot side of the same field uses the existing reader (api/ai/import, mode « shot »).
 * Quotas (billing on): « ai_entry », per New York month — Free 10, Pro 150, Elite unlimited within the day's AI budget
 * (sb_with_entry, sb_ai_consume, billing/billing-core.php). Tests: tests/ai_entry_test.php, tests/e2e_ai_entry.py.
 */

const SAI_ENTRY_FIELDS = ['account_id', 'instrument', 'direction', 'contracts', 'entry', 'exit', 'pnl_c', 'time', 'date'];
const SAI_ENTRY_LOW = 0.7;   // under this confidence the sheet highlights the field
const SAI_ENTRY_SHAPE = '{"account":string|null,"instrument":string|null,"direction":"long"|"short"|null,"contracts":integer|null,'
    . '"entry":number|null,"exit":number|null,"pnl_usd":number|null,"time":"HH:MM"|null,"date":"YYYY-MM-DD"|null,'
    . '"confidence":{"account":number,"instrument":number,"direction":number,"contracts":number,"entry":number,"exit":number,"pnl_usd":number,"time":number,"date":number}}';

/** Gemini's response schema: the same shape, enforced by the provider (sai_call retries once without it if refused). */
function sai_entry_schema(): array
{
    $n = fn(string $t) => ['type' => $t, 'nullable' => true];
    $keys = ['account', 'instrument', 'direction', 'contracts', 'entry', 'exit', 'pnl_usd', 'time', 'date'];
    return ['type' => 'OBJECT', 'properties' => [
        'account' => $n('STRING'), 'instrument' => $n('STRING'), 'direction' => ['type' => 'STRING', 'enum' => ['long', 'short'], 'nullable' => true],
        'contracts' => $n('INTEGER'), 'entry' => $n('NUMBER'), 'exit' => $n('NUMBER'), 'pnl_usd' => $n('NUMBER'), 'time' => $n('STRING'), 'date' => $n('STRING'),
        'confidence' => ['type' => 'OBJECT', 'properties' => array_fill_keys($keys, ['type' => 'NUMBER']), 'required' => $keys],
    ], 'required' => array_merge($keys, ['confidence'])];
}

function sai_entry(PDO $pdo, string $uid, string $text, string $lang): array
{
    $text = trim(preg_replace('/\s+/u', ' ', $text) ?? '');
    if ($text === '' || mb_strlen($text) > 300) throw new SaiError('bad_input', 400);
    $ctx = sai_trade_context($pdo, $uid);
    $local = sai_entry_local($text, $ctx);
    if ($local !== null) return sai_entry_result($local, $ctx, 'local');
    $cfg = sai_config();
    if (!$cfg['enabled']) {   // Sweep AI off: what the sentence plainly says, every field to check
        $part = sai_entry_local($text, $ctx, true);
        if ($part !== null) return sai_entry_result($part, $ctx, 'partial');
        throw new SaiError('disabled', 503);
    }
    $names = array_map(fn($a) => trim($a['name'] . ($a['firm'] ? ' (' . $a['firm'] . ')' : '')), $ctx['accounts']);
    $prompt = "Read ONE futures trade from this trader's sentence (it may be in English, French or Spanish).\n"
        . "Today (New York trading day) is " . sai_today_ny() . ". Times are 24h New York time.\n"
        . "Known accounts: " . json_encode($names, JSON_UNESCAPED_UNICODE) . ". Put in \"account\" the exact name of the one the trader names, else null.\n"
        . "Rules: direction is long or short (buy = long, sell = short). contracts = the number of contracts or lots. "
        . "pnl_usd = the result in US dollars as written; a loss is negative (\"stopped\" or \"lost\" without a sign is a loss). "
        . "A result in points or ticks is NOT pnl_usd: leave pnl_usd null. time = the entry time as HH:MM (24h; 2:15 pm = 14:15). "
        . "entry and exit = prices, only when written. date only when the trader says a day (\"yesterday\", \"Monday\"). "
        . "Never guess: a value that is not in the sentence is null.\n"
        . "confidence: for every field a number from 0 to 1 — 1 when written plainly, about 0.5 when you inferred it, 0 when it is null.\n"
        . "Return only JSON shaped exactly like: " . SAI_ENTRY_SHAPE . "\n\nTrader sentence:\n\"\"\"\n" . $text . "\n\"\"\"";
    $r = sai_call($pdo, $uid, 'trade_entry', $prompt, ['system' => sai_system($lang), 'max_tokens' => 400, 'temperature' => 0, 'schema' => sai_entry_schema()]);
    try { $clean = sai_entry_clean((array) $r['data'], $ctx); }
    catch (SaiError $e) {   // an answer that is not the shape asked: the use is given back, as for a provider error
        if (sai_billing() && !($r['cached'] ?? false)) sb_ai_refund($pdo, $uid, 'entry');
        throw $e;
    }
    return sai_entry_result($clean, $ctx, 'ai') + ['cached' => $r['cached'] ?? false];
}

/** [fields, confidence] → what the sheet needs: the values, their confidence, the ones to highlight, whether to ask the account */
function sai_entry_result(array $x, array $ctx, string $source): array
{
    [$f, $c] = $x;
    $low = [];
    foreach ($f as $k => $v) if ($v !== null && ($c[$k] ?? 0) < SAI_ENTRY_LOW) $low[] = $k;
    $missing = array_values(array_filter(['direction', 'pnl_c'], fn($k) => $f[$k] === null && !($k === 'pnl_c' && $f['entry'] !== null && $f['exit'] !== null)));
    return ['source' => $source, 'trade' => $f, 'confidence' => $c, 'low' => $low, 'missing' => $missing,
        // several accounts and none named: the sheet asks (copy groups will be offered there too, see shotForm in src/nav.js)
        'ask_account' => $f['account_id'] === null && count($ctx['accounts']) > 1];
}

function sai_entry_blank(): array
{
    return [array_fill_keys(SAI_ENTRY_FIELDS, null), array_fill_keys(SAI_ENTRY_FIELDS, null)];
}

/** an instrument as written (NQ, nqz6, MNQH7) → its root when Sweep knows it, else the symbol (confidence capped by the caller) */
function sai_entry_root(string $s): array
{
    $s = strtoupper(preg_replace('/[^A-Za-z0-9]/', '', $s) ?? '');
    if ($s === '') return [null, false];
    $roots = array_keys(SAI_INSTRUMENTS);
    usort($roots, fn($a, $b) => strlen($b) <=> strlen($a));
    foreach ($roots as $r) if ($s === $r || preg_match('/^' . preg_quote($r, '/') . '[FGHJKMNQUVXZ]\d{1,2}$/', $s)) return [$r, true];
    return [preg_match('/^[A-Z0-9]{1,6}$/', $s) ? $s : null, false];
}

/** the account the words name: [id, the name found] when exactly one matches, [null, null] otherwise */
function sai_entry_account(string $lower, array $ctx): array
{
    $hit = [];
    foreach ($ctx['accounts'] as $a) {
        $n = mb_strtolower(trim((string) $a['name']));
        if (mb_strlen($n) >= 3 && str_contains($lower, $n)) $hit[$a['id']] = $n;
    }
    if (count($hit) !== 1) return [null, null];
    return [array_key_first($hit), reset($hit)];
}

/**
 * The sentence read without AI. Returns [fields, confidence] when every word is understood and it gives a side and a
 * result (a P&L, or entry and exit prices); null otherwise (→ Sweep AI). $partial: what can be read even with other words.
 */
function sai_entry_local(string $text, array $ctx, bool $partial = false): ?array
{
    [$f, $c] = sai_entry_blank();
    $s = ' ' . mb_strtolower($text) . ' ';
    $s = str_replace(["\u{2212}", '–', '—', "\u{00a0}", "\u{202f}", '’', '€'], ['-', '-', '-', ' ', ' ', "'", '$'], $s);
    $ctx['_orig'] = $text;
    // the account named in the sentence (its name may hold digits: taken out first)
    [$acc, $name] = sai_entry_account($s, $ctx);
    if ($acc !== null) { $f['account_id'] = $acc; $c['account_id'] = 1.0; $s = str_replace($name, ' ', $s); }
    elseif (count($ctx['accounts']) === 1) { $f['account_id'] = $ctx['accounts'][0]['id']; $c['account_id'] = 1.0; }
    $num = function (string $v): float {
        $v = str_replace(' ', '', $v);
        if (preg_match('/^\d{1,3}(,\d{3})+(\.\d+)?$/', $v)) $v = str_replace(',', '', $v);   // 1,200.50
        return (float) str_replace(',', '.', $v);   // 21000,5 (French decimals)
    };
    // the time: « at 9:42 », « 9h42 », « 2:15 pm », « 14:05 »
    if (preg_match_all('/(?:\b(?:at|@|à|a las|a la|vers|around|hacia)\s*)?(?<![\d.,:])([01]?\d|2[0-3])\s*(?::|h)\s*([0-5]\d)(?:\s*(am|pm|a\.m\.|p\.m\.))?(?![\d])/u', $s, $m, PREG_SET_ORDER)) {
        if (count($m) > 1) return $partial ? sai_entry_local_tail($f, $c, $s, $ctx, $num, true) : null;   // two times (entry and exit): the AI reads them
        $h = (int) $m[0][1]; $ap = str_replace('.', '', $m[0][3] ?? '');
        if ($ap === 'pm' && $h < 12) $h += 12;
        if ($ap === 'am' && $h === 12) $h = 0;
        $f['time'] = sprintf('%02d:%02d', $h, (int) $m[0][2]);
        $c['time'] = $ap === '' && $h >= 1 && $h <= 7 ? 0.6 : 1.0;   // « at 2:15 »: 2:15 or 14:15? to check
        $s = str_replace($m[0][0], ' ', $s);
    }
    return sai_entry_local_tail($f, $c, $s, $ctx, $num, $partial);
}

function sai_entry_local_tail(array $f, array $c, string $s, array $ctx, callable $num, bool $partial): ?array
{
    $unknown = false;
    $N = '(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:[.,]\d+)?)';
    // the prices: « from 21000 to 21010 », « 21000 -> 21010 », « in 21000 out 21010 »
    if (preg_match('/\b(?:from|de|desde|in|entry|entrée|entree|entrada|entré)\s+' . $N . '\s+(?:to|à|a|hasta|out|exit|sortie|salida|sorti)\s+' . $N . '/u', $s, $m)
        || preg_match('/(?<![\w$])' . $N . '\s*(?:->|→|=>|>)\s*' . $N . '(?![\w$])/u', $s, $m)) {
        $f['entry'] = $num($m[1]); $f['exit'] = $num($m[2]); $c['entry'] = $c['exit'] = 1.0;
        $s = str_replace($m[0], ' ', $s);
    }
    // the result in dollars: a sign or a $ (or usd) is needed; « +$400 », « -250$ », « $1,200 », « +400 »
    if (preg_match_all('/(?<![\w.,])([+-])?\s*(\$)?\s*' . $N . '\s*(\$|usd|dollars?|dólares)?(?![\w])/u', $s, $m, PREG_SET_ORDER)) {
        $hits = array_values(array_filter($m, fn($x) => ($x[1] ?? '') !== '' || ($x[2] ?? '') !== '' || ($x[4] ?? '') !== ''));
        if (count($hits) > 1) { if (!$partial) return null; $hits = []; }
        if ($hits) {
            $x = $hits[0]; $v = $num($x[3]);
            $loss = (bool) preg_match('/\b(stopp?ed|stop|sl|loss|lost|lose|perte|perdu|perdant|pérdida|perdí|perdida)\b/u', $s);
            $win = (bool) preg_match('/\b(tp|target|win|won|profit|gain|gagné|gagnant|ganancia|gané)\b/u', $s);
            if ($x[1] === '-') { $f['pnl_c'] = -(int) round($v * 100); $c['pnl_c'] = 1.0; }
            elseif ($x[1] === '+') { $f['pnl_c'] = (int) round($v * 100); $c['pnl_c'] = 1.0; }
            else { $f['pnl_c'] = (int) round($v * 100) * ($loss && !$win ? -1 : 1); $c['pnl_c'] = ($loss xor $win) ? 0.9 : 0.6; }   // no sign: from the words, else to check
            $s = str_replace($x[0], ' ', $s);
        }
    }
    // the contracts: « 2 contracts », « 1 lot », « x2 », « 3 cts »
    if (preg_match('/\b(\d{1,3})\s*(?:contracts?|contrats?|contratos?|cts?|lots?|lotes?|x)(?![\w])/u', $s, $m) || preg_match('/(?<![\w])x\s*(\d{1,3})\b/u', $s, $m)) {
        $f['contracts'] = max(1, (int) $m[1]); $c['contracts'] = 1.0;
        $s = str_replace($m[0], ' ', $s);
    }
    $DIR = ['long' => 'long', 'buy' => 'long', 'bought' => 'long', 'achat' => 'long', 'acheté' => 'long', 'achete' => 'long', 'compra' => 'long', 'compré' => 'long', 'largo' => 'long',
        'short' => 'short', 'sell' => 'short', 'sold' => 'short', 'vente' => 'short', 'vendu' => 'short', 'venta' => 'short', 'vendí' => 'short', 'corto' => 'short'];
    $FILL = ['stopped', 'stoped', 'stop', 'sl', 'tp', 'target', 'hit', 'at', 'à', 'a', '@', 'for', 'pour', 'por', 'on', 'sur', 'en', 'in', 'out', 'trade', 'and', 'et', 'y', 'with', 'avec', 'con',
        'de', 'du', 'el', 'la', 'le', 'un', 'une', 'una', 'uno', 'one', 'net', 'p&l', 'pnl', 'win', 'won', 'loss', 'lost', 'profit', 'gain', 'perte', 'perdu', 'gagné', 'ganancia', 'pérdida', 'perdí', 'gané',
        'today', "aujourd'hui", 'hoy', 'contract', 'contracts', 'contrat', 'contrats', 'contrato', 'contratos', 'lot', 'lots', 'cts', 'ct', 'position', 'took', 'took a', 'pris', 'tomé', 'got', 'fait', 'hice', 'ma', 'mon', 'mi', 'my', 'i', 'je', "j'ai", 'yo', 'went', 'was', 'took', '-', '+', '$', 'me', 'have', 'had'];
    $toks = preg_split('/[\s,;!?()\[\]]+|\.(?!\d)/u', trim($s), -1, PREG_SPLIT_NO_EMPTY) ?: [];
    $dirs = [];
    foreach ($toks as $i => $w) {
        $w = trim($w, ".:'\"");
        if ($w === '') continue;
        if (isset($DIR[$w])) { $dirs[$DIR[$w]] = 1; continue; }
        [$root, $known] = sai_entry_root($w);
        // « es », « si » are also words (Spanish, French): the symbol only when written in capitals
        if ($known && in_array($w, ['es', 'si'], true) && !preg_match('/(?<![A-Za-z])' . strtoupper($w) . '(?![A-Za-z])/', (string) ($ctx['_orig'] ?? ''))) $known = false;
        if ($known) {
            if ($f['instrument'] !== null && $f['instrument'] !== $root) { if (!$partial) return null; continue; }
            $f['instrument'] = $root; $c['instrument'] = 1.0;
            $prev = $toks[$i - 1] ?? '';   // « long 2 NQ »: the number right before the symbol
            if ($f['contracts'] === null && preg_match('/^\d{1,3}$/', $prev)) { $f['contracts'] = max(1, (int) $prev); $c['contracts'] = 1.0; $toks[$i - 1] = ''; }
            continue;
        }
        if (in_array($w, $FILL, true)) continue;
        if (preg_match('/^\d{1,3}$/', $w) && isset($toks[$i + 1]) && sai_entry_root(trim($toks[$i + 1], ".:'\""))[1]) continue;   // read with the symbol
        $unknown = true;
    }
    if (count($dirs) === 1) { $f['direction'] = array_key_first($dirs); $c['direction'] = 1.0; }
    elseif (count($dirs) > 1 && !$partial) return null;
    $result = $f['pnl_c'] !== null || ($f['entry'] !== null && $f['exit'] !== null);
    if ($partial) {
        if ($f['direction'] === null && !$result && $f['instrument'] === null) return null;
        foreach ($c as $k => $v) if ($v !== null && $k !== 'account_id') $c[$k] = min($v, 0.5);   // other words not understood: everything to check
        return [$f, $c];
    }
    if ($unknown || $f['direction'] === null || !$result) return null;
    return [$f, $c];
}

/** The AI's answer checked field by field (strict): a wrong type → the field is dropped; not an object → bad_output. */
function sai_entry_clean(array $d, array $ctx): array
{
    if ($d === [] || array_is_list($d)) throw new SaiError('bad_output', 502);
    $keys = ['account', 'instrument', 'direction', 'contracts', 'entry', 'exit', 'pnl_usd', 'time', 'date'];
    if (!array_intersect($keys, array_keys($d))) throw new SaiError('bad_output', 502);
    [$f, $c] = sai_entry_blank();
    $conf = is_array($d['confidence'] ?? null) && !array_is_list($d['confidence']) ? $d['confidence'] : [];
    $cv = function (string $k) use ($conf): float {
        $v = $conf[$k] ?? null;
        if (!is_int($v) && !is_float($v)) return 0.5;   // no confidence given for a value: to check
        $v = (float) $v;
        if ($v > 1 && $v <= 100) $v /= 100;   // 90 → 0.9
        return max(0.0, min(1.0, $v));
    };
    $isNum = fn($v) => (is_int($v) || is_float($v) || (is_string($v) && is_numeric(trim($v)))) && is_finite((float) $v);
    if (is_string($d['account'] ?? null) && trim($d['account']) !== '') {
        $h = mb_strtolower(trim($d['account']));
        $hit = [];
        foreach ($ctx['accounts'] as $a) { $n = mb_strtolower(trim((string) $a['name'])); $nf = mb_strtolower(trim($a['name'] . ($a['firm'] ? ' (' . $a['firm'] . ')' : ''))); if ($n !== '' && ($h === $n || $h === $nf || str_contains($h, $n))) $hit[$a['id']] = 1; }
        if (count($hit) === 1) { $f['account_id'] = (string) array_key_first($hit); $c['account_id'] = $cv('account'); }
    }
    if ($f['account_id'] === null && count($ctx['accounts']) === 1) { $f['account_id'] = $ctx['accounts'][0]['id']; $c['account_id'] = 1.0; }
    if (is_string($d['instrument'] ?? null)) {
        [$root, $known] = sai_entry_root($d['instrument']);
        if ($root !== null) { $f['instrument'] = $root; $c['instrument'] = $known ? $cv('instrument') : min(0.5, $cv('instrument')); }
    }
    $dir = is_string($d['direction'] ?? null) ? strtolower(trim($d['direction'])) : '';
    $dir = ['buy' => 'long', 'sell' => 'short'][$dir] ?? $dir;
    if (in_array($dir, ['long', 'short'], true)) { $f['direction'] = $dir; $c['direction'] = $cv('direction'); }
    if ($isNum($d['contracts'] ?? null) && (float) $d['contracts'] == (int) $d['contracts'] && (int) $d['contracts'] >= 1 && (int) $d['contracts'] <= 999) { $f['contracts'] = (int) $d['contracts']; $c['contracts'] = $cv('contracts'); }
    foreach (['entry', 'exit'] as $k) if ($isNum($d[$k] ?? null) && (float) $d[$k] > 0 && (float) $d[$k] < 1e7) { $f[$k] = (float) $d[$k]; $c[$k] = $cv($k); }
    if ($isNum($d['pnl_usd'] ?? null) && abs((float) $d['pnl_usd']) < 1e7) { $f['pnl_c'] = (int) round((float) $d['pnl_usd'] * 100); $c['pnl_c'] = $cv('pnl_usd'); }
    if (is_string($d['time'] ?? null) && preg_match('/^([01]?\d|2[0-3]):([0-5]\d)(?::[0-5]\d)?$/', trim($d['time']), $m)) { $f['time'] = sprintf('%02d:%s', (int) $m[1], $m[2]); $c['time'] = $cv('time'); }
    if (is_string($d['date'] ?? null) && preg_match('/^\d{4}-\d{2}-\d{2}$/', $d['date'])) {
        $dt = DateTime::createFromFormat('!Y-m-d', $d['date'], sai_ny()); $today = new DateTime(sai_today_ny(), sai_ny());
        if ($dt && $dt->format('Y-m-d') === $d['date'] && $dt <= (clone $today)->modify('+1 day') && $dt >= (clone $today)->modify('-370 days')) { $f['date'] = $d['date']; $c['date'] = $cv('date'); }
    }
    return [$f, $c];
}
