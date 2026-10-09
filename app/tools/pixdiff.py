"""Visual A/B: same pages on two servers (same data), screenshots compared pixel by pixel.
   python3 tools/pixdiff.py <base_A> <base_B> <out_dir> [state_file]   → prints the share of differing pixels per page."""
import asyncio, sys, os
from playwright.async_api import async_playwright
from PIL import Image, ImageChops
A, B, OUT = sys.argv[1], sys.argv[2], sys.argv[3]; STATE = sys.argv[4] if len(sys.argv) > 4 else '/tmp/show_state.json'
PAGES = os.environ['PAGES'].split() if os.environ.get('PAGES') else ['#dashboard', '#trades', '#calendar', '#analytics', '#accounts', '#payouts', '#journal', '#settings']
SIZES0 = {'mobile': dict(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True, device_scale_factor=2), 'desktop': dict(viewport={'width': 1300, 'height': 850})}
SIZES = {k: v for k, v in SIZES0.items() if k in os.environ.get('SIZES', 'mobile desktop').split()}
FREEZE = "*,*::before,*::after{animation:none!important;transition:none!important;caret-color:transparent!important}"
def state_for(base, path):
    """The saved session (cookies + localStorage) made valid for this server too: localStorage is per origin (port)."""
    import json, urllib.parse
    st = json.load(open(path)); o = urllib.parse.urlsplit(base); origin = '%s://%s' % (o.scheme, o.netloc)
    if st.get('origins') and not any(x['origin'] == origin for x in st['origins']):
        st['origins'].append(dict(st['origins'][0], origin=origin))
    return st
async def shot(br, base, size, lang, scheme, page, path):
    ctx = await br.new_context(storage_state=state_for(base, STATE), locale=lang, color_scheme=scheme, reduced_motion='reduce', **SIZES[size])
    await ctx.add_init_script("sessionStorage.setItem('sw.modal','1');localStorage.setItem('tj.lang',JSON.stringify('%s'))" % lang[:2])
    pg = await ctx.new_page(); await pg.goto(base + '/' + page, wait_until='networkidle'); await pg.add_style_tag(content=FREEZE)
    await pg.evaluate('document.fonts.ready'); await pg.wait_for_timeout(int(os.environ.get('WAIT', 1200))); await pg.screenshot(path=path); await ctx.close()
async def main():
    os.makedirs(OUT, exist_ok=True); worst = 0
    async with async_playwright() as p:
        br = await p.chromium.launch()
        for size in SIZES:
            for lang, scheme in (('fr-CA', 'dark'), ('es-ES', 'light')):
                for page in PAGES:
                    n = f"{size}-{lang[:2]}-{scheme}-{page[1:]}"; a, b = f"{OUT}/{n}-A.png", f"{OUT}/{n}-B.png"
                    await shot(br, A, size, lang, scheme, page, a); await shot(br, B, size, lang, scheme, page, b)
                    ia, ib = Image.open(a).convert('RGB'), Image.open(b).convert('RGB')
                    if ia.size != ib.size: print(f"{n}: SIZE {ia.size} vs {ib.size}"); continue
                    d = ImageChops.difference(ia, ib).convert('L').point(lambda v: 255 if v > 24 else 0)
                    pct = 100 * sum(1 for v in d.get_flattened_data() if v) / (ia.size[0] * ia.size[1]); worst = max(worst, pct)
                    if pct > 0: d.save(f"{OUT}/{n}-diff.png")
                    print(f"{n:40} {pct:.3f} % pixels differ", flush=True)
        await br.close()
    print('worst', round(worst, 3))
asyncio.run(main())
