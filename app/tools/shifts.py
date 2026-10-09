"""Layout shifts while a page loads: which elements move, when, and by how much.
   python3 tools/shifts.py <base_url> [hash] [runs] [state_file]   (computer 1300×850, or SIZE=mobile for 390×844; fr-CA, dark)"""
import asyncio, json, os, sys, urllib.parse
from playwright.async_api import async_playwright
BASE = sys.argv[1]; H = sys.argv[2] if len(sys.argv) > 2 else '#dashboard'; RUNS = int(sys.argv[3]) if len(sys.argv) > 3 else 3
STATE = sys.argv[4] if len(sys.argv) > 4 else '/tmp/show_state.json'
def state_for(base, path):
    st = json.load(open(path)); o = urllib.parse.urlsplit(base); origin = '%s://%s' % (o.scheme, o.netloc)
    if st.get('origins') and not any(x['origin'] == origin for x in st['origins']): st['origins'].append(dict(st['origins'][0], origin=origin))
    return st
OBS = """window.__ls=[];new PerformanceObserver(l=>{for(const e of l.getEntries()){if(e.hadRecentInput)continue;
window.__ls.push({t:Math.round(e.startTime),v:+e.value.toFixed(4),src:e.sources.map(s=>{const n=s.node;const d=n&&n.nodeType===1?(n.tagName.toLowerCase()+(n.id?'#'+n.id:'')+(n.className&&typeof n.className==='string'?'.'+n.className.trim().split(/\\s+/).slice(0,3).join('.'):'')):(n?n.nodeName:'?');
return d+' y'+Math.round(s.previousRect.y)+'→'+Math.round(s.currentRect.y)+' x'+Math.round(s.previousRect.x)+'→'+Math.round(s.currentRect.x)+' h'+Math.round(s.previousRect.height)+'→'+Math.round(s.currentRect.height)})})}}).observe({type:'layout-shift',buffered:true});
sessionStorage.setItem('sw.modal','1');"""
async def main():
    async with async_playwright() as p:
        br = await p.chromium.launch()
        for i in range(RUNS):
            size = dict(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True, device_scale_factor=3) if os.environ.get('SIZE') == 'mobile' else dict(viewport={'width': 1300, 'height': 850})
            ctx = await br.new_context(storage_state=state_for(BASE, STATE), locale='fr-CA', color_scheme='dark', **size)
            await ctx.add_init_script(OBS); pg = await ctx.new_page()
            await pg.goto(BASE + '/' + H, wait_until='networkidle'); await pg.wait_for_timeout(2500)
            ls = await pg.evaluate('window.__ls'); print('run', i + 1, 'CLS', round(sum(e['v'] for e in ls), 4))
            for e in ls: print('  ', e['t'], 'ms', e['v'], *e['src'][:4], sep='  ')
            await ctx.close()
        await br.close()
asyncio.run(main())
