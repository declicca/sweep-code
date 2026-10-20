"""Sweep — the 90-day gameplan's texts, from the site into the app (20 Oct.): python3 -I tools/gameplan-data.py
Reads website/src/pages21.py (Mateo's three « Learning Edition » PDFs, EN / FR / ES), writes the data into src/gameplan.js
(between /*@data*/ and /*@end*/) and the XP / checks / gates of the 90 missions into game/gameplan.php (GP_MISSIONS).
Run it again whenever the site's gameplan changes, then sh tools/build.sh."""
import json, os, re, sys
APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(os.path.dirname(APP), 'website', 'src', 'pages21.py')
def T(en, fr, es): return {"en": en, "fr": fr, "es": es}
class Any:   # whatever the page builders need at import time
    def __getattr__(self, k): return Any()
    def __call__(self, *a, **k): return Any()
    def __getitem__(self, k): return Any()
    def __setitem__(self, k, v): pass
    def __iter__(self): return iter([])
    def __add__(self, o): return o
    def __radd__(self, o): return o
class NS(dict):
    def __missing__(self, k):
        import builtins
        return getattr(builtins, k) if hasattr(builtins, k) else Any()
ns = NS(T=T, CRUMBS={}, __name__='p21')
exec(compile(open(SRC, encoding='utf-8').read().replace('from core import *', ''), SRC, 'exec'), ns)
d = {k: v for k, v in ns.items() if k.isupper() and not callable(v) and isinstance(v, (list, dict, tuple))}
d = json.loads(json.dumps(d))
J_DONE, ZERO, RECAP = d['J_DONE']['en'], d['ZERO']['en'], d['RECAP_DONE']['en']
# the learning block shown with a mission (week index across the 12, day index in the week)
LEARN = {
  (0, 0): ['RULES_1_8', 'TRACKS'], (0, 2): ['VOCAB'], (0, 1): ['M1_JOURNAL'],
  (1, 0): ['SETUP'], (1, 1): ['SPECS'], (1, 2): ['ROUTINE'],
  (3, 8): ['M1_GATE'],
  (4, 0): ['M2_NEW', 'M2_SAME'], (4, 1): ['TAGS', 'M2_JOURNAL'], (4, 6): ['RULE_9'],
  (5, 1): ['RULE_10'], (5, 3): ['PATTERN'], (5, 4): ['REFINE_RULES', 'REFINE_EX'],
  (7, 8): ['M2_GATE'],
  (8, 0): ['M3_NEW', 'M3_SAME'], (8, 1): ['ARENA', 'RULE_1_M3'], (8, 2): ['EVAL_MATH'],
  (9, 1): ['LADDER'], (9, 2): ['STEP_DOWN'], (10, 2): ['PLAYBOOK'], (11, 2): ['PLAN_FIELDS'],
  (11, 8): ['M3_GATE'],
}
def auto(w, i, done_en, title_en):
  if (w, i) == (0, 0): return 'account'
  if (w, i) == (0, 1): return 'trade'
  if (w, i) == (7, 0): return 'limits'
  if done_en == RECAP: return 'weekly'
  if done_en == ZERO: return 'zero'
  if done_en == J_DONE: return 'journal'
  return ''
missions, weeks, n = [], [], 0
for mi, key in enumerate(['M1_WEEKS', 'M2_WEEKS', 'M3_WEEKS']):
  for wk in d[key]:
    wi = len(weeks)
    weeks.append({'m': mi, 't': wk[0], 'g': wk[1], 'from': n + 1, 'to': n + len(wk[2])})
    for i, (k, mk, mins, t, desc, done) in enumerate(wk[2]):
      n += 1
      x = {'n': n, 'w': wi, 'k': k, 'mk': mk, 'min': mins, 't': t, 'd': desc, 'done': done}
      a = auto(wi, i, done['en'], t['en'])
      if a: x['a'] = a
      if (wi, i) in LEARN: x['learn'] = LEARN[(wi, i)]
      if 'gate' in t['en'].lower() and i == len(wk[2]) - 1: x['gate'] = mi + 1
      missions.append(x)
assert n == 90, n
blocks = {k: d[k] for k in sorted({b for v in LEARN.values() for b in v})}
data = {'months': [{'name': d['NAMES'][i], 'span': d['SPANS'][i], 'gate': d['GATES'][i]} for i in range(3)],
        'weeks': weeks, 'missions': missions, 'blocks': blocks,
        'words': {k: d[k] for k in ('KIND', 'MKT', 'DONE', 'DAY', 'WD', 'DISCLAIM', 'NEW')}, 'how': d['M1_HOW']}
js = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
JS = js
php = '[' + ','.join(f"{m['n']}=>[{m['min']},'{m.get('a','')}',{m.get('gate',0)}]" for m in missions) + ']'
PHP = php

p = os.path.join(APP, 'src', 'gameplan.js'); s = open(p, encoding='utf-8').read()
s2 = re.sub(r'/\*@data\*/.*?/\*@end\*/', lambda m: '/*@data*/' + JS + '/*@end*/', s, count=1, flags=re.S)
assert s2 != s or JS in s, 'no /*@data*/ marker in src/gameplan.js'
open(p, 'w', encoding='utf-8').write(s2)
p = os.path.join(APP, 'game', 'gameplan.php'); s = open(p, encoding='utf-8').read()
s2 = re.sub(r'const GP_MISSIONS = \[.*?\];', lambda m: 'const GP_MISSIONS = ' + PHP + ';', s, count=1, flags=re.S)
open(p, 'w', encoding='utf-8').write(s2)
print(f"{len(missions)} missions ({sum(1 for m in missions if 'a' in m)} checked by Sweep, gates on {[m['n'] for m in missions if 'gate' in m]}), {len(JS)} bytes of texts")
