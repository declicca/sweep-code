<?php
declare(strict_types=1);
/**
 * Sweep — what each trader uses (feedback brief, step 2), on a throwaway SQLite database:
 *   php tests/mail_usage_test.php
 *  - the profile: days used in 30 days for each feature (New York days, an older use only « ever »), import and sync apart
 *    from a trade by hand, the AI coach's tasks only, payouts and firm rules from the documents, sample data never;
 *  - the most used (the firm rules aside), the trades of the last 7 days (a copy once), the streak;
 *  - the values: {top_feature}, {trades_week}, {streak}, {progress} in EN / FR / ES, {progress} empty when nothing is true
 *    (its line then gone from the email); an email that uses them gets them at sending, the others are not computed;
 *  - Admin › Emails « What they use »: the active traders, Sweep's own aside, the share for each feature; the daily run.
 */
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
$app = dirname(__DIR__);
putenv('SWEEP_TEST_DB');
$pdo = new PDO('sqlite::memory:', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC]);
$pdo->exec('CREATE TABLE users (id TEXT PRIMARY KEY, username TEXT, email TEXT, lang TEXT, first_name TEXT, created_at TEXT, last_login TEXT, disabled INTEGER DEFAULT 0, is_admin INTEGER DEFAULT 0, is_internal INTEGER DEFAULT 0)');
$pdo->exec('CREATE TABLE app_settings (k TEXT PRIMARY KEY, v TEXT NOT NULL)');
function db(): PDO { global $pdo; return $pdo; }
$GLOBALS['cfg'] = $cfg = ['app_url' => 'https://app.test/'];
require $app . '/mail/mail-core.php';
$pass = 0; $fail = 0;
$ok = function (bool $c, string $what) use (&$pass, &$fail) { echo ($c ? 'ok   ' : 'FAIL ') . $what . "\n"; $c ? $pass++ : $fail++; };
$now = time(); $D = 86400;
foreach ([['u1', 'fr', 0], ['u2', 'en', 0], ['u3', 'en', 0], ['me', 'fr', 1]] as [$id, $l, $in])
    $pdo->prepare('INSERT INTO users (id, username, email, lang, first_name, created_at, is_internal) VALUES (?, ?, ?, ?, ?, ?, ?)')->execute([$id, $id, "$id@t.dev", $l, ucfirst($id), '2026-09-01T00:00:00Z', $in]);
ml_schema($pdo);

// the app's own tables, as it keeps them
$pdo->exec('CREATE TABLE game_analytics (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL, event VARCHAR(40) NOT NULL, meta_json TEXT NULL, created_at INT NOT NULL)');
$pdo->exec('CREATE TABLE ai_log (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL, task TEXT NOT NULL, input_tokens INTEGER NOT NULL DEFAULT 0, output_tokens INTEGER NOT NULL DEFAULT 0, cost_usd REAL NOT NULL DEFAULT 0, created_at TEXT NOT NULL)');
$pdo->exec('CREATE TABLE documents (user_id TEXT NOT NULL, collection TEXT NOT NULL, id TEXT NOT NULL, data TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL, PRIMARY KEY (user_id, collection, id))');
$pdo->exec('CREATE TABLE user_game_profile (user_id TEXT PRIMARY KEY, streak_current INT NOT NULL DEFAULT 0)');
$ev = fn(string $u, string $e, int $ago, array $meta = []) => $pdo->prepare('INSERT INTO game_analytics (user_id, event, meta_json, created_at) VALUES (?, ?, ?, ?)')->execute([$u, $e, $meta ? json_encode($meta) : null, $now - $ago]);
$doc = fn(string $u, string $col, string $id, array $d, int $ago) => $pdo->prepare('INSERT INTO documents VALUES (?, ?, ?, ?, ?, ?)')->execute([$u, $col, $id, json_encode($d), gmdate('Y-m-d\TH:i:s\Z', $now - $ago), gmdate('Y-m-d\TH:i:s\Z', $now - $ago)]);
$ny = fn(int $ago) => (new DateTimeImmutable('@' . ($now - $ago)))->setTimezone(new DateTimeZone('America/New_York'))->format('Y-m-d');
// u1: trades by hand on 3 days (two the same day), one synced, 5 morning plans, a review, the stats, the coach, a share, a payout…
foreach ([1, 1, 3, 9] as $d) $ev('u1', 'trade_logged', $d * $D, ['method' => 'manual']);
$ev('u1', 'trade_logged', 2 * $D, ['method' => 'executions']);
foreach ([1, 2, 3, 4, 5] as $d) $ev('u1', 'plan_saved', $d * $D);
$ev('u1', 'review_saved', $D); $ev('u1', 'stats_viewed', 2 * $D); $ev('u1', 'share_card_created', 3 * $D);
$ev('u1', 'weekly_opened', 40 * $D);   // too old: ever, not in 30 days
$ev('u1', 'level_up', $D);             // not a feature
$pdo->prepare('INSERT INTO ai_log (user_id, task, created_at) VALUES (?, ?, ?), (?, ?, ?)')->execute(['u1', 'chat', gmdate('Y-m-d H:i:s', $now - $D), 'u1', 'trade_import', gmdate('Y-m-d H:i:s', $now - $D)]);
$doc('u1', 'payouts', 'p1', ['amount' => 1000], 4 * $D); $doc('u1', 'payouts', 'pd', ['amount' => 9, 'demo' => true], 4 * $D);
$doc('u1', 'accounts', 'a1', ['preset' => 'apex|eod50'], 20 * $D);
$doc('u1', 'trades', 't1', ['date' => $ny(1 * $D)], $D); $doc('u1', 'trades', 't2', ['date' => $ny(2), 'copy_group' => 'g'], 2 * $D); $doc('u1', 'trades', 't3', ['date' => $ny(2), 'copy_group' => 'g'], 2 * $D);
$doc('u1', 'trades', 't4', ['date' => $ny(3), 'demo' => true], 3 * $D); $doc('u1', 'trades', 't5', ['date' => $ny(20 * $D)], 20 * $D);
$doc('u1', 'trades', 't6', ['date' => $ny(30 * $D)], $D);   // an old trade imported yesterday
$pdo->exec("INSERT INTO user_game_profile VALUES ('u1', 4), ('u3', 0)");
// u3: only the AI coach, on 3 days; me: Sweep's own account
foreach ([1, 2, 6] as $d) $pdo->prepare('INSERT INTO ai_log (user_id, task, created_at) VALUES (?, ?, ?)')->execute(['u3', 'day_debrief', gmdate('Y-m-d H:i:s', $now - $d * $D)]);
$ev('me', 'plan_saved', $D);

// 1. the profile
$p = mu_profile($pdo, 'u1', $now);
$ok($p['days']['journal'] === count(array_unique([$ny($D), $ny(3 * $D), $ny(9 * $D), $ny(2 * $D)])) && $p['days']['sync'] === 1, 'journal: the days with a trade (by hand or synced), sync: the synced day only (' . json_encode($p['days']) . ')');
$ok($p['days']['plan'] === 5 && $p['days']['review'] === 1 && $p['days']['stats'] === 1 && $p['days']['share'] === 1 && $p['days']['weekly'] === 0, 'plan 5 days, review, stats, share 1, the weekly recap of 40 days ago not in 30 days');
$ok($p['days']['coach'] === 1 && $p['days']['payouts'] === 1 && $p['days']['rules'] === 1, 'the coach (chat, not the import), a real payout (not the sample one), firm rules (an account on a preset)');
$ok(in_array('weekly', $p['ever'], true) && !in_array('level', $p['ever'], true) && count($p['ever']) === 10, 'ever: all ten, the old weekly recap included (' . implode(',', $p['ever']) . ')');
$ok($p['top'] === 'plan', 'the most used: the morning plan (5 days, more than the journal)');
$ok($p['trades_week'] === 2 && $p['streak'] === 4, 'trades of the last 7 days: 2 (a copy once, sample data and older trades aside); streak 4 (' . $p['trades_week'] . ')');
$p2 = mu_profile($pdo, 'u2', $now);
$ok($p2['top'] === '' && $p2['trades_week'] === 0 && !array_filter($p2['days']) && $p2['ever'] === [], 'a trader who did nothing: nothing');

// 2. the values
$ok(mu_progress($p, 'fr') === 'Cette semaine : 2 trades journalisés, 4 jours d’affilée.' && mu_progress($p, 'en') === 'This week: 2 trades journaled, 4 days in a row.'
    && mu_progress($p, 'es') === 'Esta semana: 2 operaciones registradas, 4 días seguidos.', '{progress}: the week and the streak, in the 3 languages');
$ok(mu_progress(['trades_week' => 1, 'streak' => 1] + $p, 'fr') === 'Cette semaine : 1 trade journalisé.', 'one trade, no streak of one day');
$ok(mu_progress(['trades_week' => 0, 'streak' => 3] + $p, 'en') === '3 days in a row in Sweep.', 'no trade this week: the streak');
$p3 = mu_profile($pdo, 'u3', $now);
$ok($p3['top'] === 'coach' && mu_progress($p3, 'fr') === 'Ce mois-ci, tu as utilisé le coach IA 3 jours.', 'else the most used: « Ce mois-ci, tu as utilisé le coach IA 3 jours. »');
$ok(mu_progress($p2, 'en') === '' && mu_vars($p2, 'en') === ['top_feature' => '', 'trades_week' => '0', 'streak' => '0', 'progress' => ''], 'nothing true to say: empty');
$V = mu_vars($p, 'es');
$ok($V['top_feature'] === 'el plan de la mañana' && $V['trades_week'] === '2' && $V['streak'] === '4', '{top_feature} {trades_week} {streak} in Spanish');
$body = "Hola {first},\n\n{progress}\n\nTu función: {top_feature}.";
[, $t, $h] = ml_render($pdo, ['subject' => 's', 'preheader' => '', 'body' => $body], 'en', 'Ben', '', false, mu_vars($p2, 'en'));
[, , $h0] = ml_render($pdo, ['subject' => 's', 'preheader' => '', 'body' => "Hola {first},\n\nTu función: {top_feature}."], 'en', 'Ben', '', false, mu_vars($p2, 'en'));
$ok($h === $h0 && strpos($t, "\n\n\n\n") === false, '{progress} empty: its paragraph is gone from the email');

// 3. at sending
$cid = ml_campaign_save($pdo, null, ['name' => 'Bilan', 'content' => ['fr' => ['subject' => '{trades_week} trades', 'preheader' => '', 'body' => "Salut {first},\n\n{progress}"], 'en' => ['subject' => 'Hi', 'preheader' => '', 'body' => 'Hello {first}']], 'audience' => []])['id'];
ml_q($pdo, "UPDATE mail_campaigns SET status = 'sending' WHERE id = ?", [$cid]);
$queue = function (string $uid, string $lang) use ($pdo, $cid) { $t = ml_token(); ml_q($pdo, "INSERT INTO mail_queue (campaign_id, user_id, email, lang, first_name, kind, token, state, next_at, created_at) VALUES (?, ?, ?, ?, ?, 'marketing', ?, 'queued', 0, ?)", [$cid, $uid, "$uid@t.dev", $lang, ucfirst($uid), $t, time()]); return ml_q($pdo, 'SELECT * FROM mail_queue WHERE token = ?', [$t])->fetch(); };
$camps = []; $m = ml_compose($pdo, $queue('u1', 'fr'), $camps);
$ok($m && $m[1] === '2 trades' && strpos(str_replace("\u{00A0}", ' ', $m[2]), 'Cette semaine : 2 trades journalisés, 4 jours d’affilée.') !== false, 'an email that uses them: filled in at sending, in its language (« ' . ($m[1] ?? '') . ' »)');
$ok((int) ml_q($pdo, "SELECT COUNT(*) FROM mail_usage WHERE user_id = 'u1'")->fetchColumn() === 1, '… and the profile kept');
ml_compose($pdo, $queue('u2', 'en'), $camps);
$ok((int) ml_q($pdo, "SELECT COUNT(*) FROM mail_usage WHERE user_id = 'u2'")->fetchColumn() === 0, 'an email that does not use them: nothing computed');
$ex = mu_example('fr');
$ok($ex['top_feature'] === 'le plan du matin' && $ex['progress'] === 'Cette semaine : 12 trades journalisés, 4 jours d’affilée.', 'the preview\'s example');

// 4. Admin › Emails « What they use »
$ml = mu_daily($pdo, $now);
$S = mu_summary($pdo, $now); $by = array_column($S['features'], null, 'key');
$ok($ml === 4 && $S['active'] === 2, 'the daily run: every trader (4); active in 30 days: 2 (u1, u3; u2 did nothing, Sweep\'s own aside)');
$ok($by['coach']['pct'] === 100 && $by['plan']['pct'] === 50 && $by['weekly']['pct'] === 0 && $S['features'][0]['key'] === 'coach', 'the share for each feature, the most used first (' . json_encode(array_column($S['features'], 'pct', 'key')) . ')');
$ok($by['payouts']['name']['fr'] === 'Payouts (argent reçu d’une firme)' && $by['sync']['name']['es'] === 'Importación y sincronización', 'its names in the 3 languages, the jargon explained');
$pdo->exec("DELETE FROM users WHERE id = 'u3'"); mu_daily($pdo, $now + 4 * $D);
$ok((int) ml_q($pdo, "SELECT COUNT(*) FROM mail_usage WHERE user_id = 'u3'")->fetchColumn() === 0, 'a deleted trader leaves the table at the next runs');

echo "\n$pass passed, $fail failed\n";
exit($fail ? 1 : 0);
