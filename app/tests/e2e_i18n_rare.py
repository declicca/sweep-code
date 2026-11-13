"""
Sweep — toasts, errors and rare states in French and Spanish (13 Nov., the hunt), dev environment:
  python3 tests/e2e_i18n_rare.py http://127.0.0.1:8095 /tmp/show_state.json
These never show in a normal visit, so e2e_no_english_in_fr_es could not see them: a save that fails, a screenshot that does
not upload, « Saving… », a trade or an account that no longer exists, a file with no closed trade, the empty groups of Stats.
Each is produced on purpose and read on screen: no English left in FR and ES, and English unchanged.
"""
import sys
from playwright.sync_api import sync_playwright
B = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8095'
STATE = sys.argv[2] if len(sys.argv) > 2 else '/tmp/show_state.json'
fails = 0
def ok(c, what):
  global fails
  fails += (not c); print(('ok   ' if c else 'FAIL ') + what)
X = {
  'fr': {'save': 'Enregistrement impossible : enregistrement trop volumineux', 'save500': 'Enregistrement impossible : erreur du serveur 500', 'quota': 'Stockage plein : supprime des enregistrements pour en ajouter.',
         'up': 'Échec du téléversement : ton espace de captures est plein', 'up2': 'Échec du téléversement', 'shot1': 'Capture ajoutée', 'shot3': '3 captures ajoutées', 'saving': 'Enregistrement…',
         'trade': 'Ce trade n’existe plus.', 'account': 'Compte introuvable.', 'imp': 'Aucun trade fermé dans ce fichier.', 'tr': ['Sans setup', 'Sans tag', 'Aucune règle enfreinte sur cette période.', 'Aucune note pour l’instant.']},
  'es': {'save': 'No se pudo guardar: registro demasiado grande', 'save500': 'No se pudo guardar: error del servidor 500', 'quota': 'Almacenamiento lleno: elimina registros para añadir más.',
         'up': 'Error al subir: tu espacio de capturas está lleno', 'up2': 'Error al subir', 'shot1': 'Captura añadida', 'shot3': '3 capturas añadidas', 'saving': 'Guardando…',
         'trade': 'Esta operación ya no existe.', 'account': 'Cuenta no encontrada.', 'imp': 'Ninguna operación cerrada en este archivo.', 'tr': ['Sin setup', 'Sin etiqueta', 'Ninguna regla incumplida en este período.', 'Ninguna nota por ahora.']},
  'en': {'save': 'Could not save: record too large', 'save500': 'Could not save: server error 500', 'quota': 'Storage is full — delete some records to add more.',
         'up': 'Upload failed: your screenshot storage is full', 'up2': 'Upload failed', 'shot1': 'Screenshot added', 'shot3': '3 screenshots added', 'saving': 'Saving…',
         'trade': 'This trade no longer exists.', 'account': 'Account not found.', 'imp': 'No closed trades found in this file.', 'tr': ['No setup', 'No tag', 'No rule violations recorded in this period.', 'No ratings recorded yet.']},
}
with sync_playwright() as p:
  br = p.chromium.launch()
  for lang, w, h in (('fr', 390, 844), ('es', 1300, 850), ('en', 1300, 850)):
    ctx = br.new_context(storage_state=STATE, viewport={'width': w, 'height': h}, has_touch=w < 500, is_mobile=w < 500, locale='fr-CA')
    ctx.add_init_script("sessionStorage.setItem('sw.modal','1'); localStorage.setItem('tj.lang', JSON.stringify('%s'))" % lang)
    pg = ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:150])); pg.goto(B + '/#dashboard'); pg.wait_for_selector('#main', timeout=20000); pg.wait_for_timeout(2500)
    def toast(js):
      pg.evaluate(js); pg.wait_for_timeout(350); return pg.evaluate("document.getElementById('toast').textContent")
    got = {'save': toast("toast(saveErr(new Error('record too large')))"), 'save500': toast("toast(saveErr(new Error('server error 500')))"), 'quota': toast("toast(saveErr({code:'quota_exceeded'}))"),
           'up': toast("toast('Upload failed: ' + tr('your screenshot storage is full'))"), 'up2': toast("toast('Upload failed')"), 'shot1': toast("toast('Screenshot added')"), 'shot3': toast("toast('3 screenshots added')")}
    pg.evaluate("setSaving(1)"); pg.wait_for_timeout(300); got['saving'] = pg.evaluate("(document.getElementById('saving')||{}).textContent"); pg.evaluate("setSaving(-1)")
    pg.evaluate("location.hash='#trade/nope-nope'"); pg.wait_for_timeout(1200); got['trade'] = pg.evaluate("document.getElementById('main').innerText.trim()")
    pg.evaluate("location.hash='#account/nope-nope'"); pg.wait_for_timeout(1200); got['account'] = pg.evaluate("document.getElementById('main').innerText.trim()")
    pg.evaluate("location.hash='#import'"); pg.wait_for_timeout(900); pg.evaluate("IMP.err='No closed trades found in this file.'; IMP.file='x.csv'; IMP.rows=null; render()"); pg.wait_for_timeout(700)
    got['imp'] = pg.evaluate("document.getElementById('main').innerText")
    pg.evaluate("IMP.err=''; IMP.file=''; render()")
    got['tr'] = pg.evaluate("[tr('No setup'), tr('No tag'), tr('No rule violations recorded in this period.'), tr('No ratings recorded yet.')]")
    for k, want in X[lang].items():
      g = got[k]
      ok(g == want if k not in ('trade', 'account', 'imp') else want in g, f'{lang} {k}: « {str(g)[:90]} »')
    ok(not errs, f'{lang} no page error ({errs[:2]})')
    ctx.close()
  br.close()
print(f'{fails} failed' if fails else 'all passed')
sys.exit(1 if fails else 0)
