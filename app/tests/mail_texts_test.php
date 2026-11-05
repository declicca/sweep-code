<?php
declare(strict_types=1);
/**
 * Sweep — the automatic emails' texts and their new versions (brief « Courriels de feedback », step 3), on a throwaway
 * SQLite database, nothing sent:
 *   php tests/mail_texts_test.php
 *  - the texts: {progress} in the absences, the trade milestones, the first payout and the Pro trial (EN, FR, ES); a one-click
 *    question in the welcome, the 14-day absence and the cancellation, nowhere else; each option short enough;
 *  - the earlier texts (version 1) are the new ones without {progress} nor the questions: their fingerprints match
 *    mail/mail-auto-texts-before.php;
 *  - ma_upgrade: a language still on our earlier text takes the new one, a language Mateo changed keeps his text and gets the
 *    new one as a proposal; once per version; taken or set aside (ml_campaign_proposal); a fresh install has nothing to do;
 *  - one request for an opinion every 30 days: a second automation's question goes without it (its paragraph too), the
 *    welcome's never held nor counted, a campaign's never held; after 30 days, asked again.
 */
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
$app = dirname(__DIR__);
$tmp = sys_get_temp_dir() . '/sweep-mail-texts-' . bin2hex(random_bytes(4)); mkdir($tmp);
ini_set('error_log', $tmp . '/php.log'); putenv('SWEEP_TEST_DB=' . $tmp . '/t.db');
$pdo = new PDO('sqlite:' . $tmp . '/t.db', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC]);
$pdo->exec('CREATE TABLE users (id TEXT PRIMARY KEY, username TEXT, email TEXT, lang TEXT, first_name TEXT, created_at TEXT, last_login TEXT, disabled INTEGER DEFAULT 0, is_admin INTEGER DEFAULT 0, is_internal INTEGER DEFAULT 0)');
$pdo->exec('CREATE TABLE app_settings (k TEXT PRIMARY KEY, v TEXT NOT NULL)');
function db(): PDO { global $pdo; return $pdo; }
$GLOBALS['cfg'] = ['app_url' => 'https://app.test/'];
require $app . '/mail/mail-core.php';
require $app . '/mail/mail-auto.php';
$pass = 0; $fail = 0;
$ok = function (bool $c, string $what) use (&$pass, &$fail) { echo ($c ? 'ok   ' : 'FAIL ') . $what . "\n"; $c ? $pass++ : $fail++; };
ml_schema($pdo);

/* ───── the texts ───── */
$cat = ma_catalog();
$prog = ['tradesMilestone', 'firstPayoutLogged', 'inactive3d', 'inactive7d', 'inactive14d', 'inactive30d', 'proTrialDaysLeft', 'proTrialEnded', 'weekOne', 'months3'];
$asks = ['signedUp', 'inactive14d', 'subscriptionCanceled', 'weekOne', 'nps30', 'months3'];
$withP = []; $withQ = []; $long = [];
foreach ($cat as $k => $a) foreach (ML_LANGS as $l) {
    $b = $a['content'][$l]['body'];
    if (strpos($b, "\n\n{progress}\n\n") !== false) $withP[$k][] = $l;
    foreach (ml_questions($b) as $Q) { $withQ[$k][] = $l; foreach ($Q['opts'] as $o) if (mb_strlen($o) > 45) $long[] = "$k/$l: $o"; if ($Q['question'] === '') $long[] = "$k/$l: no question"; }
}
$ok(array_keys($withP) === $prog && count(array_filter($withP, fn($x) => $x === ML_LANGS)) === 10, '{progress} on its own line in the 10 texts (8 + 2 feedback emails), EN, FR and ES (' . implode(', ', array_keys($withP)) . ')');
$ok(array_keys($withQ) === $asks && count(array_filter($withQ, fn($x) => array_values(array_unique($x)) === ML_LANGS)) === 6, 'a one-click question in the welcome, the 14-day absence, the cancellation and 3 feedback emails only, in the 3 languages');
$ok($long === [], 'each option short, each question asked by the paragraph above' . ($long ? ' (' . implode(' · ', $long) . ')' : ''));
$fr = ml_questions($cat['signedUp']['content']['fr']['body'])[0];
$ok($fr['question'] === 'Une dernière chose : qu’est-ce qui t’amène dans Sweep ? Un clic suffit.' && count($fr['opts']) === 5 && $fr['opts'][4] === 'Autre chose', 'welcome FR: « qu’est-ce qui t’amène » with 5 chips, the last « Autre chose »');

// the earlier texts: the new ones without {progress} nor the questions, as their fingerprints say
$before = (array) require $app . '/mail/mail-auto-texts-before.php';
$old = function (string $k) use ($cat): array {
    $c = ml_clean_content($cat[$k]['content']);
    foreach (ML_LANGS as $l) $c[$l]['body'] = ml_without_questions(str_replace("\n\n{progress}", '', $c[$l]['body']));
    return $c;
};
$miss = [];
foreach ($before[1] as $k => $_) foreach (ML_LANGS as $i => $l) if (!isset($cat[$k]) || $before[1][$k][$i] !== ma_text_sig($old($k)[$l])) $miss[] = "$k/$l";   // the automations of version 1
$ok(count($before[1]) === 18 && $miss === [], 'the 54 earlier texts are the new ones without {progress} nor the questions' . ($miss ? ' (' . implode(', ', $miss) . ')' : ''));

/* ───── ma_upgrade ───── */
$row = fn(string $k) => $pdo->query("SELECT content_json, proposed_json FROM mail_campaigns WHERE auto = '$k'")->fetch();
$content = fn(string $k) => json_decode($row($k)['content_json'], true);
// a fresh install: seeded with the new texts, nothing to do
ma_seed($pdo);
$ok(ml_setting($pdo, 'mail_auto_texts_v') === (string) MA_TEXTS_V && $content('signedUp') === ml_clean_content($cat['signedUp']['content'])
    && (int) $pdo->query('SELECT COUNT(*) FROM mail_campaigns WHERE proposed_json IS NOT NULL')->fetchColumn() === 0, 'a fresh install: the new texts, nothing proposed');
// a server on version 1: our earlier texts, Mateo changed the 14-day FR and the welcome EN
$set = $pdo->prepare('UPDATE mail_campaigns SET content_json = ? WHERE auto = ?');
foreach (array_keys($before[1]) as $k) $set->execute([json_encode($old($k), JSON_UNESCAPED_UNICODE), $k]);
$mine = $old('inactive14d'); $mine['fr']['body'] = "Salut {first}, ton journal t’attend.\n\n[[Revenir|{app}#dashboard]]"; $set->execute([json_encode($mine, JSON_UNESCAPED_UNICODE), 'inactive14d']);
$mine2 = $old('signedUp'); $mine2['en']['subject'] = 'Welcome aboard, {first}'; $set->execute([json_encode($mine2, JSON_UNESCAPED_UNICODE), 'signedUp']);
$pdo->exec("UPDATE app_settings SET v = '1' WHERE k = 'mail_auto_texts_v'");
$r = ma_upgrade($pdo);
$ok($r === [28, 2], 'version 1 → 2: 28 languages replaced (10 texts changed × 3, less 2), 2 proposed (' . json_encode($r) . ')');
$c14 = $content('inactive14d'); $p14 = json_decode((string) $row('inactive14d')['proposed_json'], true);
$ok($c14['fr'] === $mine['fr'] && $c14['en'] === ml_clean_content($cat['inactive14d']['content'])['en'] && array_keys($p14) === ['fr'] && $p14['fr'] === ml_clean_content($cat['inactive14d']['content'])['fr'],
    '14 days: Mateo’s FR kept, the new FR proposed; EN and ES replaced');
$ok($content('signedUp')['en']['subject'] === 'Welcome aboard, {first}' && $content('signedUp')['fr'] === ml_clean_content($cat['signedUp']['content'])['fr'], 'welcome: Mateo’s EN kept, FR replaced');
$ok($content('profileCompleted') === ml_clean_content($cat['profileCompleted']['content']) && $content('tradesMilestone') === ml_clean_content($cat['tradesMilestone']['content']), 'the unchanged texts stay, the others take the new version');
$ok(ma_upgrade($pdo) === [0, 0] && ml_setting($pdo, 'mail_auto_texts_v') === '2', 'once per version: a second run does nothing');
$id14 = (int) $pdo->query("SELECT id FROM mail_campaigns WHERE auto = 'inactive14d'")->fetchColumn(); $idW = (int) $pdo->query("SELECT id FROM mail_campaigns WHERE auto = 'signedUp'")->fetchColumn();
$c = ml_campaign($pdo, $id14);
$ok(array_keys($c['proposed']) === ['fr'] && ml_campaign($pdo, (int) $pdo->query("SELECT id FROM mail_campaigns WHERE auto = 'inactive3d'")->fetchColumn())['proposed'] === null, 'ml_campaign: the proposal, by language (null without one)');
$ov = array_column(ml_overview($pdo)['autos'], 'proposed', 'auto');
$ok($ov['inactive14d'] === true && $ov['signedUp'] === true && $ov['inactive3d'] === false, 'the list of automations knows which have a new version');
ml_campaign_proposal($pdo, $c, true);
$ok($content('inactive14d') === ml_clean_content($cat['inactive14d']['content']) && $row('inactive14d')['proposed_json'] === null, 'taken: the new version in place, the proposal gone');
ml_campaign_proposal($pdo, ml_campaign($pdo, $idW), false);
$ok($content('signedUp')['en']['subject'] === 'Welcome aboard, {first}' && $row('signedUp')['proposed_json'] === null, 'set aside: Mateo’s text stays, the proposal gone');

/* ───── one request for an opinion every 30 days ───── */
foreach (array_keys($cat) as $k) $set->execute([json_encode(ml_clean_content($cat[$k]['content']), JSON_UNESCAPED_UNICODE), $k]);
$pdo->exec("INSERT INTO users (id, username, email, lang, first_name, created_at) VALUES ('u1', 'u1', 'u1@x.test', 'en', 'Ana', '2026-10-01 00:00:00')");
$camp = fn(string $k) => (int) $pdo->query("SELECT id FROM mail_campaigns WHERE auto = '$k'")->fetchColumn();
$n = 0;
$send = function ($cid) use ($pdo, &$n): array {
    $n++; $now = time();
    $pdo->prepare("INSERT INTO mail_queue (campaign_id, user_id, email, lang, first_name, kind, token, state, next_at, created_at, vars_json) VALUES (?, 'u1', 'u1@x.test', 'en', 'Ana', 'marketing', ?, 'sending', ?, ?, ?)")
        ->execute([$cid, 'tok' . $n, $now, $now, json_encode(['plan' => 'Pro'])]);
    $q = $pdo->query('SELECT * FROM mail_queue ORDER BY id DESC LIMIT 1')->fetch(); $camps = [];
    $m = ml_compose($pdo, $q, $camps);
    $pdo->prepare("UPDATE mail_queue SET state = 'sent', sent_at = ? WHERE id = ?")->execute([$now, $q['id']]);
    return ['text' => $m[2], 'asked' => (int) $pdo->query('SELECT COALESCE(asked, 0) FROM mail_queue WHERE id = ' . (int) $q['id'])->fetchColumn(), 'id' => (int) $q['id']];
};
$w = $send($camp('signedUp'));
$ok(strpos($w['text'], 'what brings you to Sweep?') !== false && strpos($w['text'], 'api/m/r/tok') !== false && $w['asked'] === 0, 'welcome: its question, never counted as a request for an opinion');
$a = $send($camp('inactive14d'));
$ok(strpos($a['text'], 'what stopped you?') !== false && strpos($a['text'], 'Not trading right now: https://app.test/api/m/r/') !== false && $a['asked'] === 1, '14 days away: asked « what stopped you? », counted');
$b = $send($camp('subscriptionCanceled'));
$ok(strpos($b['text'], 'why did you cancel') === false && strpos($b['text'], 'api/m/r/') === false && strpos($b['text'], 'My subscription: ') !== false && substr_count($b['text'], "\n\n\n") === 0 && $b['asked'] === 0,
    'cancellation the same week: sent without its question nor the paragraph that asks it, the button kept');
$w2 = $send($camp('signedUp'));
$ok(strpos($w2['text'], 'what brings you to Sweep?') !== false, 'the welcome’s question is never held');
$pdo->exec("INSERT INTO mail_campaigns (name, status, content_json, audience_json, created_at, updated_at) VALUES ('Poll', 'sending', '" . json_encode(['en' => ['subject' => 'Poll', 'preheader' => '', 'body' => "Which one?\n\n[[?choice|A|B]]"]]) . "', '{}', 1, 1)");
$p = $send((int) $pdo->lastInsertId());
$ok(strpos($p['text'], 'A: https://app.test/api/m/r/') !== false && $p['asked'] === 1, 'a campaign Mateo sends: never held, counted');
$pdo->prepare('UPDATE mail_queue SET sent_at = ? WHERE asked = 1')->execute([time() - 31 * 86400]);
$c2 = $send($camp('subscriptionCanceled'));
$ok(strpos($c2['text'], 'why did you cancel? One click is enough.') !== false && $c2['asked'] === 1, '31 days later: asked again');
$ok(ml_without_questions("Hi\n\n[[Go|https://x.test]]\n\n[[?note]]\n\nBye") === "Hi\n\n[[Go|https://x.test]]\n\nBye", 'a question right under a button: the button stays');

foreach (glob($tmp . '/*') as $x) @unlink($x); @rmdir($tmp);
echo "\n$pass passed, $fail failed\n";
exit($fail ? 1 : 0);
