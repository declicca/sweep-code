"""
Sweep — the end-of-day lock (1 Nov., brief avance 4), Playwright:
  python3 tests/e2e_day_lock.py http://127.0.0.1:8095
A trader of its own each time: phone 390 (fr, touch, dark), phone 390 (es, light), computer 1300 (en, light).
 1  before the limit, the discreet counter of « Now »: « 1/3 trades · $350 left today »
 2  Settings › My routine: the max loss lowered to $200 says it applies from the next session; today keeps its limits
 3  the trade that reaches the plan's max loss: Today switches to « Day closed » — the countdown to the next session, the coach's
    sentence, exactly two actions (grade my trades, close my day: the only blue button), no « Now », no steps; the server agrees
 4  the + still opens the trade form and the trade is saved; the day stays closed
 5  « Grade my trades » opens the next trade not graded, then the day's trades once all are graded; the server counts them
 6  a trade deleted: still closed (the lock reached is kept); « Close my day » opens the review
 7  after 18:00 ET (the browser's clock pinned on the day at 18:05): the lock is gone
No page error, nothing wider than the window, no English in French or Spanish.
"""
import datetime as dt, json, os, random, re, sqlite3, sys
from zoneinfo import ZoneInfo
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
H = {'Content-Type': 'application/json', 'X-Requested-With': 'fetch'}
DB = os.environ.get('SWEEP_TEST_DB', '/tmp/g/data/journal.db')
SHOTS = os.environ.get('SWEEP_SHOTS', '')
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)
X = {
  'fr': {'cnt': r'1/3 trades · 350 \$ restants aujourd’hui', 'pill': 'Journée fermée', 'loss': 'Ta perte max de 600 $ est atteinte.', 'next': 'Prochaine séance dans', 'co': 'protège ton compte',
         'grade': 'Noter mes trades', 'close': 'Fermer ma journée', 'wait': 'À partir du', 'label': 'Perte max par jour'},
  'es': {'cnt': r'1/3 operaciones · 350 \$ restantes hoy', 'pill': 'Día cerrado', 'loss': 'Alcanzaste tu pérdida máx. de 600 $.', 'next': 'Próxima sesión en', 'co': 'protege tu cuenta',
         'grade': 'Calificar mis operaciones', 'close': 'Cerrar mi día', 'wait': 'Desde el', 'label': 'Pérdida máx. por día'},
  'en': {'cnt': r'1/3 trades · \$350 left today', 'pill': 'Day closed', 'loss': 'Your max loss of $600 is reached.', 'next': 'Next session in', 'co': 'protects your account',
         'grade': 'Grade my trades', 'close': 'Close my day', 'wait': 'From ', 'label': 'Max loss per day'},
}
EN = ['Day closed', 'Next session', 'Grade my trades', 'Close my day', 'left today', 'max loss', 'Max loss per day', 'Max trades per day', 'New York time', 'your next session']
NOW = "(() => { const n = document.querySelector('#main .nav-rt .nav-now'); return n ? n.textContent.replace(/\\s+/g, ' ').trim() : null })()"
LOCK = """(() => { const c = document.querySelector('#main .nav-rt.nav-lockd'), l = c && c.querySelector('.nav-lock'); if (!l) return null;
  const bs = [...l.querySelectorAll('button')]; return { text: c.textContent.replace(/\\s+/g, ' ').trim(), n: (l.querySelector('.nav-lock-n') || {}).textContent || '',
  btn: bs.map((b) => [b.textContent.trim(), b.classList.contains('primary'), Math.round(b.getBoundingClientRect().height), getComputedStyle(b).borderTopLeftRadius]),
  steps: document.querySelectorAll('#main .nav-rt .nav-rt-steps, #main .nav-rt .nav-now').length, blue: [...document.querySelectorAll('#main .nav-rt .btn.primary')].filter((b) => b.getClientRects().length).length,
  coach: [...c.querySelectorAll('.co-today')].filter((b) => b.getClientRects().length).length } })()"""
WIDE = "document.documentElement.scrollWidth - innerWidth"
SAVE = """async (o) => { Object.assign(TK, o); tkRefresh(); const ids = new Set(S.trades.map((t) => t.id)); tkSave(); await new Promise((r) => setTimeout(r, 1500));
  const t = S.trades.find((x) => !ids.has(x.id)); return t ? [t.id, t.date, t.pnl_c] : (document.querySelector('#tkErr') || {}).innerText }"""
sp = lambda s: (s or '').replace(' ', ' ').replace(' ', ' ')
with sync_playwright() as p:
  br = p.chromium.launch()
  for lang, w, phone, theme in (('fr', 390, True, 'dark'), ('es', 390, True, 'light'), ('en', 1300, False, 'light')):
    tag = f'{w}-{lang}-{theme}'; x = X[lang]
    try: d = sqlite3.connect(DB); d.execute('DELETE FROM attempts'); d.commit(); d.close()
    except Exception: pass
    loc = {'fr': 'fr-CA', 'es': 'es-ES', 'en': 'en-US'}[lang]
    ctx = br.new_context(viewport={'width': w, 'height': 844 if phone else 850}, is_mobile=phone, has_touch=phone, locale=loc, color_scheme=theme, timezone_id='America/New_York')
    ctx.add_init_script("try { localStorage.setItem('tj.lang', JSON.stringify('%s')); sessionStorage.setItem('sw.modal', '1') } catch (e) {}" % lang)
    r = ctx.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': 'dl%06d@t.dev' % random.randint(0, 999999), 'consent': True, 'elapsed': 6000}), headers=H)
    if r.status != 201: raise RuntimeError('sign-up refused: %s' % r.status)
    ctx.request.post(B + '/api/me/profile', data=json.dumps({'first_name': 'Ari', 'experience': 'gt1'}), headers=H)
    pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
    pg.goto(B + '/#dashboard'); pg.wait_for_timeout(2500)
    pg.evaluate("put('accounts', { id: 'dl-a', name: 'Topstep 50K', status: 'active', phase: 'eval', starting_balance_c: 5000000, created_on: '2026-09-01', rules: { dd_c: 300000, dll_c: 100000 } })")
    def today(wait=1500):
      pg.wait_for_timeout(wait); pg.evaluate("location.hash = '#dashboard'; render()"); pg.wait_for_selector('#main .nav-rt:not(.ph)', timeout=10000); pg.wait_for_timeout(1200)
    today()
    day = pg.evaluate("(SweepGame.state() && SweepGame.state().today && SweepGame.state().today.day) || todayStr()")
    if not pg.evaluate("!!(SweepGame.state() && SweepGame.state().today && SweepGame.state().today.market)"):
      print(f'skip {tag}: the market is closed today (the game\'s clock)'); ctx.close(); continue
    ok(pg.evaluate("matchMedia('(prefers-color-scheme: dark)').matches") == (theme == 'dark'), f'{tag} the {theme} theme')
    # 1. the counter before the limit
    pg.evaluate("(d) => put('journals', { id: d, pre: { bias: 'bullish', max_loss: '600', max_trades: '3', saved_at: Math.floor(Date.now() / 1000) } })", day)
    pg.evaluate("(d) => put('trades', { id: 'dl-t1', account_id: 'dl-a', instrument: 'NQ', direction: 'long', contracts: 1, entry: 1, exit: 2, pnl_c: -25000, pnl_manual: true, date: d, entry_time: '09:45', exit_time: '09:50' })", day)
    today(); n = sp(pg.evaluate(NOW))
    ok(bool(n) and re.search(x['cnt'], n) is not None and pg.locator('#main .nav-lock').count() == 0, f'{tag} 1 the counter « {x["cnt"]} » before the limit ({n})')
    # 2. Settings: the max loss lowered to $200 applies from the next session
    pg.evaluate("location.hash = '#settings'"); pg.wait_for_selector('#main input[data-daylock="loss"]', state='attached', timeout=10000)
    pg.evaluate("document.querySelectorAll('#main details.nav-sgd').forEach((g) => { if (g.querySelector('input[data-daylock]')) g.open = true; })"); pg.wait_for_timeout(400)
    lab = sp(pg.evaluate("document.querySelector('#main input[data-daylock=\"loss\"]').closest('label').textContent.trim()"))
    pg.locator('#main input[data-daylock="loss"]').fill('200'); pg.locator('#main input[data-daylock="loss"]').dispatch_event('change'); pg.wait_for_timeout(1200)
    pg.evaluate("render()"); pg.wait_for_timeout(600)
    pg.evaluate("document.querySelectorAll('#main details.nav-sgd').forEach((g) => { if (g.querySelector('input[data-daylock]')) g.open = true; })"); pg.wait_for_timeout(300)
    dl = pg.evaluate("S.settings.day_lock || null"); hp = sp(pg.evaluate("(document.querySelector('#main .nav-dl-help') || {}).textContent || ''"))
    ok(lab == x['label'] and dl and dl['loss_c'] == 20000 and dl['from'] > day and x['wait'] in hp, f'{tag} 2 Settings: « {x["label"]} » $200 applies from {dl and dl["from"]}, said under it ({hp[-90:]!r})')
    if SHOTS: pg.locator('#main input[data-daylock="loss"]').evaluate("(e) => e.closest('section').scrollIntoView()"); pg.screenshot(path=os.path.join(SHOTS, f'dl-settings-{tag}.png'))
    if lang != 'en': ok(not [e for e in EN if e in pg.evaluate("document.querySelector('#main input[data-daylock]').closest('.fgrid').textContent")], f'{tag} 2 no English in the limits')
    ok(pg.evaluate(WIDE) <= 0, f'{tag} 2 Settings: nothing wider than the window')
    today(); n = sp(pg.evaluate(NOW))
    ok(bool(n) and '350' in n and pg.locator('#main .nav-lock').count() == 0, f'{tag} 2 today keeps its limits: still $350 left, not closed ({n})')
    # 3. the trade that reaches the max loss
    pg.evaluate("(d) => put('trades', { id: 'dl-t2', account_id: 'dl-a', instrument: 'NQ', direction: 'long', contracts: 1, entry: 1, exit: 2, pnl_c: -40000, pnl_manual: true, date: d, entry_time: '10:45', exit_time: '10:50' })", day)
    today(); lk = pg.evaluate(LOCK); t = sp(lk['text']) if lk else ''
    ok(bool(lk) and x['pill'] in t and x['loss'] in t and x['next'] in t and x['co'] in t and re.search(r'\d', lk['n'] or '') is not None, f'{tag} 3 « {x["pill"]} »: the limit, the countdown ({sp(lk["n"]) if lk else None}), the coach ({t[:170]!r})')
    ok(bool(lk) and [b[0] for b in lk['btn']] == [x['grade'], x['close']] and [b[1] for b in lk['btn']] == [False, True] and lk['blue'] == 1, f'{tag} 3 exactly two actions, « {x["close"]} » the only blue button ({lk and lk["btn"]})')
    ok(bool(lk) and all(b[2] >= 44 and b[3] in ('999px', '22px') or b[2] >= 44 and float(b[3].rstrip('px') or 0) >= b[2] / 2 - 1 for b in lk['btn']), f'{tag} 3 the buttons: 44 px capsules ({lk and [(b[2], b[3]) for b in lk["btn"]]})')
    ok(bool(lk) and lk['steps'] == 0 and lk['coach'] == 0, f'{tag} 3 no « Now », no steps, no coach card under it: a calm screen ({lk and (lk["steps"], lk["coach"])})')
    sv = None
    for _ in range(20):
      pg.evaluate("SweepGame.refresh && SweepGame.refresh()"); pg.wait_for_timeout(700)
      sv = pg.evaluate("(SweepGame.state().today || {}).lock || null")
      if sv: break
    ok(bool(sv) and sv['why'] == 'loss' and sv['loss_c'] == 60000 and sv['n'] == 2, f'{tag} 3 the server recorded the same lock ({sv})')
    if lang != 'en': ok(not [e for e in EN if e in t], f'{tag} 3 no English ({[e for e in EN if e in t]})')
    if SHOTS: pg.locator('#main .nav-rt').screenshot(path=os.path.join(SHOTS, f'dl-closed-{tag}.png'))
    # 4. the + still opens the trade form, and saving works
    pg.locator('.bottomnav .plus' if phone else 'aside.side .new').first.click(); pg.wait_for_timeout(1200)
    op = pg.evaluate("!!document.querySelector('#tkSlide.open, .nav-am-shot.open')")   # (phone: the quick sheet, computer: the ticket)
    if pg.locator('.nav-am-shot.open').count(): pg.keyboard.press('Escape'); pg.wait_for_timeout(500); pg.evaluate("openTicket(null, { manual: true })"); pg.wait_for_timeout(900)
    sv3 = pg.evaluate(SAVE, {'account': 'dl-a', 'inst': 'NQ', 'dir': 'long', 'qty': 1, 'entry': 21000, 'exit': 21005}) if op else None
    ok(op and isinstance(sv3, list) and sv3[1] == day and sv3[2] == 10000, f'{tag} 4 the + opens the trade form while closed, the trade is saved ({sv3})')
    pg.wait_for_timeout(800); pg.evaluate("typeof closeTicket === 'function' && closeTicket()"); pg.wait_for_timeout(600)
    today(); ok(pg.evaluate(LOCK) is not None, f'{tag} 4 still closed after it')
    # 5. grade my trades: the next one not graded, then the day's trades
    t3 = sv3[0] if isinstance(sv3, list) else ''
    seen = []
    for tid in ('dl-t1', 'dl-t2', t3):
      pg.locator('#main [data-rt="lock-grade"]').click(); pg.wait_for_timeout(900)
      seen.append(pg.evaluate("location.hash"))
      pg.evaluate("(id) => editDoc('trades', id, (t) => { t.setup = 'ORB'; t.emo = Object.assign({}, t.emo, { before: ['calm'] }); t.rules_followed = 'yes'; })", tid)
      today(800)
    pg.locator('#main [data-rt="lock-grade"]').click(); pg.wait_for_timeout(900); seen.append(pg.evaluate("location.hash"))
    ok(seen == ['#trade/dl-t1', '#trade/dl-t2', '#trade/' + t3, '#journal/' + day], f'{tag} 5 « {x["grade"]} »: each trade not graded in turn, then the day\'s trades ({seen})')
    jn = 0
    for _ in range(15):
      pg.evaluate("SweepGame.refresh && SweepGame.refresh()"); pg.wait_for_timeout(700)
      jn = pg.evaluate("(SweepGame.state().today || {}).journaled || 0")
      if jn >= 3: break
    ok(jn == 3, f'{tag} 5 grading works while closed: the server counts the 3 trades journaled ({jn})')
    # 6. a trade deleted: still closed; « Close my day » opens the review
    pg.evaluate("remove('trades', 'dl-t2')"); today(2000)
    ok(pg.evaluate(LOCK) is not None and pg.evaluate("SweepCoach.dayLock() && SweepCoach.dayLock().why") == 'loss', f'{tag} 6 the losing trade deleted: the day stays closed (the lock reached is kept)')
    pg.locator('#main .nav-lock [data-rt="fin"]').click(); pg.wait_for_timeout(1200)
    ok(pg.locator('#gSheet').count() == 1, f'{tag} 6 « {x["close"]} » opens the review')
    pg.keyboard.press('Escape'); pg.wait_for_timeout(600)
    ok(pg.evaluate(WIDE) <= 0, f'{tag} nothing wider than the window')
    ok(not errs, f'{tag} no page error ({errs[:2]})')
    # 7. after 18:00 ET on that day: the next session, the lock gone
    at = dt.datetime.fromisoformat(day + 'T18:05:00').replace(tzinfo=ZoneInfo('America/New_York'))
    p2 = ctx.new_page(); e2 = []; p2.on('pageerror', lambda e: e2.append(str(e)[:160]))
    p2.clock.install(time=at); p2.goto(B + '/#dashboard'); p2.wait_for_selector('#main .nav-rt:not(.ph)', timeout=15000); p2.wait_for_timeout(2500)
    ok(p2.evaluate("todayStr()") > day and p2.locator('#main .nav-lock').count() == 0, f'{tag} 7 {day} 18:05 ET: the next session, no lock ({p2.evaluate("todayStr()")})')
    ok(not e2, f'{tag} 7 no page error ({e2[:2]})')
    ctx.close()
  br.close()
print(f'{fails} failed' if fails else 'all passed')
sys.exit(1 if fails else 0)
