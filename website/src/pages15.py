from core import *

IDENTITY = T("Sweep is a free trading journal built for futures and prop firm traders.",
             "Sweep est un journal de trading gratuit conçu pour les traders de futures et de prop firms.",
             "Sweep es un diario de trading gratuito creado para traders de futuros y de prop firms.")

def sec_realpnl(lang, t):
    return split(t, T("Real P&L","P&L réel","P&L real"), T("Your evaluation P&L isn’t your real P&L.","Ton P&L d’évaluation n’est pas ton vrai P&L.","Tu P&L de evaluación no es tu P&L real."),
        T("Passing evaluations feels like progress. But between evaluation fees, resets and accounts that never pay out, many traders don’t know whether prop trading is actually making them money. Sweep separates your evaluation, funded and live accounts, puts income and expenses side by side, and shows you the number that matters.",
          "Réussir des évaluations donne l’impression d’avancer. Mais entre les frais d’évaluation, les resets et les comptes qui ne paient jamais, beaucoup de traders ne savent pas si le trading prop leur rapporte vraiment. Sweep sépare tes comptes d’évaluation, financés et live, met tes revenus et tes dépenses côte à côte, et te montre le chiffre qui compte.",
          "Superar evaluaciones parece un avance. Pero entre cuotas de evaluación, reinicios y cuentas que nunca pagan, muchos traders no saben si el trading prop les deja dinero de verdad. Sweep separa tus cuentas de evaluación, fondeadas y live, pone ingresos y gastos lado a lado y te muestra la cifra que importa."),
        [T("<b>Payouts received</b> against evaluations, resets and activations","<b>Payouts reçus</b> face aux évaluations, resets et activations","<b>Payouts recibidos</b> frente a evaluaciones, reinicios y activaciones"),
         T("<b>Net after fees</b> by firm and by account","<b>Net après frais</b> par firme et par compte","<b>Neto tras cuotas</b> por firma y por cuenta")],
        slot("v6-12-payouts-d.webp","desktop",t(T("Payouts and expenses with net after fees, sample data","Payouts et dépenses avec le net après frais, données d’exemple","Payouts y gastos con el neto tras cuotas, datos de ejemplo")),t),
        id_="real-pnl", more=f'<div class="cta-row"><a class="btn btn-line" href="{href(lang,"features.html")}#numbers">{t(T("How Sweep counts your P&L","Comment Sweep calcule ton P&L","Cómo calcula Sweep tu P&L"))}</a></div>')

SIX = [("shield","prop-traders.html","",T("Prop firm tracker","Suivi des prop firms","Seguimiento de prop firms"),T("Every account, every firm, rules preloaded and checked every week.","Chaque compte, chaque firme, règles préremplies et vérifiées chaque semaine.","Cada cuenta, cada firma, reglas precargadas y revisadas cada semana.")),
       ("download","prop-traders.html","#payouts",T("Payout tracker","Suivi des payouts","Seguimiento de payouts"),T("See how close each funded account is to its next payout.","Vois à quel point chaque compte financé est proche de son prochain payout.","Mira cuánto le falta a cada cuenta fondeada para su próximo payout.")),
       ("net","features.html","#numbers",T("Real P&L","P&L réel","P&L real"),T("Evaluation, funded and live, with income and expenses.","Évaluation, financé et live, avec revenus et dépenses.","Evaluación, fondeada y live, con ingresos y gastos.")),
       ("receipt","features.html","#payouts",T("Expense tracker","Suivi des dépenses","Seguimiento de gastos"),T("Fees, resets and activations against your payouts.","Frais, resets et activations face à tes payouts.","Cuotas, reinicios y activaciones frente a tus payouts.")),
       ("target2","how-it-works.html","#discipline",T("Discipline streaks","Streaks de discipline","Rachas de disciplina"),T("Daily missions and streaks you can actually show off.","Missions quotidiennes et streaks que tu peux vraiment montrer.","Misiones diarias y rachas que de verdad puedes mostrar.")),
       ("spark","ai.html","",T("Sweep AI","Sweep AI","Sweep AI"),T("Session reviews and an economic calendar with AI notes.","Revues de séance et calendrier économique avec notes IA.","Revisiones de sesión y calendario económico con notas de IA."))]

def sec_six(lang, t):
    cards = "".join(f'<a href="{href(lang,pg)}{anc}">{ico(I[ic])}<h3>{t(h)}</h3><p>{t(d)}</p></a>' for ic,pg,anc,h,d in SIX)
    return (f'<section class="rule" id="everything"><div class="wrap"><div class="head"><span class="kick">{t(T("Features","Fonctionnalités","Funciones"))}</span>'
            f'<h2>{t(T("Everything a prop trader needs, in one journal.","Tout ce qu’il faut à un trader prop, dans un seul journal.","Todo lo que necesita un trader prop, en un solo diario."))}</h2></div>'
            f'<div class="grid g3 stagger">{cards}</div></div></section>')

def sec_nytime(lang, t):
    return split(t, T("Session days","Journées de séance","Días de sesión"), T("A trading day that runs on New York time.","Une journée de trading à l’heure de New York.","Un día de trading con la hora de Nueva York."),
        T("Your Sweep day ends at 5 p.m. and the new one starts at 6 p.m. New York time, just like the futures session. News, pre-market and post-market notes, and new trades all roll over automatically.",
          "Ta journée Sweep se termine à 17 h et la suivante commence à 18 h, heure de New York, comme la séance des futures. Annonces, notes de pré-marché et de post-marché, et nouveaux trades basculent automatiquement.",
          "Tu día en Sweep termina a las 17:00 y el siguiente empieza a las 18:00, hora de Nueva York, como la sesión de futuros. Noticias, notas de premercado y postmercado y nuevas operaciones pasan solas al día siguiente."),
        [T("Overnight trades land on the right session day","Les trades de nuit arrivent sur la bonne journée de séance","Las operaciones nocturnas caen en el día de sesión correcto"),
         T("High-impact U.S. releases marked on your calendar","Les annonces américaines importantes marquées dans ton calendrier","Los datos importantes de EE. UU. marcados en tu calendario")],
        slot("v6-11-calendar-d.webp","desktop",t(T("Monthly calendar with trades and releases, sample data","Calendrier du mois avec trades et annonces, données d’exemple","Calendario del mes con operaciones y datos, datos de ejemplo")),t),
        flip=True, id_="session-days", more=f'<div class="cta-row"><a class="btn btn-line" href="{href(lang,"futures-market-hours.html")}">{t(T("Futures market hours","Heures des marchés futures","Horario de los futuros"))}</a></div>')

def sec_compare(lang, t):
    return (f'<section class="rule" id="compare"><div class="wrap narrow"><div class="head"><span class="kick">{t(T("Compare","Comparer","Comparar"))}</span>'
            f'<h2>{t(T("How Sweep compares.","Comment Sweep se compare.","Cómo se compara Sweep."))}</h2>'
            f'<p class="lead">{t(T("Sweep is built for prop firm traders first: a free-forever plan, weekly-verified firm rules, payout tracking and a P&L that separates evaluations from funded and live accounts. Need automatic broker import, trade replay or backtesting today? Other journals may suit you better, and we say so.","Sweep est conçu d’abord pour les traders de prop firms : un forfait gratuit pour toujours, des règles de firmes vérifiées chaque semaine, le suivi des payouts et un P&L qui sépare évaluations, comptes financés et live. Tu as besoin aujourd’hui d’un import automatique, d’un replay de trades ou de backtesting ? D’autres journaux te conviendront peut-être mieux, et on te le dit.","Sweep está hecho primero para traders de prop firms: un plan gratis para siempre, reglas de firmas revisadas cada semana, seguimiento de payouts y un P&L que separa evaluaciones, cuentas fondeadas y live. ¿Necesitas hoy importación automática, replay de operaciones o backtesting? Otros diarios quizá te convengan más, y te lo decimos."))}</p></div>'
            f'<div class="cta-row"><a class="btn btn-line" href="{href(lang,"how-to-choose-a-trading-journal.html")}">{t(T("How to choose a trading journal","Bien choisir son journal de trading","Cómo elegir un diario de trading"))}</a></div></div></section>')

def sec_data(lang, t):
    return (f'<section class="rule" id="your-data"><div class="wrap narrow" style="text-align:center"><div class="head" style="margin:0 auto"><span class="kick">{t(T("Your data","Tes données","Tus datos"))}</span>'
            f'<h2>{t(T("Your data stays yours.","Tes données restent à toi.","Tus datos siguen siendo tuyos."))}</h2>'
            f'<p class="lead" style="margin-left:auto;margin-right:auto">{t(T("Lose a prop account, keep your history. Export everything in one click, anytime.","Tu perds un compte prop, tu gardes ton historique. Exporte tout en un clic, à tout moment.","Pierdes una cuenta prop, conservas tu historial. Exporta todo en un clic, cuando quieras."))}</p></div>'
            f'<div class="cta-row" style="justify-content:center"><a class="btn btn-line" href="{href(lang,"security.html")}">{t(T("Security and data","Sécurité et données","Seguridad y datos"))}</a></div></div></section>')

HOME_FAQ = [
 (T("Is Sweep really free?","Sweep est-il vraiment gratuit ?","¿Sweep es realmente gratis?"),
  T("Yes. Sweep has a Free plan with no time limit and no credit card required. Every new account also gets 60 days of Pro to try every feature. After that, you can stay on Free or upgrade to Pro or Elite.","Oui. Sweep a un forfait Free sans limite de temps et sans carte de crédit. Chaque nouveau compte reçoit aussi 60 jours de Pro pour tout essayer. Ensuite, tu restes sur Free ou tu passes à Pro ou Elite.","Sí. Sweep tiene un plan Free sin límite de tiempo y sin tarjeta. Cada cuenta nueva recibe además 60 días de Pro para probarlo todo. Después, sigues en Free o pasas a Pro o Elite.")),
 (T("Does Sweep work with Topstep, Apex and Lucid?","Sweep fonctionne-t-il avec Topstep, Apex et Lucid ?","¿Sweep funciona con Topstep, Apex y Lucid?"),
  T("Yes. Sweep has preloaded rules for the main futures prop firms. Choose your firm and account type, and Sweep tracks your drawdown, consistency and payout conditions. Rules are checked against each firm’s official pages every week.","Oui. Sweep a des règles préremplies pour les principales prop firms de futures. Choisis ta firme et ton type de compte, et Sweep suit ton drawdown, ta consistance et tes conditions de payout. Les règles sont vérifiées chaque semaine sur les pages officielles des firmes.","Sí. Sweep tiene reglas precargadas para las principales prop firms de futuros. Elige tu firma y tu tipo de cuenta, y Sweep sigue tu drawdown, tu consistencia y tus condiciones de payout. Las reglas se revisan cada semana en las páginas oficiales de las firmas.")),
 (T("Can I import my trades automatically?","Puis-je importer mes trades automatiquement ?","¿Puedo importar mis operaciones automáticamente?"),
  T("Not yet. Today you add a trade from a screenshot of your platform, which Sweep AI reads, or by hand. Automatic sync with Rithmic and Tradovate is in development; we’ll announce it on our changelog as soon as it’s live.","Pas encore. Aujourd’hui, tu ajoutes un trade avec une capture de ta plateforme, que Sweep AI lit, ou à la main. La synchronisation automatique avec Rithmic et Tradovate est en développement ; on l’annoncera dans les nouveautés dès qu’elle sera disponible.","Todavía no. Hoy añades una operación con una captura de tu plataforma, que Sweep AI lee, o a mano. La sincronización automática con Rithmic y Tradovate está en desarrollo; la anunciaremos en las novedades en cuanto esté disponible.")),
 (T("How is Sweep different from TradeZella?","En quoi Sweep diffère-t-il de TradeZella ?","¿En qué se diferencia Sweep de TradeZella?"),
  T("Sweep is built for prop firm traders first: a free-forever plan, weekly-verified firm rules, payout tracking and a P&L that separates evaluations from funded and live accounts. TradeZella offers automatic import, trade replay and backtesting, which Sweep doesn’t have yet.","Sweep est conçu d’abord pour les traders de prop firms : un forfait gratuit pour toujours, des règles de firmes vérifiées chaque semaine, le suivi des payouts et un P&L qui sépare évaluations, comptes financés et live. TradeZella offre l’import automatique, le replay de trades et le backtesting, que Sweep n’a pas encore.","Sweep está hecho primero para traders de prop firms: un plan gratis para siempre, reglas de firmas revisadas cada semana, seguimiento de payouts y un P&L que separa evaluaciones, cuentas fondeadas y live. TradeZella ofrece importación automática, replay de operaciones y backtesting, que Sweep aún no tiene.")),
 (T("Is my data safe if I lose a prop account?","Mes données sont-elles en sécurité si je perds un compte prop ?","¿Mis datos están seguros si pierdo una cuenta prop?"),
  T("Yes. Your journal belongs to you, not to the firm. Closing or failing an account never deletes your history, and you can export everything in one click.","Oui. Ton journal t’appartient, pas à la firme. Fermer ou échouer un compte ne supprime jamais ton historique, et tu peux tout exporter en un clic.","Sí. Tu diario es tuyo, no de la firma. Cerrar o fallar una cuenta nunca borra tu historial, y puedes exportarlo todo en un clic.")),
 (T("Is Sweep available in French and Spanish?","Sweep est-il offert en français et en espagnol ?","¿Sweep está disponible en francés y español?"),
  T("Yes. Sweep is available in English, French and Spanish, and you can switch anytime.","Oui. Sweep est offert en anglais, en français et en espagnol, et tu peux changer de langue à tout moment.","Sí. Sweep está disponible en inglés, francés y español, y puedes cambiar de idioma cuando quieras.")),
 (T("Is there a mobile app?","Y a-t-il une app mobile ?","¿Hay una app móvil?"),
  T("Sweep is designed mobile-first and works in your phone’s browser today; you can add it to your home screen. Native iOS and Android apps are on the roadmap.","Sweep est conçu d’abord pour le mobile et fonctionne aujourd’hui dans le navigateur de ton téléphone ; tu peux l’ajouter à ton écran d’accueil. Des apps iOS et Android natives sont prévues.","Sweep está pensado primero para el móvil y hoy funciona en el navegador de tu teléfono; puedes añadirlo a tu pantalla de inicio. Las apps nativas para iOS y Android están previstas.")),
 (T("What happens after the 60 days of Pro?","Que se passe-t-il après les 60 jours de Pro ?","¿Qué pasa después de los 60 días de Pro?"),
  T("You keep everything you logged. Your account moves to the Free plan unless you choose to upgrade to Pro or Elite.","Tu gardes tout ce que tu as journalisé. Ton compte passe au forfait Free, sauf si tu choisis Pro ou Elite.","Conservas todo lo que registraste. Tu cuenta pasa al plan Free salvo que elijas Pro o Elite.")),
]

def home_faq(lang, t):
    items = "".join(faq_item(t, q, a) for q, a in HOME_FAQ)
    return (f'<section class="rule" id="faq"><div class="wrap narrow"><div class="head"><h2>{t(T("Frequently asked questions","Questions fréquentes","Preguntas frecuentes"))}</h2></div>{items}'
            f'<div class="cta-row"><a class="btn btn-line" href="{href(lang,"faq.html")}">{t(T("All questions","Toutes les questions","Todas las preguntas"))}</a></div></div></section>')

def home_faq_ld(t):
    return {"@type":"FAQPage","mainEntity":[{"@type":"Question","name":t(q),"acceptedAnswer":{"@type":"Answer","text":t(a)}} for q,a in HOME_FAQ]}

def home_final(lang, t):
    return (f'<section class="final rule"><div class="wrap"><h2>{t(T("Start building your edge today.","Commence à bâtir ton edge aujourd’hui.","Empieza a construir tu ventaja hoy."))}</h2>'
            f'<p class="lead">{t(T("Free forever · 60 days of Pro included · English, Français, Español","Gratuit pour toujours · 60 jours de Pro offerts · English, Français, Español","Gratis para siempre · 60 días de Pro incluidos · English, Français, Español"))}</p>'
            f'<div class="cta-row" style="justify-content:center"><a class="btn btn-primary btn-lg" href="{SIGNUP}">{t(T("Start free — no card required","Commencer gratuitement — sans carte","Empieza gratis — sin tarjeta"))}</a></div></div></section>')
