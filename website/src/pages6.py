from core import *
CAPTURES['ecran-apercu-anneaux.webp'] = ('phone', 1179, 2556, 'Today card with the three rings and shortcuts (hero)')
from pages4 import money, PRICES

START = T("Start free","Commencer gratuitement","Empieza gratis")
CONTRACTS14 = "NQ MNQ ES MES YM MYM RTY M2K CL MCL GC MGC SI 6E".split()
CHART_NOTE = T("Charts available 24 hours after the session. CME market data. Charts powered by TradingView Lightweight Charts™.",
               "Graphiques disponibles 24 h après la séance. Données de marché CME. Graphiques propulsés par TradingView Lightweight Charts™.",
               "Gráficos disponibles 24 h después de la sesión. Datos de mercado de CME. Gráficos impulsados por TradingView Lightweight Charts™.")
CHECK = '<svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 8.5l3 3 7-7"/></svg>'
def chips14(): return '<div class="chips">' + "".join(f"<span>{c}</span>" for c in CONTRACTS14) + "</div>"
def note(t, d): return f'<p class="fine">{t(d)}</p>'

# ----------------------------------------------------------------- sections reused on several pages
def sec_sweep_day(lang, t, id_="sweep-the-day", rule=True):
    """The daily loop (How it works), on the design system: a phone video beside the text."""
    import ui
    return ui.split(t, T("The daily loop","La boucle quotidienne","El ciclo diario"), T("Sweep your day.","Balaye ta journée.","Barre tu día."),
      T("Three rings every market day: plan before the open, trade by your rules, review after the session. Close all three and your day is swept. A day counts for your discipline streak once your platform balance is checked or synced, winning or losing. Streak freezes protect your runs, and weekends never count against you.",
        "Trois anneaux chaque jour de marché : planifier avant l’ouverture, trader selon tes règles, réviser après la séance. Les trois faites, ta journée est balayée. Une journée compte pour ton streak de discipline dès que le solde de ta plateforme est vérifié ou synchronisé, gagnante ou perdante. Les gels de streak protègent tes séries, et le week-end ne compte jamais contre toi.",
        "Tres anillos cada día de mercado: planificar antes de la apertura, operar según tus reglas, revisar tras la sesión. Completa los tres y tu día queda barrido. Un día cuenta para tu racha de disciplina cuando el saldo de tu plataforma está verificado o sincronizado, ganador o perdedor. Las congelaciones protegen tus series y los fines de semana nunca cuentan en tu contra."),
      [T("<b>Daily plan in 30 seconds:</b> bias, key levels, two scenarios, max loss. The guided plan is one tap away","<b>Plan du jour en 30 secondes :</b> biais, niveaux clés, deux scénarios, perte max. Le plan guidé est à un toucher","<b>Plan del día en 30 segundos:</b> sesgo, niveles clave, dos escenarios, pérdida máxima. El plan guiado está a un toque"),
       T("<b>Execution</b> measured by your own discipline checklist (13 questions by default, the 3 that matter most for you on the form)","<b>Exécution</b> mesurée par ta propre checklist de discipline (13 questions par défaut, les 3 qui comptent le plus pour toi sur le formulaire)","<b>Ejecución</b> medida con tu propio checklist de disciplina (13 preguntas por defecto, las 3 que más cuentan para ti en el formulario)"),
       T("<b>Close your day in 2 taps:</b> your review opens filled in from your day, and you confirm your platform balance","<b>Ferme ta journée en 2 touchers :</b> ta revue s’ouvre remplie d’après ta journée, et tu confirmes le solde de ta plateforme","<b>Cierra tu día en 2 toques:</b> tu revisión se abre rellenada según tu día y confirmas el saldo de tu plataforma"),
       T("<b>Discipline streak</b> plus freezes: 1 on Free, 2 on Pro, 3 on Elite per week","<b>Streak de discipline</b> et gels : 1 en Free, 2 en Pro, 3 en Elite par semaine","<b>Racha de disciplina</b> y congelaciones: 1 en Free, 2 en Pro, 3 en Elite por semana"),
       T("<b>Guardrail:</b> if you go past your max daily loss, Sweep tells you, without judgment","<b>Garde-fou :</b> si tu dépasses ta perte max du jour, Sweep te le dit, sans jugement","<b>Salvaguarda:</b> si superas tu pérdida máxima del día, Sweep te lo dice, sin juzgarte")],
      ui.frame_p("v6-poster-today-phone.webp", t(T("Today on a phone: rings, days, releases","Aujourd’hui sur téléphone : anneaux, jours, annonces","Hoy en el teléfono: anillos, días, datos")), t, video="v6-video-today-phone.mp4"),
      id_=id_, phone=True, more=ui.rings(t))

def sec_charts(lang, t, sp, id_="charts", flip=True):
    return sp(t, T("Real charts","Graphiques réels","Gráficos reales"), T("Your trades on real charts.","Tes trades sur de vrais graphiques.","Tus operaciones en gráficos reales."),
      T("See every trade where it happened, on real CME candles: entry, exit, stop, target and your position zone. Charts are ready the day after the session.",
        "Vois chaque trade là où il s’est passé, sur les vraies bougies du CME : entrée, sortie, stop, objectif et zone de position. Les graphiques sont prêts le lendemain de la séance.",
        "Mira cada operación donde ocurrió, sobre velas reales de CME: entrada, salida, stop, objetivo y zona de posición. Los gráficos están listos al día siguiente de la sesión."),
      [T("<b>CME market data:</b> 14 contracts, from NQ to 6E","<b>Données de marché CME :</b> 14 contrats, de NQ à 6E","<b>Datos de mercado de CME:</b> 14 contratos, de NQ a 6E"),
       T("<b>Timeframes</b> 15 s, 30 s, 1 m, 5 m, 15 m, 1 h","<b>Unités de temps</b> 15 s, 30 s, 1 m, 5 m, 15 m, 1 h","<b>Temporalidades</b> 15 s, 30 s, 1 m, 5 m, 15 m, 1 h"),
       T("<b>Result in R</b> on the chart, shareable capture in one click","<b>Résultat en R</b> affiché sur le graphique, capture partageable en un clic","<b>Resultado en R</b> en el gráfico, captura para compartir en un clic"),
       T("<b>Full screen,</b> pinch to zoom, light and dark mode","<b>Plein écran,</b> zoom au pincement, mode clair et foncé","<b>Pantalla completa,</b> zoom con pellizco, modo claro y oscuro")],
      slot("ecran-graphique-trade.webp","desktop",t(T("Trade recap on a real NQ chart with the position zone and the result in R","Récap d’un trade NQ sur vrai graphique avec la zone de position et le résultat en R","Resumen de una operación NQ en gráfico real con la zona de posición y el resultado en R")),t),
      flip=flip, id_=id_, more=f'<div style="margin-top:26px">{chips14()}</div>{note(t,CHART_NOTE)}')

def sec_trust(lang, t, id_="data"):
    """Trust and data (features page), on the design system."""
    import ui
    items = [("download", T("Full export in one click","Export complet en un clic","Exportación completa en un clic"), T("A ZIP file with a re-importable backup, CSV spreadsheets (trades, accounts, payouts, expenses, journal) and all your screenshots.","Un fichier ZIP avec sauvegarde réimportable, tableurs CSV (trades, comptes, payouts, dépenses, journal) et toutes tes captures.","Un archivo ZIP con copia reimportable, hojas CSV (operaciones, cuentas, payouts, gastos, diario) y todas tus capturas.")),
             ("trash", T("Self-serve account deletion","Suppression du compte en libre-service","Eliminación de la cuenta por tu cuenta"), T("Delete your account and all its data yourself, anytime.","Supprime toi-même ton compte et toutes ses données, en tout temps.","Elimina tú mismo tu cuenta y todos sus datos, cuando quieras.")),
             ("eye", T("Private by default","Privé par défaut","Privado por defecto"), T("No social feature is active without your consent.","Aucune fonction sociale n’est active sans ton accord.","Ninguna función social está activa sin tu consentimiento.")),
             ("chat", T("Feedback loop","Boucle de feedback","Ciclo de feedback"), {l: {"en": "Suggest an idea or report a bug from the app and follow its status. When it ships: “You asked, we built it.” Everything shipped is in the <a href=\"{u}\">changelog</a>.",
                    "fr": "Propose une idée ou signale un bug depuis l’app et suis son statut. Quand c’est livré : « Tu l’as demandé, on l’a construit. » Tout ce qui est livré est dans le <a href=\"{u}\">changelog</a>.",
                    "es": "Propón una idea o reporta un error desde la app y sigue su estado. Cuando sale: «Lo pediste, lo construimos». Todo lo que sale está en el <a href=\"{u}\">changelog</a>."}[l].replace("{u}", href(l, "changelog.html")) for l in LANGS})]
    return ui.sec(ui.head(t, T("Trust and data","Confiance et données","Confianza y datos"), T("Your data belongs to you.","Tes données t’appartiennent.","Tus datos te pertenecen."),
                          T("Private by default. Yours to export or delete, anytime.","Privées par défaut. À toi de les exporter ou de les supprimer, quand tu veux.","Privados por defecto. Tuyos para exportar o eliminar, cuando quieras."))
                  + ui.tiles(t, items, cls="trust stagger"), "n", id_)

GAME = [
 ("ecran-badges.webp", "progression", T("My progress","Ma progression","Mi progreso"), T("Swept days, a streak and 25 badges","Journées balayées, streak et 25 badges","Días barridos, racha y 25 insignias"),
  T("One sheet: the days you swept (plan, execution and review all done), your streak of complete days, and 25 badges earned by what you do: a first plan, a perfect week, stops respected. What to do next is always in “Now”, at the top of Today.",
    "Une seule feuille : tes journées balayées (plan, exécution et revue faits), ton streak de jours complets, et 25 badges gagnés par ce que tu fais : un premier plan, une semaine parfaite, des stops respectés. Quoi faire ensuite ? « Maintenant », en haut d’Aujourd’hui, te le dit toujours.",
    "Una sola hoja: tus días barridos (plan, ejecución y revisión hechos), tu racha de días completos y 25 insignias ganadas por lo que haces: un primer plan, una semana perfecta, stops respetados. Qué hacer después: «Ahora», arriba en Hoy, siempre te lo dice.")),
 (None, "freezes", T("Streak freezes","Gels de streak","Congelaciones de racha"), T("A missed day doesn’t erase your streak","Une journée manquée n’efface pas ton streak","Un día perdido no borra tu racha"),
  T("A streak freeze covers one trading day you didn’t complete, so your streak goes on. You get 1 a week in Free, 2 in Pro and 3 in Elite. Sweep uses it for you and tells you.",
    "Un gel de streak couvre une journée de trading que tu n’as pas complétée : ton streak continue. Tu en as 1 par semaine en Free, 2 en Pro et 3 en Elite. Sweep l’utilise pour toi et te le dit.",
    "Una congelación de racha cubre un día de trading que no completaste: tu racha sigue. Tienes 1 por semana en Free, 2 en Pro y 3 en Elite. Sweep la usa por ti y te avisa.")),
 ("ecran-revue-semaine.webp", "weekly", T("Weekly recap","Bilan de la semaine","Resumen semanal"), T("Your week, every Friday","Ta semaine, chaque vendredi","Tu semana, cada viernes"),
  T("Once your Friday is closed (or at 5 p.m. New York time): your complete days, your discipline for the week, your swept days, your best habit, and one thing to aim for next week. Two minutes, then the week is behind you.",
    "Dès ta journée du vendredi fermée (ou à 17 h, heure de New York) : tes jours complets, ta discipline de la semaine, tes journées balayées, ta meilleure habitude et une chose à viser la semaine suivante. Deux minutes, puis la semaine est derrière toi.",
    "En cuanto cierras tu viernes (o a las 17 h, hora de Nueva York): tus días completos, tu disciplina de la semana, tus días barridos, tu mejor hábito y algo que buscar la próxima semana. Dos minutos, y la semana queda atrás.")),
]
GAME_INTRO = T("The traders who last aren’t the most gifted. They’re the most consistent. Sweep makes your consistency visible with three rings a day, a streak and badges, all earned through process. Never through profit.",
               "Les traders qui durent ne sont pas les plus doués. Ce sont les plus réguliers. Sweep rend ta régularité visible avec trois anneaux par jour, un streak et des badges, tous gagnés par le processus. Jamais par le profit.",
               "Los traders que duran no son los más talentosos. Son los más constantes. Sweep hace visible tu constancia con tres anillos al día, una racha e insignias, todo ganado con el proceso. Nunca con el beneficio.")
GAME_TITLE = T("Discipline you can see.","Ta discipline, visible.","Tu disciplina, a la vista.")

# ----------------------------------------------------------------- HOME
def page_home(lang, t):
    """Home, on the design system (ui.py, system.css)."""
    from pages16 import bar, TOTALS_MARK, sec_oneplace, sec_only, sec_story, sec_disc, sec_friday, sec_ai, sec_trust, sec_evalcost, sec_pricing, sec_rent, sec_faq, sec_next, sec_final, faq_ld
    from pages15 import IDENTITY
    reel = (f'<video class="hero-loop" muted loop playsinline preload="none" data-auto aria-label="{html.escape(t(T("Sweep in action: your day, a trade logged in seconds, your rules, every trade, payout ready, your progress","Sweep en action : ta journée, un trade ajouté en quelques secondes, tes règles, chaque trade, payout prêt, ta progression","Sweep en acción: tu día, una operación registrada en segundos, tus reglas, cada operación, payout listo, tu progreso")))}">'
            '<source src="/video/hero-loop-720.webm" type="video/webm" media="(max-width: 860px)"><source src="/video/hero-loop-720.mp4" type="video/mp4" media="(max-width: 860px)">'
            '<source src="/video/hero-loop.webm" type="video/webm"><source src="/video/hero-loop.mp4" type="video/mp4"></video>')
    hero = f'''<div class="hero"><div class="c">
{bar(lang,t)}
<h1><span class="h1-eyebrow rise">{t(T("Free trading journal for futures & prop firm traders","Journal de trading gratuit pour traders de futures et de prop firms","Diario de trading gratis para traders de futuros y prop firms"))}</span><span class="sr">{t(T(": "," : ",": "))}</span><span class="wu h1-promise">{words(t(T("Your edge, finally in one place.","Ton edge, enfin au même endroit.","Tu edge, por fin en un solo lugar.")),0.15)}</span></h1>
<p class="offer rise d2">{t(T("Free forever. Pro free for your first 30 days.","Gratuit pour toujours. Pro offert tes 30 premiers jours.","Gratis para siempre. Pro gratis tus primeros 30 días."))}</p>
<p class="lead rise d2">{t(T("Trades, prop accounts, payouts, expenses and daily habits. Everything you track in five different places, finally together.","Trades, comptes prop, payouts, dépenses et habitudes. Tout ce que tu suis à cinq endroits, enfin réuni.","Operaciones, cuentas prop, payouts, gastos y hábitos. Todo lo que hoy sigues en cinco lugares distintos, por fin junto."))}</p>
<div class="cta-row rise d3"><a class="btn btn-primary btn-lg" href="{SIGNUP}">{t(CREATE_FREE)}</a><button type="button" class="btn btn-line btn-lg" data-tour>{PLAY}{t(TOUR_LABEL)}</button></div>
<p class="reassure rise d4">{t(T("No card required\u00a0· Cancel anytime\u00a0· Your data, always exportable","Sans carte\u00a0· Annule quand tu veux\u00a0· Tes données, toujours exportables","Sin tarjeta\u00a0· Cancela cuando quieras\u00a0· Tus datos, siempre exportables"))}</p>
<div class="cohort rise d5" id="cohort" hidden><div class="cbar"><i></i></div><a href="{href(lang,'100')}" class="ctext num" data-tpl="{t(T("{n}/{total} founding traders","{n}/{total} traders fondateurs","{n}/{total} traders fundadores"))}"></a></div>
</div>
<div class="stage has-reel c c-wide"><div class="reel"><img class="vfb" src="/video/hero-loop-poster.webp" srcset="/video/hero-loop-poster-960.webp 960w, /video/hero-loop-poster.webp 1600w" sizes="(max-width: 1067px) 92vw, 1200px" width="1600" height="900" alt="" fetchpriority="high">{reel}
<button type="button" class="reel-play" data-tour><span class="rp-ic">{PLAY}</span><span class="rp-tx">{t(TOUR_LABEL)}</span><span class="rp-dur num">1:00</span></button></div>
<p class="hero-more"><a href="{href(lang,'import.html')}">{t(T("NinjaTrader 8 or Quantower? Your trades arrive on their own","NinjaTrader 8 ou Quantower ? Tes trades arrivent tout seuls","¿NinjaTrader 8 o Quantower? Tus operaciones llegan solas"))} <span aria-hidden="true">→</span></a></p></div></div>'''
    ld = jsonld({"@context":"https://schema.org","@graph":[
        {"@type":"SoftwareApplication","@id":f"https://{DOMAIN}/#app","name":"Sweep","alternateName":"Sweep trading journal","publisher":{"@id":f"https://{DOMAIN}/#org"},"applicationCategory":"FinanceApplication","operatingSystem":"Web","url":APP,
         "description":t(IDENTITY),"inLanguage":["en","fr","es"],
         "offers":[{"@type":"Offer","name":"Free","price":"0","priceCurrency":"USD"},{"@type":"Offer","name":"Pro","price":"19","priceCurrency":"USD"},{"@type":"Offer","name":"Elite","price":"39","priceCurrency":"USD"}]},
        faq_ld(t), tour_ld(t)]})
    body = (hero + TOTALS_MARK + sec_oneplace(lang,t) + sec_only(lang,t) + sec_story(lang,t) + sec_disc(lang,t) + sec_friday(lang,t) + sec_ai(lang,t)
            + sec_trust(lang,t) + sec_evalcost(lang,t) + sec_pricing(lang,t) + sec_rent(lang,t) + sec_faq(lang,t) + sec_next(lang,t) + sec_final(lang,t) + COHORT_JS + tour_dialog(t))
    return (t(T("Sweep — Trading Journal for Prop Firm Traders · Free","Sweep — Journal de trading pour prop firms · Gratuit","Sweep — Diario de trading para prop firms · Gratis")),
            t(T("Track every prop firm account, payout and expense in one place. Free forever, Pro from $19/mo. Built for Topstep, Apex, Lucid and more.","Suis chaque compte prop, payout et dépense au même endroit. Gratuit pour toujours, Pro dès 19 $/mois. Conçu pour Topstep, Apex, Lucid et plus.","Sigue cada cuenta prop, payout y gasto en un solo lugar. Gratis para siempre, Pro desde 19 $/mes. Hecho para Topstep, Apex, Lucid y más.")),
            body, ld)
SYSTEM_PAGES.add("index.html")

# ----------------------------------------------------------------- product tour video (lightbox)
TOUR_LABEL = T("Watch the 1-min tour","Voir la visite en 1 min","Ver el tour de 1 min")

def tour_ld(t):
    """The one-minute product tour, for search engines (VideoObject)."""
    return {"@type": "VideoObject", "name": t(T("Sweep in one minute", "Sweep en une minute", "Sweep en un minuto")),
            "description": t(T("A one-minute tour of Sweep: your day, a trade logged in seconds, your rules on every trade, your next payout and your progress.",
                               "La visite de Sweep en une minute : ta journée, un trade ajouté en quelques secondes, tes règles sur chaque trade, ton prochain payout et ta progression.",
                               "Sweep en un minuto: tu día, una operación registrada en segundos, tus reglas en cada operación, tu próximo payout y tu progreso.")),
            "thumbnailUrl": f"https://{DOMAIN}/video/tour-poster.webp", "uploadDate": "2026-10-21", "duration": "PT1M",
            "contentUrl": f"https://{DOMAIN}/video/tour.mp4"}
PLAY = '<svg class="play" width="14" height="14" viewBox="0 0 16 16" aria-hidden="true"><path d="M4.5 2.8v10.4a.6.6 0 0 0 .9.5l8.2-5.2a.6.6 0 0 0 0-1L5.4 2.3a.6.6 0 0 0-.9.5z" fill="currentColor"/></svg>'
def tour_dialog(t):
    return f'''<dialog class="tour-modal" id="tour" aria-label="{t(T("Sweep product tour","Visite de Sweep","Recorrido de Sweep"))}">
<button type="button" class="tour-close" data-close aria-label="{t(T("Close","Fermer","Cerrar"))}"><svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><path d="M3.5 3.5l9 9M12.5 3.5l-9 9"/></svg></button>
<div class="tour-frame"><video controls playsinline preload="none" data-poster="/video/tour-poster.webp" data-src-webm="/video/tour.webm" data-src-mp4="/video/tour.mp4" data-src-webm-sm="" data-src-mp4-sm="/video/tour-720.mp4"></video></div>
<p class="tour-note">{t(T("Sound on · Demo data","Avec le son · Données de démonstration · Titres en anglais","Con sonido · Datos de demostración · Títulos en inglés"))}</p></dialog>'''

def tour_card(lang, t):
    """The one-minute tour as a poster that opens it; the button sits bottom-right, clear of the poster's title."""
    return (f'<button type="button" class="tourcard reveal zoom" data-tour aria-label="{t(TOUR_LABEL)}"><img src="/video/tour-poster.webp" srcset="/video/tour-poster-960.webp 960w, /video/tour-poster.webp 1600w" '
            f'sizes="(max-width: 1067px) 92vw, 1200px" width="1600" height="900" alt="" fetchpriority="high"><span class="reel-play"><span class="rp-ic">{PLAY}</span><span class="rp-tx">{t(TOUR_LABEL)}</span><span class="rp-dur num">1:00</span></span></button>')

COHORT_JS = ("""<script>(function(){var b=document.getElementById('cohort');if(!window.fetch)return;fetch('https://app.makeitsweep.com/sweep-count.php',{credentials:'omit'}).then(function(r){return r.ok?r.json():Promise.reject();}).catch(function(){return fetch('https://app.makeitsweep.com/api/cohort-count.php',{credentials:'omit'}).then(function(r){return r.ok?r.json():Promise.reject();});}).then(function(d){if(!b)return;var n=Math.max(parseInt(d.taken,10)||0,__FLOOR__),tt=parseInt(d.total,10);if(!(tt>0)||!(n>=1)||n>=tt)return;var a=b.querySelector('.ctext'),tp=a.getAttribute('data-tpl').replace('{total}',tt),fin=tp.replace('{n}',n);document.querySelectorAll('.cp-n').forEach(function(x){x.textContent=n+'/'+tt;});b.hidden=false;var bi=b.querySelector('.cbar i');requestAnimationFrame(function(){requestAnimationFrame(function(){bi.style.setProperty('--c',Math.max(.02,n/tt));});});if(window.sweepRoll)window.sweepRoll(a,fin,tp.replace('{n}','0'));else a.textContent=fin;}).catch(function(){});})();</script>""").replace('__FLOOR__', str(COHORT_FLOOR))

# ----------------------------------------------------------------- HOW IT WORKS (+ discipline & social)
def page_how(lang, t):
    """How it works, on the design system: the tour as the hero's visual, the five steps in one row, the game in even rows."""
    import ui
    anchors = [("start",T("Getting started","Démarrer","Empezar")),("sweep-the-day",T("Sweep your day","Balaye ta journée","Barre tu día")),("discipline",T("Discipline","Discipline","Disciplina"))]
    st = [("signup-split", None, T("Create your account","Crée ton compte","Crea tu cuenta"), T("A username, an email and a password. Free forever, with Pro included for your first 30 days. No credit card.","Un nom d’utilisateur, un courriel et un mot de passe. Gratuit pour toujours, avec Pro offert pendant tes 30 premiers jours. Sans carte de crédit.","Un usuario, un correo y una contraseña. Gratis para siempre, con Pro incluido tus primeros 30 días. Sin tarjeta.")),
          ("ecran-comptes-prop.webp", "accounts", T("Add your accounts","Ajoute tes comptes","Añade tus cuentas"), T("Your first name, then your prop firm and account size: the rules are prefilled, for guidance only. Or set up a personal account.","Ton prénom, puis ta prop firm et la taille du compte : les règles sont préremplies, à titre indicatif. Ou configure un compte personnel.","Tu nombre, luego tu prop firm y el tamaño de la cuenta: las reglas vienen precargadas, a título indicativo. O configura una cuenta personal.")),
          ("ecran-plan-du-jour.webp", "plan", T("Confirm your plan","Confirme ton plan","Confirma tu plan"), T("Your daily plan is prefilled from your account, max loss included: you only confirm it. Your coach follows it all session.","Ton plan du jour est prérempli à partir de ton compte, perte max comprise : tu n’as qu’à le confirmer. Ton coach le suit pendant toute la séance.","Tu plan del día viene precargado a partir de tu cuenta, pérdida máxima incluida: solo tienes que confirmarlo. Tu coach lo sigue toda la sesión.")),
          ("v6-video-log-by-screenshot.mp4", "new-trade", T("Log a trade in seconds","Ajoute un trade en quelques secondes","Registra una operación en segundos"), T("Paste a screenshot of your platform and Sweep AI fills the trade, or enter it by hand. Your coach tells you what was right and what to fix.","Colle une capture de ta plateforme et Sweep AI remplit le trade, ou ajoute-le à la main. Ton coach te dit ce qui était bien et quoi corriger.","Pega una captura de tu plataforma y Sweep AI completa la operación, o añádela a mano. Tu coach te dice lo que estuvo bien y qué corregir.")),
          ("ecran-apercu-anneaux.webp", "overview", T("Close your three rings","Ferme tes trois anneaux","Cierra tus tres anillos"), T("Plan, execution, review. Close all three and your day is swept.","Plan, exécution, revue. Ferme les trois et ta journée est balayée.","Plan, ejecución, revisión. Cierra los tres y tu día queda barrido."))]
    shots = ["v6-20-signup-m.webp", "v6-13-accounts-m.webp", "ecran-plan-du-jour.webp", "v6-03-log-by-screenshot-m.webp", "v6-22-today-swept-m.webp"]
    steps = ui.sec(ui.cards([ui.card_media(t, h, p, ui.phone_img(f"/img/captures/{shots[i]}", t(h), "50% 36%" if shots[i].startswith("ecran-plan") else "50% 0%"), crop=True, kick=T(f"0{i + 1}", f"0{i + 1}", f"0{i + 1}"))
                             for i, (_, _, h, p) in enumerate(st)], 5, cls="stagger steps5"), "t", "start")
    # a new trader's first weeks: one discovery mission per trading day (app, 29 Oct.)
    discover = ui.split(t, T("Your first weeks","Tes premières semaines","Tus primeras semanas"), T("One discovery mission a day.","Une mission de découverte par jour.","Una misión de descubrimiento al día."),
        T("New traders get 15 short missions, one per trading day, each ticked by what you do, with a “Do it now” button. My money, the guided plan, Sweep AI and your badges show up at their mission; “Show everything” opens them all at once. With the 90-day gameplan (Pro), its mission of the day takes that line.",
          "Un nouveau trader reçoit 15 courtes missions, une par jour de trading, cochées par ce que tu fais, avec un bouton « Faire maintenant ». Mon argent, le plan guidé, Sweep AI et tes badges arrivent à leur mission ; « Tout montrer » les ouvre tous d’un coup. Avec le parcours de 90 jours (Pro), c’est sa mission du jour qui prend cette ligne.",
          "Un trader nuevo recibe 15 misiones cortas, una por día de trading, marcadas por lo que haces, con un botón «Hacerlo ahora». Mi dinero, el plan guiado, Sweep AI y tus insignias aparecen en su misión; «Mostrar todo» los abre todos a la vez. Con el recorrido de 90 días (Pro), es su misión del día la que ocupa esa línea."),
        [], ui.frame_p("ecran-missions-decouverte.webp", t(T("Today: the day’s mission, one line under “Now”, sample data","Aujourd’hui : la mission du jour, une ligne sous « Maintenant », données d’exemple","Hoy: la misión del día, una línea bajo «Ahora», datos de ejemplo")), t=t),
        flip=True, id_="discovery", phone=True)
    G = {g[1]: g for g in GAME}
    POS = {"progression": "50% 30%", "weekly": "50% 14%"}
    def gcard(aid):
        img, _, k, h, p = G[aid]
        return ui.card_media(t, h, p, ui.phone_img(f"/img/captures/{img}", t(h), POS[aid]), crop=True, kick=k, id_=aid)
    _, _, fk, fh, fp = G["freezes"]
    disc = ui.sec(ui.head(t, T("Discipline","Discipline","Disciplina"), GAME_TITLE, GAME_INTRO)
                  + ui.cards([gcard(a) for a in ("progression", "weekly")], 2) + ui.cards([ui.card(t, fh, fp, kick=fk, id_="freezes")], 1)
                  + f'<p class="fine" style="margin-top:40px">{t(T("Badges are earned through process only. They have no cash value.","Les badges se gagnent uniquement par le processus. Ils n’ont aucune valeur monétaire.","Las insignias se ganan solo con el proceso. No tienen valor monetario."))}</p>', "n", "discipline")
    hero = ui.hero(t, T("How it works","Comment ça marche","Cómo funciona"), T("How Sweep works","Comment ça marche","Cómo funciona Sweep"),
                   T("Build the habits. Find the edge. Get paid.","Bâtis les habitudes. Trouve ton edge. Fais-toi payer.","Crea los hábitos. Encuentra tu edge. Cobra."),
                   cta=ui.btn(t(CREATE_FREE), SIGNUP, lg=True), visual=tour_card(lang, t))
    ld = jsonld({"@context":"https://schema.org","@graph":[{"@type":"HowTo","name":t(T("How to start with Sweep","Comment commencer avec Sweep","Cómo empezar con Sweep")),
        "step":[{"@type":"HowToStep","position":i+1,"name":t(h),"text":t(p)} for i,(_,_,h,p) in enumerate(st)]}, tour_ld(t)]})
    return (t(T("How Sweep Works: Trading Journal in 5 Steps · Sweep","Comment fonctionne Sweep : le journal de trading en 5 étapes","Cómo funciona Sweep: el diario de trading en 5 pasos · Sweep")),   # its 5 steps (SEO brief v2, 2.6)
            t(T("Create an account, add your prop accounts, log a trade from a screenshot, close your three rings, then keep your streak going with missions, badges and a weekly recap.",
                "Crée un compte, ajoute tes comptes prop, ajoute un trade depuis une capture, ferme tes trois anneaux, puis garde ton streak avec les missions, les badges et le bilan de la semaine.",
                "Crea una cuenta, añade tus cuentas prop, registra una operación desde una captura, cierra tus tres anillos y mantén tu racha con misiones, insignias y el resumen semanal.")),
            hero + ui.subnav(t, T("How it works","Comment ça marche","Cómo funciona"), anchors) + steps + discover + sec_sweep_day(lang, t) + disc
            + ui.read_next(lang, t, ["features.html", "prop-firm-tracker.html", "pricing.html"]) + ui.final(lang, t) + tour_dialog(t), ld)
SYSTEM_PAGES.add("how-it-works.html")

# ----------------------------------------------------------------- PRICING

def page_pricing(lang, t):
    """Pricing, on the design system (the billing switch and the plans deck keep their site.js hooks).
    Built for conversion (Mateo, Oct 18, carte blanche): concrete limits instead of « more / the most », one reason per plan,
    the three moments a trader outgrows Free said plainly (accounts, real net, history), the game kept but grouped last.
    Limits are the app's (billing config: Free 2 accounts, 30 days, 3 AI messages and 3 screenshots a day; Pro unlimited accounts,
    50 messages, 3 AI reviews a month; Elite 200 messages, every trade reviewed, weekly report, full calendar notes)."""
    import ui
    from pages2 import FAQ
    Y = '<span class="yes" aria-label="✓">✓</span>'; N = '<span class="no" aria-label="—">—</span>'
    lim = lambda a,b,c: (t(a),t(b),t(c))
    UNL = T("Unlimited","Illimité","Ilimitado")
    grp = lambda x: (x, None, None, None)
    rows = [
     grp(T("Your accounts and data","Tes comptes et tes données","Tus cuentas y tus datos")),
     (T("Prop accounts, with their firm’s rules","Comptes prop, avec les règles de leur firme","Cuentas prop, con las reglas de su firma"),"2",t(UNL),t(UNL)),
     (T("Stats history","Historique des stats","Historial de estadísticas"),*lim(T("Last 30 days","30 derniers jours","Últimos 30 días"),T("Complete","Complet","Completo"),T("Complete","Complet","Completo"))),
     (T("My money: payouts, expenses and real net","Mon argent : payouts, dépenses et vrai net","Mi dinero: payouts, gastos y neto real"),N,Y,Y),
     (T("Imports, NinjaTrader 8 and Quantower sync","Imports, synchro NinjaTrader 8 et Quantower","Importaciones, sincronización con NinjaTrader 8 y Quantower"),Y,Y,Y),
     (T("Journal, calendar, economic calendar","Journal, calendrier, calendrier économique","Diario, calendario, calendario económico"),Y,Y,Y),
     (T("Real CME charts","Vrais graphiques CME","Gráficos reales de CME"),Y,Y,Y),
     (T("Full export","Export complet","Exportación completa"),Y,Y,Y),
     grp(T("Coach and AI","Coach et IA","Coach e IA")),
     (T("Your coach and your edge, on every trade","Ton coach et ton edge, sur chaque trade","Tu coach y tu edge, en cada operación"),Y,Y,Y),
     (T("The 90-day gameplan, a mission a day","Le parcours de 90 jours, une mission par jour","El recorrido de 90 días, una misión al día"),N,Y,Y),
     (T("Sweep AI messages","Messages Sweep AI","Mensajes de Sweep AI"),*lim(T("3 a day","3 par jour","3 al día"),T("50 a day","50 par jour","50 al día"),T("200 a day","200 par jour","200 al día"))),
     (T("Trades read from a screenshot","Trades lus depuis une capture","Operaciones leídas desde una captura"),t(T("3 a day","3 par jour","3 al día")),t(UNL),t(UNL)),
     (T("AI trade reviews","Avis IA sur un trade","Opiniones de IA sobre una operación"),N,t(T("3 a month","3 par mois","3 al mes")),t(T("Every trade","Chaque trade","Cada operación"))),
     (T("Economic calendar notes","Notes du calendrier économique","Notas del calendario económico"),*lim(T("Headlines","Titres","Titulares"),T("Headlines","Titres","Titulares"),T("Full notes","Notes complètes","Notas completas"))),
     (T("Weekly AI report","Rapport IA de la semaine","Informe semanal de IA"),N,N,Y),
     (T("Priority support","Soutien prioritaire","Soporte prioritario"),N,N,Y),
     grp(T("The routine","La routine","La rutina")),
     (T("Rings, swept days, streak, badges","Anneaux, journées balayées, streak, badges","Anillos, días barridos, racha, insignias"),Y,Y,Y),
     (T("Discovery missions and weekly recap","Missions de découverte et bilan de la semaine","Misiones de descubrimiento y resumen semanal"),Y,Y,Y),
     (T("Streak freezes per week","Gels de streak / semaine","Congelaciones de racha / semana"),"1","2","3")]
    body = "".join(f'<tr class="grp" role="row"><th scope="colgroup" colspan="4" role="columnheader">{t(a)}</th></tr>' if b is None else
                   f'<tr role="row"><th scope="row" role="rowheader">{t(a)}</th><td role="cell">{b}</td><td role="cell">{c}</td><td role="cell">{d}</td></tr>' for a,b,c,d in rows)
    def pblock(plan):
        if plan == "free":
            return f'<div class="price"><span class="num">{money(t,0)}</span></div><p class="per muted">{t(T("forever","pour toujours","para siempre"))}</p>'
        m, y = PRICES[plan]["m"], PRICES[plan]["y"]
        ym = money(t, round(y/12, 2)); mm = money(t, m); yy = money(t, y); sv = money(t, m * 12 - y)
        by = t(T(f"billed {yy} a year · you save {sv}",f"facturé {yy} par année · {sv} d’économie",f"facturado {yy} al año · ahorras {sv}"))
        bm = t(T("billed monthly","facturé chaque mois","facturado mensualmente"))
        nb = lambda x: nbsp(lang, x)   # the values swapped in by site.js keep the page's typography (« 19 $ », « 30 % »)
        was = f'<s class="was" data-m="" data-y="{nb(mm)}"><span class="sr">{t(T("instead of","au lieu de","en lugar de"))} </span>{mm}</s>'   # the monthly price, struck, beside the yearly one
        return f'<div class="price">{was}<span class="num" data-m="{nb(mm)}" data-y="{nb(ym)}">{ym}</span><span class="muted">/{t(T("mo","mois","mes"))}</span></div><p class="per muted" data-m="{nb(bm)}" data-y="{nb(by)}">{by}</p>'
    feats = {
     "free":[T("2 prop accounts, with their firm’s rules","2 comptes prop, avec les règles de leur firme","2 cuentas prop, con las reglas de su firma"),
             T("Your coach and your edge, on every trade","Ton coach et ton edge, sur chaque trade","Tu coach y tu edge, en cada operación"),
             T("Stats on your last 30 days","Tes stats des 30 derniers jours","Tus estadísticas de los últimos 30 días"),
             T("Real CME charts, imports, NinjaTrader 8 and Quantower sync","Vrais graphiques CME, imports, synchro NinjaTrader 8 et Quantower","Gráficos reales de CME, importaciones, sincronización con NinjaTrader 8 y Quantower"),
             T("Sweep AI: 3 messages and 3 screenshots a day","Sweep AI : 3 messages et 3 captures par jour","Sweep AI: 3 mensajes y 3 capturas al día"),
             T("Rings, streak, badges and a weekly recap","Anneaux, streak, badges et bilan de la semaine","Anillos, racha, insignias y resumen semanal")],
     "pro":[T("Everything in Free, plus:","Tout Free, plus :","Todo lo de Free, más:"),
            T("<b>Unlimited prop accounts</b>","<b>Comptes prop illimités</b>","<b>Cuentas prop ilimitadas</b>"),
            T("<b>My money:</b> payouts, expenses and your real net","<b>Mon argent :</b> payouts, dépenses et ton vrai net","<b>Mi dinero:</b> payouts, gastos y tu neto real"),
            T("<b>Your whole history</b> in your stats","<b>Tout ton historique</b> dans tes stats","<b>Todo tu historial</b> en tus estadísticas"),
            T("Sweep AI: 50 messages a day, unlimited screenshots, 3 trade reviews a month","Sweep AI : 50 messages par jour, captures illimitées, 3 avis sur un trade par mois","Sweep AI: 50 mensajes al día, capturas ilimitadas, 3 opiniones sobre una operación al mes"),
            T("<b>The 90-day gameplan</b> for traders starting out","<b>Le parcours de 90 jours</b> pour les traders qui débutent","<b>El recorrido de 90 días</b> para traders que empiezan"),
            T("2 streak freezes a week","2 gels de streak par semaine","2 congelaciones de racha por semana")],
     "elite":[T("Everything in Pro, plus:","Tout Pro, plus :","Todo lo de Pro, más:"),
              T("<b>An AI review on every trade</b>","<b>Un avis de l’IA sur chaque trade</b>","<b>Una opinión de la IA en cada operación</b>"),
              T("<b>A weekly AI report</b> on your edge, your leaks and your habits","<b>Un rapport IA chaque semaine</b> sur ton edge, tes fuites et tes habitudes","<b>Un informe de IA cada semana</b> sobre tu edge, tus fugas y tus hábitos"),
              T("<b>Full AI notes</b> before and after every economic release","<b>Les notes IA complètes</b> avant et après chaque annonce économique","<b>Las notas de IA completas</b> antes y después de cada dato económico"),
              T("200 AI messages a day and priority support","200 messages IA par jour et soutien prioritaire","200 mensajes de IA al día y soporte prioritario"),
              T("3 streak freezes a week","3 gels de streak par semaine","3 congelaciones de racha por semana")]}
    def card(name, plan, tagline, btn, cls, badge=""):
        link = f"{SIGNUP}&plan={plan}" + ("" if plan == "free" else "&interval=year")
        plist = '<ul class="list">' + "".join(f"<li data-nolinks>{t(x)}</li>" for x in feats[plan]) + "</ul>"   # no glossary or page links inside a plan: the button is the way out
        return f'<div class="plan {cls} reveal">{badge}<h2>{name}</h2><p class="tagline">{t(tagline)}</p>{pblock(plan)}{plist}<a class="btn {"btn-primary" if cls=="main" else "btn-line"} btn-lg" href="{link}" data-plan="{plan}">{t(btn)}</a></div>'
    hero = ui.hero(t, T("Pricing","Tarifs","Precios"), T("Start with everything. Keep what you need.","Commence avec tout. Garde ce qu’il te faut.","Empieza con todo. Quédate con lo que necesitas."),
                   T("Every new trader gets 30 days of Pro, no card. Then Free stays free forever, or keep Pro when you run several prop accounts. Pro $19/mo or $159/yr, Elite $39/mo or $329/yr, before tax.","Chaque nouveau trader reçoit 30 jours de Pro, sans carte. Ensuite, Free reste gratuit pour toujours, ou garde Pro quand tu gères plusieurs comptes prop. Pro 19 $/mois ou 159 $/an, Elite 39 $/mois ou 329 $/an, avant taxes.","Cada trader nuevo recibe 30 días de Pro, sin tarjeta. Después, Free sigue gratis para siempre, o quédate con Pro cuando lleves varias cuentas prop. Pro 19 $/mes o 159 $/año, Elite 39 $/mes o 329 $/año, antes de impuestos."), cta=ui.btn(t(CREATE_FREE), SIGNUP, lg=True))
    cards = f'''<div class="billing" data-k="y" role="group" aria-label="{t(T("Billing period","Période de facturation","Periodo de facturación"))}"><button type="button" data-bill="m" aria-pressed="false">{t(T("Monthly","Mensuel","Mensual"))}</button><button type="button" data-bill="y" aria-pressed="true">{t(T("Yearly","Annuel","Anual"))} <span class="save">{t(T("Save 30%","Économise 30 %","Ahorra 30 %"))}</span></button></div>
<div class="plans three" id="plans">
{card("Free","free",T("To build the habit on your first accounts.","Pour bâtir l’habitude sur tes premiers comptes.","Para crear el hábito con tus primeras cuentas."),T("Start on Free","Commencer avec Free","Empezar con Free"),"")}
{card("Pro","pro",T("For traders running several prop accounts. Included for your first 30 days.","Pour les traders qui gèrent plusieurs comptes prop. Offert pendant tes 30 premiers jours.","Para traders con varias cuentas prop. Incluido tus primeros 30 días."),T("Start my 30 days of Pro","Commencer mes 30 jours de Pro","Empezar mis 30 días de Pro"),"main",f'<span class="badge">{t(T("30 days included","30 jours offerts","30 días incluidos"))}</span>')}
{card("Elite","elite",T("For an AI review on every trade and a report every week.","Pour un avis de l’IA sur chaque trade et un rapport chaque semaine.","Para una opinión de la IA en cada operación y un informe cada semana."),T("Choose Elite","Choisir Elite","Elegir Elite"),"")}
</div><div class="dots plan-dots" aria-hidden="true"><i></i><i></i><i></i></div>
<ul class="under">{"".join(f"<li>{t(x)}</li>" for x in [T("No card for your 30 days of Pro. At the end, you move to Free on your own, unless you choose a plan.","Aucune carte pour tes 30 jours de Pro. À la fin, tu passes à Free tout seul, sauf si tu choisis un forfait.","Sin tarjeta durante tus 30 días de Pro. Al final, pasas a Free solo, salvo que elijas un plan."),T("Cancel anytime: your data is never deleted.","Annule quand tu veux : tes données ne sont jamais supprimées.","Cancela cuando quieras: tus datos nunca se eliminan."),T("Prices in USD, before taxes. Secure payment by Stripe. No refunds on periods already started.","Prix en USD, avant taxes. Paiement sécurisé par Stripe. Aucun remboursement sur les périodes entamées.","Precios en USD, antes de impuestos. Pago seguro con Stripe. Sin reembolsos en periodos ya iniciados.")])}</ul>'''
    b = ui.sec(cards, "t", "plans-sec")
    why = [ui.card(t, T("Every account, in one place","Tous tes comptes, au même endroit","Todas tus cuentas, en un solo lugar"),
                   T("Free follows 2 accounts. When you scale, Pro follows all of them, each with its firm’s rules.","Free suit 2 comptes. Quand tu grandis, Pro les suit tous, chacun avec les règles de sa firme.","Free sigue 2 cuentas. Cuando creces, Pro las sigue todas, cada una con las reglas de su firma."), "layers"),
           ui.card(t, T("Your real net","Ton vrai net","Tu neto real"),
                   T("Payouts in; evaluations, resets and fees out. My money shows what trading really pays you.","Les payouts d’un côté ; les évaluations, les resets et les frais de l’autre. Mon argent montre ce que le trading te rapporte vraiment.","Los payouts por un lado; evaluaciones, resets y comisiones por el otro. Mi dinero muestra lo que el trading te paga de verdad."), "net"),
           ui.card(t, T("Your whole track record","Tout ton historique","Todo tu historial"),
                   T("Free shows your last 30 days. Every older trade stays saved, and Pro puts it back in your stats.","Free montre tes 30 derniers jours. Chaque trade plus ancien reste gardé, et Pro le remet dans tes stats.","Free muestra tus últimos 30 días. Cada operación más antigua queda guardada, y Pro la vuelve a poner en tus estadísticas."), "calendar")]
    b += ui.sec(ui.head(t, None, T("Why traders move to Pro","Pourquoi les traders passent à Pro","Por qué los traders pasan a Pro")) + ui.cards(why, 3), "t", "why")
    cmp = f'<div class="cmp-wrap"><table class="cmp" role="table"><thead role="rowgroup"><tr role="row"><th scope="col" role="columnheader"><span class="sr">{t(T("Feature","Fonctionnalité","Función"))}</span></th><th scope="col" role="columnheader">Free</th><th scope="col" role="columnheader" class="hl">Pro</th><th scope="col" role="columnheader">Elite</th></tr></thead><tbody role="rowgroup">{body}</tbody></table></div>'
    refer = f'''<div class="refer reveal">{ico(I["spark"])}<div><h3>{t(T("Invite a friend","Invite un ami","Invita a un amigo"))}</h3><p>{t(T("They get 14 days of Elite on top of their 30 days of Pro, and you get a free month as soon as they use Sweep for real (10 trades on 3 different days, or a paid plan). Up to 12 free months a year.","Il reçoit 14 jours d’Elite en plus de ses 30 jours de Pro, et toi un mois gratuit dès qu’il utilise Sweep pour vrai (10 trades sur 3 jours différents, ou un forfait payant). Jusqu’à 12 mois offerts par année.","Recibe 14 días de Elite además de sus 30 días de Pro, y tú un mes gratis en cuanto use Sweep de verdad (10 operaciones en 3 días distintos, o un plan de pago). Hasta 12 meses gratis al año."))}</p></div></div>'''
    b += ui.sec(ui.head(t, None, T("Compare plans","Compare les forfaits","Compara los planes")) + cmp + f'<div class="offers">{refer}</div>', "n", "compare")
    change = (T("Can I change plans or cancel anytime?","Puis-je changer de forfait ou annuler en tout temps ?","¿Puedo cambiar de plan o cancelar cuando quiera?"),
              T("Yes, from your plan in Sweep. A paid plan runs to the end of the period you paid, then you move to Free with all your data kept.","Oui, depuis ton forfait dans Sweep. Un forfait payé va jusqu’à la fin de la période réglée, puis tu passes à Free avec toutes tes données gardées.","Sí, desde tu plan en Sweep. Un plan pagado dura hasta el final del periodo abonado y luego pasas a Free con todos tus datos guardados."))
    pf = [FAQ[0][1][0], FAQ[0][1][1], change, FAQ[0][1][2], FAQ[0][1][6]]
    b += ui.sec(ui.head(t, None, T("Pricing questions","Questions sur les tarifs","Preguntas sobre precios")) + ui.qa(t, pf)
                + f'<p style="margin-top:24px">{ui.go(lang, t, "faq.html", T("Every other question, in the FAQ", "Toutes les autres questions, dans la FAQ", "Todas las demás preguntas, en las preguntas frecuentes"))}</p>', "n", "faq", width="read")
    offers = [{"@type":"Offer","name":n,"price":str(p),"priceCurrency":"USD"} for n,p in (("Free",0),(t(T("Pro monthly","Pro mensuel","Pro mensual")),19),(t(T("Pro yearly","Pro annuel","Pro anual")),159),(t(T("Elite monthly","Elite mensuel","Elite mensual")),39),(t(T("Elite yearly","Elite annuel","Elite anual")),329))]
    ld = jsonld({"@context":"https://schema.org","@graph":[{"@type":"SoftwareApplication","@id":f"https://{DOMAIN}/#app","name":"Sweep","applicationCategory":"FinanceApplication","operatingSystem":"Web","offers":offers,"publisher":{"@id":f"https://{DOMAIN}/#org"}},
          {"@type":"FAQPage","mainEntity":[{"@type":"Question","name":t(q),"acceptedAnswer":{"@type":"Answer","text":re.sub(r"<[^>]+>", "", t(a))}} for q,a in pf]}]})
    return (t(T("Pricing · Free forever, Pro included for 30 days · Sweep","Tarifs · Gratuit pour toujours, Pro offert 30 jours · Sweep","Precios · Gratis para siempre, Pro incluido 30 días · Sweep")),
            t(T("Free forever with 2 prop accounts. Pro, with unlimited accounts and your real net, is included for 30 days. Pro $19/mo or $159/yr, Elite $39/mo or $329/yr.","Gratuit pour toujours avec 2 comptes prop. Pro, comptes illimités et vrai net, offert 30 jours. Pro 19 $/mois ou 159 $/an, Elite 39 $/mois ou 329 $/an.","Gratis para siempre con 2 cuentas prop. Pro, cuentas ilimitadas y neto real, incluido 30 días. Pro 19 $/mes o 159 $/año, Elite 39 $/mes o 329 $/año.")),
            hero + b + ui.read_next(lang, t, ["free-trading-journal.html", "features.html", "best-trading-journal-for-prop-firms.html"]) + ui.final(lang, t), ld)
SYSTEM_PAGES.add("pricing.html")
