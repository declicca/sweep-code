"""
Sweep — « Same as last » on the manual trade form (brief 02, part 1, improvement 3), dev environment with Playwright:
  python3 tests/e2e_trade_like.py http://127.0.0.1:8095
A trader of its own with two accounts; the last trade: second account, MNQ, short, 3 contracts (an older one: first account,
NQ, long, 1). On a new trade:
 - one chip under the title: « Comme le dernier · MNQ · Vente · 3 »; one tap fills the account, instrument, side and
   contracts (the side was never pre-filled before), then the chip goes away; the trade is saved with them;
 - no previous trade: no chip; FR phone and EN computer, no horizontal scroll, no page error.
"""
import asyncio, json, random, sys
from playwright.async_api import async_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
W = {'fr': 'Comme le dernier MNQ · Vente · 3', 'en': 'Same as last MNQ · Sell · 3'}
fails = 0
def ok(c, what):
    global fails
    print(('ok   ' if c else 'FAIL ') + what); fails += 0 if c else 1
async def trader(br, lang, w, h, mob, tag):
    ctx = await br.new_context(base_url=B, locale=lang, viewport={'width': w, 'height': h}, is_mobile=mob, has_touch=mob, device_scale_factor=2 if mob else 1)
    await ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('%s'))" % lang)
    H = {'X-Requested-With': 'fetch', 'Content-Type': 'application/json'}
    r = await ctx.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': 'tl%06d@t.dev' % random.randint(0, 999999), 'consent': True, 'elapsed': 6000}), headers=H)
    ok(r.ok, f'{tag} a trader of its own ({r.status})')
    await ctx.request.post(B + '/api/me/profile', data=json.dumps({'first_name': 'Lia', 'last_name': 'Test'}), headers=H)
    pg = await ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:150]))
    await pg.goto(B + '/#trades'); await pg.wait_for_timeout(2500)
    await pg.evaluate("""() => { put('accounts', {id:'tl-a', name:'Main 50K', status:'active', phase:'live', money_type:'live', starting_balance_c:5000000, rules:{}});
      put('accounts', {id:'tl-b', name:'Second 50K', status:'active', phase:'live', money_type:'live', starting_balance_c:5000000, rules:{}}); }""")
    await pg.wait_for_timeout(700)
    return ctx, pg, errs
async def main():
  async with async_playwright() as p:
    br = await p.chromium.launch()
    for lang, w, h, mob in (('fr', 390, 844, True), ('en', 1300, 850, False)):
      tag = f'{lang} {w}px'
      # no previous trade: no chip
      ctx, pg, errs = await trader(br, lang, w, h, mob, tag + ' (new)')
      await pg.evaluate("openTicket(null,{manual:true})"); await pg.wait_for_selector('#tkSlide.open', timeout=8000); await pg.wait_for_timeout(700)
      ok(await pg.locator('#tkSlide .nav-like').count() == 0, f'{tag} no previous trade: no « same as last »')
      await ctx.close()
      ctx, pg, errs = await trader(br, lang, w, h, mob, tag)
      await pg.evaluate("""() => { put('trades', {id:'tl-0', account_id:'tl-a', instrument:'NQ', direction:'long', contracts:1, entry:21000, exit:21004, date:'2026-10-07', session_date:true, entry_time:'10:00', exit_time:'10:05', pnl_c:8000, discipline:{}});
        put('trades', {id:'tl-1', account_id:'tl-b', instrument:'MNQ', direction:'short', contracts:3, entry:21010, exit:21000, date:'2026-10-08', session_date:true, entry_time:'11:00', exit_time:'11:20', pnl_c:6000, discipline:{}}); }""")
      await pg.wait_for_timeout(700)
      await pg.evaluate("openTicket(null,{manual:true})"); await pg.wait_for_selector('#tkSlide.open .nav-like', timeout=8000); await pg.wait_for_timeout(400)
      chip = ' '.join((await pg.locator('#tkSlide .nav-like').inner_text()).split())
      dir0 = await pg.evaluate("TK.dir || ''")
      ok(chip == W[lang] and dir0 == '', f'{tag} one chip: « {chip} » (side not chosen yet: {dir0!r})')
      await pg.locator('#tkSlide .nav-like').click(); await pg.wait_for_timeout(500)
      st = await pg.evaluate("""(()=>({acc: (document.querySelector('#tkSlide select[data-tk="account"]')||{}).value, inst: (document.querySelector('#tkSlide select[data-tk="inst"]')||{}).value,
        dir: TK.dir, qty: (document.querySelector('#tkSlide [data-tk="qty"]')||{}).value, on: [...document.querySelectorAll('#tkSlide [data-act="tk-dir"]')].filter(b => /\\b(on|sel|active)\\b/.test(b.className) || b.getAttribute('aria-pressed') === 'true').map(b => b.dataset.v),
        chip: document.querySelectorAll('#tkSlide .nav-like').length}))()""")
      ok(st['acc'] == 'tl-b' and st['inst'] == 'MNQ' and st['dir'] == 'short' and str(st['qty']) == '3' and st['chip'] == 0, f'{tag} one tap: account, MNQ, short, 3 contracts filled, chip gone ({st})')
      ok(st['on'] == ['short'], f'{tag} « short » shows as chosen ({st["on"]})')
      n0 = await pg.evaluate("S.trades.length")
      await pg.evaluate("() => { TK.date = '2026-10-09'; TK.entryTime = '10:00:00'; TK.exitTime = '10:10:00'; TK.entry = 21020; TK.exit = 21015; tkRefresh(); }")
      await pg.locator('#tkSlide [data-act="tk-save"]').click(); await pg.wait_for_function(f"S.trades.length > {n0}", timeout=10000)
      t = await pg.evaluate("(()=>{const t=S.trades.find(x=>x.date==='2026-10-09'); return t ? {acc:t.account_id, inst:t.instrument, dir:t.direction, qty:t.contracts, pnl:t.pnl_c} : null})()")
      ok(t == {'acc': 'tl-b', 'inst': 'MNQ', 'dir': 'short', 'qty': 3, 'pnl': 3000}, f'{tag} saved with them: short 3 MNQ 21020 → 21015 = 5 pts × 3 × $2 = $30 ({t})')
      ok(await pg.evaluate("document.documentElement.scrollWidth <= innerWidth"), f'{tag} no horizontal scroll')
      ok(not errs, f'{tag} no page error' + ('' if not errs else ': ' + ' | '.join(errs[:2])))
      await ctx.close()
    await br.close()
    print('all passed' if not fails else f'{fails} failed'); sys.exit(1 if fails else 0)
asyncio.run(main())
