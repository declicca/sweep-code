import asyncio
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    for mob in [False, True]:
      ctx=await br.new_context(viewport={'width':390,'height':844} if mob else {'width':1440,'height':900},is_mobile=mob,has_touch=mob,locale='fr-CA',storage_state='/tmp/show_state.json')
      await ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); sessionStorage.removeItem('tj.ask')")
      pg=await ctx.new_page(); pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
      reqs=[]; pg.on('response', lambda r: '/api/ai/' in r.url and reqs.append(r.url.split('/api/ai/')[1]+' '+str(r.status)))
      await pg.goto(B+'/?x=1#dashboard'); await pg.wait_for_timeout(2500)
      # 1) the chat (Ask Sweep): a suggested question
      await pg.evaluate("askToggle(true)"); await pg.wait_for_timeout(700)
      chip=pg.locator('#askPanel .ask-chips button').first
      print('mobile' if mob else 'desktop', '| chat chips:', await pg.locator('#askPanel .ask-chips button').count())
      if await chip.count():
        if mob: await chip.tap()
        else: await chip.click()
        await pg.wait_for_timeout(1500)
      print('   requests after tapping a chat chip:', reqs, '| last message:', await pg.evaluate("ASK.msgs.length ? ASK.msgs[0].text.slice(0,40) : 'none'"))
      await pg.evaluate("askToggle(false)"); await pg.wait_for_timeout(500)
      # 2) the AI sheet's « Ask » tab
      reqs.clear()
      await pg.evaluate("(()=>{ try { AI.on = true; } catch(e){}; SweepAI.open('ask'); })()"); await pg.wait_for_timeout(900)
      print('   AI sheet:', await pg.evaluate("(document.querySelector('.sai')||{}).className||'none'"), '| tabs:', await pg.evaluate("[...document.querySelectorAll('.sai-tabs button')].map(b=>b.textContent).join(',')"))
      tab=pg.locator('.sai-tabs button', has_text='Demander'); 
      if await tab.count(): await tab.first.click(); await pg.wait_for_timeout(500)
      ex=pg.locator('.sai .sai-chip[data-act=ask-ex]').first
      print('   AI sheet ask chips:', await pg.locator('.sai .sai-chip[data-act=ask-ex]').count())
      if await ex.count():
        if mob: await ex.tap()
        else: await ex.click()
        await pg.wait_for_timeout(1500)
      print('   requests after tapping an Ask-tab chip:', reqs, '| sheet shows:', await pg.evaluate("(document.querySelector('.sai .sai-body')||{}).innerText.slice(0,260).replace(/\\n/g,' | ')"))
      await ctx.close()
    print('errors', errs[:3]); await br.close()
asyncio.run(main())
