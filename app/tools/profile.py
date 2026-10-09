"""CPU profile of one page load (phone, CPU ×4): self time per function, top 30.
   python3 tools/profile.py [base_url] [hash] [state_file]"""
import asyncio, collections, sys
from playwright.async_api import async_playwright
BASE = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:9095'; H = sys.argv[2] if len(sys.argv) > 2 else '#dashboard'
STATE = sys.argv[3] if len(sys.argv) > 3 else '/tmp/show_state.json'
async def main():
    async with async_playwright() as p:
        br = await p.chromium.launch()
        ctx = await br.new_context(storage_state=STATE, viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True, device_scale_factor=3, locale='fr-CA', color_scheme='dark')
        await ctx.add_init_script("sessionStorage.setItem('sw.modal','1')")
        pg = await ctx.new_page(); cdp = await ctx.new_cdp_session(pg)
        await cdp.send('Emulation.setCPUThrottlingRate', {'rate': 4}); await cdp.send('Profiler.enable')
        await cdp.send('Profiler.setSamplingInterval', {'interval': 200}); await cdp.send('Profiler.start')
        await pg.goto(BASE + '/' + H, wait_until='networkidle'); await pg.wait_for_timeout(1500)
        prof = (await cdp.send('Profiler.stop'))['profile']
        nodes = {n['id']: n for n in prof['nodes']}; dt = collections.Counter()
        for sid, d in zip(prof['samples'], prof['timeDeltas']): dt[sid] += d
        agg = collections.Counter()
        for sid, us in dt.items():
            cf = nodes[sid]['callFrame']; agg[(cf['functionName'] or '(anon)', cf['url'].split('/')[-1], cf['lineNumber'] + 1)] += us
        tot = sum(v for k, v in agg.items() if k[0] not in ('(idle)', '(program)'))
        print('JS+GC+native total ms (×4 CPU):', round(tot / 1000))
        for (f, u, l), us in agg.most_common(30): print(f"{us/1000:7.1f} ms  {f[:40]:40} {u}:{l}")
        await br.close()
asyncio.run(main())
