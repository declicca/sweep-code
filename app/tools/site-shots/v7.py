"""
Sweep — the site's « v7 » captures (brief « Ce que l'app doit fournir pour mettre à jour le site », 29 Oct. 2026, section 4):
PNG, computer 2880 × 1800 (1440 × 900 at 2x), phone 1170 × 2532 (390 × 844 at 3x), EN and FR, dark (and light for the
screens marked ☀︎), sample trader « Alex Martin » (seed.py, SHOTS_LAST=Martin), never real data.
  SHOTS_LAST=Martin sh tools/site-shots/serve.sh python3 tools/site-shots/v7.py <out_dir> [name …]
  Friday's screens (weekly recap, Edge Reveal): DEST=/tmp/gs2 PORT=8997 SHOTS_NOW="2026-10-16 17:30" (same command)
Writes <out_dir>/captures/{en,fr}/v7-<nn>-<name>[-light]-<desktop|mobile>-<lang>.png. Nothing is written to the site.
What a capture changes only in the page (S, render) never reaches the database; the few writes go to the capture copy.
"""
import json, os, sqlite3, sys
from playwright.sync_api import sync_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shots
from shots import go, top, tap, g, click_text, scroll_text, phone

ARGS = [a for a in sys.argv[1:] if not a.startswith('--')]
OUT = ARGS[0] if ARGS else '/tmp/v7-out'; ONLY = set(ARGS[1:])
DEV = {'mobile': (390, 844, 3, True), 'desktop': (1440, 900, 2, False)}
NOW, DEST, STATE, B, LOC = shots.NOW, shots.DEST, shots.STATE, shots.B, shots.LOC
EVENING = shots.EVENING

def mem(pg, js, wait=1500):
  """a change in the page only (S, then render): the database is not touched"""
  pg.evaluate(js); pg.wait_for_timeout(wait)

def today(pg, lang):
  if phone(pg): shots.today(pg, lang)
  else: shots.today_d(pg, lang)

def risk(pg, lang):   # « Your risk allowed today », before the first trade: today's trades left out of the page
  go(pg, '#dashboard', 2000)
  mem(pg, "S.trades = S.trades.filter((t) => t.date !== todayStr()); render()", 2500); top(pg)

def close_day(pg, lang):   # « Close my day »: the balance on the platform, then the day closed
  go(pg, '#dashboard', 2000); pg.evaluate("SweepGame.openReview(todayStr())"); pg.wait_for_timeout(2800)

def streak(pg, lang):   # « My progress »: complete days, badges
  g(pg, 'hub', None, 3500)

def tomorrow(pg, lang):   # the day closed: the lesson and tomorrow's rule on Today (writes today's review: last of the day)
  shots.swept(pg, lang)

def weekly(pg, lang): g(pg, 'weekly', None, 3000)

def money(pg, lang): go(pg, '#payouts', 3000); top(pg)

def ninja(pg, lang): shots.connections_link(pg, lang)

def quantower(pg, lang):
  shots.connections(pg, lang)
  pg.evaluate("() => { const b = document.querySelector('#main [data-sy=\"connect\"][data-p=\"quantower\"]'); if (b) b.click(); }"); pg.wait_for_timeout(2500)

def multi(pg, lang): shots.new_trade_filled(pg, lang, 'trades')

def preset(pg, lang):   # Add an account: funded › Topstep › its sizes and payout rules
  go(pg, '#accounts', 2500)
  click_text(pg, r'^\+?\s*(Add (an )?account|Ajouter un compte|Agregar (una )?cuenta|Añadir (una )?cuenta)', 'body', 2200)
  for sel in ('[data-st-ph0=funded]', '[data-st-firm=topstep]'):
    if pg.locator(sel).count(): pg.locator(sel).first.click(); pg.wait_for_timeout(1200)

def rules_alert(pg, lang):   # the firm changed a rule: « Apply the new rules » / « Keep my rules » (in the page only)
  go(pg, '#dashboard', 1500)
  mem(pg, """(() => { const a = S.accounts.find((x) => x.id === 'a2'); a.preset_ver = '2026-10-01'; a.preset_skip = null;
    if (a.rules.payout_max_c) a.rules.payout_max_c -= 50000; if (a.rules.dd_c) a.rules.dd_c += 50000; })()""", 300)
  go(pg, '#account/a2', 3000); top(pg)

def eval_reached(pg, lang):   # an evaluation past its target, the consistency still missing (one big day, in the page only)
  go(pg, '#dashboard', 1500)
  mem(pg, """(() => { const a = S.accounts.find((x) => x.id === 'a1'); const t = JSON.parse(JSON.stringify(S.trades.find((x) => x.account_id === 'a1')));
    t.id = 'v7-big'; t.date = todayStr(); t.entry_time = '10:02'; t.exit_time = '10:31'; t.pnl_manual = true; t.pnl_c = (a.rules.target_c || 900000) + 40000; delete t.copy_group;
    S.trades.push(t); })()""", 300)
  go(pg, '#account/a1', 3000); top(pg)

def onboarding(pg, lang):   # a new trader's first screen
  import random
  r = pg.request.post(B + '/api/auth/register', data=json.dumps({'password': 'Sweep-New-2026!', 'email': 'new%06d.%s@example.com' % (random.randint(0, 999999), lang), 'consent': True, 'elapsed': 6000}), headers=shots_H)
  if r.status != 201: raise RuntimeError('sign-up refused %s' % r.status)
  pg.goto(B + '/'); pg.wait_for_selector('#main .onb, form[data-onb]', timeout=20000); pg.wait_for_timeout(1500)
shots_H = {'X-Requested-With': 'fetch', 'Content-Type': 'application/json'}

def gameplan(pg, lang):   # the 90-day plan, started three weeks ago (start day moved in the capture copy)
  pg.evaluate("fetch('api/game/gameplan/start', { method: 'POST', headers: { 'X-Requested-With': 'fetch', 'Content-Type': 'application/json' }, body: JSON.stringify({ track: 'B' }) })"); pg.wait_for_timeout(1200)
  uid = pg.evaluate("S.uid")
  db = sqlite3.connect(os.path.join(DEST, 'data', 'journal.db'), timeout=60); db.execute("UPDATE game_gameplan SET start_day = '2026-09-28' WHERE user_id = ?", (uid,)); db.commit(); db.close()
  pg.evaluate("SweepGPLoad().then((g) => g.openMap())"); pg.wait_for_timeout(3500)

def ask(pg, lang): shots.ask_sweep(pg, lang)
def econ(pg, lang): shots.news_report(pg, lang)
def page(route):
  def f(pg, lang): go(pg, route, 3000); top(pg)
  return f
def trade(pg, lang): shots.trade_chart(pg, lang)
def signup(pg, lang): shots.signup(pg, lang)

M, D, MD = ('mobile',), ('desktop',), ('mobile', 'desktop')
# name → (devices, light too, steps); Friday's ones: FRI; signed out: OUT_
SHOTS = {
  'v7-01-today': (MD, True, today),
  'v7-02-risk-allowed': (MD, False, risk),
  'v7-03-close-day': (M, False, close_day),
  'v7-04-complete-days': (M, False, streak),
  'v7-08-my-money': (MD, True, money),
  'v7-09-ninjatrader-sync': (D, False, ninja),
  'v7-10-quantower-sync': (D, False, quantower),
  'v7-11-multi-trade-screenshot': (MD, False, multi),
  'v7-12-firm-preset': (MD, False, preset),
  'v7-13-rule-change-alert': (M, False, rules_alert),
  'v7-14-eval-target-reached': (D, False, eval_reached),
  'v7-15-onboarding': (M, False, onboarding),
  'v7-16-gameplan-90-days': (MD, False, gameplan),
  'v7-17-ask-sweep': (MD, False, ask),
  'v7-18-economic-calendar-ai': (MD, False, econ),
  'v7-19-accounts': (MD, False, page('#accounts')),
  'v7-20-stats': (MD, False, page('#analytics')),
  'v7-21-journal': (MD, False, page('#journal/2026-10-14')),
  'v7-22-calendar': (MD, False, page('#calendar')),
  'v7-23-trade-recap': (MD, False, trade),
  'v7-24-signup': (MD, False, signup),
  'v7-05-review-tomorrow': (M, False, tomorrow),   # last: it closes today
  'v7-06-edge-reveal': (MD, False, shots.edge_reveal),
  'v7-07-weekly-recap': (MD, False, weekly),
}
FRI = {'v7-06-edge-reveal', 'v7-07-weekly-recap'}
SIGNED_OUT = {'v7-15-onboarding', 'v7-24-signup'}
CLEAN = {'v7-09-ninjatrader-sync': shots.relink}

def shoot():
  from PIL import Image
  with sync_playwright() as p:
    br = p.chromium.launch(); errs = []
    for name, (devs, light, steps) in SHOTS.items():
      if ONLY and name not in ONLY: continue
      if (name in FRI) != EVENING: continue
      for dev in devs:
        vw, vh, sc, ph = DEV[dev]
        for scheme in (('dark', 'light') if light else ('dark',)):
          for lang in ('en', 'fr'):
            ctx = br.new_context(**({} if name in SIGNED_OUT else {'storage_state': f'{STATE}-{lang}.json'}), viewport={'width': vw, 'height': vh}, device_scale_factor=sc, is_mobile=ph, has_touch=ph,
                                 locale=LOC[lang], timezone_id='America/New_York', color_scheme=scheme, reduced_motion='reduce')
            ctx.clock.set_fixed_time(NOW)
            ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('%s')); localStorage.setItem('sw.installShown', '1'); localStorage.setItem('tj.theme', JSON.stringify('%s'));" % (lang, scheme))
            pg = ctx.new_page(); pg.on('pageerror', lambda e, n=name: errs.append(n + ': ' + str(e)[:160]))
            if name in SIGNED_OUT: pg.goto(B + '/'); pg.wait_for_timeout(3000)
            else: pg.goto(B + '/#dashboard'); pg.wait_for_selector('#main .nav-dash', timeout=30000); pg.wait_for_timeout(2500)
            try: steps(pg, lang)
            except Exception as e: errs.append(f'{name} {dev} {lang}: STEP FAILED {str(e)[:200]}'); ctx.close(); continue
            d = os.path.join(OUT, 'captures', lang); os.makedirs(d, exist_ok=True)
            f = os.path.join(d, f"{name}{'-light' if scheme == 'light' else ''}-{dev}-{lang}.png")
            pg.screenshot(path=f, animations='disabled', caret='hide')
            im = Image.open(f); want = (vw * sc, vh * sc)
            if im.size != want: im.convert('RGB').resize(want, Image.LANCZOS).save(f)
            wide = pg.evaluate("document.documentElement.scrollWidth - innerWidth")
            if wide > 0: errs.append(f'{name} {dev} {lang}: {wide}px wider than the window')
            if name in CLEAN: CLEAN[name](pg)
            print(f"{os.path.basename(f)}: {os.path.getsize(f) // 1024} KB", flush=True)
            ctx.close()
    br.close()
  print('page errors:'); [print('  ', e) for e in errs]

if __name__ == '__main__':
  if '--keep' not in sys.argv: shots.seed(['en', 'fr'])
  # Alex has used Sweep for weeks: he sees everything, like every account from before the discovery missions
  db = sqlite3.connect(os.path.join(DEST, 'data', 'journal.db'), timeout=60); db.execute("UPDATE users SET discovery_done = 1 WHERE email LIKE 'alex.%'"); db.commit(); db.close()
  shoot()
