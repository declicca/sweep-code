"""Number formats in FR / ES: every visible text with « 79% » (no space before %) or a decimal point (« 1.71 », « 1.2k »), grouped by place.
   python3 tools/numfmt.py [base_url] [state_file]"""
import asyncio, collections, json, sys, urllib.parse
from playwright.async_api import async_playwright
BASE = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'; STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
PAGES = ['#dashboard', '#trades', '#calendar', '#journal', '#analytics', '#accounts', '#payouts', '#settings', '#plan']
JS = r"""() => { const out = []; const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  while (w.nextNode()) { const n = w.currentNode, t = n.nodeValue; const el = n.parentElement;
    if (!el || !el.getClientRects().length || el.closest('script,style,[hidden]')) continue;
    if (/\d%|\d\.\d{1,2}(?!\d)|\d\.\dk/.test(t)) { const sel = el.tagName.toLowerCase() + (el.className && typeof el.className === 'string' ? '.' + el.className.trim().split(/\s+/).slice(0, 2).join('.') : '');
      const p = el.closest('[class]'); out.push([t.trim().slice(0, 50), sel, (el.closest('section, .surface, table, aside') || el).className.toString().split(' ').slice(0, 2).join('.')]); } }
  return out; }"""
async def main():
    async with async_playwright() as p:
        br = await p.chromium.launch(); res = collections.defaultdict(set)
        st = json.load(open(STATE)); o = urllib.parse.urlsplit(BASE); org = '%s://%s' % (o.scheme, o.netloc)
        if not any(x['origin'] == org for x in st['origins']): st['origins'].append(dict(st['origins'][0], origin=org))
        for lang in ('fr', 'es'):
            for size in ({'viewport': {'width': 1300, 'height': 850}}, {'viewport': {'width': 390, 'height': 844}, 'is_mobile': True, 'has_touch': True}):
                ctx = await br.new_context(storage_state=st, locale=lang, **size)
                await ctx.add_init_script("sessionStorage.setItem('sw.modal','1');localStorage.setItem('tj.lang',JSON.stringify('%s'))" % lang)
                pg = await ctx.new_page()
                for h in PAGES:
                    await pg.goto(BASE + '/' + h); await pg.wait_for_load_state('networkidle'); await pg.wait_for_timeout(800)
                    for t, sel, sec in await pg.evaluate(JS): res[(t, sel, sec)].add(lang + ' ' + h)
                await ctx.close()
        import re
        grp = collections.defaultdict(lambda: [set(), set()])
        for (t, sel, sec), where in res.items():
            kind = ('%' if re.search(r'\d%', t) else '') + ('.' if re.search(r'\d\.\d{1,2}(?!\d)', t) else '')
            g = grp[(kind, sel, sec)]; g[0].add(t); g[1].update(where)
        for (kind, sel, sec), (ts, where) in sorted(grp.items()): print(f"{kind:3} {sel:30} {sec:24} {' | '.join(sorted(ts))[:90]:90} {' '.join(sorted({w.split()[1] for w in where}))}")
        await br.close()
asyncio.run(main())
