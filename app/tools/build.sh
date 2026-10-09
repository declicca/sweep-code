#!/bin/sh
# Checks every source JS, then builds assets/ (ops/build-assets.sh stops at the first error and keeps the old files).
set -e
export PATH="$HOME/.npm-global/bin:/opt/homebrew/opt/coreutils/libexec/gnubin:/opt/homebrew/opt/gnu-sed/libexec/gnubin:/opt/homebrew/bin:$PATH"
cd "$(dirname "$0")/.."
for f in src/*.js; do node --check "$f"; done
sh ops/build-assets.sh
