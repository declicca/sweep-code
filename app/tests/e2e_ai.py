"""
Sweep — the search and « Ask Sweep » (brief 02, part 9), Playwright, phone (fr, es) and computer (en):
  python3 tests/e2e_ai.py http://127.0.0.1:8095 [storage_state, unused: each run signs up its own trader]
Sweep AI answers from its stand-in (SWEEP_AI_CHAT_MOCK = tests/samples/chat-ai-mock.json, tools/run.sh and tools/par.py):
no key, no call to Google.
 - the search understands a question in several words: « comment ajouter un payout » → « Ajouter un payout » first (it
   opens the payout form), « mes pires heures » → « Mes meilleures et pires heures », « importer tradovate » → the import
   and its help article; nothing found → « Aucun résultat » (not « No results »);
 - an answer about the trader's month says where it comes from: « D'après tes 3 trades du … au … » (counted by Sweep);
 - Sweep AI not answering (an outage): a clear sentence (not « Something went wrong »), then « Ces pages peuvent t'aider : »
   with the pages and help of the question; the first one opens the import.
Checks: no page error, nothing wider than the window, the texts in the trader's language.
"""
import json, os, re, sqlite3, sys, time
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
  'fr': {'q_pay': 'comment ajouter un payout', 'pay': 'Ajouter un payout', 'q_hours': 'mes pires heures', 'hours': 'Mes meilleures et pires heures', 'q_imp': 'importer tradovate', 'imp': 'Importer des trades',
         'help_g': 'Aide', 'none': 'Aucun résultat', 'q_month': 'Combien j’ai fait ce mois ?', 'src': 'D’après tes 3 trades du {a} au {b}.', 'q_out': 'Comment importer mes trades ? (panne)',
         'err': 'Sweep AI ne répond pas pour l’instant.', 'help': 'Ces pages peuvent t’aider :'},
  'en': {'q_pay': 'how do I add a payout', 'pay': 'Add a payout', 'q_hours': 'my worst hours', 'hours': 'My best and worst hours', 'q_imp': 'import tradovate', 'imp': 'Import trades',
         'help_g': 'Help', 'none': 'No results', 'q_month': 'How much did I make this month?', 'src': 'Based on your 3 trades from {a} to {b}.', 'q_out': 'How do I import my trades? (outage)',
         'err': "Sweep AI isn't answering right now.", 'help': 'These pages can help:'},
  'es': {'q_pay': 'como añadir un payout', 'pay': 'Añadir un payout', 'q_hours': 'mis peores horas', 'hours': 'Mis mejores y peores horas', 'q_imp': 'importar tradovate', 'imp': 'Importar operaciones',
         'help_g': 'Ayuda', 'none': 'Sin resultados', 'q_month': '¿Cuánto gané este mes?', 'src': 'Según tus 3 operaciones del {a} al {b}.', 'q_out': '¿Cómo importo mis operaciones? (caída)',
         'err': 'Sweep AI no responde ahora mismo.', 'help': 'Estas páginas pueden ayudarte:'},
}
SEED = """() => {
  const ago = (k) => { const d = new Date(todayStr() + 'T12:00:00'); d.setDate(d.getDate() - k); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`; };
  put('accounts', { id: 'a', name: 'Main 50K', status: 'active', starting_balance_c: 5000000, rules: {} });
  [[3, 30000], [8, 20000], [15, 15000], [60, -10000]].forEach(([k, v], i) => put('trades', { id: 'x' + i, account_id: 'a', instrument: 'NQ', direction: 'long', contracts: 1, entry: 1, exit: 2, pnl_c: v, date: ago(k), session_date: true, entry_time: '09:45:00', exit_time: '10:00:00' }));
  window.__D = [ago(15), ago(3)]; render(); }"""
TXT = "(sel) => [...document.querySelectorAll(sel)].map((e) => e.textContent.replace(/[\\u00a0\\u202f]/g, ' ').replace(/\\s+/g, ' ').trim())"
WIDE = "() => document.documentElement.scrollWidth - innerWidth"

def run(p, lang, phone):
  tag = f"{'390' if phone else '1300'}-{lang}"; x = X[lang]
  unthrottle()
  br = p.chromium.launch()
  ctx = br.new_context(viewport={'width': 390, 'height': 844} if phone else {'width': 1300, 'height': 850}, is_mobile=phone, has_touch=phone, bypass_csp=True, locale={'fr': 'fr-CA', 'en': 'en-US', 'es': 'es-ES'}[lang])
  ctx.add_init_script("try { localStorage.setItem('tj.lang', JSON.stringify('%s')); localStorage.setItem('sw.installShown', '1'); sessionStorage.setItem('sw.modal', '1') } catch (e) {}" % lang)
  r = ctx.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Testpass123!', 'email': 'ai%d@t.dev' % int(time.time() * 1000), 'consent': True, 'elapsed': 6000}), headers=H)
  if r.status != 201: raise RuntimeError('sign-up refused: %s' % r.status)
  ctx.request.post(B + '/api/me/profile', data=json.dumps({'first_name': 'Ana', 'experience': 'gt1'}), headers=H)
  pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
  pg.goto(B + '/'); pg.wait_for_selector('form[data-onb]', timeout=20000); pg.wait_for_timeout(500)
  pg.evaluate(SEED); pg.wait_for_selector('#main .nav-dash', timeout=10000); pg.wait_for_timeout(1200)
  pg.wait_for_function("typeof AI !== 'undefined' && AI.on", timeout=10000)
  def search(q):
    pg.evaluate("() => { if (!document.querySelector('#cmdq')) openCmd(); }"); pg.wait_for_selector('#cmdq', timeout=5000)
    pg.fill('#cmdq', q); pg.wait_for_timeout(400)
    return pg.evaluate(TXT, '#cmdl .cmd-it span'), pg.evaluate(TXT, '#cmdl .cmd-g')
  # 1. the search: questions in several words
  it, gs = search(x['q_pay'])
  ok(it[:1] == [x['pay']], f"{tag} search « {x['q_pay']} »: « {x['pay']} » first ({it[:3]})")
  it, gs = search(x['q_hours'])
  ok(it[:1] == [x['hours']], f"{tag} search « {x['q_hours']} »: « {x['hours']} » first ({it[:3]})")
  it, gs = search(x['q_imp'])
  ok(bool(it) and it[0].startswith(x['imp']) and x['help_g'] in gs, f"{tag} search « {x['q_imp']} »: the import, and a help article (« {x['help_g']} ») ({it[:4]}, {gs})")
  if SHOTS: pg.locator('#cmd').screenshot(path=os.path.join(SHOTS, f'p9-search-{tag}.png'))
  pg.evaluate("AI.on = false"); it, gs = search('zzqxw')
  ok(pg.evaluate(TXT, '#cmdl .cmd-empty') == [x['none']], f"{tag} nothing found (Sweep AI off): « {x['none']} »")
  pg.evaluate("AI.on = true")
  it, gs = search(x['q_pay']); pg.keyboard.press('Enter'); pg.wait_for_selector('#main form[data-form="payout"]', timeout=8000)
  ok(pg.evaluate("location.hash").startswith('#payouts'), f"{tag} Enter on « {x['pay']} »: the payout form is open")
  # 2. an answer about the month: where it comes from
  pg.evaluate("location.hash = '#dashboard'"); pg.wait_for_timeout(600)
  pg.evaluate("askToggle(true)"); pg.wait_for_selector('#askPanel textarea', timeout=5000); pg.wait_for_timeout(400)
  pg.evaluate("(q) => askSend(q)", x['q_month']); pg.wait_for_selector('#askPanel .ask-msg.b .ask-src', timeout=10000); pg.wait_for_timeout(300)
  d = pg.evaluate("window.__D.map((v) => fdate(v))")
  want = x['src'].replace('{a}', d[0]).replace('{b}', d[1]).replace(' ', ' ').replace(' ', ' ')
  ok(pg.evaluate(TXT, '#askPanel .ask-src')[-1:] == [re.sub(r'\s+', ' ', want)], f"{tag} the month's answer: « {want} » ({pg.evaluate(TXT, '#askPanel .ask-src')})")
  if SHOTS: pg.locator('#askPanel').screenshot(path=os.path.join(SHOTS, f'p9-src-{tag}.png'))
  # 3. Sweep AI not answering: a clear sentence, then the pages and help of the question
  pg.wait_for_timeout(2300)   # (the local AI settings keep 2 s between two questions)
  pg.evaluate("(q) => askSend(q)", x['q_out']); pg.wait_for_selector('#askPanel .ask-msg.err .ask-help', timeout=10000); pg.wait_for_timeout(300)
  e = pg.evaluate("(() => { const m = [...document.querySelectorAll('#askPanel .ask-msg.err')].pop(); return [m.querySelector(':scope > div').childNodes[0].textContent.trim(), m.querySelector('.ask-help small').textContent.trim(), [...m.querySelectorAll('[data-ask-help]')].map((b) => b.textContent.trim())]; })()")
  ok(e[0] == x['err'] and e[1] == x['help'] and len(e[2]) >= 1 and e[2][0].startswith(x['imp']), f"{tag} no answer: « {x['err']} » + « {x['help']} » {e[2]}")
  ok(pg.evaluate(WIDE) <= 1, f'{tag} nothing wider than the window')
  if SHOTS: pg.locator('#askPanel').screenshot(path=os.path.join(SHOTS, f'p9-help-{tag}.png'))
  pg.click('#askPanel .ask-msg.err [data-ask-help="0"]'); pg.wait_for_timeout(900)
  ok(pg.evaluate("location.hash").startswith('#import'), f"{tag} the first help: the import page ({pg.evaluate('location.hash')})")
  ok(not errs, f'{tag} no page error ' + '; '.join(errs[:2]))
  br.close()

with sync_playwright() as p:
  run(p, 'fr', True)
  run(p, 'en', False)
  run(p, 'es', True)
print('all passed' if not fails else f'{fails} failed'); sys.exit(1 if fails else 0)
