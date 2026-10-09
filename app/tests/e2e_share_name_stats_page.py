import asyncio, datetime, sys
from playwright.async_api import async_playwright
B='http://127.0.0.1:8095'
async def main():
  async with async_playwright() as p:
    br=await p.chromium.launch(); errs=[]
    ctx=await br.new_context(viewport={'width':1440,'height':900},device_scale_factor=1,color_scheme='dark',locale='fr-CA',storage_state='/home/claude/media/alex_state.json')
    await ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'))")
    await ctx.grant_permissions(['clipboard-read','clipboard-write'])
    pg=await ctx.new_page(); await pg.clock.install(time=datetime.datetime(2026,10,6,15,40,0,tzinfo=datetime.timezone.utc)); pg.on('pageerror',lambda e: errs.append(str(e)[:150]))
    await pg.goto(B+'/?x=1#analytics'); await pg.wait_for_timeout(3000)
    await pg.evaluate("F.period='week'; render()"); await pg.wait_for_timeout(1500)
    await pg.locator('.nav-shstats').click(); await pg.wait_for_timeout(2500)
    print('opens first:', await pg.evaluate("SH.kind"), '| discipline card:', await pg.evaluate("(()=>{const d=shData('discipline','view'); return d.label+' · '+d.big+' · '+JSON.stringify(d.stats)})()"))
    await pg.locator('#shPanel [data-dk=stats]').click(); await pg.wait_for_timeout(2200)
    print('card name:', await pg.evaluate("shData('stats','view').who"), '| placed:', await pg.evaluate("shData('stats','view').whoAt"))
    await pg.locator('#shPanel .sh-prev').screenshot(path='/tmp/sp_stats_card.png')
    print('link box: period default =', await pg.evaluate("(document.querySelector('#shPanel [data-stl-per].on')||{}).textContent"), '| parts on:', await pg.evaluate("[...document.querySelectorAll('#shPanel [data-stl-part].on')].length"))
    await pg.locator('#shPanel').screenshot(path='/tmp/sp_panel.png')
    # choose this month and drop the detailed analysis
    await pg.locator('#shPanel [data-stl-per=month]').click(); await pg.locator('#shPanel [data-stl-part=deep]').click(); await pg.wait_for_timeout(300)
    await pg.locator('#shPanel [data-stl-go]').click(); await pg.wait_for_timeout(5000)
    url=await pg.evaluate("(document.querySelector('#shPanel .nav-shl input')||{}).value||''"); print('link:', url, '| app period back to:', await pg.evaluate("F.period"))
    pub=await br.new_context(viewport={'width':1440,'height':900},color_scheme='dark'); pp=await pub.new_page(); r=await pp.goto(url); await pp.wait_for_timeout(1500)
    print('public page:', r.status, '| title:', await pp.title(), '| parts:', await pp.evaluate("['.ikpis','.nav-slip','.g-top','.g-ins','.g-two','section.ic','section.deep'].map(s=>s+':'+document.querySelectorAll('#main '+s).length).join(' ')"), '| styled:', await pp.evaluate("getComputedStyle(document.querySelector('#main .ikpis')||document.body).display"))
    await pp.screenshot(path='/tmp/sp_public.png', full_page=True); await pub.close()
    await pg.evaluate("closeShare()"); await pg.wait_for_timeout(500)
    # payout card
    await pg.evaluate("location.hash='#payouts'"); await pg.wait_for_timeout(2000)
    await pg.evaluate("openShare('payout','po-3')"); await pg.wait_for_timeout(2500)
    d=await pg.evaluate("(()=>{const d=shData('payout','po-3'); return {who:d.who, at:d.whoAt, sub:d.sub, chart:d.chart&&d.chart.length, last:d.chart&&d.chart.slice(-3).map(Math.round), max:d.chart&&Math.round(Math.max(...d.chart)), bars:d.bars}})()")
    print('payout card:', d)
    await pg.locator('#shPanel .sh-prev').screenshot(path='/tmp/sp_payout.png')
    await pg.evaluate("closeShare()"); await pg.wait_for_timeout(500)
    await pg.evaluate("openShare('net','all')"); await pg.wait_for_timeout(2500); await pg.locator('#shPanel .sh-prev').screenshot(path='/tmp/sp_net.png')
    print('errors', errs[:3]); await br.close()
asyncio.run(main())
