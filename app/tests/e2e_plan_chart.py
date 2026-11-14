"""
Sweep — Plan Sync, step 1 (BRIEF_PLAN_SYNC, 13 Nov. 2026): the plan on the chart, Playwright:
  python3 tests/e2e_plan_chart.py http://127.0.0.1:8095 /tmp/show_state.json
Phone 390 (touch) and computer 1300, FR / EN / ES, dark and light, the browser's clock at 08:30 New York on a test day:
 1  the express plan shows one row « Plan on the chart »; a tap opens its sheet over the plan (the plan stays under it):
    « Not connected yet » with the link to the add-on, no blue button on the list
 2  a level: a price off the tick is refused with the right price to try; PDH 21,290.25 on MNQ is saved on NQ with its
    40 ticks; a zone typed upside down is refused, then saved (support, long)
 3  a rule « if price sweeps PDH on the 5m, then remind me of my plan », its sentence in the trader's language, saved
 4  edited (the level moved), the zone deleted, then the level deleted: its rule goes with it; on the server, the day's
    journal carries what the sheet shows (the New York day of the plan), and nothing else
 5  « Use yesterday's zones » copies the last day's zones (once, phone FR)
 6  nothing overflows the page, every button of the sheet is inside it, no page error
The test days are removed at the end.
"""
import datetime as dt, json, sys
from zoneinfo import ZoneInfo
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
NY = ZoneInfo('America/New_York')
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)
def until(pg, expr, ms=15000):
  for _ in range(ms // 150):
    if pg.evaluate(f'!!({expr})'): return True
    pg.wait_for_timeout(150)
  return False
X = {'fr': {'row': 'Plan sur le chart', 'off': 'Pas encore connecté', 'tick': 'n’est pas un prix possible', 'zone': 'Le haut doit être au-dessus du bas',
            'say': 'Si le prix sweep « PDH » en 5m, alors rappelle-moi mon plan : « Attendre le retour sous le PDH ».', 'resumed': 'reprises', 'locale': 'fr-CA'},
     'en': {'row': 'Plan on the chart', 'off': 'Not connected yet', 'tick': 'is not a possible price', 'zone': 'The high must be above the low',
            'say': 'If price sweeps “PDH” on the 5m, then remind me of my plan: “Attendre le retour sous le PDH”.', 'resumed': 'copied', 'locale': 'en-US'},
     'es': {'row': 'Plan en el gráfico', 'off': 'Aún no conectado', 'tick': 'no es un precio posible', 'zone': 'El alto debe estar por encima del bajo',
            'say': 'Si el precio hace sweep de «PDH» en 5m, entonces recuérdame mi plan: «Attendre le retour sous le PDH».', 'resumed': 'retomadas', 'locale': 'es-ES'}}
RUNS = [(390, True, 'fr', 'dark', '2027-04-13'), (1300, False, 'en', 'light', '2027-04-14'), (390, True, 'es', 'light', '2027-04-15'), (1300, False, 'fr', 'dark', '2027-04-16')]
FIT = """() => { const sh = document.querySelector('#pcSheet'); if (!sh) return 'no sheet'; const r = sh.getBoundingClientRect(), bad = [];
  sh.querySelectorAll('button, input, select, textarea').forEach((b) => { if (!b.getClientRects().length) return; const x = b.getBoundingClientRect(); if (x.width && (x.left < r.left - 1 || x.right > r.right + 1)) bad.push((b.textContent || b.dataset.pc || b.tagName).trim().slice(0, 30)); });
  if (document.documentElement.scrollWidth > innerWidth + 1) bad.push('page ' + document.documentElement.scrollWidth); return bad.join(' | '); }"""
def server_day(pg, day):
  return pg.evaluate("(d) => fetch('api/data', { headers: { 'X-Requested-With': 'fetch' } }).then((r) => r.json()).then((x) => ((x.journals || x.data && x.data.journals || []).find((j) => j.id === d) || null))", day)
def tap(pg, sel, wait=350):
  pg.locator(sel).first.click(); pg.wait_for_timeout(wait)

with sync_playwright() as p:
  br = p.chromium.launch(); errs = []; days = []
  for w, phone, lang, scheme, day in RUNS:
    x = X[lang]; tag = f'{w}-{lang}-{scheme}'; days.append(day)
    c = br.new_context(storage_state=STATE, viewport={'width': w, 'height': 844 if phone else 850}, is_mobile=phone, has_touch=phone, locale=x['locale'], color_scheme=scheme)
    c.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('%s'))" % lang)
    y, m, d = map(int, day.split('-'))
    c.clock.set_fixed_time(dt.datetime(y, m, d, 8, 30, tzinfo=NY))
    pg = c.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
    pg.goto(B + '/#dashboard'); until(pg, 'window.SweepGame && window.SweepPlanChart && window.S && S.journals'); pg.wait_for_timeout(1500)
    pg.evaluate("(d) => { if (getDoc('journals', d)) remove('journals', d); }", day); pg.wait_for_timeout(500)
    # 1. the row in the express plan, the sheet over the plan
    pg.evaluate("(d) => SweepGame.openPlan(d)", day); until(pg, "document.querySelector('#gSheet.g-pm')"); pg.wait_for_timeout(700)
    if pg.locator('#gSheet [data-pm-screen=express]').count() == 0: pg.locator('#gSheet [data-pm=mode][data-v=express]').click(); pg.wait_for_timeout(600)   # (this test account makes guided plans)
    row = pg.locator('#gSheet .pc-row').first
    row.scroll_into_view_if_needed(); pg.wait_for_timeout(200)
    ok(row.is_visible() and x['row'] in row.inner_text(), f'1 {tag}: the plan shows the row « {x["row"]} » ({row.inner_text()[:60]!r})')
    row.click(); until(pg, "document.querySelector('#pcSheet.open')"); pg.wait_for_timeout(500)
    ok(pg.locator('#pcSheet').is_visible() and pg.locator('#gSheet.g-pm').count() == 1, f'1 {tag}: its sheet opens over the plan, the plan stays under it')
    ok(x['off'] in pg.locator('#pcSheet .pc-sync').inner_text() and pg.locator('#pcSheet .pc-sync a[href="#settings/sync"]').is_visible(), f'1 {tag}: « {x["off"]} » with the link to the add-on')
    ok(pg.locator('#pcSheet .btn.primary').count() == 0, f'1 {tag}: no blue button on the list')
    # 2. a level, then a zone
    tap(pg, '#pcSheet [data-pc=new-zone]')
    tap(pg, '#pcSheet [data-pc=set][data-k=instrument][data-v=NQ]')
    pg.fill('#pcSheet [data-pcf=price]', '21290.2'); tap(pg, '#pcSheet [data-pc=set][data-k=label][data-v=PDH]'); tap(pg, '#pcSheet [data-pc=set][data-k=role][data-v=resistance]')
    tap(pg, '#pcSheet [data-pc=save-zone]')
    er = pg.locator('#pcSheet .pc-err').inner_text() if pg.locator('#pcSheet .pc-err').count() else ''
    ok(x['tick'] in er and ('21' in er and '290,25' in er.replace(' ', ' ').replace('\xa0', ' ') if lang != 'en' else '21,290.25' in er), f'2 {tag}: off the tick: refused, with the price to try ({er!r})')
    pg.fill('#pcSheet [data-pcf=price]', '21290.25'); tap(pg, '#pcSheet [data-pc=save-zone]', 700)
    ch = pg.evaluate("(d) => (getDoc('journals', d) || {}).chart", day) or {}
    z0 = (ch.get('zones') or [{}])[0]
    ok(len(ch.get('zones', [])) == 1 and z0.get('price') == 21290.25 and z0.get('instrument') == 'NQ' and z0.get('proximity_ticks') == 40 and z0.get('label') == 'PDH' and z0.get('role') == 'resistance', f'2 {tag}: the level saved: NQ, 21290.25, 40 ticks, PDH, resistance ({z0})')
    ok(pg.locator('#pcSheet .pc-item').count() == 1 and 'PDH' in pg.locator('#pcSheet .pc-item').first.inner_text(), f'2 {tag}: back on the list, the level shown')
    tap(pg, '#pcSheet [data-pc=new-zone]'); tap(pg, '#pcSheet [data-pc=set][data-k=type][data-v=zone]')
    pg.fill('#pcSheet [data-pcf=high]', '21180'); pg.fill('#pcSheet [data-pcf=low]', '21200'); pg.fill('#pcSheet [data-pcf=label]', 'Buy zone')
    tap(pg, '#pcSheet [data-pc=set][data-k=role][data-v=support]'); tap(pg, '#pcSheet [data-pc=set][data-k=bias][data-v=long]')
    tap(pg, '#pcSheet [data-pc=save-zone]')
    ok(x['zone'] in (pg.locator('#pcSheet .pc-err').inner_text() if pg.locator('#pcSheet .pc-err').count() else ''), f'2 {tag}: a zone upside down: refused')
    fit = pg.evaluate(FIT); ok(fit == '', f'6 {tag}: the zone form fits ({fit})')
    pg.fill('#pcSheet [data-pcf=high]', '21200'); pg.fill('#pcSheet [data-pcf=low]', '21180'); tap(pg, '#pcSheet [data-pc=save-zone]', 700)
    ch = pg.evaluate("(d) => (getDoc('journals', d) || {}).chart", day) or {}
    z1 = (ch.get('zones') or [{}, {}])[-1]
    ok(len(ch.get('zones', [])) == 2 and z1.get('type') == 'zone' and z1.get('high') == 21200 and z1.get('low') == 21180 and z1.get('bias') == 'long' and z1.get('role') == 'support', f'2 {tag}: the zone saved ({z1})')
    # 3. a rule
    tap(pg, '#pcSheet [data-pc=new-rule]')
    pg.select_option('#pcSheet select[data-pcf=trigger]', 'sweep'); pg.wait_for_timeout(300)
    pg.select_option('#pcSheet select[data-pcf=zone]', z0['id']); pg.wait_for_timeout(200)
    tap(pg, '#pcSheet [data-pc=set][data-k=tf][data-v="5m"]')
    pg.select_option('#pcSheet select[data-pcf=action]', 'plan'); pg.wait_for_timeout(300)
    pg.fill('#pcSheet [data-pcf=message]', 'Attendre le retour sous le PDH'); pg.wait_for_timeout(200)
    say = pg.locator('#pcSheet [data-pc-say]').inner_text()
    ok(say == x['say'], f'3 {tag}: the rule in words ({say!r})')
    fit = pg.evaluate(FIT); ok(fit == '', f'6 {tag}: the rule form fits ({fit})')
    ok(pg.locator('#pcSheet .btn.primary').count() == 1 and pg.locator('#pcSheet .btn.primary').is_visible(), f'6 {tag}: one blue button: Save')
    tap(pg, '#pcSheet [data-pc=save-rule]', 700)
    ch = pg.evaluate("(d) => (getDoc('journals', d) || {}).chart", day) or {}
    r0 = (ch.get('rules') or [{}])[0]
    ok(r0.get('trigger') == 'sweep' and r0.get('zone') == z0['id'] and r0.get('tf') == '5m' and r0.get('action') == 'plan', f'3 {tag}: the rule saved ({r0})')
    ok(x['say'] in pg.locator('#pcSheet .pc-list').nth(1).inner_text(), f'3 {tag}: the list says the rule in words')
    fit = pg.evaluate(FIT); ok(fit == '', f'6 {tag}: the list fits ({fit})')
    if w == 390 and lang == 'fr': pg.screenshot(path='/tmp/sweep-plan-chart-390.png')
    if w == 1300 and lang == 'en': pg.screenshot(path='/tmp/sweep-plan-chart-1300.png')
    # 4. edit, delete; the server
    tap(pg, '#pcSheet .pc-item[data-pc=zone] >> nth=0'); pg.fill('#pcSheet [data-pcf=price]', '21300'); tap(pg, '#pcSheet [data-pc=save-zone]', 700)
    ch = pg.evaluate("(d) => (getDoc('journals', d) || {}).chart", day) or {}
    ok(ch['zones'][0]['price'] == 21300 and ch['zones'][0]['id'] == z0['id'], f'4 {tag}: the level moved to 21300 (same zone)')
    pg.wait_for_timeout(1200)
    sv = server_day(pg, day) or {}
    ok((sv.get('chart') or {}).get('zones', [{}])[0].get('price') == 21300 and len((sv.get('chart') or {}).get('rules', [])) == 1, f'4 {tag}: on the server, the journal of {day} (the plan\'s New York day) carries the zones and the rule')
    tap(pg, f'#pcSheet .pc-item[data-pc=zone][data-id="{z1["id"]}"]'); tap(pg, '#pcSheet [data-pc=del]', 600)
    ch = pg.evaluate("(d) => (getDoc('journals', d) || {}).chart", day) or {}
    ok(len(ch.get('zones', [])) == 1 and len(ch.get('rules', [])) == 1, f'4 {tag}: the zone deleted, the level and its rule kept')
    tap(pg, '#pcSheet .pc-item[data-pc=zone] >> nth=0'); tap(pg, '#pcSheet [data-pc=del]', 600)
    ch = pg.evaluate("(d) => (getDoc('journals', d) || {}).chart", day) or {}
    ok(len(ch.get('zones', [])) == 0 and len(ch.get('rules', [])) == 0 and pg.locator('#pcSheet .pc-item').count() == 0, f'4 {tag}: the level deleted: its rule goes with it')
    pg.wait_for_timeout(1200)
    sv = server_day(pg, day) or {}
    ok('chart' not in sv, f'4 {tag}: on the server, nothing left of the chart plan')
    # 5. yesterday's zones (once)
    if w == 390 and lang == 'fr':
      prev = '2027-04-12'; days.append(prev)
      pg.evaluate("(d) => put('journals', { id: d, chart: { zones: [{ id: 'zy1', instrument: 'NQ', type: 'level', price: 21000, label: 'PDL', role: 'support', bias: null, note: '', proximity_ticks: 40 }], rules: [], updated_at: 1 } })", prev); pg.wait_for_timeout(600)
      pg.evaluate("() => SweepPlanChart.close(true)"); pg.wait_for_timeout(200); pg.evaluate("(d) => SweepPlanChart.open(d)", day); until(pg, "document.querySelector('#pcSheet.open')"); pg.wait_for_timeout(400)
      rs = pg.locator('#pcSheet [data-pc=resume]')
      ok(rs.is_visible() and 'hier' in rs.inner_text(), f'5 {tag}: « Reprendre les zones d’hier » ({rs.inner_text() if rs.count() else ""!r})')
      rs.click(); pg.wait_for_timeout(600)
      ch = pg.evaluate("(d) => (getDoc('journals', d) || {}).chart", day) or {}
      ok(len(ch.get('zones', [])) == 1 and ch['zones'][0]['label'] == 'PDL' and x['resumed'] in pg.locator('#pcSheet').inner_text(), f'5 {tag}: yesterday\'s zone copied, and it says so')
    # the row counts, back in the plan; Escape closes the chart sheet first
    pg.keyboard.press('Escape'); pg.wait_for_timeout(500)
    ok(pg.locator('#pcSheet').count() == 0 and pg.locator('#gSheet.g-pm').count() == 1, f'1 {tag}: Escape closes the chart sheet, the plan stays')
    pg.close(); c.close()
  # clean up the test days
  c = br.new_context(storage_state=STATE); pg = c.new_page(); pg.goto(B + '/#dashboard'); until(pg, 'window.S && S.journals'); pg.wait_for_timeout(800)
  pg.evaluate("(ds) => ds.forEach((d) => { if (getDoc('journals', d)) remove('journals', d); })", days); pg.wait_for_timeout(1200)
  c.close()
  ok(not errs, f'6 no page error ({errs[:3]})')
  br.close()
print('all passed' if not fails else f'{fails} failed'); sys.exit(1 if fails else 0)
