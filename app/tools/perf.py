"""Speed measures, old vs new code served side by side, measured alternately (median of N passes).
   python3 tools/perf.py <base_url_A> <base_url_B> [passes] [state_file]
   Per page × size: FCP, LCP, TBT (long tasks over 50 ms after navigation), script / style / layout time (CDP), CLS, bytes."""
import asyncio, statistics, sys
from playwright.async_api import async_playwright
A, B = sys.argv[1], sys.argv[2]; N = int(sys.argv[3]) if len(sys.argv) > 3 else 3
STATE = sys.argv[4] if len(sys.argv) > 4 else '/tmp/show_state.json'
PAGES = ['#dashboard', '#trades', '#calendar', '#analytics', '#accounts']
SIZES = {'mobile': dict(viewport={'width': 390, 'height': 844}, device_scale_factor=3, is_mobile=True, has_touch=True), 'desktop': dict(viewport={'width': 1300, 'height': 850})}
OBS = """window.__p={lt:0,cls:0,lcp:0};new PerformanceObserver(l=>{for(const e of l.getEntries())window.__p.lt+=Math.max(0,e.duration-50)}).observe({type:'longtask',buffered:true});
new PerformanceObserver(l=>{for(const e of l.getEntries())if(!e.hadRecentInput)window.__p.cls+=e.value}).observe({type:'layout-shift',buffered:true});
new PerformanceObserver(l=>{const e=l.getEntries();window.__p.lcp=e[e.length-1].startTime}).observe({type:'largest-contentful-paint',buffered:true});
sessionStorage.setItem('sw.modal','1');"""
def state_for(base, path):
    """The saved session (cookies + localStorage) made valid for this server too: localStorage is per origin (port)."""
    import json, urllib.parse
    st = json.load(open(path)); o = urllib.parse.urlsplit(base); origin = '%s://%s' % (o.scheme, o.netloc)
    if st.get('origins') and not any(x['origin'] == origin for x in st['origins']):
        st['origins'].append(dict(st['origins'][0], origin=origin))
    return st
async def one(br, base, size, page):
    ctx = await br.new_context(locale='fr-CA', color_scheme='dark', storage_state=state_for(base, STATE), **SIZES[size])
    await ctx.add_init_script(OBS); pg = await ctx.new_page(); cdp = await ctx.new_cdp_session(pg)
    await cdp.send('Performance.enable')
    if size == 'mobile': await cdp.send('Emulation.setCPUThrottlingRate', {'rate': 4})
    nbytes = [0]; pg.on('response', lambda r: None)
    await cdp.send('Network.enable'); cdp.on('Network.loadingFinished', lambda e: nbytes.__setitem__(0, nbytes[0] + e.get('encodedDataLength', 0)))
    await pg.goto(base + '/' + page, wait_until='networkidle'); await pg.wait_for_timeout(1500)
    m = {x['name']: x['value'] for x in (await cdp.send('Performance.getMetrics'))['metrics']}
    p = await pg.evaluate("({fcp:(performance.getEntriesByName('first-contentful-paint')[0]||{}).startTime||0,...window.__p})")
    await ctx.close()
    return {'FCP': p['fcp'], 'LCP': p['lcp'], 'TBT': p['lt'], 'script': m['ScriptDuration'] * 1000, 'style': m['RecalcStyleDuration'] * 1000, 'layout': m['LayoutDuration'] * 1000, 'CLS': p['cls'], 'KB': nbytes[0] / 1024}
async def main():
    async with async_playwright() as p:
        br = await p.chromium.launch()
        for size in SIZES:
            for page in PAGES:
                res = {A: [], B: []}
                for i in range(N):
                    for base in ((A, B) if i % 2 == 0 else (B, A)): res[base].append(await one(br, base, size, page))
                med = {b: {k: statistics.median(r[k] for r in res[b]) for k in res[b][0]} for b in res}
                print(f"{size:7} {page:11} " + '  '.join(f"{k} {med[A][k]:.0f}→{med[B][k]:.0f}" if k != 'CLS' else f"CLS {med[A][k]:.3f}→{med[B][k]:.3f}" for k in med[A]), flush=True)
        await br.close()
asyncio.run(main())
