import asyncio, random
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    for w,h,mob in [(1440,900,False),(1150,800,False),(390,844,True)]:
      ctx=await br.new_context(viewport={'width':w,'height':h},device_scale_factor=1 if not mob else 2,is_mobile=mob,has_touch=mob,color_scheme='dark',locale='en-US')
      await ctx.add_init_script("sessionStorage.setItem('sw.modal','1')")
      pg=await ctx.new_page(); pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
      u='gs%d'%random.randint(1000,9999)
      await ctx.request.post(B+'/api/auth/register', data={'username':u,'password':'Testpass123!','email':u+'@t.dev','consent':True,'elapsed':6000}, headers={'X-Requested-With':'fetch'})
      await pg.goto(B+'/?x=1#dashboard'); await pg.wait_for_timeout(1500)
      await pg.evaluate("put('accounts',{id:'a-gs',name:'50K',firm_id:'',starting_balance_c:5000000,status:'active'}); put('trades',{id:'t-gs',account_id:'a-gs',instrument:'NQ',date:'2026-10-02',entry_time:'10:00:00',exit_time:'10:05:00',direction:'long',contracts:1,entry:30100,exit:30120,pnl_c:4000,emo:{},review:{},discipline:{}})"); await pg.wait_for_timeout(1500)
      await pg.reload(); await pg.wait_for_timeout(3500)
      r=await pg.evaluate("""(()=>{const g=document.querySelector('.gd-start'); if(!g) return 'no Get started'; const inDay=!!g.closest('.d-today'); const r=g.getBoundingClientRect(); const d=document.querySelector('.d-today'); const dr=d.getBoundingClientRect(); const vis=[...document.querySelectorAll('.nav-dash .d-col > *, .nav-dash .gd-start')].filter(e=>e.offsetHeight).sort((a,b)=>a.getBoundingClientRect().top-b.getBoundingClientRect().top||a.getBoundingClientRect().left-b.getBoundingClientRect().left).map(e=>e.classList.contains('gd-start')?'GET-STARTED':[...e.classList].find(c=>c.startsWith('d-'))).slice(0,5).join(' → '); return vis+' | inside day card: '+inDay+' | visible: '+(r.height>0)+' | width '+Math.round(r.width)+' vs day card '+Math.round(dr.width)+' | right after the day card: '+(g.previousElementSibling===d)})()""")
      print(w, r)
      if w==1150: await pg.screenshot(path='/tmp/gs.png', clip={'x':0,'y':0,'width':w,'height':620})
      await ctx.close()
    print('errors', errs[:3]); await br.close()
asyncio.run(main())
