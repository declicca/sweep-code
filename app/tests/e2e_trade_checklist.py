"""
Sweep — the discipline checklist on the manual trade form (brief 02, part 1, improvement 1), dev environment with Playwright:
  python3 tests/e2e_trade_checklist.py http://127.0.0.1:8095
A trader of its own with two accounts. On the form, right above « Save »: 3 questions, « See more » for the rest. The
trader answers, presses « Save » before typing the entry price (refused: « Add the entry price »), waits, types it and saves:
 - the answers are in the trade from the moment it is saved (and in its copy on the other account): never lost after a
   refused save, the discipline score is never empty when the trader answered;
 - « Step 2 » shows them at once; FR phone and EN computer, no page error;
 - questions that adapt (brief edge T7, computed, never saved): the question answered « yes » on the winners and « no » on
   the losers comes first with « This question separates your winners from your losers »; one always « yes » on the last 4
   weeks goes under « See more », marked « acquired »; « Opening range breakout » picked: its own entry criterion replaces
   the 3 questions (manual form and quick sheet) and its answer goes into the trade's discipline; Settings › Setups saves
   a criterion typed (the others keep their id, so their answers stay theirs).
"""
import asyncio, json, random, sys
from playwright.async_api import async_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
AC = {'fr': 'acquise', 'en': 'acquired'}
W = {'fr': {'yes': 'Oui', 'no': 'Non', 'na': 'N/A', 'more': 'Voir plus'}, 'en': {'yes': 'Yes', 'no': 'No', 'na': 'N/A', 'more': 'See more'}}
fails = 0
async def shot(pg):   # « New trade » shows its fields once a screenshot is there (18 Oct.): the test one, read as no table
    await pg.route('**/api/ai/import', lambda r: r.fulfill(status=200, content_type='application/json', body='{"trades": []}'))
    await pg.locator('.nav-am.open input[data-am-file]').first.set_input_files('tests/fixture-shot.png')
    await pg.wait_for_selector('.nav-am.open .nav-am-grid', timeout=8000); await pg.wait_for_timeout(300)
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
      # Edge T7: the questions adapt (computed, never saved)
      await pg.evaluate("document.querySelector('#tkSlide [data-act=\"s2-close\"]') && document.querySelector('#tkSlide [data-act=\"s2-close\"]').click()"); await pg.wait_for_timeout(500)
      sep, acq = allq[4], allq[2]
      await pg.evaluate("""([sep, acq]) => { const back = (k) => { const d = new Date(todayStr() + 'T12:00:00Z'); d.setUTCDate(d.getUTCDate() - k); return d.toISOString().slice(0, 10); };
        [8, 9, 10, 11, 12, 14, 15, 16, 17, 18, 19, 21].forEach((k, i) => put('trades', { id: 'q' + k, account_id: 'tc-a', instrument: 'NQ', direction: 'long', contracts: 1, entry: 1, exit: 2, pnl_c: i % 2 ? 20000 : -15000, pnl_manual: true, date: back(k), entry_time: '10:00:00', discipline: { [sep]: i % 2 ? 'y' : 'n', [acq]: 'y' } }));
        editDoc('settings', 'settings', (d) => { d.setups = ['Opening range breakout']; d.setup_rules = { 'Opening range breakout': [{ id: 'sr_t1', text: 'Range break' }] }; }); }""", [sep, acq])
      await pg.wait_for_timeout(1200)
      await pg.evaluate("openTicket(null,{manual:true})"); await pg.wait_for_selector('#tkSlide.open .nav-ck', timeout=8000); await pg.wait_for_timeout(500)
      v2 = await pg.evaluate("[...document.querySelectorAll('#tkSlide .nav-ck-q')].filter(q => q.offsetParent).map(q => [q.dataset.q, !!q.querySelector('.nav-q-sep')])")
      lab = await pg.evaluate("(q) => (document.querySelector(`#tkSlide .nav-ck-q[data-q=\"${q}\"] .nav-q-acq`) || {}).textContent || ''", acq)
      ok(v2 and v2[0] == [sep, True] and acq not in [q for q, _ in v2] and AC[lang] in lab, f'{tag} T7 the question that separates winners from losers first, with its mention; the acquired one under « {x["more"]} », marked ({v2}, {lab!r})')
      await pg.locator('#tkSlide [data-sp="Opening range breakout"]').click(); await pg.wait_for_timeout(400)
      v3 = await pg.evaluate("[...document.querySelectorAll('#tkSlide .nav-ck-q')].filter(q => q.offsetParent).map(q => q.dataset.q)")
      ok(v3 == ['sr_t1'], f'{tag} T7 the setup picked: its criterion replaces the 3 questions ({v3})')
      await answer('sr_t1', x['yes'])
      n1 = await pg.evaluate("S.trades.length")
      await pg.evaluate("() => { TK.account = 'tc-a'; TK.inst = 'NQ'; TK.dir = 'long'; TK.qty = 1; TK.entry = 21000; TK.exit = 21004; TK.copyTo = new Set(); tkRefresh(); }")
      await pg.locator('#tkSlide [data-act="tk-save"]').click(); await pg.wait_for_function(f"S.trades.length >= {n1} + 1", timeout=10000)
      t7 = await pg.evaluate("(()=>{const t=S.trades[S.trades.length-1]; return [t.setup, (t.discipline||{}).sr_t1]})()")
      ok(t7 == ['Opening range breakout', 'y'], f'{tag} T7 the criterion answered goes into discipline, with the setup ({t7})')
      await pg.evaluate("document.querySelector('#tkSlide [data-act=\"s2-close\"]') && document.querySelector('#tkSlide [data-act=\"s2-close\"]').click()"); await pg.wait_for_timeout(500)
      await pg.evaluate("editDoc('settings','settings', d => { d.add_mode_pref = 'shot'; })"); await pg.wait_for_timeout(400)
      await pg.evaluate("openTicket(null)"); await pg.wait_for_selector('.nav-am.open', timeout=8000); await shot(pg); await pg.wait_for_selector('.nav-am.open .nav-sp', timeout=8000); await pg.wait_for_timeout(400)
      await pg.locator('.nav-am [data-sp="Opening range breakout"]').click(); await pg.wait_for_timeout(400)
      v4 = await pg.evaluate("[...document.querySelectorAll('.nav-am .nav-am-q > span')].map(s => s.textContent)")
      ok(v4 == ['Range break'], f'{tag} T7 the quick sheet: the same criterion in place of the questions ({v4})')
      ok(await pg.evaluate("document.documentElement.scrollWidth - innerWidth") <= 0, f'{tag} T7 nothing wider than the window')
      if mob: await pg.screenshot(path='/tmp/tc_t7_quick.png')
      await pg.evaluate("document.querySelector('.nav-am [data-am=close]').click()"); await pg.wait_for_timeout(400)
      await pg.evaluate("location.hash = '#settings'"); await pg.wait_for_selector('#main .nav-sr', state='attached', timeout=8000); await pg.wait_for_timeout(400)
      await pg.evaluate("(() => { const i = document.querySelector('#main input[data-sr=\"Opening range breakout\"][data-i=\"1\"]'); i.value = 'Volume above average'; i.dispatchEvent(new Event('change', { bubbles: true })); })()"); await pg.wait_for_timeout(900)
      sr = await pg.evaluate("((S.settings.setup_rules || {})['Opening range breakout'] || []).map(c => [c.id, c.text])")
      ok(len(sr) == 2 and sr[0] == ['sr_t1', 'Range break'] and sr[1][1] == 'Volume above average' and sr[1][0].startswith('sr_'), f'{tag} T7 Settings › Setups: a 2nd criterion typed is saved, the 1st keeps its id ({sr})')
      ok(not errs, f'{tag} no page error' + ('' if not errs else ': ' + ' | '.join(errs[:2])))
      await ctx.close()
    await br.close()
    print('all passed' if not fails else f'{fails} failed'); sys.exit(1 if fails else 0)
asyncio.run(main())
