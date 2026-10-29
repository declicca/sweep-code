"""
Sweep — the site's « v7 » videos (brief of 29 Oct. 2026, section 5): no sound, MP4 H.264 and WebM VP9, computer 1920 × 1080,
phone 780 × 1688, 12 to 25 s, a poster that is the first frame, EN and FR, sample trader « Alex Martin » (capture copy only).
  SHOTS_LAST=Martin sh tools/site-shots/serve.sh python3 tools/site-shots/v7videos.py <out_dir> [name …]
  Friday's (follow-plan: the week's recap, in plan vs off plan): DEST=/tmp/gs2 PORT=8997 SHOTS_NOW="2026-10-16 17:30"
Writes <out_dir>/videos/{en,fr}/<name>-<desktop|mobile>.{mp4,webm} and -poster.webp; close-day also gives the sequence of
about 100 numbered WebP frames (900 px wide) in <out_dir>/sequences/{en,fr}/rings-fill-mobile/ (the last ring closing).
"""
import datetime as dt, json, os, shutil, sqlite3, subprocess, sys, tempfile
from zoneinfo import ZoneInfo
from playwright.sync_api import sync_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shots, videos
from videos import Rec, smooth, hash_go, g, close_sheet, no_nudge

ARGS = [a for a in sys.argv[1:] if not a.startswith('--')]
OUT = ARGS[0] if ARGS else '/tmp/v7-video'; ONLY = set(ARGS[1:])
B, DEST, STATE, NOW, LOC = shots.B, shots.DEST, shots.STATE, shots.NOW, shots.LOC
NY = ZoneInfo('America/New_York')
H = {'X-Requested-With': 'fetch', 'Content-Type': 'application/json'}

def ctx_for(br, lang, phone):
  w, h = (390, 844) if phone else (1920, 1080)
  c = br.new_context(storage_state=f'{STATE}-{lang}.json', viewport={'width': w, 'height': h}, device_scale_factor=2 if phone else 1, is_mobile=phone, has_touch=phone,
                     locale=LOC[lang], timezone_id='America/New_York', color_scheme='dark')
  c.clock.set_fixed_time(NOW)
  c.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('%s')); localStorage.setItem('sw.installShown', '1'); localStorage.setItem('tj.theme', JSON.stringify('dark'));" % lang)
  pg = c.new_page(); pg.goto(B + '/#dashboard'); pg.wait_for_selector('#main .nav-dash', timeout=30000); pg.wait_for_timeout(3500); no_nudge(pg)
  return c, pg, (780, 1688) if phone else (1920, 1080)

def finish(rec, name, lang, dev, length):
  """MP4 by the screencast, then WebM VP9 and the poster (its first frame)"""
  d = os.path.join(OUT, 'videos', lang); os.makedirs(d, exist_ok=True)
  base = os.path.join(d, f'{name}-{dev}'); rec.stop(base + '.mp4', length=length)
  subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', base + '.mp4', '-c:v', 'libvpx-vp9', '-b:v', '0', '-crf', '33', '-row-mt', '1', '-an', base + '.webm'], check=True)
  png = base + '-poster.png'
  subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', base + '.mp4', '-frames:v', '1', png], check=True)
  subprocess.run(['cwebp', '-quiet', '-q', '85', png, '-o', base + '-poster.webp'], check=True); os.remove(png)
  return base + '.mp4'

def tap_text(pg, rx, scope='body', wait=900):
  shots.click_text(pg, rx, scope, wait)

# ───── close-day (phone): the day's end, « Close my day », the balance, the day closed, the streak ─────
def close_day(br, lang):
  c, pg, (w, h) = ctx_for(br, lang, True)
  pg.evaluate("() => { const d = document.querySelector('#main details.nav-rt, #main .nav-rt'); if (d && d.tagName === 'DETAILS') d.open = true; }")
  r = Rec(pg, w, h); r.start(); pg.wait_for_timeout(2000)
  pg.evaluate("SweepGame.openReview(todayStr())"); pg.wait_for_timeout(2200)
  if not pg.locator('#gSheet [data-g=r-followed].on').count():
    b = pg.locator('#gSheet [data-g=r-followed]').first
    if b.count(): b.tap(); pg.wait_for_timeout(900)
  for b in pg.locator('#gSheet [data-bal-same]').all():
    try: b.tap(); pg.wait_for_timeout(700)
    except Exception: pass
  pg.wait_for_timeout(600); pg.locator('#gSheet [data-g=save-review]').tap(); pg.wait_for_timeout(4500)   # the day closed: « Day swept »
  pg.wait_for_timeout(2500)
  if pg.locator('[data-g=sw-close]').count(): g(pg, 'sw-close', None, 1500)
  pg.evaluate("scrollTo({ top: 0, behavior: 'smooth' })"); pg.wait_for_timeout(2500)
  out = finish(r, 'close-day', lang, 'mobile', None)
  sequence(out, lang, 'mobile', 900)   # the same moment as a scroll-driven sequence: the last ring closing
  c.close()

def sequence(mp4, lang, dev, width):
  """60 to 120 numbered WebP frames for a scroll-driven animation"""
  d = os.path.join(OUT, 'sequences', lang, f'rings-fill-{dev}'); shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
  dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', mp4], capture_output=True, text=True).stdout.strip() or 12)
  fps = 100 / dur; tmp = tempfile.mkdtemp()
  subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', mp4, '-vf', f'fps={fps:.4f},scale={width}:-2:flags=lanczos', os.path.join(tmp, '%04d.png')], check=True)
  for i, f in enumerate(sorted(os.listdir(tmp)), 1):
    subprocess.run(['cwebp', '-quiet', '-q', '80', os.path.join(tmp, f), '-o', os.path.join(d, 'rings-fill-%04d.webp' % i)], check=True)
  shutil.rmtree(tmp); print(d, len(os.listdir(d)), 'frames')

# ───── multi-trade-screenshot: a platform's history pasted, « 3 trades found », saved ─────
def multi(br, lang, phone):
  c, pg, (w, h) = ctx_for(br, lang, phone)
  json.dump({'default': json.load(open('/tmp/shots-img/readings.json'))['trades']}, open(os.path.join(shots.HERE, 'shot-ai.json'), 'w'))
  r = Rec(pg, w, h); r.start(); pg.wait_for_timeout(1500)
  pg.evaluate("() => [...document.querySelectorAll('[data-act=add-trade]')].find((e) => e.getClientRects().length).click()"); pg.wait_for_timeout(1500)
  pg.locator('.nav-am input[type=file]').first.set_input_files('/tmp/shots-img/trades.png'); pg.wait_for_timeout(5000)
  pg.evaluate("() => { const sc = [...document.querySelectorAll('.nav-am *')].find((x) => x.scrollHeight > x.clientHeight + 40 && /auto|scroll/.test(getComputedStyle(x).overflowY)); if (sc) sc.scrollTo({ top: sc.scrollHeight, behavior: 'smooth' }); }"); pg.wait_for_timeout(2200)
  tap_text(pg, r'^(Save|Enregistrer|Guardar)( (all|tout|todo|les|the) ?\d* ?(trades|operaciones)?)?', '.nav-am, [role=dialog], body', 3500)
  pg.wait_for_timeout(2500)
  finish(r, 'multi-trade-screenshot', lang, 'mobile' if phone else 'desktop', None); c.close()

# ───── my-money (computer): My money, simulated vs real, the month's real net ─────
def my_money(br, lang):
  c, pg, (w, h) = ctx_for(br, lang, False)
  hash_go(pg, '#payouts', 3000)
  r = Rec(pg, w, h); r.start(); pg.wait_for_timeout(3500)   # « My entries »: payouts received, pending, expenses
  tap_text(pg, r'^(Analysis|Analyse|Análisis)$', '#main', 4500)   # simulated vs real, the month's real net
  smooth(pg, 500, 2000); pg.wait_for_timeout(2500); smooth(pg, 0, 1500); pg.wait_for_timeout(1200)
  finish(r, 'my-money', lang, 'desktop', 16.0); c.close()

# ───── ninjatrader-sync (computer): a trade taken in NinjaTrader arrives in Sweep by itself ─────
def ny_ms(s): return int(dt.datetime.strptime(s, '%Y-%m-%d %H:%M:%S').replace(tzinfo=NY).timestamp() * 1000)
def ninja(br, lang):
  c, pg, (w, h) = ctx_for(br, lang, False)
  key = c.request.post(B + '/api/sync/key', data=json.dumps({'platform': 'ninjatrader'}), headers=H).json().get('key')
  bare = c.request   # the add-on's own request: only its key
  hash_go(pg, '#trades', 3000)
  r = Rec(pg, w, h); r.start(); pg.wait_for_timeout(3500)
  fills = [{'id': f'v7{lang}1', 'account': 'PA-APEX-224455-03', 'contract': 'MNQ 12-26', 'side': 'buy', 'qty': 4, 'price': 24688.25, 'ts': ny_ms('2026-10-15 10:58:12'), 'fee': 0.62, 'point_value': 2},
           {'id': f'v7{lang}2', 'account': 'PA-APEX-224455-03', 'contract': 'MNQ 12-26', 'side': 'sell', 'qty': 4, 'price': 24701.75, 'ts': ny_ms('2026-10-15 11:04:40'), 'fee': 0.62, 'point_value': 2}]
  res = bare.post(B + '/api/sync/push', data=json.dumps({'client': 'Sweep NT8 1.4', 'accounts': [{'name': 'PA-APEX-224455-03', 'connection': 'Apex', 'provider': 'Rithmic', 'currency': 'USD'}], 'fills': fills}), headers={'Content-Type': 'application/json', 'X-Sweep-Key': key})
  if not res.ok: print('push refused', res.status, res.text()[:200])
  pg.evaluate("typeof syncNow === 'function' && syncNow({ manual: true })"); pg.wait_for_timeout(4000)   # the app's own pull (it runs on its own every few seconds)
  pg.evaluate("() => { const t = S.trades.filter((x) => x.source === 'ninjatrader').sort((a, b) => (b.date + b.entry_time).localeCompare(a.date + a.entry_time))[0]; if (t) location.hash = '#trade/' + t.id; }"); pg.wait_for_timeout(4500)
  finish(r, 'ninjatrader-sync', lang, 'desktop', None); c.close()

# ───── follow-plan (Friday, computer): the week's recap, in plan vs off plan (Edge Reveal) ─────
def follow_plan(br, lang):
  c, pg, (w, h) = ctx_for(br, lang, False)
  r = Rec(pg, w, h); r.start(); pg.wait_for_timeout(1200)
  g(pg, 'weekly', None, 3000)
  for i in range(3):
    if pg.locator('#gSheet [data-g=wk-flip]').count(): break
    g(pg, 'wk-next', None, 2200)
  pg.evaluate("() => { const b = document.querySelector('#gSheet [data-g=wk-flip]'); if (b) b.click(); }"); pg.wait_for_timeout(5000)
  finish(r, 'follow-plan', lang, 'desktop', None); c.close()

THU = {'multi-trade-screenshot': lambda br, l: (multi(br, l, False), multi(br, l, True)),
       'my-money': my_money, 'ninjatrader-sync': ninja, 'close-day': close_day}   # close-day last: it closes the day
FRI = {'follow-plan': follow_plan}

if __name__ == '__main__':
  if '--keep' not in sys.argv:
    shots.seed(['en', 'fr'])
    db = sqlite3.connect(os.path.join(DEST, 'data', 'journal.db'), timeout=60); db.execute("UPDATE users SET discovery_done = 1 WHERE email LIKE 'alex.%'"); db.commit(); db.close()
  with sync_playwright() as p:
    br = p.chromium.launch()
    todo = FRI if shots.EVENING else {**THU}
    for n, f in todo.items():
      if ONLY and n not in ONLY: continue
      for lang in ('en', 'fr'):
        try: f(br, lang)
        except Exception as e: print('FAILED', n, lang, str(e)[:300])
    br.close()
