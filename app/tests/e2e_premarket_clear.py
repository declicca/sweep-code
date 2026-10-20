"""
Sweep — the pre-market, clear and light (20 Oct., test as a trader), phone 390 and computer 1300, the browser's clock at 08:00 New York:
  python3 tests/e2e_premarket_clear.py http://127.0.0.1:8095 /tmp/show_state.json
 1  every term says what it means: London high / low, PDH / PDL, the optional fields; the instrument is a row of chips with its name, « Autre » for any symbol
 2  what is missing is said by name and outlined (the instrument, the London levels, their order); a level far from the others (a digit missing) is asked once
 3  the last sheet's levels are a reference in grey, never kept by mistake; « 5 820,5 » is read as 5820.5; « Next » on the keyboard goes to the next field
 4  the scenarios: entry, stop and target can all be changed, the R follows in points; a stop on the wrong side says so; « Utiliser » brings the proposed target back
 5  a sheet closed without saving comes back as it was (same screen, same values); saved, the draft is gone
 6  the chart is on the levels' screen (no second instrument picker), the screenshots at the end; the session view's boxes name the level
 7  the express version: bias, key levels, the expected and the alternative scenario (no prices); every « i » explains with an example
 8  French and Spanish: no English sentence on any screen; English: no French
The test days are removed at the end.
"""
import datetime as dt, re, sys
from zoneinfo import ZoneInfo
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)
def until(pg, expr, ms=15000):
  for _ in range(ms // 150):
    if pg.evaluate(f'!!({expr})'): return True
    pg.wait_for_timeout(150)
  return False
NY = ZoneInfo('America/New_York')
SCREEN = "(document.querySelector('#gSheet.g-pm [data-pm-screen]') || {dataset: {}}).dataset.pmScreen || ''"
TAP = "(s) => { const b = document.querySelector(s); if (b) b.click(); return !!b }"
EN = re.compile(r"(?<![\w’'-])(the|your|you|with|without|this|these|those|have|been|were|will|would|should|could|which|what|why|already|never|always|none|missing|level|target|entry|scenario|sheet)(?![\w’'-])", re.I)
FR = re.compile(r"(?<![\w’'-])(le|la|les|ton|ta|tes|avec|sans|cible|entrée|scénario|fiche|niveau|séance)(?![\w’'-])", re.I)
def text(pg): return pg.evaluate("(document.querySelector('#gSheet') || {}).innerText || ''").replace('\xa0', ' ').replace(' ', ' ')
def err(pg): return pg.evaluate("(document.querySelector('#gSheet .pm-err') || {}).textContent || ''").replace('\xa0', ' ').replace(' ', ' ')
def scr(pg): return pg.evaluate(SCREEN)
def tap(pg, s): pg.evaluate(TAP, s); pg.wait_for_timeout(250)
def nxt(pg): tap(pg, '#gSheet [data-pm="next"]')
def bad(pg): return pg.evaluate("[...document.querySelectorAll('#gSheet [aria-invalid=true]')].map((x) => x.dataset.pmf)")
def open_plan(pg, day):
  pg.evaluate("(d) => SweepGame.openPlan(d)", day); until(pg, SCREEN); pg.wait_for_timeout(500)
PREV = """(d) => { const f = SweepFiche.blank(d); f.instrument = 'MES'; Object.assign(f.levels, { london_high: 5790, london_low: 5770, pdh: 5810, pdl: 5750, price: 5780 });
  f.scenarios = [{ id: 'A', direction: 'long', type: 'breakout', level: 5790, stop_estimate: 5784, target: 5810 }]; return SweepFiche.save(f) }"""

with sync_playwright() as p:
  br = p.chromium.launch(); errs = []
  for w, phone, prev, day, xday in [(390, True, '2027-07-12', '2027-07-13', '2027-07-14'), (1300, False, '2027-07-19', '2027-07-20', '2027-07-21')]:
    c = br.new_context(storage_state=STATE, viewport={'width': w, 'height': 844 if phone else 850}, is_mobile=phone, has_touch=phone, locale='fr-CA')
    c.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr')); localStorage.removeItem('pm.draft')")
    pg = c.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
    y, m, d = map(int, day.split('-'))
    pg.clock.install(time=dt.datetime(y, m, d, 8, 0, tzinfo=NY))
    pg.goto(B + '/#dashboard'); until(pg, 'window.SweepFiche && window.SweepGame && window.S && S.journals && S.settings'); pg.wait_for_timeout(1200)
    was = pg.evaluate("S.settings.pm_mode || null")
    if was: pg.evaluate("(() => { const s = structuredClone(S.settings); delete s.pm_mode; put('settings', s) })()"); pg.wait_for_timeout(400)
    pg.evaluate(PREV, prev); pg.wait_for_timeout(600)
    # 1. the words
    open_plan(pg, day); t = text(pg)
    ok(scr(pg) == 'base' and 'Séance de Londres · avant l’ouverture de New York' in t and 'Hier · facultatif' in t and 'Prix actuel · facultatif' in t and pg.locator('#gSheet .pm-tip:not([hidden])').count() == 0,
       f'1 {w}: the London levels, PDH / PDL and the optional fields, short; the explanations closed')
    tap(pg, '#gSheet [data-pm=tip][data-k=prev]')
    tip = pg.evaluate("[...document.querySelectorAll('#gSheet .pm-tip:not([hidden])')].map((x) => x.textContent)")
    ok(len(tip) == 1 and tip[0].startswith('PDH (previous day high) et PDL (previous day low) : le plus haut et le plus bas de la séance d’hier') and 'Ex. :' in tip[0] and pg.get_attribute('#gSheet [data-pm=tip][data-k=prev]', 'aria-expanded') == 'true',
       f'1 {w}: the « i » of PDH / PDL opens its explanation and an example ({tip[:1]})')
    tap(pg, '#gSheet [data-pm=tip][data-k=london]')
    tip = pg.evaluate("[...document.querySelectorAll('#gSheet .pm-tip:not([hidden])')].map((x) => x.dataset.tipk)")
    ok(tip == ['london'] and pg.locator('#gSheet [data-pm=tip]').count() >= 4, f'1 {w}: one explanation at a time; an « i » for the instrument, London, yesterday, the price ({tip})')
    tap(pg, '#gSheet [data-pm=tip][data-k=london]')
    chips = pg.evaluate("[...document.querySelectorAll('#gSheet [data-pm=inst-pick]')].map((x) => x.textContent)")
    ok(all(x in chips for x in ('MNQ', 'MES', 'NQ', 'ES', 'MGC', 'MCL')) and chips[-1] == 'Autre' and pg.locator('#gSheet [data-pm=inst-pick].on').count() == 1,
       f'1 {w}: the instrument: a row of chips (the trader\'s own first, then the usual futures), one chosen, « Autre » at the end ({chips[:5]}…)')
    tap(pg, '#gSheet [data-pm="inst-pick"][data-v="NQ"]')
    ok(pg.evaluate("(document.querySelector('#gSheet .pm-inst-n') || {}).textContent") == 'E-mini Nasdaq-100' and pg.evaluate("document.getElementById('gSheet').dataset.inst") == 'NQ', f'1 {w}: NQ chosen: its name under it, the sheet knows it (the chart follows)')
    tap(pg, '#gSheet [data-pm="inst-pick"][data-v=""]')
    ok(pg.locator('#gSheet [data-pmf=instrument]').count() == 1 and pg.evaluate("document.activeElement && document.activeElement.dataset.pmf") == 'instrument', f'1 {w}: « Autre »: a field for the symbol, the keyboard on it')
    pg.fill('#gSheet [data-pmf=instrument]', '6e'); pg.wait_for_timeout(100)
    ok(pg.evaluate("SweepFiche && document.querySelector('#gSheet [data-pmf=instrument]').value") == '6e', f'1 {w}: typed as the trader types it')
    tap(pg, '#gSheet [data-pm="inst-pick"][data-v="MES"]')
    # 3. yesterday's levels in grey
    ph = pg.evaluate("['london_high', 'london_low', 'pdh', 'pdl'].map((k) => { const i = document.querySelector(`#gSheet [data-pmf='lv.${k}']`); return [i.value, i.placeholder] })")
    ok(ph == [['', '5790'], ['', '5770'], ['', '5810'], ['', '5750']] and 'En gris : les niveaux de ta dernière fiche, pour repère.' in text(pg), f'3 {w}: the last sheet\'s levels in grey, the fields empty ({ph})')
    # 2. what is missing, by name
    nxt(pg)
    ok(err(pg) == 'Il manque : London high, London low.' and bad(pg) == ['lv.london_high', 'lv.london_low'] and pg.evaluate("document.activeElement && document.activeElement.dataset.pmf") == 'lv.london_high',
       f'2 {w}: « Il manque : London high, London low. », both outlined, the keyboard on the first ({err(pg)!r}, {bad(pg)})')
    # 3. « Next » on the keyboard
    pg.fill('#gSheet [data-pmf="lv.london_high"]', '5 820,5'); pg.press('#gSheet [data-pmf="lv.london_high"]', 'Enter'); pg.wait_for_timeout(100)
    ok(pg.evaluate("document.activeElement && document.activeElement.dataset.pmf") == 'lv.london_low' and not pg.evaluate("document.querySelector('#gSheet [data-pmf=\"lv.london_high\"]').hasAttribute('aria-invalid')"),
       f'3 {w}: « Next » goes to the London low; the field typed is no longer outlined')
    pg.fill('#gSheet [data-pmf="lv.london_low"]', '5830'); nxt(pg)
    ok(err(pg) == 'Le London high doit être au-dessus du London low.', f'2 {w}: high under low: said plainly ({err(pg)!r})')
    pg.fill('#gSheet [data-pmf="lv.london_low"]', '5800'); pg.fill('#gSheet [data-pmf="lv.pdh"]', '5850'); pg.fill('#gSheet [data-pmf="lv.pdl"]', '577'); pg.fill('#gSheet [data-pmf="lv.price"]', '5810'); nxt(pg)
    ok(scr(pg) == 'base' and err(pg) == 'Vérifie 577 : c’est loin de tes autres niveaux. Touche Continuer si c’est bien ça.' and bad(pg) == ['lv.pdl'], f'2 {w}: PDL 577 (a digit missing): asked once, outlined ({err(pg)!r})')
    pg.fill('#gSheet [data-pmf="lv.pdl"]', '5770'); nxt(pg)
    lv = pg.evaluate("(() => { const s = document.getElementById('gSheet'); return s && s.dataset.day })()")
    ok(scr(pg) == 'pos', f'2 {w}: corrected: on to the next screen')
    tap(pg, '#gSheet [data-q="A2"][data-v="high"]'); nxt(pg)
    # 4. the scenarios
    sa = pg.evaluate("[document.querySelector('#gSheet [data-pmf=C1_level]').value, document.querySelector('#gSheet [data-pmf=ST_A]').value, document.querySelector('#gSheet [data-pmf=C3_A]').value]")
    ok(scr(pg) == 'scen' and sa == ['5820.5', '5814.5', '5850'] and 'Entrée 5 820,5 · Stop 5 814,5 · Cible 5 850' in text(pg), f'3 {w}: « 5 820,5 » read as 5820.5: entry, stop (6 points), target PDH, on one line ({sa})')
    tap(pg, '#gSheet [data-pm=adj][data-s=A]')
    ok(pg.locator('#gSheet [data-sc=A] .pm-row3:not([hidden])').count() == 1 and pg.locator('#gSheet [data-sc=B] .pm-row3[hidden]').count() == 1, f'4 {w}: « Ajuster » opens the fields of that scenario only')
    pg.fill('#gSheet [data-pmf=ST_A]', '5817.5'); pg.wait_for_timeout(150)
    r = pg.locator('#gSheet [data-pm-r=A]').inner_text().replace('\xa0', ' ')
    ok(r.startswith('9,8R : tu vises 29,5 pts pour 3 pts de risque'), f'4 {w}: a closer stop: the R follows, in points ({r!r})')
    pg.fill('#gSheet [data-pmf=ST_A]', '5825'); pg.wait_for_timeout(150)
    r = pg.locator('#gSheet [data-pm-r=A]').inner_text()
    nxt(pg)
    ok(scr(pg) == 'scen' and r == 'Pour un long : le stop sous l’entrée, la cible au-dessus.' and err(pg) == r, f'4 {w}: a stop above a long\'s entry: said so, the screen stays ({r!r})')
    pg.fill('#gSheet [data-pmf=ST_A]', ''); pg.dispatch_event('#gSheet [data-pmf=ST_A]', 'change'); pg.wait_for_timeout(150)
    ok(pg.input_value('#gSheet [data-pmf=ST_A]') == '5814.5', f'4 {w}: the stop emptied: the proposed one comes back')
    pg.fill('#gSheet [data-pmf=C3_A]', '5840'); pg.wait_for_timeout(150)
    tg = pg.locator('#gSheet [data-pm-tg=A]').inner_text().replace('\xa0', ' ')
    ok('Proposée : 5 850 (PDH) · Utiliser' in tg, f'4 {w}: another target: the proposed one and « Utiliser » ({tg!r})')
    tap(pg, '#gSheet [data-pm=use-tgt][data-s=A]')
    ok(pg.input_value('#gSheet [data-pmf=C3_A]') == '5850' and 'Cible proposée : PDH, le prochain niveau.' in pg.locator('#gSheet [data-pm-tg=A]').inner_text(), f'4 {w}: « Utiliser »: back to the PDH')
    # 5. closed without saving (a swipe, a call): back as it was
    pg.fill('#gSheet [data-pmf=ST_A]', '5816.5'); pg.wait_for_timeout(100)
    pg.evaluate("document.getElementById('gScrim').click()"); pg.wait_for_timeout(600)
    open_plan(pg, day)
    ok(scr(pg) == 'scen' and pg.input_value('#gSheet [data-pmf=ST_A]') == '5816.5' and pg.input_value('#gSheet [data-pmf=C1_level]') == '5820.5', f'5 {w}: reopened: the same screen, the same values')
    nxt(pg)
    ok(scr(pg) == 'limits' and pg.locator('#gSheet [data-pm=nt]').count() == 4, f'5 {w}: the limits with what stops the day')
    if not pg.input_value('#gSheet [data-pmf="max_loss"]'): pg.fill('#gSheet [data-pmf="max_loss"]', '500')
    nxt(pg)
    # 6. the chart on the levels' screen, the screenshots at the end
    ok(scr(pg) == 'sheet' and pg.locator('#gSheet .nav-pre-shots, #gSheet .nav-pre-add').count() >= 1 and pg.locator('#gSheet [data-pre-chart]').count() == 0, f'6 {w}: the sheet: the screenshots, not the chart')
    tap(pg, '#gSheet [data-pm="save"]'); pg.wait_for_timeout(900)
    f = pg.evaluate("(d) => SweepFiche.get(d)", day)
    ok(f and f['scenarios'][0]['stop_estimate'] == 5816.5 and f['scenarios'][0]['level'] == 5820.5 and f['levels']['london_high'] == 5820.5 and pg.evaluate("localStorage.getItem('pm.draft')") is None,
       f'5 {w}: saved with the trader\'s stop and entry; the draft is gone')
    # 6. the session view names the level
    pg.evaluate("(d) => { const f = SweepFiche.get(d); f.locked_at = Math.floor(Date.now() / 1000); SweepFiche.save(f) }", day); pg.wait_for_timeout(300)
    pg.evaluate("(d) => SweepGame.openPlan(d)", day); until(pg, "document.querySelector('#gSheet.g-pm-locked')"); pg.wait_for_timeout(300)
    boxes = pg.evaluate("[...document.querySelectorAll('#gSheet [data-sc=A] .pm-chk')].map((b) => b.textContent.replace(/\\u00a0|\\u202f/g, ' ').slice(1))")
    ok(boxes[:2] == ['Bougie 15 min clôturée au-dessus de 5 820,5', 'Retest de 5 820,5 en 5 min'] and 'stop 5 816,5' in boxes[-1], f'6 {w}: the checklist names the level and the stop ({boxes})')
    tap(pg, '#gSheet [data-g=close]')
    # 6, 7. the express version
    open_plan(pg, xday); tap(pg, '#gSheet [data-pm="inst-pick"][data-v="MES"]')
    ok(pg.locator('#gSheet .pm-chart-slot .nav-pre [data-pre-chart]').count() == 1, f'6 {w}: the levels\' screen offers the chart')
    tap(pg, '#gSheet .pm-chart-slot [data-pre-chart]'); pg.wait_for_timeout(300)
    ok(pg.locator('#gSheet .pm-chart-slot iframe.nav-tv').count() == 1 and pg.locator('#gSheet .pm-chart-slot [data-pre-inst]').count() == 0 and 'MES1' in (pg.get_attribute('#gSheet .pm-chart-slot iframe', 'src') or ''),
       f'6 {w}: the chart opens on the sheet\'s instrument, without a second instrument picker')
    tap(pg, '#gSheet .pm-chart-slot [data-pre-chart]')
    tap(pg, '#gSheet [data-pm="mode"][data-v="express"]')
    t = text(pg); bias = pg.evaluate("[...document.querySelectorAll('#gSheet [data-q=X_bias]')].map((x) => x.textContent)")
    ok(bias == ['Haussier', 'Baissier', 'Neutre'] and 'Niveaux clés' in t and 'Scénario attendu' in t and 'Scénario alternatif · facultatif' in t and pg.locator('#gSheet [data-pmf=X_stop], #gSheet [data-pmf=C3_A]').count() == 0,
       f'7 {w}: the express plan: bias, key levels, expected and alternative scenario, no prices to set ({bias})')
    tap(pg, '#gSheet [data-pm=tip][data-k=plan]')
    tip = pg.evaluate("(document.querySelector('#gSheet .pm-tip:not([hidden])') || {}).textContent || ''")
    ok(tip.startswith('Ce que tu feras si le marché va dans le sens de ton biais') and 'Ex. :' in tip, f'7 {w}: its « i » gives an example ({tip[:60]!r})')
    ph = pg.get_attribute('#gSheet [data-pmf=X_plan]', 'placeholder')
    ok(ph.startswith('ex. Cassure du London high'), f'7 {w}: an example in the field too ({ph!r})')
    tap(pg, '#gSheet [data-pm="mode"][data-v="full"]'); tap(pg, '#gSheet [data-g=close]')
    # 8. the languages
    for lang, rx, name in [('es', EN, 'Spanish: no English'), ('en', FR, 'English: no French')]:
      pg.evaluate(f"localStorage.setItem('tj.lang', JSON.stringify('{lang}')); localStorage.removeItem('pm.draft')"); pg.add_init_script(f"localStorage.setItem('tj.lang', JSON.stringify('{lang}'))")
      pg.reload(); until(pg, 'window.SweepGame && window.S && S.journals && S.settings'); pg.wait_for_timeout(1000)
      open_plan(pg, xday); seen = []
      for k, v in [('lv.london_high', '5820'), ('lv.london_low', '5800'), ('lv.pdh', '5826'), ('lv.pdl', '5770'), ('lv.price', '5823')]: pg.fill(f'#gSheet [data-pmf="{k}"]', v)
      for _ in range(6):
        s = scr(pg); seen.append((s, text(pg))); seen.append((s + ' (i)', pg.evaluate("[...document.querySelectorAll('#gSheet .pm-tip')].map((x) => x.textContent).join('\\n')")))   # (the explanations too)
        if s == 'pos': tap(pg, '#gSheet [data-q="A3"][data-v="yes"]'); tap(pg, '#gSheet [data-q="A4"][data-v="obstacle"]'); tap(pg, '#gSheet [data-q="B1"][data-v="yes"]'); seen.append((s, text(pg)))
        if s == 'scen': tap(pg, '#gSheet [data-pm=adj][data-s=A]'); pg.fill('#gSheet [data-pmf=C3_A]', '5850'); pg.wait_for_timeout(150); seen.append((s, text(pg)))
        if s == 'limits' and not pg.input_value('#gSheet [data-pmf="max_loss"]'): pg.fill('#gSheet [data-pmf="max_loss"]', '500')
        if s == 'sheet': break
        if s == 'pos': pg.fill('#gSheet [data-pmf="B1_time"]', '08:30'); pg.dispatch_event('#gSheet [data-pmf="B1_time"]', 'change'); pg.wait_for_timeout(200); seen.append((s, text(pg)))
        nxt(pg)
      hits = sorted({f'{s}: {m.group(0)}' for s, tx in seen for m in rx.finditer(tx)})
      ok(any(x == 'sheet' for x, _ in seen) and not hits, f'8 {w}: {name} on {len({s for s, _ in seen})} screens {hits[:6]}')
      tap(pg, '#gSheet [data-g=close]')
    pg.evaluate("localStorage.setItem('tj.lang', JSON.stringify('fr')); localStorage.removeItem('pm.draft')")
    for x in (prev, day, xday): pg.evaluate("(d) => { if (S.journals.some((j) => j.id === d)) remove('journals', d) }", x)
    pg.evaluate("(v) => { const s = structuredClone(S.settings); if (v) s.pm_mode = v; else delete s.pm_mode; put('settings', s) }", was)
    pg.wait_for_timeout(1500)
    c.close()
  ok(not errs, f'no page error ({errs[:2]})')
  br.close()
print('all passed' if not fails else f'{fails} failed')
sys.exit(1 if fails else 0)
