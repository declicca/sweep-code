"""
Sweep — the same trade saved twice is noticed (brief 02, part 1, « Vérifier » + improvement 2), dev environment with Playwright:
  python3 tests/e2e_trade_dup.py http://127.0.0.1:8095
A trader of its own with a trade already saved (NQ, long, 1 contract, 10:32, 21000 → 21006). The rule is the one of the
« X trades found » screen: same account, instrument, side, contracts, session, entry within a minute, same prices.
 - manual form, the same trade at 10:33: « Ce trade ressemble à celui de 10 h 32. L’ajouter quand même ? » above « Save »,
   nothing saved until « Ajouter quand même »; also with ⌘/Ctrl + Enter;
 - a different trade (10:35, or another price) is saved at once, no question;
 - the single screenshot form asks the same question; FR phone and EN computer, no page error;
 - the quick sheet (net P&L only, audit of 16 Oct.): two quick trades of different P&L the same minute are both saved, no
   question; the same P&L again is asked; a trade saved without a time is never « the one at . ».
"""
import asyncio, json, random, sys
from playwright.async_api import async_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
D = '2026-10-08'
W = {'fr': ('Ce trade ressemble à celui de 10 h 32. L’ajouter quand même ?', 'Ajouter quand même'), 'en': ('This trade looks like the one at 10:32. Add it anyway?', 'Add anyway')}
DAY = {'fr': 'Ce trade ressemble à un trade déjà enregistré ce jour-là.', 'en': 'This trade looks like one already saved that day.'}
fails = 0
def ok(c, what):
    global fails
    print(('ok   ' if c else 'FAIL ') + what); fails += 0 if c else 1
async def main():
  async with async_playwright() as p:
    br = await p.chromium.launch()
    for lang, w, h, mob in (('fr', 390, 844, True), ('en', 1300, 850, False)):
      tag = f'{lang} {w}px'; msg, btn = W[lang]
      ctx = await br.new_context(base_url=B, locale=lang, viewport={'width': w, 'height': h}, is_mobile=mob, has_touch=mob, device_scale_factor=2 if mob else 1)
      await ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('%s'))" % lang)
      H = {'X-Requested-With': 'fetch', 'Content-Type': 'application/json'}
      r = await ctx.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': 'td%06d@t.dev' % random.randint(0, 999999), 'consent': True, 'elapsed': 6000}), headers=H)
      ok(r.ok, f'{tag} a trader of its own ({r.status})')
      await ctx.request.post(B + '/api/me/profile', data=json.dumps({'first_name': 'Dee', 'last_name': 'Test'}), headers=H)
      pg = await ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:150]))
      await pg.goto(B + '/#trades'); await pg.wait_for_timeout(2500)
      await pg.evaluate("""(D) => { put('accounts', {id:'td-a', name:'Main 50K', status:'active', phase:'live', money_type:'live', starting_balance_c:5000000, rules:{}});
        put('trades', {id:'td-0', account_id:'td-a', instrument:'NQ', direction:'long', contracts:1, entry:21000, exit:21006, date:D, session_date:true, entry_time:'10:32', exit_time:'10:40', pnl_c:12000, discipline:{}});
        editDoc('settings','settings', d => { d.add_mode_pref = 'shot'; }); }""", D)
      await pg.wait_for_timeout(900)
      n = lambda: pg.evaluate("S.trades.filter(t => !t.demo).length")
      async def form(time, entry, exit):
        await pg.evaluate("openTicket(null,{manual:true})"); await pg.wait_for_selector('#tkSlide.open', timeout=8000); await pg.wait_for_timeout(500)
        await pg.evaluate("([D, tm, e, x]) => { TK.account = 'td-a'; TK.inst = 'NQ'; TK.dir = 'long'; TK.qty = 1; TK.date = D; TK.entryTime = tm; TK.exitTime = '10:41:00'; TK.entry = e; TK.exit = x; TK.copyTo = new Set(); tkRefresh(); }", [D, time, entry, exit])
      async def gone(): await pg.evaluate("closeTicket()"); await pg.wait_for_timeout(500)
      # the same trade, one minute later
      await form('10:33:00', 21000, 21006); c0 = await n()
      await pg.locator('#tkSlide [data-act="tk-save"]').click(); await pg.wait_for_timeout(1500)
      box = await pg.evaluate("(document.querySelector('#tkSlide .nav-dup')||{}).innerText||''")
      ok(' '.join(box.split()).startswith(msg) and await n() == c0, f'{tag} manual form, the same trade: « {" ".join(box.split())[:70]} », nothing saved yet')
      above = await pg.evaluate("(()=>{const b=document.querySelector('#tkSlide .nav-dup'), s=document.querySelector('#tkSlide [data-act=\"tk-save\"]'); return !!(b && s && (b.compareDocumentPosition(s) & Node.DOCUMENT_POSITION_FOLLOWING))})()")
      ok(above, f'{tag} the question is right above « Save »')
      await pg.locator('#tkSlide [data-dup-ok]', has_text=btn).click(); await pg.wait_for_timeout(2200)
      ok(await n() == c0 + 1, f'{tag} « {btn} »: saved ({await n() - c0})')
      await gone()
      # with ⌘/Ctrl + Enter
      await form('10:32:30', 21000, 21006); c0 = await n()
      await pg.locator('#tkSlide [data-tk="notes"]').focus(); await pg.keyboard.press('Control+Enter'); await pg.wait_for_timeout(1500)
      ok(await pg.locator('#tkSlide .nav-dup').count() == 1 and await n() == c0, f'{tag} ⌘/Ctrl + Enter asks the same question')
      await gone()
      # different trades: saved at once
      await form('10:35:00', 21000, 21006); c0 = await n()
      await pg.locator('#tkSlide [data-act="tk-save"]').click(); await pg.wait_for_timeout(2200)
      ok(await n() == c0 + 1 and await pg.locator('#tkSlide .nav-dup').count() == 0, f'{tag} 3 minutes later: another trade, saved at once')
      await gone()
      await form('10:32:00', 21001, 21006); c0 = await n()
      await pg.locator('#tkSlide [data-act="tk-save"]').click(); await pg.wait_for_timeout(2200)
      ok(await n() == c0 + 1, f'{tag} same minute, another entry price: another trade, saved at once')
      await gone()
      # the single screenshot form, filled by hand
      await pg.evaluate("openTicket(null)"); await pg.wait_for_selector('.nav-am.open', timeout=8000); await pg.wait_for_timeout(500)
      if await pg.locator('.nav-am select[data-am-f="account"]').count(): await pg.select_option('.nav-am select[data-am-f="account"]', 'td-a')   # one account: chosen already
      if await pg.locator('.nav-am select[data-am-f="inst"]').count(): await pg.select_option('.nav-am select[data-am-f="inst"]', 'NQ')
      # the fields show once a screenshot is read: set them the way typing does (an input event)
      await pg.evaluate("(F) => { for (const [k, v] of F) { const i = document.querySelector('.nav-am input[data-am-f=\"' + k + '\"]'); i.value = v; i.dispatchEvent(new Event('input', { bubbles: true })); } }",
                        [['date', D], ['time', '10:32'], ['entry', '21000'], ['exit', '21006'], ['qty', '1'], ['net', '120']])
      c0 = await n()
      await pg.evaluate("document.querySelector('.nav-am [data-am=\"save\"]').click()"); await pg.wait_for_timeout(900)
      err = await pg.evaluate("(document.querySelector('.nav-am-err')||{}).innerText||''")
      ok(' '.join(err.split()).startswith(msg) and await n() == c0, f'{tag} single screenshot, the same trade: the same question ({" ".join(err.split())[:60]})')
      await pg.evaluate("document.querySelector('.nav-am [data-am=\"dupok\"]').click()"); await pg.wait_for_timeout(1500)
      ok(await n() == c0 + 1, f'{tag} « {btn} » on the screenshot form: saved')
      # the quick sheet: the net P&L and the side only
      async def quick(net, side='short'):
        await pg.evaluate("openTicket(null)"); await pg.wait_for_selector('.nav-am.open', timeout=8000); await pg.wait_for_timeout(400)
        await pg.locator('.nav-am input[data-am-f="net"]').fill(net)
        await pg.locator(f'.nav-am [data-am-seg="dir"][data-v="{side}"]').click(); await pg.wait_for_timeout(200)
        c0 = await n(); await pg.locator('.nav-am [data-am="save"]').click(); await pg.wait_for_timeout(1300)
        return await n() - c0, ' '.join((await pg.evaluate("(document.querySelector('.nav-am.open .nav-am-err')||{}).innerText||''")).split())
      a1, e1 = await quick('-400'); a2, e2 = await quick('-300')
      ok(a1 == 1 and a2 == 1 and not e1 and not e2, f'{tag} quick sheet: −$400 then −$300 the same minute, both saved, no question ({a1}, {a2}, {e2[:50]})')
      a3, e3 = await quick('-300')
      ok(a3 == 0 and e3.startswith(msg.split(' 10')[0]) and ' . ' not in e3 and not e3.startswith(DAY[lang]), f'{tag} the same −$300 again: asked, with its time ({e3[:70]})')
      await pg.evaluate("document.querySelector('.nav-am [data-am=\"dupok\"]').click()"); await pg.wait_for_timeout(1300)
      await pg.evaluate("put('trades', {id:'td-nt', account_id:'td-a', instrument:'NQ', direction:'short', contracts:1, date:todayStr(), session_date:true, entry_time:'', pnl_c:-25000, pnl_manual:true, discipline:{}})"); await pg.wait_for_timeout(700)
      a4, e4 = await quick('-250')
      ok(a4 == 0 and e4.startswith(DAY[lang]), f'{tag} like a trade saved without a time: « {e4[:70]} » (never « the one at . »)')
      await pg.evaluate("document.querySelector('.nav-am [data-am=\"close\"]').click()"); await pg.wait_for_timeout(500)
      ok(await pg.evaluate("document.documentElement.scrollWidth <= innerWidth"), f'{tag} no horizontal scroll')
      ok(not errs, f'{tag} no page error' + ('' if not errs else ': ' + ' | '.join(errs[:2])))
      await ctx.close()
    await br.close()
    print('all passed' if not fails else f'{fails} failed'); sys.exit(1 if fails else 0)
asyncio.run(main())
