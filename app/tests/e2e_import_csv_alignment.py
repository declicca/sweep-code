import asyncio
from playwright.async_api import async_playwright
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch()
    for w,mob in [(1440,False),(390,True)]:
      ctx=await br.new_context(viewport={'width':w,'height':900 if not mob else 844},device_scale_factor=2,is_mobile=mob,has_touch=mob, storage_state='/home/claude/media/alex_state.json', color_scheme='dark', locale='fr-CA'); pg=await ctx.new_page()
      await pg.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'))")
      for h in ['#trades','#calendar','#journal']:
        await pg.goto('http://127.0.0.1:8095/?x=1'+h); await pg.wait_for_timeout(2500)
        print(w, h, await pg.evaluate("(()=>{const a=document.querySelector('.main-wrap > .top .nav-imp-b'), b=document.querySelector('.main-wrap > .top .nav-addtop'); if(!a||!b) return 'missing'; const A=a.getBoundingClientRect(), B=b.getBoundingClientRect(); return 'mid '+Math.round(A.top+A.height/2)+'/'+Math.round(B.top+B.height/2)+' h '+Math.round(A.height)+'/'+Math.round(B.height)+' gap '+Math.round(B.left-A.right)+' | '+a.innerText.trim()})()"))
      await pg.locator('.main-wrap > .top').first.screenshot(path=f'/tmp/i4_{w}.png')
      await ctx.close()
    await br.close()
asyncio.run(main())
