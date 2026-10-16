"""
Sweep — account alerts in copy trading: one per copy group (brief 00, phase 1.2-j; question 10), dev environment:
  python3 tests/e2e_prop_alerts_group.py http://127.0.0.1:8095 [storage_state, unused: it signs up its own trader]
A trader of its own, 4 accounts with a $1,000 daily limit (one at $950). Today, one trade copied on 3 of them (−$800 each,
past 75 %) and one trade alone on the 4th (−$800). The bell gets 2 alerts, not 4: one for the copy group, about its most
fragile account (the one with the least room left, « +2 » copies), one for the account alone. Saving again, or reloading:
nothing more (once per group, level and day). Before 16 Oct.: one alert per account (10 copied accounts: up to 40 a day).
"""
import json, random, sys
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
H = {'Content-Type': 'application/json', 'X-Requested-With': 'fetch'}
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)

INBOX = "fetch('api/notifications',{headers:{'X-Requested-With':'fetch'},credentials:'same-origin'}).then(r=>r.json()).then(j=>(j.items||j.notifications||[]).filter(n=>n.type==='prop_limit').map(n=>[n.title_key,(n.params||{}).account]))"
with sync_playwright() as p:
  br = p.chromium.launch()
  for lang in ('fr', 'en'):
    ctx = br.new_context(viewport={'width': 1300, 'height': 850})
    ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('%s'))" % lang)
    r = ctx.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': 'pa%06d@t.dev' % random.randint(0, 999999), 'consent': True, 'elapsed': 6000}), headers=H)
    ok(r.ok, f'{lang} a trader of its own ({r.status})')
    pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:160])); sent = []
    pg.on('request', lambda q: sent.append(json.loads(q.post_data or '{}')) if 'notifications/prop-alert' in q.url else None)
    pg.goto(B + '/#dashboard'); pg.wait_for_timeout(2500)
    pg.evaluate("""() => { const acc = (id, name, dll) => put('accounts', { id, name, status: 'active', phase: 'funded', money_type: 'sim', starting_balance_c: 5000000, rules: { dll_c: dll } });
      acc('pa-1', 'Apex 1', 100000); acc('pa-2', 'Apex 2', 95000); acc('pa-3', 'Apex 3', 100000); acc('pa-4', 'Topstep', 100000); }""")
    pg.wait_for_timeout(1200)
    pg.evaluate("""() => { const d = todayStr(), t = (id, a, g) => put('trades', Object.assign({ id, account_id: a, instrument: 'NQ', direction: 'long', contracts: 1, entry: 21000, exit: 20960, pnl_c: -80000, pnl_manual: true, date: d, session_date: true, entry_time: '10:00', exit_time: '10:05' }, g ? { copy_group: g } : {}));
      t('pa-t1', 'pa-1', 'pa-g'); t('pa-t2', 'pa-2', 'pa-g'); t('pa-t3', 'pa-3', 'pa-g'); t('pa-t4', 'pa-4', null); }""")
    pg.wait_for_timeout(4000)
    got = sorted([(x.get('account'), x.get('kind'), x.get('level'), x.get('n', 1)) for x in sent])
    ok(got == [('pa-2', 'dll', 75, 3), ('pa-4', 'dll', 75, 1)], f'{lang} 2 alerts, not 4: the copy group (its most fragile account, Apex 2) and the account alone ({got})')
    inbox = pg.evaluate(INBOX)
    ok(len(inbox) == 2 and any('Apex 2' in (b or '') and '+2' in (b or '') for _, b in inbox), f'{lang} the bell: 2 alerts, « Apex 2 +2 » for the group ({inbox})')
    sent.clear(); pg.evaluate("sessionStorage.clear()"); pg.reload(); pg.wait_for_timeout(4500)
    inbox2 = pg.evaluate(INBOX)
    ok(len(inbox2) == 2, f'{lang} reloaded: still 2 in the bell (once per group, level and day) ({len(inbox2)}, sent again: {len(sent)})')
    ok(not errs, f'{lang} no page error ({errs[:2]})')
    ctx.close()
  br.close()
print(f'{fails} failed' if fails else 'all passed')
sys.exit(1 if fails else 0)
