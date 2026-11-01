<?php
declare(strict_types=1);
/**
 * Sweep — the « Month in Review » (1 Nov., brief avance 6), on a throwaway SQLite database (never the live one):
 *   php tests/month_review_test.php
 * The clock is pinned (SWEEP_GAME_NOW, New York time); Sweep AI answers from a mock file (SWEEP_AI_MONTH_MOCK), never Google.
 *  - a winning month built from crafted trades: every value of the snapshot checked exactly (net, win rate, split Evaluation ·
 *    Funded · Live, the curve day by day, best and toughest trade, the discipline bars, best session and setup, journaled days,
 *    streak); a copied trade once, example data left out, the platform-balance line in the P&L only, an evening trade in the
 *    next session (18:00 ET), an archived account included;
 *  - a losing month; under 3 trading days with a trade: no recap;
 *  - when: not before the last trading day's 17:00 ET close, at once if that day is reviewed earlier; the previous month later;
 *  - frozen: a trade added afterwards changes nothing; an old Wrapped row stays as it was;
 *  - the AI part: written once with the snapshot (one call, in the trader's language), its quote really the trader's, skipped on
 *    an error, with the allowance used up or the AI off; the Today card until seen to its end, at most the 7th of the next month.
 */
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
$app = dirname(__DIR__);
$tmp = sys_get_temp_dir() . '/sweep-month-' . bin2hex(random_bytes(4)); mkdir($tmp);
$pdo = new PDO('sqlite:' . $tmp . '/t.db', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC]);
function db() { global $pdo; return $pdo; }
$pdo->exec('CREATE TABLE documents (user_id TEXT NOT NULL, collection TEXT NOT NULL, id TEXT NOT NULL, data TEXT NOT NULL, created_at TEXT, updated_at TEXT, PRIMARY KEY (user_id, collection, id))');
$pdo->exec('CREATE TABLE users (id TEXT PRIMARY KEY, username TEXT, lang TEXT, email TEXT, first_name TEXT, disabled INT DEFAULT 0)');
// the AI: a test configuration (a fake key, 2 calls a day, no pause between calls) and the mock answers
file_put_contents($tmp . '/ai.php', "<?php return ['api_key' => 'test-only', 'user_daily_limit' => 2, 'min_seconds_between_calls' => 0];");
putenv('SWEEP_AI_CONFIG=' . $tmp . '/ai.php'); putenv('SWEEP_AI_OFFLINE=1');
$mock = $tmp . '/mock.json';
$mockOk = ['en' => ['month' => 'A steady month. You kept to your plan on half your trades.', 'edge' => 'ORB in the New York morning.', 'cost' => 'Two trades against the stop.',
    'journal' => 'Waited for the retest before entering.', 'next' => 'Write one line after every losing trade.'],
  'fr' => ['month' => 'Un mois régulier. Ton plan tenu sur la moitié de tes trades.', 'edge' => 'L’ORB le matin à New York.', 'cost' => 'Deux trades contre le stop.',
    'journal' => 'Waited for the retest before entering.', 'next' => 'Écris une ligne après chaque trade perdant.']];
file_put_contents($mock, json_encode($mockOk)); putenv('SWEEP_AI_MONTH_MOCK=' . $mock);
require $app . '/notify/notify.php';
require $app . '/game/game.php';
GameEngine::setPdo($pdo); GameEngine::schema(); GameV2::schema(); GameV2b::schema();
$pass = 0; $fail = 0;
$ok = function (bool $c, string $what) use (&$pass, &$fail) { echo ($c ? 'ok   ' : 'FAIL ') . $what . "\n"; $c ? $pass++ : $fail++; };
$at = function (string $ny) { putenv('SWEEP_GAME_NOW=' . $ny); };
$doc = function (string $uid, string $col, string $id, array $d) use ($pdo) { $pdo->prepare('INSERT OR REPLACE INTO documents (user_id, collection, id, data, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)')->execute([$uid, $col, $id, json_encode($d + ['id' => $id]), $d['created_at'] ?? '2026-10-01T00:00:00.000Z', '']); GameEngine::forget($uid); };
$day = fn(string $uid, string $d, array $f) => $pdo->prepare('INSERT OR REPLACE INTO game_days (user_id, trading_day, plan_valid, review_done, is_valid_streak, is_swept, activity, detail_json, updated_at) VALUES (?, ?, ?, ?, ?, ?, 1, ?, 0)')
    ->execute([$uid, $d, $f['plan'] ?? 0, $f['review'] ?? 0, $f['streak'] ?? 0, $f['swept'] ?? 0, json_encode(['trades' => $f['ok'] ?? []])]);
$row = fn(string $uid, string $m) => $pdo->query("SELECT * FROM monthly_wrapped WHERE user_id = " . $pdo->quote($uid) . " AND month = " . $pdo->quote($m))->fetch() ?: null;
$snap = function (string $uid, string $m) use ($row) { $r = $row($uid, $m); return $r ? json_decode($r['data_json'], true) : null; };
$aiCalls = fn(string $uid) => (int) $pdo->query("SELECT COUNT(*) FROM ai_log WHERE task = 'month_review' AND user_id = " . $pdo->quote($uid))->fetchColumn();
$T = fn(array $x) => $x + ['instrument' => 'NQ', 'direction' => 'long', 'contracts' => 1, 'session_date' => true];

/* ── the winning month: October 2026 for u1 ── */
$month = function (string $uid) use ($doc, $day, $T) {
    $doc($uid, 'accounts', 'E', ['name' => 'Eval 50K', 'money_type' => 'eval']);
    $doc($uid, 'accounts', 'F', ['name' => 'Funded 50K', 'phase' => 'funded', 'status' => 'archived', 'result' => 'failed']);   // archived and failed: still in its month
    $doc($uid, 'accounts', 'L', ['name' => 'Live', 'money_type' => 'live']);
    $doc($uid, 'trades', 't1', $T(['date' => '2026-10-26', 'entry_time' => '09:45', 'pnl_c' => 50000, 'setup' => 'ORB', 'account_id' => 'E', 'grade' => 'A', 'discipline' => ['plan' => 'y', 'stop' => 'y'], 'notes' => 'Waited for the retest before entering.']));
    $doc($uid, 'trades', 't2', $T(['date' => '2026-10-26', 'entry_time' => '10:30', 'direction' => 'short', 'pnl_c' => -20000, 'setup' => 'ORB', 'account_id' => 'F', 'grade' => 'B', 'discipline' => ['plan' => 'y', 'stop' => 'n']]));
    // a copy group: the original (earliest created) on E, its copy on F; one trade
    $doc($uid, 'trades', 't3', $T(['date' => '2026-10-27', 'entry_time' => '09:50', 'instrument' => 'ES', 'pnl_c' => 31000, 'setup' => 'VWAP', 'account_id' => 'E', 'grade' => 'A', 'copy_group' => 'g1', 'created_at' => '2026-10-27T13:50:00.000Z']));
    $doc($uid, 'trades', 't3b', $T(['date' => '2026-10-27', 'entry_time' => '09:50', 'instrument' => 'ES', 'pnl_c' => 31000, 'setup' => 'VWAP', 'account_id' => 'F', 'grade' => 'A', 'copy_group' => 'g1', 'created_at' => '2026-10-27T13:50:00.500Z']));
    $doc($uid, 'trades', 't4', $T(['date' => '2026-10-28', 'entry_time' => '13:30', 'pnl_c' => -10000, 'setup' => 'VWAP', 'account_id' => 'F', 'grade' => 'C', 'discipline' => ['stop' => 'n'], 'review' => ['lesson' => 'Moved my stop too early.']]));
    $doc($uid, 'trades', 't5', $T(['date' => '2026-10-28', 'entry_time' => '10:05', 'pnl_c' => 25000, 'fees_c' => 500, 'setup' => 'ORB', 'account_id' => 'L', 'grade' => 'A']));
    $doc($uid, 'trades', 'gap', ['date' => '2026-10-28', 'session_date' => true, 'untracked' => true, 'pnl_c' => -1500, 'account_id' => 'L']);   // « Trades not detailed »: in the P&L only
    $doc($uid, 'trades', 'demo1', $T(['date' => '2026-10-27', 'entry_time' => '11:00', 'pnl_c' => 999900, 'account_id' => 'E', 'demo' => true]));   // example data: never
    $doc($uid, 'trades', 't6', ['date' => '2026-09-30', 'entry_time' => '19:30', 'instrument' => 'NQ', 'direction' => 'long', 'contracts' => 1, 'pnl_c' => 5000, 'account_id' => 'E']);   // entered Sept 30 at 19:30 ET: the Oct 1 session
    $doc($uid, 'trades', 'nov', $T(['date' => '2026-11-02', 'entry_time' => '10:00', 'pnl_c' => 7000, 'account_id' => 'E']));   // next month: never
    $day($uid, '2026-10-01', ['streak' => 1]);
    $day($uid, '2026-10-26', ['plan' => 1, 'review' => 1, 'streak' => 1, 'swept' => 1, 'ok' => [['id' => 't1', 'ok' => true], ['id' => 't2', 'ok' => false]]]);
    $day($uid, '2026-10-27', ['streak' => 1]);
    $day($uid, '2026-10-28', ['plan' => 1, 'review' => 1, 'streak' => 1, 'ok' => [['id' => 't4', 'ok' => false], ['id' => 't5', 'ok' => true]]]);
};
foreach (['u1', 'u2', 'u3', 'u4', 'u5', 'u6', 'u7', 'u8'] as $u) { $at('2026-09-01 08:00'); GameEngine::profile($u); }
$month('u1');

// when: Thursday evening, Friday before the close: no recap; Friday 17:00 ET (the last trading day's close): created
$ok(GameWrapped::lastMarketDay('2026-10') === '2026-10-30' && GameWrapped::lastMarketDay('2026-05') === '2026-05-29', 'the month\'s last trading day: Friday Oct 30, Friday May 29 (the 31st is a Sunday)');
$at('2026-10-29 20:00'); GameWrapped::ensure('u1', 'en'); $ok($row('u1', '2026-10') === null, 'Thursday Oct 29 20:00 ET: October not over, no recap');
$at('2026-10-30 16:59'); GameWrapped::ensure('u1', 'en'); $ok($row('u1', '2026-10') === null, 'Friday Oct 30 16:59 ET, the day not reviewed: no recap yet');
$at('2026-10-30 17:00'); GameWrapped::ensure('u1', 'en'); $d = $snap('u1', '2026-10');
$ok($d !== null && ($d['v'] ?? 0) === 2, 'Friday Oct 30 17:00 ET (the close): the Month in Review is created, snapshot v 2');

// every value
$ok($d['trades'] === 6 && $d['days'] === 4, 'trades 6 (copy once, no example trade, no balance line, the evening trade in) over 4 trading days (Oct 1, 26, 27, 28): ' . $d['trades'] . ' / ' . $d['days']);
$ok($d['net'] === 79000, 'net +$790.00 (P&L − fees, the balance line in, the copy once): ' . $d['net']);
$ok($d['winners'] === 4 && $d['losers'] === 2 && $d['win_rate'] === 67, 'winners 4, losers 2, win rate 67 %: ' . json_encode([$d['winners'], $d['losers'], $d['win_rate']]));
$ok($d['split'] === ['eval' => 86000, 'funded' => -30000, 'live' => 23000], 'split Evaluation +$860 · Funded −$300 (archived account included) · Live +$230: ' . json_encode($d['split']));
$ok($d['curve'] === [['d' => '2026-10-01', 'v' => 5000, 'c' => 5000], ['d' => '2026-10-26', 'v' => 30000, 'c' => 35000], ['d' => '2026-10-27', 'v' => 31000, 'c' => 66000], ['d' => '2026-10-28', 'v' => 13000, 'c' => 79000]], 'the curve day by day: ' . json_encode($d['curve']));
$ok($d['best_day'] === ['d' => '2026-10-27', 'v' => 31000] && $d['worst_day'] === null, 'best day Oct 27 +$310; no losing day: no worst day (' . json_encode([$d['best_day'], $d['worst_day']]) . ')');
$ok($d['best_trade'] === ['date' => '2026-10-26', 'instrument' => 'NQ', 'direction' => 'long', 'setup' => 'ORB', 'note' => 'Waited for the retest before entering.', 'pnl' => 50000], 'best trade: Oct 26 NQ long ORB +$500 with its note: ' . json_encode($d['best_trade']));
$ok($d['tough_trade'] === ['date' => '2026-10-26', 'instrument' => 'NQ', 'direction' => 'short', 'setup' => 'ORB', 'note' => '', 'pnl' => -20000], 'toughest trade: Oct 26 NQ short −$200, no note: ' . json_encode($d['tough_trade']));
$tr = array_values(array_filter(GameEngine::onePerCopyGroup(array_values(GameEngine::docs('u1', 'trades'))), fn($t) => empty($t['untracked']) && ($t['date'] >= '2026-09-30' && $t['date'] <= '2026-10-31')));
$bars = array_column($d['how']['bars'], 'pct', 'k');
$ok($bars['plan'] === 50 && $bars['check'] === 60 && $bars['grade'] === 80 && $bars['disc'] === GameWeeklyMail::coachDisc('u1', $tr), 'bars: in the plan 50 %, checklist yes 60 %, graded A/B 80 %, clean trades = the coach\'s discipline (' . json_encode($d['how']['bars']) . ')');
$ok($d['how']['session'] === 'nyam' && $d['how']['setup'] === 'ORB', 'best session New York AM, best setup ORB: ' . json_encode([$d['how']['session'], $d['how']['setup']]));
$ok($d['how']['journaled'] === 2 && $d['how']['traded'] === 4 && $d['how']['streak'] === 3 && $d['swept'] === 1 && $d['market_days'] === 22, 'journaled 2 of 4 days, longest streak 3, 1 swept day, 22 market days: ' . json_encode([$d['how'], $d['swept'], $d['market_days']]));
$ok(!isset($d['_notes']), 'the notes sent to the AI are not stored');

// the AI part: once, in the trader's language, the quote really theirs
$ok(($d['ai']['next'] ?? null) === 'Write one line after every losing trade.' && ($d['ai']['journal'] ?? null) === 'Waited for the retest before entering.' && ($d['ai']['lang'] ?? null) === 'en', 'the AI part stored with the snapshot (EN), its quote from the trader\'s notes: ' . json_encode($d['ai']));
$at('2026-10-30 18:30'); GameWrapped::ensure('u1', 'en'); GameWrapped::ensure('u1', 'fr');
$ok($aiCalls('u1') === 1, 'opened again (twice): never generated again, 1 AI call in all (' . $aiCalls('u1') . ')');

// frozen
$doc('u1', 'trades', 'late', $T(['date' => '2026-10-29', 'entry_time' => '10:00', 'pnl_c' => -90000, 'account_id' => 'E']));
GameWrapped::ensure('u1', 'en'); $d2 = $snap('u1', '2026-10');
$ok($d2['net'] === 79000 && $d2['trades'] === 6 && GameWrapped::build('u1', '2026-10')['net'] === -11000, 'frozen: a trade added afterwards changes nothing in the snapshot (the month rebuilt would say −$110)');

// the Today card: until seen to its end, at most the 7th of November
$c = GameWrapped::card('u1');
$ok($c === ['month' => '2026-10', 'done' => false, 'mission' => 'Write one line after every losing trade.'], 'the Today card « Your October is ready » (' . json_encode($c) . ')');
GameWrapped::viewed('u1', '2026-10');
$ok(GameWrapped::card('u1')['done'] === false && GameWrapped::state('u1')['items'][0]['new'] === false, 'opened only: the card stays (not seen to its end)');
GameWrapped::viewed('u1', '2026-10', true);
$ok(GameWrapped::card('u1')['done'] === true && (bool) $row('u1', '2026-10')['done_at'], 'seen to its end: done (the card goes, its mission may be proposed)');
$at('2026-11-07 23:00'); $ok(GameWrapped::card('u1') !== null, 'Nov 7: still in its 7 days');
$at('2026-11-08 08:00'); $ok(GameWrapped::card('u1') === null, 'Nov 8: no card any more');

/* ── reviewing the last day before the close: at once (u3, French) ── */
$month('u3');
$at('2026-10-30 11:00'); GameWrapped::ensure('u3', 'fr'); $ok($row('u3', '2026-10') === null, 'u3 Friday 11:00 ET, not reviewed: no recap');
$day('u3', '2026-10-30', ['review' => 1]);
GameWrapped::ensure('u3', 'fr'); $d3 = $snap('u3', '2026-10');
$ok($d3 !== null && $d3['net'] === 79000, 'Friday 11:00 ET, the last trading day reviewed (closed): created at once, the same numbers');
$ok(($d3['ai']['lang'] ?? null) === 'fr' && ($d3['ai']['next'] ?? null) === 'Écris une ligne après chaque trade perdant.', 'the AI part in the trader\'s language (FR)');

/* ── the previous month later (cron, app opened on Nov 3) and the losing month (u2) ── */
foreach ([['a', '2026-10-05', 'NQ', -40000, 'Chased the open, I knew it.'], ['b', '2026-10-06', 'NQ', 15000, ''], ['c', '2026-10-07', 'MNQ', -30000, '']] as [$id, $dt, $in, $p, $n])
    $doc('u2', 'trades', $id, $T(['date' => $dt, 'entry_time' => '10:00', 'instrument' => $in, 'pnl_c' => $p, 'notes' => $n, 'account_id' => 'X']));
$mockQuote = $mockOk; $mockQuote['en']['journal'] = 'I will never chase again.';   // not in the notes: dropped
file_put_contents($mock, json_encode($mockQuote));
$pdo->exec("INSERT INTO users (id, username, lang) VALUES ('u2', 'u2', 'es')");
$at('2026-11-03 09:00'); GameWrapped::ensure('u2', ''); $d = $snap('u2', '2026-10');
$ok($d !== null && $d['net'] === -55000 && $d['winners'] === 1 && $d['losers'] === 2 && $d['win_rate'] === 33, 'losing month (Nov 3, the previous month): net −$550, 1 winner, 2 losers, 33 %');
$ok($d['worst_day'] === ['d' => '2026-10-05', 'v' => -40000] && $d['best_day'] === ['d' => '2026-10-06', 'v' => 15000] && $d['tough_trade']['note'] === 'Chased the open, I knew it.', 'worst day Oct 5 −$400, best day Oct 6 +$150, toughest trade with its note');
$ok($d['split'] === [] && $d['how']['bars'] === [] && $d['how']['session'] === null && $d['how']['setup'] === null, 'no account type, no checklist, no plan, no grade: nothing invented (' . json_encode([$d['split'], $d['how']]) . ')');
$ok(is_array($d['ai']) && array_key_exists('journal', $d['ai']) && $d['ai']['journal'] === null && ($d['ai']['lang'] ?? null) === 'es', 'a quote the trader never wrote: dropped; without the app\'s language, the account\'s (ES) (' . json_encode($d['ai']) . ')');
file_put_contents($mock, json_encode($mockOk));

/* ── under 3 trading days, example trades left out (u4) ── */
foreach ([['a', '2026-10-05'], ['b', '2026-10-06']] as [$id, $dt]) $doc('u4', 'trades', $id, $T(['date' => $dt, 'entry_time' => '10:00', 'pnl_c' => 1000]));
$doc('u4', 'trades', 'd', $T(['date' => '2026-10-07', 'entry_time' => '10:00', 'pnl_c' => 1000, 'demo' => true]));
$doc('u4', 'trades', 'g', ['date' => '2026-10-08', 'session_date' => true, 'untracked' => true, 'pnl_c' => -500]);
$at('2026-11-02 09:00'); GameWrapped::ensure('u4', 'en');
$ok($row('u4', '2026-10') === null && GameWrapped::build('u4', '2026-10') === null, 'two trading days (an example trade and a balance line do not count): no recap');
$doc('u4', 'trades', 'c', $T(['date' => '2026-10-09', 'entry_time' => '10:00', 'pnl_c' => 1000]));
GameWrapped::ensure('u4', 'en'); $ok($snap('u4', '2026-10')['days'] === 3, 'a third trading day: the recap');

/* ── the AI skipped: an error, the allowance used up, the AI off ── */
$month('u5'); $month('u6'); $month('u7');
file_put_contents($mock, json_encode(['error' => 'provider']));
$at('2026-11-02 09:00'); GameWrapped::ensure('u5', 'en'); $d = $snap('u5', '2026-10');
$ok($d !== null && $d['ai'] === null && $d['net'] === 79000, 'an AI error: the snapshot without its AI part (the screen is skipped)');
file_put_contents($mock, json_encode($mockOk));
foreach ([1, 2] as $k) $pdo->prepare('INSERT INTO ai_log (user_id, task, input_tokens, output_tokens, cost_usd, created_at) VALUES (?, ?, 0, 0, 0, ?)')->execute(['u6', 'chat', gmdate('Y-m-d H:i:s')]);
GameWrapped::ensure('u6', 'en'); $d = $snap('u6', '2026-10');
$ok($d !== null && $d['ai'] === null && $aiCalls('u6') === 0, 'today\'s AI allowance used up: no AI part, no call');
putenv('SWEEP_AI_MONTH_MOCK');   // the AI offline (tests, SWEEP_AI_OFFLINE): a network error
GameWrapped::ensure('u7', 'en'); $d = $snap('u7', '2026-10');
$ok($d !== null && $d['ai'] === null, 'the AI unreachable: no AI part, no error');
putenv('SWEEP_AI_MONTH_MOCK=' . $mock);

/* ── an old Wrapped row stays as it was ── */
$pdo->prepare('INSERT INTO monthly_wrapped (user_id, month, data_json, created_at) VALUES (?, ?, ?, ?)')->execute(['u8', '2026-09', json_encode(['month' => '2026-09', 'swept' => 4, 'market_days' => 21, 'best_streak' => 2]), 1]);
$at('2026-10-03 09:00'); GameWrapped::ensure('u8', 'en');
$st = GameWrapped::state('u8');
$ok(count($st['items']) === 1 && $st['items'][0]['data']['swept'] === 4 && !isset($st['items'][0]['data']['v']) && GameWrapped::card('u8') === null, 'an old Wrapped (no « v »): kept as it was, in the history, no Today card');

$pdo = null; array_map('unlink', glob($tmp . '/*') ?: []); @rmdir($tmp);
echo "\n$pass passed, $fail failed\n";
exit($fail ? 1 : 0);
