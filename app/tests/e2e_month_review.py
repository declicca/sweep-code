"""
Sweep — the « Month in Review » (1 Nov., brief avance 6), Playwright:
  python3 tests/e2e_month_review.py http://127.0.0.1:8095 [storage_state]
A new trader for each case, his trades of the month put in (a winning month, a losing one), then the server makes the snapshot
(its numbers are checked exactly in tests/month_review_test.php; the AI part comes from tests/samples/month-ai-mock.json).
The month used follows the server's clock (SWEEP_GAME_NOW of tools/run.sh, else New York time): on the month's last trading
day, the current month, closed by reviewing that day; else the month that ended. Outside the card's 7 days the server's
answer is set to « ready, not seen » (as e2e_weekly_card does) so the card is checked whatever the day.
Phone 390 touch (FR dark, ES light) and computer 1300 (EN light), a winning and a losing month each:
 - « Ton octobre est prêt » at the top of Today; one tap opens the story (it grows from the card);
 - the screens in order, the ones without data left out (a losing month without a winning trade: no « best trade »);
 - tap right = next, the left third = back, a long press pauses (the bar stops), arrows and space on the computer;
 - the end: « C’était octobre. » or « Octobre est fermé. Novembre repart à zéro. », Revoir and Partager; the share preview
   makes a 1080 × 1920 image, with the amounts or, the switch on, without any (win rate, journaled days, streak);
 - closed by sliding down (phone) or Escape (computer); seen to its end, the card goes; the month stays in « Ma progression »;
 - dark ink #0B0B0C or the light theme, no English left in FR / ES, nothing wider than the screen, no page error.
"""
import datetime, json, os, random, sqlite3, sys
from zoneinfo import ZoneInfo
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
H = {'Content-Type': 'application/json', 'X-Requested-With': 'fetch'}
DB = os.environ.get('SWEEP_TEST_DB', '/tmp/g/data/journal.db')
fails = 0
def waitf(pg, js, ms=8000):   # (the app's CSP refuses wait_for_function's eval)
  for _ in range(ms // 100):
    if pg.evaluate(js): return True
    pg.wait_for_timeout(100)
  return False
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)

MONTHS = {'en': ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'],
          'fr': ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre'],
          'es': ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']}
W = {'en': {'card': 'Your {m} is ready', 'open': 'MONTH IN REVIEW', 'win': 'That was {m}.', 'loss': '{M} is closed. {N} starts clean.', 'replay': 'Replay', 'share': 'Share', 'hide': 'Hide dollar amounts', 'tap': 'Tap to continue'},
     'fr': {'card': 'Ton {m} est prêt', 'open': 'TON MOIS EN REVUE', 'win': 'C’était {m}.', 'loss': '{M} est fermé. {N} repart à zéro.', 'replay': 'Revoir', 'share': 'Partager', 'hide': 'Masquer les montants', 'tap': 'Touche pour continuer'},
     'es': {'card': 'Tu {m} está listo', 'open': 'TU MES EN REVISIÓN', 'win': 'Así fue {m}.', 'loss': '{M} está cerrado. {N} empieza limpio.', 'replay': 'Ver de nuevo', 'share': 'Compartir', 'hide': 'Ocultar montos', 'tap': 'Toca para continuar'}}
NOTE = {'en': 'Waited for the retest before entering.', 'fr': 'J’ai attendu le retest avant d’entrer.', 'es': 'Esperé el retest antes de entrar.'}
NOTE_L = {'en': 'Chased the open, I knew it.', 'fr': 'J’ai couru après l’ouverture, je le savais.', 'es': 'Perseguí la apertura, lo sabía.'}
EN_ONLY = ['Tap to continue', 'MONTH IN REVIEW', 'NET RESULT', 'THE SHAPE', 'BEST TRADE', 'TOUGHEST', 'HOW YOU TRADED', 'YOUR AI', 'Win rate', 'Winners', 'Losers', 'Best day', 'Toughest day',
           'That was', 'starts clean', 'Replay', 'Share', 'Hide dollar', 'trading days', 'Journaled', 'Longest streak', 'Best session', 'Best setup', 'In your plan', 'Clean trades', 'Graded', 'Evaluation', 'Funded',
           'THE MONTH', 'YOUR EDGE', 'WHAT COST', 'YOUR JOURNAL', 'NEXT MONTH', 'You logged it', 'Logged and done', 'Your edge, finally']

# the server's clock → the month to review
gn = os.environ.get('SWEEP_GAME_NOW')
NOW = datetime.datetime.strptime(gn, '%Y-%m-%d %H:%M') if gn else datetime.datetime.now(ZoneInfo('America/New_York')).replace(tzinfo=None)
def weekdays(y, m):
  d = datetime.date(y, m, 1); out = []
  while d.month == m: (out.append(d) if d.weekday() < 5 else None); d += datetime.timedelta(days=1)
  return out
cur = weekdays(NOW.year, NOW.month); last = cur[-1]; today = NOW.date()
if today >= last:   # the month's last trading day: closed by its review (before 17:00) or by the close
  MODE = 'review' if today == last and NOW.hour < 17 else 'close'; Y, MO = NOW.year, NOW.month; DAYS = [x for x in cur if x <= today][-3:]
else:
  MODE = 'past'; p = NOW.replace(day=1) - datetime.timedelta(days=1); Y, MO = p.year, p.month; DAYS = weekdays(Y, MO)[-3:]
M = '%04d-%02d' % (Y, MO); NEXT = MONTHS['en'][MO % 12]
IN_WINDOW = MODE != 'past' or today.day <= 7
print(f'clock {NOW:%Y-%m-%d %H:%M} → month {M} ({MODE}), trading days {[str(x) for x in DAYS]}, card {"in its 7 days" if IN_WINDOW else "set by the test (outside its 7 days)"}')

WIN = [  # day index, time, instrument, direction, P&L (cents), setup, account, grade, checklist, note
  (0, '09:45', 'NQ', 'long', 50000, 'ORB', 'E', 'A', {'plan': 'y', 'stop': 'y'}, 'note'),
  (0, '10:30', 'NQ', 'short', -20000, 'ORB', 'F', 'B', {'plan': 'y', 'stop': 'n'}, ''),
  (1, '09:50', 'ES', 'long', 31000, 'VWAP', 'E', 'A', {}, ''),
  (2, '13:30', 'NQ', 'long', -10000, 'VWAP', 'F', 'C', {'stop': 'n'}, ''),
  (2, '10:05', 'NQ', 'long', 24500, 'ORB', 'L', 'A', {}, '')]
LOSS = [(0, '10:00', 'NQ', 'long', -40000, '', 'E', '', {}, 'note'), (1, '10:00', 'NQ', 'short', -15000, '', 'E', '', {}, ''), (2, '10:00', 'MNQ', 'long', -30000, '', 'E', '', {}, '')]

def run(br, lang, w, h, phone, scheme, kind, reduced=False):
  global fails
  tag = f'{w}-{lang}-{scheme} {kind}'; x = W[lang]; mname = MONTHS[lang][MO - 1]; errs = []
  try: d = sqlite3.connect(DB); d.execute('DELETE FROM attempts'); d.commit(); d.close()
  except Exception: pass
  ctx = br.new_context(viewport={'width': w, 'height': h}, is_mobile=phone, has_touch=phone, device_scale_factor=2 if phone else 1, color_scheme=scheme,
                       reduced_motion='reduce' if reduced else 'no-preference', locale={'fr': 'fr-CA', 'es': 'es-ES', 'en': 'en-US'}[lang])
  ctx.add_init_script("try { localStorage.setItem('tj.lang', JSON.stringify('%s')); sessionStorage.setItem('sw.modal', '1') } catch (e) {}" % lang)
  r = ctx.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': 'mr%06d@t.dev' % random.randint(0, 999999), 'consent': True, 'elapsed': 6000}), headers=H)
  if r.status != 201: raise RuntimeError('sign-up refused: %s' % r.status)
  ctx.request.post(B + '/api/me/profile', data=json.dumps({'first_name': 'Mo', 'experience': 'gt1'}), headers=H)
  seen = {'done': False}
  if not IN_WINDOW:   # outside the card's 7 days: the server says « ready, not seen » (until the story is seen to its end)
    def today_r(route):
      resp = route.fetch(); body = resp.json()
      body['month_review'] = {'month': M, 'done': seen['done'], 'mission': None}
      route.fulfill(response=resp, body=json.dumps(body), headers=dict(resp.headers, **{'content-type': 'application/json'}))
    ctx.route('**/api/game/today*', today_r)
  def viewed(route):
    try:
      if json.loads(route.request.post_data or '{}').get('done'): seen['done'] = True
    except Exception: pass
    route.continue_()
  ctx.route('**/api/game/wrapped/viewed', viewed)
  pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
  pg.goto(B + '/#dashboard'); pg.wait_for_timeout(2500)
  for a, mt in (('E', 'eval'), ('F', 'funded'), ('L', 'live')):
    pg.evaluate("([a, mt]) => put('accounts', { id: 'mr-' + a, name: a + ' 50K', status: 'active', phase: mt, money_type: mt, starting_balance_c: 5000000, created_on: '%s' })" % str(DAYS[0]), [a, mt])
  for k, (di, tm, ins, dr, pnl, st, acc, gr, disc, note) in enumerate(WIN if kind == 'win' else LOSS):
    t = {'id': 'mr-t%d' % k, 'account_id': 'mr-' + acc, 'instrument': ins, 'direction': dr, 'contracts': 1, 'entry': 1, 'exit': 2, 'pnl_c': pnl, 'pnl_manual': True, 'date': str(DAYS[di]),
         'session_date': True, 'entry_time': tm, 'exit_time': tm[:3] + '59', 'setup': st, 'grade': gr, 'discipline': disc, 'notes': (NOTE if kind == 'win' else NOTE_L)[lang] if note else ''}
    pg.evaluate("(t) => put('trades', t)", t)
  if MODE == 'review': pg.evaluate("(d) => put('journals', { id: d, post: { reviewed_at: Math.floor(Date.now() / 1000), well: 'ok' } })", str(DAYS[-1]))
  pg.wait_for_timeout(2000); pg.evaluate("SweepGame.refresh()"); pg.wait_for_timeout(3000)
  pg.evaluate("location.hash = '#dashboard'; render()")
  # 1. the Today card
  try: pg.wait_for_selector('#main .nav-mr', timeout=12000)
  except Exception: pass
  card = pg.locator('#main .nav-mr')
  ok(card.count() == 1, f'{tag}: the card at the top of Today')
  if not card.count(): ctx.close(); return
  txt = card.locator('b').inner_text().strip()
  ok(txt == x['card'].format(m=mname), f'{tag}: « {txt} »')
  first = pg.evaluate("(() => { const c = document.querySelector('#main .nav-rt'); return c && c.firstElementChild && c.firstElementChild.classList.contains('nav-mr') })()")
  ok(first, f'{tag}: the first thing of the routine card')
  card.first.scroll_into_view_if_needed()
  (card.first.tap() if phone else card.first.click())
  pg.wait_for_selector('.mr .mr-s.on', timeout=6000); pg.wait_for_timeout(200)
  keys = pg.evaluate("[...document.querySelectorAll('.mr .mr-s')].map((s) => s.dataset.k)")
  want = ['open', 'net', 'shape', 'best', 'tough', 'how', 'ai', 'end'] if kind == 'win' else ['open', 'net', 'shape', 'tough', 'how', 'ai', 'end']
  ok(keys == want, f'{tag}: the screens in order {keys}' + ('' if kind == 'win' else ' (no winning trade: no « best trade »)'))
  cur = lambda: pg.evaluate("(() => { const s = [...document.querySelectorAll('.mr .mr-s')]; return s.findIndex((x) => x.classList.contains('on')) })()")
  # the story's box, the theme
  bx = pg.evaluate("(() => { const b = document.querySelector('.mr-box').getBoundingClientRect(); return { x: b.x, y: b.y, w: b.width, h: b.height, bg: getComputedStyle(document.querySelector('.mr-box')).backgroundColor } })()")
  if phone: ok(round(bx['w']) == w and round(bx['h']) == h, f'{tag}: full screen on the phone ({bx["w"]}×{bx["h"]})')
  else: ok(abs(bx['w'] / bx['h'] - 9 / 16) < 0.01 and bx['h'] <= 0.9 * h + 1, f'{tag}: 9:16 in the middle, 90 vh at most ({round(bx["w"])}×{round(bx["h"])})')
  ok((bx['bg'] == 'rgb(11, 11, 12)') == (scheme == 'dark'), f'{tag}: background {bx["bg"]} ({scheme})')
  p0 = pg.evaluate("getComputedStyle(document.querySelector('.mr-box')).getPropertyValue('--p')")
  pill = pg.locator('.mr .mr-s.on .mr-pill').inner_text().strip()
  title = pg.locator('.mr .mr-s.on .mr-title').inner_text().strip()
  ok(pill == x['open'] and mname.lower() in title.lower() and str(Y) in title, f'{tag}: opening « {pill} » « {title} »')
  sub = pg.locator('.mr .mr-s.on .mr-sub').inner_text().strip()
  n = len(WIN if kind == 'win' else LOSS)
  ok(sub.startswith(f'{n} trades · 3 '), f'{tag}: « {sub} »')
  # 2. taps: right = next, the left third = back; a long press pauses
  tapAt = lambda fx: (pg.touchscreen.tap(bx['x'] + bx['w'] * fx, bx['y'] + bx['h'] / 2) if phone else pg.mouse.click(bx['x'] + bx['w'] * fx, bx['y'] + bx['h'] / 2))
  tapAt(0.8); pg.wait_for_timeout(150); i1 = cur()
  tapAt(0.15); pg.wait_for_timeout(150); i0 = cur()
  tapAt(0.8); pg.wait_for_timeout(450); i2 = cur()
  ok((i1, i0, i2) == (1, 0, 1), f'{tag}: tap right → next, left third → back ({i1}, {i0}, {i2})')
  net = pg.evaluate("(() => { const b = document.querySelector('.mr .mr-s.on .mr-hero'); return { v: b.querySelector('.v').textContent, g: b.querySelector('.g').textContent, pos: b.classList.contains('pos'), neg: b.classList.contains('neg') } })()")
  pg.wait_for_timeout(700); net2 = pg.evaluate("document.querySelector('.mr .mr-s.on .mr-hero .v').textContent")
  amt = '+$755' if kind == 'win' else '−$850'
  ok(net['g'].replace(' ', ' ').replace('\xa0', ' ') in ({'+$755', '−$850'} if lang == 'en' else {'+755 $', '−850 $', '+755 $', '−850 $'}) and net2 == net['g'] and (net['pos'] if kind == 'win' else net['neg']),
     f'{tag}: net result {net2!r} ({"blue" if kind == "win" else "gold"}), counted up from 0' + ('' if reduced else f' (was {net["v"]!r} at first)'))
  if reduced: ok(net['v'] == net['g'], f'{tag}: reduced motion: the final value at once')
  # long press: the bar and the story stop
  cx, cy = bx['x'] + bx['w'] / 2, bx['y'] + bx['h'] / 2
  pg.mouse.move(cx, cy); pg.mouse.down(); pg.wait_for_timeout(500)
  p1 = pg.evaluate("document.querySelector('.mr .mr-prog i:nth-child(2) s').style.transform"); paused = pg.evaluate("document.querySelector('.mr').classList.contains('paused')")
  pg.wait_for_timeout(900); p2 = pg.evaluate("document.querySelector('.mr .mr-prog i:nth-child(2) s').style.transform")
  pg.mouse.up(); pg.wait_for_timeout(150)
  still = cur(); resumed = not pg.evaluate("document.querySelector('.mr').classList.contains('paused')")
  ok(paused and p1 == p2 and still == 1 and resumed, f'{tag}: a long press pauses ({p1} = {p2}) and does not change the screen; released, it goes on')
  if not phone:   # space pauses too, the arrows go
    pg.keyboard.press('Space'); pg.wait_for_timeout(100); sp = pg.evaluate("document.querySelector('.mr').classList.contains('paused')")
    pg.keyboard.press('Space'); pg.wait_for_timeout(100); sp2 = pg.evaluate("document.querySelector('.mr').classList.contains('paused')")
    ok(sp and not sp2, f'{tag}: space pauses and goes on')
    pg.click('.mr-arr.r'); pg.wait_for_timeout(120); a1 = cur(); pg.click('.mr-arr.l'); pg.wait_for_timeout(120); a0 = cur()
    pg.keyboard.press('ArrowRight'); pg.wait_for_timeout(120); k1 = cur(); pg.keyboard.press('ArrowLeft'); pg.wait_for_timeout(120)
    ok((a1, a0, k1) == (2, 1, 2), f'{tag}: arrows on the sides and the keyboard ({a1}, {a0}, {k1})')
  # every screen: safe zones, nothing wider than the screen, the words in the right language
  texts = []; zone = []
  for k in range(len(keys)):
    pg.evaluate("(k) => { const s = [...document.querySelectorAll('.mr .mr-s')]; s.forEach((x, j) => x.classList.toggle('on', j === k)); }", k)
    pg.wait_for_timeout(60)
    z = pg.evaluate("""(() => { const b = document.querySelector('.mr-box').getBoundingClientRect(), s = document.querySelector('.mr .mr-s.on');
      const r = [...s.querySelectorAll('.mr-a')].map((e) => e.getBoundingClientRect()); const top = Math.min(...r.map((x) => x.top)) - b.top, bot = b.bottom - Math.max(...r.map((x) => x.bottom));
      const wide = [...s.querySelectorAll('*')].some((e) => { const q = e.getBoundingClientRect(); return q.width && (q.left < b.left - 1 || q.right > b.right + 1) });
      const c = s.cloneNode(true); c.querySelectorAll('.mr-ai p, .mr-card q, .mr-card p').forEach((e) => e.remove()); return { top, bot, wide, txt: c.textContent } })()""")
    texts.append(z['txt']); zone.append((keys[k], round(z['top']), round(z['bot']), z['wide']))
  ok(all(t >= 100 and b >= 110 and not wd for _, t, b, wd in zone), f'{tag}: safe zones (top ≥ 100, bottom ≥ 110) and nothing wider: {zone}')
  pg.evaluate("document.querySelectorAll('.mr .mr-s').forEach((x) => x.classList.remove('on'))")
  if lang != 'en':
    left = [wd for wd in EN_ONLY if any(wd in t for t in texts)]
    ok(not left, f'{tag}: no English left {left}')
  ai = ' '.join(t for t, kk in zip(texts, keys) if kk == 'ai')
  ok(kind == 'loss' or len(ai) > 20, f'{tag}: the AI breakdown, 5 blocks: ' + ai[:120])
  tough = texts[keys.index('tough')]
  ok(({'en': 'You logged it', 'fr': 'Tu l’as noté', 'es': 'Lo registraste'} if kind == 'loss' else {'en': 'Logged and done', 'fr': 'Noté, c’est fait', 'es': 'Registrado y listo'})[lang] in tough, f'{tag}: the toughest trade\'s last line ({"a note" if kind == "loss" else "no note"})')
  # 3. to the end (keyboard / taps), its text and buttons; the colors of a losing month go from gold to blue
  for _ in range(len(keys)):
    if cur() == len(keys) - 1: break
    if phone: tapAt(0.85)
    else: pg.keyboard.press('ArrowRight')
    pg.wait_for_timeout(120)
  pg.wait_for_timeout(500)
  pe = pg.evaluate("getComputedStyle(document.querySelector('.mr-box')).getPropertyValue('--p')")
  end = pg.locator('.mr .mr-s.on .mr-end').inner_text().strip()
  wantEnd = x['win'].format(m=mname) if kind == 'win' else x['loss'].format(M=mname.capitalize(), N=MONTHS[lang][MO % 12].capitalize())
  ok(end == wantEnd, f'{tag}: the end « {end} »')
  btn = pg.evaluate("[...document.querySelectorAll('.mr .mr-s.on .mr-acts .btn')].map((b) => [b.textContent.trim(), b.classList.contains('primary')])")
  ok(btn == [[x['replay'], False], [x['share'], True]], f'{tag}: Replay and Share (blue) {btn}')
  if kind == 'loss': ok(p0.strip() in ('0', '0.0') and pe.strip() == '1', f'{tag}: a losing month: gold to blue (--p {p0} → {pe})')
  pg.wait_for_timeout(5600); ok(cur() == len(keys) - 1, f'{tag}: no auto-advance on the end screen')
  # 4. share: the preview, with and without the amounts
  pg.click('.mr .mr-s.on [data-mr=share]'); waitf(pg, "(() => { const i = document.querySelector('.mr-sh img'); return !!(i && i.complete && i.naturalWidth > 0) })()")
  im = pg.evaluate("(() => { const i = document.querySelector('.mr-sh img'); return { w: i.naturalWidth, h: i.naturalHeight, t: i.dataset.txt, sw: document.querySelector('.mr-sw').textContent.trim() } })()")
  ok(im['w'] == 1080 and im['h'] == 1920 and ('$' in im['t']) and 'makeitsweep.com' in im['t'] and x['open'] in im['t'], f'{tag}: the share image 1080×1920 with the amounts ({im["t"][:110]}…)')
  ok(im['sw'] == x['hide'], f'{tag}: the switch « {im["sw"]} »')
  pg.click('.mr-sw'); waitf(pg, "!!(document.querySelector('.mr-sh img') && document.querySelector('.mr-sh img').dataset.hide === '1' && document.querySelector('.mr-sh img').complete)"); pg.wait_for_timeout(200)
  im2 = pg.evaluate("(() => { const i = document.querySelector('.mr-sh img'); return { w: i.naturalWidth, h: i.naturalHeight, t: i.dataset.txt } })()")
  ok(im2['w'] == 1080 and im2['h'] == 1920 and '$' not in im2['t'] and '%' in im2['t'] and '/3' in im2['t'], f'{tag}: amounts hidden: no dollar anywhere, the win rate, journaled days, streak ({im2["t"][:120]}…)')
  pg.keyboard.press('Escape'); pg.wait_for_timeout(300)
  ok(pg.locator('.mr-sh').count() == 0 and pg.locator('.mr').count() == 1, f'{tag}: Escape closes the preview first')
  pg.click('.mr .mr-s.on [data-mr=replay]'); pg.wait_for_timeout(200)
  ok(cur() == 0, f'{tag}: Replay → the first screen')
  ok(pg.evaluate("document.documentElement.scrollWidth <= innerWidth"), f'{tag}: no horizontal scroll')
  # 5. close: slide down (phone), Escape (computer)
  if phone:
    pg.mouse.move(cx, bx['y'] + 300); pg.mouse.down(); pg.mouse.move(cx, bx['y'] + 380, steps=4); pg.mouse.move(cx, bx['y'] + 560, steps=6); pg.mouse.up()
  else: pg.keyboard.press('Escape')
  pg.wait_for_timeout(900)
  ok(pg.locator('.mr').count() == 0, f'{tag}: closed by {"sliding down" if phone else "Escape"}')
  pg.wait_for_timeout(400)
  ok(pg.locator('#main .nav-mr').count() == 0 and seen['done'], f'{tag}: seen to its end: no card any more')
  # 6. later: the month in « Ma progression » (the computer, winning month)
  if not phone and kind == 'win':
    pg.evaluate("SweepGame.open('hub')"); pg.wait_for_selector('#gSheet .wr-ai[data-v="%s"]' % M, timeout=10000); pg.wait_for_timeout(400)
    pg.click('#gSheet .wr-ai[data-v="%s"]' % M); pg.wait_for_selector('.mr .mr-s.on', timeout=8000)
    ok(pg.locator('.mr .mr-s').count() == len(keys), f'{tag}: opened again from « Ma progression » (history), the same screens')
    pg.keyboard.press('Escape'); pg.wait_for_timeout(600)
  ok(not errs, f'{tag}: no page error ({errs[:2]})')
  ctx.close()

with sync_playwright() as p:
  br = p.chromium.launch()
  for lang, w, h, phone, scheme in (('fr', 390, 844, True, 'dark'), ('es', 390, 844, True, 'light'), ('en', 1300, 850, False, 'light')):
    for kind in ('win', 'loss'):
      run(br, lang, w, h, phone, scheme, kind, reduced=(lang == 'en' and kind == 'loss'))
  br.close()
print(f'{fails} failed' if fails else 'all passed')
sys.exit(1 if fails else 0)
