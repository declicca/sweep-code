"""
Sweep — what the week's recap says (brief 01 step 5), dev environment with Playwright:
  python3 tests/e2e_weekly_content.py http://127.0.0.1:8095
A trader of its own, one known week (Monday 2026-09-28): 4 trades on 3 days with checklist answers, profit on an
evaluation (simulated), one payout paid. The server's recap state is set to « ready » for that week (the moment is tested
in tests/weekly_test.php). The first screen shows:
 - the swept-day streak, the week's discipline score (average of the trades' scores), swept days out of days traded;
 - the best habit (the checklist question answered « yes » most often) and one point to work on, said positively;
 - the payouts received that week (real money) — and no other dollar amount: simulated P&L is never shown as money earned.
"""
import asyncio, json, random, re, sys
from playwright.async_api import async_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
MON = '2026-09-28'
# per trade: date, P&L (cents), checklist answers
TRADES = [('2026-09-28', 120000, {'plan': 'y', 'stop': 'n', 'size': 'y'}), ('2026-09-28', 80000, {'plan': 'y', 'stop': 'n', 'size': 'y'}),
          ('2026-09-29', -30000, {'plan': 'y', 'stop': 'y', 'size': 'n'}), ('2026-10-01', 50000, {'plan': 'y', 'stop': 'n', 'size': 'y', 'risk': 'na'})]
def disc(a): y = sum(v == 'y' for v in a.values()); n = sum(v in ('y', 'n') for v in a.values()); return y / n * 100
DISC = round(sum(disc(a) for _, _, a in TRADES) / len(TRADES))   # (66.7 + 66.7 + 66.7 + 66.7) / 4 = 67
SUMMARY = {'days': [{'day': d, 'market': True, 'rings': {'plan': 100, 'execution': 100, 'review': 100 if i < 2 else 0}, 'swept': i < 2} for i, d in enumerate(['2026-09-28', '2026-09-29', '2026-09-30', '2026-10-01', '2026-10-02'])],
           'swept': 2, 'streak': 3, 'missions': {'done': 1, 'total': 3}}
fails = 0
def ok(c, what):
    global fails
    print(('ok   ' if c else 'FAIL ') + what); fails += 0 if c else 1
async def main():
  async with async_playwright() as p:
    br = await p.chromium.launch()
    for lang, w, h, mob in (('fr', 390, 844, True), ('en', 1440, 900, False)):
      tag = f'{lang} {w}px'
      ctx = await br.new_context(base_url=B, locale=lang, viewport={'width': w, 'height': h}, is_mobile=mob, has_touch=mob, device_scale_factor=2 if mob else 1)
      await ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('%s'))" % lang)
      H = {'X-Requested-With': 'fetch', 'Content-Type': 'application/json'}; n = 'wk%06d' % random.randint(0, 999999)
      r = await ctx.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': n + '@t.dev', 'consent': True, 'elapsed': 6000}), headers=H)
      ok(r.ok, f'{tag} a trader of its own ({r.status})')
      await ctx.request.post(B + '/api/me/profile', data=json.dumps({'first_name': 'Wes', 'last_name': 'Test'}), headers=H)
      async def weekly(route):   # the server says: the recap of that week is ready
        await route.fulfill(status=200, content_type='application/json', body=json.dumps({'open': True, 'week': MON, 'seen': False, 'done': False, 'chest_opened': False,
          'intention': None, 'keys': 0, 'answers': {}, 'summary': SUMMARY, 'reveal': None, 'can_second': False, 'odds': {}}))
      await ctx.route('**/api/game/weekly', weekly)
      pg = await ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:150]))
      await pg.goto(B + '/#dashboard'); await pg.wait_for_timeout(2500)
      await pg.evaluate("""(T) => { put('firms',{id:'f-wk',name:'Topstep'}); put('accounts',{id:'a-wk',firm_id:'f-wk',name:'Combine 50K',starting_balance_c:5000000,status:'active',phase:'eval',money_type:'eval',rules:{dd_c:200000,dd_type:'eod',target_c:300000}});
        T.forEach(([d,c,a],i)=>put('trades',{id:'wk-t'+i,account_id:'a-wk',date:d,session_date:true,entry_time:'10:0'+i+':00',exit_time:'10:3'+i+':00',instrument:'NQ',direction:'long',contracts:1,pnl_c:c,pnl_manual:true,discipline:a}));
        put('payouts',{id:'wk-p1',account_id:'a-wk',firm_id:'f-wk',gross_c:120000,split_pct:100,fees_c:0,net_c:120000,amount_c:120000,status:'paid',payment_date:'2026-09-30',paid_on:'2026-09-30'}); }""", TRADES)
      await pg.wait_for_timeout(1500)
      await pg.evaluate("SweepGame.open('weekly')"); await pg.wait_for_selector('#gSheet .wk-brief', timeout=10000); await pg.wait_for_timeout(500)
      txt = re.sub(r'[\s  ]+', ' ', await pg.evaluate("document.querySelector('#gSheet .wk-body').innerText"))
      tiles = await pg.evaluate("[...document.querySelectorAll('#gSheet .wk-brief > div')].map(d=>d.innerText.replace(/\\s+/g,' ').trim())")
      want = {'fr': ['3 jours d’affilée', f'{DISC} %', '2 sur 3 jours tradés'], 'en': ['3 days in a row', f'{DISC} %', '2 of 3 days traded']}[lang]
      ok(all(any(x in re.sub(r'[  ]', ' ', t) for t in tiles) for x in want), f'{tag} streak, discipline {DISC} %, swept days out of days traded ({tiles})')
      hab = await pg.evaluate("[...document.querySelectorAll('#gSheet .wk-habits li')].map(l=>l.innerText.replace(/\\s+/g,' ').trim())")
      ok(any(('4 fois sur 4' if lang == 'fr' else '4 times out of 4') in x for x in hab), f'{tag} best habit: the question answered « yes » 4 times out of 4 ({hab[:1]})')
      ok(any(('Vise un « oui »' if lang == 'fr' else 'Aim for a « yes »') in x for x in hab), f'{tag} one point to work on, said positively ({hab[1:2]})')
      ok(any('1 200' in re.sub(r'[  ,]', ' ', x) and '$' in x for x in hab), f'{tag} payouts received this week: 1,200 $ ({hab[2:3]})')
      dollars = [m for m in re.findall(r'[+−-]?\$?\d[\d\s,.]*\s?\$?', txt) if '$' in m]
      ok(len(dollars) == 1, f'{tag} no other dollar amount on the first screen: no simulated P&L shown as money earned ({dollars})')
      ok(await pg.evaluate("document.documentElement.scrollWidth <= innerWidth"), f'{tag} no horizontal scroll')
      ok(not errs, f'{tag} no page error' + ('' if not errs else ': ' + ' | '.join(errs[:2])))
      await ctx.close()
    await br.close()
    print('all passed' if not fails else f'{fails} failed'); sys.exit(1 if fails else 0)
asyncio.run(main())
