import re
import os, html, json
HERE = os.path.dirname(os.path.abspath(__file__))
STATIC = os.path.join(HERE, "..", "static")
DOMAIN = "makeitsweep.com"
APP = "https://app.makeitsweep.com/"
SIGNUP = "https://app.makeitsweep.com/?signup=1"
EMAIL = "hello@makeitsweep.com"
LANGS = ["en", "fr", "es"]
ASSETS = {"css": "styles.css", "js": "site.js"}
TODAY = "2026-10-01"
IMGS = set(f.rsplit("-", 1)[0] for f in os.listdir(os.path.join(STATIC, "img")))

def T(en, fr, es): return {"en": en, "fr": fr, "es": es}
def href(lang, page):
    base = "/" if lang == "en" else f"/{lang}/"
    if page == "100": return base + "100"
    if page == "index.html": return base
    return base + (page[:-5] if page.endswith(".html") else page)

# W1 — first-touch UTM cookie shared with app.makeitsweep.com (runs first on every page)
UTM_JS = ("<script>(function(){try{var p=new URLSearchParams(location.search);var k=['utm_source','utm_medium','utm_campaign','utm_content'];"
          "var has=k.some(function(x){return p.get(x);});if(has&&!sessionStorage.getItem('sweep_utm_pending')){var d={};k.forEach(function(x){d[x]=(p.get(x)||'').slice(0,50);});sessionStorage.setItem('sweep_utm_pending',JSON.stringify(d));}"
          "window.sweepWriteUTM=function(){try{var v=sessionStorage.getItem('sweep_utm_pending');if(v&&document.cookie.indexOf('sweep_utm=')===-1){document.cookie='sweep_utm='+encodeURIComponent(v)+'; domain=.makeitsweep.com; path=/; max-age=2592000; SameSite=Lax; Secure';}}catch(e){}};"
          "if(localStorage.getItem('sweep-consent')==='yes')window.sweepWriteUTM();}catch(e){}})();</script>")

MARK = ('<svg viewBox="40 8 40 102" fill="none" aria-hidden="true"><line x1="60" y1="14" x2="60" y2="30" stroke="currentColor" stroke-width="6" stroke-linecap="round"/>'
        '<rect x="46" y="28" width="28" height="44" rx="5" fill="currentColor"/><line x1="60" y1="70" x2="60" y2="84" stroke="currentColor" stroke-width="6"/>'
        '<line x1="60" y1="84" x2="60" y2="104" stroke="var(--gain)" stroke-width="6" stroke-linecap="round"/></svg>')
ANIM_MARK = ('<svg viewBox="30 8 60 102" fill="none" aria-hidden="true"><line class="k-level" x1="30" y1="84" x2="90" y2="84" stroke-width="1" stroke-dasharray="2.5 3.5"/>'
        '<g class="k-candle"><line class="k-upper" x1="60" y1="14" x2="60" y2="30" stroke-width="6" stroke-linecap="round"/>'
        '<rect class="k-body" x="46" y="28" width="28" height="44" rx="5" stroke="none"/><line class="k-mid" x1="60" y1="70" x2="60" y2="84" stroke-width="6"/></g>'
        '<line class="k-swept" x1="60" y1="84" x2="60" y2="104" stroke-width="6" stroke-linecap="round"/></svg>')

SAMPLE = T("Sample data.", "Données d’exemple.", "Datos de ejemplo.")
EXAMPLE = T("Example report, sample data.", "Exemple de rapport, données d’exemple.", "Informe de ejemplo, datos de ejemplo.")

def _pick(kind, lang, screen):
    for L in (lang, "en"):
        if f"{kind}-{L}-dark-{screen}" in IMGS: return L
    raise KeyError(f"{kind} {screen}")

def picture(kind, screen, lang, alt, eager=False, sizes=None, full=False):
    L = _pick(kind, lang, screen)
    dark = f"{kind}-{L}-dark-{screen}"; light = f"{kind}-{L}-light-{screen}"
    has_light = light in IMGS
    load = 'loading="eager" fetchpriority="high"' if eager else 'loading="lazy"'
    if kind == "desktop":
        if full:
            ss = lambda n: f"/img/{n}-1200.webp 1200w"; w, h = 1200, 2364
        else:
            ss = lambda n: f"/img/{n}-1200.webp 1200w, /img/{n}-2400.webp 2400w"; w, h = 1200, 750
        sizes = sizes or "(max-width: 860px) 92vw, 1120px"
        src = f"/img/{dark}-1200.webp"
    else:
        ss = lambda n: f"/img/{n}-400.webp 400w, /img/{n}-786.webp 786w"; w, h = 393, 852
        sizes = sizes or "(max-width: 860px) 30vw, 260px"
        src = f"/img/{dark}-400.webp"
    light_src = f'<source media="(prefers-color-scheme: light)" srcset="{ss(light)}" sizes="{sizes}">' if has_light else ""
    return (f'<picture>{light_src}<source srcset="{ss(dark)}" sizes="{sizes}">'
            f'<img src="{src}" width="{w}" height="{h}" alt="{html.escape(alt)}" {load} decoding="async"></picture>')

def picture_dm(dscreen, mscreen, lang, alt, sizes="(max-width: 860px) 1px, 380px"):
    """Desktop crop on large screens, real phone capture on phones (same <img>, art-directed)."""
    base = picture("desktop", dscreen, lang, alt, sizes=sizes)
    L = _pick("mobile", lang, mscreen); m = f"mobile-{L}-dark-{mscreen}"; ml = f"mobile-{L}-light-{mscreen}"
    src = ""
    if ml in IMGS: src += f'<source media="(max-width: 860px) and (prefers-color-scheme: light)" srcset="/img/{ml}-786.webp">'
    src += f'<source media="(max-width: 860px)" srcset="/img/{m}-786.webp">'
    return base.replace("<picture>", "<picture>" + src, 1)

def has_mobile(screen):
    return f"mobile-en-dark-{screen}" in IMGS

# Old app screenshots -> current captures (desktop capture, phone capture for small screens)
REPL = {
 "overview": ("ecran-apercu-ordi.webp", "ecran-apercu-anneaux.webp"),
 "accounts": ("ecran-comptes-prop.webp", "ecran-comptes-tel.webp"),
 "payouts": ("ecran-payouts-ordi.webp", None),
 "trades": ("ecran-trades-ordi.webp", None),
 "trade-review": (None, "ecran-recap-tel.webp"),
 "new-trade": (None, "ecran-ajout-bougie-static.webp"),
 "insights": ("ecran-analyses-ordi.webp", "ecran-analyses-tel.webp"),
 "calendar": ("ecran-calendrier-ordi.webp", "ecran-calendrier-tel.webp"),
 "journal-day": ("ecran-journal-ordi.webp", "ecran-journal-tel.webp"),
 "insights-discipline": (None, "ecran-revue-60s.webp"),
}
PHONE_REPL = {"overview": "ecran-apercu-anneaux.webp", "new-trade": "ecran-ajout-bougie-static.webp", "insights": "ecran-analyses-tel.webp",
              "calendar": "ecran-calendrier-tel.webp", "trades": "ecran-journal-tel.webp", "accounts": "ecran-comptes-tel.webp"}

def dsrc(name):
    """srcset for desktop captures (1200 and 2400 wide)."""
    b = name[:-5]
    return f'/img/captures/{b}-1200.webp 1200w, /img/captures/{name} 2400w'

def capimg(name, alt, w, h, eager=False):
    ss = f' srcset="{dsrc(name)}" sizes="(max-width: 860px) 92vw, 760px"' if w >= 2000 else ""
    return f'<img src="/img/captures/{name}"{ss} width="{w}" height="{h}" alt="{html.escape(alt)}" {"fetchpriority=\"high\"" if eager else "loading=\"lazy\""} decoding="async">'

def frame(screen, lang, alt, t, cap=True, eager=False, cls="", sizes=None, swap=True, mobile=None):
    """Desktop screenshot in a frame. On phones it swaps to the real phone screenshot when one exists."""
    if screen in REPL:
        d, m = REPL[screen]
        c = f'<figcaption>{t(cap if isinstance(cap, dict) else SAMPLE)}</figcaption>' if cap else ""
        if d and m:
            return (f'<figure class="sw {cls}"><div class="frame">{capimg(d, alt, 2400, 1500, eager)}</div>'
                    f'<div class="phone m">{capimg(m, alt, 900, 1948)}</div>{c}</figure>')
        if m:
            return f'<figure class="slot {cls}"><div class="phone">{capimg(m, alt, 900, 1948, eager)}</div>{c}</figure>'
        return f'<figure class="{cls}"><div class="frame">{capimg(d, alt, 2400, 1500, eager)}</div>{c}</figure>'
    c = f'<figcaption>{t(cap if isinstance(cap, dict) else SAMPLE)}</figcaption>' if cap else ""
    ms = mobile or screen
    if swap and has_mobile(ms):
        return (f'<figure class="sw {cls}"><div class="frame">{picture("desktop", screen, lang, alt, eager, sizes or "(max-width: 860px) 1px, 760px")}</div>'
                f'<div class="phone m">{picture("mobile", ms, lang, alt, False, "(max-width: 860px) 72vw, 1px")}</div>{c}</figure>')
    return f'<figure class="{cls}"><div class="frame">{picture("desktop", screen, lang, alt, eager, sizes)}</div>{c}</figure>'

def phone(screen, lang, alt, eager=False, sizes=None):
    if screen in PHONE_REPL:
        return f'<div class="phone">{capimg(PHONE_REPL[screen], alt, 900, 1948, eager)}</div>'
    return f'<div class="phone">{picture("mobile", screen, lang, alt, eager, sizes)}</div>'

def ico(path):
    return f'<div class="ico"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{path}</svg></div>'
I = {
 "net": '<path d="M3 17l5-5 4 4 8-8"/><path d="M15 8h5v5"/>',
 "check": '<circle cx="12" cy="12" r="9"/><path d="M8 12.5l2.5 2.5L16 9.5"/>',
 "archive": '<rect x="3" y="4" width="18" height="5" rx="1.5"/><path d="M5 9v9a2 2 0 002 2h10a2 2 0 002-2V9"/><path d="M10 13h4"/>',
 "calendar": '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M8 3v4M16 3v4M3 10h18"/>',
 "layers": '<path d="M12 3l9 5-9 5-9-5 9-5z"/><path d="M3 13l9 5 9-5"/>',
 "phone": '<rect x="7" y="2.5" width="10" height="19" rx="2.5"/><path d="M11 18.5h2"/>',
 "lock": '<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V8a4 4 0 018 0v3"/>',
 "globe": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.5 2.6 3.8 5.6 3.8 9s-1.3 6.4-3.8 9c-2.5-2.6-3.8-5.6-3.8-9s1.3-6.4 3.8-9z"/>',
 "download": '<path d="M12 4v11"/><path d="M7.5 10.5L12 15l4.5-4.5"/><path d="M5 19h14"/>',
 "trash": '<path d="M4 7h16M10 11v6M14 11v6"/><path d="M6 7l1 12a2 2 0 002 2h6a2 2 0 002-2l1-12"/><path d="M9 7V4h6v3"/>',
 "eye": '<path d="M2.5 12S6 5 12 5s9.5 7 9.5 7-3.5 7-9.5 7-9.5-7-9.5-7z"/><circle cx="12" cy="12" r="2.8"/>',
 "image": '<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="9" cy="10" r="1.8"/><path d="M21 16l-5-5-9 9"/>',
 "key": '<circle cx="8" cy="15" r="4"/><path d="M11 12l9-9M17 6l3 3"/>',
 "shield": '<path d="M12 3l8 3v6c0 4.5-3.4 8.2-8 9-4.6-.8-8-4.5-8-9V6l8-3z"/>',
 "copy": '<rect x="8" y="8" width="12" height="12" rx="2"/><path d="M16 8V6a2 2 0 00-2-2H6a2 2 0 00-2 2v8a2 2 0 002 2h2"/>',
 "bolt": '<path d="M13 3L5 13h6l-1 8 8-10h-6l1-8z"/>',
 "target2": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.2"/>',
 "calc": '<rect x="5" y="3" width="14" height="18" rx="2.5"/><path d="M8.5 7h7M8.5 12h1M12 12h1M15.5 12h0M8.5 16h1M12 16h1M15.5 16h0"/>',
 "spark": '<path d="M12 3l1.8 5.4L19 10l-5.2 1.6L12 17l-1.8-5.4L5 10l5.2-1.6L12 3z"/><path d="M19 15l.7 2 2 .7-2 .7-.7 2-.7-2-2-.7 2-.7.7-2z"/>',
 "chat": '<path d="M4 5h16v11H9l-5 4V5z"/>',
 "doc": '<path d="M7 3h7l5 5v13H7z"/><path d="M14 3v5h5M10 13h6M10 17h6"/>',
 "receipt": '<path d="M6 3h12v18l-3-2-3 2-3-2-3 2V3z"/><path d="M9 8h6M9 12h6"/>',
 "tag": '<path d="M3 12V4h8l10 10-8 8L3 12z"/><circle cx="7.5" cy="8.5" r="1.3"/>',
 "command": '<path d="M9 6a3 3 0 10-3 3h12a3 3 0 10-3-3v12a3 3 0 103-3H6a3 3 0 103 3V6z"/>',
}

NAV = [("features.html", T("Features","Fonctionnalités","Funciones")),
       ("how-it-works.html", T("How it works","Comment ça marche","Cómo funciona")),
       ("prop-traders.html", T("Prop traders","Traders prop","Traders prop")),
       ("ai.html", T("Sweep AI","Sweep AI","Sweep AI")),
       ("pricing.html", T("Pricing","Tarifs","Precios"))]
PRODUCT = [("features.html", T("Features","Fonctionnalités","Funciones"), T("Everything Sweep does","Tout ce que fait Sweep","Todo lo que hace Sweep")),
           ("how-it-works.html", T("How it works","Comment ça marche","Cómo funciona"), T("From sign-up to a swept day","De l’inscription à ta journée balayée","Del registro a tu día barrido"))]
RESOURCES = [("tools.html", T("Free tools","Outils gratuits","Herramientas gratuitas"), T("Position size, drawdown, payout, expectancy","Taille de position, drawdown, payout, espérance","Tamaño de posición, drawdown, payout, esperanza")),
             ("futures-contracts.html", T("Contract specs","Fiches contrats","Fichas de contratos"), T("Tick values for NQ, ES, CL, GC…","Valeurs de tick NQ, ES, CL, GC…","Valores de tick NQ, ES, CL, GC…")),
             ("release-dates.html", T("Release dates","Dates des annonces","Fechas de datos"), T("CPI, NFP, FOMC in 2026–2027","CPI, NFP, FOMC en 2026–2027","CPI, NFP, FOMC en 2026–2027")),
             ("futures-market-hours.html", T("Market hours","Heures de marché","Horario de mercado"), T("Sessions in your time zone","Les sessions dans ton fuseau","Las sesiones en tu zona horaria")),
             ("trading-templates.html", T("Free templates","Modèles gratuits","Plantillas gratuitas"), T("Trading plan, journal, checklist (PDF)","Plan, journal, checklist (PDF)","Plan, diario, checklist (PDF)")),
             ("glossary.html", T("Glossary","Lexique","Glosario"), T("Prop and futures terms","Termes du prop et des futures","Términos de prop y futuros")),
             ("import.html", T("Import your trades","Importer tes trades","Importar operaciones"), T("Tradovate, TopstepX, Rithmic, NinjaTrader…","Tradovate, TopstepX, Rithmic, NinjaTrader…","Tradovate, TopstepX, Rithmic, NinjaTrader…")),
             ("faq.html", T("FAQ","FAQ","Preguntas frecuentes"), T("Quick answers","Réponses rapides","Respuestas rápidas")),
             ("changelog.html", T("What’s new","Nouveautés","Novedades"), T("Latest updates","Les dernières mises à jour","Últimas actualizaciones"))]
LOGIN = T("Log in","Connexion","Iniciar sesión")
CREATE = T("Start for free","Commencer gratuitement","Empieza gratis")
CREATE_FREE = T("Start free","Commencer gratuitement","Empieza gratis")
NAV_CTA = T("Start free","Commencer","Empieza gratis")
DISC = T("Sweep does not offer financial advice. Trading futures involves a substantial risk of loss.",
 "Sweep n’offre pas de conseils financiers. Le trading de contrats à terme comporte un risque de perte important.",
 "Sweep no ofrece asesoramiento financiero. Operar contratos de futuros conlleva un riesgo de pérdida importante.")
CHART_MENTION = T("CME market data. Charts powered by TradingView Lightweight Charts™.","Données de marché CME. Graphiques propulsés par TradingView Lightweight Charts™.","Datos de mercado de CME. Gráficos impulsados por TradingView Lightweight Charts™.")
CURP = ' aria-current="page"'; CURL = ' aria-current="true"'

FOOT = [
 (T("Product","Produit","Producto"), [("features.html", T("Features","Fonctionnalités","Funciones")), ("ai.html", T("Sweep AI","Sweep AI","Sweep AI")), ("how-it-works.html", T("How it works","Comment ça marche","Cómo funciona")),
   ("prop-traders.html", T("For prop traders","Pour traders prop","Para traders prop")), ("economic-calendar.html", T("Economic calendar","Calendrier économique","Calendario económico")),
   ("pricing.html", T("Pricing","Tarifs","Precios")), ("changelog.html", T("What’s new","Nouveautés","Novedades"))]),
 (T("Help","Aide","Ayuda"), [("import.html", T("Import your trades","Importer tes trades","Importar operaciones")), ("install.html", T("Install on your phone","Installer sur ton téléphone","Instalar en tu teléfono")),
   ("faq.html", T("FAQ","FAQ","Preguntas frecuentes")), ("contact.html", T("Contact","Contact","Contacto"))]),
 (T("Resources","Ressources","Recursos"), [("tools.html", T("Free calculators","Calculateurs gratuits","Calculadoras gratuitas")), ("futures-contracts.html", T("Contract specs","Fiches contrats","Fichas de contratos")),
   ("release-dates.html", T("Release dates","Dates des annonces","Fechas de datos")), ("futures-market-hours.html", T("Market hours","Heures de marché","Horario de mercado")),
   ("glossary.html", T("Glossary","Lexique","Glosario")), ("trading-templates.html", T("Free templates","Modèles gratuits","Plantillas gratuitas")),
   ("how-to-choose-a-trading-journal.html", T("Choose a trading journal","Choisir un journal de trading","Elegir un diario de trading")), ("trading-journal-routine.html", T("A daily journal routine","Routine de journal","Rutina de diario"))]),
 (T("Compare","Comparer","Comparar"), [("best-trading-journal-for-prop-firms.html", T("Best trading journal for prop firms","Meilleur journal pour prop firms","Mejor diario para prop firms")), ("sweep-vs-tradezella.html", T("Sweep vs TradeZella","Sweep vs TradeZella","Sweep vs TradeZella"))]),
 (T("Company","Entreprise","Empresa"), [("about.html", T("About","À propos","Acerca de")), ("press-kit.html", T("Press kit","Kit presse","Kit de prensa")), ("security.html", T("Security and privacy","Sécurité et confidentialité","Seguridad y privacidad"))]),
 (T("Legal","Légal","Legal"), [("privacy.html", T("Privacy policy","Confidentialité","Privacidad")), ("terms.html", T("Terms of use","Conditions d’utilisation","Términos de uso")), ("risk.html", T("Risk disclosure","Divulgation des risques","Aviso de riesgo"))]),
]

# prop firms with preloaded rules: from the app's catalogue (presets.py), never retyped here
from presets import PRESET_FIRMS

def jsonld(obj): return f'<script type="application/ld+json">{json.dumps(obj, ensure_ascii=False)}</script>'

def _trim(desc, n=158):
    if len(desc) <= n: return desc
    cut = desc[:n]
    for sep in (". ", "! ", "? "):
        k = cut.rfind(sep)
        if k > 70: return cut[:k+1]
    return cut[:cut.rfind(" ")].rstrip(",;:") + "…"

# Oct 6 visuals: older capture names now point to the matching new screens
CAPTURE_V6 = {"ecran-apercu-anneaux":"v6-01-today-m","ecran-apercu-anneaux-clair":"v6-01-today-m","ecran-apercu-ordi":"v6-01-today-d","ecran-apercu-ordi-clair":"v6-01-today-d",
  "ecran-graphique-trade":"v6-06-trade-review-d","ecran-recap-tel":"v6-06-trade-review-m","ecran-comptes-prop":"v6-13-accounts-d","ecran-comptes-tel":"v6-13-accounts-m",
  "ecran-payouts-ordi":"v6-12-payouts-d","ecran-analyses-ordi":"v6-07-stats-d","ecran-analyses-tel":"v6-07-stats-m","ecran-calendrier-ordi":"v6-11-calendar-d","ecran-calendrier-tel":"v6-11-calendar-m",
  "ecran-journal-ordi":"v6-10-journal-d","ecran-journal-tel":"v6-10-journal-m","ecran-ajout-bougie-static":"v6-05-log-by-hand-m","ecran-revue-60s":"v6-04-discipline-psychology-m",
  "ecran-formulaire-capture":"v6-03-log-by-screenshot-m","ecran-payout-apex":"v6-08-payout-conditions-d","ecran-aujourdhui-tel":"v6-01-today-m","ecran-trade-copie":"v6-01-today-d"}
UTM_CAMPAIGN = "oct-update"

TITLE_TRIMS = [" (hora de Nueva York)"," (heure de New York)"," (New York time)"," (ET)"," (NQ, ES, CL, GC…)"," (win rate, R, profit factor)"," (R, profit factor)"," (PDF)",": before, during and after the session",
               ": avant, pendant et après la séance",": antes, durante y después de la sesión"," · Track accounts, rules and payouts"," · Cuentas, reglas y payouts"," · Comptes, règles et payouts",": net after evaluations and resets"]
def _title(tl):
    for x in TITLE_TRIMS:
        if len(tl) <= 65: break
        tl = tl.replace(x, "")
    return tl

META_SEO = {
 "pricing.html": (T("Pricing — Free Trading Journal, Pro from $19 | Sweep","Tarifs — Journal de trading gratuit, Pro dès 19 $ | Sweep","Precios — Diario de trading gratis, Pro desde 19 $ | Sweep"),
                  T("Start free forever and get 60 days of Pro to test everything. Pro $19/mo or $159/yr, Elite $39/mo or $329/yr. Prices before tax.","Commence gratuitement pour toujours avec 60 jours de Pro pour tout tester. Pro 19 $/mois ou 159 $/an, Elite 39 $/mois ou 329 $/an. Prix avant taxes.","Empieza gratis para siempre con 60 días de Pro para probarlo todo. Pro 19 $/mes o 159 $/año, Elite 39 $/mes o 329 $/año. Precios antes de impuestos.")),
 "about.html": (T("About Sweep — Trading Journal Made in Québec | Sweep","À propos — Journal de trading conçu au Québec | Sweep","Acerca de Sweep — Diario de trading hecho en Quebec | Sweep"),
                T("Sweep Inc. builds the trading journal for futures and prop firm traders, from Laval, Québec. Our story and what we stand for.","Sweep Inc. conçoit le journal de trading des traders de futures et de prop firms, à Laval, au Québec. Notre histoire et nos valeurs.","Sweep Inc. crea el diario de trading para traders de futuros y de prop firms, desde Laval, Quebec. Nuestra historia y nuestros valores.")),
 "security.html": (T("Security & Data — Never Lose Your Trading History | Sweep","Sécurité et données — Ne perds jamais ton historique | Sweep","Seguridad y datos — Nunca pierdas tu historial | Sweep"),
                   T("How Sweep protects your data, where it’s stored, and how to export everything in one click, even after a prop account closes.","Comment Sweep protège tes données, où elles sont stockées, et comment tout exporter en un clic, même après la fermeture d’un compte prop.","Cómo protege Sweep tus datos, dónde se guardan y cómo exportarlo todo en un clic, incluso tras cerrar una cuenta prop.")),
}

def _shell_raw(lang, page, title, desc, body, t, extra_head=""):
    if page in META_SEO: title, desc = t(META_SEO[page][0]), t(META_SEO[page][1])
    desc = _trim(desc); title = _title(title)
    # entity markup on every page, breadcrumbs on inner pages
    org = {"@type":"Organization","@id":f"https://{DOMAIN}/#org","name":"Sweep","legalName":"Sweep Inc.","alternateName":["Make it Sweep","makeitsweep"],"url":f"https://{DOMAIN}/",
           "logo":{"@type":"ImageObject","url":f"https://{DOMAIN}/icons/icon-512.png","width":512,"height":512},"email":EMAIL,"sameAs":[u for _,u,_ in SOCIAL],
           "address":{"@type":"PostalAddress","streetAddress":"3980 Blvd St-Elzear O","addressLocality":"Laval","addressRegion":"QC","postalCode":"H7P 0M2","addressCountry":"CA"}}
    web = {"@type":"WebSite","@id":f"https://{DOMAIN}/#website","name":"Sweep","alternateName":["Make it Sweep","makeitsweep","Sweep trading journal"],"url":f"https://{DOMAIN}/","inLanguage":["en","fr","es"],"publisher":{"@id":f"https://{DOMAIN}/#org"}}
    graph = [org, web]
    if page not in ("index.html", "404.html"):
        crumb = re.split(r"\s[·|—]\s", title)[0].strip()
        graph.append({"@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"Sweep","item":f"https://{DOMAIN}{href(lang,'index.html')}"},
                      {"@type":"ListItem","position":2,"name":crumb,"item":f"https://{DOMAIN}{href(lang,page)}"}]})
    extra_head += jsonld({"@context":"https://schema.org","@graph":graph})
    if page == "404.html": extra_head += '<meta name="robots" content="noindex">'
    cl = "fr" if lang == "fr" else "en"   # Spanish pages use the English captures
    for _o, _n in CAPTURE_V6.items():
        body = body.replace(f"/img/captures/{_o}-1200.webp", f"/img/captures/{_n}-1200.webp").replace(f"/img/captures/{_o}.webp", f"/img/captures/{_n}.webp")
    body = body.replace("/img/captures/", f"/img/captures/{cl}/")
    extra_head = extra_head.replace("/img/captures/", f"/img/captures/{cl}/")
    url = f"https://{DOMAIN}{href(lang,page)}"
    alts = "".join(f'<link rel="alternate" hreflang="{l}" href="https://{DOMAIN}{href(l,page)}">' for l in LANGS)
    alts += f'<link rel="alternate" hreflang="x-default" href="https://{DOMAIN}{href("en",page)}">'
    redirect = ""   # no automatic language redirect (SEO): a suggestion banner is shown instead
    CHEV = '<svg class="chev" width="10" height="10" viewBox="0 0 10 10" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M2 3.5l3 3 3-3"/></svg>'
    def dd(label, items, key):
        cur = any(p == page for p, _, _ in items)
        links = "".join(f'<a role="menuitem" href="{href(lang,p)}"{CURP if p==page else ""}><b>{t(l)}{"<span class=\"newdot\" aria-hidden=\"true\"></span>" if p=="changelog.html" else ""}</b><span>{t(d)}</span></a>' for p, l, d in items)
        return (f'<div class="navdd" data-dd="{key}"><button type="button" class="ddbtn{" cur" if cur else ""}" aria-haspopup="true" aria-expanded="false">{t(label)}{CHEV}</button>'
                f'<div class="ddmenu" role="menu">{links}</div></div>')
    nav = (dd(T("Product","Produit","Producto"), PRODUCT, "product")
           + "".join(f'<a href="{href(lang,p)}"{CURP if p==page else ""}>{t(l)}</a>' for p, l in NAV[2:])
           + dd(T("Resources","Ressources","Recursos"), RESOURCES, "res"))
    ARROW = '<svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 3.5L10.5 8 6 12.5"/></svg>'
    sheet = "".join(f'<a href="{href(lang,p)}"{CURP if p==page else ""}><span>{t(l)}</span>{ARROW}</a>' for p, l in NAV)
    sheet += '<div class="sheet-res">' + "".join(f'<a href="{href(lang,p)}"{CURP if p==page else ""}>{t(l)}</a>' for p, l, _ in RESOURCES) + '</div>'
    names = {"en":"English","fr":"Français","es":"Español"}
    codes = {"en":"EN","fr":"FR","es":"ES"}
    GLOBE = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.5 2.6 3.8 5.6 3.8 9s-1.3 6.4-3.8 9c-2.5-2.6-3.8-5.6-3.8-9s1.3-6.4 3.8-9z"/></svg>'
    CHECK = '<svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 8.5l3 3 7-7"/></svg>'
    langmenu = "".join(f'<li role="none"><a role="menuitem" href="{href(l,page)}" hreflang="{l}" lang="{l}" data-setlang="{l}"{CURL if l==lang else ""}><span class="code">{codes[l]}</span><span>{names[l]}</span>{CHECK if l==lang else ""}</a></li>' for l in LANGS)
    langsel = f'<div class="langsel"><button class="langbtn" type="button" aria-haspopup="true" aria-expanded="false" aria-label="{t(T("Language","Langue","Idioma"))}: {names[lang]}">{GLOBE}<span>{codes[lang]}</span><svg class="chev" width="10" height="10" viewBox="0 0 10 10" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M2 3.5l3 3 3-3"/></svg></button><ul class="langmenu" role="menu">{langmenu}</ul></div>'
    seg = '<div class="langseg" role="group" aria-label="' + t(T("Language","Langue","Idioma")) + '">' + "".join(f'<a href="{href(l,page)}" hreflang="{l}" lang="{l}" data-setlang="{l}"{CURL if l==lang else ""}>{codes[l]}</a>' for l in LANGS) + '</div>'
    langlinks = "".join(f'<a href="{href(l,page)}" hreflang="{l}" lang="{l}" data-setlang="{l}"{CURL if l==lang else ""}>{names[l]}</a>' for l in LANGS)
    cols = "".join(f'<div><h3>{t(h)}</h3><ul>' + "".join(f'<li><a href="{href(lang,p)}">{t(l)}</a></li>' for p, l in items) + '</ul></div>' for h, items in FOOT)
    ogloc = {"en":"en_US","fr":"fr_CA","es":"es_ES"}[lang]
    noindex = '<meta name="robots" content="noindex">' if page == "404.html" else ""
    return f'''<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<script type="speculationrules">{{"prefetch":[{{"source":"document","where":{{"and":[{{"href_matches":"/*"}},{{"not":{{"href_matches":"/*.pdf"}}}},{{"not":{{"href_matches":"/video/*"}}}}]}},"eagerness":"moderate"}}]}}</script>
<link rel="preconnect" href="https://app.makeitsweep.com" crossorigin><link rel="dns-prefetch" href="https://app.makeitsweep.com">
<script>try{{if(sessionStorage.getItem("sw-seen"))document.documentElement.classList.add("ret");sessionStorage.setItem("sw-seen","1")}}catch(e){{}}</script>
{UTM_JS}
<script>window.sweepTrack=function(n,p){{try{{if(window.plausible)plausible(n,{{props:p||{{}}}});else if(window._paq)_paq.push(['trackEvent','site',n]);}}catch(e){{}}}};</script>
{redirect}
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
{noindex}
<link rel="canonical" href="{url}">
{alts}
<link rel="preload" href="/assets/fonts/Geist-Variable.woff2" as="font" type="font/woff2" crossorigin>
<script>document.documentElement.classList.add("js")</script>
<link rel="stylesheet" href="/assets/{ASSETS["css"]}">
<link rel="icon" href="/icons/favicon.ico" sizes="any">
<link rel="icon" href="/icons/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/icons/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<meta name="theme-color" content="#0B0B0C" media="(prefers-color-scheme: dark)">
<meta name="theme-color" content="#F7F7F8" media="(prefers-color-scheme: light)">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Sweep">
<meta property="og:locale" content="{ogloc}">{"".join(f'<meta property="og:locale:alternate" content="{x}">' for x in ["en_US","fr_CA","es_ES"] if x!=ogloc)}
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="https://{DOMAIN}/social/{("og-100-"+lang+".png") if page=="100" else ("og-image.png" if lang=="en" else "og-image-"+lang+".png")}">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Sweep — {html.escape(t(T('Your edge, finally in one place.','Ton edge, enfin au même endroit.','Tu edge, por fin en un solo lugar.')))}">
<meta name="twitter:card" content="summary_large_image">
{extra_head}
</head>
<body>
<a class="skip" href="#main">{t(T("Skip to content","Aller au contenu","Saltar al contenido"))}</a>
<header class="nav"><div class="prog" aria-hidden="true"></div><div class="wrap">
<a class="brand" href="{href(lang,'index.html')}" aria-label="Sweep">{MARK}<span>sweep</span></a>
<nav class="nav-main" aria-label="{t(T("Main","Principal","Principal"))}">{nav}</nav>
<div class="nav-cta">{langsel}<a class="btn btn-ghost" href="{APP}">{t(LOGIN)}</a><a class="btn btn-primary" href="{SIGNUP}">{t(NAV_CTA)}</a>
<button class="menu-btn" type="button" aria-expanded="false" aria-controls="sheet" aria-label="Menu"><span class="mb" aria-hidden="true"><i></i><i></i></span></button></div>
</div></header>
<div class="sheet" id="sheet" data-open="false"><nav class="sheet-nav" aria-label="Menu">{sheet}</nav>
<div class="sheet-foot"><a class="btn btn-primary" href="{SIGNUP}">{t(CREATE_FREE)}</a><a class="btn btn-line" href="{APP}">{t(LOGIN)}</a>
<div class="sheet-lang"><span>{t(T("Language","Langue","Idioma"))}</span>{seg}</div>{social_links("social sheet-social")}</div></div>
<main id="main">
{body}
</main>
<div class="langsug" id="langsug" hidden><span data-l="fr">Cette page existe aussi en français</span><span data-l="es">Esta página también está en español</span><span data-l="en">This page is also in English</span><a href="#" id="langsug-go"></a><button type="button" id="langsug-x" aria-label="{t(T("Close","Fermer","Cerrar"))}">✕</button></div>
<div class="consent" id="consent" role="dialog" aria-live="polite" aria-label="{t(T("Cookies","Témoins","Cookies"))}" hidden><p>{t(T("We use one cookie to remember how you found Sweep (the link you clicked). No ads, no cross-site tracking.","On utilise un seul témoin pour savoir comment tu as trouvé Sweep (le lien sur lequel tu as cliqué). Pas de publicité, aucun suivi d’un site à l’autre.","Usamos una sola cookie para saber cómo encontraste Sweep (el enlace en el que hiciste clic). Sin anuncios ni seguimiento entre sitios."))} <a href="{href(lang,'privacy.html')}">{t(T("Privacy","Confidentialité","Privacidad"))}</a></p><div><button type="button" class="btn btn-line" data-consent="no">{t(T("Decline","Refuser","Rechazar"))}</button><button type="button" class="btn btn-primary" data-consent="yes">{t(T("Accept","Accepter","Aceptar"))}</button></div></div>
<div class="dock" aria-hidden="true"><a class="btn btn-primary" href="{SIGNUP}" tabindex="-1">{t(T("Join the first 100","Rejoindre les 100 premiers","Unirme a los primeros 100")) if page=="100" else t(CREATE_FREE)}</a><a class="btn btn-ghost" href="{APP}" tabindex="-1">{t(LOGIN)}</a></div>
<footer><div class="wrap">
<div class="foot">
<div><a class="brand" href="{href(lang,'index.html')}" aria-label="Sweep">{MARK}<span>sweep</span></a><p style="max-width:28ch">{t(T("Your edge, finally in one place.","Ton edge, enfin au même endroit.","Tu edge, por fin en un solo lugar."))}<br><span class="fine">{t(T("Sweep doesn’t offer financial advice. Trading futures involves risk.","Sweep n’offre pas de conseils financiers. Le trading de futures comporte des risques.","Sweep no ofrece asesoría financiera. Operar futuros implica riesgos."))}</span></p>
<div class="cta-row" style="margin-top:20px"><a class="btn btn-line" href="{SIGNUP}">{t(CREATE)}</a><a class="btn btn-ghost" href="{APP}">{t(LOGIN)}</a></div>{social_links()}</div>
{cols}
</div>
<div class="foot-bottom"><span>© 2026 Sweep Inc. · Laval, Québec · <a href="mailto:{EMAIL}">{EMAIL}</a></span><nav class="lang" aria-label="{t(T("Language","Langue","Idioma"))}">{langlinks}</nav></div>
<p class="disclaimer">Sweep Inc. · 3980 Blvd St-Elzear O, Laval (Québec) H7P 0M2 · <a href="mailto:{EMAIL}">{EMAIL}</a> · <a href="{APP}">app.makeitsweep.com</a></p>
<p class="disclaimer" style="margin-top:8px">{t(DISC)} {t(CHART_MENTION)}</p>
</div></footer>
<script src="/assets/{ASSETS["js"]}" defer></script>
</body>
</html>
'''

def final_cta(lang, t, title=None, sub=None):
    title = title or T("Start your record today.","Commence ton historique aujourd’hui.","Empieza tu historial hoy.")
    sub = sub or T("Free forever. Pro included for 60 days.","Gratuit pour toujours. Pro offert pendant 60 jours.","Gratis para siempre. Pro incluido durante 60 días.")
    return f'''<section class="final rule"><div class="wrap">
<span class="mark" aria-hidden="true">{ANIM_MARK}</span>
<h2>{t(title)}</h2>
<p class="lead">{t(sub)}</p>
<div class="cta-row"><a class="btn btn-primary btn-lg" href="{SIGNUP}">{t(CREATE_FREE)}</a><a class="btn btn-line btn-lg" href="{href(lang,'how-it-works.html')}">{t(T("See how it works","Voir comment ça marche","Ver cómo funciona"))}</a></div>
<p class="signoff">{t(T("Your edge, finally in one place.","Ton edge, enfin au même endroit.","Tu edge, por fin en un solo lugar."))}</p>
</div></section>'''

def words(text, delay=0.0):
    """Wrap each word so headlines can rise in line by line. Plain text stays readable without CSS/JS."""
    out = []
    for i, w in enumerate(text.split(" ")):
        out.append(f'<span class="w"><span style="--d:{delay + i*0.045:.3f}s">{w}</span></span>')
    return " ".join(out)

def page_hero(t, h1, lead, kick=None, cta=None):
    k = f'<span class="kick">{t(kick)}</span>' if kick else ""
    c = f'<div class="cta-row">{cta}</div>' if cta else ""
    return f'<div class="page-hero"><div class="wrap">{k}<h1 class="wu">{words(t(h1))}</h1><p class="lead rise d3">{t(lead)}</p>{c}</div></div>'

def ul(t, items, cls="list"):
    return f'<ul class="{cls}">' + "".join(f"<li>{t(x)}</li>" for x in items) + "</ul>"

def split(t, kick, h, p, items, media, flip=False, id_="", rule=True, more=""):
    k = f'<span class="kick">{t(kick)}</span>' if kick else ""
    return f'''<section{f' id="{id_}"' if id_ else ""}{' class="rule"' if rule else ""}><div class="wrap split{" flip" if flip else ""}">
<div class="copy">{k}<h2>{t(h)}</h2><p class="lead">{t(p)}</p>{ul(t, items) if items else ""}{more}</div>
<div class="reveal">{media}</div></div></section>'''

def grid(t, items, cols="g3"):
    return f'<div class="grid stagger {cols}">' + "".join(f'<div>{ico(I[k])}<h3>{t(a)}</h3><p>{t(b)}</p></div>' for k, a, b in items) + '</div>'

def faq_item(t, q, a):
    return f'<details><summary>{t(q)}<span class="plus" aria-hidden="true"></span></summary><div class="ans"><p>{t(a)}</p></div></details>'

SOCIAL = [
 ("Instagram", "https://www.instagram.com/makeitsweep", '<rect x="3.5" y="3.5" width="17" height="17" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.2" cy="6.8" r=".7" fill="currentColor" stroke="none"/>'),
 ("TikTok", "https://www.tiktok.com/@makeitsweep", '<path d="M14 3v11.2a3.8 3.8 0 1 1-3.8-3.8"/><path d="M14 3c.6 2.7 2.4 4.3 5 4.6"/>'),
 ("Facebook", "https://www.facebook.com/share/1Q6uHzUfQf/", '<path d="M14.5 21v-7.5h2.6l.4-3.2h-3V8.4c0-.9.3-1.6 1.6-1.6h1.6V4c-.3 0-1.2-.1-2.3-.1-2.3 0-3.9 1.4-3.9 4v2.4H8.9v3.2h2.6V21"/>'),
]
def social_links(cls="social"):
    return f'<div class="{cls}">' + "".join(
        f'<a href="{u}" target="_blank" rel="noopener me" aria-label="Sweep on {n}" title="{n}"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ic}</svg></a>'
        for n, u, ic in SOCIAL) + '</div>'

# ---------- screenshot slots: final captures go in /img/captures/ (one English set) ----------
CAPTURES = {}   # name -> (kind, width, height, description) for the delivery list
def slot(name, kind, alt, t, fallback=None, cap=True, video=False, poster=None, cls="", alt_video=None, alt_poster=None):
    """Phone or desktop frame showing /img/captures/<name>. If the file isn't there yet, it shows the
    fallback screenshot (if any) or a clean placeholder with the expected file name."""
    w, h = {"phone": (1179, 2556), "desktop": (2880, 1800), "card": (1080, 1920)}[kind]
    CAPTURES[name] = (kind, w, h, alt)
    if poster: CAPTURES[poster] = (kind, w, h, alt + " (poster)")
    fb = ""
    if fallback and fallback.startswith("cap:"):
        fb = "/img/captures/" + fallback[4:]
    elif fallback:
        fb_kind = "mobile" if kind == "phone" else "desktop"
        L = _pick(fb_kind, "en", fallback)
        fb = f"/img/{fb_kind}-{L}-dark-{fallback}-{'786' if kind=='phone' else '1200'}.webp"
    err = f"this.onerror=null;this.src='{fb}'" if fb else "var f=this.closest('figure');if(f)f.classList.add('missing');this.remove()"
    label = ""
    if video:
        ptr = ""
        last = 'onerror="var v=this.closest(\'video\');if(v)v.remove();"'
        if alt_video:
            CAPTURES[alt_video] = (kind, w, h, alt + " (fallback)")
            srcs = f'<source src="/img/captures/{name}" type="video/mp4"><source src="/img/captures/{alt_video}" type="video/mp4" {last}>'
        else:
            srcs = f'<source src="/img/captures/{name}" type="video/mp4" {last}>'
        media = f'<video muted loop playsinline preload="none" data-auto{ptr} aria-label="{html.escape(alt)}">{srcs}</video>'
        vf = f"/img/captures/{poster}" if poster else fb
        ap = f"/img/captures/{alt_poster}" if alt_poster else fb
        oe = f' onerror="this.onerror=null;this.src=\'{ap}\'"' if ap else ""
        if vf: media = f'<img src="{vf}" alt="" aria-hidden="true" class="vfb" loading="lazy"{oe}>' + media
    else:
        _has1200 = os.path.exists(os.path.join(os.path.dirname(__file__), "..", "static", "img", "captures", "en", name[:-5] + "-1200.webp"))
        ss = f' srcset="{dsrc(name)}" sizes="(max-width: 860px) 92vw, 760px"' if (kind == "desktop" and _has1200) else ""
        media = f'<img src="/img/captures/{name}"{ss} alt="{html.escape(alt)}" width="{w}" height="{h}" loading="lazy" decoding="async" onerror="{err}">'
    c = f'<figcaption>{t(SAMPLE)}</figcaption>' if cap else ""
    box = {"phone": "phone", "desktop": "frame", "card": "scard"}[kind]
    return f'<figure class="slot {cls}"><div class="{box} ph {kind}">{label}{media}</div>{c}</figure>'


def capphone(name, alt, light=None):
    """Phone frame with a capture from /img/captures (used in phone rows)."""
    src = f'<source media="(prefers-color-scheme: light)" srcset="/img/captures/{light}">' if light else ""
    return f'<div class="phone"><picture>{src}<img src="/img/captures/{name}" width="900" height="1948" alt="{html.escape(alt)}" loading="lazy" decoding="async"></picture></div>'

# Founding cohort: minimum confirmed count shown while the app endpoint catches up (never inflates: the real count wins as soon as it is higher)
COHORT_FLOOR = 0   # live count only (from the app database)

# Activity numbers appear on the home page only once there are at least this many trades journaled
STATS_MIN = 250


def shell(lang, page, title, desc, body, t, extra_head=""):
    out = _shell_raw(lang, page, title, desc, body, t, extra_head)
    medium = "home" if page == "index.html" else page.replace(".html", "").replace("/", "-")
    return out.replace(SIGNUP, f"{SIGNUP}&amp;utm_source=site&amp;utm_medium={medium}&amp;utm_campaign={UTM_CAMPAIGN}")
