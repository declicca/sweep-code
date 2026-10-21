"""
Sweep — clarity (points B9 to B17), dev environment with Playwright:
  python3 tests/e2e_clarity.py http://127.0.0.1:8095 /tmp/show_state.json
"""
import asyncio, sys
from playwright.async_api import async_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)
CUT = """[...document.querySelectorAll('#main *')].filter(e=>e.children.length===0&&/\\d/.test(e.textContent)&&/\\$/.test(e.textContent)&&e.getClientRects().length).filter(e=>{const s=getComputedStyle(e); const p=e.parentElement, ps=p&&getComputedStyle(p);
  return ((s.textOverflow==='ellipsis'||s.overflow==='hidden'||s.overflowX==='hidden')&&e.scrollWidth>e.clientWidth+1) || (ps&&(ps.overflow==='hidden'||ps.textOverflow==='ellipsis')&&e.getBoundingClientRect().right>p.getBoundingClientRect().right+1)}).map(e=>e.textContent.trim())"""

async def page(br, desk, lang='fr'):
  kw = {'viewport': {'width': 1440, 'height': 900}} if desk else {'viewport': {'width': 390, 'height': 844}, 'is_mobile': True, 'has_touch': True}
  ctx = await br.new_context(**kw, locale='fr-CA', storage_state=STATE)
  await ctx.add_init_script(f"sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('{lang}'))")
  pg = await ctx.new_page(); dlg = []
  pg.on('dialog', lambda d: (dlg.append(d.message), asyncio.ensure_future(d.dismiss())))
  await pg.goto(B + '/?x=1#dashboard'); await pg.wait_for_timeout(2600)
  return ctx, pg, dlg

async def main():
  async with async_playwright() as p:
    br = await p.chromium.launch()
    # ── phone
    ctx, pg, dlg = await page(br, False)
    await pg.wait_for_timeout(6000)
    ok(await pg.locator('#main .nav-rt').count() == 1 and await pg.locator('#main .nav-rt.closed-rt').count() == 0, 'B9 the routine is open (still open after 8 s)')
    ok(await pg.locator('#main .nav-rt-s.next .btn.primary').count() == 1, 'B9 the next step stands out with its own button')
    await pg.evaluate("""(async()=>{const a=S.accounts.find(x=>x.status!=='archived'); put('trades',{id:'b10-big',account_id:a.id,instrument:'NQ',direction:'short',contracts:1,entry:1,exit:2,pnl_c:-1234567,pnl_manual:true,date:todayStr(),entry_time:'10:00',exit_time:'10:01',session_date:true}); await new Promise(r=>setTimeout(r,1800));})()""")
    cut = []
    for h in ['#dashboard', '#accounts', '#analytics', '#trades']:
      await pg.evaluate(f"location.hash='{h}'"); await pg.wait_for_timeout(1500); cut += [f'{h}: {x}' for x in await pg.evaluate(CUT)]
    ok(not cut, f'B10 a −12,345.67 day at 390 px: no figure cut ({cut[:4]})')
    await pg.evaluate("remove('trades','b10-big')"); await pg.wait_for_timeout(500)
    # B12 account page
    acc = await pg.evaluate("(S.accounts.find(a=>a.status!=='archived'&&S.trades.some(t=>t.account_id===a.id))||{}).id")
    await pg.evaluate(f"location.hash='#account/{acc}'"); await pg.wait_for_timeout(1600)
    row = await pg.evaluate("(()=>{const r=document.querySelector('#main > .row'); return r?[...r.querySelectorAll('button, summary')].filter(b=>b.getClientRects().length&&!b.closest('.menu-pop')&&!b.matches('.nav-accname')).map(b=>b.textContent.trim()):[]})()")
    ok(len([x for x in row if x != '⋯']) == 1 and '⋯' in row, f'B12 one button + the « ⋯ » menu ({row})')
    items = await pg.evaluate("[...document.querySelectorAll('#main .acc-menu .menu-pop button')].map(b=>b.textContent.trim())")
    ok(any('Retirer le compte' in x for x in items) and not any('Fermer' in x for x in items) and any('chou' in x for x in items) and any('Supprimer' in x for x in items), f'B12 the menu: remove (with a result, 15 Oct.), mark as failed, delete ({items})')
    backs = await pg.evaluate("[...document.querySelectorAll('#main a[href=\"#accounts\"]')].filter(a=>a.getClientRects().length).length")
    ok(backs == 1, f'B12 one way back ({backs})')
    ok('Ouvrir le tableau de bord' not in await pg.evaluate("document.getElementById('main').innerText"), 'B12 no « Ouvrir le tableau de bord »')
    txt = await pg.evaluate("document.getElementById('main').innerText")
    ok('Drawdown max' not in txt, 'B12 « Drawdown max » is gone (« Pire recul »)')
    # B14 copy banner only when another account traded the same session
    tid = await pg.evaluate("""(()=>{const a=S.accounts.filter(x=>x.status!=='archived'); const id='b14-'+Date.now(); put('trades',{id,account_id:a[0].id,instrument:'NQ',direction:'long',contracts:1,entry:1,exit:2,pnl_c:100,pnl_manual:true,date:'2026-07-01',entry_time:'10:00',exit_time:'10:01',session_date:true}); return id})()""")
    await pg.wait_for_timeout(700); await pg.evaluate(f"location.hash='#trade/{tid}'"); await pg.wait_for_timeout(1500)
    ok(await pg.locator('#main .nav-copy:not(.done)').count() == 0 and await pg.locator('#main [data-act=copy-open]').count() >= 1, 'B14 no other account traded that session: no banner, the action stays in « ⋯ »')
    await pg.evaluate(f"remove('trades','{tid}')")
    # B15 settings
    await pg.evaluate("location.hash='#settings'"); await pg.wait_for_timeout(1800)
    g = await pg.evaluate("[...document.querySelectorAll('#main details.nav-sgd > summary')].map(s=>s.textContent.trim())")
    last = await pg.evaluate("(()=>{const m=document.getElementById('main'); const k=[...m.children].filter(c=>c.getClientRects().length); return k.length?k[k.length-1].className:''})()")
    ok(len(g) == 5 and g[-1] in ('Avancé', 'Advanced', 'Avanzado'), f'B15 five foldable groups, the advanced options last (brief 03 step 5) ({g})')
    ok('nav-logout' in last, f'B15 « Déconnexion » at the bottom ({last})')
    # B16 sample data
    await pg.evaluate("void loadDemo()")   # not awaited: it waits for the answer in the window
    ask = ''
    for _ in range(40):   # the sample trades are built on real candles first: up to 20 s
      await pg.wait_for_timeout(500); ask = await pg.evaluate("(document.querySelector('aside.nav-ask.open')||{}).innerText||''")
      if ask: break
    import re
    ok(bool(ask) and re.search(r'\d+ trades', ask) and not dlg, f'B16 the app’s own window with the number of trades ({ask[:90]!r}), no browser window')
    if ask: await pg.locator('aside.nav-ask [data-ask="0"]').click(); await pg.wait_for_timeout(400)
    # B17
    fmt = await pg.evaluate("[moneyU(168800), money(-1234567), moneyShort(168800)]")
    ok(fmt[0] == '1\u202f688\u00a0$' and fmt[1].startswith('−12\u202f345,67'), f'B17 French money format ({fmt})')
    await pg.evaluate("location.hash='#nope/xyz'"); await pg.wait_for_timeout(1200)
    ok(await pg.evaluate("location.hash") == '#dashboard', 'B17 an unknown page → Today')
    for h in ['#calendar', '#journal']:
      await pg.evaluate(f"location.hash='{h}'"); await pg.wait_for_timeout(1200)
      ok(await pg.locator('.main-wrap .top .nav-imp').count() == 0, f'B17 no CSV button on {h}')
    await ctx.close()
    # ── computer
    ctx, pg, dlg = await page(br, True)
    await pg.wait_for_timeout(1500)
    # the sidebar stays the icon rail (the page names show when it opens), as Mateo prefers
    # the columns are balanced in passes, as late content arrives (nav.js B11: 0.7, 1.6 and 3.2 s after Today is drawn): read until
    # the balance is reached, 8 s at most (21 Oct.: a busy CI machine read them before the last pass). The balance's promise
    # (nav.js B11): a gap of 20 % at most, or else no card it may still move (not moved yet, not the day, the routine or the
    # merged card) would make the gap smaller — the columns measured as the app measures them (each shown card + its 16 px gap).
    # 21 Oct.: the CI's fonts gave 20.1 % then 20.2 % with no card left to move; the test asked for 20 % the app never promises.
    B11 = """(() => { const a = document.querySelector('#main .d-col-a'), b = document.querySelector('#main .d-col-b'); if (!a || !b) return null;
      const h = (c) => [...c.children].reduce((s, x) => s + (x.getClientRects().length ? x.getBoundingClientRect().height + 16 : 0), 0);
      const ha = h(a), hb = h(b), big = ha > hb ? a : b, hi = Math.max(ha, hb), lo = Math.min(ha, hb), gap = hi ? (hi - lo) / hi : 0;
      const mg = big.querySelector(':scope > .nav-merge');
      const cand = [...big.children].filter((x) => x.getClientRects().length && !x.dataset.balMoved && !x.matches('.d-today, .nav-rt, .d-perf, .nav-merge, .d-news, .nav-trial'))
        .concat(mg ? [...mg.children].filter((x) => x.matches('.d-pay, .d-cal') && !x.dataset.balMoved && x.getClientRects().length) : []);
      const helps = cand.filter((c) => { const ch = c.getBoundingClientRect().height + 16; return Math.abs((hi - ch) - (lo + ch)) < hi - lo; }).map((c) => c.className.split(' ').find((k) => /^d-/.test(k)) || c.className);
      const cards = [a, b].map((c) => [...c.children].filter((x) => x.getClientRects().length).map((x) => (x.className.split(' ').find((k) => /^(d-|nav-)/.test(k)) || '?') + ':' + Math.round(x.getBoundingClientRect().height)));
      return { hs: [Math.round(ha), Math.round(hb)], gap: Math.round(gap * 1000) / 10, ok: gap <= 0.2 || !helps.length, helps, cards, passes: (document.querySelector('#main .nav-dash') || {}).__bal || 0 }; })()"""
    for i in range(10):
      bl = await pg.evaluate(B11)
      if bl and bl['ok']: break
      await pg.wait_for_timeout(800)
    ok(bool(bl and bl['ok']), f'B11 balanced columns, or no card left that would make them closer ({bl})')
    await ctx.close(); await br.close()
  print(f'\n{"all passed" if not fails else str(fails) + " failed"}'); sys.exit(1 if fails else 0)
asyncio.run(main())
