import asyncio
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    for w,h,mob in [(1440,900,False),(390,844,True)]:
      ctx=await br.new_context(viewport={'width':w,'height':h},device_scale_factor=1 if not mob else 2,is_mobile=mob,has_touch=mob,color_scheme='dark',locale='fr-CA',storage_state='/tmp/show_state.json')
      await ctx.add_init_script("sessionStorage.setItem('sw.modal','1')")
      pg=await ctx.new_page(); pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
      await pg.goto(B+'/?x=1#accounts'); await pg.wait_for_timeout(2000)
      aid=await pg.evaluate("S.accounts.find(a=>a.status!=='archived').id")
      await pg.evaluate(f"location.hash='#account/{aid}'"); await pg.wait_for_timeout(2500)
      box=pg.locator('.ux-preset-apply')
      card=box.locator('xpath=ancestor::*[contains(@class,\"surface\")][1]')
      bw=(await box.bounding_box())['width']; cw=(await card.bounding_box())['width'] if await card.count() else 0
      print(w, '| folded:', await box.evaluate("e=>e.classList.contains('folded')"), '| width', round(bw), 'of card', round(cw))
      await card.screenshot(path=f'/tmp/ap_{w}_a.png')
      await box.locator('[data-st-open]').click(); await pg.wait_for_timeout(400)
      if await box.locator('[data-st-type]').count()==0 and await box.locator('[data-st-firm]').count(): await box.locator('[data-st-firm]').first.click(); await pg.wait_for_timeout(300)
      await box.locator('[data-st-type]').first.click(); await pg.wait_for_timeout(300)
      await box.locator('[data-st-size]').nth(1).click(); await pg.wait_for_timeout(300)
      await card.screenshot(path=f'/tmp/ap_{w}_b.png')
      await box.locator('[data-pk-apply]').click(); await pg.wait_for_timeout(1500)
      print('   applied, folded again:', await pg.locator('.ux-preset-apply').evaluate("e=>e.classList.contains('folded')"), '| labels FR:', await pg.evaluate("['Règles de la firme','Type de drawdown','Jours de trading minimum','Copier les règles'].every(t=>document.querySelector('#main').innerText.includes(t))"))
      await ctx.close()
    print('errors', errs[:3]); await br.close()
asyncio.run(main())
