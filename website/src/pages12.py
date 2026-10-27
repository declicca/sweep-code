from core import *
import ui

# symbol, name, exchange, tick size, tick value, point value, months, sibling, family
C = [
 ("NQ","E-mini Nasdaq-100","CME",0.25,5.0,20.0,"H M U Z","MNQ","idx"),
 ("MNQ","Micro E-mini Nasdaq-100","CME",0.25,0.5,2.0,"H M U Z","NQ","idx"),
 ("ES","E-mini S&P 500","CME",0.25,12.5,50.0,"H M U Z","MES","idx"),
 ("MES","Micro E-mini S&P 500","CME",0.25,1.25,5.0,"H M U Z","ES","idx"),
 ("YM","E-mini Dow ($5)","CBOT",1.0,5.0,5.0,"H M U Z","MYM","idx"),
 ("MYM","Micro E-mini Dow","CBOT",1.0,0.5,0.5,"H M U Z","YM","idx"),
 ("RTY","E-mini Russell 2000","CME",0.1,5.0,50.0,"H M U Z","M2K","idx"),
 ("M2K","Micro E-mini Russell 2000","CME",0.1,0.5,5.0,"H M U Z","RTY","idx"),
 ("CL","Crude Oil (WTI)","NYMEX",0.01,10.0,1000.0,"F G H J K M N Q U V X Z","MCL","energy"),
 ("MCL","Micro WTI Crude Oil","NYMEX",0.01,1.0,100.0,"F G H J K M N Q U V X Z","CL","energy"),
 ("GC","Gold","COMEX",0.1,10.0,100.0,"G J M Q V Z","MGC","metal"),
 ("MGC","Micro Gold","COMEX",0.1,1.0,10.0,"G J M Q V Z","GC","metal"),
 ("SI","Silver","COMEX",0.005,25.0,5000.0,"H K N U Z",None,"metal"),
 ("6E","Euro FX","CME",0.00005,6.25,125000.0,"H M U Z",None,"fx"),
]
def slug(s): return f"contracts/{s.lower()}-futures.html"
# the English title's last words, after the tick value (YM and MYM: a tick is one point)
TITLE_TAIL = {"YM": "E-mini Dow Specs", "MYM": "Micro Dow Specs", "CL": "Crude Oil Futures Specs", "MCL": "Micro Crude Oil Specs", "GC": "Gold Futures Specs",
              "MGC": "Micro Gold Specs", "SI": "Silver Futures Specs", "6E": "Euro FX Futures Specs"}
def spec_title(s, tv, pv, ts, L):
    """« NQ Tick Value: $5 per Tick, $20 per Point · Specs », « Valeur du tick NQ : 5 $ par tick, 20 $ par point », « Valor del tick NQ: 5 $ por tick, 20 $ por punto »."""
    one = ts == 1   # YM, MYM: a tick is a point
    if L == "en":
        if one: c = [f"{s} Tick Value: {_fmt(tv)} per Point · {TITLE_TAIL[s]}", f"{s} Tick Value: {_fmt(tv)} per Point"]
        elif s in TITLE_TAIL: c = [f"{s} Tick Value: {_fmt(tv)} per Tick · {TITLE_TAIL[s]}", f"{s} Tick Value: {_fmt(tv)} per Tick"]
        else: c = [f"{s} Tick Value: {_fmt(tv)} per Tick, {_fmt(pv)} per Point · Specs", f"{s} Tick Value: {_fmt(tv)} per Tick, {_fmt(pv)} per Point"]
    elif L == "fr": c = [f"Valeur du tick {s} : {_fmt(tv, 'fr')} par point"] if one else [f"Valeur du tick {s} : {_fmt(tv, 'fr')} par tick, {_fmt(pv, 'fr')} par point"]
    else: c = [f"Valor del tick {s}: {_fmt(tv, 'es')} por punto"] if one else [f"Valor del tick {s}: {_fmt(tv, 'es')} por tick, {_fmt(pv, 'es')} por punto"]
    return next((x for x in c if len(x) <= 60), c[-1])

def _fmt(v, lang="en"):
    """Money as the rest of the site writes it: $12.50, 12,50 $ (FR), 12,50 $ (ES); thousands 1,000 / 1 000 / 1.000."""
    s = f"{v:,.0f}" if float(v).is_integer() else f"{v:,.2f}"
    if lang == "en": return "$" + s
    return s.replace(",", "\0").replace(".", ",").replace("\0", "\u202f" if lang == "fr" else ".") + "\u00a0$"

def _tick(ts, lang="en"):
    """A price step without scientific notation (0.00005, not 5e-05), with a decimal comma in FR and ES."""
    x = ("%.5f" % ts).rstrip("0").rstrip(".")
    return x if lang == "en" else x.replace(".", ",")

NOTE = T("Specifications for guidance only. Always check the official CME Group contract page before trading.",
         "Spécifications à titre indicatif. Vérifie toujours la fiche officielle du CME Group avant de trader.",
         "Especificaciones a título indicativo. Verifica siempre la ficha oficial de CME Group antes de operar.")
HOURS = T("CME Globex: Sunday to Friday, 6:00 p.m. to 5:00 p.m. New York time, with a daily one-hour break from 5:00 to 6:00 p.m.",
          "CME Globex : du dimanche au vendredi, de 18 h à 17 h heure de New York, avec une pause quotidienne d’une heure de 17 h à 18 h.",
          "CME Globex: de domingo a viernes, de 18:00 a 17:00 hora de Nueva York, con una pausa diaria de una hora de 17:00 a 18:00.")

# when each family trades most, and the scheduled releases that move it (links: @page.html, localized per language)
ACTIVE = {
 "idx": T("{s} trades nearly 24 hours a day on CME Globex, but most of its volume comes during the New York cash session, from 9:30 a.m. to 4:00 p.m. New York time. The first hour after the 9:30 open is usually the most active, and activity picks up again into the close. Overnight, the market stays open with lower volume.",
          "{s} se négocie presque 24 h sur 24 sur CME Globex, mais l’essentiel de son volume se fait pendant la séance au comptant de New York, de 9 h 30 à 16 h, heure de New York. La première heure après l’ouverture de 9 h 30 est généralement la plus active, et l’activité reprend à l’approche de la clôture. La nuit, le marché reste ouvert avec moins de volume.",
          "{s} cotiza casi las 24 horas en CME Globex, pero la mayor parte de su volumen llega durante la sesión de contado de Nueva York, de 9:30 a 16:00 hora de Nueva York. La primera hora tras la apertura de las 9:30 suele ser la más activa, y la actividad vuelve a subir hacia el cierre. Por la noche, el mercado sigue abierto con menos volumen."),
 "energy": T("{s} trades nearly 24 hours a day on CME Globex, but volume is highest during the New York day session, from 9:00 a.m. to the 2:30 p.m. settlement, New York time. Outside those hours, moves can come from headlines with fewer contracts behind them.",
             "{s} se négocie presque 24 h sur 24 sur CME Globex, mais le volume est le plus fort pendant la séance de jour de New York, de 9 h au règlement de 14 h 30, heure de New York. En dehors de ces heures, les mouvements peuvent venir de nouvelles, avec moins de contrats derrière.",
             "{s} cotiza casi las 24 horas en CME Globex, pero el volumen es mayor durante la sesión diurna de Nueva York, de 9:00 a la liquidación de las 14:30, hora de Nueva York. Fuera de ese horario, los movimientos pueden venir de noticias, con menos contratos detrás."),
 "metal": T("{s} trades nearly 24 hours a day. Volume builds with London in the early morning and peaks when London and New York overlap, roughly 8:00 a.m. to noon New York time, before the COMEX settlement in the early afternoon.",
            "{s} se négocie presque 24 h sur 24. Le volume monte avec Londres tôt le matin et culmine quand Londres et New York se chevauchent, environ de 8 h à midi, heure de New York, avant le règlement du COMEX en début d’après-midi.",
            "{s} cotiza casi las 24 horas. El volumen crece con Londres a primera hora y llega a su máximo cuando Londres y Nueva York coinciden, más o menos de 8:00 a mediodía hora de Nueva York, antes de la liquidación del COMEX a primera hora de la tarde."),
 "fx": T("{s} follows the euro against the dollar. It is most active during the London session and above all when London and New York overlap, roughly 8:00 a.m. to noon New York time.",
         "{s} suit l’euro contre le dollar. Il est le plus actif pendant la séance de Londres, et surtout quand Londres et New York se chevauchent, environ de 8 h à midi, heure de New York.",
         "{s} sigue al euro frente al dólar. Tiene más actividad durante la sesión de Londres y, sobre todo, cuando Londres y Nueva York coinciden, más o menos de 8:00 a mediodía hora de Nueva York."),
}
MOVERS = {
 "idx": T("U.S. data released at 8:30 a.m. New York time, before the open, often sets the tone: <a href=\"@cpi-release-dates.html\">CPI</a>, <a href=\"@nfp-release-dates.html\">Nonfarm Payrolls</a>, <a href=\"@pce-release-dates.html\">PCE</a>, PPI, GDP and retail sales. <a href=\"@fomc-meeting-dates.html\">FOMC</a> decisions at 2:00 p.m. move the whole index complex, and ISM at 10:00 a.m. lands in the middle of the morning session.",
          "Les données américaines publiées à 8 h 30, heure de New York, avant l’ouverture, donnent souvent le ton : <a href=\"@cpi-release-dates.html\">CPI</a>, <a href=\"@nfp-release-dates.html\">emploi (NFP)</a>, <a href=\"@pce-release-dates.html\">PCE</a>, PPI, PIB et ventes au détail. Les décisions du <a href=\"@fomc-meeting-dates.html\">FOMC</a> à 14 h font bouger tous les indices, et l’ISM de 10 h tombe en pleine séance du matin.",
          "Los datos de EE. UU. publicados a las 8:30 hora de Nueva York, antes de la apertura, suelen marcar el tono: <a href=\"@cpi-release-dates.html\">CPI</a>, <a href=\"@nfp-release-dates.html\">empleo (NFP)</a>, <a href=\"@pce-release-dates.html\">PCE</a>, PPI, PIB y ventas minoristas. Las decisiones del <a href=\"@fomc-meeting-dates.html\">FOMC</a> a las 14:00 mueven todos los índices, y el ISM de las 10:00 llega en plena sesión de la mañana."),
 "energy": T("The EIA weekly petroleum status report, on Wednesdays at 10:30 a.m. New York time (a day later in holiday weeks), is the main scheduled release for crude; the API’s private estimate comes out the day before, on Tuesdays at 4:30 p.m. OPEC+ meetings and U.S. data such as <a href=\"@cpi-release-dates.html\">CPI</a>, <a href=\"@nfp-release-dates.html\">Nonfarm Payrolls</a> and <a href=\"@fomc-meeting-dates.html\">FOMC</a> decisions matter too.",
             "Le rapport hebdomadaire de l’EIA sur les stocks de pétrole, le mercredi à 10 h 30, heure de New York (un jour plus tard les semaines de congé), est la principale publication prévue pour le brut ; l’estimation privée de l’API sort la veille, le mardi à 16 h 30. Les réunions de l’OPEP+ et les données américaines comme le <a href=\"@cpi-release-dates.html\">CPI</a>, l’<a href=\"@nfp-release-dates.html\">emploi (NFP)</a> et les décisions du <a href=\"@fomc-meeting-dates.html\">FOMC</a> comptent aussi.",
             "El informe semanal de la EIA sobre inventarios de petróleo, los miércoles a las 10:30 hora de Nueva York (un día después en semanas festivas), es la principal publicación prevista para el crudo; la estimación privada del API sale el día anterior, los martes a las 16:30. Las reuniones de la OPEP+ y los datos de EE. UU. como el <a href=\"@cpi-release-dates.html\">CPI</a>, el <a href=\"@nfp-release-dates.html\">empleo (NFP)</a> y las decisiones del <a href=\"@fomc-meeting-dates.html\">FOMC</a> también cuentan."),
 "metal": T("Precious metals react to anything that moves interest rates and the dollar: <a href=\"@cpi-release-dates.html\">CPI</a>, <a href=\"@nfp-release-dates.html\">Nonfarm Payrolls</a>, <a href=\"@pce-release-dates.html\">PCE</a> and <a href=\"@fomc-meeting-dates.html\">FOMC</a> decisions above all. The 8:30 a.m. releases land in the middle of the busiest hours.",
            "Les métaux précieux réagissent à tout ce qui fait bouger les taux d’intérêt et le dollar : le <a href=\"@cpi-release-dates.html\">CPI</a>, l’<a href=\"@nfp-release-dates.html\">emploi (NFP)</a>, le <a href=\"@pce-release-dates.html\">PCE</a> et surtout les décisions du <a href=\"@fomc-meeting-dates.html\">FOMC</a>. Les publications de 8 h 30 tombent en pleine période la plus active.",
            "Los metales preciosos reaccionan a todo lo que mueve los tipos de interés y el dólar: el <a href=\"@cpi-release-dates.html\">CPI</a>, el <a href=\"@nfp-release-dates.html\">empleo (NFP)</a>, el <a href=\"@pce-release-dates.html\">PCE</a> y, sobre todo, las decisiones del <a href=\"@fomc-meeting-dates.html\">FOMC</a>. Los datos de las 8:30 llegan en plenas horas de más actividad."),
 "fx": T("Both sides of the pair matter: U.S. data such as <a href=\"@cpi-release-dates.html\">CPI</a>, <a href=\"@nfp-release-dates.html\">Nonfarm Payrolls</a> and <a href=\"@fomc-meeting-dates.html\">FOMC</a> decisions, and on the euro side, European Central Bank rate decisions and eurozone inflation.",
         "Les deux côtés de la paire comptent : les données américaines comme le <a href=\"@cpi-release-dates.html\">CPI</a>, l’<a href=\"@nfp-release-dates.html\">emploi (NFP)</a> et les décisions du <a href=\"@fomc-meeting-dates.html\">FOMC</a>, et du côté de l’euro, les décisions de taux de la Banque centrale européenne et l’inflation de la zone euro.",
         "Cuentan los dos lados del par: los datos de EE. UU. como el <a href=\"@cpi-release-dates.html\">CPI</a>, el <a href=\"@nfp-release-dates.html\">empleo (NFP)</a> y las decisiones del <a href=\"@fomc-meeting-dates.html\">FOMC</a>, y del lado del euro, las decisiones de tipos del Banco Central Europeo y la inflación de la eurozona."),
}
STOP_PTS = {"NQ": 20, "MNQ": 20, "ES": 5, "MES": 5, "YM": 40, "MYM": 40, "RTY": 5, "M2K": 5, "CL": 0.2, "MCL": 0.2, "GC": 5, "MGC": 5, "SI": 0.1, "6E": 0.002}   # example stop, in points
SIZE = {"SI": T("One SI contract is 5,000 troy ounces of silver: each {ts} tick is worth {tv}, and a full {one} move is worth {pv} per contract. With $500 of risk per trade, a stop can’t be wider than 20 ticks (0.10). CME also lists a smaller Micro Silver contract (SIL, 1,000 ounces, one fifth of SI).",
                "Un contrat SI, c’est 5 000 onces troy d’argent : chaque tick de {ts} vaut {tv}, et un mouvement complet de {one} vaut {pv} par contrat. Avec 500 $ de risque par trade, un stop ne peut pas dépasser 20 ticks (0,10). Le CME propose aussi un contrat plus petit, le Micro Silver (SIL, 1 000 onces, un cinquième de SI).",
                "Un contrato SI son 5.000 onzas troy de plata: cada tick de {ts} vale {tv}, y un movimiento completo de {one} vale {pv} por contrato. Con 500 $ de riesgo por operación, un stop no puede superar los 20 ticks (0,10). CME también ofrece un contrato más pequeño, el Micro Silver (SIL, 1.000 onzas, una quinta parte de SI)."),
        "6E": T("One 6E contract is €125,000: each {ts} tick is worth {tv}, and a one-cent move (0.0100) is worth $1,250 per contract. With $500 of risk per trade, a stop can’t be wider than 80 ticks (0.0040). CME also lists a smaller E-micro EUR/USD contract (M6E, €12,500, one tenth of 6E).",
                "Un contrat 6E, c’est 125 000 € : chaque tick de {ts} vaut {tv}, et un mouvement d’un cent (0,0100) vaut 1 250 $ par contrat. Avec 500 $ de risque par trade, un stop ne peut pas dépasser 80 ticks (0,0040). Le CME propose aussi un contrat plus petit, l’E-micro EUR/USD (M6E, 12 500 €, un dixième de 6E).",
                "Un contrato 6E son 125.000 €: cada tick de {ts} vale {tv}, y un movimiento de un centavo (0,0100) vale 1.250 $ por contrato. Con 500 $ de riesgo por operación, un stop no puede superar los 80 ticks (0,0040). CME también ofrece un contrato más pequeño, el E-micro EUR/USD (M6E, 12.500 €, una décima parte de 6E).")}
RISK = 500   # risk per trade used in the worked example
MAX_LOSS = 2000   # the max loss of a 50K evaluation, a common size, in the prop firm paragraph

def make_contract(sym):
    s, name, exch, ts, tv, pv, months, sib, fam = next(c for c in C if c[0] == sym)
    CRUMBS[slug(s)] = T(f"{s} futures", f"Futures {s}", f"Futuros {s}")
    SYSTEM_PAGES.add(slug(s))
    def page(lang, t):
        F = lambda v: _fmt(v, lang); K = lambda v: _tick(v, lang)
        loc = lambda x: re.sub(r'href="@([^"]+)"', lambda m: f'href="{href(lang, m.group(1))}"', x)
        h1 = T(f"{s} futures: tick size, tick value and specs.", f"Contrat à terme {s} : taille et valeur du tick.", f"Futuros {s}: tamaño y valor del tick.")
        if ts == 1: lead = T(f"{s} moves in 1-point ticks worth {F(tv)} each, per contract. {name} ({s}), on {exch}.",
                             f"{s} bouge par ticks de 1 point qui valent {F(tv)} chacun, par contrat. {name} ({s}), sur {exch}.",
                             f"{s} se mueve en ticks de 1 punto que valen {F(tv)} cada uno, por contrato. {name} ({s}), en {exch}.")
        else: lead = T(f"One {s} point is worth {F(pv)} per contract; each {K(ts)} tick is worth {F(tv)}. {name} ({s}), on {exch}.",
                       f"Un point {s} vaut {F(pv)} par contrat ; chaque tick de {K(ts)} vaut {F(tv)}. {name} ({s}), sur {exch}.",
                       f"Un punto de {s} vale {F(pv)} por contrato; cada tick de {K(ts)} vale {F(tv)}. {name} ({s}), en {exch}.")
        hero = ui.hero(t, T("Contract specs","Fiche contrat","Ficha del contrato"), h1, lead)
        key = ui.stats([(t(T("Tick size","Taille du tick","Tamaño del tick")), K(ts), ""), (t(T("Tick value","Valeur du tick","Valor del tick")), F(tv), ""), (t(T("Point value","Valeur du point","Valor del punto")), F(pv), "")])   # the three numbers first; the rest of the sheet under them
        rows = [(T("Symbol","Symbole","Símbolo"), s), (T("Name","Nom","Nombre"), name), (T("Exchange","Bourse","Mercado"), exch),
                (T("Contract months","Mois de contrat","Meses de contrato"), f'<span class="num">{months}</span>'), (T("Trading hours","Heures de marché","Horario"), t(HOURS))]
        tbl = '<table class="tbl specs"><tbody>' + "".join(f"<tr><th>{t(a)}</th><td>{b}</td></tr>" for a, b in rows) + "</tbody></table>"
        stops = [5, 10, 20, 40] if fam == "idx" and pv >= 5 else ([10, 20, 40, 80] if fam=="idx" else None)
        if fam == "energy": stops_t = [10, 20, 30, 50]
        elif fam == "metal": stops_t = [20, 50, 100, 200]
        elif fam == "fx": stops_t = [10, 20, 40, 80]
        else: stops_t = [int(x/ts) for x in stops]
        risk = "".join(f"<tr><th scope=\"row\">{n} ticks <small>({K(round(n*ts, 6))} pts)</small></th><td>{F(n*tv)}</td><td>{F(n*tv*5)}</td></tr>" for n in stops_t)
        rtbl = (f'<div class="cmp-wrap"><table class="cmp risk"><thead><tr><th>{t(T("Stop","Stop","Stop"))}</th><th>{t(T("1 contract","1 contrat","1 contrato"))}</th><th>{t(T("5 contracts","5 contrats","5 contratos"))}</th></tr></thead><tbody>{risk}</tbody></table></div>')
        calc = f'<div class="cta-row"><a class="btn btn-line" href="{href(lang,"position-size-calculator.html")}?sym={s}">{t(T(f"Position size calculator for {s}",f"Calculateur de taille de position pour {s}",f"Calculadora de tamaño de posición para {s}"))}</a></div>'
        # trading it: when it moves, mini or micro, what moves it, a worked stop
        big, mic = (s, sib) if sib and len(sib) > len(s) else (sib, s)
        if sib:
            cb, cm = next(c for c in C if c[0] == big), next(c for c in C if c[0] == mic)
            size_h = T(f"{big} or {mic}", f"{big} ou {mic}", f"{big} o {mic}")
            if s == mic:   # each twin tells its own side: the micro page why the micro, the mini page why the mini
                size_p = T(f"{mic} is the micro version of {big}: one {big} equals 10 {mic}, and every tick is worth ten times less ({F(cm[4])} instead of {F(cb[4])}). The price and the chart are the same; only the size changes. When one {big} is too much risk for your stop, 2 to 9 {mic} fill the gap. Micros also let you exit in steps, one contract at a time, where a single {big} can’t be split.",
                           f"{mic} est la version micro de {big} : un {big} équivaut à 10 {mic}, et chaque tick vaut dix fois moins ({F(cm[4])} au lieu de {F(cb[4])}). Le prix et le graphique sont les mêmes ; seule la taille change. Quand un {big} représente trop de risque pour ton stop, 2 à 9 {mic} comblent l’écart. Les micros permettent aussi de sortir par étapes, un contrat à la fois, là où un seul {big} ne se divise pas.",
                           f"{mic} es la versión micro de {big}: un {big} equivale a 10 {mic}, y cada tick vale diez veces menos ({F(cm[4])} en lugar de {F(cb[4])}). El precio y el gráfico son los mismos; solo cambia el tamaño. Cuando un {big} es demasiado riesgo para tu stop, de 2 a 9 {mic} cubren la diferencia. Los micros también permiten salir por partes, un contrato cada vez, donde un solo {big} no se puede dividir.")
            else:
                size_p = T(f"{big} is the full-size contract; {mic} is its micro, one tenth of it: one {big} equals 10 {mic}, and a tick is worth {F(cb[4])} on {big} against {F(cm[4])} on {mic}. The price and the chart are the same. Once your stop fits one {big}, a single order replaces ten micros: one fill and one commission instead of ten.",
                           f"{big} est le contrat de taille normale ; {mic} est sa version micro, dix fois plus petite : un {big} équivaut à 10 {mic}, et un tick vaut {F(cb[4])} sur {big} contre {F(cm[4])} sur {mic}. Le prix et le graphique sont les mêmes. Quand ton stop tient sur un {big}, un seul ordre remplace dix micros : une exécution et une commission au lieu de dix.",
                           f"{big} es el contrato de tamaño normal; {mic} es su versión micro, diez veces más pequeña: un {big} equivale a 10 {mic}, y un tick vale {F(cb[4])} en {big} frente a {F(cm[4])} en {mic}. El precio y el gráfico son los mismos. Cuando tu stop cabe en un {big}, una sola orden sustituye a diez micros: una ejecución y una comisión en lugar de diez.")
            size_p = {l: size_p[l] + f' <a href="{href(l, slug(sib))}">{sib} →</a>' for l in LANGS}
        else:
            size_h = T("Contract size", "Taille du contrat", "Tamaño del contrato")
            size_p = {l: SIZE[s][l].format(ts=_tick(ts, l), tv=_fmt(tv, l), pv=_fmt(pv, l), one=_fmt(1, l)) for l in LANGS}
        pts = STOP_PTS[s]; ticks = round(pts / ts); cost = ticks * tv; n = int(RISK // cost + 1e-9)
        ct = lambda k: t(T("contract" if k == 1 else "contracts", "contrat" if k == 1 else "contrats", "contrato" if k == 1 else "contratos"))
        ex = T(f"A {K(pts)}-point stop on {s} is {ticks} ticks × {F(tv)} = {F(cost)} per contract. With {F(RISK)} of risk per trade, that’s {n} {ct(n)}, {F(n * cost)} at risk.",
               f"Un stop de {K(pts)} point{'s' if pts >= 2 else ''} sur {s}, c’est {ticks} ticks × {F(tv)} = {F(cost)} par contrat. Avec {F(RISK)} de risque par trade, ça fait {n} {ct(n)}, soit {F(n * cost)} de risque.",
               f"Un stop de {K(pts)} puntos en {s} son {ticks} ticks × {F(tv)} = {F(cost)} por contrato. Con {F(RISK)} de riesgo por operación, {"es" if n == 1 else "son"} {n} {ct(n)}, con {F(n * cost)} en riesgo.")
        if sib:
            c2 = next(c for c in C if c[0] == sib); cost2 = ticks * c2[4]; n2 = int(RISK // cost2 + 1e-9)
            ex = {l: ex[l] + " " + {"en": f"On {sib}, the same stop costs {_fmt(cost2, l)} per contract: {n2} {('contract' if n2 == 1 else 'contracts')}, {_fmt(n2 * cost2, l)} at risk.",
                                    "fr": f"Sur {sib}, le même stop coûte {_fmt(cost2, l)} par contrat : {n2} {('contrat' if n2 == 1 else 'contrats')}, soit {_fmt(n2 * cost2, l)} de risque.",
                                    "es": f"En {sib}, el mismo stop cuesta {_fmt(cost2, l)} por contrato: {n2} {('contrato' if n2 == 1 else 'contratos')}, con {_fmt(n2 * cost2, l)} en riesgo."}[l] for l in LANGS}
        # on a 50K evaluation: how much of the max loss that stop uses, and how many contracts keep a loss under a tenth of it
        pct = round(cost / MAX_LOSS * 100, 1); pcs = lambda l: (f"{pct:g}" if l == "en" else f"{pct:g}".replace(".", ",")); k = int(MAX_LOSS / 10 // cost + 1e-9)
        smaller = mic if sib and s == big else ""
        prop_p = T(f"On a 50K evaluation with a {F(MAX_LOSS)} max loss, a common size, that {K(pts)}-point stop costs {F(cost)} per contract: {pcs('en')}% of the whole allowance on one trade. "
                   + (f"To keep each loss under a tenth of it ({F(MAX_LOSS / 10)}), trade at most {k} {'contract' if k == 1 else 'contracts'}." if k else f"Even one contract risks more than a tenth of it ({F(MAX_LOSS / 10)}): tighten the stop{' or trade ' + smaller if smaller else ''}."),
                   f"Sur une évaluation de 50K avec une perte max de {F(MAX_LOSS)}, une taille courante, ce stop de {K(pts)} point{'s' if pts >= 2 else ''} coûte {F(cost)} par contrat : {pcs('fr')} % de toute la marge sur un seul trade. "
                   + (f"Pour garder chaque perte sous le dixième de cette marge ({F(MAX_LOSS / 10)}), trade au plus {k} {'contrat' if k == 1 else 'contrats'}." if k else f"Même un seul contrat risque plus du dixième de cette marge ({F(MAX_LOSS / 10)}) : resserre le stop{' ou passe à ' + smaller if smaller else ''}."),
                   f"En una evaluación de 50K con una pérdida máxima de {F(MAX_LOSS)}, un tamaño habitual, ese stop de {K(pts)} puntos cuesta {F(cost)} por contrato: el {pcs('es')} % de todo el margen en una sola operación. "
                   + (f"Para mantener cada pérdida por debajo de la décima parte de ese margen ({F(MAX_LOSS / 10)}), opera como máximo {k} {'contrato' if k == 1 else 'contratos'}." if k else f"Incluso un solo contrato arriesga más de la décima parte de ese margen ({F(MAX_LOSS / 10)}): ajusta el stop{' o pasa a ' + smaller if smaller else ''}."))
        art = (f'<h2>{t(T(f"When {s} is most active", f"Quand {s} est le plus actif", f"Cuándo tiene {s} más actividad"))}</h2><p>{t(ACTIVE[fam]).replace("{s}", s)}</p>'
               f'<h2>{t(size_h)}</h2><p>{t(size_p)}</p>'
               f'<h2>{t(T(f"What moves {s}", f"Ce qui fait bouger {s}", f"Qué mueve {s}"))}</h2><p>{loc(t(MOVERS[fam]))} '
               + t(T(f'Check the <a href="{href("en", "release-dates.html")}">release dates</a> before you plan the day.', f'Vérifie les <a href="{href("fr", "release-dates.html")}">dates des annonces</a> avant de planifier ta journée.', f'Revisa las <a href="{href("es", "release-dates.html")}">fechas de publicación</a> antes de planificar el día.')) + '</p>'
               f'<h2>{t(T("Example","Exemple","Ejemplo"))}</h2><p>{t(ex)}</p>'
               + (f'<p>{t(T(f"On {s}, the previous day’s high and low are levels many traders watch: see <a href=\"{href("en", "liquidity-sweep.html")}\">what a liquidity sweep is</a>.", f"Sur {s}, le plus haut et le plus bas de la veille sont des niveaux que beaucoup de traders surveillent : voir <a href=\"{href("fr", "liquidity-sweep.html")}\">ce qu’est un liquidity sweep</a>.", f"En {s}, el máximo y el mínimo del día anterior son niveles que muchos traders vigilan: mira <a href=\"{href("es", "liquidity-sweep.html")}\">qué es un liquidity sweep</a>."))}</p>' if s in ("NQ", "MNQ") else "")
               + f'<h2>{t(T(f"{s} on a prop firm account", f"{s} sur un compte de prop firm", f"{s} en una cuenta de prop firm"))}</h2><p>{t(prop_p)}</p>')
        band = ui.band(t(T(f"Journal your {s} trades.",f"Journalise tes trades {s}.",f"Registra tus operaciones de {s}.")),
                       t(T(f"Sweep knows the {s} tick value: your net P&L and R are exact, and every trade shows on real CME candles.",f"Sweep connaît la valeur du tick {s} : ton P&L net et ton R sont exacts, et chaque trade s’affiche sur de vraies bougies CME.",f"Sweep conoce el valor del tick de {s}: tu P&L neto y tu R son exactos, y cada operación se ve sobre velas reales de CME.")),
                       ui.btn(t(CREATE_FREE), SIGNUP, lg=True, attrs='data-track="signup_contract"'))
        others = (f'<div class="chiprow" style="margin-top:40px"><span class="eyebrow">{t(T("Other contracts","Autres contrats","Otros contratos"))}</span>'
                  + "".join(f'<a class="chip" href="{href(lang,slug(c[0]))}">{c[0]}</a>' for c in C if c[0] != s) + "</div>")
        faqs = [(T(f"What is the tick value of {s}?",f"Quelle est la valeur du tick de {s} ?",f"¿Cuál es el valor del tick de {s}?"),
                 T(f"One {s} tick ({_tick(ts)}) is worth {_fmt(tv)} per contract.",f"Un tick {s} ({_tick(ts, 'fr')}) vaut {_fmt(tv, 'fr')} par contrat.",f"Un tick de {s} ({_tick(ts, 'es')}) vale {_fmt(tv, 'es')} por contrato.")),
                (T(f"How much is one point of {s} worth?",f"Combien vaut un point de {s} ?",f"¿Cuánto vale un punto de {s}?"),
                 T(f"One full point is worth {_fmt(pv)} per contract.",f"Un point complet vaut {_fmt(pv, 'fr')} par contrat.",f"Un punto completo vale {_fmt(pv, 'es')} por contrato."))]
        if sib:
            faqs.append((T(f"How many {mic} equal one {big}?", f"Combien de {mic} font un {big} ?", f"¿Cuántos {mic} equivalen a un {big}?"),
                         T(f"Ten. One {big} equals 10 {mic}: same price and chart, a tenth of the size.", f"Dix. Un {big} équivaut à 10 {mic} : même prix et même graphique, dix fois moins gros.",
                           f"Diez. Un {big} equivale a 10 {mic}: mismo precio y mismo gráfico, una décima parte del tamaño.")))
        faqs.append((T(f"What are {s} trading hours?", f"Quelles sont les heures de marché de {s} ?", f"¿Cuál es el horario de {s}?"), HOURS))
        b = (ui.sec(key + calc + tbl + f'<p class="fine" style="margin-top:16px">{t(NOTE)}</p>', "t", "specs", width="read")
             + ui.sec(ui.head(t, None, T(f"What a stop costs on {s}",f"Ce que coûte un stop sur {s}",f"Lo que cuesta un stop en {s}")) + rtbl, "n", "stops", width="read")
             + ui.sec(f'<article class="article">{art}</article>' + ui.head(t, None, T("Questions","Questions","Preguntas")) + ui.qa(t, faqs), "n", "trading", width="read")
             + ui.sec(band + others, "t", "journal"))
        ld = jsonld({"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{"@type":"Question","name":t(q),"acceptedAnswer":{"@type":"Answer","text":t(a)}} for q,a in faqs]})
        return (spec_title(s, tv, pv, ts, lang),
                t(T(f"{name} ({s}) futures: tick size {_tick(ts)}, tick value {_fmt(tv)}, point value {_fmt(pv)}, trading hours and what a stop costs, for prop traders.",
                    f"Contrat {name} ({s}) : tick de {_tick(ts, 'fr')}, valeur du tick {_fmt(tv, 'fr')}, valeur du point {_fmt(pv, 'fr')}, heures de marché et coût d’un stop, pour les traders prop.",
                    f"Futuros {name} ({s}): tick de {_tick(ts, 'es')}, valor del tick {_fmt(tv, 'es')}, valor del punto {_fmt(pv, 'es')}, horario y coste de un stop, para traders prop.")),
                hero + b + ui.final(lang, t), ld)
    return page

def page_contracts(lang, t):
    hero = ui.hero(t, T("Contract specs","Fiches contrats","Fichas"), T("CME futures contract specs.","Fiches des contrats à terme CME.","Fichas de los contratos de futuros de CME."),
        T("Tick size, tick value and point value for the 14 contracts Sweep charts.","Taille du tick, valeur du tick et valeur du point pour les 14 contrats que Sweep affiche en graphique.","Tamaño del tick, valor del tick y valor del punto para los 14 contratos que Sweep muestra en gráfico."))
    L = [t(T("Name","Nom","Nombre")), t(T("Tick","Tick","Tick")), t(T("Tick value","Valeur du tick","Valor del tick")), t(T("Point value","Valeur du point","Valor del punto"))]
    rows = "".join(f'<tr><th scope="row"><a href="{href(lang,slug(s))}">{s}</a></th><td data-label="{L[0]}">{n}</td><td class="num" data-label="{L[1]}">{_tick(ts, lang)}</td><td class="num" data-label="{L[2]}">{_fmt(tv, lang)}</td><td class="num" data-label="{L[3]}">{_fmt(pv, lang)}</td></tr>' for s,n,_,ts,tv,pv,_,_,_ in C)
    tbl = (f'<div class="cmp-wrap"><table class="cmp guide specs-all"><thead><tr><th scope="col">{t(T("Symbol","Symbole","Símbolo"))}</th>' + "".join(f'<th scope="col">{x}</th>' for x in L) + f'</tr></thead><tbody>{rows}</tbody></table></div>')
    guide = T("""<h2>How to read a contract spec</h2><ul>
<li><b>Tick size.</b> The smallest price step: 0.25 points on NQ and ES, 1 point on YM, 0.01 on crude oil.</li>
<li><b>Tick value.</b> What one tick is worth per contract. Your P&L is ticks × tick value × contracts.</li>
<li><b>Point value.</b> What a full one-point move is worth: tick value ÷ tick size, so $5 ÷ 0.25 = $20 on NQ.</li>
<li><b>Micro contracts.</b> MNQ, MES, MYM, M2K, MCL and MGC are one tenth of their mini: same price, same chart, ticks worth ten times less.</li></ul>
<h2>Contract months and rollover</h2><p>Each letter is a delivery month: F January, G February, H March, J April, K May, M June, N July, Q August, U September, V October, X November, Z December. The year follows: NQZ6 is the December 2026 Nasdaq-100 contract.</p>
<p>Equity index futures expire every quarter, on the third Friday of March, June, September and December. Volume moves to the next contract about a week before, which is when most traders roll. Crude oil has a contract for every month, and gold trades mostly in its even months.</p>
<h2>Why it matters on a prop account</h2><p>Your firm’s max loss is in dollars, but your stop is in points. The point value turns one into the other: a $2,000 max loss is 100 points on one NQ, 40 points on one ES and 1,000 points on one MNQ. It tells you how many losing trades your account can take before the limit, and the <a href="@position-size-calculator.html">position size calculator</a> does the math for any stop.</p>""",
"""<h2>Comment lire une fiche contrat</h2><ul>
<li><b>Taille du tick.</b> Le plus petit pas de prix : 0,25 point sur NQ et ES, 1 point sur YM, 0,01 sur le pétrole brut.</li>
<li><b>Valeur du tick.</b> Ce que vaut un tick par contrat. Ton P&L, c’est ticks × valeur du tick × contrats.</li>
<li><b>Valeur du point.</b> Ce que vaut un mouvement complet d’un point : valeur du tick ÷ taille du tick, donc 5 $ ÷ 0,25 = 20 $ sur NQ.</li>
<li><b>Contrats micro.</b> MNQ, MES, MYM, M2K, MCL et MGC valent un dixième de leur mini : même prix, même graphique, des ticks dix fois plus petits.</li></ul>
<h2>Mois de contrat et rollover</h2><p>Chaque lettre est un mois de livraison : F janvier, G février, H mars, J avril, K mai, M juin, N juillet, Q août, U septembre, V octobre, X novembre, Z décembre. L’année suit : NQZ6 est le contrat Nasdaq-100 de décembre 2026.</p>
<p>Les contrats sur indices boursiers expirent chaque trimestre, le troisième vendredi de mars, juin, septembre et décembre. Le volume passe au contrat suivant environ une semaine avant : c’est là que la plupart des traders font leur rollover. Le pétrole brut a un contrat chaque mois, et l’or se négocie surtout sur ses mois pairs.</p>
<h2>Pourquoi ça compte sur un compte prop</h2><p>La perte max de ta firme est en dollars, mais ton stop est en points. La valeur du point fait le lien : une perte max de 2 000 $, c’est 100 points sur un NQ, 40 points sur un ES et 1 000 points sur un MNQ. Elle te dit combien de trades perdants ton compte peut encaisser avant la limite, et le <a href="@position-size-calculator.html">calculateur de taille de position</a> fait le calcul pour n’importe quel stop.</p>""",
"""<h2>Cómo leer una ficha de contrato</h2><ul>
<li><b>Tamaño del tick.</b> El paso de precio más pequeño: 0,25 puntos en NQ y ES, 1 punto en YM, 0,01 en el crudo.</li>
<li><b>Valor del tick.</b> Lo que vale un tick por contrato. Tu P&L son ticks × valor del tick × contratos.</li>
<li><b>Valor del punto.</b> Lo que vale un movimiento completo de un punto: valor del tick ÷ tamaño del tick, así que 5 $ ÷ 0,25 = 20 $ en NQ.</li>
<li><b>Contratos micro.</b> MNQ, MES, MYM, M2K, MCL y MGC valen una décima parte de su mini: mismo precio, mismo gráfico, ticks diez veces menores.</li></ul>
<h2>Meses de contrato y rollover</h2><p>Cada letra es un mes de entrega: F enero, G febrero, H marzo, J abril, K mayo, M junio, N julio, Q agosto, U septiembre, V octubre, X noviembre, Z diciembre. Después va el año: NQZ6 es el contrato del Nasdaq-100 de diciembre de 2026.</p>
<p>Los futuros sobre índices bursátiles vencen cada trimestre, el tercer viernes de marzo, junio, septiembre y diciembre. El volumen pasa al contrato siguiente más o menos una semana antes, y es cuando la mayoría de los traders hacen el rollover. El crudo tiene un contrato cada mes, y el oro se negocia sobre todo en sus meses pares.</p>
<h2>Por qué importa en una cuenta prop</h2><p>La pérdida máx. de tu firma está en dólares, pero tu stop está en puntos. El valor del punto une las dos cosas: una pérdida máx. de 2.000 $ son 100 puntos en un NQ, 40 puntos en un ES y 1.000 puntos en un MNQ. Te dice cuántas operaciones perdedoras aguanta tu cuenta antes del límite, y la <a href="@position-size-calculator.html">calculadora de tamaño de posición</a> hace el cálculo para cualquier stop.</p>""")
    compare = (f'<div class="chiprow" style="margin-top:32px"><span class="eyebrow">{t(T("Compare", "Comparer", "Comparar"))}</span>'
               + "".join(f'<a class="chip" href="{href(lang, p)}">{CROSS_NAME(p)}</a>' for p in CROSS_PAGES) + "</div>")
    b = (ui.sec(tbl + f'<p class="fine" style="margin-top:16px">{t(NOTE)}</p>' + compare, "t", "contracts")
         + ui.sec(f'<article class="article">{re.sub(r'href="@([^"]+)"', lambda m: f'href="{href(lang, m.group(1))}"', t(guide))}</article>', "n", "read", width="read"))
    return (t(T("Futures tick values: NQ, ES, YM, RTY, CL, GC, SI, 6E · Sweep","Valeur du tick : NQ, ES, YM, RTY, CL, GC, SI, 6E · Sweep","Valor del tick: NQ, ES, YM, RTY, CL, GC, SI, 6E · Sweep")),
            t(T("Tick size, tick value and point value for NQ, MNQ, ES, MES, YM, MYM, RTY, M2K, CL, MCL, GC, MGC, SI and 6E futures, with what a stop costs.","Taille, valeur du tick et valeur du point pour NQ, MNQ, ES, MES, YM, MYM, RTY, M2K, CL, MCL, GC, MGC, SI et 6E, avec le coût d’un stop.","Tamaño, valor del tick y valor del punto para NQ, MNQ, ES, MES, YM, MYM, RTY, M2K, CL, MCL, GC, MGC, SI y 6E, con el coste de un stop.")),
            hero + b + ui.final(lang, t), "")
SYSTEM_PAGES.add("futures-contracts.html")

# ---------------------------------------------------------------- mini vs micro, and NQ vs ES (SEO brief v2, 4.4): the two contracts side by side, and what each one means on a 50K prop account
PAIRS = [("NQ", "MNQ"), ("ES", "MES"), ("CL", "MCL"), ("GC", "MGC"), ("YM", "MYM"), ("NQ", "ES")]
def pair_slug(a, b): return f"{a.lower()}-vs-{b.lower()}.html"
PAIR_PAGES = [pair_slug(a, b) for a, b in PAIRS]
MKT = {"NQ": T("Nasdaq-100 index", "indice Nasdaq-100", "índice Nasdaq-100"), "ES": T("S&P 500 index", "indice S&P 500", "índice S&P 500"),
       "YM": T("Dow Jones Industrial Average", "indice Dow Jones", "índice Dow Jones"), "CL": T("WTI crude oil", "pétrole brut WTI", "crudo WTI"), "GC": T("gold", "or", "oro")}
UNIT = {"NQ": (20, "idx"), "MNQ": (2, "idx"), "ES": (50, "idx"), "MES": (5, "idx"), "YM": (5, "idx"), "MYM": (0.5, "idx"),
        "CL": (1000, "bbl"), "MCL": (100, "bbl"), "GC": (100, "oz"), "MGC": (10, "oz")}   # what one contract is: $ × the index, or barrels, or troy ounces (CME)
def _unit(s, lang):
    v, k = UNIT[s]
    if k == "idx": return {"en": f"{_fmt(v)} × index", "fr": f"{_fmt(v, 'fr')} × indice", "es": f"{_fmt(v, 'es')} × índice"}[lang]
    n = f"{v:,}".replace(",", {"en": ",", "fr": " ", "es": "."}[lang])
    return {"bbl": {"en": f"{n} barrels", "fr": f"{n} barils", "es": f"{n} barriles"}, "oz": {"en": f"{n} troy ounces", "fr": f"{n} onces troy", "es": f"{n} onzas troy"}}[k][lang]
CROSS_PAGES = [pair_slug(a, b) for a, b in PAIRS] + ["mes-vs-mnq.html"]
CROSS_NAME = lambda p: p[:-5].upper().replace("-VS-", " vs ")

def _contract_limits():
    """(fewest, most) minis allowed on a 50K evaluation, from the app's catalogue."""
    import presets
    v = [s["eval"]["max_minis"] for f in presets.FIRMS for p in f["programs"] for s in p["sizes"] if s["size"] == 50000 and (s.get("eval") or {}).get("max_minis")]
    return min(v), max(v)

def make_pair(a, b):
    ca, cb = next(c for c in C if c[0] == a), next(c for c in C if c[0] == b)
    micro = ca[7] == b   # mini vs its micro; otherwise two minis (NQ vs ES)
    page_id = pair_slug(a, b)
    CRUMBS[page_id] = T(f"{a} vs {b}", f"{a} ou {b}", f"{a} o {b}")
    SYSTEM_PAGES.add(page_id)
    def page(lang, t):
        F = lambda v: _fmt(v, lang); K = lambda v: _tick(v, lang)
        loc = lambda x: re.sub(r'href="@([^"]+)"', lambda m: f'href="{href(lang, m.group(1))}"', x)
        lo, hi = _contract_limits()
        lk = lambda s: f'<a href="{href(lang, slug(s))}">{s}</a>'
        if micro:
            fam = ca[8]; pts = STOP_PTS[a]; ts = ca[3]
            cost_a, cost_b = round(pts / ts) * ca[4], round(pts / ts) * cb[4]
            na, nb = int(MAX_LOSS // cost_a + 1e-9), int(MAX_LOSS // cost_b + 1e-9)
            kind = T("mini or micro?", "mini ou micro ?", "¿mini o micro?") if fam == "idx" else T("full size or micro?", "taille normale ou micro ?", "¿tamaño normal o micro?")
            h1 = T(f"{a} vs {b}: {kind['en']}", f"{a} ou {b} : {kind['fr']}", f"{a} o {b}: {kind['es']}")
            lead = T(f"{b} is a tenth of {a}: same {MKT[a]['en']}, same tick size ({_tick(ts)}), but {_fmt(cb[5])} a point instead of {_fmt(ca[5])}. On a 50K prop account, a {_tick(pts)}-point stop costs {_fmt(cost_a)} on 1 {a} and {_fmt(cost_b)} on 1 {b}.",
                     f"{b} vaut un dixième de {a} : même {MKT[a]['fr']}, même taille de tick ({_tick(ts, 'fr')}), mais {_fmt(cb[5], 'fr')} le point au lieu de {_fmt(ca[5], 'fr')}. Sur un compte prop de 50K, un stop de {_tick(pts, 'fr')} point{'s' if pts >= 2 else ''} coûte {_fmt(cost_a, 'fr')} sur 1 {a} et {_fmt(cost_b, 'fr')} sur 1 {b}.",
                     f"{b} vale una décima parte de {a}: mismo {MKT[a]['es']}, mismo tamaño de tick ({_tick(ts, 'es')}), pero {_fmt(cb[5], 'es')} por punto en lugar de {_fmt(ca[5], 'es')}. En una cuenta prop de 50K, un stop de {_tick(pts, 'es')} puntos cuesta {_fmt(cost_a, 'es')} en 1 {a} y {_fmt(cost_b, 'es')} en 1 {b}.")
            rows = [(T("One contract", "Un contrat", "Un contrato"), _unit(a, lang), _unit(b, lang)),
                    (T("Tick size", "Taille du tick", "Tamaño del tick"), K(ts), K(ts)), (T("Tick value", "Valeur du tick", "Valor del tick"), F(ca[4]), F(cb[4])),
                    (T("Point value", "Valeur du point", "Valor del punto"), F(ca[5]), F(cb[5])),
                    (T(f"A {_tick(pts)}-point stop", f"Un stop de {_tick(pts, 'fr')} point{'s' if pts >= 2 else ''}", f"Un stop de {_tick(pts, 'es')} puntos"), F(cost_a), F(cost_b)),
                    (T(f"Losing trades before a {_fmt(MAX_LOSS)} max loss", f"Pertes avant une perte max de {_fmt(MAX_LOSS, 'fr')}", f"Pérdidas antes de una pérdida máx. de {_fmt(MAX_LOSS, 'es')}"), str(na), str(nb)),
                    (T("Exchange", "Bourse", "Mercado"), ca[2], cb[2])]
            body = (f'<h2>{t(T("Same chart, a tenth of the dollars", "Même graphique, dix fois moins de dollars", "Mismo gráfico, diez veces menos dólares"))}</h2>'
                    f'<p>{t(T(f"{a} and {b} follow the same {MKT[a]["en"]}, so they move the same number of points in a session: whatever the market does, {b} gains or loses a tenth of the dollars of {a}. The volatility in points is the same; only the size of your position changes. Both trade on CME Globex, with the same hours.",
                              f"{a} et {b} suivent le même {MKT[a]["fr"]}, donc ils bougent du même nombre de points dans une séance : quoi que fasse le marché, {b} gagne ou perd un dixième des dollars de {a}. La volatilité en points est la même ; seule la taille de ta position change. Les deux se négocient sur CME Globex, aux mêmes heures.",
                              f"{a} y {b} siguen el mismo {MKT[a]["es"]}, así que se mueven el mismo número de puntos en una sesión: haga lo que haga el mercado, {b} gana o pierde una décima parte de los dólares de {a}. La volatilidad en puntos es la misma; solo cambia el tamaño de tu posición. Los dos cotizan en CME Globex, con el mismo horario."))}</p>'
                    f'<h2>{t(T("Which one for a 50K prop account?", "Lequel pour un compte prop de 50K ?", "¿Cuál para una cuenta prop de 50K?"))}</h2>'
                    f'<p>{t(T(f"Take a 50K evaluation with a {_fmt(MAX_LOSS)} max loss, a common size, and a {_tick(pts)}-point stop. On {a}, that stop costs {_fmt(cost_a)} per contract: {na} losing trades in a row reach the max loss. On {b}, it costs {_fmt(cost_b)}: {nb} losing trades. {b} also lets you size in steps, 2, 3 or 5 micros, instead of all or nothing.",
                              f"Prends une évaluation de 50K avec une perte max de {_fmt(MAX_LOSS, 'fr')}, une taille courante, et un stop de {_tick(pts, 'fr')} point{'s' if pts >= 2 else ''}. Sur {a}, ce stop coûte {_fmt(cost_a, 'fr')} par contrat : {na} pertes de suite atteignent la perte max. Sur {b}, il coûte {_fmt(cost_b, 'fr')} : {nb} pertes. {b} permet aussi d’ajuster ta taille par paliers, 2, 3 ou 5 micros, au lieu de tout ou rien.",
                              f"Toma una evaluación de 50K con una pérdida máxima de {_fmt(MAX_LOSS, 'es')}, un tamaño habitual, y un stop de {_tick(pts, 'es')} puntos. En {a}, ese stop cuesta {_fmt(cost_a, 'es')} por contrato: {na} pérdidas seguidas llegan a la pérdida máxima. En {b}, cuesta {_fmt(cost_b, 'es')}: {nb} pérdidas. {b} también te deja ajustar el tamaño por escalones, 2, 3 o 5 micros, en lugar de todo o nada."))}</p>'
                    f'<p>{t(T(f"Start on {b}. Move to {a} when your plan risks at least {_fmt(cost_a)} per trade with that stop, the cost of 10 micros, and your journal shows you follow your rules at that size. Commissions are charged per contract: check what 10 {b} cost you against 1 {a}. The <a href=\"@position-size-calculator.html\">position size calculator</a> gives the number of contracts for your stop and your risk.",
                              f"Commence sur {b}. Passe à {a} quand ton plan risque au moins {_fmt(cost_a, 'fr')} par trade avec ce stop, le coût de 10 micros, et que ton journal montre que tu suis tes règles à cette taille. Les commissions se paient par contrat : compare ce que te coûtent 10 {b} et 1 {a}. Le <a href=\"@position-size-calculator.html\">calculateur de taille de position</a> donne le nombre de contrats pour ton stop et ton risque.",
                              f"Empieza en {b}. Pasa a {a} cuando tu plan arriesgue al menos {_fmt(cost_a, 'es')} por operación con ese stop, el coste de 10 micros, y tu diario muestre que sigues tus reglas a ese tamaño. Las comisiones se cobran por contrato: compara lo que te cuestan 10 {b} y 1 {a}. La <a href=\"@position-size-calculator.html\">calculadora de tamaño de posición</a> da el número de contratos para tu stop y tu riesgo."))}</p>')
            faqs = [(T(f"Is {b} the same as {a}?", f"{b} est-il pareil que {a} ?", f"¿Es {b} lo mismo que {a}?"),
                     T(f"Same market and chart, a tenth of the size: one {a} equals 10 {b}. One {b} tick is worth {_fmt(cb[4])}, one {a} tick {_fmt(ca[4])}.",
                       f"Même marché et même graphique, dix fois plus petit : un {a} équivaut à 10 {b}. Un tick {b} vaut {_fmt(cb[4], 'fr')}, un tick {a} {_fmt(ca[4], 'fr')}.",
                       f"Mismo mercado y mismo gráfico, una décima parte del tamaño: un {a} equivale a 10 {b}. Un tick de {b} vale {_fmt(cb[4], 'es')}, uno de {a} {_fmt(ca[4], 'es')}.")),
                    (T(f"Should I trade {a} or {b} on a prop firm account?", f"Faut-il trader {a} ou {b} sur un compte de prop firm ?", f"¿Debo operar {a} o {b} en una cuenta de prop firm?"),
                     T(f"Start with {b}: on a 50K with a {_fmt(MAX_LOSS)} max loss, a {_tick(pts)}-point stop is {_fmt(cost_b)} on {b} and {_fmt(cost_a)} on {a}. Move to {a} once your risk per trade covers 10 micros and you follow your rules at that size.",
                       f"Commence par {b} : sur un 50K avec une perte max de {_fmt(MAX_LOSS, 'fr')}, un stop de {_tick(pts, 'fr')} point{'s' if pts >= 2 else ''} vaut {_fmt(cost_b, 'fr')} sur {b} et {_fmt(cost_a, 'fr')} sur {a}. Passe à {a} quand ton risque par trade couvre 10 micros et que tu suis tes règles à cette taille.",
                       f"Empieza con {b}: en una 50K con una pérdida máxima de {_fmt(MAX_LOSS, 'es')}, un stop de {_tick(pts, 'es')} puntos son {_fmt(cost_b, 'es')} en {b} y {_fmt(cost_a, 'es')} en {a}. Pasa a {a} cuando tu riesgo por operación cubra 10 micros y sigas tus reglas a ese tamaño.")),
                    (T(f"How much is one point on {a} and {b}?", f"Combien vaut un point sur {a} et {b} ?", f"¿Cuánto vale un punto en {a} y {b}?"),
                     T(f"{_fmt(ca[5])} on {a} and {_fmt(cb[5])} on {b}, per contract.", f"{_fmt(ca[5], 'fr')} sur {a} et {_fmt(cb[5], 'fr')} sur {b}, par contrat.", f"{_fmt(ca[5], 'es')} en {a} y {_fmt(cb[5], 'es')} en {b}, por contrato."))]
            name_t = {"NQ": T("Nasdaq Mini or Micro Futures?", "mini ou micro Nasdaq, lequel choisir ?", "¿mini o micro Nasdaq?"), "ES": T("S&P 500 Mini or Micro Futures?", "mini ou micro S&P 500, lequel choisir ?", "¿mini o micro S&P 500?"),
                      "YM": T("Dow Mini or Micro Futures?", "mini ou micro Dow, lequel choisir ?", "¿mini o micro Dow?"), "CL": T("Crude Oil or Micro Crude Oil?", "pétrole brut ou micro, lequel choisir ?", "¿crudo o micro crudo?"),
                      "GC": T("Gold or Micro Gold Futures?", "or ou micro or, lequel choisir ?", "¿oro o micro oro?")}[a]
            title = T(f"{a} vs {b}: {name_t['en']} · Sweep", f"{a} vs {b} : {name_t['fr']} · Sweep", f"{a} vs {b}: {name_t['es']} · Sweep")
            desc = T(f"{a} vs {b}: tick and point values side by side, what a {_tick(pts)}-point stop costs on each, and which one fits a 50K prop firm account.",
                     f"{a} ou {b} : valeurs du tick et du point côte à côte, ce que coûte un stop de {_tick(pts, 'fr')} point{'s' if pts >= 2 else ''} sur chacun, et lequel convient à un compte prop de 50K.",
                     f"{a} o {b}: valores del tick y del punto lado a lado, lo que cuesta un stop de {_tick(pts, 'es')} puntos en cada uno, y cuál encaja en una cuenta prop de 50K.")
        else:   # NQ vs ES: two minis, the same dollars in points
            pa, pb = RISK / ca[5], RISK / cb[5]; sa, sb = STOP_PTS[a], STOP_PTS[b]
            cost_a, cost_b = sa * ca[5], sb * cb[5]
            h1 = T(f"{a} vs {b}: which E-mini to trade?", f"{a} ou {b} : quel E-mini trader ?", f"{a} o {b}: ¿qué E-mini operar?")
            lead = T(f"{a} follows the Nasdaq-100 at {_fmt(ca[5])} a point; {b} follows the S&P 500 at {_fmt(cb[5])} a point. Both tick in {_tick(ca[3])} points on CME. {a} usually moves more points in a session, so the same dollar risk gives a wider stop: {_fmt(RISK)} is {pa:g} {a} points or {pb:g} {b} points.",
                     f"{a} suit le Nasdaq-100 à {_fmt(ca[5], 'fr')} le point ; {b} suit le S&P 500 à {_fmt(cb[5], 'fr')} le point. Les deux bougent par ticks de {_tick(ca[3], 'fr')} point sur le CME. {a} bouge en général de plus de points dans une séance, donc le même risque en dollars donne un stop plus large : {_fmt(RISK, 'fr')}, c’est {pa:g} points {a} ou {pb:g} points {b}.",
                     f"{a} sigue al Nasdaq-100 a {_fmt(ca[5], 'es')} por punto; {b} sigue al S&P 500 a {_fmt(cb[5], 'es')} por punto. Los dos se mueven en ticks de {_tick(ca[3], 'es')} puntos en CME. {a} suele moverse más puntos en una sesión, así que el mismo riesgo en dólares da un stop más ancho: {_fmt(RISK, 'es')} son {pa:g} puntos de {a} o {pb:g} puntos de {b}.")
            rows = [(T("Market", "Marché", "Mercado"), t(MKT[a]), t(MKT[b])), (T("One contract", "Un contrat", "Un contrato"), _unit(a, lang), _unit(b, lang)),
                    (T("Tick size", "Taille du tick", "Tamaño del tick"), K(ca[3]), K(cb[3])), (T("Tick value", "Valeur du tick", "Valor del tick"), F(ca[4]), F(cb[4])),
                    (T("Point value", "Valeur du point", "Valor del punto"), F(ca[5]), F(cb[5])),
                    (T(f"{_fmt(RISK)} of risk, in points", f"{_fmt(RISK, 'fr')} de risque, en points", f"{_fmt(RISK, 'es')} de riesgo, en puntos"), f"{pa:g}", f"{pb:g}"),
                    (T("Its micro (a tenth)", "Son micro (un dixième)", "Su micro (una décima parte)"), lk(ca[7]), lk(cb[7])),
                    (T("Exchange", "Bourse", "Mercado"), ca[2], cb[2])]
            body = (f'<h2>{t(T("Points and dollars", "Points et dollars", "Puntos y dólares"))}</h2>'
                    f'<p>{t(T(f"The Nasdaq-100 is quoted at a higher level than the S&P 500 and usually moves more points in a session, while a tick is worth less on {a} ({_fmt(ca[4])}) than on {b} ({_fmt(cb[4])}). The same idea in dollars needs a wider stop in points on {a}: plan your stop in dollars first, then turn it into points for the contract you trade.",
                              f"Le Nasdaq-100 est coté à un niveau plus élevé que le S&P 500 et bouge en général de plus de points dans une séance, alors qu’un tick vaut moins sur {a} ({_fmt(ca[4], 'fr')}) que sur {b} ({_fmt(cb[4], 'fr')}). La même idée en dollars demande un stop plus large en points sur {a} : fixe ton stop en dollars d’abord, puis traduis-le en points pour le contrat que tu trades.",
                              f"El Nasdaq-100 cotiza a un nivel más alto que el S&P 500 y suele moverse más puntos en una sesión, mientras que un tick vale menos en {a} ({_fmt(ca[4], 'es')}) que en {b} ({_fmt(cb[4], 'es')}). La misma idea en dólares pide un stop más ancho en puntos en {a}: fija tu stop en dólares primero y luego pásalo a puntos para el contrato que operas."))}</p>'
                    f'<h2>{t(T("Which one for a 50K prop account?", "Lequel pour un compte prop de 50K ?", "¿Cuál para una cuenta prop de 50K?"))}</h2>'
                    f'<p>{t(T(f"On a 50K evaluation with a {_fmt(MAX_LOSS)} max loss, a common size, one {a} with a {sa:g}-point stop risks {_fmt(cost_a)}, and one {b} with a {sb:g}-point stop risks {_fmt(cost_b)}: {int(MAX_LOSS // cost_a)} and {int(MAX_LOSS // cost_b)} losing trades before the max loss. Both are big for a 50K. Their micros, {ca[7]} and {cb[7]}, cost a tenth: they are compared in <a href=\"@mes-vs-mnq.html\">MES vs MNQ</a>.",
                              f"Sur une évaluation de 50K avec une perte max de {_fmt(MAX_LOSS, 'fr')}, une taille courante, un {a} avec un stop de {sa:g} points risque {_fmt(cost_a, 'fr')}, et un {b} avec un stop de {sb:g} points risque {_fmt(cost_b, 'fr')} : {int(MAX_LOSS // cost_a)} et {int(MAX_LOSS // cost_b)} pertes avant la perte max. Les deux sont gros pour un 50K. Leurs micros, {ca[7]} et {cb[7]}, coûtent dix fois moins : ils sont comparés dans <a href=\"@mes-vs-mnq.html\">MES ou MNQ</a>.",
                              f"En una evaluación de 50K con una pérdida máxima de {_fmt(MAX_LOSS, 'es')}, un tamaño habitual, un {a} con un stop de {sa:g} puntos arriesga {_fmt(cost_a, 'es')}, y un {b} con un stop de {sb:g} puntos arriesga {_fmt(cost_b, 'es')}: {int(MAX_LOSS // cost_a)} y {int(MAX_LOSS // cost_b)} pérdidas antes de la pérdida máxima. Los dos son grandes para una 50K. Sus micros, {ca[7]} y {cb[7]}, cuestan diez veces menos: están comparados en <a href=\"@mes-vs-mnq.html\">MES o MNQ</a>."))}</p>'
                    f'<p>{t(T("Neither is better in itself. Pick the chart you read best after watching both for a few sessions in your window, then keep it: switching markets resets what your journal can tell you.",
                              "Aucun n’est meilleur en soi. Choisis le graphique que tu lis le mieux après avoir observé les deux quelques séances dans ta fenêtre, puis garde-le : changer de marché remet à zéro ce que ton journal peut t’apprendre.",
                              "Ninguno es mejor en sí. Elige el gráfico que lees mejor después de observar los dos unas sesiones en tu ventana, y quédate con él: cambiar de mercado reinicia lo que tu diario puede decirte."))}</p>')
            faqs = [(T(f"Is {a} or {b} better for prop firm trading?", f"{a} ou {b}, lequel est meilleur en prop firm ?", f"¿Es mejor {a} o {b} para operar en prop firms?"),
                     T(f"Neither in itself. {a} is {_fmt(ca[5])} a point and usually moves more points; {b} is {_fmt(cb[5])} a point. Pick the chart you read best, size it in dollars, then keep it.",
                       f"Aucun en soi. {a} vaut {_fmt(ca[5], 'fr')} le point et bouge en général de plus de points ; {b} vaut {_fmt(cb[5], 'fr')} le point. Choisis le graphique que tu lis le mieux, calcule ta taille en dollars, puis garde-le.",
                       f"Ninguno en sí. {a} vale {_fmt(ca[5], 'es')} por punto y suele moverse más puntos; {b} vale {_fmt(cb[5], 'es')} por punto. Elige el gráfico que lees mejor, calcula tu tamaño en dólares y quédate con él.")),
                    (T(f"How much is one point on {a} and {b}?", f"Combien vaut un point sur {a} et {b} ?", f"¿Cuánto vale un punto en {a} y {b}?"),
                     T(f"{_fmt(ca[5])} on {a} and {_fmt(cb[5])} on {b}, per contract. One tick (0.25 point) is {_fmt(ca[4])} on {a} and {_fmt(cb[4])} on {b}.",
                       f"{_fmt(ca[5], 'fr')} sur {a} et {_fmt(cb[5], 'fr')} sur {b}, par contrat. Un tick (0,25 point) vaut {_fmt(ca[4], 'fr')} sur {a} et {_fmt(cb[4], 'fr')} sur {b}.",
                       f"{_fmt(ca[5], 'es')} en {a} y {_fmt(cb[5], 'es')} en {b}, por contrato. Un tick (0,25 puntos) vale {_fmt(ca[4], 'es')} en {a} y {_fmt(cb[4], 'es')} en {b}.")),
                    (T(f"What are {a} and {b} trading hours?", f"Quelles sont les heures de marché de {a} et {b} ?", f"¿Cuál es el horario de {a} y {b}?"), HOURS)]
            title = T(f"{a} vs {b}: Which E-mini Index Future to Trade? · Sweep", f"{a} vs {b} : quel E-mini trader en prop firm ? · Sweep", f"{a} vs {b}: ¿qué E-mini operar en prop firms? · Sweep")
            desc = T(f"{a} vs {b}: tick and point values side by side, the same {_fmt(RISK)} of risk in points on each, and what one contract means on a 50K prop account.",
                     f"{a} ou {b} : valeurs du tick et du point côte à côte, le même risque de {_fmt(RISK, 'fr')} en points sur chacun, et ce que pèse un contrat sur un compte prop de 50K.",
                     f"{a} o {b}: valores del tick y del punto lado a lado, el mismo riesgo de {_fmt(RISK, 'es')} en puntos en cada uno, y lo que pesa un contrato en una cuenta prop de 50K.")
        limits = (f'<h2>{t(T("Contract limits at prop firms", "Les limites de contrats des prop firms", "Los límites de contratos de las prop firms"))}</h2>'
                  f'<p>{t(T(f"Firms also cap your size: on a 50K evaluation, the firms Sweep tracks allow {lo} to {hi} full-size contracts depending on the account, and each firm sets how micros count toward that limit. The exact limit of each account is on its firm’s <a href=\"@prop-firms/index.html\">rules page</a>.",
                            f"Les firmes plafonnent aussi ta taille : sur une évaluation de 50K, les firmes que suit Sweep permettent de {lo} à {hi} contrats de taille normale selon le compte, et chaque firme fixe comment les micros comptent dans cette limite. La limite exacte de chaque compte est sur la <a href=\"@prop-firms/index.html\">page de règles</a> de sa firme.",
                            f"Las firmas también limitan tu tamaño: en una evaluación de 50K, las firmas que sigue Sweep permiten de {lo} a {hi} contratos de tamaño normal según la cuenta, y cada firma fija cómo cuentan los micros en ese límite. El límite exacto de cada cuenta está en la <a href=\"@prop-firms/index.html\">página de reglas</a> de su firma."))}</p>'
                  f'<p>{t(T(f"Full specs: {lk(a)} and {lk(b)}. Trading hours: {t(HOURS)} See <a href=\"@futures-market-hours.html\">futures market hours</a> in your time zone.",
                            f"Fiches complètes : {lk(a)} et {lk(b)}. Heures de marché : {t(HOURS)} Voir les <a href=\"@futures-market-hours.html\">heures du marché des futures</a> dans ton fuseau.",
                            f"Fichas completas: {lk(a)} y {lk(b)}. Horario: {t(HOURS)} Mira el <a href=\"@futures-market-hours.html\">horario del mercado de futuros</a> en tu zona horaria."))}</p>')
        tbl = ('<div class="cmp-wrap"><table class="cmp"><thead><tr><th scope="col"><span class="sr">' + t(T("Spec", "Spécification", "Especificación")) + f'</span></th><th scope="col">{lk(a)}</th><th scope="col">{lk(b)}</th></tr></thead><tbody>'
               + "".join(f'<tr><th scope="row">{t(r)}</th><td>{x}</td><td>{y}</td></tr>' for r, x, y in rows) + "</tbody></table></div>"
               + f'<p class="fine" style="margin-top:16px">{t(NOTE)}</p>')
        calc = f'<div class="cta-row" style="margin-top:24px"><a class="btn btn-line" href="{href(lang, "position-size-calculator.html")}?sym={b if micro else a}">{t(T("Position size calculator", "Calculateur de taille de position", "Calculadora de tamaño de posición"))}</a></div>'
        others = (f'<div class="chiprow" style="margin-top:40px"><span class="eyebrow">{t(T("Other comparisons", "Autres comparaisons", "Otras comparaciones"))}</span>'
                  + "".join(f'<a class="chip" href="{href(lang, p)}">{CROSS_NAME(p)}</a>' for p in CROSS_PAGES if p != page_id) + "</div>")
        hero = ui.hero(t, T("Futures contracts", "Contrats à terme", "Futuros"), h1, lead, cta=ui.btn(t(CREATE_FREE), SIGNUP, lg=True, attrs='data-track="signup_contract_pair"'))
        b_ = (ui.sec(ui.head(t, None, T("Side by side", "Côte à côte", "Lado a lado")) + tbl + calc, "t", "specs", width="read")
              + ui.sec(f'<article class="article">{loc(body + limits)}</article>', "n", "compare", width="read")
              + ui.sec(ui.head(t, None, T("Questions", "Questions", "Preguntas")) + ui.qa(t, faqs) + others, "n", "faq", width="read"))
        ld = jsonld({"@context": "https://schema.org", "@graph": [
            {"@type": "Article", "headline": t(title).split(" · ")[0], "inLanguage": lang, "datePublished": "2026-10-27", "publisher": {"@id": f"https://{DOMAIN}/#org"}, "author": {"@type": "Organization", "name": "Sweep"}},
            {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": t(q), "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", t(x))}} for q, x in faqs]}]})
        return (t(title), t(desc), hero + b_ + ui.final(lang, t), ld)
    return page

# « Read next »: each pair page leads to its two sheets and the calculator; each sheet leads to its comparison (SEO brief v2, lot 5)
for _s, _n, _e, _ts, _tv, _pv, *_ in C:
    REL_INFO.setdefault(slug(_s), (T(f"{_s} futures", f"Futures {_s}", f"Futuros {_s}"), T(f"{_fmt(_tv)} a tick, {_fmt(_pv)} a point.", f"{_fmt(_tv, 'fr')} le tick, {_fmt(_pv, 'fr')} le point.", f"{_fmt(_tv, 'es')} por tick, {_fmt(_pv, 'es')} por punto.")))
for _a, _b in PAIRS:
    _micro = next(c for c in C if c[0] == _a)[7] == _b
    REL_INFO[pair_slug(_a, _b)] = (T(f"{_a} vs {_b}", f"{_a} ou {_b}", f"{_a} o {_b}"),
        T("Mini or micro, side by side.", "Mini ou micro, côte à côte.", "Mini o micro, lado a lado.") if _micro else T("Two E-minis, side by side.", "Deux E-minis, côte à côte.", "Dos E-minis, lado a lado."))
    RELATED[pair_slug(_a, _b)] = [slug(_a), slug(_b), "position-size-calculator.html"]
_SHEET_REL = {"NQ": ["nq-vs-mnq.html", "nq-vs-es.html"], "ES": ["es-vs-mes.html", "nq-vs-es.html"], "MNQ": ["nq-vs-mnq.html", "mes-vs-mnq.html"], "MES": ["es-vs-mes.html", "mes-vs-mnq.html"]}
for _a, _b in PAIRS[:5]:
    for _s in (_a, _b): RELATED[slug(_s)] = (_SHEET_REL.get(_s) or [pair_slug(_a, _b), "futures-market-hours.html"]) + ["position-size-calculator.html"]
