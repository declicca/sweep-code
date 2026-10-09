"""
Sweep — points 10, 11, 12 (dev environment with Playwright, not on the server):
  python3 tests/e2e_delete_undo_copy_dates.py http://127.0.0.1:8095 /tmp/show_state.json
 10. a trade copied on 3 accounts → « Delete all » → no browser window, « Deleted on 3 accounts · Undo » for 5 s → Undo:
     3 trades back, same copy_group, checklist intact (also after a reload). Screenshot, checklist question, sample data
     and Sweep-account deletions never open the browser's window either.
 11. the copy panel and the « ⋯ » menu of a trade have no English left in French and Spanish.
 12. at 20:30 New York time, with the device clock in UTC, Europe/Paris and Asia/Tokyo: the header date, the strip of
     days, the trade form and the saved trade all show the same session (the next day: futures sessions start at 18:00).
"""
import asyncio, sys, re
from playwright.async_api import async_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)

SETUP = """async () => {   // three accounts of the same firm, created once
  const mine = (S.accounts || []).filter(a => (a.name || '').startsWith('Copy test'));
  if (mine.length >= 3) return mine.slice(0, 3).map(a => a.id);
  const fid = 'ftest' + Date.now(); put('firms', { id: fid, name: 'Apex Trader Funding' });
  const ids = [1, 2, 3].map(i => { const id = 'acp' + i + Date.now(); put('accounts', { id, firm_id: fid, name: 'Copy test ' + i, starting_balance_c: 5000000, status: 'active', created_on: '2026-10-01', phase: 'eval', rules: {} }); return id; });
  await new Promise(r => setTimeout(r, 1500)); return ids;
}"""

async def main():
  async with async_playwright() as p:
    br = await p.chromium.launch()

    # ───────── 10 + 11 in French, 11 in Spanish ─────────
    for lang in ['fr', 'es']:
      ctx = await br.new_context(viewport={'width': 1280, 'height': 900}, locale='fr-CA' if lang == 'fr' else 'es-ES', storage_state=STATE)
      await ctx.add_init_script(f"sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('{lang}'))")
      pg = await ctx.new_page(); dialogs = []; errs = []
      pg.on('dialog', lambda d: (dialogs.append(d.message), asyncio.ensure_future(d.dismiss())))
      pg.on('pageerror', lambda e: errs.append(str(e)[:150]))
      await pg.goto(B + '/?x=1#trades'); await pg.wait_for_timeout(2500)
      acc = await pg.evaluate(SETUP)
      tid = await pg.evaluate("""(a) => { const id = 'tcp' + Date.now(); put('trades', { id, account_id: a, instrument: 'NQ', direction: 'long', contracts: 2, entry: 21000, exit: 21010, date: '2026-10-06', entry_time: '10:00', exit_time: '10:05', pnl_c: 40000, fees_c: 0, discipline: {} }); return id; }""", acc[0])
      await pg.wait_for_timeout(600)
      await pg.evaluate(f"location.hash='#trade/{tid}'"); await pg.wait_for_timeout(1500)
      # the copy panel, opened from the « ⋯ » menu
      menu = pg.locator('#main details.menu').first
      await menu.locator('summary').click(); await pg.wait_for_timeout(300)
      menu_txt = await menu.inner_text()
      await pg.locator('#main [data-act=copy-open]').first.click(); await pg.wait_for_timeout(500)
      panel = pg.locator('#main [data-act=copy-do]').locator('xpath=ancestor::div[contains(@class,"surface")][1]')
      txt0 = await panel.inner_text()
      for a in acc[1:]: await pg.locator(f'#main [data-act=copy-pick][data-v="{a}"]').click(); await pg.wait_for_timeout(250)
      txt2 = await panel.inner_text(); btn = (await pg.locator('#main [data-act=copy-do]').inner_text()).strip()
      EN = re.compile(r'\b(Copy to|Copy this trade|Same prices|stay in sync|already on every|Delete all|Delete this copy|Share trade card|Edit trade|account[s]?\b(?! ?:))')
      left = sorted(set(EN.findall(menu_txt + '\n' + txt0 + '\n' + txt2)))
      ok(not left, f'[{lang}] copy panel and « ⋯ » menu: no English left' + ('' if not left else f' → {left}'))
      want = {'fr': 'Copier sur 2 comptes', 'es': 'Copiar a 2 cuentas'}[lang]
      ok(btn == want, f'[{lang}] copy button: « {btn} »')
      await pg.locator('#main [data-act=copy-do]').click(); await pg.wait_for_timeout(1200)
      toast_txt = await pg.evaluate("(document.querySelector('#toast')||{}).innerText||''")
      ok(any(w in toast_txt for w in (['Copié sur 2 comptes'] if lang == 'fr' else ['Copiado a 2 cuentas', 'Copiado en 2 cuentas'])), f'[{lang}] toast: « {toast_txt.strip()} »')
      if lang == 'es': await ctx.close(); continue

      # checklist answered on one copy → synced to the 3
      grp = await pg.evaluate(f"getDoc('trades','{tid}').copy_group")
      await pg.evaluate(f"""editDoc('trades','{tid}',d=>{{d.discipline=Object.assign({{}},d.discipline,{{q_test:'y',q_test2:'n'}}); d.notes='kept note'}}); syncTrade('{tid}',['discipline','notes'])""")
      await pg.wait_for_timeout(1200)
      grp_ids = await pg.evaluate(f"S.trades.filter(t=>t.copy_group==='{grp}').map(t=>t.id)")
      ok(len(grp_ids) == 3, 'the trade is on 3 accounts, one copy_group')
      before = await pg.evaluate(f"JSON.stringify(S.trades.filter(t=>t.copy_group==='{grp}').map(t=>[t.id,t.account_id,t.discipline,t.notes]).sort())")
      # « Delete all 3 »
      await pg.evaluate(f"location.hash='#trade/{tid}'"); await pg.wait_for_timeout(1200)
      await pg.locator('#main details.menu summary').first.click(); await pg.wait_for_timeout(300)
      dall = pg.locator('#main [data-act=del-trade-all]')
      ok((await dall.inner_text()).strip() == 'Tout supprimer (3)', 'the menu says « Tout supprimer (3) »')
      await dall.click(); await pg.wait_for_timeout(500)
      ok(not dialogs, 'no browser window' + ('' if not dialogs else f': {dialogs}'))
      und = pg.locator('.nav-undo')
      ok(await und.count() == 1 and 'Supprimé sur 3 comptes' in await und.inner_text() and 'Annuler' in await und.inner_text(), 'toast « Supprimé sur 3 comptes · Annuler »')
      ok(await pg.evaluate(f"S.trades.filter(t=>t.copy_group==='{grp}').length") == 0, 'the 3 copies are gone at once')
      await und.locator('button').click(); await pg.wait_for_timeout(1500)
      after = await pg.evaluate(f"JSON.stringify(S.trades.filter(t=>t.copy_group==='{grp}').map(t=>[t.id,t.account_id,t.discipline,t.notes]).sort())")
      ok(after == before, '« Annuler »: 3 trades back, same copy_group, checklist and notes intact')
      await pg.reload(); await pg.wait_for_timeout(2500)
      again = await pg.evaluate(f"JSON.stringify(S.trades.filter(t=>t.copy_group==='{grp}').map(t=>[t.id,t.account_id,t.discipline,t.notes]).sort())")
      ok(again == before, 'still there after a reload (saved on the server)')
      # the toast leaves after 5 s if nothing is done: delete all again and wait
      await pg.evaluate(f"location.hash='#trade/{tid}'"); await pg.wait_for_timeout(1200)
      await pg.locator('#main details.menu summary').first.click(); await pg.locator('#main [data-act=del-trade-all]').click(); await pg.wait_for_timeout(5600)
      ok(await pg.locator('.nav-undo').count() == 0 and await pg.evaluate(f"S.trades.filter(t=>t.copy_group==='{grp}').length") == 0, 'without « Annuler », the toast leaves after 5 s and the copies stay deleted')
      # the other deletions that used the browser's window
      await pg.goto(B + '/?x=2#settings'); await pg.wait_for_timeout(2500)
      q = pg.locator('#main [data-act=q-del]')
      if await q.count():
        n0 = await pg.evaluate("getDoc('settings','settings').questions.length")
        await q.first.click(); await pg.wait_for_timeout(400)
        n1 = await pg.evaluate("getDoc('settings','settings').questions.length")
        await pg.locator('.nav-undo button').click(); await pg.wait_for_timeout(600)
        n2 = await pg.evaluate("getDoc('settings','settings').questions.length")
        ok(n1 == n0 - 1 and n2 == n0 and not dialogs, f'a checklist question: removed, « Annuler » brings it back ({n0} → {n1} → {n2}), no browser window')
      sid = await pg.evaluate("(a)=>{const id='tshot'+Date.now(); put('trades',{id,account_id:a,instrument:'NQ',direction:'long',contracts:1,entry:21000,exit:21002,date:'2026-10-06',entry_time:'11:00',exit_time:'11:02',pnl_c:4000,fees_c:0,shots:[{id:'shot-test',name:'x.png'}]}); return id}", acc[0]); await pg.wait_for_timeout(500)
      await pg.evaluate(f"location.hash='#trade/{sid}'"); await pg.wait_for_timeout(1200)
      await pg.evaluate("document.querySelector('#main [data-act=del-shot]') ? document.querySelector('#main [data-act=del-shot]').click() : null"); await pg.wait_for_timeout(400)
      s1 = await pg.evaluate(f"(getDoc('trades','{sid}').shots||[]).length")
      await pg.locator('.nav-undo button').click(); await pg.wait_for_timeout(500)
      s2 = await pg.evaluate(f"(getDoc('trades','{sid}').shots||[]).length")
      ok(s1 == 0 and s2 == 1 and not dialogs, 'a screenshot: removed, « Annuler » brings it back, no browser window')
      await pg.goto(B + '/?x=3#settings'); await pg.wait_for_timeout(2500)
      f = pg.locator('#main form[data-form=delete-account], #main [name=password]').last
      if await pg.locator('#main form input[type=password][name=password]').count():
        await pg.evaluate("(()=>{const i=[...document.querySelectorAll('#main form input[name=password]')].pop(); i.value='x'; deleteAccount(i.form)})()"); await pg.wait_for_timeout(500)
        ok(await pg.locator('aside.nav-ask.open').count() == 1 and not dialogs, 'deleting the Sweep account asks in the app’s own window (no browser window)')
        await pg.locator('.nav-ask [data-ask="0"]').click(); await pg.wait_for_timeout(400)
        ok(await pg.evaluate("!!S.me"), '« Annuler » keeps the account')
      ok(not errs, 'no browser error' + ('' if not errs else ': ' + ' | '.join(errs[:3])))
      await ctx.close()

    # ───────── 12. one session everywhere, whatever the device's time zone ─────────
    NOW = '2026-10-08T00:30:00Z'   # 20:30 New York (EDT) on Wednesday Oct 7 → session of Thursday Oct 8
    for tz in ['UTC', 'Europe/Paris', 'Asia/Tokyo']:
      ctx = await br.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True, locale='fr-CA', timezone_id=tz, storage_state=STATE)
      await ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'))")
      pg = await ctx.new_page(); await pg.clock.install(time=NOW)
      await pg.goto(B + '/?x=1#dashboard'); await pg.wait_for_timeout(2600)
      hi = await pg.evaluate("(document.querySelector('.main-wrap .top #title')||{}).dataset ? document.querySelector('.main-wrap .top #title').dataset.hi||'' : ''")
      greet = await pg.evaluate("(document.querySelector('#main .greet')||{}).textContent||''")
      strip = await pg.evaluate("[...document.querySelectorAll('#main .nav-fd.today, #main .nav-fd.sel')].map(b=>b.dataset.fd)")
      today = await pg.evaluate('todayStr()')
      await pg.evaluate("editDoc('settings','settings',d=>{d.add_mode='manual'})"); await pg.wait_for_timeout(300)   # the form, not the screenshot reader
      await pg.evaluate("openTicket(null,{manual:true})"); await pg.wait_for_timeout(900)
      form = await pg.evaluate("TK && TK.date"); etime = await pg.evaluate("TK && TK.entryTime")
      # save a trade from the form (entry and exit typed): the trade's date
      saved = await pg.evaluate("""(async () => { TK.entry = 21000; TK.exit = 21004; TK.qty = 1; TK.dir = 'long'; const ids = new Set(S.trades.map(t => t.id));
        tkSave(); await new Promise(r => setTimeout(r, 1500));
        const t = S.trades.find(x => !ids.has(x.id)); return t ? { date: t.date, time: t.entry_time, ex: (t.executions || []).map(x => x.t) } : null; })()""")
      head_ok = 'jeudi 8 octobre' in (hi + greet).lower()
      ok(today == '2026-10-08' and head_ok and strip and set(strip) == {'2026-10-08'} and form == '2026-10-08' and saved and saved['date'] == '2026-10-08',
         f'[{tz}] 20:30 ET → header « {(hi or greet).strip()} », strip {strip or "(today)"}, form {form} {etime}, saved trade {saved and saved["date"]} {saved and saved["time"]}')
      ok(bool(saved) and all(x.startswith('2026-10-07 20:') for x in saved['ex']) if saved and saved['ex'] else bool(saved), f'[{tz}] the executions keep the real clock time (Oct 7 20:30 ET), the chart finds its candles')
      await ctx.close()
    await br.close()
  print(f'\n{"all passed" if not fails else str(fails) + " failed"}'); sys.exit(1 if fails else 0)
asyncio.run(main())
