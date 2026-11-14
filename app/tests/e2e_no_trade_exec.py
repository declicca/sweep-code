"""
Sweep — « I took no trade » in the Execution step of the routine (14 Nov., Mateo), Playwright:
  python3 tests/e2e_no_trade_exec.py http://127.0.0.1:8095
A new trader with a plan for the day and no trade: under Execution, « I took no trade » (phone: « No trade »); tapped, the step is
done (« No trade: that keeps to your plan »), the review becomes the next step, the choice is kept in the day's journal and
survives a reload; « Undo » takes it back; chosen again, a trade saved later takes over (the link goes, the step counts the
trade). Without a plan it is not offered. At 390 (touch) and 1300, light and dark, in FR, EN and ES: nothing cut or overlapping,
no horizontal scroll, no page error. Screenshots: $TMPDIR/nt-*.png.
"""
import json, os, random, sys, tempfile
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
OUT = os.environ.get('TMPDIR', tempfile.gettempdir())
H = {'Content-Type': 'application/json', 'X-Requested-With': 'fetch'}
DB = os.environ.get('SWEEP_TEST_DB', '')
fails = 0
def ok(c, what):
    global fails
    print(('ok   ' if c else 'FAIL ') + what); fails += 0 if c else 1
TXT = {'fr': {'nt': 'Je n’ai pas pris de trade', 'ntS': 'Aucun trade', 'done': 'Aucun trade : ça respecte ton plan', 'undo': 'Annuler'},
       'en': {'nt': 'I took no trade', 'ntS': 'No trade', 'done': 'No trade: that keeps to your plan', 'undo': 'Undo'},
       'es': {'nt': 'No tomé ninguna operación', 'ntS': 'Sin operar', 'done': 'Sin operar: respeta tu plan', 'undo': 'Deshacer'}}
CARD = '#main .nav-rt:not(.ph) .nav-rt-steps'
S2 = CARD + ' .nav-rt-s:nth-child(2)'
WIDE = "Math.max(document.documentElement.scrollWidth, document.body.scrollWidth) - innerWidth"   # the page itself (a row that scrolls sideways inside its own box is fine)

def until(pg, expr, ms=12000):
  for _ in range(ms // 150):
    if pg.evaluate(f'!!({expr})'): return True
    pg.wait_for_timeout(150)
  return False

def shot(pg, path):   # the steps in the middle of the screen (above the phone's tab bar)
  pg.evaluate("(s) => { const e = document.querySelector(s); const r = e.getBoundingClientRect(); scrollBy(0, r.top - innerHeight / 2 + r.height / 2); }", CARD)
  pg.wait_for_timeout(400); pg.screenshot(path=path)


def run(p, lang, phone, scheme):
  tag = f'{390 if phone else 1300} {lang} {scheme}'; T = TXT[lang]
  if DB:
    import sqlite3
    try: d = sqlite3.connect(DB); d.execute('DELETE FROM attempts'); d.commit(); d.close()
    except Exception: pass
  br = p.chromium.launch(); errs = []
  c = br.new_context(viewport={'width': 390 if phone else 1300, 'height': 844 if phone else 850}, is_mobile=phone, has_touch=phone,
                     locale={'fr': 'fr-CA', 'en': 'en-US', 'es': 'es-ES'}[lang], color_scheme=scheme)
  c.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('%s'))" % lang)
  r = c.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': 'nt%07d@t.dev' % random.randint(0, 9999999), 'consent': True, 'elapsed': 6000}), headers=H)
  ok(r.status == 201, f'{tag} a new trader signs up ({r.status})')
  pg = c.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
  pg.goto(B + '/#dashboard'); pg.wait_for_function("() => !!(window.SweepGame && SweepGame.state && window.put)", timeout=20000); pg.wait_for_timeout(800)
  pg.evaluate("""() => { put('firms', {id: 'nt-f', name: 'Topstep'}); put('accounts', {id: 'nt-a', firm_id: 'nt-f', name: 'Topstep 50K', starting_balance_c: 5000000, status: 'active', phase: 'eval', rules: {dd_c: 200000, dd_type: 'eod', target_c: 300000}}); }""")
  pg.wait_for_timeout(1200); pg.goto(B + '/#dashboard')
  ok(until(pg, "SweepGame.state().today && document.querySelector('%s')" % CARD, 20000), f'{tag} the routine card is there')
  day = pg.evaluate('SweepGame.state().today.day')
  # without a plan: not offered
  ok(pg.locator(S2 + ' [data-rt=nt]').count() == 0, f'{tag} without a plan: no « {T["nt"]} »')
  # the plan of the day (bias and max loss: a valid plan)
  pg.evaluate("(d) => { put('journals', { id: d, pre: { bias: 'bullish', max_loss: '500', saved_at: Math.floor(Date.now() / 1000) - 600 } }); SweepGame.refresh(); }", day)
  ok(until(pg, "document.querySelector('%s [data-rt=nt]')" % S2, 15000), f'{tag} with a plan and no trade: the link is under Execution')
  lk = pg.locator(S2 + ' [data-rt=nt]')
  ok(lk.inner_text().strip() == (T['ntS'] if phone else T['nt']), f'{tag} it says « {lk.inner_text().strip()} »')
  bx = lk.bounding_box(); sb = pg.locator(S2).bounding_box(); btn = pg.locator(S2 + ' [data-rt=trade]').bounding_box()
  inside = bx and sb and bx['x'] >= sb['x'] - 1 and bx['x'] + bx['width'] <= sb['x'] + sb['width'] + 1 and bx['y'] + bx['height'] <= sb['y'] + sb['height'] + 1
  apart = btn and (bx['y'] >= btn['y'] + btn['height'] - 1 or bx['x'] >= btn['x'] + btn['width'] - 1 or bx['y'] + bx['height'] <= btn['y'] + 1)
  ok(inside and apart and bx['height'] >= 20, f'{tag} inside its step, clear of « Add a trade », {round(bx["height"])} px tall')
  shot(pg, f'{OUT}/nt-{lang}-{390 if phone else 1300}-{scheme}-a.png')
  # tapped: the step is done, the review is next, kept in the journal, the server agrees (execution ring closed)
  lk.click()
  ok(until(pg, "document.querySelector('%s').classList.contains('done')" % S2), f'{tag} tapped: the Execution step is done')
  st = pg.locator(S2 + ' .nav-rt-st').inner_text().strip()
  ok(st == T['done'], f'{tag} « {st} »')
  ok(pg.locator(CARD).get_attribute('data-next') == '3', f'{tag} the review is the next step ({pg.locator(CARD).get_attribute("data-next")})')
  ok(pg.evaluate("(d) => !!(getDoc('journals', d).post || {}).no_trade_at", day), f'{tag} kept in the day\'s journal (post.no_trade_at)')
  g = c.request.get(B + '/api/game/today').json()
  ok(((g.get('today') or {}).get('rings') or {}).get('execution') == 100, f'{tag} the server closes the execution ring too')
  pg.wait_for_timeout(600)
  shot(pg, f'{OUT}/nt-{lang}-{390 if phone else 1300}-{scheme}-b.png')
  pg.reload(); ok(until(pg, "document.querySelector('%s.done [data-rt=nt-undo]')" % S2, 20000), f'{tag} after a reload: still done, with « {T["undo"]} »')
  # undo
  pg.locator(S2 + ' [data-rt=nt-undo]').click()
  ok(until(pg, "document.querySelector('%s [data-rt=nt]') && !document.querySelector('%s').classList.contains('done')" % (S2, S2)), f'{tag} « {T["undo"]} »: the step waits again')
  ok(not pg.evaluate("(d) => !!(getDoc('journals', d).post || {}).no_trade_at", day), f'{tag} undone in the journal')
  # chosen again, then a trade: the trade takes over
  pg.locator(S2 + ' [data-rt=nt]').click(); until(pg, "document.querySelector('%s').classList.contains('done')" % S2)
  pg.evaluate("(d) => { put('trades', { id: 'nt-t1', account_id: 'nt-a', instrument: 'NQ', direction: 'long', contracts: 1, entry: 1, exit: 2, pnl_c: 10000, pnl_manual: true, date: d, entry_time: '10:00', exit_time: '10:05', session_date: true }); SweepGame.refresh(); }", day)
  ok(until(pg, "!document.querySelector('%s [data-rt^=nt]')" % S2, 15000), f'{tag} a trade saved: the link is gone')
  st = pg.locator(S2 + ' .nav-rt-st').inner_text().strip()
  ok(st != T['done'], f'{tag} the step counts the trade (« {st} »)')
  ok(pg.evaluate(WIDE) <= 1, f'{tag} no horizontal scroll')
  ok(pg.evaluate("(s) => { const r = document.querySelector(s).getBoundingClientRect(); return r.left >= -1 && r.right <= innerWidth + 1; }", CARD), f'{tag} the 3 steps fit the width')
  ok(not errs, f'{tag} no page error {errs[:2]}')
  br.close()

with sync_playwright() as p:
  for lang, phone, scheme in (('fr', True, 'dark'), ('en', False, 'light'), ('es', True, 'light'), ('fr', False, 'dark')):
    run(p, lang, phone, scheme)
print('all passed' if not fails else f'{fails} failed')
sys.exit(1 if fails else 0)
