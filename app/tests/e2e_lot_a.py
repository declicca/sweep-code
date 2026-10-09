"""
Sweep — UI/UX lot A (targeted fixes), dev environment with Playwright:
  python3 tests/e2e_lot_a.py http://127.0.0.1:8095 /tmp/show_state.json
Uses the signed-in trader's data (sample data is enough) and adds then removes its own few test documents.
 1.1 the routine folds (chevron), stays folded for the session (after a reload), opens again on the next session
 1.2 « What to watch » stays under the day, whatever the account type, on a wide screen (1680 px)
 1.3 the Week tab shows Actual · Forecast · Previous (or « No number ») on each release
 2   « Save the trade »: 44 px on a computer, 48 px on a phone, 15 px semibold (the global primary look)
 3   « Make my plan »: still solid blue on hover
 5   « Add a trade on this day » is a neutral button (not primary)
 10  every account group can be reordered (grips in each), only within its group, and the order is kept
 11  a −12,345.67 day at 390 / 360 / 320 px: the Net P&L fits its tile, the exact amount stays in its label
 12  search: one box (the field is transparent), no empty frame when the search is hidden
 13/16 phone: ≥ 12 px between the account-type selector and what follows (Trades, Stats)
 14  the Calendar has the selector and its month total follows it
 15.2/15.3 Pre-market / Post-market keep a rounded header when open
 17.2/17.3 Accounts (active and closed): no line under the last row
 9/18.1 the CSV is what the page shows: period, account type and firm
"""
import csv, io, sys
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)

def page(br, w, phone, h=900, dl=False):
  c = br.new_context(storage_state=STATE, viewport={'width': w, 'height': h}, is_mobile=phone, has_touch=phone, color_scheme='dark', accept_downloads=dl)
  c.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('fr')); if(!sessionStorage.getItem('la.once')){sessionStorage.setItem('la.once','1'); localStorage.removeItem('sw.rtClosedDay')}")
  pg = c.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
  pg.goto(B + '/?x=1#dashboard'); pg.wait_for_timeout(2800)
  pg.evaluate("U.mtype='all'; saveU()")
  return c, pg, errs

SETUP = """(()=>{ if (S.accounts.some(a=>a.id==='la-ev-0')) return; put('firms',{id:'la-f',name:'LotA Firm'});
  const mk=(id,name,mt,extra)=>put('accounts',Object.assign({id,firm_id:'la-f',name,starting_balance_c:5000000,status:'active',created_on:'2026-09-01',money_type:mt,phase:mt,rules:{dd_c:200000,target_c:mt==='eval'?300000:null}},extra||{}));
  for (let i=0;i<3;i++){ mk('la-ev-'+i,'LA Éval '+(i+1),'eval'); mk('la-fu-'+i,'LA Financé '+(i+1),'funded'); }
  mk('la-cl-0','LA Fermé','eval',{status:'archived',result:'failed'}); render(); })()"""
CLEAN = """(()=>{ S.accounts.filter(a=>/^la-/.test(a.id)).map(a=>a.id).forEach(id=>remove('accounts',id)); remove('firms','la-f'); remove('trades','la-big'); render(); })()"""

with sync_playwright() as p:
  br = p.chromium.launch()
  # ── computer
  c, pg, errs = page(br, 1680, False)
  pg.evaluate(SETUP); pg.wait_for_timeout(1500)
  print('— 1.2 / 1.1 / 1.3 / 3 (Today, 1680 px)')
  pos = []
  for k in ['all', 'personal', 'live', 'all']:
    pg.locator(f'#main .mny-tseg [data-mtype={k}]').first.click(); pg.wait_for_timeout(1300)
    pos.append(pg.evaluate("(()=>{const w=document.querySelector('#main section.d-news'); return w ? [w.parentElement.className.includes('nav-merge'), Math.round(w.getBoundingClientRect().left)] : null})()"))
  ok(all(x and x[0] and x[1] < 700 for x in pos), f'1.2 « À surveiller » stays under the day (left column) for Tout / Perso / Live ({pos})')
  fold = pg.locator('#main .nav-rt-fold')
  ok(fold.count() == 1 and fold.get_attribute('aria-expanded') == 'true', '1.1 the routine has its fold button, open by default')
  fold.click(); pg.wait_for_timeout(600)
  pg.reload(); pg.wait_for_timeout(2800)
  ok(pg.evaluate("document.querySelector('#main .nav-rt').classList.contains('closed-rt')"), '1.1 still folded after a reload (same session)')
  pg.evaluate("localStorage.setItem('sw.rtClosedDay','2020-01-02')"); pg.reload(); pg.wait_for_timeout(2800)
  ok(not pg.evaluate("document.querySelector('#main .nav-rt').classList.contains('closed-rt')"), '1.1 open again on another session')
  b = pg.locator('#main .nav-rt-s.next .btn.primary').first
  if b.count():
    b.hover(); pg.wait_for_timeout(400)
    bg = pg.evaluate("getComputedStyle(document.querySelector('#main .nav-rt-s.next .btn.primary')).backgroundColor")
    ok(bg in ('rgb(76, 141, 255)', 'rgb(47, 111, 228)'), f'3 « Faire mon plan » stays solid blue on hover ({bg})')   # the button blue (#2F6FE4 since the audit, step 1)
  wk = pg.locator('#main button').filter(has_text='Semaine')
  if wk.count():
    wk.first.click(); pg.wait_for_timeout(1500)
    n = pg.evaluate("[...document.querySelectorAll('#main .d-news .nav-ev')].map(e=>!!e.querySelector('.nav-ev-v3, .nav-nonum'))")
    ok(n and all(n), f'1.3 Week tab: every release shows Réel · Prév. · Préc. or « Sans chiffre » ({n})')
  print('— 2 / 10 / 14 / 9 (computer)')
  pg.evaluate("openTicket(null)"); pg.wait_for_timeout(1500)
  sv = pg.evaluate("(()=>{const b=[...document.querySelectorAll('button')].find(b=>/Enregistrer le trade/.test(b.textContent)&&b.getClientRects().length); if(!b) return null; const s=getComputedStyle(b); return [s.height, s.fontSize, s.fontWeight]})()")
  ok(sv == ['44px', '15px', '600'], f'2 « Enregistrer le trade » on a computer: 44 px, 15 px, semibold ({sv})')
  pg.keyboard.press('Escape'); pg.wait_for_timeout(500); pg.evaluate("document.querySelectorAll('.evp.open [data-am=close], .nav-am.open [data-am=close]').forEach(b=>b.click())"); pg.wait_for_timeout(400)
  pg.evaluate("location.hash='#accounts'"); pg.wait_for_timeout(2000)
  g = pg.evaluate("[...[...document.querySelectorAll('#main .surface')].find(s=>s.querySelector('.mny-grp')).querySelectorAll('.mny-grp')].map(g=>[g.querySelectorAll('tbody tr').length, g.querySelectorAll('.nav-grip').length])")
  ok(g and all(r[0] == r[1] for r in g if r[0]) and len([r for r in g if r[1]]) >= 3, f'10 every group of active accounts has its grips ({g})')
  def dnd(src, dst):
    pg.evaluate("""([a,b])=>{const dt=new DataTransfer(); const fire=(el,t)=>{const r=el.getBoundingClientRect(); el.dispatchEvent(new DragEvent(t,{bubbles:true,cancelable:true,dataTransfer:dt,clientX:r.left+20,clientY:r.top+3}))}; fire(a,'dragstart'); fire(b,'dragover'); fire(b,'drop'); fire(a,'dragend')}""", [src.element_handle(), dst.element_handle()]); pg.wait_for_timeout(900)
  grp = lambda name: pg.evaluate("(n)=>{const g=[...document.querySelectorAll('#main .mny-grp')].find(g=>g.querySelector('h3').textContent.trim().startsWith(n)); return g?[...g.querySelectorAll('tbody tr')].map(r=>decodeURIComponent((r.dataset.href||'').replace('#account/',''))):[]}", name)
  ev = pg.locator('#main .mny-grp').filter(has=pg.locator('h3', has_text='Évaluations')).first.locator('tbody tr')
  # (exceeded accounts always stay at the bottom — a product rule — so the 2nd account, never an exceeded one, goes to the top)
  before = grp('Évaluations'); dnd(ev.nth(1), ev.nth(0)); after = grp('Évaluations')
  ok(after and len(before) > 1 and after[0] == before[1], f'10 Évaluations: the 2nd account dragged to the top ({after[:2]})')
  fu = pg.locator('#main .mny-grp').filter(has=pg.locator('h3', has_text='Financés')).first.locator('tbody tr').nth(0)
  dnd(pg.locator('#main .mny-grp').filter(has=pg.locator('h3', has_text='Évaluations')).first.locator('tbody tr').nth(0), fu)
  ok(grp('Évaluations') == after, '10 an evaluation cannot be dragged into Financés')
  pg.reload(); pg.wait_for_timeout(2500)
  ok(grp('Évaluations') == after, '10 the new order is kept after a reload')
  pg.evaluate("location.hash='#calendar'"); pg.wait_for_timeout(2000)
  ok(pg.locator('#main .mny-tseg').count() == 1, '14 the Calendar shows the account-type selector')
  for k in ['eval', 'live', 'all']:
    pg.locator(f'#main .mny-tseg [data-mtype={k}]').first.click(); pg.wait_for_timeout(1100)
    got = pg.evaluate("(()=>{const m=document.getElementById('main').innerText.match(/P&L du mois\\s*\\n\\s*([^\\n]+)/); return m?m[1].trim():null})()")
    exp = pg.evaluate(f"(()=>{{const mo=todayStr().slice(0,7); const c=mergeCopies(S.trades.filter(t=>t.date.startsWith(mo)&&('{k}'==='all'||moneyTypeOf(S.accounts.find(a=>a.id===t.account_id))==='{k}'))).reduce((s,t)=>s+tNet(t),0); return money(c,{{dec:Math.abs(c)%100?2:0}})}})()")
    ok(got is not None and got.replace('+', '') == exp.replace('+', ''), f'14 Calendar « {k} »: month total {got} = {exp}')
  pg.evaluate("U.mtype='all'; saveU()")
  c.close()
  c, pg, errs2 = page(br, 1440, False, dl=True)
  pg.evaluate("location.hash='#payouts'"); pg.wait_for_timeout(2000)
  for per, mt in [('month', 'all'), ('year', 'funded'), ('all', 'live')]:
    pg.evaluate(f"(()=>{{U.mper='{per}'; U.mtype='{mt}'; F.firm='all'; F.account='all'; saveU(); render()}})()"); pg.wait_for_timeout(900)
    with pg.expect_download() as d: pg.locator('#main [data-mny=csv]').first.click()
    rows = list(csv.reader(io.StringIO(open(d.value.path(), encoding='utf-8-sig').read())))[1:]
    exp = pg.evaluate("""(()=>{const [from,to]=SweepMoney.periodOf(U.mper,U.mcustom); const m=SweepMoney.moneyOf({from,to,mtype:U.mtype}); const inP=d=>!!d&&(!from||d>=from)&&(!to||d<=to);
      return [m.payouts.filter(p=>SweepMoney.pState(p)==='paid'&&inP(SweepMoney.pPaidOn(p))).length + m.expenses.length + m.trades.filter(t=>['live','personal'].includes(moneyTypeOf(S.accounts.find(a=>a.id===t.account_id)))).length, from, to]})()""")
    out = [r for r in rows if (exp[1] and r[0] < exp[1]) or (exp[2] and r[0] > exp[2])]
    ok(len(rows) == exp[0] and not out, f'9 CSV {per} · {mt}: {len(rows)} lines = the page ({exp[0]}), none outside the period')
  pg.evaluate("U.mper='month'; U.mtype='all'; saveU()")
  c.close()
  # ── phone
  print('— 2 / 5 / 11 / 12 / 13 / 15 / 16 / 17 (phone)')
  c, pg, errs3 = page(br, 390, True, h=1300)
  pg.evaluate("openTicket(null)"); pg.wait_for_timeout(1500)
  sv = pg.evaluate("(()=>{const b=[...document.querySelectorAll('button')].find(b=>/Enregistrer le trade/.test(b.textContent)&&b.getClientRects().length); if(!b) return null; const s=getComputedStyle(b); return [s.height, s.fontSize]})()")
  ok(sv == ['48px', '15px'], f'2 « Enregistrer le trade » on a phone: 48 px, 15 px ({sv})')
  pg.reload(); pg.wait_for_timeout(2500)
  d = pg.evaluate("(()=>{const t=S.trades.filter(x=>x.date).map(x=>x.date).sort(); return t[t.length-1]})()")
  pg.evaluate(f"location.hash='#journal/{d}'"); pg.wait_for_timeout(1800)
  ad = pg.evaluate("(()=>{const b=document.querySelector('#main .nav-addday'); return b?b.classList.contains('primary'):null})()")
  ok(ad is False, f'5 / 15.1 « Ajouter un trade ce jour-là » is neutral ({ad})')
  heads = []
  for i in range(pg.locator('#main .nav-fold-t').count()):
    pg.locator('#main .nav-fold-t').nth(i).click(); pg.wait_for_timeout(700)
    heads.append(pg.evaluate(f"getComputedStyle(document.querySelectorAll('#main .nav-fold')[{i}].querySelector('.nav-fold-h')).borderBottomLeftRadius"))
  ok(heads and all(h == '14px' for h in heads), f'15.2 / 15.3 Pre-market and Post-market keep a rounded header when open ({heads})')
  pg.evaluate("location.hash='#accounts'"); pg.wait_for_timeout(2000)
  lines = pg.evaluate("[...document.querySelectorAll('#main .surface')].filter(s=>s.querySelector('table.acct-tbl')).map(s=>{const t=[...s.querySelectorAll('table.acct-tbl')].pop(); return getComputedStyle(t.querySelector('tbody tr:last-child')).borderBottomWidth})")
  ok(lines and all(l == '0px' for l in lines), f'17.2 / 17.3 no line under the last account, active and closed ({lines})')
  for h in ['trades', 'analytics']:
    pg.evaluate(f"location.hash='#{h}'"); pg.wait_for_timeout(1800)
    gap = pg.evaluate("(()=>{let t=document.querySelector('#main .mny-cseg')||document.querySelector('#main .mny-tsw'); let n=t&&t.nextElementSibling; while(n&&!n.getClientRects().length) n=n.nextElementSibling; return t&&n?Math.round(n.getBoundingClientRect().top-t.getBoundingClientRect().bottom):null})()")
    ok(gap is not None and gap >= 12, f'13 / 16.1 {h}: {gap} px between the selector and what follows')
  pg.evaluate("location.hash='#trades'"); pg.wait_for_timeout(1500)
  sr = pg.evaluate("(()=>{const f=document.querySelector('#main .msearch'), few=document.body.classList.contains('nav-few-trades'); if(!f) return 'none'; if(few) return f.getClientRects().length?'empty frame shown':'hidden'; const i=f.querySelector('input'); return getComputedStyle(i).backgroundColor==='rgba(0, 0, 0, 0)'&&getComputedStyle(i).boxShadow==='none'?'one box':'two boxes'})()")
  ok(sr in ('hidden', 'one box', 'none'), f'12 search: {sr}')
  c.close()
  for w in [390, 360, 320]:
    c, pg, e4 = page(br, w, True)
    pg.evaluate("(()=>{const a=S.accounts.find(x=>x.status!=='archived'); put('trades',{id:'la-big',account_id:a.id,instrument:'NQ',direction:'short',contracts:1,entry:1,exit:2,pnl_c:-1234567,pnl_manual:true,date:todayStr(),entry_time:'10:00',exit_time:'10:01',session_date:true}); render()})()"); pg.wait_for_timeout(1600)
    r = pg.evaluate("(()=>{const k=document.querySelector('#main .nav-kpi-g > div:first-child b'); if(!k) return null; const a=k.getBoundingClientRect(), b=k.parentElement.getBoundingClientRect(); return [a.right<=b.right+1, k.textContent.trim(), k.getAttribute('aria-label')||k.textContent.trim()]})()")
    ok(r and r[0] and '12' in r[2] and '345' in r[2], f'11 {w} px: a −12,345.67 day fits its tile ({r})')
    pg.evaluate("remove('trades','la-big')"); pg.wait_for_timeout(400)
    if w == 320: pg.evaluate(CLEAN); pg.wait_for_timeout(800)
    c.close()
  allerr = errs + errs2 + errs3
  ok(not allerr, f'no page error ({allerr[:2]})')
  br.close()
print(f'{fails} failed' if fails else 'all passed')
sys.exit(1 if fails else 0)
