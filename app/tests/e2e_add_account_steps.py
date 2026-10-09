import asyncio
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    ctx=await br.new_context(viewport={'width':390,'height':844},device_scale_factor=2,is_mobile=True,has_touch=True,color_scheme='dark',locale='fr-CA',storage_state='/tmp/show_state.json')
    await ctx.add_init_script("sessionStorage.setItem('sw.modal','1')")
    pg=await ctx.new_page(); pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
    await pg.goto(B+'/?x=1#accounts'); await pg.wait_for_timeout(2500)
    await pg.get_by_text('Ajouter un compte').first.click(); await pg.wait_for_timeout(1500)
    form=pg.locator('form[data-form=account]')
    async def shot(n):
      await form.scroll_into_view_if_needed(); await pg.wait_for_timeout(250); await form.screenshot(path=f'/tmp/st_{n}.png')
    print('visible fields at start:', await pg.evaluate("[...document.querySelectorAll('form[data-form=account] input, form[data-form=account] select')].filter(e=>e.offsetParent).length"))
    await shot(1)
    print('first question:', await pg.locator('form[data-form=account] .ux-st-q').first.inner_text())
    await pg.locator('[data-st-ph0=eval]').tap(); await pg.wait_for_timeout(300)
    await pg.locator('[data-st-firm=topstep]').tap(); await pg.wait_for_timeout(300)
    # Topstep has one account type: does it ask anyway?
    await shot(2)
    print('Topstep skips the type step:', await pg.locator('[data-st-size]').count() > 0); await shot(3)
    await pg.locator('[data-st-size="50000"]').tap(); await pg.wait_for_timeout(300)
    await pg.locator('.ux-st-opt').scroll_into_view_if_needed(); await pg.locator('.ux-st-opt').click(); await pg.wait_for_timeout(300); print('option on:', await pg.locator('[data-st-dll]').is_checked()); await shot(4)
    print('fields filled:', await pg.evaluate("(()=>{const f=document.querySelector('form[data-form=account]'); return [(f.querySelector('[name=name]')||{}).value,(f.querySelector('[name=start]')||{}).value,(f.querySelector('[name=firm]')||{}).value, f.dataset.uxPreset].join(' | ')})()"))
    await pg.locator('[data-st-go=firm]').tap(); await pg.wait_for_timeout(300)
    print('back to firms via the crumb:', await pg.locator('[data-st-firm]').count() > 0)
    await pg.locator('[data-st-manual]').tap(); await pg.wait_for_timeout(300)
    print('manual: app fields visible again:', await pg.evaluate("[...document.querySelectorAll('form[data-form=account] input, form[data-form=account] select')].filter(e=>e.offsetParent).length"))
    await shot(5)
    await pg.locator('.ux-st-manualback').tap(); await pg.wait_for_timeout(300)
    await pg.locator('[data-st-firm=lucid]').tap(); await pg.locator('[data-st-type=lucidflex]').tap(); await pg.locator('[data-st-size="50000"]').tap(); await pg.wait_for_timeout(300)
    await pg.evaluate("document.querySelector('form[data-form=account]').requestSubmit()"); await pg.wait_for_timeout(2000)
    print('created:', await pg.evaluate("(()=>{const a=S.accounts.find(a=>a.name==='LucidFlex 50K'); return a? (firm(a.firm_id)||{}).name+' '+JSON.stringify(a.rules):'none'})()"))
    print('errors', errs[:3]); await br.close()
asyncio.run(main())
