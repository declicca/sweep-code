from core import *
CAPTURES['ecran-apercu-anneaux.webp'] = ('phone', 1179, 2556, 'Today card with the three rings and shortcuts (hero)')
from pages4 import money, PRICES

START = T("Start for free","Commencer gratuitement","Empieza gratis")
FREE_LINE = T("Free forever. Pro included for 60 days.","Gratuit pour toujours. Pro offert pendant 60 jours.","Gratis para siempre. Pro incluido durante 60 días.")
CONFIDENCE = T("Private by default. Your P&L is never shared. Export or delete your data whenever you want.",
               "Privé par défaut. Jamais de P&L partagé. Exporte ou supprime tes données quand tu veux.",
               "Privado por defecto. Tu P&L nunca se comparte. Exporta o elimina tus datos cuando quieras.")
CONTRACTS14 = "NQ MNQ ES MES YM MYM RTY M2K CL MCL GC MGC SI 6E".split()
CHART_NOTE = T("Charts available 24 hours after the session. CME market data. Charts powered by TradingView Lightweight Charts™.",
               "Graphiques disponibles 24 h après la séance. Données de marché CME. Graphiques propulsés par TradingView Lightweight Charts™.",
               "Gráficos disponibles 24 h después de la sesión. Datos de mercado de CME. Gráficos impulsados por TradingView Lightweight Charts™.")
PROP_NOTE = T("Rules prefilled for guidance only. Always check your firm’s current rules.",
              "Règles préremplies à titre indicatif. Vérifie toujours les règles actuelles de ta firme.",
              "Reglas precargadas solo a título indicativo. Verifica siempre las reglas actuales de tu firma.")
CHECK = '<svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 8.5l3 3 7-7"/></svg>'
def chips14(): return '<div class="chips">' + "".join(f"<span>{c}</span>" for c in CONTRACTS14) + "</div>"
def note(t, d): return f'<p class="fine">{t(d)}</p>'

# ----------------------------------------------------------------- sections reused on several pages
def sec_sweep_day(lang, t, id_="sweep-the-day", rule=True):
    return split(t, T("The daily loop","La boucle quotidienne","El ciclo diario"), T("Sweep your day.","Balaye ta journée.","Barre tu día."),
      T("Three rings every market day: plan before the open, trade by your rules, review after the session. Close all three and your day is swept, and your discipline streak moves forward. Streak freezes protect your runs, and weekends never count against you.",
        "Trois anneaux chaque jour de marché : planifier avant l’ouverture, trader selon tes règles, réviser après la séance. Ferme les trois et ta journée est balayée : ton streak de discipline avance. Les gels de streak protègent tes séries, et le week-end ne compte jamais contre toi.",
        "Tres anillos cada día de mercado: planificar antes de la apertura, operar según tus reglas, revisar tras la sesión. Cierra los tres y tu día queda barrido: tu racha de disciplina avanza. Las congelaciones protegen tus series y los fines de semana nunca cuentan en tu contra."),
      [T("<b>Daily plan in 2 minutes:</b> bias, levels, scenario, max loss","<b>Plan du jour en 2 minutes :</b> biais, niveaux, scénario, perte max","<b>Plan del día en 2 minutos:</b> sesgo, niveles, escenario, pérdida máxima"),
       T("<b>Execution</b> measured by your own discipline checklist (5 questions)","<b>Exécution</b> mesurée par ta propre checklist de discipline (5 questions)","<b>Ejecución</b> medida con tu propio checklist de disciplina (5 preguntas)"),
       T("<b>Review in 60 seconds,</b> without leaving the Overview","<b>Revue en 60 secondes,</b> sans quitter l’Aperçu","<b>Revisión en 60 segundos,</b> sin salir del Resumen"),
       T("<b>Discipline streak</b> plus freezes: 1 on Free, 2 on Pro, 3 on Elite per week","<b>Streak de discipline</b> et gels : 1 en Free, 2 en Pro, 3 en Elite par semaine","<b>Racha de disciplina</b> y congelaciones: 1 en Free, 2 en Pro, 3 en Elite por semana"),
       T("<b>Guardrail:</b> if you go past your max daily loss, Sweep tells you, without judgment","<b>Garde-fou :</b> si tu dépasses ta perte max du jour, Sweep te le dit, sans jugement","<b>Salvaguarda:</b> si superas tu pérdida máxima del día, Sweep te lo dice, sin juzgarte")],
      slot("video-journee-balayee.mp4","phone",t(T("Today card with the three rings closing","Carte Aujourd’hui avec les trois anneaux qui se ferment","Tarjeta Hoy con los tres anillos cerrándose")),t,fallback="overview",video=True,poster="ecran-journee-balayee.webp"),
      id_=id_, rule=rule)

def sec_charts(lang, t, id_="charts", flip=True):
    return split(t, T("Real charts","Graphiques réels","Gráficos reales"), T("Your trades on real charts.","Tes trades sur de vrais graphiques.","Tus operaciones en gráficos reales."),
      T("See every trade where it happened, on real CME candles: entry, exit, stop, target and your position zone. Charts are ready the day after the session.",
        "Vois chaque trade là où il s’est passé, sur les vraies bougies du CME : entrée, sortie, stop, objectif et zone de position. Les graphiques sont prêts le lendemain de la séance.",
        "Mira cada operación donde ocurrió, sobre velas reales de CME: entrada, salida, stop, objetivo y zona de posición. Los gráficos están listos al día siguiente de la sesión."),
      [T("<b>CME market data:</b> 14 contracts, from NQ to 6E","<b>Données de marché CME :</b> 14 contrats, de NQ à 6E","<b>Datos de mercado de CME:</b> 14 contratos, de NQ a 6E"),
       T("<b>Timeframes</b> 15 s, 30 s, 1 m, 5 m, 15 m, 1 h","<b>Unités de temps</b> 15 s, 30 s, 1 m, 5 m, 15 m, 1 h","<b>Temporalidades</b> 15 s, 30 s, 1 m, 5 m, 15 m, 1 h"),
       T("<b>Result in R</b> on the chart, shareable capture in one click","<b>Résultat en R</b> affiché sur le graphique, capture partageable en un clic","<b>Resultado en R</b> en el gráfico, captura para compartir en un clic"),
       T("<b>Full screen,</b> pinch to zoom, light and dark mode","<b>Plein écran,</b> zoom au pincement, mode clair et foncé","<b>Pantalla completa,</b> zoom con pellizco, modo claro y oscuro")],
      slot("ecran-graphique-trade.webp","desktop",t(T("Trade recap on a real NQ chart with the position zone and the result in R","Récap d’un trade NQ sur vrai graphique avec la zone de position et le résultat en R","Resumen de una operación NQ en gráfico real con la zona de posición y el resultado en R")),t),
      flip=flip, id_=id_, more=f'<div style="margin-top:26px">{chips14()}</div>{note(t,CHART_NOTE)}')

def sec_prop(lang, t, id_="prop", flip=False, link=True, title=None):
    m = f'<div class="cta-row"><a class="btn btn-line" href="{href(lang,"prop-traders.html")}">{t(T("Sweep for prop traders","Sweep pour les traders prop","Sweep para traders prop"))}</a></div>' if link else ""
    return split(t, T("Prop firms","Prop firms","Prop firms"), title or T("Built for prop firm traders.","Construit pour les traders de prop firms.","Hecho para traders de prop firms."),
      T("Pick your firm and account size: Topstep, Apex Trader Funding, Take Profit Trader, Lucid Trading or MyFundedFutures. Target, drawdown, daily loss, consistency and minimum days fill in by themselves. Sweep watches every rule and tells you when you’re ready for the payout.",
        "Choisis ta firme et la taille du compte : Topstep, Apex Trader Funding, Take Profit Trader, Lucid Trading ou MyFundedFutures. Objectif, drawdown, perte quotidienne, consistance et jours minimum se remplissent seuls. Sweep surveille chaque règle et te dit quand tu es prêt pour le payout.",
        "Elige tu firma y el tamaño de la cuenta: Topstep, Apex Trader Funding, Take Profit Trader, Lucid Trading o MyFundedFutures. Objetivo, drawdown, pérdida diaria, consistencia y días mínimos se completan solos. Sweep vigila cada regla y te dice cuándo estás listo para el payout."),
      [T("<b>Rule presets</b> by firm and account size (25K to 150K)","<b>Préréglages de règles</b> par firme et par taille de compte (25K à 150K)","<b>Reglas predefinidas</b> por firma y tamaño de cuenta (25K a 150K)"),
       T("<b>Copy a trade</b> to several accounts at once","<b>Copier un trade</b> sur plusieurs comptes en même temps","<b>Copiar una operación</b> en varias cuentas a la vez"),
       T("<b>“Ready for payout”</b> meter in %, with a golden moment at 100%","<b>Compteur « Prêt pour le payout »</b> en %, avec un moment doré à 100 %","<b>Indicador «Listo para el payout»</b> en %, con un momento dorado al 100 %"),
       T("<b>Payouts</b> (requested → approved → paid) and <b>expenses</b> (evaluations, activations, resets)","<b>Suivi des payouts</b> (demandé → approuvé → payé) et des <b>dépenses</b> (évaluations, activations, resets)","<b>Payouts</b> (solicitado → aprobado → pagado) y <b>gastos</b> (evaluaciones, activaciones, reinicios)"),
       T("<b>Discipline rules</b> detected automatically from your executions","<b>Règles de discipline</b> détectées automatiquement à partir des exécutions","<b>Reglas de disciplina</b> detectadas automáticamente a partir de las ejecuciones")],
      slot("ecran-comptes-prop.webp","desktop",t(T("Prop accounts with the ready-for-payout meter","Comptes prop avec le compteur prêt pour le payout","Cuentas prop con el indicador listo para el payout")),t,fallback="accounts"),
      flip=flip, id_=id_, more=note(t,PROP_NOTE) + m)

def sec_trust(lang, t, id_="data"):
    items = [("download", T("Full export in one click","Export complet en un clic","Exportación completa en un clic"), T("A ZIP file with a re-importable backup, CSV spreadsheets (trades, accounts, payouts, expenses, journal) and all your screenshots.","Un fichier ZIP avec sauvegarde réimportable, tableurs CSV (trades, comptes, payouts, dépenses, journal) et toutes tes captures.","Un archivo ZIP con copia reimportable, hojas CSV (operaciones, cuentas, payouts, gastos, diario) y todas tus capturas.")),
             ("trash", T("Self-serve account deletion","Suppression du compte en libre-service","Eliminación de la cuenta por tu cuenta"), T("Delete your account and all its data yourself, anytime.","Supprime toi-même ton compte et toutes ses données, en tout temps.","Elimina tú mismo tu cuenta y todos sus datos, cuando quieras.")),
             ("eye", T("Private by default","Privé par défaut","Privado por defecto"), T("No social feature is active without your consent.","Aucune fonction sociale n’est active sans ton accord.","Ninguna función social está activa sin tu consentimiento.")),
             ("chat", T("Feedback loop","Boucle de feedback","Ciclo de feedback"), T("Suggest an idea or report a bug from the app and follow its status. When it ships: “You asked, we built it.”","Propose une idée ou signale un bug depuis l’app et suis son statut. Quand c’est livré : « Tu l’as demandé, on l’a construit. »","Propón una idea o reporta un error desde la app y sigue su estado. Cuando sale: «Lo pediste, lo construimos».")),
             ("globe", T("English, French and Spanish","Français, anglais et espagnol","Español, inglés y francés"), T("The whole app, in your language.","Toute l’app, dans ta langue.","Toda la app, en tu idioma."))]
    return f'''<section id="{id_}" class="rule"><div class="wrap"><div class="head"><span class="kick">{t(T("Trust and data","Confiance et données","Confianza y datos"))}</span><h2>{t(T("Your data belongs to you.","Tes données t’appartiennent.","Tus datos te pertenecen."))}</h2><p class="lead">{t(T("Private by default. Yours to export or delete, anytime.","Privées par défaut. À toi de les exporter ou de les supprimer, quand tu veux.","Privados por defecto. Tuyos para exportar o eliminar, cuando quieras."))}</p></div>
<div class="grid stagger g3 g5">{"".join(f'<div>{ico(I[k])}<h3>{t(a)}</h3><p>{t(b)}</p></div>' for k,a,b in items)}<div class="cta-cell"><span class="cta-mark" aria-hidden="true">{MARK}</span><h3>{t(T("Try it with your own trades.","Essaie-le avec tes propres trades.","Pruébalo con tus propias operaciones."))}</h3><p>{t(FREE_LINE)}</p><a class="btn btn-primary" href="{SIGNUP}">{t(START)}</a></div></div></div></section>'''

GAME = [
 ("ecran-parcours.webp", "progression", T("Progression","Progression","Progresión"), T("XP, levels and 7 ranks","XP, niveaux et 7 rangs","XP, niveles y 7 rangos"),
  T("Recruit → Apprentice → Disciplined → Consistent → Seasoned → Master → Sweeper. Over 35 badges, including secret ones, and a 5-chapter path from “First steps” to “Ready for payout”. Each step you unlock guides you to the next.",
    "Recrue → Apprenti → Discipliné → Constant → Aguerri → Maître → Sweeper. Plus de 35 badges (dont des badges secrets) et un parcours en 5 chapitres, de « Premiers pas » jusqu’à « Prêt pour le payout ». Chaque étape débloquée te guide vers la suivante.",
    "Recluta → Aprendiz → Disciplinado → Constante → Curtido → Maestro → Sweeper. Más de 35 insignias (algunas secretas) y un recorrido en 5 capítulos, de «Primeros pasos» a «Listo para el payout». Cada etapa desbloqueada te guía hacia la siguiente.")),
 (None, "missions", T("Weekly missions","Missions hebdomadaires","Misiones semanales"), T("3 missions every Monday","3 missions chaque lundi","3 misiones cada lunes"),
  T("Every Monday, 3 missions tailored to your weak spots of the past weeks. Finish all three and earn a chest key.",
    "Chaque lundi, 3 missions adaptées à tes points faibles des dernières semaines. Termine les trois et gagne une clé de coffre.",
    "Cada lunes, 3 misiones adaptadas a tus puntos débiles de las últimas semanas. Completa las tres y gana una llave de cofre.")),
 ("ecran-boss-revenge.webp", "boss", T("Bosses","Boss","Jefes"), T("Your bad habits, as bosses","Tes mauvaises habitudes, en boss","Tus malos hábitos, como jefes"),
  T("Sweep detects your bad habits in your own data and turns them into bosses: The Revenge, The Opening FOMO, The Oversize, The Slipping Stop, The Overheat, The Improviser… Every clean day takes a hit point off. Beat it for good.",
    "Sweep détecte tes mauvaises habitudes dans tes propres données et les transforme en boss : Le Revenge, Le FOMO de l’ouverture, L’Oversize, Le Stop fuyant, Le Surchauffe, L’Improvisateur… Chaque journée propre lui retire un point de vie. Bats-le pour de bon.",
    "Sweep detecta tus malos hábitos en tus propios datos y los convierte en jefes: El Revenge, El FOMO de la apertura, El Oversize, El Stop huidizo, El Sobrecalentamiento, El Improvisador… Cada día limpio le quita un punto de vida. Derrótalo para siempre.")),
 ("ecran-revue-semaine.webp", "weekly", T("Weekly review","Revue de la semaine","Revisión semanal"), T("A chest every Friday","Un coffre chaque vendredi","Un cofre cada viernes"),
  T("Every Friday evening: your week at a glance, your discovery of the week, three questions, then a chest to open (XP, streak freezes, ring themes, days of Pro…). Odds shown, never sold.",
    "Chaque vendredi soir : ta semaine en un coup d’œil, ta découverte de la semaine, trois questions, puis un coffre à ouvrir (XP, gels de streak, thèmes d’anneaux, jours de Pro…). Probabilités affichées, jamais vendu.",
    "Cada viernes por la noche: tu semana de un vistazo, tu descubrimiento de la semana, tres preguntas y un cofre para abrir (XP, congelaciones de racha, temas de anillos, días de Pro…). Probabilidades visibles, nunca se vende.")),
 ("ecran-edge-reveal.webp", "edge", T("Edge Reveal","Edge Reveal","Edge Reveal"), T("One truth from your trades","Une vérité tirée de tes trades","Una verdad de tus operaciones"),
  T("Every week, Sweep reveals a truth from your own trades: your best time slot, your most profitable setup in R, the effect of an emotion, the difference when you plan before the open.",
    "Chaque semaine, Sweep révèle une vérité tirée de tes propres trades : ton meilleur créneau horaire, ton setup le plus rentable en R, l’effet d’une émotion, la différence quand tu fais ton plan avant l’ouverture.",
    "Cada semana, Sweep revela una verdad de tus propias operaciones: tu mejor franja horaria, tu setup más rentable en R, el efecto de una emoción, la diferencia cuando planificas antes de la apertura.")),
 ("ecran-wrapped-1.webp", "wrapped", T("Sweep Wrapped","Sweep Wrapped","Sweep Wrapped"), T("Your month and year, as a story","Ton mois et ton année, en story","Tu mes y tu año, como una historia"),
  T("Your month, then your year, told as a story: swept days, best streak, signature setup, golden time slot, bosses defeated. A card to share, with no amounts.",
    "Ton mois, puis ton année, racontés comme une story : journées balayées, meilleur streak, setup signature, créneau d’or, boss vaincus. Une carte à partager, sans aucun montant.",
    "Tu mes y luego tu año, contados como una historia: días barridos, mejor racha, setup estrella, franja dorada, jefes derrotados. Una tarjeta para compartir, sin importes.")),
 ("ecran-saison.webp", "seasons", T("Seasons","Saisons","Temporadas"), T("A new season every month","Une nouvelle saison chaque mois","Una nueva temporada cada mes"),
  T("Every month, a new season with its name, its theme and a 30-tier pass. A free track for everyone, and a Pro track with a reward at every tier.",
    "Chaque mois, une nouvelle saison avec son nom, son thème et un pass de 30 paliers. Piste gratuite pour tous, piste Pro avec une récompense à chaque palier.",
    "Cada mes, una nueva temporada con su nombre, su tema y un pase de 30 niveles. Pista gratuita para todos y pista Pro con una recompensa en cada nivel.")),
 ("ecran-badges.webp", "moments", T("Wow moments","Moments « wow »","Momentos «wow»"), T("Every milestone, celebrated","Chaque étape, célébrée","Cada hito, celebrado"),
  T("100 trades logged, your first week without an off-plan trade, your best month of discipline: Sweep celebrates every step.",
    "100 trades journalisés, ta première semaine sans trade hors plan, ton meilleur mois de discipline : Sweep célèbre chaque étape.",
    "100 operaciones registradas, tu primera semana sin operaciones fuera del plan, tu mejor mes de disciplina: Sweep celebra cada paso.")),
]
GAME_INTRO = T("The traders who last aren’t the most gifted. They’re the most consistent. Sweep makes your consistency visible with levels, ranks, badges, missions and bosses to beat, all earned through process. Never through profit.",
               "Les traders qui durent ne sont pas les plus doués. Ce sont les plus réguliers. Sweep rend ta régularité visible avec des niveaux, des rangs, des badges, des missions et des boss à battre, tous gagnés par le processus. Jamais par le profit.",
               "Los traders que duran no son los más talentosos. Son los más constantes. Sweep hace visible tu constancia con niveles, rangos, insignias, misiones y jefes que vencer, todo ganado con el proceso. Nunca con el beneficio.")
GAME_TITLE = T("Discipline, video-game style.","La discipline, version jeu vidéo.","La disciplina, al estilo videojuego.")

def game_teaser(lang, t):
    picks = [g for g in GAME if g[0]][:4]
    cards = "".join(f'<article class="gcard"><div class="gtxt"><span class="kick">{t(k)}</span><h3>{t(h)}</h3></div>{slot(img,"phone",t(h),t,cap=False)}</article>' for img,_,k,h,_p in picks)
    return f'''<section class="rule game-band" id="discipline"><div class="wrap">
<div class="head"><span class="kick">{t(T("Gamification","Gamification","Gamificación"))}</span><h2>{t(GAME_TITLE)}</h2><p class="lead">{t(GAME_INTRO)}</p></div>
<div class="gcards rail stagger">{cards}</div>
<div class="cta-row"><a class="btn btn-line" href="{href(lang,'how-it-works.html')}#discipline">{t(T("See everything you can unlock","Voir tout ce que tu peux débloquer","Ver todo lo que puedes desbloquear"))}</a></div>
</div></section>'''

SOCIAL_POINTS = [
 T("<b>Weekly leagues:</b> Bronze → Silver → Gold → Platinum → Diamond, ranked by discipline XP. Real traders only.","<b>Ligues hebdomadaires :</b> Bronze → Argent → Or → Platine → Diamant. Classement par XP de discipline. Que de vrais traders.","<b>Ligas semanales:</b> Bronce → Plata → Oro → Platino → Diamante, por XP de disciplina. Solo traders reales."),
 T("<b>Crews</b> (3 to 5 traders): a shared goal of swept days, an activity feed and reactions. Goal reached = a chest key for each member.","<b>Crews</b> (3 à 5 traders) : objectif commun de journées balayées, fil d’activité, réactions. Objectif atteint = une clé de coffre pour chacun.","<b>Crews</b> (3 a 5 traders): objetivo común de días barridos, feed de actividad y reacciones. Objetivo cumplido = una llave de cofre para cada uno."),
 T("<b>Accountability buddy:</b> a partner who sees your rings and streak, and can cheer you on once a day.","<b>Accountability buddy :</b> un partenaire qui voit tes anneaux et ton streak, et peut t’encourager une fois par jour.","<b>Accountability buddy:</b> un compañero que ve tus anillos y tu racha, y puede animarte una vez al día."),
 T("<b>Discord:</b> connect your account and your Sweep rank becomes a role on your community’s server.","<b>Discord :</b> connecte ton compte, et ton rang Sweep devient un rôle sur le serveur de ta communauté.","<b>Discord:</b> conecta tu cuenta y tu rango de Sweep se convierte en un rol en el servidor de tu comunidad.")]
def sec_social(lang, t, id_="social", flip=True):
    return split(t, T("Social","Social","Social"), T("Progress together. Your P&L stays yours.","Progresse en groupe. Ton P&L reste à toi.","Progresa en grupo. Tu P&L sigue siendo tuyo."),
      T("Leagues, crews and a buddy keep you showing up. Everything is opt-in and private by default: others see your username, rank and consistency. Never your trades, amounts or accounts.",
        "Ligues, crews et buddy t’aident à être au rendez-vous. Tout est opt-in et privé par défaut : les autres voient ton pseudo, ton rang et ta régularité. Jamais tes trades, tes montants ou tes comptes.",
        "Ligas, crews y un buddy te ayudan a no fallar. Todo es opcional y privado por defecto: los demás ven tu usuario, tu rango y tu constancia. Nunca tus operaciones, importes ni cuentas."),
      SOCIAL_POINTS,
      f'<div class="duo">{slot("ecran-ligue.webp","phone",t(T("Weekly league ranking with the promotion zone","Classement de ligue avec la zone de promotion","Clasificación de liga con la zona de ascenso")),t,cap=False)}{slot("ecran-crew.webp","phone",t(T("Crew weekly goal and activity feed","Objectif de la semaine et fil du crew","Objetivo semanal y feed del crew")),t,cap=False)}</div>',
      flip=flip, id_=id_)

# ----------------------------------------------------------------- HOME
def page_home(lang, t):
    from pages16 import bar, faq_ld
    from pages3 import ai_band
    hero = f'''<div class="hero"><div class="wrap">
<div class="hero-copy">
{bar(lang,t)}
<h1><span class="h1-eyebrow rise">{t(T("Free trading journal for futures & prop firm traders","Journal de trading gratuit pour traders de futures et de prop firms","Diario de trading gratis para traders de futuros y prop firms"))}</span><span class="wu h1-promise">{words(t(T("Your edge, finally in one place.","Ton edge, enfin au même endroit.","Tu edge, por fin en un solo lugar.")),0.15)}</span></h1>
<p class="lead rise d2">{t(T("Trades, prop accounts, payouts, expenses and daily habits. Everything you track in five different places, finally together.","Trades, comptes prop, payouts, dépenses et habitudes. Tout ce que tu suis à cinq endroits, enfin réuni.","Operaciones, cuentas prop, payouts, gastos y hábitos. Todo lo que hoy sigues en cinco lugares distintos, por fin junto."))}</p>
<div class="cta-row rise d3"><a class="btn btn-primary btn-lg" href="{SIGNUP}">{t(T("Start free","Commencer gratuitement","Empieza gratis"))}</a><button type="button" class="btn btn-line btn-lg" data-tour>{PLAY}{t(TOUR_LABEL)}</button></div>
<p class="reassure rise d4">{t(T("Free forever · 60 days of Pro included · No card","Gratuit pour toujours · 60 jours de Pro inclus · Sans carte","Gratis para siempre · 60 días de Pro incluidos · Sin tarjeta"))}</p>
<div class="cohort rise d5" id="cohort" hidden><div class="cbar"><i></i></div><a href="{href(lang,'100')}" class="ctext num" data-tpl="{t(T("{n}/{total} founding traders","{n}/{total} traders fondateurs","{n}/{total} traders fundadores"))}"></a></div>
</div>
<div class="stage has-reel">
<div class="reel"><video class="hero-loop" muted loop playsinline preload="none" data-auto aria-label="{html.escape(t(T("Sweep in action: your day, a trade logged in seconds, your rules, every trade, payout ready, your progress","Sweep en action : ta journée, un trade ajouté en quelques secondes, tes règles, chaque trade, payout prêt, ta progression","Sweep en acción: tu día, una operación registrada en segundos, tus reglas, cada operación, payout listo, tu progreso")))}"><source src="/video/hero-loop-720.webm" type="video/webm" media="(max-width: 860px)"><source src="/video/hero-loop-720.mp4" type="video/mp4" media="(max-width: 860px)"><source src="/video/hero-loop.webm" type="video/webm"><source src="/video/hero-loop.mp4" type="video/mp4"></video>
<button type="button" class="reel-play" data-tour><span class="rp-ic">{PLAY}</span><span class="rp-tx">{t(TOUR_LABEL)}</span><span class="rp-dur num">1:00</span></button></div>
<div class="phone"><picture><source media="(prefers-color-scheme: light)" srcset="/img/captures/ecran-apercu-anneaux-clair.webp"><img src="/img/captures/ecran-apercu-anneaux.webp" width="393" height="852" alt="{html.escape(t(T("Today card with the three rings and shortcuts","Carte Aujourd’hui avec les 3 anneaux et les raccourcis","Tarjeta Hoy con los 3 anillos y los accesos")))}" fetchpriority="high"></picture></div>

<div class="phone back" aria-hidden="true"><img src="/img/captures/ecran-ajout-bougie-static.webp" width="393" height="852" alt="" loading="lazy"></div>
<div class="stage-fade"></div>
</div></div></div>'''
    facts = [(14, T("CME futures contracts on real charts","contrats à terme CME sur vrais graphiques","contratos de futuros de CME en gráficos reales")),
             (3, T("rings a day: plan, execution, review","anneaux par jour : plan, exécution, revue","anillos al día: plan, ejecución, revisión")),
             (7, T("ranks, from Recruit to Sweeper","rangs, de Recrue à Sweeper","rangos, de Recluta a Sweeper")),
             (35, T("badges and more, some of them secret","badges et plus, dont des secrets","insignias y más, algunas secretas"))]
    RINGS = '<svg class="rings" viewBox="0 0 44 44" aria-hidden="true"><circle cx="22" cy="22" r="19" pathLength="100"/><circle cx="22" cy="22" r="13" pathLength="100"/><circle cx="22" cy="22" r="7" pathLength="100"/></svg>'
    fx = "".join(f'<div><span class="num" data-count="{n}">{n}</span>{"<span class=\"plus\">+</span>" if n==35 else ""}{RINGS if n==3 else ""}<span>{t(l)}</span></div>' for n,l in facts)
    facts_html = f'<section style="padding:64px 0 0"><div class="wrap"><div class="facts stagger">{fx}</div></div></section>'
    pillars = [("bolt", T("Lightning-fast journal","Journal ultra rapide","Diario ultrarrápido"), T("A trade in 10 seconds, on real charts.","Un trade en 10 secondes, sur de vrais graphiques.","Una operación en 10 segundos, en gráficos reales.")),
               ("target2", T("Gamified discipline","Discipline gamifiée","Disciplina gamificada"), T("Rings, streaks, missions, bosses. We reward the process, never the P&L.","Anneaux, streaks, missions, boss. On récompense le processus, jamais le P&L.","Anillos, rachas, misiones, jefes. Premiamos el proceso, nunca el P&L.")),
               ("shield", T("Made for prop firms","Fait pour les prop firms","Hecho para prop firms"), T("Preset rules, drawdown, consistency, a “ready for payout” meter.","Règles préconfigurées, drawdown, consistance, compteur « prêt pour le payout ».","Reglas predefinidas, drawdown, consistencia, indicador «listo para el payout»."))]
    pil = f'<section class="rule"><div class="wrap">{grid(t, pillars)}</div></section>'
    from pages2 import FAQ
    picks = [FAQ[1][1][0], FAQ[0][1][0], FAQ[0][1][1], FAQ[1][1][1], FAQ[2][1][0]]
    faq = f'''<section class="rule"><div class="wrap narrow"><div class="head"><h2>{t(T("Questions","Questions","Preguntas"))}</h2></div>{"".join(faq_item(t,q,a) for q,a in picks)}
<div class="cta-row"><a class="btn btn-line" href="{href(lang,'faq.html')}">{t(T("All questions","Toutes les questions","Todas las preguntas"))}</a></div></div></section>'''
    from pages15 import home_faq_ld, IDENTITY
    from pages16 import bar, faq_ld
    ld = jsonld({"@context":"https://schema.org","@graph":[
        {"@type":"SoftwareApplication","@id":f"https://{DOMAIN}/#app","name":"Sweep","alternateName":"Sweep trading journal","publisher":{"@id":f"https://{DOMAIN}/#org"},"applicationCategory":"FinanceApplication","operatingSystem":"Web","url":APP,
         "description":t(IDENTITY),"inLanguage":["en","fr","es"],
         "offers":[{"@type":"Offer","name":"Free","price":"0","priceCurrency":"USD"},{"@type":"Offer","name":"Pro","price":"19","priceCurrency":"USD"},{"@type":"Offer","name":"Elite","price":"39","priceCurrency":"USD"}]},
        faq_ld(t)]})
    from pages4 import plans_band
    ld = ('<link rel="preload" as="image" href="/video/hero-loop-poster-960.webp" media="(max-width: 860px)" fetchpriority="high">'
          '<link rel="preload" as="image" href="/video/hero-loop-poster.webp" media="(min-width: 861px)" fetchpriority="high">') + ld
    from pages9 import sec_why, sec_capture, sec_rules
    from pages10 import sec_eval, sec_share, sec_today, sec_signup
    from pages15 import sec_realpnl, sec_six, sec_nytime, sec_compare, sec_data, home_faq, home_faq_ld, home_final
    from pages9 import sec_why, sec_capture, sec_rules
    from pages16 import bar, sec_oneplace, sec_log, sec_firms, sec_payouts, sec_disc, sec_ai, sec_trust, sec_pricing, sec_faq, sec_final, faq_ld
    body = (hero + sec_oneplace(lang,t) + sec_log(lang,t) + sec_firms(lang,t) + sec_payouts(lang,t) + sec_disc(lang,t) + sec_ai(lang,t)
            + sec_trust(lang,t) + sec_pricing(lang,t) + sec_faq(lang,t) + sec_final(lang,t) + COHORT_JS + tour_dialog(t))
    return (t(T("Sweep — Free Trading Journal for Futures & Prop Firm Traders","Sweep — Journal de trading gratuit pour futures et prop firms","Sweep — Diario de trading gratis para futuros y prop firms")),
            t(T("Track every prop firm account, payout and expense in one place. Free forever, Pro from $19/mo. Built for Topstep, Apex, Lucid and more.","Suis chaque compte prop, payout et dépense au même endroit. Gratuit pour toujours, Pro dès 19 $/mois. Conçu pour Topstep, Apex, Lucid et plus.","Sigue cada cuenta prop, payout y gasto en un solo lugar. Gratis para siempre, Pro desde 19 $/mes. Hecho para Topstep, Apex, Lucid y más.")),
            body, ld)


# ----------------------------------------------------------------- product tour video (lightbox)
TOUR_LABEL = T("Watch the 1-min tour","Voir la visite en 1 min","Ver el tour de 1 min")
PLAY = '<svg class="play" width="14" height="14" viewBox="0 0 16 16" aria-hidden="true"><path d="M4.5 2.8v10.4a.6.6 0 0 0 .9.5l8.2-5.2a.6.6 0 0 0 0-1L5.4 2.3a.6.6 0 0 0-.9.5z" fill="currentColor"/></svg>'
def tour_dialog(t):
    return f'''<dialog class="tour-modal" id="tour" aria-label="{t(T("Sweep product tour","Visite de Sweep","Recorrido de Sweep"))}">
<button type="button" class="tour-close" data-close aria-label="{t(T("Close","Fermer","Cerrar"))}"><svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><path d="M3.5 3.5l9 9M12.5 3.5l-9 9"/></svg></button>
<div class="tour-frame"><video controls playsinline preload="none" poster="/video/tour-poster.webp" data-src-webm="/video/tour.webm" data-src-mp4="/video/tour.mp4" data-src-webm-sm="" data-src-mp4-sm="/video/tour-720.mp4"></video></div>
<p class="tour-note">{t(T("Sound on · Demo data","Avec le son · Données de démonstration · Titres en anglais","Con sonido · Datos de demostración · Títulos en inglés"))}</p></dialog>'''

def tour_card(lang, t):
    return f'''<section class="rule" id="tour-video"><div class="wrap"><div class="head center"><span class="kick">{t(T("Product tour","Visite","Recorrido"))}</span><h2>{t(T("Sweep in one minute.","Sweep en une minute.","Sweep en un minuto."))}</h2></div>
<button type="button" class="tour-card reveal" data-tour aria-label="{t(TOUR_LABEL)}"><img src="/video/tour-poster.webp" srcset="/video/tour-poster-960.webp 960w, /video/tour-poster.webp 1920w" sizes="(max-width: 860px) 92vw, 1120px" width="1600" height="900" alt="" loading="lazy" decoding="async"><span class="tour-btn">{PLAY}<span>{t(TOUR_LABEL)}</span></span></button></div></section>'''

# ----------------------------------------------------------------- home sections (audit, Oct 2026)
def sec_logging(lang, t):
    rows = [
     (T("Tap the candle","Touche la bougie","Toca la vela"), T("Tap a candle for the price and time, then drag your stop and target into place.","Touche une bougie pour le prix et l’heure, puis glisse ton stop et ton objectif en place.","Toca una vela para el precio y la hora, y arrastra tu stop y tu objetivo a su sitio."), ""),
     (T("Say it in words","Dis-le en mots","Dilo con palabras"), T("Sweep AI fills the ticket. You confirm.","Sweep AI remplit le ticket. Tu confirmes.","Sweep AI completa el ticket. Tú confirmas."),
      T("“Long NQ at the open, 2 contracts, stopped at 21,450”","« Long NQ à l’ouverture, 2 contrats, stoppé à 21 450 »","«Largo en NQ en la apertura, 2 contratos, stop en 21.450»")),
     (T("Drop a screenshot or import","Dépose une capture ou importe","Suelta una captura o importa"), T("A screenshot of your platform, or your Tradovate history.","Une capture de ta plateforme, ou ton historique Tradovate.","Una captura de tu plataforma, o tu historial de Tradovate."), "")]
    items = "".join(f'<li><span class="n num">{i+1:02d}</span><div><h3>{t(h)}</h3><p>{t(d)}</p>{f"<p class=\"say num\">{t(q)}</p>" if q else ""}</div></li>' for i,(h,d,q) in enumerate(rows))
    media = slot("video-ajout-bougie.mp4","phone",t(T("Adding a trade by tapping a candle","Ajout d’un trade en touchant une bougie","Añadir una operación tocando una vela")),t,video=True,poster="ecran-ajout-bougie.webp")
    return f'''<section id="logging" class="rule"><div class="wrap split">
<div class="copy"><span class="kick">{t(T("Logging","Saisie","Registro"))}</span><h2>{t(T("Logging that doesn’t feel like homework.","Journaliser, sans que ça ressemble à des devoirs.","Registrar sin que parezca tarea."))}</h2>
<p class="lead">{t(T("Three ways to log a trade. Use whichever is fastest in the moment.","Trois façons d’ajouter un trade. Prends la plus rapide sur le moment.","Tres formas de registrar una operación. Usa la más rápida en cada momento."))}</p>
<ol class="ways">{items}</ol></div>
<div class="reveal">{media}</div></div></section>'''

def disc_mini(lang, t):
    return f'''<section class="rule game-band" id="discipline"><div class="wrap split flip">
<div class="copy"><span class="kick">{t(T("Gamification","Gamification","Gamificación"))}</span><h2>{t(GAME_TITLE)}</h2><p class="lead">{t(GAME_INTRO)}</p>
<p class="meta">{t(T("Optional leagues and crews. Your P&L always stays private.","Ligues et crews optionnels. Ton P&L reste toujours privé.","Ligas y crews opcionales. Tu P&L siempre es privado."))}</p>
<div class="cta-row"><a class="btn btn-line" href="{href(lang,'how-it-works.html')}#discipline">{t(T("See everything you can unlock","Voir tout ce que tu peux débloquer","Ver todo lo que puedes desbloquear"))}</a></div></div>
<div class="reveal">{slot("ecran-boss-revenge.webp","phone",t(T("A boss built from your own habits","Un boss tiré de tes propres habitudes","Un jefe creado con tus propios hábitos")),t)}</div></div></section>'''

def trust_line(lang, t):
    items = [("download",T("Full export in one click","Export complet en un clic","Exportación completa en un clic")),("trash",T("Delete anytime","Supprime en tout temps","Elimina cuando quieras")),
             ("eye",T("Private by default","Privé par défaut","Privado por defecto")),("globe",T("English, French, Spanish","Français, anglais, espagnol","Español, inglés, francés"))]
    act = (f'<div class="activity" id="activity" hidden><div><span class="num" data-k="trades">0</span><span>{t(T("trades journaled","trades journalisés","operaciones registradas"))}</span></div>'
           f'<div><span class="num" data-k="journal_days">0</span><span>{t(T("journal days","journées journalisées","días de diario"))}</span></div>'
           f'<div><span class="num" data-k="taken">0</span><span>{t(T("traders","traders","traders"))}</span></div></div>')
    return f'''<section class="rule trustline-sec"><div class="wrap">{act}<ul class="trustrow stagger">{"".join(f"<li>{ico(I[k])}<span>{t(l)}</span></li>" for k,l in items)}</ul>
<p class="fine" style="text-align:center;margin:18px auto 0"><a href="{href(lang,'security.html')}">{t(T("How we handle your data","Comment on traite tes données","Cómo tratamos tus datos"))}</a></p></div></section>'''

COHORT_JS = ("""<script>(function(){var b=document.getElementById('cohort'),A=document.getElementById('activity');if(!window.fetch)return;fetch('https://app.makeitsweep.com/sweep-count.php',{credentials:'omit'}).then(function(r){return r.ok?r.json():Promise.reject();}).catch(function(){return fetch('https://app.makeitsweep.com/api/cohort-count.php',{credentials:'omit'}).then(function(r){return r.ok?r.json():Promise.reject();});}).then(function(d){if(A&&(parseInt(d.trades,10)||0)>=__STATSMIN__){A.querySelectorAll('[data-k]').forEach(function(e){var v=parseInt(d[e.getAttribute('data-k')],10)||0;e.textContent=v.toLocaleString(document.documentElement.lang);});A.hidden=false;}if(!b)return;var n=Math.max(parseInt(d.taken,10)||0,__FLOOR__),tt=parseInt(d.total,10);if(!(tt>0)||!(n>=1)||n>=tt)return;var a=b.querySelector('.ctext');a.textContent=a.getAttribute('data-tpl').replace('{n}',n).replace('{total}',tt);document.querySelectorAll('.cp-n').forEach(function(x){x.textContent=n+'/'+tt;});b.querySelector('.cbar i').style.width=Math.max(2,Math.round(n/tt*100))+'%';b.hidden=false;}).catch(function(){});})();</script>""").replace('__FLOOR__', str(COHORT_FLOOR)).replace('__STATSMIN__', str(STATS_MIN))

# ----------------------------------------------------------------- HOW IT WORKS (+ discipline & social)
def page_how(lang, t):
    hero = page_hero(t, T("How Sweep works","Comment Sweep fonctionne","Cómo funciona Sweep"),
        T("Build the habits. Find the edge. Get paid.","Bâtis les habitudes. Trouve ton edge. Fais-toi payer.","Crea los hábitos. Encuentra tu edge. Cobra."),
        T("How it works","Comment ça marche","Cómo funciona"))
    anchors = [("start",T("Getting started","Démarrer","Empezar")),("sweep-the-day",T("Sweep your day","Balaye ta journée","Barre tu día")),("discipline",T("Discipline","Discipline","Disciplina")),("social",T("Social","Social","Social"))]
    sub = '<nav class="subnav" aria-label="How it works"><div class="wrap">' + "".join(f'<a href="#{a}">{t(l)}</a>' for a,l in anchors) + "</div></nav>"
    st = [("signup-split", None, T("Create your account","Crée ton compte","Crea tu cuenta"), T("A username, an email and a password. Free forever, with Pro included for your first 60 days. No credit card.","Un nom d’utilisateur, un courriel et un mot de passe. Gratuit pour toujours, avec Pro offert pendant tes 60 premiers jours. Sans carte de crédit.","Un usuario, un correo y una contraseña. Gratis para siempre, con Pro incluido tus primeros 60 días. Sin tarjeta.")),
          ("ecran-comptes-prop.webp", "accounts", T("Add your accounts","Ajoute tes comptes","Añade tus cuentas"), T("Pick your prop firm and account size: the rules are prefilled, for guidance only. Or set up a personal account.","Choisis ta prop firm et la taille du compte : les règles sont préremplies, à titre indicatif. Ou configure un compte personnel.","Elige tu prop firm y el tamaño de la cuenta: las reglas vienen precargadas, a título indicativo. O configura una cuenta personal.")),
          ("video-ajout-bougie.mp4", "new-trade", T("Log a trade in seconds","Ajoute un trade en quelques secondes","Registra una operación en segundos"), T("Paste a screenshot of your platform and Sweep AI fills the trade, or enter it by hand. Your discipline checklist is on the same screen.","Colle une capture de ta plateforme et Sweep AI remplit le trade, ou ajoute-le à la main. Ta checklist de discipline est sur le même écran.","Pega una captura de tu plataforma y Sweep AI completa la operación, o añádela a mano. Tu checklist de disciplina está en la misma pantalla.")),
          ("ecran-graphique-trade.webp", None, T("Review it on the real chart","Revois-le sur le vrai graphique","Revísala en el gráfico real"), T("Entry, exit, stop, target and position zone on CME candles, with your result in R. Charts are available 24 hours after the session.","Entrée, sortie, stop, objectif et zone de position sur les bougies du CME, avec ton résultat en R. Les graphiques sont disponibles 24 h après la séance.","Entrada, salida, stop, objetivo y zona de posición sobre velas de CME, con tu resultado en R. Los gráficos están disponibles 24 h después de la sesión.")),
          ("ecran-apercu-anneaux.webp", "overview", T("Close your three rings","Ferme tes trois anneaux","Cierra tus tres anillos"), T("Plan, execution, review. Close all three and your day is swept.","Plan, exécution, revue. Ferme les trois et ta journée est balayée.","Plan, ejecución, revisión. Cierra los tres y tu día queda barrido."))]
    items = ""
    for img, fb, h, p in st:
        if img == "signup-split":
            media = frame("signup-split", lang, t(h), t, mobile="signup")
        elif img.endswith(".mp4"):
            media = slot(img, "phone", t(h), t, fallback=fb, video=True, poster="ecran-ajout-bougie.webp")
        else:
            kind = "desktop" if img in ("ecran-comptes-prop.webp","ecran-graphique-trade.webp") else "phone"
            media = slot(img, kind, t(h), t, fallback=fb)
        items += f'<li><div><span class="n"></span><h2 style="font-size:clamp(22px,2.2vw,30px)">{t(h)}</h2><p>{t(p)}</p></div><div class="reveal">{media}</div></li>'
    steps = f'<section id="start" style="padding-top:24px"><div class="wrap"><ol class="steps">{items}</ol></div></section>'
    # discipline deep dive
    blocks = ""
    order = ["progression","missions","boss","weekly","edge","seasons","wrapped","moments"]
    G = {g[1]: g for g in GAME}
    for aid in order:
        img, _, k, h, p = G[aid]
        txt = f'<div class="gtxt"><span class="kick">{t(k)}</span><h3>{t(h)}</h3><p>{t(p)}</p></div>'
        if aid == "wrapped":
            trio = "".join(slot(f"ecran-wrapped-{i}.webp","phone",t(T(f"Sweep Wrapped, screen {i}",f"Sweep Wrapped, écran {i}",f"Sweep Wrapped, pantalla {i}")),t,cap=False) for i in (1,2,3))
            blocks += f'<article class="gblock wide reveal" id="{aid}">{txt}<div class="trio">{trio}</div></article>'
        elif aid == "moments":
            blocks += f'<article class="gblock wide reveal" id="{aid}">{txt}{slot(img,"phone",t(h),t,cap=False)}</article>'
        else:
            media = slot(img, "phone", t(h), t, cap=False) if img else ""
            blocks += f'<article class="gblock reveal" id="{aid}">{txt}{media}</article>'
    wrapped_more = ""
    disc = f'''<section id="discipline" class="rule game-band"><div class="wrap"><div class="head"><span class="kick">{t(T("Gamification","Gamification","Gamificación"))}</span><h2>{t(GAME_TITLE)}</h2><p class="lead">{t(GAME_INTRO)}</p></div>
<div class="gblocks">{blocks}</div>{wrapped_more}
<p class="fine">{t(T("Rewards are earned through process only. They have no cash value.","Les récompenses se gagnent uniquement par le processus. Elles n’ont aucune valeur monétaire.","Las recompensas se ganan solo con el proceso. No tienen valor monetario."))}</p></div></section>'''
    ld = jsonld({"@context":"https://schema.org","@type":"HowTo","name":t(T("How to start with Sweep","Comment commencer avec Sweep","Cómo empezar con Sweep")),
        "step":[{"@type":"HowToStep","position":i+1,"name":t(h),"text":t(p)} for i,(_,_,h,p) in enumerate(st)]})
    return (t(T("How Sweep works · Sweep your day, discipline and social","Comment marche Sweep · Balaye ta journée, discipline et social","Cómo funciona Sweep · Barre tu día, disciplina y social")),
            t(T("Create an account, add your prop accounts, log a trade by tapping a candle, close your three rings, and progress with ranks, missions, bosses, seasons and leagues.",
                "Crée un compte, ajoute tes comptes prop, ajoute un trade en touchant une bougie, ferme tes trois anneaux, et progresse avec rangs, missions, boss, saisons et ligues.",
                "Crea una cuenta, añade tus cuentas prop, registra una operación tocando una vela, cierra tus tres anillos y progresa con rangos, misiones, jefes, temporadas y ligas.")),
            hero + sub + steps + tour_card(lang,t) + sec_sweep_day(lang,t) + disc + sec_social(lang,t) + final_cta(lang, t) + tour_dialog(t), ld)

# ----------------------------------------------------------------- PRICING
PRICE_FAQ = None  # filled from FAQ in pages2

def page_pricing(lang, t):
    from pages2 import FAQ
    Y = '<span class="yes" aria-label="✓">✓</span>'; N = '<span class="no" aria-label="—">—</span>'
    lim = lambda a,b,c: (t(a),t(b),t(c))
    rows = [
     (T("Journal, calendar, analytics, economic calendar","Journal, calendrier, analyses, calendrier économique","Diario, calendario, análisis, calendario económico"),Y,Y,Y),
     (T("Real CME charts","Vrais graphiques CME","Gráficos reales de CME"),Y,Y,Y),
     (T("Log with AI (words or screenshot)","Log with AI (mots ou capture)","Log with AI (palabras o captura)"),Y,Y,Y),
     (T("Prop accounts","Comptes prop","Cuentas prop"),*lim(T("Limited","Limité","Limitado"),T("More","Plus","Más"),T("The most","Le plus","El máximo"))),
     (T("Sweep AI (Ask Sweep, trade feedback)","Sweep AI (Ask Sweep, avis sur un trade)","Sweep AI (Ask Sweep, opinión sobre una operación)"),*lim(T("Base quota","Quota de base","Cuota básica"),T("Extended quota","Quota élargi","Cuota ampliada"),T("Maximum quota","Quota maximal","Cuota máxima"))),
     (T("Rings, streak, badges, ranks","Anneaux, streak, badges, rangs","Anillos, racha, insignias, rangos"),Y,Y,Y),
     (T("Streak freezes per week","Gels de streak / semaine","Congelaciones de racha / semana"),"1","2","3"),
     (T("Path","Parcours","Recorrido"),*lim(T("Chapters 1 and 2","Chapitres 1 et 2","Capítulos 1 y 2"),T("Complete","Complet","Completo"),T("Complete","Complet","Completo"))),
     (T("Weekly missions","Missions hebdomadaires","Misiones semanales"),"1","3",t(T("3 + 1 reroll","3 + 1 relance","3 + 1 relanzamiento"))),
     (T("Active bosses","Boss actifs","Jefes activos"),"1","1",t(T("2 + rematch","2 + revanche","2 + revancha"))),
     (T("Edge Reveal","Edge Reveal","Edge Reveal"),*lim(T("1 a month","1 par mois","1 al mes"),T("Every week","Chaque semaine","Cada semana"),T("Every week + a 2nd","Chaque semaine + un 2e","Cada semana + un 2.º"))),
     (T("Monthly and yearly Wrapped","Wrapped mensuel et annuel","Wrapped mensual y anual"),*lim(T("Short version","Version courte","Versión corta"),T("Complete","Complet","Completo"),T("Complete","Complet","Completo"))),
     (T("Season pass","Pass de saison","Pase de temporada"),*lim(T("Free track","Piste gratuite","Pista gratuita"),T("Pro track","Piste Pro","Pista Pro"),T("Pro track + exclusive theme","Piste Pro + thème exclusif","Pista Pro + tema exclusivo"))),
     (T("Leagues, buddy, join a crew","Ligues, buddy, rejoindre un crew","Ligas, buddy, unirse a un crew"),Y,Y,Y),
     (T("Create a crew","Créer un crew","Crear un crew"),N,Y,Y),
     (T("Full export","Export complet","Exportación completa"),Y,Y,Y)]
    body = "".join(f'<tr><th scope="row">{t(a)}</th><td>{b}</td><td>{c}</td><td>{d}</td></tr>' for a,b,c,d in rows)
    def pblock(plan):
        if plan == "free":
            return f'<div class="price"><span class="num">{money(t,0)}</span></div><p class="per muted">{t(T("forever","pour toujours","para siempre"))}</p>'
        m, y = PRICES[plan]["m"], PRICES[plan]["y"]
        ym = money(t, round(y/12, 2)); mm = money(t, m); yy = money(t, y)
        by = t(T(f"billed {yy} a year · 2 months free",f"facturé {yy} par année · 2 mois offerts",f"facturado {yy} al año · 2 meses gratis"))
        bm = t(T("billed monthly","facturé chaque mois","facturado mensualmente"))
        return f'<div class="price"><span class="num" data-m="{mm}" data-y="{ym}">{ym}</span><span class="muted">/{t(T("mo","mois","mes"))}</span></div><p class="per muted" data-m="{bm}" data-y="{by}">{by}</p>'
    feats = {
     "free":[T("Journal, calendar, analytics, economic calendar","Journal, calendrier, analyses, calendrier économique","Diario, calendario, análisis, calendario económico"),T("Real CME charts and Log with AI","Vrais graphiques CME et Log with AI","Gráficos reales de CME y Log with AI"),T("Rings, streak, badges, ranks","Anneaux, streak, badges, rangs","Anillos, racha, insignias, rangos"),T("Leagues, buddy, join a crew","Ligues, buddy, rejoindre un crew","Ligas, buddy, unirse a un crew"),T("Full export","Export complet","Exportación completa")],
     "pro":[T("Everything in Free, plus:","Tout Free, plus :","Todo lo de Free, más:"),T("More prop accounts","Plus de comptes prop","Más cuentas prop"),T("Extended Sweep AI quota","Quota Sweep AI élargi","Cuota de Sweep AI ampliada"),T("2 streak freezes a week","2 gels de streak par semaine","2 congelaciones de racha por semana"),T("Complete path, 3 weekly missions","Parcours complet, 3 missions par semaine","Recorrido completo, 3 misiones semanales"),T("Edge Reveal every week, complete Wrapped","Edge Reveal chaque semaine, Wrapped complet","Edge Reveal cada semana, Wrapped completo"),T("Pro season track, create a crew","Piste de saison Pro, créer un crew","Pista de temporada Pro, crear un crew")],
     "elite":[T("Everything in Pro, plus:","Tout Pro, plus :","Todo lo de Pro, más:"),T("The most prop accounts","Le plus de comptes prop","El máximo de cuentas prop"),T("Maximum Sweep AI quota","Quota Sweep AI maximal","Cuota de Sweep AI máxima"),T("3 streak freezes a week","3 gels de streak par semaine","3 congelaciones de racha por semana"),T("3 missions + 1 reroll, 2 bosses + rematch","3 missions + 1 relance, 2 boss + revanche","3 misiones + 1 relanzamiento, 2 jefes + revancha"),T("A 2nd Edge Reveal every week","Un 2e Edge Reveal chaque semaine","Un 2.º Edge Reveal cada semana"),T("Exclusive season theme","Thème de saison exclusif","Tema de temporada exclusivo")]}
    def card(name, plan, tagline, btn, cls, badge=""):
        link = f"{SIGNUP}&plan={plan}" + ("" if plan == "free" else "&interval=year")
        return f'<div class="plan {cls} reveal">{badge}<h2>{name}</h2><p class="tagline">{t(tagline)}</p>{pblock(plan)}{ul(t,feats[plan])}<a class="btn {"btn-primary" if cls=="main" else "btn-line"} btn-lg" href="{link}" data-plan="{plan}">{t(btn)}</a></div>'
    hero = f'<div class="page-hero" style="text-align:center"><div class="wrap"><span class="kick">{t(T("Pricing","Tarifs","Precios"))}</span><h1 class="wu" style="margin:0 auto;max-width:22ch">{words(t(T("Start free. Stay free if you like.","Commence gratuitement. Reste gratuit si tu veux.","Empieza gratis. Quédate gratis si quieres.")))}</h1><p class="lead rise d3" style="margin-left:auto;margin-right:auto">{t(T("Every new trader gets 60 days of Pro. Then keep Free, or pick the plan that fits. Pro $19/mo or $159/yr, Elite $39/mo or $329/yr, before tax.","Chaque nouveau trader reçoit 60 jours de Pro. Ensuite, garde Free ou choisis le forfait qui te convient. Pro 19 $/mois ou 159 $/an, Elite 39 $/mois ou 329 $/an, avant taxes.","Cada trader nuevo recibe 60 días de Pro. Después, sigue en Free o elige el plan que te conviene. Pro $19/mes o $159/año, Elite $39/mes o $329/año, antes de impuestos."))}</p></div></div>'
    cards = f'''<div class="billing" data-k="y" role="group" aria-label="{t(T("Billing period","Période de facturation","Periodo de facturación"))}"><button type="button" data-bill="m" aria-pressed="false">{t(T("Monthly","Mensuel","Mensual"))}</button><button type="button" data-bill="y" aria-pressed="true">{t(T("Yearly","Annuel","Anual"))} <span class="save">{t(T("Save 30%","Économise 30 %","Ahorra 30 %"))}</span></button></div>
<div class="plans three" id="plans">
{card("Free","free",T("Your journal, real charts and the full daily loop.","Ton journal, les vrais graphiques et toute la boucle quotidienne.","Tu diario, los gráficos reales y todo el ciclo diario."),START,"")}
{card("Pro","pro",T("More accounts, more AI and the whole game. Included for your first 60 days.","Plus de comptes, plus d’IA et tout le jeu. Offert pendant tes 60 premiers jours.","Más cuentas, más IA y todo el juego. Incluido tus primeros 60 días."),START,"main",f'<span class="badge">{t(T("60 days included","60 jours offerts","60 días incluidos"))}</span>')}
{card("Elite","elite",T("The most accounts and AI, 3 streak freezes a week, 2 bosses with rematch and a second Edge Reveal every week.","Le plus de comptes et d’IA, 3 gels de streak par semaine, 2 boss avec revanche et un 2e Edge Reveal chaque semaine.","El máximo de cuentas e IA, 3 congelaciones de racha por semana, 2 jefes con revancha y un 2.º Edge Reveal cada semana."),T("Choose Elite","Choisir Elite","Elegir Elite"),"")}
</div><div class="dots plan-dots" aria-hidden="true"><i></i><i></i><i></i></div>
<ul class="under">{"".join(f"<li>{t(x)}</li>" for x in [T("No credit card to start. Cancel anytime.","Sans carte de crédit pour commencer. Annule quand tu veux.","Sin tarjeta para empezar. Cancela cuando quieras."),T("Monthly or yearly billing (yearly is about 2 months free). Prices in USD, before taxes.","Facturation mensuelle ou annuelle (l’annuel revient à environ 2 mois offerts). Prix en USD, affichés avant taxes.","Facturación mensual o anual (la anual equivale a unos 2 meses gratis). Precios en USD, antes de impuestos."),T("Secure payment by Stripe. No refunds on periods already started.","Paiement sécurisé par Stripe. Aucun remboursement sur les périodes entamées.","Pago seguro con Stripe. Sin reembolsos en periodos ya iniciados.")])}</ul>'''
    b = f'<section style="padding-top:8px"><div class="wrap">{cards}</div></section>'
    cmp = f'<div class="cmp-wrap"><table class="cmp"><thead><tr><th scope="col"><span class="sr">{t(T("Feature","Fonctionnalité","Función"))}</span></th><th scope="col">Free</th><th scope="col" class="hl">Pro</th><th scope="col">Elite</th></tr></thead><tbody>{body}</tbody></table></div>'
    stat = lambda big, small: f'<div><span class="num">{t(big)}</span><span>{t(small)}</span></div>'
    early = f'''<div class="early reveal"><div class="early-copy"><span class="kick">{t(T("Founding member offer","Offre Membre fondateur","Oferta Miembro fundador"))}</span>
<h3>{t(T("Signed up during early access? You get 50% off for life on Pro or Elite.","Tu t’es inscrit pendant l’accès anticipé ? Tu profites de 50 % de rabais à vie sur Pro ou Elite.","¿Te registraste durante el acceso anticipado? Tienes un 50 % de descuento de por vida en Pro o Elite."))}</h3>
<p>{t(T("Reserved for early-access sign-ups, valid until December 1, 2026.","Offre réservée aux inscrits de l’accès anticipé, valable jusqu’au 1er décembre 2026.","Reservada a quienes se registraron en el acceso anticipado, válida hasta el 1 de diciembre de 2026."))}</p></div>
<div class="early-stats">{stat(T(f"{money(t,9.5)}/mo",f"{money(t,9.5)}/mois",f"{money(t,9.5)}/mes"),T(f"Pro for life · {money(t,79.5)} a year",f"Pro à vie · {money(t,79.5)} par an",f"Pro de por vida · {money(t,79.5)} al año"))}{stat(T(f"{money(t,19.5)}/mo",f"{money(t,19.5)}/mois",f"{money(t,19.5)}/mes"),T(f"Elite for life · {money(t,164.5)} a year",f"Elite à vie · {money(t,164.5)} par an",f"Elite de por vida · {money(t,164.5)} al año"))}{stat(T("Dec 1","1er déc.","1 dic."),T("last day, 2026","dernier jour, 2026","último día, 2026"))}</div></div>'''
    refer = f'''<div class="refer reveal">{ico(I["spark"])}<div><h3>{t(T("Invite a friend","Invite un ami","Invita a un amigo"))}</h3><p>{t(T("They get 30 days of Pro, and you get a free month as soon as they use Sweep for real (10 trades on 3 different days, or a paid plan). Up to 12 free months a year.","Il reçoit 30 jours de Pro, et toi un mois gratuit dès qu’il utilise Sweep pour vrai (10 trades sur 3 jours différents, ou un forfait payant). Jusqu’à 12 mois offerts par année.","Recibe 30 días de Pro, y tú un mes gratis en cuanto use Sweep de verdad (10 operaciones en 3 días distintos, o un plan de pago). Hasta 12 meses gratis al año."))}</p></div></div>'''
    b += f'<section class="rule"><div class="wrap"><div class="head"><h2>{t(T("Compare plans","Compare les forfaits","Compara los planes"))}</h2></div>{cmp}{early}{refer}</div></section>'
    pf = [FAQ[0][1][0], FAQ[0][1][1], FAQ[0][1][2], FAQ[0][1][5]]
    b += f'<section class="rule"><div class="wrap narrow"><div class="head"><h2>{t(T("Pricing questions","Questions sur les tarifs","Preguntas sobre precios"))}</h2></div>{"".join(faq_item(t,q,a) for q,a in pf)}</div></section>'
    offers = [{"@type":"Offer","name":n,"price":str(p),"priceCurrency":"USD"} for n,p in (("Free",0),("Pro monthly",19),("Pro yearly",159),("Elite monthly",39),("Elite yearly",329))]
    ld = jsonld({"@context":"https://schema.org","@graph":[{"@type":"Product","name":"Sweep","brand":{"@type":"Brand","name":"Sweep"},"offers":offers},
          {"@type":"FAQPage","mainEntity":[{"@type":"Question","name":t(q),"acceptedAnswer":{"@type":"Answer","text":t(a)}} for q,a in pf]}]})
    return (t(T("Pricing · Free forever, Pro included for 60 days · Sweep","Tarifs · Gratuit pour toujours, Pro offert 60 jours · Sweep","Precios · Gratis para siempre, Pro incluido 60 días · Sweep")),
            t(T("Free forever. Pro included for your first 60 days. Pro $19/mo or $159/yr, Elite $39/mo or $329/yr. Founding member offer and referrals.","Gratuit pour toujours. Pro offert pendant tes 60 premiers jours. Pro 19 $/mois ou 159 $/an, Elite 39 $/mois ou 329 $/an. Offre Membre fondateur et parrainage.","Gratis para siempre. Pro incluido tus primeros 60 días. Pro 19 $/mes o 159 $/año, Elite 39 $/mes o 329 $/año. Oferta de miembro fundador y referidos.")),
            hero + b + final_cta(lang, t), ld)
