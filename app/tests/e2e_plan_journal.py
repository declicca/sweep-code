"""
Sweep — the plan made from Today (1. Plan, the pre-market questionnaire since the brief « Plan pre-market adaptatif ») is in
the journal's Pre-market: bias from the main scenario, max loss, max trades, the levels; « Not trading today » too
(dev environment with Playwright):  python3 tests/e2e_plan_journal.py http://127.0.0.1:8095 /tmp/show_state.json
"""
import asyncio, sys
from playwright.async_api import async_playwright
from pm_helper import apremarket
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
    await pg.locator('#main .nav-rt [data-rt=plan]').first.click(); await pg.wait_for_timeout(900)
    opened = await pg.evaluate("!!document.querySelector('#gSheet.g-pm')")
    ok(opened, 'the routine card opens the pre-market (the full questionnaire, or the express version after the lock time)')
    await pg.evaluate("document.querySelector('#gSheet [data-g=close]').click()"); await pg.wait_for_timeout(400)
    day = '2027-06-01'   # a day ahead: the full questionnaire whatever the time of the test
    before = None
    await pg.evaluate(f"SweepGame.openPlan('{day}')"); await pg.wait_for_timeout(900)
    # « Not trading today » from the plan (its first screen)
    await pg.locator('#gSheet [data-pm=dayoff]').click(); await pg.wait_for_timeout(1000)
    await pg.evaluate(f"location.hash='#journal/{day}'"); await pg.wait_for_timeout(1500)
    nb = await pg.evaluate("(document.querySelector('#main [data-path=\"pre.bias\"].on')||{}).textContent||''")
    ok(nb.strip() == 'Pas de trade', f'« Not trading today » in the plan shows in the journal ({nb.strip()})')
    # then the plan after all: the sheet
    await pg.evaluate("location.hash='#dashboard'"); await pg.wait_for_timeout(1500)
    await apremarket(pg, day=day, max_loss=800, max_trades=3)
    await pg.evaluate(f"location.hash='#journal/{day}'"); await pg.wait_for_timeout(1800)
    vals = await pg.evaluate("Object.fromEntries([...document.querySelectorAll('#main [data-bind*=\"|pre.\"]')].map(e=>[e.dataset.bind.split('|').pop(), e.value.replace(/[\\u00a0\\u202f]/g, ' ')]))")
    bias = await pg.evaluate("(document.querySelector('#main [data-path=\"pre.bias\"].on')||{}).dataset?.v")
    ok(bias == 'bullish', f'journal: the bias of the plan, from the main scenario (long) ({bias})')
    ok(vals.get('pre.max_loss') == '800' and vals.get('pre.max_trades') == '3' and vals.get('pre.levels') == 'LH 5 820 · LL 5 800 · PDH 5 850 · PDL 5 770', f'journal: max loss, max trades, key levels of the plan ({vals.get("pre.max_loss")}, {vals.get("pre.max_trades")}, {vals.get("pre.levels")})')
    await pg.wait_for_timeout(1500); await pg.evaluate("(d) => remove('journals', d)", day); await pg.wait_for_timeout(1500)
    if before: await pg.evaluate("(j) => put('journals', j)", before); await pg.wait_for_timeout(1200)
    ok(not errs, 'no browser error' + ('' if not errs else ': ' + ' | '.join(errs[:3])))
    await br.close()
  print(f'\n{"all passed" if not fails else str(fails) + " failed"}'); sys.exit(1 if fails else 0)
asyncio.run(main())
