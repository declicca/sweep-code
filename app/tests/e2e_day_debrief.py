"""
Sweep — « Debrief my day » without the trades (15 Oct.), with Playwright:
  python3 tests/e2e_day_debrief.py http://127.0.0.1:8095 /tmp/show_state.json
The answer of Sweep AI is played by the test (the request is caught): no call to Google. Phone 390 (fr) and computer 1300 (en).
 1  Journal › « Debrief my day »: the day's window has « Include my trades of the day » (ticked) and « Your day in a few words »
 2  unticked + a few words: the request says with_trades false and carries the words; the debrief shows without trade figures
 3  ticked (as before): with_trades true
"""
import sys, json
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)

ANSWER = {'date': '', 'stats': {'trades': 0, 'net_c': 0, 'win_rate': None}, 'debrief': {'verdict': 'followed', 'summary': 'Plan followed, patient session.', 'checks': [{'label': 'Plan', 'ok': True, 'detail': 'Bias written before the open.'}], 'lesson': 'Waiting paid.', 'tomorrow': 'Same routine.'}, 'cached': False}

with sync_playwright() as p:
  br = p.chromium.launch(); allerr = []
  for w, phone, lang in [(390, True, 'fr'), (1300, False, 'en')]:
    c = br.new_context(storage_state=STATE, viewport={'width': w, 'height': 850}, is_mobile=phone, has_touch=phone)
    c.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('%s'))" % lang)
    pg = c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
    bodies = []
    def handle(route):
      try: bodies.append(json.loads(route.request.post_data or '{}'))
      except Exception: bodies.append({})
      a = dict(ANSWER); a['date'] = bodies[-1].get('date', '')
      route.fulfill(status=200, content_type='application/json', body=json.dumps(a))
    c.route('**/api/ai/day-debrief*', handle)
    pg.goto(B + '/#journal'); pg.wait_for_timeout(2600)
    b = pg.locator('#main [data-act="ai-day"]').first
    if not b.count():
      ok(False, f'{w}: « Debrief my day » is in the Journal'); c.close(); continue
    b.click(); pg.wait_for_timeout(900)
    ck = pg.locator('.sai [data-act="rev-trades"]'); note = pg.locator('.sai textarea[data-bind="rev.note"]')
    ok(ck.count() == 1 and ck.is_checked() and note.count() == 1, f'1 {w} {lang}: the window offers « include my trades » (ticked) and a few words of his own')
    ck.click(); note.fill('Pas de trade aujourd’hui, je suis resté patient et j’ai suivi ma routine.' if lang == 'fr' else 'No trade today, I stayed patient and kept my routine.')
    pg.locator('.sai [data-act="gen-day"]').click(); pg.wait_for_timeout(1200)
    last = bodies[-1] if bodies else {}
    ok(last.get('with_trades') is False and len(last.get('note', '')) > 20, f'2 {w}: sent without the trades, with his words ({ {k: (v if k != "note" else v[:30]) for k, v in last.items()} })')
    shown = pg.evaluate("(()=>{const r=document.querySelector('.sai'); return {card:!!r.querySelector('.sai-card'), kpis:!!r.querySelector('.sai-kpis')}})()")
    ok(shown['card'] and not shown['kpis'], f'2 {w}: the debrief shows, no trade figures ({shown})')
    ck.click(); pg.locator('.sai [data-act="gen-day"]').click(); pg.wait_for_timeout(1000)
    ok(bodies[-1].get('with_trades') is True, f'3 {w}: ticked again: with the trades ({bodies[-1].get("with_trades")})')
    allerr += errs; c.close()
  ok(not allerr, f'no page error ({allerr[:2]})')
  br.close()
print(f'{fails} failed' if fails else 'all passed')
sys.exit(1 if fails else 0)
