"""
Sweep — the site's captures: 1-minute bars of NQ for each of Alex's days (drawn, not market data), so the trade charts show
his entries and exits where they happened: the price goes through each entry at its time and each exit at its time.
Written in the chart's own cache format (chart/chart.php: <dir>/1m/NQ/<day>.json.gz, bars [t, o, h, l, c, v]).
  python3 tools/site-shots/bars.py <cache_dir>
"""
import datetime as dt, gzip, json, os, random, sys
from zoneinfo import ZoneInfo
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import data
NY = ZoneInfo('America/New_York')

def epoch(day, hm): return int(dt.datetime.fromisoformat(day + 'T' + hm).replace(tzinfo=NY).timestamp())

def main(out):
  d = data.build('en'); R = random.Random(5)
  by = {}
  for t in d['trades']:
    by.setdefault(t['date'], {})[t['entry_time']] = t
  os.makedirs(os.path.join(out, '1m', 'NQ'), exist_ok=True)
  for day, ts in by.items():
    start = int((dt.datetime.fromisoformat(day + 'T17:00').replace(tzinfo=NY) - dt.timedelta(days=1) + dt.timedelta(hours=1)).timestamp())
    end = epoch(day, '17:00')
    first = min(ts.values(), key=lambda t: t['entry_time'])
    anchors = [(start, first['entry'] + R.uniform(-60, 60))]
    for t in sorted(ts.values(), key=lambda t: t['entry_time']):
      anchors += [(epoch(day, t['entry_time']), t['entry']), (epoch(day, t['exit_time']), t['exit'])]
    anchors.append((end, anchors[-1][1] + R.uniform(-40, 40)))
    anchors = sorted({a[0]: a for a in anchors}.values())
    closes = {}
    for (t0, p0), (t1, p1) in zip(anchors, anchors[1:]):   # a Brownian bridge between anchors, about 2.5 points of noise a minute
      n = max(1, (t1 - t0) // 60); w = 0.0; walk = [0.0]
      for i in range(n): w += R.gauss(0, 2.6); walk.append(w)
      for i in range(n + 1):
        closes[t0 + 60 * i] = p0 + (p1 - p0) * i / n + walk[i] - walk[-1] * i / n
    bars = []; prev = None
    for t in sorted(closes):
      if t >= end: break
      c = round(closes[t] * 4) / 4; o = prev if prev is not None else c
      h = max(o, c) + round(abs(R.gauss(0, 1.8)) * 4) / 4; l = min(o, c) - round(abs(R.gauss(0, 1.8)) * 4) / 4
      v = int(abs(R.gauss(900, 400)) * (3 if epoch(day, '09:30') <= t < epoch(day, '11:30') else 1))
      bars.append([t, o, h, l, c, v]); prev = c
    with gzip.open(os.path.join(out, '1m', 'NQ', day + '.json.gz'), 'wt') as f:
      json.dump({'contract': 'NQZ6', 'tf': '1m', 'fetched_at': '2026-10-16T12:00:00Z', 'complete': True, 'bars': bars}, f)
  print('bars:', len(by), 'days in', out)

main(sys.argv[1] if len(sys.argv) > 1 else '/tmp/gs-bars')
