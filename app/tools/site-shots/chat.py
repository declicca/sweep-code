"""
Sweep — the site's captures: Ask Sweep's answer to « What is my best setup this month? », written from Alex's own trades
(data.py: the last 30 days, a copied trade counted once), in EN / FR / ES. Written to chat-ai.json, the stand-in that
serve.sh gives the server (SWEEP_AI_CHAT_MOCK): no call to Google.
  python3 tools/site-shots/chat.py
"""
import datetime as dt, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import data
HERE = os.path.dirname(os.path.abspath(__file__))

def stats(lang):
  d = data.build(lang); today = dt.date.fromisoformat(d['journals'][-1]['date']); since = (today - dt.timedelta(days=30)).isoformat()
  one = {}
  for t in d['trades']:
    if t['date'] >= since and t['account_id'] == 'a4': one[t['copy_group']] = t   # one account: each copied trade once
  by = {}
  for t in one.values():
    r = (t['exit'] - t['entry']) / abs(t['entry'] - t['stop']) * (1 if t['direction'] == 'long' else -1)
    by.setdefault(t['setup'], []).append(r)
  rows = sorted(((s, len(v), sum(1 for x in v if x > 0) / len(v), sum(v) / len(v)) for s, v in by.items() if len(v) >= 4), key=lambda x: -x[3])
  return rows, len(one)

def fmt(lang, x, d=1):
  s = ('%.' + str(d) + 'f') % x
  return s.replace('.', ',') if lang != 'en' else s

def main():
  rules = []
  for lang, match in (('en', 'best setup'), ('fr', 'meilleur setup'), ('es', 'mejor setup')):
    rows, n = stats(lang); (b, bn, bw, br), (w, wn, ww, wr) = rows[0], rows[-1]
    pct = lambda v: ('%d %%' if lang != 'en' else '%d%%') % round(v * 100)
    reply = {
      'en': f"Your best setup is {b}: {bn} trades, {pct(bw)} winners, +{fmt(lang, br, 2)}R on average. Your weakest is {w} ({wn} trades, {fmt(lang, wr, 2)}R on average). Keep {b} as your A setup and size {w} down until it proves itself again.",
      'fr': f"Ton meilleur setup est {b} : {bn} trades, {pct(bw)} de gagnants, +{fmt(lang, br, 2)} R en moyenne. Le plus faible est {w} ({wn} trades, {fmt(lang, wr, 2)} R en moyenne). Garde {b} comme setup A et réduis la taille sur {w} tant qu’il ne refait pas ses preuves.",
      'es': f"Tu mejor setup es {b}: {bn} operaciones, {pct(bw)} ganadoras, +{fmt(lang, br, 2)} R de media. El más débil es {w} ({wn} operaciones, {fmt(lang, wr, 2)} R de media). Mantén {b} como tu setup A y reduce el tamaño en {w} hasta que vuelva a demostrar su valor.",
    }[lang]
    fu = {'en': ['When do I trade it best?', 'Show my worst hours'], 'fr': ['À quelle heure il marche le mieux ?', 'Mes pires heures'], 'es': ['¿A qué hora funciona mejor?', 'Mis peores horas']}[lang]
    rules.append({'match': match, 'out': {'reply': reply, 'data': 'last_30_days', 'followups': fu}})
  base = json.load(open(os.path.join(os.path.dirname(HERE), '..', 'tests', 'samples', 'chat-ai-mock.json')))
  json.dump({'_': 'Ask Sweep for the site captures (written by chat.py).', 'rules': rules + base['rules'], 'default': base['default']},
            open(os.path.join(HERE, 'chat-ai.json'), 'w'), ensure_ascii=False, indent=1)
  print('chat-ai.json:', [r['out']['reply'][:70] for r in rules])

main()
