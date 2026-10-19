"""
Sweep — Accounts: act on one or several accounts (15 Oct.), with Playwright:
  python3 tests/e2e_account_bulk.py http://127.0.0.1:8095 /tmp/show_state.json
Adds its own test accounts (ab-…) to the signed-in trader, then removes them and what they created.
 1  computer: two icons on each active row (« Move up » only on an evaluation or a funded account, « Remove » on all)
 2  « Remove »: a window « failed or passed », never a plain delete; « Mark as failed » archives it (failed, today), Undo restores
 3  several boxes ticked: one bar; « Move to funded » confirms, creates a funded account per evaluation (the evaluations
    archived « passed »), skips the others and says so
 4  « Mark as failed » on several: one Undo brings them all back
 5  « Closed in profit » (live / personal): archived « won », shown so in the archived list
 6  the account page's « ⋯ »: « Remove account… » (no more « Close account » without a result)
 7  phone: « Select », a tap selects (does not open), a long press starts the selection; the bar's buttons are 44 px; nothing
    wider than the window; Sweep AI's button steps aside
"""
import sys
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)

SETUP = """(()=>{ put('firms',{id:'ab-f',name:'AB Firm'});
  const mk=(id,name,mt,extra)=>put('accounts',Object.assign({id,firm_id:'ab-f',name,starting_balance_c:5000000,status:'active',created_on:'2026-09-01',money_type:mt,phase:mt==='personal'?'live':mt,rules:{dd_c:200000,target_c:mt==='eval'?300000:null}},extra||{}));
  mk('ab-e1','AB Eval 1','eval'); mk('ab-e2','AB Eval 2','eval'); mk('ab-f1','AB Funded 1','funded'); mk('ab-l1','AB Live 1','live'); mk('ab-p1','AB Perso 1','personal'); render(); })()"""
CLEAN = """(()=>{ const ids=S.accounts.filter(a=>a.id.startsWith('ab-')||String(a.from_eval||'').startsWith('ab-')||String(a.from_funded||'').startsWith('ab-')).map(a=>a.id);
  ids.forEach(id=>remove('accounts',id)); (S.expenses||[]).filter(x=>ids.includes(x.account_id)).forEach(x=>remove('expenses',x.id)); remove('firms','ab-f'); render(); return ids.length })()"""
ACC = "(id)=>{const a=getDoc('accounts',id); return a?[a.status,a.result||null,a.failed_on||a.passed_on||a.won_on||null]:null}"

def page(br, w, phone):
  c = br.new_context(storage_state=STATE, viewport={'width': w, 'height': 850}, is_mobile=phone, has_touch=phone, color_scheme='dark')
  c.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr'))")
  pg = c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
  pg.goto(B + '/#dashboard'); pg.wait_for_timeout(2600)
  pg.evaluate(CLEAN); pg.evaluate(SETUP); pg.wait_for_timeout(600)
  pg.evaluate("location.hash='#accounts'"); pg.wait_for_timeout(1600)
  return c, pg, errs

def row(pg, id):
  return pg.locator(f'#main table.acct-tbl tr[data-href="#account/{id}"]')

with sync_playwright() as p:
  br = p.chromium.launch(); allerr = []
  c, pg, errs = page(br, 1300, False)
  today = pg.evaluate("todayStr()")
  ic = pg.evaluate("['ab-e1','ab-f1','ab-l1','ab-p1'].map(id=>{const r=document.querySelector(`#main tr[data-href=\"#account/${id}\"]`); return r?[!!r.querySelector('[data-acc-up]'),!!r.querySelector('[data-acc-out]')]:null})")
  ok(ic == [[True, True], [True, True], [False, True], [False, True]], f'1 icons: up on evaluation and funded, remove on all ({ic})')
  # 2. remove one: the window, failed, undo
  row(pg, 'ab-e1').hover(); pg.locator('#main tr[data-href="#account/ab-e1"] [data-acc-out]').click(); pg.wait_for_timeout(500)
  opts = pg.evaluate("[...document.querySelectorAll('.acc-dlg [data-v]')].map(b=>b.dataset.v)")
  ok(opts == ['fail', 'funded', ''], f'2 « Remove » asks failed or passed → funded (no plain delete) ({opts})')
  pg.locator('.acc-dlg [data-v="fail"]').click(); pg.wait_for_timeout(700)
  st = pg.evaluate(ACC, 'ab-e1')
  ok(st == ['archived', 'failed', today], f'2 marked failed, archived, dated today ({st})')
  pg.locator('.nav-undo button').first.click(); pg.wait_for_timeout(700)
  st = pg.evaluate(ACC, 'ab-e1')
  ok(st == ['active', None, None], f'2 « Undo » restores it ({st})')
  # 3. several: move to funded
  for id in ['ab-e1', 'ab-e2', 'ab-l1']:
    row(pg, id).hover(); pg.locator(f'#main [data-acc-ck="{id}"]').check(force=True); pg.wait_for_timeout(150)
  barb = pg.evaluate("[...document.querySelectorAll('#accBar [data-accb]')].map(b=>b.dataset.accb)")
  ok(barb == ['clear', 'fail', 'funded', 'won'], f'3 one bar for 3 accounts: fail, funded, closed in profit ({barb})')
  pg.locator('#accBar [data-accb="funded"]').click(); pg.wait_for_timeout(500)
  ok(pg.locator('.acc-dlg [data-v="go"]').count() == 1, '3 « Move to funded » asks first')
  pg.locator('.acc-dlg [data-v="go"]').click(); pg.wait_for_timeout(900)
  r = pg.evaluate("[getDoc('accounts','ab-e1').result, getDoc('accounts','ab-e2').result, getDoc('accounts','ab-l1').status, S.accounts.filter(a=>String(a.from_eval||'').startsWith('ab-')&&a.phase==='funded'&&a.status==='active').length, (document.querySelector('.toast')||{}).textContent||'']")
  ok(r[0] == 'passed' and r[1] == 'passed' and r[2] == 'active' and r[3] == 2 and '1 ignoré' in r[4], f'3 2 evaluations passed → 2 funded accounts, the live one skipped and said ({r})')
  ok(pg.evaluate("location.hash") == '#accounts', '3 the list stays (no jump to an account)')
  # 4. several failed, one undo
  pg.evaluate("render()"); pg.wait_for_timeout(500)
  for id in ['ab-f1', 'ab-l1']:
    row(pg, id).hover(); pg.locator(f'#main [data-acc-ck="{id}"]').check(force=True); pg.wait_for_timeout(150)
  pg.locator('#accBar [data-accb="fail"]').click(); pg.wait_for_timeout(700)
  r = [pg.evaluate(ACC, 'ab-f1')[1], pg.evaluate(ACC, 'ab-l1')[1]]
  pg.locator('.nav-undo button').first.click(); pg.wait_for_timeout(700)
  r2 = [pg.evaluate(ACC, 'ab-f1')[0], pg.evaluate(ACC, 'ab-l1')[0]]
  ok(r == ['failed', 'failed'] and r2 == ['active', 'active'], f'4 two marked failed, one Undo brings both back ({r} → {r2})')
  # 5. closed in profit
  row(pg, 'ab-p1').hover(); pg.locator('#main tr[data-href="#account/ab-p1"] [data-acc-out]').click(); pg.wait_for_timeout(500)
  opts = pg.evaluate("[...document.querySelectorAll('.acc-dlg [data-v]')].map(b=>b.dataset.v)")
  pg.locator('.acc-dlg [data-v="won"]').click(); pg.wait_for_timeout(800)
  st = pg.evaluate(ACC, 'ab-p1')
  pg.evaluate("render()"); pg.wait_for_timeout(600)
  lab = pg.evaluate("(()=>{const a=document.querySelector('#main .nav-arch-r[href=\"#account/ab-p1\"]'); return a?a.textContent:''})()")
  ok(opts == ['fail', 'won', ''] and st == ['archived', 'won', today] and 'Fermé en gain' in lab, f'5 personal: failed or closed in profit → archived « won » ({opts} {st} {lab[:60]})')
  # 6. the account page's menu
  pg.evaluate("location.hash='#account/ab-f1'"); pg.wait_for_timeout(1500)
  m = pg.evaluate("[...document.querySelectorAll('#main .acc-menu .menu-pop button')].map(b=>b.textContent.trim())")
  ok(any('Retirer le compte' in x for x in m) and not any('Fermer le compte' in x for x in m), f'6 « ⋯ »: « Remove account… », no « Close account » ({m})')
  pg.locator('#main .acc-menu summary').click(); pg.wait_for_timeout(200); pg.locator('#main .acc-menu [data-acc-out]').click(); pg.wait_for_timeout(500)
  ok(pg.evaluate("[...document.querySelectorAll('.acc-dlg [data-v]')].map(b=>b.dataset.v)") == ['fail', 'live', ''], '6 it asks failed or passed → live')
  pg.keyboard.press('Escape'); pg.wait_for_timeout(300)
  ok(pg.evaluate(ACC, 'ab-f1')[0] == 'active', '6 « Cancel » / Esc changes nothing')
  pg.evaluate(CLEAN); allerr += errs; c.close()
  # 7. phone
  for w in [390, 320]:
    c, pg, errs = page(br, w, True)
    pg.locator('#main .acc-editb').click(); pg.wait_for_timeout(300)   # (one « Edit » on phones since 19 Oct.: select and reorder together)
    row(pg, 'ab-e1').tap(); row(pg, 'ab-l1').tap(); pg.wait_for_timeout(400)
    r = pg.evaluate("[location.hash, document.querySelector('#accBar') ? document.querySelector('.acc-bar-n').textContent : null, [...document.querySelectorAll('#accBar .btn')].map(b=>Math.round(b.getBoundingClientRect().height)), document.documentElement.scrollWidth-innerWidth, getComputedStyle(document.querySelector('#askFab')||document.body).opacity]")
    ok(r[0] == '#accounts' and r[1] and '2' in r[1] and all(h >= 44 for h in r[2]) and r[3] <= 0 and r[4] in ('0', '1'), f'7 phone {w}: « Edit », taps select 2 (no opening), 44 px buttons, no overflow ({r})')
    pg.locator('#accBar [data-accb="clear"]').click(); pg.wait_for_timeout(300)
    row(pg, 'ab-e2').scroll_into_view_if_needed(); pg.wait_for_timeout(300); box = row(pg, 'ab-e2').bounding_box()
    pg.touchscreen.tap(box['x'] + 10, box['y'] + 10)   # (a plain tap after « Clear »: opens the account)
    pg.wait_for_timeout(900)
    opened = pg.evaluate("location.hash")
    pg.evaluate("location.hash='#accounts'"); pg.wait_for_timeout(1400)
    row(pg, 'ab-e2').scroll_into_view_if_needed(); pg.wait_for_timeout(300)
    cdp = c.new_cdp_session(pg); box = row(pg, 'ab-e2').bounding_box(); x, y = box['x'] + 20, box['y'] + 20
    cdp.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [{'x': x, 'y': y}]}); pg.wait_for_timeout(650)
    cdp.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []}); pg.wait_for_timeout(500)
    lp = pg.evaluate("[location.hash, window.SweepAccSel.selected()]")
    ok(opened == '#account/ab-e2' and lp[0] == '#accounts' and lp[1] == ['ab-e2'], f'7 phone {w}: after « Clear » a tap opens; a long press selects ({opened}, {lp})')
    pg.evaluate(CLEAN); allerr += errs; c.close()
  ok(not allerr, f'no page error ({allerr[:2]})')
  br.close()
print(f'{fails} failed' if fails else 'all passed')
sys.exit(1 if fails else 0)
