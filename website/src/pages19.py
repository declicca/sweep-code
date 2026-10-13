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
         + "".join(faq_item(t, q, a) for q, a in faqs)
         + f'<p class="firm-others" style="margin-top:36px"><span>{t(T("Related","Voir aussi","Ver también"))}</span>'
         + "".join(f'<a href="{href(lang, s)}">{t(n)}</a>' for s, n in rel) + "</p></div></section>")
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
    rel = [("consistency-rule-calculator.html", T("Consistency rule calculator", "Calculateur de consistance", "Calculadora de consistencia")), (GUIDE_DD, T("Drawdown rules compared", "Règles de drawdown comparées", "Reglas de drawdown comparadas")),
           ("prop-firms/index.html", T("Prop firm rules", "Règles des prop firms", "Reglas de las prop firms")), (HUB, T("All guides", "Tous les guides", "Todas las guías"))]
    return _page(lang, t, T("Guide", "Guide", "Guía"),
        T("Prop firm consistency rules, compared (2026).", "Les règles de consistance des prop firms, comparées (2026).", "Las reglas de consistencia de las prop firms, comparadas (2026)."),
        T(f"How {FIRMS_N} futures prop firms limit your best day, in evaluations and on funded accounts, account type by account type.",
          f"Comment {FIRMS_N} prop firms de futures limitent ton meilleur jour, en évaluation et en compte financé, type de compte par type de compte.",
          f"Cómo {FIRMS_N} prop firms de futuros limitan tu mejor día, en evaluaciones y en cuentas financiadas, tipo de cuenta por tipo de cuenta."),
        intro, table, "", faqs, rel,
        T("Prop Firm Consistency Rules Compared (2026) · Sweep", "Règles de consistance des prop firms comparées (2026) · Sweep", "Reglas de consistencia de prop firms (2026) · Sweep"),
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
    rel = [("trailing-drawdown-calculator.html", T("Trailing drawdown calculator", "Calculateur de drawdown suiveur", "Calculadora de drawdown dinámico")), (GUIDE_CONS, T("Consistency rules compared", "Règles de consistance comparées", "Reglas de consistencia comparadas")),
           ("prop-firms/index.html", T("Prop firm rules", "Règles des prop firms", "Reglas de las prop firms")), (HUB, T("All guides", "Tous les guides", "Todas las guías"))]
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
    b = (f'<section style="padding-top:8px"><div class="wrap"><div class="tool-grid">{cards}</div></div></section>'
         f'<section class="rule"><div class="wrap narrow"><p class="firm-others"><span>{t(T("Also", "Aussi", "También"))}</span>'
         + "".join(f'<a href="{href(lang, s)}">{t(n)}</a>' for s, n in [("prop-firms/index.html", T("Prop firm rules", "Règles des prop firms", "Reglas de las prop firms")), ("tools.html", T("Free calculators", "Calculateurs gratuits", "Calculadoras gratuitas")), ("glossary.html", T("Glossary", "Lexique", "Glosario"))])
         + "</p></div></section>")
    ld = jsonld({"@context": "https://schema.org", "@type": "ItemList", "name": t(T("Guides", "Guides", "Guías")),
                 "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": t(n), "url": f"https://{DOMAIN}{href(lang, s)}"} for i, (s, n, _) in enumerate(GUIDES)]})
    return _fr_nbsp(lang, t(T("Guides for Futures Prop Firm Traders · Sweep", "Guides pour traders de prop firms en futures · Sweep", "Guías para traders de prop firms de futuros · Sweep")),
                    t(T("Guides for futures prop firm traders: consistency and drawdown rules compared, choosing a trading journal and a daily journaling routine.",
                        "Guides pour traders de prop firms en futures : règles de consistance et de drawdown comparées, choisir un journal et routine de journal.",
                        "Guías para traders de prop firms de futuros: reglas de consistencia y drawdown comparadas, elegir un diario y rutina de diario.")),
                    hero + b + final_cta(lang, t), ld)
