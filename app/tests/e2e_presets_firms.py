"""
Sweep — prop firm presets in the browser (dev environment with Playwright, not on the server):
  python3 tests/e2e_presets_firms.py http://127.0.0.1:8095 /tmp/show_state.json
  1. an account for every firm, every account type and every size, through the picker (French), without an error;
  2. Topstep: « Standard / Consistency » chosen for a funded account, and when an evaluation becomes funded;
  3. Apex: « Rules from before March 2026 »;
  4. a firm changed its rules: the account page shows what changes, « Apply the new rules » / « Keep my rules »;
  5. Admin → Presets: last check, status per firm, red alert after 8 days, « Check now ».
The server must run with SWEEP_PRESETS_MOCK=tests/presets_mock.json so « Check now » reads the simulated pages.
"""
import asyncio, json, sys, os, time, datetime
from playwright.async_api import async_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
DATA = os.environ.get('SWEEP_DATA', '/tmp/g/data')
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)

async def main():
  async with async_playwright() as p:
    br = await p.chromium.launch(); errs = []
    ctx = await br.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True, locale='fr-CA', storage_state=STATE)
    await ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'))")
    pg = await ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
    await pg.goto(B + '/?x=1#accounts'); await pg.wait_for_timeout(2500)
    cat = await pg.evaluate("fetch('api/presets',{credentials:'same-origin'}).then(r=>r.json())")

    async def open_form():
      for _ in range(5):   # a celebration or a sheet can cover the page after an account is added: close it and try again
        await pg.keyboard.press('Escape'); await pg.evaluate("document.querySelectorAll('.nt-modal .btn, #gSheet [data-g=close]').forEach(b=>b.click()); location.hash='#accounts'"); await pg.wait_for_timeout(700)
        b = pg.locator('#main [data-act=acct-add]')
        if await b.count(): await b.last.click(); await pg.wait_for_timeout(700)
        if await pg.locator('form[data-form=account] [data-st-ph0]').count(): return
      raise RuntimeError('account form did not open')
    async def tap(sel):
      el = pg.locator(sel).first; await el.scroll_into_view_if_needed(); await el.click(); await pg.wait_for_timeout(180)

    print('— 1. one account per firm, account type and size')
    made, bad = 0, []
    for f in cat['firms']:
      for prog in f['programs']:
        for s in prog['sizes']:
          phase = 'eval' if s.get('eval') else 'funded'
          await open_form()
          await tap(f'[data-st-ph0={phase}]'); await tap(f'[data-st-firm="{f["id"]}"]')
          if await pg.locator(f'[data-st-type="{prog["id"]}"]').count(): await tap(f'[data-st-type="{prog["id"]}"]')
          if await pg.locator(f'[data-st-size="{s["size"]}"]').count(): await tap(f'[data-st-size="{s["size"]}"]')
          val = await pg.evaluate("document.querySelector('form[data-form=account]').dataset.uxPreset")
          before = await pg.evaluate("S.accounts.map(a=>a.id)")   # only the account created now (a re-run leaves older ones)
          await pg.evaluate("document.querySelector('form[data-form=account]').requestSubmit()"); await pg.wait_for_timeout(900)
          got = await pg.evaluate("([v, ids])=>{const a=S.accounts.find(a=>a.preset===v && !ids.includes(a.id)); if(!a) return null; return {r:a.rules, ph:a.phase, ver:a.preset_ver}}", [val, before])
          good = bool(got) and got['r'].get('dd_c', 0) > 0 and (phase != 'eval' or got['r'].get('target_c', 0) > 0) and got['ph'] == phase and got['ver'] == cat['version']
          made += 1
          if not good: bad.append(f"{f['id']}|{prog['id']}|{s['size']} → {val} {got}")
    ok(not bad, f'{made} accounts created (every firm, type and size), each with its rules, phase and catalogue version' + ('' if not bad else ': ' + '; '.join(bad[:3])))
    names = await pg.evaluate("[...new Set(S.accounts.map(a=>(firm(a.firm_id)||{}).name))].join(', ')")
    ok(all(n.split()[0] in names for n in [f['name'] for f in cat['firms']]), 'firms in the journal: ' + names)   # a firm already in the journal under a short name (« Lucid ») is reused
    ok('Tradeify' not in [f['name'] for f in cat['firms']] and 'Alpha Futures' not in [f['name'] for f in cat['firms']], 'Tradeify and Alpha Futures (empty) are not offered')

    print('— 2. Topstep: Standard / Consistency')
    await open_form(); await tap('[data-st-ph0=funded]'); await tap('[data-st-firm=topstep]'); await tap('[data-st-size="100000"]')
    ok(await pg.locator('[data-st-opt=path]').count() == 2, 'a funded Topstep account asks « Standard / Consistance »')
    await tap('[data-st-opt=path][data-st-val=consistency]')
    txt = await pg.locator('.ux-st-sum').evaluate('e=>e.textContent')
    ok('3 jours tradés' in txt and ('4,000' in txt or '4\u202f000' in txt), 'the summary shows the Consistency payout rules (3 traded days, max $4,000)')
    v = await pg.evaluate("document.querySelector('form[data-form=account]').dataset.uxPreset")
    await pg.evaluate("document.querySelector('form[data-form=account]').requestSubmit()"); await pg.wait_for_timeout(900)
    r = await pg.evaluate("(v)=>{const a=S.accounts.find(a=>a.preset===v); return a&&a.rules}", v)
    ok(v.endswith('|consistency') and r and r['consistency_pct'] == 40 and r['payout_trade_days'] == 3 and r['payout_max_c'] == 400000, 'saved with 40 %, 3 traded days, $4,000 cap')
    await pg.screenshot(path='/tmp/pr_topstep_choice.png')
    # an evaluation that passes → the « You passed » window asks for the option
    aid = await pg.evaluate("""(()=>{const id='evt'+Date.now(); put('accounts',{id, firm_id:S.accounts.find(a=>a.preset&&a.preset.startsWith('topstep')).firm_id, name:'Combine 50K', starting_balance_c:5000000, status:'active', created_on:'2026-10-01', phase:'eval', preset:'topstep|combine|50000|eval|', rules:SweepPresets.rulesOf('topstep|combine|50000|eval|').rules}); return id})()""")
    await pg.evaluate("(id)=>{const a=getDoc('accounts',id); SweepPass.ask(a)}", aid); await pg.wait_for_timeout(600)
    ok(await pg.locator('[data-pass-choice]').count() == 2, 'evaluation passed: the window offers « Standard » and « Consistance »')
    await pg.screenshot(path='/tmp/pr_pass_choice.png')
    await pg.locator('[data-pass-choice="path:consistency"]').click(); await pg.wait_for_timeout(1200)
    fr = await pg.evaluate("(id)=>{const a=S.accounts.find(a=>a.from_eval===id); return a&&{p:a.preset,c:a.rules.consistency_pct,d:a.rules.payout_trade_days}}", aid)
    ok(fr and fr['p'] == 'topstep|combine|50000|funded|consistency' and fr['c'] == 40 and fr['d'] == 3, 'the funded account gets the Consistency rules')

    print('— 3. Apex: rules from before March 2026')
    await open_form(); await tap('[data-st-ph0=funded]'); await tap('[data-st-firm=apex]')
    ok('Règles d’avant mars 2026' in await pg.locator('form[data-form=account] .ux-st').inner_text(), 'the Apex account types show « Règles d’avant mars 2026 »')
    await pg.screenshot(path='/tmp/pr_apex_types.png')
    await tap('[data-st-type=apex-legacy]'); await tap('[data-st-size="50000"]')
    v = await pg.evaluate("document.querySelector('form[data-form=account]').dataset.uxPreset")
    await pg.evaluate("document.querySelector('form[data-form=account]').requestSubmit()"); await pg.wait_for_timeout(900)
    r = await pg.evaluate("(v)=>{const a=S.accounts.find(a=>a.preset===v); return a&&a.rules}", v)
    ok(r and r['consistency_pct'] == 30 and r['payout_trade_days'] == 8 and r['payout_win_min_c'] == 5000 and r['dd_type'] == 'trade', 'Legacy 50K saved: 30 %, 8 days incl. 5 of $50, real-time drawdown')

    print('— 4. a firm changed its rules: the account page')
    acc = await pg.evaluate("(()=>{const a=S.accounts.find(a=>a.preset==='apex|apex-eod|50000|eval|'); editDoc('accounts',a.id,d=>{d.phase='funded'; d.preset='apex|apex-eod|50000|funded|'; d.rules=Object.assign({},d.rules,SweepPresets.rulesOf('apex|apex-eod|50000|funded|').rules); d.rules.payout_win_min_c=(d.rules.payout_win_min_c||0)+5000; d.preset_ver='old'}); return a.id})()")
    want = await pg.evaluate("SweepPresets.rulesOf('apex|apex-eod|50000|funded|').rules.payout_win_min_c")   # the catalogue's value (the account had +$50)
    await pg.evaluate(f"location.hash='#account/{acc}'"); await pg.wait_for_timeout(1800)
    ban = pg.locator('.ux-newrules')
    ok(await ban.count() == 1 and 'Minimum par jour gagnant' in await ban.inner_text(), 'the account shows « Apex Trader Funding a changé ses règles » with what changes')
    await ban.screenshot(path='/tmp/pr_banner.png')
    await pg.locator('[data-nr-apply]').click(); await pg.wait_for_timeout(900)
    r = await pg.evaluate(f"getDoc('accounts','{acc}').rules.payout_win_min_c")
    ok(r == want and await pg.locator('.ux-newrules').count() == 0, f'« Appliquer les nouvelles règles »: the catalogue minimum per winning day ({r} = {want}), banner gone')
    await pg.evaluate(f"editDoc('accounts','{acc}',d=>{{d.rules.payout_win_min_c={want + 5000}; d.preset_ver='old'}})"); await pg.evaluate("render()"); await pg.wait_for_timeout(700)
    await pg.locator('[data-nr-keep]').click(); await pg.wait_for_timeout(700)
    ok(await pg.evaluate(f"getDoc('accounts','{acc}').rules.payout_win_min_c") == want + 5000 and await pg.locator('.ux-newrules').count() == 0, '« Garder mes règles »: rules kept, banner gone')

    print('— 5. Admin → Presets')
    st = json.load(open(f'{DATA}/presets-status.json')) if os.path.exists(f'{DATA}/presets-status.json') else {}   # a fresh base has never been checked
    st['last_run'] = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=9)).strftime('%Y-%m-%dT%H:%M:%S+00:00'); json.dump(st, open(f'{DATA}/presets-status.json', 'w'))
    await pg.goto(B + '/?x=2#admin'); await pg.wait_for_timeout(2500)
    box = pg.locator('.ux-presets-admin')
    ok(await box.count() == 1 and 'Préréglages' in await box.inner_text(), 'Admin shows the « Préréglages » block')
    ok(await pg.locator('.ux-pr-alert').count() == 1 and 'plus de 8 jours' in await pg.locator('.ux-pr-alert').inner_text(), 'red alert: no check for more than 8 days')
    t = await box.inner_text()
    chips = await pg.evaluate("[...document.querySelectorAll('.ux-presets-admin .ux-pr-chip')].map(c=>c.textContent.trim())")
    ok('Apex Trader Funding' in t and 'Dernière vérification' in t and chips and all(c in ('inchangé', 'mis à jour', 'à revoir', 'erreur', 'pas encore vérifié') for c in chips), f'status per firm and the date of the last check ({sorted(set(chips))})')
    await box.screenshot(path='/tmp/pr_admin_alert.png')
    await pg.locator('[data-pr-run]').click()
    for _ in range(60):
      await pg.wait_for_timeout(500)
      if await pg.locator('[data-pr-run]:not([disabled])').count() and 'Vérifier maintenant' in await pg.locator('[data-pr-run]').inner_text(): break
    ok(await pg.locator('.ux-pr-alert').count() == 0, '« Vérifier maintenant » runs every firm, then the alert is gone')
    t = await box.inner_text()
    ok('il y a 0 j' in t and 'Vérifier maintenant' in t, 'last check: today, by « Vérifier maintenant »')
    await box.screenshot(path='/tmp/pr_admin_after.png')
    ctx2 = await br.new_context(); r = await ctx2.request.post(B + '/api/admin/presets/check', data={'finish': True}, headers={'X-Requested-With': 'fetch'})
    ok(r.status in (401, 403), f'« Check now » is refused without an admin session (HTTP {r.status})')
    ok(not errs, 'no browser error' + ('' if not errs else ': ' + ' | '.join(errs[:3])))
    await br.close()
  print(f'\n{"all passed" if not fails else str(fails) + " failed"}'); sys.exit(1 if fails else 0)
asyncio.run(main())
