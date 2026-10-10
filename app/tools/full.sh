#!/bin/sh
# Fresh database + full suite (tests/run-all.sh runs tests/setup.py first). Run inside run.sh:  sh tools/run.sh sh tools/full.sh
TOOLS="$(cd "$(dirname "$0")" && pwd)"; DEST=${DEST:-/tmp/g}
sh "$TOOLS/fresh.sh" && (cd "$DEST" && sh tests/run-all.sh "$@")
