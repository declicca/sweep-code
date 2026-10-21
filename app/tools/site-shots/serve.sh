#!/bin/sh
# Sweep — the site's captures (brief of 20 Oct. 2026): a served copy with an empty database, the clock pinned on a weekday
# of the New York session, Sweep AI answered by this folder's stand-ins; runs the command, then stops the server.
#   sh tools/site-shots/serve.sh <command…>        (DEST=/tmp/gs, PORT=8996, SHOTS_NOW="2026-10-15 11:05" New York time)
DEST=${DEST:-/tmp/gs}; PORT=${PORT:-8996}; HERE="$(cd "$(dirname "$0")" && pwd)"; TOOLS="$(dirname "$HERE")"
export PATH="$HOME/.venvs/sweep/bin:/opt/homebrew/bin:/opt/homebrew/opt/coreutils/libexec/gnubin:/opt/homebrew/opt/gnu-sed/libexec/gnubin:$PATH"
sh "$TOOLS/sync.sh" "$DEST" >/dev/null && rm -rf "$DEST/data" && mkdir -p "$DEST/data"
export SWEEP_TEST_DB="$DEST/data/journal.db" SWEEP_GAME_NOW="${SHOTS_NOW:-2026-10-15 11:05}" SHOTS_NOW="${SHOTS_NOW:-2026-10-15 11:05}"
export SWEEP_AI_CONFIG="$TOOLS/ai-config.local.php" SWEEP_AI_MOCK="$HERE/shot-ai.json" SWEEP_AI_CHAT_MOCK="$HERE/chat-ai.json" SWEEP_AI_OFFLINE=1
export SWEEP_CHART_CONFIG="$HERE/chart-config.php" SHOTS_BARS="${SHOTS_BARS:-/tmp/gs-bars}"
export SWEEP_PUSH_CONFIG="$TOOLS/push-config.local.php" SWEEP_PUSH_MOCK="$DEST/data/push-sent.jsonl"
rm -rf "$SHOTS_BARS" && python3 "$HERE/bars.py" "$SHOTS_BARS" >/dev/null
(cd "$DEST" && PHP_CLI_SERVER_WORKERS=4 exec php -S 127.0.0.1:$PORT router.php > "${TMPDIR:-/tmp}/sweep-php-$PORT.log" 2>&1) &
SRV=$!
for i in $(seq 1 50); do curl -s -o /dev/null "http://127.0.0.1:$PORT/api/auth/config" && break; sleep 0.2; done
"$@"; rc=$?
kill $SRV 2>/dev/null; pkill -P $SRV 2>/dev/null; wait $SRV 2>/dev/null
exit $rc
