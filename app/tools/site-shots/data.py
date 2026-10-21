"""
Sweep — the site's captures: Alex's data, written for the captures (seed.py sends them through the app's own bulkPut).
Same history in every language, his own words (notes, plans, reviews, setups) in the language of the capture.
A disciplined trader, two and a half months on 5 prop accounts (one copied trade on several accounts), no account
breached, 4 payouts received, one requested. Deterministic: random.Random(seed).
"""
import datetime as dt, os, random

HOLIDAYS = {'2026-09-07'}
SETUPS = {'en': ['Liquidity sweep', 'FVG retest', 'Opening range', 'Break & retest'],
          'fr': ['Liquidity sweep', 'Retest de FVG', 'Opening range', 'Cassure et retest'],
          'es': ['Liquidity sweep', 'Retest de FVG', 'Opening range', 'Ruptura y retest']}
FOCUS = {'en': ['Wait for the sweep of London before any entry.', 'One setup, one stop, no adding to a loser.', 'Two trades max, then I close the platform.',
                'Patience at the open: let the first 15 minutes print.', 'Size stays at plan, even after two wins.'],
         'fr': ['Attendre le sweep de Londres avant toute entrée.', 'Un setup, un stop, jamais de renfort sur un perdant.', 'Deux trades max, puis je ferme la plateforme.',
                'Patience à l’ouverture : je laisse passer les 15 premières minutes.', 'La taille reste celle du plan, même après deux gains.'],
         'es': ['Esperar el sweep de Londres antes de cualquier entrada.', 'Un setup, un stop, nunca añadir a una pérdida.', 'Dos operaciones como máximo y cierro la plataforma.',
                'Paciencia en la apertura: dejo pasar los primeros 15 minutos.', 'El tamaño sigue el plan, incluso después de dos ganancias.']}
WELL = {'en': ['Waited for my level and took the clean entry.', 'Stopped after my max trades, no forcing.', 'Respected the stop without moving it.', 'Took profit at the planned target.'],
        'fr': ['J’ai attendu mon niveau et pris l’entrée propre.', 'Arrêté après mon max de trades, sans forcer.', 'Stop respecté, sans le déplacer.', 'Profit pris à la cible prévue.'],
        'es': ['Esperé mi nivel y tomé la entrada limpia.', 'Paré tras mi máximo de operaciones, sin forzar.', 'Respeté el stop sin moverlo.', 'Tomé ganancias en el objetivo previsto.']}
WRONG = {'en': ['Entered a bit early on the second trade.', 'Hesitated on the best setup of the day.', 'Watched the chart too long after my last trade.'],
         'fr': ['Entré un peu tôt sur le deuxième trade.', 'J’ai hésité sur le meilleur setup de la journée.', 'Resté trop longtemps devant le graphique après mon dernier trade.'],
         'es': ['Entré un poco pronto en la segunda operación.', 'Dudé en el mejor setup del día.', 'Me quedé demasiado frente al gráfico tras mi última operación.']}
LESSON = {'en': ['The best trades come after the sweep, not before.', 'Fewer trades, better trades.', 'My stop is my plan: I never move it.'],
          'fr': ['Les meilleurs trades viennent après le sweep, pas avant.', 'Moins de trades, de meilleurs trades.', 'Mon stop, c’est mon plan : je ne le déplace jamais.'],
          'es': ['Las mejores operaciones llegan después del sweep, no antes.', 'Menos operaciones, mejores operaciones.', 'Mi stop es mi plan: nunca lo muevo.']}
TOMORROW = {'en': ['Same plan: wait for the London level.', 'Watch the 8:30 release, no trade before 9:45.', 'Two trades max.'],
            'fr': ['Même plan : attendre le niveau de Londres.', 'Annonce de 8 h 30 : aucun trade avant 9 h 45.', 'Deux trades max.'],
            'es': ['Mismo plan: esperar el nivel de Londres.', 'Dato de las 8:30: ninguna operación antes de las 9:45.', 'Dos operaciones como máximo.']}
NOTE = {'en': ['Swept the London low, reclaimed it, entry on the retest.', 'Clean FVG fill, stop under the wick.', 'Opening range break, held the retest.', 'Took the planned target, no greed.'],
        'fr': ['Sweep du bas de Londres, reprise, entrée sur le retest.', 'FVG comblé proprement, stop sous la mèche.', 'Cassure de l’opening range, le retest a tenu.', 'Cible prévue prise, sans gourmandise.'],
        'es': ['Sweep del mínimo de Londres, recuperado, entrada en el retest.', 'FVG cubierto limpio, stop bajo la mecha.', 'Ruptura del opening range, el retest aguantó.', 'Objetivo previsto tomado, sin codicia.']}
EMO_OK = ['Calm', 'Focused', 'Patient', 'Confident']

# id, firm, preset, name, created_on, instrument, contracts
ACCOUNTS = [
  ('a1', 'topstep', 'topstep|combine|150000|eval', 'Combine 150K', '2026-09-28', 'NQ', 1),
  ('a2', 'topstep', 'topstep|combine|50000|funded', 'XFA 50K', '2026-08-17', 'MNQ', 4),
  ('a3', 'lucid', 'lucid|lucidflex|50000|funded', 'Flex 50K', '2026-08-03', 'MNQ', 4),
  ('a4', 'apex', 'apex|apex-eod|50000|funded', 'PA 50K', '2026-07-27', 'MNQ', 4),
  ('a5', 'topstep', 'topstep|combine|50000|live', 'Live 50K', '2026-09-14', 'MNQ', 2),
]
FIRMS = [('f-topstep', 'Topstep'), ('f-lucid', 'Lucid Trading'), ('f-apex', 'Apex Trader Funding')]
PAYOUTS = [  # id, account, amount $, status, request, approval, payment
  ('p1', 'a4', 2000, 'paid', '2026-08-26', '2026-08-27', '2026-08-28'),
  ('p2', 'a3', 1800, 'paid', '2026-09-09', '2026-09-10', '2026-09-11'),
  ('p3', 'a4', 2500, 'paid', '2026-09-22', '2026-09-23', '2026-09-24'),
  ('p4', 'a2', 1500, 'paid', '2026-10-05', '2026-10-06', '2026-10-07'),
  ('p5', 'a3', 1200, 'requested', '2026-10-13', None, None),
]
EXPENSES = [  # id, firm, account, category, $, date
  ('e1', 'f-apex', 'a4', 'evaluation', 35, '2026-07-06'), ('e2', 'f-apex', 'a4', 'activation', 85, '2026-07-24'),
  ('e3', 'f-lucid', 'a3', 'evaluation', 80, '2026-07-13'), ('e4', 'f-topstep', 'a2', 'evaluation', 49, '2026-07-20'),
  ('e5', 'f-topstep', 'a2', 'reset', 49, '2026-08-03'), ('e6', 'f-topstep', 'a1', 'evaluation', 109, '2026-09-25'),
  ('e7', 'f-topstep', '', 'data', 39, '2026-08-01'), ('e8', 'f-topstep', '', 'data', 39, '2026-09-01'), ('e9', 'f-topstep', '', 'data', 39, '2026-10-01'),
]

def days(a, b):
  d = dt.date.fromisoformat(a); e = dt.date.fromisoformat(b)
  while d <= e:
    if d.weekday() < 5 and d.isoformat() not in HOLIDAYS: yield d.isoformat()
    d += dt.timedelta(days=1)

def hm(m): return '%02d:%02d' % (m // 60, m % 60)

def build(lang, today=None, seed=11, today_review=None):
  today = today or os.environ.get('SHOTS_NOW', '2026-10-15 11:05')[:10]
  if today_review is None: today_review = os.environ.get('SHOTS_NOW', '')[11:] >= '16:30'   # an evening capture: the day is reviewed
  R = random.Random(seed); T = random.Random(seed + 1)   # R: the market (same in every language), T: the words
  pick = lambda xs: xs[T.randrange(len(xs))]
  st = SETUPS[lang]
  trades, journals = [], []
  price = 24620.0
  for d in days('2026-07-27', today):
    price += R.uniform(-60, 75)
    n = R.choices([1, 2, 3], [.35, .45, .2])[0]
    bias = R.choice(['bullish', 'bullish', 'bearish', 'neutral'])
    if d == today: bias = 'bullish'
    slots = [R.randint(9 * 60 + 36, 10 * 60 + 8), R.randint(10 * 60 + 18, 11 * 60 + 25), R.randint(13 * 60 + 35, 14 * 60 + 25)][:n]
    if d == today: slots = [9 * 60 + 41, 10 * 60 + 22]
    plan_setups = st[:3] if R.random() < .7 else st
    day_trades = []
    revenge = False
    for k in range(len(slots)):
      t0 = slots[k]
      direction = 'long' if bias == 'bullish' else 'short' if bias == 'bearish' else R.choice(['long', 'short'])
      if d == today: direction = 'long'
      sgn = 1 if direction == 'long' else -1
      entry = round((price + R.uniform(-40, 40)) * 4) / 4
      stop_pts = R.choice([10, 12, 12.5, 14, 15, 16, 18])
      roll = R.random()
      rr = R.uniform(1.4, 2.3) if roll < .53 else (0.15 if roll < .6 else -1.0 if roll < .92 else -0.6)
      if d == today: rr = [2.1, 1.0][k]
      exit_ = round((entry + sgn * rr * stop_pts) * 4) / 4
      setup = R.choice(plan_setups[:3])
      dur = R.randint(4, 26)
      # the last 4 weeks: after a loss, he sometimes jumps right back in (the habit Sweep's boss « The Revenge » is made of)
      quick = rr < 0 and k + 1 < len(slots) and '2026-09-17' <= d < today and R.random() < .55
      if quick: slots[k + 1] = t0 + dur + R.randint(3, 8)
      gid = 'g-%s-%d' % (d, k)
      bad = (R.random() < .1) and d != today
      disc = {q: 'y' for q in ('plan', 'size', 'risk', 'stop', 'widen', 'addloser', 'revenge', 'chase', 'dll', 'emotion', 'exit', 'confirm', 'entry')}
      if bad: disc[R.choice(['confirm', 'entry', 'exit', 'chase'])] = 'n'
      if revenge: disc['revenge'] = 'n'
      for aid, firm, preset, name, created, inst, ctr in ACCOUNTS:
        if d < created: continue
        if aid == 'a5' and R.random() < .35: continue
        if aid == 'a1' and d >= '2026-10-16': continue   # the evaluation stays just short of its target (no « You passed » on top of Friday's recap)
        trades.append({'id': 't-%s-%d-%s' % (d, k, aid), 'instrument': inst, 'account_id': aid, 'date': d, 'session_date': True,
          'entry_time': hm(t0), 'exit_time': hm(t0 + dur), 'session': 'nyam' if t0 < 12 * 60 else 'nypm', 'direction': direction,
          'contracts': ctr, 'entry': entry, 'exit': exit_, 'stop': entry - sgn * stop_pts, 'target': entry + sgn * 2 * stop_pts,
          'pnl_manual': False, 'fees_c': ctr * (420 if inst == 'NQ' else 124), 'setup': setup,
          'grade': 'A' if rr > 1 and not bad else 'B' if not bad else 'C', 'tags': [], 'copy_group': gid,
          'notes': NOTE[lang][st.index(setup)] if R.random() < .55 else '', 'review': {}, 'shots': [], 'discipline': dict(disc),
          'emo': {'before': [pick(EMO_OK)], 'after': [pick(EMO_OK)], 'confidence': 4, 'execution': 5 if not bad else 3, 'quality': 4},
          'news': [], 'news_min': None, 'news_near': None})
      day_trades.append(rr)
      revenge = quick
    saved = int(dt.datetime.fromisoformat(d + 'T08:45:00-04:00').timestamp())
    pre = {'bias': bias, 'focus': pick(FOCUS[lang]), 'max_loss': '600', 'max_trades': '3', 'setups': plan_setups, 'saved_at': saved}
    post = {}
    if d != today or today_review:
      post = {'well': pick(WELL[lang]), 'wrong': pick(WRONG[lang]) if T.random() < .5 else '', 'lesson': pick(LESSON[lang]), 'tomorrow': pick(TOMORROW[lang]),
              'grade': 'A' if sum(day_trades) > 1 else 'B', 'followed': 'yes'}
    journals.append({'id': d, 'date': d, 'pre': pre, 'post': post})
  accounts = [{'id': aid, 'firm_id': 'f-' + firm, 'name': name, 'preset': preset, 'status': 'active', 'created_on': created, 'notes': ''}
              for aid, firm, preset, name, created, inst, ctr in ACCOUNTS]
  firms = [{'id': i, 'name': n} for i, n in FIRMS]
  fid = {a[0]: 'f-' + a[1] for a in ACCOUNTS}
  payouts = [dict({'id': i, 'account_id': a, 'firm_id': fid[a], 'amount_c': v * 100, 'status': s, 'request_date': r},
                  **({'approval_date': ap} if ap else {}), **({'payment_date': pd} if pd else {})) for i, a, v, s, r, ap, pd in PAYOUTS]
  expenses = [{'id': i, 'firm_id': f, 'account_id': a, 'category': c, 'amount_c': v * 100, 'date': d, 'notes': ''} for i, f, a, c, v, d in EXPENSES]
  return {'firms': firms, 'accounts': accounts, 'trades': trades, 'journals': journals, 'payouts': payouts, 'expenses': expenses}
