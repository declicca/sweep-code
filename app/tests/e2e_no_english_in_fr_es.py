"""E20 · No English sentence left on the main pages in French and Spanish (sample account, phone and computer)."""
import asyncio, re
from playwright.async_api import async_playwright
EN = re.compile(r"\b(Not enough data|See all|Add a trade|Your routine|Trades in your plan|Win rate|No trade|Net P&L|Payouts received|Share my|What to watch|Quick access|Settings|Search trades|This week|This month|Copy to|Copy this trade|Same prices|stay in sync|already on every|Delete all|Delete this copy|Share trade card|Edit trade)\b")
PAGES = ['#dashboard', '#trades', '#calendar', '#journal', '#analytics', '#accounts', '#payouts', '#settings', '#news']
async def main():
  async with async_playwright() as p:
    br = await p.chromium.launch(); bad = []
    for lang in ['fr', 'es']:
      for kw in [p.devices['iPhone 13'], {'viewport': {'width': 1440, 'height': 900}}]:
        ctx = await br.new_context(**kw, storage_state='/tmp/show_state.json'); pg = await ctx.new_page()
        await pg.add_init_script(f"sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('{lang}'))")
        for h in PAGES:
          await pg.goto('http://127.0.0.1:8095/?x=1' + h); await pg.wait_for_timeout(1800)
          txt = await pg.evaluate("document.querySelector('.main-wrap') ? document.querySelector('.main-wrap').innerText : document.body.innerText")
          for m in set(EN.findall(txt)): bad.append(f'{lang} {h}: « {m} »')
        # a trade page: its « ⋯ » menu and the copy panel (points 11)
        tid = await pg.evaluate("(()=>{const t=(S.trades||[]).find(x=>!x.demo)||(S.trades||[])[0]; return t&&t.id})()")
        if tid:
          await pg.goto(f'http://127.0.0.1:8095/?x=2#trade/{tid}'); await pg.wait_for_timeout(1800)
          for sm in await pg.locator('#main details.menu summary').all():
            try: await sm.click(); await pg.wait_for_timeout(200)
            except Exception: pass
          if await pg.locator('#main [data-act=copy-open]').count(): await pg.locator('#main [data-act=copy-open]').first.evaluate('b=>b.click()'); await pg.wait_for_timeout(500)
          txt = await pg.evaluate("[...document.querySelectorAll('#main details.menu, #main .surface')].map(e=>e.innerText).join('\\n')")
          for m in set(EN.findall(txt)): bad.append(f'{lang} #trade (menu « ⋯ » / copy panel): « {m} »')
        else: bad.append(f'{lang}: no trade to open (menu « ⋯ » and copy panel not checked)')
        await ctx.close()
    print('English left:', len(set(bad))); [print('  ', b) for b in sorted(set(bad))[:20]]
    await br.close()
asyncio.run(main())
