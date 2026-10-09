"""Three simulated returns (server AND browser clocks moved): tomorrow 08:30, 12:00 and 18:30 ET. Today + the highlighted step."""
import asyncio, sys, datetime
from playwright.async_api import async_playwright
H, M, TAG = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
async def main():
  async with async_playwright() as p:
    br = await p.chromium.launch(); ctx = await br.new_context(**p.devices['iPhone 13'], storage_state='/home/claude/media/alex_state.json', locale='fr-CA', color_scheme='dark'); pg = await ctx.new_page()
    await pg.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'))")
    await pg.clock.install(time=datetime.datetime(2026, 10, 7, H + 4, M, 0, tzinfo=datetime.timezone.utc))
    await pg.goto('http://127.0.0.1:8095/?x=1#dashboard'); await pg.wait_for_selector('.nav-rt-steps', timeout=15000); await pg.wait_for_timeout(1200)
    r = await pg.evaluate("""(()=>{const n=document.querySelector('.nav-rt-steps'); const k=n&&n.dataset.next; const s=k&&document.querySelectorAll('.nav-rt-s')[k-1]; const p=document.querySelector('.nav-rt .nav-rt-pill'); return 'next step: '+(s? s.querySelector('h3,b').textContent.trim():'none (day done or closed)')+' | primary button: '+((s&&s.querySelector('.btn.primary'))||{textContent:'—'}).textContent.trim()+' | status: '+(p?p.textContent.trim():'')})()""")
    print(f'{TAG} ({H:02d}:{M:02d} ET) → {r}')
    await pg.screenshot(path=f'/tmp/ret_{TAG}.png'); await br.close()
asyncio.run(main())
