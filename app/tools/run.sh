#!/bin/sh
# Starts php -S on the served copy (port 8095, or PORT=…; DEST=/tmp/g), with mocked presets and Sweep AI, runs the command, stops the server.
#   sh tools/run.sh <command…>
DEST=${DEST:-/tmp/g}; PORT=${PORT:-8095}; TOOLS="$(cd "$(dirname "$0")" && pwd)"
export PATH="$HOME/.venvs/sweep/bin:/opt/homebrew/bin:/opt/homebrew/opt/coreutils/libexec/gnubin:/opt/homebrew/opt/gnu-sed/libexec/gnubin:$PATH"
export SWEEP_PRESETS_MOCK="$DEST/tests/presets_mock.json" SWEEP_TEST_DB="$DEST/data/journal.db"
export SWEEP_AI_CONFIG="$TOOLS/ai-config.local.php" SWEEP_AI_MOCK="$DEST/tests/samples/shot-ai-mock.json"
# market weekend: the game runs on Friday 15:00 ET (tools/game-now.py), the tests need an open session
GN=$(python3 -I "$TOOLS/game-now.py"); [ -n "$GN" ] && export SWEEP_GAME_NOW="$GN" && echo "SWEEP_GAME_NOW=$GN (market weekend)" >&2
(cd "$DEST" && PHP_CLI_SERVER_WORKERS=4 exec php -S 127.0.0.1:$PORT router.php > "${TMPDIR:-/tmp}/sweep-php-$PORT.log" 2>&1) &
SRV=$!
for i in $(seq 1 50); do curl -s -o /dev/null "http://127.0.0.1:$PORT/api/auth/config" && break; sleep 0.2; done
"$@"; rc=$?
kill $SRV 2>/dev/null; pkill -P $SRV 2>/dev/null; wait $SRV 2>/dev/null
exit $rc
