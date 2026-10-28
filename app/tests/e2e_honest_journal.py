"""
Sweep — what forgotten losses distort, and a logged loss rewarded (brief « pertes oubliées », steps 3 and 4, 28 Oct.), Playwright:
  python3 tests/e2e_honest_journal.py http://127.0.0.1:8095
A trader of its own, a Topstep 50K evaluation; phone 390 (fr, touch), computer 1300 (en), phone 390 (es).
 3a a « Trades not detailed » line: Stats and the account page say it in a grey line (« 340 $ non détaillés… Ajouter le détail › »,
    never gold); Stats' win rate leaves it out; once detailed, the line goes away
 3b the coach, the first gap: « Ton journal disait qu'il te restait … Ta plateforme dit … », once (a second gap says nothing more)
 4a a day closed on the platform's balance counts (« Jours complets »); a day reviewed without it does not
 4b the coach after a loss in the plan, stop respected: « Perte dans ton plan, stop respecté : c'est un bon trade. »
 4c the form, a loss typed: checklist and emotions folded under « + Ajouter le contexte (facultatif) »; a loss in as many taps as a win
 4d the badge « Journal honnête » on the 5th day in a row the platform and the journal agree
No page error, nothing wider than the window.
"""
import json, os, random, sqlite3, sys, time
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
H = {'Content-Type': 'application/json', 'X-Requested-With': 'fetch'}
DB = os.environ.get('SWEEP_TEST_DB', '/tmp/g/data/journal.db')
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)
X = {'fr': {'note': 'non détaillés : ton taux de réussite et ta force/fuite ne les comptent pas.', 'detail': 'Ajouter le détail', 'coach': 'Ton journal disait qu’il te restait', 'plat': 'Ta plateforme dit', 'good': 'Perte dans ton plan, stop respecté : c’est un bon trade.', 'ctx': '+ Ajouter le contexte (facultatif)', 'days': 'Jours complets'},
     'en': {'note': 'not detailed: your win rate and your edge and leak don’t count them.', 'detail': 'Add the detail', 'coach': 'Your journal said you had', 'plat': 'Your platform says', 'good': 'A loss within your plan, stop respected: that’s a good trade.', 'ctx': '+ Add context (optional)', 'days': 'Complete days'},
     'es': {'note': 'sin detallar: tu tasa de acierto y tu fuerza/fuga no los cuentan.', 'detail': 'Añadir el detalle', 'coach': 'Tu diario decía que te quedaban', 'plat': 'Tu plataforma dice', 'good': 'Pérdida dentro de tu plan, stop respetado: es una buena operación.', 'ctx': '+ Añadir el contexto (opcional)', 'days': 'Días completos'}}
ACC = "([id, name]) => put('accounts', { id, name, status: 'active', phase: 'eval', starting_balance_c: 5000000, created_on: '2026-09-01', rules: { dd_c: 200000, dd_type: 'eod', dll_c: 100000, target_c: 300000 } })"
TRADE = "([id, acc, d, c, more]) => put('trades', Object.assign({ id, account_id: acc, instrument: 'MNQ', direction: 'long', contracts: 1, entry: 1, exit: 2, pnl_c: c, pnl_manual: true, date: d, entry_time: '10:00', exit_time: '10:05', discipline: { plan: 'y', stop: 'y' } }, more || {}))"
FLUSH = "Promise.all(Object.values(chains)).then(() => true)"
def ymd_back(day, n):   # n market days before
  t = time.mktime(time.strptime(day, '%Y-%m-%d')) + 43200; out = []
  while len(out) < n:
    t -= 86400; d = time.localtime(t)
    if d.tm_wday < 5: out.append(time.strftime('%Y-%m-%d', d))
  return out
with sync_playwright() as p:
  br = p.chromium.launch(); errs = []
  for lang, phone in (('fr', True), ('en', False), ('es', True)):
    w = 390 if phone else 1300; tag = f'{w}-{lang}'; x = X[lang]
    try: d = sqlite3.connect(DB); d.execute('DELETE FROM attempts'); d.commit(); d.close()
    except Exception: pass
    ctx = br.new_context(viewport={'width': w, 'height': 844 if phone else 850}, is_mobile=phone, has_touch=phone, locale={'fr': 'fr-CA', 'en': 'en-US', 'es': 'es-ES'}[lang])
    ctx.add_init_script("try { localStorage.setItem('tj.lang', JSON.stringify('%s')); sessionStorage.setItem('sw.modal', '1') } catch (e) {}" % lang)
    r = ctx.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': 'hj%06d@t.dev' % random.randint(0, 999999), 'consent': True, 'elapsed': 6000}), headers=H)
    if r.status != 201: raise RuntimeError('sign-up refused: %s' % r.status)
    ctx.request.post(B + '/api/me/profile', data=json.dumps({'first_name': 'Léa', 'experience': 'gt1'}), headers=H)
    pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
    SWC = "document.querySelectorAll('.g-sweep [data-g=sw-close]').forEach((b) => b.click())"
    def tap(l):
      pg.evaluate(SWC); l.tap() if phone else l.click()
    pg.goto(B + '/#dashboard'); pg.wait_for_timeout(2500)
    day = pg.evaluate("todayStr()")
    pg.evaluate(ACC, ['hj-a', 'Topstep 50K'])
    pg.evaluate("(d) => put('journals', { id: d, pre: { bias: 'bullish', max_loss: '1500', max_trades: '5', saved_at: Math.floor(Date.now() / 1000) - 3600 } })", day)
    pg.evaluate(TRADE, ['hj-t1', 'hj-a', day, 15000, None]); pg.evaluate(TRADE, ['hj-t0', 'hj-a', day, -5000, {'entry_time': '09:40', 'exit_time': '09:45'}])
    pg.evaluate(FLUSH); pg.evaluate("SweepGame.refresh()"); pg.wait_for_timeout(2500)
    # 4b. a loss in the plan, the stop respected
    gl = pg.evaluate("(() => { const c = SweepCoach.trade(getDoc('trades', 'hj-t0')); return [c.goodLoss, !c.fix] })()")
    pg.evaluate("location.hash = '#trade/hj-t0'"); pg.wait_for_timeout(1500)
    ok(gl == [True, True] and x['good'] in pg.evaluate("document.getElementById('main').innerText"), f'4b {tag}: « {x["good"]} » ({gl})')
    # 4a/3. close the day: the platform says −$190 for the day (+$150 −$50 logged): « Trades I didn't log »
    pg.evaluate("location.hash = '#dashboard'"); pg.wait_for_timeout(1200)
    pg.evaluate("(d) => SweepGame.openReview(d)", day); pg.wait_for_selector('#gSheet [data-bal-in]', timeout=8000); pg.wait_for_timeout(500)
    for k in ('r-followed', 'r-score', 'r-grade'):
      if not pg.locator(f'#gSheet [data-g={k}].on').count(): tap(pg.locator(f'#gSheet [data-g={k}]').first); pg.wait_for_timeout(150)
    pg.locator('#gSheet [data-bal-in="hj-a"]').fill('49810.00'); pg.wait_for_timeout(250)
    tap(pg.locator('#gSheet [data-bal-k=trades]')); pg.wait_for_timeout(150)
    tap(pg.locator('#gSheet [data-g=save-review]')); pg.wait_for_timeout(1500)
    gc = pg.evaluate("S.settings.gap_coach || null")
    ok(gc and gc['day'] == day and gc['before_c'] - gc['after_c'] == 29000, f'3b {tag}: the first gap kept for the coach: left before and after ({gc})')
    pg.evaluate(FLUSH); pg.evaluate("SweepGame.refresh()"); pg.wait_for_timeout(2500); pg.evaluate("render()"); pg.wait_for_timeout(1200)
    co = pg.evaluate("(document.querySelector('#main .co-today .co-gap') || {}).textContent || ''")
    if os.environ.get('SWEEP_SHOTS') and pg.locator('#main .co-today').count(): pg.evaluate(SWC); pg.wait_for_timeout(600); pg.locator('#main .co-today').screenshot(path=os.path.join(os.environ['SWEEP_SHOTS'], f'honest-coach-{tag}.png'))
    ok(x['coach'] in co and x['plat'] in co, f'3b {tag}: the coach says it on Today ({co[:90]!r})')
    st = pg.evaluate("(() => { const s = SweepGame.state(); return s && s.today ? [s.today.valid, s.today.review_done] : null })()")
    ok(st == [True, True], f'4a {tag}: a day closed on the platform\'s balance counts for the streak ({st})')
    # 3a. the grey line on Stats and on the account page
    pg.evaluate("location.hash = '#analytics'"); pg.wait_for_timeout(1800)
    nt = pg.evaluate("(() => { const n = document.querySelector('#main .ut-note'); return n ? [n.textContent, getComputedStyle(n).color] : null })()")
    ok(nt and '290' in nt[0] and x['note'] in nt[0] and x['detail'] in nt[0], f'3a {tag}: Stats, the grey line ({nt})')
    if os.environ.get('SWEEP_SHOTS'): pg.evaluate(SWC); pg.wait_for_timeout(600); pg.screenshot(path=os.path.join(os.environ['SWEEP_SHOTS'], f'honest-stats-{tag}.png'))
    wr = pg.evaluate("stats(ft().filter((t) => !t.untracked)).n")
    ok(wr == 2, f'3a {tag}: Stats counts the 2 trades, not the line ({wr})')
    pg.evaluate("location.hash = '#account/hj-a'"); pg.wait_for_timeout(1800)
    ok(x['note'] in pg.evaluate("(document.querySelector('#main .ut-note') || {}).textContent || ''"), f'3a {tag}: the account page, the grey line')
    tap(pg.locator('#main .ut-note [data-ut-go]')); pg.wait_for_timeout(1200)
    ok(pg.evaluate("!!document.querySelector('.nav-am.open, #tkSlide.open')"), f'3a {tag}: « {x["detail"]} › » opens the trade form')
    pg.keyboard.press('Escape'); pg.wait_for_timeout(300); pg.evaluate("document.querySelectorAll('.nav-am.open [data-am=close]').forEach((b) => b.click()); typeof closeTicket === 'function' && closeTicket()"); pg.wait_for_timeout(400)
    pg.evaluate(TRADE, ['hj-t2', 'hj-a', day, -29000, {'entry_time': '11:00', 'exit_time': '11:05'}]); pg.wait_for_timeout(800); pg.evaluate("render()"); pg.wait_for_timeout(800)
    ok(not pg.evaluate("S.trades.some((t) => t.untracked)") and pg.locator('#main .ut-note').count() == 0, f'3a {tag}: detailed: the line and the grey line go away')
    # 3b once: a second gap says nothing more
    pg.evaluate("SweepGap.apply('hj-a', todayStr(), -1000, 'trades')"); pg.wait_for_timeout(500)
    ok(pg.evaluate("S.settings.gap_coach.before_c") == gc['before_c'], f'3b {tag}: a second gap: the coach\'s sentence stays the first one')
    # 4a. a day reviewed without the platform's balance does not count (the journal written directly)
    pg.evaluate(ACC, ['hj-b', 'Topstep 50K #2']); pg.evaluate(TRADE, ['hj-t3', 'hj-b', day, 2000, None])
    pg.evaluate(FLUSH); pg.evaluate("SweepGame.refresh()"); pg.wait_for_timeout(2500)
    st = pg.evaluate("(() => { const s = SweepGame.state(); return s && s.today ? [s.today.valid, s.today.review_done] : null })()")
    ok(st == [False, True], f'4a {tag}: another account traded, not checked: the day does not count yet ({st})')
    # 4c. the form, a loss typed: as many taps as a win
    def quick(net):
      pg.evaluate("openTicket(null)"); pg.wait_for_selector('.nav-am.open [data-am=no-shot]', timeout=8000); pg.wait_for_timeout(400)
      tap(pg.locator('.nav-am.open [data-am=no-shot]')); pg.wait_for_selector('.nav-am.open [data-am-f=net]', timeout=8000); pg.wait_for_timeout(300)
      n0 = pg.evaluate("S.trades.length"); taps = 1
      pg.locator('.nav-am.open [data-am-f=net]').fill(net); pg.wait_for_timeout(300)
      fold = pg.evaluate("(() => { const w = document.querySelector('.nav-am.open .nav-am-ctxw'); return w ? [w.classList.contains('fold'), [...w.querySelectorAll('.nav-am-sec')].every((s) => !s.getClientRects().length), (w.querySelector('.nav-am-ctxb') || {}).textContent] : null })()")
      if os.environ.get('SWEEP_SHOTS') and net.startswith('-'): pg.screenshot(path=os.path.join(os.environ['SWEEP_SHOTS'], f'honest-loss-form-{tag}.png'))
      tap(pg.locator('.nav-am.open [data-am-seg=dir][data-v=short]')); taps += 1
      tap(pg.locator('.nav-am.open [data-am=save]')); taps += 1; pg.wait_for_timeout(1200)
      return fold, taps, pg.evaluate("S.trades.length") - n0
    fl, tl, nl = quick('-120')
    ok(fl and fl[0] and fl[1] and fl[2] == x['ctx'], f'4c {tag}: a loss typed: checklist and emotions under « {x["ctx"]} » ({fl})')
    fw, tw, nw = quick('80')
    ok(fw and not fw[0], f'4c {tag}: a win: the checklist shown as before ({fw})')
    ok(nl >= 1 and nw >= 1 and tl <= tw, f'4c {tag}: a loss saved in {tl} taps, a win in {tw} ({nl}, {nw})')
    # 4d. « Journal honnête »: 4 earlier traded days that agreed with the platform, then today closed with « C'est le même »
    uid = pg.evaluate("S.uid")
    past = ymd_back(day, 4)
    db = sqlite3.connect(DB)
    for d in past:
      db.execute("INSERT OR REPLACE INTO game_days (user_id, trading_day, trades_count, is_valid_streak, review_done, updated_at) VALUES (?, ?, 1, 1, 1, ?)", (uid, d, int(time.time())))
    db.commit(); db.close()
    for d in past: pg.evaluate("(d) => put('journals', { id: d, post: { reviewed_at: 'x', bal: [{ acc: 'hj-a', gap_c: 0 }] } })", d)
    pg.evaluate("(d) => editDoc('journals', d, (j) => { j.post = Object.assign({}, j.post, { bal: [{ acc: 'hj-a', gap_c: 0 }, { acc: 'hj-b', gap_c: 0 }] }); })", day)
    pg.evaluate(FLUSH); pg.evaluate("SweepGame.refresh()"); pg.wait_for_timeout(3000)
    b = pg.evaluate("fetch('api/game/profile', { headers: { 'X-Requested-With': 'fetch' } }).then((r) => r.json()).then((j) => (j.badges || []).find((x) => x.id === 'honest_5'))")
    ok(b and b['unlocked'], f'4d {tag}: « Journal honnête » on the 5th day in a row ({b})')
    ok(pg.evaluate("document.documentElement.scrollWidth - innerWidth") <= 0, f'{tag}: nothing wider than the window')
    pg.evaluate(FLUSH)
    ctx.close()
  ok(not errs, f'no page error ({errs[:2]})')
  br.close()
print(f'{fails} failed' if fails else 'all passed')
sys.exit(1 if fails else 0)
