"""
Sweep — the site's videos (brief of 20 Oct. 2026, section 5): one source each, MP4 H.264, no sound, from the current app on
the capture server (serve.sh, sample trader Alex). The frames are Chromium's own screencast (sharp, unlike a recorded
WebM), put together by ffmpeg at their real timing.
  sh tools/site-shots/serve.sh python3 tools/site-shots/videos.py <out_dir> [name …] [--keep]
  hero-loop.mp4 (1920 × 1080, ~14 s), tour.mp4 (1920 × 1080, 60 s), captures/{en,fr}/v6-video-today-phone.mp4 (780 × 1688, ~24 s)
"""
import base64, datetime as dt, json, os, shutil, subprocess, sys, tempfile, time
from zoneinfo import ZoneInfo
from playwright.sync_api import sync_playwright
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
B = 'http://127.0.0.1:%s' % os.environ.get('PORT', '8996')
ARGS = [a for a in sys.argv[1:] if not a.startswith('--')]
OUT = ARGS[0] if ARGS else '/tmp/shots-video'; ONLY = set(ARGS[1:])
DEST = os.environ.get('DEST', '/tmp/gs'); STATE = DEST + '-state'
NY = ZoneInfo('America/New_York')
NOW = dt.datetime.strptime(os.environ.get('SHOTS_NOW', '2026-10-15 11:05'), '%Y-%m-%d %H:%M').replace(tzinfo=NY)
LOC = {'en': 'en-US', 'fr': 'fr-CA', 'es': 'es-ES'}

class Rec:
  """Chromium's screencast: every new frame with its time; ffmpeg gives each one its real duration"""
  def __init__(self, pg, w, h):
    self.cdp = pg.context.new_cdp_session(pg); self.frames = []; self.dir = tempfile.mkdtemp(prefix='sweep-vid-'); self.w, self.h = w, h
    self.cdp.on('Page.screencastFrame', self.frame)
  def frame(self, e):
    f = os.path.join(self.dir, '%05d.jpg' % len(self.frames))
    open(f, 'wb').write(base64.b64decode(e['data'])); self.frames.append((time.time(), f))
    try: self.cdp.send('Page.screencastFrameAck', {'sessionId': e['sessionId']})
    except Exception: pass
  def start(self):
    self.cdp.send('Page.startScreencast', {'format': 'jpeg', 'quality': 95, 'maxWidth': self.w, 'maxHeight': self.h, 'everyNthFrame': 1}); self.t0 = time.time()
  def stop(self, out, length=None):
    self.cdp.send('Page.stopScreencast'); end = time.time()
    if length: end = self.frames[0][0] + length
    lst = os.path.join(self.dir, 'list.txt')
    with open(lst, 'w') as L:
      fr = [x for x in self.frames if x[0] <= end]
      for i, (t, f) in enumerate(fr):
        nxt = fr[i + 1][0] if i + 1 < len(fr) else end
        L.write(f"file '{f}'\nduration {max(0.001, nxt - t):.4f}\n")
      L.write(f"file '{fr[-1][1]}'\n")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', lst, *(['-t', f'{length:.2f}'] if length else []), '-vf', f'scale={self.w}:{self.h}:flags=lanczos,fps=30,format=yuv420p',
                    '-c:v', 'libx264', '-preset', 'slow', '-crf', '21', '-movflags', '+faststart', '-an', out], check=True)
    shutil.rmtree(self.dir, ignore_errors=True)
    print(out, f'{os.path.getsize(out) // 1024} KB', f'{len(fr)} frames')

def ctx_for(br, lang, w, h, phone):
  c = br.new_context(storage_state=f'{STATE}-{lang}.json', viewport={'width': w, 'height': h}, device_scale_factor=1 if not phone else 2, is_mobile=phone, has_touch=phone,
                     locale=LOC[lang], timezone_id='America/New_York', color_scheme='dark')
  c.clock.set_fixed_time(NOW)
  c.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('%s')); localStorage.setItem('sw.installShown', '1');" % lang)
  return c

def no_nudge(pg):
  """the « Complete your history in 1 minute » card closed (a one-time suggestion, not the subject of the video)"""
  pg.evaluate("() => { const b = document.querySelector('#main .rn-inv-x'); if (b) b.click(); }"); pg.wait_for_timeout(600)

def smooth(pg, y, ms=1200):
  pg.evaluate("([y, ms]) => new Promise((ok) => { const y0 = scrollY, t0 = performance.now(); const f = (t) => { const p = Math.min(1, (t - t0) / ms), e = p < .5 ? 2 * p * p : 1 - Math.pow(-2 * p + 2, 2) / 2; scrollTo(0, y0 + (y - y0) * e); p < 1 ? requestAnimationFrame(f) : ok(); }; requestAnimationFrame(f); })", [y, ms])

def hash_go(pg, r, wait):
  pg.evaluate("(r) => { location.hash = r; scrollTo(0, 0); }", r); pg.wait_for_timeout(wait)

def add_by_screenshot(pg):
  json.dump({'default': json.load(open('/tmp/shots-img/readings.json'))['trades']}, open(os.path.join(HERE, 'shot-ai.json'), 'w'))
  pg.evaluate("() => [...document.querySelectorAll('[data-act=add-trade]')].find((e) => e.getClientRects().length).click()"); pg.wait_for_timeout(1300)
  pg.locator('.nav-am input[type=file]').first.set_input_files('/tmp/shots-img/trades.png'); pg.wait_for_timeout(2600)
  pg.evaluate("() => { const c = [...document.querySelectorAll('button, a')].find((e) => e.getClientRects().length && /^(Cancel|Annuler|Cancelar)$/.test(e.textContent.trim())); if (c) c.click(); }"); pg.wait_for_timeout(700)

def g(pg, a, v=None, wait=1500):
  pg.evaluate("([a, v]) => { const b = document.createElement('button'); b.dataset.g = a; if (v) b.dataset.v = v; b.hidden = true; document.body.appendChild(b); b.click(); b.remove(); }", [a, v]); pg.wait_for_timeout(wait)

def close_sheet(pg, wait=600):
  g(pg, 'close', None, wait)

def hero(br, lang='en'):
  """~14 s, in a loop: your day, a trade added in seconds, your rules, each trade, payout ready, your progress"""
  c = ctx_for(br, lang, 1920, 1080, False); pg = c.new_page()
  pg.goto(B + '/#dashboard'); pg.wait_for_selector('#main .nav-dash'); pg.wait_for_timeout(3500); no_nudge(pg)
  r = Rec(pg, 1920, 1080); r.start(); pg.wait_for_timeout(1300)                 # your day
  add_by_screenshot(pg)                                                           # a trade in seconds (~4.6 s)
  hash_go(pg, '#account/a1', 1500)                                                # your rules (the account's limits)
  hash_go(pg, '#trade/t-2026-10-15-0-a2', 900)                                    # each trade, on its chart
  pg.evaluate("() => { const b = [...document.querySelectorAll('#main button')].find((e) => e.textContent.trim() === '1m'); if (b) b.click(); }"); pg.wait_for_timeout(500)
  pg.evaluate("() => { const b = [...document.querySelectorAll('#main button')].find((e) => e.textContent.trim() === '1m'); const x = b && (b.closest('.tr-chart') || b.parentElement); if (x) scrollTo({ top: x.getBoundingClientRect().top + scrollY - 24, behavior: 'smooth' }); }"); pg.wait_for_timeout(1500)
  hash_go(pg, '#account/a4', 600)                                                 # payout ready
  pg.evaluate("() => { const h = [...document.querySelectorAll('#main h2, #main h3')].find((e) => /^(Payout|Pago|Retiro)$/i.test(e.textContent.trim())); if (h) scrollTo({ top: h.getBoundingClientRect().top + scrollY - 30, behavior: 'smooth' }); }"); pg.wait_for_timeout(1700)
  hash_go(pg, '#dashboard', 400); g(pg, 'league', None, 1700)                     # your progress
  close_sheet(pg, 500); pg.wait_for_timeout(600)
  r.stop(os.path.join(OUT, 'video', 'hero-loop.mp4'), length=14.4); c.close()

def tour(br, lang='en'):
  """60 s: the product in one minute"""
  c = ctx_for(br, lang, 1920, 1080, False); pg = c.new_page()
  pg.goto(B + '/#dashboard'); pg.wait_for_selector('#main .nav-dash'); pg.wait_for_timeout(3500); no_nudge(pg)
  r = Rec(pg, 1920, 1080); r.start()
  pg.wait_for_timeout(2500); smooth(pg, 700, 2200); pg.wait_for_timeout(1200); smooth(pg, 0, 1200)           # Today
  add_by_screenshot(pg); pg.wait_for_timeout(300)                                                             # a trade from a screenshot
  hash_go(pg, '#trade/t-2026-10-15-0-a2', 1500)                                                              # the trade, its coach
  pg.evaluate("() => { const b = [...document.querySelectorAll('#main button')].find((e) => e.textContent.trim() === '1m'); if (b) b.click(); }"); pg.wait_for_timeout(700)
  pg.evaluate("() => { const b = [...document.querySelectorAll('#main button')].find((e) => e.textContent.trim() === '1m'); const x = b && (b.closest('.tr-chart') || b.parentElement); if (x) scrollTo({ top: x.getBoundingClientRect().top + scrollY - 24, behavior: 'smooth' }); }"); pg.wait_for_timeout(3000)
  hash_go(pg, '#accounts', 3000)                                                                              # the accounts and their rules
  hash_go(pg, '#account/a4', 1200)
  pg.evaluate("() => { const h = [...document.querySelectorAll('#main h2, #main h3')].find((e) => /^(Payout|Pago|Retiro)$/i.test(e.textContent.trim())); if (h) scrollTo({ top: h.getBoundingClientRect().top + scrollY - 30, behavior: 'smooth' }); }"); pg.wait_for_timeout(3200)
  hash_go(pg, '#payouts', 3500)                                                                               # my money
  hash_go(pg, '#analytics', 2500); smooth(pg, 900, 2500); pg.wait_for_timeout(1500)                           # stats
  hash_go(pg, '#calendar', 3500)                                                                              # calendar
  hash_go(pg, '#journal/2026-10-14', 3500)                                                                    # journal
  hash_go(pg, '#news', 3000)                                                                                  # economic calendar
  hash_go(pg, '#dashboard', 1200); g(pg, 'map', None, 3000); close_sheet(pg, 700)                             # the journey
  g(pg, 'league', None, 3000); close_sheet(pg, 700)                                                           # the league
  g(pg, 'social', None, 3000); close_sheet(pg, 900)                                                           # the crew
  pg.wait_for_timeout(2500)
  r.stop(os.path.join(OUT, 'video', 'tour.mp4'), length=60.0); c.close()

def today_phone(br, lang):
  """~24 s, phone: Today — the rings, the days, the releases"""
  c = ctx_for(br, lang, 390, 844, True); pg = c.new_page()
  pg.goto(B + '/#dashboard'); pg.wait_for_selector('#main .nav-dash'); pg.wait_for_timeout(3500); no_nudge(pg)
  r = Rec(pg, 780, 1688); r.start(); pg.wait_for_timeout(2500)
  for y in (460, 900, 1340):
    smooth(pg, y, 1700); pg.wait_for_timeout(2200)
  smooth(pg, 0, 1800); pg.wait_for_timeout(1300)
  g(pg, 'detail', None, 3000); close_sheet(pg, 900); pg.wait_for_timeout(1500)
  r.stop(os.path.join(OUT, 'captures', lang, 'v6-video-today-phone.mp4'), length=24.0); c.close()

VIDEOS = {'hero-loop': lambda br: hero(br), 'tour': lambda br: tour(br),
          'v6-video-today-phone': lambda br: [today_phone(br, l) for l in ('en', 'fr')]}

if __name__ == '__main__':
  with sync_playwright() as p:
    br = p.chromium.launch()
    for n, f in VIDEOS.items():
      if ONLY and n not in ONLY: continue
      f(br)
    br.close()
