#!/bin/sh
# Sweep — build the served files of our modules from the readable sources in src/.
# Each module is minified (terser for JS, csso without restructuring for CSS) and named with a content hash.
# CSS: all the style sheets are joined, in order, into ONE file (assets/bundle.<hash>.css) — one request instead of seven.
# JS: app.html loads the modules in order (app.js, the core, first); chart.js is loaded on demand (nav.js: window.SWEEP_LAZY).
# Run from the app folder:  sh ops/build-assets.sh        Needs Node: npm install -g terser csso-cli
set -e
cd "$(dirname "$0")/.."
for k in app nav game ux guide notify chart coach; do   # app: the core (src/app.js since 9 Oct 2026); coach: brief 03 step 2
  for e in js css; do
    src="src/$k.$e"; [ -f "$src" ] || continue
    tmp="assets/$k.build.$e"
    if [ "$e" = js ]; then terser "$src" -c -m --ecma 2020 --comments false -o "$tmp"; else csso "$src" --no-restructure -o "$tmp"; fi
    h=$(md5sum "$tmp" | cut -c1-10); new="assets/$k.$h.$e"
    mv "$tmp" "$new"
    # every older copy goes, and app.html points to the new one, whatever name it had (16 Oct.: after a merge, only the first
    # copy by name was replaced — app.html kept a stale or missing module, and the CSS bundle could take a stale one)
    for old in $(grep -o "assets/$k\.[0-9a-f]\{10\}\.$e" app.html; ls assets/$k.*.$e 2>/dev/null | grep -v -e '\.build\.' -e '^assets/bundle\.'); do
      [ "$old" = "$new" ] && continue; sed -i "s#$old#$new#g" app.html; rm -f "$old"
    done
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
for old in $(grep -o 'assets/bundle\.[a-z0-9]*\.css' app.html; ls assets/bundle.*.css 2>/dev/null | grep -v '\.build\.'); do
  [ "$old" = "$new" ] && continue; sed -i "s#$old#$new#g" app.html; rm -f "$old"
done
echo "bundle.css → $new"
