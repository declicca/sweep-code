import asyncio, json, sys
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
SKIP=r'del|remove|logout|reset|clear|archive|export|upload|demo|cmd|add-trade|ev-open|more|import|file|delete|copy|share|save-img|full|print|ask|ai-|stripe|checkout|buy|cancel|close|logout|sb-|plan-|referral|invite|crew|discord|claim|install|nt-'
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    ctx=await br.new_context(viewport={'width':390,'height':844},device_scale_factor=2,is_mobile=True,has_touch=True,color_scheme='dark',locale='fr-CA',storage_state='/tmp/show_state.json')
    await ctx.add_init_script("""sessionStorage.setItem('sw.modal','1'); localStorage.setItem('sw.guide', JSON.stringify({tips:{},hideStart:true,visited:{}}));
      document.addEventListener('DOMContentLoaded',()=>{const st=document.createElement('style'); st.textContent='*{overflow-anchor:none!important}'; document.head.append(st)});
      window.__anim=[]; document.addEventListener('animationstart', e=>window.__anim.push(((e.target.className||e.target.tagName)+'').split(' ')[0]+':'+e.animationName), true);
      window.__canv=0; new MutationObserver(ms=>{for(const m of ms) for(const n of m.addedNodes){ if(n.nodeType===1 && (n.tagName==='CANVAS' || (n.querySelector && n.querySelector('canvas')))) window.__canv++ }}).observe(document,{childList:true,subtree:true});""")
    pg=await ctx.new_page(); pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
    async def slow(route):
      if route.request.method in ('POST','PUT','PATCH','DELETE'): await asyncio.sleep(0.2)
      await route.continue_()
    await pg.route('**/api/**', slow)
    await pg.goto(B+'/?x=1#dashboard'); await pg.wait_for_timeout(3000)
    tid=await pg.evaluate("S.trades.filter(t=>t.demo)[0].id"); aid=await pg.evaluate("S.accounts[0].id")
    PAGES=['#dashboard','#trades','#calendar','#journal','#journal/weekly','#analytics','#accounts','#payouts',f'#account/{aid}','#settings','#news',f'#trade/{tid}']
    for route in PAGES:
      await pg.evaluate(f"location.hash='{route}'"); await pg.wait_for_timeout(1800)
      # candidate controls: visible, in #main, that act in place (no navigation, nothing destructive)
      cands=await pg.evaluate(f"""(()=>{{const skip=new RegExp({json.dumps(SKIP)}); const out=[];
        for(const b of document.querySelectorAll('#main button, #main [role=tab], #main .chip, #main .seg a')){{
          const r=b.getBoundingClientRect(); if(!r.width||!r.height) continue; const act=(b.dataset.act||b.getAttribute('data-kt')||b.getAttribute('data-tn')||b.getAttribute('data-ux-setup')||b.textContent||'').trim();
          if(skip.test(act) || skip.test(b.className) || b.closest('form,.nav-ch')) continue; if(b.tagName==='A' && b.getAttribute('href') && !b.closest('.seg')) continue;
          b.dataset.qa=out.length; out.push(act.slice(0,24)); }} return out}})()""")
      picks=list(range(len(cands)))[:: max(1,len(cands)//8)][:8]
      issues=[]
      for i in picks:
        before_hash=await pg.evaluate("location.hash")
        el=pg.locator(f'[data-qa="{i}"]').first
        if not await el.count(): continue
        try: await el.scroll_into_view_if_needed(timeout=1500)
        except Exception: continue
        await pg.evaluate("window.scrollBy(0, 120)"); await pg.wait_for_timeout(250)
        await pg.evaluate(f"""window.__anim=[]; window.__canv=0; window.__p=[]; window.__stop=false; const k=document.querySelector('[data-qa="{i}"]'); window.__k=k; window.__sig=[k.dataset.act,k.dataset.path,k.dataset.v,k.textContent.trim()].join('|'); window.__y0=k.getBoundingClientRect().top;
          const tick=()=>{{ setTimeout(()=>{{ let e=document.contains(window.__k)? window.__k : [...document.querySelectorAll('#main button, #main a, #main .chip')].find(x=>[x.dataset.act,x.dataset.path,x.dataset.v,x.textContent.trim()].join('|')===window.__sig); if(e) window.__p.push(Math.round(e.getBoundingClientRect().top-window.__y0)); }},0); if(!window.__stop) requestAnimationFrame(tick)}}; requestAnimationFrame(tick);""")
        try: await el.tap(timeout=1500)
        except Exception: continue
        await pg.wait_for_timeout(800)
        r=await pg.evaluate("window.__stop=true; [window.__p, [...new Set(window.__anim)], window.__canv, location.hash]")
        moved=[d for d in r[0] if abs(d)>=6]
        if r[3]!=before_hash: await pg.evaluate(f"location.hash='{route}'"); await pg.wait_for_timeout(1200); continue   # it navigated: not an in-place control
        # a move that stays is the page legitimately changing; a move that comes back is a jump
        jump = moved and r[0] and abs(r[0][-1])<6
        anims=[a for a in r[1] if not a.startswith('nav-dot') and 'spin' not in a and 'shimmer' not in a and 'sc-sh' not in a and 'toastIn' not in a]
        if jump or anims or r[2]>0: issues.append(f"{cands[i]!r}: " + ', '.join(filter(None,[f'jump {max(moved,key=abs)}px' if jump else '', f'animations {anims[:4]}' if anims else '', f'{r[2]} canvas rebuilt' if r[2] else ''])))
        await pg.evaluate("document.querySelectorAll('#gSheet [data-g=close]').forEach(b=>b.click()); typeof closeTicket==='function'&&closeTicket()"); await pg.wait_for_timeout(300)
      print(f"{route:22} tested {len(picks):2} controls | {'OK' if not issues else ' ; '.join(issues)[:400]}")
    print('errors', errs[:3]); await br.close()
asyncio.run(main())
