"""
Sweep — « Now », on top of the routine (SWEEP.md step 3), Playwright:
  python3 tests/e2e_now.py http://127.0.0.1:8095
A trader of its own. Phone 390 (fr, touch) and computer 1300 (en):
 1  before the first trade, no plan: « Your risk allowed today » = the account's daily limit ($1,000), and where it comes from;
    the accounts card is on Today from the first account (no trade yet); « This month », the news card, the trends and the
    rank are not on Today any more
 2  a plan with a $600 max loss and 2 trades max: the risk allowed is $600, « your plan's max loss »
 3  a −$250 trade: « Left today » $350, « before your max loss · trade 2 of 2 », the same figure as « Before this trade »
 4  a −$400 trade: « Day over by your plan », the coach's reason
 5  at each moment, one blue button in the routine card; the day reviewed: no « Now » any more
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
X = {'fr': {'risk': 'Ton risque permis aujourd’hui', 'dll': 'la limite du jour de Topstep 50K', 'plan': 'la perte max de ton plan', 'left': 'Il te reste', 'Lplan': 'avant ta perte max', 'count': 'trade 2 sur 2', 'end': 'Journée terminée selon ton plan'},
     'en': {'risk': 'Your risk allowed today', 'dll': 'the daily limit of Topstep 50K', 'plan': 'your plan’s max loss', 'left': 'Left today', 'Lplan': 'before your max loss', 'count': 'trade 2 of 2', 'end': 'Day over by your plan'}}
NOW = "(() => { const n = document.querySelector('#main .nav-rt .nav-now'); return n ? { state: n.dataset.now, text: n.textContent.replace(/\\s+/g, ' ').trim(), v: (n.querySelector('.nav-now-v') || {}).textContent || '' } : null })()"
BLUE = "[...document.querySelectorAll('#main .nav-rt .btn.primary')].filter((b) => b.getClientRects().length && getComputedStyle(b).visibility !== 'hidden').length"
CARDS = "['.d-cal', '.d-news', '.d-trends', '.d-rank', '.d-acc'].filter((q) => { const e = document.querySelector('#main .nav-dash ' + q); return e && e.getClientRects().length })"
WIDE = "document.documentElement.scrollWidth - innerWidth"
sp = lambda s: (s or '').replace(' ', ' ').replace(' ', ' ')
with sync_playwright() as p:
  br = p.chromium.launch()
  for lang, w, phone in (('fr', 390, True), ('en', 1300, False)):
    tag = f'{w}-{lang}'; x = X[lang]
    try: d = sqlite3.connect(DB); d.execute('DELETE FROM attempts'); d.commit(); d.close()
    except Exception: pass
    ctx = br.new_context(viewport={'width': w, 'height': 844 if phone else 850}, is_mobile=phone, has_touch=phone, locale='fr-CA' if lang == 'fr' else 'en-US')
    ctx.add_init_script("try { localStorage.setItem('tj.lang', JSON.stringify('%s')); sessionStorage.setItem('sw.modal', '1') } catch (e) {}" % lang)
    r = ctx.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': 'nw%06d@t.dev' % random.randint(0, 999999), 'consent': True, 'elapsed': 6000}), headers=H)
    if r.status != 201: raise RuntimeError('sign-up refused: %s' % r.status)
    ctx.request.post(B + '/api/me/profile', data=json.dumps({'first_name': 'Ari', 'experience': 'gt1'}), headers=H)
    pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
    pg.goto(B + '/#dashboard'); pg.wait_for_timeout(2500)
    pg.evaluate("put('accounts', { id: 'nw-a', name: 'Topstep 50K', status: 'active', phase: 'eval', starting_balance_c: 5000000, created_on: '2026-09-01', rules: { dd_c: 200000, dll_c: 100000 } })")
    def today():
      pg.wait_for_timeout(1500); pg.evaluate("location.hash = '#dashboard'; render()"); pg.wait_for_selector('#main .nav-rt', timeout=8000); pg.wait_for_timeout(1200)
      return pg.evaluate(NOW)
    m = pg.evaluate("location.hash = '#dashboard'") or None
    day = pg.evaluate("(SweepGame.state() && SweepGame.state().today && SweepGame.state().today.day) || todayStr()")
    market = pg.evaluate("!!(SweepGame.state() && SweepGame.state().today && SweepGame.state().today.market)")
    if not market:
      print(f'skip {tag}: the market is closed today (the game\'s clock)'); ctx.close(); continue
    # 1. no plan, no trade: the account's daily limit
    n = today()
    ok(n and n['state'] == 'before' and x['risk'] in n['text'] and x['dll'] in n['text'] and '1' in n['v'] and '000' in sp(n['v']).replace(',', '').replace(' ', ''), f'{tag} 1 before the session, no plan: {n}')
    cards = pg.evaluate(CARDS)
    ok(cards == ['.d-acc'], f'{tag} 1 Today: the accounts from the first account, no « This month », news card, trends or rank ({cards})')
    ok(pg.evaluate(BLUE) == 1, f'{tag} 1 one blue button in the routine ({pg.evaluate(BLUE)})')
    # 2. a plan
    pg.evaluate("(d) => put('journals', { id: d, pre: { bias: 'bullish', max_loss: '600', max_trades: '2', saved_at: Math.floor(Date.now() / 1000) } })", day)
    n = today()
    ok(n and n['state'] == 'before' and x['plan'] in n['text'] and '600' in sp(n['v']), f'{tag} 2 a plan: the risk allowed is its max loss ({n})')
    ok(pg.evaluate(BLUE) == 1, f'{tag} 2 one blue button in the routine ({pg.evaluate(BLUE)})')
    # 3. during the session
    pg.evaluate("(d) => put('trades', { id: 'nw-t1', account_id: 'nw-a', instrument: 'NQ', direction: 'long', contracts: 1, entry: 1, exit: 2, pnl_c: -25000, pnl_manual: true, date: d, entry_time: '09:45', exit_time: '09:50' })", day)
    n = today()
    before = sp(pg.evaluate("(d) => SweepCoach.before({ form: 'manual', account: 'nw-a', date: d, qty: 1 })", day))
    ok(n and n['state'] == 'during' and x['left'] in n['text'] and x['Lplan'] in n['text'] and x['count'] in n['text'] and '350' in sp(n['v']), f'{tag} 3 during the session: what is left ({n})')
    ok('350' in before, f'{tag} 3 the same figure as « Before this trade » ({before[-80:]})')
    ok(pg.evaluate(BLUE) == 1, f'{tag} 3 one blue button in the routine ({pg.evaluate(BLUE)})')
    # 4. the max loss reached
    pg.evaluate("(d) => put('trades', { id: 'nw-t2', account_id: 'nw-a', instrument: 'NQ', direction: 'long', contracts: 1, entry: 1, exit: 2, pnl_c: -40000, pnl_manual: true, date: d, entry_time: '10:45', exit_time: '10:50' })", day)
    n = today()
    ok(n and n['state'] == 'end' and x['end'] in n['text'] and '600' in sp(n['text']), f'{tag} 4 the max loss reached: the day is over, the coach\'s reason ({n})')
    co = pg.evaluate("(document.querySelector('#main .co-today') || {}).textContent || ''")
    ok(x['end'] not in co and sp(co).count('600') <= 1, f'{tag} 4 the coach card does not say it again ({co[:120]!r})')
    ok(pg.evaluate(BLUE) == 1, f'{tag} 4 one blue button in the routine ({pg.evaluate(BLUE)})')
    # 5. the day reviewed
    pg.evaluate("(d) => editDoc('journals', d, (j) => { j.post = Object.assign(j.post || {}, { followed: 'yes', discipline: 4, grade: 'B', reviewed_at: Math.floor(Date.now() / 1000) }); })", day)
    pg.wait_for_timeout(1500); pg.evaluate("SweepGame.refresh()"); n = today()
    ok(n is None, f'{tag} 5 the day reviewed: no « Now » ({n})')
    ok(pg.evaluate(WIDE) <= 0, f'{tag} nothing wider than the window')
    ok(not errs, f'{tag} no page error ({errs[:2]})')
    ctx.close()
  br.close()
print(f'{fails} failed' if fails else 'all passed')
sys.exit(1 if fails else 0)
