"""
Sweep — copy trading (brief 02, part 4), Playwright, phone (fr, es) and computer (en):
  python3 tests/e2e_copy_trading.py http://127.0.0.1:8095 [storage_state, unused: each run signs up its own trader]
A new trader: an Apex group of 3 accounts traded together (a1 $5 commission, a2 $4, a3 none, its copies at 50 %), a Topstep
account outside the group, and sample data (an account and a trade, flagged demo).
 - the banner « Did you take it on other accounts too? » only when another real active account has a trade in the same
   session (the sample data's never counts); otherwise the action stays in the « ⋯ » menu;
 - « Size of copies on this account (%) » on the account page (50 %);
 - « Copy to my Apex group (2 accounts) »: one tap, each copy at its size (2 MNQ → 1 on a3), its P&L for that size, its
   account's commission (or the original's fees for that size), « Undo »; the group counts once, as its original;
 - the copy panel: « Apex group · 3 » selects the group in one tap, a copy's size shows when it differs, « Save these
   2 accounts as a group » → the account page says « Copy group: 2 accounts », « Leave the group »;
 - the add form: the group's copies stay in sight in the short form; editing the original moves every copy (its own size,
   MNQ's point value, not NQ's).
Checks: no page error, nothing wider than the window, the texts in the trader's language.
"""
import json, os, sqlite3, sys, time
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
H = {'Content-Type': 'application/json', 'X-Requested-With': 'fetch'}
DB = os.environ.get('SWEEP_TEST_DB', '/tmp/g/data/journal.db')
SHOTS = os.environ.get('SWEEP_SHOTS', '')
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)
def unthrottle():
  try: d = sqlite3.connect(DB); d.execute('DELETE FROM attempts'); d.commit(); d.close()
  except Exception: pass
X = {
  'fr': {'btn': 'Copier sur d’autres comptes', 'grp': 'Copier sur mon groupe Apex (2 comptes)', 'done': 'Copié sur 2 comptes', 'chip': 'Groupe Apex · 3', 'save4': 'Enregistrer ces 4 comptes comme groupe',
         'save2': 'Enregistrer ces 2 comptes comme groupe', 'cpct': 'Taille des copies sur ce compte (%)', 'line3': 'Groupe de copie : Apex (3 comptes)', 'line2': 'Groupe de copie : 2 comptes', 'leave': 'Retirer du groupe'},
  'en': {'btn': 'Copy to other accounts', 'grp': 'Copy to my Apex group (2 accounts)', 'done': 'Copied to 2 accounts', 'chip': 'Apex group · 3', 'save4': 'Save these 4 accounts as a group',
         'save2': 'Save these 2 accounts as a group', 'cpct': 'Size of copies on this account (%)', 'line3': 'Copy group: Apex (3 accounts)', 'line2': 'Copy group: 2 accounts', 'leave': 'Leave the group'},
  'es': {'btn': 'Copiar a otras cuentas', 'grp': 'Copiar a mi grupo Apex (2 cuentas)', 'done': 'Copiado en 2 cuentas', 'chip': 'Grupo Apex · 3', 'save4': 'Guardar estas 4 cuentas como grupo',
         'save2': 'Guardar estas 2 cuentas como grupo', 'cpct': 'Tamaño de las copias en esta cuenta (%)', 'line3': 'Grupo de copia: Apex (3 cuentas)', 'line2': 'Grupo de copia: 2 cuentas', 'leave': 'Quitar del grupo'},
}
SEED = """() => {
  const ago = (k) => { const d = new Date(todayStr() + 'T12:00:00'); d.setDate(d.getDate() - k); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`; };
  put('firms', { id: 'apx', name: 'Apex' }); put('firms', { id: 'tsp', name: 'Topstep' });
  const A = (id, name, firm, extra) => put('accounts', Object.assign({ id, name, firm_id: firm, starting_balance_c: 5000000, status: 'active', phase: 'funded', money_type: 'funded', created_on: ago(40), rules: { consistency_pct: 50 } }, extra || {}));
  A('a1', 'Apex A', 'apx', { group_id: 'grp-x', fee_rt_c: 500 }); A('a2', 'Apex B', 'apx', { group_id: 'grp-x', fee_rt_c: 400 }); A('a3', 'Apex C', 'apx', { group_id: 'grp-x' });
  A('b1', 'Combine', 'tsp'); A('dm', 'Sample', 'apx', { demo: true });
  window.__D = { d: ago(3), d2: ago(5), d3: ago(2) };
  const T = (id, acc, day, extra) => put('trades', Object.assign({ id, account_id: acc, instrument: 'NQ', direction: 'long', contracts: 1, entry: 100, exit: 101, pnl_c: 2000, date: day, session_date: true, entry_time: '10:00:00', exit_time: '10:05:00' }, extra || {}));
  T('tb1', 'b1', ago(3)); T('dt', 'dm', ago(3), { demo: true }); T('tb2', 'b1', ago(5));
  render(); }"""
TXT = "(sel) => [...document.querySelectorAll(sel)].map((e) => e.textContent.replace(/[\\u00a0\\u202f]/g, ' ').replace(/\\s+/g, ' ').trim())"
WIDE = "() => document.documentElement.scrollWidth - innerWidth"
TRADE = """([id, acc, day, extra]) => put('trades', Object.assign({ id, account_id: acc, instrument: 'NQ', direction: 'long', contracts: 1, entry: 100, exit: 101, pnl_c: 2000, date: day, session_date: true, entry_time: '10:00:00', exit_time: '10:05:00' }, extra || {}))"""
COPIES = "(id) => { const t = getDoc('trades', id); return t && t.copy_group ? S.trades.filter((x) => x.copy_group === t.copy_group && x.id !== id).map((x) => [x.account_id, x.contracts, x.pnl_c, x.fees_c, x.created_at > t.created_at]).sort() : []; }"

def run(p, lang, phone):
  tag = f"{'390' if phone else '1300'}-{lang}"; x = X[lang]
  unthrottle()
  br = p.chromium.launch()
  ctx = br.new_context(viewport={'width': 390, 'height': 844} if phone else {'width': 1300, 'height': 850}, is_mobile=phone, has_touch=phone, bypass_csp=True, locale={'fr': 'fr-CA', 'en': 'en-US', 'es': 'es-ES'}[lang])
  ctx.add_init_script("try { localStorage.setItem('tj.lang', JSON.stringify('%s')); localStorage.setItem('sw.installShown', '1'); sessionStorage.setItem('sw.modal', '1') } catch (e) {}" % lang)
  r = ctx.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': 'cp%d@t.dev' % int(time.time() * 1000), 'consent': True, 'elapsed': 6000}), headers=H)
  if r.status != 201: raise RuntimeError('sign-up refused: %s' % r.status)
  ctx.request.post(B + '/api/me/profile', data=json.dumps({'first_name': 'Zoé', 'experience': 'gt1'}), headers=H)
  pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
  pg.goto(B + '/'); pg.wait_for_selector('form[data-onb]', timeout=20000); pg.wait_for_timeout(500)
  pg.evaluate(SEED); pg.wait_for_selector('#main .nav-dash', timeout=10000); pg.wait_for_timeout(1500)
  D = pg.evaluate("window.__D")
  def trade(tid):
    pg.evaluate(f"location.hash = '#trade/{tid}'"); pg.wait_for_selector('#main .tr-top, #main [data-act=edit-trade]', timeout=10000); pg.wait_for_timeout(800)
  # 1. the banner: the sample data's trade on the same day is not a reason; a real account's is
  trade('tb1')
  ok(pg.locator('#main .nav-copy').count() == 0, f'{tag} a trade alone in its session (the sample data aside): no banner')
  pg.evaluate(TRADE, ['ta0', 'a2', D['d'], {}]); pg.evaluate("render()"); pg.wait_for_timeout(600)
  ok(pg.evaluate(TXT, '#main .nav-copy:not(.done) [data-act=copy-open]') == [x['btn']], f"{tag} another account traded that session: « {x['btn']} »")
  trade('tb2')
  ok(pg.locator('#main .nav-copy').count() == 0 and pg.locator('#main details.menu [data-act=copy-open]').count() == 1, f'{tag} a session with no other trade: no banner, the action is in the « ⋯ » menu')
  # 2. the size of copies on a3: 50 %
  pg.evaluate("location.hash = '#account/a3'"); pg.wait_for_selector('#main .nav-cpct input', timeout=10000)
  ok(pg.evaluate(TXT, '#main .nav-cpct > span') == [x['cpct']], f"{tag} the account page: « {x['cpct']} »")
  ok(pg.evaluate(TXT, '#main .nav-grp > span') == [x['line3']], f"{tag} the account page: « {x['line3']} »")
  pg.fill('#main .nav-cpct input', '50'); pg.dispatch_event('#main .nav-cpct input', 'change'); pg.wait_for_timeout(400)
  ok(pg.evaluate("getDoc('accounts', 'a3').copy_pct") == 50, f'{tag} saved: copies at 50 % on Apex C')
  if SHOTS: pg.locator('#main .nav-cpct').screenshot(path=os.path.join(SHOTS, f'p4-pct-{tag}.png'))
  # 3. « Copy to my Apex group (2 accounts) »: one tap, each at its size
  pg.evaluate(TRADE, ['ta1', 'a1', D['d3'], {'instrument': 'MNQ', 'contracts': 2, 'exit': 110, 'pnl_c': 4000}]); pg.wait_for_timeout(300)
  trade('ta1')
  ok(pg.evaluate("getDoc('trades', 'ta1').fees_c") == 1000, f"{tag} the original: Apex A's commission ($5 × 2)")
  ok(pg.evaluate(TXT, '#main .nav-copy [data-copy-grp]') == [x['grp']], f"{tag} « {x['grp']} »")
  ok(pg.evaluate(WIDE) <= 1, f'{tag} the trade page: nothing wider than the window')
  if SHOTS: pg.locator('#main .nav-copy').screenshot(path=os.path.join(SHOTS, f'p4-banner-{tag}.png'))
  pg.click('#main .nav-copy [data-copy-grp]'); pg.wait_for_timeout(700)
  cp = pg.evaluate(COPIES, 'ta1')
  ok(cp == [['a2', 2, 4000, 800, True], ['a3', 1, 2000, 500, True]], f"{tag} 2 copies: Apex B 2 MNQ $40 its $4 × 2; Apex C 1 MNQ $20, half the original's fees; both made after the original ({cp})")
  ok(pg.evaluate(TXT, '.nav-undo span') == [x['done']], f"{tag} « {x['done']} · Undo »")
  pg.click('.nav-undo button'); pg.wait_for_timeout(600)
  ok(pg.evaluate("S.trades.filter((t) => t.date === window.__D.d3).length") == 1 and not pg.evaluate("getDoc('trades', 'ta1').copy_group"), f'{tag} « Undo »: the copies are gone, the original as before')
  pg.click('#main .nav-copy [data-copy-grp]'); pg.wait_for_timeout(700)
  ok(len(pg.evaluate(COPIES, 'ta1')) == 2 and pg.locator('#main .nav-copy.done').count() == 1, f'{tag} copied again: the line says where it is')
  rep = pg.evaluate("(() => { const g = getDoc('trades', 'ta1').copy_group; const keep = F.account; F.account = 'all'; try { const m = mergeCopies(sorted(S.trades.filter((t) => t.copy_group === g).reverse())); return m.map((t) => [t.id, t.pnl_c, t._copies.length]); } finally { F.account = keep; } })()")
  ok(rep == [['ta1', 4000, 3]], f'{tag} the group counts once, as its original ({rep})')
  # 4. the copy panel: a whole group in one tap, the size of each copy, a group saved, then left
  pg.evaluate(TRADE, ['tb3', 'b1', D['d'], {'contracts': 2, 'pnl_c': 4000}]); trade('tb3')
  pg.click('#main .nav-copy [data-act=copy-open]'); pg.wait_for_selector('#main .cp-grps', timeout=5000)
  ok(pg.evaluate(TXT, '#main .cp-grps [data-act=copy-grp]') == [x['chip']], f"{tag} the panel: « {x['chip']} »")
  pg.click('#main .cp-grps [data-act=copy-grp]'); pg.wait_for_timeout(400)
  on = pg.evaluate("[...document.querySelectorAll('#main [data-act=copy-pick].on')].map((b) => b.dataset.v).sort()")
  ok(on == ['a1', 'a2', 'a3'] and pg.evaluate(TXT, '#main [data-act=copy-pick][data-v=a3] .cp-ct') == ['· 1 ct'], f'{tag} one tap: the 3 accounts of the group, Apex C at 1 contract ({on})')
  ok(pg.evaluate(TXT, '#main [data-act=copy-save-grp]') == [x['save4']], f"{tag} « {x['save4']} »")
  if SHOTS: pg.locator('#main [data-act=copy-do]').locator('xpath=ancestor::div[contains(@class, "surface")][1]').screenshot(path=os.path.join(SHOTS, f'p4-panel-{tag}.png'))
  pg.click('#main [data-act=copy-do]'); pg.wait_for_timeout(700)
  ok(pg.evaluate(COPIES, 'tb3') == [['a1', 2, 4000, 1000, True], ['a2', 2, 4000, 800, True], ['a3', 1, 2000, None, True]], f"{tag} copied: each account at its size and commission (none on Apex C, none on the original) ({pg.evaluate(COPIES, 'tb3')})")
  pg.evaluate(TRADE, ['tb4', 'b1', D['d'], {}]); trade('tb4')
  pg.click('#main .nav-copy [data-act=copy-open]'); pg.wait_for_selector('#main [data-act=copy-pick][data-v=a2]', timeout=5000)
  pg.click('#main [data-act=copy-pick][data-v=a2]'); pg.wait_for_timeout(300)
  ok(pg.evaluate(TXT, '#main [data-act=copy-save-grp]') == [x['save2']], f"{tag} « {x['save2']} »")
  pg.click('#main [data-act=copy-save-grp]'); pg.wait_for_timeout(500)
  g = pg.evaluate("[getDoc('accounts', 'b1').group_id, getDoc('accounts', 'a2').group_id, getDoc('accounts', 'a1').group_id, getDoc('accounts', 'a3').group_id]")
  ok(g[0] and g[0] == g[1] and g[0] != 'grp-x' and g[2] == g[3] == 'grp-x', f'{tag} saved: Combine and Apex B together, Apex A and C still the Apex group ({g})')
  pg.evaluate("location.hash = '#account/a2'"); pg.wait_for_selector('#main .nav-grp', timeout=10000)
  ok(pg.evaluate(TXT, '#main .nav-grp > span') == [x['line2']] and pg.evaluate(TXT, '#main .nav-grp [data-grp-leave]') == [x['leave']], f"{tag} the account page: « {x['line2']} » · « {x['leave']} »")
  pg.click('#main .nav-grp [data-grp-leave]'); pg.wait_for_timeout(500)
  ok(pg.evaluate("[getDoc('accounts', 'a2').group_id || null, getDoc('accounts', 'b1').group_id || null]") == [None, None] and pg.locator('#main .nav-grp').count() == 0, f'{tag} left: a group of one is no group')
  # 5. the add form: the group's copies in sight, then an edit moves every copy at its size (MNQ's point value)
  pg.evaluate("location.hash = '#dashboard'"); pg.wait_for_timeout(800)
  pg.evaluate("openTicket(null, { manual: true })"); pg.wait_for_selector('#tkSlide.open', timeout=8000); pg.wait_for_timeout(500)
  pg.evaluate("() => { TK.account = 'a1'; tkRefresh(); }"); pg.wait_for_timeout(900)
  vis = pg.evaluate("(() => { const c = document.querySelector('#tkSlide .tk-copies'); return [!!document.querySelector('#tkSlide.nav-tk-min'), !!c && c.getBoundingClientRect().height > 0, [...TK.copyTo].sort()]; })()")
  ok(vis[1] and vis[2] == ['a3'], f'{tag} the add form: the group (Apex C; Apex B left it) is chosen and in sight, short form too ({vis})')
  n0 = pg.evaluate("S.trades.length")
  pg.evaluate("() => { TK.inst = 'MNQ'; TK.dir = 'long'; TK.qty = 2; TK.entry = 200; TK.exit = 210; tkRefresh(); }")
  pg.click('#tkSlide [data-act="tk-save"]'); pg.wait_for_function(f"S.trades.length >= {n0} + 2", timeout=10000); pg.wait_for_timeout(800)
  oid = pg.evaluate(f"S.trades.slice({n0}).find((t) => t.account_id === 'a1').id")
  ok(pg.evaluate(COPIES, oid) == [['a3', 1, 2000, 500, True]], f"{tag} saved: Apex C at 1 MNQ, $20, half of Apex A's $10 of fees ({pg.evaluate(COPIES, oid)})")
  pg.evaluate("() => { try { closeTicket(); } catch (e) {} }"); pg.wait_for_timeout(400)
  pg.evaluate(f"() => {{ openTicket('{oid}'); TK.exit = 205; tkRefresh(); }}"); pg.wait_for_selector('#tkSlide.open', timeout=5000); pg.wait_for_timeout(500)
  pg.click('#tkSlide [data-act="tk-save"]'); pg.wait_for_timeout(1200)
  c = pg.evaluate(f"(() => {{ const t = getDoc('trades', '{oid}'); const k = S.trades.find((x) => x.copy_group === t.copy_group && x.id !== t.id); return [t.pnl_c, k.contracts, k.pnl_c, k.exit]; }})()")
  ok(c == [2000, 1, 1000, 205], f'{tag} the original edited (exit 205): Apex C follows at its size, 1 MNQ × 5 points = $10 ({c})')
  ok(not errs, f'{tag} no page error ' + '; '.join(errs[:2]))
  br.close()

with sync_playwright() as p:
  run(p, 'fr', True)
  run(p, 'en', False)
  run(p, 'es', True)
print('all passed' if not fails else f'{fails} failed'); sys.exit(1 if fails else 0)
