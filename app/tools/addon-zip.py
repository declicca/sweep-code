"""Sweep — the NinjaTrader 8 add-on's import file: sync/addon/SweepSync.cs → sync/addon/SweepSync.zip
(NinjaTrader: Tools > Import > NinjaScript Add-On). Same source → same bytes (fixed dates), so the zip only changes with the code.
   python3 -I tools/addon-zip.py
   python3 -I tools/addon-zip.py --plan OUT.zip   # (Plan Sync, step 4) the same, plus the Sweep Plan indicator, to OUT.zip
Layout of a NinjaScript archive: Info.xml at the root (the NinjaTrader version it was made for), each source in its folder
(AddOns/, Indicators/). Info.xml says 8.1.0.0 so that every NinjaTrader 8.1 accepts it. If an import is refused, the reference is
a zip exported by NinjaTrader itself (Tools > Export > NinjaScript Add-On) from the same files.
--plan adds Indicators/SweepPlan.cs (sync/addon/ninjatrader-plan) and AddOns/SweepPlanCore.cs (the logic shared with Quantower,
sync/addon/plan/PlanCore.cs). It is not the served zip until Mateo has tried it in NinjaTrader 8 (a source NinjaTrader cannot
compile would stop the import of Sweep Sync too); then it becomes SweepSync.zip: python3 -I tools/addon-zip.py --plan sync/addon/SweepSync.zip"""
import os, sys, zipfile
APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADDON = os.path.join(APP, 'sync', 'addon')
OUT = os.path.join(ADDON, 'SweepSync.zip')
INFO = '<?xml version="1.0" encoding="utf-8"?>\r\n<NinjaTrader>\r\n  <Export>\r\n    <Version>8.1.0.0</Version>\r\n  </Export>\r\n</NinjaTrader>\r\n'
SYNC = [('AddOns/SweepSync.cs', 'SweepSync.cs')]
PLAN = [('AddOns/SweepPlanCore.cs', os.path.join('plan', 'PlanCore.cs')), ('Indicators/SweepPlan.cs', os.path.join('ninjatrader-plan', 'SweepPlan.cs'))]

def build(out, files):
  tmp = out + '.tmp'
  with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as z:
    entries = [('Info.xml', INFO.encode('utf-8'))]
    for name, src in files:   # Windows line endings, as NinjaTrader writes them
      entries.append((name, open(os.path.join(ADDON, src), 'rb').read().replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')))
    for name, data in entries:
      zi = zipfile.ZipInfo(name, date_time=(2026, 10, 12, 0, 0, 0)); zi.compress_type = zipfile.ZIP_DEFLATED; zi.external_attr = 0o644 << 16
      z.writestr(zi, data)
  os.replace(tmp, out)
  print('%s (%d bytes)' % (os.path.relpath(out, APP) if out.startswith(APP) else out, os.path.getsize(out)))

if __name__ == '__main__':
  if len(sys.argv) == 3 and sys.argv[1] == '--plan': build(os.path.abspath(sys.argv[2]), SYNC + PLAN)
  else: build(OUT, SYNC)
