from core import *
import re

L3 = lambda en, fr, es: T(en, fr, es)

def bar(lang, t):
    return (f'<a class="pill rise cohort-pill" href="{href(lang,"100")}"><span class="tag">{t(L3("Founding cohort","Cohorte fondatrice","Cohorte fundadora"))}</span>'
            f'<b><span class="cp-n num">100</span> traders</b><span class="arr" aria-hidden="true">→</span></a>')

def head(t, kick, h2, line):
    return f'<div class="head"><span class="kick">{t(kick)}</span><h2>{t(h2)}</h2><p class="lead">{t(line)}</p></div>'

def link(lang, t, page, label, anchor=""):
    return f'<a class="tlink" href="{href(lang,page)}{anchor}">{t(label)} <span aria-hidden="true">→</span></a>'

def sec_oneplace(lang, t):
    tools = [("doc", L3("Spreadsheet","Tableur","Hoja de cálculo")), ("shield", L3("Firm dashboard","Dashboard de la firme","Panel de la firma")),
             ("calendar", L3("Notes","Notes","Notas")), ("image", L3("Camera roll","Pellicule","Galería")), ("receipt", L3("Bank app","App bancaire","App del banco"))]
    labels = [L3("Trades & charts","Trades et graphiques","Operaciones y gráficos"), L3("Prop firm rules","Règles des prop firms","Reglas de prop firms"),
              L3("Payouts & expenses","Payouts et dépenses","Payouts y gastos"), L3("Plan & reviews","Plan et revues","Plan y revisiones"), L3("Habits & streaks","Habitudes et streaks","Hábitos y rachas")]
    chips = "".join(f'<li style="--i:{i}">{ico(I[k])}<span>{t(n)}</span></li>' for i,(k,n) in enumerate(tools))
    lab = "".join(f'<li style="--i:{i}"><span class="ok-dot" aria-hidden="true"></span>{t(n)}</li>' for i,n in enumerate(labels))
    viz = (f'<div class="oneplace reveal" aria-hidden="true"><ul class="op-from">{chips}</ul><div class="op-arrow"></div>'
           f'<div class="op-card"><div class="op-brand"><span class="op-mark">{MARK}</span>sweep</div><ul>{lab}</ul></div></div>')
    return (f'<section class="rule" id="one-place"><div class="wrap">'
            + head(t, L3("Why Sweep","Pourquoi Sweep","Por qué Sweep"), L3("Stop piecing your trading together.","Arrête de recoller les morceaux.","Deja de armar tu trading a pedazos."),
                   L3("A spreadsheet for trades. Your firm’s dashboard for drawdown. Notes for your plan. Screenshots in your camera roll. Sweep puts it all in one calm place.",
                      "Un tableur pour tes trades. Le dashboard de ta firme pour le drawdown. Des notes pour ton plan. Des captures dans ta pellicule. Sweep réunit tout au même endroit, au calme.",
                      "Una hoja de cálculo para tus operaciones. El panel de tu firma para el drawdown. Notas para tu plan. Capturas en tu galería. Sweep lo reúne todo en un solo lugar, con calma."))
            + viz + '</div></section>')

def cards3(t, items):
    return '<div class="grid g3 stagger cards3x">' + "".join(f'<div>{ico(I[k])}<h3>{t(h)}</h3><p>{t(p)}</p></div>' for k,h,p in items) + '</div>'

def sec_log(lang, t):
    items = [("image", L3("Screenshot","Capture","Captura"), L3("One capture, every trade on it.","Une capture, tous ses trades ajoutés.","Una captura, todas sus operaciones.")),
             ("chat", L3("Your words","Tes mots","Tus palabras"), L3("“Long 2 NQ at the open, out at target.”","« Long 2 NQ à l’ouverture, sorti à la cible. »","«Largo 2 NQ en la apertura, salida en el objetivo.»")),
             ("download", L3("Import","Import","Importar"), L3("Bring in your platform’s export.","L’export de ta plateforme, importé.","Trae la exportación de tu plataforma."))]
    return (f'<section class="rule" id="logging"><div class="wrap">'
            + head(t, L3("Log","Saisie","Registro"), L3("Log a trade in seconds.","Un trade ajouté en quelques secondes.","Registra una operación en segundos."),
                   L3("No homework. Drop a screenshot, say it in your own words, or import your platform’s export. Sweep fills in the rest.",
                      "Pas de devoirs. Dépose une capture, raconte-le avec tes mots ou importe l’export de ta plateforme. Sweep fait le reste.",
                      "Sin tareas. Sube una captura, cuéntala con tus palabras o importa la exportación de tu plataforma. Sweep completa el resto."))
            + cards3(t, items)
            + f'<div class="log-shot reveal">{slot("v6-03-log-by-screenshot-d.webp","desktop",t(L3("A trade filled in from a screenshot, sample data","Un trade rempli à partir d’une capture, données d’exemple","Una operación completada desde una captura, datos de ejemplo")),t,cap=False)}'
            + f'<p class="shot-note">{t(L3("Sample data · Real CME charts appear on your trades the day after the session.","Données d’exemple · Les vrais graphiques CME apparaissent sur tes trades le lendemain de la séance.","Datos de ejemplo · Los gráficos reales de CME aparecen en tus operaciones al día siguiente de la sesión."))}</p></div>'
            + f'<p class="center-note">{link(lang,t,"how-it-works.html",L3("See how logging works","Voir comment ça marche","Ver cómo funciona"))}</p></div></section>')


def sec_firms(lang, t):
    import pages18
    firms = ", ".join(f'<a href="{href(lang, pages18.page_of(f))}">{f["name"]}</a>' for f in pages18.presets.FIRMS)
    pts = [T(firms + ". Another firm? Enter its rules once.", firms + ". Une autre firme ? Saisis ses règles une fois.", firms + ". ¿Otra firma? Introduce sus reglas una vez."),
           L3("Rules checked every week against each firm’s official pages.","Règles vérifiées chaque semaine sur les pages officielles des firmes.","Reglas verificadas cada semana en las páginas oficiales de cada firma."),
           L3("A rule changes? You see what it means for your account, and you decide.","Une règle change ? Tu vois ce que ça change pour ton compte, et tu décides.","¿Cambia una regla? Ves qué significa para tu cuenta, y tú decides.")]
    return split(t, L3("Prop firms","Prop firms","Prop firms"), L3("Your firm’s rules, already loaded.","Les règles de ta firme, déjà chargées.","Las reglas de tu firma, ya cargadas."),
        L3("Pick your firm and account type. Sweep tracks drawdown, consistency and payout conditions for every account you run.",
           "Choisis ta firme et ton type de compte. Sweep suit le drawdown, la consistance et les conditions de payout de chaque compte.",
           "Elige tu firma y tu tipo de cuenta. Sweep sigue el drawdown, la consistencia y las condiciones de payout de cada cuenta."),
        pts, slot("v6-08-payout-conditions-d.webp","desktop",t(L3("Payout conditions for a prop account, sample data","Conditions de payout d’un compte prop, données d’exemple","Condiciones de payout de una cuenta prop, datos de ejemplo")),t),
        id_="prop", more=link(lang,t,"prop-traders.html",L3("See prop firm tracking","Voir le suivi des prop firms","Ver el seguimiento de prop firms")))

def sec_payouts(lang, t):
    return split(t, L3("Payouts","Payouts","Payouts"), L3("Every account. Every payout. One record.","Chaque compte. Chaque payout. Un seul historique.","Cada cuenta. Cada payout. Un solo historial."),
        L3("Eval fees, resets and activations on one side, payouts on the other. See what prop trading really pays you, and how close each funded account is to its next payout.",
           "D’un côté les frais d’évaluation, les resets et les activations ; de l’autre les payouts. Vois ce que le prop trading te rapporte vraiment, et à quelle distance chaque compte financé est de son prochain payout.",
           "De un lado, tarifas de evaluación, resets y activaciones; del otro, los payouts. Mira cuánto te paga realmente el trading con prop firms y qué tan cerca está cada cuenta fondeada de su próximo payout."),
        [L3("Evaluations, funded and live accounts stay separate, so the P&L you see is the real one.","Évaluations, comptes financés et live restent séparés : le P&L que tu vois est le vrai.","Evaluaciones, cuentas fondeadas y live siempre separadas: el P&L que ves es el real."),
         L3("Simulated and real money are never added together.","Le simulé et l’argent réel ne sont jamais additionnés.","Lo simulado y el dinero real nunca se suman."),
         L3("<b>Lose an account, keep your history.</b>","<b>Tu perds un compte, tu gardes ton historique.</b>","<b>Pierdes una cuenta, conservas tu historial.</b>")],
        slot("v6-12-payouts-d.webp","desktop",t(L3("Payouts and expenses, sample data","Payouts et dépenses, données d’exemple","Payouts y gastos, datos de ejemplo")),t), flip=True, id_="payouts")

def sec_disc(lang, t):
    pts = [L3("Streaks, missions and a weekly boss turn good habits into progress.","Streaks, missions et un boss chaque semaine : tes bonnes habitudes deviennent du progrès.","Rachas, misiones y un jefe semanal convierten los buenos hábitos en progreso."),
           L3("A rough session never blocks your day. It shows up in your discipline score, not as a penalty.","Une séance difficile ne bloque jamais ta journée. Elle compte dans ton score de discipline, pas comme une punition.","Una mala sesión nunca bloquea tu día. Cuenta en tu puntuación de disciplina, no como castigo."),
           L3("Leagues and crews are optional. Your P&L always stays private.","Ligues et crews optionnels. Ton P&L reste toujours privé.","Ligas y crews opcionales. Tu P&L siempre es privado.")]
    return split(t, L3("Discipline","Discipline","Disciplina"), L3("Sweep your day.","Balaye ta journée.","Barre tu día."),
        L3("Three steps every trading day: Plan before the open, Execution during the session, Review after the close. Complete all three and your day is swept.",
           "Trois étapes chaque jour de trading : le Plan avant l’ouverture, l’Exécution pendant la séance, la Revue après la clôture. Les trois faites, ta journée est balayée.",
           "Tres pasos cada día de trading: el Plan antes de la apertura, la Ejecución durante la sesión y la Revisión después del cierre. Completa los tres y tu día queda barrido."),
        pts, slot("v6-video-today-phone.mp4","phone",t(L3("Today on a phone: rings, days, releases","Aujourd’hui sur téléphone : anneaux, jours, annonces","Hoy en el teléfono: anillos, días, datos")),t,video=True,poster="v6-poster-today-phone.webp"),
        id_="discipline", more=link(lang,t,"how-it-works.html",L3("See how discipline works","Voir comment fonctionne la discipline","Ver cómo funciona la disciplina"),"#discipline"))

def sec_ai(lang, t):
    items = [("spark", T("Edge Reveal","Edge Reveal","Edge Reveal"), L3("The setups and hours that pay you most.","Les setups et les heures qui te rapportent le plus.","Los setups y horarios que más te pagan.")),
             ("chat", L3("Ask your journal","Demande à ton journal","Pregúntale a tu diario"), L3("“What’s my best time of day on NQ?”","« Quelle est ma meilleure heure sur NQ ? »","«¿Cuál es mi mejor hora en NQ?»")),
             ("calendar", L3("Economic calendar","Calendrier économique","Calendario económico"), L3("AI notes before every major release.","Des notes IA avant chaque annonce majeure.","Notas de IA antes de cada dato importante."))]
    return (f'<section class="rule ai-sec" id="sweep-ai"><div class="wrap">'
            + head(t, T("Sweep AI","Sweep AI","Sweep AI"), L3("Ask your journal anything.","Pose n’importe quelle question à ton journal.","Pregúntale lo que quieras a tu diario."),
                   L3("Sweep AI reads your trades, plans and reviews, then answers in plain words.","Sweep AI lit tes trades, tes plans et tes revues, puis répond simplement.","Sweep AI lee tus operaciones, planes y revisiones, y responde con palabras simples."))
            + cards3(t, items) + f'<p class="center-note">{link(lang,t,"ai.html",L3("Meet Sweep AI","Découvrir Sweep AI","Conoce Sweep AI"))}</p></div></section>')

def sec_trust(lang, t):
    items = [("download", L3("Export everything in one click","Export complet en un clic","Exporta todo en un clic")), ("archive", L3("Nothing lost when an account closes","Rien de perdu quand un compte ferme","Nada se pierde al cerrar una cuenta")),
             ("lock", L3("Secure payments by Stripe","Paiements sécurisés par Stripe","Pagos seguros con Stripe")), ("globe", L3("Built in Québec","Conçu au Québec","Hecho en Quebec"))]
    return (f'<section class="rule trustline-sec"><div class="wrap"><h2 class="trust-h">{t(L3("Your data stays yours.","Tes données t’appartiennent.","Tus datos son tuyos."))}</h2>'
            f'<ul class="trustrow stagger">{"".join(f"<li>{ico(I[k])}<span>{t(l)}</span></li>" for k,l in items)}</ul>'
            f'<p class="fine" style="text-align:center;margin:18px auto 0">{t(L3("Sweep doesn’t offer financial advice.","Sweep n’offre pas de conseils financiers.","Sweep no ofrece asesoría financiera."))} <a href="{href(lang,"security.html")}">{t(L3("Security and data","Sécurité et données","Seguridad y datos"))}</a></p></div></section>')

def sec_pricing(lang, t):
    tiles = [("Free", L3("$0, forever","0 $, pour toujours","0 $, para siempre")), ("Pro", L3("$19/mo","19 $/mois","19 $/mes")), ("Elite", L3("$39/mo","39 $/mois","39 $/mes"))]
    tl = "".join(f'<div class="ptile2{" main" if n=="Pro" else ""}"><b>{n}</b><span class="num">{t(v)}</span></div>' for n,v in tiles)
    return (f'<section class="rule" id="pricing"><div class="wrap" style="text-align:center">'
            f'<div class="head" style="margin:0 auto"><span class="kick">{t(L3("Pricing","Tarifs","Precios"))}</span><h2>{t(L3("Start free. Stay free if you like.","Commence gratuitement. Reste gratuit si tu veux.","Empieza gratis. Quédate gratis si quieres."))}</h2>'
            f'<p class="lead" style="margin-left:auto;margin-right:auto">{t(L3("Every new trader gets 60 days of Pro to try everything. Then keep Free, or upgrade.","Chaque nouveau trader reçoit 60 jours de Pro pour tout essayer. Ensuite, garde Free ou passe à un forfait.","Cada trader nuevo recibe 60 días de Pro para probarlo todo. Después, sigue en Free o mejora tu plan."))}</p></div>'
            f'<div class="ptiles2 stagger">{tl}</div><p class="fine" style="margin-top:12px">{t(L3("Annual billing: −30%. Prices before tax.","Facturation annuelle : −30 %. Prix avant taxes.","Facturación anual: −30 %. Precios antes de impuestos."))}</p>'
            f'<p class="center-note">{link(lang,t,"pricing.html",L3("Compare plans","Comparer les forfaits","Comparar planes"))} · {link(lang,t,"best-trading-journal-for-prop-firms.html",L3("Compare Sweep","Comparer Sweep","Comparar Sweep"))}</p></div></section>')

FAQ5 = [
 (L3("Is Sweep really free?","Sweep est-il vraiment gratuit ?","¿Sweep es realmente gratis?"),
  L3("Yes. The Free plan has no time limit and needs no card. Every new account also gets 60 days of Pro, so you can try everything before deciding.","Oui. Le forfait Free n’a pas de limite de temps et ne demande aucune carte. Chaque nouveau compte reçoit aussi 60 jours de Pro pour tout essayer avant de décider.","Sí. El plan Free no tiene límite de tiempo ni pide tarjeta. Cada cuenta nueva recibe además 60 días de Pro para probarlo todo antes de decidir.")),
 (L3("Which prop firms does Sweep support?","Quelles prop firms Sweep prend-il en charge ?","¿Qué prop firms admite Sweep?"),
  L3("Apex, Topstep, Lucid, Take Profit Trader and MyFundedFutures, with each firm’s account types preloaded. Any other firm, like Tradeify or Alpha Futures, can be added with its rules entered by hand. Rules are checked every week, and you’re notified when something changes for your account.","Apex, Topstep, Lucid, Take Profit Trader et MyFundedFutures, avec leurs types de comptes préchargés. Toute autre firme, comme Tradeify ou Alpha Futures, s’ajoute avec ses règles saisies à la main. Les règles sont vérifiées chaque semaine, et tu es averti quand quelque chose change pour ton compte.","Apex, Topstep, Lucid, Take Profit Trader y MyFundedFutures, con sus tipos de cuenta precargados. Cualquier otra firma, como Tradeify o Alpha Futures, se añade con sus reglas introducidas a mano. Las reglas se verifican cada semana y te avisamos cuando algo cambia para tu cuenta.")),
 (L3("How do I add my trades?","Comment j’ajoute mes trades ?","¿Cómo agrego mis operaciones?"),
  L3("Drop a screenshot (a history screenshot adds every trade on it at once), describe the trade in your own words, or import your platform’s export. Automatic live sync with Rithmic and Tradovate is in development.","Dépose une capture (une capture de l’historique ajoute tous ses trades d’un coup), décris le trade avec tes mots ou importe l’export de ta plateforme. La synchronisation automatique avec Rithmic et Tradovate est en développement.","Sube una captura (una captura del historial agrega todas sus operaciones de una vez), describe la operación con tus palabras o importa la exportación de tu plataforma. La sincronización automática con Rithmic y Tradovate está en desarrollo.")),
 (L3("What happens after the 60 days of Pro?","Que se passe-t-il après les 60 jours de Pro ?","¿Qué pasa después de los 60 días de Pro?"),
  L3("You keep everything you logged. Your account moves to Free unless you choose Pro or Elite.","Tu gardes tout ce que tu as enregistré. Ton compte passe à Free, sauf si tu choisis Pro ou Elite.","Conservas todo lo que registraste. Tu cuenta pasa a Free, salvo que elijas Pro o Elite.")),
 (L3("What is a trading journal, and why use Sweep?","C’est quoi un journal de trading, et pourquoi Sweep ?","¿Qué es un diario de trading y por qué Sweep?"),
  L3("A trading journal records every trade, your plan and your review, so you can see what works. Sweep is a free trading journal built for futures and prop firm traders: it also tracks your firm’s rules, payouts and expenses in the same place. To compare it with other journals, read <a href=\"/best-trading-journal-for-prop-firms\">the best trading journal for prop firm traders</a> or <a href=\"/sweep-vs-tradezella\">Sweep vs TradeZella</a>.","Un journal de trading enregistre chaque trade, ton plan et ta revue, pour voir ce qui fonctionne. Sweep est un journal de trading gratuit conçu pour les traders de futures et de prop firms : il suit aussi les règles de ta firme, tes payouts et tes dépenses, au même endroit. Pour le comparer aux autres journaux, lis <a href=\"/fr/best-trading-journal-for-prop-firms\">le meilleur journal de trading pour les prop firms</a> ou <a href=\"/fr/sweep-vs-tradezella\">Sweep vs TradeZella</a>.","Un diario de trading registra cada operación, tu plan y tu revisión, para ver qué funciona. Sweep es un diario de trading gratis creado para traders de futuros y prop firms: además sigue las reglas de tu firma, tus payouts y tus gastos, en el mismo lugar. Para compararlo con otros diarios, lee <a href=\"/es/best-trading-journal-for-prop-firms\">el mejor diario de trading para prop firms</a> o <a href=\"/es/sweep-vs-tradezella\">Sweep vs TradeZella</a>.")),
]
def sec_faq(lang, t):
    return (f'<section class="rule" id="faq"><div class="wrap narrow"><div class="head"><h2>{t(L3("Questions","Questions","Preguntas"))}</h2></div>'
            + "".join(faq_item(t,q,a) for q,a in FAQ5) + f'<p style="margin-top:20px">{link(lang,t,"faq.html",L3("All questions","Toutes les questions","Todas las preguntas"))}</p></div></section>')
def faq_ld(t):
    return {"@type":"FAQPage","mainEntity":[{"@type":"Question","name":t(q),"acceptedAnswer":{"@type":"Answer","text":re.sub(r"<[^>]+>","",t(a))}} for q,a in FAQ5]}

REASSURE = L3("Free forever · 60 days of Pro included · No card","Gratuit pour toujours · 60 jours de Pro inclus · Sans carte","Gratis para siempre · 60 días de Pro incluidos · Sin tarjeta")
def sec_final(lang, t):
    return (f'<section class="final rule"><div class="wrap" style="text-align:center"><h2>{t(L3("Your edge, finally in one place.","Ton edge, enfin au même endroit.","Tu edge, por fin en un solo lugar."))}</h2>'
            f'<div class="cta-row" style="justify-content:center;margin-top:26px"><a class="btn btn-primary btn-lg" href="{SIGNUP}">{t(L3("Start free","Commencer gratuitement","Empieza gratis"))}</a></div>'
            f'<p class="fine" style="margin-top:14px">{t(L3("Free forever · 60 days of Pro · No card","Gratuit pour toujours · 60 jours de Pro · Sans carte","Gratis para siempre · 60 días de Pro · Sin tarjeta"))}</p></div></section>')
