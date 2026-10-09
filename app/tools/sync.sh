#!/bin/sh
# Copies app/ to the served copy (default /tmp/g) without data/ and config.php, then installs the local config.
set -e
DEST=${1:-/tmp/g}; APP="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "$DEST"
rsync -a --delete --exclude data/ --exclude config.php --exclude .DS_Store "$APP/" "$DEST/"
cp "$APP/tools/router.php" "$DEST/router.php"
cp "$APP/tools/config.local.php" "$DEST/config.php"
