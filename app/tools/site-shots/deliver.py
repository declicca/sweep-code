"""
Sweep — the site's captures: check the new files against the ones they replace (same name, same exact size), then copy
them into website/static (images) and website/static/video (videos). The site's code is not touched; its smaller copies
(-600, -1200, -540, -960), the 720p, the WebM and the posters are made by the Site session.
  python3 tools/site-shots/deliver.py <out_dir> [--copy]
"""
import os, subprocess, sys
from PIL import Image
OUT = sys.argv[1]; COPY = '--copy' in sys.argv
SITE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'website', 'static')
NEW = {'ecran-connexions.webp', 'v6-26-connections-d.webp', 'mobile-fr-dark-economic-calendar-786.webp', 'mobile-es-dark-economic-calendar-786.webp',
       'desktop-fr-dark-economic-calendar-2400.webp', 'desktop-es-dark-economic-calendar-2400.webp'}
bad = 0; rows = []; todo = []
for root, _, files in os.walk(OUT):
  for f in sorted(files):
    if not (f.endswith('.webp') or f.endswith('.mp4')): continue
    src = os.path.join(root, f); rel = os.path.relpath(src, OUT)
    dst = os.path.join(SITE, 'img', rel) if rel.startswith('captures') else os.path.join(SITE, rel)   # captures/… → img/captures/…, img/… and video/… as they are
    have = os.path.exists(dst)
    if f.endswith('.webp'):
      w, h = Image.open(src).size
      if have:
        ow, oh = Image.open(dst).size
        ok = (w, h) == (ow, oh)
      else: ok = f in NEW; ow = oh = None
      rows.append(f"{'ok  ' if ok else 'BAD '} {rel:58s} {w}×{h}{'' if have else '  (new)'}{'' if ok or not have else f'  ≠ {ow}×{oh}'}  {os.path.getsize(src) // 1024} KB")
      bad += not ok
    else:
      p = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height,codec_name:format=duration', '-of', 'csv=p=0', src], capture_output=True, text=True).stdout.split()
      rows.append(f"ok   {rel:58s} {' '.join(p)}  {os.path.getsize(src) // 1024} KB")
    todo.append((src, dst))
if COPY and not bad:   # all or nothing
  for src, dst in todo: os.makedirs(os.path.dirname(dst), exist_ok=True); subprocess.run(['cp', src, dst], check=True)
print('\n'.join(rows)); print(f'{len(rows)} files, {bad} wrong' + (' — copied' if COPY and not bad else ''))
sys.exit(1 if bad else 0)
