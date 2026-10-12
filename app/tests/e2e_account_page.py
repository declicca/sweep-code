"""
Sweep — the account page (brief 02, part 2), dev environment with Playwright:
  python3 tests/e2e_account_page.py http://127.0.0.1:8095 /tmp/show_state.json
 - the firm's rule is « Drawdown permis » / « Max drawdown allowed » / « Drawdown permitido »; « Pire recul » stays the
   account's own worst drawdown (the tile);
 - the drawdown room in points: 50K, $2,000 end of day, stopped at the start; +$400 and −$100 on NQ at 2 contracts, +$20 on
   MNQ at 5 → peak $50,400, limit $48,400, room $1,920 = 48 points of NQ at 2 contracts ($20 a point a contract); only on
   the account's page, not on the list; nothing without a trade;
 - the daily loss limit with nothing lost today reads « 0 $ / 1 000 $ » in French (not « $0 »);
 - « Marquer comme échoué »: no browser window, marked at once, « Annuler » puts the account back as it was; without
   « Annuler » it stays failed;
 - the funded account is named after its firm: « Topstep XFA 50K #2 », « Apex Trader Funding PA 50K », « Take Profit
   Trader PRO 50K », « Lucid Trading Financé 50K » (no code of its own); an account without a firm keeps its name.
"""
import asyncio, json, os, sys
from playwright.async_api import async_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
SEED = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'presets', 'seed.json')))
fails = 0
def ok(c, what):
    global fails
    print(('ok   ' if c else 'FAIL ') + what); fails += 0 if c else 1
ACC = {'id': 'ap-acc', 'firm_id': 'ap-f', 'name': 'Page 50K', 'starting_balance_c': 5000000, 'status': 'active', 'phase': 'funded', 'money_type': 'funded', 'rules': {'dd_c': 200000, 'dd_type': 'eod', 'dd_lock': True, 'dll_c': 100000}}
TRADES = [{'id': 'ap-t1', 'account_id': 'ap-acc', 'instrument': 'NQ', 'direction': 'long', 'contracts': 2, 'pnl_c': 40000, 'pnl_manual': True, 'fees_c': 0, 'date': '2026-10-01', 'entry_time': '10:00', 'exit_time': '10:05', 'session_date': True},
          {'id': 'ap-t2', 'account_id': 'ap-acc', 'instrument': 'NQZ6', 'direction': 'short', 'contracts': 2, 'pnl_c': -10000, 'pnl_manual': True, 'fees_c': 0, 'date': '2026-10-02', 'entry_time': '10:00', 'exit_time': '10:05', 'session_date': True},
          {'id': 'ap-t3', 'account_id': 'ap-acc', 'instrument': 'MNQ', 'direction': 'long', 'contracts': 5, 'pnl_c': 2000, 'pnl_manual': True, 'fees_c': 0, 'date': '2026-10-05', 'entry_time': '10:00', 'exit_time': '10:05', 'session_date': True}]
def preset(fid):
    f = next(x for x in SEED['firms'] if x['id'] == fid); p = f['programs'][0]; s = next(x for x in p['sizes'] if x['size'] == 50000)
    return f['name'], f"{fid}|{p['id']}|{s['size']}|eval"
async def page(br, lang, w=1300, h=900):
    ctx = await br.new_context(storage_state=STATE, locale={'fr': 'fr-CA', 'en': 'en-US', 'es': 'es-ES'}[lang], viewport={'width': w, 'height': h}, bypass_csp=True)
    await ctx.add_init_script(f"sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('{lang}'))")
    pg = await ctx.new_page(); pg.errs = []; pg.dialogs = []
    pg.on('pageerror', lambda e: pg.errs.append(str(e)[:160]))
    async def dlg(d): pg.dialogs.append(d.message); await d.dismiss()
    pg.on('dialog', dlg)
    await pg.goto(B + '/#dashboard'); await pg.wait_for_function("!!window.SweepPresets && typeof put === 'function'", timeout=15000); await pg.wait_for_timeout(1500)
    return ctx, pg
async def main():
  async with async_playwright() as p:
    br = await p.chromium.launch(); errs = []
    ctx, pg = await page(br, 'fr')
    await pg.evaluate("([a, tr]) => { put('firms', {id:'ap-f', name:'Topstep'}); put('accounts', a); tr.forEach(t => put('trades', t)); }", [ACC, TRADES])
    await pg.wait_for_timeout(800); await pg.evaluate("location.hash='#account/ap-acc'"); await pg.wait_for_timeout(1800)
    # « Drawdown permis » for the rule, « Pire recul » for the tile
    labs = await pg.evaluate("[...document.querySelectorAll('#main .fgrid label.f > span')].map(s=>s.textContent.trim())")
    tiles = await pg.evaluate("[...document.querySelectorAll('#main .statline > div > span:first-child')].map(s=>s.textContent.trim())")
    ok('Drawdown permis' in labs and 'Pire recul' not in labs, f'FR the rule: « Drawdown permis » ({[x for x in labs if "rawdown" in x or "recul" in x]})')
    ok('Pire recul' in tiles, f'FR the tile stays « Pire recul » ({[x for x in tiles if "recul" in x or "rawdown" in x]})')
    # the room in points
    pv = await pg.evaluate("PV('NQ')"); ok(pv == 2000, f'NQ: $20 a point a contract ({pv} cents)')
    room = await pg.evaluate("(()=>{const r=[...document.querySelectorAll('#main .rule')].find(x=>/Marge de drawdown/.test(x.textContent)); return r?{b:r.querySelector('b').textContent.replace(/\\s+/g,' ').trim(), pts:(r.querySelector('.rule-pts')||{}).textContent||''}:null})()")
    ok(room and room['b'].replace(' ', ' ').replace('\xa0', ' ') == '1 920 $', f"room $1,920 ({room and room['b']})")
    ok(room and room['pts'] == 'soit 48 points de NQ à 2 contrats', f"« {room and room['pts']} » (expects « soit 48 points de NQ à 2 contrats »)")
    dll = await pg.evaluate("(()=>{const r=[...document.querySelectorAll('#main .rule')].find(x=>/Limite de perte/.test(x.textContent)); return r?r.querySelector('b').textContent.replace(/\\s+/g,' ').trim():''})()")
    ok(dll == '0 $ / 1 000 $', f'daily loss limit « {dll} » (no « $0 » in French)')
    await pg.evaluate("location.hash='#accounts'"); await pg.wait_for_timeout(1500)
    ok(await pg.locator('#main .rule-pts').count() == 0, 'not on the Accounts list')
    await pg.evaluate("put('accounts', Object.assign({}, %s, {id:'ap-none', name:'Sans trade'}))" % json.dumps(ACC)); await pg.wait_for_timeout(600)
    await pg.evaluate("location.hash='#account/ap-none'"); await pg.wait_for_timeout(1500)
    ok(await pg.locator('#main .rule').count() > 0 and await pg.locator('#main .rule-pts').count() == 0, 'no trade: no points')
    # « Marquer comme échoué »: at once, « Annuler » puts it back
    await pg.evaluate("location.hash='#account/ap-acc'"); await pg.wait_for_timeout(1500)
    await pg.locator('#main .acc-menu summary').click(); await pg.wait_for_timeout(300)
    await pg.locator('#main .acc-menu [data-fail]').click(); await pg.wait_for_timeout(700)
    a = await pg.evaluate("(({status,result,failed_on})=>({status,result,failed_on}))(getDoc('accounts','ap-acc'))")
    ok(not pg.dialogs, f'no browser window ({pg.dialogs})')
    ok(a['status'] == 'archived' and a['result'] == 'failed' and a['failed_on'], f'marked at once ({a})')
    toast = await pg.evaluate("(()=>{const t=document.querySelector('.nav-undo'); return t?t.innerText.replace(/\\n/g,' · '):''})()")
    ok('Compte marqué comme échoué' in toast and 'Annuler' in toast, f'« {toast} »')
    ok(await pg.evaluate("location.hash") == '#accounts', 'back to the Accounts list')
    await pg.locator('.nav-undo button').click(); await pg.wait_for_timeout(700)
    a = await pg.evaluate("(()=>{const d=getDoc('accounts','ap-acc'); return {status:d.status, has:['result','failed_on'].filter(k=>k in d)}})()")
    ok(a['status'] == 'active' and not a['has'], f'« Annuler »: the account is back as it was ({a})')
    await pg.evaluate("location.hash='#account/ap-acc'"); await pg.wait_for_timeout(1500)
    await pg.locator('#main .acc-menu summary').click(); await pg.wait_for_timeout(300)
    await pg.locator('#main .acc-menu [data-fail]').click(); await pg.wait_for_timeout(5800)
    a = await pg.evaluate("(({status,result})=>({status,result}))(getDoc('accounts','ap-acc'))")
    ok(a == {'status': 'archived', 'result': 'failed'} and await pg.locator('.nav-undo').count() == 0, f'without « Annuler » it stays failed ({a})')
    # the funded account's name
    await pg.evaluate("SweepPresets.load()"); await pg.wait_for_function("SweepPresets.ready()", timeout=15000)
    cases = [('topstep', ' #2', 'XFA'), ('apex', '', 'PA'), ('tpt', '', 'PRO'), ('lucid', '', 'Financé')]
    for fid, suffix, code in cases:
      fname, pv = preset(fid); eid = f'ap-ev-{fid}'
      await pg.evaluate("([fid, fname, pv, eid, nm]) => { put('firms', {id:'ap-'+fid, name:fname}); put('accounts', {id:eid, firm_id:'ap-'+fid, name:nm, starting_balance_c:5000000, status:'active', phase:'eval', preset:pv, rules:{dd_c:200000, target_c:300000}}); }", [fid, fname, pv, eid, f'Mon éval {fid}{suffix}'])
      await pg.wait_for_timeout(300); await pg.evaluate("(id) => SweepPass.toFunded(id, null)", eid); await pg.wait_for_timeout(500)
      got = await pg.evaluate("(id) => (S.accounts.find(x => x.from_eval === id) || {}).name", eid)
      want = f'{fname} {code} 50K{suffix}'
      ok(got == want, f'funded: « {got} » (expects « {want} »)')
    await pg.evaluate("put('accounts', {id:'ap-ev-x', firm_id:'', name:'Mon compte', starting_balance_c:5000000, status:'active', phase:'eval', rules:{dd_c:200000, target_c:300000}})")
    await pg.wait_for_timeout(300); await pg.evaluate("SweepPass.toFunded('ap-ev-x', null)"); await pg.wait_for_timeout(500)
    got = await pg.evaluate("(S.accounts.find(x => x.from_eval === 'ap-ev-x') || {}).name")
    ok(got == 'Mon compte', f'no firm: keeps its name (« {got} »)')
    errs += pg.errs
    # cleanup: archived, nothing left active
    await pg.evaluate("S.accounts.filter(a => /^ap-/.test(a.id) || /^ap-ev-/.test(a.from_eval || '')).forEach(a => editDoc('accounts', a.id, d => { d.status = 'archived'; }))")
    await pg.wait_for_timeout(800); await ctx.close()
    # the rule's name in English and Spanish
    for lang, want in (('en', 'Max drawdown allowed'), ('es', 'Drawdown permitido')):
      ctx, pg = await page(br, lang)
      await pg.evaluate("(a) => { put('accounts', Object.assign({}, a, {id:'ap-l', name:'Lang 50K'})); }", ACC); await pg.wait_for_timeout(600)
      await pg.evaluate("location.hash='#account/ap-l'"); await pg.wait_for_timeout(1500)
      labs = await pg.evaluate("[...document.querySelectorAll('#main .fgrid label.f > span')].map(s=>s.textContent.trim())")
      ok(want in labs, f'{lang.upper()} the rule: « {want} » ({[x for x in labs if "rawdown" in x or "etroceso" in x]})')
      await pg.evaluate("editDoc('accounts','ap-l', d => { d.status = 'archived'; })"); await pg.wait_for_timeout(500)
      errs += pg.errs; await ctx.close()
    ok(not errs, 'no page error' + ('' if not errs else ': ' + ' | '.join(errs[:2])))
    await br.close()
    print('all passed' if not fails else f'{fails} failed'); sys.exit(1 if fails else 0)
asyncio.run(main())
