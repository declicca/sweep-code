<?php
/*
 * Sweep — real charts (Databento). Copy this file to the PRIVATE folder, outside the web root,
 * next to ai-config.php:   /home/matnsabc/sweep-private/chart-config.php
 * Then put your Databento API key between the quotes. Never put the key anywhere else.
 */
return [
    'databento_api_key'        => '',                 // ← your key (db-…), only here
    'databento_dataset'        => 'GLBX.MDP3',        // CME Globex
    'chart_data_min_age_hours' => 24,                 // CME redistribution licence not confirmed: keep 24
    'chart_cache_dir'          => '',                 // empty = sweep-private/bars next to this file
    'chart_daily_budget_usd'   => 2.00,               // hard stop for Databento spending per UTC day
    'chart_enabled'            => true,               // global switch
];
