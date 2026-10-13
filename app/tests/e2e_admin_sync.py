"""
Sweep — Admin › Sync, dev environment with Playwright:
  python3 tests/e2e_admin_sync.py http://127.0.0.1:8095 /tmp/show_state.json      (SWEEP_TEST_DB: the dev server's SQLite file)
Two traders of its own: one linked a Quantower account and has a synced trade, one created a NinjaTrader 8 key the add-on
never used. On the Admin page (an administrator, fr-CA, computer 1300×850 and phone 390×844):
 - « Synchro » comes after « Préréglages », with one card per platform (traders, seen within 24 h, accounts linked, trades in 7 d);
 - one line per key: name, platform, state chip (blue « Synchronise », gold « Add-on jamais vu »), email, add-on version,
   seen how long ago, accounts and trades, the contracts received with the instrument Sweep reads (MNQZ6 → MNQ), one it does
   not recognize in red (a ProjectX-style name), also in an alert above; and what a gold state means;
 - never a key; only administrators can read it; no horizontal scroll, no page error.
"""
import json, os, random, sqlite3, sys, time
from datetime import datetime
from zoneinfo import ZoneInfo
from playwright.sync_api import sync_playwright
B = (sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095').rstrip('/')
STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
DB = os.environ.get('SWEEP_TEST_DB', '/tmp/g/data/journal.db')
SHOTS = os.environ.get('TMPDIR', '/tmp').rstrip('/')
H = {'Content-Type': 'application/json', 'X-Requested-With': 'fetch'}
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)
def unthrottle():
  try: d = sqlite3.connect(DB); d.execute('DELETE FROM attempts'); d.commit(); d.close()
  except Exception: pass
ms = lambda ny: int(datetime.strptime(ny, '%Y-%m-%d %H:%M:%S').replace(tzinfo=ZoneInfo('America/New_York')).timestamp() * 1000)

def trader(p, first):   # a trader of its own, signed in through the API (no browser page)
  unthrottle()
  ctx = p.request.new_context(base_url=B)
  email = 'as%06d@t.dev' % random.randint(0, 999999)
  r = ctx.post('/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': email, 'consent': True, 'elapsed': 6000}), headers=H)
  if r.status != 201: raise RuntimeError('sign-up refused: %s %s' % (r.status, r.text()[:80]))
  ctx.post('/api/me/profile', data=json.dumps({'first_name': first, 'last_name': 'Sync', 'experience': 'gt1'}), headers=H)
  return ctx, email

with sync_playwright() as p:
  # A: Quantower key, an execution pair pushed, the account linked → « Synchronise »
  a, ea = trader(p, 'Alma')
  a.put('/api/docs/accounts/acc-as', data=json.dumps({'name': 'Apex Q', 'firm_id': '', 'starting_balance_c': 5000000, 'status': 'active', 'money_type': 'eval', 'phase': 'eval', 'created_on': '2026-10-07'}), headers=H)
  key = a.post('/api/sync/key', data=json.dumps({'platform': 'quantower'}), headers=H).json()['key']
  fills = [{'id': 'q1', 'account': 'APEX-901-01', 'contract': 'MNQZ6', 'side': 'buy', 'qty': 1, 'price': 21000, 'ts': ms('2026-10-07 10:00:00'), 'point_value': 2},
           {'id': 'q2', 'account': 'APEX-901-01', 'contract': 'MNQZ6', 'side': 'sell', 'qty': 1, 'price': 21010, 'ts': ms('2026-10-07 10:05:00'), 'point_value': 2},
           {'id': 'q3', 'account': 'APEX-901-01', 'contract': 'CON.F.US.ENQ.Z25', 'side': 'buy', 'qty': 1, 'price': 21020, 'ts': ms('2026-10-07 10:20:00'), 'point_value': 20}]   # still open: no trade
  r = a.post('/api/sync/push', data=json.dumps({'client': 'Sweep Quantower test', 'accounts': [{'name': 'APEX-901-01', 'connection': 'Rithmic', 'provider': 'Rithmic'}], 'fills': fills}), headers={'Content-Type': 'application/json', 'X-Sweep-Key': key})
  sid = [x for x in a.get('/api/sync', headers=H).json()['accounts'] if x['name'] == 'APEX-901-01'][0]['id']
  ln = a.post('/api/sync/accounts/' + sid, data=json.dumps({'action': 'link', 'account_id': 'acc-as'}), headers=H).json()
  ok(r.status == 200 and ln.get('ok') and ln.get('created') == 1, 'trader A: Quantower key, executions pushed, account linked (1 trade)')
  # B: a NinjaTrader 8 key the add-on never used → « Add-on jamais vu »
  b, eb = trader(p, 'Bruno')
  ok(b.post('/api/sync/key', data=json.dumps({'platform': 'ninjatrader'}), headers=H).status == 200, 'trader B: a NinjaTrader 8 key, never used')
  # a trader who is not an administrator cannot read it
  ok(b.get('/api/admin/sync', headers=H).status == 403, 'api/admin/sync: administrators only (403 for a trader)')

  br = p.chromium.launch()
  for w, h, mob in ((1300, 850, False), (390, 844, True)):
    tag = f'{w}px'
    ctx = br.new_context(storage_state=STATE, locale='fr-CA', viewport={'width': w, 'height': h}, is_mobile=mob, has_touch=mob, device_scale_factor=2 if mob else 1)
    ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'))")
    pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:150]))
    pg.goto(B + '/#admin'); pg.wait_for_selector('#main .ux-sync-admin .ux-sy-list li', timeout=20000); pg.wait_for_timeout(600)
    after = pg.evaluate("(()=>{const s=document.querySelector('#main .ux-sync-admin'), p=document.querySelector('#main .ux-presets-admin'); return !p || !!(p.compareDocumentPosition(s) & Node.DOCUMENT_POSITION_FOLLOWING)})()")
    ok(after and pg.inner_text('#main .ux-sync-admin h2') == 'Synchro', f'{tag} « Synchro » after « Préréglages » on the Admin page')
    cards = pg.eval_on_selector_all('#main .ux-sync-admin .ux-m', 'l => l.map(x => [x.querySelector("small").textContent, +x.querySelector("b").textContent, (x.querySelector("span")||{}).textContent || ""])')
    names = [c[0] for c in cards]
    ok(names == ['Traders sur NinjaTrader 8', 'Traders sur Quantower'] and all(c[1] >= 1 for c in cards) and 'vu(s) en 24 h' in cards[1][2] and 'trade(s) en 7 j' in cards[1][2], f'{tag} one card per platform: traders, seen in 24 h, linked, trades in 7 d ({cards})')
    row = lambda email: pg.evaluate("(e)=>{const l=[...document.querySelectorAll('#main .ux-sy-list li')].find(x=>x.innerText.includes(e)); return l && {c:l.className, b:l.querySelector('b').textContent, chip:l.querySelector('.ux-pr-chip').textContent, t:l.innerText.replace(/\\s+/g,' ')}}", email)
    ra, rb = row(ea), row(eb)
    ok(ra and ra['c'] == 'ux-hl-ok' and ra['b'] == 'Alma Sync' and ra['chip'] == 'Synchronise' and 'Quantower' in ra['t'] and 'Sweep Quantower test' in ra['t'] and ('vu à l’instant' in ra['t'] or 'vu il y a' in ra['t']), f'{tag} trader A: blue « Synchronise », Quantower, add-on version, seen just now ({ra and ra["t"][:140]})')
    ok(ra and '1 relié(s) · 0 à relier · 0 ignoré(s) · 1 trade(s) (1 en 7 j)' in ra['t'], f'{tag} trader A: accounts and trades')
    unk = pg.evaluate("(e)=>{const l=[...document.querySelectorAll('#main .ux-sy-list li')].find(x=>x.innerText.includes(e)); return l && [(l.querySelector('[data-sy-ctr]')||{}).textContent, (l.querySelector('[data-sy-unk]')||{}).textContent, getComputedStyle(l.querySelector('[data-sy-unk]')).color]}", ea)
    alert = pg.inner_text('#main .ux-sync-admin [data-sy-alert]') if pg.locator('#main .ux-sync-admin [data-sy-alert]').count() else ''
    ok(unk and unk[0] == 'Contrats (30 j) : MNQZ6 → MNQ' and unk[1] == 'Non reconnu(s) : CON.F.US.ENQ.Z25' and unk[2] == 'rgb(200, 30, 30)', f'{tag} trader A: contracts received (MNQZ6 → MNQ) and the one Sweep does not recognize, in red ({unk})')
    ok('CON.F.US.ENQ.Z25 (Quantower)' in alert and 'gardent le bon P&L, pas le bon instrument' in alert, f'{tag} alert above the list: the contracts Sweep does not recognize ({alert[:120]})')
    ok(rb and rb['c'] == 'ux-hl-late' and rb['chip'] == 'Add-on jamais vu' and 'NinjaTrader 8' in rb['t'] and 'installé ? clé collée ?' in rb['t'], f'{tag} trader B: gold « Add-on jamais vu », NinjaTrader 8, what to check ({rb and rb["t"][:140]})')
    order = pg.evaluate("(a)=>{const l=[...document.querySelectorAll('#main .ux-sy-list li')].map(x=>x.innerText); return [l.findIndex(t=>t.includes(a[0])), l.findIndex(t=>t.includes(a[1]))]}", [ea, eb])
    ok(0 <= order[0] < order[1], f'{tag} most recently seen first (A before B: {order})')
    ok('swk_' not in pg.inner_text('#main .ux-sync-admin'), f'{tag} never a key')
    ok(pg.evaluate("document.documentElement.scrollWidth <= innerWidth"), f'{tag} no horizontal scroll')
    ok(not errs, f'{tag} no page error' + ('' if not errs else ': ' + ' | '.join(errs[:2])))
    pg.evaluate("document.querySelector('#main .ux-sync-admin').scrollIntoView()"); pg.wait_for_timeout(300)
    pg.screenshot(path=f'{SHOTS}/admin-sync-{w}.png')
    ctx.close()
  br.close()
  a.dispose(); b.dispose()
print('\n%s' % ('%d failed' % fails if fails else 'all passed'))
sys.exit(1 if fails else 0)
