"""Home page sections, built with the design system (ui.py, system.css)."""
from core import *
from ui import sec, head, btn, go, split, card, card_media, cards, tiles, frame_d, frame_p, phone_img, qa, final, read_next
import re

L3 = lambda en, fr, es: T(en, fr, es)

def bar(lang, t):
    return (f'<a class="pill rise cohort-pill" href="{href(lang,"100")}"><span class="tag">{t(L3("Founding cohort","Cohorte fondatrice","Cohorte fundadora"))}</span>'
            f'<b><span class="cp-n num">100</span> traders</b><span class="arr" aria-hidden="true">→</span></a>')

def link(lang, t, page, label, anchor=""):
    return go(lang, t, page, label, anchor)

def sec_oneplace(lang, t):
    tools = [("doc", L3("Spreadsheet","Tableur","Hoja de cálculo")), ("shield", L3("Firm dashboard","Dashboard de la firme","Panel de la firma")),
             ("calendar", L3("Notes","Notes","Notas")), ("image", L3("Camera roll","Pellicule","Galería")), ("receipt", L3("Bank app","App bancaire","App del banco"))]
    labels = [L3("Trades & charts","Trades et graphiques","Operaciones y gráficos"), L3("Prop firm rules","Règles des prop firms","Reglas de prop firms"),
              L3("Payouts & expenses","Payouts et dépenses","Payouts y gastos"), L3("Plan & reviews","Plan et revues","Plan y revisiones"), L3("Habits & streaks","Habitudes et streaks","Hábitos y rachas")]
    chips = "".join(f'<li>{ico(I[k])}<span>{t(n)}</span></li>' for k, n in tools)
    lab = "".join(f'<li><span class="ok-dot" aria-hidden="true"></span>{t(n)}</li>' for n in labels)
    viz = (f'<div class="oneplace reveal" aria-hidden="true"><ul class="op-from stagger">{chips}</ul><div class="op-arrow"></div>'
           f'<div class="op-card"><div class="op-brand"><span class="op-mark">{MARK}</span>sweep</div><ul>{lab}</ul></div></div>')
    return split(t, L3("Why Sweep","Pourquoi Sweep","Por qué Sweep"), L3("Stop piecing your trading together.","Arrête de recoller les morceaux.","Deja de armar tu trading a pedazos."),
                 L3("A spreadsheet for trades. Your firm’s dashboard for drawdown. Notes for your plan. Screenshots in your camera roll. Sweep puts it all in one calm place.",
                    "Un tableur pour tes trades. Le dashboard de ta firme pour le drawdown. Des notes pour ton plan. Des captures dans ta pellicule. Sweep réunit tout au même endroit, au calme.",
                    "Una hoja de cálculo para tus operaciones. El panel de tu firma para el drawdown. Notas para tu plan. Capturas en tu galería. Sweep lo reúne todo en un solo lugar, con calma."),
                 None, viz, id_="one-place")

def sec_log(lang, t):
    items = [card(t, L3("Screenshot","Capture","Captura"), L3("One capture, every trade on it.","Une capture, tous ses trades ajoutés.","Una captura, todas sus operaciones."), "image"),
             card(t, L3("Your words","Tes mots","Tus palabras"), L3("“Long 2 NQ at the open, out at target.”","« Long 2 NQ à l’ouverture, sorti à la cible. »","«Largo 2 NQ en la apertura, salida en el objetivo.»"), "chat"),
             card(t, L3("Import","Import","Importar"), L3(f'Bring in your platform’s export, or <a href="{href(lang, "ninjatrader.html")}">sync NinjaTrader 8</a>.', f'L’export de ta plateforme, importé, ou <a href="{href(lang, "ninjatrader.html")}">NinjaTrader 8 synchronisé</a>.', f'Trae la exportación de tu plataforma o <a href="{href(lang, "ninjatrader.html")}">sincroniza NinjaTrader 8</a>.'), "download")]
    shot = frame_d("v6-03-log-by-screenshot-d.webp", t(L3("A trade filled in from a screenshot, sample data","Un trade rempli à partir d’une capture, données d’exemple","Una operación completada desde una captura, datos de ejemplo")),
                   m="v6-03-log-by-screenshot-m.webp", sizes="(max-width: 1067px) 92vw, 1200px", cls="reveal zoom")
    note = f'<p class="cap">{t(L3("Sample data · Real CME charts appear on your trades the day after the session.","Données d’exemple · Les vrais graphiques CME apparaissent sur tes trades le lendemain de la séance.","Datos de ejemplo · Los gráficos reales de CME aparecen en tus operaciones al día siguiente de la sesión."))}</p>'
    return sec(head(t, L3("Log","Saisie","Registro"), L3("Log a trade in seconds.","Un trade ajouté en quelques secondes.","Registra una operación en segundos."),
                    L3("No homework. Drop a screenshot, say it in your own words, or import your platform’s export. Sweep fills in the rest.",
                       "Pas de devoirs. Dépose une capture, raconte-le avec tes mots ou importe l’export de ta plateforme. Sweep fait le reste.",
                       "Sin tareas. Sube una captura, cuéntala con tus palabras o importa la exportación de tu plataforma. Sweep completa el resto."),
                    links=link(lang, t, "how-it-works.html", L3("See how logging works","Voir comment ça marche","Ver cómo funciona")), center=True)
               + cards(items, 3) + f'<div style="margin-top:64px">{shot}{note}</div>', "n", "logging")

def sec_firms(lang, t):
    import pages18
    firms = ", ".join(f'<a href="{href(lang, pages18.page_of(f))}">{f["name"]}</a>' for f in pages18.presets.FIRMS)
    pts = [T(firms + ". Another firm? Enter its rules once.", firms + ". Une autre firme ? Saisis ses règles une fois.", firms + ". ¿Otra firma? Introduce sus reglas una vez."),
           L3("Rules checked every week against each firm’s official pages.","Règles vérifiées chaque semaine sur les pages officielles des firmes.","Reglas verificadas cada semana en las páginas oficiales de cada firma."),
           L3("A rule changes? You see what it means for your account, and you decide.","Une règle change ? Tu vois ce que ça change pour ton compte, et tu décides.","¿Cambia una regla? Ves qué significa para tu cuenta, y tú decides.")]
    more = ('<div class="links">' + link(lang, t, "prop-firm-tracker.html", L3("See prop firm tracking","Voir le suivi des prop firms","Ver el seguimiento de prop firms"))
            + link(lang, t, "prop-firms/index.html", L3("Compare every firm’s rules","Compare les règles de chaque firme","Compara las reglas de cada firma")) + '</div>')
    return split(t, L3("Prop firms","Prop firms","Prop firms"), L3("Your firm’s rules, already loaded.","Les règles de ta firme, déjà chargées.","Las reglas de tu firma, ya cargadas."),
        L3("Pick your firm and account type. Sweep tracks drawdown, consistency and payout conditions for every account you run.",
           "Choisis ta firme et ton type de compte. Sweep suit le drawdown, la consistance et les conditions de payout de chaque compte.",
           "Elige tu firma y tu tipo de cuenta. Sweep sigue el drawdown, la consistencia y las condiciones de payout de cada cuenta."),
        pts, frame_d("v6-08-payout-conditions-d.webp", t(L3("Payout conditions for a prop account, sample data","Conditions de payout d’un compte prop, données d’exemple","Condiciones de payout de una cuenta prop, datos de ejemplo")),
                     m="v6-08-payout-conditions-m.webp", t=t), id_="prop", more=more)

def sec_payouts(lang, t):
    return split(t, L3("Payouts","Payouts","Payouts"), L3("Every account. Every payout. One record.","Chaque compte. Chaque payout. Un seul historique.","Cada cuenta. Cada payout. Un solo historial."),
        L3("Eval fees, resets and activations on one side, payouts on the other. See what prop trading really pays you, and how close each funded account is to its next payout.",
           "D’un côté les frais d’évaluation, les resets et les activations ; de l’autre les payouts. Vois ce que le prop trading te rapporte vraiment, et à quelle distance chaque compte financé est de son prochain payout.",
           "De un lado, tarifas de evaluación, resets y activaciones; del otro, los payouts. Mira cuánto te paga realmente el trading con prop firms y qué tan cerca está cada cuenta fondeada de su próximo payout."),
        [L3("Evaluations, funded and live accounts stay separate, so the P&L you see is the real one.","Évaluations, comptes financés et live restent séparés : le P&L que tu vois est le vrai.","Evaluaciones, cuentas fondeadas y live siempre separadas: el P&L que ves es el real."),
         L3("Simulated and real money are never added together.","Le simulé et l’argent réel ne sont jamais additionnés.","Lo simulado y el dinero real nunca se suman."),
         L3("<b>Lose an account, keep your history.</b>","<b>Tu perds un compte, tu gardes ton historique.</b>","<b>Pierdes una cuenta, conservas tu historial.</b>")],
        frame_d("v6-12-payouts-d.webp", t(L3("Payouts and expenses, sample data","Payouts et dépenses, données d’exemple","Payouts y gastos, datos de ejemplo")), m="v6-12-payouts-m.webp", t=t),
        flip=True, id_="payouts", more=f'<p class="fine" style="margin-top:24px">{t(MONEY_PLAN)}</p>')

def sec_disc(lang, t):
    """A showcase across the page: the day, swept."""
    pts = [L3("Streaks, missions and a weekly boss turn good habits into progress.","Streaks, missions et un boss chaque semaine : tes bonnes habitudes deviennent du progrès.","Rachas, misiones y un jefe semanal convierten los buenos hábitos en progreso."),
           L3("A rough session never blocks your day. It shows up in your discipline score, not as a penalty.","Une séance difficile ne bloque jamais ta journée. Elle compte dans ton score de discipline, pas comme une punition.","Una mala sesión nunca bloquea tu día. Cuenta en tu puntuación de disciplina, no como castigo."),
           L3("Leagues and crews are optional. Your P&L always stays private.","Ligues et crews optionnels. Ton P&L reste toujours privé.","Ligas y crews opcionales. Tu P&L siempre es privado.")]
    points = '<ul class="points stagger">' + "".join(f"<li>{t(x)}</li>" for x in pts) + "</ul>"
    shot = frame_d("v6-22-today-swept-d.webp", t(L3("Today: plan, execution and review done, the day swept, sample data","Aujourd’hui : plan, exécution et revue faits, journée balayée, données d’exemple","Hoy: plan, ejecución y revisión hechos, día barrido, datos de ejemplo")),
                   m="v6-22-today-swept-m.webp", sizes="(max-width: 1067px) 92vw, 1320px", t=t, cls="reveal zoom")
    return sec(head(t, L3("Discipline","Discipline","Disciplina"), L3("Sweep your day.","Balaye ta journée.","Barre tu día."),
                    L3("Three steps every trading day: Plan before the open, Execution during the session, Review after the close. Complete all three and your day is swept.",
                       "Trois étapes chaque jour de trading : le Plan avant l’ouverture, l’Exécution pendant la séance, la Revue après la clôture. Les trois faites, ta journée est balayée.",
                       "Tres pasos cada día de trading: el Plan antes de la apertura, la Ejecución durante la sesión y la Revisión después del cierre. Completa los tres y tu día queda barrido."),
                    links=link(lang, t, "how-it-works.html", L3("See how discipline works","Voir comment fonctionne la discipline","Ver cómo funciona la disciplina"), "#discipline"), center=True)
               + points + shot, "a", "discipline", cls="show", width="wide")

def sec_ai(lang, t):
    L = "fr" if lang == "fr" else ("es" if lang == "es" else "en")
    items = [card_media(t, T("Edge Reveal","Edge Reveal","Edge Reveal"), L3("The setups and hours that pay you most.","Les setups et les heures qui te rapportent le plus.","Los setups y horarios que más te pagan."),
                        phone_img("/img/captures/ecran-edge-reveal.webp", t(L3("Edge Reveal: one truth from your trades","Edge Reveal : une vérité tirée de tes trades","Edge Reveal: una verdad de tus operaciones")), "50% 74%"), crop=True),
             card_media(t, L3("Ask your journal","Demande à ton journal","Pregúntale a tu diario"), L3("“What’s my best time of day on NQ?”","« Quelle est ma meilleure heure sur NQ ? »","«¿Cuál es mi mejor hora en NQ?»"),
                        phone_img(f"/img/mobile-{L}-dark-ask-sweep-786.webp", t(L3("Ask Sweep answers from your trades","Ask Sweep répond à partir de tes trades","Ask Sweep responde con tus operaciones")), "50% 4%"), crop=True),
             card_media(t, L3("Economic calendar","Calendrier économique","Calendario económico"), L3("AI notes before every major release.","Des notes IA avant chaque annonce majeure.","Notas de IA antes de cada dato importante."),
                        phone_img("/img/mobile-en-dark-economic-calendar-786.webp", t(L3("The week’s economic releases","Les annonces économiques de la semaine","Los datos económicos de la semana")), "50% 6%"), crop=True)]
    return sec(head(t, T("Sweep AI","Sweep AI","Sweep AI"), L3("Ask your journal anything.","Pose n’importe quelle question à ton journal.","Pregúntale lo que quieras a tu diario."),
                    L3("Sweep AI reads your trades, plans and reviews, then answers in plain words.","Sweep AI lit tes trades, tes plans et tes revues, puis répond simplement.","Sweep AI lee tus operaciones, planes y revisiones, y responde con palabras simples."),
                    links=link(lang, t, "ai.html", L3("Meet Sweep AI","Découvrir Sweep AI","Conoce Sweep AI")))
               + cards(items, 3), "n", "sweep-ai")

def sec_trust(lang, t):
    items = [("download", L3("Export everything in one click","Export complet en un clic","Exporta todo en un clic"), None), ("archive", L3("Nothing lost when an account closes","Rien de perdu quand un compte ferme","Nada se pierde al cerrar una cuenta"), None),
             ("lock", L3("Secure payments by Stripe","Paiements sécurisés par Stripe","Pagos seguros con Stripe"), None), ("globe", L3("Built in Québec","Conçu au Québec","Hecho en Quebec"), None)]
    return sec(head(t, None, L3("Your data stays yours.","Tes données t’appartiennent.","Tus datos son tuyos."),
                    links=link(lang, t, "security.html", L3("Security and data","Sécurité et données","Seguridad y datos")))
               + tiles(t, items) + f'<p class="fine" style="margin-top:20px">{t(L3("Sweep doesn’t offer financial advice.","Sweep n’offre pas de conseils financiers.","Sweep no ofrece asesoría financiera."))}</p>', "t", "trust")

def sec_pricing(lang, t):
    tiles_ = [("Free", L3("$0","0 $","0 $"), L3("forever","pour toujours","para siempre")), ("Pro", L3("$19","19 $","19 $"), L3("/mo","/mois","/mes")), ("Elite", L3("$39","39 $","39 $"), L3("/mo","/mois","/mes"))]
    tl = "".join(f'<div class="plan-mini{" main" if n == "Pro" else ""}"><b>{n}</b><span class="num">{t(p)} <small>{t(u)}</small></span></div>' for n, p, u in tiles_)
    return sec(head(t, L3("Pricing","Tarifs","Precios"), L3("Start free. Stay free if you like.","Commence gratuitement. Reste gratuit si tu veux.","Empieza gratis. Quédate gratis si quieres."),
                    L3("Every new trader gets 60 days of Pro to try everything. Then keep Free, or upgrade.","Chaque nouveau trader reçoit 60 jours de Pro pour tout essayer. Ensuite, garde Free ou passe à un forfait.","Cada trader nuevo recibe 60 días de Pro para probarlo todo. Después, sigue en Free o mejora tu plan."), center=True)
               + f'<div class="plans-mini stagger">{tl}</div><p class="cap">{t(L3("Annual billing: −30%. Prices before tax.","Facturation annuelle : −30 %. Prix avant taxes.","Facturación anual: −30 %. Precios antes de impuestos."))}</p>'
               + f'<div class="links" style="justify-content:center">{link(lang, t, "pricing.html", L3("Compare plans","Comparer les forfaits","Comparar planes"))}{link(lang, t, "best-trading-journal-for-prop-firms.html", L3("Compare Sweep","Comparer Sweep","Comparar Sweep"))}</div>',
               "n", "pricing")

FAQ5 = [
 (L3("Is Sweep really free?","Sweep est-il vraiment gratuit ?","¿Sweep es realmente gratis?"),
  L3("Yes. The Free plan has no time limit and needs no card. Every new account also gets 60 days of Pro, so you can try everything before deciding.","Oui. Le forfait Free n’a pas de limite de temps et ne demande aucune carte. Chaque nouveau compte reçoit aussi 60 jours de Pro pour tout essayer avant de décider.","Sí. El plan Free no tiene límite de tiempo ni pide tarjeta. Cada cuenta nueva recibe además 60 días de Pro para probarlo todo antes de decidir.")),
 (L3("Which prop firms does Sweep support?","Quelles prop firms Sweep prend-il en charge ?","¿Qué prop firms admite Sweep?"),
  {l: FIRMS_TXT[l] + {"en": ", with each firm’s account types preloaded. ", "fr": ", avec leurs types de comptes préchargés. ", "es": ", con sus tipos de cuenta precargados. "}[l]
      + ({"en": f"Any other firm, like {and_list(other_firms(), 'en').replace(' and ', ' or ')}, can be added with its rules entered by hand. ", "fr": f"Toute autre firme, comme {and_list(other_firms(), 'fr').replace(' et ', ' ou ')}, s’ajoute avec ses règles saisies à la main. ", "es": f"Cualquier otra firma, como {and_list(other_firms(), 'es').replace(' y ', ' o ')}, se añade con sus reglas introducidas a mano. "}[l] if other_firms()
         else {"en": "Any other firm can be added with its rules entered by hand. ", "fr": "Toute autre firme s’ajoute avec ses règles saisies à la main. ", "es": "Cualquier otra firma se añade con sus reglas introducidas a mano. "}[l])
      + {"en": "Rules are checked every week, and you’re notified when something changes for your account.", "fr": "Les règles sont vérifiées chaque semaine, et tu es averti quand quelque chose change pour ton compte.", "es": "Las reglas se verifican cada semana y te avisamos cuando algo cambia para tu cuenta."}[l] for l in LANGS}),
 (L3("How do I add my trades?","Comment j’ajoute mes trades ?","¿Cómo agrego mis operaciones?"),
  L3("On NinjaTrader 8, connect it once with Sweep’s free add-on: your trades arrive on their own. Otherwise, drop a screenshot (a history screenshot adds every trade on it at once), describe the trade in your own words, or import your platform’s export.","Sur NinjaTrader 8, connecte-le une fois avec l’add-on gratuit de Sweep : tes trades arrivent seuls. Sinon, dépose une capture (une capture de l’historique ajoute tous ses trades d’un coup), décris le trade avec tes mots ou importe l’export de ta plateforme.","En NinjaTrader 8, conéctalo una vez con el add-on gratis de Sweep: tus operaciones llegan solas. Si no, sube una captura (una captura del historial agrega todas sus operaciones de una vez), describe la operación con tus palabras o importa la exportación de tu plataforma.")),
 (L3("What happens after the 60 days of Pro?","Que se passe-t-il après les 60 jours de Pro ?","¿Qué pasa después de los 60 días de Pro?"),
  L3("You keep everything you logged. Your account moves to Free unless you choose Pro or Elite.","Tu gardes tout ce que tu as enregistré. Ton compte passe à Free, sauf si tu choisis Pro ou Elite.","Conservas todo lo que registraste. Tu cuenta pasa a Free, salvo que elijas Pro o Elite.")),
 (L3("What is a trading journal, and why use Sweep?","C’est quoi un journal de trading, et pourquoi Sweep ?","¿Qué es un diario de trading y por qué Sweep?"),
  L3("A trading journal records every trade, your plan and your review, so you can see what works. Sweep is a free trading journal built for futures and prop firm traders: it also tracks your firm’s rules and, on Pro and Elite, your payouts and expenses in the same place. To compare it with other journals, read <a href=\"/best-trading-journal-for-prop-firms\">the best trading journal for prop firm traders</a> or <a href=\"/sweep-vs-tradezella\">Sweep vs TradeZella</a>.","Un journal de trading enregistre chaque trade, ton plan et ta revue, pour voir ce qui fonctionne. Sweep est un journal de trading gratuit conçu pour les traders de futures et de prop firms : il suit aussi les règles de ta firme et, avec Pro et Elite, tes payouts et tes dépenses, au même endroit. Pour le comparer aux autres journaux, lis <a href=\"/fr/best-trading-journal-for-prop-firms\">le meilleur journal de trading pour les prop firms</a> ou <a href=\"/fr/sweep-vs-tradezella\">Sweep vs TradeZella</a>.","Un diario de trading registra cada operación, tu plan y tu revisión, para ver qué funciona. Sweep es un diario de trading gratis creado para traders de futuros y prop firms: además sigue las reglas de tu firma y, con Pro y Elite, tus payouts y tus gastos, en el mismo lugar. Para compararlo con otros diarios, lee <a href=\"/es/best-trading-journal-for-prop-firms\">el mejor diario de trading para prop firms</a> o <a href=\"/es/sweep-vs-tradezella\">Sweep vs TradeZella</a>.")),
]
def sec_faq(lang, t):
    return sec(head(t, None, L3("Questions","Questions","Preguntas")) + qa(t, FAQ5, link(lang, t, "faq.html", L3("All questions","Toutes les questions","Todas las preguntas"))), "n", "faq", width="read")
def faq_ld(t):
    return {"@type":"FAQPage","mainEntity":[{"@type":"Question","name":t(q),"acceptedAnswer":{"@type":"Answer","text":re.sub(r"<[^>]+>","",t(a))}} for q,a in FAQ5]}

REASSURE = L3("Free forever · 60 days of Pro included · No card","Gratuit pour toujours · 60 jours de Pro inclus · Sans carte","Gratis para siempre · 60 días de Pro incluidos · Sin tarjeta")
def sec_next(lang, t):
    return read_next(lang, t, ["features.html", "prop-firm-tracker.html", "tools.html"])
def sec_final(lang, t):
    return final(lang, t)
