"""
Sweep — E20 · no English left in French and Spanish (sample account, phone and computer):
  python3 tests/e2e_no_english_in_fr_es.py http://127.0.0.1:8095 /tmp/show_state.json
The 15 main pages of a trader (brief 02 part 7) and their views: Today, Trades and a trade (its « ⋯ » menu and copy panel),
Stats and its News tab, Accounts and an account, My money, Calendar, Journal (today, a day with more trades than its
maximum, the week), News (today, the week), Settings, Progression, Plan, Import, Referral, Feedback.
English = the app's phrases known to slip through, and English words that exist in neither French nor Spanish. The trader's
own words stay as typed (setup names, notes, the sample accounts' names), the platforms' menus on Import too.
Administration (Mateo only) is not checked. Fails on the first English text found (« FAIL »), lists them all.
"""
import asyncio, re, sys
from playwright.async_api import async_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
PHRASES = (r"Not enough data|See all|Add a trade|Your routine|Trades in your plan|Win rate|No trade|Net P&L|Payouts received|Share my|What to watch|Quick access|Settings|"
           r"Search trades|This week|This month|Copy to|Copy this trade|Same prices|stay in sync|already on every|Delete all|Delete this copy|Share trade card|Edit trade|"
           # brief 02 part 7
           r"Exceeded|Max trades|Entered without confirmation|Broke daily loss limit|None recorded|Show all accounts|Filtered to|Previously reported|In line|older trades|no news data|"
           r"Fed presser|FOMC minutes|Unemployment|ISM Mfg|ISM Svc|Retail Sales|Retail|Nonfarm Payrolls|Rate Decision|Press Conference|Meeting Minutes|Jobless Claims|Consumer Confidence|"
           r"Hourly Earnings|Job Openings|Price Index|est\. date|tent\.|High impact|Medium impact|Awaiting|Above forecast|Below forecast|Previous|Forecast")   # (« actual » is Spanish too)
WORDS = r"the|your|you|with|without|this|these|those|have|been|were|will|would|should|could|which|what|why|already|never|always|none"
EN = re.compile(r"(?<![\w’'-])(" + PHRASES + r"|" + WORDS + r")(?![\w’'-])", re.I)
PLATFORM_MENUS = re.compile(r"Account Reports|Completed Orders|Export data|Order History|Qty Filled|Avg Fill Price|Update Time|Buy/Sell")   # Import: the platforms' own (English) menus
PAGES = ['#dashboard', '#trades', 'TRADE', '#analytics', '#analytics/news', '#accounts', 'ACCOUNT', '#payouts', '#calendar', '#journal', 'DAY', '#journal/weekly',
         '#news', '#news/week', '#settings', '#progress', '#plan', '#import', '#referral', '#feedback']
TEXT = """(() => {   // the page's text, without the trader's own words (setups, notes, account names: data, not the app)
  const root = document.querySelector('.main-wrap') || document.body; const c = root.cloneNode(true);
  const own = new Set([...(S.trades || []).flatMap((t) => [t.setup, t.notes]), ...(S.accounts || []).flatMap((a) => [a.name, a.notes]), ...(S.trades || []).flatMap((t) => [t.strategy])].filter(Boolean));
  const walk = document.createTreeWalker(c, NodeFilter.SHOW_TEXT); const out = [];
  while (walk.nextNode()) { let v = walk.currentNode.textContent; for (const o of own) if (o && v.includes(o)) v = v.split(o).join(' '); out.push(v); }
  return out.join('\\n');
})()"""

async def main():
  async with async_playwright() as p:
    br = await p.chromium.launch(); bad = []
    for lang in ['fr', 'es']:
      for kw in [p.devices['iPhone 13'], {'viewport': {'width': 1440, 'height': 900}}]:
        ctx = await br.new_context(**kw, storage_state=STATE); pg = await ctx.new_page()
        await pg.add_init_script(f"sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('{lang}'))")
        await pg.goto(B + '/?x=1#dashboard'); await pg.wait_for_timeout(2500)
        ids = await pg.evaluate("""({ acc: (S.accounts.find((a) => a.status !== 'archived') || {}).id, tr: ((S.trades.find((t) => !t.demo) || S.trades[0]) || {}).id,
          day: (() => { const by = {}; S.trades.forEach((t) => { by[t.date] = (by[t.date] || 0) + 1; }); return Object.keys(by).sort().reverse().find((d) => by[d] > 3) || ''; })() })""")
        for h in PAGES:
          url = {'ACCOUNT': '#account/%s' % ids['acc'], 'TRADE': '#trade/%s' % ids['tr'], 'DAY': '#journal/%s' % ids['day']}.get(h, h)
          await pg.goto(B + '/?x=1' + url); await pg.wait_for_timeout(1800)
          await pg.evaluate("document.querySelectorAll('#main details:not([open])').forEach((d) => { d.open = true; })"); await pg.wait_for_timeout(400)
          if h == '#news/week':   # a release's panel too (« impact », « In line », the dates)
            evs = pg.locator('#main [data-act=ev-open]')
            for k in range(min(2, await evs.count())):
              await evs.nth(k).evaluate('b => b.click()'); await pg.wait_for_timeout(900)
              t2 = await pg.evaluate("(document.getElementById('evPanel') || {}).innerText || ''")
              for line in t2.split('\n'):
                for m in EN.finditer(line): bad.append(f"{lang} {'390' if kw.get('is_mobile') else '1440'} {h} (a release's panel): « {m.group(1)} » in « {line.strip()[:90]} »")
              await pg.keyboard.press('Escape'); await pg.wait_for_timeout(300)
          if h == 'TRADE':
            if await pg.locator('#main [data-act=copy-open]').count(): await pg.locator('#main [data-act=copy-open]').first.evaluate('b => b.click()'); await pg.wait_for_timeout(500)
          txt = await pg.evaluate(TEXT)
          if h == '#import': txt = PLATFORM_MENUS.sub(' ', txt)
          for line in txt.split('\n'):
            for m in EN.finditer(line):
              bad.append(f"{lang} {'390' if kw.get('is_mobile') else '1440'} {h}: « {m.group(1)} » in « {line.strip()[:90]} »")
        await ctx.close()
    await br.close()
    bad = sorted(set(bad))
    for b in bad[:40]: print('FAIL', b)
    print('English left:', len(bad))
    print('all passed' if not bad else f'{len(bad)} failed')
    sys.exit(1 if bad else 0)
asyncio.run(main())
