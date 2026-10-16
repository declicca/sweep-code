"""Share images (og:image, 1200×630) for the firm pages, comparisons, compared-rules guides and calculators, in EN, FR and ES.

Run from website/ with a Python that has Playwright (Chromium) installed:  python tools/og_images.py
The images go to static/social/og/<lang>/<page>.png, with static/social/og/manifest.json (the verification date each one shows).
build.py uses an image when it exists, and warns when a firm's rules were checked after its image was made: run this again then.
Development tool only: nothing here runs on the server."""
import asyncio, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "src")
OUT = os.path.join(HERE, "..", "static", "social", "og")
os.environ.setdefault("SWEEP_PRESETS_OFFLINE", "1")   # the copy of the app's catalogue the site was built with
sys.path.insert(0, SRC)
import core, presets, pages4, pages7, pages8, pages17, pages18, pages19  # noqa: E402
from core import T  # noqa: E402

LANGS = ("en", "fr", "es")
import base64  # noqa: E402
# the font travels inside the page (a generated page can't load a local file)
FONT = "data:font/woff2;base64," + base64.b64encode(open(os.path.join(HERE, "..", "static", "fonts", "Geist-Variable.woff2"), "rb").read()).decode()

def name_of(page):
    return page.replace(".html", "").replace("/", "-")

def entries():
    """(page, {lang: (title, subtitle)}, date shown or None)"""
    out = []
    for f in presets.FIRMS:
        name, when = f["name"], pages18.checked_of(f)
        out.append((pages18.page_of(f), {l: (T(f"{name} rules 2026", f"Règles {name} 2026", f"Reglas de {name} 2026")[l],
                                             T(f"Drawdown, consistency and payouts · Verified {pages18.day(when, 'en')}",
                                               f"Drawdown, consistance et payouts · Vérifiées le {pages18.day(when, 'fr')}",
                                               f"Drawdown, consistencia y payouts · Revisadas el {pages18.day(when, 'es')}")[l]) for l in LANGS}, when))
    for slug, name in pages8.FIRMS:
        if name in presets.PRESET_FIRMS: continue
        out.append((slug, {l: (T(f"{name} rules", f"Règles {name}", f"Reglas de {name}")[l],
                               T("Enter them once. Every trade is checked.", "Saisis-les une fois. Chaque trade est vérifié.", "Introdúcelas una vez. Cada operación se revisa.")[l]) for l in LANGS}, None))
    for c in pages17.VS:
        out.append((c["slug"], {l: (f"Sweep vs {c['name']}",
                                    T("Price, prop firm rules and features, side by side", "Prix, règles des prop firms et fonctions, côte à côte", "Precio, reglas de prop firms y funciones, lado a lado")[l]) for l in LANGS}, None))
    when = presets.CHECKED
    for page, title in ((pages19.GUIDE_CONS, T("Consistency rules, compared", "Règles de consistance, comparées", "Reglas de consistencia, comparadas")),
                        (pages19.GUIDE_DD, T("Drawdown rules, compared", "Règles de drawdown, comparées", "Reglas de drawdown, comparadas")),
                        (pages19.GUIDE_PAYOUT, T("Payout rules, compared", "Règles de payout, comparées", "Reglas de payout, comparadas")),
                        (pages19.GUIDE_SIZES, T("Account sizes and targets, compared", "Tailles de compte et objectifs, comparés", "Tamaños de cuenta y objetivos, comparados")),
                        (pages19.GUIDE_DAYS, T("Minimum trading days, compared", "Jours minimum, comparés", "Días mínimos, comparados")),
                        (pages19.GUIDE_COSTS, T("Prop firm costs, compared", "Coût des prop firms, comparé", "Costo de las prop firms, comparado"))):
        if page not in pages19.RULE_GUIDES: continue   # a guide not published yet
        out.append((page, {l: (title[l], T(f"{core.FIRMS_N} prop firms · Verified {pages18.day(when, 'en')}", f"{core.FIRMS_N} prop firms · Vérifiées le {pages18.day(when, 'fr')}",
                                           f"{core.FIRMS_N} prop firms · Revisadas el {pages18.day(when, 'es')}")[l]) for l in LANGS}, when))
    for page, title, sub in (   # the landing pages (audit n° 3, 2.1)
        ("free-trading-journal.html", T("Free trading journal", "Journal de trading gratuit", "Diario de trading gratis"),
         T("For futures and prop firm traders · Free forever", "Pour les traders de futures et de prop firms · Gratuit", "Para traders de futuros y prop firms · Gratis")),
        ("prop-firm-tracker.html", T("Prop firm tracker", "Suivi des comptes prop", "Seguimiento de cuentas prop"),
         T("Every account, its rules and where it stands", "Chaque compte, ses règles et où il en est", "Cada cuenta, sus reglas y cómo va")),
        ("payout-tracker.html", T("Payout tracker", "Suivi des payouts", "Seguimiento de payouts"),
         T("From request to paid, and your real net", "De la demande au paiement, et ton vrai net", "De la solicitud al pago, y tu neto real")),
        ("ninjatrader.html", T("NinjaTrader 8 → Sweep", "NinjaTrader 8 → Sweep", "NinjaTrader 8 → Sweep"),
         T("Free add-on: your trades arrive on their own", "Module gratuit : tes trades arrivent tout seuls", "Complemento gratis: tus operaciones llegan solas"))):
        out.append((page, {l: (title[l], sub[l]) for l in LANGS}, None))
    pro = pages4.PRICES["pro"]["m"]
    for page, title, sub, day in (   # the key pages of the SEO brief (Oct 15): comparison, pricing, features, rules hub, rule changes
        ("best-trading-journal-for-prop-firms.html", T("Best trading journal for prop firms (2026)", "Meilleur journal de trading pour prop firms (2026)", "Mejor diario de trading para prop firms (2026)"),
         T("Sweep, TradeZella, Tradervue, TraderSync and Edgewonk, compared", "Sweep, TradeZella, Tradervue, TraderSync et Edgewonk, comparés", "Sweep, TradeZella, Tradervue, TraderSync y Edgewonk, comparados"), None),
        ("pricing.html", T("Pricing", "Tarifs", "Precios"),
         T(f"Free forever · Pro from ${pro}/mo", f"Gratuit pour toujours · Pro dès {pro} $/mois", f"Gratis para siempre · Pro desde {pro} $/mes"), None),
        ("features.html", T("Trading journal features", "Fonctionnalités du journal de trading", "Funciones del diario de trading"),
         T("Logging, charts, prop firm rules, payouts, discipline and AI", "Saisie, graphiques, règles des prop firms, payouts, discipline et IA", "Registro, gráficos, reglas de prop firms, payouts, disciplina e IA"), None),
        ("prop-firms/index.html", T("Prop firm rules 2026", "Règles des prop firms 2026", "Reglas de las prop firms 2026"),
         T(f"{core.FIRMS_N} futures prop firms · Verified {pages18.day(when, 'en')}", f"{core.FIRMS_N} prop firms de futures · Vérifiées le {pages18.day(when, 'fr')}",
           f"{core.FIRMS_N} prop firms de futuros · Revisadas el {pages18.day(when, 'es')}"), when),
        ("prop-firm-rule-changes.html", T("Prop firm rule changes", "Changements de règles des prop firms", "Cambios de reglas de las prop firms"),
         T("Every change found on the firms’ official pages, dated", "Chaque changement trouvé sur les pages officielles des firmes, daté", "Cada cambio encontrado en las páginas oficiales de las firmas, fechado"), None)):
        out.append((page, {l: (title[l], sub[l]) for l in LANGS}, day))
    for slug, _, name, _ in pages7.TOOLS:
        out.append((slug, {l: (name[l], T("Free calculator for futures and prop traders", "Calculateur gratuit pour traders de futures et de prop firms", "Calculadora gratis para traders de futuros y prop firms")[l]) for l in LANGS}, None))
    return out

def html_of(title, sub):
    esc = lambda s: s.replace("&", "&amp;").replace("<", "&lt;")
    return f'''<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{{font-family:Geist;src:url("{FONT}") format("woff2");font-weight:100 900}}
*{{margin:0;box-sizing:border-box}}
:root{{--gain:#4C8DFF}}
body{{width:1200px;height:630px;overflow:hidden;font-family:Geist,sans-serif;color:#F2F2F3;
 background:radial-gradient(60% 70% at 8% 0%,rgba(76,141,255,.20),transparent 60%),radial-gradient(45% 55% at 100% 100%,rgba(212,162,76,.10),transparent 60%),#08080A}}
.wrap{{position:absolute;inset:0;padding:72px 80px;display:flex;flex-direction:column}}
.brand{{display:flex;align-items:center;gap:12px;font-size:34px;font-weight:500;letter-spacing:-.02em}}
.brand svg{{height:44px;width:auto;color:#F2F2F3}}
h1{{margin-top:auto;font-size:76px;line-height:1.04;font-weight:600;letter-spacing:-.035em;max-width:1000px}}
p{{margin-top:26px;font-size:30px;color:#9A9AA2;letter-spacing:-.01em}}
.url{{margin-top:auto;font-size:28px;color:#4C8DFF;font-weight:500}}
</style></head><body><div class="wrap"><div class="brand">{core.MARK}<span>sweep</span></div>
<h1>{esc(title)}</h1><p>{esc(sub)}</p><div class="url">makeitsweep.com</div></div></body></html>'''

async def main():
    from playwright.async_api import async_playwright
    manifest = {}
    async with async_playwright() as p:
        br = await p.chromium.launch(channel="chrome")
        pg = await br.new_page(viewport={"width": 1200, "height": 630}, device_scale_factor=1)
        for page, texts, when in entries():
            for l in LANGS:
                title, sub = texts[l]
                await pg.set_content(html_of(title, sub)); await pg.evaluate("document.fonts.ready")
                os.makedirs(os.path.join(OUT, l), exist_ok=True)
                await pg.screenshot(path=os.path.join(OUT, l, name_of(page) + ".png"))
                manifest.setdefault(page, {})[l] = {"alt": f"{title} · {sub}", "date": when}
        await br.close()
    json.dump(manifest, open(os.path.join(OUT, "manifest.json"), "w"), ensure_ascii=False, indent=1)
    print(f"{sum(len(v) for v in manifest.values())} share images in static/social/og/")

if __name__ == "__main__":
    asyncio.run(main())
