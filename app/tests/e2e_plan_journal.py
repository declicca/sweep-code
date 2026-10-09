"""
Sweep — the plan made from Today (1. Plan) is in the journal's Pre-market, and the other way round
(dev environment with Playwright):  python3 tests/e2e_plan_journal.py http://127.0.0.1:8095 /tmp/show_state.json
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
    br = await p.chromium.launch(); ctx = await br.new_context(viewport={'width': 1440, 'height': 900}, locale='fr-CA', storage_state=STATE)
    await ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'))")
    pg = await ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:150]))
    await pg.goto(B + '/?x=1#dashboard'); await pg.wait_for_timeout(3000)
    await pg.evaluate("editDoc('settings','settings',d=>{d.setups=[...new Set([...(d.setups||[]),'Liquidity sweep','Break & retest'])]})")
    await pg.locator('#main .nav-rt [data-rt=plan]').first.click(); await pg.wait_for_timeout(900)
    day = await pg.evaluate("document.getElementById('gSheet').dataset.day")
    await pg.locator('#gSheet [data-g=bias][data-v=bullish]').click()
    await pg.evaluate("[...document.querySelectorAll('#gSheet [data-g=setup]')].forEach(b=>{ if(b.classList.contains('on')) b.click(); })")
    await pg.evaluate("[...document.querySelectorAll('#gSheet [data-g=setup]')].find(b=>b.dataset.v==='Liquidity sweep').click()")
    await pg.locator('#gSheet [data-gp=max_loss]').fill('800'); await pg.locator('#gSheet [data-gp=max_trades]').fill('3'); await pg.locator('#gSheet [data-gp=levels]').fill('PDH 21500 · ONL 21310')
    await pg.locator('#gSheet [data-g=save-plan]').click(); await pg.wait_for_timeout(1200)
    await pg.evaluate(f"location.hash='#journal/{day}'"); await pg.wait_for_timeout(1800)
    vals = await pg.evaluate("Object.fromEntries([...document.querySelectorAll('#main [data-bind*=\"|pre.\"]')].map(e=>[e.dataset.bind.split('|').pop(), e.value]))")
    bias = await pg.evaluate("(document.querySelector('#main [data-path=\"pre.bias\"].on')||{}).dataset?.v")
    chips = await pg.evaluate("[...document.querySelectorAll('#main [data-jsetup].on')].map(b=>b.dataset.jsetup)")
    ok(bias == 'bullish', f'journal: the bias of the plan ({bias})')
    ok(vals.get('pre.max_loss') == '800' and vals.get('pre.max_trades') == '3' and vals.get('pre.levels') == 'PDH 21500 · ONL 21310', f'journal: max loss, max trades, key levels of the plan ({vals.get("pre.max_loss")}, {vals.get("pre.max_trades")}, {vals.get("pre.levels")})')
    ok(chips == ['Liquidity sweep'], f'journal: the planned setups ({chips})')
    # the journal changes the plan too
    await pg.evaluate("document.querySelector('#main [data-jsetup=\"Break & retest\"]').click()"); await pg.wait_for_timeout(600)
    await pg.evaluate("location.hash='#dashboard'"); await pg.wait_for_timeout(1500)
    await pg.evaluate(f"SweepGame.openPlan('{day}')"); await pg.wait_for_timeout(900)
    on = await pg.evaluate("[...document.querySelectorAll('#gSheet [data-g=setup].on')].map(b=>b.dataset.v).sort()")
    ok(on == ['Break & retest', 'Liquidity sweep'], f'the plan shows what was changed in the journal ({on})')
    await pg.locator('#gSheet [data-g=bias][data-v=no_trade]').click(); await pg.locator('#gSheet [data-g=save-plan]').click(); await pg.wait_for_timeout(1000)
    await pg.evaluate(f"location.hash='#journal/{day}'"); await pg.wait_for_timeout(1500)
    nb = await pg.evaluate("(document.querySelector('#main [data-path=\"pre.bias\"].on')||{}).textContent||''")
    ok(nb.strip() == 'Pas de trade', f'« No trade » in the plan shows in the journal ({nb.strip()})')
    ok(not errs, 'no browser error' + ('' if not errs else ': ' + ' | '.join(errs[:3])))
    await br.close()
  print(f'\n{"all passed" if not fails else str(fails) + " failed"}'); sys.exit(1 if fails else 0)
asyncio.run(main())
