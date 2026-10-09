"""Subsets Geist and Geist Mono (tools/fonts-src → assets/fonts): Latin, Latin-1, Latin Extended-A, punctuation, currency,
   plus every character found in the app's own code and data (EN/FR/ES). Drops Cyrillic and unused symbols (−45 %).
   A character outside the subset (rare, typed by a trader) shows in the system font. Needs fonttools + brotli.
   python3 -I tools/subset-fonts.py   (from the app folder)"""
import glob, os, re
from fontTools.ttLib import TTFont
from fontTools import subset
txt = ''
for f in glob.glob('src/*.js') + glob.glob('src/*.css') + glob.glob('assets/*.js') + ['app.html', 'auth.html'] + glob.glob('*.php') + glob.glob('*/*.php') + glob.glob('*.json') + glob.glob('presets/*.json'):
    txt += open(f, encoding='utf-8', errors='ignore').read()
txt += ''.join(chr(int(h, 16)) for h in re.findall(r'\\u([0-9a-fA-F]{4})', txt))
used = {ord(c) for c in txt}
base = set(range(0x20, 0x7F)) | set(range(0xA0, 0x180)) | set(range(0x2000, 0x2070)) | set(range(0x20A0, 0x20C1)) | {0x2122, 0x2190, 0x2191, 0x2192, 0x2193, 0x2212, 0x2264, 0x2265, 0x00D7, 0x2026}
for name in ['Geist-Variable', 'GeistMono-Variable']:
    src, dst = 'tools/fonts-src/%s.woff2' % name, 'assets/fonts/%s.woff2' % name
    keep = [u for u in TTFont(src).getBestCmap() if u in base or u in used]
    o = subset.Options(); o.flavor = 'woff2'; o.layout_features = ['*']; o.name_IDs = ['*']; o.notdef_outline = True; o.hinting = True
    f = TTFont(src); s = subset.Subsetter(o); s.populate(unicodes=keep); s.subset(f); f.flavor = 'woff2'; f.save(dst)
    print(name, os.path.getsize(src), '->', os.path.getsize(dst), 'bytes,', len(keep), 'characters')
