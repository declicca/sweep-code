"""
Sweep — several trades from one screenshot (dev environment; Gemini answers are mocked: no credit spent):
  SWEEP_AI_CONFIG=<ai-config with any key> SWEEP_AI_MOCK=tests/samples/shot-ai-mock.json php -S … then
  python3 tests/e2e_shot_multi.py http://127.0.0.1:8095 /tmp/show_state.json
 - a screenshot with ONE trade: the usual screen, filled (unchanged path);
 - a Tradovate fills screenshot (13 fills → 6 trades): « 6 trades found », uncheck 2, edit one (P&L follows), save
   4 trades in one go (one import_batch_id, one screenshot for all), then « Undo » removes the whole batch;
 - computer and phone (iPhone); no browser window; no English left in French.
"""
import asyncio, sys, os, re, sqlite3
from playwright.async_api import async_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
DB = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3].endswith('.db') else '/tmp/g/data/journal.db'
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'samples')
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)
EN = re.compile(r"\b(trades found|Check all|Uncheck all|Save \d+ trades|To check|Already in Sweep|Open — to complete|Net of the batch|won|lost|Answer trade by trade)\b")
async def run(p, name, kw):
  br = await p.chromium.launch(); ctx = await br.new_context(**kw, locale='fr-CA', storage_state=STATE)
  await ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'))")
  pg = await ctx.new_page(); dlg = []; errs = []
  pg.on('dialog', lambda d: (dlg.append(d.message), asyncio.ensure_future(d.dismiss()))); pg.on('pageerror', lambda e: errs.append(str(e)[:150]))
  await pg.goto(B + '/?x=1#dashboard'); await pg.wait_for_timeout(3000)
  acc = await pg.evaluate("(S.accounts.find(a=>a.status!=='archived')||{}).id")
  ok(await pg.evaluate("document.body.classList.contains('ai-on')"), f'[{name}] Sweep AI is on (mocked answers)')
  async def open_reader():
    await pg.evaluate("editDoc('settings','settings',d=>{d.add_mode='shot'; d.add_mode_pref='shot'})"); await pg.wait_for_timeout(300)
    await pg.evaluate("openTicket(null)"); await pg.wait_for_timeout(900)
  # 1. one trade: unchanged screen
  await open_reader()
  await pg.locator('.nav-am input[type=file]').first.set_input_files(os.path.join(D, 'shot-topstepx-one-trade.png')); await pg.wait_for_timeout(3500)
  one = await pg.evaluate("[!!document.querySelector('.nav-shm'), (document.querySelector('.nav-am [data-am-f=net]')||{}).value, (document.querySelector('.nav-am [data-am-f=inst]')||{}).value]")
  ok(not one[0] and one[1] in ('250.00', '250'), f'[{name}] one trade on the screenshot: the usual screen, filled (net {one[1]})')
  await pg.evaluate("document.querySelectorAll('.nav-am .nav-am-x, .nav-am [data-am=close]').forEach(b=>b.click())"); await pg.keyboard.press('Escape'); await pg.wait_for_timeout(500)
  # a Tradesea single-trade page: the symbol is only on the chart title (« Gold (GCZ6) »)
  await open_reader()
  await pg.locator('.nav-am input[type=file]').first.set_input_files(os.path.join(D, 'shot-tradesea-one-trade.png')); await pg.wait_for_timeout(3500)
  ts = await pg.evaluate("[(document.querySelector('.nav-am [data-am-f=net]')||{}).value, SH_STATUS = (document.querySelector('.nav-am .nav-am-st, .nav-am-status')||{}).textContent||'', document.querySelector('.nav-am').innerText.includes('GC')]")
  ok(ts[0] in ('204.00', '204') and ts[2] and 'inconnu' not in ts[1], f'[{name}] Tradesea single-trade page: GC read from the chart title, net $204 ({ts})')
  await pg.evaluate("document.querySelectorAll('.nav-am .nav-am-x, .nav-am [data-am=close]').forEach(b=>b.click())"); await pg.keyboard.press('Escape'); await pg.wait_for_timeout(500)
  # 2. six trades
  await open_reader()
  await pg.locator('.nav-am input[type=file]').first.set_input_files(os.path.join(D, 'shot-tradovate-fills.png')); await pg.wait_for_timeout(4000)
  title = await pg.evaluate("(document.querySelector('.nav-shm-title')||{}).textContent||''")
  ok('6 trades trouvés' in title, f'[{name}] « 6 trades trouvés » ({title})')
  await pg.evaluate(f"(()=>{{const s=document.querySelector('[data-shm-acc]'); s.value='{acc}'; s.dispatchEvent(new Event('change',{{bubbles:true}}));}})()"); await pg.wait_for_timeout(1500)
  pnl = await pg.evaluate("SweepShotMulti.state.trades.map(t=>[t.instrument,t.direction,t.contracts,t.pnl_c])")
  ok(pnl == [['NQ', 'long', 2, 65500], ['MNQ', 'short', 3, 5850], ['ES', 'long', 1, -16250], ['NQ', 'short', 1, 22500], ['MNQ', 'long', 2, 4600], ['MES', 'short', 2, 3750]], f'[{name}] the 6 trades and their P&L (FIFO, scale-in, micro/mini, shorts)')
  txt = await pg.evaluate("document.querySelector('.nav-shm').innerText")
  ok(not EN.findall(txt), f'[{name}] no English left ({EN.findall(txt)[:3]})')
  for i in (1, 2):
    await pg.locator(f'[data-shm-sel="{i}"]').check(force=True) if False else await pg.evaluate(f"(()=>{{const c=document.querySelector('[data-shm-sel=\"{i}\"]'); c.checked=false; c.dispatchEvent(new Event('change',{{bubbles:true}}));}})()")
    await pg.wait_for_timeout(200)
  await pg.locator('[data-shm-edit="0"]').click(); await pg.wait_for_timeout(300)
  await pg.evaluate("(()=>{const i=document.querySelector('[data-shm-f=exit][data-i=\"0\"]'); i.value='21030.5'; i.dispatchEvent(new Event('change',{bubbles:true}));})()"); await pg.wait_for_timeout(300)
  e0 = await pg.evaluate("SweepShotMulti.state.trades[0].pnl_c")
  ok(e0 == round((21030.5 - 21010.125) * 2 * 20 * 100), f'[{name}] editing the exit recalculates the P&L live ({e0})')
  btn = await pg.evaluate("document.querySelector('[data-shm-save]').textContent")
  ok('Enregistrer 4 trades' in btn, f'[{name}] « {btn} » after unchecking 2')
  n0 = await pg.evaluate("S.trades.length")
  uid = (await (await ctx.request.get(B + '/api/data', headers={'X-Requested-With': 'fetch'})).json())['user']; uid = uid.get('id') or uid.get('uid')
  def rows():
    try:
      con = sqlite3.connect(DB); c = {'cel': [r[0] for r in con.execute('SELECT type FROM game_celebrations WHERE user_id = ? ORDER BY id', (uid,))], 'nt': [r[0] for r in con.execute('SELECT type FROM notifications WHERE user_id = ? ORDER BY id', (uid,))]}; con.close(); return c
    except Exception: return {'cel': [], 'nt': []}
  before = rows()
  await pg.locator('[data-shm-save]').click(); await pg.wait_for_timeout(2500)
  saved = await pg.evaluate("(()=>{const x=S.trades.filter(t=>t.import_batch_id); const b=[...new Set(x.map(t=>t.import_batch_id))]; const last=b[b.length-1]; const lot=x.filter(t=>t.import_batch_id===last); return {n:lot.length, ids:lot.map(t=>t.id), shots:[...new Set(lot.flatMap(t=>(t.shots||[]).map(s=>s.id)))].length, acc:[...new Set(lot.map(t=>t.account_id))]}})()")
  await pg.wait_for_timeout(1500); after = rows()
  newc, newn = after['cel'][len(before['cel']):], after['nt'][len(before['nt']):]
  ok(all(newc.count(x) == 1 for x in newc) and all(newn.count(x) == 1 for x in newn), f'[{name}] one celebration / notification per kind for the batch, not one per trade ({newc} {newn})')
  ok(saved['n'] == 4 and saved['shots'] == 1 and saved['acc'] == [acc], f'[{name}] 4 trades saved in one batch, one screenshot for all, one account ({saved["n"]}, {saved["shots"]})')
  toast = await pg.evaluate("(document.querySelector('.nav-undo')||{}).innerText||''")
  ok('4 trades ajoutés' in toast, f'[{name}] one toast « 4 trades ajoutés · … » ({toast[:60]})')
  srv = await (await ctx.request.get(B + '/api/data', headers={'X-Requested-With': 'fetch'})).json()
  ok(len([t for t in srv['trades'] if t['id'] in saved['ids']]) == 4, f'[{name}] the server has the 4 trades')
  await pg.locator('.nav-undo button').first.click(); await pg.wait_for_timeout(2000)
  srv = await (await ctx.request.get(B + '/api/data', headers={'X-Requested-With': 'fetch'})).json()
  left = len([t for t in srv['trades'] if t['id'] in saved['ids']]) + await pg.evaluate(f"S.trades.filter(t=>{saved['ids']}.includes(t.id)).length")
  ok(left == 0, f'[{name}] « Undo » removes the whole batch ({left} left)')
  # duplicates: the same screenshot again after saving → every trade « Already in Sweep », unchecked
  await open_reader(); await pg.locator('.nav-am input[type=file]').first.set_input_files(os.path.join(D, 'shot-tradovate-fills.png')); await pg.wait_for_timeout(4000)
  await pg.evaluate(f"(()=>{{const s=document.querySelector('[data-shm-acc]'); s.value='{acc}'; s.dispatchEvent(new Event('change',{{bubbles:true}}));}})()"); await pg.wait_for_timeout(1500)
  await pg.locator('[data-shm-save]').click(); await pg.wait_for_timeout(2500)
  ids2 = await pg.evaluate("(()=>{const x=S.trades.filter(t=>t.import_batch_id); const b=x[x.length-1].import_batch_id; return x.filter(t=>t.import_batch_id===b).map(t=>t.id)})()")
  await open_reader(); await pg.locator('.nav-am input[type=file]').first.set_input_files(os.path.join(D, 'shot-tradovate-fills.png')); await pg.wait_for_timeout(4000)
  await pg.evaluate(f"(()=>{{const s=document.querySelector('[data-shm-acc]'); s.value='{acc}'; s.dispatchEvent(new Event('change',{{bubbles:true}}));}})()"); await pg.wait_for_timeout(1500)
  dup = await pg.evaluate("SweepShotMulti.state.trades.map(t=>[t.dup,t.sel])")
  ok(len(dup) == 6 and all(d and not s2 for d, s2 in dup), f'[{name}] the same trades again: « Déjà dans Sweep », unchecked ({dup[:2]})')
  await pg.keyboard.press('Escape'); await pg.wait_for_timeout(300)
  await ctx.request.post(B + '/api/docs/batch', data={'col': 'trades', 'del': ids2}, headers={'X-Requested-With': 'fetch'})
  # a Lucid trade list (copied as written): directions, real times and P&L right, nothing « to check »
  await open_reader(); await pg.locator('.nav-am input[type=file]').first.set_input_files(os.path.join(D, 'shot-lucid-trades.png')); await pg.wait_for_timeout(4000)
  await pg.evaluate(f"(()=>{{const s=document.querySelector('[data-shm-acc]'); s.value='{acc}'; s.dispatchEvent(new Event('change',{{bubbles:true}}));}})()"); await pg.wait_for_timeout(1500)
  lu = await pg.evaluate("SweepShotMulti.state.trades.map(t=>[t.instrument,t.direction,t.entry_time,t.exit_time,t.pnl_c,t.fees_c,!!t.check])")
  ok(lu == [['ES', 'long', '09:31', '09:38', -16250, 420, False], ['NQ', 'long', '10:02', '10:09', 65000, 840, False], ['MNQ', 'short', '10:41', '10:44', 6150, 186, False], ['MES', 'short', '15:02', '15:09', 3750, 124, False]], f'[{name}] Lucid list: sides, entry/exit times, P&L and fees as on the screenshot ({lu})')
  await pg.keyboard.press('Escape'); await pg.wait_for_timeout(300)
  ok(not dlg and not errs, f'[{name}] no browser window, no error ({dlg[:1]} {errs[:2]})')
  await br.close()
async def main():
  async with async_playwright() as p:
    await run(p, 'ordinateur', {'viewport': {'width': 1440, 'height': 900}})
    await run(p, 'iPhone', dict(p.devices['iPhone 13']))
  print(f'\n{"all passed" if not fails else str(fails) + " failed"}'); sys.exit(1 if fails else 0)
asyncio.run(main())
