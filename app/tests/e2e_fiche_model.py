"""
Sweep — the pre-market sheet's model (brief « Plan pre-market adaptatif », step 1), with Playwright, phone 390 and computer 1300:
  python3 tests/e2e_fiche_model.py http://127.0.0.1:8095 /tmp/show_state.json
 1  the trading day in the app is the server's (game/fiche.php), moment by moment: 17:59 / 18:00 NY, Friday evening, weekend
 2  the lock time: 09:25 NY of the sheet's day, the same on both sides
 3  a new sheet: the instrument of the last real trade (sample data never count), default limits (0.5 %, 2 trades), unlocked
 4  saved in the day's journal, back after a reload; the server keeps only the model (an unknown field, a risk of 3 %, 99 trades)
 5  a locked sheet changes no more (the app refuses)
The test day (2027-03-01) is removed at the end.
"""
import json, os, subprocess, sys
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails = 0
def until(pg, expr, ms=20000):   # (the app's CSP forbids wait_for_function)
  for _ in range(ms // 200):
    if pg.evaluate(f'!!({expr})'): return True
    pg.wait_for_timeout(200)
  return False
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)

MOMENTS = ['2026-10-19 17:59', '2026-10-19 18:00', '2026-10-20 09:25', '2026-10-23 17:59', '2026-10-23 18:00', '2026-10-24 12:00', '2026-10-25 18:05', '2026-11-01 01:30', '2026-03-08 18:00']
php = subprocess.run(['php', '-r', 'require "game/fiche.php"; $z = new DateTimeZone("America/New_York"); $o = [];'
                      'foreach (json_decode($argv[1], true) as $m) { $t = (new DateTimeImmutable($m, $z))->getTimestamp(); $o[] = [$t, Fiche::dayOf($t)]; }'
                      'echo json_encode(["days" => $o, "lock" => [Fiche::lockEpoch("2026-10-20"), Fiche::lockEpoch("2026-12-14")]]);', json.dumps(MOMENTS)],
                     cwd=APP, capture_output=True, text=True)
ref = json.loads(php.stdout)
DAY = '2027-03-01'
H = "{'Content-Type': 'application/json', 'X-Requested-With': 'fetch'}"

with sync_playwright() as p:
  br = p.chromium.launch(); errs = []
  for w, phone in [(390, True), (1300, False)]:
    c = br.new_context(storage_state=STATE, viewport={'width': w, 'height': 844 if phone else 850}, is_mobile=phone, has_touch=phone, locale='fr-CA')
    c.add_init_script("sessionStorage.setItem('sw.modal','1')")
    pg = c.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
    pg.goto(B + '/#dashboard'); until(pg, 'window.SweepFiche && window.S && S.trades'); pg.wait_for_timeout(1200)
    got = pg.evaluate("(l) => l.map(([t]) => SweepFiche.dayOf(t * 1000))", ref['days'])
    ok(got == [d for _, d in ref['days']], f'1 {w}: the trading day matches the server, moment by moment ({got})')
    lock = pg.evaluate("[SweepFiche.lockAt('2026-10-20', '09:25'), SweepFiche.lockAt('2026-12-14', '09:25')]")
    ok(lock == ref['lock'], f'2 {w}: lock at 09:25 NY, summer and winter, the same as the server ({lock})')
    b = pg.evaluate("(d) => { const f = SweepFiche.blank(d); const real = (S.trades || []).filter((t) => !t.demo && t.instrument && t.date < d).sort((a, b) => (b.date + (b.entry_time || '')).localeCompare(a.date + (a.entry_time || '')))[0]; return [f, real ? real.instrument : '', SweepFiche.locked(f)] }", DAY)
    ok(b[0]['instrument'] == b[1] and b[0]['limits'] == {'risk_pct': 0.5, 'max_trades': 2, 'time_limit': None} and b[0]['mode'] == 'full' and not b[2],
       f"3 {w}: a new sheet — last real instrument ({b[1]!r}), 0.5 %, 2 trades, full, unlocked")
    saved = pg.evaluate("(d) => { const f = SweepFiche.blank(d); f.instrument = 'MES'; f.levels.london_high = 5820; f.levels.london_low = 5800; f.limits.time_limit = '11:30';"
                        " f.scenarios = [{ id: 'A', direction: 'short', type: 'breakdown', level: 5800, stop_estimate: 5806, target: 5780, r_estimate: 3.33 }]; return SweepFiche.save(f) }", DAY)
    pg.wait_for_timeout(1500); pg.reload(); until(pg, 'window.SweepFiche && window.S && S.journals'); pg.wait_for_timeout(1500)
    f = pg.evaluate("(d) => SweepFiche.get(d)", DAY)
    ok(saved and f and f['instrument'] == 'MES' and f['levels']['london_high'] == 5820 and f['scenarios'][0]['conditions'] == ['close_15m', 'retest_5m', 'trigger_5m', 'risk_checked'] and f['limits']['time_limit'] == '11:30',
       f'4 {w}: the sheet is in the day\'s journal and back after a reload')
    st = pg.evaluate("async ([d, f]) => { f.junk = 'x'; f.limits.risk_pct = 3; f.limits.max_trades = 99; const j = structuredClone(getDoc('journals', d)); j.fiche = f;"
                     " const r = await fetch('api/docs/journals/' + d, {method: 'PUT', headers: " + H + ", body: JSON.stringify(j)}); return r.status }", [DAY, f])
    srv = pg.evaluate("async (d) => { const r = await fetch('api/data', {headers: {'X-Requested-With': 'fetch'}}); const x = await r.json(); const j = ((x.journals || x.data && x.data.journals) || []).find((y) => y.id === d); return j && j.fiche }", DAY)
    ok(st == 200 and srv and 'junk' not in srv and srv['limits']['risk_pct'] == 0.5 and srv['limits']['max_trades'] == 20, f'4 {w}: the server keeps the model only ({srv and srv["limits"]})')
    lk = pg.evaluate("(d) => { const f = SweepFiche.get(d); f.locked_at = Math.floor(Date.now() / 1000); const a = SweepFiche.save(f); const g = SweepFiche.get(d); g.instrument = 'NQ'; return [a, SweepFiche.save(g), SweepFiche.get(d).instrument] }", DAY)
    ok(lk == [True, False, 'MES'], f'5 {w}: locked, the sheet changes no more ({lk})')
    pg.evaluate("async (d) => { await fetch('api/docs/journals/' + d, {method: 'DELETE', headers: {'X-Requested-With': 'fetch'}}) }", DAY)
    c.close()
  ok(not errs, f'no page error ({errs[:2]})')
  br.close()
print('all passed' if not fails else f'{fails} failed')
sys.exit(1 if fails else 0)
