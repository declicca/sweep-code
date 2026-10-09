from core import *
import json, os, datetime

_EV = json.load(open(os.path.join(os.path.dirname(__file__), "data", "econ-us-2026-2027.json"), encoding="utf-8"))["events"]
TODAY_ISO = datetime.date.today().isoformat()

# key, slug, event names in the data, title (short), what it is, why futures traders watch it
REL = [
 ("cpi","cpi-release-dates.html",["CPI m/m"],"CPI",
  T("The Consumer Price Index measures the change in prices paid by consumers. It’s the most watched U.S. inflation number.","L’indice des prix à la consommation mesure la variation des prix payés par les consommateurs. C’est le chiffre d’inflation américain le plus suivi.","El Índice de Precios al Consumo mide la variación de los precios que pagan los consumidores. Es el dato de inflación más seguido de EE. UU."),
  "BLS"),
 ("nfp","nfp-release-dates.html",["Nonfarm Payrolls"],"Nonfarm Payrolls (NFP)",
  T("The monthly jobs report: jobs added outside agriculture, released with the unemployment rate and average hourly earnings.","Le rapport mensuel sur l’emploi : emplois créés hors agriculture, publié avec le taux de chômage et le salaire horaire moyen.","El informe mensual de empleo: empleos creados fuera de la agricultura, publicado con la tasa de paro y el salario por hora."),
  "BLS"),
 ("fomc","fomc-meeting-dates.html",["FOMC Rate Decision"],"FOMC",
  T("The Federal Reserve’s rate decision, at 2:00 p.m. New York time, followed by the press conference at 2:30 p.m.","La décision de taux de la Réserve fédérale, à 14 h heure de New York, suivie de la conférence de presse à 14 h 30.","La decisión de tipos de la Reserva Federal, a las 14:00 hora de Nueva York, seguida de la rueda de prensa a las 14:30."),
  "Federal Reserve"),
 ("ppi","ppi-release-dates.html",["PPI m/m"],"PPI",
  T("The Producer Price Index measures prices received by producers, an early look at inflation upstream.","L’indice des prix à la production mesure les prix reçus par les producteurs, un premier aperçu de l’inflation en amont.","El Índice de Precios al Productor mide los precios que reciben los productores, una primera mirada a la inflación."),
  "BLS"),
 ("pce","pce-release-dates.html",["PCE Price Index m/m"],"PCE",
  T("The Personal Consumption Expenditures price index, the inflation measure the Federal Reserve targets.","L’indice des prix des dépenses de consommation personnelle, la mesure d’inflation que vise la Réserve fédérale.","El índice de precios del gasto en consumo personal, la medida de inflación que sigue la Reserva Federal."),
  "BEA"),
 ("retail","retail-sales-release-dates.html",["Retail Sales m/m"],"Retail Sales",
  T("Monthly change in U.S. retail sales, a direct read on consumer spending.","Variation mensuelle des ventes au détail aux États-Unis, une lecture directe des dépenses des consommateurs.","Variación mensual de las ventas minoristas en EE. UU., una lectura directa del consumo."),
  "Census Bureau"),
 ("gdp","gdp-release-dates.html",["GDP q/q (Advance)","GDP q/q (Second Estimate)","GDP q/q (Third Estimate)"],"GDP",
  T("Quarterly growth of the U.S. economy, published in three estimates: advance, second and third.","La croissance trimestrielle de l’économie américaine, publiée en trois estimations : avancée, deuxième et troisième.","El crecimiento trimestral de la economía de EE. UU., publicado en tres estimaciones: avance, segunda y tercera."),
  "BEA"),
 ("ism","ism-manufacturing-release-dates.html",["ISM Manufacturing PMI"],"ISM Manufacturing PMI",
  T("A monthly survey of U.S. purchasing managers in manufacturing. Above 50 means expansion, below 50 contraction.","Une enquête mensuelle auprès des directeurs d’achat de l’industrie américaine. Au-dessus de 50, expansion ; en dessous, contraction.","Una encuesta mensual a los directores de compras de la industria de EE. UU. Por encima de 50, expansión; por debajo, contracción."),
  "ISM"),
]
STATUS = {"official": T("Official","Officielle","Oficial"), "official-tentative": T("Tentative","Provisoire","Provisional"), "estimated": T("Estimated","Estimée","Estimada")}

def _date(t, iso):
    d = datetime.date.fromisoformat(iso)
    L = t(T("en","fr","es"))
    mf = {"en":["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"],"fr":["janv.","févr.","mars","avr.","mai","juin","juil.","août","sept.","oct.","nov.","déc."],"es":["ene.","feb.","mar.","abr.","may.","jun.","jul.","ago.","sept.","oct.","nov.","dic."]}[L]
    wd = {"en":["Mon","Tue","Wed","Thu","Fri","Sat","Sun"],"fr":["lun.","mar.","mer.","jeu.","ven.","sam.","dim."],"es":["lun.","mar.","mié.","jue.","vie.","sáb.","dom."]}[L][d.weekday()]
    return f"{wd} {mf[d.month-1]} {d.day}, {d.year}" if L == "en" else f"{wd} {d.day} {mf[d.month-1]} {d.year}"

def make_release(key):
    k, sl, names, title, what, src = next(r for r in REL if r[0] == key)
    evs = sorted([e for e in _EV if e["event"] in names], key=lambda e: (e["date"], e["time"]))
    def page(lang, t):
        nxt = next((e for e in evs if e["date"] >= TODAY_ISO), None)
        hero = page_hero(t, T(f"{title} release dates 2026–2027.", f"Dates de publication {title} 2026–2027.", f"Fechas de publicación {title} 2026–2027."), what, T("Economic calendar","Calendrier économique","Calendario económico"))
        nx = ""
        if nxt:
            nx = f'<div class="nextrel"><span class="kick">{t(T("Next release","Prochaine publication","Próxima publicación"))}</span><b class="num">{_date(t,nxt["date"])} · {nxt["time"]} ET</b><span class="plan-tag">{t(STATUS[nxt["status"]])}</span></div>'
        rows = ""
        for e in evs:
            past = e["date"] < TODAY_ISO
            lbl = e["event"].replace("GDP q/q ","GDP ") if k == "gdp" else ""
            rows += f'<tr class="{"past" if past else ""}"><td class="num">{_date(t,e["date"])}</td><td class="num">{e["time"]} ET</td>{f"<td>{lbl}</td>" if k=="gdp" else ""}<td><span class="st st-{e["status"]}">{t(STATUS[e["status"]])}</span></td></tr>'
        head = f'<tr><th>{t(T("Date","Date","Fecha"))}</th><th>{t(T("Time","Heure","Hora"))}</th>{"<th>"+t(T("Estimate","Estimation","Estimación"))+"</th>" if k=="gdp" else ""}<th>{t(T("Status","Statut","Estado"))}</th></tr>'
        tbl = f'<div class="cmp-wrap"><table class="cmp reltbl"><thead>{head}</thead><tbody>{rows}</tbody></table></div>'
        note = T(f"Times in New York time (ET). Source: {src}. “Estimated” dates are projected from the usual release pattern: check the official calendar closer to the date. Not financial advice.",
                 f"Heures de New York (ET). Source : {src}. Les dates « estimées » sont projetées selon le calendrier habituel : vérifie le calendrier officiel à l’approche. Ce n’est pas un conseil financier.",
                 f"Horas de Nueva York (ET). Fuente: {src}. Las fechas «estimadas» se proyectan según el patrón habitual: verifica el calendario oficial cuando se acerque. No es asesoramiento financiero.")
        why = T(f"Releases like {title} can move NQ, ES, yields and the dollar within seconds. Sweep marks every high-impact release on your calendar, warns you in the trade ticket when one is close, and shows how you trade around them.",
                f"Des publications comme {title} peuvent faire bouger NQ, ES, les taux et le dollar en quelques secondes. Sweep marque chaque annonce importante dans ton calendrier, t’avertit dans le ticket quand une approche, et montre comment tu trades autour.",
                f"Datos como {title} pueden mover NQ, ES, los rendimientos y el dólar en segundos. Sweep marca cada dato importante en tu calendario, te avisa en el ticket cuando se acerca uno y muestra cómo operas a su alrededor.")
        others = "".join(f'<a href="{href(lang,r[1])}">{r[3]}</a>' for r in REL if r[0] != k)
        b = (f'<section style="padding-top:8px"><div class="wrap narrow">{nx}{tbl}<p class="fine">{t(note)}</p></div></section>'
             f'<section class="rule"><div class="wrap narrow"><div class="head"><h2>{t(T("Trade the news with a plan.","Trade les nouvelles avec un plan.","Opera las noticias con un plan."))}</h2><p class="lead">{t(why)}</p></div>'
             f'<div class="cta-row"><a class="btn btn-line" href="{href(lang,"economic-calendar.html")}">{t(T("The economic calendar in Sweep","Le calendrier économique dans Sweep","El calendario económico en Sweep"))}</a></div>'
             f'<p class="firm-others" style="margin-top:28px"><span>{t(T("Other releases","Autres publications","Otros datos"))}</span>{others}</p></div></section>')
        ld = jsonld({"@context":"https://schema.org","@type":"ItemList","name":t(T(f"{title} release dates",f"Dates {title}",f"Fechas {title}")),
                     "itemListElement":[{"@type":"ListItem","position":i+1,"name":f'{title} {e["date"]} {e["time"]} ET'} for i,e in enumerate(evs) if e["date"] >= TODAY_ISO][:12]})
        return (t(T(f"{title} release dates 2026 and 2027 (ET) · Sweep",f"Dates {title} 2026 et 2027 (heure de New York) · Sweep",f"Fechas {title} 2026 y 2027 (hora de Nueva York) · Sweep")),
                t(T(f"Every {title} release date and time for 2026 and 2027 in New York time, with the next release and what it means for futures traders.",
                    f"Toutes les dates et heures de publication {title} pour 2026 et 2027, en heure de New York, avec la prochaine publication.",
                    f"Todas las fechas y horas de publicación {title} para 2026 y 2027, en hora de Nueva York, con el próximo dato.")),
                hero + b + final_cta(lang, t), ld)
    return page

def page_release_hub(lang, t):
    hero = page_hero(t, T("U.S. economic release dates.","Dates des annonces économiques américaines.","Fechas de los datos económicos de EE. UU."),
        T("The high-impact releases futures traders plan around, with every date for 2026 and 2027.","Les annonces importantes autour desquelles les traders de futures planifient, avec toutes les dates 2026 et 2027.","Los datos importantes que los traders de futuros tienen en cuenta, con todas las fechas de 2026 y 2027."), T("Economic calendar","Calendrier économique","Calendario económico"))
    cards = ""
    for k, sl, names, title, what, src in REL:
        nxt = next((e for e in sorted([e for e in _EV if e["event"] in names], key=lambda e: e["date"]) if e["date"] >= TODAY_ISO), None)
        nx = f'<span class="go num">{t(T("Next","Prochaine","Próxima"))} : {_date(t,nxt["date"])} · {nxt["time"]} ET</span>' if nxt else ""
        cards += f'<a class="tool-card" href="{href(lang,sl)}"><h2>{title}</h2><p>{t(what)}</p>{nx}</a>'
    b = f'<section style="padding-top:8px"><div class="wrap"><div class="tool-grid">{cards}</div></div></section>'
    return (t(T("U.S. economic release dates 2026–2027: CPI, NFP, FOMC… · Sweep","Dates des annonces économiques 2026–2027 : CPI, NFP, FOMC… · Sweep","Fechas de datos económicos 2026–2027: CPI, NFP, FOMC… · Sweep")),
            t(T("Release dates and times for CPI, NFP, FOMC, PPI, PCE, retail sales, GDP and ISM in 2026 and 2027, in New York time.","Dates et heures de CPI, NFP, FOMC, PPI, PCE, ventes au détail, PIB et ISM en 2026 et 2027, en heure de New York.","Fechas y horas de CPI, NFP, FOMC, PPI, PCE, ventas minoristas, PIB e ISM en 2026 y 2027, en hora de Nueva York.")),
            hero + b + final_cta(lang, t), "")

# ------------------------------------------------------------------ glossary
G = [
 ("tick", "Tick", T("The smallest price move a futures contract can make. On NQ, one tick is 0.25 points.","Le plus petit mouvement de prix possible d’un contrat à terme. Sur NQ, un tick vaut 0,25 point.","El menor movimiento de precio posible de un contrato de futuros. En NQ, un tick son 0,25 puntos.")),
 ("tick-value", T("Tick value","Valeur du tick","Valor del tick"), T("What one tick is worth per contract, in dollars: $5 on NQ, $12.50 on ES.","Ce que vaut un tick par contrat, en dollars : 5 $ sur NQ, 12,50 $ sur ES.","Lo que vale un tick por contrato, en dólares: 5 $ en NQ, 12,50 $ en ES.")),
 ("point-value", T("Point value","Valeur du point","Valor del punto"), T("What one full point is worth per contract: $20 on NQ, $50 on ES.","Ce que vaut un point complet par contrat : 20 $ sur NQ, 50 $ sur ES.","Lo que vale un punto completo por contrato: 20 $ en NQ, 50 $ en ES.")),
 ("micro", T("Micro contract","Contrat micro","Contrato micro"), T("A contract one tenth the size of its E-mini: MNQ for NQ, MES for ES.","Un contrat dix fois plus petit que son E-mini : MNQ pour NQ, MES pour ES.","Un contrato diez veces menor que su E-mini: MNQ para NQ, MES para ES.")),
 ("r-multiple", T("R multiple","R multiple","Múltiplo R"), T("A trade’s result divided by the risk you took. Risk $200 and make $400: +2R.","Le résultat d’un trade divisé par le risque pris. Tu risques 200 $ et gagnes 400 $ : +2R.","El resultado de una operación dividido por el riesgo asumido. Arriesgas 200 $ y ganas 400 $: +2R.")),
 ("expectancy", T("Expectancy","Espérance","Esperanza"), T("What a trade earns on average: win rate × average win − loss rate × average loss.","Ce que rapporte un trade en moyenne : taux de réussite × gain moyen − taux de perte × perte moyenne.","Lo que gana una operación de media: tasa de acierto × ganancia media − tasa de pérdida × pérdida media.")),
 ("profit-factor", "Profit factor", T("Gross profits divided by gross losses. Above 1, the strategy made money over the period.","Profits bruts divisés par les pertes brutes. Au-dessus de 1, la stratégie a gagné sur la période.","Beneficios brutos divididos por pérdidas brutas. Por encima de 1, la estrategia ganó en el periodo.")),
 ("drawdown", "Drawdown", T("The drop from a peak balance. In a prop account, the maximum drawdown is the loss limit that ends the account.","La baisse depuis un sommet du solde. Dans un compte prop, le drawdown maximum est la limite de perte qui met fin au compte.","La caída desde un máximo del saldo. En una cuenta prop, el drawdown máximo es el límite de pérdida que cierra la cuenta.")),
 ("trailing-drawdown", T("Trailing drawdown","Drawdown suiveur","Drawdown dinámico"), T("A drawdown limit that rises with your highest balance and never moves down. Often it stops at the starting balance.","Une limite de drawdown qui monte avec ton plus haut solde et ne redescend jamais. Souvent, elle s’arrête au solde de départ.","Un límite de drawdown que sube con tu saldo más alto y nunca baja. A menudo se detiene en el saldo inicial.")),
 ("eod-drawdown", T("End-of-day drawdown","Drawdown de fin de journée","Drawdown de fin de día"), T("A trailing drawdown that only moves with your closing balance, not with open profit during the day.","Un drawdown suiveur qui ne bouge qu’avec ton solde de clôture, pas avec le profit latent de la journée.","Un drawdown dinámico que solo se mueve con tu saldo de cierre, no con el beneficio abierto del día.")),
 ("daily-loss", T("Daily loss limit","Perte quotidienne max","Pérdida diaria máxima"), T("The most you can lose in one day before the account is locked for the day, or fails.","Le maximum que tu peux perdre en une journée avant que le compte soit bloqué pour la journée, ou échoue.","Lo máximo que puedes perder en un día antes de que la cuenta se bloquee ese día o falle.")),
 ("consistency", T("Consistency rule","Règle de consistance","Regla de consistencia"), T("A limit on how much of your total profit can come from a single day.","Une limite sur la part de ton profit total qui peut venir d’une seule journée.","Un límite a la parte del beneficio total que puede venir de un solo día.")),
 ("evaluation", T("Evaluation","Évaluation","Evaluación"), T("The test phase of a prop firm: reach a profit target without breaking the rules.","La phase de test d’une prop firm : atteindre un objectif de profit sans enfreindre les règles.","La fase de prueba de una prop firm: alcanzar un objetivo de beneficio sin romper las reglas.")),
 ("funded", T("Funded account","Compte financé","Cuenta fondeada"), T("The account you get after passing an evaluation, with its own rules and payouts.","Le compte obtenu après une évaluation réussie, avec ses propres règles et payouts.","La cuenta que obtienes al superar una evaluación, con sus propias reglas y payouts.")),
 ("payout", "Payout", T("A withdrawal of profits from a funded account, subject to the firm’s conditions.","Un retrait de profits d’un compte financé, soumis aux conditions de la firme.","Una retirada de beneficios de una cuenta fondeada, sujeta a las condiciones de la firma.")),
 ("safety-net", T("Safety net (cushion)","Coussin (safety net)","Colchón (safety net)"), T("A balance you must keep above the starting balance before some firms allow a payout.","Un solde à garder au-dessus du solde de départ avant que certaines firmes autorisent un payout.","Un saldo que debes mantener por encima del saldo inicial antes de que algunas firmas permitan un payout.")),
 ("reset", "Reset", T("Paying to restart an evaluation after breaking a rule.","Payer pour recommencer une évaluation après avoir enfreint une règle.","Pagar para reiniciar una evaluación tras romper una regla.")),
 ("slippage", T("Slippage","Glissement","Deslizamiento"), T("The difference between the price you expected and the price you got.","L’écart entre le prix attendu et le prix obtenu.","La diferencia entre el precio esperado y el obtenido.")),
 ("mae-mfe", "MAE / MFE", T("Maximum adverse and maximum favorable excursion: how far a trade went against you, and in your favor, before it closed.","Excursion maximale défavorable et favorable : jusqu’où un trade est allé contre toi, et pour toi, avant la sortie.","Excursión máxima adversa y favorable: cuánto fue una operación en tu contra, y a tu favor, antes de cerrarse.")),
 ("rth", T("RTH and ETH","RTH et ETH","RTH y ETH"), T("Regular trading hours (9:30 a.m. to 4:00 p.m. New York time for index futures) and extended hours (the rest of the Globex session).","Heures régulières (9 h 30 à 16 h, heure de New York, pour les indices) et heures étendues (le reste de la session Globex).","Horario regular (9:30 a 16:00 hora de Nueva York para índices) y horario extendido (el resto de la sesión Globex).")),
 ("globex", "Globex", T("CME’s electronic trading platform, open nearly 23 hours a day from Sunday evening to Friday.","La plateforme électronique du CME, ouverte près de 23 heures par jour du dimanche soir au vendredi.","La plataforma electrónica de CME, abierta casi 23 horas al día de domingo por la tarde a viernes.")),
 ("rollover", "Rollover", T("Moving from the expiring contract month to the next one, usually about a week before expiration for index futures.","Passer du mois de contrat qui expire au suivant, en général environ une semaine avant l’échéance pour les indices.","Pasar del mes de contrato que vence al siguiente, normalmente una semana antes del vencimiento en los índices.")),
 ("copy-trading", "Copy trading", T("Placing the same trade on several accounts at once. In Sweep, a copied trade shows once with the total.","Placer le même trade sur plusieurs comptes en même temps. Dans Sweep, un trade copié s’affiche une seule fois avec le total.","Colocar la misma operación en varias cuentas a la vez. En Sweep, una operación copiada se muestra una vez con el total.")),
 ("journal", T("Trading journal","Journal de trading","Diario de trading"), T("A record of every trade with its reason, its result and what you learned, used to find your edge and fix your mistakes.","Un registre de chaque trade avec sa raison, son résultat et ce que tu en retiens, pour trouver ton edge et corriger tes erreurs.","Un registro de cada operación con su motivo, su resultado y lo aprendido, para encontrar tu ventaja y corregir errores.")),
]
def page_glossary(lang, t):
    hero = page_hero(t, T("Futures and prop trading glossary.","Lexique du trading de futures et prop.","Glosario de trading de futuros y prop."),
        T("The terms you meet every day, in one sentence each.","Les termes que tu croises chaque jour, en une phrase chacun.","Los términos que encuentras cada día, en una frase cada uno."), T("Glossary","Lexique","Glosario"))
    idx = "".join(f'<a href="#{k}">{t(n) if isinstance(n,dict) else n}</a>' for k,n,_ in G)
    items = "".join(f'<div class="term" id="{k}"><dt>{t(n) if isinstance(n,dict) else n}</dt><dd>{t(d)}</dd></div>' for k,n,d in G)
    links = f'<p class="firm-others" style="margin-top:32px"><span>{t(T("Free tools","Outils gratuits","Herramientas gratuitas"))}</span><a href="{href(lang,"position-size-calculator.html")}">{t(T("Position size","Taille de position","Tamaño de posición"))}</a><a href="{href(lang,"trailing-drawdown-calculator.html")}">{t(T("Trailing drawdown","Drawdown suiveur","Drawdown dinámico"))}</a><a href="{href(lang,"consistency-rule-calculator.html")}">{t(T("Consistency","Consistance","Consistencia"))}</a><a href="{href(lang,"futures-contracts.html")}">{t(T("Contract specs","Fiches contrats","Fichas de contratos"))}</a></p>'
    b = f'<section style="padding-top:8px"><div class="wrap narrow"><nav class="gl-idx">{idx}</nav><dl class="glossary">{items}</dl>{links}</div></section>'
    ld = jsonld({"@context":"https://schema.org","@type":"DefinedTermSet","name":t(T("Futures and prop trading glossary","Lexique du trading de futures et prop","Glosario de trading de futuros y prop")),
                 "hasDefinedTerm":[{"@type":"DefinedTerm","name":(t(n) if isinstance(n,dict) else n),"description":t(d),"url":f"https://{DOMAIN}{href(lang,'glossary.html')}#{k}"} for k,n,d in G]})
    return (t(T("Futures and prop firm trading glossary · Sweep","Lexique du trading de futures et prop firms · Sweep","Glosario de trading de futuros y prop firms · Sweep")),
            t(T("Tick value, R multiple, trailing drawdown, consistency rule, payout, slippage, RTH and more, explained in one sentence each.","Valeur du tick, R multiple, drawdown suiveur, règle de consistance, payout, glissement, RTH et plus, expliqués en une phrase.","Valor del tick, múltiplo R, drawdown dinámico, regla de consistencia, payout, deslizamiento, RTH y más, explicados en una frase.")),
            hero + b + final_cta(lang, t), ld)

# ------------------------------------------------------------------ market hours
def page_hours(lang, t):
    hero = page_hero(t, T("Futures market hours, in your time zone.","Heures des marchés futures, dans ton fuseau horaire.","Horario de los mercados de futuros, en tu zona horaria."),
        T("CME Globex sessions converted to your local time, with what’s open right now.","Les sessions CME Globex converties à ton heure locale, avec ce qui est ouvert en ce moment.","Las sesiones de CME Globex convertidas a tu hora local, con lo que está abierto ahora."), T("Market hours","Heures de marché","Horario"))
    S = [("globex",T("Globex session","Session Globex","Sesión Globex"),"18:00","17:00"),("asia",T("Asia","Asie","Asia"),"18:00","03:00"),("london",T("London","Londres","Londres"),"03:00","08:00"),
         ("ny",T("New York (RTH)","New York (RTH)","Nueva York (RTH)"),"09:30","16:00"),("break",T("Daily break","Pause quotidienne","Pausa diaria"),"17:00","18:00")]
    rows = "".join(f'<tr data-s="{k}" data-a="{a}" data-b="{b_}"><th>{t(n)}</th><td class="num">{a} – {b_} ET</td><td class="num loc">—</td></tr>' for k,n,a,b_ in S)
    clock = f'''<div class="clock"><div><span class="kick">{t(T("New York","New York","Nueva York"))}</span><b class="num" id="hk-ny">--:--</b></div><div><span class="kick">{t(T("Your time","Ton heure","Tu hora"))}</span><b class="num" id="hk-me">--:--</b><span id="hk-tz" class="muted"></span></div><div><span class="kick">{t(T("Right now","En ce moment","Ahora mismo"))}</span><b id="hk-st">—</b></div></div>'''
    tbl = f'<div class="cmp-wrap"><table class="cmp"><thead><tr><th>{t(T("Session","Session","Sesión"))}</th><th>{t(T("New York time","Heure de New York","Hora de Nueva York"))}</th><th>{t(T("Your time","Ton heure","Tu hora"))}</th></tr></thead><tbody>{rows}</tbody></table></div>'
    st = {"closed":t(T("Market closed (weekend)","Marché fermé (week-end)","Mercado cerrado (fin de semana)")),"break":t(T("Daily break","Pause quotidienne","Pausa diaria")),"rth":t(T("Open · New York session (RTH)","Ouvert · session de New York (RTH)","Abierto · sesión de Nueva York (RTH)")),"london":t(T("Open · London session","Ouvert · session de Londres","Abierto · sesión de Londres")),"asia":t(T("Open · Asia session","Ouvert · session asiatique","Abierto · sesión asiática")),"open":t(T("Open · Globex","Ouvert · Globex","Abierto · Globex"))}
    js = f'''<script>(function(){{var L={json.dumps(st)},$=function(i){{return document.getElementById(i)}};
function nyParts(d){{var f=new Intl.DateTimeFormat('en-US',{{timeZone:'America/New_York',hour12:false,weekday:'short',hour:'2-digit',minute:'2-digit'}}).formatToParts(d),o={{}};f.forEach(function(p){{o[p.type]=p.value}});return o;}}
function toLocal(hm){{var now=new Date(),p=nyParts(now),nyMin=(+p.hour%24)*60+(+p.minute),locMin=now.getHours()*60+now.getMinutes(),diff=locMin-nyMin;var h=+hm.slice(0,2),m=+hm.slice(3);var x=((h*60+m+diff)%1440+1440)%1440;return new Date(2000,0,1,Math.floor(x/60),x%60).toLocaleTimeString(document.documentElement.lang,{{hour:'2-digit',minute:'2-digit'}});}}
function tick(){{var now=new Date(),p=nyParts(now),h=(+p.hour)%24,m=+p.minute,t=h*60+m,wd=p.weekday;
$('hk-ny').textContent=String(h).padStart(2,'0')+':'+String(m).padStart(2,'0');$('hk-me').textContent=now.toLocaleTimeString(document.documentElement.lang,{{hour:'2-digit',minute:'2-digit'}});
try{{$('hk-tz').textContent=Intl.DateTimeFormat().resolvedOptions().timeZone}}catch(e){{}}
var s;if(wd==='Sat'||(wd==='Sun'&&t<1080)||(wd==='Fri'&&t>=1020))s='closed';else if(t>=1020&&t<1080)s='break';else if(t>=570&&t<960)s='rth';else if(t>=180&&t<480)s='london';else if(t>=1080||t<180)s='asia';else s='open';
$('hk-st').textContent=L[s];$('hk-st').className=s==='closed'||s==='break'?'st-out':'st-ok';
document.querySelectorAll('tr[data-s]').forEach(function(r){{r.querySelector('.loc').textContent=toLocal(r.dataset.a)+' – '+toLocal(r.dataset.b)}});}}
tick();setInterval(tick,30000);}})();</script>'''
    note = T("Hours for CME Globex equity index, energy, metals and FX futures. Holiday hours differ: check the CME Group holiday calendar. Session names are conventions.",
             "Heures CME Globex pour les futures sur indices, énergie, métaux et devises. Les jours fériés ont des heures différentes : vérifie le calendrier des jours fériés du CME Group. Les noms des sessions sont des conventions.",
             "Horario de CME Globex para futuros de índices, energía, metales y divisas. Los festivos tienen otro horario: consulta el calendario de festivos de CME Group. Los nombres de las sesiones son convenciones.")
    b = f'<section style="padding-top:8px"><div class="wrap narrow">{clock}{tbl}<p class="fine">{t(note)}</p></div></section>' + js
    return (t(T("Futures market hours in your time zone (CME Globex) · Sweep","Heures des marchés futures dans ton fuseau (CME Globex) · Sweep","Horario de futuros en tu zona horaria (CME Globex) · Sweep")),
            t(T("CME Globex futures hours converted to your local time: Asia, London and New York sessions, daily break, and whether the market is open now.","Les heures CME Globex converties à ton heure locale : sessions Asie, Londres et New York, pause quotidienne, et si le marché est ouvert maintenant.","El horario de CME Globex en tu hora local: sesiones de Asia, Londres y Nueva York, pausa diaria y si el mercado está abierto ahora.")),
            hero + b + final_cta(lang, t), "")

# ------------------------------------------------------------------ press kit
def page_press(lang, t):
    hero = page_hero(t, T("Press kit.","Kit presse.","Kit de prensa."), T("Everything you need to write about Sweep or feature it in a video.","Tout ce qu’il faut pour parler de Sweep ou le montrer en vidéo.","Todo lo necesario para hablar de Sweep o mostrarlo en un vídeo."), T("Press","Presse","Prensa"))
    boiler = T("Sweep is a trading journal for futures prop firm traders. It keeps your platform’s real numbers, follows your firm’s real rules from evaluation to funded to live, logs a trade from a screenshot in seconds, and builds a daily routine that rewards discipline, never profit. Sweep is made by Sweep Inc. in Laval, Quebec, and is available in English, French and Spanish at makeitsweep.com.",
               "Sweep est un journal de trading pour les traders de prop firms de futures. Il garde les vrais chiffres de ta plateforme, suit les vraies règles de ta firme de l’évaluation au financé puis au live, ajoute un trade à partir d’une capture en quelques secondes, et bâtit une routine quotidienne qui récompense la discipline, jamais le profit. Sweep est conçu par Sweep Inc. à Laval, au Québec, et offert en français, en anglais et en espagnol sur makeitsweep.com.",
               "Sweep es un diario de trading para traders de prop firms de futuros. Mantiene los números reales de tu plataforma, sigue las reglas reales de tu firma de la evaluación a la cuenta fondeada y live, registra una operación desde una captura en segundos y crea una rutina diaria que premia la disciplina, nunca el beneficio. Sweep lo hace Sweep Inc. en Laval, Quebec, y está disponible en inglés, francés y español en makeitsweep.com.")
    files = [("sweep-logo-horizontal-white.svg",T("Logo, white (SVG)","Logo blanc (SVG)","Logo blanco (SVG)")),("sweep-logo-horizontal-ink.svg",T("Logo, dark (SVG)","Logo foncé (SVG)","Logo oscuro (SVG)")),
             ("sweep-logo-horizontal-white@2x.png",T("Logo, white (PNG)","Logo blanc (PNG)","Logo blanco (PNG)")),("sweep-mark-white-512.png",T("Mark, white (PNG)","Symbole blanc (PNG)","Símbolo blanco (PNG)")),
             ("sweep-mark-ink-512.png",T("Mark, dark (PNG)","Symbole foncé (PNG)","Símbolo oscuro (PNG)")),("sweep-press-kit.zip",T("Everything (ZIP)","Tout le kit (ZIP)","Todo (ZIP)"))]
    fl = "".join(f'<a class="tool-mini" href="/press/{f}" download>{ico(I["download"])}<span>{t(l)}</span></a>' for f,l in files)
    colors = [("#0B0B0C","Ink"),("#F2F2F3","Text"),("#4C8DFF","Gain · action"),("#D4A24C","Loss · alert")]
    cl = "".join(f'<div class="sw-c"><i style="background:{c}"></i><b class="num">{c}</b><span>{n}</span></div>' for c,n in colors)
    shots = "".join(slot(n,"desktop",t(T("Sweep screen, demo data","Écran de Sweep, données de démonstration","Pantalla de Sweep, datos de demostración")),t,cap=False) for n in ("v6-01-today-d.webp","v6-08-payout-conditions-d.webp","v6-07-stats-d.webp"))
    b = (f'<section style="padding-top:8px"><div class="wrap narrow"><div class="head"><h2>{t(T("About Sweep","À propos de Sweep","Sobre Sweep"))}</h2></div><p class="lead">{t(boiler)}</p>'
         f'<p class="meta">{t(T("Contact","Contact","Contacto"))} : <a href="mailto:{EMAIL}">{EMAIL}</a></p></div></section>'
         f'<section class="rule"><div class="wrap"><div class="head"><h2>{t(T("Logo and files","Logo et fichiers","Logo y archivos"))}</h2><p class="lead">{t(T("Always lowercase “sweep” in the wordmark. Don’t stretch, recolor or add effects to the logo; the blue wick stays blue.","Le mot-symbole s’écrit toujours en minuscules : « sweep ». N’étire pas le logo, ne change pas ses couleurs et n’y ajoute pas d’effet ; la mèche bleue reste bleue.","El logotipo siempre en minúsculas: «sweep». No estires el logo, no cambies sus colores ni añadas efectos; la mecha azul sigue siendo azul."))}</p></div>'
         f'<div class="tool-row">{fl}</div><div class="swatches">{cl}</div></div></section>'
         f'<section class="rule"><div class="wrap"><div class="head"><h2>{t(T("Screenshots","Captures","Capturas"))}</h2><p class="lead">{t(T("Real app screens with demo data. Free to use when writing about Sweep.","De vrais écrans de l’app avec des données de démonstration. Libres d’utilisation pour parler de Sweep.","Pantallas reales de la app con datos de demostración. De uso libre para hablar de Sweep."))}</p></div><div class="press-shots">{shots}</div></div></section>')
    return (t(T("Sweep press kit: logo, screenshots and description","Kit presse de Sweep : logo, captures et description","Kit de prensa de Sweep: logo, capturas y descripción")),
            t(T("Download the Sweep logo, brand colors and app screenshots, and read the official description of Sweep.","Télécharge le logo de Sweep, ses couleurs et des captures de l’app, et lis la description officielle de Sweep.","Descarga el logo de Sweep, sus colores y capturas de la app, y lee la descripción oficial de Sweep.")),
            hero + b + final_cta(lang, t), "")
