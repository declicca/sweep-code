<?php
declare(strict_types=1);
/**
 * Sweep — what the hunt of 13 Nov. found (leftovers of the 10 Nov. cleanup, and the server review), on a throwaway SQLite database:
 *   php tests/leftovers_test.php
 *  - a shared Stats page: no redirect, no outside link, no full-screen layer survives the cleaning, whatever the nesting or the
 *    quotes (before: « <me<input>ta http-equiv=refresh …> » left a live <meta>, and href='…' passed); an honest page is untouched;
 *  - referrals: the address is the connection's, never a « CF-Connecting-IP » header the caller types;
 *  - badges: the 12 that nothing unlocks any more (bosses, chest, league, buddy) are not shown locked nor counted; one earned stays;
 *  - the words: the Sunday notification no longer promises missions; the guide no longer speaks of XP or of a level.
 */
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
$app = dirname(__DIR__);
$tmp = sys_get_temp_dir() . '/sweep-left-' . bin2hex(random_bytes(4)); mkdir($tmp);
$pdo = new PDO('sqlite:' . $tmp . '/t.db', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC]);
function db() { global $pdo; return $pdo; }
$pdo->exec('CREATE TABLE documents (user_id TEXT NOT NULL, collection TEXT NOT NULL, id TEXT NOT NULL, data TEXT NOT NULL, updated_at TEXT, PRIMARY KEY (user_id, collection, id))');
$pdo->exec('CREATE TABLE users (id TEXT PRIMARY KEY, username TEXT, lang TEXT, email TEXT, first_name TEXT, disabled INT DEFAULT 0)');
$DATA = $tmp; $cfg = ['referral_salt' => 's'];
require_once $app . '/notify/notify.php';
require_once $app . '/game/game.php';
require_once $app . '/growth/share-links.php';
require_once $app . '/growth/referral.php';
GameEngine::setPdo($pdo); GameEngine::schema(); GameV2::schema(); GameV2b::schema();
$pass = 0; $fail = 0;
$ok = function (bool $c, string $what) use (&$pass, &$fail) { echo ($c ? 'ok   ' : 'FAIL ') . $what . "\n"; $c ? $pass++ : $fail++; };

// 1. the shared page
$bad = [
    'a nested tag that becomes a redirect' => "<p>x</p><me<input>ta http-equiv=refresh content='0;url=https://evil.example'>",
    'nested twice' => '<me<me<input>ta>ta http-equiv="refresh" content="0;url=https://evil.example">',
    'a link in single quotes' => "<a href='https://evil.example'>Sign in again</a>",
    'a link without quotes' => '<a href=https://evil.example>Sign in again</a>',
    'a script URL without quotes' => '<a href=javascript:alert(1)>x</a>',
    'a handler' => '<div onclick="x()" onmouseover=y()>x</div>',
    'a script split by a tag' => '<scr<script></script>ipt>alert(1)</scr<script></script>ipt>',
    'a form' => '<form action="https://evil.example"><input name=p></form>',
    'a full-screen layer' => '<div style="position:fixed;inset:0;background:#08080a">Sign in again</div><div style="POSITION : FIXED">x</div>',
];
foreach ($bad as $what => $h) {
    $o = sl_sanitize($h);
    $ok(!preg_match('#<\s*(meta|script|form|input|iframe|base|link)\b|evil\.example|javascript:|\son[a-z]+\s*=|position\s*:\s*fixed#i', $o), "shared page, $what: cleaned (« " . substr($o, 0, 70) . ' »)');
}
$good = '<section class="st-card"><h3 style="margin:0">Win rate</h3><svg viewBox="0 0 10 10"><use xlink:href="#ic-up"></use><path d="M0 0L10 10" style="stroke:#4C8DFF"/></svg><a href="#top">Top</a><button type="button" class="chip on">30 d</button><img src="data:image/png;base64,AAAA" alt=""></section>';
$ok(sl_sanitize($good) === $good, 'shared page, an honest snapshot (styles, SVG, « # » links, chips, an inline image): untouched');

// 2. referrals: the caller's header is not his address
$_SERVER['REMOTE_ADDR'] = '203.0.113.7'; $_SERVER['HTTP_CF_CONNECTING_IP'] = '198.51.100.1'; $a = ref_ip_hash();
$_SERVER['HTTP_CF_CONNECTING_IP'] = '198.51.100.2'; $b = ref_ip_hash();
$_SERVER['REMOTE_ADDR'] = '203.0.113.8'; $c = ref_ip_hash();
$ok($a === $b && $a !== $c, 'referrals: the same connection is the same address whatever « CF-Connecting-IP » says; another connection is another');

// 3. badges
$pdo->exec("INSERT INTO users (id, username) VALUES ('b1', 'b1')");
GameEngine::profile('b1');
$ids = array_column(GameEngine::badgesState('b1'), 'id');
$ok(count(GAME_BADGES_RETIRED) === 12 && !array_intersect($ids, GAME_BADGES_RETIRED) && count($ids) === count(GAME_BADGES) - 12, 'badges: the 12 retired ones are not listed (' . count($ids) . ' shown of ' . count(GAME_BADGES) . ')');
$pdo->prepare('INSERT INTO user_badges (user_id, badge_id, unlocked_at) VALUES (?, ?, ?)')->execute(['b1', 'buddy_10', time()]);
$st = array_column(GameEngine::badgesState('b1'), null, 'id');
$ok(isset($st['buddy_10']) && $st['buddy_10']['unlocked'] === true && !isset($st['league_promoted']), 'badges: one earned before 10 Nov. stays in the trader\'s list');

// 4. the words
$n = (string) file_get_contents($app . '/src/notify.js'); $g = (string) file_get_contents($app . '/src/guide.js'); $game = (string) file_get_contents($app . '/src/game.js');
$ok(!preg_match("/'g_intention\\.title': '[^']*(mission|misiones)/i", $n) && substr_count($n, "'g_intention.title'") === 3, 'the Sunday notification: no missions promised, in 3 languages');
$ok(!preg_match('/\\bXP\\b|ton niveau|and level|y nivel/', $g), 'the guide: no XP, no level');
// the guide: every article has as many paragraphs in Spanish as in English and French (7 were shorter)
$short = [];
if (preg_match_all("/body: \\{ fr: \\[(.*?)\\],\\s*en: \\[(.*?)\\],\\s*es: \\[(.*?)\\] \\}/s", $g, $m, PREG_SET_ORDER)) foreach ($m as $i => $b) {
    $n = array_map(fn($x) => preg_match_all("/'(?:[^'\\\\]|\\\\.)*'/", $x), [$b[1], $b[2], $b[3]]);
    if ($n[0] !== $n[1] || $n[1] !== $n[2]) $short[] = "#$i " . implode('/', $n);
}
$ok(count($m) >= 10 && !$short, 'the guide: ' . count($m) . ' articles, the same number of paragraphs in FR, EN and ES (' . implode(', ', $short) . ')');
$ok(strpos($game, 'chest_opened') === false, 'the week\'s recap is done when it is saved (it no longer waits for the chest)');

$pdo = null; array_map('unlink', glob($tmp . '/*') ?: []); @array_map('rmdir', glob($tmp . '/*') ?: []); @rmdir($tmp);
echo "\n$pass passed, $fail failed\n";
exit($fail ? 1 : 0);
