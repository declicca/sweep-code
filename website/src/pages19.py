from core import *
import re, html
import presets
from pages18 import fr_de, page_of, anchor, usd, pc, kk, day, rep, DDT, colon, checked_of, METHOD, TRACK_PROPS, RULES_FILL
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

def _firm_rows(lang, t, cells, firms=None):
    """One block per firm (header row linking to its rules page), one row per account type."""
    body = ""
    for f in firms or presets.FIRMS:
        body += f'<tr class="grp"><th colspan="3" scope="colgroup"><a href="{href(lang, page_of(f))}">{f["name"]}</a></th></tr>'
        for p in f["programs"]:
            a, b = cells(f, p)
            body += f'<tr><th scope="row"><a href="{href(lang, page_of(f))}#{anchor(f, p)}">{p["name"]}</a></th><td>{a}</td><td>{b}</td></tr>'
    return body

def _table(lang, t, h1, h2, body):
    head = (f'<thead><tr><th scope="col">{t(T("Account type","Type de compte","Tipo de cuenta"))}</th>'
            f'<th scope="col">{t(h1)}</th><th scope="col">{t(h2)}</th></tr></thead>')
    # on phones each row becomes a small card: every value carries its column's name
    body = re.sub(r"<td>(.*?)</td><td>(.*?)</td>", lambda m: f'<td data-label="{html.escape(t(h1))}">{m.group(1)}</td><td data-label="{html.escape(t(h2))}">{m.group(2)}</td>', body)
    return f'<div class="cmp-wrap"><table class="cmp rules guide n2">{head}<tbody>{body}</tbody></table></div>'

def _checked_note(lang, t):
    d = presets.CHECKED
    how = f' <a href="{href(lang, METHOD)}">{t(T("How we verify", "Notre méthode", "Nuestro método"))}</a>'
    return t(T(f"From Sweep’s weekly check of each firm’s official pages, last run on {day(d, 'en')}. “{DASH}” means the rule isn’t in the rules Sweep tracks for that account. Rules change: always confirm on the firm’s site. Sweep is not affiliated with these firms.",
               f"Tiré de la vérification hebdomadaire des pages officielles de chaque firme par Sweep, faite le {day(d, 'fr')}. « {DASH} » veut dire que la règle n’est pas dans les règles suivies par Sweep pour ce compte. Les règles changent : confirme toujours sur le site de la firme. Sweep n’est affilié à aucune de ces firmes.",
               f"Tomado de la revisión semanal de las páginas oficiales de cada firma por Sweep, hecha el {day(d, 'es')}. «{DASH}» significa que la regla no está en las reglas que Sweep sigue para esa cuenta. Las reglas cambian: confirma siempre en el sitio de la firma. Sweep no está afiliado a estas firmas.")) + how

def _by_firm(pairs, lang):
    """[(firm name, item)] → « Firm A: x, y; Firm B: z. » in the catalogue's order."""
    order, groups = [], {}
    for firm, item in pairs:
        if firm not in groups: order.append(firm); groups[firm] = []
        groups[firm].append(item)
    sep = " ; " if lang == "fr" else "; "
    return sep.join(firm + colon(lang) + ", ".join(groups[firm]) for firm in order) + "."

def _page(lang, t, kick, h1, lead, intro, table, after, faqs, rel, title, desc):
    """A rules-compared guide, on the design system: the numbers first (summary, then the table), the explanations after."""
    import ui
    hero = ui.hero(t, kick, h1, lead, cta=ui.btn(t(CREATE_FREE), SIGNUP, lg=True, attrs='data-track="signup_guide_hero"'))
    n_types = sum(len(f["programs"]) for f in presets.FIRMS)
    summary = ui.stats([(t(T("Firms","Firmes","Firmas")), str(len(presets.FIRMS)), ""), (t(T("Account types","Types de compte","Tipos de cuenta")), str(n_types), ""),
                        (t(T("Checked","Vérifiées le","Revisadas el")), day(presets.CHECKED, lang), t(T("every week","chaque semaine","cada semana")))])
    body_intro = "".join(f"<h2>{t(h)}</h2>" + "".join(f"<p>{t(x)}</p>" for x in ps) for h, ps in intro)
    band = ui.band(t(TRACK_PROPS), t(RULES_FILL), ui.btn(t(CREATE_FREE), SIGNUP, lg=True, attrs='data-track="signup_guide_card"'))
    b = (ui.sec(summary, "t", "summary")
         + ui.sec(ui.head(t, None, T("Firm by firm.","Firme par firme.","Firma por firma.")) + table + f'<p class="fine vs-note" style="margin-top:20px">{_checked_note(lang, t)}</p>' + band, "t", "firms")
         + ui.sec(f'<article class="article">{body_intro}</article>', "n", "explained", width="read")
         + (ui.sec(f'<article class="article">{after}</article>', "n", "more", width="read") if after else "")
         + ui.sec(ui.head(t, None, T("Questions","Questions","Preguntas")) + ui.qa(t, faqs), "n", "faq", width="read"))
    ld = jsonld({"@context": "https://schema.org", "@graph": [
        {"@type": "Article", "headline": re.sub(r"\.$", "", t(h1)), "inLanguage": lang, "datePublished": "2026-10-13", "dateModified": presets.CHECKED,
         "publisher": {"@id": f"https://{DOMAIN}/#org"}, "author": {"@type": "Organization", "name": "Sweep"}},
        {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": t(q), "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", t(a))}} for q, a in faqs]}]})
    return _fr_nbsp(lang, t(title), t(desc), hero + b + ui.final(lang, t), ld)

# ---------------------------------------------------------------- consistency rules
def cons_cells(lang, t, f, p):
    """Consistency: (evaluation, funded account) for an account type."""
    e, fu, va = _vals(p, "eval", "consistency"), _vals(p, "funded", "consistency"), _variant_cons(p)
    best = t(T("Best day ≤ ", "Meilleur jour ≤ ", "Mejor día ≤ "))
    ec = best + _pct_range(e, lang) if e else DASH
    parts = ([best + _pct_range(fu, lang)] if fu else []) + [best + _pct_range(v, lang) + " " + t(T(f"({label['en']} option)", f"(option {label['fr']})", f"(opción {label['es']})")) for label, v in va]
    return ec, "<br>".join(parts) or DASH
CONS_HEADS = (T("Evaluation", "Évaluation", "Evaluación"), T("Funded account", "Compte financé", "Cuenta financiada"))

def page_consistency(lang, t):
    table = _table(lang, t, *CONS_HEADS, _firm_rows(lang, t, lambda f, p: cons_cells(lang, t, f, p)))
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
        T("Prop Firm Consistency Rules Compared (2026) · Sweep", "Règle de consistance des prop firms, comparée (2026) · Sweep", "Regla de consistencia de las prop firms (2026) · Sweep"),
        T(f"The consistency rule of {FIRMS_N} futures prop firms, side by side: best-day limits in evaluations and funded accounts, from Sweep’s weekly check.",
          f"La règle de consistance de {FIRMS_N} prop firms de futures, côte à côte : limite du meilleur jour en évaluation et en compte financé, vérifiée chaque semaine.",
          f"La regla de consistencia de {FIRMS_N} prop firms de futuros, lado a lado: límite del mejor día en evaluación y cuenta financiada, revisada cada semana."))

# ---------------------------------------------------------------- drawdown rules
def _dd_cell(lang, t, p, ph):
    s = rep(p); r = s.get(ph) or {}
    if not r.get("dd"): return DASH
    typ = t(DDT[r["dd_type"]]) if r.get("dd_type") in DDT else ""
    txt = f"{typ} · {usd(r['dd'], lang)}" + ("" if s["size"] == 50000 else f" ({kk(s['size'])})")
    if ph == "funded" and r.get("dd_lock") and r.get("dd_type") != "static":
        off = r.get("dd_lock_offset") or 0
        txt += "<br>" + t(T("stops at the starting balance", "s’arrête au solde de départ", "se detiene en el saldo inicial")) + (f" + {usd(off, lang)}" if off else "")
    return txt
def dd_cells(lang, t, f, p):
    """Drawdown at 50K (or the closest size): (evaluation, funded account)."""
    return _dd_cell(lang, t, p, "eval"), _dd_cell(lang, t, p, "funded")
DD_HEADS = (T("Evaluation (50K)", "Évaluation (50K)", "Evaluación (50K)"), T("Funded account (50K)", "Compte financé (50K)", "Cuenta financiada (50K)"))

def page_drawdown_guide(lang, t):
    table = _table(lang, t, *DD_HEADS, _firm_rows(lang, t, lambda f, p: dd_cells(lang, t, f, p)))
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
        T("Prop Firm Drawdown Rules Compared (2026) · Sweep", "Drawdown des prop firms : règles comparées (2026) · Sweep", "Drawdown de las prop firms: reglas comparadas (2026) · Sweep"),
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
 ("trading-journal-guide.html", T("How to keep a trading journal", "Tenir un journal de trading", "Cómo llevar un diario de trading"),
  T("What to record on every trade, the numbers to watch, the review and prop firm accounts.", "Quoi noter pour chaque trade, les chiffres à suivre, la revue et les comptes prop.", "Qué anotar en cada operación, las cifras a seguir, la revisión y las cuentas prop.")),
 ("trading-journal-routine.html", T("A daily trading journal routine", "Une routine de journal de trading", "Una rutina diaria de diario de trading"),
  T("Five minutes before the open, one line per trade, sixty seconds after the close.", "Cinq minutes avant l’ouverture, une ligne par trade, soixante secondes après la clôture.", "Cinco minutos antes de la apertura, una línea por operación, sesenta segundos tras el cierre.")),
]

GUIDES_HELP = T("""<h2>Where to start</h2><ul>
<li><b>New to prop firms?</b> Start with <a href="@prop-firm-profit-targets.html">account sizes, profit targets and max loss</a>, then the <a href="@prop-firm-drawdown-rules.html">drawdown rules</a>: most accounts end on the max loss, not on the target.</li>
<li><b>Close to a payout?</b> Read the <a href="@prop-firm-consistency-rules.html">consistency rules</a> and the <a href="@prop-firm-payout-rules.html">payout rules</a>: winning days, cushion, caps and split.</li>
<li><b>Choosing a journal?</b> <a href="@best-trading-journal-for-prop-firms.html">The best journal for prop firm traders</a> lists what matters and compares five of them.</li>
<li><b>Building the habit?</b> The <a href="@trading-journal-routine.html">daily journal routine</a> fits in a few minutes a day.</li>
<li><b>Unsure about a term?</b> The <a href="@glossary.html">glossary</a> explains trailing drawdown, consistency, cushion, payout and the rest in a line or two.</li></ul>
<h2>How the comparisons stay accurate</h2><p>The firm-by-firm tables come from the catalogue Sweep uses to prefill prop accounts, checked every week against each firm’s official pages. Each guide shows the date of the last check, and “—” means the rule isn’t in the rules Sweep tracks for that account. Firms change their rules: always confirm on the firm’s site before you trade. Each guide ends with the questions traders ask most about the rule.</p>
<p>Each rules guide goes with a free calculator to check your own numbers: <a href="@trailing-drawdown-calculator.html">trailing drawdown</a>, <a href="@consistency-rule-calculator.html">consistency</a> and <a href="@payout-calculator.html">payout</a>.</p>""",
"""<h2>Par où commencer</h2><ul>
<li><b>Nouveau dans les prop firms ?</b> Commence par les <a href="@prop-firm-profit-targets.html">tailles de compte, objectifs et perte max</a>, puis les <a href="@prop-firm-drawdown-rules.html">règles de drawdown</a> : la plupart des comptes finissent sur la perte max, pas sur l’objectif.</li>
<li><b>Proche d’un payout ?</b> Lis les <a href="@prop-firm-consistency-rules.html">règles de consistance</a> et les <a href="@prop-firm-payout-rules.html">règles de payout</a> : jours gagnants, coussin, plafonds et partage.</li>
<li><b>Tu choisis un journal ?</b> <a href="@best-trading-journal-for-prop-firms.html">Le meilleur journal pour les traders de prop firms</a> liste ce qui compte et en compare cinq.</li>
<li><b>Tu bâtis l’habitude ?</b> La <a href="@trading-journal-routine.html">routine de journal</a> tient en quelques minutes par jour.</li>
<li><b>Un terme t’échappe ?</b> Le <a href="@glossary.html">lexique</a> explique le drawdown suiveur, la consistance, le coussin, le payout et le reste en une ou deux lignes.</li></ul>
<h2>Comment les comparatifs restent justes</h2><p>Les tableaux firme par firme viennent du catalogue que Sweep utilise pour préremplir les comptes prop, vérifié chaque semaine sur les pages officielles de chaque firme. Chaque guide affiche la date de la dernière vérification, et « — » veut dire que la règle ne fait pas partie de celles que Sweep suit pour ce compte. Les firmes changent leurs règles : confirme toujours sur le site de la firme avant de trader. Chaque guide se termine par les questions que les traders posent le plus sur la règle.</p>
<p>Chaque guide de règles a son calculateur gratuit pour vérifier tes propres chiffres : <a href="@trailing-drawdown-calculator.html">drawdown suiveur</a>, <a href="@consistency-rule-calculator.html">consistance</a> et <a href="@payout-calculator.html">payout</a>.</p>""",
"""<h2>Por dónde empezar</h2><ul>
<li><b>¿Nuevo en las prop firms?</b> Empieza por los <a href="@prop-firm-profit-targets.html">tamaños de cuenta, objetivos y pérdida máx.</a>, y luego las <a href="@prop-firm-drawdown-rules.html">reglas de drawdown</a>: la mayoría de las cuentas terminan en la pérdida máx., no en el objetivo.</li>
<li><b>¿Cerca de un payout?</b> Lee las <a href="@prop-firm-consistency-rules.html">reglas de consistencia</a> y las <a href="@prop-firm-payout-rules.html">reglas de payout</a>: días ganadores, colchón, límites y reparto.</li>
<li><b>¿Eliges un diario?</b> <a href="@best-trading-journal-for-prop-firms.html">El mejor diario para traders de prop firms</a> enumera lo que importa y compara cinco.</li>
<li><b>¿Creando el hábito?</b> La <a href="@trading-journal-routine.html">rutina de diario</a> cabe en pocos minutos al día.</li>
<li><b>¿Dudas con un término?</b> El <a href="@glossary.html">glosario</a> explica el drawdown dinámico, la consistencia, el colchón, el payout y lo demás en una o dos líneas.</li></ul>
<h2>Cómo se mantienen exactas las comparativas</h2><p>Las tablas firma por firma salen del catálogo que Sweep usa para precargar las cuentas prop, revisado cada semana en las páginas oficiales de cada firma. Cada guía muestra la fecha de la última revisión, y «—» significa que la regla no está entre las que Sweep sigue para esa cuenta. Las firmas cambian sus reglas: confirma siempre en el sitio de la firma antes de operar. Cada guía termina con las preguntas que más hacen los traders sobre la regla.</p>
<p>Cada guía de reglas tiene su calculadora gratuita para comprobar tus propias cifras: <a href="@trailing-drawdown-calculator.html">drawdown dinámico</a>, <a href="@consistency-rule-calculator.html">consistencia</a> y <a href="@payout-calculator.html">payout</a>.</p>""")

GUIDE_ICON = {"prop-firm-payout-rules.html": "receipt", "prop-firm-profit-targets.html": "target2", "prop-firm-minimum-days.html": "calendar", "prop-firm-consistency-rules.html": "layers",
              "prop-firm-drawdown-rules.html": "shield", "prop-firm-costs.html": "tag", "best-trading-journal-for-prop-firms.html": "check", "trading-journal-routine.html": "doc", "trading-journal-guide.html": "archive"}
JOURNAL_GUIDES = ("best-trading-journal-for-prop-firms.html", "trading-journal-guide.html", "trading-journal-routine.html")

def page_hub(lang, t):
    """The guides in two rows: the prop firm rules compared, then the journal."""
    import ui
    hero = ui.hero(t, T("Guides", "Guides", "Guías"), T("Guides for prop firm traders.", "Des guides pour les traders de prop firms.", "Guías para traders de prop firms."),
        T("Straight answers to the questions futures prop traders ask, with the firms’ rules checked every week.",
          "Des réponses claires aux questions des traders de prop firms en futures, avec les règles des firmes vérifiées chaque semaine.",
          "Respuestas claras a las preguntas de los traders de prop firms de futuros, con las reglas de las firmas revisadas cada semana."),
        cta=ui.btn(t(CREATE_FREE), SIGNUP, lg=True, attrs='data-track="signup_guides_hero"'))
    card = lambda s, n, d: ui.card(t, n, d, icon=GUIDE_ICON.get(s), more=T("Read", "Lire", "Leer"), url=href(lang, s))
    rules = [card(*g) for g in GUIDES if g[0] not in JOURNAL_GUIDES]
    journal = [card(*g) for g in GUIDES if g[0] in JOURNAL_GUIDES]
    cols = lambda n: 5 if n == 5 else 3 if n % 3 == 0 else 2 if n % 2 == 0 else n   # one row of five, or full rows
    b = (ui.sec(ui.head(t, None, T("Prop firm rules, compared", "Les règles des prop firms, comparées", "Las reglas de las prop firms, comparadas")) + ui.cards(rules, cols(len(rules)), "stagger index"), "t", "rules")
         + ui.sec(ui.head(t, None, T("Your trading journal", "Ton journal de trading", "Tu diario de trading")) + ui.cards(journal, cols(len(journal))), "t", "journal")
         + ui.sec(f'<article class="article">{localize(lang, t(GUIDES_HELP))}</article>', "n", "start", width="read"))
    ld = jsonld({"@context": "https://schema.org", "@type": "ItemList", "name": t(T("Guides", "Guides", "Guías")),
                 "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": t(n), "url": f"https://{DOMAIN}{href(lang, s)}"} for i, (s, n, _) in enumerate(GUIDES)]})
    return _fr_nbsp(lang, t(T("Guides for Futures Prop Firm Traders · Sweep", "Guides pour traders de prop firms en futures · Sweep", "Guías para traders de prop firms de futuros · Sweep")),
                    t(T("Guides for futures prop firm traders: consistency and drawdown rules compared, choosing a trading journal and a daily journaling routine.",
                        "Guides pour traders de prop firms en futures : règles de consistance et de drawdown comparées, choisir un journal et routine de journal.",
                        "Guías para traders de prop firms de futuros: reglas de consistencia y drawdown comparadas, elegir un diario y rutina de diario.")),
                    hero + b + ui.final(lang, t), ld)
SYSTEM_PAGES.add("guides.html")

# ---------------------------------------------------------------- payout rules
GUIDE_PAYOUT = "prop-firm-payout-rules.html"

def _day_conds(po, lang, t):
    """The payout conditions counted in days: winning days (and their minimum profit), traded days, days between payouts."""
    U = lambda v: usd(v, lang); out = []
    if po.get("win_days"): out.append(t(T(f"{po['win_days']:g} winning days", f"{po['win_days']:g} jours gagnants", f"{po['win_days']:g} días ganadores")) + (t(T(f" of {U(po['win_min'])}+", f" de {U(po['win_min'])} et +", f" de {U(po['win_min'])} o más")) if po.get("win_min") else ""))
    if po.get("trade_days"): out.append(t(T(f"{po['trade_days']:g} traded days", f"{po['trade_days']:g} jours tradés", f"{po['trade_days']:g} días operados")))
    if po.get("cycle_days"): out.append(t(T(f"{po['cycle_days']:g} days between payouts", f"{po['cycle_days']:g} jours entre deux payouts", f"{po['cycle_days']:g} días entre payouts")))
    return out

def _payout_conds(po, size, lang, t):
    U = lambda v: usd(v, lang); out = _day_conds(po, lang, t)
    if po.get("first_min") and po.get("cycle_min"): out.append(t(T(f"{U(po['first_min'])} of profit before the 1st, then {U(po['cycle_min'])} before each next one", f"{U(po['first_min'])} de profit avant le 1er, puis {U(po['cycle_min'])} avant chaque suivant", f"{U(po['first_min'])} de beneficio antes del 1.º, luego {U(po['cycle_min'])} antes de cada siguiente")))
    elif po.get("first_min"): out.append(t(T(f"{U(po['first_min'])} of profit before the 1st payout", f"{U(po['first_min'])} de profit avant le 1er payout", f"{U(po['first_min'])} de beneficio antes del 1.er payout")))
    elif po.get("cycle_min"): out.append(t(T(f"{U(po['cycle_min'])} of profit since the last payout", f"{U(po['cycle_min'])} de profit depuis le dernier payout", f"{U(po['cycle_min'])} de beneficio desde el último payout")))
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

def payout_cells(lang, t, f, p):
    """Payouts at 50K (or the closest size): (conditions to request, amount and split)."""
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
PAYOUT_HEADS = (T("Conditions to request (50K)", "Conditions pour demander (50K)", "Condiciones para pedir (50K)"), T("Amount and split (50K)", "Montant et partage (50K)", "Importe y reparto (50K)"))

def page_payout_guide(lang, t):
    table = _table(lang, t, *PAYOUT_HEADS, _firm_rows(lang, t, lambda f, p: payout_cells(lang, t, f, p)))
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
        T("Prop Firm Payout Rules Compared (2026) · Sweep", "Payouts des prop firms : règles comparées (2026) · Sweep", "Payouts de las prop firms: reglas comparadas (2026) · Sweep"),
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

def sizes_table(lang, t, f):
    """One firm's account types × sizes: target, max loss, daily loss limit in each cell."""
    sizes = sorted({s["size"] for p in f["programs"] for s in p["sizes"]})
    head = (f'<thead><tr><th scope="col">{t(T("Account type", "Type de compte", "Tipo de cuenta"))}</th>' + "".join(f'<th scope="col">{kk(z)}</th>' for z in sizes) + "</tr></thead>")
    rows = ""
    for p in f["programs"]:
        by = {s["size"]: s for s in p["sizes"]}
        direct = not any((s.get("eval") or {}).get("dd") for s in p["sizes"])
        name = f'<a href="{href(lang, page_of(f))}#{anchor(f, p)}">{p["name"]}</a>' + (f'<br><span class="fine">{t(T("funded directly", "financé direct", "financiada directa"))}</span>' if direct else "")
        rows += f'<tr><th scope="row">{name}</th>' + "".join(f"<td>{_size_cell(by[z], lang, t) if z in by else DASH}</td>" for z in sizes) + "</tr>"
    return (f'<h3><a href="{href(lang, page_of(f))}">{f["name"]}</a></h3>'
            f'<div class="cmp-wrap"><table class="cmp rules sizes n{len(sizes)}">{head}<tbody>{rows}</tbody></table></div>')
SIZES_HOW = T("In each cell: the profit target (bold), the max loss, then the daily loss limit when the account has one. Evaluation values; for accounts funded directly, the funded account’s.", "Dans chaque case : l’objectif de profit (en gras), la perte max, puis la limite de perte du jour quand le compte en a une. Valeurs de l’évaluation ; pour les comptes financés directement, celles du compte financé.", "En cada casilla: el objetivo de beneficio (en negrita), la pérdida máx. y, si la cuenta lo tiene, el límite de pérdida diaria. Valores de la evaluación; en las cuentas financiadas directamente, los de la cuenta financiada.")
def page_sizes_guide(lang, t):
    secs = "".join(sizes_table(lang, t, f) for f in presets.FIRMS)
    table = (f'<p>{t(SIZES_HOW)}</p>'
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
        T("Prop Firm Profit Targets & Max Loss by Size (2026) · Sweep", "Objectif de profit et perte max des prop firms · Sweep", "Objetivo de beneficio y pérdida máx. de prop firms · Sweep"),
        T(f"Profit target, max loss and daily loss limit for every account size at {FIRMS_N} futures prop firms, side by side, from Sweep’s weekly check of their pages.",
          f"Objectif de profit, perte max et limite du jour de chaque taille de compte chez {FIRMS_N} prop firms de futures, côte à côte, vérifiés chaque semaine.",
          f"Objetivo de beneficio, pérdida máx. y límite diario de cada tamaño de cuenta en {FIRMS_N} prop firms de futuros, lado a lado, revisados cada semana."))

GUIDES.insert(1, (GUIDE_SIZES, T("Account sizes, profit targets and max loss, compared", "Tailles de compte, objectifs et perte max, comparés", "Tamaños de cuenta, objetivos y pérdida máx., comparados"),
                  T("Every size from 25K up, firm by firm: target, max loss, daily limit.", "Chaque taille dès 25K, firme par firme : objectif, perte max, limite du jour.", "Cada tamaño desde 25K, firma por firma: objetivo, pérdida máx., límite diario.")))

# ---------------------------------------------------------------- minimum days
GUIDE_DAYS = "prop-firm-minimum-days.html"

def _days(v, lang, t):
    """[2] → « 2 days », [1, 3] → « 1–3 days »."""
    n = f"{v[0]:g}" if len(v) == 1 else f"{v[0]:g}–{v[-1]:g}"
    one = v == [1]
    return t(T(f"{n} day" if one else f"{n} days", f"{n} jour" if one else f"{n} jours", f"{n} día" if one else f"{n} días"))

def _direct(p):
    """An account funded directly: no evaluation phase in any size."""
    return not any((s.get("eval") or {}).get("dd") for s in p["sizes"])

def days_cells(lang, t, f, p):
    """Days: (evaluation minimum days, funded days before a payout at 50K)."""
    v = _vals(p, "eval", "min_days")
    ev = _days(v, lang, t) if v else t(T("No evaluation", "Pas d’évaluation", "Sin evaluación")) if _direct(p) else DASH
    s = rep(p); po = (s.get("funded") or {}).get("payout") or {}
    conds = _day_conds(po, lang, t)
    for label, vp in _payout_variants(p, s):
        vc = _day_conds(vp, lang, t)
        if vc and vc != conds: conds.append(f"<i>{t(T(f"{label['en']} option", f"option {label['fr']}", f"opción {label['es']}"))}{colon(lang)}{', '.join(vc)}</i>")
    tag = "" if s["size"] == 50000 else f" ({kk(s['size'])})"
    return ev, ("<br>".join(conds) + tag if conds else DASH)

DAYS_HEADS = (T("Evaluation: minimum days", "Évaluation : jours minimum", "Evaluación: días mínimos"), T("Funded: days before a payout (50K)", "Financé : jours avant un payout (50K)", "Financiada: días antes de un payout (50K)"))

def page_days_guide(lang, t):
    cells = lambda f, p: days_cells(lang, t, f, p)
    table = _table(lang, t, *DAYS_HEADS, _firm_rows(lang, t, cells))
    intro = [
     (T("What minimum days are", "Ce que sont les jours minimum", "Qué son los días mínimos"), [
      T("Many evaluations set a minimum number of trading days: even if you reach the profit target sooner, you pass only once you’ve traded that many days. On funded accounts, the days that count before a payout are usually winning days, days that close with at least a set profit, counted again after each payout.",
        "Beaucoup d’évaluations fixent un nombre minimum de jours de trading : même si tu atteins l’objectif de profit plus tôt, tu réussis seulement après avoir tradé ce nombre de jours. En compte financé, les jours qui comptent avant un payout sont en général des jours gagnants, des journées qui finissent avec au moins un certain profit, comptés de nouveau après chaque payout.",
        "Muchas evaluaciones fijan un número mínimo de días de trading: aunque alcances el objetivo de beneficio antes, apruebas solo cuando has operado esos días. En las cuentas financiadas, los días que cuentan antes de un payout suelen ser días ganadores, jornadas que cierran con al menos cierto beneficio, contados de nuevo después de cada payout."),
      T("A trading day runs from one session close to the next, not from midnight to midnight, and each firm sets what makes a day count. The details are on each firm’s rules page.",
        "Une journée de trading va d’une clôture de séance à la suivante, pas de minuit à minuit, et chaque firme fixe ce qui fait compter une journée. Les détails sont sur la page de règles de chaque firme.",
        "Un día de trading va de un cierre de sesión al siguiente, no de medianoche a medianoche, y cada firma fija qué hace contar un día. Los detalles están en la página de reglas de cada firma.")]),
    ]
    ev = {l: [] for l in LANGS}; fu = {l: [] for l in LANGS}
    for f in presets.FIRMS:
        for p in f["programs"]:
            v = _vals(p, "eval", "min_days")
            s = next((x for x in p["sizes"] if x["size"] == 50000), None)
            po = ((s or {}).get("funded") or {}).get("payout") or {}
            for l in LANGS:
                tl = lambda d, L=l: d[L]
                if v: ev[l].append((f["name"], f"{p['name']} {_days(v, l, tl)}"))
                if s and po.get("win_days"): fu[l].append((f["name"], f"{p['name']} {', '.join(_day_conds(po, l, tl))}"))
    faqs = []
    if ev["en"]:
        faqs.append((T("How many days do I need to pass a prop firm evaluation?", "Combien de jours faut-il pour réussir une évaluation de prop firm ?", "¿Cuántos días necesito para aprobar una evaluación de prop firm?"),
                     {l: {"en": "At least the firm’s minimum, and only once the profit target is reached. ", "fr": "Au moins le minimum de la firme, et seulement une fois l’objectif de profit atteint. ", "es": "Al menos el mínimo de la firma, y solo una vez alcanzado el objetivo de beneficio. "}[l] + _by_firm(ev[l], l) for l in LANGS}))
    if fu["en"]:
        faqs.append((T("How many winning days do I need before a payout?", "Combien de jours gagnants faut-il avant un payout ?", "¿Cuántos días ganadores necesito antes de un payout?"),
                     {l: {"en": "On a 50K funded account: ", "fr": "Sur un compte financé de 50K : ", "es": "En una cuenta financiada de 50K: "}[l] + _by_firm(fu[l], l) for l in LANGS}))
    faqs.append((T("How does Sweep count my days?", "Comment Sweep compte-t-il mes jours ?", "¿Cómo cuenta Sweep mis días?"),
                 T("For each account, Sweep counts the days you trade and your winning days against your firm’s rules, and shows when the account is ready for a payout.",
                   "Pour chaque compte, Sweep compte les jours où tu trades et tes jours gagnants selon les règles de ta firme, et t’indique quand le compte est prêt pour un payout.",
                   "En cada cuenta, Sweep cuenta los días que operas y tus días ganadores según las reglas de tu firma, y te muestra cuándo la cuenta está lista para un payout.")))
    return _page(lang, t, T("Guide", "Guide", "Guía"),
        T("Prop firm minimum trading days, compared (2026).", "Les jours minimum des prop firms, comparés (2026).", "Los días mínimos de las prop firms, comparados (2026)."),
        T(f"How many days {FIRMS_N} futures prop firms require to pass an evaluation, and how many winning days before each payout.",
          f"Combien de jours {FIRMS_N} prop firms de futures demandent pour réussir une évaluation, et combien de jours gagnants avant chaque payout.",
          f"Cuántos días piden {FIRMS_N} prop firms de futuros para aprobar una evaluación, y cuántos días ganadores antes de cada payout."),
        intro, table, "", faqs, None,
        T("Prop Firm Minimum Trading Days Compared (2026) · Sweep", "Jours de trading minimum des prop firms (2026) · Sweep", "Días mínimos de trading de las prop firms (2026) · Sweep"),
        T(f"Minimum trading days to pass the evaluation and winning days before a payout at {FIRMS_N} futures prop firms, side by side, from Sweep’s weekly check.",
          f"Jours minimum pour réussir l’évaluation et jours gagnants avant un payout chez {FIRMS_N} prop firms de futures, côte à côte, vérifiés chaque semaine.",
          f"Días mínimos para aprobar la evaluación y días ganadores antes de un payout en {FIRMS_N} prop firms de futuros, lado a lado, revisados cada semana."))

GUIDES.insert(2, (GUIDE_DAYS, T("Prop firm minimum trading days, compared", "Les jours minimum des prop firms, comparés", "Los días mínimos de las prop firms, comparados"),
                  T("Days to pass the evaluation, and winning days before each payout.", "Les jours pour réussir l’évaluation, et les jours gagnants avant chaque payout.", "Los días para aprobar la evaluación, y los días ganadores antes de cada payout.")))

# ---------------------------------------------------------------- costs
GUIDE_COSTS = "prop-firm-costs.html"

def _price_cell(pr, lang, t):
    """« $49/month » then the activation fee, from the app's catalogue; « — » when it has no price."""
    lines = []
    if pr.get("eval") is not None:
        lines.append(f"<b>{usd(pr['eval'], lang)}{t(T('/month', '/mois', '/mes')) if pr.get('eval_period') == 'month' else ''}</b>")
    if pr.get("activation") is not None:
        lines.append(t(T(f"activation {usd(pr['activation'], lang)}", f"activation {usd(pr['activation'], lang)}", f"activación {usd(pr['activation'], lang)}")) if pr["activation"]
                     else t(T("no activation fee", "sans frais d’activation", "sin tarifa de activación")))
    return "<br>".join(lines) or DASH

def page_costs_guide(lang, t):
    secs, missing = "", []
    for f in presets.FIRMS:
        priced = [p for p in f["programs"] if any((s.get("price") or {}).get("eval") is not None or (s.get("price") or {}).get("activation") is not None for s in p["sizes"])]
        if not priced:
            missing.append(f); continue
        sizes = sorted({s["size"] for p in priced for s in p["sizes"]})
        head = (f'<thead><tr><th scope="col">{t(T("Account type", "Type de compte", "Tipo de cuenta"))}</th>' + "".join(f'<th scope="col">{kk(z)}</th>' for z in sizes) + "</tr></thead>")
        rows = ""
        for p in priced:
            by = {s["size"]: s for s in p["sizes"]}
            name = f'<a href="{href(lang, page_of(f))}#{anchor(f, p)}">{p["name"]}</a>' + (f'<br><span class="fine">{t(T("funded directly", "financé direct", "financiada directa"))}</span>' if _direct(p) else "")
            rows += f'<tr><th scope="row">{name}</th>' + "".join(f"<td>{_price_cell(by[z].get('price') or {}, lang, t) if z in by else DASH}</td>" for z in sizes) + "</tr>"
        when = max((s.get("price") or {}).get("checked") or "" for p in priced for s in p["sizes"]) or checked_of(f)
        fine = t(T(f"Prices checked on {day(when, 'en')}", f"Prix vérifiés le {day(when, 'fr')}", f"Precios revisados el {day(when, 'es')}")) + "."
        secs += (f'<h3><a href="{href(lang, page_of(f))}">{f["name"]}</a></h3>'
                 f'<div class="cmp-wrap"><table class="cmp rules sizes costs n{len(sizes)}">{head}<tbody>{rows}</tbody></table></div><p class="fine">{fine}</p>')
    if missing:
        names = and_list([f'<a href="{href(lang, page_of(f))}">{f["name"]}</a>' for f in missing], lang)
        secs += f'<p>{t(T(f"Prices for {names} aren’t in Sweep’s catalogue yet: see each firm’s site.", f"Les prix {fr_de(names)} ne sont pas encore dans le catalogue de Sweep : vois le site de chaque firme.", f"Los precios de {names} aún no están en el catálogo de Sweep: consulta el sitio de cada firma."))}</p>'
    table = (f'<p>{t(T("In each cell: the evaluation’s price (bold), then the activation fee paid once the evaluation is passed. For accounts funded directly, the activation fee is the account’s price.", "Dans chaque case : le prix de l’évaluation (en gras), puis les frais d’activation payés une fois l’évaluation réussie. Pour les comptes financés directement, les frais d’activation sont le prix du compte.", "En cada casilla: el precio de la evaluación (en negrita) y luego la tarifa de activación que se paga al aprobar la evaluación. En las cuentas financiadas directamente, la tarifa de activación es el precio de la cuenta."))}</p>'
             + secs)
    intro = [
     (T("What a prop account costs", "Ce que coûte un compte prop", "Lo que cuesta una cuenta prop"), [
      T("Two prices add up: the evaluation, often billed every month until you pass or stop it, and an activation fee when you get the funded account. Some firms have no activation fee; others sell an account funded directly, with no evaluation.",
        "Deux prix s’additionnent : l’évaluation, souvent facturée chaque mois jusqu’à ce que tu réussisses ou que tu l’arrêtes, et des frais d’activation quand tu obtiens le compte financé. Certaines firmes n’ont pas de frais d’activation ; d’autres vendent un compte financé directement, sans évaluation.",
        "Se suman dos precios: la evaluación, a menudo cobrada cada mes hasta que apruebas o la cancelas, y una tarifa de activación cuando obtienes la cuenta financiada. Algunas firmas no cobran activación; otras venden una cuenta financiada directamente, sin evaluación."),
      T("Firms often run discounts, so the price you pay can be lower. What matters is the total over every attempt and reset, against what your payouts bring back.",
        "Les firmes font souvent des rabais, donc le prix payé peut être plus bas. Ce qui compte, c’est le total de toutes les tentatives et réinitialisations, comparé à ce que tes payouts rapportent.",
        "Las firmas hacen descuentos a menudo, así que el precio pagado puede ser menor. Lo que importa es el total de todos los intentos y reinicios, frente a lo que te devuelven tus payouts.")]),
    ]
    p50 = {l: [] for l in LANGS}; free_act = {l: [] for l in LANGS}
    for f in presets.FIRMS:
        for p in f["programs"]:
            s = next((x for x in p["sizes"] if x["size"] == 50000), None); pr = (s or {}).get("price") or {}
            for l in LANGS:
                tl = lambda d, L=l: d[L]
                if pr.get("eval") is not None: p50[l].append((f["name"], f"{p['name']} {_price_cell({'eval': pr['eval'], 'eval_period': pr.get('eval_period')}, l, tl)}".replace("<b>", "").replace("</b>", "")))
            if any((x.get("price") or {}).get("activation") == 0 for x in p["sizes"]):
                for l in LANGS: free_act[l].append((f["name"], p["name"]))
    faqs = []
    if p50["en"]:
        faqs.append((T("How much does a 50K prop firm evaluation cost?", "Combien coûte une évaluation de prop firm de 50K ?", "¿Cuánto cuesta una evaluación de prop firm de 50K?"),
                     {l: _by_firm(p50[l], l) + {"en": " Before discounts, from Sweep’s catalogue.", "fr": " Avant rabais, selon le catalogue de Sweep.", "es": " Antes de descuentos, según el catálogo de Sweep."}[l] for l in LANGS}))
    if free_act["en"]:
        faqs.append((T("Which prop firms have no activation fee?", "Quelles prop firms n’ont pas de frais d’activation ?", "¿Qué prop firms no cobran tarifa de activación?"),
                     {l: _by_firm(free_act[l], l) for l in LANGS}))
    faqs.append((T("How do I track what my prop accounts really cost?", "Comment suivre ce que mes comptes prop coûtent vraiment ?", "¿Cómo sigo lo que me cuestan de verdad mis cuentas prop?"),
                 T(f'Log every evaluation, reset and activation fee as an expense, and every payout as it’s paid: Sweep’s <a href="{href("en", "payout-tracker.html")}">payout tracker</a> shows your real net, on the Pro and Elite plans. To see if an account can pay for itself, try the free <a href="{href("en", "prop-firm-roi-calculator.html")}">prop firm ROI calculator</a>.',
                   f'Note chaque évaluation, réinitialisation et frais d’activation comme une dépense, et chaque payout quand il est payé : le <a href="{href("fr", "payout-tracker.html")}">suivi des payouts</a> de Sweep montre ton vrai net, avec les forfaits Pro et Elite. Pour voir si un compte peut se rembourser, essaie le <a href="{href("fr", "prop-firm-roi-calculator.html")}">calculateur de rentabilité</a> gratuit.',
                   f'Anota cada evaluación, reinicio y tarifa de activación como gasto, y cada payout cuando se paga: el <a href="{href("es", "payout-tracker.html")}">seguimiento de payouts</a> de Sweep muestra tu neto real, con los planes Pro y Elite. Para ver si una cuenta puede pagarse sola, prueba la <a href="{href("es", "prop-firm-roi-calculator.html")}">calculadora de rentabilidad</a> gratuita.')))
    return _page(lang, t, T("Guide", "Guide", "Guía"),
        T("Prop firm costs: evaluation and activation fees, compared (2026).", "Le coût des prop firms : évaluation et frais d’activation, comparés (2026).", "El coste de las prop firms: evaluación y tarifa de activación, comparados (2026)."),
        T("What an evaluation and a funded account cost, account size by account size, from the prices in Sweep’s catalogue.",
          "Ce que coûtent une évaluation et un compte financé, taille de compte par taille de compte, d’après les prix du catalogue de Sweep.",
          "Lo que cuestan una evaluación y una cuenta financiada, tamaño por tamaño, según los precios del catálogo de Sweep."),
        intro, table, "", faqs, None,
        T("Prop Firm Costs: Evaluation & Activation Fees (2026) · Sweep", "Coût des prop firms : évaluation et activation · Sweep", "Costo de las prop firms: evaluación y activación · Sweep"),
        T("Evaluation prices and activation fees of futures prop firms, account size by account size, from Sweep’s catalogue, with the date each price was checked.",
          "Prix des évaluations et frais d’activation des prop firms de futures, taille par taille, d’après le catalogue de Sweep, avec la date de vérification.",
          "Precios de las evaluaciones y tarifas de activación de las prop firms de futuros, tamaño por tamaño, según el catálogo de Sweep, con la fecha de revisión."))

COSTS_LIVE = False   # held until the app's catalogue has every firm's prices (none for Lucid, Apex and MFFU on Oct 13: brief sent to the App session)
if COSTS_LIVE: GUIDES.insert(3, (GUIDE_COSTS, T("Prop firm costs, compared", "Le coût des prop firms, comparé", "El coste de las prop firms, comparado"),
                  T("Evaluation prices and activation fees, size by size.", "Prix des évaluations et frais d’activation, taille par taille.", "Precios de evaluación y tarifas de activación, tamaño por tamaño.")))

RULE_GUIDES = (GUIDE_CONS, GUIDE_DD, GUIDE_PAYOUT, GUIDE_SIZES, GUIDE_DAYS) + ((GUIDE_COSTS,) if COSTS_LIVE else ())   # firm-by-firm guides built from the catalogue
SYSTEM_PAGES.update(RULE_GUIDES)

# ---------------------------------------------------------------- firm vs firm (SEO brief, Oct 15, step 4): two firms, the guides' tables side by side
from pages18 import slug as _slug
SHORT = {"lucid": "Lucid", "topstep": "Topstep", "apex": "Apex", "tpt": "Take Profit Trader", "mffu": "MyFundedFutures", "alpha": "Alpha Futures"}
FIRM_VS = [("topstep", "apex"), ("apex", "lucid"), ("topstep", "tpt"), ("topstep", "lucid"), ("apex", "mffu")]
def vs_page_of(a, b): return f"prop-firms/{_slug(a)}-vs-{_slug(b)}.html"
NONE_TRACKED = T("none in the rules Sweep tracks", "aucune dans les règles suivies par Sweep", "ninguna en las reglas que sigue Sweep")

def _lower1(x): return x[:1].lower() + x[1:]
def _eval_or_funded(s): return (s.get("eval") or {}) if (s.get("eval") or {}).get("dd") else (s.get("funded") or {})

def _dd_kinds(f, lang, t):
    """[(firm name, « end of day (EOD Trail, Apex Legacy) »)]: the evaluation's drawdown, the funded account's when funded directly."""
    groups = {}
    for p in f["programs"]:
        r = _eval_or_funded(rep(p)); typ = r.get("dd_type")
        if typ not in DDT: continue
        label = _lower1(t(DDT[typ])) + ("" if (rep(p).get("eval") or {}).get("dd") else ", " + t(T("funded directly", "financé direct", "financiada directa")))
        groups.setdefault(label, []).append(p["name"])
    return [(f["name"], f"{k} ({', '.join(v)})") for k, v in groups.items()] or [(f["name"], t(NONE_TRACKED))]

def _dll_of(f, lang, t):
    out = []
    for p in f["programs"]:
        rs = [r for s in p["sizes"] for r in (s.get("eval") or {}, s.get("funded") or {}) if r.get("dll")]
        if rs: out.append(p["name"] + (" " + t(T("(option)", "(option)", "(opción)")) if all(r.get("dll_optional") for r in rs) else ""))
    return [(f["name"], x) for x in out] or [(f["name"], t(NONE_TRACKED))]

def _cons_of(f, lang, t):
    out = []
    for p in f["programs"]:
        e, fu, va = _vals(p, "eval", "consistency"), _vals(p, "funded", "consistency"), _variant_cons(p)
        funded = t(T("funded", "financé", "financiada"))
        parts = (([t(T("evaluation", "évaluation", "evaluación")) + " ≤ " + _pct_range(e, lang)] if e else []) + ([funded + " ≤ " + _pct_range(fu, lang)] if fu else [])
                 + [funded + " ≤ " + _pct_range(v, lang) + " " + t(T(f"with the {label['en']} option", f"avec l’option {label['fr']}", f"con la opción {label['es']}")) for label, v in va])
        if parts: out.append(f"{p['name']} ({', '.join(parts)})")
    return [(f["name"], x) for x in out] or [(f["name"], t(NONE_TRACKED))]

def _eod_of(f, lang, t):
    out = [p["name"] for p in f["programs"] if _eval_or_funded(rep(p)).get("dd_type") == "eod"]
    return [(f["name"], x) for x in out] or [(f["name"], t(T("none of its account types", "aucun de ses types de compte", "ninguno de sus tipos de cuenta")))]

def make_firm_vs(a_id, b_id):
    A, B = (next(f for f in presets.FIRMS if f["id"] == i) for i in (a_id, b_id))
    a, b = SHORT[a_id], SHORT[b_id]
    page_slug = vs_page_of(A, B)
    SYSTEM_PAGES.add(page_slug)
    CRUMBS[page_slug] = {l: f"{a} vs {b}" for l in LANGS}
    def page(lang, t):
        import ui
        hero = ui.hero(t, T(f"{a} vs {b}", f"{a} vs {b}", f"{a} vs {b}"), T("Prop firm rules, side by side.", "Les règles, côte à côte.", "Las reglas, lado a lado."),
            T(f"Account sizes, profit targets, drawdown, consistency, minimum days and payouts at {A['name']} and {B['name']}, from Sweep’s weekly check of each firm’s official pages. For guidance only: confirm on each firm’s site.",
              f"Tailles de compte, objectifs, drawdown, consistance, jours minimum et payouts chez {A['name']} et {B['name']}, tirés de la vérification hebdomadaire des pages officielles de chaque firme par Sweep. À titre indicatif : confirme sur le site de chaque firme.",
              f"Tamaños de cuenta, objetivos, drawdown, consistencia, días mínimos y payouts en {A['name']} y {B['name']}, tomados de la revisión semanal de las páginas oficiales de cada firma por Sweep. Solo como referencia: confirma en el sitio de cada firma."),
            kick_in_h1=True, cta=ui.btn(t(CREATE_FREE), SIGNUP, lg=True, attrs='data-track="signup_firmvs_hero"'))
        kinds = lambda f: t(T("account type", "type de compte", "tipo de cuenta") if len(f["programs"]) == 1 else T("account types", "types de compte", "tipos de cuenta"))
        summary = ui.stats([(A["name"], str(len(A["programs"])), kinds(A)), (B["name"], str(len(B["programs"])), kinds(B)),
                            (t(T("Checked", "Vérifiées le", "Revisadas el")), day(presets.CHECKED, lang), t(T("every week", "chaque semaine", "cada semana")))])
        both = [A, B]
        sizes = lambda f: ", ".join(kk(z) for z in sorted({s["size"] for p in f["programs"] for s in p["sizes"]}))
        glance = [(T("Account sizes", "Tailles de compte", "Tamaños de cuenta"), [(f["name"], x) for f in both for x in [sizes(f)]]),
                  (T("Drawdown in the evaluation", "Drawdown en évaluation", "Drawdown en la evaluación"), _dd_kinds(A, lang, t) + _dd_kinds(B, lang, t)),
                  (T("Daily loss limit", "Limite de perte du jour", "Límite de pérdida diaria"), _dll_of(A, lang, t) + _dll_of(B, lang, t)),
                  (T("Consistency rule", "Règle de consistance", "Regla de consistencia"), _cons_of(A, lang, t) + _cons_of(B, lang, t))]
        glance_html = '<ul class="list">' + "".join(f"<li><b>{t(h)}</b>{colon(lang)}{_by_firm(pairs, lang)}</li>" for h, pairs in glance) + "</ul>"
        every = lambda g, h: f'<p class="fine" style="margin-top:12px"><a href="{href(lang, g)}">{t(T("All firms, compared", "Toutes les firmes, comparées", "Todas las firmas, comparadas"))}<span class="sr">, {t(h)}</span> <span aria-hidden="true">→</span></a></p>'
        rows = lambda cells: _firm_rows(lang, t, lambda f, p: cells(lang, t, f, p), firms=both)
        topics = [("sizes", T("Account sizes and targets", "Tailles de compte et objectifs", "Tamaños de cuenta y objetivos"), f"<p>{t(SIZES_HOW)}</p>" + sizes_table(lang, t, A) + sizes_table(lang, t, B), GUIDE_SIZES),
                  ("drawdown", T("Drawdown", "Drawdown", "Drawdown"), _table(lang, t, *DD_HEADS, rows(dd_cells)), GUIDE_DD),
                  ("consistency", T("Consistency", "Consistance", "Consistencia"), _table(lang, t, *CONS_HEADS, rows(cons_cells)), GUIDE_CONS),
                  ("days", T("Minimum days", "Jours minimum", "Días mínimos"), _table(lang, t, *DAYS_HEADS, rows(days_cells)), GUIDE_DAYS),
                  ("payouts", T("Payouts", "Payouts", "Payouts"), _table(lang, t, *PAYOUT_HEADS, rows(payout_cells)), GUIDE_PAYOUT)]
        band = ui.band(t(TRACK_PROPS), t(RULES_FILL), ui.btn(t(CREATE_FREE), SIGNUP, lg=True, attrs='data-track="signup_firmvs_card"'))
        faqs = [(T(f"Which has an end-of-day drawdown, {a} or {b}?", f"Lequel a un drawdown de fin de journée, {a} ou {b} ?", f"¿Cuál tiene drawdown al cierre, {a} o {b}?"),
                 {l: _by_firm(_eod_of(A, l, lambda d, L=l: d[L]) + _eod_of(B, l, lambda d, L=l: d[L]), l) for l in LANGS}),
                (T(f"Do {a} and {b} have a consistency rule?", f"{a} et {b} ont-ils une règle de consistance ?", f"¿{a} y {b} tienen una regla de consistencia?"),
                 {l: _by_firm(_cons_of(A, l, lambda d, L=l: d[L]) + _cons_of(B, l, lambda d, L=l: d[L]), l) for l in LANGS}),
                (T(f"Which is better, {a} or {b}?", f"Lequel est le meilleur, {a} ou {b} ?", f"¿Cuál es mejor, {a} o {b}?"),
                 T("Sweep doesn’t recommend a firm, and nothing here is financial advice. Compare what matters for how you trade (the drawdown type, the daily loss limit, consistency and the payout conditions above), then confirm on each firm’s site.",
                   "Sweep ne recommande pas de firme, et rien ici n’est un conseil financier. Compare ce qui compte pour ta façon de trader (le type de drawdown, la limite du jour, la consistance et les conditions de payout ci-dessus), puis confirme sur le site de chaque firme.",
                   "Sweep no recomienda ninguna firma, y nada aquí es un consejo financiero. Compara lo que importa según tu forma de operar (el tipo de drawdown, el límite diario, la consistencia y las condiciones de payout de arriba) y confirma en el sitio de cada firma."))]
        firms_chips = [(page_of(f), {l: f["name"] for l in LANGS}) for f in both]
        others = [(vs_page_of(*(next(f for f in presets.FIRMS if f["id"] == i) for i in pr)), {l: f"{SHORT[pr[0]]} vs {SHORT[pr[1]]}" for l in LANGS}) for pr in FIRM_VS if pr != (a_id, b_id)]
        from pages17 import chiprow
        b_ = (ui.sec(summary, "t", "summary")
              + ui.sec(ui.head(t, None, T("The differences at a glance.", "Les différences en bref.", "Las diferencias de un vistazo.")) + f'<div class="read">{glance_html}</div>', "n", "glance")
              + "".join(ui.sec(ui.head(t, None, h) + body + every(g, h), "t", k) for k, h, body, g in topics)
              + ui.sec(f'<p class="fine vs-note">{_checked_note(lang, t)}</p>' + band, "n", "note")
              + ui.sec(ui.head(t, None, T("Questions", "Questions", "Preguntas")) + ui.qa(t, faqs)
                       + chiprow(lang, t, T("Firm pages", "Pages des firmes", "Páginas de las firmas"), firms_chips, 32)
                       + chiprow(lang, t, T("Compare too", "Compare aussi", "Compara también"), others, 12), "n", "faq", width="read")
              + ui.read_next(lang, t, ["prop-firms/index.html", "prop-firm-rule-changes.html", "how-we-verify-prop-firm-rules.html"]) + ui.final(lang, t))
        ld = jsonld({"@context": "https://schema.org", "@graph": [
            {"@type": "Article", "headline": f"{a} vs {b}", "inLanguage": lang, "datePublished": "2026-10-16", "dateModified": presets.CHECKED,
             "publisher": {"@id": f"https://{DOMAIN}/#org"}, "author": {"@type": "Organization", "name": "Sweep"}},
            {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": t(q), "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", t(x))}} for q, x in faqs]}]})
        title = T(f"{a} vs {b}: Rules Compared (2026) · Sweep", f"{a} vs {b} : règles comparées (2026) · Sweep", f"{a} vs {b}: reglas comparadas (2026) · Sweep")
        desc = T(f"{a} vs {b}, side by side: account sizes, profit targets, drawdown, consistency, minimum days and payout rules, checked every week.",
                 f"{a} vs {b}, côte à côte : tailles de compte, objectifs, drawdown, consistance, jours minimum et payouts, vérifiés chaque semaine.",
                 f"{a} vs {b}, lado a lado: tamaños de cuenta, objetivos, drawdown, consistencia, días mínimos y payouts, revisados cada semana.")
        tt = t(title) if len(t(title)) <= 60 else t(title).replace(" (2026)", "")   # long firm names: the year goes
        return _fr_nbsp(lang, tt, t(desc), hero + b_, ld)
    return page_slug, page

VS_PAGES = dict(make_firm_vs(a, b) for a, b in FIRM_VS)
