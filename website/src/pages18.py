from core import *
import re
import presets

# Prop firm rule pages. Every number comes from the app's catalogue (presets.py); a value missing there is a row left out.
SLUG = {"tpt": "take-profit-trader", "mffu": "myfundedfutures"}
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
     (T("Max contracts","Contrats max","Contratos máx."), lambda r, s: r.get("max_minis"), lambda v: f"{v:g} minis"),
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
     (T("Activation fee","Frais d’activation","Tarifa de activación"), lambda pr, s: pr.get("activation"), lambda v: usd(v, lang)),
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
            + "".join(f'<th scope="col">{kk(s["size"])}</th>' for s in sizes) + "</tr></thead>")
    body = ""
    for gi, (gt, rows, get) in enumerate(groups):
        out = []
        for label, val, fmt in rows:
            vals = [val(get(s), s) for s in sizes]
            if all(v is None for v in vals): continue          # not in the catalogue: the row is left out
            if only_diff_from is not None:
                base = [val(only_diff_from[gi][2](s), s) for s in sizes]
                if vals == base: continue
            out.append(f'<tr><th scope="row">{t(label)}</th>' + "".join(f'<td>{fmt(v) if v is not None else "—"}</td>' for v in vals) + "</tr>")
        if out: body += f'<tr class="grp"><th colspan="{cols + 1}" scope="colgroup">{t(gt)}</th></tr>' + "".join(out)
    return f'<div class="cmp-wrap"><table class="cmp rules n{cols}">{head}<tbody>{body}</tbody></table></div>' if body else ""

# ---------------------------------------------------------------- what it means in practice (generated from the rules, reviewed before publishing)
def practice(lang, t, f, p):
    s = rep(p); size = kk(s["size"]); U = lambda v: usd(v, lang); E, F, L = _ph(s, "eval"), _ph(s, "funded"), _ph(s, "live")
    pts = []
    if E.get("dd") and E.get("dd_type") in DDT:
        pts.append({"eod": T(f"The max loss ({U(E['dd'])} on the {size}) follows your highest end-of-day balance: a peak during the day doesn’t move it.",
                             f"La perte max ({U(E['dd'])} sur le {size}) suit ton solde de fin de journée le plus haut : un sommet pendant la journée ne la déplace pas.",
                             f"La pérdida máx. ({U(E['dd'])} en la {size}) sigue tu saldo de cierre más alto: un máximo durante el día no la mueve."),
                    "trade": T(f"The max loss ({U(E['dd'])} on the {size}) follows your highest balance in real time, during the day too.",
                               f"La perte max ({U(E['dd'])} sur le {size}) suit ton solde le plus haut en temps réel, pendant la journée aussi.",
                               f"La pérdida máx. ({U(E['dd'])} en la {size}) sigue tu saldo más alto en tiempo real, también durante el día."),
                    "static": T(f"The max loss ({U(E['dd'])} on the {size}) is fixed: it doesn’t move up with your profit.",
                                f"La perte max ({U(E['dd'])} sur le {size}) est fixe : elle ne monte pas avec ton profit.",
                                f"La pérdida máx. ({U(E['dd'])} en la {size}) es fija: no sube con tu beneficio.")}[E["dd_type"]])
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
        pts.append(T(f"Daily loss limit: lose {U(dll)} in a day on the {size} and you stop for the day.", f"Limite du jour : perds {U(dll)} dans une journée sur le {size} et tu t’arrêtes pour la journée.", f"Límite diario: pierde {U(dll)} en un día en la {size} y paras por ese día."))
    if E.get("consistency") and E.get("target"):
        c = E["consistency"]; mx = E["target"] * c / 100
        pts.append(T(f"To pass, your best day can’t be more than {pc(c, lang)} of your profit: right at the {U(E['target'])} target ({size}), that’s {U(mx)} at most in one day.",
                     f"Pour réussir, ton meilleur jour ne peut pas dépasser {pc(c, lang)} de ton profit : pile à l’objectif de {U(E['target'])} ({size}), c’est {U(mx)} au plus en une journée.",
                     f"Para aprobar, tu mejor día no puede superar el {pc(c, lang)} de tu beneficio: justo en el objetivo de {U(E['target'])} ({size}), son {U(mx)} como máximo en un día."))
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
        if po.get("min_bal"): bits.append({"en": f"a balance above {U(po['min_bal'])}", "fr": f"un solde au-dessus de {U(po['min_bal'])}", "es": f"un saldo por encima de {U(po['min_bal'])}"}[l])
        rng = ({"en": f"from {U(po['min'])} to {U(po['max'])} per payout", "fr": f"de {U(po['min'])} à {U(po['max'])} par payout", "es": f"de {U(po['min'])} a {U(po['max'])} por payout"}[l] if po.get("min") and po.get("max")
               else {"en": f"at least {U(po['min'])} per payout", "fr": f"au moins {U(po['min'])} par payout", "es": f"al menos {U(po['min'])} por payout"}[l] if po.get("min") else "")
        if not bits and not rng: return None
        where = label[l] if label else {"en": f"the {size}", "fr": f"le {size}", "es": f"la {size}"}[l]
        if opt: where += {"en": f" ({opt[1]['label'][l]} option)", "fr": f" (option {opt[1]['label'][l]})", "es": f" (opción {opt[1]['label'][l]})"}[l]
        txt = {"en": "To request a payout on ", "fr": "Pour demander un payout sur ", "es": "Para pedir un payout en "}[l] + where + colon(l) + {"en": " and ", "fr": " et ", "es": " y "}[l].join(bits)
        if rng:
            txt += ({"en": ", then ", "fr": ", puis ", "es": ", luego "}[l] if bits else "") + ({"en": f"up to {pc(po['max_pct'], l)} of your profit, ", "fr": f"jusqu’à {pc(po['max_pct'], l)} de ton profit, ", "es": f"hasta el {pc(po['max_pct'], l)} de tu beneficio, "}[l] if po.get("max_pct") else "") + rng
        if po.get("split_pct"): txt += {"en": f"; you keep {pc(po['split_pct'], l)}", "fr": f" ; tu gardes {pc(po['split_pct'], l)}", "es": f"; te quedas con el {pc(po['split_pct'], l)}"}[l]
        out[l] = txt + "."
    return out

# ---------------------------------------------------------------- page
RULE_NAMES = {"eval": T("evaluation","évaluation","evaluación"), "funded": T("funded","financé","financiada"), "live": T("live","live","live")}

def history(lang, t, f):
    rows = [c for c in presets.CHANGES if c.get("firm") == f["id"]][:8]
    if not rows:
        return f'<p>{t(T(f"No rule change recorded since we started tracking on {day(TRACK_SINCE, lang)}.", f"Aucun changement de règle enregistré depuis le début du suivi, le {day(TRACK_SINCE, lang)}.", f"Ningún cambio de regla registrado desde el inicio del seguimiento, el {day(TRACK_SINCE, lang)}."))}</p>'
    prog = {p.get("id", p["name"]): p["name"] for p in f["programs"]}
    def v(x): return "—" if x is None else (usd(x, lang) if isinstance(x, (int, float)) and not isinstance(x, bool) and abs(x) >= 100 else str(x))
    items = "".join(f'<li><b>{day(c["date"], lang)}</b> · {prog.get(c["program"], c["program"])} {kk(c["size"])} · {c["rule"]}: {v(c["old"])} → {v(c["new"])}</li>' for c in rows)
    return f'<ul class="list">{items}</ul>'

def make_rules_page(f):
    CRUMBS[page_of(f)] = f["name"]
    def page(lang, t):
        name, progs = f["name"], f["programs"]
        when, src = checked_of(f), source_of(f)
        sizes_all = sorted({s["size"] for p in progs for s in p["sizes"]})
        verified = T(f'Last verified: {day(when, "en")}, against <a href="{src}" rel="nofollow noopener" target="_blank">{name}’s official pages</a>.',
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
        disclaimer = T(f"Sweep is not affiliated with {name}. Rules can change at any time; always confirm on {name}’s official site. Values are shown for information, from Sweep’s weekly check of {name}’s pages.",
                       f"Sweep n’est pas affilié à {name}. Les règles peuvent changer à tout moment ; confirme toujours sur le site officiel de {name}. Valeurs présentées à titre indicatif, tirées de la vérification hebdomadaire des pages de {name} par Sweep.",
                       f"Sweep no está afiliado a {name}. Las reglas pueden cambiar en cualquier momento; confirma siempre en el sitio oficial de {name}. Valores a título informativo, tomados de la revisión semanal de las páginas de {name} por Sweep.")
        b = (f'<section style="padding-top:8px"><div class="wrap narrow">{jump}</div></section>' if jump else "") + secs
        b += f'<section style="padding-top:0"><div class="wrap narrow"><p class="fine">{t(disclaimer)}</p></div></section>'
        b += (f'<section class="rule"><div class="wrap narrow"><div class="head"><h2>{t(T("Rule changes","Changements de règles","Cambios de reglas"))}</h2></div>{history(lang, t, f)}</div></section>')
        b += split(t, T("Track it","Suis-le","Síguelo"), T(f"Track your {name} account in Sweep.", f"Suis ton compte {name} dans Sweep.", f"Sigue tu cuenta de {name} en Sweep."),
                   T(f"Pick {name} and your account type: these rules fill in, and Sweep counts your payout conditions on every trade. Free forever, no card.",
                     f"Choisis {name} et ton type de compte : ces règles se remplissent, et Sweep compte tes conditions de payout à chaque trade. Gratuit pour toujours, sans carte.",
                     f"Elige {name} y tu tipo de cuenta: estas reglas se completan y Sweep cuenta tus condiciones de payout en cada operación. Gratis para siempre, sin tarjeta."),
                   [], slot("v6-08-payout-conditions-d.webp", "desktop", t(T("Payout conditions for a prop account, sample data","Conditions de payout d’un compte prop, données d’exemple","Condiciones de payout de una cuenta prop, datos de ejemplo")), t),
                   more=f'<div class="cta-row"><a class="btn btn-primary btn-lg" href="{SIGNUP}" data-track="signup_rules">{t(T(f"Track my {name} account", f"Suivre mon compte {name}", f"Seguir mi cuenta de {name}"))}</a></div>')
        faqs = faq_of(lang, t, f)
        from pages8 import FIRMS as JOURNALS
        jp = next((s for s, n in JOURNALS if n == name), None)
        rel = ([("trailing-drawdown-calculator.html", T("Trailing drawdown calculator","Calculateur de drawdown suiveur","Calculadora de drawdown dinámico")),
                ("payout-calculator.html", T("Payout calculator","Calculateur de payout","Calculadora de payout")),
                ("futures-contracts.html", T("Contract specs","Fiches contrats","Fichas de contratos")),
                ("best-trading-journal-for-prop-firms.html", T("Best trading journal for prop firms","Meilleur journal pour prop firms","Mejor diario para prop firms"))]
               + ([(jp, T(f"{name} trading journal", f"Journal de trading {name}", f"Diario de trading para {name}"))] if jp else []))
        b += (f'<section class="rule"><div class="wrap narrow"><div class="head"><h2>{t(T("Questions","Questions","Preguntas"))}</h2></div>'
              + "".join(faq_item(t, q, a) for q, a in faqs)
              + f'<p class="firm-others" style="margin-top:36px"><span>{t(T("Related","Voir aussi","Ver también"))}</span>' + "".join(f'<a href="{href(lang, s)}">{t(n)}</a>' for s, n in rel) + "</p></div></section>")
        title = t(T(f"{name} Rules 2026: Drawdown, Consistency & Payout Rules · Sweep", f"Règles {name} 2026 : drawdown, consistance et payouts · Sweep", f"Reglas de {name} 2026: drawdown, consistencia y payouts · Sweep"))
        if len(title) > 65: title = t(T(f"{name} Rules 2026: Drawdown & Payouts · Sweep", f"Règles {name} 2026 : drawdown et payouts · Sweep", f"Reglas de {name} 2026: drawdown y payouts · Sweep"))
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
        E = [(s["size"], _ph(s, "eval")) for s in p["sizes"] if _ph(s, "eval").get("dd")]
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
                T(f"No. Sweep is independent. The rules on this page come from Sweep’s weekly check of {name}’s official pages; always confirm on {name}’s site.",
                  f"Non. Sweep est indépendant. Les règles de cette page viennent de la vérification hebdomadaire des pages officielles de {name} par Sweep ; confirme toujours sur le site de {name}.",
                  f"No. Sweep es independiente. Las reglas de esta página vienen de la revisión semanal de las páginas oficiales de {name} por Sweep; confirma siempre en el sitio de {name}.")))
    return out
