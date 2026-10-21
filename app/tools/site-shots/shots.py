"""
Sweep — the site's captures (brief of 20 Oct. 2026, briefs/brief-captures-site-2026-10-20.md), from the current app, dark
theme, sample trader « Alex » (seed.py), each in its languages, at the exact size of the file it replaces.
  sh tools/site-shots/serve.sh python3 tools/site-shots/shots.py <out_dir> [name …]
Writes <out_dir>/captures/{en,fr}/<name>.webp and <out_dir>/img/<name>.webp (the names and sizes of website/static/img),
plus a PNG next to each for checking. Nothing is written to the site.
"""
import datetime as dt, json, os, subprocess, sys
from zoneinfo import ZoneInfo
from playwright.sync_api import sync_playwright
HERE = os.path.dirname(os.path.abspath(__file__))
B = 'http://127.0.0.1:%s' % os.environ.get('PORT', '8996')
ARGS = [a for a in sys.argv[1:] if not a.startswith('--')]; KEEP = '--keep' in sys.argv; SEEDONLY = '--seed' in sys.argv
OUT = ARGS[0] if ARGS else '/tmp/shots-out'; ONLY = set(ARGS[1:])
GAME_FROM = os.environ.get('SHOTS_GAME_FROM', '2026-09-08')   # his first day in the game: a streak of about 27 days
DEST = os.environ.get('DEST', '/tmp/gs')
STATE = DEST + '-state'   # -<lang>.json
NY = ZoneInfo('America/New_York')
NOW = dt.datetime.strptime(os.environ.get('SHOTS_NOW', '2026-10-15 11:05'), '%Y-%m-%d %H:%M').replace(tzinfo=NY)
LOC = {'en': 'en-US', 'fr': 'fr-CA', 'es': 'es-ES'}
# sizes: (viewport w, h, scale, file w, file h, phone)
SIZE = {'m': (390, 844, 900 / 390, 900, 1948, True), 'd': (1200, 750, 2, 2400, 1500, False),
        'm786': (393, 852, 2, 786, 1704, True), 'd2400': (1200, 750, 2, 2400, 1500, False)}
QUALITY = {'m': 82, 'd': 82, 'm786': 82, 'd2400': 82}

def go(pg, route, wait=2500):
  pg.evaluate("(r) => { location.hash = r; }", route); pg.wait_for_timeout(wait)

def top(pg):
  pg.evaluate("scrollTo(0, 0)"); pg.wait_for_timeout(300)

def scroll_to(pg, sel, off=0):
  pg.evaluate("([s, o]) => { const e = document.querySelector(s); if (e) { const y = e.getBoundingClientRect().top + scrollY - o; scrollTo(0, Math.max(0, y)); } }", [sel, off]); pg.wait_for_timeout(500)

def tap(pg, sel, wait=900):
  pg.locator(sel).first.click(); pg.wait_for_timeout(wait)

def g(pg, action, v=None, wait=1800):
  """a game sheet, through the game's own click handler (a button with its data-g, as in the app)"""
  pg.evaluate("([a, v]) => { const b = document.createElement('button'); b.dataset.g = a; if (v) b.dataset.v = v; b.hidden = true; document.body.appendChild(b); b.click(); b.remove(); }", [action, v]); pg.wait_for_timeout(wait)

def put(pg, col, doc, wait=1500):
  pg.evaluate("([c, d]) => put(c, Object.assign({}, (S[c] || []).find((x) => x.id === d.id) || {}, d))", [col, doc]); pg.wait_for_timeout(wait)

# ───────────── the captures: name → (size, langs, folder, steps(pg, lang)) ─────────────
def today(pg, lang):
  go(pg, '#dashboard', 3000); top(pg)

def today_d(pg, lang):   # the routine folded: the day's trade, copied on the accounts, in view
  go(pg, '#dashboard', 3000); top(pg); tap(pg, '#main [data-rt="toggle"]', 1500); top(pg)

def swept(pg, lang):
  W = {'en': ('Waited for the London sweep, two clean entries.', 'Patience pays: same plan tomorrow.'), 'fr': ('J’ai attendu le sweep de Londres, deux entrées propres.', 'La patience paie : même plan demain.'), 'es': ('Esperé el sweep de Londres, dos entradas limpias.', 'La paciencia paga: mismo plan mañana.')}[lang]
  put(pg, 'journals', {'id': '2026-10-15', 'date': '2026-10-15', 'post': {'well': W[0], 'lesson': W[1], 'grade': 'A', 'followed': 'yes', 'reviewed_at': 1792076400}}, 2500)
  pg.evaluate("SweepGame.refresh()"); pg.wait_for_timeout(2500)
  go(pg, '#dashboard', 2500)
  for i in range(6):   # the « Day swept » moment (it can come a little later), then Today with its 3 steps done
    if pg.evaluate("!!document.querySelector('[data-g=sw-close]')"): g(pg, 'sw-close', None, 1200)
    pg.wait_for_timeout(700)
  top(pg)

def account_payout(pg, lang):
  go(pg, '#account/a4', 3000); scroll_to(pg, '#main section:has(> h2), #main .surface', 0)
  pg.evaluate("""() => { const h = [...document.querySelectorAll('#main h2, #main h3')].find((e) => /^(Payout|Pago|Retiro)$/i.test(e.textContent.trim()));
    if (h) scrollTo(0, h.getBoundingClientRect().top + scrollY - (innerWidth < 700 ? 130 : 30)); }"""); pg.wait_for_timeout(600)

def page(route, sel=None, off=0):
  def f(pg, lang):
    go(pg, route, 3000); top(pg)
    if sel: scroll_to(pg, sel, off)
  return f

def money(pg, lang):
  go(pg, '#payouts', 3000); top(pg)

def click_text(pg, rx, scope='body', wait=1500, last=False):
  """the first (or last: a sheet opened on top) visible button / link whose text matches rx (a JS regex), in scope"""
  ok = pg.evaluate("""([rx, sc, last]) => { const r = new RegExp(rx); const l = [...document.querySelectorAll(sc + ' button, ' + sc + ' a, ' + sc + ' [role=tab], ' + sc + ' summary')]
    .filter((x) => x.getClientRects().length && r.test(x.textContent.replace(/\\s+/g, ' ').trim())); const e = last ? l[l.length - 1] : l[0]; if (e) e.click(); return !!e; }""", [rx, scope, last]); pg.wait_for_timeout(wait)
  return ok

def scroll_text(pg, rx, sel='#main h2, #main h3, #main summary', off=90, box=None):
  """scroll the page (or the sheet box) so the first heading matching rx is near the top"""
  pg.evaluate("""([rx, sel, off, box]) => { const r = new RegExp(rx); const e = [...document.querySelectorAll(sel)].find((x) => x.getClientRects().length && r.test(x.textContent.trim())); if (!e) return;
    const sc = box ? [...document.querySelectorAll(box + ' *')].find((x) => x.scrollHeight > x.clientHeight + 40 && /auto|scroll/.test(getComputedStyle(x).overflowY)) : null;
    if (sc) sc.scrollTop += e.getBoundingClientRect().top - sc.getBoundingClientRect().top - off; else scrollTo(0, e.getBoundingClientRect().top + scrollY - off); }""", [rx, sel, off, box]); pg.wait_for_timeout(700)

def phone(pg): return pg.viewport_size['width'] < 700

def reading(kind):
  """Sweep AI's reading of the next screenshot (the stand-in answer of serve.sh)"""
  r = json.load(open('/tmp/shots-img/readings.json'))[kind]
  json.dump({'default': r}, open(os.path.join(HERE, 'shot-ai.json'), 'w'))

def new_trade(pg, lang):
  go(pg, '#dashboard', 2000); pg.evaluate("() => [...document.querySelectorAll('[data-act=add-trade]')].find((e) => e.getClientRects().length).click()"); pg.wait_for_timeout(1800)

def new_trade_filled(pg, lang, img='trades'):
  reading(img); new_trade(pg, lang)
  pg.locator('.nav-am input[type=file]').first.set_input_files('/tmp/shots-img/%s.png' % img); pg.wait_for_timeout(5000)

def by_screenshot(pg, lang): new_trade_filled(pg, lang, 'chart')

def by_hand(pg, lang):
  new_trade(pg, lang); click_text(pg, r'^(Enter by hand|Saisir à la main|Entrer à la main|Ingresar a mano|A mano|Saisie manuelle)', wait=2200)

TODAY_TRADE = 't-2026-10-15-0-a2'   # 9:41, copied on the 5 accounts
YDAY_TRADE = 't-2026-10-14-0-a2'

def trade_chart(pg, lang):
  go(pg, '#trade/' + TODAY_TRADE, 3000)
  click_text(pg, r'^1m$', '#main', 2500)
  pg.evaluate("() => { const b = [...document.querySelectorAll('#main button')].find((e) => e.textContent.trim() === '1m'); const box = b && (b.closest('.tr-chart') || b.parentElement); if (box) scrollTo(0, box.getBoundingClientRect().top + scrollY - (innerWidth < 700 ? 80 : 24)); }"); pg.wait_for_timeout(1200)

TMP = 'shots-tmp-trade'
def tmp_trade(pg):
  """a trade of this morning not reviewed yet (removed after the capture)"""
  pg.evaluate("""(id) => { const t = JSON.parse(JSON.stringify(S.trades.find((x) => x.id === 't-2026-10-15-1-a2'))); t.id = id; delete t.copy_group;
    t.discipline = {}; t.emo = {}; t.review = {}; t.notes = ''; t.grade = ''; t.entry_time = '10:48'; t.exit_time = '10:57'; t.entry = t.entry + 9; t.exit = t.exit + 9; t.stop = t.stop + 9; t.target = t.target + 9;
    t.pnl_c = calcPnl(t.direction, t.entry, t.exit, t.contracts, t.instrument); put('trades', t); }""", TMP); pg.wait_for_timeout(1500)
def tmp_clean(pg):
  pg.evaluate("(id) => remove('trades', id)", TMP); pg.wait_for_timeout(1200)

def trade_review(pg, lang):   # the trade's page, « Answer your coach »
  go(pg, '#dashboard', 1500); tmp_trade(pg); go(pg, '#trade/' + TMP, 3000); top(pg)
  scroll_text(pg, r'^(Answer your coach|Réponds au coach|Responde a tu coach)', '#main b, #main h2, #main h3', 150 if phone(pg) else 40)

def checklist(pg, lang):      # the full review in 4 steps
  go(pg, '#trade/' + YDAY_TRADE, 3000)
  pg.evaluate("() => { const d = document.querySelector('#main details.co-full'); if (d) d.open = true; }"); pg.wait_for_timeout(800)
  scroll_text(pg, r'.', '#main details.co-full > summary', 110 if phone(pg) else 40)

def psychology(pg, lang):   # the end of the checklist and the psychology step
  go(pg, '#trade/' + YDAY_TRADE, 3000)
  pg.evaluate("() => { const d = document.querySelector('#main details.co-full'); if (d) d.open = true; }"); pg.wait_for_timeout(800)
  scroll_text(pg, r'^(Psychology|Psychologie|Psicología)', '#main details.co-full h3, #main details.co-full h2, #main details.co-full b, #main details.co-full span', 470)

def discipline_d(pg, lang):   # computer: the discipline analyses of Stats (process vs outcome, rules followed vs broken)
  go(pg, '#analytics', 3000); top(pg)
  pg.evaluate("""() => { const h = [...document.querySelectorAll('#main h2, #main h3')].find((e) => /^(Process vs|Processus vs|Proceso vs)/.test(e.textContent.trim()));
    if (h) scrollTo(0, h.getBoundingClientRect().top + scrollY - 70); }"""); pg.wait_for_timeout(700)

def share_payout(pg, lang):
  go(pg, '#payouts', 3000)
  click_text(pg, r'^(Share|Partager|Compartir)$', '#main .surface', 2200)
  click_text(pg, r'^(Payout|Pago)$', '.nav-sh, [role=dialog], body', 1800)

def signup(pg, lang):
  click_text(pg, r'^(Create account|Créer un compte|Crear cuenta)$', 'body', 1200)

def plan_sheet(pg, lang):   # the express plan, being filled: his bias, his levels, his two scenarios
  P = {'en': ('PDH 24,412 · London high 24,380 · London low 24,318', 'Sweep of the London low that holds: long toward the London high.', 'Back under 24,318: short toward the PDL. Otherwise, no trade.'),
       'fr': ('PDH 24 412 · London high 24 380 · London low 24 318', 'Sweep du London low qui tient : achat vers le London high.', 'Retour sous 24 318 : vente vers le PDL. Sinon, pas de trade.'),
       'es': ('PDH 24.412 · London high 24.380 · London low 24.318', 'Sweep del London low que aguanta: compra hacia el London high.', 'Vuelta bajo 24.318: venta hacia el PDL. Si no, sin operación.')}[lang]
  go(pg, '#dashboard', 1500); tap(pg, '#main [data-rt="plan"]', 2500)
  click_text(pg, r'^(Bullish|Haussier|Alcista)$', '#gSheet', 800)
  ta = pg.locator('#gSheet input[type=text]:visible, #gSheet textarea:visible')
  for i, v in enumerate(P):
    if i < ta.count(): ta.nth(i).fill(v)
  pg.wait_for_timeout(800)
  pg.evaluate("() => { const e = document.activeElement; if (e) e.blur(); }"); pg.wait_for_timeout(500)

def boss(pg, lang):
  row = pg.evaluate("fetch('api/game/boss?lang=%s', { headers: { 'X-Requested-With': 'fetch' } }).then((r) => r.json()).then((d) => (d.active && d.active[0] && d.active[0].row) || null)" % lang)
  pg.evaluate("SweepGame.refresh()"); pg.wait_for_timeout(1500); g(pg, 'boss', str(row), 2200)

def badges(pg, lang):   # the collection's badge grid (its section title is not shown in the sheet)
  g(pg, 'hub', None, 3500)
  pg.evaluate("() => { const sc = document.querySelector('#gSheet .evp-in'), gr = sc && sc.querySelector('.g-badges'); if (gr) sc.scrollTop += gr.getBoundingClientRect().top - sc.getBoundingClientRect().top - 16; }"); pg.wait_for_timeout(900)

def wrapped(n):
  def f(pg, lang):
    g(pg, 'wrapped', None, 2500)
    for i in range(n - 1): pg.mouse.click(300, 420); pg.wait_for_timeout(1600)
  return f

def connections(pg, lang):
  import sqlite3, time   # « add-on seen 2 min ago » (the server counts from the real clock)
  db = sqlite3.connect(os.path.join(DEST, 'data', 'journal.db'), timeout=60); db.execute('UPDATE sync_connections SET last_seen_at = ?, last_push_at = ?', (int(time.time()) - 130, int(time.time()) - 130)); db.commit(); db.close()
  go(pg, '#settings', 2500)
  pg.evaluate("() => { const d = document.querySelector('#main details.nav-sgd[data-i=\\'3\\']'); if (d) d.open = true; }"); pg.wait_for_timeout(1200)
  scroll_text(pg, r'^(Connections|Connexions|Conexiones)$', '#main h2, #main h3, #main h4, #main b', 90 if phone(pg) else 30)

SYNC_LINK = """(act) => fetch('api/sync', { headers: { 'X-Requested-With': 'fetch' } }).then((r) => r.json()).then((st) => Promise.all((st.accounts || []).map((a) => {
  const to = { 'PA-APEX-224455-03': 'a4', 'XFA-50K-771204': 'a2' }[a.name || (a.info && a.info.name) || a.ext_id]; if (!to) return null;
  return fetch('api/sync/accounts/' + a.id, { method: 'POST', headers: { 'X-Requested-With': 'fetch', 'Content-Type': 'application/json' }, body: JSON.stringify(act === 'link' ? { action: 'link', account_id: to } : { action: 'unlink' }) }); })))"""
def connections_link(pg, lang):   # computer: « Link my accounts » open, the 3 accounts found at once (linked again afterwards)
  pg.evaluate(SYNC_LINK, 'unlink'); pg.wait_for_timeout(800)
  connections(pg, lang); tap(pg, '#main .sy-sec [data-sy="linkall"]', 2200)
def relink(pg): pg.evaluate(SYNC_LINK, 'link'); pg.wait_for_timeout(800)

def ask_sweep(pg, lang):
  Q = {'en': 'What is my best setup this month?', 'fr': 'Quel est mon meilleur setup ce mois-ci ?', 'es': '¿Cuál es mi mejor setup este mes?'}[lang]
  go(pg, '#dashboard', 1500)
  pg.evaluate("() => document.querySelector('.ask-fab').click()"); pg.wait_for_timeout(1800)
  inp = pg.locator('.ask-bar textarea').first
  inp.fill(Q); inp.press('Enter'); pg.wait_for_timeout(4000)

def news_report(pg, lang):   # the recap of Thursday's retail sales, from the economic calendar
  rid = json.load(open(DEST + '-econ.json'))['retail']
  go(pg, '#news', 2500)
  pg.evaluate("(id) => { const e = document.querySelector('#main [data-act=ev-open][data-id=\"' + id + '\"]'); if (e) e.click(); }", rid); pg.wait_for_timeout(3000)

def edge_reveal(pg, lang):   # the week's recap, its Edge Reveal card turned over
  g(pg, 'weekly', None, 2500)
  for i in range(3):
    if pg.locator('#gSheet [data-g=wk-flip]').count(): break
    g(pg, 'wk-next', None, 1500)
  pg.evaluate("() => { const b = document.querySelector('#gSheet [data-g=wk-flip]'); if (b) b.click(); }"); pg.wait_for_timeout(2500)

def econ_week(pg, lang):
  go(pg, '#news', 2500); click_text(pg, r'^(This week|Cette semaine|Esta semana)$', '#main', 2000)

SHOTS = {
  # phone, captures/{en,fr} (900 × 1948)
  'v6-01-today-m': ('m', ('en', 'fr'), 'captures', today),
  'v6-03-log-by-screenshot-m': ('m', ('en', 'fr'), 'captures', by_screenshot),
  'v6-04-discipline-psychology-m': ('m', ('en', 'fr'), 'captures', psychology),
  'v6-05-log-by-hand-m': ('m', ('en', 'fr'), 'captures', by_hand),
  'v6-06-trade-review-m': ('m', ('en', 'fr'), 'captures', trade_review),
  'v6-07-stats-m': ('m', ('en', 'fr'), 'captures', page('#analytics')),
  'v6-08-payout-conditions-m': ('m', ('en', 'fr'), 'captures', account_payout),
  'v6-10-journal-m': ('m', ('en', 'fr'), 'captures', page('#journal/2026-10-14')),
  'v6-11-calendar-m': ('m', ('en', 'fr'), 'captures', page('#calendar')),
  'v6-12-payouts-m': ('m', ('en', 'fr'), 'captures', money),
  'v6-13-accounts-m': ('m', ('en', 'fr'), 'captures', page('#accounts')),
  'v6-17b-share-one-payout-m': ('m', ('en', 'fr'), 'captures', share_payout),
  'v6-18-add-trade-choice-m': ('m', ('en', 'fr'), 'captures', new_trade),
  'v6-20-signup-m': ('m', ('en', 'fr'), 'captures', signup),
  'v6-23-discipline-checklist-m': ('m', ('en', 'fr'), 'captures', checklist),
  'v6-24-new-trade-filled-m': ('m', ('en', 'fr'), 'captures', new_trade_filled),
  'v6-25-new-trade-empty-m': ('m', ('en', 'fr'), 'captures', new_trade),
  'ecran-parcours': ('m', ('en', 'fr'), 'captures', lambda pg, l: g(pg, 'map', None, 2200)),
  'ecran-boss-revenge': ('m', ('en', 'fr'), 'captures', boss),
  'ecran-saison': ('m', ('en', 'fr'), 'captures', lambda pg, l: g(pg, 'season', None, 2200)),
  'ecran-badges': ('m', ('en', 'fr'), 'captures', badges),
  'ecran-ligue': ('m', ('en', 'fr'), 'captures', lambda pg, l: g(pg, 'league', None, 2500)),
  'ecran-crew': ('m', ('en', 'fr'), 'captures', lambda pg, l: g(pg, 'social', None, 2500)),
  'ecran-plan-du-jour': ('m', ('en', 'fr'), 'captures', plan_sheet),
  'ecran-wrapped-1': ('m', ('en', 'fr'), 'captures', wrapped(1)),
  'ecran-wrapped-2': ('m', ('en', 'fr'), 'captures', wrapped(2)),
  'ecran-wrapped-3': ('m', ('en', 'fr'), 'captures', wrapped(3)),
  'ecran-connexions': ('m', ('en', 'fr'), 'captures', connections),
  # computer, captures/{en,fr} (2400 × 1500)
  'v6-01-today-d': ('d', ('en', 'fr'), 'captures', today_d),
  'v6-04-discipline-psychology-d': ('d', ('en', 'fr'), 'captures', discipline_d),
  'v6-05-log-by-hand-d': ('d', ('en', 'fr'), 'captures', by_hand),
  'v6-06-trade-review-d': ('d', ('en', 'fr'), 'captures', trade_chart),
  'v6-07-stats-d': ('d', ('en', 'fr'), 'captures', page('#analytics')),
  'v6-08-payout-conditions-d': ('d', ('en', 'fr'), 'captures', account_payout),
  'v6-11-calendar-d': ('d', ('en', 'fr'), 'captures', page('#calendar')),
  'v6-12-payouts-d': ('d', ('en', 'fr'), 'captures', money),
  'v6-13-accounts-d': ('d', ('en', 'fr'), 'captures', page('#accounts')),
  'v6-17b-share-one-payout-d': ('d', ('en', 'fr'), 'captures', share_payout),
  'v6-18-add-trade-choice-d': ('d', ('en', 'fr'), 'captures', new_trade),
  'v6-24-new-trade-filled-d': ('d', ('en', 'fr'), 'captures', new_trade_filled),
  'v6-25-new-trade-empty-d': ('d', ('en', 'fr'), 'captures', new_trade),
  'v6-26-connections-d': ('d', ('en', 'fr'), 'captures', connections_link),
  # img/ (en, fr, es)
  'ecran-revue-semaine': ('m', ('en', 'fr'), 'captures', lambda pg, l: g(pg, 'weekly', None, 2500)),
  'ecran-edge-reveal': ('m', ('en', 'fr'), 'captures', edge_reveal),
  'mobile-{lang}-dark-ask-sweep-786': ('m786', ('en', 'fr', 'es'), 'img', ask_sweep),
  'mobile-{lang}-dark-calendar-786': ('m786', ('en', 'fr', 'es'), 'img', page('#calendar')),
  'mobile-{lang}-dark-economic-calendar-786': ('m786', ('en', 'fr', 'es'), 'img', econ_week),
  'mobile-{lang}-dark-news-impact-report-786': ('m786', ('en', 'fr', 'es'), 'img', news_report),
  'desktop-{lang}-dark-news-impact-report-2400': ('d2400', ('en', 'fr', 'es'), 'img', news_report),
  'desktop-{lang}-dark-calendar-2400': ('d2400', ('en', 'fr', 'es'), 'img', page('#calendar')),
  'desktop-{lang}-dark-economic-calendar-2400': ('d2400', ('en', 'fr', 'es'), 'img', econ_week),
  # last: they write today's review
  'v6-22-today-swept-m': ('m', ('en', 'fr'), 'captures', swept),
  'v6-22-today-swept-d': ('d', ('en', 'fr'), 'captures', swept),
}
SIGNED_OUT = {'v6-20-signup-m'}
# Friday after the close (SHOTS_NOW="2026-10-16 17:30", a second server: serve.sh with DEST=/tmp/gs2 PORT=8997): the week's recap
FRIDAY = {'ecran-revue-semaine', 'ecran-edge-reveal'}
EVENING = NOW.weekday() == 4 and NOW.hour >= 17
CLEAN = {'v6-06-trade-review-m': tmp_clean, 'v6-26-connections-d': relink}

# ───────────── the share cards: the app's own « Save image » (or the game's card), at the site's sizes ─────────────
SAVE = r'^(Save image|Enregistrer l.image|Guardar (la )?imagen)$'
def stats_card(kind, fmt):   # « net » (Mon argent's net after fees) and « week » (the week's recap), as the app opens them
  def f(pg, lang):
    go(pg, '#analytics', 2500)
    pg.evaluate("(k) => openShare(k, k === 'net' ? 'all' : todayStr())", kind); pg.wait_for_timeout(2000)
    second_tab(pg)
    tap(pg, '[data-sh-fmt="%s"]' % fmt, 1500)
    return lambda: click_text(pg, SAVE, 'body', 300, last=True)
  return f
def second_tab(pg):
  """the share window opens on the Discipline card (since 14 Oct.): its second tab is the card asked for"""
  pg.evaluate("() => { const sg = [...document.querySelectorAll('#shPanel .seg, #shPanel [role=tablist]')].find((e) => e.getClientRects().length); const b = sg && sg.querySelectorAll('button')[1]; if (b) b.click(); }"); pg.wait_for_timeout(1500)

def payout_card(pg, lang):
  share_payout(pg, lang); tap(pg, '[data-sh-fmt="post"]', 1500)
  return lambda: click_text(pg, SAVE, 'body', 300, last=True)
def trade_card(pg, lang):
  go(pg, '#trade/' + TODAY_TRADE, 2500); pg.evaluate("() => document.querySelector('#main [data-act=share]').click()"); pg.wait_for_timeout(1800); second_tab(pg); tap(pg, '[data-sh-fmt="wide"]', 1500)
  return lambda: click_text(pg, SAVE, 'body', 300, last=True)
def game_card(kind, v=None, before=None):
  def f(pg, lang):
    if before: g(pg, before, None, 2500)
    return lambda: pg.evaluate("([k, v]) => { const b = document.createElement('button'); b.dataset.g = 'share'; b.dataset.k = k; if (v) b.dataset.v = v; b.hidden = true; document.body.appendChild(b); b.click(); b.remove(); }", [kind, v])
  return f
CARDS = {   # name → (folder, langs, size, steps returning the click that saves)
  'share-payout-1080': ('img', ('en',), (1080, 1350), payout_card),
  'share-net-1080': ('img', ('en',), (1080, 1920), stats_card('net', 'story')),
  'share-trade-1080': ('img', ('en',), (1080, 608), trade_card),
  'share-weekly-hidden-1080': ('img', ('en',), (1080, 1350), stats_card('week', 'post')),
  'carte-journee-balayee': ('captures', ('en', 'fr'), (900, 1600), game_card('sweep')),
  'carte-payout': ('captures', ('en', 'fr'), (900, 1600), game_card('payout')),
  'carte-wrapped': ('captures', ('en', 'fr'), (900, 1600), game_card('wrapped', '2026-09', 'wrapped')),
}
def cards():
  from PIL import Image
  with sync_playwright() as p:
    br = p.chromium.launch(); errs = []
    for name, (folder, langs, (fw, fh), steps) in CARDS.items():
      if ONLY and name not in ONLY: continue
      for lang in langs:
        ctx = br.new_context(storage_state=f'{STATE}-{lang}.json', viewport={'width': 1200, 'height': 900}, locale=LOC[lang], timezone_id='America/New_York',
                             color_scheme='dark', reduced_motion='reduce', accept_downloads=True)
        ctx.clock.set_fixed_time(NOW)
        ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('%s')); try { delete Navigator.prototype.share; delete Navigator.prototype.canShare; } catch (e) {}" % lang)
        pg = ctx.new_page(); pg.on('pageerror', lambda e, n=name: errs.append(n + ': ' + str(e)[:160]))
        pg.goto(B + '/#dashboard'); pg.wait_for_selector('#main .nav-dash', timeout=30000); pg.wait_for_timeout(2500)
        try:
          save = steps(pg, lang)
          with pg.expect_download(timeout=20000) as dl: save()
          raw = '/tmp/shots-card.png'; dl.value.save_as(raw)
        except Exception as e: errs.append(f'{name} {lang}: CARD FAILED {str(e)[:200]}'); ctx.close(); continue
        d = os.path.join(OUT, folder, lang) if folder == 'captures' else os.path.join(OUT, folder); os.makedirs(d, exist_ok=True)
        im = Image.open(raw).convert('RGB'); print(name, lang, 'saved', im.size, end=' ')
        if im.size != (fw, fh):   # same proportions (a story card for the 900 × 1600 ones), else cover-crop from the centre
          r = max(fw / im.size[0], fh / im.size[1]); im = im.resize((round(im.size[0] * r), round(im.size[1] * r)), Image.LANCZOS)
          x, y = (im.size[0] - fw) // 2, (im.size[1] - fh) // 2; im = im.crop((x, y, x + fw, y + fh))
        png = os.path.join(d, name + '.png'); im.save(png); webp(png, os.path.join(d, name + '.webp'), 86)
        print(f"→ {os.path.getsize(os.path.join(d, name + '.webp')) // 1024} KB"); ctx.close()
    br.close()
  print('card errors:'); [print('  ', e) for e in errs]

def webp(png, dst, q):
  subprocess.run(['cwebp', '-quiet', '-q', str(q), '-m', '6', png, '-o', dst], check=True)

def main():
  langs = sorted({l for k, (kind, ls, f, st) in SHOTS.items() if not ONLY or k in ONLY for l in ls}) if not SEEDONLY else ['en', 'fr', 'es']
  if not KEEP: seed(langs)
  if SEEDONLY: return
  if '--cards' in sys.argv: cards(); return
  shoot()

def seed(langs):
  for t in ('images.py', 'chat.py'): subprocess.run([sys.executable, os.path.join(HERE, t)] + (['/tmp/shots-img'] if t == 'images.py' else []), check=True, capture_output=True)
  subprocess.run([sys.executable, os.path.join(HERE, 'seed.py'), B, STATE, *langs], check=True)
  for lang, uid in json.load(open(STATE + '-uids.json')).items():
    r = subprocess.run(['php', os.path.join(DEST, 'tools', 'site-shots', 'history.php'), uid, GAME_FROM, NOW.strftime('%Y-%m-%d'), NOW.strftime('%H:%M')], capture_output=True, text=True)
    print('history', lang, r.stdout.strip(), r.stderr.strip()[-300:])
  uids = json.load(open(STATE + '-uids.json')); H = {'en': 'AlexM', 'fr': 'Alex.M', 'es': 'Alex_M'}
  r = subprocess.run(['php', os.path.join(DEST, 'tools', 'site-shots', 'social.php'), NOW.strftime('%Y-%m-%d'), *[x for l in uids for x in (uids[l], H[l])]], capture_output=True, text=True)
  print('social', r.stdout.strip(), r.stderr.strip()[-300:])
  for lang in uids: subprocess.run([sys.executable, os.path.join(HERE, 'connect.py'), B, f'{STATE}-{lang}.json'], check=True, capture_output=True)
  econ()

# the week's releases (fictional figures): the calendar shows them published, with their forecast and previous
ECON = {'CPI m/m': ('0.3%', '0.3%', '0.4%'), 'Core CPI m/m': ('0.3%', '0.3%', '0.3%'), 'Core PPI m/m': ('0.2%', '0.3%', '0.1%'), 'PPI m/m': ('0.2%', '0.2%', '0.0%'),
        'Retail Sales m/m': ('0.7%', '0.4%', '0.5%'), 'Initial Jobless Claims': ('228K', '232K', '231K')}
def econ():
  import sqlite3
  db = sqlite3.connect(os.path.join(DEST, 'data', 'journal.db'), timeout=60)
  for ev, (a, f, pv) in ECON.items():
    db.execute("UPDATE econ_events SET actual = ?, forecast = ?, previous = ?, source = 'manual' WHERE event = ? AND ts BETWEEN ? AND ?", (a, f, pv, ev, 1791777600, 1792209600))
  db.execute("UPDATE econ_events SET forecast = '230K', previous = '228K' WHERE event = 'Initial Jobless Claims' AND ts > ?", (1792209600,))
  db.commit(); db.close()
  # Sweep AI's recap of Thursday's retail sales (what its report would say; written here: no call to Google)
  R = {'en': {'headline': 'Retail sales beat: shoppers kept spending in September', 'verdict': 'stronger',
              'summary': 'Retail sales rose 0.7% in September, above the 0.4% expected and the 0.5% of August. Spending held up across most categories, a sign that consumers are still resilient.',
              'vs_expectations': 'Actual 0.7% vs 0.4% forecast and 0.5% previous: a clear beat.',
              'reaction': {'nq': 'NQ dipped about 40 points in the first minutes, then recovered by the open.', 'es': 'ES slipped about 8 points before stabilising.', 'yields': 'The 10-year yield rose about 4 basis points.', 'dollar': 'The dollar firmed slightly.'},
              'drivers': ['Stronger consumer spending than expected', 'Higher yields weighed on tech at first', 'Same-day PPI came in line'],
              'fed_read': 'A strong consumer gives the Fed less reason to cut quickly.', 'what_to_watch': 'Next week: jobless claims on Thursday at 8:30.', 'confidence': 'medium', 'stage': 'final'},
         'fr': {'headline': 'Ventes au détail au-dessus des attentes en septembre', 'verdict': 'stronger',
              'summary': 'Les ventes au détail ont progressé de 0,7 % en septembre, au-dessus des 0,4 % attendus et des 0,5 % d’août. La consommation a tenu dans la plupart des catégories : le consommateur reste solide.',
              'vs_expectations': 'Publié 0,7 % contre 0,4 % prévu et 0,5 % le mois précédent : nettement au-dessus.',
              'reaction': {'nq': 'Le NQ a perdu une quarantaine de points dans les premières minutes, puis s’est repris avant l’ouverture.', 'es': 'L’ES a cédé environ 8 points avant de se stabiliser.', 'yields': 'Le taux à 10 ans a pris environ 4 points de base.', 'dollar': 'Le dollar s’est légèrement raffermi.'},
              'drivers': ['Une consommation plus forte que prévu', 'La hausse des taux a d’abord pesé sur la tech', 'L’IPP publié en même temps était conforme'],
              'fed_read': 'Un consommateur solide donne moins de raisons à la Fed de baisser vite ses taux.', 'what_to_watch': 'La semaine prochaine : inscriptions au chômage jeudi à 8 h 30.', 'confidence': 'medium', 'stage': 'final'},
         'es': {'headline': 'Las ventas minoristas superan lo esperado en septiembre', 'verdict': 'stronger',
              'summary': 'Las ventas minoristas subieron un 0,7 % en septiembre, por encima del 0,4 % esperado y del 0,5 % de agosto. El consumo se mantuvo en la mayoría de categorías: el consumidor sigue fuerte.',
              'vs_expectations': 'Dato 0,7 % frente al 0,4 % previsto y el 0,5 % anterior: claramente por encima.',
              'reaction': {'nq': 'El NQ cedió unos 40 puntos en los primeros minutos y se recuperó antes de la apertura.', 'es': 'El ES bajó unos 8 puntos antes de estabilizarse.', 'yields': 'El rendimiento a 10 años subió unos 4 puntos básicos.', 'dollar': 'El dólar se fortaleció ligeramente.'},
              'drivers': ['Un consumo más fuerte de lo esperado', 'La subida de los rendimientos pesó al principio sobre la tecnología', 'El IPP del mismo día salió en línea'],
              'fed_read': 'Un consumidor fuerte le da a la Fed menos motivos para bajar los tipos rápido.', 'what_to_watch': 'La próxima semana: solicitudes de desempleo el jueves a las 8:30.', 'confidence': 'medium', 'stage': 'final'}}
  db = sqlite3.connect(os.path.join(DEST, 'data', 'journal.db'), timeout=60)
  db.execute("CREATE TABLE IF NOT EXISTS econ_report (event_id TEXT NOT NULL, lang TEXT NOT NULL, data TEXT NOT NULL, sources TEXT, suggest TEXT, created_at INTEGER NOT NULL, PRIMARY KEY (event_id, lang))")
  rid = db.execute("SELECT id FROM econ_events WHERE event = 'Retail Sales m/m' AND ts BETWEEN 1791777600 AND 1792209600").fetchone()[0]
  for l, rep in R.items():
    db.execute('DELETE FROM econ_report WHERE event_id = ? AND lang = ?', (rid, l))
    db.execute('INSERT INTO econ_report (event_id, lang, data, sources, suggest, created_at) VALUES (?, ?, ?, ?, ?, ?)', (rid, l, json.dumps(rep, ensure_ascii=False), '[]', '', 1792067460))
  db.commit(); db.close()
  json.dump({'retail': rid}, open(DEST + '-econ.json', 'w'))

def shoot():
  with sync_playwright() as p:
    br = p.chromium.launch(); errs = []
    for name, (kind, langs, folder, steps) in SHOTS.items():
      if ONLY and name not in ONLY: continue
      if (name in FRIDAY) != EVENING: continue
      vw, vh, sc, fw, fh, phone = SIZE[kind]
      for lang in langs:
        ctx = br.new_context(**({} if name in SIGNED_OUT else {'storage_state': f'{STATE}-{lang}.json'}), viewport={'width': vw, 'height': vh}, device_scale_factor=sc, is_mobile=phone, has_touch=phone,
                             locale=LOC[lang], timezone_id='America/New_York', color_scheme='dark', reduced_motion='reduce')
        ctx.clock.set_fixed_time(NOW)
        ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('%s')); localStorage.setItem('sw.installShown', '1');" % lang)
        pg = ctx.new_page(); pg.on('pageerror', lambda e, n=name: errs.append(n + ': ' + str(e)[:160]))
        pg.goto(B + '/#dashboard')
        if name in SIGNED_OUT: pg.wait_for_timeout(3000)
        else: pg.wait_for_selector('#main .nav-dash', timeout=30000); pg.wait_for_timeout(2500)
        try: steps(pg, lang)
        except Exception as e: errs.append(f'{name} {lang}: STEP FAILED {str(e)[:200]}'); ctx.close(); continue
        d = os.path.join(OUT, folder, lang) if folder == 'captures' else os.path.join(OUT, folder)
        os.makedirs(d, exist_ok=True)
        base = name if folder == 'captures' else name.replace('{lang}', lang)
        png = os.path.join(d, base + '.png'); pg.screenshot(path=png, animations='disabled', caret='hide')
        from PIL import Image
        im = Image.open(png)
        if im.size != (fw, fh): im.convert('RGB').resize((fw, fh), Image.LANCZOS).save(png)
        webp(png, os.path.join(d, base + '.webp'), QUALITY[kind])
        if name in CLEAN: CLEAN[name](pg)
        print(f"{name} {lang}: {os.path.getsize(os.path.join(d, base + '.webp')) // 1024} KB")
        ctx.close()
    br.close()
  print('page errors:'); [print('  ', e) for e in errs]

main()
