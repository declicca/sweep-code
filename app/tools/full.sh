#!/bin/sh
# Fresh database + profile + sample data + full suite. Run inside run.sh:  sh tools/run.sh sh tools/full.sh
TOOLS="$(cd "$(dirname "$0")" && pwd)"; DEST=${DEST:-/tmp/g}
sh "$TOOLS/fresh.sh" && python3 "$TOOLS/prof.py" && (cd "$DEST" && sh tests/run-all.sh "$@")
