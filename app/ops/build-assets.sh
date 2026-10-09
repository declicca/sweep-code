#!/bin/sh
# Sweep — build the served files of our modules from the readable sources in src/.
# Each module is minified (terser for JS, csso without restructuring for CSS) and named with a content hash.
# CSS: all the style sheets are joined, in order, into ONE file (assets/bundle.<hash>.css) — one request instead of seven.
# JS: app.html loads the modules in order; chart.js is loaded on demand (nav.js: window.SWEEP_LAZY).
# Run from the app folder:  sh ops/build-assets.sh        Needs Node: npm install -g terser csso-cli
set -e
cd "$(dirname "$0")/.."
for k in nav game ux guide notify chart; do
  for e in js css; do
    src="src/$k.$e"; [ -f "$src" ] || continue
    old=$(ls assets/$k.*.$e 2>/dev/null | grep -v '\.build\.' | head -1 || true)
    tmp="assets/$k.build.$e"
    if [ "$e" = js ]; then terser "$src" -c -m --ecma 2020 --comments false -o "$tmp"; else csso "$src" --no-restructure -o "$tmp"; fi
    h=$(md5sum "$tmp" | cut -c1-10); new="assets/$k.$h.$e"
    mv "$tmp" "$new"
    if [ -n "$old" ] && [ "$old" != "$new" ]; then sed -i "s#$old#$new#g" app.html; rm -f "$old"; fi
    echo "$k.$e → $new"
  done
done
# one CSS file, in the cascade order of ops/css-order.txt (app first, nav last)
tmp=assets/bundle.build.css; : > "$tmp"
for k in $(cat ops/css-order.txt); do
  f=$(ls assets/$k.*.css 2>/dev/null | grep -v -e '\.build\.' -e '^assets/bundle\.' | head -1)
  [ -n "$f" ] || { echo "missing CSS for $k" >&2; exit 1; }
  cat "$f" >> "$tmp"; printf '\n' >> "$tmp"
done
h=$(md5sum "$tmp" | cut -c1-10); new="assets/bundle.$h.css"; mv "$tmp" "$new"
old=$(grep -o 'assets/bundle\.[a-z0-9]*\.css' app.html | head -1 || true)
if [ -n "$old" ] && [ "$old" != "$new" ]; then sed -i "s#$old#$new#g" app.html; rm -f "$old"; fi
echo "bundle.css → $new"
