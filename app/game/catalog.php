<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli' && realpath((string) ($_SERVER['SCRIPT_FILENAME'] ?? '')) === realpath(__FILE__)) { http_response_code(404); exit; }
/**
 * Sweep — gamification V1 catalog: badges, XP table, ranks, streak milestones, freezes.
 * Names and descriptions live in the app's i18n dictionary (assets/game.*.js) under badge.<id>.name / .desc.
 * "target" is the counter shown on a locked badge ("7/10"); conditions are evaluated in GameEngine::badgeProgress().
 */

const GAME_BADGES = [
    'welcome'       => ['rarity' => 'common', 'secret' => false, 'xp' => 20,  'target' => 1],
    'first_plan'    => ['rarity' => 'common', 'secret' => false, 'xp' => 20,  'target' => 1],
    'first_journal' => ['rarity' => 'common', 'secret' => false, 'xp' => 20,  'target' => 1],
    'first_sweep'   => ['rarity' => 'common', 'secret' => false, 'xp' => 50,  'target' => 1],
    'sweep_5'       => ['rarity' => 'common', 'secret' => false, 'xp' => 50,  'target' => 5],
    'sweep_25'      => ['rarity' => 'rare',   'secret' => false, 'xp' => 150, 'target' => 25],
    'sweep_100'     => ['rarity' => 'epic',   'secret' => false, 'xp' => 500, 'target' => 100],
    'streak_7'      => ['rarity' => 'common', 'secret' => false, 'xp' => 0,   'target' => 7],
    'streak_30'     => ['rarity' => 'rare',   'secret' => false, 'xp' => 0,   'target' => 30],
    'streak_100'    => ['rarity' => 'epic',   'secret' => false, 'xp' => 0,   'target' => 100],
    'full_week'     => ['rarity' => 'rare',   'secret' => false, 'xp' => 150, 'target' => 1],
    'patience'      => ['rarity' => 'common', 'secret' => false, 'xp' => 30,  'target' => 1],
    'guardrail'     => ['rarity' => 'rare',   'secret' => false, 'xp' => 100, 'target' => 1],
    'early_plan'    => ['rarity' => 'rare',   'secret' => false, 'xp' => 100, 'target' => 10],
    'sniper'        => ['rarity' => 'rare',   'secret' => false, 'xp' => 100, 'target' => 10],
    'sacred_stop'   => ['rarity' => 'epic',   'secret' => false, 'xp' => 300, 'target' => 50],
    'reviewer_20'   => ['rarity' => 'rare',   'secret' => false, 'xp' => 100, 'target' => 20],
    'resilience'    => ['rarity' => 'rare',   'secret' => true,  'xp' => 150, 'target' => 1],
    'comeback'      => ['rarity' => 'rare',   'secret' => true,  'xp' => 100, 'target' => 1],
    'perfectionist' => ['rarity' => 'epic',   'secret' => true,  'xp' => 200, 'target' => 5],
    'zen'           => ['rarity' => 'rare',   'secret' => true,  'xp' => 100, 'target' => 1],
    // V3 bosses: unlocked when the boss is defeated (the boss itself pays 500 XP)
    'boss_revenge' => ['rarity' => 'epic', 'secret' => true, 'xp' => 0, 'target' => 1], 'boss_fomo_open' => ['rarity' => 'epic', 'secret' => true, 'xp' => 0, 'target' => 1],
    'boss_cursed_day' => ['rarity' => 'epic', 'secret' => true, 'xp' => 0, 'target' => 1], 'boss_oversize' => ['rarity' => 'epic', 'secret' => true, 'xp' => 0, 'target' => 1],
    'boss_moving_stop' => ['rarity' => 'epic', 'secret' => true, 'xp' => 0, 'target' => 1], 'boss_overtrader' => ['rarity' => 'epic', 'secret' => true, 'xp' => 0, 'target' => 1],
    'boss_offplan' => ['rarity' => 'epic', 'secret' => true, 'xp' => 0, 'target' => 1], 'boss_no_plan' => ['rarity' => 'epic', 'secret' => true, 'xp' => 0, 'target' => 1],
    'boss_for_good' => ['rarity' => 'epic', 'secret' => true, 'xp' => 200, 'target' => 1],
    // V2 step 2
    'weekly_4' => ['rarity' => 'rare', 'secret' => false, 'xp' => 100, 'target' => 1], 'weekly_12' => ['rarity' => 'epic', 'secret' => false, 'xp' => 300, 'target' => 1],
    'lucky' => ['rarity' => 'rare', 'secret' => true, 'xp' => 50, 'target' => 1],
    'payout_ready' => ['rarity' => 'epic', 'secret' => false, 'xp' => 200, 'target' => 1],
    'league_promoted' => ['rarity' => 'rare', 'secret' => false, 'xp' => 100, 'target' => 1],
    'buddy_10' => ['rarity' => 'rare', 'secret' => false, 'xp' => 150, 'target' => 1],
];

const GAME_XP = [
    'plan' => 20, 'plan_late' => 10, 'journal' => 5, 'journal_cap' => 5, 'review' => 20, 'ring' => 10,
    'sweep' => 50, 'dayoff' => 10, 'guardrail' => 25, 'onboarding' => 10,
];

const GAME_STREAK_MILESTONES = [7 => 100, 14 => 200, 30 => 500, 60 => 1000, 100 => 2000];

/** [first level, rank key] in ascending order */
const GAME_RANKS = [[1, 'rookie'], [5, 'apprentice'], [10, 'disciplined'], [15, 'consistent'], [20, 'seasoned'], [30, 'master'], [40, 'sweeper']];

const GAME_FREEZES = ['free' => 1, 'pro' => 2, 'elite' => 3];

/** "Démarrage" checklist: step => percent (the account itself is the first 20 %) */
const GAME_START_STEPS = ['goal' => 10, 'style' => 10, 'rules' => 15, 'journal' => 15, 'plan' => 15, 'review' => 15];

/**
 * Progressive reveal of the game: each mechanic appears when it becomes useful (one « new » moment each).
 * Conditions (all must hold): swept = days swept ever, level, trades = trades journaled, days = days since start.
 * 'or' = alternative set of conditions. Plan limits (entitlements) still apply on top: an unlock never bypasses them.
 * Traders who were already playing before this feature keep everything.
 */
const GAME_UNLOCKS = [
    'missions' => ['swept' => 1],
    'weekly'   => ['swept' => 2],
    'boss'     => ['level' => 3, 'or' => ['trades' => 10]],
    'season'   => ['days' => 7],
    'league'   => ['days' => 7],
    'social'   => ['days' => 7],
];

/**
 * « What's new » after the navigation redesign. SET THIS TO THE REAL GO-LIVE DATE (YYYY-MM-DD, New York).
 * Shown once to traders who signed up before it AND had at least one active day before it; never to anyone who joins that day or later.
 */
const GAME_RELEASE_DATE = '2026-10-04';
