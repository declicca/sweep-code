"""
Sweep — rows that open on a tap and boxes that stay closed (dev environment with Playwright):
  python3 tests/e2e_rows_open.py http://127.0.0.1:8095 /tmp/show_state.json
 - Payouts & expenses: a row opens its edit form on a tap (no « Edit » button); « Share » and « Mark as paid » do not open it;
 - Accounts: the add-account box is closed when the page opens, even if it was left open; no line above it when open;
 - Today: the highlighted routine step is not clipped (whole rounded border and glow).
"""
import asyncio, sys
from playwright.async_api import async_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)
async def main():
  async with async_playwright() as p:
    br = await p.chromium.launch()
    ctx = await br.new_context(viewport={'width': 1440, 'height': 900}, locale='fr-CA', storage_state=STATE)
    await ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'))")
    pg = await ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:150]))
    await pg.goto(B + '/?x=1#payouts'); await pg.wait_for_timeout(2500)
    await pg.evaluate("""(()=>{const a=S.accounts.find(x=>x.status!=='archived'); put('payouts',{id:'ro-p1',account_id:a.id,amount_c:123400,status:'paid',request_date:'2026-10-01',payment_date:'2026-10-02'}); put('payouts',{id:'ro-p2',account_id:a.id,amount_c:50000,status:'requested',request_date:'2026-10-05'}); put('expenses',{id:'ro-e1',account_id:a.id,firm_id:a.firm_id,amount_c:9900,category:'evaluation',date:'2026-10-03'}); render();})()""")
    await pg.wait_for_timeout(1200)
    ok(await pg.locator('#main .pz-row [data-act=edit-payout]:not(li), #main .pz-row [data-act=edit-expense]:not(li)').count() == 0, 'no « Edit » button in the rows')
    await pg.locator('#main li[data-id="ro-p1"] .pz-main').click(); await pg.wait_for_timeout(700)
    ok(await pg.evaluate("U.editP") == 'ro-p1' and await pg.locator('#main li.pz-edit').count() == 1, 'a tap on a payout row opens its form')
    await pg.evaluate("U.editP=null; render()"); await pg.wait_for_timeout(500)
    sh = pg.locator('#main li[data-id="ro-p1"] .sh-link')
    ok(await sh.count() == 1, '« Share » stays on a paid payout')
    await pg.locator('#main li[data-id="ro-p2"] [data-pz-paid]').click(); await pg.wait_for_timeout(700)
    ok(await pg.evaluate("U.editP") in (None, '') and await pg.evaluate("getDoc('payouts','ro-p2').status") == 'paid', '« Mark as paid » marks it paid without opening the form')
    tab = pg.locator('#main [data-pz-tab="expenses"], #main [data-v="expenses"]')
    if await tab.count(): await tab.first.click(); await pg.wait_for_timeout(500)
    await pg.evaluate("document.querySelector('#main li[data-id=\"ro-e1\"] .pz-main').click()"); await pg.wait_for_timeout(700)
    ok(await pg.evaluate("U.editE") == 'ro-e1', 'a tap on an expense row opens its form')
    await pg.evaluate("U.editE=null; ['ro-p1','ro-p2'].forEach(i=>remove('payouts',i)); remove('expenses','ro-e1'); render()")
    # accounts: the box left open comes back closed
    await pg.evaluate("U.addAcct=true; saveU()")
    await pg.goto(B + '/?x=2#accounts'); await pg.wait_for_timeout(2500)
    ok(await pg.locator('#main .acct-add').count() == 0, 'Accounts: the add-account box is closed when the page opens')
    await pg.locator('#main [data-act=acct-add]').last.click(); await pg.wait_for_timeout(700)
    bt = await pg.evaluate("getComputedStyle(document.querySelector('#main .acct-add')).borderTopWidth")
    ok(bt == '0px', f'no line above the open box ({bt})')
    await pg.evaluate("location.hash='#trades'"); await pg.wait_for_timeout(600); await pg.evaluate("location.hash='#accounts'"); await pg.wait_for_timeout(1200)
    ok(await pg.locator('#main .acct-add').count() == 0, 'leaving Accounts closes the box')
    # routine step not clipped
    await pg.evaluate("location.hash='#dashboard'"); await pg.wait_for_timeout(2500)
    clip = await pg.evaluate("""(()=>{const s=document.querySelector('#main .nav-rt-s'); let e=s&&s.parentElement, c=[]; while(e&&e.id!=='main'){ if(getComputedStyle(e).overflow!=='visible') c.push(e.className); e=e.parentElement;} return c})()""")
    ok(clip == [], f'routine steps: no parent clips them ({clip})')
    ok(not errs, 'no browser error' + ('' if not errs else ': ' + ' | '.join(errs[:3])))
    await br.close()
  print(f'\n{"all passed" if not fails else str(fails) + " failed"}'); sys.exit(1 if fails else 0)
asyncio.run(main())
