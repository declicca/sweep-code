<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli' && realpath((string) ($_SERVER['SCRIPT_FILENAME'] ?? '')) === realpath(__FILE__)) { http_response_code(404); exit; }
/**
 * Sweep — complete export in one tap: a ZIP with
 *   README.txt, sweep-backup.json (same format as « Import data (JSON) », re-importable),
 *   trades.csv, accounts.csv, payouts.csv, expenses.csv, journals.csv (UTF-8 with BOM, opens in Excel/Numbers/Sheets),
 *   screenshots/ (your uploaded images, when they total 200 MB or less; above that the README explains how to get them).
 * Built with a tiny streaming ZIP writer (no PHP zip extension needed): nothing is written to disk.
 */

const EXPORT_SHOTS_MAX = 200 * 1024 * 1024;

final class ZipStream
{
    private int $offset = 0; private array $cd = [];
    public function add(string $name, string $data): void
    {
        $crc = crc32($data); $len = strlen($data); [$t, $d] = self::dos(time());
        $h = pack('VvvvvvVVVvv', 0x04034b50, 20, 0x0800, 0, $t, $d, $crc, $len, $len, strlen($name), 0) . $name;
        echo $h; echo $data; flush();
        $this->cd[] = pack('VvvvvvvVVVvvvvvVV', 0x02014b50, 20, 20, 0x0800, 0, $t, $d, $crc, $len, $len, strlen($name), 0, 0, 0, 0, 0, $this->offset) . $name;
        $this->offset += strlen($h) + $len;
    }
    public function finish(): void
    {
        $cd = implode('', $this->cd);
        echo $cd;
        echo pack('VvvvvVVv', 0x06054b50, 0, 0, count($this->cd), count($this->cd), strlen($cd), $this->offset, 0);
        flush();
    }
    private static function dos(int $ts): array
    {
        $d = getdate($ts);
        return [($d['hours'] << 11) | ($d['minutes'] << 5) | intdiv($d['seconds'], 2), (max(0, $d['year'] - 1980) << 9) | ($d['mon'] << 5) | $d['mday']];
    }
}

function export_csv(array $head, array $rows): string
{
    $f = fopen('php://temp', 'w+');
    fwrite($f, "\xEF\xBB\xBF");
    fputcsv($f, $head);
    foreach ($rows as $r) fputcsv($f, array_map(fn($v) => is_array($v) ? implode(' | ', array_map('strval', $v)) : (string) ($v ?? ''), $r));
    rewind($f); $s = stream_get_contents($f); fclose($f);
    return (string) $s;
}


function export_full(PDO $pdo, string $uid, string $dataDir): void
{
    $cols = ['firms', 'accounts', 'trades', 'journals', 'weekly', 'payouts', 'expenses'];
    $docs = array_fill_keys($cols, []); $settings = null;
    $st = $pdo->prepare('SELECT collection, id, data FROM documents WHERE user_id = ?'); $st->execute([$uid]);
    foreach ($st as $r) {
        $d = json_decode((string) $r['data'], true); if (!is_array($d)) continue;
        if ($r['collection'] === 'meta' && $r['id'] === 'settings') { $settings = $d; continue; }
        if (isset($docs[$r['collection']])) $docs[$r['collection']][] = $d;
    }
    $firm = []; foreach ($docs['firms'] as $f) $firm[$f['id']] = $f['name'] ?? '';
    $acct = []; foreach ($docs['accounts'] as $a) $acct[$a['id']] = trim(($firm[$a['firm_id'] ?? ''] ?? '') . ' — ' . ($a['name'] ?? ''), ' —');
    $m = fn($c) => $c === null || $c === '' ? '' : number_format(((int) $c) / 100, 2, '.', '');
    usort($docs['trades'], fn($a, $b) => strcmp(($a['date'] ?? '') . ($a['entry_time'] ?? ''), ($b['date'] ?? '') . ($b['entry_time'] ?? '')));

    $name = 'sweep-export-' . date('Y-m-d');
    header('Content-Type: application/zip');
    header('Content-Disposition: attachment; filename="' . $name . '.zip"');
    header('Cache-Control: no-store');
    header('X-Content-Type-Options: nosniff');
    @set_time_limit(300);
    while (ob_get_level()) ob_end_clean();
    $z = new ZipStream();

    // 1. the full backup, same shape as the in-app JSON export (re-importable)
    $backup = ['exported_at' => gmdate('c'), 'settings' => $settings] + $docs;
    $z->add("$name/sweep-backup.json", json_encode($backup, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES));

    // 2. spreadsheets
    $z->add("$name/trades.csv", export_csv(
        ['date', 'entry_time', 'exit_time', 'account', 'instrument', 'contract', 'direction', 'contracts', 'entry', 'exit', 'stop', 'target', 'pnl', 'fees', 'net', 'setup', 'grade', 'tags', 'emotions_before', 'rules_followed', 'notes', 'sample_data', 'id'],
        array_map(fn($t) => [$t['date'] ?? '', $t['entry_time'] ?? '', $t['exit_time'] ?? '', $acct[$t['account_id'] ?? ''] ?? '', $t['instrument'] ?? '', $t['contract'] ?? '', $t['direction'] ?? '', $t['contracts'] ?? '',
            $t['entry'] ?? '', $t['exit'] ?? '', $t['stop'] ?? '', $t['target'] ?? '', $m($t['pnl_c'] ?? null), $m($t['fees_c'] ?? null), $m(((int) ($t['pnl_c'] ?? 0)) - ((int) ($t['fees_c'] ?? 0))),
            $t['setup'] ?? '', $t['grade'] ?? '', $t['tags'] ?? [], (($t['emo'] ?? [])['before'] ?? []), $t['rules_followed'] ?? '', $t['notes'] ?? '', !empty($t['demo']) ? 'yes' : '', $t['id'] ?? ''], $docs['trades'])));
    $z->add("$name/accounts.csv", export_csv(['firm', 'account', 'status', 'starting_balance', 'profit_target', 'max_drawdown', 'drawdown_type', 'daily_loss_limit', 'consistency_pct', 'min_days', 'created_on', 'id'],
        array_map(fn($a) => [$firm[$a['firm_id'] ?? ''] ?? '', $a['name'] ?? '', $a['status'] ?? '', $m($a['starting_balance_c'] ?? null), $m(($a['rules'] ?? [])['target_c'] ?? null), $m(($a['rules'] ?? [])['dd_c'] ?? null),
            ($a['rules'] ?? [])['dd_type'] ?? '', $m(($a['rules'] ?? [])['dll_c'] ?? null), ($a['rules'] ?? [])['consistency_pct'] ?? '', ($a['rules'] ?? [])['min_days'] ?? '', $a['created_on'] ?? '', $a['id'] ?? ''], $docs['accounts'])));
    $z->add("$name/payouts.csv", export_csv(['account', 'amount', 'status', 'request_date', 'approval_date', 'payment_date', 'notes'],
        array_map(fn($p) => [$acct[$p['account_id'] ?? ''] ?? '', $m($p['amount_c'] ?? null), $p['status'] ?? '', $p['request_date'] ?? '', $p['approval_date'] ?? '', $p['payment_date'] ?? '', $p['notes'] ?? ''], $docs['payouts'])));
    $z->add("$name/expenses.csv", export_csv(['date', 'firm', 'account', 'category', 'amount', 'notes'],
        array_map(fn($x) => [$x['date'] ?? '', $firm[$x['firm_id'] ?? ''] ?? '', $acct[$x['account_id'] ?? ''] ?? '', $x['category'] ?? '', $m($x['amount_c'] ?? null), $x['notes'] ?? ''], $docs['expenses'])));
    $z->add("$name/journals.csv", export_csv(['date', 'bias', 'key_levels', 'scenario', 'plan', 'max_loss', 'max_trades', 'focus', 'went_well', 'went_wrong', 'lesson', 'tomorrow', 'grade', 'followed_plan'],
        array_map(fn($j) => [$j['id'] ?? '', ($j['pre'] ?? [])['bias'] ?? '', ($j['pre'] ?? [])['levels'] ?? '', ($j['pre'] ?? [])['scenario'] ?? '', ($j['pre'] ?? [])['plan'] ?? '', ($j['pre'] ?? [])['max_loss'] ?? '', ($j['pre'] ?? [])['max_trades'] ?? '',
            ($j['pre'] ?? [])['focus'] ?? '', ($j['post'] ?? [])['well'] ?? '', ($j['post'] ?? [])['wrong'] ?? '', ($j['post'] ?? [])['lesson'] ?? '', ($j['post'] ?? [])['tomorrow'] ?? '', ($j['post'] ?? [])['grade'] ?? '', ($j['post'] ?? [])['followed'] ?? ''], $docs['journals'])));

    // 3. screenshots, named after their trade
    $shotOf = []; foreach ($docs['trades'] as $t) foreach ((array) ($t['shots'] ?? []) as $s) if (!empty($s['id'])) $shotOf[$s['id']] = ($t['date'] ?? 'trade') . '_' . preg_replace('/[^A-Za-z0-9]/', '', (string) ($t['instrument'] ?? '')) . '_' . substr((string) ($t['id'] ?? ''), -6);
    $up = $pdo->prepare('SELECT id, content_type, size FROM uploads WHERE user_id = ?'); $up->execute([$uid]); $files = $up->fetchAll(PDO::FETCH_ASSOC);
    $total = array_sum(array_map(fn($f) => (int) $f['size'], $files)); $shots = 0;
    if ($total <= EXPORT_SHOTS_MAX) {
        $ext = ['image/png' => 'png', 'image/jpeg' => 'jpg', 'image/gif' => 'gif', 'image/webp' => 'webp'];
        foreach ($files as $i => $f) {
            $path = $dataDir . '/uploads/' . basename((string) $f['id']);
            if (!is_file($path)) continue;
            $z->add("$name/screenshots/" . ($shotOf[$f['id']] ?? 'image') . '_' . ($i + 1) . '.' . ($ext[$f['content_type']] ?? 'bin'), (string) file_get_contents($path));
            $shots++;
        }
    }
    $readme = "Sweep — your complete export (" . gmdate('Y-m-d H:i') . " UTC)\n\n"
        . "sweep-backup.json   Everything, re-importable in Sweep (Settings → Import data).\n"
        . "trades.csv          " . count($docs['trades']) . " trades. Amounts in USD, times in New York time (ET).\n"
        . "accounts.csv        " . count($docs['accounts']) . " accounts and their rules.\n"
        . "payouts.csv         " . count($docs['payouts']) . " payouts.\n"
        . "expenses.csv        " . count($docs['expenses']) . " expenses.\n"
        . "journals.csv        " . count($docs['journals']) . " journal days (pre-market plan and review).\n"
        . ($total <= EXPORT_SHOTS_MAX ? "screenshots/        $shots images, named date_instrument_trade.\n"
            : "screenshots/        Not included: your images total " . round($total / 1048576) . " MB (limit 200 MB). Write to support and we will send them to you.\n")
        . "\nCSV files are UTF-8 and open in Excel, Numbers and Google Sheets.\n";
    $z->add("$name/README.txt", $readme);
    $z->finish();
    exit;
}
