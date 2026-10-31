"""
Sweep — the 5 points of the 30 Oct. tour (briefs/brief-app-tour-2026-10-30.md), Playwright:
  python3 tests/e2e_tour_1030.py http://127.0.0.1:8095
A trader of its own; phone 390 (fr, touch, dark), computer 1300 (en, light), phone 390 (es, light).
 W1 a trade without a time typed while the market is closed goes to the last session that ended (clock pinned):
    Friday 18:44, Saturday 12:00 and Sunday 12:00 → Friday; Tuesday 17:30 → Tuesday; Tuesday 19:00 (open) → Wednesday
 W2 the welcome on Friday evening: « Prépare ta séance de lundi », « Ton plan de lundi »; Sunday noon: « demain »
 W3 Settings: every group folded on arrival, « Account » last, the 90-day gameplan in « My routine »
 W4 the gameplan: « 1 mission faite », never « 1 missions »
 W5 Today (computer): « of which Eval … »: the words in Geist, the amounts in Geist Mono
No page error, nothing wider than the window.
"""
import json, os, random, sqlite3, sys
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
H = {'Content-Type': 'application/json', 'X-Requested-With': 'fetch'}
DB = os.environ.get('SWEEP_TEST_DB', '/tmp/g/data/journal.db')
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)
X = {'fr': {'mon': 'Prépare ta séance de lundi.', 'mon2': 'Ton plan de lundi', 'tom': 'Prépare ta séance de demain.', 'g': ['Ma routine', 'Notifications', 'Données', 'Avancé', 'Compte'], 'one': '1 mission faite'},
     'en': {'mon': 'Prepare Monday’s session.', 'mon2': 'Your plan for Monday', 'tom': 'Prepare tomorrow’s session.', 'g': ['My routine', 'Notifications', 'Data', 'Advanced', 'Account'], 'one': '1 mission done'},
     'es': {'mon': 'Prepara tu sesión del lunes.', 'mon2': 'Tu plan del lunes', 'tom': 'Prepara tu sesión de mañana.', 'g': ['Mi rutina', 'Notificaciones', 'Datos', 'Avanzado', 'Cuenta'], 'one': '1 misión hecha'}}
# New York times (EDT until Sunday 1 Nov. 2:00, EST after) → the day the trade goes to
W1 = [('2026-10-30T18:44:00-04:00', '2026-10-30'), ('2026-10-31T12:00:00-04:00', '2026-10-30'), ('2026-11-01T12:00:00-05:00', '2026-10-30'),
      ('2026-11-03T17:30:00-05:00', '2026-11-03'), ('2026-11-03T19:00:00-05:00', '2026-11-04')]
FLUSH = "Promise.all(Object.values(chains)).then(() => true)"
def clear():
  try: d = sqlite3.connect(DB); d.execute('DELETE FROM attempts'); d.commit(); d.close()
  except Exception: pass
with sync_playwright() as p:
  br = p.chromium.launch(); errs = []
  for lang, phone, scheme in (('fr', True, 'dark'), ('en', False, 'light'), ('es', True, 'light')):
    w = 390 if phone else 1300; tag = f'{w}-{lang}-{scheme}'; x = X[lang]
    kw = dict(viewport={'width': w, 'height': 844 if phone else 850}, is_mobile=phone, has_touch=phone, color_scheme=scheme, locale={'fr': 'fr-CA', 'en': 'en-US', 'es': 'es-MX'}[lang])
    # W2: the welcome page on Friday evening, then on Sunday noon
    for now, want, step in (('2026-10-30T18:44:00-04:00', x['mon'], x['mon2']), ('2026-11-01T12:00:00-05:00', x['tom'], None)):
      clear(); c1 = br.new_context(**kw)
      c1.add_init_script("localStorage.setItem('tj.lang', JSON.stringify('%s')); window.__swNow = '%s'" % (lang, now))
      c1.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': 'tw%06d@t.dev' % random.randint(0, 999999), 'consent': True, 'elapsed': 6000}), headers=H)
      p1 = c1.new_page(); p1.on('pageerror', lambda e: errs.append(str(e)[:160])); p1.goto(B + '/'); p1.wait_for_selector('#main .onb', timeout=20000); p1.wait_for_timeout(800)
      txt = p1.locator('#main .onb').inner_text(); steps = p1.evaluate("[...document.querySelectorAll('#main .onb-steps li')].map((l) => l.textContent.replace(/^\\d+/, '').trim())")
      ok(want in txt and (step is None or steps[-1:] == [step]), f'W2 {tag} {now[5:16]}: « {want} »{" « " + step + " »" if step else ""} ({steps})')
      c1.close()
    clear()
    ctx = br.new_context(**kw)
    ctx.add_init_script("try { localStorage.setItem('tj.lang', JSON.stringify('%s')); sessionStorage.setItem('sw.modal', '1') } catch (e) {}" % lang)
    ctx.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': 'tx%06d@t.dev' % random.randint(0, 999999), 'consent': True, 'elapsed': 6000}), headers=H)
    ctx.request.post(B + '/api/me/profile', data=json.dumps({'first_name': 'Léa', 'experience': 'lt6'}), headers=H)
    pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
    pg.goto(B + '/#dashboard'); pg.wait_for_timeout(2500)
    pg.evaluate("put('accounts', { id: 'tx-a', name: 'Topstep 50K', status: 'active', phase: 'eval', starting_balance_c: 5000000, created_on: '2026-09-01', rules: { dd_c: 200000, dll_c: 100000 } })")
    pg.evaluate("put('accounts', { id: 'tx-b', name: 'Topstep 50K F', status: 'active', phase: 'funded', starting_balance_c: 5000000, created_on: '2026-09-01', rules: { dd_c: 200000 } })")
    pg.evaluate(FLUSH)
    # W1: the quick sheet (« No screenshot? »), no time typed, at each pinned time
    got = []
    for now, want in W1:
      pg.clock.set_fixed_time(now); pg.wait_for_timeout(200)
      pg.evaluate("SweepAddMode.open()"); pg.wait_for_selector('.nav-am.open [data-am=no-shot]', timeout=8000); pg.wait_for_timeout(300)
      pg.locator('.nav-am.open [data-am=no-shot]').click(); pg.wait_for_selector('.nav-am.open [data-am-f=net]', timeout=8000)
      pg.locator('.nav-am.open [data-am-f=net]').fill(str(-50 - 7 * len(got))); pg.locator('.nav-am.open [data-am-seg=dir][data-v=short]').click()
      ids = pg.evaluate("S.trades.map((t) => t.id)")
      pg.locator('.nav-am.open [data-am=save]').click(); pg.wait_for_timeout(1200)
      t = pg.evaluate("(ids) => (S.trades.find((t) => !ids.includes(t.id)) || {}).date || null", ids)
      got.append(t); ok(t == want, f'W1 {tag}: a trade typed at {now[:16]} goes to {want} ({t})')
      pg.evaluate("document.querySelectorAll('.g-sweep [data-g=sw-close], .nav-am.open [data-am=close]').forEach((b) => b.click())"); pg.wait_for_timeout(300)
    pg.evaluate(FLUSH)
    # W5: computer, Today's week line « of which Eval … · Funded … »
    if not phone:
      for i, (acc, c) in enumerate((('tx-a', -517700), ('tx-b', 30000))):
        pg.evaluate("([id, a, c]) => put('trades', { id, account_id: a, instrument: 'MNQ', direction: 'long', contracts: 1, entry: 1, exit: 2, pnl_c: c, pnl_manual: true, date: todayStr(), session_date: true, entry_time: '10:0' + id.slice(-1), exit_time: '10:30' })", [f'tx-w{i}', acc, c])
      pg.evaluate(FLUSH); pg.evaluate("location.hash = '#calendar'"); pg.wait_for_timeout(600); pg.evaluate("location.hash = '#dashboard'"); pg.wait_for_timeout(1800)
      pg.evaluate("document.querySelectorAll('#main [data-kt=week]').forEach((b) => b.click())"); pg.wait_for_timeout(800)
      f = pg.evaluate("""(() => { const s = document.querySelector('#main .nav-split'); if (!s) return null; const b = s.querySelector('b'), w = s.querySelector('span');
        return [getComputedStyle(s).fontFamily, getComputedStyle(w).fontFamily, b && getComputedStyle(b).fontFamily] })()""")
      ok(f and not f[0].startswith('"Geist Mono"') and 'Mono' not in f[1] and 'Mono' in (f[2] or ''), f'W5 {tag}: « of which … »: the words in Geist, the amounts in Geist Mono ({f})')
    # W3: Settings
    pg.evaluate("sessionStorage.removeItem('sw.sgd'); location.hash = '#settings'"); pg.wait_for_selector('#main details.nav-sgd', timeout=10000)
    pg.wait_for_selector('#main .gp-set h2', state='attached', timeout=10000); pg.wait_for_timeout(600)
    g = pg.evaluate("[...document.querySelectorAll('#main details.nav-sgd')].map((d) => [d.querySelector('summary').textContent.trim(), d.open])")
    ok([n for n, o in g] == x['g'] and not any(o for n, o in g), f'W3 {tag}: groups all folded, « {x["g"][-1]} » last ({g})')
    ok(pg.evaluate("(() => { const s = document.querySelector('#main .gp-set'), d = s && s.closest('details.nav-sgd'); return !!d && d.dataset.i === '1' })()"), f'W3 {tag}: the 90-day gameplan in « {x["g"][0]} »')
    # W4: one mission done
    pg.evaluate("fetch('api/game/gameplan/start', { method: 'POST', headers: { 'X-Requested-With': 'fetch', 'Content-Type': 'application/json' }, body: JSON.stringify({ track: 'B' }) })"); pg.wait_for_timeout(1200)
    pg.evaluate("SweepGPLoad().then((g) => { const st = Object.assign({}, g.state(), { started: true, day: 2, done: { 1: 1 } }); g.mount(st); })"); pg.wait_for_timeout(800)
    s = pg.evaluate("document.querySelector('#main .gp-set').textContent")
    ok(x['one'] in s and ('1 missions' not in s and '1 misiones' not in s), f'W4 {tag}: « {x["one"]} » ({s[-120:]!r})')
    pg.evaluate("SweepGPLoad().then((g) => g.openMap())"); pg.wait_for_timeout(1500)
    m = pg.evaluate("(document.querySelector('#gSheet') || document.body).innerText")
    ok(x['one'] in m, f'W4 {tag}: the map says « {x["one"]} » too')
    ok(pg.evaluate("document.documentElement.scrollWidth - innerWidth") <= 0, f'{tag}: nothing wider than the window')
    ctx.close()
  ok(not errs, f'no page error ({errs[:2]})')
  br.close()
print(f'{fails} failed' if fails else 'all passed')
sys.exit(1 if fails else 0)
