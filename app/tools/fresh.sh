#!/bin/sh
# Empty database for the served copy.
DEST=${DEST:-/tmp/g}; rm -rf "$DEST/data"; mkdir -p "$DEST/data"
