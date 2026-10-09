import asyncio
from playwright.async_api import async_playwright
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); ctx=await br.new_context(viewport={'width':1440,'height':900}, storage_state='/tmp/show_state.json', locale='fr-CA', color_scheme='dark'); pg=await ctx.new_page()
    await pg.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'))")
    await pg.goto('http://127.0.0.1:8095/?x=1#accounts'); await pg.wait_for_timeout(2500)
    await pg.locator('#main [data-act=acct-add][data-v="1"]').first.click(); await pg.wait_for_timeout(900)
    await pg.locator('#main form[data-form=account] [data-st-ph0=live]').click(); await pg.wait_for_timeout(900)
    print('visible fields:', await pg.evaluate("[...document.querySelectorAll('#main form.nav-live input, #main form.nav-live select')].filter(i=>i.offsetParent).map(i=>i.name).join(', ')"))
    f='#main form[data-form=account]'
    if await pg.locator(f+' [name=firm]').is_visible(): await pg.select_option(f+' [name=firm]', index=0)
    if await pg.locator(f+' [name=firmName]').is_visible(): await pg.fill(f+' [name=firmName]','Interactive Brokers')
    await pg.fill(f+' [name=name]','IBKR Live'); await pg.fill(f+' [name=start]','25000')
    await pg.locator('#main form[data-form=account]').screenshot(path='/tmp/lv.png')
    n0=await pg.evaluate("S.accounts.length"); await pg.locator(f+' [type=submit]').click(); await pg.wait_for_timeout(2000)
    print('account created:', await pg.evaluate("S.accounts.length")-n0, '|', await pg.evaluate("JSON.stringify((S.accounts.slice(-1)[0]||{}).name)"), '| rules preset:', await pg.evaluate("JSON.stringify(Object.keys((S.accounts.slice(-1)[0]||{}).rules||{}))"))
    await pg.evaluate("const a=S.accounts.slice(-1)[0]; if(a&&a.name==='IBKR Live') remove('accounts',a.id)")
    await br.close()
asyncio.run(main())
