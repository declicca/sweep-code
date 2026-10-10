"""
Sweep — the « Your week » email says the same as the app (brief 01 step 5, lot 3), dev environment with Playwright:
  python3 tests/e2e_weekly_parity.py http://127.0.0.1:8095        (SWEEP_TEST_DB: the dev server's SQLite file)
A trader of its own, one known week (Monday 2026-09-28), saved through the app: trades with checklist answers (a demo
trade, a Saturday and a Sunday trade left out), a question of the trader's own, a tie between two questions, payouts paid,
pending, rejected and paid the next Monday. The recap's first screen computed by the app (weekBrief in src/game.js) and by
the server for the email (GameWeeklyMail::brief, read with tests/weekly_brief.php) must be identical, in FR, EN and ES.
Then the link at the bottom of the email (api/email/weekly): one button stops the email, one starts it again, the mail
apps' one-click « Unsubscribe » works without the app's header, an unknown link says so; phone and computer.
"""
import asyncio, json, os, random, re, subprocess, sys
from playwright.async_api import async_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
DB = os.environ.get('SWEEP_TEST_DB', '/tmp/g/data/journal.db')
APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MON = '2026-09-28'
TRADES = [('2026-09-28', {'plan': 'y', 'stop': 'n', 'size': 'y'}), ('2026-09-28', {'plan': 'y', 'stop': 'n', 'size': 'y', 'aplus': 'y'}),
          ('2026-09-29', {'plan': 'n', 'stop': 'y', 'size': 'n', 'risk': 'na', 'entry': 'y'}), ('2026-10-01', {'plan': 'y', 'stop': 'n', 'aplus': 'y', 'entry': 'y'}),
          ('2026-10-02', {}), ('2026-09-30', {'stop': 'n', 'plan': 'n'}, True), ('2026-10-03', {'plan': 'n'}), ('2026-09-27', {'stop': 'y'})]
PAYOUTS = [('pp1', 'paid', '2026-09-30', 120000, None), ('pp2', 'paid', '2026-10-04', None, 30050), ('pp3', 'requested', '2026-10-01', 90000, None),
           ('pp4', 'paid', '2026-10-05', 90000, None), ('pp5', 'rejected', '2026-09-30', 90000, None)]
fails = 0
def ok(c, what):
    global fails
    print(('ok   ' if c else 'FAIL ') + what); fails += 0 if c else 1
def server(uid, lang):
    r = subprocess.run(['php', os.path.join(APP, 'tests', 'weekly_brief.php'), DB, uid, MON, lang], capture_output=True, text=True, timeout=60)
    if r.returncode: print(r.stderr[:400])
    return json.loads(r.stdout)
async def main():
  async with async_playwright() as p:
    br = await p.chromium.launch()
    ctx = await br.new_context(base_url=B, locale='fr-CA', viewport={'width': 1300, 'height': 850})
    await ctx.add_init_script("sessionStorage.setItem('sw.modal','1')")
    H = {'X-Requested-With': 'fetch', 'Content-Type': 'application/json'}; n = 'wp%06d' % random.randint(0, 999999)
    r = await ctx.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': n + '@t.dev', 'consent': True, 'elapsed': 6000}), headers=H)
    ok(r.ok, f'a trader of its own ({r.status})')
    await ctx.request.post(B + '/api/me/profile', data=json.dumps({'first_name': 'Pia', 'last_name': 'Test'}), headers=H)
    pg = await ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:150]))
    await pg.goto(B + '/#dashboard'); await pg.wait_for_timeout(2500)
    uid = await pg.evaluate("S.me && S.me.id")
    await pg.evaluate("""([T, P]) => { put('firms',{id:'f-wp',name:'Topstep'}); put('accounts',{id:'a-wp',firm_id:'f-wp',name:'Combine 50K',starting_balance_c:5000000,status:'active',phase:'eval',money_type:'eval',rules:{dd_c:200000,dd_type:'eod',target_c:300000}});
      put('settings', Object.assign({}, S.settings, {questions: S.settings.questions.concat([{id:'aplus', text:'Only my A+ setup?', viol:'Not my A+ setup', active:true}])}));
      T.forEach(([d,a,demo],i)=>put('trades',Object.assign({id:'wp-t'+i,account_id:'a-wp',date:d,session_date:true,entry_time:'10:0'+i+':00',exit_time:'10:3'+i+':00',instrument:'NQ',direction:'long',contracts:1,pnl_c:50000,pnl_manual:true,discipline:a}, demo?{demo:true}:{})));
      P.forEach(([id,st,d,net,amt])=>put('payouts',Object.assign({id,account_id:'a-wp',firm_id:'f-wp',status:st,paid_on:d,payment_date:d}, net!=null?{net_c:net,gross_c:net,split_pct:100,fees_c:0}:{}, amt!=null?{amount_c:amt}:{}))); }""", [TRADES, PAYOUTS])
    await pg.wait_for_timeout(3500)   # saved on the server
    for lang in ('fr', 'en', 'es'):
      await pg.evaluate("l => localStorage.setItem('tj.lang', JSON.stringify(l))", lang); await pg.reload(); await pg.wait_for_timeout(2500)
      ok(await pg.evaluate("S.trades.filter(t=>String(t.id).startsWith('wp-t')).length") == len(TRADES), f'{lang} the week\'s trades came back from the server')
      sv = server(uid, lang); s = sv['brief']; s.pop('week', None)
      c = await pg.evaluate("sm => SweepGame.weekBrief('%s', sm)" % MON, {'swept': sv['summary']['swept'], 'streak': sv['summary']['streak']})
      ok(c == s, f'{lang} app and email: the same numbers ({json.dumps(c, ensure_ascii=False)})' + ('' if c == s else f'\n      server: {json.dumps(s, ensure_ascii=False)}'))
      if lang == 'fr':
        ok(s['traded'] == 4 and s['payouts'] == 150050 and s['disc'] is not None, f"fr 4 days traded (demo, Saturday, Sunday left out), payouts 1,200 + 300.50 = 1,500.50 ({s['traded']}, {s['payouts']})")
        ok((s['best'] or {}).get('q') == 'Only my A+ setup?' and (s['work'] or {}).get('q') == 'Ai-je respecté mon stop ?', f"fr own question as written, a tie (A+ and entry, 2 of 2) broken the same way; default question in French ({s['best']}, {s['work']})")
    ok(not errs, 'no page error' + ('' if not errs else ': ' + ' | '.join(errs[:2])))
    await ctx.close()
    # the link at the bottom of the email
    tok = server(uid, 'en')['token']; url = B + '/api/email/weekly?t=' + tok
    for w, h, mob in ((390, 844, True), (1300, 850, False)):
      tag = f'{w}px'
      c2 = await br.new_context(locale='en-US', viewport={'width': w, 'height': h}, is_mobile=mob, has_touch=mob, device_scale_factor=2 if mob else 1)
      pg = await c2.new_page(); cons = []; pg.on('console', lambda m: cons.append(m.text[:120]) if m.type == 'error' else None)
      r = await pg.goto(url); t = re.sub(r'\s+', ' ', await pg.inner_text('body'))
      ok(r.status == 200 and 'Your week by email' in t and await pg.locator('button').inner_text() == 'Stop the weekly email', f'{tag} the page: one button « Stop the weekly email » ({t[:80]})')
      await pg.click('button'); await pg.wait_for_load_state(); t = re.sub(r'\s+', ' ', await pg.inner_text('body'))
      ok('Done' in t and server(uid, 'en')['off'] is True, f'{tag} one tap: stopped ({t[:90]})')
      ok(await pg.evaluate("document.documentElement.scrollWidth <= innerWidth"), f'{tag} no horizontal scroll')
      await pg.screenshot(path=os.path.join(os.environ.get('TMPDIR', '/tmp'), f'weekly-off-{w}.png'))
      await pg.click('button'); await pg.wait_for_load_state()
      ok(server(uid, 'en')['off'] is False and 'Stop the weekly email' in await pg.inner_text('body'), f'{tag} « Get it again »: started again')
      ok(not cons, f'{tag} no console error' + ('' if not cons else ': ' + ' | '.join(cons[:2])))
      await c2.close()
    rq = await br.new_context()
    r = await rq.request.post(url, form={'List-Unsubscribe': 'One-Click'})
    ok(r.status == 200 and server(uid, 'en')['off'] is True, f'the mail apps\' one-click « Unsubscribe » (no app header): stopped ({r.status})')
    r = await rq.request.get(B + '/api/email/weekly?t=' + '0' * 32)
    ok(r.status == 404 and 'no longer valid' in await r.text(), f'an unknown link: « This link is no longer valid. » ({r.status})')
    await rq.close(); await br.close()
    print('all passed' if not fails else f'{fails} failed'); sys.exit(1 if fails else 0)
asyncio.run(main())
