from core import *

def vslot(name, kind, alt, t, poster):
    return slot(name, kind, alt, t, video=True, poster=poster, cap=True)

def sec_eval(lang, t):
    return split(t, T("Evaluation → funded → live","Évaluation → financé → live","Evaluación → fondeada → live"),
        T("From evaluation to live.","De l’évaluation au live.","De la evaluación al live."),
        T("Passed your evaluation? Sweep congratulates you and creates your funded account with its rules. Then your live account, with its own rules.",
          "Tu réussis ton évaluation ? Sweep te félicite et crée ton compte financé avec ses règles. Puis ton compte live, avec ses propres règles.",
          "¿Superaste tu evaluación? Sweep te felicita y crea tu cuenta fondeada con sus reglas. Luego tu cuenta live, con sus propias reglas."),
        [T("<b>Evaluation, funded or live:</b> the first question when you add an account","<b>Évaluation, financé ou live :</b> la première question à l’ajout d’un compte","<b>Evaluación, fondeada o live:</b> la primera pregunta al añadir una cuenta"),
         T("<b>The evaluation stays archived</b> as passed","<b>L’évaluation reste archivée</b> comme réussie","<b>La evaluación queda archivada</b> como superada"),
         T("<b>Live accounts</b> get a LIVE badge","<b>Les comptes live</b> ont un badge LIVE","<b>Las cuentas live</b> llevan una insignia LIVE")],
        vslot("v6-video-evaluation-to-funded.mp4","desktop",t(T("Payout conditions, evaluation passed, funded account created","Conditions de payout, évaluation réussie, compte financé créé","Condiciones de payout, evaluación superada, cuenta fondeada creada")),t,"v6-poster-evaluation-to-funded.webp"),
        flip=True, id_="evaluation")

def sec_share(lang, t):
    return split(t, T("Share","Partage","Compartir"), T("Show your work.","Montre ton travail.","Muestra tu trabajo."),
        T("Share your stats as an image, or your full Stats page as a link: you pick the period and what to show.",
          "Partage tes stats en image, ou ta page Stats complète en lien : tu choisis la période et ce que tu montres.",
          "Comparte tus estadísticas en imagen, o tu página de Stats completa como enlace: eliges el periodo y lo que muestras."),
        [T("<b>Stats card</b> with your name, amounts optional","<b>Carte de stats</b> avec ton nom, montants optionnels","<b>Tarjeta de stats</b> con tu nombre, importes opcionales"),
         T("<b>Read-only link</b> to your Stats page, deletable anytime","<b>Lien en lecture seule</b> vers ta page Stats, supprimable à tout moment","<b>Enlace de solo lectura</b> a tu página de Stats, se puede borrar cuando quieras"),
         T("<b>Payout cards:</b> one payout, or totals for the day, week, month or all time","<b>Cartes de payout :</b> un payout, ou les totaux du jour, de la semaine, du mois ou depuis le début","<b>Tarjetas de payout:</b> un payout, o los totales del día, la semana, el mes o desde el inicio")],
        vslot("v6-video-share-stats.mp4","desktop",t(T("Stats card, then a link to the public Stats page","Carte de stats, puis lien vers la page Stats publique","Tarjeta de stats y enlace a la página de Stats pública")),t,"v6-poster-share-stats.webp"),
        id_="share")

def sec_today(lang, t):
    copy = f'''<div class="copytrade"><span class="kick">{t(T("Copy trading","Copy trading","Copy trading"))}</span><h3>{t(T("Copy trading, no duplicates.","Copy trading, sans doublons.","Copy trading, sin duplicados."))}</h3>
<p>{t(T("One trade on 5 accounts shows once, with the total.","Un trade sur 5 comptes s’affiche une seule fois, avec le total.","Una operación en 5 cuentas se muestra una sola vez, con el total."))}</p></div>'''
    return split(t, T("Today","Aujourd’hui","Hoy"), T("Your day at a glance.","Ta journée d’un coup d’œil.","Tu día de un vistazo."),
        T("Plan, Execution and Review rings, your level, P&L, today’s economic releases and every account with its drawdown room.",
          "Les anneaux Plan, Exécution et Revue, ton niveau, ton P&L, les annonces économiques du jour et chaque compte avec sa marge de drawdown.",
          "Los anillos Plan, Ejecución y Revisión, tu nivel, tu P&L, los datos económicos del día y cada cuenta con su margen de drawdown."),
        [T("Swipe through the days on your phone","Fais défiler les jours sur ton téléphone","Desliza entre los días en tu teléfono"),
         T("Tap a ring to see why, and what to do next","Touche un anneau pour savoir pourquoi, et quoi faire","Toca un anillo para saber por qué y qué hacer")],
        vslot("v6-video-today-phone.mp4","phone",t(T("Today on a phone: days, releases, week, payout card","Aujourd’hui sur téléphone : jours, annonces, semaine, carte payout","Hoy en el teléfono: días, datos, semana, tarjeta de payout")),t,"v6-poster-today-phone.webp"),
        id_="today", more=copy)

def sec_signup(lang, t):
    return f'''<section class="rule signup-sec"><div class="wrap split">
<div class="copy"><span class="kick">{t(T("Sign up","Inscription","Registro"))}</span><h2>{t(T("Start in 30 seconds.","Commence en 30 secondes.","Empieza en 30 segundos."))}</h2>
<p class="lead">{t(T("Your email, a password, and you’re in. Free forever, with Pro included for 60 days.","Ton email, un mot de passe, et tu es dedans. Gratuit pour toujours, avec Pro offert pendant 60 jours.","Tu email, una contraseña y listo. Gratis para siempre, con Pro incluido durante 60 días."))}</p>
<div class="cta-row"><a class="btn btn-primary btn-lg" href="{SIGNUP}">{t(T("Start for free","Commencer gratuitement","Empieza gratis"))}</a></div>
<p class="meta">{t(T("Questions? Write to","Une question ? Écris à","¿Una pregunta? Escribe a"))} <a href="mailto:{EMAIL}">{EMAIL}</a></p></div>
<div class="reveal">{slot("v6-20-signup-d.webp","desktop",t(T("The one-screen sign-up","L’inscription en un écran","El registro en una pantalla")),t)}</div></div></section>'''
