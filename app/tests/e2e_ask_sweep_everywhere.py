import asyncio
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    for w,h,mob in [(1440,900,False),(390,844,True)]:
      ctx=await br.new_context(viewport={'width':w,'height':h},is_mobile=mob,has_touch=mob,locale='fr-CA',storage_state='/tmp/show_state.json')
      await ctx.add_init_script("sessionStorage.setItem('sw.modal','1')")
      pg=await ctx.new_page(); pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
      await pg.goto(B+'/?x=1#dashboard'); await pg.wait_for_timeout(2500)
      await pg.evaluate("AI.on = true; document.body.classList.add('ai-on'); askShow(true); render()"); await pg.wait_for_timeout(600)
      res=[]
      for r in ['#dashboard','#trades','#calendar','#journal','#analytics','#accounts','#settings']:
        await pg.evaluate(f"location.hash='{r}'"); await pg.wait_for_timeout(900)
        res.append(r+':'+await pg.evaluate("(()=>{const f=document.getElementById('askFab'); if(!f) return 'none'; const cs=getComputedStyle(f), b=f.getBoundingClientRect(); return cs.display==='none'||cs.visibility==='hidden'||+cs.opacity<.1 ? 'hidden('+cs.display+')' : 'visible@'+Math.round(b.right)+','+Math.round(b.bottom)})()"))
      print(w, ' | '.join(res))
      for r in ['#journal','#analytics']:
        await pg.evaluate(f"location.hash='{r}'"); await pg.wait_for_timeout(800)
        await pg.locator('#askFab').click(); await pg.wait_for_timeout(700)
        print('   ', r, 'starters:', await pg.evaluate("[...document.querySelectorAll('#askPanel .ask-chips button')].map(b=>b.textContent).join(' | ')"))
        await pg.evaluate("askToggle(false)"); await pg.wait_for_timeout(400)
      tid=await pg.evaluate("S.trades[0].id"); await pg.evaluate(f"location.hash='#trade/{tid}'"); await pg.wait_for_timeout(1200)
      await pg.locator('#askFab').click(); await pg.wait_for_timeout(700)
      print('    #trade starters:', await pg.evaluate("[...document.querySelectorAll('#askPanel .ask-chips button')].map(b=>b.textContent).join(' | ')"))
      await pg.evaluate("askToggle(false)"); await pg.wait_for_timeout(400)
      await pg.evaluate("openTicket()"); await pg.wait_for_timeout(900)
      print('    with the add-trade form open, button hidden:', await pg.evaluate("getComputedStyle(document.getElementById('askFab')).opacity==='0'"))
      await pg.evaluate("closeTicket()"); await pg.wait_for_timeout(400)
      await pg.evaluate("location.hash='#trades'"); await pg.wait_for_timeout(800)
      await pg.screenshot(path=f'/tmp/fab_{w}.png')
      await ctx.close()
    print('errors', errs[:3]); await br.close()
asyncio.run(main())
