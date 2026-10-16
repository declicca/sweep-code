"""
Sweep — live accounts and moving a funded account to live (Playwright, phone, a trader of its own):
  python3 tests/e2e_live_accounts.py http://127.0.0.1:8095
The form offers Evaluation, Funded and « Live account · Real money »; a live account takes a broker, a name and a balance
(no preset); a Lucid funded account gets its catalogue rules; its page offers « Move to live », which creates the live
account (its own rules), archives the funded one as « live », opens the new one with its LIVE badge. No page error.
(16 Oct.: checks, it only printed.)
"""
import asyncio, datetime, random, sys
from playwright.async_api import async_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    ctx=await br.new_context(viewport={'width':390,'height':844},device_scale_factor=2,is_mobile=True,has_touch=True,color_scheme='dark',locale='fr-CA')
    await ctx.add_init_script("sessionStorage.setItem('sw.modal','1')")
    pg=await ctx.new_page(); pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
    u='lv%d'%random.randint(1000,9999)
    await ctx.request.post(B+'/api/auth/register', data={'username':u,'password':'Testpass123!','email':u+'@t.dev','consent':True,'elapsed':6000}, headers={'X-Requested-With':'fetch'})
    # the profile is asked before the first account (since 2026-10-06): filled here so the « Complete your profile » window does not cover the page
    await ctx.request.post(B+'/api/me/profile', data={'first_name':'Test','last_name':'Trader','username':u}, headers={'X-Requested-With':'fetch'})
    await pg.goto(B+'/?x=1#dashboard'); await pg.wait_for_timeout(1500)
    await pg.evaluate("put('accounts',{id:'a-seed',name:'Perso',firm_id:'',starting_balance_c:1000000,status:'active'})"); await pg.wait_for_timeout(1000)
    async def add(phase, firm, size_idx, name, shot=None):
      await pg.evaluate("location.hash='#accounts'"); await pg.wait_for_timeout(1500)
      await pg.locator('#main [data-act=acct-add]:not([data-v="0"])').first.click(); await pg.wait_for_timeout(900)
      st=pg.locator('form[data-form=account] .ux-st')
      if shot:
        ch = await pg.evaluate("[...document.querySelectorAll('form[data-form=account] [data-st-ph0]')].map(b=>b.innerText.replace(/\\n/g,' — ')).join(' | ')")
        ok(all(w in ch for w in ('Évaluation', 'Financé', 'Compte live')), f'three choices: {ch[:90]}')
        await st.screenshot(path=shot)
      await st.locator(f'[data-st-ph0={phase}]').click(); await pg.wait_for_timeout(500)
      if phase == 'live':   # since the « live account » form (no presets: live rules differ by platform): broker, name, balance
        f = pg.locator('form[data-form=account]')
        sel = f.locator('select[name=firm]')
        if await sel.count():
          try: await sel.select_option('__new')
          except Exception: pass
        if await f.locator('[name=firmName]').count(): await f.locator('[name=firmName]').fill('Topstep')
        await f.locator('[name=start]').fill('10000'); await f.locator('[name=name]').fill(name)
        await f.locator('[type=submit]').click(); await pg.wait_for_timeout(1500)
        a = await pg.evaluate(f"(()=>{{const a=S.accounts.find(x=>x.name==='{name}'); return a?{{id:a.id,phase:a.phase,start:a.starting_balance_c/100}}:null}})()")
        return 'live form (no preset)', a
      await st.locator(f'[data-st-firm="{firm}"]').click(); await pg.wait_for_timeout(300)
      if await st.locator('[data-st-type]').count(): await st.locator('[data-st-type]').first.click(); await pg.wait_for_timeout(300)
      if await st.locator('[data-st-size]').count(): await st.locator('[data-st-size]').nth(size_idx).click(); await pg.wait_for_timeout(300)
      summ=await st.locator('.ux-st-sum').inner_text() if await st.locator('.ux-st-sum').count() else ''
      start=await pg.locator('form[data-form=account] [name=start]').input_value()
      await pg.locator('form[data-form=account] [name=name]').fill(name)
      await pg.locator('form[data-form=account] [type=submit]').click(); await pg.wait_for_timeout(1500)
      a=await pg.evaluate(f"(()=>{{const a=S.accounts.find(x=>x.name==='{name}'); return a?{{id:a.id,phase:a.phase,start:a.starting_balance_c/100,dd:a.rules.dd_c/100,dd_type:a.rules.dd_type,dll:a.rules.dll_c&&a.rules.dll_c/100,win:a.rules.payout_win_days,pct:a.rules.payout_max_pct,max:a.rules.payout_max_c}}:null}})()")
      await pg.evaluate("closeTicket && closeTicket()"); await pg.wait_for_timeout(400)
      return summ.replace('\n',' ')+' | start field: '+start, a
    s,a=await add('live','topstep',0,'Topstep Live 50K','/tmp/live_q.png')
    ok(a and a['phase'] == 'live' and a['start'] == 10000, f'a live account: broker, name, balance $10,000 ({a})')
    s,b=await add('funded','lucid',1,'LucidFlex 50K')
    ok(b and b['phase'] == 'funded' and b['dd'] and b['dd_type'], f'Lucid funded: its catalogue drawdown ({b})')
    await pg.evaluate("location.hash='#dashboard'"); await pg.wait_for_timeout(1500)
    await pg.evaluate(f"location.hash='#account/{b['id']}'"); await pg.wait_for_timeout(1500)
    row = await pg.evaluate("(document.querySelector('#main .nav-live-row')||{innerText:''}).innerText.replace(/\\n/g,' ')")
    ok('Passer en live' in row, f'the funded account offers « Passer en live » ({row})')
    await pg.locator('#main [data-live-go]').click(); await pg.wait_for_timeout(1800)
    r=await pg.evaluate(f"(()=>{{const o=getDoc('accounts','{b['id']}'), n=S.accounts.find(x=>x.from_funded==='{b['id']}'); return {{old:[o.status,o.result], new:n?[n.phase,n.preset,n.rules.payout_max_c,n.rules.payout_max_pct,n.rules.payout_win_days]:null, page:location.hash, badge:!!document.querySelector('#main .nav-live')}}}})()")
    ok(r['new'] and r['new'][0] == 'live' and (r['new'][1] or '').endswith('|live|'), f'moved: the live account with its own rules ({r["new"]})')
    ok(r['old'] == ['archived', 'live'] and r['page'].startswith('#account/') and r['badge'], f'the funded account archived as « live », the new one opened with its LIVE badge ({r["old"]}, {r["page"]}, {r["badge"]})')
    ok(not errs, f'no page error ({errs[:3]})'); await br.close()
asyncio.run(main())
print(f'{fails} failed' if fails else 'all passed'); sys.exit(1 if fails else 0)
