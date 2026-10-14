<?php
declare(strict_types=1);
/**
 * Sweep — sharing (brief 02 part 12), on a throwaway SQLite database and folder:
 *   php tests/profile_test.php
 *  - the public discipline profile: off by default, one link kept when turned on again, « not public » (404) when off;
 *    the 4 weeks (Monday-Friday) as the week's recap counts them: discipline of every trade, a copy once, example data and
 *    weekends left out; days swept and traded, the streak; never an amount, the full name or the username; the visitor's language;
 *  - « Verified » only when every trade of those weeks was written by a platform sync (sync_trades), never by a trade's « source »;
 *  - a share link keeps its wide preview (-og.png) and gives its size to Discord, X and iMessage;
 *  - a deleted account takes its links (and their images) and its profile with it.
 */
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
$app = dirname(__DIR__);
$tmp = sys_get_temp_dir() . '/sweep-profile-' . bin2hex(random_bytes(4)); mkdir($tmp);
$DATA = $tmp;
$pdo = new PDO('sqlite:' . $tmp . '/t.db', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC]);
function db() { global $pdo; return $pdo; }
$pdo->exec('CREATE TABLE documents (user_id TEXT NOT NULL, collection TEXT NOT NULL, id TEXT NOT NULL, data TEXT NOT NULL, updated_at TEXT, PRIMARY KEY (user_id, collection, id))');
$pdo->exec('CREATE TABLE users (id TEXT PRIMARY KEY, username TEXT, lang TEXT, email TEXT, first_name TEXT, full_name TEXT, disabled INT DEFAULT 0)');
$pdo->exec('CREATE TABLE sync_trades (user_id TEXT NOT NULL, trade_id TEXT NOT NULL, doc_id TEXT NOT NULL, sync_account_id TEXT NOT NULL, sig TEXT NOT NULL, fills TEXT NOT NULL, entry_at TEXT NOT NULL, inst TEXT NOT NULL, dir TEXT NOT NULL, copy_group TEXT, created_at INTEGER NOT NULL, updated_at INTEGER NOT NULL, PRIMARY KEY (user_id, trade_id))');
require_once $app . '/notify/notify.php';
require_once $app . '/game/game.php';
GameEngine::setPdo($pdo); GameEngine::schema(); GameV2::schema(); GameV2b::schema();
require $app . '/growth/public-profile.php';
require $app . '/growth/share-links.php';
$pass = 0; $fail = 0;
$ok = function (bool $c, string $what) use (&$pass, &$fail) { echo ($c ? 'ok   ' : 'FAIL ') . $what . "\n"; $c ? $pass++ : $fail++; };
putenv('SWEEP_GAME_NOW=2026-10-21 12:00');   // Wednesday: this week is 19-23 Oct.; the 4 weeks start Monday 28 Sept.
$pdo->exec("INSERT INTO users (id, username, lang, email, first_name, full_name) VALUES ('u1', 'jean.dupont', 'fr', 'jean.dupont@t.dev', 'Noa', 'Noa Tremblay')");
GameEngine::profile('u1');
$trade = function (string $id, string $date, array $disc, array $more = []) use ($pdo) {
    $pdo->prepare("INSERT OR REPLACE INTO documents (user_id, collection, id, data) VALUES ('u1', 'trades', ?, ?)")->execute([$id, json_encode(['id' => $id, 'date' => $date, 'pnl_c' => 125000, 'account_id' => 'a', 'discipline' => $disc] + $more)]);
};
$day = fn(string $d, int $swept) => $pdo->prepare("INSERT OR REPLACE INTO game_days (user_id, trading_day, trades_count, ring_plan, ring_execution, ring_review, is_swept, activity, updated_at) VALUES ('u1', ?, 1, 100, 100, ?, ?, 1, 0)")->execute([$d, $swept ? 100 : 0, $swept]);
// 28 Sept. week: 2 trades (100 %, 50 %); 5 Oct.: none; 12 Oct.: 1 trade (0 %), its copy (once, as the original), an example;
// 19 Oct.: 1 trade (100 %), a Saturday trade (left out)
$trade('t1', '2026-09-29', ['plan' => 'y', 'stop' => 'y']); $trade('t2', '2026-09-30', ['plan' => 'y', 'stop' => 'n']);
$trade('t3', '2026-10-13', ['plan' => 'n', 'stop' => 'n'], ['copy_group' => 'g1', 'created_at' => '2026-10-13T14:00:00Z']);
$trade('t3c', '2026-10-13', ['plan' => 'y', 'stop' => 'y'], ['copy_group' => 'g1', 'created_at' => '2026-10-13T14:05:00Z']);
$trade('t4', '2026-10-14', ['plan' => 'y'], ['demo' => true]);
$trade('t5', '2026-10-19', ['plan' => 'y', 'stop' => 'y'], ['source' => 'ninjatrader']); $trade('t6', '2026-10-24', ['plan' => 'n']);
$day('2026-09-29', 1); $day('2026-09-30', 0); $day('2026-10-13', 1); $day('2026-10-19', 1);

// 1. off by default; one link, kept
$ok(pp_state($pdo, 'u1') === ['on' => false, 'url' => null], 'off by default: no link');
$s1 = pp_set($pdo, 'u1', true); $slug = substr((string) $s1['url'], 3);
$ok($s1['on'] && (bool) preg_match('~^/p/[A-Za-z0-9]{14}$~', (string) $s1['url']) && stripos($s1['url'], 'jean') === false, 'turned on: a personal link of 14 random characters, never the username (' . $s1['url'] . ')');
pp_set($pdo, 'u1', false); $off = pp_html($pdo, $slug, 'fr');
$s2 = pp_set($pdo, 'u1', true);
$ok($off[0] === 404 && strpos($off[1], 'Ce profil n’est pas public.') !== false && strpos($off[1], 'Noa') === false && $s2['url'] === $s1['url'], 'off: « not public » (404) at once, nothing of the trader; on again: the same link');
$ok(pp_html($pdo, 'NoSuchLink0000', 'en')[0] === 404, 'an unknown link: 404');

// 2. the 4 weeks, as the week's recap counts them
$d = pp_data($pdo, 'u1');
$w = array_column($d['weeks'], null, 'mon');
$ok(array_keys($w) === ['2026-09-28', '2026-10-05', '2026-10-12', '2026-10-19'], 'the 4 weeks: this one and the 3 before (' . implode(', ', array_keys($w)) . ')');
$ok($w['2026-09-28']['disc'] === 75 && $w['2026-10-05']['disc'] === null && $w['2026-10-12']['disc'] === 0 && $w['2026-10-19']['disc'] === 100,
    'each week: 75 %, none, 0 % (the copy once, as its original; the example left out), 100 % (Saturday left out) (' . json_encode(array_column($d['weeks'], 'disc')) . ')');
$ok($d['disc'] === 63 && $d['trades'] === 4, 'the 4 weeks together: every trade\'s score, (100 + 50 + 0 + 100) / 4 = 63 % (' . json_encode([$d['disc'], $d['trades']]) . ')');
$ok($d['swept'] === 3 && $d['traded'] === 4 && $w['2026-09-28']['swept'] === 1 && $w['2026-09-28']['traded'] === 2 && $w['2026-10-19']['days'][0]['swept'] === true && $w['2026-09-28']['days'][2] === ['day' => '2026-09-30', 'market' => true, 'swept' => false, 'active' => true] && $w['2026-09-28']['days'][3]['active'] === false && $w['2026-10-12']['days'][3]['active'] === false,
    'days swept 3, days traded 4; each day: swept, traded, or nothing (an example trade is not a day traded)');
$ok($d['name'] === 'Noa' && $d['verified'] === false, 'the first name; not verified (t5 says « ninjatrader », but no trade came from a sync)');

// 3. the page: the visitor's language, never an amount, the full name or the username
[$c, $fr] = pp_html($pdo, $slug, 'fr');
$nb = "\u{202F}";
$ok($c === 200 && strpos($fr, '<h1>Noa</h1>') !== false && strpos($fr, 'Discipline · 4 dernières semaines') !== false && strpos($fr, "63{$nb}%") !== false
    && strpos($fr, 'Cette semaine') !== false && strpos($fr, 'Semaine du 28 sept.') !== false && strpos($fr, '1 balayées sur 2 jours tradés') !== false && strpos($fr, 'Journées balayées') !== false,
    'French: the first name, « 4 dernières semaines », 63 %, this week first, « Semaine du 28 sept. », days swept of days traded');
$frx = str_replace($slug, '', $fr);   // (the random link could hold any letters)
$ok(strpos($frx, '$') === false && strpos($frx, '1 250') === false && strpos($frx, 'Tremblay') === false && stripos($frx, 'jean') === false && strpos($frx, 'NQ') === false, 'never an amount, the last name, the username or an instrument');
$ok(strpos($fr, '<meta name="robots" content="noindex">') !== false && strpos($fr, 'og:title" content="Noa · Discipline sur Sweep"') !== false && strpos($fr, "og:description\" content=\"4 semaines : 63{$nb}% de discipline, 3 journées balayées") !== false
    && strpos($fr, 'twitter:card" content="summary_large_image"') !== false && strpos($fr, 'og:image:width" content="1200"') !== false && strpos($fr, '✓ Vérifié') === false,
    'noindex; the preview: « Noa · Discipline sur Sweep », « 4 semaines : 63 % de discipline, 3 journées balayées… », a 1200 × 630 image; no « Vérifié »');
$_SERVER['HTTP_ACCEPT_LANGUAGE'] = 'es-ES,es;q=0.9,en;q=0.8'; [, $es] = pp_html($pdo, $slug);
$_SERVER['HTTP_ACCEPT_LANGUAGE'] = ''; [, $dflt] = pp_html($pdo, $slug);
$ok(strpos($es, 'Disciplina · últimas 4 semanas') !== false && strpos($es, 'Esta semana') !== false && strpos($dflt, 'Discipline · 4 dernières semaines') !== false && strpos(pp_html($pdo, $slug, 'en')[1], "63%") !== false,
    'the visitor\'s language (Spanish); none given: the trader\'s (French); English writes « 63% »');
// 4. verified: every trade written by a sync
foreach (['t1', 't2', 't3', 't5'] as $i => $id) $pdo->prepare("INSERT INTO sync_trades (user_id, trade_id, doc_id, sync_account_id, sig, fills, entry_at, inst, dir, created_at, updated_at) VALUES ('u1', ?, ?, 'sa', 'x', '[]', '2026-10-01 09:30:00', 'NQ', 'long', 0, 0)")->execute(["tr$i", $id]);
$d = pp_data($pdo, 'u1'); [, $vf] = pp_html($pdo, $slug, 'fr');
$ok($d['verified'] === true && $d['platforms'] === ['NinjaTrader 8'] && strpos($vf, '✓ Vérifié') !== false && strpos($vf, 'vient de NinjaTrader 8, synchronisé automatiquement') !== false, 'every trade from a sync: « ✓ Vérifié », from NinjaTrader 8');
$trade('t7', '2026-10-20', ['plan' => 'y']);
$ok(pp_data($pdo, 'u1')['verified'] === false, 'one trade entered by hand among them: not verified');

// 5. share links: the wide preview and its size
$png = function (int $w, int $h): string {
    $raw = ''; $row = "\0" . str_repeat("\x10\x20\x30", $w); for ($y = 0; $y < $h; $y++) $raw .= $row;
    $chunk = fn(string $t, string $d) => pack('N', strlen($d)) . $t . $d . pack('N', crc32($t . $d));
    return "\x89PNG\r\n\x1a\n" . $chunk('IHDR', pack('NNCCCCC', $w, $h, 8, 2, 0, 0, 0)) . $chunk('IDAT', gzcompress($raw)) . $chunk('IEND', '');
};
$me = ['id' => 'u1', 'username' => 'jean.dupont', 'full_name' => 'Noa Tremblay'];
$card = ['label' => 'Ma discipline', 'eyebrow' => 'octobre 2026', 'big' => '63 %', 'stats' => [['Série', '3'], ['Discipline', '63 %'], ['Journées balayées', '3']], 'cap' => '3 jours de suite, 63 % de discipline.'];
$a = sl_create($pdo, $me, ['kind' => 'discipline', 'lang' => 'fr', 'image' => 'data:image/png;base64,' . base64_encode($png(1080, 1350)), 'preview' => 'data:image/png;base64,' . base64_encode($png(1200, 675)), 'card' => $card]);
$b = sl_create($pdo, $me, ['kind' => 'week', 'lang' => 'fr', 'image' => 'data:image/png;base64,' . base64_encode($png(1080, 1920)), 'card' => $card]);
$kind = $pdo->query("SELECT kind FROM public_shares WHERE id = " . $pdo->quote($a['id'] ?? ''))->fetchColumn();
$ma = sl_meta('https://app.makeitsweep.com', $a['id'], 'Ma discipline · octobre 2026', $card['cap'], 'fr'); $mb = sl_meta('https://app.makeitsweep.com', $b['id'], 'x', 'y', 'fr');
$ok($kind === 'discipline' && is_file("$tmp/shares/{$a['id']}-og.png") && strpos($ma, 'og:image" content="https://app.makeitsweep.com/s/' . $a['id'] . '-og.png"') !== false
    && strpos($ma, 'og:image:width" content="1200"') !== false && strpos($ma, 'og:image:height" content="675"') !== false && strpos($ma, 'twitter:title" content="Ma discipline · octobre 2026"') !== false
    && strpos($ma, 'og:url" content="https://app.makeitsweep.com/s/' . $a['id'] . '"') !== false, 'a link with its wide preview: og:image -og.png, 1200 × 675, og:url, twitter:title (kind « discipline » kept)');
$ok(strpos($mb, '/s/' . $b['id'] . '.png"') !== false && strpos($mb, 'og:image:height" content="1920"') !== false, 'a link without a preview: the card itself, its real size (1080 × 1920)');
$big = sl_create($pdo, $me, ['kind' => 'discipline', 'image' => 'data:image/png;base64,' . base64_encode($png(1080, 1350)), 'preview' => 'data:image/png;base64,' . base64_encode(random_bytes(2 * 1048576)), 'card' => $card]);
$ok(!empty($big['id']) && !is_file("$tmp/shares/{$big['id']}-og.png"), 'a preview that is not an image (or over 1.5 MB): ignored, the link still made');

// 6. the account deleted: its links, their images and its profile
sl_delete_user($pdo, 'u1'); pp_delete_user($pdo, 'u1');
$ok((int) $pdo->query("SELECT COUNT(*) FROM public_shares WHERE user_id = 'u1'")->fetchColumn() === 0 && glob("$tmp/shares/*") === [] && pp_state($pdo, 'u1')['on'] === false && pp_html($pdo, $slug, 'fr')[0] === 404,
    'account deleted: no link, no image, no profile (before 14 Oct., the links stayed online)');

$pdo = null; foreach (array_merge(glob("$tmp/shares/*") ?: [], glob("$tmp/*") ?: []) as $f) is_dir($f) ? @rmdir($f) : @unlink($f); @rmdir($tmp);
echo "\n$pass passed, $fail failed\n";
exit($fail ? 1 : 0);
