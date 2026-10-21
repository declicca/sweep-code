"""
Sweep — the site's captures: the platform screenshots Alex drops into « New trade » (drawn here, no real platform's data):
a trades table and a 1-minute chart with its closed position. Each comes with Sweep AI's reading (the stand-in answer
written to shot-ai.json just before the capture, serve.sh: SWEEP_AI_MOCK).
  python3 tools/site-shots/images.py <out_dir>     → trades.png, chart.png and their readings
"""
import json, os, random, sys
from PIL import Image, ImageDraw, ImageFont

def font(size, bold=False):
  for f in (('/System/Library/Fonts/Supplemental/Arial Bold.ttf' if bold else '/System/Library/Fonts/Supplemental/Arial.ttf'), '/System/Library/Fonts/Helvetica.ttc'):
    if os.path.exists(f): return ImageFont.truetype(f, size)
  return ImageFont.load_default()

# the trade Alex adds from a screenshot: today, after his two logged trades (data.py)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import data
_last = max((t for t in data.build('en')['trades'] if t['date'] == '2026-10-15'), key=lambda t: t['entry_time'])['exit']   # the price at 10:45
TRADE = {'symbol': 'NQZ6', 'side': 'Long', 'qty': 1, 'entry': _last - 3.5, 'exit': _last + 13.0, 'in': '10/15/2026 10:48:12', 'out': '10/15/2026 10:57:40'}
CHART = {'symbol': 'MNQZ6', 'side': 'Short', 'qty': 4, 'entry': _last + 6.25, 'exit': _last - 15.0, 'in': '10:31', 'out': '10:44'}
BASE = round(_last / 10) * 10

def trades_png(path):
  W, H = 1520, 300; im = Image.new('RGB', (W, H), (17, 17, 19)); d = ImageDraw.Draw(im)
  d.text((44, 34), 'TopstepX  ·  Trades', font=font(30, True), fill=(235, 235, 240))
  cols = [('ContractName', 44), ('EnteredAt', 250), ('ExitedAt', 560), ('Entry', 870), ('Exit', 1010), ('Size', 1150), ('Type', 1240), ('PnL', 1350)]
  for c, x in cols: d.text((x, 110), c, font=font(26), fill=(150, 150, 160))
  d.line((44, 152, W - 44, 152), fill=(45, 45, 52), width=2)
  pnl = (TRADE['exit'] - TRADE['entry']) * 20 * TRADE['qty']
  row = [TRADE['symbol'], TRADE['in'], TRADE['out'], '%.2f' % TRADE['entry'], '%.2f' % TRADE['exit'], str(TRADE['qty']), TRADE['side'], '%.2f' % pnl]
  for (c, x), v in zip(cols, row): d.text((x, 178), v, font=font(26), fill=(90, 200, 120) if c == 'PnL' else (230, 230, 235))
  im.save(path)
  return {'source_type': 'closed_trades', 'platform_guess': 'topstepx', 'timezone_shown': 'ET', 'date_shown': '10/15/2026', 'account_label': 'XFA 50K',
          'columns': [c for c, x in cols], 'table': [row], 'pnl_colors': ['green'], 'rows': []}

def chart_png(path):
  W, H = 1520, 980; im = Image.new('RGB', (W, H), (14, 15, 18)); d = ImageDraw.Draw(im); R = random.Random(4)
  d.text((30, 22), 'MNQZ6  ·  Micro E-mini Nasdaq-100  ·  1 min', font=font(26, True), fill=(225, 225, 230))
  top, bot, left, right = 80, 900, 30, 1130
  lo, hi = BASE - 40, BASE + 40
  y = lambda p: bot - (p - lo) / (hi - lo) * (bot - top)
  for k in range(9):
    p = lo + k * 10; d.line((left, y(p), right, y(p)), fill=(28, 29, 34)); d.text((right + 10, y(p) - 12), '%d' % p, font=font(20), fill=(120, 120, 130))
  price = BASE - 2.0; n = 66; w = (right - left) / n
  for i in range(n):
    drift = 0.9 if i < 22 else (-1.2 if i < 50 else 0.2)
    o = price; c = o + drift + R.uniform(-4, 4); h = max(o, c) + R.uniform(0.5, 3); l = min(o, c) - R.uniform(0.5, 3); price = c
    x = left + i * w + w / 2; col = (76, 141, 255) if c >= o else (212, 162, 76)
    d.line((x, y(h), x, y(l)), fill=col, width=2); d.rectangle((x - w * 0.32, y(max(o, c)), x + w * 0.32, y(min(o, c)) + 1), fill=col)
  for p, lab, col in ((CHART['entry'], 'Entry', (235, 235, 240)), (CHART['exit'], 'Exit', (90, 200, 120))):
    d.line((left, y(p), right, y(p)), fill=col, width=1); d.text((left + 8, y(p) - 30), '%s  %.2f' % (lab, p), font=font(20), fill=col)
  for k, t in enumerate(['10:00', '10:15', '10:30', '10:45', '11:00']): d.text((left + k * (right - left) / 4.4, bot + 14), t, font=font(20), fill=(120, 120, 130))
  px = 1210; d.rounded_rectangle((px, 80, W - 24, 560), radius=14, fill=(22, 23, 28), outline=(45, 46, 54), width=2)
  pnl = (CHART['entry'] - CHART['exit']) * 2 * CHART['qty']
  lines = [('Position closed', ''), ('Side', CHART['side']), ('Qty', str(CHART['qty'])), ('Avg entry', '%.2f' % CHART['entry']), ('Avg exit', '%.2f' % CHART['exit']),
           ('Opened', CHART['in']), ('Closed', CHART['out']), ('Net P&L', '+$%.2f' % pnl)]
  for k, (a, b) in enumerate(lines):
    yy = 104 + k * 56
    d.text((px + 22, yy), a, font=font(24, k == 0), fill=(235, 235, 240) if k == 0 else (150, 150, 160))
    if b: d.text((W - 48 - d.textlength(b, font=font(24, True)), yy), b, font=font(24, True), fill=(90, 200, 120) if a == 'Net P&L' else (230, 230, 235))
  im.save(path)
  return {'source_type': 'chart', 'platform_guess': 'other', 'timezone_shown': 'ET', 'date_shown': '10/15/2026', 'account_label': None,
          'rows': [{'symbol': CHART['symbol'], 'side': 'short', 'qty': CHART['qty'], 'price': None, 'entry_price': CHART['entry'], 'exit_price': CHART['exit'],
                    'datetime': None, 'entry_time': '10/15/2026 ' + CHART['in'] + ':05', 'exit_time': '10/15/2026 ' + CHART['out'] + ':40', 'pnl_shown': pnl, 'commission_shown': None, 'confidence': 0.93}]}

if __name__ == '__main__':
  out = sys.argv[1]; os.makedirs(out, exist_ok=True)
  r = {'trades': trades_png(os.path.join(out, 'trades.png')), 'chart': chart_png(os.path.join(out, 'chart.png'))}
  json.dump(r, open(os.path.join(out, 'readings.json'), 'w'), indent=1)
  print('ok', out)
