"""
Sweep — the discipline checklist on the manual trade form (brief 02, part 1, improvement 1), dev environment with Playwright:
  python3 tests/e2e_trade_checklist.py http://127.0.0.1:8095
A trader of its own with two accounts. On the form, right above « Save »: 3 questions, « See more » for the rest. The
trader answers, presses « Save » before typing the entry price (refused: « Add the entry price »), waits, types it and saves:
 - the answers are in the trade from the moment it is saved (and in its copy on the other account): never lost after a
   refused save, the discipline score is never empty when the trader answered;
 - « Step 2 » shows them at once; FR phone and EN computer, no page error.
"""
import asyncio, json, random, sys
from playwright.async_api import async_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
W = {'fr': {'yes': 'Oui', 'no': 'Non', 'na': 'N/A', 'more': 'Voir plus'}, 'en': {'yes': 'Yes', 'no': 'No', 'na': 'N/A', 'more': 'See more'}}
fails = 0
def ok(c, what):
    global fails
    print(('ok   ' if c else 'FAIL ') + what); fails += 0 if c else 1
async def main():
  async with async_playwright() as p:
    br = await p.chromium.launch()
    for lang, w, h, mob in (('fr', 390, 844, True), ('en', 1300, 850, False)):
      tag = f'{lang} {w}px'; x = W[lang]
      ctx = await br.new_context(base_url=B, locale=lang, viewport={'width': w, 'height': h}, is_mobile=mob, has_touch=mob, device_scale_factor=2 if mob else 1)
      await ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('%s'))" % lang)
      H = {'X-Requested-With': 'fetch', 'Content-Type': 'application/json'}
      r = await ctx.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': 'tc%06d@t.dev' % random.randint(0, 999999), 'consent': True, 'elapsed': 6000}), headers=H)
      ok(r.ok, f'{tag} a trader of its own ({r.status})')
      await ctx.request.post(B + '/api/me/profile', data=json.dumps({'first_name': 'Cora', 'last_name': 'Test'}), headers=H)
      pg = await ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:150]))
      await pg.goto(B + '/#trades'); await pg.wait_for_timeout(2500)
      await pg.evaluate("""() => { put('accounts', {id:'tc-a', name:'Main 50K', status:'active', phase:'live', money_type:'live', starting_balance_c:5000000, rules:{}});
        put('accounts', {id:'tc-b', name:'Copy 50K', status:'active', phase:'live', money_type:'live', starting_balance_c:5000000, rules:{}}); }""")
      await pg.wait_for_timeout(800)
      qs = await pg.evaluate("S.settings.questions.filter(q => q.active !== false).map(q => q.id)")
      await pg.evaluate("openTicket(null,{manual:true})"); await pg.wait_for_selector('#tkSlide.open .nav-ck', timeout=8000); await pg.wait_for_timeout(500)
      vis = await pg.evaluate("[...document.querySelectorAll('#tkSlide .nav-ck-q')].filter(q => q.offsetParent).map(q => q.dataset.q)")
      before = await pg.evaluate("(()=>{const c=document.querySelector('#tkSlide .nav-ck'), s=document.querySelector('#tkSlide [data-act=\"tk-save\"]'); return !!(c && s && (c.compareDocumentPosition(s) & Node.DOCUMENT_POSITION_FOLLOWING))})()")
      ok(len(vis) == 3 and before, f'{tag} 3 questions shown, right above « Save » ({vis})')
      async def answer(q, word):
        await pg.locator(f'#tkSlide .nav-ck-q[data-q="{q}"] .nav-ck-b button', has_text=word).first.click()
      await answer(vis[0], x['yes']); await answer(vis[1], x['no'])
      await pg.locator('#tkSlide .nav-ck-more', has_text=x['more']).click(); await pg.wait_for_timeout(200)
      allq = await pg.evaluate("[...document.querySelectorAll('#tkSlide .nav-ck-q')].filter(q => q.offsetParent).map(q => q.dataset.q)")
      ok(len(allq) == len(qs) and len(qs) > 3, f'{tag} « {x["more"]} »: every active question ({len(allq)} of {len(qs)})')
      await answer(allq[3], x['na'])
      await pg.evaluate("() => { TK.account = 'tc-a'; TK.inst = 'NQ'; TK.dir = 'long'; TK.qty = 1; TK.entry = ''; TK.exit = ''; TK.copyTo = new Set(['tc-b']); tkRefresh(); }")
      await pg.locator('#tkSlide [data-act="tk-save"]').click(); await pg.wait_for_timeout(1500)   # refused, and longer than the old 900 ms
      err = await pg.evaluate("(document.querySelector('#tkErr')||{}).innerText||''")
      ok(err.strip() != '' and await pg.evaluate("S.trades.filter(t=>!t.demo).length") == 0, f'{tag} saved without an entry price: refused ({err.strip()[:50]})')
      n0 = await pg.evaluate("S.trades.length")
      await pg.evaluate("() => { TK.entry = 21000; TK.exit = 21006; tkRefresh(); }")
      await pg.locator('#tkSlide [data-act="tk-save"]').click()
      await pg.wait_for_function(f"S.trades.length >= {n0} + 2", timeout=10000)
      got = await pg.evaluate("S.trades.filter(t=>!t.demo).map(t => ({acc: t.account_id, d: t.discipline || {}, score: tDisc(t)}))")
      want = {vis[0]: 'y', vis[1]: 'n', allq[3]: 'na'}
      ok(len(got) == 2 and all(all(g['d'].get(k) == v for k, v in want.items()) for g in got), f'{tag} the answers are in the trade and its copy as soon as they are saved ({[g["d"] for g in got]})')
      ok(all(g['score'] is not None for g in got), f'{tag} the discipline score is not empty ({[g["score"] for g in got]})')
      await pg.wait_for_timeout(600)
      s2 = await pg.evaluate("(()=>{const s=document.querySelector('#tkSlide .score b'); return s ? s.textContent.trim() : null})()")
      ok(s2 not in (None, '—') and s2.endswith('%'), f'{tag} « Step 2 » shows the score at once ({s2})')
      ok(not errs, f'{tag} no page error' + ('' if not errs else ': ' + ' | '.join(errs[:2])))
      await ctx.close()
    await br.close()
    print('all passed' if not fails else f'{fails} failed'); sys.exit(1 if fails else 0)
asyncio.run(main())
