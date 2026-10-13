"""
Sweep — Alpha Futures in the catalogue (13 Oct.), Playwright:
  python3 tests/e2e_alpha_rules.py http://127.0.0.1:8095 /tmp/show_state.json
The rules of every Alpha account (SweepPresets.rulesOf) against a table copied by hand from the official pages
(alpha-futures.com and help.alpha-futures.com « Payout Policy », read on 2026-10-13) — never from the catalogue itself:
 - Zero, Standard, Advanced, Direct: max loss (end of day, stopped at the start), daily loss guard, consistency, days, target;
 - payouts: 5 winning days of $200 (not Direct), minimum per request ($200 / $500 / $1,000 / $500), cap per size, at most
   50 % of the profit per request, 90 % split, and NO limit on the number of payouts (« up to 4 times a month » was read as
   4 payouts in all by the weekly check of 12 Oct.);
 - Direct: a withdrawal target, $1,500 before the first payout on the 25K, then $1,000 since the last one;
 - no « profitable since the last payout » (between two requests: 5 new winning days, or the Direct target; added by the
   check of 13 Oct. after the update, removed the same day).
Then an Alpha Direct 25K account: $1,200 of profit → not ready (« Profit before the first payout » 1 200 $ / 1 500 $);
$1,600 → ready, up to $800 (50 %); after a payout, the next target is $1,000 since that payout. The firm picker's summary
says the targets, and no Alpha account says « up to N payouts ».
"""
import asyncio, json, re, sys
from playwright.async_api import async_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
fails = 0
def ok(c, what):
    global fails
    print(('ok   ' if c else 'FAIL ') + what); fails += 0 if c else 1
# size: (target, max loss, daily loss guard eval, daily loss guard funded, consistency eval, consistency funded, min days, max payout)
OFF = {
  'zero': {'min': 200, 'win': True, 'sizes': {25000: (1500, 1000, 500, 500, None, 40, 1, 1000), 50000: (3000, 2000, 1000, 1000, None, 40, 1, 1500), 100000: (6000, 3000, 2000, 2000, None, 40, 1, 2500)}},
  'standard': {'min': 500, 'win': True, 'sizes': {50000: (3000, 2000, None, 1000, 50, 40, 2, 3000), 100000: (6000, 3000, None, 2000, 50, 40, 2, 4000), 150000: (9000, 4500, None, 3000, 50, 40, 2, 5000)}},
  'advanced': {'min': 1000, 'win': True, 'sizes': {50000: (4000, 1750, None, None, 40, None, 3, 15000), 100000: (8000, 3500, None, None, 40, None, 3, 15000), 150000: (12000, 5250, None, None, 40, None, 3, 15000)}},
  'direct': {'min': 500, 'win': False, 'sizes': {25000: (None, 1000, None, 500, None, 20, None, 1000), 50000: (None, 2000, None, 1000, None, 20, None, 2000), 100000: (None, 3000, None, 2000, None, 20, None, 2500), 150000: (None, 4500, None, 3000, None, 20, None, 3000)}},
}
TARGETS = {25000: (1500, 1000), 50000: (3000, 2000), 100000: (6000, 4000), 150000: (9000, 6000)}   # Direct: first withdrawal, then each next one
c = lambda v: None if v is None else v * 100
async def main():
  async with async_playwright() as p:
    br = await p.chromium.launch()
    ctx = await br.new_context(storage_state=STATE, locale='fr-CA', viewport={'width': 1300, 'height': 900}, bypass_csp=True)
    await ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'))")
    pg = await ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
    await pg.goto(B + '/#dashboard'); await pg.wait_for_function("!!window.SweepPresets", timeout=15000)
    await pg.evaluate("SweepPresets.load()"); await pg.wait_for_function("SweepPresets.ready()", timeout=15000)
    n = 0
    for pid, prog in OFF.items():
      for size, (tgt, dd, dll_e, dll_f, cons_e, cons_f, days, mx) in prog['sizes'].items():
        for phase in (('funded',) if pid == 'direct' else ('eval', 'funded')):
          got = await pg.evaluate("(v) => { const r = SweepPresets.rulesOf(v); return r && r.rules; }", f'alpha|{pid}|{size}|{phase}')
          tag = f'Alpha {pid} {size // 1000}K {phase}'
          if not got: ok(False, f'{tag}: in the catalogue'); continue
          n += 1
          want = {'dd_c': c(dd), 'dd_type': 'eod', 'dd_lock': True, 'dll_c': c(dll_e if phase == 'eval' else dll_f), 'consistency_pct': cons_e if phase == 'eval' else cons_f}
          if phase == 'eval': want.update({'target_c': c(tgt), 'min_days': days})
          else:
            f1, nx = TARGETS[size] if pid == 'direct' else (None, None)
            want.update({'payout_min_c': c(prog['min']), 'payout_max_c': c(mx), 'payout_max_pct': 50, 'payout_split_pct': 90, 'payout_max_n': None,
                         'payout_win_days': 5 if prog['win'] else None, 'payout_win_min_c': c(200) if prog['win'] else None, 'payout_first_min_c': c(f1), 'payout_cycle_min_c': c(nx), 'payout_cycle_pos': None})
          bad = {k: (v, got.get(k)) for k, v in want.items() if got.get(k) != v}
          ok(not bad, f'{tag}: as on the official pages' + (f' — {bad}' if bad else ''))
    ok(n == 22, f'{n} Alpha accounts checked (4 types, 13 sizes, evaluation and funded)')
    # an Alpha Direct 25K: the first withdrawal target, then the next one
    ru = await pg.evaluate("SweepPresets.rulesOf('alpha|direct|25000|funded').rules")
    await pg.evaluate("""(ru) => { put('firms', {id:'al-f', name:'Alpha Futures'}); put('accounts', {id:'al-d', firm_id:'al-f', name:'Alpha Direct 25K', starting_balance_c:2500000, status:'active', phase:'funded', money_type:'funded', preset:'alpha|direct|25000|funded', rules: ru}); }""", ru)
    days = ['2026-09-21', '2026-09-22', '2026-09-23', '2026-09-24', '2026-09-25', '2026-09-28']
    for i, d in enumerate(days):
      await pg.evaluate(f"put('trades', {{id:'al-t{i}', account_id:'al-d', instrument:'NQ', direction:'long', contracts:1, pnl_c:20000, pnl_manual:true, fees_c:0, date:'{d}', entry_time:'10:00', exit_time:'10:05', session_date:true}})")
    await pg.wait_for_timeout(1200)
    st = await pg.evaluate("(() => { const s = SweepPayout.status(getDoc('accounts', 'al-d')); return { ready: s.ready, avail: s.avail, conds: s.conds.map((x) => [x.k, x.ok, x.have]) }; })()")
    fm = next((x for x in st['conds'] if x[0] == 'fmin'), None)
    ok(not st['ready'] and fm and not fm[1] and '1 200' in fm[2].replace(' ', ' ').replace('\xa0', ' ') and '1 500' in fm[2].replace(' ', ' ').replace('\xa0', ' '), f'$1,200 of profit: not ready, the first target is missing ({fm})')
    for i, d in enumerate(['2026-09-29', '2026-09-30']):
      await pg.evaluate(f"put('trades', {{id:'al-u{i}', account_id:'al-d', instrument:'NQ', direction:'long', contracts:1, pnl_c:20000, pnl_manual:true, fees_c:0, date:'{d}', entry_time:'10:00', exit_time:'10:05', session_date:true}})")
    await pg.wait_for_timeout(1200)
    st = await pg.evaluate("(() => { const s = SweepPayout.status(getDoc('accounts', 'al-d')); return { ready: s.ready, avail: s.avail, conds: s.conds.map((x) => [x.k, x.ok, x.have]) }; })()")
    ok(st['ready'] and st['avail'] == 80000, f"$1,600 of profit: ready, up to $800 (50 % of the profit) ({st['ready']}, {st['avail']}, {st['conds']})")
    await pg.evaluate("put('payouts', {id:'al-p1', account_id:'al-d', amount_c:80000, status:'paid', request_date:'2026-09-30', approval_date:'2026-10-01', payment_date:'2026-10-01'})"); await pg.wait_for_timeout(1000)
    st = await pg.evaluate("(() => { const s = SweepPayout.status(getDoc('accounts', 'al-d')); return { ready: s.ready, conds: s.conds.map((x) => [x.k, x.ok, x.have]) }; })()")
    keys = [x[0] for x in st['conds']]; cm = next((x for x in st['conds'] if x[0] == 'cmin'), None)
    ok('fmin' not in keys and cm and not cm[1] and '1 000' in cm[2].replace(' ', ' ').replace('\xa0', ' ') and not st['ready'], f'after a payout: the next target is $1,000 since that payout ({cm})')
    # the firm picker says the targets; no Alpha account says « up to N payouts »
    await pg.evaluate("editDoc('accounts', 'al-d', (d) => { d.status = 'archived'; })")
    await pg.evaluate("location.hash='#accounts'"); await pg.wait_for_timeout(1200)
    await pg.locator('#main [data-act=acct-add]').last.click(); await pg.wait_for_timeout(600)
    await pg.locator('[data-st-ph0=funded]').first.click(); await pg.wait_for_timeout(250)
    await pg.locator('[data-st-firm=alpha]').first.click(); await pg.wait_for_timeout(250)
    await pg.locator('[data-st-type=direct]').first.click(); await pg.wait_for_timeout(250)
    await pg.locator('[data-st-size="25000"]').first.click(); await pg.wait_for_timeout(400)
    summ = (await pg.locator('form[data-form=account] .ux-st-sum').text_content()).replace(' ', ' ').replace('\xa0', ' ')   # « See all the rules » included
    ok('1 500 $ de profit avant le 1er' in summ and 'puis 1 000 $ avant chaque suivant' in summ, f'Direct 25K summary: the withdrawal targets ({" ".join(summ.split())[:200]})')
    ok(not re.search(r'jusqu.à \d+ payouts', summ), 'Direct 25K summary: no « jusqu’à N payouts »')
    ok(not errs, 'no page error' + ('' if not errs else ': ' + ' | '.join(errs[:2])))
    await br.close()
    print('all passed' if not fails else f'{fails} failed'); sys.exit(1 if fails else 0)
asyncio.run(main())
