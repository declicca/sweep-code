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
ok(empty($fs['tradeify']['programs']) && empty($fs['alpha']['programs']), 'Tradeify and Alpha Futures are still empty (the app hides firms without accounts)');

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

exec('rm -rf ' . escapeshellarg($DATA));
echo "\n" . ($n - $fails) . "/$n passed\n";
exit($fails ? 1 : 0);
