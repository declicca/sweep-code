<?php
/**
 * Sweep — public share links.
 *
 * A trader shares a card (his stats for a period, for now) as a link anyone can open, without an account.
 * The link is a SNAPSHOT: only what was on the card when he created it (title, period, the numbers he chose
 * to show — amounts hidden stay hidden) and its image. Nothing else of the account is reachable from it.
 *
 *   POST /api/share/create   {kind, card:{label, eyebrow, big, stats:[[k,v]…], cap}, image: dataURL png, lang}  → {url, id}
 *   POST /api/share/delete   {id}                                                                            → {ok}
 *   GET  /api/share/list                                                                                     → {links:[…]}
 *   GET  /s/{id}       public page (preview image + numbers + link to Sweep), noindex, social preview tags
 *   GET  /s/{id}.png   the card image
 */

function sl_dir(): string
{
    global $DATA;
    $d = rtrim((string) ($DATA ?? (__DIR__ . '/../data')), '/') . '/shares';
    if (!is_dir($d)) @mkdir($d, 0750, true);
    return $d;
}

function sl_table(PDO $pdo): void
{
    static $done = false;
    if ($done) return;
    $pdo->exec('CREATE TABLE IF NOT EXISTS public_shares (id VARCHAR(32) NOT NULL PRIMARY KEY, user_id VARCHAR(120) NOT NULL, kind VARCHAR(24) NOT NULL, payload TEXT NOT NULL, created_at INT NOT NULL, views INT NOT NULL DEFAULT 0, revoked INT NOT NULL DEFAULT 0)');
    $done = true;
}

function sl_id(): string
{
    $a = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789'; $s = '';
    for ($i = 0; $i < 14; $i++) $s .= $a[random_int(0, strlen($a) - 1)];
    return $s;
}

function sl_clean(string $s, int $max): string
{
    $s = trim(preg_replace('/\s+/u', ' ', strip_tags($s)) ?? '');
    return mb_substr($s, 0, $max);
}

function sl_create(PDO $pdo, array $me, array $b): array
{
    sl_table($pdo);
    $kind = in_array($b['kind'] ?? '', ['stats', 'stats_page', 'payouts', 'net', 'week', 'day', 'payout', 'trade'], true) ? $b['kind'] : 'stats';
    $c = (array) ($b['card'] ?? []);
    $stats = [];
    foreach (array_slice((array) ($c['stats'] ?? []), 0, 6) as $p) if (is_array($p) && count($p) >= 2) $stats[] = [sl_clean((string) $p[0], 40), sl_clean((string) $p[1], 40)];
    $card = ['label' => sl_clean((string) ($c['label'] ?? ''), 60), 'eyebrow' => sl_clean((string) ($c['eyebrow'] ?? ''), 90), 'big' => sl_clean((string) ($c['big'] ?? ''), 40),
        'stats' => $stats, 'cap' => sl_clean((string) ($c['cap'] ?? ''), 240), 'lang' => in_array($b['lang'] ?? '', ['en', 'fr', 'es'], true) ? $b['lang'] : 'en',
        'by' => sl_clean((string) ($me['username'] ?? ''), 32), 'name' => sl_clean((string) ($b['name'] ?? ($me['full_name'] ?? '')), 80), 'period' => sl_clean((string) ($b['period'] ?? ''), 60)];
    // the card image (png only, 3 MB max)
    $img = (string) ($b['image'] ?? '');
    $img = preg_replace('#^data:image/(png|jpeg);base64,#', '', $img) ?? '';
    $raw = base64_decode($img, true);
    $isPng = $raw !== false && substr($raw, 0, 8) === "\x89PNG\r\n\x1a\n"; $isJpg = $raw !== false && substr($raw, 0, 3) === "\xFF\xD8\xFF";
    if ($raw === false || strlen($raw) < 100 || strlen($raw) > 3 * 1048576 || (!$isPng && !$isJpg)) return ['error' => 'image'];
    $page = null;
    if ($kind === 'stats_page') {
        $html = (string) ($b['html'] ?? '');
        if ($html === '' && !empty($b['html_gz'])) { $z = base64_decode((string) $b['html_gz'], true); $html = $z !== false ? (string) @gzdecode($z) : ''; }   // the page comes gzipped (smaller request)
        $page = sl_sanitize($html); if ($page === '' || strlen($page) > 6 * 1048576) return ['error' => 'page'];
    }
    // a few links per minute at most
    $recent = (int) $pdo->query("SELECT COUNT(*) FROM public_shares WHERE user_id = " . $pdo->quote($me['id']) . " AND created_at > " . (time() - 60))->fetchColumn();
    if ($recent >= 6) return ['error' => 'slow_down'];
    $id = sl_id();
    file_put_contents(sl_dir() . '/' . $id . '.png', $raw);
    if ($page !== null) file_put_contents(sl_dir() . '/' . $id . '.html', $page);
    $st = $pdo->prepare('INSERT INTO public_shares (id, user_id, kind, payload, created_at) VALUES (?, ?, ?, ?, ?)');
    $st->execute([$id, $me['id'], $kind, json_encode($card, JSON_UNESCAPED_UNICODE), time()]);
    return ['id' => $id];
}

/** the snapshot of the Stats page: markup only (no script, no handler, no outside resource); the page's CSP blocks scripts anyway */
function sl_sanitize(string $h): string
{
    $h = preg_replace('#<(script|style|iframe|object|embed|link|meta|base|form|noscript|template)\b[^>]*>.*?</\1\s*>#is', '', $h) ?? '';
    $h = preg_replace('#<(script|iframe|object|embed|link|meta|base|form|input|textarea|select)\b[^>]*/?>#is', '', $h) ?? '';
    $h = preg_replace('#\son[a-z]+\s*=\s*("[^"]*"|\'[^\']*\'|[^\s>]+)#i', '', $h) ?? '';
    $h = preg_replace('#\s(href|src|xlink:href|action|formaction|srcdoc)\s*=\s*("\s*(javascript|vbscript|data:text)[^"]*"|\'\s*(javascript|vbscript|data:text)[^\']*\')#i', '', $h) ?? '';
    $h = preg_replace('#\shref\s*=\s*"(?!\#)[^"]*"#i', '', $h) ?? '';
    return trim($h);
}

function sl_list(PDO $pdo, array $me): array
{
    sl_table($pdo);
    $st = $pdo->prepare('SELECT id, kind, payload, created_at, views FROM public_shares WHERE user_id = ? AND revoked = 0 ORDER BY created_at DESC LIMIT 50');
    $st->execute([$me['id']]);
    $out = [];
    foreach ($st->fetchAll() as $r) { $p = json_decode((string) $r['payload'], true) ?: []; $out[] = ['id' => $r['id'], 'kind' => $r['kind'], 'label' => $p['label'] ?? '', 'eyebrow' => $p['eyebrow'] ?? '', 'created_at' => (int) $r['created_at'], 'views' => (int) $r['views']]; }
    return $out;
}

function sl_delete(PDO $pdo, array $me, string $id): bool
{
    sl_table($pdo);
    $st = $pdo->prepare('UPDATE public_shares SET revoked = 1 WHERE id = ? AND user_id = ?');
    $st->execute([$id, $me['id']]);
    if ($st->rowCount()) { @unlink(sl_dir() . '/' . basename($id) . '.png'); @unlink(sl_dir() . '/' . basename($id) . '.html'); return true; }
    return false;
}

/** GET /s/{id} and /s/{id}.png */
function sl_public(PDO $pdo, string $id, bool $png): void
{
    sl_table($pdo);
    $st = $pdo->prepare('SELECT * FROM public_shares WHERE id = ? AND revoked = 0');
    $st->execute([$id]);
    $r = $st->fetch();
    $file = sl_dir() . '/' . basename($id) . '.png';
    if (!$r || !is_file($file)) { http_response_code(404); header('Content-Type: text/html; charset=utf-8'); echo '<!doctype html><meta charset="utf-8"><meta name="robots" content="noindex"><title>Sweep</title><body style="font:16px system-ui;background:#0b0b0d;color:#ddd;display:grid;place-items:center;height:100vh;margin:0"><p>This link is no longer available. <a style="color:#5b8cff" href="https://makeitsweep.com">makeitsweep.com</a></p>'; exit; }
    if ($png) {
        header('Content-Type: ' . (substr((string) file_get_contents($file, false, null, 0, 3), 0, 3) === "\xFF\xD8\xFF" ? 'image/jpeg' : 'image/png')); header('Cache-Control: public, max-age=300'); header('X-Content-Type-Options: nosniff');
        readfile($file); exit;
    }
    try { $pdo->prepare('UPDATE public_shares SET views = views + 1 WHERE id = ?')->execute([$id]); } catch (Throwable $e) { /* counting never blocks */ }
    $p = json_decode((string) $r['payload'], true) ?: [];
    $lang = $p['lang'] ?? 'en';
    $T = ['en' => ['cta' => 'Track your trading with Sweep', 'sub' => 'The trading journal for prop firm traders. Discipline first.', 'by' => 'Shared by', 'go' => 'Try Sweep'],
          'fr' => ['cta' => 'Suis ton trading avec Sweep', 'sub' => 'Le journal de trading des traders de prop firms. La discipline d’abord.', 'by' => 'Partagé par', 'go' => 'Essayer Sweep'],
          'es' => ['cta' => 'Sigue tu trading con Sweep', 'sub' => 'El diario de trading para traders de prop firms. Primero la disciplina.', 'by' => 'Compartido por', 'go' => 'Probar Sweep']][$lang] ?? [];
    $h = fn($s) => htmlspecialchars((string) $s, ENT_QUOTES, 'UTF-8');
    $host = 'https://' . preg_replace('/[^A-Za-z0-9.:-]/', '', (string) ($_SERVER['HTTP_HOST'] ?? 'app.makeitsweep.com'));
    $title = trim(($p['label'] ?? 'Sweep') . ' · ' . ($p['eyebrow'] ?? ''), ' ·');
    $desc = $p['cap'] ?? $T['sub'];
    $site = 'https://makeitsweep.com/' . ($lang === 'en' ? '' : $lang . '/') . '?utm_source=share&utm_medium=link&utm_campaign=' . rawurlencode((string) $r['kind']) . (!empty($p['by']) ? '&ref=' . rawurlencode($p['by']) : '');
    $rows = '';
    foreach ((array) ($p['stats'] ?? []) as $s) $rows .= '<div class="st"><span>' . $h($s[0]) . '</span><b>' . $h($s[1]) . '</b></div>';
    $pageFile = sl_dir() . '/' . basename($id) . '.html';
    if (is_file($pageFile)) {   // the whole Stats page, read-only, with the app's own styles
        $css = '';
        $app = (string) @file_get_contents(__DIR__ . '/../app.html');
        if (preg_match_all('#href="(assets/[a-z0-9.-]+\.css)"#', $app, $mm)) foreach (array_unique($mm[1]) as $f) $css .= '<link rel="stylesheet" href="/' . $h($f) . '">';
        $Tp = ['en' => ['t' => 'Trading stats', 'by' => 'Shared on Sweep'], 'fr' => ['t' => 'Stats de trading', 'by' => 'Partagé sur Sweep'], 'es' => ['t' => 'Stats de trading', 'by' => 'Compartido en Sweep']][$lang] ?? ['t' => 'Trading stats', 'by' => 'Shared on Sweep'];
        $who = $p['name'] ?: ('@' . ($p['by'] ?? ''));
        $ttl = $who . ' · ' . $Tp['t'] . ($p['period'] ? ' · ' . $p['period'] : '');
        header('Content-Type: text/html; charset=utf-8'); header('Cache-Control: no-cache, max-age=0'); header('X-Robots-Tag: noindex');
        header("Content-Security-Policy: default-src 'none'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; font-src 'self' data:; base-uri 'none'; form-action 'none'; frame-ancestors 'none'");
        echo '<!doctype html><html lang="' . $h($lang) . '" data-theme="dark"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex">'
            . '<title>' . $h($ttl) . '</title><meta name="description" content="' . $h($desc) . '">'
            . '<meta property="og:type" content="website"><meta property="og:site_name" content="Sweep"><meta property="og:title" content="' . $h($ttl) . '"><meta property="og:description" content="' . $h($desc) . '">'
            . '<meta property="og:image" content="' . $h($host . '/s/' . $id . '.png') . '"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="' . $h($host . '/s/' . $id . '.png') . '">' . $css
            . '<style>body{margin:0}.pub-h{max-width:1240px;margin:0 auto;padding:28px 24px 8px;display:flex;align-items:flex-end;justify-content:space-between;gap:16px;flex-wrap:wrap}.pub-h h1{margin:0;font-size:30px;letter-spacing:-.02em}.pub-h p{margin:4px 0 0;color:var(--muted)}.pub-logo{font-weight:600;font-size:15px;color:var(--text);text-decoration:none;opacity:.9}.pub-main{max-width:1240px;margin:0 auto;padding:8px 24px 40px}.pub-main button,.pub-main .seg{pointer-events:none}.pub-cta{max-width:1240px;margin:0 auto 48px;padding:0 24px}.pub-cta div{padding:22px;border-radius:18px;background:var(--panel);box-shadow:inset 0 0 0 1px var(--line);display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap}.pub-cta h2{margin:0 0 4px;font-size:18px}.pub-cta p{margin:0;color:var(--muted)}.pub-cta a{padding:12px 22px;border-radius:999px;background:var(--pos);color:#0b0b0d;font-weight:600;text-decoration:none}</style></head>'
            . '<body><header class="pub-h"><div><h1>' . $h($who) . '</h1><p>' . $h($Tp['t']) . ($p['period'] ? ' · ' . $h($p['period']) : '') . ' · ' . $h(gmdate('Y-m-d', (int) $r['created_at'])) . '</p></div><a class="pub-logo" href="' . $h($site) . '">sweep</a></header>'
            . '<main class="pub-main" id="main">' . file_get_contents($pageFile) . '</main>'
            . '<section class="pub-cta"><div><div><h2>' . $h($T['cta']) . '</h2><p>' . $h($T['sub']) . '</p></div><a href="' . $h($site) . '">' . $h($T['go']) . ' →</a></div></section></body></html>';
        exit;
    }
    header('Content-Type: text/html; charset=utf-8'); header('Cache-Control: no-cache, max-age=0'); header('X-Robots-Tag: noindex');   // a deleted link disappears at once
    header("Content-Security-Policy: default-src 'none'; img-src 'self'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'");
    echo '<!doctype html><html lang="' . $h($lang) . '"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex">'
        . '<title>' . $h($title) . '</title><meta name="description" content="' . $h($desc) . '">'
        . '<meta property="og:type" content="website"><meta property="og:site_name" content="Sweep"><meta property="og:title" content="' . $h($title) . '"><meta property="og:description" content="' . $h($desc) . '">'
        . '<meta property="og:image" content="' . $h($host . '/s/' . $id . '.png') . '"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="' . $h($host . '/s/' . $id . '.png') . '">'
        . '<style>body{margin:0;background:#0b0b0d;color:#e9e9ee;font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Inter,sans-serif;display:flex;justify-content:center;padding:28px 16px}main{width:min(680px,100%)}img{display:block;width:100%;height:auto;border-radius:18px;box-shadow:0 20px 60px rgba(0,0,0,.5)}.sts{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px;margin:18px 0}.st{padding:12px 14px;border-radius:12px;background:#16161a;border:1px solid #26262c}.st span{display:block;font-size:12px;color:#9a9aa5}.st b{font-size:17px}.by{color:#9a9aa5;font-size:13px;margin:14px 0 0}.cta{margin-top:22px;padding:20px;border-radius:16px;background:#121a2e;border:1px solid #2a3b66}.cta h2{margin:0 0 4px;font-size:18px}.cta p{margin:0 0 14px;color:#b5b9c6}.cta a{display:inline-block;padding:11px 20px;border-radius:999px;background:#5b8cff;color:#0b0b0d;font-weight:600;text-decoration:none}</style></head><body><main>'
        . '<img src="/s/' . $h($id) . '.png" alt="' . $h($title) . '">'
        . ($rows ? '<div class="sts">' . $rows . '</div>' : '')
        . (!empty($p['by']) ? '<p class="by">' . $h($T['by']) . ' @' . $h($p['by']) . ' · ' . $h(gmdate('Y-m-d', (int) $r['created_at'])) . '</p>' : '')
        . '<div class="cta"><h2>' . $h($T['cta']) . '</h2><p>' . $h($T['sub']) . '</p><a href="' . $h($site) . '">' . $h($T['go']) . ' →</a></div>'
        . '</main></body></html>';
    exit;
}
