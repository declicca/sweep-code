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
import core, presets, pages4, pages7, pages8, pages11, pages12, pages13, pages17, pages18, pages19  # noqa: E402
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
        ("trading-journal-guide.html", T("How to keep a trading journal", "Tenir un journal de trading", "Cómo llevar un diario de trading"),
         T("The complete guide: what to record, the numbers, the review", "Le guide complet : quoi noter, les chiffres, la revue", "La guía completa: qué anotar, las cifras, la revisión")),
        ("ninjatrader.html", T("NinjaTrader 8 → Sweep", "NinjaTrader 8 → Sweep", "NinjaTrader 8 → Sweep"),
         T("Free add-on: your trades arrive on their own", "Module gratuit : tes trades arrivent tout seuls", "Complemento gratis: tus operaciones llegan solas")),
        ("quantower.html", T("Quantower → Sweep", "Quantower → Sweep", "Quantower → Sweep"),
         T("Free add-on: your trades arrive on their own", "Module gratuit : tes trades arrivent tout seuls", "Complemento gratis: tus operaciones llegan solas")),
        ("how-to-start-prop-firm-trading.html", T("How to start prop firm trading", "Débuter en prop firm", "Empezar en prop firms"),
         T("The free 90-day gameplan", "Le plan gratuit de 90 jours", "El plan gratis de 90 días")),
        ("prop-firm-gameplan-month-1.html", T("Month 1 · Foundation", "Mois 1 · Fondations", "Mes 1 · Cimientos"),
         T("Protect first, then execute", "Protège d’abord, exécute ensuite", "Primero protege, luego ejecuta")),
        ("prop-firm-gameplan-month-2.html", T("Month 2 · Consistency", "Mois 2 · Constance", "Mes 2 · Constancia"),
         T("Same setup, now measure it", "Même setup, maintenant on mesure", "Mismo setup, ahora mídelo")),
        ("prop-firm-gameplan-month-3.html", T("Month 3 · Prove it", "Mois 3 · Fais tes preuves", "Mes 3 · Demuéstralo"),
         T("Real rules, earned size", "Vraies règles, taille méritée", "Reglas reales, tamaño ganado")),
        ("pass-prop-firm-evaluation.html", T("How to pass a prop firm evaluation", "Réussir une évaluation prop firm", "Aprobar una evaluación de prop firm"),
         T("A plan, not speed", "Un plan, pas de la vitesse", "Un plan, no velocidad")),
        ("prop-firm-position-sizing.html", T("When to size up", "Quand augmenter sa taille", "Cuándo subir el tamaño"),
         T("Up slowly, down instantly", "Monter lentement, redescendre tout de suite", "Subir despacio, bajar al instante")),
        ("funded-account-playbook.html", T("Funded account playbook", "Playbook du compte financé", "Playbook de la cuenta financiada"),
         T("Five rules after you pass", "Cinq règles après la réussite", "Cinco reglas tras aprobar")),
        ("liquidity-sweep.html", T("What is a liquidity sweep?", "Qu’est-ce qu’un liquidity sweep ?", "¿Qué es un liquidity sweep?"),
         T("And how to journal it", "Et comment le journaliser", "Y cómo registrarlo")),
        ("mes-vs-mnq.html", T("MES or MNQ?", "MES ou MNQ ?", "¿MES o MNQ?"),
         T("Which micro to start with", "Quel micro pour débuter", "Con qué micro empezar"))):
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
    byid = {f["id"]: f for f in presets.FIRMS}
    for x, y in pages19.FIRM_VS:   # firm vs firm (SEO brief, step 4)
        a_, b_ = pages19.SHORT[x], pages19.SHORT[y]
        out.append((pages19.vs_page_of(byid[x], byid[y]), {l: (f"{a_} vs {b_}", T(f"Rules compared · Verified {pages18.day(when, 'en')}", f"Règles comparées · Vérifiées le {pages18.day(when, 'fr')}",
                                                                                   f"Reglas comparadas · Revisadas el {pages18.day(when, 'es')}")[l]) for l in LANGS}, when))
    for g in pages11.EXPORT_GUIDES:   # export guides (SEO brief, step 3)
        out.append((g["slug"], {l: (g["kick"][l], T("CSV export, then into your journal", "Export CSV, puis dans ton journal", "Exportación CSV, luego a tu diario")[l]) for l in LANGS}, None))
    for c in pages12.C:   # contract specs (audit, Oct 18)
        s, _, _, ts, tv, pv = c[:6]
        out.append((pages12.slug(s), {l: (T(f"{s} futures", f"Futures {s}", f"Futuros {s}")[l],
                    T(f"Tick {pages12._tick(ts)} · {pages12._fmt(tv)} a tick · {pages12._fmt(pv)} a point", f"Tick {pages12._tick(ts, 'fr')} · {pages12._fmt(tv, 'fr')} le tick · {pages12._fmt(pv, 'fr')} le point",
                      f"Tick {pages12._tick(ts, 'es')} · {pages12._fmt(tv, 'es')} por tick · {pages12._fmt(pv, 'es')} por punto")[l]) for l in LANGS}, None))
    for k, sl, _, title, _, _ in pages13.REL:   # release dates
        nm = {l: (title[l] if isinstance(title, dict) else title) for l in LANGS}; of = {l: (pages13.OF[k][l] if k in pages13.OF else nm[l]) for l in LANGS}
        out.append((sl, {l: (T(f"{nm['en']} release dates", f"Dates de publication {of['fr']}", f"Fechas de publicación {of['es']}")[l],
                    T("2026 and 2027, New York time", "2026 et 2027, heure de New York", "2026 y 2027, hora de Nueva York")[l]) for l in LANGS}, None))
    done = {e[0] for e in out}
    for page, title, sub in (("glossary.html", T("Prop trading glossary", "Lexique du trading prop", "Glosario del trading prop"), T("65 terms of futures and prop firms, explained", "65 termes des futures et des prop firms, expliqués", "65 términos de futuros y prop firms, explicados")),
                             ("how-it-works.html", T("How Sweep works", "Comment ça marche", "Cómo funciona Sweep"), T("Plan, execution, review: sweep your day", "Plan, exécution, revue : balaye ta journée", "Plan, ejecución, revisión: barre tu día")),
                             ("import.html", T("Import your trades", "Importer tes trades", "Importar tus operaciones"), T("NinjaTrader 8, Tradovate, Rithmic, TopstepX, TradingView", "NinjaTrader 8, Tradovate, Rithmic, TopstepX, TradingView", "NinjaTrader 8, Tradovate, Rithmic, TopstepX, TradingView")),
                             ("economic-calendar.html", T("Economic calendar", "Calendrier économique", "Calendario económico"), T("Every U.S. release, recapped in a minute", "Chaque annonce américaine, résumée en une minute", "Cada dato de EE. UU., resumido en un minuto")),
                             ("tools.html", T("Free calculators", "Calculateurs gratuits", "Calculadoras gratis"), T("Position size, drawdown, consistency, payouts", "Taille de position, drawdown, consistance, payouts", "Tamaño de posición, drawdown, consistencia, payouts")),
                             ("release-dates.html", T("U.S. economic release dates", "Dates des annonces américaines", "Fechas de los datos de EE. UU."), T("CPI, NFP, FOMC and more, 2026 and 2027", "CPI, NFP, FOMC et plus, 2026 et 2027", "CPI, NFP, FOMC y más, 2026 y 2027")),
                             ("futures-contracts.html", T("CME futures contract specs", "Fiches des contrats CME", "Fichas de los contratos de CME"), T("Tick size and tick value of 14 contracts", "Taille et valeur du tick de 14 contrats", "Tamaño y valor del tick de 14 contratos"))):
        if page not in done: out.append((page, {l: (title[l], sub[l]) for l in LANGS}, None))
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
    try: old = json.load(open(os.path.join(OUT, "manifest.json"), encoding="utf-8"))   # an image whose text and date haven't changed is kept as is
    except (OSError, ValueError): old = {}
    made = 0
    async with async_playwright() as p:
        br = await p.chromium.launch(channel="chrome")
        pg = await br.new_page(viewport={"width": 1200, "height": 630}, device_scale_factor=1)
        for page, texts, when in entries():
            for l in LANGS:
                title, sub = texts[l]
                entry = {"alt": f"{title} · {sub}", "date": when}
                manifest.setdefault(page, {})[l] = entry
                png = os.path.join(OUT, l, name_of(page) + ".png")
                if os.path.exists(png) and old.get(page, {}).get(l) == entry: continue
                await pg.set_content(html_of(title, sub)); await pg.evaluate("document.fonts.ready")
                os.makedirs(os.path.join(OUT, l), exist_ok=True)
                await pg.screenshot(path=png); made += 1
        await br.close()
    json.dump(manifest, open(os.path.join(OUT, "manifest.json"), "w"), ensure_ascii=False, indent=1)
    print(f"{sum(len(v) for v in manifest.values())} share images in static/social/og/, {made} made now")

if __name__ == "__main__":
    asyncio.run(main())
