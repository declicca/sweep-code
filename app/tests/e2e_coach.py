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
Then, brief 03 step 3 (a new trader: an account with a $1,000 daily limit, 3 trades today, the last loss 4 min ago):
  G. both add forms (manual and screenshot) say it before the trade: « your last loss was 4 min ago: wait 6 more min »,
     with his own number (his past re-entries after a loss), and what is left (max loss, trades);
  H. the account at 80 % then 100 % of its daily limit: the « saved » message, the coach's card and the bell (« Prop firm
     alerts »), each level once.
Then, brief 03 step 4 (5 weeks of trades, the stop broken less and less, the ORB setup always winning):
  I. the Stats page opens with « What works for you »: the strength (best setup, its sample), the leak (the stop), the rule,
     the progress of the stop week by week (going up); the Friday recap's coach block speaks in % and counts, no dollar.
Then, brief 03 step 5 (fewer options in sight, nothing removed):
  J. the trade's page: « Answer your coach » (the plan, what pushed him in, his lesson) in place of « Review x of 4 », the
     answers saved in the same fields; the full review folded, still open after a tap in it; the screenshot form and the
     manual form's step 2: 3 questions, the rest one tap away; Settings: « Advanced » last, folded.
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
Y = {
  'fr': {'wait': 'Ta dernière perte date de', 'own': 'Tes trades pris moins de 10 min après une perte', 'left': 'avant ta perte max', 'd75': 'de ta limite du jour utilisés', 'd100': 'limite du jour atteinte'},
  'en': {'wait': 'Your last loss was', 'own': 'Your trades taken less than 10 min after a loss', 'left': 'before your max loss', 'd75': 'of your daily limit used', 'd100': 'daily limit reached'},
  'es': {'wait': 'Tu última pérdida fue hace', 'own': 'Tus operaciones tomadas menos de 10 min', 'left': 'antes de tu pérdida máxima', 'd75': 'de tu límite diario usado', 'd100': 'límite diario alcanzado'},
}
Z = {
  'fr': {'title': 'Ce qui fonctionne pour toi', 'strong': 'Ton meilleur setup : « ORB »', 'leak': 'Le stop non respecté', 'ago': 'Il y a 4 semaines', 'rule': 'Un stop placé avant chaque entrée'},
  'en': {'title': 'What works for you', 'strong': 'Your best setup: “ORB”', 'leak': 'The stop not respected', 'ago': '4 weeks ago', 'rule': 'A stop set before each entry'},
  'es': {'title': 'Lo que funciona para ti', 'strong': 'Tu mejor setup: « ORB »', 'leak': 'El stop no respetado', 'ago': 'Hace 4 semanas', 'rule': 'Un stop puesto antes de cada entrada'},
}
HIST = """() => { put('firms', { id: 'wf', name: 'Topstep' }); put('accounts', { id: 'wa', firm_id: 'wf', name: 'TS 50K', starting_balance_c: 5000000, status: 'active', created_on: '2026-08-01' });
  const iso = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
  const t0 = new Date(todayStr() + 'T12:00:00'), mon = new Date(t0); mon.setDate(t0.getDate() - ((t0.getDay() + 6) % 7)); let n = 0;
  for (let w = 4; w >= 0; w--) for (let d = 0; d < 5; d++) {
    const day = new Date(mon); day.setDate(mon.getDate() - 7 * w + d); if (day > t0) continue; const ds = iso(day);
    put('journals', { id: ds, pre: { bias: 'bullish', max_loss: '1000', max_trades: '3', setups: ['orb', 'vwap'], saved_at: 1 } });
    [['09:35', 'ORB', 1], ['10:40', 'VWAP', -1], ['11:15', 'ORB', 1]].forEach(([tm, st, sg], k) => {
      const bad = (w * 5 + d + k) % 10 < (w + 1) * 2 - 1;   // the stop broken often 4 weeks ago, rarely now
      put('trades', { id: 'w' + (++n), account_id: 'wa', instrument: 'NQ', direction: 'long', contracts: 1, entry: 1, exit: 2, pnl_c: sg * (st === 'ORB' ? 30000 : 15000), pnl_manual: true, date: ds, entry_time: tm, exit_time: tm.slice(0, 3) + '50', setup: st, discipline: { stop: bad ? 'n' : 'y' } });
    });
  }
  render(); return n; }"""
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

def live(p, lang, phone):   # brief 03 step 3: during the session
  tag = f"{'390' if phone else '1300'}-{lang}"; y = Y[lang]
  unthrottle()
  br = p.chromium.launch()
  ctx = br.new_context(viewport={'width': 390, 'height': 844} if phone else {'width': 1300, 'height': 850}, is_mobile=phone, has_touch=phone, locale={'fr': 'fr-CA', 'en': 'en-US', 'es': 'es-ES'}[lang])
  ctx.add_init_script("try { localStorage.setItem('tj.lang', JSON.stringify('%s')); localStorage.setItem('sw.installShown', '1'); sessionStorage.setItem('sw.modal', '1') } catch (e) {}" % lang)
  r = ctx.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': 'cl%d@t.dev' % int(time.time() * 1000), 'consent': True, 'elapsed': 6000}), headers=H)
  if r.status != 201: raise RuntimeError('sign-up refused: %s' % r.status)
  ctx.request.post(B + '/api/me/profile', data=json.dumps({'first_name': 'Léa', 'experience': 'gt1'}), headers=H)
  pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
  pg.goto(B + '/'); pg.wait_for_selector('form[data-onb]', timeout=20000); pg.wait_for_timeout(600)
  pg.evaluate(SEED); pg.wait_for_selector('#main .nav-dash', timeout=10000); pg.wait_for_timeout(700)
  early = pg.evaluate("(() => { const [h, m] = nowET().slice(11, 16).split(':').map(Number); return h * 60 + m < 70 })()")
  if early: print(f'      {tag}: just after midnight New York, the « minutes since the last loss » part is left out')
  # his history: 5 past days with a re-entry 3 min after a loss (losing), the rest winning
  pg.evaluate("""() => { const d0 = new Date(todayStr() + 'T12:00:00'); for (let k = 20; k < 25; k++) { const d = new Date(d0); d.setDate(d0.getDate() - k);
      const day = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
      [['h' + k + 'a', '10:00', '10:05', -3000], ['h' + k + 'b', '10:08', '10:15', -5000], ['h' + k + 'c', '11:00', '11:10', 8000]].forEach(([id, a, b, pnl]) => put('trades', { id, account_id: 'ca', instrument: 'NQ', direction: 'long', contracts: 1, entry: 1, exit: 2, pnl_c: pnl, pnl_manual: true, date: day, entry_time: a, exit_time: b })); } }""")
  # today: a plan, a win, then 2 losses, the last one 4 min ago
  pg.evaluate("""() => { const day = todayStr(), now = nowET().slice(11, 16), m = (d) => { let [h, mi] = now.split(':').map(Number); const x = Math.max(0, h * 60 + mi + d); return String(Math.floor(x / 60)).padStart(2, '0') + ':' + String(x % 60).padStart(2, '0'); };
      put('journals', { id: day, pre: { bias: 'bullish', max_loss: '2000', max_trades: '5', setups: [], saved_at: 1 } });
      [['t1', m(-60), m(-50), 20000], ['t2', m(-30), m(-20), -15000], ['t3', m(-12), m(-4), -10000]].forEach(([id, a, b, pnl]) => put('trades', { id, account_id: 'ca', instrument: 'NQ', direction: 'long', contracts: 1, entry: 1, exit: 2, pnl_c: pnl, pnl_manual: true, date: day, entry_time: a, exit_time: b })); render(); }""")
  pg.wait_for_timeout(900)
  # G. the two forms
  pg.evaluate("openTicket(null, { manual: true })"); pg.wait_for_selector('#tkSlide.open #tkAlerts', timeout=8000); pg.wait_for_timeout(600)
  man = pg.evaluate(TXT, '#tkSlide .co-before')
  pg.evaluate("closeTicket()"); pg.wait_for_timeout(500)
  pg.evaluate("SweepAddMode.open()"); pg.wait_for_selector('.nav-am-shot.open', timeout=8000); pg.wait_for_timeout(600)
  sh = pg.evaluate(TXT, '.nav-am-shot .co-before')
  if phone: pg.screenshot(path=f'/tmp/co_{tag}_shot_before.png')
  pg.keyboard.press('Escape'); pg.wait_for_timeout(400)
  for name, txt in (('manual', man), ('screenshot', sh)):
    ok(bool(txt) and y['left'] in txt and (early or (y['wait'] in txt and y['own'] in txt)), f'{tag} G the {name} form: « {txt[:110]}… »')
  # H. 80 % then 100 % of the daily limit (the account: $1,000)
  pg.evaluate("location.hash = '#dashboard'"); pg.wait_for_timeout(500)
  pg.evaluate(TRADE, ['t4', pg.evaluate("todayStr()"), '23:58', '23:59', 'long', -70000, {}]); pg.evaluate("toast('Trade saved')"); pg.wait_for_timeout(150)
  toast = pg.evaluate("document.getElementById('toast').textContent"); pg.evaluate("render()"); pg.wait_for_timeout(2600)
  card = pg.evaluate(TXT, '#main .co-lim')
  bell = [i.get('title_key') for i in ctx.request.get(B + '/api/notifications', headers=H).json().get('items', [])]
  ok(y['d75'] in toast and y['d75'] in card and bell.count('prop_dll75.title') == 1, f'{tag} H 80 %: the message, the card and the bell ({card[:60]}… {bell})')
  pg.evaluate(TRADE, ['t5', pg.evaluate("todayStr()"), '23:59', '23:59', 'long', -30000, {}]); pg.evaluate("render()"); pg.wait_for_timeout(2600)   # the day: −1,050 $
  card = pg.evaluate(TXT, '#main .co-lim'); pg.evaluate("render()"); pg.wait_for_timeout(1500)
  bell = [i.get('title_key') for i in ctx.request.get(B + '/api/notifications', headers=H).json().get('items', [])]
  ok(y['d100'] in card.lower() and bell.count('prop_dll100.title') == 1 and bell.count('prop_dll75.title') == 1, f'{tag} H 100 %: the card, the bell, each level once ({card[:70]}… {bell})')
  ok(not errs, f'{tag} G-H no page error ({errs[:2]})')
  br.close()

def works(p, lang, phone):   # brief 03 step 4: what works for you
  tag = f"{'390' if phone else '1300'}-{lang}"; z = Z[lang]
  unthrottle()
  br = p.chromium.launch()
  ctx = br.new_context(viewport={'width': 390, 'height': 844} if phone else {'width': 1300, 'height': 850}, is_mobile=phone, has_touch=phone, locale={'fr': 'fr-CA', 'en': 'en-US', 'es': 'es-ES'}[lang])
  ctx.add_init_script("try { localStorage.setItem('tj.lang', JSON.stringify('%s')); localStorage.setItem('sw.installShown', '1'); sessionStorage.setItem('sw.modal', '1') } catch (e) {}" % lang)
  r = ctx.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': 'cw%d@t.dev' % int(time.time() * 1000), 'consent': True, 'elapsed': 6000}), headers=H)
  if r.status != 201: raise RuntimeError('sign-up refused: %s' % r.status)
  ctx.request.post(B + '/api/me/profile', data=json.dumps({'first_name': 'Léa', 'experience': 'gt1'}), headers=H)
  pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
  pg.goto(B + '/'); pg.wait_for_selector('form[data-onb]', timeout=20000); pg.wait_for_timeout(600)
  n = pg.evaluate(HIST); pg.wait_for_timeout(900)
  pg.evaluate("location.hash = '#analytics'"); pg.wait_for_selector('#main .co-stats', timeout=10000); pg.wait_for_timeout(700)
  st = pg.evaluate(TXT, '#main .co-stats')
  first = pg.evaluate("(() => { const c = document.querySelector('#main .co-stats'), k = document.querySelector('#main .ikpis'); return !!(c && k && (c.compareDocumentPosition(k) & Node.DOCUMENT_POSITION_FOLLOWING)) })()")
  pr = pg.evaluate("SweepCoach.progress().map((h) => [h.key, h.first.pct, h.last.pct])")
  ok(z['title'] in st and z['strong'] in st and z['leak'] in st and z['rule'] in st and first, f'{tag} I Stats: « {z["title"]} » first, strength, leak, rule ({n} trades)')
  stop = next((x for x in pr if x[0] == 'no_stop'), None)
  ok(z['ago'] in st and stop and stop[1] < stop[2], f'{tag} I the stop week by week, going up ({stop})')
  if phone: pg.screenshot(path=f'/tmp/co_{tag}_stats.png')
  mon = pg.evaluate("(() => { const d = new Date(todayStr() + 'T12:00:00'); d.setDate(d.getDate() - ((d.getDay() + 6) % 7)); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}` })()")
  wk = pg.evaluate("(m) => { const d = document.createElement('div'); d.innerHTML = SweepCoach.weekHtml(m); return d.textContent }", mon)
  ok(wk and '$' not in wk and z['rule'] in wk, f'{tag} I the Friday recap: the coach in % and counts, no dollar ({wk[:80]}…)')
  ok(pg.evaluate("document.documentElement.scrollWidth - innerWidth") <= 0 and not errs, f'{tag} I nothing wider than the window, no page error ({errs[:2]})')
  br.close()

W5 = {'fr': ('Réponds au coach', 'Avancé'), 'en': ('Answer your coach', 'Advanced'), 'es': ('Responde a tu coach', 'Avanzado')}
def fewer(p, lang, phone):   # brief 03 step 5
  tag = f"{'390' if phone else '1300'}-{lang}"; w = W5[lang]
  unthrottle()
  br = p.chromium.launch()
  ctx = br.new_context(viewport={'width': 390, 'height': 844} if phone else {'width': 1300, 'height': 850}, is_mobile=phone, has_touch=phone, locale={'fr': 'fr-CA', 'en': 'en-US', 'es': 'es-ES'}[lang])
  ctx.add_init_script("try { localStorage.setItem('tj.lang', JSON.stringify('%s')); localStorage.setItem('sw.installShown', '1'); sessionStorage.setItem('sw.modal', '1') } catch (e) {}" % lang)
  r = ctx.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': 'cf%d@t.dev' % int(time.time() * 1000), 'consent': True, 'elapsed': 6000}), headers=H)
  if r.status != 201: raise RuntimeError('sign-up refused: %s' % r.status)
  ctx.request.post(B + '/api/me/profile', data=json.dumps({'first_name': 'Léa', 'experience': 'gt1'}), headers=H)
  pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
  pg.goto(B + '/'); pg.wait_for_selector('form[data-onb]', timeout=20000); pg.wait_for_timeout(600)
  pg.evaluate(SEED); pg.wait_for_selector('#main .nav-dash', timeout=10000); pg.wait_for_timeout(600)
  day = pg.evaluate("todayStr()")
  pg.evaluate(PLAN, [day, {'bias': 'bullish', 'max_loss': '1000', 'setups': []}])
  pg.evaluate(TRADE, ['f1', day, '10:00', '10:05', 'long', -20000, {}]); pg.evaluate(TRADE, ['f2', day, '10:08', '10:15', 'long', -10000, {}]); pg.evaluate("render()"); pg.wait_for_timeout(600)
  pg.evaluate("location.hash = '#trade/f2'"); pg.wait_for_selector('#main .co-ask', timeout=8000); pg.wait_for_timeout(500)
  ask = pg.evaluate(TXT, '#main .co-ask')
  ok(w[0] in ask and pg.evaluate("document.querySelector('#main .rprog').hidden && !document.querySelector('#main details.co-full').open") and pg.locator('#main .co-ask .co-q').count() == 3, f'{tag} J the trade page: « {w[0]} », 3 questions, the full review folded')
  pg.locator('#main .co-ask [data-path="discipline.plan"][data-v="y"]').click(); pg.wait_for_timeout(400)
  pg.locator('#main .co-ask [data-path="emo.before"]').first.click(); pg.wait_for_timeout(400)
  pg.locator('#main .co-ask textarea').fill('10 min'); pg.wait_for_timeout(1200)
  sv = pg.evaluate("(() => { const t = getDoc('trades', 'f2'); return [t.discipline && t.discipline.plan, ((t.emo || {}).before || []).length, (t.review || {}).lesson] })()")
  ok(sv == ['y', 1, '10 min'], f'{tag} J the answers in the same fields ({sv})')
  pg.locator('#main details.co-full > summary').click(); pg.wait_for_timeout(300); pg.locator('#main #rs-chk [data-act=set]').first.click(); pg.wait_for_timeout(600)
  ok(pg.evaluate("document.querySelector('#main details.co-full').open"), f'{tag} J the full review stays open after a tap in it')
  pg.evaluate("location.hash = '#dashboard'"); pg.wait_for_timeout(500); pg.evaluate("SweepAddMode.open()"); pg.wait_for_selector('.nav-am-shot.open', timeout=8000); pg.wait_for_timeout(400)
  q1 = pg.evaluate("[document.querySelectorAll('.nav-am-shot .nav-am-q').length, !!document.querySelector('.nav-am-shot .nav-am-scores')]")
  pg.keyboard.press('Escape'); pg.wait_for_timeout(400)
  pg.evaluate("openTicket(null, { manual: true })"); pg.wait_for_selector('#tkSlide.open', timeout=8000); pg.evaluate("showStep2('f1')"); pg.wait_for_timeout(400)
  q2 = pg.evaluate("document.querySelectorAll('#tkPanel .qlist .q').length"); pg.locator('#tkPanel [data-act=s2-more]').first.click(); pg.wait_for_timeout(400)
  q3 = pg.evaluate("document.querySelectorAll('#tkPanel .qlist .q').length"); pg.evaluate("closeStep2()"); pg.wait_for_timeout(400)
  ok(q1 == [3, False] and q2 == 3 and q3 > 3, f'{tag} J the forms: 3 questions, confidence folded ({q1}); step 2: 3, then {q3} after « More »')
  pg.evaluate("location.hash = '#settings'"); pg.wait_for_selector('#main details.nav-sgd', timeout=8000); pg.wait_for_timeout(500)
  g = pg.evaluate("[...document.querySelectorAll('#main details.nav-sgd')].map((d) => [d.querySelector('summary').textContent.trim(), d.open])")
  ok(g and g[-1] == [w[1], False], f'{tag} J Settings: « {w[1]} » last, folded ({g[-1] if g else None})')
  ok(pg.evaluate("document.documentElement.scrollWidth - innerWidth") <= 0 and not errs, f'{tag} J nothing wider than the window, no page error ({errs[:2]})')
  br.close()

with sync_playwright() as p:
  for lang, phone in (('fr', True), ('en', False), ('es', True)):
    print(f"— {'phone' if phone else 'computer'} {lang}")
    run(p, lang, phone)
    live(p, lang, phone)
    works(p, lang, phone)
    fewer(p, lang, phone)
print(f'{fails} failed' if fails else 'all passed')
sys.exit(1 if fails else 0)
