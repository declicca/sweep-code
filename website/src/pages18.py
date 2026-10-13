from core import *
import re
import presets

# Prop firm rule pages. Every number comes from the app's catalogue (presets.py); a value missing there is a row left out.
SLUG = {"tpt": "take-profit-trader", "mffu": "myfundedfutures", "alpha": "alpha-futures"}
TRACK_SINCE = "2026-10-09"   # first copy of the app's catalogue kept by the site: changes are logged from this date
NB, NNB = " ", " "

def slug(f): return SLUG.get(f["id"], f["id"])
def page_of(f): return f"prop-firms/{slug(f)}.html"

# ---------------------------------------------------------------- formats (same as the app: FR « 3 000 $ », ES « 3.000 $ »)
def usd(v, lang):
    s = f"{v:,.0f}" if float(v).is_integer() else f"{v:,.2f}"
    if lang == "en": return "$" + s
    return s.replace(",", "\0").replace(".", ",").replace("\0", NNB if lang == "fr" else ".") + NB + "$"
def colon(lang): return " : " if lang == "fr" else ": "
PLUS = {"en": "+", "fr": " et +", "es": " o más"}
def pc(v, lang): return f"{v:g}%" if lang == "en" else f"{v:g}{NNB}%"
def kk(size): return f"{size / 1000:g}K"
MONTHS = {"en": ["January","February","March","April","May","June","July","August","September","October","November","December"],
          "fr": ["janvier","février","mars","avril","mai","juin","juillet","août","septembre","octobre","novembre","décembre"],
          "es": ["enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"]}
def day(iso, lang):
    y, m, d = (int(x) for x in iso[:10].split("-")); mo = MONTHS[lang][m - 1]
    if lang == "en": return f"{mo} {d}, {y}"
    if lang == "fr": return f"{'1er' if d == 1 else d} {mo} {y}"
    return f"{d} de {mo} de {y}"
def anchor(f, p):
    a = re.sub(r"[^a-z0-9]+", "-", p["name"].lower()).strip("-")
    first = f["name"].split()[0].lower()
    return (a[len(first):].strip("-") if a.startswith(first) and len(a) > len(first) else a) or p.get("id", "rules")
def rep(p):
    """The size used for examples: 50K when the program has it."""
    sizes = p["sizes"]; return next((s for s in sizes if s["size"] == 50000), sizes[0])
def src_name(url):
    """« https://help.topstep.com/en/articles/8284233-topstep-payout-policy » → « Topstep payout policy »; a bare site → its domain."""
    path = [x for x in re.sub(r"^https?://", "", url).split("?")[0].split("/") if x]
    last = re.sub(r"^\d+-", "", path[-1]) if len(path) > 1 else ""
    if not last or "." in last: return re.sub(r"^www\.", "", path[0])
    words_ = last.replace("-", " ").replace("_", " ").strip()
    return words_[:1].upper() + words_[1:]
def checked_of(f):
    ds = [v["date"] for p in f["programs"] for v in p.get("verified", []) if v.get("date")]
    return max(ds) if ds else presets.CHECKED
def source_of(f):
    for p in f["programs"]:
        for v in p.get("verified", []):
            if v.get("url"): return v["url"]
    return (f.get("sources") or [""])[0]

# ---------------------------------------------------------------- rows: (label, value of a size, format)
DDT = {"eod": T("End of day","Fin de journée","Al cierre"), "trade": T("Real time","Temps réel","Tiempo real"), "static": T("Static","Fixe","Fijo")}
def _ph(s, ph): return s.get(ph) or {}
def _po(r): return r.get("payout") or {}

def phase_rows(lang, t, ph):
    """Rules of a phase (eval / funded / live): `r` is that phase's dict, `s` the size."""
    U = lambda v: usd(v, lang)
    return [
     (T("Starting balance","Solde de départ","Saldo inicial"), lambda r, s: (r.get("start_pct"), s["size"]) if r.get("start_pct") else None,
      lambda v: f"{U(v[1] * v[0] / 100)} ({pc(v[0], lang)})"),
     (T("Profit target","Objectif de profit","Objetivo de beneficio"), lambda r, s: r.get("target"), U),
     (T("Max loss","Perte max","Pérdida máx."), lambda r, s: r.get("dd"), U),
     (T("Balance to stay above","Solde à garder au-dessus de","Saldo mínimo"), lambda r, s: r.get("floor"), U),
     (T("Drawdown type","Type de drawdown","Tipo de drawdown"), lambda r, s: r.get("dd_type"), lambda v: t(DDT[v]) if v in DDT else v),
     (T("Trailing stops at","Le drawdown cesse de suivre à","El drawdown deja de seguir en"), lambda r, s: ("lock", r.get("dd_lock_offset") or 0) if r.get("dd_lock") and r.get("dd_type") != "static" else None,
      lambda v: t(T("Starting balance","Solde de départ","Saldo inicial")) + (f" + {U(v[1])}" if v[1] else "")),
     (T("Daily loss limit","Limite de perte du jour","Límite de pérdida diaria"), lambda r, s: (r.get("dll"), bool(r.get("dll_optional"))) if r.get("dll") else None,
      lambda v: U(v[0]) + (" " + t(T("(option)","(option)","(opción)")) if v[1] else "")),
     (T("Consistency","Consistance","Consistencia"), lambda r, s: r.get("consistency"),
      lambda v: t(T("Best day ≤ ","Meilleur jour ≤ ","Mejor día ≤ ")) + pc(v, lang)),
     (T("Minimum days","Jours minimum","Días mínimos"), lambda r, s: r.get("min_days"), lambda v: f"{v:g}"),
     (T("Max contracts","Contrats max","Contratos máx."), lambda r, s: r.get("max_minis"), lambda v: f"{v:g} mini" + ("s" if v != 1 else "")),
    ]

def payout_rows(lang, t):
    U = lambda v: usd(v, lang)
    return [
     (T("Winning days","Jours gagnants","Días ganadores"), lambda po, s: (po.get("win_days"), po.get("win_min")) if po.get("win_days") else None,
      lambda v: (f"{v[0]:g} " + t(T("of ","de ","de ")) + U(v[1]) + PLUS[lang]) if v[1] else f"{v[0]:g}"),
     (T("Trading days","Jours tradés","Días operados"), lambda po, s: po.get("trade_days"), lambda v: f"{v:g}"),
     (T("Days between payouts","Jours entre deux payouts","Días entre payouts"), lambda po, s: po.get("cycle_days"), lambda v: f"{v:g}"),
     (T("Profitable since the last payout","Profitable depuis le dernier payout","Rentable desde el último payout"), lambda po, s: True if po.get("cycle_pos") else None,
      lambda v: t(T("Required","Obligatoire","Obligatorio"))),
     (T("Profit before the 1st payout","Profit avant le 1er payout","Beneficio antes del 1.er payout"), lambda po, s: po.get("first_min"), U),
     (T("Profit since the last payout","Profit depuis le dernier payout","Beneficio desde el último payout"), lambda po, s: po.get("cycle_min"), U),
     (T("Balance to keep","Solde à garder","Saldo a mantener"), lambda po, s: po.get("min_bal"), U),
     (T("Minimum payout","Payout minimum","Payout mínimo"), lambda po, s: po.get("min"), U),
     (T("Maximum per payout","Maximum par payout","Máximo por payout"), lambda po, s: po.get("max"), U),
     (T("Maximum with the daily loss limit option","Maximum avec l’option limite du jour","Máximo con la opción de límite diario"), lambda po, s: po.get("max_dll"), U),
     (T("Payout caps, in order","Plafonds des payouts, dans l’ordre","Topes de los payouts, en orden"), lambda po, s: po.get("ladder"),
      lambda v: " / ".join(U(x) if x is not None else "∞" for x in v)),
     (T("Max % of the profit","Max % du profit","Máx. % del beneficio"), lambda po, s: po.get("max_pct"), lambda v: pc(v, lang)),
     (T("Max number of payouts","Nombre max de payouts","Número máx. de payouts"), lambda po, s: po.get("max_payouts"), lambda v: f"{v:g}"),
     (T("Profit split","Partage des profits","Reparto de beneficios"), lambda po, s: po.get("split_pct"), lambda v: pc(v, lang)),
    ]

def price_rows(lang, t):
    return [
     (T("Evaluation","Évaluation","Evaluación"), lambda pr, s: (pr.get("eval"), pr.get("eval_period")) if pr.get("eval") is not None else None,
      lambda v: usd(v[0], lang) + (t(T("/month","/mois","/mes")) if v[1] == "month" else "")),
     (T("Activation fee","Frais d’activation","Tarifa de activación"), lambda pr, s: pr.get("activation"), lambda v: usd(v, lang) if v else t(T("None","Aucuns","Ninguna"))),
    ]

def groups_of(lang, t, sizes, variant=None):
    """(title, rows, value-of-size getter) for each block of the table. `variant` = (option id, phase) merged like the app does."""
    def ph(s, name):
        r = dict(_ph(s, name))
        if variant and name == variant[1]:
            for k, v in ((s.get("variants") or {}).get(variant[0], {}).get(name) or {}).items():
                if v is None: r.pop(k, None)
                else: r[k] = v
        return r
    G = []
    if not variant:
        G.append((T("Evaluation","Évaluation","Evaluación"), phase_rows(lang, t, "eval"), lambda s: ph(s, "eval")))
    G.append((T("Funded account","Compte financé","Cuenta financiada"), phase_rows(lang, t, "funded"), lambda s: ph(s, "funded")))
    G.append((T("Payouts, funded account","Payouts, compte financé","Payouts, cuenta financiada"), payout_rows(lang, t), lambda s: _po(ph(s, "funded"))))
    if not variant:
        if any(s.get("live") for s in sizes):
            G.append((T("Live account","Compte live","Cuenta live"), phase_rows(lang, t, "live"), lambda s: _ph(s, "live")))
            G.append((T("Payouts, live account","Payouts, compte live","Payouts, cuenta live"), payout_rows(lang, t), lambda s: _po(_ph(s, "live"))))
        elif any(_ph(s, "funded").get("payout_live") for s in sizes):
            G.append((T("Payouts once live","Payouts une fois en live","Payouts ya en live"), payout_rows(lang, t), lambda s: _ph(s, "funded").get("payout_live") or {}))
        G.append((T("Fees","Frais","Tarifas"), price_rows(lang, t), lambda s: s.get("price") or {}))
    return G

def table(lang, t, sizes, groups, only_diff_from=None):
    cols = len(sizes)
    head = (f'<thead><tr><th scope="col">{t(T("Account size","Taille du compte","Tamaño de la cuenta"))}</th>'
            + "".join(f'<th scope="col" class="cc c{i}">{kk(s["size"])}</th>' for i, s in enumerate(sizes)) + "</tr></thead>")
    body = ""
    for gi, (gt, rows, get) in enumerate(groups):
        out = []
        for label, val, fmt in rows:
            vals = [val(get(s), s) for s in sizes]
            if all(v is None for v in vals): continue          # not in the catalogue: the row is left out
            if only_diff_from is not None:
                base = [val(only_diff_from[gi][2](s), s) for s in sizes]
                if vals == base: continue
            out.append(f'<tr><th scope="row">{t(label)}</th>' + "".join(f'<td class="cc c{i}">{fmt(v) if v is not None else "—"}</td>' for i, v in enumerate(vals)) + "</tr>")
        if out: body += f'<tr class="grp"><th colspan="{cols + 1}" scope="colgroup">{t(gt)}</th></tr>' + "".join(out)
    # on phones, one account size at a time (site.js shows the switch; without JavaScript, the whole table)
    seg = ("" if cols < 2 else f'<div class="seg sizes" role="group" aria-label="{t(T("Account size","Taille du compte","Tamaño de la cuenta"))}" hidden>'
           + "".join(f'<button type="button" data-size="{s["size"]}" aria-pressed="{"true" if i == 0 else "false"}">{kk(s["size"])}</button>' for i, s in enumerate(sizes)) + "</div>")
    return f'<div class="rules-tbl">{seg}<div class="cmp-wrap"><table class="cmp rules n{cols}">{head}<tbody>{body}</tbody></table></div></div>' if body else ""

# ---------------------------------------------------------------- what it means in practice (generated from the rules, reviewed before publishing)
def practice(lang, t, f, p):
    s = rep(p); size = kk(s["size"]); U = lambda v: usd(v, lang); E, F, L = _ph(s, "eval"), _ph(s, "funded"), _ph(s, "live")
    pts = []
    D = E if E.get("dd") else F
    if D.get("dd") and D.get("dd_type") in DDT:
        pts.append({"eod": T(f"The max loss ({U(E['dd'])} on the {size}) follows your highest end-of-day balance: a peak during the day doesn’t move it.",
                             f"La perte max ({U(E['dd'])} sur le {size}) suit ton solde de fin de journée le plus haut : un sommet pendant la journée ne la déplace pas.",
                             f"La pérdida máx. ({U(E['dd'])} en la {size}) sigue tu saldo de cierre más alto: un máximo durante el día no la mueve."),
                    "trade": T(f"The max loss ({U(E['dd'])} on the {size}) follows your highest balance in real time, during the day too.",
                               f"La perte max ({U(E['dd'])} sur le {size}) suit ton solde le plus haut en temps réel, pendant la journée aussi.",
                               f"La pérdida máx. ({U(E['dd'])} en la {size}) sigue tu saldo más alto en tiempo real, también durante el día."),
                    "static": T(f"The max loss ({U(E['dd'])} on the {size}) is fixed: it doesn’t move up with your profit.",
                                f"La perte max ({U(E['dd'])} sur le {size}) est fixe : elle ne monte pas avec ton profit.",
                                f"La pérdida máx. ({U(E['dd'])} en la {size}) es fija: no sube con tu beneficio.")}[D["dd_type"]] if D is E else
                   {"eod": T(f"The max loss ({U(F['dd'])} on the {size}) follows your highest end-of-day balance: a peak during the day doesn’t move it.", f"La perte max ({U(F['dd'])} sur le {size}) suit ton solde de fin de journée le plus haut : un sommet pendant la journée ne la déplace pas.", f"La pérdida máx. ({U(F['dd'])} en la {size}) sigue tu saldo de cierre más alto: un máximo durante el día no la mueve."),
                    "trade": T(f"The max loss ({U(F['dd'])} on the {size}) follows your highest balance in real time, during the day too.", f"La perte max ({U(F['dd'])} sur le {size}) suit ton solde le plus haut en temps réel, pendant la journée aussi.", f"La pérdida máx. ({U(F['dd'])} en la {size}) sigue tu saldo más alto en tiempo real, también durante el día."),
                    "static": T(f"The max loss ({U(F['dd'])} on the {size}) is fixed: it doesn’t move up with your profit.", f"La perte max ({U(F['dd'])} sur le {size}) est fixe : elle ne monte pas avec ton profit.", f"La pérdida máx. ({U(F['dd'])} en la {size}) es fija: no sube con tu beneficio.")}[D["dd_type"]])
    if D is E and F.get("dd_type") in DDT and E.get("dd_type") != F.get("dd_type"):
        pts.append({"eod": T("Once funded, it follows your end-of-day balance instead.", "Une fois financé, elle suit plutôt ton solde de fin de journée.", "Ya financiada, sigue en cambio tu saldo al cierre."),
                    "trade": T("Once funded, it follows your balance in real time instead.", "Une fois financé, elle suit plutôt ton solde en temps réel.", "Ya financiada, sigue en cambio tu saldo en tiempo real."),
                    "static": T("Once funded, it becomes fixed.", "Une fois financé, elle devient fixe.", "Ya financiada, pasa a ser fija.")}[F["dd_type"]])
    if F.get("dd_lock") and F.get("dd_type") != "static":
        off = F.get("dd_lock_offset") or 0
        pts.append(T("Once funded, it stops trailing when it reaches your starting balance" + (f" + {U(off)}" if off else "") + ".",
                     "Une fois financé, elle arrête de suivre quand elle atteint ton solde de départ" + (f" + {U(off)}" if off else "") + ".",
                     "Ya financiada, deja de seguir cuando llega a tu saldo inicial" + (f" + {U(off)}" if off else "") + "."))
    dll = F.get("dll") or E.get("dll")
    if dll and (F.get("dll_optional") or E.get("dll_optional")):
        po = _po(F)
        more = (T(f" With it, the maximum per payout goes from {U(po['max'])} to {U(po['max_dll'])} on the {size}.", f" Avec elle, le maximum par payout passe de {U(po['max'])} à {U(po['max_dll'])} sur le {size}.", f" Con él, el máximo por payout pasa de {U(po['max'])} a {U(po['max_dll'])} en la {size}.")
                if po.get("max") and po.get("max_dll") else T("", "", ""))
        pts.append({l: v + more[l] for l, v in T("The daily loss limit is an option you choose when you buy.", "La limite de perte du jour est une option que tu choisis à l’achat.", "El límite de pérdida diaria es una opción que eliges al comprar.").items()})
    elif dll:
        pts.append(T(f"On the {size}, a day can’t lose more than {U(dll)}: that’s the daily loss limit.", f"Sur le {size}, une journée ne peut pas perdre plus de {U(dll)} : c’est la limite de perte du jour.", f"En la {size}, un día no puede perder más de {U(dll)}: es el límite de pérdida diaria."))
    if E.get("consistency") and E.get("target"):
        c = E["consistency"]; mx = E["target"] * c / 100
        pts.append(T(f"To pass, your best day can’t be more than {pc(c, lang)} of your profit: right at the {U(E['target'])} target ({size}), that’s {U(mx)} at most in one day.",
                     f"Pour réussir, ton meilleur jour ne peut pas dépasser {pc(c, lang)} de ton profit : pile à l’objectif de {U(E['target'])} ({size}), c’est {U(mx)} au plus en une journée.",
                     f"Para aprobar, tu mejor día no puede superar el {pc(c, lang)} de tu beneficio: justo en el objetivo de {U(E['target'])} ({size}), son {U(mx)} como máximo en un día."))
    if F.get("consistency"):
        pts.append(T(f"Once funded, consistency is checked at each payout: your best day can be at most {pc(F['consistency'], lang)} of the profit since your last payout.",
                     f"Une fois financé, la consistance est vérifiée à chaque payout : ton meilleur jour peut représenter au plus {pc(F['consistency'], lang)} du profit depuis ton dernier payout.",
                     f"Ya financiada, la consistencia se revisa en cada payout: tu mejor día puede ser como máximo el {pc(F['consistency'], lang)} del beneficio desde tu último payout."))
    pay = payout_sentence(f, p, s, None)
    if pay: pts.append(pay)
    if L.get("start_pct"):
        st = s["size"] * L["start_pct"] / 100
        pts.append(T(f"In a live account, you start with {pc(L['start_pct'], lang)} of the size ({U(st)} on the {size})" + (f" and must stay above {U(L['floor'])}." if L.get("floor") else "."),
                     f"En compte live, tu commences avec {pc(L['start_pct'], lang)} de la taille ({U(st)} sur le {size})" + (f" et tu dois rester au-dessus de {U(L['floor'])}." if L.get("floor") else "."),
                     f"En cuenta live, empiezas con el {pc(L['start_pct'], lang)} del tamaño ({U(st)} en la {size})" + (f" y debes mantenerte por encima de {U(L['floor'])}." if L.get("floor") else ".")))
    return [t(x) for x in pts[:5]]

def payout_sentence(f, p, s, label):
    """« To request a payout on the 50K (Standard option): … » in the 3 languages, or None. `label` replaces « the 50K » (FAQ)."""
    po = _po(_ph(s, "funded"))
    if not po: return None
    size = kk(s["size"])
    opt = next(((o, c) for o in (p.get("options") or []) if o.get("phase") == "funded" for c in (o.get("choices") or []) if c["id"] == o.get("default")), None)
    out = {}
    for l in LANGS:
        U = lambda v: usd(v, l)
        bits = []
        if po.get("win_days"): bits.append({"en": f"{po['win_days']:g} winning days" + (f" of {U(po['win_min'])} or more" if po.get("win_min") else ""), "fr": f"{po['win_days']:g} jours gagnants" + (f" de {U(po['win_min'])} et +" if po.get("win_min") else ""), "es": f"{po['win_days']:g} días ganadores" + (f" de {U(po['win_min'])} o más" if po.get("win_min") else "")}[l])
        if po.get("trade_days"): bits.append({"en": f"{po['trade_days']:g} traded days", "fr": f"{po['trade_days']:g} jours tradés", "es": f"{po['trade_days']:g} días operados"}[l])
        if po.get("cycle_days"): bits.append({"en": f"{po['cycle_days']:g} days since the last payout", "fr": f"{po['cycle_days']:g} jours depuis le dernier payout", "es": f"{po['cycle_days']:g} días desde el último payout"}[l])
        if po.get("cycle_pos") and not po.get("cycle_min"): bits.append({"en": "a profit since the last payout", "fr": "un profit depuis le dernier payout", "es": "un beneficio desde el último payout"}[l])
        if po.get("first_min") and po.get("cycle_min"):   # the app's wording (Alpha Direct)
            bits.append({"en": f"{U(po['first_min'])} of profit before the 1st, then {U(po['cycle_min'])} before each next one", "fr": f"{U(po['first_min'])} de profit avant le 1er, puis {U(po['cycle_min'])} avant chaque suivant", "es": f"{U(po['first_min'])} de beneficio antes del 1.º, luego {U(po['cycle_min'])} antes de cada siguiente"}[l])
        elif po.get("first_min"): bits.append({"en": f"{U(po['first_min'])} of profit before the 1st payout", "fr": f"{U(po['first_min'])} de profit avant le 1er payout", "es": f"{U(po['first_min'])} de beneficio antes del 1.er payout"}[l])
        elif po.get("cycle_min"): bits.append({"en": f"at least {U(po['cycle_min'])} of profit since the last payout", "fr": f"au moins {U(po['cycle_min'])} de profit depuis le dernier payout", "es": f"al menos {U(po['cycle_min'])} de beneficio desde el último payout"}[l])
        if po.get("min_bal"): bits.append({"en": f"a balance above {U(po['min_bal'])}", "fr": f"un solde au-dessus de {U(po['min_bal'])}", "es": f"un saldo por encima de {U(po['min_bal'])}"}[l])
        lad = po.get("ladder")
        caps = " / ".join(U(x) if x is not None else {"en": "no cap", "fr": "sans plafond", "es": "sin tope"}[l] for x in lad) if lad else ""
        rng = ({"en": f"from {U(po['min'])} per payout, capped at {caps} for payouts 1 to {len(lad)}", "fr": f"à partir de {U(po['min'])} par payout, avec des plafonds de {caps} pour les payouts 1 à {len(lad)}", "es": f"desde {U(po['min'])} por payout, con topes de {caps} para los payouts 1 a {len(lad)}"}[l] if lad and po.get("min")
               else {"en": f"from {U(po['min'])} to {U(po['max'])} per payout", "fr": f"de {U(po['min'])} à {U(po['max'])} par payout", "es": f"de {U(po['min'])} a {U(po['max'])} por payout"}[l] if po.get("min") and po.get("max")
               else {"en": f"at least {U(po['min'])} per payout", "fr": f"au moins {U(po['min'])} par payout", "es": f"al menos {U(po['min'])} por payout"}[l] if po.get("min") else "")
        if not bits and not rng: return None
        where = label[l] if label else {"en": f"the {size}", "fr": f"le {size}", "es": f"la {size}"}[l]
        if opt: where += {"en": f" ({opt[1]['label'][l]} option)", "fr": f" (option {opt[1]['label'][l]})", "es": f" (opción {opt[1]['label'][l]})"}[l]
        if not bits:   # only an amount: « On the 50K, each payout is at least $500. »
            one = ({"en": f"each payout is between {U(po['min'])} and {U(po['max'])}", "fr": f"chaque payout va de {U(po['min'])} à {U(po['max'])}", "es": f"cada payout va de {U(po['min'])} a {U(po['max'])}"}[l] if po.get("min") and po.get("max") and not lad
                   else {"en": f"each payout is at least {U(po['min'])}", "fr": f"chaque payout est d’au moins {U(po['min'])}", "es": f"cada payout es de al menos {U(po['min'])}"}[l] if po.get("min") and not lad else rng)
            txt = {"en": "On ", "fr": "Sur ", "es": "En "}[l] + where + ", " + one
            if po.get("split_pct"): txt += {"en": f"; you keep {pc(po['split_pct'], l)}", "fr": f" ; tu gardes {pc(po['split_pct'], l)}", "es": f"; te quedas con el {pc(po['split_pct'], l)}"}[l]
            if po.get("max_payouts") and not lad: txt += {"en": f", up to {po['max_payouts']:g} payouts", "fr": f", jusqu’à {po['max_payouts']:g} payouts", "es": f", hasta {po['max_payouts']:g} payouts"}[l]
            out[l] = txt + "."; continue
        txt = {"en": "To request a payout on ", "fr": "Pour demander un payout sur ", "es": "Para pedir un payout en "}[l] + where + colon(l) + (", ".join(bits[:-1]) + {"en": " and ", "fr": " et ", "es": " y "}[l] + bits[-1] if len(bits) > 1 else bits[0])
        if rng:
            txt += ({"en": ", then ", "fr": ", puis ", "es": ", luego "}[l] if bits else "") + ({"en": f"up to {pc(po['max_pct'], l)} of your profit, ", "fr": f"jusqu’à {pc(po['max_pct'], l)} de ton profit, ", "es": f"hasta el {pc(po['max_pct'], l)} de tu beneficio, "}[l] if po.get("max_pct") else "") + rng
        if po.get("split_pct"): txt += {"en": f"; you keep {pc(po['split_pct'], l)}", "fr": f" ; tu gardes {pc(po['split_pct'], l)}", "es": f"; te quedas con el {pc(po['split_pct'], l)}"}[l]
        if po.get("max_payouts") and not lad: txt += {"en": f"; up to {po['max_payouts']:g} payouts", "fr": f" ; jusqu’à {po['max_payouts']:g} payouts", "es": f"; hasta {po['max_payouts']:g} payouts"}[l]
        out[l] = txt + "."
    return out

# ---------------------------------------------------------------- page
RULE_NAMES = {"eval": T("evaluation","évaluation","evaluación"), "funded": T("funded","financé","financiada"), "live": T("live","live","live")}

FIELD = {"target": T("Profit target","Objectif de profit","Objetivo de beneficio"), "dd": T("Max loss","Perte max","Pérdida máx."), "dd_type": T("Drawdown type","Type de drawdown","Tipo de drawdown"),
         "dll": T("Daily loss limit","Limite de perte du jour","Límite de pérdida diaria"), "consistency": T("Consistency","Consistance","Consistencia"), "min_days": T("Minimum days","Jours minimum","Días mínimos"),
         "max_minis": T("Max contracts","Contrats max","Contratos máx."), "floor": T("Balance to stay above","Solde à garder au-dessus de","Saldo mínimo"), "start_pct": T("Starting balance","Solde de départ","Saldo inicial"),
         "dd_lock": T("Trailing stops at the start","Suivi bloqué au départ","Drawdown fijo en el inicio"), "dd_lock_offset": T("Trailing stops at start +","Suivi bloqué à départ +","Drawdown fijo en inicio +"),
         "win_days": T("Winning days","Jours gagnants","Días ganadores"), "win_min": T("Minimum per winning day","Minimum par jour gagnant","Mínimo por día ganador"), "trade_days": T("Trading days","Jours tradés","Días operados"),
         "cycle_days": T("Days between payouts","Jours entre deux payouts","Días entre payouts"), "cycle_pos": T("Profitable since the last payout","Profitable depuis le dernier payout","Rentable desde el último payout"),
         "cycle_min": T("Profit since the last payout","Profit depuis le dernier payout","Beneficio desde el último payout"), "first_min": T("Profit before the 1st payout","Profit avant le 1er payout","Beneficio antes del 1.er payout"), "min_bal": T("Balance to keep","Solde à garder","Saldo a mantener"),
         "min": T("Minimum payout","Payout minimum","Payout mínimo"), "max": T("Maximum per payout","Maximum par payout","Máximo por payout"), "max_dll": T("Maximum with the daily loss limit option","Maximum avec l’option limite du jour","Máximo con la opción de límite diario"),
         "ladder": T("Payout caps","Plafonds des payouts","Topes de los payouts"), "max_pct": T("Max % of the profit","Max % du profit","Máx. % del beneficio"), "max_payouts": T("Max number of payouts","Nombre max de payouts","Número máx. de payouts"),
         "split_pct": T("Profit split","Partage des profits","Reparto de beneficios"), "eval": T("Evaluation price","Prix de l’évaluation","Precio de la evaluación"), "activation": T("Activation fee","Frais d’activation","Tarifa de activación")}
MONEY = {"target", "dd", "dll", "floor", "dd_lock_offset", "win_min", "cycle_min", "first_min", "min_bal", "min", "max", "max_dll", "eval", "activation"}
PCT = {"consistency", "start_pct", "max_pct", "split_pct"}
PHASE = {"eval": T("evaluation","évaluation","evaluación"), "funded": T("funded","financé","financiada"), "live": T("live","live","live"), "price": T("fees","frais","tarifas")}

def change_label(path, lang, t):
    """« funded.payout.max » → « Maximum per payout (funded) »; None for what isn't a rule (dates, notes)."""
    parts = path.split(".")
    if parts[0] == "variants" and len(parts) > 2: parts = parts[2:]
    phase, field = parts[0], parts[-1]
    if field not in FIELD or phase not in PHASE: return None
    return f"{t(FIELD[field])} ({t(PHASE[phase])})"

def change_value(path, v, lang, t):
    field = path.split(".")[-1]
    if v is None: return "—"
    if isinstance(v, bool): return t(T("yes","oui","sí")) if v else t(T("no","non","no"))
    if isinstance(v, list): return " / ".join(usd(x, lang) if x is not None else "∞" for x in v)
    if field in MONEY and isinstance(v, (int, float)): return usd(v, lang)
    if field in PCT and isinstance(v, (int, float)): return pc(v, lang)
    if field == "dd_type" and v in DDT: return t(DDT[v])
    return str(v)

def history(lang, t, f):
    # only a value that changed: a value that appears or disappears is the catalogue being completed or corrected, not a rule change
    rows = [c for c in presets.CHANGES if c.get("firm") == f["id"] and c.get("old") is not None and c.get("new") is not None and change_label(c.get("rule", ""), lang, t)][:8]
    if not rows:
        return f'<p>{t(T(f"No rule change recorded since our first check on {day(TRACK_SINCE, lang)}.", f"Aucun changement de règle enregistré depuis notre première vérification, le {day(TRACK_SINCE, lang)}.", f"Ningún cambio de regla registrado desde nuestra primera revisión, el {day(TRACK_SINCE, lang)}."))}</p>'
    prog = {p.get("id", p["name"]): p["name"] for p in f["programs"]}
    items = "".join(f'<li><b>{day(c["date"], lang)}</b> · {prog.get(c["program"], c["program"])} {kk(c["size"])} · {change_label(c["rule"], lang, t)}{colon(lang)}{change_value(c["rule"], c["old"], lang, t)} → {change_value(c["rule"], c["new"], lang, t)}</li>' for c in rows)
    return f'<ul class="list">{items}</ul>'

def make_rules_page(f):
    CRUMBS[page_of(f)] = f["name"]
    def page(lang, t):
        name, progs = f["name"], f["programs"]
        when, src = checked_of(f), source_of(f)
        sizes_all = sorted({s["size"] for p in progs for s in p["sizes"]})
        verified = T(f'Last verified: {day(when, "en")}, against <a href="{src}" rel="nofollow noopener" target="_blank">{poss(name)} official pages</a>.',
                     f'Dernière vérification : {day(when, "fr")}, sur <a href="{src}" rel="nofollow noopener" target="_blank">les pages officielles de {name}</a>.',
                     f'Última verificación: {day(when, "es")}, en <a href="{src}" rel="nofollow noopener" target="_blank">las páginas oficiales de {name}</a>.')
        names = ", ".join(p["name"] for p in progs)
        rng = f"{kk(sizes_all[0])}" + (f" – {kk(sizes_all[-1])}" if len(sizes_all) > 1 else "")
        if len(progs) == 1:
            lead = T(f"Sweep tracks one {name} account type: the {names}, {rng}.", f"Sweep suit un type de compte chez {name} : le {names}, {rng}.", f"Sweep sigue un tipo de cuenta de {name}: el {names}, {rng}.")
        else:
            lead = T(f"Sweep tracks {len(progs)} {name} account types: {names}, {rng}.", f"Sweep suit {len(progs)} types de compte chez {name} : {names}, {rng}.", f"Sweep sigue {len(progs)} tipos de cuenta de {name}: {names}, {rng}.")
        if len(progs) <= 2:
            lead = {l: lead[l] + " " + " ".join((p.get("note") or {}).get(l, "") for p in progs).strip() for l in LANGS}
        hero = (f'<div class="page-hero"><div class="wrap"><span class="kick">{t(T("Prop firms","Prop firms","Prop firms"))}</span>'
                f'<h1 class="wu">{words(t(T(f"{name} rules, explained.", f"Les règles de {name}, expliquées.", f"Las reglas de {name}, explicadas.")))}</h1>'
                f'<p class="lead rise d3">{t(lead)}</p><p class="fine rise d4 verified">{t(verified)}</p></div></div>')
        jump = ("" if len(progs) < 2 else '<p class="firm-others">' + "".join(f'<a href="#{anchor(f, p)}">{p["name"]}</a>' for p in progs) + "</p>")
        secs = ""
        for p in progs:
            sizes = p["sizes"]; G = groups_of(lang, t, sizes)
            note = (p.get("note") or {}).get(lang, "")
            sec = f'<h2 id="{anchor(f, p)}">{p["name"]}</h2>' + (f"<p>{note}</p>" if note and len(progs) > 2 else "") + table(lang, t, sizes, G)
            for o in p.get("options") or []:
                for c in o.get("choices") or []:
                    if c["id"] == o.get("default") or not any(((s.get("variants") or {}).get(c["id"]) or {}).get(o["phase"]) for s in sizes): continue
                    VG = groups_of(lang, t, sizes, (c["id"], o["phase"]))
                    base = [g for g in G if g[0] in [vg[0] for vg in VG]]
                    sub = (c.get("sub") or {}).get(lang, "")
                    sec += (f'<h3>{(o.get("label") or {}).get(lang, "")} : {c["label"][lang]}</h3>'.replace(" : ", ": " if lang != "fr" else " : ")
                            + (f'<p>{sub}. {t(T("Only the rules that differ from the default option:","Seules les règles qui diffèrent de l’option par défaut :","Solo las reglas que cambian respecto a la opción por defecto:"))}</p>')
                            + table(lang, t, sizes, VG, only_diff_from=base))
            pts = practice(lang, t, f, p)
            if pts: sec += f'<h3>{t(T("In practice","En pratique","En la práctica"))}</h3>' + "<ul class=\"list\">" + "".join(f"<li>{x}</li>" for x in pts) + "</ul>"
            vs = [v for v in p.get("verified", []) if v.get("url")] or [{"url": u, "date": presets.CHECKED} for u in (f.get("sources") or [])[:1]]
            if vs:
                sec += '<p class="fine">' + t(T("Sources","Sources","Fuentes")) + " · " + " · ".join(f'<a href="{v["url"]}" rel="nofollow noopener" target="_blank">{src_name(v["url"])}</a> ({day(v.get("date") or presets.CHECKED, lang)})' for v in vs) + "</p>"
            secs += f'<section class="rule rules-prog"><div class="wrap narrow"><article class="article">{sec}</article></div></section>'
        disclaimer = T(f"Sweep is not affiliated with {name}. Rules can change at any time; always confirm on {poss(name)} official site. Values are shown for information, from Sweep’s weekly check of {poss(name)} pages.",
                       f"Sweep n’est pas affilié à {name}. Les règles peuvent changer à tout moment ; confirme toujours sur le site officiel de {name}. Valeurs présentées à titre indicatif, tirées de la vérification hebdomadaire des pages de {name} par Sweep.",
                       f"Sweep no está afiliado a {name}. Las reglas pueden cambiar en cualquier momento; confirma siempre en el sitio oficial de {name}. Valores a título informativo, tomados de la revisión semanal de las páginas de {name} por Sweep.")
        card = (f'<section style="padding-top:0"><div class="wrap narrow"><div class="calc-act"><div><b>{t(T(f"Track your {name} account in Sweep.", f"Suis ton compte {name} dans Sweep.", f"Sigue tu cuenta de {name} en Sweep."))}</b>'
                f'<p data-nolinks>{t(T("These rules fill in automatically.", "Ces règles se remplissent toutes seules.", "Estas reglas se rellenan solas."))}</p></div>'
                f'<a class="btn btn-primary" href="{SIGNUP}" data-track="signup_rules_card">{t(CREATE_FREE)}</a></div></div></section>')
        b = (f'<section style="padding-top:8px"><div class="wrap narrow">{jump}</div></section>' if jump else "") + secs + card
        b += f'<section style="padding-top:0"><div class="wrap narrow"><p class="fine">{t(disclaimer)}</p></div></section>'
        b += (f'<section class="rule"><div class="wrap narrow"><div class="head"><h2>{t(T("Rule changes","Changements de règles","Cambios de reglas"))}</h2></div>{history(lang, t, f)}</div></section>')
        b += split(t, T("Track it","Suis-le","Síguelo"), T(f"Track your {name} account in Sweep.", f"Suis ton compte {name} dans Sweep.", f"Sigue tu cuenta de {name} en Sweep."),
                   T(f"Pick {name} and your account type: these rules fill in, and Sweep counts your payout conditions on every trade. Free forever, no card.",
                     f"Choisis {name} et ton type de compte : ces règles se remplissent, et Sweep compte tes conditions de payout à chaque trade. Gratuit pour toujours, sans carte.",
                     f"Elige {name} y tu tipo de cuenta: estas reglas se completan y Sweep cuenta tus condiciones de payout en cada operación. Gratis para siempre, sin tarjeta."),
                   [T(f"<b>Rules prefilled</b> for every {name} account type and size, each value editable", f"<b>Règles préremplies</b> pour chaque type et taille de compte {name}, chaque valeur modifiable", f"<b>Reglas precargadas</b> para cada tipo y tamaño de cuenta de {name}, cada valor editable"),
                    T("<b>Every trade checked:</b> target, room above the max loss, today’s limit, consistency and payout readiness in %", "<b>Chaque trade vérifié :</b> objectif, marge au-dessus de la perte max, limite du jour, consistance et prêt pour le payout en %", "<b>Cada operación comprobada:</b> objetivo, margen sobre la pérdida máx., límite del día, consistencia y listo para el payout en %"),
                    T("<b>One trade on several accounts</b> with the copier; a failed account keeps its history", "<b>Un trade sur plusieurs comptes</b> avec le copieur ; un compte échoué garde son historique", "<b>Una operación en varias cuentas</b> con el copiador; una cuenta fallida conserva su historial")],
                   slot("v6-08-payout-conditions-d.webp", "desktop", t(T("Payout conditions for a prop account, sample data","Conditions de payout d’un compte prop, données d’exemple","Condiciones de payout de una cuenta prop, datos de ejemplo")), t),
                   more=f'<div class="cta-row"><a class="btn btn-primary btn-lg" href="{SIGNUP}" data-track="signup_rules">{t(T(f"Track my {name} account", f"Suivre mon compte {name}", f"Seguir mi cuenta de {name}"))}</a></div><p class="fine" style="margin-top:16px">{t(MONEY_PLAN)}</p>', id_="track")
        faqs = faq_of(lang, t, f) + [
            (T(f"Is Sweep affiliated with {name}?", f"Sweep est-il affilié à {name} ?", f"¿Sweep está afiliado a {name}?"),
             T(f"No. Sweep is independent and isn’t affiliated with, endorsed by or connected to {name}. The {name} name belongs to its owner.", f"Non. Sweep est indépendant et n’est ni affilié à {name}, ni approuvé par {name}. Le nom {name} appartient à son propriétaire.", f"No. Sweep es independiente y no está afiliado, respaldado ni vinculado a {name}. El nombre {name} pertenece a su propietario.")),
            (T(f"Can I track several {name} accounts?", f"Puis-je suivre plusieurs comptes {name} ?", f"¿Puedo seguir varias cuentas de {name}?"),
             T("Yes, as many as your plan allows, each with its own rules, and you can copy one trade to several accounts at once.", "Oui, autant que ton forfait le permet, chacun avec ses propres règles, et tu peux copier un trade sur plusieurs comptes en une fois.", "Sí, tantas como permita tu plan, cada una con sus propias reglas, y puedes copiar una operación en varias cuentas a la vez.")),
            (T("Is it free?", "C’est gratuit ?", "¿Es gratis?"),
             T("Yes. Sweep is free forever, with Pro included for your first 60 days. No credit card.", "Oui. Sweep est gratuit pour toujours, avec Pro offert pendant tes 60 premiers jours. Sans carte de crédit.", "Sí. Sweep es gratis para siempre, con Pro incluido tus primeros 60 días. Sin tarjeta."))]
        rel = ["prop-firm-payout-rules.html", "prop-firm-drawdown-rules.html", "prop-firm-consistency-rules.html"]
        b += (f'<section class="rule"><div class="wrap narrow"><div class="head"><h2>{t(T("Questions","Questions","Preguntas"))}</h2></div>'
              + "".join(faq_item(t, q, a) for q, a in faqs)
              + "</div></section>" + related(lang, t, rel[:3]))
        for cand in (T(f"{name} Rules 2026: Drawdown, Payouts & Journal · Sweep", f"Règles {name} 2026 : drawdown, payouts et journal · Sweep", f"Reglas de {name} 2026: drawdown, payouts y diario · Sweep"),
                     T(f"{name} Rules 2026: Payouts & Journal · Sweep", f"Règles {name} 2026 : payouts et journal · Sweep", f"Reglas de {name} 2026: payouts y diario · Sweep"),
                     T(f"{name} Rules & Journal 2026 · Sweep", f"Règles et journal {name} 2026 · Sweep", f"Reglas y diario de {name} 2026 · Sweep"),
                     T(f"{name} Rules 2026 · Sweep", f"Règles {name} 2026 · Sweep", f"Reglas de {name} 2026 · Sweep")):
            title = t(cand)
            if len(title) <= 60: break
        desc = t(T(f"{name} rules from Sweep’s weekly check ({day(when, 'en')}): max loss, daily loss limit, consistency, minimum days and payout conditions, {kk(sizes_all[0])} to {kk(sizes_all[-1])}.",
                   f"Les règles de {name} selon la vérification hebdomadaire de Sweep ({day(when, 'fr')}) : perte max, limite du jour, consistance, jours minimum et payouts.",
                   f"Las reglas de {name} según la revisión semanal de Sweep ({day(when, 'es')}): pérdida máx., límite diario, consistencia, días mínimos y payouts."))
        ld = jsonld({"@context":"https://schema.org","@graph":[
            {"@type":"WebPage","name":title,"inLanguage":lang,"dateModified":when,"url":f"https://{DOMAIN}{href(lang, page_of(f))}","about":{"@type":"Organization","name":name,"url":(f.get("sources") or [None])[0]}},
            {"@type":"FAQPage","mainEntity":[{"@type":"Question","name":t(q),"acceptedAnswer":{"@type":"Answer","text":re.sub(r"<[^>]+>", "", t(a))}} for q, a in faqs]}]})
        body = hero + b + final_cta(lang, t)
        if lang == "fr":   # French: no « : », « ; » or « ? » alone at the start of a line
            body, title, desc = (re.sub(r" ([:;?!])(?=\s|<|$)", "\u00a0\\1", x) for x in (body, title, desc))
        return (title, desc, body, ld)
    return page

def faq_of(lang, t, f):
    name, progs = f["name"], f["programs"]; U = lambda v, l: usd(v, l)
    out = []
    # max loss
    parts = {l: [] for l in LANGS}
    for p in progs:
        E = [(s["size"], _ph(s, "eval")) for s in p["sizes"] if _ph(s, "eval").get("dd")] or [(s["size"], _ph(s, "funded")) for s in p["sizes"] if _ph(s, "funded").get("dd")]
        if not E: continue
        typ = E[0][1].get("dd_type")
        for l in LANGS:
            amounts = ", ".join(f"{U(e['dd'], l)} ({kk(sz)})" for sz, e in E)
            tw = {"eod": {"en": "trailing on the end-of-day balance", "fr": "qui suit le solde de fin de journée", "es": "que sigue el saldo al cierre"},
                  "trade": {"en": "trailing in real time", "fr": "qui suit le solde en temps réel", "es": "que sigue el saldo en tiempo real"},
                  "static": {"en": "fixed", "fr": "fixe", "es": "fija"}}.get(typ, {}).get(l, "")
            parts[l].append(p["name"] + colon(l) + amounts + (f", {tw}" if tw else ""))
    if parts["en"]:
        out.append((T(f"What is the {name} max loss (drawdown)?", f"Quelle est la perte max (drawdown) chez {name} ?", f"¿Cuál es la pérdida máx. (drawdown) en {name}?"),
                    {l: {"en": "; ", "fr": " ; ", "es": "; "}[l].join(parts[l]) + "." for l in LANGS}))
    # consistency
    cons = {l: [] for l in LANGS}
    for p in progs:
        e = next((_ph(s, "eval").get("consistency") for s in p["sizes"] if _ph(s, "eval").get("consistency")), None)
        fu = next((_ph(s, "funded").get("consistency") for s in p["sizes"] if _ph(s, "funded").get("consistency")), None)
        va = next(((c, ((s.get("variants") or {}).get(c["id"]) or {}).get("funded", {}).get("consistency")) for o in (p.get("options") or []) for c in (o.get("choices") or []) for s in p["sizes"]
                   if (((s.get("variants") or {}).get(c["id"]) or {}).get("funded") or {}).get("consistency")), None)
        for l in LANGS:
            bits = ([{"en": f"{pc(e, l)} in the evaluation", "fr": f"{pc(e, l)} en évaluation", "es": f"{pc(e, l)} en la evaluación"}[l]] if e else []) \
                 + ([{"en": f"{pc(fu, l)} on the funded account", "fr": f"{pc(fu, l)} en compte financé", "es": f"{pc(fu, l)} en la cuenta financiada"}[l]] if fu else []) \
                 + ([{"en": f"{pc(va[1], l)} on a funded account with the {va[0]['label'][l]} option", "fr": f"{pc(va[1], l)} en compte financé avec l’option {va[0]['label'][l]}", "es": f"{pc(va[1], l)} en la cuenta financiada con la opción {va[0]['label'][l]}"}[l]] if va else [])
            if bits: cons[l].append(p["name"] + colon(l) + {"en": "; ", "fr": " ; ", "es": "; "}[l].join(bits))
    if cons["en"]:
        out.append((T(f"Does {name} have a consistency rule?", f"{name} a-t-il une règle de consistance ?", f"¿{name} tiene una regla de consistencia?"),
                    {l: {"en": "Yes: your best day can be at most a share of your profit. ", "fr": "Oui : ton meilleur jour peut représenter au plus une part de ton profit. ", "es": "Sí: tu mejor día puede ser como máximo una parte de tu beneficio. "}[l] + ". ".join(cons[l]) + "." for l in LANGS}))
    # payouts (first program, 50K when it exists)
    p = progs[0]; s = rep(p)
    pay = payout_sentence(f, p, s, {"en": f"a {p['name']} {kk(s['size'])}", "fr": f"un {p['name']} {kk(s['size'])}", "es": f"una cuenta {p['name']} de {kk(s['size'])}"})
    if pay:
        out.append((T(f"When can I request a payout from {name}?", f"Quand puis-je demander un payout chez {name} ?", f"¿Cuándo puedo pedir un payout en {name}?"), pay))
    # prices
    pr = [(sz["size"], sz["price"]) for sz in p["sizes"] if (sz.get("price") or {}).get("eval") is not None]
    if pr:
        per = {"en": "/month", "fr": "/mois", "es": "/mes"}
        act = next((x.get("activation") for _, x in pr if x.get("activation")), None)
        chk = next((x.get("checked") for _, x in pr if x.get("checked")), presets.CHECKED)
        out.append((T(f"How much does a {name} {p['name']} cost?", f"Combien coûte un {p['name']} chez {name} ?", f"¿Cuánto cuesta un {p['name']} en {name}?"),
                    {l: ", ".join(f"{U(x['eval'], l)}{per[l] if x.get('eval_period') == 'month' else ''} ({kk(sz)})" for sz, x in pr)
                        + ({"en": f"; activation fee {U(act, l)}", "fr": f" ; frais d’activation de {U(act, l)}", "es": f"; tarifa de activación de {U(act, l)}"}[l] if act else "")
                        + {"en": f". Prices checked on {day(chk, l)}.", "fr": f". Prix vérifiés le {day(chk, l)}.", "es": f". Precios revisados el {day(chk, l)}."}[l] for l in LANGS}))
    out.append((T(f"Is Sweep affiliated with {name}?", f"Sweep est-il affilié à {name} ?", f"¿Sweep está afiliado a {name}?"),
                T(f"No. Sweep is independent. The rules on this page come from Sweep’s weekly check of {poss(name)} official pages; always confirm on {poss(name)} site.",
                  f"Non. Sweep est indépendant. Les règles de cette page viennent de la vérification hebdomadaire des pages officielles de {name} par Sweep ; confirme toujours sur le site de {name}.",
                  f"No. Sweep es independiente. Las reglas de esta página vienen de la revisión semanal de las páginas oficiales de {name} por Sweep; confirma siempre en el sitio de {name}.")))
    return out

# ---------------------------------------------------------------- hub: /prop-firms
CRUMBS["prop-firms/index.html"] = "Prop firms"

HUB_HELP = T("""<h2>What each rules page covers</h2><p>For every account type and size: the evaluation’s profit target, the max loss and how it trails, the daily loss limit, consistency and minimum days, then the funded account’s rules and payout conditions. Each page also gives practical points, the rule changes we’ve recorded and answers to common questions.</p>
<h2>How the rules are checked</h2><p>Sweep checks each firm’s official pages every week and keeps the values it uses to prefill prop accounts in the app. The date of the last check is on each page, and when a rule changes, the page lists it with the old and the new value.</p>
<h2>Compare the firms</h2><p>To compare one rule across every firm, use the guides: <a href="@prop-firm-drawdown-rules.html">drawdown</a>, <a href="@prop-firm-consistency-rules.html">consistency</a>, <a href="@prop-firm-payout-rules.html">payouts</a> and <a href="@prop-firm-profit-targets.html">account sizes and targets</a>.</p>
<h2>In Sweep</h2><p>Pick the firm and the account type: the rules fill in, every value stays editable, and Sweep checks each trade against them, so you see how close you are to the target, to the max loss and to your next payout.</p>""",
"""<h2>Ce que couvre chaque page de règles</h2><p>Pour chaque type et chaque taille de compte : l’objectif de profit de l’évaluation, la perte max et la façon dont elle suit, la limite de perte quotidienne, la consistance et les jours minimum, puis les règles du compte financé et les conditions de payout. Chaque page donne aussi des points pratiques, les changements de règles enregistrés et des réponses aux questions fréquentes.</p>
<h2>Comment les règles sont vérifiées</h2><p>Sweep vérifie chaque semaine les pages officielles de chaque firme et garde les valeurs qui servent à préremplir les comptes prop dans l’app. La date de la dernière vérification est sur chaque page, et quand une règle change, la page l’indique avec l’ancienne et la nouvelle valeur.</p>
<h2>Comparer les firmes</h2><p>Pour comparer une règle d’une firme à l’autre, utilise les guides : <a href="@prop-firm-drawdown-rules.html">drawdown</a>, <a href="@prop-firm-consistency-rules.html">consistance</a>, <a href="@prop-firm-payout-rules.html">payouts</a> et <a href="@prop-firm-profit-targets.html">tailles de compte et objectifs</a>.</p>
<h2>Dans Sweep</h2><p>Choisis la firme et le type de compte : les règles se remplissent, chaque valeur reste modifiable, et Sweep vérifie chaque trade contre elles. Tu vois à quelle distance tu es de l’objectif, de la perte max et de ton prochain payout.</p>""",
"""<h2>Qué cubre cada página de reglas</h2><p>Para cada tipo y tamaño de cuenta: el objetivo de beneficio de la evaluación, la pérdida máx. y cómo sigue al saldo, el límite de pérdida diaria, la consistencia y los días mínimos, y luego las reglas de la cuenta fondeada y las condiciones de payout. Cada página incluye también puntos prácticos, los cambios de reglas registrados y respuestas a las preguntas frecuentes.</p>
<h2>Cómo se revisan las reglas</h2><p>Sweep revisa cada semana las páginas oficiales de cada firma y guarda los valores que usa para precargar las cuentas prop en la app. La fecha de la última revisión está en cada página y, cuando una regla cambia, la página lo indica con el valor anterior y el nuevo.</p>
<h2>Comparar las firmas</h2><p>Para comparar una regla entre todas las firmas, usa las guías: <a href="@prop-firm-drawdown-rules.html">drawdown</a>, <a href="@prop-firm-consistency-rules.html">consistencia</a>, <a href="@prop-firm-payout-rules.html">payouts</a> y <a href="@prop-firm-profit-targets.html">tamaños de cuenta y objetivos</a>.</p>
<h2>En Sweep</h2><p>Elige la firma y el tipo de cuenta: las reglas se rellenan, cada valor sigue siendo editable y Sweep comprueba cada operación con ellas, así ves lo cerca que estás del objetivo, de la pérdida máx. y de tu próximo payout.</p>""")

def page_hub(lang, t):
    firms = presets.FIRMS
    when = max(checked_of(f) for f in firms)
    hero = page_hero(t, T("Prop firm rules, explained.", "Les règles des prop firms, expliquées.", "Las reglas de las prop firms, explicadas."),
        T(f"Drawdown, consistency and payout rules for {len(firms)} futures prop firms, from Sweep’s weekly check of their official pages. Last check: {day(when, 'en')}.",
          f"Drawdown, consistance et payouts de {len(firms)} prop firms de futures, selon la vérification hebdomadaire de leurs pages officielles par Sweep. Dernière vérification : {day(when, 'fr')}.",
          f"Drawdown, consistencia y payouts de {len(firms)} prop firms de futuros, según la revisión semanal de sus páginas oficiales por Sweep. Última verificación: {day(when, 'es')}."),
        T("Prop firms", "Prop firms", "Prop firms"))
    def card(f):
        sz = sorted({s["size"] for p in f["programs"] for s in p["sizes"]})
        types = ", ".join(p["name"] for p in f["programs"])
        return (f'<a class="tool-card" href="{href(lang, page_of(f))}"><h2>{f["name"]}</h2><p>{types} · {kk(sz[0])}' + (f" – {kk(sz[-1])}" if len(sz) > 1 else "") + "</p>"
                f'<p class="fine">{t(T("Verified on ", "Vérifié le ", "Verificado el "))}{day(checked_of(f), lang)}</p><span class="go">{t(T("See the rules", "Voir les règles", "Ver las reglas"))} →</span></a>')
    from pages8 import FIRMS as JOURNALS
    others = [(s, n) for s, n in JOURNALS if n not in presets.PRESET_FIRMS]
    other = ""
    if others:
        names = {l: {"en": " or ", "fr": " ou ", "es": " o "}[l].join(n for _, n in others) for l in LANGS}
        one = len(others) == 1
        other = (f'<p>{t(T(f"{names["en"]}? {"Its" if one else "Their"} rules aren’t preloaded in Sweep yet: add your account as “Other firm” and enter its rules once.", f"{names["fr"]} ? {"Ses" if one else "Leurs"} règles ne sont pas encore préremplies dans Sweep : ajoute ton compte comme « Autre firme » et saisis ses règles une fois.", f"¿{names["es"]}? Sus reglas aún no están precargadas en Sweep: añade tu cuenta como «Otra firma» e introduce sus reglas una vez."))}</p>'
                 '<p class="firm-others">' + "".join(f'<a href="{href(lang, s)}">{n}</a>' for s, n in others) + "</p>")
    disclaimer = T("Sweep is not affiliated with these firms. Rules can change at any time; always confirm on each firm’s official site.",
                   "Sweep n’est affilié à aucune de ces firmes. Les règles peuvent changer à tout moment ; confirme toujours sur le site officiel de chaque firme.",
                   "Sweep no está afiliado a estas firmas. Las reglas pueden cambiar en cualquier momento; confirma siempre en el sitio oficial de cada firma.")
    b = (f'<section style="padding-top:8px"><div class="wrap"><div class="tool-grid">{"".join(card(f) for f in firms)}</div>'
         f'<p class="fine" style="margin-top:18px">{t(disclaimer)}</p></div></section>'
         + f'<section class="rule"><div class="wrap narrow"><article class="article">{localize(lang, t(HUB_HELP))}</article></div></section>'
         + (f'<section class="rule"><div class="wrap narrow"><div class="head"><h2>{t(T("Another firm?", "Une autre firme ?", "¿Otra firma?"))}</h2></div>{other}</div></section>' if other else "")
         + f'<section class="rule"><div class="wrap narrow"><p class="firm-others"><span>{t(T("Free tools", "Outils gratuits", "Herramientas gratuitas"))}</span>'
         + "".join(f'<a href="{href(lang, s)}">{t(n)}</a>' for s, n in [("trailing-drawdown-calculator.html", T("Trailing drawdown calculator", "Calculateur de drawdown suiveur", "Calculadora de drawdown dinámico")),
                    ("consistency-rule-calculator.html", T("Consistency rule calculator", "Calculateur de consistance", "Calculadora de consistencia")), ("payout-calculator.html", T("Payout calculator", "Calculateur de payout", "Calculadora de payout")),
                    ("prop-firm-profit-targets.html", T("Profit targets and max loss compared", "Objectifs et perte max comparés", "Objetivos y pérdida máx. comparados"))])
         + "</p></div></section>")
    ld = jsonld({"@context": "https://schema.org", "@type": "ItemList", "name": t(T("Prop firm rules", "Règles des prop firms", "Reglas de las prop firms")),
                 "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": f["name"], "url": f"https://{DOMAIN}{href(lang, page_of(f))}"} for i, f in enumerate(firms)]})
    title = t(T("Prop Firm Rules 2026: Drawdown & Payouts by Firm · Sweep", "Règles des prop firms 2026 : drawdown et payouts · Sweep", "Reglas de prop firms 2026: drawdown y payouts · Sweep"))
    desc = t(T(f"Drawdown, daily loss, consistency and payout rules for {', '.join(f['name'] for f in firms)}, checked every week against each firm’s official pages.",
               f"Drawdown, perte du jour, consistance et payouts de {', '.join(f['name'] for f in firms)}, vérifiés chaque semaine sur leurs pages officielles.",
               f"Drawdown, pérdida diaria, consistencia y payouts de {', '.join(f['name'] for f in firms)}, revisados cada semana en sus páginas oficiales."))
    body = hero + b + final_cta(lang, t)
    if lang == "fr": body, title, desc = (re.sub(r" ([:;?!])(?=\s|<|$)", " \\1", x) for x in (body, title, desc))
    return (title, desc, body, ld)

# ---------------------------------------------------------------- a firm whose rules aren't in the app's catalogue yet (Tradeify)
MANUAL_RULES = T("""<h2>The rules to enter</h2><ul>
<li><b>Profit target</b> of the evaluation, in dollars.</li>
<li><b>Max loss</b> and how it trails: end of day, in real time or static, and whether it stops at the starting balance.</li>
<li><b>Daily loss limit,</b> if the account has one.</li>
<li><b>Consistency:</b> the most your best day can be, as a share of your profit.</li>
<li><b>Minimum days</b> before passing or before a payout.</li>
<li><b>Payout conditions:</b> winning days, a balance to keep, the minimum and maximum per payout, and your profit split.</li></ul>
<p>Take them from {F}’s current rules for your exact account type and size: rules differ by account and change over time. The <a href="@glossary.html">glossary</a> explains each term, and the <a href="@prop-firm-drawdown-rules.html">drawdown</a> and <a href="@prop-firm-payout-rules.html">payout</a> guides show how the other firms set them.</p>""",
"""<h2>Les règles à saisir</h2><ul>
<li><b>Objectif de profit</b> de l’évaluation, en dollars.</li>
<li><b>Perte max</b> et sa façon de suivre : en fin de journée, en temps réel ou fixe, et si elle s’arrête au solde de départ.</li>
<li><b>Limite de perte du jour,</b> si le compte en a une.</li>
<li><b>Consistance :</b> le poids maximal de ta meilleure journée dans ton profit.</li>
<li><b>Jours minimum</b> avant de réussir ou avant un payout.</li>
<li><b>Conditions de payout :</b> jours gagnants, solde à garder, minimum et maximum par payout, et ton partage des profits.</li></ul>
<p>Prends-les dans les règles actuelles de {F} pour ton type et ta taille de compte exacts : les règles diffèrent selon le compte et changent avec le temps. Le <a href="@glossary.html">lexique</a> explique chaque terme, et les guides du <a href="@prop-firm-drawdown-rules.html">drawdown</a> et des <a href="@prop-firm-payout-rules.html">payouts</a> montrent comment les autres firmes les fixent.</p>""",
"""<h2>Las reglas que debes introducir</h2><ul>
<li><b>Objetivo de beneficio</b> de la evaluación, en dólares.</li>
<li><b>Pérdida máx.</b> y cómo sigue al saldo: al cierre, en tiempo real o fija, y si se detiene en el saldo inicial.</li>
<li><b>Límite de pérdida diaria,</b> si la cuenta lo tiene.</li>
<li><b>Consistencia:</b> el peso máximo de tu mejor día en tu beneficio.</li>
<li><b>Días mínimos</b> antes de aprobar o antes de un payout.</li>
<li><b>Condiciones de payout:</b> días ganadores, saldo a mantener, mínimo y máximo por payout, y tu reparto de beneficios.</li></ul>
<p>Tómalas de las reglas actuales de {F} para tu tipo y tamaño de cuenta exactos: las reglas cambian según la cuenta y con el tiempo. El <a href="@glossary.html">glosario</a> explica cada término, y las guías de <a href="@prop-firm-drawdown-rules.html">drawdown</a> y de <a href="@prop-firm-payout-rules.html">payouts</a> muestran cómo las fijan las demás firmas.</p>""")

def make_manual_page(slug, name):
    CRUMBS[slug] = name
    def page(lang, t):
        hero = page_hero(t, T(f"{name} rules, in Sweep.", f"Les règles de {name}, dans Sweep.", f"Las reglas de {name}, en Sweep."),
            T(f"{poss(name)} rules aren’t preloaded in Sweep yet: add your account as “Other firm”, enter its rules once, and Sweep checks every trade against them.",
              f"Les règles de {name} ne sont pas encore préremplies dans Sweep : ajoute ton compte comme « Autre firme », saisis ses règles une fois, et Sweep vérifie chaque trade contre elles.",
              f"Las reglas de {name} aún no están precargadas en Sweep: añade tu cuenta como «Otra firma», introduce sus reglas una vez y Sweep comprueba cada operación con ellas."),
            T("Prop firms", "Prop firms", "Prop firms"), f'<a class="btn btn-primary btn-lg" href="{SIGNUP}" data-track="signup_firm">{t(CREATE_FREE)}</a>')
        b = f'<section style="padding-top:8px"><div class="wrap narrow"><article class="article">{localize(lang, t(MANUAL_RULES)).replace("{F}", name)}</article></div></section>'
        items = [T("<b>Every trade checked</b> against your rules: target, room above the max loss, today’s limit, consistency", "<b>Chaque trade vérifié</b> contre tes règles : objectif, marge au-dessus de la perte max, limite du jour, consistance", "<b>Cada operación comprobada</b> con tus reglas: objetivo, margen sobre la pérdida máx., límite del día, consistencia"),
                 T("<b>Ready for payout</b> in %, once funded, from the conditions you entered", "<b>Prêt pour le payout</b> en %, une fois financé, selon les conditions saisies", "<b>Listo para el payout</b> en %, ya fondeada, según las condiciones introducidas"),
                 T(f"<b>One trade on several {name} accounts</b> with the trade copier", f"<b>Un trade sur plusieurs comptes {name}</b> avec le copieur de trades", f"<b>Una operación en varias cuentas de {name}</b> con el copiador"),
                 T("<b>A failed or closed account keeps its history</b>", "<b>Un compte échoué ou fermé garde son historique</b>", "<b>Una cuenta fallida o cerrada conserva su historial</b>")]
        b += split(t, T("In Sweep", "Dans Sweep", "En Sweep"), T(f"Track your {name} account in Sweep.", f"Suis ton compte {name} dans Sweep.", f"Sigue tu cuenta de {name} en Sweep."),
                   T("Enter the rules once; then every value is tracked on every trade, next to your other firms.", "Saisis les règles une fois ; ensuite, chaque valeur est suivie à chaque trade, à côté de tes autres firmes.", "Introduce las reglas una vez; después, cada valor se sigue en cada operación, junto a tus otras firmas."),
                   items, frame("accounts", lang, t(T(f"{name} accounts in Sweep, sample data", f"Comptes {name} dans Sweep, données d’exemple", f"Cuentas de {name} en Sweep, datos de ejemplo")), t), id_="track",
                   more=f'<p class="fine" style="margin-top:16px">{t(MONEY_PLAN)}</p>')
        faqs = [(T(f"Is Sweep affiliated with {name}?", f"Sweep est-il affilié à {name} ?", f"¿Sweep está afiliado a {name}?"),
                 T(f"No. Sweep is independent and isn’t affiliated with, endorsed by or connected to {name}. The {name} name belongs to its owner.", f"Non. Sweep est indépendant et n’est ni affilié à {name}, ni approuvé par {name}. Le nom {name} appartient à son propriétaire.", f"No. Sweep es independiente y no está afiliado, respaldado ni vinculado a {name}. El nombre {name} pertenece a su propietario.")),
                (T(f"Are {poss(name)} rules preloaded in Sweep?", f"Les règles de {name} sont-elles préremplies dans Sweep ?", f"¿Las reglas de {name} están precargadas en Sweep?"),
                 T(f"Not yet. Add your account as “Other firm” and enter its rules once; you can edit them anytime. Sweep preloads the rules of {FIRMS_TXT['en']}.", f"Pas encore. Ajoute ton compte comme « Autre firme » et saisis ses règles une fois ; tu peux les modifier à tout moment. Sweep préremplit les règles de {FIRMS_TXT['fr']}.", f"Todavía no. Añade tu cuenta como «Otra firma» e introduce sus reglas una vez; puedes editarlas cuando quieras. Sweep precarga las reglas de {FIRMS_TXT['es']}.")),
                (T(f"Can I track several {name} accounts?", f"Puis-je suivre plusieurs comptes {name} ?", f"¿Puedo seguir varias cuentas de {name}?"),
                 T("Yes, as many as your plan allows, each with its own rules, and you can copy one trade to several accounts at once.", "Oui, autant que ton forfait le permet, chacun avec ses propres règles, et tu peux copier un trade sur plusieurs comptes en une fois.", "Sí, tantas como permita tu plan, cada una con sus propias reglas, y puedes copiar una operación en varias cuentas a la vez.")),
                (T("Is it free?", "C’est gratuit ?", "¿Es gratis?"),
                 T("Yes. Sweep is free forever, with Pro included for your first 60 days. No credit card.", "Oui. Sweep est gratuit pour toujours, avec Pro offert pendant tes 60 premiers jours. Sans carte de crédit.", "Sí. Sweep es gratis para siempre, con Pro incluido tus primeros 60 días. Sin tarjeta."))]
        b += (f'<section class="rule"><div class="wrap narrow"><div class="head"><h2>{t(T("Questions", "Questions", "Preguntas"))}</h2></div>'
              + "".join(faq_item(t, q, a) for q, a in faqs) + "</div></section>"
              + related(lang, t, ["prop-firms/index.html", "prop-firm-drawdown-rules.html", "prop-firm-payout-rules.html"]))
        ld = jsonld({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": t(q), "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", t(a))}} for q, a in faqs]})
        return (t(T(f"{name} Rules & Trading Journal · Sweep", f"Règles {name} et journal de trading · Sweep", f"Reglas de {name} y diario de trading · Sweep")),
                t(T(f"Track your {name} accounts in Sweep: enter the rules once (target, max loss, daily limit, consistency, payouts) and every trade is checked. Free.",
                    f"Suis tes comptes {name} dans Sweep : saisis les règles une fois (objectif, perte max, limite du jour, consistance, payouts) et chaque trade est vérifié.",
                    f"Sigue tus cuentas de {name} en Sweep: introduce las reglas una vez (objetivo, pérdida máx., límite diario, consistencia, payouts) y se revisa cada operación.")),
                hero + b + final_cta(lang, t), ld)
    return page
