from core import *
import re
import presets
from pages18 import page_of, anchor, usd, pc, kk, day, rep, DDT, colon
from pages17 import _fr_nbsp

# Guides built from the app's prop firm catalogue (presets.py): every number is the app's, never retyped here.
GUIDE_CONS = "prop-firm-consistency-rules.html"
GUIDE_DD = "prop-firm-drawdown-rules.html"
HUB = "guides.html"
DASH = "—"

def _vals(p, phase, key):
    return sorted({(s.get(phase) or {}).get(key) for s in p["sizes"]} - {None})

def _variant_cons(p):
    """[(choice label dict, %)] for funded options that change the consistency rule (Topstep's « Consistency »)."""
    out = []
    for o in p.get("options") or []:
        for c in o.get("choices") or []:
            v = sorted({((s.get("variants") or {}).get(c["id"]) or {}).get(o.get("phase", "funded"), {}).get("consistency") for s in p["sizes"]} - {None})
            if v: out.append((c["label"], v))
    return out

def _pct_range(v, lang): return pc(v[0], lang) if len(v) == 1 else f"{pc(v[0], lang)}–{pc(v[-1], lang)}"

def _firm_rows(lang, t, cells):
    """One block per firm (header row linking to its rules page), one row per account type."""
    body = ""
    for f in presets.FIRMS:
        body += f'<tr class="grp"><th colspan="3" scope="colgroup"><a href="{href(lang, page_of(f))}">{f["name"]}</a></th></tr>'
        for p in f["programs"]:
            a, b = cells(f, p)
            body += f'<tr><th scope="row"><a href="{href(lang, page_of(f))}#{anchor(f, p)}">{p["name"]}</a></th><td>{a}</td><td>{b}</td></tr>'
    return body

def _table(lang, t, h1, h2, body):
    head = (f'<thead><tr><th scope="col">{t(T("Account type","Type de compte","Tipo de cuenta"))}</th>'
            f'<th scope="col">{t(h1)}</th><th scope="col">{t(h2)}</th></tr></thead>')
    return f'<div class="cmp-wrap"><table class="cmp rules guide n2">{head}<tbody>{body}</tbody></table></div>'

def _checked_note(lang, t):
    d = presets.CHECKED
    return t(T(f"From Sweep’s weekly check of each firm’s official pages, last run on {day(d, 'en')}. “{DASH}” means the rule isn’t in the rules Sweep tracks for that account. Rules change: always confirm on the firm’s site. Sweep is not affiliated with these firms.",
               f"Tiré de la vérification hebdomadaire des pages officielles de chaque firme par Sweep, faite le {day(d, 'fr')}. « {DASH} » veut dire que la règle n’est pas dans les règles suivies par Sweep pour ce compte. Les règles changent : confirme toujours sur le site de la firme. Sweep n’est affilié à aucune de ces firmes.",
               f"Tomado de la revisión semanal de las páginas oficiales de cada firma por Sweep, hecha el {day(d, 'es')}. «{DASH}» significa que la regla no está en las reglas que Sweep sigue para esa cuenta. Las reglas cambian: confirma siempre en el sitio de la firma. Sweep no está afiliado a estas firmas."))

def _and(items, lang): return and_list(items, lang)

def _by_firm(pairs, lang):
    """[(firm name, item)] → « Firm A: x, y; Firm B: z. » in the catalogue's order."""
    order, groups = [], {}
    for firm, item in pairs:
        if firm not in groups: order.append(firm); groups[firm] = []
        groups[firm].append(item)
    sep = " ; " if lang == "fr" else "; "
    return sep.join(firm + colon(lang) + ", ".join(groups[firm]) for firm in order) + "."

def _page(lang, t, kick, h1, lead, intro, table, after, faqs, rel, title, desc):
    hero = page_hero(t, h1, lead, kick)
    body_intro = "".join(f"<h2>{t(h)}</h2>" + "".join(f"<p>{t(x)}</p>" for x in ps) for h, ps in intro)
    b = (f'<section style="padding-top:8px"><div class="wrap narrow"><article class="article">{body_intro}</article></div></section>'
         f'<section class="rule"><div class="wrap narrow"><div class="head"><h2>{t(T("Firm by firm.","Firme par firme.","Firma por firma."))}</h2></div>{table}'
         f'<p class="fine vs-note">{_checked_note(lang, t)}</p></div></section>'
         + (f'<section class="rule"><div class="wrap narrow"><article class="article">{after}</article></div></section>' if after else "")
         + f'<section class="rule"><div class="wrap narrow"><div class="head"><h2>{t(T("Questions","Questions","Preguntas"))}</h2></div>'
         + "".join(faq_item(t, q, a) for q, a in faqs) + "</div></section>")
    ld = jsonld({"@context": "https://schema.org", "@graph": [
        {"@type": "Article", "headline": re.sub(r"\.$", "", t(h1)), "inLanguage": lang, "datePublished": "2026-10-13", "dateModified": presets.CHECKED,
         "publisher": {"@id": f"https://{DOMAIN}/#org"}, "author": {"@type": "Organization", "name": "Sweep"}},
        {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": t(q), "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", t(a))}} for q, a in faqs]}]})
    return _fr_nbsp(lang, t(title), t(desc), hero + b + final_cta(lang, t), ld)

FIRM_PAGES = lambda: [(page_of(f), T(f["name"], f["name"], f["name"])) for f in presets.FIRMS]

# ---------------------------------------------------------------- consistency rules
def page_consistency(lang, t):
    def cells(f, p):
        e, fu, va = _vals(p, "eval", "consistency"), _vals(p, "funded", "consistency"), _variant_cons(p)
        best = t(T("Best day ≤ ", "Meilleur jour ≤ ", "Mejor día ≤ "))
        ec = best + _pct_range(e, lang) if e else DASH
        parts = ([best + _pct_range(fu, lang)] if fu else []) + [best + _pct_range(v, lang) + " " + t(T(f"({label['en']} option)", f"(option {label['fr']})", f"(opción {label['es']})")) for label, v in va]
        return ec, "<br>".join(parts) or DASH
    table = _table(lang, t, T("Evaluation", "Évaluation", "Evaluación"), T("Funded account", "Compte financé", "Cuenta financiada"), _firm_rows(lang, t, cells))
    intro = [
     (T("What a consistency rule is", "C’est quoi une règle de consistance", "Qué es una regla de consistencia"), [
      T("A consistency rule caps how much of your profit can come from a single day. In an evaluation, your best day is compared with your total profit; on a funded account, most firms compare it with the profit since your last payout.",
        "Une règle de consistance limite la part de ton profit qui peut venir d’une seule journée. En évaluation, ton meilleur jour est comparé à ton profit total ; en compte financé, la plupart des firmes le comparent au profit depuis ton dernier payout.",
        "Una regla de consistencia limita qué parte de tu beneficio puede venir de un solo día. En una evaluación, tu mejor día se compara con tu beneficio total; en una cuenta financiada, la mayoría de las firmas lo comparan con el beneficio desde tu último payout."),
      T(f"Example: with a 50% rule and {usd(3000, 'en')} of profit, your best day can be at most {usd(1500, 'en')}. If one day made {usd(2000, 'en')}, you need more profit on other days before you pass or get paid.",
        f"Exemple : avec une règle de 50 % et {usd(3000, 'fr')} de profit, ton meilleur jour peut valoir au plus {usd(1500, 'fr')}. Si une journée a rapporté {usd(2000, 'fr')}, il te faut plus de profit sur d’autres jours avant de réussir ou d’être payé.",
        f"Ejemplo: con una regla del 50 % y {usd(3000, 'es')} de beneficio, tu mejor día puede ser como máximo de {usd(1500, 'es')}. Si un día dio {usd(2000, 'es')}, necesitas más beneficio en otros días antes de aprobar o cobrar.")]),
    ]
    # generated answers
    def listing(phase):
        items = {l: [] for l in LANGS}
        for f in presets.FIRMS:
            for p in f["programs"]:
                v = _vals(p, phase, "consistency")
                if v:
                    for l in LANGS: items[l].append((f["name"], f"{p['name']} {_pct_range(v, l)}"))
        return items
    ev, fu = listing("eval"), listing("funded")
    allv = [(v, f["name"], p["name"], ph) for f in presets.FIRMS for p in f["programs"] for ph in ("eval", "funded") for v in _vals(p, ph, "consistency")]
    lo = min(v for v, *_ in allv) if allv else None
    strict = [(n, pn, ph) for v, n, pn, ph in allv if v == lo]
    PH = {"eval": T("evaluation", "évaluation", "evaluación"), "funded": T("funded account", "compte financé", "cuenta financiada")}
    faqs = []
    if ev["en"]:
        faqs.append((T("Which prop firms have a consistency rule in the evaluation?", "Quelles prop firms ont une règle de consistance en évaluation ?", "¿Qué prop firms tienen una regla de consistencia en la evaluación?"),
                     {l: _by_firm(ev[l], l) for l in LANGS}))
    if fu["en"]:
        faqs.append((T("Which prop firms have a consistency rule on funded accounts?", "Quelles prop firms ont une règle de consistance en compte financé ?", "¿Qué prop firms tienen una regla de consistencia en cuentas financiadas?"),
                     {l: _by_firm(fu[l], l) for l in LANGS}))
    if strict:
        faqs.append((T("What is the strictest consistency rule?", "Quelle est la règle de consistance la plus stricte ?", "¿Cuál es la regla de consistencia más estricta?"),
                     {l: {"en": f"{pc(lo, l)}, the lowest share in Sweep’s catalogue: ", "fr": f"{pc(lo, l)}, la part la plus basse du catalogue de Sweep : ", "es": f"{pc(lo, l)}, la parte más baja del catálogo de Sweep: "}[l]
                         + _by_firm([(n, f"{pn} ({PH[ph][l]})") for n, pn, ph in strict], l) for l in LANGS}))
    faqs.append((T("How do I check my consistency?", "Comment vérifier ma consistance ?", "¿Cómo compruebo mi consistencia?"),
                 T(f'Divide your best day by your profit (total, or since your last payout) and compare it with your firm’s percentage. The free <a href="{href("en", "consistency-rule-calculator.html")}">consistency rule calculator</a> does it for you, and Sweep checks it on every trade.',
                   f'Divise ton meilleur jour par ton profit (total, ou depuis ton dernier payout) et compare avec le pourcentage de ta firme. Le <a href="{href("fr", "consistency-rule-calculator.html")}">calculateur de consistance</a> gratuit le fait pour toi, et Sweep le vérifie à chaque trade.',
                   f'Divide tu mejor día entre tu beneficio (total, o desde tu último payout) y compáralo con el porcentaje de tu firma. La <a href="{href("es", "consistency-rule-calculator.html")}">calculadora de consistencia</a> gratuita lo hace por ti, y Sweep lo revisa en cada operación.')))
    rel = [("consistency-rule-calculator.html", T("Consistency rule calculator", "Calculateur de consistance", "Calculadora de consistencia")), (GUIDE_DD, T("Drawdown rules compared", "Règles de drawdown comparées", "Reglas de drawdown comparadas")), ("prop-firm-payout-rules.html", T("Payout rules compared", "Règles de payout comparées", "Reglas de payout comparadas")),
           ("prop-firms/index.html", T("Prop firm rules", "Règles des prop firms", "Reglas de las prop firms")), (HUB, T("All guides", "Tous les guides", "Todas las guías"))]
    return _page(lang, t, T("Guide", "Guide", "Guía"),
        T("Prop firm consistency rules, compared (2026).", "Les règles de consistance des prop firms, comparées (2026).", "Las reglas de consistencia de las prop firms, comparadas (2026)."),
        T(f"How {FIRMS_N} futures prop firms limit your best day, in evaluations and on funded accounts, account type by account type.",
          f"Comment {FIRMS_N} prop firms de futures limitent ton meilleur jour, en évaluation et en compte financé, type de compte par type de compte.",
          f"Cómo {FIRMS_N} prop firms de futuros limitan tu mejor día, en evaluaciones y en cuentas financiadas, tipo de cuenta por tipo de cuenta."),
        intro, table, "", faqs, rel,
        T("Prop Firm Consistency Rules Compared (2026) · Sweep", "Règles de consistance des prop firms (2026) · Sweep", "Reglas de consistencia de prop firms (2026) · Sweep"),
        T(f"The consistency rule of {FIRMS_N} futures prop firms, side by side: best-day limits in evaluations and funded accounts, from Sweep’s weekly check.",
          f"La règle de consistance de {FIRMS_N} prop firms de futures, côte à côte : limite du meilleur jour en évaluation et en compte financé, vérifiée chaque semaine.",
          f"La regla de consistencia de {FIRMS_N} prop firms de futuros, lado a lado: límite del mejor día en evaluación y cuenta financiada, revisada cada semana."))

# ---------------------------------------------------------------- drawdown rules
def page_drawdown_guide(lang, t):
    def phase_cell(p, ph):
        s = rep(p); r = s.get(ph) or {}
        if not r.get("dd"): return DASH
        typ = t(DDT[r["dd_type"]]) if r.get("dd_type") in DDT else ""
        txt = f"{typ} · {usd(r['dd'], lang)}" + ("" if s["size"] == 50000 else f" ({kk(s['size'])})")
        if ph == "funded" and r.get("dd_lock") and r.get("dd_type") != "static":
            off = r.get("dd_lock_offset") or 0
            txt += "<br>" + t(T("stops at the starting balance", "s’arrête au solde de départ", "se detiene en el saldo inicial")) + (f" + {usd(off, lang)}" if off else "")
        return txt
    table = _table(lang, t, T("Evaluation (50K)", "Évaluation (50K)", "Evaluación (50K)"), T("Funded account (50K)", "Compte financé (50K)", "Cuenta financiada (50K)"),
                   _firm_rows(lang, t, lambda f, p: (phase_cell(p, "eval"), phase_cell(p, "funded"))))
    intro = [
     (T("Three kinds of drawdown", "Trois sortes de drawdown", "Tres tipos de drawdown"), [
      T("<b>End of day</b>: the max loss follows your highest closing balance. A peak during the session doesn’t move it, so open profit you give back intraday doesn’t cost you room.",
        "<b>Fin de journée</b> : la perte max suit ton solde de clôture le plus haut. Un sommet pendant la séance ne la déplace pas : un profit latent rendu pendant la journée ne te coûte pas de marge.",
        "<b>Al cierre</b>: la pérdida máx. sigue tu saldo de cierre más alto. Un máximo durante la sesión no la mueve, así que el beneficio abierto que devuelves en el día no te cuesta margen."),
      T("<b>Real time</b> (intraday): the max loss follows your highest balance during the day, open profit included. Giving back a winning trade can use up room even if you close the day green.",
        "<b>Temps réel</b> (intraday) : la perte max suit ton solde le plus haut pendant la journée, profit latent compris. Rendre un trade gagnant peut consommer ta marge même si tu finis la journée dans le vert.",
        "<b>Tiempo real</b> (intradía): la pérdida máx. sigue tu saldo más alto durante el día, beneficio abierto incluido. Devolver una operación ganadora puede consumir margen aunque cierres el día en verde."),
      T("<b>Static</b>: the max loss is a fixed level that never moves up with your profit.",
        "<b>Fixe</b> : la perte max est un niveau fixe qui ne monte jamais avec ton profit.",
        "<b>Fijo</b>: la pérdida máx. es un nivel fijo que nunca sube con tu beneficio."),
      T("On funded accounts, many firms stop the trailing once it reaches your starting balance (sometimes plus a small amount): from then on, your max loss is fixed.",
        "En compte financé, beaucoup de firmes arrêtent le suivi une fois qu’il atteint ton solde de départ (parfois plus un petit montant) : ensuite, ta perte max est fixe.",
        "En cuentas financiadas, muchas firmas detienen el seguimiento cuando llega a tu saldo inicial (a veces más un pequeño importe): desde ahí, tu pérdida máx. es fija.")]),
    ]
    def group(typ, phases=("eval", "funded")):
        return [(f["name"], p["name"]) for f in presets.FIRMS for p in f["programs"] if any(typ in _vals(p, ph, "dd_type") for ph in phases)]
    eod, trade = group("eod"), group("trade")
    switch = [(f["name"], p["name"]) for f in presets.FIRMS for p in f["programs"] if _vals(p, "eval", "dd_type") == ["eod"] and _vals(p, "funded", "dd_type") == ["trade"]]
    locks = {l: [] for l in LANGS}
    for f in presets.FIRMS:
        for p in f["programs"]:
            offs = sorted({(s.get("funded") or {}).get("dd_lock_offset") or 0 for s in p["sizes"] if (s.get("funded") or {}).get("dd_lock")})
            if offs:
                for l in LANGS: locks[l].append((f["name"], p["name"] + (f" (+ {usd(offs[0], l)})" if offs[0] else "")))
    faqs = []
    if eod:
        faqs.append((T("Which prop firms use an end-of-day drawdown?", "Quelles prop firms utilisent un drawdown de fin de journée ?", "¿Qué prop firms usan un drawdown al cierre?"),
                     {l: _by_firm(eod, l) for l in LANGS}))
    if trade:
        faqs.append((T("Which prop firms use a real-time (intraday) trailing drawdown?", "Quelles prop firms utilisent un drawdown suiveur en temps réel (intraday) ?", "¿Qué prop firms usan un drawdown dinámico en tiempo real (intradía)?"),
                     {l: _by_firm(trade, l) + ({"en": " These switch from end of day in the evaluation to real time once funded: ", "fr": " Ceux-ci passent de la fin de journée en évaluation au temps réel une fois financés : ", "es": " Estas pasan del cierre en la evaluación al tiempo real ya financiadas: "}[l] + _by_firm(switch, l) if switch else "") for l in LANGS}))
    if locks["en"]:
        faqs.append((T("When does a trailing drawdown stop moving?", "Quand le drawdown suiveur arrête-t-il de suivre ?", "¿Cuándo deja de moverse el drawdown dinámico?"),
                     {l: {"en": "On these funded accounts, once it reaches your starting balance: ", "fr": "Sur ces comptes financés, une fois qu’il atteint ton solde de départ : ", "es": "En estas cuentas financiadas, cuando llega a tu saldo inicial: "}[l] + _by_firm(locks[l], l) for l in LANGS}))
    faqs.append((T("How do I know how much room I have left?", "Comment savoir combien de marge il me reste ?", "¿Cómo sé cuánto margen me queda?"),
                 T(f'Your liquidation level is your peak minus the max loss (or the fixed level once it stops trailing). The free <a href="{href("en", "trailing-drawdown-calculator.html")}">trailing drawdown calculator</a> shows it, and Sweep tracks it on every trade.',
                   f'Ton seuil de liquidation, c’est ton sommet moins la perte max (ou le niveau fixe une fois le suivi arrêté). Le <a href="{href("fr", "trailing-drawdown-calculator.html")}">calculateur de drawdown suiveur</a> gratuit te le montre, et Sweep le suit à chaque trade.',
                   f'Tu nivel de liquidación es tu máximo menos la pérdida máx. (o el nivel fijo una vez detenido el seguimiento). La <a href="{href("es", "trailing-drawdown-calculator.html")}">calculadora de drawdown dinámico</a> gratuita te lo muestra, y Sweep lo sigue en cada operación.')))
    rel = [("trailing-drawdown-calculator.html", T("Trailing drawdown calculator", "Calculateur de drawdown suiveur", "Calculadora de drawdown dinámico")), (GUIDE_CONS, T("Consistency rules compared", "Règles de consistance comparées", "Reglas de consistencia comparadas")), ("prop-firm-payout-rules.html", T("Payout rules compared", "Règles de payout comparées", "Reglas de payout comparadas")),
           ("prop-firm-profit-targets.html", T("Profit targets and max loss compared", "Objectifs et perte max comparés", "Objetivos y pérdida máx. comparados")), ("prop-firms/index.html", T("Prop firm rules", "Règles des prop firms", "Reglas de las prop firms")), (HUB, T("All guides", "Tous les guides", "Todas las guías"))]
    return _page(lang, t, T("Guide", "Guide", "Guía"),
        T("Prop firm drawdown rules, compared (2026).", "Les règles de drawdown des prop firms, comparées (2026).", "Las reglas de drawdown de las prop firms, comparadas (2026)."),
        T(f"End of day, real time or static: how {FIRMS_N} futures prop firms trail your max loss, and when it stops, account type by account type.",
          f"Fin de journée, temps réel ou fixe : comment {FIRMS_N} prop firms de futures font suivre ta perte max, et quand elle s’arrête, type de compte par type de compte.",
          f"Al cierre, en tiempo real o fijo: cómo {FIRMS_N} prop firms de futuros hacen seguir tu pérdida máx. y cuándo se detiene, tipo de cuenta por tipo de cuenta."),
        intro, table, "", faqs, rel,
        T("Prop Firm Drawdown Rules Compared (2026) · Sweep", "Règles de drawdown des prop firms comparées (2026) · Sweep", "Reglas de drawdown de prop firms (2026) · Sweep"),
        T(f"End-of-day, intraday or static drawdown at {FIRMS_N} futures prop firms, side by side: max loss on a 50K and when trailing stops, checked every week.",
          f"Drawdown de fin de journée, intraday ou fixe chez {FIRMS_N} prop firms de futures, côte à côte : perte max sur un 50K et fin du suivi, vérifiés chaque semaine.",
          f"Drawdown al cierre, intradía o fijo en {FIRMS_N} prop firms de futuros, lado a lado: pérdida máx. en una 50K y fin del seguimiento, revisado cada semana."))

# ---------------------------------------------------------------- hub: /guides
GUIDES = [
 (GUIDE_CONS, T("Prop firm consistency rules, compared", "Les règles de consistance des prop firms, comparées", "Las reglas de consistencia de las prop firms, comparadas"),
  T("Best-day limits in evaluations and funded accounts, firm by firm.", "La limite du meilleur jour en évaluation et en compte financé, firme par firme.", "El límite del mejor día en evaluaciones y cuentas financiadas, firma por firma.")),
 (GUIDE_DD, T("Prop firm drawdown rules, compared", "Les règles de drawdown des prop firms, comparées", "Las reglas de drawdown de las prop firms, comparadas"),
  T("End of day, real time or static, and when trailing stops.", "Fin de journée, temps réel ou fixe, et quand le suivi s’arrête.", "Al cierre, en tiempo real o fijo, y cuándo se detiene el seguimiento.")),
 ("best-trading-journal-for-prop-firms.html", T("The best trading journal for prop firm traders", "Le meilleur journal de trading pour les traders de prop firms", "El mejor diario de trading para traders de prop firms"),
  T("Five journals compared on price, firm rules and how trades get in.", "Cinq journaux comparés : prix, règles des firmes et ajout des trades.", "Cinco diarios comparados: precio, reglas de las firmas y cómo entran las operaciones.")),
 ("how-to-choose-a-trading-journal.html", T("How to choose a trading journal", "Bien choisir son journal de trading", "Cómo elegir un diario de trading"),
  T("Five things that matter for evaluations and funded accounts.", "Cinq choses qui comptent pour les évaluations et les comptes financés.", "Cinco cosas que importan para evaluaciones y cuentas financiadas.")),
 ("trading-journal-routine.html", T("A daily trading journal routine", "Une routine de journal de trading", "Una rutina diaria de diario de trading"),
  T("Five minutes before the open, one line per trade, sixty seconds after the close.", "Cinq minutes avant l’ouverture, une ligne par trade, soixante secondes après la clôture.", "Cinco minutos antes de la apertura, una línea por operación, sesenta segundos tras el cierre.")),
]

def page_hub(lang, t):
    hero = page_hero(t, T("Guides for prop firm traders.", "Des guides pour les traders de prop firms.", "Guías para traders de prop firms."),
        T("Straight answers to the questions futures prop traders ask, with the firms’ rules checked every week.",
          "Des réponses claires aux questions des traders de prop firms en futures, avec les règles des firmes vérifiées chaque semaine.",
          "Respuestas claras a las preguntas de los traders de prop firms de futuros, con las reglas de las firmas revisadas cada semana."),
        T("Guides", "Guides", "Guías"))
    cards = "".join(f'<a class="tool-card" href="{href(lang, s)}"><h2>{t(n)}</h2><p>{t(d)}</p><span class="go">{t(T("Read", "Lire", "Leer"))} →</span></a>' for s, n, d in GUIDES)
    b = f'<section style="padding-top:8px"><div class="wrap"><div class="tool-grid">{cards}</div></div></section>'
    ld = jsonld({"@context": "https://schema.org", "@type": "ItemList", "name": t(T("Guides", "Guides", "Guías")),
                 "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": t(n), "url": f"https://{DOMAIN}{href(lang, s)}"} for i, (s, n, _) in enumerate(GUIDES)]})
    return _fr_nbsp(lang, t(T("Guides for Futures Prop Firm Traders · Sweep", "Guides pour traders de prop firms en futures · Sweep", "Guías para traders de prop firms de futuros · Sweep")),
                    t(T("Guides for futures prop firm traders: consistency and drawdown rules compared, choosing a trading journal and a daily journaling routine.",
                        "Guides pour traders de prop firms en futures : règles de consistance et de drawdown comparées, choisir un journal et routine de journal.",
                        "Guías para traders de prop firms de futuros: reglas de consistencia y drawdown comparadas, elegir un diario y rutina de diario.")),
                    hero + b + final_cta(lang, t), ld)

# ---------------------------------------------------------------- payout rules
GUIDE_PAYOUT = "prop-firm-payout-rules.html"

def _payout_conds(po, size, lang, t):
    U = lambda v: usd(v, lang); out = []
    if po.get("win_days"): out.append(t(T(f"{po['win_days']:g} winning days", f"{po['win_days']:g} jours gagnants", f"{po['win_days']:g} días ganadores")) + (t(T(f" of {U(po['win_min'])}+", f" de {U(po['win_min'])} et +", f" de {U(po['win_min'])} o más")) if po.get("win_min") else ""))
    if po.get("trade_days"): out.append(t(T(f"{po['trade_days']:g} traded days", f"{po['trade_days']:g} jours tradés", f"{po['trade_days']:g} días operados")))
    if po.get("cycle_days"): out.append(t(T(f"{po['cycle_days']:g} days between payouts", f"{po['cycle_days']:g} jours entre deux payouts", f"{po['cycle_days']:g} días entre payouts")))
    if po.get("cycle_min"): out.append(t(T(f"{U(po['cycle_min'])} of profit since the last payout", f"{U(po['cycle_min'])} de profit depuis le dernier payout", f"{U(po['cycle_min'])} de beneficio desde el último payout")))
    elif po.get("cycle_pos"): out.append(t(T("a profit since the last payout", "un profit depuis le dernier payout", "beneficio desde el último payout")))
    if po.get("min_bal"): out.append(t(T(f"balance above {U(po['min_bal'])}", f"solde au-dessus de {U(po['min_bal'])}", f"saldo por encima de {U(po['min_bal'])}")))
    return out

def _payout_amounts(po, lang, t):
    U = lambda v: usd(v, lang); out = []
    lad = po.get("ladder")
    if lad:
        caps = " / ".join(U(x) if x is not None else "∞" for x in lad)
        out.append((t(T(f"from {U(po['min'])}, ", f"dès {U(po['min'])}, ", f"desde {U(po['min'])}, ")) if po.get("min") else "") + t(T(f"caps by payout: {caps}", f"plafonds par payout : {caps}", f"topes por payout: {caps}")))
    elif po.get("min") and po.get("max"): out.append(t(T(f"{U(po['min'])} to {U(po['max'])} per payout", f"{U(po['min'])} à {U(po['max'])} par payout", f"{U(po['min'])} a {U(po['max'])} por payout")))
    elif po.get("min"): out.append(t(T(f"at least {U(po['min'])} per payout", f"au moins {U(po['min'])} par payout", f"al menos {U(po['min'])} por payout")))
    elif po.get("max"): out.append(t(T(f"up to {U(po['max'])} per payout", f"jusqu’à {U(po['max'])} par payout", f"hasta {U(po['max'])} por payout")))
    if po.get("max_pct"): out.append(t(T(f"up to {pc(po['max_pct'], lang)} of the profit", f"jusqu’à {pc(po['max_pct'], lang)} du profit", f"hasta el {pc(po['max_pct'], lang)} del beneficio")))
    if po.get("max_dll"): out.append(t(T(f"up to {U(po['max_dll'])} with the daily loss limit option", f"jusqu’à {U(po['max_dll'])} avec l’option limite du jour", f"hasta {U(po['max_dll'])} con la opción de límite diario")))
    if po.get("max_payouts"): out.append(t(T(f"{po['max_payouts']:g} payouts max", f"{po['max_payouts']:g} payouts max", f"{po['max_payouts']:g} payouts máx.")))
    if po.get("split_pct"): out.append(t(T(f"you keep {pc(po['split_pct'], lang)}", f"tu gardes {pc(po['split_pct'], lang)}", f"te quedas con el {pc(po['split_pct'], lang)}")))
    return out

def _payout_variants(p, s):
    """[(choice label dict, payout)] for funded options that replace the payout rules (Topstep's « Consistency »)."""
    out = []
    for o in p.get("options") or []:
        for c in o.get("choices") or []:
            v = (((s.get("variants") or {}).get(c["id"]) or {}).get(o.get("phase", "funded")) or {}).get("payout")
            if v: out.append((c["label"], v))
    return out

def page_payout_guide(lang, t):
    def cells(f, p):
        s = rep(p); po = (s.get("funded") or {}).get("payout") or {}
        if not po: return DASH, DASH
        tag = "" if s["size"] == 50000 else f" ({kk(s['size'])})"
        conds, amts = _payout_conds(po, s["size"], lang, t), _payout_amounts(po, lang, t)
        for label, v in _payout_variants(p, s):
            opt = t(T(f"{label['en']} option", f"option {label['fr']}", f"opción {label['es']}"))
            vc, va = _payout_conds(v, s["size"], lang, t), _payout_amounts(v, lang, t)
            if vc: conds.append(f"<i>{opt}{colon(lang)}{', '.join(vc)}</i>")
            if va: amts.append(f"<i>{opt}{colon(lang)}{', '.join(va)}</i>")
        return ("<br>".join(conds) or DASH) + tag, ("<br>".join(amts) or DASH)
    table = _table(lang, t, T("Conditions to request (50K)", "Conditions pour demander (50K)", "Condiciones para pedir (50K)"), T("Amount and split (50K)", "Montant et partage (50K)", "Importe y reparto (50K)"),
                   _firm_rows(lang, t, cells))
    intro = [
     (T("How prop firm payouts work", "Comment marchent les payouts des prop firms", "Cómo funcionan los payouts de las prop firms"), [
      T("Before each payout, firms check conditions since your last request: a number of winning days (sometimes with a minimum profit per day) or traded days, sometimes a balance to keep above your starting balance, and often a consistency rule.",
        "Avant chaque payout, les firmes vérifient des conditions depuis ta dernière demande : un nombre de jours gagnants (parfois avec un profit minimum par jour) ou de jours tradés, parfois un solde à garder au-dessus de ton solde de départ, et souvent une règle de consistance.",
        "Antes de cada payout, las firmas revisan condiciones desde tu última solicitud: un número de días ganadores (a veces con un beneficio mínimo por día) o de días operados, a veces un saldo a mantener por encima de tu saldo inicial y, a menudo, una regla de consistencia."),
      T("Then they limit the amount: a minimum and a maximum per payout (at some firms the maximum rises with each payout), sometimes a share of your profit, and a profit split, the share you keep.",
        "Ensuite, elles limitent le montant : un minimum et un maximum par payout (chez certaines firmes, le maximum monte à chaque payout), parfois une part de ton profit, et un partage des profits, la part que tu gardes.",
        "Después limitan el importe: un mínimo y un máximo por payout (en algunas firmas el máximo sube con cada payout), a veces una parte de tu beneficio, y un reparto de beneficios, la parte que te quedas."),
      T(f"Example: on a 50K where you must keep {usd(52100, 'en')}, with a balance of {usd(53800, 'en')} you can request at most {usd(1700, 'en')}, within the firm’s minimum and maximum.",
        f"Exemple : sur un 50K où tu dois garder {usd(52100, 'fr')}, avec un solde de {usd(53800, 'fr')}, tu peux demander au plus {usd(1700, 'fr')}, dans les limites du minimum et du maximum de la firme.",
        f"Ejemplo: en una 50K donde debes mantener {usd(52100, 'es')}, con un saldo de {usd(53800, 'es')} puedes pedir como máximo {usd(1700, 'es')}, dentro del mínimo y el máximo de la firma.")]),
    ]
    def pairs(fn):
        out = {l: [] for l in LANGS}
        for f in presets.FIRMS:
            for p in f["programs"]:
                s = rep(p); po = (s.get("funded") or {}).get("payout") or {}
                for l in LANGS:
                    v = fn(po, s, l)
                    if v: out[l].append((f["name"], f"{p['name']} {v}"))
        return out
    wins = pairs(lambda po, s, l: (f"({po['win_days']:g}" + ({"en": f" × {usd(po['win_min'], l)}+", "fr": f" × {usd(po['win_min'], l)} et +", "es": f" × {usd(po['win_min'], l)} o más"}[l] if po.get("win_min") else "") + ")") if po.get("win_days") else None)
    def cap_text(po, l):
        """« $1,500–$3,000 », « $2,000 » or « $2,000, then no cap » (a ladder of caps by payout)."""
        lad = po.get("ladder")
        if not lad: return usd(po["max"], l) if po.get("max") else None
        vals = [x for x in lad if x is not None]
        txt = usd(vals[0], l) if min(vals) == max(vals) else f"{usd(min(vals), l)}–{usd(max(vals), l)}"
        return txt + ({"en": ", then no cap", "fr": ", puis sans plafond", "es": ", luego sin tope"}[l] if None in lad else "")
    caps = pairs(lambda po, s, l: cap_text(po, l))
    splits = pairs(lambda po, s, l: pc(po["split_pct"], l) if po.get("split_pct") else None)
    bufs = pairs(lambda po, s, l: ({"en": f"{usd(po['min_bal'], l)} ({usd(po['min_bal'] - s['size'], l)} above the start)", "fr": f"{usd(po['min_bal'], l)} ({usd(po['min_bal'] - s['size'], l)} au-dessus du départ)", "es": f"{usd(po['min_bal'], l)} ({usd(po['min_bal'] - s['size'], l)} sobre el inicio)"}[l]) if po.get("min_bal") else None)
    faqs = []
    if wins["en"]:
        faqs.append((T("Which prop firms require winning days before a payout?", "Quelles prop firms exigent des jours gagnants avant un payout ?", "¿Qué prop firms exigen días ganadores antes de un payout?"),
                     {l: {"en": "Number of winning days (and minimum profit per day) on a 50K: ", "fr": "Nombre de jours gagnants (et profit minimum par jour) sur un 50K : ", "es": "Número de días ganadores (y beneficio mínimo por día) en una 50K: "}[l] + _by_firm(wins[l], l) for l in LANGS}))
    if caps["en"]:
        faqs.append((T("How much can I withdraw per payout?", "Combien puis-je retirer par payout ?", "¿Cuánto puedo retirar por payout?"),
                     {l: {"en": "Maximum per payout on a 50K (a range when the cap rises with each payout): ", "fr": "Maximum par payout sur un 50K (une fourchette quand le plafond monte à chaque payout) : ", "es": "Máximo por payout en una 50K (un rango cuando el tope sube con cada payout): "}[l] + _by_firm(caps[l], l) for l in LANGS}))
    if splits["en"]:
        faqs.append((T("What profit split do prop firms pay?", "Quel partage des profits les prop firms versent-elles ?", "¿Qué reparto de beneficios pagan las prop firms?"),
                     {l: {"en": "The share you keep, where the firm’s rules state it: ", "fr": "La part que tu gardes, quand les règles de la firme l’indiquent : ", "es": "La parte que te quedas, cuando las reglas de la firma la indican: "}[l] + _by_firm(splits[l], l) for l in LANGS}))
    if bufs["en"]:
        faqs.append((T("Do I need to keep a buffer above my starting balance?", "Dois-je garder un coussin au-dessus de mon solde de départ ?", "¿Debo mantener un colchón sobre mi saldo inicial?"),
                     {l: {"en": "At these firms, yes. Balance to keep on a 50K: ", "fr": "Chez ces firmes, oui. Solde à garder sur un 50K : ", "es": "En estas firmas, sí. Saldo a mantener en una 50K: "}[l] + _by_firm(bufs[l], l) for l in LANGS}))
    faqs.append((T("How do I know how much I can request?", "Comment savoir combien je peux demander ?", "¿Cómo sé cuánto puedo pedir?"),
                 T(f'Take your balance, subtract the balance to keep, then stay within the firm’s minimum and maximum. The free <a href="{href("en", "payout-calculator.html")}">payout calculator</a> does it for you, and Sweep counts your payout conditions on every trade.',
                   f'Prends ton solde, retire le solde à garder, puis reste entre le minimum et le maximum de la firme. Le <a href="{href("fr", "payout-calculator.html")}">calculateur de payout</a> gratuit le fait pour toi, et Sweep compte tes conditions de payout à chaque trade.',
                   f'Toma tu saldo, resta el saldo a mantener y quédate entre el mínimo y el máximo de la firma. La <a href="{href("es", "payout-calculator.html")}">calculadora de payout</a> gratuita lo hace por ti, y Sweep cuenta tus condiciones de payout en cada operación.')))
    rel = [("payout-calculator.html", T("Payout calculator", "Calculateur de payout", "Calculadora de payout")), (GUIDE_CONS, T("Consistency rules compared", "Règles de consistance comparées", "Reglas de consistencia comparadas")),
           (GUIDE_DD, T("Drawdown rules compared", "Règles de drawdown comparées", "Reglas de drawdown comparadas")), ("prop-firms/index.html", T("Prop firm rules", "Règles des prop firms", "Reglas de las prop firms")), (HUB, T("All guides", "Tous les guides", "Todas las guías"))]
    return _page(lang, t, T("Guide", "Guide", "Guía"),
        T("Prop firm payout rules, compared (2026).", "Les règles de payout des prop firms, comparées (2026).", "Las reglas de payout de las prop firms, comparadas (2026)."),
        T(f"When {FIRMS_N} futures prop firms let you request a payout, how much, and how much you keep, account type by account type.",
          f"Quand {FIRMS_N} prop firms de futures te laissent demander un payout, combien, et ce que tu gardes, type de compte par type de compte.",
          f"Cuándo {FIRMS_N} prop firms de futuros te dejan pedir un payout, cuánto y cuánto te quedas, tipo de cuenta por tipo de cuenta."),
        intro, table, "", faqs, rel,
        T("Prop Firm Payout Rules Compared (2026) · Sweep", "Règles de payout des prop firms comparées (2026) · Sweep", "Reglas de payout de prop firms (2026) · Sweep"),
        T(f"Payout rules of {FIRMS_N} futures prop firms, side by side: winning days, balance to keep, caps per payout and profit split, from Sweep’s weekly check.",
          f"Les règles de payout de {FIRMS_N} prop firms de futures, côte à côte : jours gagnants, solde à garder, plafonds et partage des profits, vérifiés chaque semaine.",
          f"Las reglas de payout de {FIRMS_N} prop firms de futuros, lado a lado: días ganadores, saldo a mantener, topes y reparto de beneficios, revisadas cada semana."))

GUIDES.insert(0, (GUIDE_PAYOUT, T("Prop firm payout rules, compared", "Les règles de payout des prop firms, comparées", "Las reglas de payout de las prop firms, comparadas"),
                  T("When you can request, how much, and the share you keep, firm by firm.", "Quand demander, combien, et la part que tu gardes, firme par firme.", "Cuándo pedir, cuánto y la parte que te quedas, firma por firma.")))

# ---------------------------------------------------------------- account sizes, profit targets and max loss
GUIDE_SIZES = "prop-firm-profit-targets.html"

def _size_cell(s, lang, t):
    """« $3,000 / $2,000 / $1,000 (option) »: target, max loss, daily loss limit (evaluation; funded when there's no evaluation)."""
    U = lambda v: usd(v, lang)
    e, f = s.get("eval") or {}, s.get("funded") or {}
    r = e if e.get("dd") else f
    if not r.get("dd"): return DASH
    lines = [f"<b>{U(e['target'])}</b>" if e.get("target") else DASH, U(r["dd"])]
    if r.get("dll"): lines.append(U(r["dll"]) + (" " + t(T("(option)", "(option)", "(opción)")) if r.get("dll_optional") else ""))
    return "<br>".join(lines)

def page_sizes_guide(lang, t):
    secs = ""
    for f in presets.FIRMS:
        sizes = sorted({s["size"] for p in f["programs"] for s in p["sizes"]})
        head = (f'<thead><tr><th scope="col">{t(T("Account type", "Type de compte", "Tipo de cuenta"))}</th>' + "".join(f'<th scope="col">{kk(z)}</th>' for z in sizes) + "</tr></thead>")
        rows = ""
        for p in f["programs"]:
            by = {s["size"]: s for s in p["sizes"]}
            direct = not any((s.get("eval") or {}).get("dd") for s in p["sizes"])
            name = f'<a href="{href(lang, page_of(f))}#{anchor(f, p)}">{p["name"]}</a>' + (f'<br><span class="fine">{t(T("funded directly", "financé direct", "financiada directa"))}</span>' if direct else "")
            rows += f'<tr><th scope="row">{name}</th>' + "".join(f"<td>{_size_cell(by[z], lang, t) if z in by else DASH}</td>" for z in sizes) + "</tr>"
        secs += (f'<h3><a href="{href(lang, page_of(f))}">{f["name"]}</a></h3>'
                 f'<div class="cmp-wrap"><table class="cmp rules sizes n{len(sizes)}">{head}<tbody>{rows}</tbody></table></div>')
    table = (f'<p>{t(T("In each cell: the profit target (bold), the max loss, then the daily loss limit when the account has one. Evaluation values; for accounts funded directly, the funded account’s.", "Dans chaque case : l’objectif de profit (en gras), la perte max, puis la limite de perte du jour quand le compte en a une. Valeurs de l’évaluation ; pour les comptes financés directement, celles du compte financé.", "En cada casilla: el objetivo de beneficio (en negrita), la pérdida máx. y, si la cuenta lo tiene, el límite de pérdida diaria. Valores de la evaluación; en las cuentas financiadas directamente, los de la cuenta financiada."))}</p>'
             + secs)
    intro = [
     (T("Reading the numbers", "Lire les chiffres", "Cómo leer las cifras"), [
      T("The <b>profit target</b> is what you must make to pass the evaluation. The <b>max loss</b> is how far your balance can fall below its reference before the account fails; how that reference moves (end of day, real time or fixed) is in our drawdown guide. The <b>daily loss limit</b> caps what one day can lose.",
        "L’<b>objectif de profit</b>, c’est ce que tu dois gagner pour réussir l’évaluation. La <b>perte max</b>, c’est jusqu’où ton solde peut descendre sous sa référence avant que le compte échoue ; la façon dont cette référence bouge (fin de journée, temps réel ou fixe) est dans notre guide du drawdown. La <b>limite de perte du jour</b> plafonne ce qu’une journée peut perdre.",
        "El <b>objetivo de beneficio</b> es lo que debes ganar para aprobar la evaluación. La <b>pérdida máx.</b> es cuánto puede caer tu saldo bajo su referencia antes de que la cuenta falle; cómo se mueve esa referencia (al cierre, en tiempo real o fija) está en nuestra guía del drawdown. El <b>límite de pérdida diaria</b> limita lo que puede perder un día."),
      T("A bigger account means a bigger target and more room, usually in proportion. Compare the target with the max loss: a $3,000 target with $2,000 of room is a different challenge from $3,000 with $2,500.",
        "Un plus gros compte, c’est un objectif plus haut et plus de marge, en général dans les mêmes proportions. Compare l’objectif à la perte max : un objectif de 3 000 $ avec 2 000 $ de marge, ce n’est pas le même défi qu’avec 2 500 $.",
        "Una cuenta mayor implica un objetivo más alto y más margen, en general en la misma proporción. Compara el objetivo con la pérdida máx.: un objetivo de 3.000 $ con 2.000 $ de margen no es el mismo reto que con 2.500 $.")]),
    ]
    def pairs50(fn):
        out = {l: [] for l in LANGS}
        for f in presets.FIRMS:
            for p in f["programs"]:
                s = next((x for x in p["sizes"] if x["size"] == 50000), None)
                if not s: continue
                for l in LANGS:
                    v = fn(s, l)
                    if v: out[l].append((f["name"], f"{p['name']} {v}"))
        return out
    targets = pairs50(lambda s, l: usd(s["eval"]["target"], l) if (s.get("eval") or {}).get("target") else None)
    maxloss = pairs50(lambda s, l: usd(((s.get("eval") or {}).get("dd") or (s.get("funded") or {}).get("dd")), l) if ((s.get("eval") or {}).get("dd") or (s.get("funded") or {}).get("dd")) else None)
    big = {l: [] for l in LANGS}
    for f in presets.FIRMS:
        top = max(s["size"] for p in f["programs"] for s in p["sizes"])
        if top >= 150000:
            for l in LANGS: big[l].append((f["name"], kk(top)))
    dll = {l: [] for l in LANGS}
    for f in presets.FIRMS:
        for p in f["programs"]:
            ds = [(s.get("eval") or {}) if (s.get("eval") or {}).get("dd") else (s.get("funded") or {}) for s in p["sizes"]]
            if any(d.get("dll") for d in ds):
                opt = all(d.get("dll_optional") for d in ds if d.get("dll"))
                for l in LANGS: dll[l].append((f["name"], p["name"] + (" " + {"en": "(option)", "fr": "(option)", "es": "(opción)"}[l] if opt else "")))
    faqs = []
    if targets["en"]:
        faqs.append((T("What is the profit target on a 50K prop firm account?", "Quel est l’objectif de profit d’un compte prop de 50K ?", "¿Cuál es el objetivo de beneficio de una cuenta prop de 50K?"), {l: _by_firm(targets[l], l) for l in LANGS}))
    if maxloss["en"]:
        faqs.append((T("What is the max loss on a 50K prop firm account?", "Quelle est la perte max d’un compte prop de 50K ?", "¿Cuál es la pérdida máx. de una cuenta prop de 50K?"), {l: _by_firm(maxloss[l], l) for l in LANGS}))
    if big["en"]:
        faqs.append((T("Which prop firms offer 150K accounts or bigger?", "Quelles prop firms offrent des comptes de 150K ou plus ?", "¿Qué prop firms ofrecen cuentas de 150K o más?"),
                     {l: {"en": "Largest account size in Sweep’s catalogue: ", "fr": "Plus grande taille de compte dans le catalogue de Sweep : ", "es": "Mayor tamaño de cuenta en el catálogo de Sweep: "}[l] + _by_firm(big[l], l) for l in LANGS}))
    if dll["en"]:
        faqs.append((T("Which prop firm accounts have a daily loss limit?", "Quels comptes de prop firms ont une limite de perte du jour ?", "¿Qué cuentas de prop firms tienen límite de pérdida diaria?"),
                     {l: _by_firm(dll[l], l) + {"en": " “(option)” means you choose it when you buy.", "fr": " « (option) » veut dire que tu la choisis à l’achat.", "es": " «(opción)» significa que la eliges al comprar."}[l] for l in LANGS}))
    faqs.append((T("How many contracts can I trade on my account?", "Combien de contrats puis-je trader sur mon compte ?", "¿Cuántos contratos puedo operar en mi cuenta?"),
                 T(f'Each firm sets a contract limit per account size (on each firm’s rules page). To size each trade so a stop never costs more than you planned, use the free <a href="{href("en", "position-size-calculator.html")}">position size calculator</a>.',
                   f'Chaque firme fixe un nombre de contrats max par taille de compte (sur la page de règles de chaque firme). Pour dimensionner chaque trade sans qu’un stop coûte plus que prévu, utilise le <a href="{href("fr", "position-size-calculator.html")}">calculateur de taille de position</a> gratuit.',
                   f'Cada firma fija un máximo de contratos por tamaño de cuenta (en la página de reglas de cada firma). Para dimensionar cada operación sin que un stop cueste más de lo previsto, usa la <a href="{href("es", "position-size-calculator.html")}">calculadora de tamaño de posición</a> gratuita.')))
    rel = [("position-size-calculator.html", T("Position size calculator", "Calculateur de taille de position", "Calculadora de tamaño de posición")), (GUIDE_DD, T("Drawdown rules compared", "Règles de drawdown comparées", "Reglas de drawdown comparadas")),
           (GUIDE_PAYOUT, T("Payout rules compared", "Règles de payout comparées", "Reglas de payout comparadas")), ("prop-firms/index.html", T("Prop firm rules", "Règles des prop firms", "Reglas de las prop firms")), (HUB, T("All guides", "Tous les guides", "Todas las guías"))]
    return _page(lang, t, T("Guide", "Guide", "Guía"),
        T("Prop firm account sizes, profit targets and max loss, compared (2026).", "Tailles de compte, objectifs de profit et perte max des prop firms, comparés (2026).", "Tamaños de cuenta, objetivos de beneficio y pérdida máx. de las prop firms, comparados (2026)."),
        T(f"The profit target, max loss and daily loss limit of every account size at {FIRMS_N} futures prop firms, from 25K to the largest.",
          f"L’objectif de profit, la perte max et la limite du jour de chaque taille de compte chez {FIRMS_N} prop firms de futures, de 25K à la plus grande.",
          f"El objetivo de beneficio, la pérdida máx. y el límite diario de cada tamaño de cuenta en {FIRMS_N} prop firms de futuros, de 25K a la mayor."),
        intro, table, "", faqs, rel,
        T("Prop Firm Profit Targets & Max Loss by Size (2026) · Sweep", "Objectifs et perte max des prop firms (2026) · Sweep", "Objetivos y pérdida máx. de prop firms (2026) · Sweep"),
        T(f"Profit target, max loss and daily loss limit for every account size at {FIRMS_N} futures prop firms, side by side, from Sweep’s weekly check of their pages.",
          f"Objectif de profit, perte max et limite du jour de chaque taille de compte chez {FIRMS_N} prop firms de futures, côte à côte, vérifiés chaque semaine.",
          f"Objetivo de beneficio, pérdida máx. y límite diario de cada tamaño de cuenta en {FIRMS_N} prop firms de futuros, lado a lado, revisados cada semana."))

GUIDES.insert(1, (GUIDE_SIZES, T("Account sizes, profit targets and max loss, compared", "Tailles de compte, objectifs et perte max, comparés", "Tamaños de cuenta, objetivos y pérdida máx., comparados"),
                  T("Every size from 25K up, firm by firm: target, max loss, daily limit.", "Chaque taille dès 25K, firme par firme : objectif, perte max, limite du jour.", "Cada tamaño desde 25K, firma por firma: objetivo, pérdida máx., límite diario.")))
