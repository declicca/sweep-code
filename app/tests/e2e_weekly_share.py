"""
Sweep — share the week (brief 01 step 5, lot 4), dev environment with Playwright:
  python3 tests/e2e_weekly_share.py http://127.0.0.1:8095
A trader of its own, one known week (Monday 2026-09-28: 4 trades on 3 days, one payout of $1,200 paid), the server's
recap state set to « ready » (the moment is tested in tests/weekly_test.php). On the recap's first screen:
 - « Share my week »: a gray button (« Analyse my week » stays the only primary one);
 - the card (1080×1920 image): the trader's first name, the week, the 5 days' rings, the swept-day streak, the discipline
   score, swept days out of days traded — and no dollar amount by default;
 - « Add my payouts received » (off by default, shown only with payouts that week) adds the payouts to the card;
 - phone: the system share sheet gets the image; computer: the image is downloaded. No page error, no horizontal scroll.
"""
import asyncio, base64, json, os, random, re, struct, sys
from playwright.async_api import async_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
OUT = os.environ.get('TMPDIR', '/tmp')
MON = '2026-09-28'
TRADES = [('2026-09-28', 120000, {'plan': 'y', 'stop': 'n', 'size': 'y'}), ('2026-09-28', 80000, {'plan': 'y', 'stop': 'n', 'size': 'y'}),
          ('2026-09-29', -30000, {'plan': 'y', 'stop': 'y', 'size': 'n'}), ('2026-10-01', 50000, {'plan': 'y', 'stop': 'n', 'size': 'y', 'risk': 'na'})]
SUMMARY = {'days': [{'day': d, 'market': True, 'rings': {'plan': 100, 'execution': 100 if i < 3 else 0, 'review': 100 if i < 2 else 0}, 'swept': i < 2} for i, d in enumerate(['2026-09-28', '2026-09-29', '2026-09-30', '2026-10-01', '2026-10-02'])],
           'swept': 2, 'streak': 3, 'missions': {'done': 1, 'total': 3}}
WANT = {'fr': ['La semaine de Wes', '3 jours d’affilée', '67 %', '2 sur 3 jours tradés'], 'en': ['Wes’s week', '3 days in a row', '67 %', '2 of 3 days traded']}
PAY = {'fr': ('Payouts reçus cette semaine', '1 200 $'), 'en': ('Payouts received this week', '$1,200')}
HOOK = """window.__txt = []; (() => { const f = CanvasRenderingContext2D.prototype.fillText;
  CanvasRenderingContext2D.prototype.fillText = function (t, ...r) { window.__txt.push(String(t)); return f.call(this, t, ...r); }; })();"""
SHARE_MOCK = """navigator.canShare = () => true; navigator.share = async (d) => { const f = d.files[0];
  window.__shared = { name: f.name, type: f.type, data: await new Promise((r) => { const fr = new FileReader(); fr.onload = () => r(fr.result); fr.readAsDataURL(f); }) }; };"""
NO_SHARE = "Object.defineProperty(navigator, 'canShare', { value: undefined, configurable: true });"
fails = 0
def ok(c, what):
    global fails
    print(('ok   ' if c else 'FAIL ') + what); fails += 0 if c else 1
def png_size(raw): return struct.unpack('>II', raw[16:24]) if raw[:8] == b'\x89PNG\r\n\x1a\n' else (0, 0)
sp = lambda s: re.sub(r'[  ]', ' ', s)
# what sticks out on the right (elements clipped by a scrolling row or inside a fixed layer don't count; the app clips
# html / body with overflow-x:clip, so the trader never gets a sideways scroll, but the content is cut)
WIDE = """(()=>{ const W = document.documentElement.clientWidth, out = [];
  const name = (e) => e.tagName.toLowerCase() + '.' + String(e.className).trim().split(/\\s+/).slice(0, 2).join('.');
  const inside = (e) => { for (let x = e; x; x = x.parentElement) { const c = getComputedStyle(x); if (x === document.body) break; if (c.position === 'fixed' || (x !== e && c.overflowX !== 'visible' && x.getBoundingClientRect().right <= W + .5)) return true; } return false; };   // body / html clip the page itself: not a scrolling row
  document.querySelectorAll('body *').forEach((e) => {
    const r = e.getBoundingClientRect(); if (!r.width || inside(e)) return;
    if (r.right > W + .5) out.push(name(e) + ' ' + Math.round(r.right) + 'px');
    for (const ps of ['::before', '::after']) { const c = getComputedStyle(e, ps); if (c.content === 'none' || c.position !== 'absolute') continue;   // a pseudo-element: right edge from its inset
      const rr = parseFloat(c.right); if (!isNaN(rr) && r.right - rr > W + .5) out.push(name(e) + ps + ' ' + Math.round(r.right - rr) + 'px'); }
  });
  const tw = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);   // text running out of its box
  for (let n = tw.nextNode(); n; n = tw.nextNode()) { if (!n.textContent.trim() || inside(n.parentElement)) continue; const g = document.createRange(); g.selectNodeContents(n); const r = g.getBoundingClientRect();
    if (r.right > W + .5) out.push('text « ' + n.textContent.trim().slice(0, 30) + ' » in ' + name(n.parentElement) + ' ' + Math.round(r.right) + 'px'); }
  return { sw: document.documentElement.scrollWidth, w: innerWidth, cw: W, out: out.slice(-8) }; })()"""
async def no_hscroll(pg, what):
    d = await pg.evaluate(WIDE)
    ok(d['sw'] <= d['w'], what + ('' if d['sw'] <= d['w'] else f" — page {d['sw']}px for {d['w']}px (usable {d['cw']}px): {d['out']}"))
async def main():
  async with async_playwright() as p:
    br = await p.chromium.launch()
    for lang, w, h, mob in (('fr', 390, 844, True), ('en', 1300, 850, False)):
      tag = f'{lang} {w}px'
      ctx = await br.new_context(base_url=B, locale=lang, viewport={'width': w, 'height': h}, is_mobile=mob, has_touch=mob, device_scale_factor=2 if mob else 1, accept_downloads=True, bypass_csp=True)
      await ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('%s'));" % lang + HOOK + (SHARE_MOCK if mob else NO_SHARE))
      H = {'X-Requested-With': 'fetch', 'Content-Type': 'application/json'}; n = 'ws%06d' % random.randint(0, 999999)
      r = await ctx.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': n + '@t.dev', 'consent': True, 'elapsed': 6000}), headers=H)
      ok(r.ok, f'{tag} a trader of its own ({r.status})')
      await ctx.request.post(B + '/api/me/profile', data=json.dumps({'first_name': 'Wes', 'last_name': 'Test'}), headers=H)
      async def weekly(route):
        await route.fulfill(status=200, content_type='application/json', body=json.dumps({'open': True, 'week': MON, 'seen': False, 'done': False, 'chest_opened': False,
          'intention': None, 'keys': 0, 'answers': {}, 'summary': SUMMARY, 'reveal': None, 'can_second': False, 'odds': {}}))
      await ctx.route('**/api/game/weekly', weekly)
      shares = []
      async def share_log(route): shares.append(route.request.post_data or ''); await route.continue_()
      await ctx.route('**/api/game/share', share_log)
      pg = await ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:150]))
      await pg.goto(B + '/#dashboard'); await pg.wait_for_timeout(2500)
      await pg.evaluate("""(T) => { put('firms',{id:'f-ws',name:'Topstep'}); put('accounts',{id:'a-ws',firm_id:'f-ws',name:'Combine 50K',starting_balance_c:5000000,status:'active',phase:'eval',money_type:'eval',rules:{dd_c:200000,dd_type:'eod',target_c:300000}});
        T.forEach(([d,c,a],i)=>put('trades',{id:'ws-t'+i,account_id:'a-ws',date:d,session_date:true,entry_time:'10:0'+i+':00',exit_time:'10:3'+i+':00',instrument:'NQ',direction:'long',contracts:1,pnl_c:c,pnl_manual:true,discipline:a}));
        put('payouts',{id:'ws-p1',account_id:'a-ws',firm_id:'f-ws',gross_c:120000,split_pct:100,fees_c:0,net_c:120000,amount_c:120000,status:'paid',payment_date:'2026-09-30',paid_on:'2026-09-30'}); }""", TRADES)
      await pg.wait_for_timeout(1500)
      await pg.evaluate("SweepGame.open('weekly')"); await pg.wait_for_selector('#gSheet .wk-share', timeout=10000); await pg.wait_for_timeout(500)
      btn = await pg.evaluate("(()=>{const b=document.querySelector('#gSheet .wk-sh'); return b?{t:b.innerText.trim(), prim:b.classList.contains('primary'), n:document.querySelectorAll('#gSheet .wk-body .btn.primary').length}:null})()")
      ok(btn is not None and btn['t'] == ('Partager ma semaine' if lang == 'fr' else 'Share my week') and not btn['prim'] and btn['n'] == 1,
         f'{tag} « {btn and btn["t"]} »: a gray button, one primary button on the screen ({btn})')
      sw = await pg.evaluate("(()=>{const i=document.querySelector('#gSheet [data-wk-pay]'); return i?{on:i.checked, l:i.closest('.wk-sh-pay').innerText.replace(/\\s+/g,' ').trim()}:null})()")
      ok(sw is not None and sw['on'] is False and ('Ajouter mes payouts reçus' if lang == 'fr' else 'Add my payouts received') in sw['l'], f'{tag} « add my payouts »: shown (payouts this week), off by default ({sw})')
      await no_hscroll(pg, f'{tag} no horizontal scroll, recap open')
      vis = await pg.evaluate("(()=>{const b=document.querySelector('#gSheet .wk-sh').getBoundingClientRect(); return b.width>0 && b.right<=innerWidth})()")
      ok(vis, f'{tag} the button fits the screen')
      async def make():
        await pg.evaluate("window.__txt = []; window.__shared = null")
        if mob:
          await pg.click('#gSheet .wk-sh'); await pg.wait_for_function("window.__shared", timeout=10000)
          d = await pg.evaluate("window.__shared"); raw = base64.b64decode(d['data'].split(',', 1)[1]); name = d['name']
        else:
          async with pg.expect_download(timeout=10000) as dl: await pg.click('#gSheet .wk-sh')
          d = await dl.value; path = await d.path(); raw = open(path, 'rb').read(); name = d.suggested_filename
        return raw, name, [sp(x) for x in await pg.evaluate("window.__txt")]
      raw, name, txt = await make()
      open(os.path.join(OUT, f'week-card-{lang}.png'), 'wb').write(raw)
      ok(png_size(raw) == (1080, 1920) and name == 'sweep-week.png', f'{tag} the card: a 1080×1920 image « {name} » ({"share sheet" if mob else "download"})')
      miss = [x for x in WANT[lang] if not any(x in t for t in txt)]
      ok(not miss, f'{tag} first name, streak, discipline, swept days of days traded on the card' + (f' — missing {miss} in {txt}' if miss else ''))
      ok(not [t for t in txt if '$' in t], f'{tag} no dollar amount on the card by default ({[t for t in txt if "$" in t]})')
      await pg.click('#gSheet .wk-sh-pay label.sw'); await pg.wait_for_timeout(200)
      ok(await pg.evaluate("document.querySelector('#gSheet [data-wk-pay]').checked"), f'{tag} « add my payouts »: on')
      raw2, _, txt2 = await make()
      open(os.path.join(OUT, f'week-card-{lang}-pay.png'), 'wb').write(raw2)
      ok(any(PAY[lang][0] in t for t in txt2) and any(t.strip() == PAY[lang][1] for t in txt2), f'{tag} with the payouts: « {PAY[lang][0]} · {PAY[lang][1]} » on the card')
      ok(len([t for t in txt2 if '$' in t]) == 1, f'{tag} the payouts are the only amount ({[t for t in txt2 if "$" in t]})')
      ok(any('"week"' in x for x in shares), f'{tag} the share is counted (api/game/share, kind week)')
      await no_hscroll(pg, f'{tag} no horizontal scroll, after sharing')
      ok(not errs, f'{tag} no page error' + ('' if not errs else ': ' + ' | '.join(errs[:2])))
      await pg.screenshot(path=os.path.join(OUT, f'week-share-{lang}-{w}.png'))
      await ctx.close()
    await br.close()
    print('all passed' if not fails else f'{fails} failed'); sys.exit(1 if fails else 0)
asyncio.run(main())
