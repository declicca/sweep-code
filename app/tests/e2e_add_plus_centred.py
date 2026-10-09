import asyncio
from playwright.async_api import async_playwright
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); ctx=await br.new_context(viewport={'width':1440,'height':900},device_scale_factor=3, storage_state='/tmp/show_state.json', color_scheme='dark', locale='en-US'); pg=await ctx.new_page()
    await pg.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('en'))")
    shots=[]
    for h,sel in [('#trades','#main .nav-addrow'),('#accounts','#main .nav-acc-top .nav-addrow'),('#payouts','#main .nav-pz-b[data-k=payout]'),('#payouts','#main .nav-pz-b[data-k=expense]')]:
      await pg.goto('http://127.0.0.1:8095/?x=1'+h); await pg.wait_for_timeout(2500)
      ic=pg.locator(sel+' .add-ic').first
      r=await ic.evaluate("""e=>{const b=e.getBoundingClientRect(); const s=getComputedStyle(e); return {w:Math.round(b.width),h:Math.round(b.height), bgpos:s.backgroundPosition, text:JSON.stringify(e.textContent)}}""")
      print(h, sel.split(' ')[-1][:24], r)
      bb=await pg.locator(sel).first.bounding_box(); f=f'/tmp/plus_{len(shots)}.png'; await pg.screenshot(path=f, clip={'x':bb['x'],'y':bb['y'],'width':220,'height':bb['height']}); shots.append(f)
    await br.close()
    from PIL import Image
    ims=[Image.open(f) for f in shots]; W=max(i.width for i in ims); H=sum(i.height+6 for i in ims)
    o=Image.new('RGB',(W,H),'white'); y=0
    for i in ims: o.paste(i,(0,y)); y+=i.height+6
    o.save('/tmp/plus_all.png')
asyncio.run(main())
