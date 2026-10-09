import asyncio, re
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    for w,h,mob in [(1440,900,False),(390,844,True)]:
      ctx=await br.new_context(viewport={'width':w,'height':h},device_scale_factor=2 if mob else 1,is_mobile=mob,has_touch=mob,color_scheme='dark',locale='fr-CA',storage_state='/tmp/show_state.json')
      await ctx.add_init_script("sessionStorage.setItem('sw.modal','1')")
      await ctx.grant_permissions(['clipboard-read','clipboard-write'])
      pg=await ctx.new_page(); pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
      await pg.goto(B+'/?x=1#analytics'); await pg.wait_for_timeout(2500)
      b=pg.locator('.nav-shstats')
      print(w, '| button on Stats:', await b.count(), (await b.inner_text()).strip() if await b.count() else '')
      await b.click(); await pg.wait_for_timeout(2000)
      print('   card:', await pg.evaluate("(()=>{const d=shData(SH.kind,SH.id); return d.label+' · '+d.eyebrow+' · '+d.big+' · '+JSON.stringify(d.stats)+' · chart:'+(d.chart?d.chart.length:0)})()"))
      if mob: await pg.locator('#shPanel').screenshot(path='/tmp/shst_card.png')
      await pg.locator('#shPanel [data-stl-go], #shPanel [data-shl=create]').first.click(); await pg.wait_for_timeout(5000)
      url=await pg.evaluate("(document.querySelector('#shPanel .nav-shl input')||{}).value||''")
      print('   link:', url)
      if mob: await pg.locator('#shPanel .nav-shl').screenshot(path='/tmp/shst_link.png')
      # anyone can open it, without an account
      anon=await br.new_context(viewport={'width':1200,'height':900})
      ap=await anon.new_page(); r=await ap.goto(url); await ap.wait_for_timeout(800)
      html=await ap.content()
      print('   public page:', r.status, '| full Stats page:', await ap.evaluate("!!document.querySelector('#main .ikpis')"), '| og:image:', bool(re.search(r'og:image" content="[^"]+/s/[A-Za-z0-9]+\.png', html)), '| numbers shown:', await ap.evaluate("[...document.querySelectorAll('.st')].map(e=>e.innerText.replace(/\\n/g,': ')).join(' | ')"))
      img=await anon.request.get(url+'.png'); print('   image:', img.status, img.headers.get('content-type'), len(await img.body()), 'bytes')
      if w==1440: await ap.screenshot(path='/tmp/shst_public.png', full_page=True)
      # delete → gone
      await pg.locator('#shPanel [data-stl-del], #shPanel [data-shl=delete]').first.click(); await pg.wait_for_timeout(1200)
      r2=await ap.goto(url); print('   after « Supprimer le lien »:', r2.status)
      await anon.close(); await ctx.close()
    print('errors', errs[:3]); await br.close()
asyncio.run(main())
