<?php
declare(strict_types=1);
/**
 * Sweep — tests only: the server's « ready for a payout » (GameV2::payoutStatus) for the cases tests/e2e_payout_firms.py sends as
 * JSON on stdin ([{start, rules, trades, pays}, …]); prints [[ready, 0-100], …] for its comparison with the app's counter.
 */
if (PHP_SAPI !== 'cli') { http_response_code(404); exit; }
function db() { static $p = null; return $p ??= new PDO('sqlite::memory:'); }   // (the game's classes load with a database; none is used here)
require dirname(__DIR__) . '/game/game.php';
$out = [];
foreach ((array) json_decode((string) stream_get_contents(STDIN), true) as $c)
    $out[] = GameV2::payoutStatus(['id' => 'acc', 'starting_balance_c' => $c['start'], 'rules' => $c['rules']], (array) $c['trades'], (array) $c['pays']);
echo json_encode($out);
