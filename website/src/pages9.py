from core import *

GAME_LIVE = True   # set False to label all gamification as "Coming soon" across the site

def soon(t):
    return "" if GAME_LIVE else f' <span class="plan-tag">{t(T("Coming soon","Bientôt","Pronto"))}</span>'

# ------------------------------------------------------------------ home: why Sweep (section 4.2)
def sec_why(lang, t):
    items = [("net", T("The same numbers as your platform.","Les mêmes chiffres que ta plateforme.","Los mismos números que tu plataforma."),
                       T("Real P&L, fees and slippage. No more gaps with your account.","P&L réel, frais et glissement. Fini les écarts avec ton compte.","P&L real, comisiones y deslizamiento. Se acabaron las diferencias con tu cuenta.")),
             ("shield", T("Your firm’s real rules.","Les vraies règles de ta firme.","Las reglas reales de tu firma."),
                       T("Drawdown, payout conditions, evaluation → funded → live.","Drawdown, conditions de payout, évaluation → financé → live.","Drawdown, condiciones de payout, evaluación → fondeada → live.")),
             ("target2", T("A routine that rewards discipline.","Une routine qui récompense ta discipline.","Una rutina que premia tu disciplina."),
                       T("Never your profit.","Jamais ton profit.","Nunca tu beneficio."))]
    cells = "".join(f'<div>{ico(I[k])}<h3>{t(h)}</h3><p>{t(p)}</p></div>' for k,h,p in items)
    return f'<section class="why-sec"><div class="wrap"><div class="why stagger">{cells}</div></div></section>'

# ------------------------------------------------------------------ home: log by screenshot (2.1)
def sec_capture(lang, t):
    pts = [T("<b>Net P&L like on your platform,</b> and your R, shown first","<b>Le P&L net comme sur ta plateforme,</b> et ton R, en premier","<b>El P&L neto como en tu plataforma,</b> y tu R, primero"),
           T("<b>Discipline and psychology</b> on the same screen","<b>Discipline et psychologie</b> sur le même écran","<b>Disciplina y psicología</b> en la misma pantalla"),
           T("<b>Several accounts at once</b> with “Also on”","<b>Plusieurs comptes d’un coup</b> avec « Aussi sur »","<b>Varias cuentas a la vez</b> con «También en»"),
           T("<b>Prefer typing?</b> Entry and exit side by side, quick exits at the stop or target","<b>Tu préfères à la main ?</b> Entrée et sortie côte à côte, sorties rapides au stop ou à l’objectif","<b>¿Prefieres a mano?</b> Entrada y salida lado a lado, salidas rápidas al stop o al objetivo")]
    media = slot("v6-03-log-by-screenshot-m.webp","phone",t(T("Pasting a screenshot fills the trade","Coller une capture remplit le trade","Pegar una captura completa la operación")),t)
    return split(t, T("New · Logging","Nouveau · Saisie","Nuevo · Registro"), T("One screenshot. Trade logged.","Une capture. Ton trade est fait.","Una captura. Operación registrada."),
        T("Paste your platform’s screenshot: Sweep AI fills in the trade, your net P&L and your R. Answer your discipline and psychology on the same screen.",
          "Colle la capture de ta plateforme : Sweep AI remplit le trade, ton P&L net et ton R. Tu réponds à ta discipline et ta psychologie sur le même écran.",
          "Pega la captura de tu plataforma: Sweep AI completa la operación, tu P&L neto y tu R. Respondes tu disciplina y tu psicología en la misma pantalla."),
        pts, media, id_="logging")

# ------------------------------------------------------------------ home + features: real prop rules (2.4)
def sec_rules(lang, t, id_="prop", flip=False, link=True):
    pts = [T("<b>Real payout conditions,</b> counted since your last request: winning days, cushion, minimum and maximum","<b>Conditions de payout réelles,</b> comptées depuis ta dernière demande : jours gagnants, coussin, minimum et maximum","<b>Condiciones de payout reales,</b> contadas desde tu última solicitud: días ganadores, colchón, mínimo y máximo"),
           T("<b>Evaluation passed → funded,</b> created automatically with your firm’s funded rules","<b>Évaluation réussie → financé,</b> créé automatiquement avec les règles financées de ta firme","<b>Evaluación superada → fondeada,</b> creada automáticamente con las reglas fondeadas de tu firma"),
           T("<b>Live accounts</b> highlighted, funded → live in one tap","<b>Comptes live</b> mis en avant, financé → live en un toucher","<b>Cuentas live</b> destacadas, fondeada → live en un toque"),
           T("<b>A rule changes?</b> You see what it means for your account, and you decide","<b>Une règle change ?</b> Tu vois ce que ça change pour ton compte, et tu décides","<b>¿Cambia una regla?</b> Ves qué significa para tu cuenta, y tú decides")]
    m = f'<div class="cta-row"><a class="btn btn-line" href="{href(lang,"prop-traders.html")}">{t(T("Sweep for prop traders","Sweep pour les traders prop","Sweep para traders prop"))}</a></div>' if link else ""
    note = f'<p class="fine">{t(T("Rules prefilled for guidance only. Catalog checked every week. Always check your firm’s current rules.","Règles préremplies à titre indicatif. Catalogue vérifié chaque semaine. Vérifie toujours les règles actuelles de ta firme.","Reglas precargadas a título indicativo. Catálogo revisado cada semana. Verifica siempre las reglas actuales de tu firma."))}</p>'
    media = slot("ecran-payout-apex.webp","desktop",t(T("Payout conditions card for a prop account","Carte des conditions de payout d’un compte prop","Tarjeta de condiciones de payout de una cuenta prop")),t,fallback="cap:ecran-comptes-prop.webp")
    return split(t, T("Prop firms","Prop firms","Prop firms"), T("Your firm’s real rules.","Les vraies règles de ta firme.","Las reglas reales de tu firma."),
        T("Apex, Topstep, Lucid, Take Profit Trader, MyFundedFutures: winning days, safety net, payout minimum and maximum. Sweep tells you when you can request, and how much.",
          "Apex, Topstep, Lucid, Take Profit Trader, MyFundedFutures : jours gagnants, coussin, minimum et maximum de payout. Sweep te dit quand tu peux demander, et combien.",
          "Apex, Topstep, Lucid, Take Profit Trader, MyFundedFutures: días ganadores, colchón, mínimo y máximo de payout. Sweep te dice cuándo puedes pedirlo y cuánto."),
        pts, media, flip=flip, id_=id_, more=note + m)

# ------------------------------------------------------------------ features: platform numbers (2.2 + 2.3)
def sec_numbers(lang, t):
    pts = [T("<b>Real P&L (platform):</b> type the P&L your platform shows, it becomes the truth everywhere","<b>P&L réel (plateforme) :</b> tape le P&L affiché par ta plateforme, il devient la vérité partout","<b>P&L real (plataforma):</b> escribe el P&L de tu plataforma y se convierte en la referencia en todas partes"),
           T("<b>Commission per contract</b> on each account, deducted automatically","<b>Commission par contrat</b> sur chaque compte, déduite automatiquement","<b>Comisión por contrato</b> en cada cuenta, descontada automáticamente"),
           T("<b>Slippage and fees:</b> what slippage costs you, in $ and in R","<b>Glissement et frais :</b> ce que le glissement te coûte, en $ et en R","<b>Deslizamiento y comisiones:</b> lo que te cuesta el deslizamiento, en $ y en R"),
           T("<b>Add to a position and partial exits,</b> with the average entry price recalculated like on your platform","<b>Ajout à la position et sorties partielles,</b> avec le prix moyen recalculé comme sur ta plateforme","<b>Añadir a la posición y salidas parciales,</b> con el precio medio recalculado como en tu plataforma"),
           T("<b>Recalibrate an account</b> to your platform balance without skewing your stats","<b>Recalibrer un compte</b> sur le solde de ta plateforme, sans fausser tes statistiques","<b>Recalibrar una cuenta</b> al saldo de tu plataforma sin alterar tus estadísticas")]
    return split(t, T("Your numbers","Tes chiffres","Tus números"), T("The same numbers as your platform.","Les mêmes chiffres que ta plateforme.","Los mismos números que tu plataforma."),
        T("Exact P&L on average prices, to the cent. Enter prices or dollar amounts for the exit, stop and target.","P&L exact sur les prix moyens, au cent près. Saisis des prix ou des montants en $ pour la sortie, le stop et l’objectif.","P&L exacto sobre precios medios, al céntimo. Introduce precios o importes en $ para la salida, el stop y el objetivo."),
        pts, slot("ecran-formulaire-capture.webp","phone",t(T("Trade form with net P&L and R first","Formulaire avec P&L net et R en premier","Formulario con P&L neto y R primero")),t,fallback="cap:ecran-ajout-bougie-static.webp"), flip=True, id_="numbers")

# ------------------------------------------------------------------ changelog page
CARDS = [
 ("v6-12-payouts-d.webp","desktop",T("My money","Mon argent","Mi dinero"),T("Real net = payouts received + live and personal P&L − expenses. Simulated and real are never mixed.","Net réel = payouts reçus + P&L live et perso − dépenses. Le simulé et le réel ne sont jamais mélangés.","Neto real = payouts recibidos + P&L live y personal − gastos. Lo simulado y lo real nunca se mezclan.")),
 (None,None,T("Every trade from one screenshot","Tous les trades d’une seule capture","Todas las operaciones de una captura"),T("A history screenshot from Tradovate, Rithmic, NinjaTrader or TopstepX creates all its trades at once. You check, you save.","Une capture d’historique Tradovate, Rithmic, NinjaTrader ou TopstepX crée tous ses trades d’un coup. Tu vérifies, tu enregistres.","Una captura del historial de Tradovate, Rithmic, NinjaTrader o TopstepX crea todas sus operaciones de una vez. Revisas y guardas.")),
 (None,None,T("Your day runs on New York time","Ta journée suit New York","Tu día sigue Nueva York"),T("At 6 p.m. ET the whole app moves to the next session. Evening trades land on the right day.","À 18 h ET, toute l’app passe à la séance suivante. Les trades du soir arrivent sur le bon jour.","A las 18:00 ET toda la app pasa a la sesión siguiente. Las operaciones de la noche caen en el día correcto.")),
 ("ecran-formulaire-capture.webp","phone",T("Log a trade from a screenshot","Ajoute un trade par capture d’écran","Registra una operación con una captura"),T("Paste your screenshot, Sweep AI fills the trade. You check, you save.","Colle ta capture, Sweep AI remplit le trade. Tu vérifies, tu enregistres.","Pega tu captura, Sweep AI completa la operación. Revisas y guardas.")),
 (None,None,T("The same numbers as your platform","Les mêmes chiffres que ta plateforme","Los mismos números que tu plataforma"),T("Real P&L, commission per contract, slippage and fees. No more gaps with your account.","P&L réel, commission par contrat, glissement et frais. Plus d’écart avec ton compte.","P&L real, comisión por contrato, deslizamiento y comisiones. Sin diferencias con tu cuenta.")),
 (None,None,T("Multiple entries and partial exits","Entrées multiples et sorties partielles","Entradas múltiples y salidas parciales"),T("Average price recalculated like on your platform, entries in price or in $.","Prix moyen recalculé comme sur ta plateforme, saisie en prix ou en $.","Precio medio recalculado como en tu plataforma, en precio o en $.")),
 ("ecran-payout-apex.webp","desktop",T("Your prop firm’s real rules","Les vraies règles de ta prop firm","Las reglas reales de tu prop firm"),T("Real payout conditions, evaluation → funded → live, a catalog checked every week.","Conditions de payout réelles, évaluation → financé → live, catalogue vérifié chaque semaine.","Condiciones de payout reales, evaluación → fondeada → live, catálogo revisado cada semana.")),
 ("ecran-trade-copie.webp","desktop",T("Copy trading","Copy trading","Copy trading"),T("“Also on” when you add a trade. A copied trade shows once, with the total.","« Aussi sur » à l’ajout. Un trade copié s’affiche une seule fois, avec le total.","«También en» al añadir. Una operación copiada se muestra una vez, con el total.")),
 ("ecran-aujourdhui-tel.webp","phone",T("Today","Aujourd’hui","Hoy"),T("Your day in one card: P&L, today’s releases, trades, and why your rings have that score.","Ta journée en une carte : P&L, annonces du jour, trades, et pourquoi tes anneaux ont ce score.","Tu día en una tarjeta: P&L, datos del día, operaciones y por qué tus anillos tienen esa puntuación.")),
 (None,None,T("The trader’s routine","La routine du trader","La rutina del trader"),T("Daily plan, pre-market with a chart and screenshots, weekly review.","Plan du jour, pré-marché avec graphique et captures, bilan de la semaine.","Plan del día, premercado con gráfico y capturas, revisión semanal.")),
 (None,None,T("Ask Sweep everywhere","Ask Sweep partout","Ask Sweep en todas partes"),T("On every page, with questions that fit the page. One tap and it’s sent.","Sur chaque page, avec des questions adaptées. Un toucher et c’est envoyé.","En cada página, con preguntas adaptadas. Un toque y se envía.")),
]
DAYS = [
 ("2026-10-08", T("October 8","8 octobre","8 de octubre"), [
   T("<b>My money:</b> real net (payouts received + live and personal P&L − expenses), by period, by firm, with ROI and a yearly CSV export","<b>Mon argent :</b> net réel (payouts reçus + P&L live et perso − dépenses), par période, par firme, avec ROI et export annuel en CSV","<b>Mi dinero:</b> neto real (payouts recibidos + P&L live y personal − gastos), por periodo, por firma, con ROI y exportación anual en CSV"),
   T("Account types Evaluation, Funded, Live and Personal; amounts labeled <b>Simulated</b> or <b>Real</b>, never added together","Types de comptes Évaluation, Financé, Live et Perso ; montants étiquetés <b>Simulé</b> ou <b>Réel</b>, jamais additionnés","Tipos de cuenta Evaluación, Fondeada, Live y Personal; importes marcados <b>Simulado</b> o <b>Real</b>, nunca sumados"),
   T("Payouts with gross, split, transfer fees and net received; expenses by category, refunds and monthly subscriptions","Payouts avec brut, split, frais de virement et net reçu ; dépenses par catégorie, remboursements et abonnements mensuels","Payouts con bruto, split, comisiones de transferencia y neto recibido; gastos por categoría, reembolsos y suscripciones mensuales"),
   T("<b>Several trades from one screenshot:</b> a history capture creates every trade at once, with duplicates unchecked and one Undo","<b>Plusieurs trades sur une capture :</b> une capture d’historique crée tous les trades d’un coup, doublons décochés et un seul Annuler","<b>Varias operaciones en una captura:</b> una captura del historial crea todas las operaciones de una vez, sin duplicados y con un solo Deshacer"),
   T("Imports: TradingView CSV (Order History), Rithmic files with several accounts, fees from the file or your account","Imports : CSV TradingView (Order History), fichiers Rithmic à plusieurs comptes, frais du fichier ou de ton compte","Importaciones: CSV de TradingView (Order History), archivos de Rithmic con varias cuentas, comisiones del archivo o de tu cuenta"),
   T("<b>The day follows New York:</b> at 6 p.m. ET the whole app moves to the next session","<b>La journée suit New York :</b> à 18 h ET, toute l’app passe à la séance suivante","<b>El día sigue Nueva York:</b> a las 18:00 ET toda la app pasa a la sesión siguiente"),
   T("Prop firm presets checked October 7 (Topstep, Apex, MyFundedFutures, Take Profit Trader, Lucid); you choose whether to apply rule changes","Préréglages des prop firms vérifiés le 7 octobre (Topstep, Apex, MyFundedFutures, Take Profit Trader, Lucid) ; tu choisis d’appliquer ou non les changements","Preajustes de prop firms revisados el 7 de octubre (Topstep, Apex, MyFundedFutures, Take Profit Trader, Lucid); tú eliges si aplicar los cambios"),
   T("“Target reached” only when target, consistency and minimum days are all met; drawdown accounts for payouts already withdrawn","« Objectif atteint » seulement quand objectif, consistance et jours minimum sont remplis ; le drawdown tient compte des payouts retirés","«Objetivo alcanzado» solo cuando objetivo, consistencia y días mínimos se cumplen; el drawdown tiene en cuenta los payouts retirados"),
   T("New instruments: 6E, M6E, ZN, ZB, SI, SIL, NG, HG, MBT, MET","Nouveaux instruments : 6E, M6E, ZN, ZB, SI, SIL, NG, HG, MBT, MET","Nuevos instrumentos: 6E, M6E, ZN, ZB, SI, SIL, NG, HG, MBT, MET"),
   T("Plan and Journal linked; your daily routine always open with the next step highlighted","Plan et Journal reliés ; ta routine du jour toujours ouverte, avec l’étape suivante mise en avant","Plan y Diario vinculados; tu rutina diaria siempre abierta con el siguiente paso destacado"),
   T("Clearer design, Undo on deletions, accessible labels on every control, about 18% faster first load on phones","Design plus clair, Annuler sur les suppressions, noms accessibles sur chaque contrôle, premier affichage environ 18 % plus rapide sur téléphone","Diseño más claro, Deshacer en las eliminaciones, nombres accesibles en cada control, primera carga un 18 % más rápida en el teléfono")]),
 ("2026-10-06", T("October 6","6 octobre","6 de octubre"), [
   T("Log a trade from a screenshot or by hand: you choose on your first trade, same look for both","Ajout de trade par capture d’écran ou à la main : tu choisis au premier ajout, même visuel pour les deux","Registro por captura o a mano: eliges en la primera operación, mismo diseño para ambos"),
   T("Screenshot form: net P&L and R first, details folded, discipline and psychology on the same screen","Formulaire par capture : P&L net et R d’abord, détails repliés, discipline et psychologie sur le même écran","Formulario por captura: P&L neto y R primero, detalles plegados, disciplina y psicología en la misma pantalla"),
   T("Manual form reordered: entry and exit, quick exits, stop and target, time, then real P&L","Formulaire manuel réordonné : entrée et sortie, sorties rapides, stop et objectif, heure, puis P&L réel","Formulario manual reordenado: entrada y salida, salidas rápidas, stop y objetivo, hora y luego P&L real"),
   T("Today on phones: one card with the days, the releases and your trades","Aujourd’hui sur téléphone : une seule carte avec les jours, les annonces et les trades","Hoy en el móvil: una sola tarjeta con los días, los datos y tus operaciones"),
   T("Copy trading visible everywhere, a copied trade shown only once","Copy trading visible partout, trade copié affiché une seule fois","Copy trading visible en todas partes, operación copiada mostrada una sola vez"),
   T("<b>Real payout conditions by firm</b> (Apex, Topstep, Lucid, TPT, MFFU)","<b>Conditions de payout réelles par firme</b> (Apex, Topstep, Lucid, TPT, MFFU)","<b>Condiciones de payout reales por firma</b> (Apex, Topstep, Lucid, TPT, MFFU)"),
   T("<b>Evaluation → funded automatically,</b> live accounts highlighted","<b>Évaluation → financé automatique,</b> comptes live mis en avant","<b>Evaluación → fondeada automática,</b> cuentas live destacadas")]),
 ("2026-10-05", T("October 5","5 octobre","5 de octubre"), [
   T("Guide and help center, tips on every page","Guide et centre d’aide, astuces par page","Guía y centro de ayuda, consejos en cada página"),
   T("Backups, launch offers, features unlocked step by step, polished empty states","Sauvegardes, offres de lancement, fonctions débloquées progressivement, états vides soignés","Copias de seguridad, ofertas de lanzamiento, funciones desbloqueadas poco a poco, estados vacíos cuidados"),
   T("<b>Navigation redesigned,</b> then a finishing pass on phones","<b>Navigation repensée,</b> puis une passe de finition sur téléphone","<b>Navegación rediseñada,</b> y una pasada de acabado en el móvil"),
   T("<b>New Today page:</b> performance, economic releases, calendar with trades and releases","<b>Nouvelle page Aujourd’hui :</b> performance, annonces économiques, calendrier avec trades et annonces","<b>Nueva página Hoy:</b> rendimiento, datos económicos, calendario con operaciones y datos"),
   T("<b>Prop firm catalog</b> checked every week, guided choice (firm → type → size)","<b>Catalogue de prop firms</b> vérifié chaque semaine, choix guidé (firme → type → taille)","<b>Catálogo de prop firms</b> revisado cada semana, elección guiada (firma → tipo → tamaño)"),
   T("Plan first before your first trade, suggested setups","Plan d’abord avant le premier trade, setups suggérés","Primero el plan antes de la primera operación, setups sugeridos"),
   T("Fixes: emotions and scores saved, trade notes saved, prices with a comma (French keyboards), Back button","Corrections : émotions et scores enregistrés, notes de trade enregistrées, prix avec virgule (claviers français), bouton Retour","Correcciones: emociones y puntuaciones guardadas, notas guardadas, precios con coma (teclados franceses), botón Atrás"),
   T("Journal with a recap, amounts in $, multiple entries and partial exits","Journal avec récap, montants en $, entrées multiples et sorties partielles","Diario con resumen, importes en $, entradas múltiples y salidas parciales"),
   T("Real P&L, slippage and fees, commission per account","P&L réel, glissement et frais, commission par compte","P&L real, deslizamiento y comisiones, comisión por cuenta"),
   T("Weekly review (summary, then questions), Sweep AI front and center, Quick access","Bilan de la semaine (résumé puis questions), Sweep AI mis en avant, Accès rapide","Revisión semanal (resumen y luego preguntas), Sweep AI destacado, Acceso rápido"),
   T("Ring explanations, account recalibration and renaming, exact P&L on average prices","Explication des anneaux, recalibrage et renommage des comptes, P&L exact sur prix moyens","Explicación de los anillos, recalibrado y renombrado de cuentas, P&L exacto sobre precios medios"),
   T("Pre-market: a chart and screenshots","Pré-marché : un graphique et des captures","Premercado: un gráfico y capturas")]),
 ("2026-10-04", T("October 4","4 octobre","4 de octubre"), [
   T("Real charts on the trade recap and in the add form","Graphiques réels sur le récap de trade et dans le formulaire d’ajout","Gráficos reales en el resumen de la operación y en el formulario"),
   T("Weekly review with a chest, cosmetics, Edge Reveal and a comeback quest","Bilan de la semaine avec coffre, cosmétiques, Edge Reveal et quête de retour","Revisión semanal con cofre, cosméticos, Edge Reveal y misión de regreso"),
   T("Monthly and yearly Wrapped, scheduled reminders","Wrapped mensuel et annuel, rappels programmés","Wrapped mensual y anual, recordatorios programados"),
   T("Seasons, leagues, crews, buddy, Discord roles","Saisons, ligues, équipes, buddy, rôles Discord","Temporadas, ligas, crews, buddy, roles de Discord"),
   T("Full ZIP export, prop firm presets (first version), wow moments","Export complet en ZIP, préréglages de prop firms (première version), moments « wow »","Exportación completa en ZIP, preajustes de prop firms (primera versión), momentos «wow»")]),
 ("2026-10-03", T("October 3","3 octobre","3 de octubre"), [
   T("Notification center and event system","Centre de notifications et système d’événements","Centro de notificaciones y sistema de eventos"),
   T("Full design pass: menus, animations, new sign-in page","Passe complète de design : menus, animations, nouvelle page de connexion","Revisión completa del diseño: menús, animaciones, nueva página de acceso"),
   T("Simpler payouts and expenses","Payouts et dépenses simplifiés","Payouts y gastos simplificados"),
   T("Progression V1: 3 rings, XP, streaks, badges, onboarding","Progression V1 : 3 anneaux, XP, streaks, badges, onboarding","Progresión V1: 3 anillos, XP, rachas, insignias, onboarding"),
   T("Path map, weekly missions, “ready for payout” status","Carte du parcours, missions de la semaine, état « prêt pour le payout »","Mapa del recorrido, misiones semanales, estado «listo para el payout»"),
   T("First real candlestick charts","Premiers graphiques en bougies réelles","Primeros gráficos de velas reales")]),
]

def page_changelog(lang, t, older=""):
    hero = page_hero(t, T("What’s new in Sweep.","Ce qui est nouveau dans Sweep.","Lo nuevo en Sweep."),
        T("A trading journal built for futures prop traders: your account’s real numbers, your firm’s real rules, a trade logged in seconds and a daily routine that rewards discipline, not profit.",
          "Un journal de trading pensé pour les traders de prop firms de futures : les vrais chiffres de ton compte, les vraies règles de ta firme, un trade ajouté en quelques secondes et une routine quotidienne qui récompense la discipline, pas le profit.",
          "Un diario de trading pensado para traders de prop firms de futuros: los números reales de tu cuenta, las reglas reales de tu firma, una operación registrada en segundos y una rutina diaria que premia la disciplina, no el beneficio."),
        T("What’s new","Nouveautés","Novedades"))
    cards = ""
    for img, kind, h, p in CARDS:
        media = slot(img, "phone" if kind == "phone" else "desktop", t(h), t, cap=False) if img else ""
        cards += f'<article class="ncard reveal{" has-media" if img else ""}"><div class="ntxt"><h2>{t(h)}</h2><p>{t(p)}</p></div>{media}</article>'
    days = ""
    for i, (iso, label, items) in enumerate(DAYS):
        days += f'<details class="day"{" open" if i == 0 else ""}><summary><time datetime="{iso}">{t(label)}</time><span class="cnt num">{len(items)}</span></summary>{ul(t, items)}</details>'
    b = (f'<section style="padding-top:8px"><div class="wrap"><div class="ncards">{cards}</div></div></section>'
         f'<section class="rule"><div class="wrap narrow"><div class="head"><h2>{t(T("Day by day","Jour par jour","Día a día"))}</h2></div><div class="days">{days}</div>'
         + (f'<details class="day older"><summary><span>{t(T("Earlier releases","Versions précédentes","Versiones anteriores"))}</span></summary><div class="older-body">{older}</div></details>' if older else "")
         + '</div></section>')
    return (t(T("What’s new in Sweep · Changelog","Nouveautés de Sweep · Changelog","Novedades de Sweep · Changelog")),
            t(T("Log a trade from a screenshot, your platform’s real numbers, real prop firm payout rules, copy trading and a new Today page.","Ajout de trade par capture, les vrais chiffres de ta plateforme, les vraies règles de payout des prop firms, copy trading et nouvelle page Aujourd’hui.","Registro por captura, los números reales de tu plataforma, reglas de payout reales de las prop firms, copy trading y nueva página Hoy.")),
            hero + b + final_cta(lang, t), "")
