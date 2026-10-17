<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli' && realpath((string) ($_SERVER['SCRIPT_FILENAME'] ?? '')) === realpath(__FILE__)) { http_response_code(404); exit; }
/**
 * Sweep — the public discipline profile (brief 02 part 12): optional, OFF by default, on a personal link
 * (/p/<random id>, never the username, which can come from the email). It shows the last 4 weeks of discipline only:
 * the discipline score (the share of trades without a mistake, by the coach's rules), days swept, days traded, the current streak, week by week.
 * Never an amount, an instrument, an account or a firm. « Verified » only when every trade of those weeks came from a
 * platform sync (NinjaTrader 8, Quantower), as the server knows it (table sync_trades, written by the sync only: the
 * trader cannot set it). Turned off: the link answers « not public » at once. Account deleted: the profile goes too.
 *
 *   GET  api/profile/public          {on, url}
 *   POST api/profile/public {on}     turns it on (the link is made once and kept) or off
 *   GET  /p/<id>                     the public page, noindex, preview tags (Discord, X, iMessage)
 */

const PP_PLATFORMS = ['ninjatrader' => 'NinjaTrader 8', 'quantower' => 'Quantower'];

function pp_table(PDO $pdo): void
{
    static $done = false;
    if ($done) return;
    $pdo->exec('CREATE TABLE IF NOT EXISTS public_profiles (user_id VARCHAR(120) NOT NULL PRIMARY KEY, slug VARCHAR(32) NOT NULL UNIQUE, enabled INT NOT NULL DEFAULT 0, created_at INT NOT NULL, updated_at INT NOT NULL, views INT NOT NULL DEFAULT 0)');
    $done = true;
}

function pp_q(PDO $pdo, string $sql, array $a = []): PDOStatement { pp_table($pdo); $st = $pdo->prepare($sql); $st->execute($a); return $st; }

function pp_state(PDO $pdo, string $uid): array
{
    $r = pp_q($pdo, 'SELECT slug, enabled FROM public_profiles WHERE user_id = ?', [$uid])->fetch(PDO::FETCH_ASSOC);
    $on = $r && (int) $r['enabled'] === 1;
    return ['on' => $on, 'url' => $on ? '/p/' . $r['slug'] : null];
}

/** on: the link is made the first time and kept (the same link when turned on again); off: the page stops at once */
function pp_set(PDO $pdo, string $uid, bool $on): array
{
    $r = pp_q($pdo, 'SELECT slug FROM public_profiles WHERE user_id = ?', [$uid])->fetchColumn();
    if ($r === false) {
        if (!$on) return pp_state($pdo, $uid);
        $a = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789'; $slug = '';
        for ($i = 0; $i < 14; $i++) $slug .= $a[random_int(0, strlen($a) - 1)];
        pp_q($pdo, 'INSERT INTO public_profiles (user_id, slug, enabled, created_at, updated_at) VALUES (?, ?, 1, ?, ?)', [$uid, $slug, time(), time()]);
    } else pp_q($pdo, 'UPDATE public_profiles SET enabled = ?, updated_at = ? WHERE user_id = ?', [$on ? 1 : 0, time(), $uid]);
    return pp_state($pdo, $uid);
}

function pp_delete_user(PDO $pdo, string $uid): void { pp_q($pdo, 'DELETE FROM public_profiles WHERE user_id = ?', [$uid]); }

/**
 * The 4 weeks (this week and the 3 before, Monday-Friday, New York session days), the same numbers as the week's recap
 * (GameWeeklyMail::brief: discipline = the share of trades without a mistake by the coach's rules, example data left out, a copy once).
 */
function pp_data(PDO $pdo, string $uid): array
{
    GameEngine::schema();
    $mon = GameEngine::monday(GameEngine::today());
    $first = GameEngine::addDays($mon, -21); $fri = GameEngine::addDays($mon, 4);
    // the 4 weeks' trades (Monday-Friday, example data left out, a copy once)
    $tr = [];
    foreach (GameEngine::q('SELECT id, data FROM documents WHERE user_id = ? AND collection = ?', [$uid, 'trades'])->fetchAll(PDO::FETCH_ASSOC) as $r) {
        $d = json_decode((string) $r['data'], true);
        if (!is_array($d) || !empty($d['demo'])) continue;
        $day = (string) ($d['date'] ?? '');
        if ($day < $first || $day > $fri || (int) date('N', strtotime($day . ' 12:00')) > 5) continue;   // Monday-Friday, as each week
        $d['id'] = $d['id'] ?? $r['id']; $tr[] = $d;
    }
    $tr = GameEngine::onePerCopyGroup($tr);
    $traded = array_fill_keys(array_map(fn($t) => (string) $t['date'], $tr), true);
    $weeks = [];
    for ($i = 3; $i >= 0; $i--) {
        $m = GameEngine::addDays($mon, -7 * $i);
        $b = GameWeeklyMail::brief($uid, $m);
        $days = array_map(fn($d) => ['day' => $d['day'], 'market' => (bool) $d['market'], 'swept' => (bool) $d['swept'], 'active' => isset($traded[$d['day']])],
            GameV2b::weekSummary($uid, $m)['days']);   // each day: swept, traded, or nothing
        $weeks[] = ['mon' => $m, 'disc' => $b['disc'], 'traded' => (int) $b['traded'], 'swept' => (int) $b['swept'], 'days' => $days];
    }
    // the 4 weeks together: the share of all their trades without a mistake, by the coach's rules (not the average of the weeks)
    $disc = GameWeeklyMail::coachDisc($uid, $tr);
    // verified: every trade of these weeks written by a platform sync (sync_trades: the server's own record)
    $synced = [];
    try { foreach ($pdo->query('SELECT doc_id FROM sync_trades WHERE user_id = ' . $pdo->quote($uid))->fetchAll(PDO::FETCH_COLUMN) as $id) $synced[(string) $id] = true; }
    catch (Throwable $e) { /* sync tables not created yet */ }
    $plat = [];
    $verified = (bool) $tr;
    foreach ($tr as $t) {
        if (!isset($synced[(string) $t['id']])) { $verified = false; break; }
        if (isset(PP_PLATFORMS[$t['source'] ?? ''])) $plat[PP_PLATFORMS[$t['source']]] = true;
    }
    $u = GameEngine::q('SELECT first_name, lang FROM users WHERE id = ?', [$uid])->fetch(PDO::FETCH_ASSOC) ?: [];
    return ['name' => trim((string) ($u['first_name'] ?? '')), 'lang' => (string) ($u['lang'] ?? 'en'), 'weeks' => $weeks, 'trades' => count($tr),
        'disc' => $disc, 'swept' => array_sum(array_column($weeks, 'swept')),
        'traded' => array_sum(array_column($weeks, 'traded')), 'streak' => (int) (GameEngine::profileState($uid)['streak']['current'] ?? 0),
        'verified' => $verified, 'platforms' => array_keys($plat)];
}

/** the visitor's language (Accept-Language), else the trader's */
function pp_lang(string $fallback): string
{
    foreach (explode(',', (string) ($_SERVER['HTTP_ACCEPT_LANGUAGE'] ?? '')) as $p) {
        $l = strtolower(substr(trim($p), 0, 2));
        if (in_array($l, ['en', 'fr', 'es'], true)) return $l;
    }
    $l = strtolower(substr($fallback, 0, 2));
    return in_array($l, ['fr', 'es'], true) ? $l : 'en';
}

const PP_T = [
    'en' => ['title' => '{n} · Discipline on Sweep', 'sub' => 'Discipline · last 4 weeks', 'disc' => 'Discipline', 'streak' => 'Current streak', 'days' => 'days', 'day1' => 'day',
        'swept' => 'Days swept', 'traded' => 'Days traded', 'week' => 'Week of {d}', 'now' => 'This week', 'wk' => '{s} swept of {t} days traded', 'none' => 'No trade in these 4 weeks yet.',
        'ver' => 'Verified', 'verS' => 'Every trade of these 4 weeks comes from {p}, synced automatically.', 'plat' => 'the trading platform',
        'foot' => 'Discipline only, never an amount. Discipline = the share of the trader\'s trades without a mistake (plan, stop, checklist…), by the rules of their Sweep coach.',
        'desc' => '4 weeks: {d} discipline, {s} days swept, {k}-day streak.', 'desc0' => '4 weeks of discipline, on Sweep.', 'anon' => 'A Sweep trader',
        'cta' => 'Track your discipline with Sweep', 'ctaS' => 'The trading journal for prop firm traders. Discipline first.', 'go' => 'Try Sweep', 'gone' => 'This profile is not public.',
        'mon' => ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'], 'dow' => ['M', 'T', 'W', 'T', 'F']],
    'fr' => ['title' => '{n} · Discipline sur Sweep', 'sub' => 'Discipline · 4 dernières semaines', 'disc' => 'Discipline', 'streak' => 'Série actuelle', 'days' => 'jours', 'day1' => 'jour',
        'swept' => 'Journées balayées', 'traded' => 'Jours tradés', 'week' => 'Semaine du {d}', 'now' => 'Cette semaine', 'wk' => '{s} balayées sur {t} jours tradés', 'none' => 'Pas encore de trade sur ces 4 semaines.',
        'ver' => 'Vérifié', 'verS' => 'Chaque trade de ces 4 semaines vient de {p}, synchronisé automatiquement.', 'plat' => 'la plateforme de trading',
        'foot' => 'Seulement la discipline, jamais de montant. Discipline = la part des trades sans erreur du trader (plan, stop, checklist…), selon les règles de son coach Sweep.',
        'desc' => '4 semaines : {d} de discipline, {s} journées balayées, série de {k} jours.', 'desc0' => '4 semaines de discipline, sur Sweep.', 'anon' => 'Un trader Sweep',
        'cta' => 'Suis ta discipline avec Sweep', 'ctaS' => 'Le journal de trading des traders de prop firms. La discipline d’abord.', 'go' => 'Essayer Sweep', 'gone' => 'Ce profil n’est pas public.',
        'mon' => ['janv.', 'févr.', 'mars', 'avr.', 'mai', 'juin', 'juil.', 'août', 'sept.', 'oct.', 'nov.', 'déc.'], 'dow' => ['L', 'M', 'M', 'J', 'V']],
    'es' => ['title' => '{n} · Disciplina en Sweep', 'sub' => 'Disciplina · últimas 4 semanas', 'disc' => 'Disciplina', 'streak' => 'Racha actual', 'days' => 'días', 'day1' => 'día',
        'swept' => 'Días barridos', 'traded' => 'Días operados', 'week' => 'Semana del {d}', 'now' => 'Esta semana', 'wk' => '{s} barridos de {t} días operados', 'none' => 'Aún no hay operaciones en estas 4 semanas.',
        'ver' => 'Verificado', 'verS' => 'Cada operación de estas 4 semanas viene de {p}, sincronizada automáticamente.', 'plat' => 'la plataforma de trading',
        'foot' => 'Solo la disciplina, nunca un monto. Disciplina = la proporción de operaciones sin error del trader (plan, stop, checklist…), según las reglas de su coach de Sweep.',
        'desc' => '4 semanas: {d} de disciplina, {s} días barridos, racha de {k} días.', 'desc0' => '4 semanas de disciplina, en Sweep.', 'anon' => 'Un trader de Sweep',
        'cta' => 'Sigue tu disciplina con Sweep', 'ctaS' => 'El diario de trading para traders de prop firms. Primero la disciplina.', 'go' => 'Probar Sweep', 'gone' => 'Este perfil no es público.',
        'mon' => ['ene.', 'feb.', 'mar.', 'abr.', 'may.', 'jun.', 'jul.', 'ago.', 'sept.', 'oct.', 'nov.', 'dic.'], 'dow' => ['L', 'M', 'X', 'J', 'V']],
];

/** the page: [HTTP status, HTML] (pp_public prints it; the tests read it) */
function pp_html(PDO $pdo, string $slug, ?string $lang = null): array
{
    $r = pp_q($pdo, 'SELECT user_id FROM public_profiles WHERE slug = ? AND enabled = 1', [$slug])->fetchColumn();
    $L = $lang ?? pp_lang('en'); $T = PP_T[$L];
    $h = fn($s) => htmlspecialchars((string) $s, ENT_QUOTES, 'UTF-8');
    $head = fn(string $title, string $extra = '') => '<!doctype html><html lang="' . $L . '"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        . '<meta name="robots" content="noindex"><title>' . $h($title) . '</title>' . $extra . '<style>' . PP_CSS . '</style></head>';
    if ($r === false) return [404, $head('Sweep') . '<body><main class="pp"><p class="pp-gone">' . $h($T['gone']) . '</p><a class="pp-go" href="https://makeitsweep.com/">makeitsweep.com</a></main></body></html>'];
    $uid = (string) $r;
    $d = pp_data($pdo, $uid);
    if ($lang === null) { $L = pp_lang($d['lang']); $T = PP_T[$L]; }
    $pct = fn($v) => $v === null ? '—' : $v . ($L === 'en' ? '%' : "\u{202F}%");
    $fill = fn(string $s, array $p) => preg_replace_callback('/\{(\w)\}/', fn($m) => (string) ($p[$m[1]] ?? $m[0]), $s);
    $name = $d['name'] !== '' ? $d['name'] : $T['anon'];
    $title = $fill($T['title'], ['n' => $name]);
    $desc = $d['disc'] === null ? $T['desc0'] : $fill($T['desc'], ['d' => $pct($d['disc']), 's' => $d['swept'], 'k' => $d['streak']]);
    $host = 'https://' . preg_replace('/[^A-Za-z0-9.:-]/', '', (string) ($_SERVER['HTTP_HOST'] ?? 'app.makeitsweep.com'));
    $img = 'https://makeitsweep.com/social/og-image.png';
    $meta = '<meta name="description" content="' . $h($desc) . '"><meta property="og:type" content="profile"><meta property="og:site_name" content="Sweep">'
        . '<meta property="og:url" content="' . $h($host . '/p/' . $slug) . '"><meta property="og:title" content="' . $h($title) . '"><meta property="og:description" content="' . $h($desc) . '">'
        . '<meta property="og:image" content="' . $img . '"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:image:type" content="image/png">'
        . '<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="' . $h($title) . '"><meta name="twitter:description" content="' . $h($desc) . '"><meta name="twitter:image" content="' . $img . '">'
        . '<meta name="theme-color" content="#08080A">';
    $date = function (string $ymd) use ($T, $L) { [$y, $m, $dd] = array_map('intval', explode('-', $ymd)); $mo = $T['mon'][$m - 1]; return $L === 'en' ? "$mo $dd" : "$dd $mo"; };
    $rows = '';
    foreach (array_reverse($d['weeks']) as $i => $w) {
        $dots = '';
        foreach ($w['days'] as $k => $x) $dots .= '<i class="' . (!$x['market'] ? 'off' : ($x['swept'] ? 'sw' : ($x['active'] ? 'on' : ''))) . '" title="' . $h($T['dow'][$k]) . '"></i>';
        $rows .= '<li><div><b>' . $h($i === 0 ? $T['now'] : $fill($T['week'], ['d' => $date($w['mon'])])) . '</b><small>' . $h($fill($T['wk'], ['s' => $w['swept'], 't' => $w['traded']])) . '</small></div>'
            . '<span class="pp-dots" aria-hidden="true">' . $dots . '</span><strong>' . $h($pct($w['disc'])) . '</strong></li>';
    }
    $plat = $d['platforms'] ? implode(' · ', $d['platforms']) : $T['plat'];
    $site = 'https://makeitsweep.com/' . ($L === 'en' ? '' : $L . '/') . '?utm_source=share&utm_medium=profile&utm_campaign=discipline_profile';
    $body = '<body><main class="pp"><header><a class="pp-logo" href="' . $h($site) . '">sweep</a>' . ($d['verified'] ? '<span class="pp-ver">✓ ' . $h($T['ver']) . '</span>' : '') . '</header>'
        . '<h1>' . $h($name) . '</h1><p class="pp-sub">' . $h($T['sub']) . '</p>'
        . ($d['trades'] ? '<div class="pp-big"><b>' . $h($pct($d['disc'])) . '</b><span>' . $h($T['disc']) . '</span></div>'
            . '<div class="pp-tiles"><div><span>' . $h($T['streak']) . '</span><b>' . $d['streak'] . ' <small>' . $h($d['streak'] === 1 ? $T['day1'] : $T['days']) . '</small></b></div>'
            . '<div><span>' . $h($T['swept']) . '</span><b>' . $d['swept'] . '</b></div><div><span>' . $h($T['traded']) . '</span><b>' . $d['traded'] . '</b></div></div>'
            . '<ul class="pp-weeks">' . $rows . '</ul>'
            . ($d['verified'] ? '<p class="pp-vs">' . $h($fill($T['verS'], ['p' => $plat])) . '</p>' : '')
            : '<p class="pp-none">' . $h($T['none']) . '</p>')
        . '<p class="pp-foot">' . $h($T['foot']) . '</p>'
        . '<section class="pp-cta"><div><h2>' . $h($T['cta']) . '</h2><p>' . $h($T['ctaS']) . '</p></div><a class="pp-go" href="' . $h($site) . '">' . $h($T['go']) . ' →</a></section></main></body></html>';
    return [200, $head($title, $meta) . $body];
}

/** GET /p/<id> */
function pp_public(PDO $pdo, string $slug): void
{
    [$code, $html] = pp_html($pdo, $slug);
    if ($code === 200) { try { pp_q($pdo, 'UPDATE public_profiles SET views = views + 1 WHERE slug = ?', [$slug]); } catch (Throwable $e) { /* counting never blocks */ } }
    http_response_code($code);
    header('Content-Type: text/html; charset=utf-8'); header('Cache-Control: no-cache, max-age=0'); header('X-Robots-Tag: noindex'); header('X-Content-Type-Options: nosniff');
    header("Content-Security-Policy: default-src 'none'; style-src 'unsafe-inline'; font-src 'self'; img-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'");
    echo $html;
    exit;
}

const PP_CSS = "@font-face{font-family:Geist;src:url(/assets/fonts/Geist-Variable.woff2) format('woff2');font-weight:100 900;font-display:swap}"
    . ":root{--bg:#08080A;--panel:#121216;--line:#25252b;--text:#F2F2F3;--muted:#9A9AA2;--blue:#4C8DFF;color-scheme:dark}"
    . "@media (prefers-color-scheme:light){:root{--bg:#F7F7F8;--panel:#fff;--line:#e5e5ea;--text:#111114;--muted:#6b6b73;color-scheme:light}}"
    . "*{box-sizing:border-box}body{margin:0;background:var(--bg) radial-gradient(120% 60% at 50% 0,rgba(76,141,255,.08),transparent 60%) no-repeat;color:var(--text);font:15px/1.5 Geist,-apple-system,system-ui,sans-serif;-webkit-font-smoothing:antialiased}"
    . ".pp{max-width:560px;margin:0 auto;padding:28px 16px 40px}header{display:flex;align-items:center;justify-content:space-between;margin-bottom:28px}"
    . ".pp-logo{font-weight:600;font-size:18px;color:var(--text);text-decoration:none;letter-spacing:-.01em}.pp-ver{font-size:13px;font-weight:500;color:var(--blue);padding:5px 10px;border-radius:999px;background:rgba(76,141,255,.12)}"
    . "h1{margin:0;font-size:30px;font-weight:600;letter-spacing:-.02em}.pp-sub{margin:4px 0 20px;color:var(--muted)}"
    . ".pp-big{display:flex;align-items:baseline;gap:10px;margin-bottom:14px}.pp-big b{font-size:56px;font-weight:600;letter-spacing:-.03em;line-height:1;color:var(--blue)}.pp-big span{color:var(--muted)}"
    . ".pp-tiles{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-bottom:18px}.pp-tiles div{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:12px}"
    . ".pp-tiles span{display:block;font-size:12px;color:var(--muted);line-height:1.3}.pp-tiles b{font-size:22px;font-weight:600}.pp-tiles small{font-size:13px;font-weight:400;color:var(--muted)}"
    . ".pp-weeks{list-style:none;margin:0;padding:0;background:var(--panel);border:1px solid var(--line);border-radius:20px;overflow:hidden}"
    . ".pp-weeks li{display:flex;align-items:center;gap:12px;padding:14px 16px}.pp-weeks li+li{border-top:1px solid var(--line)}.pp-weeks li>div{flex:1;min-width:0}"
    . ".pp-weeks b{display:block;font-weight:500}.pp-weeks small{color:var(--muted);font-size:13px}.pp-weeks strong{font-weight:600;min-width:54px;text-align:right}"
    . ".pp-dots{display:flex;gap:5px}.pp-dots i{width:10px;height:10px;border-radius:50%;box-shadow:inset 0 0 0 1.5px var(--line)}.pp-dots i.on{box-shadow:inset 0 0 0 1.5px var(--blue)}.pp-dots i.sw{background:var(--blue);box-shadow:none}.pp-dots i.off{opacity:.35}"
    . ".pp-vs,.pp-none,.pp-foot,.pp-gone{color:var(--muted);font-size:13px;margin:14px 2px 0}.pp-none{font-size:15px}.pp-gone{font-size:16px;margin:30vh 0 12px;text-align:center}"
    . ".pp-cta{margin-top:26px;padding:18px;border-radius:20px;background:var(--panel);border:1px solid var(--line);display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap}"
    . ".pp-cta h2{margin:0;font-size:16px;font-weight:600}.pp-cta p{margin:2px 0 0;color:var(--muted);font-size:13px}"
    . ".pp-go{display:inline-block;padding:10px 16px;border-radius:14px;background:var(--blue);color:#fff;text-decoration:none;font-weight:500}main.pp>.pp-go{display:block;width:max-content;margin:0 auto}";
