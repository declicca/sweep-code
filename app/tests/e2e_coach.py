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
Then, the audit of 16 Oct. (step 2), a LucidPro 50K ($2,000 drawdown, $1,200 daily limit) with $870 of drawdown room left:
  K. the plan's max loss starts at $870 (not $1,200), « Drawdown room of LucidPro 50K: $870 » under it; the coach before a
     trade says $870 left (a $1,200 plan typed anyway too); after a −$780 trade ($90 left): « Room: $90. Stop for today. » (after the trade, before the next
     one, on Today), and the rule for the next session « Max loss $90 or no trade ».
Then, the audit of 16 Oct. (step 5), a day with a trade against the bias and a trade saved without a time:
  L. the coach's card speaks of the most recent trade (by entry time, else by when it was saved), not of the one without a
     time; the last trade clean while an earlier one is against the bias: « Nothing to fix on this trade. Earlier today:
     trading against your bias. », never « Do exactly the same again »; no plan for the day: the routine says « 1 trade · no
     plan », not « 1 of 1 trades in your plan » (the server counts 0 in the plan too); what is left counts the whole session.
Then « Your edge » before the trade (brief edge T3, 17 Oct.): 12 ORB of the morning over the last 3 weeks, mostly winning,
  and losing afternoon trades:
  M. an ORB at 9:45: the blue line « In your edge: Opening range breakout, 10 winners out of 12. Keep your usual size. »,
     first in « Before this trade »; at 14:00 without a setup: a neutral « What works for you: … » (never « in your edge »);
     on the quick sheet, tapping « Opening range breakout » turns the line blue at once;
  N. (brief edge T4) Today before the session: « Keep doing what works: Opening range breakout (… over 12 trades) »; the
     plan sheet: « What works for you: … » under its title, « Opening range breakout » first among the trader's setups;
  O. (brief edge T5) 4 winners today between 9:30 and 10:00: « Your streak: 4 winners in a row. In common: 09:30–10:00. »
     on Today; Stats › Trading stats shows « Longest winning streak » and « Green days in a row »;
  P. (brief edge T6) the top of Stats and the Friday recap: « Your edge », the ORB « Trend » over 12 trades, no dollar.
  Q. (brief edge T7) « Answer your coach » follows the edge: a trade of today's streak « What put you in this streak? », an
     ORB of the morning « What was the same as usual? », an afternoon reversal « Why this trade off your edge? » (kept in review.edge).
  R. (brief edge T8) a lesson written on an ORB: « Your lesson of Oct 13 on Opening range breakout: … » before the next ORB,
     never before a reversal.
Checks: no page error, nothing wider than the window, the coach's texts in the trader's language.
"""
import json, os, re, sqlite3, sys, time
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
H = {'Content-Type': 'application/json', 'X-Requested-With': 'fetch'}
DB = os.environ.get('SWEEP_TEST_DB', '/tmp/g/data/journal.db')
fails = 0
def shot(pg):   # « New trade » shows its fields once a screenshot is there (18 Oct.): the test one, read as no table
    pg.route('**/api/ai/import', lambda r: r.fulfill(status=200, content_type='application/json', body='{"trades": []}'))
    pg.locator('.nav-am.open input[data-am-file]').first.set_input_files('tests/fixture-shot.png')
    pg.wait_for_selector('.nav-am.open .nav-am-grid', timeout=8000); pg.wait_for_timeout(300)
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
  # (15 Oct.) inside the routine card, between its figures and its 3 steps, its full width; it folds with the steps
  pl = pg.evaluate("(()=>{const c=document.querySelector('#main .co-today'), rt=c&&c.closest('.nav-rt'); if(!rt) return null; const n=c.nextElementSibling; return [!!n&&n.classList.contains('nav-rt-steps'), Math.abs(c.getBoundingClientRect().width-n.getBoundingClientRect().width)<=2]})()")
  ok(pl == [True, True], f'{tag} Today: the coach is in the routine card, above the 3 steps, as wide as them ({pl})')
  pg.locator('#main .nav-rt-fold').click(); pg.wait_for_timeout(500)
  fd = pg.evaluate("getComputedStyle(document.querySelector('#main .co-today')).display")
  pg.locator('#main .nav-rt-fold').click(); pg.wait_for_timeout(500)
  ok(fd == 'none' and pg.locator('#main .co-today').is_visible(), f'{tag} Today: folding the routine hides the coach with the steps, unfolding shows it ({fd})')
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
  pg.evaluate("SweepAddMode.open()"); pg.wait_for_selector('.nav-am-shot.open', timeout=8000); pg.wait_for_timeout(600); shot(pg)
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

ES = {'fr': ('Ta série : 4 gagnants de suite.', 'Point commun : ', 'Plus longue série gagnante', 'Jours verts de suite'), 'en': ('Your streak: 4 winners in a row.', 'In common: ', 'Longest winning streak', 'Green days in a row'),
      'es': ('Tu racha: 4 ganadoras seguidas.', 'En común: ', 'Racha ganadora más larga', 'Días en verde seguidos')}
EL = {'fr': 'Ta leçon du ', 'en': 'Your lesson of ', 'es': 'Tu lección del '}
EQ = {'fr': ('Qu’est-ce qui était pareil que d’habitude ?', 'Pourquoi ce trade hors de ton edge ?', 'Qu’est-ce qui t’a mis dans cette série ?'), 'en': ('What was the same as usual?', 'Why this trade off your edge?', 'What put you in this streak?'),
      'es': ('¿Qué fue igual que de costumbre?', '¿Por qué esta operación fuera de tu edge?', '¿Qué te puso en esta racha?')}
EV = {'fr': ('Ton edge', 'Tendance'), 'en': ('Your edge', 'Trend'), 'es': ('Tu edge', 'Tendencia')}
EK = {'fr': 'Continue ce qui marche : Opening range breakout', 'en': 'Keep doing what works: Opening range breakout', 'es': 'Sigue con lo que funciona: Opening range breakout'}
EG = {'fr': ('Dans ton edge : Opening range breakout, 10 gagnants sur 12', 'Ce qui marche pour toi : Opening range breakout'),
      'en': ('In your edge: Opening range breakout, 10 winners out of 12', 'What works for you: Opening range breakout'),
      'es': ('En tu edge: Opening range breakout, 10 ganadoras de 12', 'Lo que te funciona: Opening range breakout')}
def edge_case(p, lang, phone):   # brief edge T3: « Your edge » before the trade
  tag = f"{'390' if phone else '1300'}-{lang} edge"; e = EG[lang]
  unthrottle()
  br = p.chromium.launch()
  ctx = br.new_context(viewport={'width': 390, 'height': 844} if phone else {'width': 1300, 'height': 850}, is_mobile=phone, has_touch=phone, locale={'fr': 'fr-CA', 'en': 'en-US', 'es': 'es-ES'}[lang])
  ctx.add_init_script("try { localStorage.setItem('tj.lang', JSON.stringify('%s')); localStorage.setItem('sw.installShown', '1'); sessionStorage.setItem('sw.modal', '1') } catch (e) {}" % lang)
  r = ctx.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': 'ce%d@t.dev' % int(time.time() * 1000), 'consent': True, 'elapsed': 6000}), headers=H)
  if r.status != 201: raise RuntimeError('sign-up refused: %s' % r.status)
  ctx.request.post(B + '/api/me/profile', data=json.dumps({'first_name': 'Eli', 'experience': 'gt1'}), headers=H)
  pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e2: errs.append(str(e2)[:160]))
  pg.goto(B + '/'); pg.wait_for_selector('form[data-onb]', timeout=20000); pg.wait_for_timeout(600)
  pg.evaluate(SEED); pg.wait_for_selector('#main .nav-dash', timeout=10000); pg.wait_for_timeout(900)
  day = pg.evaluate("(SweepGame.state() && SweepGame.state().today && SweepGame.state().today.day) || todayStr()")
  pg.evaluate("""(day) => { const back = (k) => { const d = new Date(day + 'T12:00:00Z'); d.setUTCDate(d.getUTCDate() - k); return d.toISOString().slice(0, 10); };
    [1, 2, 3, 4, 5, 8, 9, 10, 11, 12, 15, 16].forEach((k, i) => {
      put('trades', { id: 'eo' + k, account_id: 'ca', instrument: 'NQ', direction: 'long', contracts: 1, entry: 1, exit: 2, pnl_c: i % 6 === 5 ? -10000 : 25000, pnl_manual: true, date: back(k), entry_time: '09:45:00', exit_time: '09:55:00', setup: 'Opening range breakout' });
      put('trades', { id: 'ea' + k, account_id: 'ca', instrument: 'NQ', direction: 'long', contracts: 1, entry: 1, exit: 2, pnl_c: -6000, pnl_manual: true, date: back(k), entry_time: '14:05:00', exit_time: '14:20:00', setup: 'Reversal' }); }); }""", day)
  pg.wait_for_timeout(1500)
  txt = "(h) => { const e = document.createElement('div'); e.innerHTML = h; const q = e.querySelector('.co-edge'); return { all: e.textContent.replace(/\\s+/g, ' '), edge: q ? q.textContent : '', blue: !!(q && q.classList.contains('in')), first: !!(q && q === e.querySelector('p')) } }"
  inn = pg.evaluate("([d, f]) => (new Function('return ' + f))()(SweepCoach.before({ form: 'shot', account: 'ca', date: d, qty: 1, time: '09:45', setup: 'Opening range breakout', dir: 'long', inst: 'NQ' }))", [day, txt])
  ok(e[0] in inn['edge'] and inn['blue'] and inn['first'], f'{tag} M an ORB at 9:45: « {e[0]}… », in blue, first ({inn["edge"][:110]})')
  out = pg.evaluate("([d, f]) => (new Function('return ' + f))()(SweepCoach.before({ form: 'shot', account: 'ca', date: d, qty: 1, time: '14:00', setup: '', dir: 'long', inst: 'NQ' }))", [day, txt])
  ok(e[1] in out['edge'] and not out['blue'] and e[0][:8] not in out['edge'], f'{tag} M at 14:00 without a setup: neutral « {e[1]}… » ({out["edge"][:110]})')
  pg.evaluate("openTicket(null)"); pg.wait_for_selector('.nav-am.open', timeout=8000); shot(pg); pg.wait_for_selector('.nav-am.open .nav-sp', timeout=8000); pg.wait_for_timeout(500)
  pg.locator('.nav-am [data-am-seg="dir"][data-v="long"]').click(); pg.wait_for_timeout(300)
  b0 = pg.evaluate("!!document.querySelector('.nav-am .co-edge.in')")
  pg.locator('.nav-am [data-sp="Opening range breakout"]').click(); pg.wait_for_timeout(300)
  b1 = pg.evaluate("(() => { const q = document.querySelector('.nav-am .co-edge'); return q ? [q.classList.contains('in'), q.textContent] : null })()")
  ok(b1 and (b1[0] or not b0), f'{tag} M the quick sheet: the line follows the setup tapped ({b0} → {b1})')
  # N. (T4) Today before the session, then the plan sheet
  pg.evaluate("document.querySelector('.nav-am [data-am=close]') && document.querySelector('.nav-am [data-am=close]').click()"); pg.wait_for_timeout(500)
  pg.evaluate("editDoc('settings', 'settings', (d) => { d.setups = ['Reversal', 'VWAP reclaim', 'Opening range breakout']; })"); pg.wait_for_timeout(500)
  pg.evaluate("location.hash = '#dashboard'; render()"); pg.wait_for_selector('#main .co-today', timeout=8000); pg.wait_for_timeout(1200)
  kt = pg.evaluate("(() => { const q = document.querySelector('#main .co-today .co-edge'); return q ? q.textContent : '' })()")
  ok(EK[lang] in kt and '12' in kt, f'{tag} N Today before the session: « {EK[lang]}… » ({kt[:110]})')
  pg.evaluate("(d) => SweepGame.openPlan(d)", day); pg.wait_for_selector('#gSheet .g-setups', state='attached', timeout=8000); pg.wait_for_timeout(600)
  pl = pg.evaluate("(() => { const q = document.querySelector('#gSheet .g-edge'); return { line: q ? q.textContent : '', first: ((document.querySelector('#gSheet .g-setups [data-g=setup]') || {}).dataset || {}).v || '' } })()")
  ok(e[1] in pl['line'] and pl['first'] == 'Opening range breakout', f'{tag} N the plan: « {e[1]}… », the ORB first among the setups ({pl})')
  if phone: pg.screenshot(path=f'/tmp/co_{tag}_plan.png')
  ok(pg.evaluate("document.documentElement.scrollWidth - innerWidth") <= 0, f'{tag} N nothing wider than the window')
  # O. (T5) 4 winners today, all between 9:30 and 10:00: the streak and its point in common; Stats: the longest streak
  pg.evaluate("""(day) => ['09:35', '09:40', '09:50', '09:55'].forEach((hm, i) => put('trades', { id: 'es' + i, account_id: 'ca', instrument: 'NQ', direction: 'long', contracts: 1, entry: 1, exit: 2, pnl_c: 8000, pnl_manual: true, date: day, entry_time: hm + ':00', exit_time: hm + ':30' }))""", day)
  pg.wait_for_timeout(1500); pg.evaluate("location.hash = '#dashboard'; render()"); pg.wait_for_selector('#main .co-today', timeout=8000); pg.wait_for_timeout(1200)
  sk = pg.evaluate("(() => [...document.querySelectorAll('#main .co-today .co-edge')].map((q) => q.textContent).join(' | '))()")
  slot = pg.evaluate("SweepEdge.words({ dims: [['slot', '09:30']] })")
  ok(ES[lang][0] in sk and (ES[lang][1] + slot) in sk, f'{tag} O 4 winners before 10:00: « {ES[lang][0]} … {ES[lang][1]}{slot} » ({sk[:140]})')
  pg.evaluate("location.hash = '#analytics'"); pg.wait_for_selector('#main .g-ins .tiles', state='attached', timeout=10000); pg.wait_for_timeout(800)
  mt = pg.evaluate("(document.querySelector('#main .g-ins .tiles') || {}).textContent || ''")
  ok(ES[lang][2] in mt and ES[lang][3] in mt, f'{tag} O Stats › Trading stats: « {ES[lang][2]} » ({mt[mt.find(ES[lang][2][:6]):][:60] if ES[lang][2][:6] in mt else mt[:80]})')
  # P. (T6) the profile's card: Stats (top) and the Friday recap, in counts and %
  pg.wait_for_selector('#main .co-stats', state='attached', timeout=10000); pg.wait_for_timeout(500)
  sc = pg.evaluate("(document.querySelector('#main .co-stats .co-edgecard') || {}).textContent || ''")
  ok(EV[lang][0] in sc and EV[lang][1] in sc and 'Opening range breakout' in sc and '12' in sc, f'{tag} P Stats: « {EV[lang][0]} », the ORB « {EV[lang][1]} » over 12 trades ({sc[:120]})')
  mon = pg.evaluate("(() => { const d = new Date(todayStr() + 'T12:00:00'); d.setDate(d.getDate() - ((d.getDay() + 6) % 7)); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}` })()")
  wk = pg.evaluate("(m) => { const d = document.createElement('div'); d.innerHTML = SweepCoach.weekHtml(m); const c = d.querySelector('.co-edgecard'); return [c ? c.textContent : '', d.textContent] }", mon)
  ok(EV[lang][0] in wk[0] and '$' not in wk[1], f'{tag} P the Friday recap: the same card, no dollar ({wk[0][:90]})')
  ok(pg.evaluate("document.documentElement.scrollWidth - innerWidth") <= 0, f'{tag} P nothing wider than the window')
  if phone: pg.screenshot(path=f'/tmp/co_{tag}_edgecard.png')
  # Q. (T7) « Answer your coach » follows the edge: a trade of the streak, an ORB of the morning, an afternoon reversal
  qs = {}
  for tid in ('es1', 'eo2', 'ea2'):
    pg.evaluate(f"location.hash = '#trade/{tid}'"); pg.wait_for_selector('#main .co-ask', timeout=8000); pg.wait_for_timeout(500)
    qs[tid] = pg.evaluate(TXT, '#main .co-ask')
  ok(EQ[lang][2] in qs['es1'] and EQ[lang][0] in qs['eo2'] and EQ[lang][1] in qs['ea2'], f'{tag} Q the review question: the streak, in the edge, off the edge ({[v[:60] for v in qs.values()]})')
  pg.locator('#main .co-ask textarea[data-bind$="review.edge"]').fill('Same 15-min range, same size'); pg.locator('#main .co-ask textarea[data-bind$="review.edge"]').blur(); pg.wait_for_timeout(900)
  ok(pg.evaluate("(getDoc('trades', 'ea2').review || {}).edge") == 'Same 15-min range, same size', f'{tag} Q the answer is kept in the trade (review.edge)')
  # R. (T8) a lesson written on an ORB comes back before the next ORB, not before another setup
  pg.evaluate("editDoc('trades', 'eo3', (d) => { d.review = Object.assign({}, d.review || {}, { lesson: 'Wait for the candle to close' }); })"); pg.wait_for_timeout(900)
  lo = pg.evaluate("(d) => { const e = document.createElement('div'); e.innerHTML = SweepCoach.before({ form: 'shot', account: 'ca', date: d, qty: 1, time: '09:45', setup: 'Opening range breakout', dir: 'long', inst: 'NQ' }); const q = e.querySelector('.co-lesson'); return q ? q.textContent : '' }", day)
  lr = pg.evaluate("(d) => { const e = document.createElement('div'); e.innerHTML = SweepCoach.before({ form: 'shot', account: 'ca', date: d, qty: 1, time: '09:45', setup: 'Reversal', dir: 'long', inst: 'NQ' }); return e.textContent }", day)
  ok(EL[lang] in lo and 'Opening range breakout' in lo and 'Wait for the candle to close' in lo and 'Wait for the candle' not in lr, f'{tag} R the ORB lesson before an ORB ({lo[:100]}), not before a reversal')
  ok(pg.evaluate("document.documentElement.scrollWidth - innerWidth") <= 0 and not errs, f'{tag} M nothing wider than the window, no page error ({errs[:2]})')
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
  pg.evaluate("location.hash = '#dashboard'"); pg.wait_for_timeout(500); pg.evaluate("SweepAddMode.open()"); pg.wait_for_selector('.nav-am-shot.open', timeout=8000); pg.wait_for_timeout(400); shot(pg)
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

R = {'fr': {'hint': 'Marge de drawdown de LucidPro 50K', 'left': 'de marge de drawdown sur LucidPro 50K', 'stop': 'Arrête pour aujourd’hui', 'rule': 'Perte max 90'},
     'en': {'hint': 'Drawdown room of LucidPro 50K', 'left': 'of drawdown room left on LucidPro 50K', 'stop': 'Stop for today', 'rule': 'Max loss $90'},
     'es': {'hint': 'Margen de drawdown de LucidPro 50K', 'left': 'de margen de drawdown en LucidPro 50K', 'stop': 'Para por hoy', 'rule': 'Pérdida máxima 90'}}
def room(p, lang, phone):
  tag = f"{'390' if phone else '1300'}-{lang} room"; x = R[lang]
  unthrottle()
  br = p.chromium.launch()
  ctx = br.new_context(viewport={'width': 390, 'height': 844} if phone else {'width': 1300, 'height': 850}, is_mobile=phone, has_touch=phone, locale={'fr': 'fr-CA', 'en': 'en-US', 'es': 'es-ES'}[lang])
  ctx.add_init_script("try { localStorage.setItem('tj.lang', JSON.stringify('%s')); localStorage.setItem('sw.installShown', '1'); sessionStorage.setItem('sw.modal', '1') } catch (e) {}" % lang)
  r = ctx.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': 'cr%d@t.dev' % int(time.time() * 1000), 'consent': True, 'elapsed': 6000}), headers=H)
  if r.status != 201: raise RuntimeError('sign-up refused: %s' % r.status)
  ctx.request.post(B + '/api/me/profile', data=json.dumps({'first_name': 'Alex', 'experience': 'gt1'}), headers=H)
  pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
  pg.goto(B + '/'); pg.wait_for_selector('form[data-onb]', timeout=20000); pg.wait_for_timeout(600)
  pg.evaluate("""() => { put('firms', { id: 'lf', name: 'Lucid Trading' }); put('accounts', { id: 'la', firm_id: 'lf', name: 'LucidPro 50K', starting_balance_c: 5000000, status: 'active', created_on: '2026-09-01', rules: { dll_c: 120000, dd_c: 200000, dd_type: 'static' } }); render(); }""")
  pg.wait_for_selector('#main .nav-dash', timeout=10000); pg.wait_for_timeout(900)
  for _ in range(30):
    day = pg.evaluate("(SweepGame.state() && SweepGame.state().today && SweepGame.state().today.day) || ''")
    if day: break
    pg.wait_for_timeout(300)
  day = day or pg.evaluate("todayStr()")
  # $1,130 lost the session before: $870 of room left
  pg.evaluate("(d) => put('trades', { id: 'r0', account_id: 'la', instrument: 'NQ', direction: 'long', contracts: 1, entry: 1, exit: 2, pnl_c: -113000, pnl_manual: true, date: ymdAdd(d, -1), entry_time: '10:00', exit_time: '10:20' })", day); pg.wait_for_timeout(800)
  m = pg.evaluate("(d) => { const m = SweepCoach.margin(d); return m && [m.c, m.start, m.low] }", day)
  ok(m == [87000, 87000, False], f'{tag} the room is the account page\'s: $870 ({m})')
  pg.evaluate("(d) => SweepGame.openPlan(d)", day); pg.wait_for_selector('#gSheet [data-g=save-plan]', timeout=8000); pg.wait_for_timeout(400)
  ml = pg.evaluate("(document.querySelector('#gSheet [data-gp=max_loss]') || {}).value"); hint = pg.evaluate(TXT, '#gSheet .g-dll')
  ok(ml == '870' and x['hint'] in hint and '870' in hint, f'{tag} the plan\'s max loss starts at the room, not the $1,200 daily limit ({ml}, « {hint} »)')
  # he types $1,200 anyway: the coach still counts the room
  pg.locator('#gSheet [data-g=bias][data-v=bullish]').click(); pg.wait_for_timeout(200); pg.locator('#gSheet [data-gp=max_loss]').fill('1200'); pg.locator('#gSheet [data-g=save-plan]').click(); pg.wait_for_timeout(900)
  b1 = pg.evaluate("(d) => { const h = SweepCoach.before({ form: 'shot', account: 'la', date: d, qty: 1 }); const e = document.createElement('div'); e.innerHTML = h; return e.textContent.replace(/\\s+/g, ' ') }", day)
  ok('870' in b1 and x['left'] in b1, f'{tag} a $1,200 plan, before a trade: $870 of room left, not $1,200 ({b1[:120]})')
  # −$780 today: $90 left
  pg.evaluate("(d) => put('trades', { id: 'r1', account_id: 'la', instrument: 'NQ', direction: 'long', contracts: 1, entry: 1, exit: 2, pnl_c: -78000, pnl_manual: true, date: d, entry_time: '10:00', exit_time: '10:15' })", day); pg.wait_for_timeout(900)
  ses = pg.evaluate("() => { const c = SweepCoach.trade(getDoc('trades', 'r1')); return c && c.ses }")
  ok(ses and ses['stop'] and x['stop'] in ses['t'] and '90' in ses['t'], f'{tag} after the trade (« saved », the trade\'s page): {ses and ses["t"]}')
  b2 = pg.evaluate("(d) => { const h = SweepCoach.before({ form: 'shot', account: 'la', date: d, qty: 1 }); const e = document.createElement('div'); e.innerHTML = h; return e.textContent.replace(/\\s+/g, ' ') }", day)
  ok(x['stop'] in b2 and '90' in b2 and '870' not in b2, f'{tag} before the next trade: {b2[:110]}')
  rule = pg.evaluate("(d) => SweepCoach.lesson(d).rule", day)
  ok(rule.startswith(x['rule']), f'{tag} the rule for the next session: « {rule} »')
  pg.evaluate("location.hash = '#dashboard'; render()"); pg.wait_for_selector('#main .co-today', timeout=8000); pg.wait_for_timeout(900)
  td = pg.evaluate(TXT, '#main .co-today')
  ok(x['stop'] in td, f'{tag} Today: the coach says to stop ({td[:120]})')
  ok(pg.evaluate("document.documentElement.scrollWidth - innerWidth") <= 0, f'{tag} nothing wider than the window')
  ok(not errs, f'{tag} no page error ({errs[:2]})')
  br.close()

LT = {'fr': {'fix': 'À l’inverse de ton biais', 'earlier': 'Plus tôt aujourd’hui : trader contre ton biais', 'same': 'Refais exactement pareil', 'last': 'Dernier trade · ', 'noplan': '1 trade · pas de plan'},
      'en': {'fix': 'Against your bias', 'earlier': 'Earlier today: trading against your bias', 'same': 'Do exactly the same again', 'last': 'Last trade · ', 'noplan': '1 trade · no plan'},
      'es': {'fix': 'Contra tu sesgo', 'earlier': 'Antes, hoy:', 'same': 'Repite exactamente lo mismo', 'last': 'Última operación · ', 'noplan': '1 operación · sin plan'}}
def latest_case(p, lang, phone):
  from datetime import datetime
  from zoneinfo import ZoneInfo
  tag = f"{'390' if phone else '1300'}-{lang} latest"; x = LT[lang]
  unthrottle()
  br = p.chromium.launch()
  ctx = br.new_context(viewport={'width': 390, 'height': 844} if phone else {'width': 1300, 'height': 850}, is_mobile=phone, has_touch=phone, locale={'fr': 'fr-CA', 'en': 'en-US', 'es': 'es-ES'}[lang])
  ctx.add_init_script("try { localStorage.setItem('tj.lang', JSON.stringify('%s')); localStorage.setItem('sw.installShown', '1'); sessionStorage.setItem('sw.modal', '1') } catch (e) {}" % lang)
  r = ctx.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': 'cl%d@t.dev' % int(time.time() * 1000), 'consent': True, 'elapsed': 6000}), headers=H)
  if r.status != 201: raise RuntimeError('sign-up refused: %s' % r.status)
  ctx.request.post(B + '/api/me/profile', data=json.dumps({'first_name': 'Alex', 'experience': 'gt1'}), headers=H)
  pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
  pg.goto(B + '/'); pg.wait_for_selector('form[data-onb]', timeout=20000); pg.wait_for_timeout(600)
  pg.evaluate(SEED); pg.wait_for_selector('#main .nav-dash', timeout=10000); pg.wait_for_timeout(900)
  for _ in range(30):
    day = pg.evaluate("(SweepGame.state() && SweepGame.state().today && SweepGame.state().today.day) || ''")
    if day: break
    pg.wait_for_timeout(300)
  day = day or pg.evaluate("todayStr()")
  at = lambda hm: datetime.strptime(f'{day} {hm}', '%Y-%m-%d %H:%M').replace(tzinfo=ZoneInfo('America/New_York')).astimezone(ZoneInfo('UTC')).strftime('%Y-%m-%dT%H:%M:%S.000Z')
  card = lambda: pg.evaluate(TXT, '#main .co-today')
  # no plan: one clean trade → the routine says « 1 trade · no plan »
  pg.evaluate(TRADE, ['l1', day, '10:00', '10:10', 'long', 12000, {'created_at': at('10:11')}]); pg.wait_for_timeout(2500)
  pg.evaluate("location.hash = '#dashboard'; render()"); pg.wait_for_selector('#main .nav-rt', timeout=8000); pg.wait_for_timeout(1500)
  rt = pg.evaluate(TXT, '#main .nav-rt')
  ok(x['noplan'] in rt, f'{tag} no plan: the routine says « {x["noplan"]} » ({rt[:140]})')
  # a bullish plan; a short (against the bias) at 10:30, then a trade saved at 10:45 without a time
  pg.evaluate(PLAN, [day, {'bias': 'bullish', 'max_loss': '1000'}])
  pg.evaluate(TRADE, ['l2', day, '10:30', '10:40', 'short', -30000, {'created_at': at('10:41')}])
  pg.evaluate(TRADE, ['l3', day, '', '', 'long', -10000, {'created_at': at('09:45'), 'entry': None, 'exit': None}]); pg.wait_for_timeout(1500)
  pg.evaluate("location.hash = '#dashboard'; render()"); pg.wait_for_selector('#main .co-today', timeout=8000); pg.wait_for_timeout(1200)
  c1 = card()
  ok((x['last'] + '10:30') in c1 and x['fix'] in c1 and x['same'] not in c1, f'{tag} the last trade is the 10:30 short, not the one without a time: {c1[:140]}')
  # the trade without a time saved at 11:15: now the most recent, clean; the 10:30 short is still a mistake of the day
  pg.evaluate("(at) => editDoc('trades', 'l3', (d) => { d.created_at = at; d.direction = 'long'; })", at('11:15')); pg.wait_for_timeout(1200)
  pg.evaluate("location.hash = '#dashboard'; render()"); pg.wait_for_timeout(1200)
  c2 = card()
  ok((x['last'] + '11:15') in c2 and x['earlier'] in c2 and x['same'] not in c2, f'{tag} the last trade clean, the short earlier: never « nothing to fix, do the same »: {c2[:160]}')
  left = pg.evaluate("money(72000, { sign: false, dec: 0 })").replace('\u00a0', ' ').replace('\u202f', ' ')
  ok(left in c2.replace('\u00a0', ' ').replace('\u202f', ' '), f'{tag} what is left counts the whole session: {left} ($1,000 − $280)')
  ok(not errs, f'{tag} no page error ({errs[:2]})')
  br.close()

with sync_playwright() as p:
  for lang, phone in (('fr', True), ('en', False), ('es', True)):
    print(f"— {'phone' if phone else 'computer'} {lang}")
    run(p, lang, phone)
    live(p, lang, phone)
    works(p, lang, phone)
    fewer(p, lang, phone)
    room(p, lang, phone)
    latest_case(p, lang, phone)
    edge_case(p, lang, phone)
print(f'{fails} failed' if fails else 'all passed')
sys.exit(1 if fails else 0)
