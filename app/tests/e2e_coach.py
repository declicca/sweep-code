"""
Sweep — « Your coach » (brief 03 step 2), dev environment with Playwright:
  python3 tests/e2e_coach.py http://127.0.0.1:8095 [storage_state, unused: every case signs up its own trader]
A new trader with one account (daily limit $1,000), phone (fr, es) and computer (en):
  A. the plan sheet: one live sentence (no bias, a max loss above the account's limit, no setup);
  B. trades of the day: after a clean trade, what was right and where the session stands; a re-entry 4 min after a loss
     against the bias: the one thing to improve with its fix, « 2 losses in a row: pause », the same on the trade's page and
     in the « saved » message; the server's own out-of-plan codes are all seen by the coach (same rules);
  C. the 3rd of 3 planned trades: « session done »; a trade after the max loss: « taken after your max loss »;
  D. the review: the lesson in the sheet, the suggested rule; reviewed → Today shows the lesson and the rule for tomorrow;
     the next plan starts with that rule and saves it;
  E. the habit of the week (the rule broken most often the week before), with yesterday's or today's score;
  F. a trader starting out: the why under the fix, 2 trades max to start.
Checks: no page error, nothing wider than the window, the coach's texts in the trader's language.
"""
import json, os, re, sqlite3, sys, time
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
H = {'Content-Type': 'application/json', 'X-Requested-With': 'fetch'}
DB = os.environ.get('SWEEP_TEST_DB', '/tmp/g/data/journal.db')
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)
def unthrottle():
  try: d = sqlite3.connect(DB); d.execute('DELETE FROM attempts'); d.commit(); d.close()
  except Exception: pass
X = {
  'fr': {'need': 'Choisis ton biais et ta perte max', 'above': 'au-dessus de la limite du jour', 'nosetup': 'Pas de setup choisi', 'ok': 'Dans ton plan, stop respecté', 'left': 'Il te reste', 'fix': 'Pris 4 min après une perte',
         'loss2': '2ᵉ perte de suite', 'done': '3 trades sur 3 prévus', 'maxloss': 'Pris après ta perte max', 'lesson': 'sans erreur', 'rule': 'Après une perte : 10 minutes de pause', 'habit': 'Cette semaine : un stop sur chaque trade', 'why': 'Pourquoi :', 'new2': 'Pour commencer, 2 trades max'},
  'en': {'need': 'Pick your bias and your max loss', 'above': 'above the daily limit', 'nosetup': 'No setup chosen', 'ok': 'In your plan, stop respected', 'left': 'You have', 'fix': 'Taken 4 min after a loss',
         'loss2': '2 losses in a row', 'done': '3 of 3 planned trades', 'maxloss': 'Taken after your max loss', 'lesson': 'without a mistake', 'rule': 'After a loss: a 10-minute break', 'habit': 'This week: a stop on every trade', 'why': 'Why:', 'new2': 'To start, 2 trades max'},
  'es': {'need': 'Elige tu sesgo y tu pérdida máx.', 'above': 'por encima del límite diario', 'nosetup': 'Ningún setup elegido', 'ok': 'Dentro de tu plan, stop respetado', 'left': 'Te quedan', 'fix': 'Tomada 4 min después de una pérdida',
         'loss2': '2 pérdidas seguidas', 'done': '3 de 3 operaciones previstas', 'maxloss': 'Tomada después de tu pérdida máxima', 'lesson': 'sin error', 'rule': 'Tras una pérdida: 10 minutos de pausa', 'habit': 'Esta semana: un stop en cada operación', 'why': 'Por qué:', 'new2': 'Para empezar, 2 operaciones máx.'},
}
EN_ONLY = ['Your coach', 'To improve', 'In your plan', 'stop respected', 'losses in a row', 'You have', 'Rule for tomorrow', 'This week', 'without a mistake']
TXT = "(sel) => { const e = document.querySelector(sel); return e ? e.textContent.replace(/\\s+/g, ' ').trim() : '' }"
SEED = """() => {
  put('firms', { id: 'cf', name: 'Apex Trader Funding' });
  put('accounts', { id: 'ca', firm_id: 'cf', name: 'EOD 50K', starting_balance_c: 5000000, status: 'active', created_on: '2026-09-01', rules: { dll_c: 100000, dd_c: 200000 } });
  render(); }"""
TRADE = """([id, date, t1, t2, dir, pnl, extra]) => put('trades', Object.assign({ id, account_id: 'ca', instrument: 'NQ', direction: dir, contracts: 1, entry: 1, exit: 2, pnl_c: pnl, pnl_manual: true, date, entry_time: t1, exit_time: t2 }, extra || {}))"""
PLAN = """([day, pre]) => put('journals', Object.assign({}, getDoc('journals', day) || {}, { id: day, pre: Object.assign({ saved_at: Math.floor(Date.now() / 1000) }, pre) }))"""

def run(p, lang, phone):
  tag = f"{'390' if phone else '1300'}-{lang}"; x = X[lang]; texts = []
  unthrottle()
  br = p.chromium.launch()
  ctx = br.new_context(viewport={'width': 390, 'height': 844} if phone else {'width': 1300, 'height': 850}, is_mobile=phone, has_touch=phone, locale={'fr': 'fr-CA', 'en': 'en-US', 'es': 'es-ES'}[lang])
  ctx.add_init_script("try { localStorage.setItem('tj.lang', JSON.stringify('%s')); localStorage.setItem('sw.installShown', '1'); sessionStorage.setItem('sw.modal', '1') } catch (e) {}" % lang)
  r = ctx.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': 'co%d@t.dev' % int(time.time() * 1000), 'consent': True, 'elapsed': 6000}), headers=H)
  if r.status != 201: raise RuntimeError('sign-up refused: %s' % r.status)
  ctx.request.post(B + '/api/me/profile', data=json.dumps({'first_name': 'Léa', 'experience': 'gt1'}), headers=H)
  pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
  pg.goto(B + '/'); pg.wait_for_selector('form[data-onb]', timeout=20000); pg.wait_for_timeout(600)
  pg.evaluate(SEED); pg.wait_for_selector('#main .nav-dash', timeout=10000); pg.wait_for_timeout(900)
  for _ in range(30):   # the session the routine shows (the game's day: a weekend run plays Friday 15:00 ET)
    day = pg.evaluate("(SweepGame.state() && SweepGame.state().today && SweepGame.state().today.day) || ''")
    if day: break
    pg.wait_for_timeout(300)
  day = day or pg.evaluate("todayStr()")
  # Today before any plan
  t0 = pg.evaluate(TXT, '#main .co-today'); texts.append(t0)
  ok(bool(t0) and pg.locator('#main .co-today').is_visible(), f'{tag} Today: the coach card is there before the plan ({t0[:60]})')
  # A. the plan sheet, live
  pg.evaluate("(d) => SweepGame.openPlan(d)", day); pg.wait_for_selector('#gSheet [data-g=save-plan]', timeout=8000); pg.wait_for_timeout(400)
  note = lambda: pg.evaluate(TXT, '#gSheet .co-plan')
  n1 = note(); pg.locator('#gSheet [data-g=bias][data-v=bullish]').click(); pg.wait_for_timeout(250)
  pg.locator('#gSheet [data-gp=max_loss]').fill('1500'); pg.wait_for_timeout(250); n2 = note()
  pg.locator('#gSheet [data-gp=max_loss]').fill('1000'); pg.wait_for_timeout(250); n3 = note(); texts += [n1, n2, n3]   # (no max of trades yet: C sets it)
  ok(x['need'] in n1 and x['above'] in n2 and x['nosetup'] in n3, f'{tag} A plan sheet: « {n1[-40:]} » → « {n2[-40:]} » → « {n3[-40:]} »')
  pg.locator('#gSheet [data-g=save-plan]').click(); pg.wait_for_timeout(900)
  pre = pg.evaluate("(d) => (getDoc('journals', d) || {}).pre", day)
  ok(pre and pre.get('bias') == 'bullish' and pre.get('max_loss') == '1000', f'{tag} A the plan is saved as before ({pre and [pre.get("bias"), pre.get("max_loss")]})')
  # B. trades of the day
  pg.evaluate(TRADE, ['c1', day, '09:41', '09:50', 'long', 30000, {'discipline': {'stop': 'y'}, 'stop': 1}]); pg.evaluate("render()"); pg.wait_for_timeout(700)
  b1 = pg.evaluate(TXT, '#main .co-today'); texts.append(b1)
  ok(x['ok'] in b1 and x['left'] in b1, f'{tag} B a clean trade: « {x["ok"]} » and the money left before the max loss ({b1[-70:]})')
  pg.evaluate(TRADE, ['c2', day, '10:05', '10:20', 'long', -45000, {}]); pg.wait_for_timeout(500)   # (two trades saved by hand are never milliseconds apart)
  pg.evaluate(TRADE, ['c3', day, '10:24', '10:30', 'short', -20000, {}]); pg.evaluate("toast('Trade saved')"); pg.wait_for_timeout(150)
  toast = pg.evaluate("document.getElementById('toast').textContent"); texts.append(toast)
  pg.evaluate("render()"); pg.wait_for_timeout(800)
  b3 = pg.evaluate(TXT, '#main .co-today'); texts.append(b3)
  ok(x['fix'] in b3 and x['loss2'] in b3, f'{tag} B the re-entry 4 min after a loss: the fix and « {x["loss2"]} » ({b3[:90]}…)')
  ok(x['loss2'] in toast, f'{tag} B the « saved » message says it too ({toast[:80]})')
  ok(pg.locator('#main .co-today').is_visible() and pg.evaluate("document.documentElement.scrollWidth - innerWidth") <= 0, f'{tag} B Today: the card is visible, nothing wider than the window')
  if phone: pg.screenshot(path=f'/tmp/co_{tag}_today.png')
  pg.evaluate("location.hash = '#trade/c3'"); pg.wait_for_selector('#main .co-trade', timeout=8000); pg.wait_for_timeout(500)
  tp = pg.evaluate(TXT, '#main .co-trade'); texts.append(tp)
  ok(x['fix'] in tp and x['loss2'] in tp and pg.locator('#main .co-trade [data-act=ai-feedback]').count() == 1, f'{tag} B the trade page: the same coach, and « Go further with Sweep AI » at its place')
  ok(pg.locator('#main .tr-top [data-act=ai-feedback]').count() == 0, f'{tag} B no other AI button in the trade header')
  if phone: pg.screenshot(path=f'/tmp/co_{tag}_trade.png')
  # the server's out-of-plan codes (game/game.php) are all seen by the coach
  for _ in range(20):
    det = pg.evaluate("(SweepGame.state() && SweepGame.state().today && SweepGame.state().today.detail) || []")
    if len(det) >= 3: break
    pg.wait_for_timeout(500)
  miss = [[d['id'], c] for d in det for c in (d.get('v') or []) if c not in (pg.evaluate("(id) => SweepCoach.trade(getDoc('trades', id)).all", d['id']) or [])]
  ok(len(det) >= 3 and not miss, f'{tag} B the server\'s codes are all in the coach\'s ({len(det)} trades, missing {miss})')
  # C. the session done, then a trade after the max loss
  pg.evaluate("location.hash = '#dashboard'"); pg.wait_for_timeout(600)
  pg.evaluate(PLAN, [day, {'bias': 'bullish', 'max_loss': '1000', 'max_trades': '3', 'setups': []}]); pg.evaluate("render()"); pg.wait_for_timeout(600)
  c3 = pg.evaluate("(id) => SweepCoach.trade(getDoc('trades', id)).ses.t", 'c3'); texts.append(c3)
  pg.evaluate(TRADE, ['c4', day, '11:00', '11:10', 'long', -70000, {}]); pg.evaluate(TRADE, ['c5', day, '11:30', '11:40', 'long', 10000, {}]); pg.evaluate("render()"); pg.wait_for_timeout(600)
  c5 = pg.evaluate("(id) => { const c = SweepCoach.trade(getDoc('trades', id)); return [c.fix && c.fix[0], c.all] }", 'c5'); texts.append(c5[0] or '')
  ok(x['done'] in c3 and c5[0] and x['maxloss'] in c5[0] and 'over_max_trades' in c5[1], f'{tag} C « {c3[:40]} »; after the max loss: « {c5[0]} » ({c5[1]})')
  # D. the review, the rule for tomorrow, the next plan
  pg.evaluate("(d) => SweepGame.openReview(d)", day); pg.wait_for_selector('#gSheet [data-gr=tomorrow]', timeout=6000); pg.wait_for_timeout(400)
  rv = pg.evaluate(TXT, '#gSheet .co-rv'); ph = pg.evaluate("document.querySelector('#gSheet [data-gr=tomorrow]').placeholder"); texts += [rv, ph]
  ok(x['lesson'] in rv and ph, f'{tag} D the review sheet: the lesson ({rv[:70]}…), a suggested rule ({ph[:50]}…)')
  for sel in ('[data-g=r-followed][data-v=partly]', '[data-g=r-score][data-v="3"]', '[data-g=r-grade][data-v=C]'): pg.locator('#gSheet ' + sel).click(); pg.wait_for_timeout(150)
  pg.evaluate("document.querySelector('#gSheet [data-gr=tomorrow]').value = ''"); pg.locator('#gSheet [data-g=save-review]').click(); pg.wait_for_timeout(1200)
  d1 = pg.evaluate(TXT, '#main .co-today'); texts.append(d1)
  rule = pg.evaluate("(d) => SweepCoach.lesson(d).rule", day)
  ok(x['lesson'] in d1 and rule and rule in d1, f'{tag} D reviewed: Today shows the lesson and the rule for tomorrow ({rule})')
  nx = pg.evaluate("(d) => { const n = new Date(d + 'T12:00:00'); do n.setDate(n.getDate() + 1); while (n.getDay() === 0 || n.getDay() === 6); return `${n.getFullYear()}-${String(n.getMonth() + 1).padStart(2, '0')}-${String(n.getDate()).padStart(2, '0')}` }", day)
  pg.evaluate("(d) => SweepGame.openPlan(d)", nx); pg.wait_for_selector('#gSheet [data-g=save-plan]', timeout=6000); pg.wait_for_timeout(400)
  rv2 = pg.evaluate("(document.querySelector('#gSheet [data-gp=rule]') || {}).value")
  pg.locator('#gSheet [data-g=save-plan]').click(); pg.wait_for_timeout(700)
  saved = pg.evaluate("(d) => ((getDoc('journals', d) || {}).pre || {}).rule", nx)
  ok(rv2 == rule and saved == rule, f'{tag} D the next plan starts with the rule and saves it ({rv2!r})')
  # E. the habit of the week: last week, the stop broken most often
  pg.evaluate("""(day) => { const t0 = new Date(day + 'T12:00:00'), mon = new Date(t0); mon.setDate(t0.getDate() - ((t0.getDay() + 6) % 7));
      const iso = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
      [1, 2, 3].forEach((k) => { const d = new Date(mon); d.setDate(mon.getDate() - 7 + k); put('journals', { id: iso(d), pre: { bias: 'bullish', max_loss: '1000' } });
        put('trades', { id: 'w' + k, account_id: 'ca', instrument: 'NQ', direction: 'long', contracts: 1, entry: 1, exit: 2, pnl_c: 5000, pnl_manual: true, date: iso(d), entry_time: '09:45', exit_time: '09:55', discipline: { stop: 'n' } }); });
      render(); }""", day)
  pg.wait_for_timeout(800)
  hb = pg.evaluate(TXT, '#main .co-habit'); texts.append(hb)
  ok(x['habit'] in hb and re.search(r'\d', hb), f'{tag} E the habit of the week, with a score ({hb})')
  # F. a trader starting out: the why, simple goals
  pg.evaluate("S.me.experience = 'new'; location.hash = '#trade/c3'"); pg.wait_for_selector('#main .co-trade', timeout=6000); pg.wait_for_timeout(500)
  why = pg.evaluate(TXT, '#main .co-why'); texts.append(why)
  pn = pg.evaluate("SweepCoach.plan({ bias: 'bullish', maxLoss: 50000, maxTrades: 0, setups: 0 })"); texts.append(pn)
  ok(why.startswith(x['why']) and x['new2'] in pn, f'{tag} F starting out: « {why[:50]}… », « {pn[:45]}… »')
  if lang != 'en':
    bad = [w for w in EN_ONLY if any(w in t for t in texts if t)]
    ok(not bad, f'{tag} the coach speaks {lang} ({bad})')
  ok(not errs, f'{tag} no page error ({errs[:2]})')
  br.close()

with sync_playwright() as p:
  for lang, phone in (('fr', True), ('en', False), ('es', True)):
    print(f"— {'phone' if phone else 'computer'} {lang}")
    run(p, lang, phone)
print(f'{fails} failed' if fails else 'all passed')
sys.exit(1 if fails else 0)
