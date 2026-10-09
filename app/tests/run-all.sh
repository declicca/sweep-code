#!/bin/sh
# Sweep — runs the tests and prints « N passed, N failed » (dev environment: PHP, Python 3 + Playwright).
#   sh tests/run-all.sh [base_url] [storage_state] [--all]
# The app must be served at base_url (default http://127.0.0.1:8095) with a signed-in admin session saved in
# storage_state (default /tmp/show_state.json). Without --all: the server tests and every end-to-end test that checks
# its own result (exit code, or « FAIL » / « ❌ » / a traceback in its output). With --all: also the older visual and
# exploratory scripts of tests/ (screenshots, measures), counted as failed only when they crash.
BASE=${1:-http://127.0.0.1:8095}; STATE=${2:-/tmp/show_state.json}; ALL=0
for a in "$@"; do [ "$a" = "--all" ] && ALL=1; done
cd "$(dirname "$0")/.."
CORE="e2e_session_parity e2e_accuracy e2e_clarity e2e_a11y_names e2e_import_session_day e2e_delete_undo_copy_dates e2e_session_news_ui
e2e_presets_firms e2e_prop_rules e2e_isolation e2e_eval_to_funded e2e_payout_conditions e2e_live_accounts
e2e_acceptance e2e_no_english_in_fr_es e2e_redraw_no_replay e2e_no_jumps e2e_quiet_sync e2e_history_back e2e_rows_open e2e_plan_journal e2e_import_tradingview e2e_visual_fit e2e_money e2e_money_parity e2e_shot_multi e2e_scroll_stable e2e_realnet e2e_lot_a"
pass=0; fail=0; failed=""; log=${TMPDIR:-/tmp}/sweep-run-all.log; : > "$log"
# SWEEP_TEST_DB (SQLite of the dev server): sign-up attempts are cleared before each test (the tests create many traders)
reset_attempts() { [ -n "$SWEEP_TEST_DB" ] && php -r '$p=new PDO("sqlite:".getenv("SWEEP_TEST_DB")); try { $p->exec("DELETE FROM attempts"); } catch (Throwable $e) {}' 2>/dev/null; return 0; }
check() {   # name, exit code, output file
  if [ "$2" -eq 0 ] && ! grep -q -E '^FAIL|❌|Traceback|^[0-9]+ failed|^failed$' "$3"; then pass=$((pass+1)); echo "ok    $1"
  else fail=$((fail+1)); failed="$failed $1"; echo "FAIL  $1"; fi
  { echo "===== $1 (exit $2)"; cat "$3"; } >> "$log"
}
out=$(mktemp)
php tests/presets_test.php > "$out" 2>&1; check presets_test.php $? "$out"
php tests/shot_trades_test.php > "$out" 2>&1; check shot_trades_test.php $? "$out"
for t in $CORE; do
  [ -f "tests/$t.py" ] || continue
  reset_attempts; timeout 900 python3 "tests/$t.py" "$BASE" "$STATE" > "$out" 2>&1; check "$t" $? "$out"
done
if [ "$ALL" = 1 ]; then
  for f in tests/*.py; do
    t=$(basename "$f" .py); case " $(echo $CORE | tr '\n' ' ') " in *" $t "*) continue;; esac
    timeout 600 python3 "$f" "$BASE" "$STATE" > "$out" 2>&1; rc=$?
    if [ $rc -eq 0 ] || ! grep -q 'Traceback' "$out"; then rc=0; : > "$out.ok"; check "$t (script)" 0 "$out.ok"; else check "$t (script)" 1 "$out"; fi
  done
fi
rm -f "$out" "$out.ok"
echo; echo "$pass passed, $fail failed"; [ -n "$failed" ] && echo "failed:$failed" && echo "details: $log"
[ "$fail" -eq 0 ]
