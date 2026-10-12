"""Sweep — the NinjaTrader 8 add-on's import file: sync/addon/SweepSync.cs → sync/addon/SweepSync.zip
(NinjaTrader: Tools > Import > NinjaScript Add-On). Same source → same bytes (fixed dates), so the zip only changes with the code.
   python3 -I tools/addon-zip.py
Layout of a NinjaScript archive: Info.xml at the root (the NinjaTrader version it was made for), the source in its folder
(AddOns/). Info.xml says 8.1.0.0 so that every NinjaTrader 8.1 accepts it. If an import is refused, the reference is a zip
exported by NinjaTrader itself (Tools > Export > NinjaScript Add-On) from the same SweepSync.cs."""
import os, zipfile
APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(APP, 'sync', 'addon', 'SweepSync.cs'); OUT = os.path.join(APP, 'sync', 'addon', 'SweepSync.zip')
INFO = '<?xml version="1.0" encoding="utf-8"?>\r\n<NinjaTrader>\r\n  <Export>\r\n    <Version>8.1.0.0</Version>\r\n  </Export>\r\n</NinjaTrader>\r\n'
code = open(SRC, 'rb').read().replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')   # Windows line endings, as NinjaTrader writes them
tmp = OUT + '.tmp'
with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as z:
  for name, data in [('Info.xml', INFO.encode('utf-8')), ('AddOns/SweepSync.cs', code)]:
    zi = zipfile.ZipInfo(name, date_time=(2026, 10, 12, 0, 0, 0)); zi.compress_type = zipfile.ZIP_DEFLATED; zi.external_attr = 0o644 << 16
    z.writestr(zi, data)
os.replace(tmp, OUT)
print('%s (%d bytes)' % (os.path.relpath(OUT, APP), os.path.getsize(OUT)))
