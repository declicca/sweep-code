"""
Sweep — « Bring your history » to the end (activation D, 29 Oct.), Playwright:
  python3 tests/e2e_history_sync.py http://127.0.0.1:8095
A trader of « More than a year » signs up on a market open (the clock pinned: a Tuesday 10:30 New York), phone 390 (fr, touch):
 1  the first account, the plan, then « Ramène ton historique »: NinjaTrader 8 opens the connection with the personal key
 2  the add-on's push with that key (its executions), the account linked: the trade in the journal, on Today, mission 8 of the
    discovery missions ticked by it
No page error, nothing wider than the window.
"""
import json, os, random, sqlite3, sys, time
from datetime import datetime
from zoneinfo import ZoneInfo
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
H = {'Content-Type': 'application/json', 'X-Requested-With': 'fetch'}
DB = os.environ.get('SWEEP_TEST_DB', '/tmp/g/data/journal.db')
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)
ms = lambda s: int(datetime.strptime(s, '%Y-%m-%d %H:%M:%S').replace(tzinfo=ZoneInfo('America/New_York')).timestamp() * 1000)
with sync_playwright() as p:
  br = p.chromium.launch(); errs = []
  try: d = sqlite3.connect(DB); d.execute('DELETE FROM attempts'); d.commit(); d.close()
  except Exception: pass
  ctx = br.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True, locale='fr-CA')
  ctx.add_init_script("localStorage.setItem('tj.lang', JSON.stringify('fr')); window.__swNow = '2026-10-27T10:30:00-04:00'")
  r = ctx.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': 'hs%06d@t.dev' % random.randint(0, 999999), 'consent': True, 'elapsed': 6000}), headers=H)
  if r.status != 201: raise RuntimeError('sign-up refused: %s' % r.status)
  pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
  tap = lambda sel: (pg.locator(sel).first.tap(), pg.wait_for_timeout(300))
  pg.goto(B + '/'); pg.wait_for_selector('form[data-form=account][data-onb] [data-st-ph0=eval]', timeout=20000); pg.wait_for_timeout(700)
  uid = pg.evaluate("S.uid"); d = sqlite3.connect(DB); d.execute('UPDATE users SET discovery_done = 2 WHERE id = ?', (uid,)); d.commit(); d.close()   # follows the missions
  # 1. the first account (Apex EOD 50K), « More than a year », the plan, then « Bring your history »
  tap('form[data-form=account] [data-st-ph0=eval]'); tap('[data-st-firm=apex]')
  if pg.locator('[data-st-type=apex-eod]').count(): tap('[data-st-type=apex-eod]')
  tap('[data-st-size="50000"]')
  pg.locator('[data-onb-fn]').click(); pg.keyboard.type('Léa'); tap('.nav-onb-me [data-exp="gt1"]')
  tap('form[data-form=account][data-onb] [type=submit]')
  pg.wait_for_selector('#gSheet [data-g=save-plan]', timeout=10000); pg.wait_for_timeout(400)
  tap('#gSheet [data-g=bias][data-v=bullish]'); tap('#gSheet [data-g=save-plan]')
  pg.wait_for_selector('aside.nav-hist.open', timeout=8000); pg.wait_for_timeout(300)
  tap('aside.nav-hist.open [data-sy=connect][data-p=ninjatrader]')
  pg.wait_for_selector('#sySheet .sy-key code', timeout=10000); pg.wait_for_timeout(500)
  key = pg.evaluate("document.querySelector('#sySheet .sy-key code').textContent.trim()")
  ok(key.startswith('swk_') and pg.locator('aside.nav-hist.open').count() == 0, f'1 « Ramène ton historique » › NinjaTrader 8: the connection opens with the personal key ({key[:8]}…)')
  # 2. the add-on's push (its own request: no session, the key alone), then the account linked
  fills = [{'id': 'h1', 'account': 'APEX-H-01', 'contract': 'MNQ 12-26', 'side': 'buy', 'qty': 1, 'price': 21000.25, 'ts': ms('2026-10-07 09:31:05'), 'fee': 0.62, 'point_value': 2},
           {'id': 'h2', 'account': 'APEX-H-01', 'contract': 'MNQ 12-26', 'side': 'sell', 'qty': 1, 'price': 21012.25, 'ts': ms('2026-10-07 09:39:00'), 'fee': 0.62, 'point_value': 2}]
  bare = p.request.new_context()
  r = bare.post(B + '/api/sync/push', data=json.dumps({'client': 'Sweep NT8', 'accounts': [{'name': 'APEX-H-01', 'connection': 'Apex', 'provider': 'Rithmic', 'currency': 'USD', 'cash': 50024}], 'fills': fills}), headers={'Content-Type': 'application/json', 'X-Sweep-Key': key})
  ok(r.status == 200 and r.json().get('new') == 2, f'2 the add-on\'s push with that key: 2 executions ({r.status})')
  st = ctx.request.get(B + '/api/sync', headers=H).json(); acc = (st.get('accounts') or [{}])[0]
  aid = pg.evaluate("S.accounts.find((a) => !a.demo).id")
  ln = ctx.request.post(B + '/api/sync/accounts/%s' % acc.get('id'), data=json.dumps({'action': 'link', 'account_id': aid}), headers=H).json()
  ok(ln.get('ok') and ln.get('created') == 1, f'2 the account linked: 1 trade written ({ln})')
  pg.evaluate("document.querySelectorAll('#sySheet [data-sy=close], #sySheet .sy-x').forEach((b) => b.click())"); pg.wait_for_timeout(300)
  pg.reload(); pg.wait_for_timeout(3000); pg.evaluate("location.hash = '#trades'"); pg.wait_for_timeout(1500)
  tr = pg.evaluate("S.trades.filter((t) => t.source === 'ninjatrader').map((t) => [t.instrument, t.contracts, t.pnl_c, t.date])")
  ok(tr == [['MNQ', 1, 2400, '2026-10-07']], f'2 the trade in the journal ({tr})')
  ok('MNQ' in pg.evaluate("document.getElementById('main').innerText"), '2 the Trades page shows it')
  pg.evaluate("location.hash = '#dashboard'"); pg.evaluate("SweepGame.refresh()"); pg.wait_for_timeout(2500)
  dd = pg.evaluate("(SweepGame.state() && SweepGame.state().discovery) || null")
  ok(dd and 8 in (dd.get('done') or []), f'2 mission 8 « Tes trades arrivent seuls » ticked by the sync ({dd and dd.get("done")})')
  ok(pg.evaluate("document.documentElement.scrollWidth - innerWidth") <= 0, 'nothing wider than the window')
  ok(not errs, f'no page error ({errs[:2]})')
  br.close()
print(f'{fails} failed' if fails else 'all passed')
sys.exit(1 if fails else 0)
