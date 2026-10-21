<?php
// Sweep — the site's captures only (serve.sh: SWEEP_CHART_CONFIG): the chart reads the bars drawn by bars.py from a local
// cache; the key is a placeholder and the Databento address is unreachable, so nothing is ever asked outside this machine.
return [
    'databento_api_key' => 'capture-local-only',
    'databento_base_url' => 'http://127.0.0.1:9/v0',
    'chart_cache_dir' => (string) (getenv('SHOTS_BARS') ?: '/tmp/gs-bars'),
    'chart_data_min_age_hours' => 24,
    'chart_daily_budget_usd' => 0,
];
