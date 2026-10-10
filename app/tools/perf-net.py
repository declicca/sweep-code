"""Speed on a simulated phone, as in brief 01 (step 3): CPU ×4, network 1.6 Mbit/s down / 750 kbit/s up, 150 ms latency,
empty cache. Old and new code served side by side (same data), measured alternately, median of N.
   python3 tools/perf-net.py <base_A> <base_B> [passes] [state_file]
Per page: first paint (FCP), the page ready (#main filled), load event, kilobytes transferred."""
import asyncio, json, statistics, sys, urllib.parse
from playwright.async_api import async_playwright
A, B = sys.argv[1], sys.argv[2]; N = int(sys.argv[3]) if len(sys.argv) > 3 else 3
STATE = sys.argv[4] if len(sys.argv) > 4 else '/tmp/show_state.json'
PAGES = ['#dashboard', '#trades', '#analytics', '#accounts']
def state_for(base):
    st = json.load(open(STATE)); o = urllib.parse.urlsplit(base); origin = '%s://%s' % (o.scheme, o.netloc)
    if st.get('origins') and not any(x['origin'] == origin for x in st['origins']): st['origins'].append(dict(st['origins'][0], origin=origin))
    return st
async def one(br, base, page):
    ctx = await br.new_context(storage_state=state_for(base), viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True, device_scale_factor=3, locale='fr-CA')
    await ctx.add_init_script("sessionStorage.setItem('sw.modal','1')")
    pg = await ctx.new_page(); cdp = await ctx.new_cdp_session(pg)
    await cdp.send('Network.enable'); await cdp.send('Network.setCacheDisabled', {'cacheDisabled': True})
    await cdp.send('Network.emulateNetworkConditions', {'offline': False, 'latency': 150, 'downloadThroughput': 1.6e6 / 8, 'uploadThroughput': 750e3 / 8})
    await cdp.send('Emulation.setCPUThrottlingRate', {'rate': 4})
    kb = [0]; cdp.on('Network.loadingFinished', lambda e: kb.__setitem__(0, kb[0] + e.get('encodedDataLength', 0)))
    await pg.goto(base + '/' + page, wait_until='load', timeout=120000)
    await pg.wait_for_selector('#main > :not(.boot)', state='attached', timeout=120000)
    ready = await pg.evaluate('performance.now()')
    await pg.wait_for_timeout(1500)
    t = await pg.evaluate("(()=>{const n=performance.getEntriesByType('navigation')[0];return {fcp:(performance.getEntriesByName('first-contentful-paint')[0]||{}).startTime||0, load:n.loadEventEnd}})()")
    await ctx.close()
    return {'FCP': t['fcp'] / 1000, 'prêt': ready / 1000, 'load': t['load'] / 1000, 'Ko': kb[0] / 1024}
async def main():
    async with async_playwright() as p:
        br = await p.chromium.launch()
        for page in PAGES:
            res = {A: [], B: []}
            for i in range(N):
                for base in ((A, B) if i % 2 == 0 else (B, A)): res[base].append(await one(br, base, page))
            med = {b: {k: statistics.median(r[k] for r in res[b]) for k in res[b][0]} for b in res}
            print(f"{page:11} " + '   '.join(f"{k} {med[A][k]:.1f}{' s' if k != 'Ko' else ''} → {med[B][k]:.1f}{' s' if k != 'Ko' else ''}" for k in med[A]), flush=True)
        await br.close()
asyncio.run(main())
