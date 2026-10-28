"""
Sweep — « Close my day » checks the platform's balance (brief « pertes oubliées », step 2, 27 Oct.), Playwright:
  python3 tests/e2e_platform_balance.py http://127.0.0.1:8095
A trader of its own, a Topstep 50K evaluation; phone 390 (fr, touch), computer 1300 (en), phone 390 (es).
 1  a day without a gap: « Ton solde sur Topstep ? », filled in with Sweep's balance; closing without it asks for it, one tap on
    « C'est le même » and the day closes (one tap more than before); the balance is kept (journal.post.bal), no line
 2  a day with a gap: +$150 logged, the platform says −$190: « Il manque −340 $… C'était quoi ? », three chips; « Des trades pas
    notés »: a « Trades non détaillés −340 $ » line on that account and day; the day's P&L −$190, the balance and the drawdown
    room follow; the line in the trade list, its page with « Ajouter le détail »; a trade logged then leaves the line
 3  an account synced today (NinjaTrader 8) does not get the line
 4  « Recalibrer » on the account page offers the same chips: fees (an adjustment and an expense in My money) — payout on the
    computer (My money's payout form, filled in)
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
X = {'fr': {'q': 'Ton solde sur Topstep ?', 'same': 'C’est le même', 'need': 'Confirme ton solde sur Topstep.', 'gap': 'Il manque', 'what': 'C’était quoi ?', 'trades': 'Des trades pas notés', 'fees': 'Des frais', 'payout': 'Un payout', 'line': 'Trades non détaillés', 'detail': 'Ajouter le détail'},
     'en': {'q': 'Your balance on Topstep?', 'same': 'It matches', 'need': 'Confirm your balance on Topstep.', 'gap': 'missing between your platform', 'what': 'What was it?', 'trades': 'Trades I didn’t log', 'fees': 'Fees', 'payout': 'A payout', 'line': 'Trades not detailed', 'detail': 'Add the detail'},
     'es': {'q': '¿Tu saldo en Topstep?', 'same': 'Es el mismo', 'need': 'Confirma tu saldo en Topstep.', 'gap': 'Faltan', 'what': '¿Qué fue?', 'trades': 'Operaciones sin anotar', 'fees': 'Comisiones', 'payout': 'Un payout', 'line': 'Operaciones sin detallar', 'detail': 'Añadir el detalle'}}
ACC = "([id, name]) => put('accounts', { id, name, firm_id: 'pb-f', status: 'active', phase: 'eval', starting_balance_c: 5000000, created_on: '2026-09-01', rules: { dd_c: 200000, dd_type: 'eod', dll_c: 100000, target_c: 300000, consistency_pct: 50 } })"
TRADE = "([id, acc, d, c, src]) => put('trades', Object.assign({ id, account_id: acc, instrument: 'MNQ', direction: 'long', contracts: 1, entry: 1, exit: 2, pnl_c: c, pnl_manual: true, date: d, entry_time: '10:00', exit_time: '10:05', discipline: { plan: 'y' } }, src ? { source: src } : {}))"
ERR = "(document.getElementById('gErr') || {}).textContent || ''"
OPEN = "!!document.querySelector('#gSheet.open, #gSheet .g-in [data-g=save-review]')"
with sync_playwright() as p:
  br = p.chromium.launch(); errs = []
  for lang, phone in (('fr', True), ('en', False), ('es', True)):
    w = 390 if phone else 1300; tag = f'{w}-{lang}'; x = X[lang]
    try: d = sqlite3.connect(DB); d.execute('DELETE FROM attempts'); d.commit(); d.close()
    except Exception: pass
    ctx = br.new_context(viewport={'width': w, 'height': 844 if phone else 850}, is_mobile=phone, has_touch=phone, locale={'fr': 'fr-CA', 'en': 'en-US', 'es': 'es-ES'}[lang])
    ctx.add_init_script("try { localStorage.setItem('tj.lang', JSON.stringify('%s')); sessionStorage.setItem('sw.modal', '1') } catch (e) {}" % lang)
    r = ctx.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': 'pb%06d@t.dev' % random.randint(0, 999999), 'consent': True, 'elapsed': 6000}), headers=H)
    if r.status != 201: raise RuntimeError('sign-up refused: %s' % r.status)
    ctx.request.post(B + '/api/me/profile', data=json.dumps({'first_name': 'Léa', 'experience': 'gt1'}), headers=H)
    pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
    SWC = "document.querySelectorAll('.g-sweep [data-g=sw-close]').forEach((b) => b.click())"   # (a day swept: its celebration, whenever it comes)
    def tap(l):
      pg.evaluate(SWC); l.tap() if phone else l.click()
    pg.goto(B + '/#dashboard'); pg.wait_for_timeout(2500)
    pg.evaluate("put('firms', { id: 'pb-f', name: 'Topstep' })")
    pg.evaluate(ACC, ['pb-a', 'Topstep 50K'])
    day = pg.evaluate("todayStr()")
    pg.evaluate("(d) => put('journals', { id: d, pre: { bias: 'bullish', max_loss: '500', max_trades: '5', saved_at: Math.floor(Date.now() / 1000) - 3600 } })", day)
    pg.evaluate(TRADE, ['pb-t1', 'pb-a', day, 10000, ''])
    pg.evaluate("Promise.all(Object.values(chains)).then(() => true)"); pg.evaluate("SweepGame.refresh()"); pg.wait_for_timeout(2500)
    def review():
      pg.evaluate("(d) => SweepGame.openReview(d)", day); pg.wait_for_selector('#gSheet [data-g=save-review]', timeout=8000); pg.wait_for_timeout(500)
      for k in ('r-followed', 'r-score', 'r-grade'):   # (filled in by Sweep on a day it knows; else the first answer)
        if not pg.locator(f'#gSheet [data-g={k}].on').count(): tap(pg.locator(f'#gSheet [data-g={k}]').first); pg.wait_for_timeout(150)
    # 1. a day without a gap
    review()
    rows = pg.evaluate("[...document.querySelectorAll('#gSheet .g-bal')].map((e) => [e.dataset.bal, e.querySelector(':scope > span').textContent, e.querySelector('input').value])")
    bal = pg.evaluate("acctState(getDoc('accounts', 'pb-a')).bal")
    ok(len(rows) == 1 and rows[0][0] == 'pb-a' and rows[0][1] == x['q'] and abs(float(rows[0][2]) * 100 - bal) < 1, f'1 {tag}: « {x["q"]} », filled in with Sweep\'s balance ({rows}, {bal})')
    tap(pg.locator('#gSheet [data-g=save-review]')); pg.wait_for_timeout(400)
    ok(pg.evaluate(ERR) == x['need'] and pg.evaluate(OPEN), f'1 {tag}: closing without it asks for it ({pg.evaluate(ERR)!r})')
    tap(pg.locator('#gSheet [data-bal-same]')); pg.wait_for_timeout(200)
    tap(pg.locator('#gSheet [data-g=save-review]')); pg.wait_for_timeout(900)
    j = pg.evaluate("(d) => (getDoc('journals', d).post || {}).bal", day)
    ok(not pg.evaluate("!!document.querySelector('#gSheet.open')") and j and j[0]['acc'] == 'pb-a' and j[0]['gap_c'] == 0 and not pg.evaluate("S.trades.some((t) => t.untracked)"), f'1 {tag}: one tap on « {x["same"]} » and the day closes; the balance kept, no line ({j})')
    # 2. a day with a gap (another account: +$150 logged, the platform at −$190)
    pg.evaluate(ACC, ['pb-b', 'Topstep 50K #2'])
    pg.evaluate(TRADE, ['pb-t2', 'pb-b', day, 15000, ''])
    pg.evaluate("Promise.all(Object.values(chains)).then(() => true)"); pg.wait_for_timeout(600)
    review()
    rows = pg.evaluate("[...document.querySelectorAll('#gSheet .g-bal')].map((e) => e.dataset.bal)")
    ok(rows == ['pb-b'], f'2 {tag}: only the account not checked yet today ({rows})')
    inp = pg.locator('#gSheet [data-bal-in="pb-b"]'); inp.fill('49810.00'); pg.wait_for_timeout(300)
    gap = pg.evaluate("(document.querySelector('#gSheet .g-bal-gap p') || {}).textContent || ''")
    chips = pg.evaluate("[...document.querySelectorAll('#gSheet [data-bal-k]')].map((b) => b.textContent)")
    ok(x['gap'] in gap and '340' in gap and x['what'] in gap and chips == [x['trades'], x['fees'], x['payout']], f'2 {tag}: the gap said without judging, three chips ({gap!r}, {chips})')
    tap(pg.locator('#gSheet [data-g=save-review]')); pg.wait_for_timeout(300)
    ok(pg.evaluate(OPEN) and pg.evaluate(ERR) != '', f'2 {tag}: a gap: one tap says what it was ({pg.evaluate(ERR)!r})')
    if os.environ.get('SWEEP_SHOTS'): pg.locator('#gSheet .g-bal').screenshot(path=os.path.join(os.environ['SWEEP_SHOTS'], f'balance-gap-{tag}.png'))
    tap(pg.locator('#gSheet [data-bal-k=trades]')); pg.wait_for_timeout(150)
    tap(pg.locator('#gSheet [data-g=save-review]')); pg.wait_for_timeout(1200)
    ln = pg.evaluate("S.trades.filter((t) => t.untracked).map((t) => [t.account_id, t.date, t.pnl_c])")
    st = pg.evaluate("(() => { const s = acctState(getDoc('accounts', 'pb-b')); return [s.bal, s.net, s.buffer] })()")
    ok(ln == [['pb-b', day, -34000]], f'2 {tag}: « {x["line"]} −340 » on that account and day ({ln})')
    ok(st[0] == 4981000 and st[1] == -19000, f'2 {tag}: the balance and the P&L follow: {st}')
    pg.evaluate("location.hash = '#trades'"); pg.wait_for_timeout(1500)
    ok(x['line'] in pg.evaluate("document.getElementById('main').innerText"), f'2 {tag}: the line in the trade list')
    lid = pg.evaluate("S.trades.find((t) => t.untracked).id")
    pg.evaluate("(id) => location.hash = '#trade/' + id", lid); pg.wait_for_timeout(1200)
    btn = pg.locator('#main [data-act=ut-detail]')
    ok(btn.count() == 1 and btn.text_content() == x['detail'], f'2 {tag}: its page, « {x["detail"]} »')
    tap(btn); pg.wait_for_timeout(1200)
    ok(pg.evaluate("!!document.querySelector('.nav-am.open, #tkSlide.open')"), f'2 {tag}: « {x["detail"]} » opens the trade form')
    pg.keyboard.press('Escape'); pg.wait_for_timeout(300); pg.evaluate("document.querySelectorAll('.nav-am.open [data-am=close]').forEach((b) => b.click()); typeof closeTicket === 'function' && closeTicket()"); pg.wait_for_timeout(400)
    pg.evaluate(TRADE, ['pb-t3', 'pb-b', day, -10000, '']); pg.wait_for_timeout(600)
    ln = pg.evaluate("S.trades.filter((t) => t.untracked).map((t) => [t.pnl_c, t.untracked.detailed_c])")
    ok(ln == [[-24000, -10000]] and pg.evaluate("acctState(getDoc('accounts', 'pb-b')).bal") == 4981000, f'2 {tag}: a trade logged leaves the line, the balance stays the platform\'s ({ln})')
    # 3. an account synced today
    pg.evaluate(ACC, ['pb-c', 'Topstep 50K #3']); pg.evaluate(TRADE, ['pb-t4', 'pb-c', day, 5000, 'ninjatrader'])
    pg.evaluate("Promise.all(Object.values(chains)).then(() => true)"); pg.wait_for_timeout(500)
    pg.evaluate("(d) => editDoc('journals', d, (j) => { j.post = {}; })", day); pg.wait_for_timeout(400)
    review()
    rows = pg.evaluate("[...document.querySelectorAll('#gSheet .g-bal')].map((e) => e.dataset.bal)")
    ok('pb-c' not in rows and 'pb-a' in rows, f'3 {tag}: an account synced today does not get the line ({rows})')
    pg.evaluate("document.querySelector('#gSheet [data-g=close]') && document.querySelector('#gSheet [data-g=close]').click()"); pg.wait_for_timeout(500)
    # 4. « Recalibrer » on the account page
    pg.evaluate("location.hash = '#account/pb-a'"); pg.wait_for_timeout(1800)
    if pg.locator('#main details.nav-accset:not([open]) > summary').count(): tap(pg.locator('#main details.nav-accset > summary')); pg.wait_for_timeout(400)   # « Account settings »
    b0 = pg.evaluate("acctState(getDoc('accounts', 'pb-a')).bal")
    pg.locator('#main .nav-recal [data-recal=bal]').fill('%.2f' % ((b0 - 2500) / 100)); tap(pg.locator('#main .nav-recal [data-recal-go=bal]')); pg.wait_for_timeout(400)
    chips = pg.evaluate("[...document.querySelectorAll('#main .nav-recal [data-recal-k]')].map((b) => b.textContent)")
    ok(chips == [x['trades'], x['fees'], x['payout']] and pg.evaluate("acctState(getDoc('accounts', 'pb-a')).bal") == b0, f'4 {tag}: « Recalibrer » says the gap and offers the same chips, nothing changed yet ({chips})')
    if phone:
      tap(pg.locator('#main .nav-recal [data-recal-k=fees]')); pg.wait_for_timeout(900)
      ex = pg.evaluate("S.expenses.filter((e) => e.account_id === 'pb-a').map((e) => [e.category, e.amount_c, !!e.adj_id])")
      ok(pg.evaluate("acctState(getDoc('accounts', 'pb-a')).bal") == b0 - 2500 and ex == [['platform', 2500, True]], f'4 {tag}: fees: an adjustment and an expense in My money ({ex})')
    else:
      tap(pg.locator('#main .nav-recal [data-recal-k=payout]')); pg.wait_for_timeout(1800)
      v = pg.evaluate("(() => { const f = document.querySelector('#main form[data-form=payout]'); return f ? [location.hash, f.querySelector('[name=account]').value, f.querySelector('[name=gross]').value] : [location.hash] })()")
      ok(v == ['#payouts', 'pb-a', '25'], f'4 {tag}: a payout: My money\'s payout form, filled in ({v})')
    ok(pg.evaluate("document.documentElement.scrollWidth - innerWidth") <= 0, f'{tag}: nothing wider than the window')
    pg.evaluate("Promise.all(Object.values(chains)).then(() => true)")
    ctx.close()
  ok(not errs, f'no page error ({errs[:2]})')
  br.close()
print(f'{fails} failed' if fails else 'all passed')
sys.exit(1 if fails else 0)
