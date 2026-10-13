<?php
declare(strict_types=1);
/**
 * Sweep — tests of the prop firm presets (no network, no AI: the answers come from a simulated reading).
 *   php tests/presets_test.php
 * Works in a temporary folder: the real data/ is never touched.
 */
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
$root = dirname(__DIR__);
$DATA = sys_get_temp_dir() . '/sweep-presets-test-' . getmypid();
@mkdir($DATA, 0700, true);
$pdo = new PDO('sqlite:' . $DATA . '/journal.db', null, null, [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION, PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC]);
function db(): PDO { global $pdo; return $pdo; }
$cfg = ['notifications' => ['daily_limit' => 50]];
$pdo->exec('CREATE TABLE documents (user_id TEXT NOT NULL, collection TEXT NOT NULL, id TEXT NOT NULL, data TEXT NOT NULL, updated_at TEXT, created_at TEXT, PRIMARY KEY (user_id, collection, id))');
require_once $root . '/notify/notify.php';
require_once $root . '/presets/check.php';

$fails = 0; $n = 0;
function ok(bool $c, string $what) { global $fails, $n; $n++; if (!$c) $fails++; echo ($c ? 'ok   ' : 'FAIL ') . $what . "\n"; }
function put_acc(string $uid, string $id, array $d) { db()->prepare('INSERT OR REPLACE INTO documents (user_id, collection, id, data) VALUES (?, ?, ?, ?)')->execute([$uid, 'accounts', $id, json_encode($d)]); }
function acc(string $uid, string $id): array { return json_decode((string) db()->query("SELECT data FROM documents WHERE user_id = '$uid' AND id = '$id'")->fetchColumn(), true); }
function notifs(string $uid): array { return db()->query("SELECT * FROM notifications WHERE user_id = '$uid'")->fetchAll(); }
function mock(array $answers): void { $f = $GLOBALS['DATA'] . '/mock.json'; file_put_contents($f, json_encode($answers)); putenv('SWEEP_PRESETS_MOCK=' . $f); }
/** a firm's answer = today's catalogue as the AI would return it (no notes, no Legacy, no variants), then edited */
function answer_of(string $fid, ?callable $edit = null): array {
    foreach (pr_current()['firms'] as $f) if ($f['id'] === $fid) {
        $progs = [];
        foreach ($f['programs'] as $p) { if (!empty($p['legacy'])) continue; $q = ['id' => $p['id'], 'name' => $p['name'], 'direct' => !empty($p['direct']), 'sizes' => []];
            foreach ($p['sizes'] as $s) { $r = ['size' => $s['size']]; foreach (['eval', 'funded', 'price'] as $k) if (isset($s[$k])) $r[$k] = $s[$k]; $q['sizes'][] = $r; } $progs[] = $q; }
        $a = ['programs' => $progs]; if ($edit) $edit($a); return $a;
    }
    throw new RuntimeException("no firm $fid");
}

echo "— Catalogue shipped (presets/seed.json)\n";
$cat = pr_current();
ok(!pr_validate_catalogue($cat), 'every number of the shipped catalogue is valid');
$count = 0; $bad = [];
foreach ($cat['firms'] as $f) foreach ($f['programs'] as $p) foreach ($p['sizes'] as $s) foreach (['eval', 'funded', 'live'] as $ph) {
    if ($ph !== 'live' && empty($s[$ph])) continue;
    if ($ph === 'live' && empty($s['funded'])) continue;
    $opts = [''];
    foreach ((array) ($p['options'] ?? []) as $o) foreach ($o['choices'] as $c) if ($c['id'] !== $o['default']) $opts[] = $c['id'];
    if (!empty($s[$ph]['dll_optional'])) $opts[] = 'dll';
    foreach ($opts as $o) {
        $v = "{$f['id']}|{$p['id']}|{$s['size']}|$ph|$o"; $r = pr_rules_of($cat, $v); $count++;
        if (!$r || !($r['rules']['dd_c'] > 0)) $bad[] = $v;
        if ($ph === 'eval' && $r && !($r['rules']['target_c'] > 0)) $bad[] = "$v (target)";
    }
}
ok(!$bad, "an account can be made from every firm, type, size, phase and option ($count combinations)" . ($bad ? ': ' . implode(', ', array_slice($bad, 0, 5)) : ''));
$fs = array_column($cat['firms'], null, 'id');
$tpt = pr_rules_of($cat, 'tpt|tpt-test|50000|eval|');
ok($tpt['rules']['min_days'] === 3, 'Take Profit Trader Test: 3 minimum days (cut from 5 on 2026-08-17)');
$ts = pr_rules_of($cat, 'topstep|combine|50000|eval|');
ok($ts['rules']['consistency_pct'] === 55, 'Topstep Combine: 55 % consistency target');
$std = pr_rules_of($cat, 'topstep|combine|50000|funded|')['rules']; $con = pr_rules_of($cat, 'topstep|combine|50000|funded|consistency')['rules'];
ok($std['payout_win_days'] === 5 && $std['payout_max_c'] === 200000 && !$std['consistency_pct'], 'Topstep funded Standard: 5 winning days of $150, cap $2,000, no consistency');
ok($con['payout_trade_days'] === 3 && $con['consistency_pct'] === 40 && $con['payout_max_c'] === 300000 && !$con['payout_win_days'], 'Topstep funded Consistency: 3 traded days, 40 %, cap $3,000');
ok(pr_rules_of($cat, 'topstep|combine|150000|funded|dll+consistency')['rules']['payout_max_c'] === 1200000, 'Topstep Consistency 150K with the daily-limit option: cap doubled to $12,000');
$leg = pr_rules_of($cat, 'apex|apex-legacy|50000|funded|')['rules'];
ok($leg['dd_c'] === 250000 && $leg['dd_type'] === 'trade' && $leg['consistency_pct'] === 30 && $leg['payout_trade_days'] === 8 && $leg['payout_win_days'] === 5 && $leg['payout_win_min_c'] === 5000 && $leg['payout_ladder_c'][5] === null, 'Apex « rules from before March 2026 » 50K: $2,500 real-time, 30 %, 8 days incl. 5 of $50, no cap from the 6th payout');
ok(pr_rules_of($cat, 'apex|apex-legacy|50000|eval|')['rules']['min_days'] === 7, 'Apex Legacy evaluation: 7 minimum days');
ok((bool) pr_rules_of($cat, 'mffu|mffu-builder|25000|eval|') && pr_rules_of($cat, 'mffu|mffu-builder|25000|eval|')['rules']['dll_c'] === null, 'MyFundedFutures Builder 25K exists, without a daily limit');
ok(pr_rules_of($cat, 'lucid|luciddirect|150000|funded|')['rules']['dll_c'] === 300000 && pr_rules_of($cat, 'lucid|luciddirect|25000|funded|')['rules']['dll_c'] === null, 'LucidDirect: 150K daily limit $3,000, 25K none');
ok(empty($fs['tradeify']['programs']), 'Tradeify is still empty (the app hides firms without accounts)');
// Alpha Futures (13 Oct.): checked by hand on alpha-futures.com and its Payout Policy — the weekly check of 12 Oct. had read « up to 4 times a month » as 4 payouts in all
$az = pr_rules_of($cat, 'alpha|zero|50000|funded|')['rules']; $ad = pr_rules_of($cat, 'alpha|direct|25000|funded|')['rules']; $aa = pr_rules_of($cat, 'alpha|advanced|50000|funded|')['rules'];
ok(count($fs['alpha']['programs']) === 4 && $az['payout_max_n'] === null && $ad['payout_max_n'] === null && $aa['payout_max_n'] === null, 'Alpha Futures: 4 account types, no limit on the number of payouts');
ok($az['payout_min_c'] === 20000 && $az['payout_max_c'] === 150000 && $az['payout_max_pct'] === 50 && $az['payout_win_days'] === 5 && $az['payout_win_min_c'] === 20000 && $az['consistency_pct'] === 40, 'Alpha Zero 50K funded: 5 winning days of $200, $200 to $1,500, 50 % of the profit, 40 %');
ok($ad['payout_first_min_c'] === 150000 && $ad['payout_cycle_min_c'] === 100000 && $ad['payout_min_c'] === 50000 && $ad['payout_max_c'] === 100000 && $ad['consistency_pct'] === 20 && !$ad['payout_win_days'], 'Alpha Direct 25K: $1,500 before the first payout, then $1,000 since the last one, $500 to $1,000, 20 %');
ok($aa['payout_min_c'] === 100000 && $aa['payout_max_c'] === 1500000 && $aa['consistency_pct'] === null && $aa['dll_c'] === null, 'Alpha Advanced 50K funded: $1,000 to $15,000, no consistency, no daily limit');
ok(strpos(pr_describe(['payout_first_min_c' => [null, 150000]], 'fr'), 'Profit avant le premier payout') !== false, 'the new rule has its words in the notifications');
// Apex EOD / Intraday PA and TPT PRO (13 Oct.), against the official help centers — the check of 12 Oct. had put Apex Legacy's rules on them
foreach (['apex-eod', 'apex-intraday'] as $pid) foreach ([[25000, 2, 50000, 100000], [50000, 4, 100000, 150000], [100000, 6, 175000, 200000], [150000, 10, 250000, 250000]] as [$sz, $mn, $dll, $cap]) {
    $hit = pr_find($cat, "apex|$pid|$sz|funded|"); $r = pr_rules_of($cat, "apex|$pid|$sz|funded|")['rules'];
    $ok = $r['payout_split_pct'] === 100 && $r['payout_trade_days'] === null && $r['payout_max_pct'] === null && $r['payout_cycle_pos'] === null && $r['payout_win_days'] === 5 && $r['payout_min_c'] === 50000
        && $r['payout_max_n'] === 6 && $r['payout_ladder_c'][0] === $cap && $r['consistency_pct'] === 50 && $r['dll_c'] === $dll && $hit[0]['funded']['max_minis'] === $mn;
    ok($ok, "Apex $pid " . ($sz / 1000) . "K funded: 100 % split, 5 days, no 8 traded days / 30 % / « profitable since », 6 payouts, cap \$" . ($cap / 100) . ", daily limit \$" . ($dll / 100) . " (level 1), $mn contracts");
}
foreach ([[25000, 3, 2650000], [50000, 6, 5200000], [75000, 9, 7750000], [100000, 12, 10300000], [150000, 15, 15450000]] as [$sz, $mn, $bal]) {
    $hit = pr_find($cat, "tpt|tpt-test|$sz|funded|"); $r = pr_rules_of($cat, "tpt|tpt-test|$sz|funded|")['rules'];
    ok($r['payout_split_pct'] === 80 && $r['payout_min_bal_c'] === $bal && $r['dd_type'] === 'trade' && $hit[0]['funded']['max_minis'] === $mn, "TPT PRO " . ($sz / 1000) . "K: 80 % split, buffer zone \$" . number_format($bal / 100) . ", real-time drawdown, $mn contracts");
}

echo "— Simulated weekly check with a payout change\n";
put_acc('u1', 'a1', ['name' => 'EOD 50K', 'status' => 'active', 'phase' => 'funded', 'preset' => 'apex|apex-eod|50000|funded|', 'rules' => pr_rules_of($cat, 'apex|apex-eod|50000|funded|')['rules']]);
put_acc('u1', 'a2', ['name' => 'Old eval', 'status' => 'archived', 'phase' => 'eval', 'preset' => 'apex|apex-eod|50000|eval|', 'rules' => []]);
put_acc('u2', 'a3', ['name' => 'Intraday 100K', 'status' => 'active', 'phase' => 'funded', 'preset' => 'apex|apex-intraday|100000|funded|', 'rules' => []]);
put_acc('u3', 'a4', ['name' => 'Combine', 'status' => 'active', 'phase' => 'eval', 'preset' => 'topstep|combine|50000|eval|', 'rules' => []]);
put_acc('u4', 'a5', ['name' => 'Legacy 50K', 'status' => 'active', 'phase' => 'funded', 'preset' => 'apex|apex-legacy|50000|funded|', 'rules' => []]);
$before = acc('u1', 'a1')['rules'];
mock(['apex' => answer_of('apex', function (&$a) {
    foreach ($a['programs'] as &$p) if ($p['id'] === 'apex-eod') foreach ($p['sizes'] as &$s) if ($s['size'] === 50000) { $s['funded']['payout']['win_min'] = 200; $s['funded']['payout']['ladder'][0] = 2000; $s['price'] = ['eval' => 450, 'eval_period' => 'once', 'activation' => 99]; }
})]);
$apex = $fs['apex'];
[$st, $new] = pr_check_firm($pdo, $apex);
ok($st['status'] === 'updated' && $new, 'the payout change is read and applied (status « updated »)');
ok((bool) array_filter($st['changes'], fn($c) => strpos($c, 'payout win_min: 250 → 200') !== false), 'the admin sees « EOD Trail 50K payout win_min: 250 → 200 »');
ok((bool) array_filter($st['changes'], fn($c) => strpos($c, 'price activation: — → 99') !== false), 'the new price is read too');
$st = pr_apply($pdo, 'apex', $st, $new);
$cat2 = pr_current();
ok(pr_rules_of($cat2, 'apex|apex-eod|50000|funded|')['rules']['payout_win_min_c'] === 20000, 'the catalogue the app serves now has the new payout rule');
ok((bool) array_filter($cat2['firms'], fn($f) => $f['id'] === 'apex' && array_filter($f['programs'], fn($p) => $p['id'] === 'apex-legacy')), 'the Legacy account type survives the check (never on today’s pages)');
ok(acc('u1', 'a1')['rules'] == $before, 'the trader’s account keeps its own rules until they apply the new ones');
$n1 = notifs('u1');
ok(count($n1) === 1 && $n1[0]['type'] === 'rules_changed' && $n1[0]['action_url'] === '#account/a1', 'the trader with an active Apex EOD 50K account gets one notification, linked to the account');
$p1 = json_decode((string) $n1[0]['params'], true);
ok(strpos($p1['changes_fr'], 'Minimum par jour gagnant : 250 $') !== false || strpos($p1['changes_fr'], 'Minimum par jour gagnant : $250 → $200') !== false, 'the notification says what changes for HIS account, in French: « ' . $p1['changes_fr'] . ' »');
ok(strpos($p1['changes_es'], 'Mínimo por día ganador') !== false && strpos($p1['changes'], 'Minimum per winning day: $250 → $200') !== false, 'and in English and Spanish');
ok(!notifs('u2') && !notifs('u3') && !notifs('u4'), 'nobody else is notified (other size, other firm, Legacy, archived account)');
ok($st['notified'] === 1, 'the admin sees « 1 trader notified »');
[$st2, $new2] = pr_check_firm($pdo, array_column(pr_current()['firms'], null, 'id')['apex']);
ok($st2['status'] === 'unchanged', 'the same reading a second time: « unchanged »');

echo "— Doubtful changes are never applied\n";
$cur = pr_current();
mock(['topstep' => answer_of('topstep', function (&$a) { $a['programs'][0]['sizes'][0]['funded']['payout']['max'] = 9000; })]);
[$st, $new] = pr_check_firm($pdo, array_column($cur['firms'], null, 'id')['topstep']);
ok($st['status'] === 'review' && $new === null && (bool) array_filter($st['errors'], fn($e) => strpos($e, 'payout max 2000 → 9000') !== false), 'a payout cap ×4.5 → « to review », not applied');
pr_apply($pdo, 'topstep', $st, $new);
ok(pr_rules_of(pr_current(), 'topstep|combine|50000|funded|')['rules']['payout_max_c'] === 200000, 'Topstep keeps its previous cap');
mock(['topstep' => answer_of('topstep', function (&$a) { $a['programs'][0]['sizes'][1]['price']['eval'] = 990; })]);
[$st] = pr_check_firm($pdo, array_column(pr_current()['firms'], null, 'id')['topstep']);
ok($st['status'] === 'review', 'an evaluation price ×10 → « to review »');
mock(['topstep' => answer_of('topstep', function (&$a) { $a['programs'][0]['sizes'][0]['funded']['payout']['win_days'] = 50; })]);
[$st] = pr_check_firm($pdo, array_column(pr_current()['firms'], null, 'id')['topstep']);
ok($st['status'] === 'review', 'an impossible payout rule (50 winning days) → « to review »');
mock(['topstep' => answer_of('topstep', function (&$a) { unset($a['programs'][0]['sizes'][0]['funded']['payout'], $a['programs'][0]['sizes'][0]['price']); })]);
[$st, $new] = pr_check_firm($pdo, array_column(pr_current()['firms'], null, 'id')['topstep']);
ok($st['status'] === 'unchanged', 'a payout rule or a price not found on the page is kept (not « removed »)');
mock(['lucid' => ['programs' => [answer_of('lucid')['programs'][0]]]]);
[$st] = pr_check_firm($pdo, array_column(pr_current()['firms'], null, 'id')['lucid']);
ok($st['status'] === 'review', 'half of Lucid’s accounts gone at once → « to review »');
putenv('SWEEP_PRESETS_MOCK=' . $DATA . '/none.json'); file_put_contents($DATA . '/none.json', '{}');
[$st] = pr_check_firm($pdo, array_column(pr_current()['firms'], null, 'id')['mffu']);
ok($st['status'] === 'error' && $st['errors'], 'a reading that fails → « error », with the message for the admin');

echo "— 8 days without a check: alert in Admin + email to support\n";
$mails = [];
$send = function (string $s, string $t) use (&$mails) { $mails[] = [$s, $t]; return true; };
$now = time();
$status = pr_status(); $status['last_run'] = gmdate('c', $now - 2 * 86400); pr_save_status($status);
@unlink(pr_watch_path());
ok(!pr_admin_summary($now)['stale'] && pr_watchdog($send, $now) === null && !$mails, 'checked 2 days ago: no alert, no email');
$status['last_run'] = gmdate('c', $now - 9 * 86400); pr_save_status($status);
@unlink(pr_watch_path());
$sum = pr_admin_summary($now);
ok($sum['stale'] && $sum['days_since'] === 9, 'checked 9 days ago: the Admin block shows the red alert (stale, 9 days)');
ok(pr_watchdog($send, $now) === 'mailed' && count($mails) === 1 && strpos($mails[0][0], '8 days') !== false, 'and one email goes to the support address');
ok(pr_admin_summary($now)['alert_mailed_at'] !== null, 'the Admin block says when the email was sent');
ok(pr_watchdog($send, $now + 1800) === null && count($mails) === 1, 'not twice within the hour');
ok(pr_watchdog($send, $now + 6 * 3600) === null && count($mails) === 1, 'not twice the same day');
ok(pr_watchdog($send, $now + 25 * 3600) === 'mailed' && count($mails) === 2, 'again the next day if still late');
$status['last_run'] = null; pr_save_status($status); @unlink(pr_watch_path());
ok(pr_admin_summary($now)['stale'], 'never checked at all: alert too');
pr_finish_run('admin');
ok(!pr_admin_summary()['stale'] && pr_status()['last_run_by'] === 'admin', '« Check now » finished: alert gone, « Check now » shown as the last check');

echo "— A new catalogue shipped in an update wins over an older checked one\n";
$live = json_decode((string) file_get_contents(pr_live_path()), true);
$live['seed_version'] = '2026-01-01'; file_put_contents(pr_live_path(), json_encode($live));
ok(pr_current()['version'] === pr_read(pr_seed_path())['version'], 'live file built on an older seed → the shipped seed is used');

echo "— After an update: the checked rules are not ignored in silence (brief app-depuis-site, step 1)\n";
$seedV = pr_read(pr_seed_path())['version'];
$origin = fn() => strpos((string) (pr_current()['origin'] ?? ''), 'seed') === 0 ? 'seed' : 'checked';   // what api/presets says
ok($origin() === 'seed' && pr_recheck_due(), 'checked catalogue on an older seed: api/presets says « seed », and a check is due');
@unlink($GLOBALS['DATA'] . '/mock.json'); putenv('SWEEP_PRESETS_MOCK=' . $GLOBALS['DATA'] . '/none.json'); file_put_contents($GLOBALS['DATA'] . '/none.json', '{}');
pr_run_all($pdo);   // every firm fails (no answer): nothing was read
ok($origin() === 'seed' && pr_read(pr_live_path())['seed_version'] === '2026-01-01', 'a check that could read no firm claims nothing: still « seed »');
$answers = []; foreach (pr_current()['firms'] as $f) if ($f['programs']) $answers[$f['id']] = answer_of($f['id']);
mock($answers);
$r = pr_recheck_if_seed_changed($pdo);   // what game/cron.php does after an update
$l = pr_read(pr_live_path());
ok(is_array($r) && count($r) === count(pr_read(pr_seed_path())['firms']), 'after an update: one full check against the official pages (' . (is_array($r) ? count($r) : 0) . ' firms)');
ok($l['seed_version'] === $seedV && $origin() === 'checked' && abs(strtotime($l['checked_at']) - time()) < 120, "nothing changed on the pages: the catalogue is saved on the current seed, api/presets says « checked » with today's date");
ok(pr_current()['version'] === $l['version'] && count(pr_current()['firms']) === count(pr_read(pr_seed_path())['firms']), 'the rules served are the current seed, now checked (same firms)');
ok(!pr_recheck_due() && pr_recheck_if_seed_changed($pdo) === null, 'no second check for the same seed');
$l['seed_version'] = '2026-01-02'; file_put_contents(pr_live_path(), json_encode($l));
$st = pr_status(); $st['recheck_for'] = $seedV; pr_save_status($st);
ok(!pr_recheck_due(), 'a check already tried for this seed (even a failed one) is not repeated every 15 minutes: the weekly task tries again');

echo "— A check never removes on its own: an account or a rule no longer read goes to review (12 Oct.)\n";
$firmOf = function (string $id) { foreach (pr_current()['firms'] as $f) if ($f['id'] === $id) return $f; return null; };
$run1 = function (string $id, callable $edit) use ($pdo, $firmOf) { mock([$id => answer_of($id, $edit)]); [$st, $new] = pr_check_firm($pdo, $firmOf($id)); return pr_apply($pdo, $id, $st, $new); };
$st = $run1('topstep', function (array &$a) { foreach ($a['programs'] as &$p) foreach ($p['sizes'] as &$s) unset($s['funded']['dll_optional']); });
ok($st['status'] === 'review' && strpos(implode(' ', $st['errors']), 'dll_optional') !== false, "Topstep's optional daily loss limit no longer read on the pages: to review, not applied (" . ($st['errors'][0] ?? '') . ')');
ok(!empty($firmOf('topstep')['programs'][0]['sizes'][0]['funded']['dll_optional']), '… and traders are still offered the option');
$st = $run1('mffu', function (array &$a) { array_pop($a['programs'][0]['sizes']); });
ok($st['status'] === 'review' && strpos(implode(' ', $st['errors']), 'no longer found on the official pages') !== false, 'an account no longer found on the pages: to review, the account stays');
$st = $run1('tpt', function (array &$a) { $a['programs'][0]['name'] = 'Test'; });
ok($st['status'] === 'unchanged' && $firmOf('tpt')['programs'][0]['name'] === 'Test → PRO', 'a program read under another name keeps ours (« Test → PRO »): nothing changes (' . $st['status'] . ')');
$st = $run1('topstep', function (array &$a) { foreach ($a['programs'][0]['sizes'] as &$s) $s['funded']['max_minis'] = ($s['funded']['max_minis'] ?? 0) + 1; });
ok($st['status'] === 'updated' && $firmOf('topstep')['programs'][0]['sizes'][0]['funded']['max_minis'] >= 1, 'a number read on the pages (max contracts) is still applied automatically (' . $st['status'] . ')');

// Alpha, 12 Oct.: « up to 4 times a month » read as « 4 payouts in all » — a limit on the number of payouts that appears is not applied on its own
$st = $run1('alpha', function (array &$a) { foreach ($a['programs'] as &$p) foreach ($p['sizes'] as &$s) if (isset($s['funded']['payout'])) $s['funded']['payout']['max_payouts'] = 4; });
ok($st['status'] === 'review' && strpos(implode(' ', $st['errors']), 'max_payouts none → 4') !== false && pr_rules_of(pr_current(), 'alpha|zero|50000|funded|')['rules']['payout_max_n'] === null, 'a payout count limit read where there was none: to review, not applied (' . ($st['errors'][0] ?? $st['status']) . ')');
// Alpha, 13 Oct.: the check after the update added « profitable since the last payout » (the Payout Policy asks 5 new winning days, or the Direct target)
$st = $run1('alpha', function (array &$a) { foreach ($a['programs'] as &$p) foreach ($p['sizes'] as &$s) if (isset($s['funded']['payout'])) $s['funded']['payout']['cycle_pos'] = true; });
ok($st['status'] === 'review' && strpos(implode(' ', $st['errors']), 'cycle_pos none → true') !== false && pr_rules_of(pr_current(), 'alpha|zero|50000|funded|')['rules']['payout_cycle_pos'] === null, '« profitable since the last payout » read where there was none: to review, not applied');
$st = $run1('alpha', function (array &$a) { foreach ($a['programs'] as &$p) if ($p['id'] === 'advanced') foreach ($p['sizes'] as &$s) $s['funded']['consistency'] = 40; });
ok($st['status'] === 'review' && strpos(implode(' ', $st['errors']), 'funded consistency none → 40') !== false && pr_rules_of(pr_current(), 'alpha|advanced|50000|funded|')['rules']['consistency_pct'] === null, 'a funded consistency read where there was none (Alpha Advanced): to review, not applied');
$st = $run1('alpha', function (array &$a) { foreach ($a['programs'] as &$p) if ($p['id'] === 'zero') foreach ($p['sizes'] as &$s) $s['funded']['payout']['win_days'] = 6; });
ok($st['status'] === 'updated' && pr_rules_of(pr_current(), 'alpha|zero|50000|funded|')['rules']['payout_win_days'] === 6, 'a condition the catalogue has already, read with a new value (5 → 6 winning days): still applied (' . $st['status'] . ')');
$st = $run1('alpha', function (array &$a) { foreach ($a['programs'] as &$p) foreach ($p['sizes'] as &$s) if (isset($s['funded']['payout'])) unset($s['funded']['payout']['first_min'], $s['funded']['payout']['min'], $s['funded']['payout']['max_pct']); });
ok(in_array($st['status'], ['unchanged', 'updated'], true) && pr_rules_of(pr_current(), 'alpha|direct|25000|funded|')['rules']['payout_first_min_c'] === 150000 && pr_rules_of(pr_current(), 'alpha|zero|25000|funded|')['rules']['payout_min_c'] === 20000, 'payout rules the pages do not repeat (first target, minimum, 50 %) keep their value (' . $st['status'] . ')');

exec('rm -rf ' . escapeshellarg($DATA));
echo "\n" . ($n - $fails) . "/$n passed\n";
exit($fails ? 1 : 0);
