#!/bin/sh
# Sweep — prop firm presets, without network or AI.
#  1. the full test (temporary folder, real data untouched): simulated check with a payout change, doubtful changes,
#     notifications, 8-day alert, every firm / type / size / option:
#       php tests/presets_test.php
#  2. a simulated weekly check on a staging copy (Apex reads « $200 per winning day » instead of $250 on the EOD 50K):
#       SWEEP_PRESETS_MOCK=tests/presets_mock.json php presets/cron.php --firm=apex --dry-run
cd "$(dirname "$0")/.." && php tests/presets_test.php
