/*
 * Sweep — Gamification V1 « Sweep the day » (front-end).
 * Loaded after app.js. Reads the game state from api/game/*; writes the plan and the review into the day's
 * journal document and the journaling fields into the trade documents (the same documents the app already uses),
 * so the Journal page and the game always agree. The server recomputes the rings on every save.
 * Discipline and process only: nothing here shows P&L, amounts or trade counts on a card.
 */
(function () {
  'use strict';
  if (typeof S === 'undefined' || typeof apiJSON !== 'function') return;

  /* ───────────── strings ───────────── */
  const D = {
    en: {
      progress: 'Progress', today: 'Today', plan: 'Plan', execution: 'Execution', review: 'Review',
      swept_title: 'Day swept.', cta_plan: 'Make my plan', cta_journal: 'Checklist to do · {n} trades', cta_journal1: 'Checklist to do · 1 trade', cta_review: 'Daily review',
      cta_swept: 'Day swept', cta_dayoff: 'Not trading today', dayoff_msg: 'A planned day off is a win too.', dayoff_confirm: 'Mark today as a day off? Taking a trade later will count as off-plan.',
      guardrail_msg: "You stopped at the right time. That's discipline.", streak_lost: 'Fresh start. Your best streak is still {n} days.',
      freeze_used: 'A freeze protected your streak on {day}.', offplan: 'This trade was outside your plan.', next_level: '{xp} XP to {rank}',
      market_closed: 'Markets are closed. Rest is part of the process.', yday: 'Yesterday is still open until {t}', yday_cta: 'Finish yesterday',
      streak: 'Streak', best: 'Best', freezes: 'Freezes', level: 'Level', lvl: 'Lv {n}', days: '{n} days', day1: '1 day',
      start_title: 'Getting started', start_steps: { goal: 'Goal chosen', style: 'Style chosen', rules: 'Account rules', journal: 'First trade journaled', plan: 'First plan', review: 'First review' },
      plan_title: 'Plan of the day', bias: 'Bias', long: 'Long', short: 'Short', neutral: 'Neutral', no_trade: 'No trading today', setups: 'Allowed setups',
      no_setups: 'Pick the setups you allow yourself today. They are kept for your next plans and trades.', other_setup: 'Other setup', setup_ph: 'Name of your setup', add: 'Add', max_loss: 'Max loss today', max_trades: 'Max trades (optional)', levels: 'Key levels / note (optional)',
      gate_intro: 'Before your first trade: 30 seconds for your plan.', gate_skip: 'Skip, add my trade', gate_save: 'Save and add my trade', same_plan: 'Same plan as yesterday', save_plan: 'Save my plan', plan_needs: 'Pick a bias and your max loss for the day.', plan_late: 'Your first trade is already in: this plan counts as late.',
      plan_past: 'A plan can only be made for today.',
      journal_title: 'Journal', setup: 'Setup', emotion: 'Emotion before entry', rules: 'Did you follow your rules?', yes: 'Yes', partial: 'Partly', no: 'No',
      next: 'Next', done: 'Done', skip: 'Skip', of: '{a} of {b}', all_journaled: 'Every trade is journaled.',
      review_title: 'Daily review', went_well: 'What went well', improve: 'One thing to improve tomorrow', discipline: 'Discipline today', save_review: 'Save my review',
      today_title: 'Your day', step_plan: 'Plan before the first trade', step_exec: 'Trades inside your plan', step_review: 'Trades journaled and day reviewed',
      v_setup_not_in_plan: 'Setup outside your plan', v_no_stop: 'Stop not respected', v_against_bias: 'Against your bias', v_over_max_loss: 'Taken after your max loss', v_over_max_trades: 'Above your max number of trades',
      v_plan_no_trade: 'Taken on a day off', v_rules: 'Rules partly followed',
      xp: 'XP', plus_xp: '+{n} XP', continue: 'Continue', share: 'Share', new_badge: 'New badge', level_up: 'Level {n}', rank_up: 'New rank', streak_title: '{n}-day streak',
      backfill: 'Your history already earned you {xp} XP and {n} badges.', guardrail_t: 'Guardrail respected',
      rank_card: 'Rank', streak_card: 'Discipline streak', calendar: 'Calendar', badges: 'Badges', counters: 'Counters', swept_days: 'Days swept', reviews_done: 'Reviews done',
      compliant_run: 'Trades in plan in a row', sound: 'Sweep sound', sound_d: 'A short, soft sound when you sweep a day.', locked: 'Locked', secret: 'Secret badge',
      ob_goal: "What's your main goal?", g_evaluation: 'Pass my evaluation', g_payout: 'Get my first payout', g_consistency: 'Become consistent', g_edge: 'Find my edge',
      ob_style: 'How do you trade?', scalp: 'Scalp', intraday: 'Intraday', swing: 'Swing', instruments: 'Instruments', other: 'Other',
      ob_profile: 'Trader profile', ob_account: 'Your daily limit', ob_rules: 'We already know your rules.', ob_rules_sub: 'Daily loss limit on {acct}: {v}. It fills your plan for you.',
      ob_maxloss: 'What is your max loss per day?', ob_win: 'Your first win', ob_mission_journal: 'Journal your last trade', ob_mission_plan: 'Make your plan for today',
      ob_mission_plan_t: 'Make your plan for the next session', ob_reward: 'Reward: a badge and your first closed ring.', ob_skip: 'Later', ob_next: 'Continue', ob_go: "Let's go",
      ob_hello: 'Sweep the day.', ob_hello_sub: 'Plan, execute, review. Close your three rings: the discipline is the game.',
      rk: { rookie: 'Rookie', apprentice: 'Apprentice', disciplined: 'Disciplined', consistent: 'Consistent', seasoned: 'Seasoned', master: 'Master', sweeper: 'Sweeper' },
      share_sweep: 'Day swept.', share_streak: '{n}-day discipline streak', share_rank: 'Rank: {rank}', share_badge: 'Badge unlocked', share_week: 'Perfect week',
      share_sub: 'Plan. Execute. Review.', code: 'Code {c}', saved: 'Image saved',
      emo: { Calm: 'Calm', Confident: 'Confident', Patient: 'Patient', Focused: 'Focused', FOMO: 'FOMO', Fearful: 'Fearful', Frustrated: 'Frustrated', Greedy: 'Greedy', Hesitant: 'Hesitant', Impulsive: 'Impulsive' },
      b: {
        welcome: ['Welcome', 'Finish getting started.'], first_plan: ['First plan', 'Make your first valid plan.'], first_journal: ['First page', 'Journal your first trade.'],
        first_sweep: ['First Sweep', 'Sweep your first day.'], sweep_5: ['On a roll', 'Sweep 5 days.'], sweep_25: ['Habit', 'Sweep 25 days.'], sweep_100: ['Machine', 'Sweep 100 days.'],
        streak_7: ['One week', '7-day streak.'], streak_30: ['One month', '30-day streak.'], streak_100: ['One hundred', '100-day streak.'],
        full_week: ['Perfect week', 'Sweep every market day of one week.'], patience: ['Patience', 'Sweep a planned day off.'], guardrail: ['Guardrail', 'Stop for the day at your max loss.'],
        early_plan: ['Ready before the open', '10 plans made before 9:00 ET.'], sniper: ['Sniper', '10 trades in your plan in a row.'], sacred_stop: ['The sacred stop', '50 trades in a row with a stop.'],
        reviewer_20: ['Introspection', '20 end-of-day reviews.'], resilience: ['Resilience', 'Sweep the day right after a red day.'], comeback: ['The comeback', 'Sweep a day after 7+ quiet market days.'],
        perfectionist: ['Perfectionist', '5 days in a row where every trade has a screenshot and a note.'], zen: ['Zen', '3 planned days off in a row, then a swept day.'],
      },
    },
    fr: {
      progress: 'Progression', today: "Aujourd'hui", plan: 'Plan', execution: 'Exécution', review: 'Revue',
      swept_title: 'Journée réussie.', cta_plan: 'Faire mon plan', cta_journal: 'Checklist à faire · {n} trades', cta_journal1: 'Checklist à faire · 1 trade', cta_review: 'Revue du jour',
      cta_swept: 'Journée balayée', cta_dayoff: "Pas de trading aujourd'hui", dayoff_msg: "Un jour off planifié, c'est aussi une victoire.", dayoff_confirm: 'Déclarer un jour off ? Un trade pris ensuite comptera comme hors plan.',
      guardrail_msg: "Tu t'es arrêté au bon moment. C'est ça, la discipline.", streak_lost: 'Nouveau départ. Ton meilleur streak reste à {n} jours.',
      freeze_used: 'Un gel a protégé ton streak {day}.', offplan: 'Ce trade était hors de ton plan.', next_level: '{xp} XP avant {rank}',
      market_closed: 'Les marchés sont fermés. Le repos fait partie du processus.', yday: "Hier reste ouvert jusqu'à {t}", yday_cta: 'Terminer hier',
      streak: 'Streak', best: 'Meilleur', freezes: 'Gels', level: 'Niveau', lvl: 'Niv. {n}', days: '{n} jours', day1: '1 jour',
      start_title: 'Démarrage', start_steps: { goal: 'Objectif choisi', style: 'Style choisi', rules: 'Règles du compte', journal: 'Premier trade journalisé', plan: 'Premier plan', review: 'Première revue' },
      plan_title: 'Plan du jour', bias: 'Biais', long: 'Long', short: 'Short', neutral: 'Neutre', no_trade: "Pas de trading aujourd'hui", setups: 'Setups autorisés',
      no_setups: 'Choisis les setups que tu t’autorises aujourd’hui. Ils sont gardés pour tes prochains plans et trades.', other_setup: 'Autre setup', setup_ph: 'Nom de ton setup', add: 'Ajouter', max_loss: 'Perte max du jour', max_trades: 'Nombre max de trades (facultatif)', levels: 'Niveaux clés / note (facultatif)',
      gate_intro: 'Avant ton premier trade : 30 secondes pour ton plan.', gate_skip: 'Passer, ajouter mon trade', gate_save: 'Enregistrer et ajouter mon trade', same_plan: "Même plan qu'hier", save_plan: 'Enregistrer mon plan', plan_needs: 'Choisis un biais et ta perte max du jour.', plan_late: 'Ton premier trade est déjà fait : ce plan compte comme tardif.',
      plan_past: "Un plan ne peut être fait que pour aujourd'hui.",
      journal_title: 'Journaliser', setup: 'Setup', emotion: "Émotion avant l'entrée", rules: 'As-tu suivi tes règles ?', yes: 'Oui', partial: 'En partie', no: 'Non',
      next: 'Suivant', done: 'Terminé', skip: 'Passer', of: '{a} sur {b}', all_journaled: 'Tous les trades sont journalisés.',
      review_title: 'Revue du jour', went_well: 'Ce qui a bien fonctionné', improve: 'Une chose à améliorer demain', discipline: "Discipline aujourd'hui", save_review: 'Enregistrer ma revue',
      today_title: 'Ta journée', step_plan: 'Plan avant le premier trade', step_exec: 'Trades dans ton plan', step_review: 'Trades journalisés et journée revue',
      v_setup_not_in_plan: 'Setup hors de ton plan', v_no_stop: 'Stop non respecté', v_against_bias: 'À l’inverse de ton biais', v_over_max_loss: 'Pris après ta perte max', v_over_max_trades: 'Au-delà de ton nombre max de trades',
      v_plan_no_trade: "Pris pendant un jour off", v_rules: 'Règles suivies en partie',
      xp: 'XP', plus_xp: '+{n} XP', continue: 'Continuer', share: 'Partager', new_badge: 'Nouveau badge', level_up: 'Niveau {n}', rank_up: 'Nouveau rang', streak_title: 'Streak de {n} jours',
      backfill: "Ton historique t'a déjà rapporté {xp} XP et {n} badges.", guardrail_t: 'Garde-fou respecté',
      rank_card: 'Rang', streak_card: 'Streak de discipline', calendar: 'Calendrier', badges: 'Badges', counters: 'Compteurs', swept_days: 'Journées balayées', reviews_done: 'Revues faites',
      compliant_run: 'Trades conformes de suite', sound: 'Son Sweep', sound_d: 'Un son court et feutré quand tu balaies une journée.', locked: 'Verrouillé', secret: 'Badge secret',
      ob_goal: 'Quel est ton objectif principal ?', g_evaluation: 'Passer mon évaluation', g_payout: 'Obtenir mon premier payout', g_consistency: 'Devenir constant', g_edge: 'Trouver mon edge',
      ob_style: 'Comment trades-tu ?', scalp: 'Scalp', intraday: 'Intraday', swing: 'Swing', instruments: 'Instruments', other: 'Autre',
      ob_profile: 'Profil de trader', ob_account: 'Ta limite quotidienne', ob_rules: 'On connaît déjà tes règles.', ob_rules_sub: 'Perte max quotidienne sur {acct} : {v}. Elle remplit ton plan pour toi.',
      ob_maxloss: 'Quelle est ta perte max par jour ?', ob_win: 'Ta première victoire', ob_mission_journal: 'Fais la checklist de ton dernier trade', ob_mission_plan: "Fais ton plan pour aujourd'hui",
      ob_mission_plan_t: 'Fais ton plan pour la prochaine séance', ob_reward: 'Récompense : un badge et ton premier anneau fermé.', ob_skip: 'Plus tard', ob_next: 'Continuer', ob_go: "C'est parti",
      ob_hello: 'Sweep the day.', ob_hello_sub: 'Planifie, exécute, fais ta revue. Ferme tes trois anneaux : la discipline, c’est le jeu.',
      rk: { rookie: 'Recrue', apprentice: 'Apprenti', disciplined: 'Discipliné', consistent: 'Constant', seasoned: 'Aguerri', master: 'Maître', sweeper: 'Sweeper' },
      share_sweep: 'Journée balayée.', share_streak: 'Streak de discipline : {n} jours', share_rank: 'Rang : {rank}', share_badge: 'Badge débloqué', share_week: 'Semaine parfaite',
      share_sub: 'Planifier. Exécuter. Revoir.', code: 'Code {c}', saved: 'Image enregistrée',
      emo: { Calm: 'Calme', Confident: 'Confiant', Patient: 'Patient', Focused: 'Concentré', FOMO: 'FOMO', Fearful: 'Craintif', Frustrated: 'Frustré', Greedy: 'Avide', Hesitant: 'Hésitant', Impulsive: 'Impulsif' },
      b: {
        welcome: ['Bienvenue', 'Termine le démarrage.'], first_plan: ['Premier plan', 'Fais ton premier plan valide.'], first_journal: ['Première page', 'Journalise ton premier trade.'],
        first_sweep: ['Premier Sweep', 'Balaie ta première journée.'], sweep_5: ['Sur la lancée', 'Balaie 5 journées.'], sweep_25: ['Habitude', 'Balaie 25 journées.'], sweep_100: ['Machine', 'Balaie 100 journées.'],
        streak_7: ['Une semaine', 'Streak de 7 jours.'], streak_30: ['Un mois', 'Streak de 30 jours.'], streak_100: ['Cent', 'Streak de 100 jours.'],
        full_week: ['Semaine parfaite', "Balaie chaque jour de marché d'une semaine."], patience: ['Patience', 'Balaie un jour off planifié.'], guardrail: ['Garde-fou', "Arrête-toi pour la journée à ta perte max."],
        early_plan: ["Prêt avant l'ouverture", '10 plans faits avant 9 h 00 ET.'], sniper: ['Sniper', '10 trades conformes de suite.'], sacred_stop: ['Le stop sacré', '50 trades de suite avec un stop.'],
        reviewer_20: ['Introspection', '20 revues de fin de journée.'], resilience: ['Résilience', 'Balaie la journée juste après une journée rouge.'], comeback: ['Le retour', 'Balaie une journée après 7+ jours de marché calmes.'],
        perfectionist: ['Perfectionniste', '5 jours de suite où chaque trade a une capture et une note.'], zen: ['Zen', '3 jours off planifiés de suite, puis une journée balayée.'],
      },
    },
    es: {
      progress: 'Progreso', today: 'Hoy', plan: 'Plan', execution: 'Ejecución', review: 'Revisión',
      swept_title: 'Día barrido.', cta_plan: 'Hacer mi plan', cta_journal: 'Checklist pendiente · {n} operaciones', cta_journal1: 'Checklist pendiente · 1 operación', cta_review: 'Revisión del día',
      cta_swept: 'Día barrido', cta_dayoff: 'Hoy no opero', dayoff_msg: 'Un día libre planificado también es una victoria.', dayoff_confirm: '¿Marcar hoy como día libre? Un trade tomado después contará fuera del plan.',
      guardrail_msg: 'Te detuviste en el momento justo. Eso es disciplina.', streak_lost: 'Nuevo comienzo. Tu mejor racha sigue siendo de {n} días.',
      freeze_used: 'Un congelador protegió tu racha el {day}.', offplan: 'Este trade estaba fuera de tu plan.', next_level: '{xp} XP para {rank}',
      market_closed: 'Los mercados están cerrados. El descanso es parte del proceso.', yday: 'Ayer sigue abierto hasta {t}', yday_cta: 'Terminar ayer',
      streak: 'Racha', best: 'Mejor', freezes: 'Congeladores', level: 'Nivel', lvl: 'Nv. {n}', days: '{n} días', day1: '1 día',
      start_title: 'Primeros pasos', start_steps: { goal: 'Objetivo elegido', style: 'Estilo elegido', rules: 'Reglas de la cuenta', journal: 'Primer trade registrado', plan: 'Primer plan', review: 'Primera revisión' },
      plan_title: 'Plan del día', bias: 'Sesgo', long: 'Largo', short: 'Corto', neutral: 'Neutral', no_trade: 'Hoy no opero', setups: 'Setups permitidos',
      no_setups: 'Elige los setups que te permites hoy. Se guardan para tus próximos planes y operaciones.', other_setup: 'Otro setup', setup_ph: 'Nombre de tu setup', add: 'Añadir', max_loss: 'Pérdida máx. del día', max_trades: 'Máx. de trades (opcional)', levels: 'Niveles clave / nota (opcional)',
      gate_intro: 'Antes de tu primera operación: 30 segundos para tu plan.', gate_skip: 'Saltar, añadir mi operación', gate_save: 'Guardar y añadir mi operación', same_plan: 'Mismo plan que ayer', save_plan: 'Guardar mi plan', plan_needs: 'Elige un sesgo y tu pérdida máx. del día.', plan_late: 'Tu primer trade ya está hecho: este plan cuenta como tardío.',
      plan_past: 'Solo se puede hacer un plan para hoy.',
      journal_title: 'Registrar', setup: 'Setup', emotion: 'Emoción antes de entrar', rules: '¿Seguiste tus reglas?', yes: 'Sí', partial: 'En parte', no: 'No',
      next: 'Siguiente', done: 'Listo', skip: 'Saltar', of: '{a} de {b}', all_journaled: 'Todos los trades están registrados.',
      review_title: 'Revisión del día', went_well: 'Lo que salió bien', improve: 'Una cosa a mejorar mañana', discipline: 'Disciplina hoy', save_review: 'Guardar mi revisión',
      today_title: 'Tu día', step_plan: 'Plan antes del primer trade', step_exec: 'Trades dentro de tu plan', step_review: 'Trades registrados y día revisado',
      v_setup_not_in_plan: 'Setup fuera de tu plan', v_no_stop: 'Stop no respetado', v_against_bias: 'En contra de tu sesgo', v_over_max_loss: 'Tomado después de tu pérdida máx.', v_over_max_trades: 'Por encima de tu máx. de trades',
      v_plan_no_trade: 'Tomado en un día libre', v_rules: 'Reglas seguidas en parte',
      xp: 'XP', plus_xp: '+{n} XP', continue: 'Continuar', share: 'Compartir', new_badge: 'Nueva insignia', level_up: 'Nivel {n}', rank_up: 'Nuevo rango', streak_title: 'Racha de {n} días',
      backfill: 'Tu historial ya te dio {xp} XP y {n} insignias.', guardrail_t: 'Límite respetado',
      rank_card: 'Rango', streak_card: 'Racha de disciplina', calendar: 'Calendario', badges: 'Insignias', counters: 'Contadores', swept_days: 'Días barridos', reviews_done: 'Revisiones hechas',
      compliant_run: 'Trades dentro del plan seguidos', sound: 'Sonido Sweep', sound_d: 'Un sonido corto y suave al barrer un día.', locked: 'Bloqueada', secret: 'Insignia secreta',
      ob_goal: '¿Cuál es tu objetivo principal?', g_evaluation: 'Pasar mi evaluación', g_payout: 'Obtener mi primer payout', g_consistency: 'Ser constante', g_edge: 'Encontrar mi ventaja',
      ob_style: '¿Cómo operas?', scalp: 'Scalp', intraday: 'Intradía', swing: 'Swing', instruments: 'Instrumentos', other: 'Otro',
      ob_profile: 'Perfil de trader', ob_account: 'Tu límite diario', ob_rules: 'Ya conocemos tus reglas.', ob_rules_sub: 'Pérdida máx. diaria en {acct}: {v}. Rellena tu plan por ti.',
      ob_maxloss: '¿Cuál es tu pérdida máxima por día?', ob_win: 'Tu primera victoria', ob_mission_journal: 'Registra tu último trade', ob_mission_plan: 'Haz tu plan para hoy',
      ob_mission_plan_t: 'Haz tu plan para la próxima sesión', ob_reward: 'Recompensa: una insignia y tu primer anillo cerrado.', ob_skip: 'Más tarde', ob_next: 'Continuar', ob_go: 'Vamos',
      ob_hello: 'Sweep the day.', ob_hello_sub: 'Planifica, ejecuta, revisa. Cierra tus tres anillos: la disciplina es el juego.',
      rk: { rookie: 'Novato', apprentice: 'Aprendiz', disciplined: 'Disciplinado', consistent: 'Constante', seasoned: 'Veterano', master: 'Maestro', sweeper: 'Sweeper' },
      share_sweep: 'Día barrido.', share_streak: 'Racha de disciplina: {n} días', share_rank: 'Rango: {rank}', share_badge: 'Insignia desbloqueada', share_week: 'Semana perfecta',
      share_sub: 'Planificar. Ejecutar. Revisar.', code: 'Código {c}', saved: 'Imagen guardada',
      emo: { Calm: 'Tranquilo', Confident: 'Seguro', Patient: 'Paciente', Focused: 'Concentrado', FOMO: 'FOMO', Fearful: 'Temeroso', Frustrated: 'Frustrado', Greedy: 'Codicioso', Hesitant: 'Indeciso', Impulsive: 'Impulsivo' },
      b: {
        welcome: ['Bienvenida', 'Completa los primeros pasos.'], first_plan: ['Primer plan', 'Haz tu primer plan válido.'], first_journal: ['Primera página', 'Registra tu primer trade.'],
        first_sweep: ['Primer Sweep', 'Barre tu primer día.'], sweep_5: ['En racha', 'Barre 5 días.'], sweep_25: ['Hábito', 'Barre 25 días.'], sweep_100: ['Máquina', 'Barre 100 días.'],
        streak_7: ['Una semana', 'Racha de 7 días.'], streak_30: ['Un mes', 'Racha de 30 días.'], streak_100: ['Cien', 'Racha de 100 días.'],
        full_week: ['Semana perfecta', 'Barre cada día de mercado de una semana.'], patience: ['Paciencia', 'Barre un día libre planificado.'], guardrail: ['Límite', 'Detente en tu pérdida máxima del día.'],
        early_plan: ['Listo antes de la apertura', '10 planes antes de las 9:00 ET.'], sniper: ['Francotirador', '10 trades dentro del plan seguidos.'], sacred_stop: ['El stop sagrado', '50 trades seguidos con stop.'],
        reviewer_20: ['Introspección', '20 revisiones de cierre.'], resilience: ['Resiliencia', 'Barre el día justo después de un día en rojo.'], comeback: ['El regreso', 'Barre un día tras 7+ días de mercado sin actividad.'],
        perfectionist: ['Perfeccionista', '5 días seguidos con captura y nota en cada trade.'], zen: ['Zen', '3 días libres planificados seguidos y luego un día barrido.'],
      },
    },
  };
  /* ───────────── V2 strings ───────────── */
  const V2 = {
    en: {
      chapter: 'Chapter {n}', journey: 'Your journey', next: 'Next step', soon: 'Coming soon', locked_ch: 'Unlock with Pro', back: 'Back', go: 'Go',
      ch: { 1: 'Foundations', 2: 'Find your edge', 3: 'Consistency', 4: 'Payout', 5: 'Scale' },
      ch_done: 'Chapter complete', node_done: 'Step completed', nodes_done: '{n} steps completed', map_backfill: 'Your history already completed {n} steps of your journey (+{xp} XP).',
      missions: 'This week', mission_done: 'Mission complete', key: 'All 3 missions done: you earned a chest key.', keys: '{n} key', reroll: 'Swap', ends: 'Until {t}', pro: 'Pro',
      payout_ready: 'Payout readiness', payout_full: 'Ready for payout',
      n: {
        c1_goal: ['Goal and style', 'Tell Sweep what you are working toward.'], c1_rules: ['Account rules', 'Add your account and its daily loss limit.'], c1_plan: ['First plan', 'Make a plan before you trade.'],
        c1_journal: ['First journaled trade', 'Setup, emotion and rules on one trade.'], c1_review: ['First review', 'The daily end-of-day review.'], c1_journal10: ['10 journaled trades', 'Journal 10 trades.'],
        c1_sweep: ['First Sweep', 'Close your three rings on one day.'], c2_setups: ['3 setups', 'Tag your trades with 3 different setups.'], c2_journal30: ['30 journaled trades', 'Journal 30 trades.'],
        c2_edge: ['First Edge Reveal', 'Discover what works for you.'], c2_sweep5: ['5 days swept', 'Sweep 5 days.'], c2_weekly: ['First weekly recap', 'Close your week with the weekly recap.'],
        c2_journal50: ['50 complete trades', '50 trades with setup and emotion: unlocks your best setup.'], c3_streak10: ['10-day streak', 'Show up 10 market days in a row.'],
        c3_window: ['10 of 15', '10 swept days within 15 market days.'], c3_week: ['Perfect week', 'Sweep every market day of one week.'], c3_weekly4: ['4 weekly recaps', '4 weekly recaps in a row.'],
        c3_compliant20: ['20 in plan', '20 trades in your plan in a row.'], c4_setup: ['Payout rules', 'Add the payout minimum or target of your account.'], c4_half: ['Halfway', 'Payout readiness at 50 %.'],
        c4_ready: ['Ready', 'Payout readiness at 100 %.'], c4_payout: ['First payout', 'Record your first payout in Sweep.'], c4p_month1: ['A steady month', 'A month with 70 % valid market days.'],
        c4p_month2: ['Two steady months', '2 months in a row with 70 % valid days.'], c4p_month3: ['Three steady months', '3 months in a row with 70 % valid days.'],
        c5_accounts: ['Second account', 'Track a second account.'], c5_expenses: ['Expenses tracked', 'Record your evaluation and subscription costs.'], c5_payouts3: ['3 payouts', 'Record 3 payouts.'],
        c5_net: ['Net profitable', 'Payouts above expenses.'], c5_streak60: ['60-day streak', '60 market days in a row.'],
      },
      m: {
        m_review_3: 'Do your review 3 days', m_plan_3: 'Plan before your first trade 3 days', m_emotion_5: 'Note your emotion on 5 trades', m_plan_early: 'Plan before the open 3 days',
        m_screens: 'Add a screenshot to 5 trades', m_sweep_2: 'Sweep 2 days', m_no_offplan: '4 days with no trade outside your plan', m_review_all: 'Review every market day',
        m_sweep_3: 'Sweep 3 days', m_emotion_all: 'Note your emotion on every trade, 4 days', m_maxloss: 'Respect your max loss, 3 planned days',
      },
    },
    fr: {
      chapter: 'Chapitre {n}', journey: 'Ton parcours', next: 'Prochaine étape', soon: 'Bientôt', locked_ch: 'Débloquer avec Pro', back: 'Retour', go: 'Y aller',
      ch: { 1: 'Fondations', 2: 'Trouver ton edge', 3: 'Consistance', 4: 'Payout', 5: 'Scale' },
      ch_done: 'Chapitre terminé', node_done: 'Étape franchie', nodes_done: '{n} étapes franchies', map_backfill: 'Ton historique a déjà franchi {n} étapes de ton parcours (+{xp} XP).',
      missions: 'Cette semaine', mission_done: 'Mission accomplie', key: 'Les 3 missions sont faites : tu gagnes une clé de coffre.', keys: '{n} clé', reroll: 'Changer', ends: "Jusqu'à {t}", pro: 'Pro',
      payout_ready: 'Prêt pour le payout', payout_full: 'Prêt pour le payout',
      n: {
        c1_goal: ['Objectif et style', 'Dis à Sweep vers quoi tu avances.'], c1_rules: ['Règles du compte', 'Ajoute ton compte et sa perte max quotidienne.'], c1_plan: ['Premier plan', 'Fais un plan avant de trader.'],
        c1_journal: ['Premier trade journalisé', 'Setup, émotion et règles sur un trade.'], c1_review: ['Première revue', 'La revue de fin de journée en 60 s.'], c1_journal10: ['10 trades journalisés', 'Journalise 10 trades.'],
        c1_sweep: ['Premier Sweep', 'Ferme tes trois anneaux sur une journée.'], c2_setups: ['3 setups', 'Tague tes trades avec 3 setups différents.'], c2_journal30: ['30 trades journalisés', 'Journalise 30 trades.'],
        c2_edge: ['Premier Edge Reveal', 'Découvre ce qui marche pour toi.'], c2_sweep5: ['5 journées balayées', 'Balaie 5 journées.'], c2_weekly: ['Premier bilan de la semaine', 'Termine ta semaine avec le bilan de la semaine.'],
        c2_journal50: ['50 trades complets', '50 trades avec setup et émotion : débloque ton meilleur setup.'], c3_streak10: ['Streak de 10', 'Présente-toi 10 jours de marché de suite.'],
        c3_window: ['10 sur 15', '10 journées balayées sur 15 jours de marché.'], c3_week: ['Semaine parfaite', "Balaie chaque jour de marché d'une semaine."], c3_weekly4: ['4 revues hebdo', '4 revues hebdomadaires de suite.'],
        c3_compliant20: ['20 dans le plan', '20 trades conformes de suite.'], c4_setup: ['Règles de payout', 'Ajoute le minimum de payout ou l’objectif de ton compte.'], c4_half: ['À mi-chemin', 'Prêt pour le payout à 50 %.'],
        c4_ready: ['Prêt', 'Prêt pour le payout à 100 %.'], c4_payout: ['Premier payout', 'Enregistre ton premier payout dans Sweep.'], c4p_month1: ['Un mois solide', 'Un mois avec 70 % de jours valides.'],
        c4p_month2: ['Deux mois solides', '2 mois de suite à 70 % de jours valides.'], c4p_month3: ['Trois mois solides', '3 mois de suite à 70 % de jours valides.'],
        c5_accounts: ['Deuxième compte', 'Suis un deuxième compte.'], c5_expenses: ['Dépenses suivies', "Enregistre tes frais d'évaluation et d'abonnement."], c5_payouts3: ['3 payouts', 'Enregistre 3 payouts.'],
        c5_net: ['Rentable net', 'Payouts supérieurs aux dépenses.'], c5_streak60: ['Streak de 60', '60 jours de marché de suite.'],
      },
      m: {
        m_review_3: 'Fais ta revue 3 jours', m_plan_3: 'Plan avant ton premier trade, 3 jours', m_emotion_5: 'Note ton émotion sur 5 trades', m_plan_early: "Plan avant l'ouverture, 3 jours",
        m_screens: 'Ajoute une capture à 5 trades', m_sweep_2: 'Balaie 2 journées', m_no_offplan: '4 jours sans trade hors plan', m_review_all: 'Revue chaque jour de marché',
        m_sweep_3: 'Balaie 3 journées', m_emotion_all: 'Émotion notée sur chaque trade, 4 jours', m_maxloss: 'Respecte ta perte max, 3 jours planifiés',
      },
    },
    es: {
      chapter: 'Capítulo {n}', journey: 'Tu recorrido', next: 'Siguiente paso', soon: 'Pronto', locked_ch: 'Desbloquear con Pro', back: 'Volver', go: 'Ir',
      ch: { 1: 'Fundamentos', 2: 'Encuentra tu ventaja', 3: 'Constancia', 4: 'Payout', 5: 'Escalar' },
      ch_done: 'Capítulo completado', node_done: 'Paso completado', nodes_done: '{n} pasos completados', map_backfill: 'Tu historial ya completó {n} pasos de tu recorrido (+{xp} XP).',
      missions: 'Esta semana', mission_done: 'Misión cumplida', key: 'Las 3 misiones hechas: ganaste una llave de cofre.', keys: '{n} llave', reroll: 'Cambiar', ends: 'Hasta {t}', pro: 'Pro',
      payout_ready: 'Listo para el payout', payout_full: 'Listo para el payout',
      n: {
        c1_goal: ['Objetivo y estilo', 'Cuéntale a Sweep hacia dónde vas.'], c1_rules: ['Reglas de la cuenta', 'Añade tu cuenta y su pérdida máxima diaria.'], c1_plan: ['Primer plan', 'Haz un plan antes de operar.'],
        c1_journal: ['Primer trade registrado', 'Setup, emoción y reglas en un trade.'], c1_review: ['Primera revisión', 'La revisión de cierre de 60 s.'], c1_journal10: ['10 trades registrados', 'Registra 10 trades.'],
        c1_sweep: ['Primer Sweep', 'Cierra tus tres anillos en un día.'], c2_setups: ['3 setups', 'Etiqueta tus trades con 3 setups distintos.'], c2_journal30: ['30 trades registrados', 'Registra 30 trades.'],
        c2_edge: ['Primer Edge Reveal', 'Descubre lo que funciona para ti.'], c2_sweep5: ['5 días barridos', 'Barre 5 días.'], c2_weekly: ['Primer resumen semanal', 'Cierra tu semana con el resumen semanal.'],
        c2_journal50: ['50 trades completos', '50 trades con setup y emoción: desbloquea tu mejor setup.'], c3_streak10: ['Racha de 10', '10 días de mercado seguidos.'],
        c3_window: ['10 de 15', '10 días barridos en 15 días de mercado.'], c3_week: ['Semana perfecta', 'Barre cada día de mercado de una semana.'], c3_weekly4: ['4 revisiones semanales', '4 revisiones semanales seguidas.'],
        c3_compliant20: ['20 en el plan', '20 trades dentro del plan seguidos.'], c4_setup: ['Reglas de payout', 'Añade el mínimo de payout u objetivo de tu cuenta.'], c4_half: ['A mitad', 'Listo para el payout al 50 %.'],
        c4_ready: ['Listo', 'Listo para el payout al 100 %.'], c4_payout: ['Primer payout', 'Registra tu primer payout en Sweep.'], c4p_month1: ['Un mes sólido', 'Un mes con 70 % de días válidos.'],
        c4p_month2: ['Dos meses sólidos', '2 meses seguidos con 70 % de días válidos.'], c4p_month3: ['Tres meses sólidos', '3 meses seguidos con 70 % de días válidos.'],
        c5_accounts: ['Segunda cuenta', 'Sigue una segunda cuenta.'], c5_expenses: ['Gastos registrados', 'Registra tus costos de evaluación y suscripción.'], c5_payouts3: ['3 payouts', 'Registra 3 payouts.'],
        c5_net: ['Rentable neto', 'Payouts por encima de los gastos.'], c5_streak60: ['Racha de 60', '60 días de mercado seguidos.'],
      },
      m: {
        m_review_3: 'Haz tu revisión 3 días', m_plan_3: 'Plan antes de tu primer trade, 3 días', m_emotion_5: 'Anota tu emoción en 5 trades', m_plan_early: 'Plan antes de la apertura, 3 días',
        m_screens: 'Añade una captura a 5 trades', m_sweep_2: 'Barre 2 días', m_no_offplan: '4 días sin trades fuera del plan', m_review_all: 'Revisión cada día de mercado',
        m_sweep_3: 'Barre 3 días', m_emotion_all: 'Emoción anotada en cada trade, 4 días', m_maxloss: 'Respeta tu pérdida máx., 3 días planificados',
      },
    },
  };
  for (const l of ['en', 'fr', 'es']) D[l].v2 = V2[l];
  D.en.b.boss_for_good = ['For good', 'A beaten boss stayed gone for 30 days.'];
  Object.assign(D.en.b, { buddy_10: ['Buddies', '10 days both swept with your buddy.'] }); Object.assign(D.fr.b, { buddy_10: ['Binôme', '10 journées balayées tous les deux avec ton buddy.'] }); Object.assign(D.es.b, { buddy_10: ['Compañeros', '10 días barridos los dos con tu buddy.'] });
  Object.assign(D.en.b, { league_promoted: ['Promoted', 'Move up a league tier.'], payout_ready: ['Ready for payout', 'An account reached 100 % payout readiness.'] });
  Object.assign(D.fr.b, { league_promoted: ['Promu', 'Monte d’un niveau de ligue.'], payout_ready: ['Prêt pour le payout', 'Un compte a atteint 100 % de préparation au payout.'] });
  Object.assign(D.es.b, { league_promoted: ['Ascendido', 'Sube un nivel de liga.'], payout_ready: ['Listo para el payout', 'Una cuenta llegó al 100 % de preparación.'] });
  Object.assign(D.en.b, { weekly_4: ['Steady', '4 weekly recaps in a row.'], weekly_12: ['Quarter', '12 weekly recaps in a row.'], lucky: ['Lucky', 'Found in a chest.'] });
  Object.assign(D.fr.b, { weekly_4: ['Régulier', '4 revues hebdo de suite.'], weekly_12: ['Trimestre', '12 revues hebdo de suite.'], lucky: ['Chanceux', 'Trouvé dans un coffre.'] });
  Object.assign(D.es.b, { weekly_4: ['Constante', '4 revisiones semanales seguidas.'], weekly_12: ['Trimestre', '12 revisiones semanales seguidas.'], lucky: ['Suertudo', 'Encontrado en un cofre.'] });
  D.fr.b.boss_for_good = ['Pour de bon', "Un boss battu n'est pas revenu en 30 jours."];
  D.es.b.boss_for_good = ['Para siempre', 'Un jefe vencido no volvió en 30 días.'];
  const L = () => (LANG === 'fr' || LANG === 'es' ? LANG : 'en');
  const get = (o, path) => path.split('.').reduce((a, k) => (a == null ? a : a[k]), o);
  function t(key, p) {
    let s = get(D[L()], key); if (s == null) s = get(D.en, key); if (s == null) s = key;
    if (p && typeof s === 'string') s = s.replace(/\{(\w+)\}/g, (m, k) => (p[k] != null ? p[k] : m));
    return s;
  }
  if (window.I18N_FR) Object.assign(window.I18N_FR, { Progress: 'Progression' });
  if (window.I18N_ES) Object.assign(window.I18N_ES, { Progress: 'Progreso' });

  const rankName = (k) => t('rk.' + k);
  const bName = (id) => /^season_\d{6}$/.test(id) && typeof sst === 'function' ? sst('season', { n: seasonNum(id.slice(7)) }) : (/^boss_/.test(id) && id !== 'boss_for_good' && typeof bossName === 'function' ? bossName(id.slice(5)) : (D[L()].b[id] || D.en.b[id] || [id])[0]);
  const bDesc = (id) => /^season_\d{6}$/.test(id) ? '' : (/^boss_/.test(id) && id !== 'boss_for_good' ? bt('defeated', { name: bossName(id.slice(5)) }) : (D[L()].b[id] || D.en.b[id] || ['', ''])[1]);
  const reduced = () => matchMedia('(prefers-reduced-motion: reduce)').matches;
  const buzz = (ms) => { try { if (typeof haptic === 'function') haptic(ms); } catch (e) { /* iOS web: no vibration API */ } };
  const on = () => S.mode === 'server' && !!S.me;
  const loc = () => (typeof LOC === 'function' ? LOC() : 'en-US');

  /* ───────────── icons ───────────── */
  const CANDLE = (cls = '') => `<svg class="g-candle ${cls}" viewBox="40 8 40 102" fill="none" aria-hidden="true"><line x1="60" y1="14" x2="60" y2="30" stroke="currentColor" stroke-width="7" stroke-linecap="round"/><rect x="46" y="28" width="28" height="44" rx="6" fill="currentColor"/><line x1="60" y1="70" x2="60" y2="84" stroke="currentColor" stroke-width="7"/><line class="g-wick" x1="60" y1="84" x2="60" y2="104" stroke-width="7" stroke-linecap="round"/></svg>`;
  const IC = {
    flag: '<path d="M6 21V4M6 4h11l-2 4 2 4H6"/>', book: '<path d="M5 4h10a3 3 0 0 1 3 3v13H8a3 3 0 0 1-3-3z"/><path d="M5 17a3 3 0 0 1 3-3h10"/>',
    sweep: '<circle cx="12" cy="12" r="8"/><path d="M8.5 12.5l2.4 2.4 4.8-5.4"/>', fire: '<path d="M12 21c3.9 0 6.5-2.6 6.5-6.2 0-3.6-2.6-5.6-3.9-8.8-.5 2.2-1.7 3.4-3 3.9.3-2.6-.6-5.2-3.2-6.9.2 3.4-2.9 5.6-2.9 10.1C5.5 18.4 8.1 21 12 21z"/>',
    cal: '<rect x="4" y="5" width="16" height="15" rx="3"/><path d="M4 10h16M9 3v4M15 3v4"/>', leaf: '<path d="M5 19c0-8 5-13 14-14-1 9-6 14-14 14z"/><path d="M5 19l7-7"/>',
    shield: '<path d="M12 3l7 3v5c0 4.5-3 8.3-7 10-4-1.7-7-5.5-7-10V6z"/>', sun: '<circle cx="12" cy="14" r="4"/><path d="M3 18h18M12 4v3M5.6 7.6l2 2M18.4 7.6l-2 2"/>',
    target: '<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="4"/><circle cx="12" cy="12" r=".8" fill="currentColor"/>', stop: '<path d="M8 3h8l5 5v8l-5 5H8l-5-5V8z"/><path d="M8 12h8"/>',
    eye: '<path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12z"/><circle cx="12" cy="12" r="3"/>', spark: '<path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z"/>',
    star: '<path d="M12 3.5l2.6 5.3 5.9.9-4.3 4.1 1 5.8-5.2-2.7-5.2 2.7 1-5.8-4.3-4.1 5.9-.9z"/>', hand: '<path d="M7 12V6.5a1.5 1.5 0 0 1 3 0V11M10 11V4.5a1.5 1.5 0 0 1 3 0V11M13 11V5.5a1.5 1.5 0 0 1 3 0V12M16 9.5a1.5 1.5 0 0 1 3 0V15a6 6 0 0 1-6 6h-1a6 6 0 0 1-5.2-3L4.5 14a1.5 1.5 0 0 1 2.5-1.6L7 12"/>',
    lock: '<rect x="5" y="11" width="14" height="9" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/>', q: '<circle cx="12" cy="12" r="9"/><path d="M9.5 9.5a2.5 2.5 0 1 1 3.5 2.3c-.6.3-1 .8-1 1.5V14M12 17h.01"/>',
    snow: '<path d="M12 3v18M4.2 7.5l15.6 9M4.2 16.5l15.6-9M9.5 4.5L12 7l2.5-2.5M9.5 19.5L12 17l2.5 2.5"/>', share: '<path d="M12 15V3M7 8l5-5 5 5"/><path d="M5 12v7a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-7"/>',
    x: '<path d="M6 6l12 12M18 6L6 18"/>', chev: '<path d="M9 6l6 6-6 6"/>',
  };
  const BADGE_IC = { welcome: 'hand', first_plan: 'flag', first_journal: 'book', first_sweep: 'sweep', sweep_5: 'sweep', sweep_25: 'sweep', sweep_100: 'sweep', streak_7: 'fire', streak_30: 'fire', streak_100: 'fire',
    full_week: 'cal', patience: 'leaf', guardrail: 'shield', early_plan: 'sun', sniper: 'target', sacred_stop: 'stop', reviewer_20: 'eye', resilience: 'spark', comeback: 'spark', perfectionist: 'star', zen: 'leaf' };
  const svg = (name, cls = '') => `<svg class="${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${IC[name] || IC.star}</svg>`;

  /* ───────────── state ───────────── */
  const G = { today: null, yesterday: null, profile: null, start: null, busy: false, at: 0, cq: [], showing: false, prog: null, hist: null, histMonth: null, obOpen: false };
  const lsGetJ = (k, d) => { try { const v = localStorage.getItem(k); return v ? JSON.parse(v) : d; } catch (e) { return d; } };
  const lsSetJ = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) { /* private mode */ } };

  async function load(force) {
    if (!on() || (G.busy && !force) || (!force && Date.now() - G.at < 4000)) return;
    G.busy = true;
    try {
      const r = await apiJSON('api/game/today');
      G.today = r.today; G.yesterday = r.yesterday; G.profile = r.profile; G.start = r.start; G.map = r.map; G.missions = r.missions; G.unlocked = r.unlocked || null; G.weekly = r.weekly; G.quest = r.quest; G.wrapped = r.wrapped; G.season = r.season; G.league = r.league; G.crew = r.crew; G.buddy = r.buddy; if (r.cosmetic !== G.cosmetic) { G.cosmetic = r.cosmetic; applyTheme(r.cosmetic); } G.at = Date.now();
      queue(r.celebrations || []);
      paint();
      loadBoss();
      maybeOnboarding(); maybeWhatsNew();
    } catch (e) { /* the game never blocks the journal */ }
    G.busy = false;
  }
  let reloadT = 0;
  const soon = (ms = 700) => { clearTimeout(reloadT); reloadT = setTimeout(() => load(true), ms); };

  // refresh after the server saved a trade or a journal page (it recomputes the rings on save)
  if (typeof srvSend === 'function') {
    const orig = srvSend;
    srvSend = async function (col) {
      const out = await orig.apply(this, arguments);
      if (col === 'trades' || col === 'journals') soon();
      return out;
    };
  }

  /* ───────────── rings ───────────── */
  const RING = [['plan', 44], ['execution', 33], ['review', 22]];
  function ringsSvg(r, { size = 112, stroke = 9, id = 'g' } = {}) {
    const prev = lsGetJ('g.rings.' + id, null);
    return `<svg class="g-rings" viewBox="0 0 112 112" width="${size}" height="${size}" aria-hidden="true">${RING.map(([k, rad]) => {
      const c = 2 * Math.PI * rad, v = Math.max(0, Math.min(100, r[k] || 0)), from = prev && prev[k] != null ? prev[k] : 0;
      return `<circle class="g-track g-${k}" cx="56" cy="56" r="${rad}" stroke-width="${stroke}"/><circle class="g-arc g-${k}" cx="56" cy="56" r="${rad}" stroke-width="${stroke}" stroke-dasharray="${c.toFixed(2)}" stroke-dashoffset="${(c * (1 - from / 100)).toFixed(2)}" data-to="${(c * (1 - v / 100)).toFixed(2)}" transform="rotate(-90 56 56)"/>`;
    }).join('')}</svg>`;
  }
  function animateRings(root, r, id) {
    root.querySelectorAll('.g-arc').forEach((a) => requestAnimationFrame(() => requestAnimationFrame(() => a.setAttribute('stroke-dashoffset', a.dataset.to))));
    lsSetJ('g.rings.' + id, r);
  }

  /* ───────────── Today card (top of Overview) ───────────── */
  const etHM = () => new Intl.DateTimeFormat('en-GB', { timeZone: 'America/New_York', hour: '2-digit', minute: '2-digit', hourCycle: 'h23' }).format(new Date());
  function nextAction(d) {
    if (!d || !d.market) return null;
    const unj = d.trades - d.journaled, hm = etHM(), inSession = hm < '16:00', nextSession = hm >= '18:00';
    const weekly = G.weekly && G.weekly.open && !(G.weekly.done && G.weekly.chest_opened) && (!G.unlocked || G.unlocked.includes('weekly'));
    if (d.swept) return weekly ? { k: 'weekly', label: wt('weekly') } : { k: 'swept', label: t('cta_swept') };
    if (nextSession && unj <= 0) {
      // the session that just ended is still editable: journal its trades / review it before planning the next one
      const y = G.yesterday && G.yesterday.market && !G.yesterday.locked ? G.yesterday : null;
      const yUnj = y ? (y.trades || 0) - (y.journaled || 0) : 0;
      if (y && yUnj > 0) return { k: 'yday', label: yUnj === 1 ? t('cta_journal1') : t('cta_journal', { n: yUnj }) };
      if (y && (y.trades > 0 || y.plan_valid) && !y.review_done) return { k: 'yday', label: t('cta_review') };
      return !d.plan_valid ? { k: 'plan', label: t('cta_plan') } : { k: 'add', label: TA[L()] || TA.en };   // evening: plan the next session
    }
    if (!d.plan_valid && !d.plan_past && inSession && d.trades === 0) return { k: 'plan', label: t('cta_plan') };   // before the plan
    if (unj > 0) return { k: 'journal', label: unj === 1 ? t('cta_journal1') : t('cta_journal', { n: unj }) };     // trades to journal
    if (inSession) return { k: 'add', label: TA[L()] || TA.en };                                                      // plan done, session running
    if (!d.review_done) return { k: 'review', label: t('cta_review') };                                               // after the session
    if (!d.plan_valid && !d.plan_past) return { k: 'plan', label: t('cta_plan') };
    return { k: 'detail', label: t('today_title') };
  }
  const TA = { en: 'Add a trade', fr: 'Ajouter un trade', es: 'Añadir una operación' };
  const fmtDeadline = (ts) => new Date(ts * 1000).toLocaleString(loc(), { weekday: 'short', hour: 'numeric', minute: '2-digit' });

  function todayCard() {
    const d = G.today, p = G.profile;
    if (!d || !p) return `<section class="g-today surface gc g-skel" data-noi18n><div class="skel" style="height:64px;border-radius:14px"></div></section>`;
    const a = nextAction(d), st = p.streak;
    const lvlPct = Math.max(0, Math.min(100, ((p.xp - p.level_xp) / Math.max(1, p.next_level_xp - p.level_xp)) * 100));
    const y = G.yesterday && G.yesterday.market && !G.yesterday.valid ? G.yesterday : null;
    const m = G.map, ms = G.missions, boss = G.boss && G.boss.active && G.boss.active[0];
    const done = ms && ms.missions ? ms.missions.filter((x) => x.done).length : 0, tot = ms && ms.missions ? ms.missions.filter((x) => !x.locked).length : 0;
    // all progression shortcuts, most actionable first; the card shows 3 and a « + N » pill opens the rest
    const allPills = [
      false && m && m.current ? `<button type="button" class="gc-pill" data-g="map">${svg('flag')}<span><small>${t('v2.chapter', { n: m.current.pos })}</small><b>${esc(m.next ? nodeName(m.next.id) : t('v2.ch.' + m.current.n))}</b></span></button>` : '',
      tot ? `<button type="button" class="gc-pill" data-g="missions">${svg('target')}<span><small>${t('v2.missions')}</small><b>${done}/${tot}</b></span></button>` : '',
      G.weekly && G.weekly.open && !(G.weekly.done && G.weekly.chest_opened) ? `<button type="button" class="gc-pill wk" data-g="weekly">${svg('star')}<span><small>${wt('weekly')}</small><b>${G.weekly.done ? wt('open_chest') : wt('w_title')}</b></span></button>` : '',
      questPill(),
      wrappedPill(),
      seasonPill(),
      leaguePill(),
      socialPill(),
      false && boss ? `<button type="button" class="gc-pill boss" data-g="boss" data-v="${boss.row}">${bossArt(boss.boss)}<span><small>${esc(bossName(boss.boss))}</small><b>${boss.hp}/${boss.hp_max}</b></span></button>` : '',
      m && m.payout && m.payout.configured && m.payout.ready >= 70 ? `<button type="button" class="gc-pill pay" data-g="season">${svg('star')}<span><small>${t('v2.payout_ready')}</small><b>${m.payout.ready} %</b></span></button>` : '',
    ].filter(Boolean).filter((h) => {   // progressive reveal: a mechanic shows up once it is unlocked
      const m = /data-g="(missions|boss|weekly|season|league|social)"/.exec(h);
      return !m || !G.unlocked || G.unlocked.includes(m[1]);
    });
    const rank = (h) => /data-g="weekly"|data-g="quest"|wr-pill new|cr-pill has|ss-pill has/.test(h) ? 0 : /data-g="map"|data-g="missions"/.test(h) ? 1 : 2;
    allPills.sort((x, y) => rank(x) - rank(y));
    G.morePills = allPills.slice(3); G.allPills = allPills.slice();
    const near = ms && ms.missions && (!G.unlocked || G.unlocked.includes('missions')) ? ms.missions.filter((x) => !x.done && !x.locked && x.target > 0 && x.progress / x.target >= 0.66).sort((x, y) => y.progress / y.target - x.progress / x.target)[0] : null;
    const pills = near ? `<button type="button" class="gc-pill gc-near" data-g="missions">${svg('target')}<span><small>${esc(t('v2.m.' + near.mission))}</small><b>${near.progress}/${near.target}</b></span></button>` : '';
    const status = d.market
      ? `<button type="button" class="btn primary gc-cta ${a && a.k === 'swept' ? 'is-swept' : ''}" data-g="${a ? a.k : 'detail'}">${a ? esc(a.label) : ''}${a && a.k === 'swept' ? ' ✓' : ''}</button>
         ${!d.swept && !d.day_off && d.trades === 0 && !d.plan_valid ? `<button type="button" class="link gc-off" data-g="dayoff">${t('cta_dayoff')}</button>` : ''}`
      : `<p class="gc-msg">${t('market_closed')}</p>`;
    const note = d.day_off ? t('dayoff_msg') : d.guardrail ? t('guardrail_msg') : (G.weekly && G.weekly.intention ? wt('intention', { v: G.weekly.intention }) : '');
    return `<section class="g-today surface gc" data-noi18n>
      <div class="gc-c1">
        <button type="button" class="g-ringbtn" data-g="detail" aria-label="${t('today_title')}">${ringsSvg(d.market ? d.rings : { plan: 0, execution: 0, review: 0 }, { id: 'today', size: 52, stroke: 9 })}</button>
        <div class="gc-mid">
          <div class="gc-legend">${RING.map(([k]) => `<span class="g-lg g-${k}"><i></i>${t(k)} <b>${d.market ? (d.rings[k] || 0) : '—'}</b></span>`).join('')}</div>
          <button type="button" class="gc-meta" data-g="hub" aria-label="${esc(hbt('title'))}"><span class="g-chip g-streak ${st.today_valid ? 'on' : ''}" title="${t('streak')}">${CANDLE()}<b>${st.current}</b></span>
            <span class="g-chip g-lvl"><b>${t('lvl', { n: p.level })}</b><i class="g-mini"><s style="width:${lvlPct}%"></s></i></span></button>
        </div>
      </div>
      ${pills ? `<div class="gc-c2">${pills}</div>` : ''}
      <div class="gc-c3">${status}${note ? `<p class="gc-note">${note}</p>` : ''}
        ${y ? `<button type="button" class="gc-line" data-g="yday"><span>${t('yday', { t: fmtDeadline(y.deadline) })}</span><b>${t('yday_cta')} ›</b></button>` : ''}</div>
    </section>`;
  }
  function missionsSheet() {
    const h = missionsHtml(); if (!h) return;
    const b = G.boss && G.boss.active && G.boss.active[0] && (!G.unlocked || G.unlocked.includes('boss')) ? G.boss.active[0] : null;
    const SP = { en: 'Special mission', fr: 'Mission spéciale', es: 'Misión especial' }[L()] || 'Special mission';
    const special = b ? `<button type="button" class="gc-pill boss gm-special" data-g="boss" data-v="${b.row}">${bossArt(b.boss)}<span><small>${SP}</small><b>${esc(bossName(b.boss))} · ${b.hp}/${b.hp_max}</b></span></button>` : '';
    openSheet(`${head(t('v2.missions'))}<div class="gc-missheet">${special}${h.replace(/<div class="sec-h">.*?<\/div>/s, '')}</div>`, { cls: 'gm-misheet' });
  }
  function paint() {
    if (!on()) return;
    const v = typeof route === 'function' ? route().v : '';
    const main = document.getElementById('main');
    if (!main) return;
    if (v === 'dashboard' && S.accounts && S.accounts.length) {
      let el = document.getElementById('gToday');
      const html = todayCard();
      if (!el) { el = document.createElement('div'); el.id = 'gToday'; (main.querySelector('.d-today') || main).prepend(el); }   // straight into its place on the dashboard
      if (el._html !== html) { el.innerHTML = html; el._html = html; if (G.today) animateRings(el, G.today.market ? G.today.rings : { plan: 0, execution: 0, review: 0 }, 'today'); }
      ['gMis', 'gBoss'].forEach((id) => { const x = document.getElementById(id); if (x) x.remove(); });
    }
    paintSections();
    paintNav();
  }
  function paintNav() {
    document.querySelectorAll('[data-g-streak]').forEach((e) => { e.textContent = G.profile ? G.profile.streak.current : ''; });
  }

  /* ───────────── sheets (shared) ───────────── */
  let sheetN = 0;
  function openSheet(html, { cls = '', onClose } = {}) {
    closeSheet(true);
    const el = document.createElement('aside');
    el.className = 'evp g-sheet ' + cls; el.id = 'gSheet'; el.setAttribute('data-noi18n', ''); el.setAttribute('role', 'dialog'); el.setAttribute('aria-modal', 'true');
    el.innerHTML = `<div class="evp-in g-in">${html}</div>`;
    const sc = document.createElement('div'); sc.className = 'evp-scrim'; sc.id = 'gScrim';
    sc.addEventListener('click', () => closeSheet());
    document.body.append(sc, el);
    el._onClose = onClose; el._n = ++sheetN;
    if (typeof swipeDismiss === 'function') swipeDismiss(el, { scroller: () => el.querySelector('.g-in'), onClose: () => closeSheet(), ignore: '.g-car,.g-chips-row,textarea,input' });
    requestAnimationFrame(() => { el.classList.add('open'); sc.classList.add('open'); document.body.classList.add('evp-lock'); });
    return el;
  }
  function closeSheet(instant) {
    const el = document.getElementById('gSheet'), sc = document.getElementById('gScrim');
    if (!el) return;
    const cb = el._onClose; el.id = ''; if (sc) sc.id = '';
    el.classList.remove('open'); if (sc) sc.classList.remove('open');
    if (!document.querySelector('.evp.open:not(.g-sheet)')) document.body.classList.remove('evp-lock');
    setTimeout(() => { el.remove(); if (sc) sc.remove(); }, instant ? 0 : 350);
    if (cb) cb();
  }
  const head = (title, sub) => `<div class="g-head"><div><h2>${title}</h2>${sub ? `<span class="muted">${sub}</span>` : ''}</div><button type="button" class="g-x" data-g="close" aria-label="Close">${svg('x')}</button></div>`;

  /* ───────────── Plan sheet ───────────── */
  const journalOf = (day) => (typeof getDoc === 'function' ? getDoc('journals', day) : null) || { id: day };
  function lastPlan(before) {
    return (S.journals || []).filter((j) => j.id < before && j.pre && j.pre.bias && !j.demo).sort((a, b) => b.id.localeCompare(a.id))[0] || null;
  }
  function defaultMaxLoss() {
    const lp = lastPlan('9999');
    if (lp && lp.pre.max_loss) return String(lp.pre.max_loss).replace(/[^0-9.]/g, '');
    if (G.profile && G.profile.onboarding.max_loss) return String(G.profile.onboarding.max_loss / 100);
    const a = (S.accounts || []).find((x) => x.status !== 'archived' && x.rules && x.rules.dll_c && !x.demo);
    return a ? String(a.rules.dll_c / 100) : '';
  }
  const PL = { bias: null, setups: new Set(), max_loss: '', max_trades: '', levels: '' };
  function openPlan(day, opts) {
    day = day || (G.today && G.today.day);
    PL.then = opts && typeof opts.then === 'function' ? opts.then : null;
    const j = journalOf(day), pre = j.pre || {};
    PL.day = day; PL.bias = pre.bias && pre.bias !== 'no_trade' ? pre.bias : (pre.bias || null);
    PL.setups = new Set(pre.setups || []); PL.max_loss = pre.max_loss ? String(pre.max_loss).replace(/[^0-9.]/g, '') : defaultMaxLoss();
    PL.max_trades = pre.max_trades || ''; PL.levels = pre.levels || ''; PL.extra = [];
    openSheet(planHtml(), { cls: 'g-plan' });
    const sh = document.getElementById('gSheet'); if (sh) sh.dataset.day = day;   // the pre-market chart and screenshots attach to this day
  }
  /** common setups offered until the trader has a few of their own (tapping one keeps it in their list) */
  const SUGGESTED_SETUPS = ['Liquidity sweep', 'Break & retest', 'Opening range breakout', 'Fair value gap', 'VWAP reclaim', 'Trend pullback', 'Reversal'];
  function setupsHtml(setups) {
    const own = S.settings && S.settings.setups || [];
    const sug = own.length < 5 ? SUGGESTED_SETUPS.filter((x) => !setups.some((y) => y.toLowerCase() === x.toLowerCase())) : [];
    return `${own.length ? '' : `<p class="g-hint g-hint-sm">${t('no_setups')}</p>`}<div class="g-chips-row wrap">${setups.map((x) => `<button type="button" class="chip ${PL.setups.has(x) ? 'on' : ''}" data-g="setup" data-v="${esc(x)}">${esc(x)}</button>`).join('')}${sug.map((x) => `<button type="button" class="chip g-sug" data-g="setup" data-v="${esc(x)}">${esc(x)}</button>`).join('')}<button type="button" class="chip g-sug g-new" data-g="setup-new">+ ${t('other_setup')}</button></div>
      <div class="g-setup-add" hidden><input type="text" maxlength="40" data-g-newsetup placeholder="${esc(t('setup_ph'))}" enterkeyhint="done"><button type="button" class="btn" data-g="setup-add">${t('add')}</button></div>`;
  }
  function planHtml() {
    const setups = [...new Set([...(S.settings && S.settings.setups || []), ...PL.setups, ...(PL.extra || [])])];
    const d = G.today || {};
    const lp = lastPlan(PL.day);
    const bias = [['bullish', 'long'], ['bearish', 'short'], ['neutral', 'neutral'], ['no_trade', 'no_trade']];
    return `${head(t('plan_title'), fdate(PL.day, { weekday: 'long', month: 'long', day: 'numeric' }))}
      ${PL.then ? `<p class="g-hint g-gate">${t('gate_intro')}</p>` : ''}
      ${d.trades > 0 && !d.plan_valid && !PL.then ? `<p class="g-hint">${t('plan_late')}</p>` : ''}
      ${lp ? `<button type="button" class="link g-same" data-g="same-plan">${t('same_plan')}</button>` : ''}
      <div class="g-f"><span>${t('bias')}</span><div class="g-seg4">${bias.map(([v, k]) => `<button type="button" class="${PL.bias === v ? 'on' : ''} b-${v}" data-g="bias" data-v="${v}">${t(k)}</button>`).join('')}</div></div>
      ${PL.bias === 'no_trade' ? '' : `<div class="g-f g-setups"><span>${t('setups')}</span>${setupsHtml(setups)}</div>
      <div class="g-row2"><label class="g-f"><span>${t('max_loss')}</span><input inputmode="decimal" data-gp="max_loss" value="${esc(PL.max_loss)}" placeholder="$"></label>
      <label class="g-f"><span>${t('max_trades')}</span><input inputmode="numeric" data-gp="max_trades" value="${esc(PL.max_trades)}"></label></div>
      <label class="g-f"><span>${t('levels')}</span><textarea rows="2" data-gp="levels">${esc(PL.levels)}</textarea></label>`}
      <p class="g-err" id="gErr"></p>
      <button type="button" class="btn primary g-big" data-g="save-plan">${PL.then ? t('gate_save') : t('save_plan')}</button>
      ${PL.then ? `<button type="button" class="link g-gate-skip" data-g="plan-skip">${t('gate_skip')} ›</button>` : ''}`;
  }
  function addPlanSetup(wrap) {
    const i = wrap && wrap.querySelector('[data-g-newsetup]'); const v = i && i.value.trim(); if (!v) return;
    PL.extra = [...new Set([...(PL.extra || []), v])]; PL.setups.add(v);
    document.querySelectorAll('#gSheet [data-gp]').forEach((x) => { PL[x.dataset.gp] = x.value; });
    wrap.outerHTML = `<div class="g-f g-setups"><span>${t('setups')}</span>${setupsHtml([...new Set([...(S.settings && S.settings.setups || []), ...PL.setups, ...PL.extra])])}</div>`;
    buzz(5);
  }
  document.addEventListener('keydown', (e) => { if (e.key === 'Enter' && e.target.matches && e.target.matches('[data-g-newsetup]')) { e.preventDefault(); addPlanSetup(e.target.closest('.g-setups')); } });
  function savePlan() {
    const setupsAll = S.settings && S.settings.setups || [];
    const ml = parseFloat(String(PL.max_loss).replace(/[^0-9.]/g, ''));
    const ok = PL.bias && (PL.bias === 'no_trade' || ml > 0);   // setups are optional (same rule as the server)
    if (!ok) { const e = document.getElementById('gErr'); if (e) e.textContent = t('plan_needs'); buzz(20); return; }
    const j = structuredClone(journalOf(PL.day));
    j.id = PL.day;
    j.pre = Object.assign({}, j.pre || {}, { saved_at: (j.pre && j.pre.saved_at) || Math.floor(Date.now() / 1000), bias: PL.bias, setups: [...PL.setups], max_loss: PL.bias === 'no_trade' ? (j.pre && j.pre.max_loss) || '' : String(ml), max_trades: PL.max_trades ? String(parseInt(PL.max_trades, 10) || '') : '', levels: PL.levels });
    put('journals', j);
    const own = S.settings && S.settings.setups || [], add = [...PL.setups].filter((x) => !own.some((y) => y.toLowerCase() === x.toLowerCase()));
    if (add.length && typeof editDoc === 'function') editDoc('settings', 'settings', (r) => { r.setups = [...(r.setups || []), ...add]; });
    const then = PL.then; PL.then = null;
    buzz(10); closeSheet(); soon(500);
    if (then) setTimeout(then, 380);   // the trade form opens right after the plan
  }

  function dayOff() {
    if (!G.today || !confirm(t('dayoff_confirm'))) return;
    const day = G.today.day, j = structuredClone(journalOf(day));
    j.id = day;
    j.pre = Object.assign({}, j.pre || {}, { bias: 'no_trade', day_off: true });
    j.post = Object.assign({}, j.post || {}, { reviewed_at: new Date().toISOString() });
    put('journals', j);
    buzz(10); soon(400);
  }

  /* ───────────── Quick journal (carousel) ───────────── */
  const EMOS = ['Calm', 'Confident', 'Patient', 'Focused', 'FOMO', 'Fearful', 'Frustrated', 'Greedy', 'Hesitant', 'Impulsive'];
  const JN = { ids: [], i: 0 };
  function openJournal(dayState) {
    const d = dayState || G.today;
    JN.ids = (d.detail || []).filter((x) => !x.j).map((x) => x.id).filter((id) => getDoc('trades', id));
    JN.i = 0;
    if (!JN.ids.length) { toast(t('all_journaled')); return; }
    openSheet(journalHtml(), { cls: 'g-jn' });
  }
  function journalHtml() {
    const id = JN.ids[JN.i], tr = getDoc('trades', id) || {};
    const setups = [...new Set([...(S.settings && S.settings.setups || []), ...(tr.setup ? [tr.setup] : [])])];
    const eb = tr.emo && tr.emo.before, emo = Array.isArray(eb) ? eb : (typeof eb === 'string' && eb ? [eb] : []);
    const rules = tr.rules_followed || '';
    const sideL = tr.direction === 'long' ? 'Long' : 'Short';
    return `${head(t('journal_title'), t('of', { a: JN.i + 1, b: JN.ids.length }))}
      <div class="g-car" data-id="${esc(id)}">
        <div class="g-tcard"><b>${esc(tr.instrument || 'NQ')} ${sideL} · ${esc(String(tr.contracts || 1))}</b><span>${fdate(tr.date, { weekday: 'short', month: 'short', day: 'numeric' })} · ${esc(tr.entry_time || '')} ET${typeof acctLabel === 'function' ? ' · ' + esc(acctLabel(tr.account_id)) : ''}</span></div>
        <div class="g-f"><span>${t('setup')}</span>${setups.length ? `<div class="g-chips-row">${setups.map((s) => `<button type="button" class="chip ${tr.setup === s ? 'on' : ''}" data-g="j-setup" data-v="${esc(s)}">${esc(s)}</button>`).join('')}</div>` : `<input data-g-setup value="${esc(tr.setup || '')}" placeholder="${t('setup')}">`}</div>
        <div class="g-f"><span>${t('emotion')}</span><div class="g-chips-row wrap">${EMOS.map((e) => `<button type="button" class="chip ${emo.includes(e) ? 'on' : ''}" data-g="j-emo" data-v="${e}">${esc(t('emo.' + e))}</button>`).join('')}</div></div>
        <div class="g-f"><span>${t('rules')}</span><div class="g-seg3">${['yes', 'partial', 'no'].map((v) => `<button type="button" class="${rules === v ? 'on' : ''} r-${v}" data-g="j-rules" data-v="${v}">${t(v)}</button>`).join('')}</div></div>
      </div>
      <div class="g-acts"><button type="button" class="link" data-g="j-skip">${t('skip')}</button><button type="button" class="btn primary g-big" data-g="j-next">${JN.i < JN.ids.length - 1 ? t('next') : t('done')}</button></div>`;
  }
  function jEdit(fn) {
    const id = JN.ids[JN.i];
    editDoc('trades', id, fn);
    if (typeof syncTrade === 'function') syncTrade(id, ['setup', 'emo', 'rules_followed']);
    const el = document.querySelector('#gSheet .g-in'); if (el) el.innerHTML = journalHtml();
  }
  function jNext(skip) {
    if (!skip) buzz(6);
    if (JN.i < JN.ids.length - 1) {
      JN.i++;
      const el = document.querySelector('#gSheet .g-in');
      if (el) { el.innerHTML = journalHtml(); const c = el.querySelector('.g-car'); if (c && !reduced()) c.animate([{ opacity: 0, transform: 'translateX(40px)' }, { opacity: 1, transform: 'none' }], { duration: 320, easing: 'cubic-bezier(.32,.72,0,1)' }); }
    } else { closeSheet(); soon(500); }
  }

  /* ───────────── Review sheet ───────────── */
  const RV = { day: null, score: null };
  function openReview(day) {
    RV.day = day || (G.today && G.today.day);
    const post = Object.assign({}, journalOf(RV.day).post || {});
    // a review saved with repeated lines (copied trades, before this fix): shown and saved with each line once
    ['well', 'tomorrow'].forEach((k) => { if (typeof post[k] === 'string' && post[k].includes('\n')) post[k] = [...new Set(post[k].split('\n').map((x) => x.trim()).filter(Boolean))].join('\n'); });
    // nothing written for the day yet: bring in what the trade reviews of that day already say
    if (!(post.well || '').trim() || !(post.tomorrow || '').trim()) {
      const tr = (S.trades || []).filter((x) => !x.demo && x.date === RV.day && x.review);
      const pick = (keys) => tr.map((x) => keys.map((k) => (x.review[k] || '').trim()).find(Boolean)).filter(Boolean);
      // a trade copied on several accounts carries the same review on each copy: each sentence once
      const uniq = (arr) => [...new Set(arr.map((x) => String(x).trim()).filter(Boolean))];
      if (!(post.well || '').trim()) post.well = uniq(pick(['well'])).join('\n');
      if (!(post.tomorrow || '').trim()) post.tomorrow = uniq(pick(['lesson', 'wrong', 'differently'])).join('\n');
    }
    RV.score = post.discipline || null;
    openSheet(`${head(t('review_title'), fdate(RV.day, { weekday: 'long', month: 'long', day: 'numeric' }))}
      <label class="g-f"><span>${t('went_well')}</span><textarea rows="2" data-gr="well" maxlength="400">${esc(post.well || '')}</textarea></label>
      <label class="g-f"><span>${t('improve')}</span><textarea rows="2" data-gr="tomorrow" maxlength="400">${esc(post.tomorrow || '')}</textarea></label>
      <div class="g-f"><span>${t('discipline')}</span><div class="g-dots">${[1, 2, 3, 4, 5].map((n) => `<button type="button" class="${RV.score === n ? 'on' : ''}" data-g="r-score" data-v="${n}">${n}</button>`).join('')}</div></div>
      <button type="button" class="btn primary g-big" data-g="save-review">${t('save_review')}</button>`, { cls: 'g-rv' });
  }
  function saveReview() {
    const el = document.getElementById('gSheet');
    const well = el.querySelector('[data-gr=well]').value.trim(), tom = el.querySelector('[data-gr=tomorrow]').value.trim();
    const j = structuredClone(journalOf(RV.day));
    j.id = RV.day;
    j.post = Object.assign({}, j.post || {}, { well, tomorrow: tom, discipline: RV.score, reviewed_at: new Date().toISOString() });
    put('journals', j);
    buzz(10); closeSheet(); soon(500);
  }

  /* ───────────── Day detail ───────────── */
  function openDetail(dayState) {
    const d = dayState || G.today;
    if (!d) return;
    const vlabel = (v) => t('v_' + v);
    const off = (d.detail || []).filter((x) => !x.ok);
    const step = (k, title, val, act) => `<button type="button" class="g-step g-${k}" data-g="${act}"><span class="g-step-r">${ringsMini(k, val)}</span><span><b>${title}</b><small>${val} / 100</small></span>${svg('chev', 'g-chev')}</button>`;
    openSheet(`${head(t('today_title'), fdate(d.day, { weekday: 'long', month: 'long', day: 'numeric' }))}
      <div class="g-detail-rings">${ringsSvg(d.rings, { size: 150, stroke: 11, id: 'detail' })}</div>
      ${step('plan', t('step_plan'), d.rings.plan, 'plan')}${step('execution', t('step_exec'), d.rings.execution, 'exec-why')}${step('review', t('step_review'), d.rings.review, d.trades - d.journaled > 0 ? 'journal' : 'review')}
      ${off.length ? `<div class="g-off-list">${off.map((x) => { const tr = getDoc('trades', x.id) || {}; return `<a class="g-offrow" href="#trade/${esc(x.id)}" data-g="close-nav"><span><b>${esc(tr.entry_time || '')} · ${esc(tr.setup || '—')}</b><small>${t('offplan')}</small></span><span class="g-tags">${[...x.v, ...(x.rules === 'partial' || x.rules === 'no' ? ['rules'] : [])].map((v) => `<i>${esc(vlabel(v))}</i>`).join('')}</span></a>`; }).join('')}</div>` : ''}`, { cls: 'g-dt', onClose: () => {} });
    const el = document.getElementById('gSheet'); if (el) animateRings(el, d.rings, 'detail');
    G.detailDay = d;
  }
  /* « Trades in your plan »: why each trade counts or not, and what to do */
  const XW = {
    en: { title: 'Trades in your plan', how: 'A trade counts when it goes the way of your bias, uses a setup from your plan (if you chose some), comes before your max loss and your max number of trades, and you did not answer « no » to your rules.', allOk: 'Every trade of the day is in your plan.', none: 'No trade yet today: this ring is full as soon as your plan is set.', ok: 'In your plan', fix: { no_stop: ['No stop on this trade.', 'Add the stop you had: tap the trade, then « Details ».', 'Open the trade'], setup_not_in_plan: ['This setup was not in today\'s plan.', 'If it was planned, add it to your plan. Otherwise it is a trade to avoid.', 'Edit my plan'], over_max_loss: ['Taken after your max loss of the day.', 'The rule is to stop once the max loss is reached.', ''], over_max_trades: ['Above your max number of trades.', 'The rule is to stop at your max number of trades.', ''], plan_no_trade: ['You had chosen « No trading today ».', 'If you did plan to trade, change your plan.', 'Edit my plan'], rules_partial: ['Rules followed: partly.', 'Note in the trade review which rule slipped, to catch it next time.', 'Open the trade'], rules_no: ['Rules followed: no.', 'Review what broke the rules in the trade review.', 'Open the trade'] } },
    fr: { title: 'Trades dans ton plan', how: 'Un trade compte s’il va dans le sens de ton biais, utilise un setup de ton plan (si tu en as choisi), arrive avant ta perte max et ton nombre max de trades, et que tu n’as pas répondu « non » à tes règles.', allOk: 'Tous les trades du jour sont dans ton plan.', none: 'Aucun trade aujourd’hui : cet anneau est plein dès que ton plan est fait.', ok: 'Dans ton plan', fix: { no_stop: ['Aucun stop sur ce trade.', 'Ajoute le stop que tu avais : ouvre le trade, puis « Détails ».', 'Ouvrir le trade'], setup_not_in_plan: ['Ce setup n’était pas dans ton plan du jour.', 'S’il était prévu, ajoute-le à ton plan. Sinon, c’est un trade à éviter.', 'Modifier mon plan'], over_max_loss: ['Pris après ta perte max du jour.', 'La règle : t’arrêter une fois la perte max atteinte.', ''], over_max_trades: ['Au-delà de ton nombre max de trades.', 'La règle : t’arrêter à ton nombre max de trades.', ''], plan_no_trade: ['Tu avais choisi « Pas de trading aujourd’hui ».', 'Si tu avais prévu de trader, modifie ton plan.', 'Modifier mon plan'], rules_partial: ['Règles suivies : en partie.', 'Note dans le bilan quelle règle a glissé, pour la repérer la prochaine fois.', 'Ouvrir le trade'], rules_no: ['Règles suivies : non.', 'Note ce qui a brisé tes règles dans le bilan du trade.', 'Ouvrir le trade'] } },
    es: { title: 'Operaciones en tu plan', how: 'Una operación cuenta si tiene stop, usa un setup de tu plan, llega antes de tu pérdida máx. y de tu número máx. de operaciones, y seguiste tus reglas.', allOk: 'Todas las operaciones del día están en tu plan.', none: 'Ninguna operación hoy: este anillo se llena en cuanto haces tu plan.', ok: 'En tu plan', fix: { no_stop: ['Sin stop en esta operación.', 'Añade el stop que tenías: abre la operación y luego « Detalles ».', 'Abrir la operación'], setup_not_in_plan: ['Este setup no estaba en tu plan del día.', 'Si estaba previsto, añádelo a tu plan. Si no, es una operación a evitar.', 'Editar mi plan'], over_max_loss: ['Tomada después de tu pérdida máx. del día.', 'La regla: parar al alcanzar la pérdida máx.', ''], over_max_trades: ['Más allá de tu número máx. de operaciones.', 'La regla: parar en tu número máx. de operaciones.', ''], plan_no_trade: ['Habías elegido « No operar hoy ».', 'Si sí planeabas operar, cambia tu plan.', 'Editar mi plan'], rules_partial: ['Reglas seguidas: en parte.', 'Anota en la revisión qué regla falló, para detectarla la próxima vez.', 'Abrir la operación'], rules_no: ['Reglas seguidas: no.', 'Anota qué rompió tus reglas en la revisión.', 'Abrir la operación'] } } };
  function execWhy(d) {
    const x = XW[LANG] || XW.en, list = d.detail || [];
    const rows = list.map((it) => {
      const tr = getDoc('trades', it.id) || {};
      const codes = [...(Array.isArray(it.v) ? it.v : it.v ? [it.v] : [])];
      if (it.rules === 'partial') codes.push('rules_partial'); else if (it.rules === 'no') codes.push('rules_no');
      const pnl = typeof tNet === 'function' && typeof money === 'function' ? money(tNet(tr)) : '';
      const head = `<div class="gx-h"><b>${esc((tr.entry_time || '').slice(0, 5))} · ${esc(tr.instrument || 'NQ')} ${tr.direction === 'short' ? 'Short' : 'Long'}${tr.setup ? ' · ' + esc(tr.setup) : ''}</b><span>${pnl}</span></div>`;
      if (!codes.length || it.ok) return `<div class="gx-row ok">${head}<p class="gx-ok">✓ ${x.ok}</p></div>`;
      const fixes = codes.map((c) => { const f = x.fix[c]; if (!f) return ''; const go = f[2] ? (c === 'setup_not_in_plan' || c === 'plan_no_trade' ? `<button type="button" class="link" data-g="plan">${f[2]} ›</button>` : `<a class="link" href="#trade/${esc(it.id)}" data-g="close-nav">${f[2]} ›</a>`) : ''; return `<li><b>${f[0]}</b><span>${f[1]}</span>${go}</li>`; }).join('');
      return `<div class="gx-row">${head}<ul class="gx-fix">${fixes}</ul></div>`;
    }).join('');
    const box = document.querySelector('#gSheet .g-in'); if (!box) return;
    box.innerHTML = `<div class="g-head"><button type="button" class="link" data-g="detail-back">‹ ${t('v2.back')}</button><button type="button" class="g-x" data-g="close" aria-label="Close">${svg('x')}</button></div>
      <h2 class="gx-t">${x.title} <span>${d.rings.execution} / 100</span></h2><p class="gx-how">${x.how}</p>
      ${list.length ? (list.every((i) => i.ok) ? `<p class="gx-all">✓ ${x.allOk}</p>` : '') + rows : `<p class="gx-all">${x.none}</p>`}`;
  }
  function ringsMini(k, v) {
    const c = 2 * Math.PI * 10;
    return `<svg viewBox="0 0 28 28" width="28" height="28"><circle class="g-track g-${k}" cx="14" cy="14" r="10" stroke-width="4"/><circle class="g-arc g-${k}" cx="14" cy="14" r="10" stroke-width="4" stroke-dasharray="${c.toFixed(1)}" stroke-dashoffset="${(c * (1 - v / 100)).toFixed(1)}" transform="rotate(-90 14 14)"/></svg>`;
  }



  /* ───────────── next useful progression step (Today rank card) and the « reward waiting » dot ───────────── */
  const NX = {
    en: { season: 'Season reward to claim', chest: 'Your chest is ready to open', mission: 'Mission almost done: {m} {p}/{t}', league: '{t} league · {r}', streak: 'Streak {n} days · best {b}' },
    fr: { season: 'Récompense de saison à réclamer', chest: 'Ton coffre est prêt à ouvrir', mission: 'Mission presque finie : {m} {p}/{t}', league: 'Ligue {t} · {r}', streak: 'Streak {n} jours · record {b}' },
    es: { season: 'Recompensa de temporada por reclamar', chest: 'Tu cofre está listo', mission: 'Misión casi lista: {m} {p}/{t}', league: 'Liga {t} · {r}', streak: 'Racha {n} días · récord {b}' },
  };
  function progNext() {
    const x = NX[L()] || NX.en, p = G.profile; if (!p) return null;
    const unl = (k) => !G.unlocked || G.unlocked.includes(k);
    const ss = G.season, wk = G.weekly;
    if (ss && ss.claimable && unl('season')) return { text: x.season, dot: true, sig: 's' + ss.number + ':' + ss.claimable };
    if (wk && wk.open && wk.done && !wk.chest_opened && unl('weekly')) return { text: x.chest, dot: true, sig: 'c' + (wk.week || '') };
    const ms = G.missions; const near = ms && ms.missions && unl('missions') ? ms.missions.filter((m) => !m.done && !m.locked && m.target > 0 && m.progress / m.target >= 0.66)[0] : null;
    if (near) return { text: x.mission.replace('{m}', t('v2.m.' + near.mission)).replace('{p}', near.progress).replace('{t}', near.target), dot: false };
    const l = G.league, dow = new Date().getDay();
    if (l && unl('league') && (dow === 1 || dow === 2)) return { text: x.league.replace('{t}', lgt('tiers.' + l.tier)).replace('{r}', lgt('rank', { r: ord(l.rank), n: l.of })), dot: false };
    return { text: x.streak.replace('{n}', p.streak.current).replace('{b}', p.streak.best), dot: false };
  }

  /* ───────────── « What's new » (once per trader who started before the redesign; it is the session's modal) ───────────── */
  const WN = {
    en: ['What’s new', 'Your tabs are now Today, Trades, Stats and Accounts.', 'Progression, Settings and Subscription are under your avatar.', 'For everything else: « Search or ask Sweep ».', 'Got it'],
    fr: ['Quoi de neuf', 'Les onglets sont maintenant Aujourd’hui, Trades, Stats et Comptes.', 'Progression, Réglages et Abonnement sont sous ton avatar.', 'Pour tout le reste : « Rechercher ou demander à Sweep ».', 'Compris'],
    es: ['Novedades', 'Tus pestañas ahora son Hoy, Operaciones, Stats y Cuentas.', 'Progreso, Ajustes y Suscripción están en tu avatar.', 'Para todo lo demás: « Buscar o preguntar a Sweep ».', 'Entendido'],
  };
  function maybeWhatsNew() {
    const p = G.profile;
    if (!p || !p.onboarding || !p.onboarding.whats_new_due || G.obOpen || G.wnOpen || document.querySelector('#gSheet')) return;
    if (!useModal()) return;
    G.wnOpen = true;
    const w = WN[L()] || WN.en;
    openSheet(`<div class="g-wn"><span class="g-wn-ic">${svg('spark')}</span><h2>${w[0]}</h2><ul><li>${esc(w[1])}</li><li>${esc(w[2])}</li><li>${esc(w[3])}</li></ul>
      <button type="button" class="btn primary g-wn-ok" data-g="wn-ok">${w[4]}</button></div>`, { cls: 'g-wnsheet' });
    p.onboarding.whats_new_due = false;   // once: marked as seen as soon as it is shown
    apiJSON('api/game/onboarding', { method: 'POST', body: { whats_new: 1 } }).catch(() => {});
  }

  /* ───────────── one automatic modal per session ───────────── */
  // priority: onboarding (opens first, at load) → rank up / major badge / payout ready / boss beaten. Everything else: a 3 s toast
  // (the bell keeps the notifications). « Day swept » after your own review is not automatic: it always plays.
  const MKEY = 'sw.modal';
  const modalUsed = () => { try { return sessionStorage.getItem(MKEY) === '1'; } catch (e) { return false; } };
  const useModal = () => { if (modalUsed()) return false; try { sessionStorage.setItem(MKEY, '1'); } catch (e) { /* private mode */ } return true; };
  const isMajor = (c) => (c.type === 'level' && c.data && c.data.rank_up) || (c.type === 'badge' && c.data && /epic|legend/.test(c.data.rarity || '')) || c.type === 'payout_ready' || c.type === 'boss_defeated';
  const fresh = (c) => !c.created_at || Date.now() / 1000 - c.created_at < 300;
  const TOAST = {
    en: { badge: 'New badge unlocked', level: 'Level {n} reached', streak: '{n}-day streak', sweep: 'Day swept', unlock: 'Unlocked: {f}', crew_goal: 'Crew goal reached', league_result: 'Your league result is in', quest_done: 'Comeback quest complete', boss_spawn: 'New boss: see Progression', freeze_used: 'Streak freeze used', streak_lost: 'Streak ended. A new one starts today.', guardrail: 'Daily max loss passed', node: 'Step completed', mission: 'Mission complete', chest: 'Chest ready', def: 'Nice: see Progression' },
    fr: { badge: 'Nouveau badge débloqué', level: 'Niveau {n} atteint', streak: 'Streak de {n} jours', sweep: 'Journée balayée', unlock: 'Débloqué : {f}', crew_goal: 'Objectif du crew atteint', league_result: 'Ton résultat de ligue est arrivé', quest_done: 'Quête de retour réussie', boss_spawn: 'Nouveau boss : vois Progression', freeze_used: 'Gel de streak utilisé', streak_lost: 'Streak terminé. Un nouveau commence aujourd’hui.', guardrail: 'Perte max du jour dépassée', node: 'Étape franchie', mission: 'Mission accomplie', chest: 'Coffre prêt', def: 'Bravo : vois Progression' },
    es: { badge: 'Nueva insignia desbloqueada', level: 'Nivel {n} alcanzado', streak: 'Racha de {n} días', sweep: 'Día barrido', unlock: 'Desbloqueado: {f}', crew_goal: 'Objetivo del crew alcanzado', league_result: 'Tu resultado de liga llegó', quest_done: 'Misión de regreso completada', boss_spawn: 'Nuevo jefe: mira Progreso', freeze_used: 'Congelador usado', streak_lost: 'Racha terminada. Hoy empieza otra.', guardrail: 'Pérdida máxima del día superada', node: 'Etapa superada', mission: 'Misión completada', chest: 'Cofre listo', def: '¡Bien! Mira Progreso' },
  };
  const TS = { shown: 0, extra: 0, reset: 0 };
  const SUMT = { en: '{n} new · See Progression', fr: '{n} nouveautés · Voir Progression', es: '{n} novedades · Ver Progreso' };
  function summaryToast() {
    const n = TS.extra; TS.extra = 0; if (!n) return;
    document.querySelectorAll('.gm-sumtoast').forEach((e) => e.remove());
    const el = document.createElement('button'); el.type = 'button'; el.className = 'gm-sumtoast'; el.setAttribute('data-noi18n', '');
    el.innerHTML = `${svg('star')}<span>${esc((SUMT[L()] || SUMT.en).replace('{n}', n))}</span>`;
    el.addEventListener('click', () => { el.remove(); openHub(); });
    document.body.append(el); requestAnimationFrame(() => el.classList.add('on'));
    setTimeout(() => { el.classList.remove('on'); setTimeout(() => el.remove(), 300); }, 5000);
  }
  function smallToast(c) {
    clearTimeout(TS.reset); TS.reset = setTimeout(() => { TS.shown = 0; }, 8000);
    if (TS.shown >= 2) { TS.extra++; return Promise.resolve(); }   // the rest stays in Progression and the bell
    TS.shown++;
    const T = TOAST[L()] || TOAST.en, d = c.data || {};
    let msg = T[c.type] || (/node|map/.test(c.type) ? T.node : /mission/.test(c.type) ? T.mission : /chest|key/.test(c.type) ? T.chest : T.def);
    msg = msg.replace('{n}', d.level || d.n || d.days || '').replace('{f}', c.type === 'unlock' && unt(d.feature) ? unt(d.feature)[0] : '');
    if (c.data && c.data.xp) msg += ` · +${c.data.xp} XP`;
    if (typeof toast === 'function') toast(msg);
    return new Promise((r) => setTimeout(r, 3200));
  }

  /* ───────────── celebrations ───────────── */
  function queue(list) {
    const seen = new Set(G.cq.map((c) => c.id));
    for (const c of list) if (!seen.has(c.id) && !(G.done || new Set()).has(c.id)) G.cq.push(c);
    runQueue();
  }
  G.done = new Set();
  async function runQueue() {
    if (G.showing || !G.cq.length || G.obOpen) return;
    if (document.querySelector('#gSheet, .nt-modal, .sb-layer, .sai.sai-open, #tkSlide.open')) { setTimeout(runQueue, 1500); return; }
    G.showing = true;
    // merge consecutive XP toasts into one
    let c = G.cq.shift();
    if (c.type === 'xp') { let xp = c.data.xp || 0; const ids = [c.id]; while (G.cq[0] && G.cq[0].type === 'xp') { const n = G.cq.shift(); xp += n.data.xp || 0; ids.push(n.id); } seenIds(ids); await xpFloat(xp); G.showing = false; runQueue(); return; }
    seenIds([c.id]);
    try {
      if (!['sweep'].includes(c.type) && c.type !== 'quest_start' && !isMajor(c)) { await smallToast(c); }
      else if (c.type === 'sweep' && !fresh(c)) { await smallToast(c); }
      else if (isMajor(c) && modalUsed()) { await smallToast(c); }
      else if (isMajor(c) && !useModal()) { await smallToast(c); }
      else if (c.type === 'unlock' && unt(c.data.feature)) { const u = unt(c.data.feature); await infoSheet(UN_IC[c.data.feature] || 'star', u[1], `${(UN_T[L()] || UN_T.en).kick} · ${u[0]}`, 0); }
      else if (c.type === 'crew_goal') await infoSheet('hand', crt('crew_goal_s', { n: c.data.name }), crt('crew_goal'), c.data.xp);
      else if (c.type === 'league_result') { const d = c.data, tn = lgt('tiers.' + d.tier); await infoSheet('shield', lgt('res_r', { r: ord(d.rank), n: d.of }), d.outcome === 'promoted' ? lgt('res_p', { t: tn }) : d.outcome === 'relegated' ? lgt('res_d', { t: tn }) : lgt('res_s', { t: tn }), d.xp); }
      else if (c.type === 'payout_ready') await payoutReady();
      else if (c.type === 'quest_start') { await load(true); questSheet(); await waitSheetClose(document.getElementById('gSheet')); }
      else if (c.type === 'quest_done') await infoSheet('fire', c.data.restore ? wt('quest_done_sub', { n: c.data.restore }) : wt('quest_done_sub0'), wt('quest_done_t'), c.data.xp);
      else if (c.type === 'boss_spawn') await bossSpawnSheet(c.data);
      else if (c.type === 'boss_defeated') await bossDefeat(c.data);
      else if (await v2Celebrate(c)) { /* handled */ }
      else if (c.type === 'sweep') await sweepAnim(c.data);
      else if (c.type === 'badge') await badgeSheet(c.data);
      else if (c.type === 'level') await levelSheet(c.data);
      else if (c.type === 'streak') await streakSheet(c.data);
      else if (c.type === 'freeze_used') await infoSheet('snow', t('freeze_used', { day: fdate(c.data.day, { weekday: 'long' }) }));
      else if (c.type === 'streak_lost') await infoSheet('fire', t('streak_lost', { n: c.data.best }));
      else if (c.type === 'guardrail') await infoSheet('shield', t('guardrail_msg'), t('guardrail_t'), c.data.xp);
      else if (c.type === 'backfill') await infoSheet('star', t('backfill', { xp: c.data.xp, n: (c.data.badges || []).length }));
    } catch (e) { /* never block */ }
    G.showing = false;
    if (!G.cq.length && TS.extra) summaryToast();
    setTimeout(runQueue, 250);
  }
  function seenIds(ids) {
    ids.forEach((i) => G.done.add(i));
    apiJSON('api/game/celebrations/seen', { method: 'POST', body: { ids } }).catch(() => {});
  }
  function xpFloat(xp, label) {
    return new Promise((res) => {
      const el = document.createElement('div');
      el.className = 'g-xpf'; el.setAttribute('data-noi18n', ''); el.textContent = label || t('plus_xp', { n: xp });
      document.body.append(el);
      const a = el.animate(reduced() ? [{ opacity: 0 }, { opacity: 1, offset: .2 }, { opacity: 1, offset: .8 }, { opacity: 0 }]
        : [{ opacity: 0, transform: 'translate(-50%,12px) scale(.9)' }, { opacity: 1, transform: 'translate(-50%,0) scale(1)', offset: .18 }, { opacity: 1, transform: 'translate(-50%,-6px)', offset: .8 }, { opacity: 0, transform: 'translate(-50%,-18px)' }],
        { duration: 1500, easing: 'cubic-bezier(.32,.72,0,1)' });
      a.onfinish = () => { el.remove(); res(); };
    });
  }
  function waitSheetClose(el) { return new Promise((res) => { const iv = setInterval(() => { if (!document.body.contains(el) || !el.classList.contains('open')) { clearInterval(iv); res(); } }, 200); }); }
  const medal = (id, rarity, big) => `<span class="g-medal r-${rarity} ${big ? 'big' : ''}">${svg(BADGE_IC[id] || 'star')}</span>`;
  async function badgeSheet(b) {
    const el = openSheet(`<div class="g-cel">${medal(b.id, b.rarity, true)}<span class="g-kick">${t('new_badge')}</span><h2>${esc(bName(b.id))}</h2><p>${esc(bDesc(b.id))}</p>${b.xp ? `<span class="g-xp">${t('plus_xp', { n: b.xp })}</span>` : ''}
      <div class="g-acts">${b.rarity !== 'common' ? `<button type="button" class="btn" data-g="share" data-k="badge" data-v="${esc(b.id)}">${svg('share')}${t('share')}</button>` : ''}<button type="button" class="btn primary" data-g="close">${t('continue')}</button></div></div>`, { cls: 'g-celsheet' });
    pop(el.querySelector('.g-medal')); buzz(15); chime();
    await waitSheetClose(el);
  }
  async function levelSheet(l) {
    const el = openSheet(`<div class="g-cel">${l.rank_up ? `<span class="g-medal r-epic big">${CANDLE()}</span><span class="g-kick">${t('rank_up')}</span><h2>${esc(rankName(l.rank))}</h2><p>${t('level_up', { n: l.level })}</p>` : `<span class="g-lvlbig">${l.level}</span><span class="g-kick">${t('level')}</span><h2>${t('level_up', { n: l.level })}</h2><p>${esc(rankName(l.rank))}</p>`}
      <div class="g-acts">${l.rank_up ? `<button type="button" class="btn" data-g="share" data-k="rank" data-v="${esc(l.rank)}">${svg('share')}${t('share')}</button>` : ''}<button type="button" class="btn primary" data-g="close">${t('continue')}</button></div></div>`, { cls: 'g-celsheet' });
    pop(el.querySelector('.g-medal, .g-lvlbig')); buzz(12);
    await waitSheetClose(el);
  }
  async function streakSheet(s) {
    const el = openSheet(`<div class="g-cel"><span class="g-medal r-epic big g-stk">${CANDLE()}<b>${s.n}</b></span><span class="g-kick">${t('streak_card')}</span><h2>${t('streak_title', { n: s.n })}</h2>${s.xp ? `<span class="g-xp gold">${t('plus_xp', { n: s.xp })}</span>` : ''}
      <div class="g-acts"><button type="button" class="btn" data-g="share" data-k="streak" data-v="${s.n}">${svg('share')}${t('share')}</button><button type="button" class="btn primary" data-g="close">${t('continue')}</button></div></div>`, { cls: 'g-celsheet' });
    pop(el.querySelector('.g-medal')); buzz(15);
    await waitSheetClose(el);
  }
  async function infoSheet(icon, msg, title, xp) {
    const el = openSheet(`<div class="g-cel"><span class="g-medal r-common big">${svg(icon)}</span>${title ? `<h2>${esc(title)}</h2>` : ''}<p class="g-msg">${esc(msg)}</p>${xp ? `<span class="g-xp">${t('plus_xp', { n: xp })}</span>` : ''}
      <div class="g-acts"><button type="button" class="btn primary" data-g="close">${t('continue')}</button></div></div>`, { cls: 'g-celsheet' });
    pop(el.querySelector('.g-medal'));
    await waitSheetClose(el);
  }
  function pop(node) {
    if (!node || reduced()) return;
    node.animate([{ transform: 'scale(.4) rotate(-12deg)', opacity: 0 }, { transform: 'scale(1.08) rotate(3deg)', opacity: 1, offset: .65 }, { transform: 'scale(1) rotate(0)', opacity: 1 }], { duration: 650, easing: 'cubic-bezier(.34,1.56,.64,1)', delay: 120, fill: 'backwards' });
  }

  /* The signature: rings close, melt into one, the candle draws itself and sweeps below the line. */
  function sweepAnim(data) {
    return new Promise((res) => {
      const ov = document.createElement('div');
      ov.className = 'g-sweep'; ov.setAttribute('data-noi18n', ''); ov.setAttribute('role', 'dialog'); ov.setAttribute('aria-label', t('swept_title'));
      const prev = lsGetJ('g.rings.today', { plan: 100, execution: 100, review: 80 });
      ov.innerHTML = `<div class="g-sw-bg"></div><div class="g-sw-c">
        <svg class="g-sw-svg" viewBox="0 0 200 200" aria-hidden="true">
          <g class="g-sw-rings">${[['plan', 78], ['execution', 62], ['review', 46]].map(([k, r]) => { const c = 2 * Math.PI * r; const from = Math.min(99, prev[k] || 0); return `<circle class="g-track g-${k}" cx="100" cy="100" r="${r}" stroke-width="12"/><circle class="g-arc g-${k} sw-${k}" cx="100" cy="100" r="${r}" stroke-width="12" stroke-dasharray="${c.toFixed(2)}" stroke-dashoffset="${(c * (1 - from / 100)).toFixed(2)}" transform="rotate(-90 100 100)"/>`; }).join('')}</g>
          <circle class="g-sw-one" cx="100" cy="100" r="62" stroke-width="12" fill="none" opacity="0"/>
          <line class="g-sw-line" x1="56" y1="140" x2="144" y2="140" opacity="0"/>
          <g class="g-sw-candle" opacity="0"><line class="c-top" x1="100" y1="58" x2="100" y2="72"/><rect class="c-body" x="88" y="70" width="24" height="40" rx="5"/><line class="c-mid" x1="100" y1="108" x2="100" y2="120"/><line class="c-wick" x1="100" y1="120" x2="100" y2="150"/></g>
        </svg>
        <h2 class="g-sw-t">${esc(t('swept_title'))}</h2><span class="g-sw-xp">${t('plus_xp', { n: data.xp || 50 })}</span>
        <div class="g-sw-acts"><button type="button" class="btn" data-g="share" data-k="sweep">${svg('share')}${t('share')}</button><button type="button" class="btn primary" data-g="sw-close">${t('continue')}</button></div></div>`;
      document.body.append(ov);
      lsSetJ('g.rings.today', { plan: 100, execution: 100, review: 100 });
      const q = (s) => ov.querySelector(s);
      const close = () => { ov.classList.add('out'); setTimeout(() => { ov.remove(); res(); }, reduced() ? 150 : 280); };
      ov.addEventListener('click', (e) => { if (e.target.closest('[data-g="sw-close"]') || e.target.classList.contains('g-sw-bg')) close(); });
      buzz([20, 40, 30]); chime();
      if (reduced()) {
        ['.g-sw-rings', '.g-sw-candle', '.g-sw-line'].forEach((s) => q(s).setAttribute('opacity', s === '.g-sw-rings' ? '0' : '1'));
        ov.querySelectorAll('.g-arc').forEach((a) => a.setAttribute('stroke-dashoffset', '0'));
        ov.classList.add('in', 'done'); return;
      }
      ov.classList.add('in');
      const spring = 'cubic-bezier(.34,1.56,.64,1)', ios = 'cubic-bezier(.32,.72,0,1)';
      // 0–300 ms: the last ring(s) close with a spring
      ov.querySelectorAll('.g-arc').forEach((a) => a.animate([{ strokeDashoffset: a.getAttribute('stroke-dashoffset') }, { strokeDashoffset: 0 }], { duration: 420, easing: spring, fill: 'forwards' }));
      // 300–700 ms: rings melt into one circle
      q('.g-sw-rings').animate([{ opacity: 1, transform: 'scale(1)' }, { opacity: 0, transform: 'scale(.86)' }], { duration: 380, delay: 320, easing: ios, fill: 'forwards' });
      q('.g-sw-one').animate([{ opacity: 0, strokeWidth: 30 }, { opacity: 1, strokeWidth: 6 }], { duration: 380, delay: 360, easing: ios, fill: 'forwards' });
      // the candle draws itself
      const cand = q('.g-sw-candle');
      cand.animate([{ opacity: 0 }, { opacity: 1 }], { duration: 200, delay: 420, fill: 'forwards' });
      q('.c-body').animate([{ transform: 'scaleY(0)' }, { transform: 'scaleY(1)' }], { duration: 300, delay: 460, easing: spring, fill: 'backwards' });
      // 700–1100 ms: the wick sweeps below the line, then the body springs back up
      q('.g-sw-line').animate([{ opacity: 0, transform: 'scaleX(0)' }, { opacity: 1, transform: 'scaleX(1)' }], { duration: 300, delay: 650, easing: ios, fill: 'forwards' });
      q('.c-wick').animate([{ strokeDashoffset: 30 }, { strokeDashoffset: 0 }], { duration: 260, delay: 720, easing: ios, fill: 'backwards' });
      cand.animate([{ transform: 'translateY(0)' }, { transform: 'translateY(10px)', offset: .4 }, { transform: 'translateY(-6px)', offset: .75 }, { transform: 'translateY(0)' }], { duration: 520, delay: 760, easing: ios });
      // 1100–1600 ms: title + XP
      q('.g-sw-t').animate([{ opacity: 0, transform: 'translateY(10px)' }, { opacity: 1, transform: 'none' }], { duration: 420, delay: 1100, easing: ios, fill: 'backwards' });
      q('.g-sw-xp').animate([{ opacity: 0, transform: 'translateY(14px)' }, { opacity: 1, transform: 'none' }], { duration: 500, delay: 1250, easing: ios, fill: 'backwards' });
      q('.g-sw-acts').animate([{ opacity: 0 }, { opacity: 1 }], { duration: 300, delay: 1500, fill: 'backwards' });
    });
  }

  /* one short, soft sound (off by default, Progress → Sweep sound) */
  function chime() {
    if (!G.profile || !G.profile.sound) return;
    try {
      const ac = new (window.AudioContext || window.webkitAudioContext)(), o = ac.createOscillator(), g = ac.createGain();
      o.type = 'sine'; o.frequency.setValueAtTime(880, ac.currentTime); o.frequency.exponentialRampToValueAtTime(1320, ac.currentTime + 0.18);
      g.gain.setValueAtTime(0.0001, ac.currentTime); g.gain.exponentialRampToValueAtTime(0.08, ac.currentTime + 0.03); g.gain.exponentialRampToValueAtTime(0.0001, ac.currentTime + 0.6);
      o.connect(g); g.connect(ac.destination); o.start(); o.stop(ac.currentTime + 0.62);
    } catch (e) { /* audio blocked */ }
  }

  /* ───────────── Progression page (#progress) ───────────── */
  /* ───────────── Progress lives where it is useful: Insights (rank, streak, this week) and Settings (badges) ───────────── */
  const addD = (d, n) => { const x = new Date(d + 'T12:00:00'); x.setDate(x.getDate() + n); return `${x.getFullYear()}-${String(x.getMonth() + 1).padStart(2, '0')}-${String(x.getDate()).padStart(2, '0')}`; };
  const mondayOf = (d) => addD(d, -((new Date(d + 'T12:00:00').getDay() + 6) % 7));
  async function loadProgress() {
    try {
      const mon = mondayOf(G.today ? G.today.day : todayStr());
      const [p, h] = await Promise.all([apiJSON('api/game/profile'), apiJSON(`api/game/history?from=${mon}&to=${addD(mon, 4)}`)]);
      G.prog = p; G.profile = p.profile; G.week = h; G.progAt = Date.now();
      try { G.cos = await apiJSON('api/game/cosmetics'); } catch (e) { /* optional */ }
      try { G.wrList = (await apiJSON('api/game/wrapped')).items || []; } catch (e) { /* optional */ }
      try { G.social = await apiJSON('api/game/social'); } catch (e) { /* optional */ }
      try { G.dc = await apiJSON('api/game/discord'); } catch (e) { /* optional */ }
      paintSections();
    } catch (e) { /* retry on next render */ }
  }
  function insightsHtml() {
    const P = G.prog;
    if (!P) return '<div class="skel" style="height:132px;border-radius:20px"></div>';
    const p = P.profile, c = P.counters, nr = p.next_rank;
    const pct = Math.max(0, Math.min(100, ((p.xp - p.level_xp) / Math.max(1, p.next_level_xp - p.level_xp)) * 100));
    const w = G.week || { days: [], holidays: [] }, by = {}; (w.days || []).forEach((d) => { by[d.trading_day] = d; });
    const mon = mondayOf(G.today ? G.today.day : todayStr()), today = G.today ? G.today.day : todayStr();
    const days = [0, 1, 2, 3, 4].map((i) => {
      const ds = addD(mon, i), g = by[ds], hol = (w.holidays || []).includes(ds);
      const r = g ? { plan: +g.ring_plan, execution: +g.ring_execution, review: +g.ring_review } : { plan: 0, execution: 0, review: 0 };
      return `<span class="g-wd ${g && +g.is_swept ? 'swept' : ''} ${ds === today ? 'today' : ''} ${hol || ds > today ? 'off' : ''}"><i>${new Date(ds + 'T12:00:00').toLocaleDateString(loc(), { weekday: 'narrow' })}</i>${miniRings(r)}</span>`;
    }).join('');
    return `<div class="gm-ins-rank"><span class="g-medal r-epic">${CANDLE()}</span>
        <div class="gm-ins-rt"><span class="g-kick">${t('rank_card')}</span><b>${esc(rankName(p.rank))}</b><small class="muted">${t('lvl', { n: p.level })} · ${p.xp.toLocaleString(loc())} ${t('xp')}</small>
          <span class="g-bar"><i style="width:${pct}%"></i></span><small class="muted">${nr ? t('next_level', { xp: nr.xp.toLocaleString(loc()), rank: rankName(nr.rank) }) : ''}</small></div>
        <button type="button" class="g-x gm-ins-share" data-g="share" data-k="rank" data-v="${esc(p.rank)}" aria-label="${t('share')}">${svg('share')}</button></div>
      <div class="gm-ins-stats">
        <div><span class="g-streak ${p.streak.today_valid ? 'on' : ''}">${CANDLE()}</span><b>${p.streak.current}</b><small>${t('streak')}</small></div>
        <div><b>${p.streak.best}</b><small>${t('best')}</small></div>
        <div><b>${c.swept}</b><small>${t('swept_days')}</small></div>
        <div><b>${p.streak.freezes}<span class="faint">/${p.streak.quota}</span></b><small>${t('freezes')}</small></div>
      </div>
      <div class="gm-ins-week">${days}</div>`;
  }
  function badgesHtml() {
    const P = G.prog;
    if (!P) return `<div class="sec-h"><h2>${t('badges')}</h2></div><div class="skel" style="height:220px;border-radius:18px"></div>`;
    return `${socialCard()}<div class="sec-h" style="margin-top:18px"><h2>${t('badges')}</h2><span class="help">${P.badges.filter((b) => b.unlocked).length} / ${P.badges.length}</span></div>
      <div class="g-badges">${P.badges.map((b) => `<button type="button" class="g-bdg ${b.unlocked ? 'got' : 'lock'} r-${b.rarity}" data-g="badge" data-v="${b.id}">
        ${b.secret ? `<span class="g-medal r-none">${svg('q')}</span><b>${t('secret')}</b>` : `${medal(b.id, b.unlocked ? b.rarity : 'none')}<b>${esc(bName(b.id))}</b>`}
        ${!b.unlocked && b.progress && b.progress[1] > 1 ? `<small>${b.progress[0]}/${b.progress[1]}</small>` : ''}</button>`).join('')}</div>
      ${themesHtml()}${archiveHtml()}
      <div class="surface pad g-sound"><span><b>${t('sound')}</b><small class="muted">${t('sound_d')}</small></span><label class="sw"><input type="checkbox" data-g-sound ${G.prog.profile.sound ? 'checked' : ''}><i></i></label></div>`;
  }
  function miniRings(r) {
    return `<svg viewBox="0 0 30 30" class="g-mr">${[['plan', 12], ['execution', 8.5], ['review', 5]].map(([k, rad]) => { const c = 2 * Math.PI * rad; return `<circle class="g-track g-${k}" cx="15" cy="15" r="${rad}" stroke-width="2.6"/><circle class="g-arc g-${k}" cx="15" cy="15" r="${rad}" stroke-width="2.6" stroke-dasharray="${c.toFixed(1)}" stroke-dashoffset="${(c * (1 - (r[k] || 0) / 100)).toFixed(1)}" transform="rotate(-90 15 15)"/>`; }).join('')}</svg>`;
  }
  function slot(id, tag, cls, place) {
    let el = document.getElementById(id);
    if (!el) { el = document.createElement(tag); el.id = id; el.className = cls; el.setAttribute('data-noi18n', ''); place(el); }
    return el;
  }
  function paintSections() {
    const main = document.getElementById('main');
    if (!main || !on() || typeof route !== 'function') return;
    const v = route().v;
    if (v !== 'analytics') return;
    if (v === 'analytics') {
      const el = slot('gIns', 'section', 'gm-ins surface', (e) => main.prepend(e));
      const h = insightsHtml(); if (el._h !== h) { el.innerHTML = h; el._h = h; }
    } else {
      const el = slot('gBdg', 'section', 'sec g-bdgsec', (e) => { const first = main.querySelector(':scope > section'); first ? first.after(e) : main.prepend(e); });
      const h = badgesHtml(); if (el._h !== h) { el.innerHTML = h; el._h = h; }
    }
    if ((!G.prog || Date.now() - (G.progAt || 0) > 30000) && !G.progLoading) { G.progLoading = true; loadProgress().finally(() => { G.progLoading = false; }); }
  }
  function badgeInfo(id) {
    const b = (G.prog && G.prog.badges || []).find((x) => x.id === id);
    if (!b) return;
    openSheet(`<div class="g-cel">${b.secret ? `<span class="g-medal r-none big">${svg('q')}</span><h2>${t('secret')}</h2>` : `${medal(b.id, b.unlocked ? b.rarity : 'none', true)}<h2>${esc(bName(b.id))}</h2><p>${esc(bDesc(b.id))}</p>`}
      ${!b.unlocked && b.progress && b.progress[1] > 1 ? `<span class="g-bar"><i style="width:${(b.progress[0] / b.progress[1]) * 100}%"></i></span><small class="muted">${b.progress[0]} / ${b.progress[1]}</small>` : ''}
      ${b.unlocked && b.unlocked_at ? `<small class="muted">${new Date(b.unlocked_at * 1000).toLocaleDateString(loc(), { month: 'long', day: 'numeric', year: 'numeric' })}</small>` : ''}
      ${b.xp ? `<span class="g-xp">${t('plus_xp', { n: b.xp })}</span>` : ''}
      <div class="g-acts">${b.unlocked && b.rarity !== 'common' ? `<button type="button" class="btn" data-g="share" data-k="badge" data-v="${b.id}">${svg('share')}${t('share')}</button>` : ''}<button type="button" class="btn primary" data-g="close">${t('continue')}</button></div></div>`, { cls: 'g-celsheet' });
  }

  /* ───────────── onboarding (60 s) ───────────── */
  const OB = { step: 0, goal: null, style: null, inst: new Set(), maxLoss: '', steps: [] };
  /* ───────────── « + » at the start of the day: the plan first, once ───────────── */
  const skipKey = 'sw.planSkip';
  function planGateNeeded() {
    return false;   // no automatic plan before the first trade: the routine card offers it (step Plan)
    const d = G.today; if (!on() || !d || !d.market || d.plan_valid) return false;
    const pre = (journalOf(d.day).pre || {}); if (pre.bias) return false;          // a plan (or « no trading today ») already exists
    try { if (localStorage.getItem(skipKey) === d.day) return false; } catch (e) { /* private mode */ }
    return true;
  }
  (function wrapTicket(n) {
    if (typeof window.openTicket !== 'function') { if (n < 40) setTimeout(() => wrapTicket(n + 1), 100); return; }
    if (window.openTicket.__gated) return;
    const orig = window.openTicket;
    const gated = function (id) {
      if (!id && !document.getElementById('gSheet') && planGateNeeded()) { const args = arguments, self = this; openPlan(G.today.day, { then: () => orig.apply(self, args) }); return; }
      return orig.apply(this, arguments);
    };
    gated.__gated = true; window.openTicket = gated;
  })(0);
  /** « Goal and style » step of the journey: the same two questions as the welcome, opened on demand */
  function openGoalQuestions() {
    const p = G.profile; if (!p || document.getElementById('gOb')) return;   // opened on demand: only one at a time
    OB.steps = ['goal', 'win']; OB.step = 0; OB.goal = p.onboarding.goal; OB.style = p.onboarding.style; OB.inst = new Set(p.onboarding.instruments || []);
    G.obOpen = true;
    const el = document.createElement('div');
    el.className = 'g-ob'; el.id = 'gOb'; el.setAttribute('data-noi18n', ''); el.setAttribute('role', 'dialog'); el.setAttribute('aria-modal', 'true');
    document.body.append(el); obRender(); requestAnimationFrame(() => el.classList.add('in'));
  }
  function maybeOnboarding() {
    return;   // no automatic welcome window: the goal and style questions open from the journey step « Goal and style »
    const p = G.profile;
    if (!p || p.onboarding.seen || G.obOpen || !S.accounts) return;
    if (modalUsed()) return;   // one automatic modal per session: it will open next time
    if (!S.accounts.length && !(S.trades || []).length) return;     // the app's own first-account screen goes first
    // first value first: the profile questions wait until the first real trade is logged (or day 2)
    if (!(S.trades || []).some((t) => !t.demo) && !(p.started_on && p.started_on < todayStr())) return;
    if (document.querySelector('#gSheet, .nt-modal, .sb-layer, #tkSlide.open')) { setTimeout(maybeOnboarding, 2000); return; }
    OB.steps = ['goal', 'win'];   // two screens: the firm and its rules were set by the account preset
    OB.step = 0; OB.goal = p.onboarding.goal; OB.style = p.onboarding.style; OB.inst = new Set(p.onboarding.instruments || []);
    useModal();
    G.obOpen = true;
    const el = document.createElement('div');
    el.className = 'g-ob'; el.id = 'gOb'; el.setAttribute('data-noi18n', ''); el.setAttribute('role', 'dialog'); el.setAttribute('aria-modal', 'true');
    document.body.append(el);
    obRender();
    requestAnimationFrame(() => el.classList.add('in'));
  }
  function obRender(dir = 1) {
    const el = document.getElementById('gOb'); if (!el) return;
    const s = OB.steps[OB.step], dots = OB.steps.map((_, i) => `<i class="${i <= OB.step ? 'on' : ''}"></i>`).join('');
    let body = '';
    if (s === 'goal') {
      body = `<div class="g-ob-logo">${CANDLE('draw')}</div><h1>${t('ob_hello')}</h1><p class="muted">${t('ob_hello_sub')}</p><h2>${t('ob_goal')}</h2>
        <div class="g-ob-opts">${['evaluation', 'payout', 'consistency', 'edge'].map((g) => `<button type="button" class="${OB.goal === g ? 'on' : ''}" data-g="ob-goal" data-v="${g}">${svg({ evaluation: 'flag', payout: 'star', consistency: 'cal', edge: 'target' }[g])}<span>${t('g_' + g)}</span></button>`).join('')}</div>`;
    } else if (s === 'style') {
      body = `<h2>${t('ob_style')}</h2><div class="g-seg3 big">${['scalp', 'intraday', 'swing'].map((v) => `<button type="button" class="${OB.style === v ? 'on' : ''}" data-g="ob-style" data-v="${v}">${t(v)}</button>`).join('')}</div>
        <h3>${t('instruments')}</h3><div class="g-chips-row wrap">${['NQ', 'ES', 'MNQ', 'MES', 'CL', 'GC', 'OTHER'].map((v) => `<button type="button" class="chip ${OB.inst.has(v) ? 'on' : ''}" data-g="ob-inst" data-v="${v}">${v === 'OTHER' ? t('other') : v}</button>`).join('')}</div>
        <div class="g-profile-host">${OB.style ? profileCard() : ''}</div>`;
    } else if (s === 'account') {
      const a = (S.accounts || []).find((x) => !x.demo && x.rules && x.rules.dll_c);
      body = a ? `<span class="g-medal r-rare big">${svg('shield')}</span><h2>${t('ob_rules')}</h2><p class="muted">${t('ob_rules_sub', { acct: esc(typeof acctLabel === 'function' ? acctLabel(a.id) : a.name), v: typeof moneyU === 'function' ? moneyU(a.rules.dll_c) : '$' + a.rules.dll_c / 100 })}</p>`
        : `<h2>${t('ob_account')}</h2><label class="g-f"><span>${t('ob_maxloss')}</span><input inputmode="decimal" data-g-obml value="${esc(OB.maxLoss)}" placeholder="$ 500"></label>`;
    } else {
      const pct = G.start ? G.start.percent : 20, hasTrade = (S.trades || []).some((x) => !x.demo);
      const mk = G.today && G.today.market;
      body = `<h2>${t('ob_win')}</h2><div class="g-start big"><span class="g-start-l"><b>${t('start_title')}</b><span>${pct} %</span></span><span class="g-bar"><i style="width:0" data-to="${pct}"></i></span></div>
        <button type="button" class="g-mission" data-g="ob-mission" data-v="${hasTrade ? 'journal' : 'plan'}">${svg(hasTrade ? 'book' : 'flag')}<span><b>${hasTrade ? t('ob_mission_journal') : (mk ? t('ob_mission_plan') : t('ob_mission_plan_t'))}</b><small>${t('ob_reward')}</small></span>${svg('chev', 'g-chev')}</button>`;
    }
    const last = OB.step === OB.steps.length - 1;
    el.innerHTML = `<div class="g-ob-in"><div class="g-ob-top"><span class="g-ob-dots">${dots}</span><button type="button" class="link" data-g="ob-skip">${t('ob_skip')}</button></div>
      <div class="g-ob-body">${body}</div>
      <button type="button" class="btn primary g-big" data-g="ob-next" ${(s === 'goal' && !OB.goal) || (s === 'style' && !OB.style) ? 'disabled' : ''}>${last ? t('ob_go') : t('ob_next')}</button></div>`;
    const b = el.querySelector('.g-ob-body');
    if (!reduced()) b.animate([{ opacity: 0, transform: `translateX(${dir * 30}px)` }, { opacity: 1, transform: 'none' }], { duration: 380, easing: 'cubic-bezier(.32,.72,0,1)' });
    const bar = el.querySelector('[data-to]'); if (bar) requestAnimationFrame(() => requestAnimationFrame(() => { bar.style.width = bar.dataset.to + '%'; }));
    const lg = el.querySelector('.g-ob-logo .g-candle'); if (lg && !reduced()) lg.animate([{ transform: 'translateY(16px) scale(.8)', opacity: 0 }, { transform: 'none', opacity: 1 }], { duration: 700, easing: 'cubic-bezier(.34,1.56,.64,1)' });
  }
  const profileLine = () => `${t(OB.style)}${OB.inst.size ? ' · ' + [...OB.inst].map((x) => (x === 'OTHER' ? t('other') : x)).join(' · ') : ''}`;
  const profileCard = () => `<div class="g-profile-card"><span class="g-kick">${t('ob_profile')}</span><b>${profileLine()}</b><small>${OB.goal ? t('g_' + OB.goal) : ''}</small></div>`;
  /** a choice only updates what changed: no re-render, no flash */
  function obUpdate() {
    const el = document.getElementById('gOb'); if (!el) return;
    el.querySelectorAll('[data-g=ob-goal]').forEach((b) => b.classList.toggle('on', b.dataset.v === OB.goal));
    el.querySelectorAll('[data-g=ob-style]').forEach((b) => b.classList.toggle('on', b.dataset.v === OB.style));
    el.querySelectorAll('[data-g=ob-inst]').forEach((b) => b.classList.toggle('on', OB.inst.has(b.dataset.v)));
    const s = OB.steps[OB.step], nx = el.querySelector('[data-g=ob-next]');
    if (nx) nx.disabled = (s === 'goal' && !OB.goal) || (s === 'style' && !OB.style);
    const host = el.querySelector('.g-profile-host');
    if (host && OB.style) { const card = host.querySelector('.g-profile-card'); if (card) card.querySelector('b').textContent = profileLine(); else host.innerHTML = profileCard(); }
  }
  async function obSave(extra) {
    const body = Object.assign({ goal: OB.goal, style: OB.style, instruments: [...OB.inst] }, extra || {});
    try { const r = await apiJSON('api/game/onboarding', { method: 'POST', body }); if (r.start) G.start = r.start; if (r.profile) G.profile = r.profile; if (r.celebrations) queue(r.celebrations); } catch (e) { /* keep going */ }
  }
  async function obNext() {
    const s = OB.steps[OB.step];
    if (s === 'account') { const v = document.querySelector('[data-g-obml]'); OB.maxLoss = v ? v.value : ''; await obSave(OB.maxLoss ? { max_loss: parseFloat(OB.maxLoss.replace(/[^0-9.]/g, '')) } : {}); }
    else if (s === 'goal' || s === 'style') obSave();
    if (OB.step < OB.steps.length - 1) { OB.step++; buzz(6); obRender(1); return; }
    obClose();
  }
  async function obClose(mission) {
    await obSave({ seen: true });
    const el = document.getElementById('gOb');
    if (el) { el.classList.remove('in'); setTimeout(() => el.remove(), 300); }
    G.obOpen = false;
    paint();
    if (mission === 'journal') { const lastT = (S.trades || []).filter((x) => !x.demo).sort((a, b) => (b.date + b.entry_time).localeCompare(a.date + a.entry_time))[0]; if (lastT) { JN.ids = [lastT.id]; JN.i = 0; setTimeout(() => openSheet(journalHtml(), { cls: 'g-jn' }), 350); } }
    else if (mission === 'plan') setTimeout(() => openPlan(), 350);
    setTimeout(runQueue, 1200);
  }

  /* ───────────── share cards (1080×1920, never any amount — except the payouts received, when the trader adds them to the week's card) ───────────── */
  async function shareCard(kind, v) {
    const W = 1080, H = 1920, cv = document.createElement('canvas'); cv.width = W; cv.height = H;
    const x = cv.getContext('2d');
    try { await Promise.all([document.fonts.load('600 120px Geist'), document.fonts.load('500 40px Geist')]); } catch (e) { /* system font */ }
    const F = 'Geist, -apple-system, "SF Pro Display", system-ui, sans-serif', BLUE = '#4C8DFF', GOLD = '#D4A24C', TXT = '#F2F2F3', MUT = '#9A9AA2';
    x.fillStyle = '#0B0B0C'; x.fillRect(0, 0, W, H);
    let g = x.createRadialGradient(W * .5, H * .38, 0, W * .5, H * .38, W * .9); g.addColorStop(0, 'rgba(76,141,255,.20)'); g.addColorStop(1, 'rgba(76,141,255,0)'); x.fillStyle = g; x.fillRect(0, 0, W, H);
    // logo
    const logo = (cx, cy, s, wick = BLUE, body = TXT) => { x.save(); x.translate(cx - 60 * s, cy - 59 * s); x.scale(s, s); x.lineCap = 'round'; x.strokeStyle = body; x.fillStyle = body; x.lineWidth = 7; x.beginPath(); x.moveTo(60, 14); x.lineTo(60, 30); x.stroke(); rr(46, 28, 28, 44, 6); x.fill(); x.lineCap = 'butt'; x.beginPath(); x.moveTo(60, 70); x.lineTo(60, 84); x.stroke(); x.lineCap = 'round'; x.strokeStyle = wick; x.beginPath(); x.moveTo(60, 84); x.lineTo(60, 104); x.stroke(); x.restore(); };
    const rr = (a, b, w, h, r) => { x.beginPath(); x.moveTo(a + r, b); x.arcTo(a + w, b, a + w, b + h, r); x.arcTo(a + w, b + h, a, b + h, r); x.arcTo(a, b + h, a, b, r); x.arcTo(a, b, a + w, b, r); x.closePath(); };
    logo(140, 170, .9); x.fillStyle = TXT; x.font = `500 58px ${F}`; x.textBaseline = 'middle'; x.fillText('sweep', 196, 172);
    const cx = W / 2, cy = 820;
    let title = '', sub = t('share_sub'), tone = BLUE;
    if (kind === 'sweep') {
      [[300, BLUE], [236, '#7FA9FF'], [172, '#2E6BE0']].forEach(([r, col]) => { x.beginPath(); x.arc(cx, cy, r, 0, Math.PI * 2); x.strokeStyle = col; x.lineWidth = 46; x.lineCap = 'round'; x.stroke(); });
      logo(cx, cy, 1.5); title = t('share_sweep');
    } else if (kind === 'wrapped' && G.wr) {
      const d = G.wr.data;
      [[300, BLUE], [236, '#7FA9FF'], [172, '#2E6BE0']].forEach(([r, col], i) => { x.beginPath(); x.arc(cx, cy, r, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * Math.min(1, (d.kind === 'year' ? [Math.min(1, d.swept / 200), Math.min(1, d.best_streak / 60), 1] : [d.swept / Math.max(1, d.market_days), d.active_days / Math.max(1, d.market_days), 1])[i])); x.strokeStyle = col; x.lineWidth = 46; x.lineCap = 'round'; x.stroke(); });
      x.fillStyle = TXT; x.font = `600 220px ${F}`; x.textAlign = 'center'; x.textBaseline = 'middle'; x.fillText(String(d.swept), cx, cy + 10); x.textAlign = 'left'; x.textBaseline = 'alphabetic';
      title = d.kind === 'year' ? wrt('ycard', { y: d.year }) : wrt('card_t', { m: monthName(d.month) }); sub = d.kind === 'year' ? wrt('ycard_s', { n: d.swept, s: d.best_streak }) : wrt('card_s', { n: d.swept, s: d.best_streak });
    } else if (kind === 'week' && WK.data) {   // the week's recap (brief 01 step 5): discipline first, no amount unless the trader adds the payouts received
      const d = WK.data, sm = d.summary || { days: [], swept: 0, streak: 0 }, b = weekBrief(d.week, sm), first = String((S.me && S.me.first_name) || '').trim();
      const fit = (str, w, wt, fs, min) => { x.font = `${wt} ${fs}px ${F}`; while (x.measureText(str).width > w && fs > min) { fs -= 4; x.font = `${wt} ${fs}px ${F}`; } };
      x.textAlign = 'center'; x.textBaseline = 'alphabetic'; x.fillStyle = TXT;
      const ttl = first ? wq('sh_t', { name: first }) : wq('sh_t0'); fit(ttl, W - 160, 600, 88, 48); x.fillText(ttl, cx, 420);
      x.fillStyle = MUT; x.font = `400 44px ${F}`; x.fillText(weekRecap(d.week).range, cx, 492);
      (sm.days || []).slice(0, 5).forEach((dy, i) => {   // the 5 days' rings
        const rx = 180 + i * 180, ry = 690, rg = dy.rings || {};
        [['plan', 64, BLUE], ['execution', 46, '#7FA9FF'], ['review', 28, '#2E6BE0']].forEach(([k, rad, col]) => {
          x.lineWidth = 14; x.lineCap = 'round'; x.beginPath(); x.arc(rx, ry, rad, 0, Math.PI * 2); x.strokeStyle = 'rgba(255,255,255,.08)'; x.stroke();
          const v2 = Math.max(0, Math.min(100, +rg[k] || 0)) / 100; if (v2 > 0) { x.beginPath(); x.arc(rx, ry, rad, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * v2); x.strokeStyle = col; x.stroke(); }
        });
        x.fillStyle = dy.market ? MUT : 'rgba(154,154,162,.45)'; x.font = `500 34px ${F}`; x.fillText(new Date(dy.day + 'T12:00:00').toLocaleDateString(loc(), { weekday: 'short' }), rx, ry + 124);
      });
      const rows = [[wq('b_streak'), wq(b.streak === 1 ? 'b_streak_1' : 'b_streak_v', { k: b.streak }).split('{n}').join(b.streak)], [wq('b_disc'), b.disc != null ? b.disc + '\u202f%' : '—'], [wq('b_swept'), wq('b_swept_v', { a: b.swept, b: b.traded })]];
      if (v === 'pay' && b.payouts > 0) rows.push([wq('b_pay'), money(b.payouts, { sign: false }), BLUE]);
      const top = 900, rh = 170; rr(120, top, W - 240, rows.length * rh, 40); x.fillStyle = 'rgba(255,255,255,.05)'; x.fill();
      x.textAlign = 'left';
      rows.forEach(([l, val, col], i) => {
        const y0 = top + i * rh; if (i) { x.fillStyle = 'rgba(255,255,255,.08)'; x.fillRect(170, y0, W - 340, 2); }
        x.fillStyle = MUT; fit(l, W - 340, 400, 38, 28); x.fillText(l, 170, y0 + 66);
        x.fillStyle = col || TXT; fit(val, W - 340, 600, 60, 36); x.fillText(val, 170, y0 + 136);
      });
    } else if (kind === 'payout') {
      x.beginPath(); x.arc(cx, cy, 300, 0, Math.PI * 2); x.strokeStyle = GOLD; x.lineWidth = 40; x.stroke();
      logo(cx, cy, 2.4, GOLD, TXT); title = wrt('pay_t'); tone = GOLD;
    } else if (kind === 'streak') {
      x.beginPath(); x.arc(cx, cy, 300, 0, Math.PI * 2); x.fillStyle = 'rgba(212,162,76,.10)'; x.fill(); x.strokeStyle = 'rgba(212,162,76,.5)'; x.lineWidth = 6; x.stroke();
      logo(cx, cy - 70, 2, GOLD, TXT); x.fillStyle = GOLD; x.font = `600 190px ${F}`; x.textAlign = 'center'; x.fillText(String(v), cx, cy + 190); x.textAlign = 'left';
      title = t('share_streak', { n: v }); tone = GOLD;
    } else {
      const isRank = kind === 'rank';
      const rare = isRank || kind === 'chapter' || kind === 'boss' || ['rare', 'epic'].includes(((G.prog && G.prog.badges) || []).find((b) => b.id === v)?.rarity);
      const col = rare ? GOLD : BLUE;
      x.beginPath(); x.arc(cx, cy, 280, 0, Math.PI * 2); const mg = x.createRadialGradient(cx, cy - 80, 20, cx, cy, 280); mg.addColorStop(0, rare ? 'rgba(212,162,76,.35)' : 'rgba(76,141,255,.35)'); mg.addColorStop(1, rare ? 'rgba(212,162,76,.08)' : 'rgba(76,141,255,.08)'); x.fillStyle = mg; x.fill();
      x.strokeStyle = col; x.lineWidth = 8; x.stroke();
      logo(cx, cy, 2.2, col, TXT);
      title = isRank ? t('share_rank', { rank: rankName(v) }) : kind === 'chapter' ? t('v2.ch.' + v) : kind === 'boss' ? bt('share', { name: bossName(v) }) : bName(v); sub = isRank || kind === 'boss' ? t('share_sub') : kind === 'chapter' ? t('v2.ch_done') : t('share_badge'); tone = col;
    }
    x.textAlign = 'center'; x.fillStyle = TXT; x.textBaseline = 'alphabetic';
    if (kind !== 'week') {
      let fs = 96; x.font = `600 ${fs}px ${F}`; while (x.measureText(title).width > W - 160 && fs > 48) { fs -= 6; x.font = `600 ${fs}px ${F}`; }
      x.fillText(title, cx, 1330);
      x.fillStyle = MUT; x.font = `400 44px ${F}`; x.fillText(sub, cx, 1410);
    }
    x.fillStyle = 'rgba(255,255,255,.08)'; x.fillRect(120, 1640, W - 240, 2);
    x.fillStyle = tone; x.font = `500 46px ${F}`; x.fillText('makeitsweep.com', cx, 1730);
    const ref = G.prog && G.prog.ref;
    if (ref) { x.fillStyle = MUT; x.font = `400 36px ${F}`; x.fillText(t('code', { c: ref }), cx, 1790); }
    const blob = await new Promise((r) => cv.toBlob(r, 'image/png'));
    apiJSON('api/game/share', { method: 'POST', body: { kind } }).catch(() => {});
    const file = new File([blob], `sweep-${kind}.png`, { type: 'image/png' });
    if (navigator.canShare && navigator.canShare({ files: [file] })) {
      try { await navigator.share({ files: [file], title: 'Sweep' }); apiJSON('api/game/share', { method: 'POST', body: { kind, shared: true } }).catch(() => {}); return; }
      catch (e) { if (e && e.name === 'AbortError') return; }
    }
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = file.name; document.body.append(a); a.click(); a.remove();
    toast(t('saved'));
  }

  /* ───────────── V2: journey map (replaces « Démarrage ») and weekly missions ───────────── */
  const NODE_IC = { goal: 'target', rules: 'shield', plans: 'flag', journaled: 'book', journaled_full: 'book', reviews: 'eye', swept: 'sweep', setups: 'star',
    edge_reveals: 'spark', weekly_reviews: 'cal', weekly_run: 'cal', best_streak: 'fire', swept_15: 'sweep', perfect_week: 'cal', compliant_best: 'target',
    payout_config: 'shield', payout_ready: 'star', payouts: 'star', accounts: 'book', expenses: 'book', net_positive: 'star', months_70: 'cal' };
  const MIS_IC = { review_days: 'eye', plan_days: 'flag', plan_early_days: 'sun', emotion_trades: 'hand', emotion_days: 'hand', screen_trades: 'eye', swept_days: 'sweep', clean_days: 'target', maxloss_days: 'shield' };
  const MIS_METRIC = { m_review_3: 'review_days', m_plan_3: 'plan_days', m_emotion_5: 'emotion_trades', m_plan_early: 'plan_early_days', m_screens: 'screen_trades', m_sweep_2: 'swept_days', m_no_offplan: 'clean_days', m_review_all: 'review_days', m_sweep_3: 'swept_days', m_emotion_all: 'emotion_days', m_maxloss: 'maxloss_days' };
  const nodeName = (id) => (t('v2.n.' + id) || [id])[0];
  const nodeDesc = (id) => (t('v2.n.' + id) || ['', ''])[1];

  function journeyStrip() {
    const m = G.map; if (!m || !m.current) return '';
    const c = m.current, nx = m.next, pct = Math.round((c.done / Math.max(1, c.total)) * 100);
    const pay = m.payout && m.payout.configured && m.payout.ready >= 70 ? `<span class="gm-pay ${m.payout.ready >= 100 ? 'full' : ''}"><i style="width:${Math.min(100, m.payout.ready)}%"></i><b>${m.payout.ready >= 100 ? t('v2.payout_full') : t('v2.payout_ready')} · ${m.payout.ready} %</b></span>` : '';
    return `<button type="button" class="gm-journey" data-g="map">
        <span class="gm-j-top"><b>${t('v2.chapter', { n: c.pos })} · ${esc(t('v2.ch.' + c.n))}</b><span>${c.done}/${c.total}</span></span>
        <span class="g-bar"><i style="width:${pct}%"></i></span>
        ${nx ? `<span class="gm-j-next">${svg(NODE_IC[nx.metric] || 'star')}<span><small>${t('v2.next')}</small>${esc(nodeName(nx.id))}${nx.target > 1 ? ` · ${nx.progress}/${nx.target}` : ''}</span>${svg('chev', 'g-chev')}</span>` : ''}
      </button>${pay}`;
  }

  function missionsHtml() {
    const ms = G.missions; if (!ms || !ms.missions || !ms.missions.length) return '';
    const ends = new Date(ms.ends * 1000).toLocaleDateString(loc(), { weekday: 'long' });
    return `<div class="sec-h"><h2>${t('v2.missions')}</h2><span class="help">${t('v2.ends', { t: ends })}${ms.keys ? ' · ' + t('v2.keys', { n: ms.keys }) : ''}</span></div>
      <div class="surface gm-mis">${ms.missions.map((x) => `<div class="gm-mrow ${x.done ? 'done' : ''} ${x.locked ? 'locked' : ''}" ${x.locked ? 'data-g="locked"' : ''}>
        <span class="gm-mic d${x.difficulty}">${x.done ? svg('sweep') : svg(MIS_IC[MIS_METRIC[x.mission]] || 'target')}</span>
        <span class="gm-mtx"><b>${esc(t('v2.m.' + x.mission))}</b><span class="g-bar"><i style="width:${(x.progress / Math.max(1, x.target)) * 100}%"></i></span></span>
        <span class="gm-mright">${x.locked ? `${svg('lock', 'gm-lock')}<small>${t('v2.pro')}</small>` : `<b>${x.progress}/${x.target}</b><small>+${x.xp} XP</small>`}
        ${ms.can_reroll && !x.done && !x.locked ? `<button type="button" class="link gm-reroll" data-g="reroll" data-v="${x.id}">${t('v2.reroll')}</button>` : ''}</span></div>`).join('')}</div>`;
  }

  /* map sheet: a vertical path, chapter by chapter */
  async function openMap() {
    openSheet(`${head(t('v2.journey'))}<div class="gm-map"><div class="skel" style="height:420px;border-radius:18px"></div></div>`, { cls: 'gm-mapsheet' });
    try { G.mapFull = await apiJSON('api/game/map'); } catch (e) { return; }
    const box = document.querySelector('#gSheet .gm-map'); if (!box) return;
    box.innerHTML = mapHtml();
    const nx = box.querySelector('.gm-node.next'); if (nx) nx.scrollIntoView({ block: 'center', behavior: reduced() ? 'auto' : 'smooth' });
  }
  function mapHtml() {
    const M = G.mapFull; if (!M) return '';
    const nextId = M.next && M.next.id;
    return M.chapters.map((ch) => {
      const nodes = ch.nodes.map((n, i) => {
        const cls = ['gm-node', n.done ? 'done' : '', n.id === nextId ? 'next' : '', n.soon ? 'soon' : '', i % 2 ? 'r' : 'l'].join(' ');
        return `<button type="button" class="${cls}" data-g="node" data-v="${n.id}" ${ch.locked ? 'disabled' : ''}>
          <span class="gm-dot">${n.done ? svg('sweep') : svg(NODE_IC[n.metric] || 'star')}</span>
          <span class="gm-lab"><b>${esc(nodeName(n.id))}</b><small>${n.done ? fdate(new Date(n.at * 1000).toISOString().slice(0, 10), { month: 'short', day: 'numeric' }) : n.soon ? t('v2.soon') : n.target > 1 ? `${n.progress}/${n.target}` : `+${n.xp} XP`}</small></span></button>`;
      }).join('');
      return `<section class="gm-ch ${ch.done ? 'done' : ''} ${ch.locked ? 'locked' : ''}">
        <header><span class="g-kick">${t('v2.chapter', { n: ch.pos })}</span><h3>${esc(t('v2.ch.' + ch.n))}</h3></header>
        <div class="gm-path">${nodes}</div>
        ${ch.locked ? `<button type="button" class="btn gm-unlock" data-g="locked">${svg('lock')}${t('v2.locked_ch')}</button>` : ''}</section>`;
    }).join('');
  }
  function nodeSheet(id) {
    const M = G.mapFull; if (!M) return;
    let n = null; for (const c of M.chapters) for (const x of c.nodes) if (x.id === id) n = x;
    if (!n) return;
    const act = { goal: 'goal', plans: 'plan', reviews: 'review', journaled: 'journal', journaled_full: 'journal', swept: 'detail', setups: '#settings', rules: '#accounts', payout_config: '#accounts',
      accounts: '#accounts', expenses: '#payouts', payouts: '#payouts', net_positive: '#payouts', payout_ready: '#accounts' }[n.metric];
    const box = document.querySelector('#gSheet .g-in'); if (!box) return;
    box.innerHTML = `<div class="g-head"><button type="button" class="link" data-g="map-back">‹ ${t('v2.back')}</button><button type="button" class="g-x" data-g="close" aria-label="Close">${svg('x')}</button></div>
      <div class="g-cel">${`<span class="g-medal ${n.done ? 'r-common' : 'r-none'} big">${svg(n.done ? 'sweep' : NODE_IC[n.metric] || 'star')}</span>`}<h2>${esc(nodeName(n.id))}</h2><p>${esc(nodeDesc(n.id))}</p>
      ${!n.done && n.target > 1 ? `<span class="g-bar" style="max-width:260px"><i style="width:${(n.progress / n.target) * 100}%"></i></span><small class="muted">${n.progress} / ${n.target}</small>` : ''}
      ${n.soon ? `<small class="muted">${t('v2.soon')}</small>` : `<span class="g-xp">+${n.xp} XP</span>`}
      ${!n.done && act && !n.soon ? `<div class="g-acts"><button type="button" class="btn primary" data-g="node-go" data-v="${act}">${t('v2.go')}</button></div>` : ''}</div>`;
  }
  function nodeGo(act) {
    closeSheet(true);
    if (act[0] === '#') { location.hash = act; return; }
    if (act === 'goal') openGoalQuestions(); else if (act === 'plan') openPlan(); else if (act === 'review') openReview(); else if (act === 'journal') openJournal(); else openDetail(G.today);
  }

  /* V2 celebrations */
  async function v2Celebrate(c) {
    if (c.type === 'node') { await xpFloat(0, (c.data.nodes || []).length === 1 ? t('v2.node_done') + ' · ' + nodeName(c.data.nodes[0]) : t('v2.nodes_done', { n: (c.data.nodes || []).length })); return true; }
    if (c.type === 'mission') return await infoSheet('target', t('v2.m.' + c.data.id), t('v2.mission_done'), c.data.xp), true;
    if (c.type === 'key') return await infoSheet('star', t('v2.key')), true;
    if (c.type === 'map_backfill') return await infoSheet('flag', t('v2.map_backfill', { n: c.data.nodes, xp: c.data.xp })), true;
    if (c.type === 'chapter') {
      const el = openSheet(`<div class="g-cel"><span class="g-medal r-epic big">${svg('flag')}</span><span class="g-kick">${t('v2.ch_done')}</span><h2>${t('v2.chapter', { n: c.data.pos })} · ${esc(t('v2.ch.' + c.data.chapter))}</h2><span class="g-xp gold">${t('plus_xp', { n: c.data.xp })}</span>
        <div class="g-acts"><button type="button" class="btn" data-g="share" data-k="chapter" data-v="${c.data.chapter}">${svg('share')}${t('share')}</button><button type="button" class="btn primary" data-g="close">${t('continue')}</button></div></div>`, { cls: 'g-celsheet' });
      pop(el.querySelector('.g-medal')); buzz([15, 30, 15]); chime();
      await waitSheetClose(el); return true;
    }
    return false;
  }

  /* ───────────── V3: bosses ───────────── */
  const BOSS_T = {
    en: { title: 'Boss', appears: 'A boss appears', defeated: 'You beat {name}', why: 'Why this boss', how: 'How to beat it', hits: 'Hits', rematch: 'Rematch',
      today_hit: 'Hit landed today', today_relapse: 'It healed today', today_pending: 'No hit yet today', hp: '{hp}/{max} HP', clean: 'Each clean day lands a hit. Relapses only heal it: no XP or streak lost.',
      share: 'I beat {name}', intro: '{name} is hiding in your stats. Every clean day lands a hit: {max} and it is gone.',
      wd: ['', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
      n: { revenge: 'The Revenge', fomo_open: 'The Opening FOMO', cursed_day: 'The Cursed Day', oversize: 'The Oversizer', moving_stop: 'The Slipping Stop', overtrader: 'The Overheater', offplan: 'The Improviser', no_plan: 'The Planless' },
      ev: { revenge: '{pct} % of your losses were followed by a new trade within 10 minutes.', fomo_open: '{pct} % of your trades start in the first 5 minutes of the open, averaging {r}R.',
        cursed_day: 'Your {wd} trades average {r}R, versus {others}R on other days.', oversize: 'You sized up after 2 wins in a row {times} times.',
        moving_stop: 'Your stop slipped or rules were partly followed on {pct} % of trades.', overtrader: 'You went past your max number of trades on {pct} % of planned days.',
        offplan: '{pct} % of your trades were outside your plan’s setups.', no_plan: 'No plan before the open on {pct} % of market days.' },
      how_t: { revenge: 'After a loss, wait 10 minutes before the next entry.', fomo_open: 'No trade from 9:30 to 9:35 ET unless it is a planned setup.', cursed_day: 'On {wd}: plan first, and every trade inside your plan.',
        oversize: 'Keep the same size all day.', moving_stop: 'Respect every stop, and follow your rules fully.', overtrader: 'Stay within your max number of trades.', offplan: 'Only take your plan’s setups.', no_plan: 'Make your plan before 9:30 ET.' } },
    fr: { title: 'Boss', appears: 'Un boss apparaît', defeated: 'Tu as battu {name}', why: 'Pourquoi ce boss', how: 'Comment le battre', hits: 'Coups', rematch: 'Revanche',
      today_hit: "Coup porté aujourd'hui", today_relapse: "Il s'est soigné aujourd'hui", today_pending: "Pas encore de coup aujourd'hui", hp: '{hp}/{max} PV', clean: 'Chaque journée propre lui porte un coup. Une rechute le soigne seulement : aucune XP ni streak perdu.',
      share: "J'ai battu {name}", intro: '{name} se cache dans tes stats. Chaque journée propre lui porte un coup : {max} et il disparaît.',
      wd: ['', 'lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi', 'dimanche'],
      n: { revenge: 'Le Revenge', fomo_open: "Le FOMO de l'ouverture", cursed_day: 'Le Jour maudit', oversize: "L'Oversize", moving_stop: 'Le Stop fuyant', overtrader: 'Le Surchauffe', offplan: "L'Improvisateur", no_plan: 'Le Sans-plan' },
      ev: { revenge: "{pct} % de tes pertes ont été suivies d'un nouveau trade en moins de 10 minutes.", fomo_open: "{pct} % de tes trades partent dans les 5 premières minutes de l'ouverture, à {r}R en moyenne.",
        cursed_day: 'Tes trades du {wd} sont à {r}R en moyenne, contre {others}R les autres jours.', oversize: 'Tu as augmenté ta taille après 2 gains de suite {times} fois.',
        moving_stop: 'Ton stop a glissé ou tes règles ont été suivies en partie sur {pct} % des trades.', overtrader: 'Tu as dépassé ton nombre max de trades {pct} % des jours planifiés.',
        offplan: '{pct} % de tes trades étaient hors des setups de ton plan.', no_plan: "Aucun plan avant l'ouverture {pct} % des jours de marché." },
      how_t: { revenge: "Après une perte, attends 10 minutes avant la prochaine entrée.", fomo_open: "Aucun trade de 9 h 30 à 9 h 35 ET, sauf un setup planifié.", cursed_day: 'Le {wd} : plan d’abord, et chaque trade dans ton plan.',
        oversize: 'Garde la même taille toute la journée.', moving_stop: 'Respecte chaque stop et suis tes règles au complet.', overtrader: 'Reste sous ton nombre max de trades.', offplan: 'Ne prends que les setups de ton plan.', no_plan: 'Fais ton plan avant 9 h 30 ET.' } },
    es: { title: 'Jefe', appears: 'Aparece un jefe', defeated: 'Venciste a {name}', why: 'Por qué este jefe', how: 'Cómo vencerlo', hits: 'Golpes', rematch: 'Revancha',
      today_hit: 'Golpe dado hoy', today_relapse: 'Hoy se curó', today_pending: 'Aún sin golpe hoy', hp: '{hp}/{max} PV', clean: 'Cada día limpio le da un golpe. Una recaída solo lo cura: no pierdes XP ni racha.',
      share: 'Vencí a {name}', intro: '{name} se esconde en tus estadísticas. Cada día limpio le da un golpe: {max} y desaparece.',
      wd: ['', 'lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo'],
      n: { revenge: 'La Revancha', fomo_open: 'El FOMO de la apertura', cursed_day: 'El Día maldito', oversize: 'El Sobredimensionado', moving_stop: 'El Stop fugitivo', overtrader: 'El Sobrecalentado', offplan: 'El Improvisador', no_plan: 'El Sin plan' },
      ev: { revenge: 'El {pct} % de tus pérdidas fue seguido de un nuevo trade en menos de 10 minutos.', fomo_open: 'El {pct} % de tus trades empieza en los 5 primeros minutos de la apertura, con {r}R de media.',
        cursed_day: 'Tus trades del {wd} promedian {r}R, frente a {others}R los demás días.', oversize: 'Aumentaste el tamaño tras 2 ganancias seguidas {times} veces.',
        moving_stop: 'Tu stop se movió o seguiste tus reglas en parte en el {pct} % de los trades.', overtrader: 'Superaste tu máximo de trades el {pct} % de los días planificados.',
        offplan: 'El {pct} % de tus trades estuvo fuera de los setups de tu plan.', no_plan: 'Sin plan antes de la apertura el {pct} % de los días de mercado.' },
      how_t: { revenge: 'Tras una pérdida, espera 10 minutos antes de la siguiente entrada.', fomo_open: 'Ningún trade de 9:30 a 9:35 ET salvo un setup planificado.', cursed_day: 'El {wd}: primero el plan, y cada trade dentro del plan.',
        oversize: 'Mantén el mismo tamaño todo el día.', moving_stop: 'Respeta cada stop y sigue tus reglas por completo.', overtrader: 'Quédate dentro de tu máximo de trades.', offplan: 'Toma solo los setups de tu plan.', no_plan: 'Haz tu plan antes de las 9:30 ET.' } },
  };
  const bt = (k, p) => { const d = BOSS_T[L()] || BOSS_T.en; let s = k.split('.').reduce((a, x) => (a == null ? a : a[x]), d); if (s == null) s = k.split('.').reduce((a, x) => (a == null ? a : a[x]), BOSS_T.en); return typeof s === 'string' && p ? s.replace(/\{(\w+)\}/g, (m, x) => (p[x] != null ? p[x] : m)) : s; };
  const bossName = (id) => bt('n.' + id) || id;
  const evParams = (ev) => Object.assign({}, ev, { wd: bt('wd')[ev.weekday || 0] || '', r: ev.r != null ? (ev.r > 0 ? '+' : '') + ev.r : '', others: ev.others != null ? (ev.others > 0 ? '+' : '') + ev.others : '' });
  /** abstract, geometric illustration per boss (no character, no licensed art) */
  const BOSS_ART = {
    revenge: '<path d="M14 50 L32 12 L42 34 Z" class="a"/><path d="M30 52 L48 18 L54 44 Z" class="b"/>',
    fomo_open: '<circle cx="32" cy="32" r="8" class="a"/><circle cx="32" cy="32" r="17" class="o"/><circle cx="32" cy="32" r="25" class="o2"/>',
    cursed_day: '<path d="M40 10 A22 22 0 1 0 40 54 A16 16 0 1 1 40 10 Z" class="a"/><circle cx="46" cy="20" r="3" class="b"/>',
    oversize: '<rect x="12" y="40" width="10" height="12" rx="2" class="b"/><rect x="26" y="28" width="10" height="24" rx="2" class="a"/><rect x="40" y="12" width="12" height="40" rx="2" class="a"/>',
    moving_stop: '<path d="M10 22 H54" class="l"/><path d="M10 34 H54" class="l d"/><path d="M10 46 H54" class="l d2"/><circle cx="48" cy="46" r="5" class="a"/>',
    overtrader: '<g class="a">' + [...Array(12)].map((_, i) => `<circle cx="${14 + (i % 4) * 12}" cy="${18 + Math.floor(i / 4) * 14}" r="${3 + (i % 3)}"/>`).join('') + '</g>',
    offplan: '<path d="M8 44 L20 20 L30 40 L40 14 L56 46" class="z"/><circle cx="56" cy="46" r="4" class="a"/>',
    no_plan: '<rect x="14" y="14" width="36" height="36" rx="6" class="o"/><path d="M26 26 h12 M26 34 h8" class="l d"/><circle cx="44" cy="44" r="6" class="a"/>',
  };
  const bossArt = (id, cls = '') => `<svg class="gb-art ${cls}" viewBox="0 0 64 64" aria-hidden="true">${BOSS_ART[id] || BOSS_ART.revenge}</svg>`;

  async function loadBoss(force) {
    if (!on() || G.bossBusy || (!force && Date.now() - (G.bossAt || 0) < 30000)) return;
    G.bossBusy = true;
    try { G.boss = await apiJSON('api/game/boss?lang=' + L()); G.bossAt = Date.now(); paint(); } catch (e) { /* the game never blocks */ }
    G.bossBusy = false;
  }
  function bossCard() {
    const B = G.boss; if (!B || !B.active || !B.active.length) return '';
    return `<div class="sec-h"><h2>${bt('title')}</h2></div>${B.active.map((b) => {
      const pct = (b.hp / b.hp_max) * 100;
      return `<button type="button" class="surface gb-card" data-g="boss" data-v="${b.row}">
        <span class="gb-art-w">${bossArt(b.boss)}</span>
        <span class="gb-mid"><span class="gb-name"><b>${esc(bossName(b.boss))}</b>${b.variant === 'rematch' ? `<i>${bt('rematch')}</i>` : ''}</span>
          <span class="gb-hp" style="--n:${b.hp_max}">${[...Array(b.hp_max)].map((_, i) => `<s class="${i < b.hp ? 'on' : ''}"></s>`).join('')}</span>
          <small class="gb-today ${b.today}">${bt('today_' + b.today)}</small></span>
        <span class="gb-hpn">${b.hp}<small>/${b.hp_max}</small></span></button>`;
    }).join('')}`;
  }
  function bossSheet(row) {
    const b = (G.boss && G.boss.active || []).find((x) => x.row === +row); if (!b) return;
    const p = evParams(b.evidence);
    openSheet(`${head(esc(bossName(b.boss)), b.variant === 'rematch' ? bt('rematch') : bt('hp', { hp: b.hp, max: b.hp_max }))}
      <div class="gb-hero">${bossArt(b.boss, 'big')}<span class="gb-hp big" style="--n:${b.hp_max}">${[...Array(b.hp_max)].map((_, i) => `<s class="${i < b.hp ? 'on' : ''}"></s>`).join('')}</span></div>
      <p class="gb-intro">${esc(b.intro || bt('intro', { name: bossName(b.boss), max: b.hp_max }))}</p>
      <div class="gb-blk"><span class="g-kick">${bt('why')}</span><p>${esc(bt('ev.' + b.boss, p))}</p></div>
      <div class="gb-blk"><span class="g-kick">${bt('how')}</span><p>${esc(bt('how_t.' + b.boss, p))}</p><small class="muted">${bt('clean')}</small></div>
      ${b.hits.length ? `<div class="gb-blk"><span class="g-kick">${bt('hits')}</span><div class="gb-hist">${b.hits.map((h) => `<i class="${h.delta < 0 ? 'hit' : 'heal'}" title="${h.day}"></i>`).join('')}</div></div>` : ''}`, { cls: 'gb-sheet' });
  }
  async function bossSpawnSheet(d) {
    const el = openSheet(`<div class="g-cel">${bossArt(d.boss, 'big')}<span class="g-kick">${bt('appears')}</span><h2>${esc(bossName(d.boss))}</h2><p>${esc(bt('how_t.' + d.boss, evParams({})))}</p>
      <div class="g-acts"><button type="button" class="btn primary" data-g="close">${t('continue')}</button></div></div>`, { cls: 'g-celsheet' });
    pop(el.querySelector('.gb-art'));
    await waitSheetClose(el); loadBoss(true);
  }
  /* defeat: the boss dissolves and the candle sweeps through */
  function bossDefeat(d) {
    return new Promise((res) => {
      const ov = document.createElement('div');
      ov.className = 'g-sweep gb-win'; ov.setAttribute('data-noi18n', '');
      ov.innerHTML = `<div class="g-sw-bg"></div><div class="g-sw-c"><div class="gb-stage">${bossArt(d.boss, 'big')}<span class="gb-cand">${CANDLE()}</span></div>
        <h2 class="g-sw-t">${esc(bt('defeated', { name: bossName(d.boss) }))}</h2><span class="g-sw-xp">${t('plus_xp', { n: d.xp })}</span>
        <div class="g-sw-acts"><button type="button" class="btn" data-g="share" data-k="boss" data-v="${esc(d.boss)}">${svg('share')}${t('share')}</button><button type="button" class="btn primary" data-g="sw-close">${t('continue')}</button></div></div>`;
      document.body.append(ov);
      const close = () => { ov.classList.add('out'); setTimeout(() => { ov.remove(); res(); loadBoss(true); }, 260); };
      ov.addEventListener('click', (e) => { if (e.target.closest('[data-g="sw-close"]') || e.target.classList.contains('g-sw-bg')) close(); });
      ov.classList.add('in'); buzz([20, 40, 30]); chime();
      if (reduced()) { ov.classList.add('done'); return; }
      const art = ov.querySelector('.gb-art'), cand = ov.querySelector('.gb-cand');
      art.animate([{ opacity: 1, transform: 'scale(1)', filter: 'blur(0)' }, { opacity: 1, transform: 'scale(1.06)', offset: .25 }, { opacity: 0, transform: 'scale(.6) rotate(-8deg)', filter: 'blur(6px)' }], { duration: 900, easing: 'cubic-bezier(.32,.72,0,1)', fill: 'forwards' });
      cand.animate([{ opacity: 0, transform: 'translateX(-90px) rotate(-20deg)' }, { opacity: 1, transform: 'translateX(0) rotate(0)', offset: .6 }, { opacity: 1, transform: 'translateY(8px)', offset: .8 }, { opacity: 1, transform: 'none' }], { duration: 900, delay: 350, easing: 'cubic-bezier(.34,1.56,.64,1)', fill: 'forwards' });
      ov.querySelector('.g-sw-t').animate([{ opacity: 0, transform: 'translateY(10px)' }, { opacity: 1, transform: 'none' }], { duration: 420, delay: 1000, fill: 'backwards' });
      ov.querySelector('.g-sw-xp').animate([{ opacity: 0 }, { opacity: 1 }], { duration: 400, delay: 1150, fill: 'backwards' });
      ov.querySelector('.g-sw-acts').animate([{ opacity: 0 }, { opacity: 1 }], { duration: 300, delay: 1350, fill: 'backwards' });
    });
  }

  /* ───────────── V2 step 2: weekly recap, chest, Edge Reveal, comeback quest, ring themes ───────────── */
  const W_T = {
    en: { weekly: 'Weekly recap', open_chest: 'Open your chest', w_title: 'Your week', w_swept: 'Days swept', w_streak: 'Streak', w_missions: 'Missions',
      reveal_t: 'Edge Reveal', reveal_tap: 'Tap to reveal your discovery of the week', reveal_locked: 'One Edge Reveal a month on Free. Weekly with Pro.', unlock: 'Unlock with Pro', another: 'Another reveal',
      q_best: 'Best decision of the week', q_fix: 'A pattern to fix', q_int: 'Intention for next week', save_go: 'Save and open the chest',
      chest_t: 'Your chest', chest_key: 'With a key: a richer chest', chest_open: 'Open', odds: 'Possible contents', close: 'Done',
      it_xp: '+{v} XP', it_freeze: '+1 streak freeze', it_cosmetic: 'Ring theme: {v}', it_ai: '+{v} Sweep AI messages today', it_pro: '{v} days of Pro', it_badge: 'Secret badge: Lucky',
      o_xp: 'Bonus XP (25–150)', o_freeze: 'Streak freeze', o_cosmetic: 'Ring theme', o_ai: 'Sweep AI messages', o_pro: '3 days of Pro (Free only)', o_lucky: 'Secret badge',
      intention: 'Intention: {v}', quest: 'Comeback {d}/3', quest_t: 'Good to see you again.', quest_sub: "Let's pick up where you left off. Within 5 market days:",
      qs_review: 'Do a review', qs_plan: 'Plan before the open', qs_sweep: 'Sweep a day', quest_done_t: "You're back.", quest_done_sub: 'Your streak gets {n} days back.', quest_done_sub0: 'Welcome back in the game.',
      themes: 'Ring themes', th: { ring_default: 'Sweep', ring_aurora: 'Aurora', ring_ember: 'Ember', ring_mono: 'Mono', ring_violet: 'Violet', ring_ocean: 'Ocean' },
      wd: ['', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
      tpl: { best_slot: 'Your trades between {start} and {end} average {r}R, your best time slot (overall: {all}R).', best_setup: '“{setup}” is your best setup: {r}R on average over {n} trades.',
        emotion: 'When you feel “{emotion}” before entering, your trades average {r}R. Worth a pause next time.', best_day: '{wd} is your best day: {r}R on average over {n} trades.',
        plan_effect: 'With a plan before the open: {with}R per trade. Without: {without}R.', compliance: 'Trades inside your plan: {in_plan}R. Outside: {off_plan}R. You stay in plan {pct} % of the time.',
        beginner: 'You have logged {trades} trades, {plans} plans and {reviews} reviews. At 20 trades with a stop, your first real edge appears here.' } },
    fr: { weekly: 'Bilan de la semaine', open_chest: 'Ouvrir ton coffre', w_title: 'Ta semaine', w_swept: 'Journées balayées', w_streak: 'Streak', w_missions: 'Missions',
      reveal_t: 'Edge Reveal', reveal_tap: 'Touche pour révéler ta découverte de la semaine', reveal_locked: 'Un Edge Reveal par mois avec Gratuit. Chaque semaine avec Pro.', unlock: 'Débloquer avec Pro', another: 'Un autre reveal',
      q_best: 'Meilleure décision de la semaine', q_fix: 'Un pattern à corriger', q_int: 'Intention pour la semaine prochaine', save_go: 'Enregistrer et ouvrir le coffre',
      chest_t: 'Ton coffre', chest_key: 'Avec une clé : un coffre plus riche', chest_open: 'Ouvrir', odds: 'Contenu possible', close: 'Terminé',
      it_xp: '+{v} XP', it_freeze: '+1 gel de streak', it_cosmetic: 'Thème d’anneaux : {v}', it_ai: '+{v} messages Sweep AI aujourd’hui', it_pro: '{v} jours de Pro', it_badge: 'Badge secret : Chanceux',
      o_xp: 'XP bonus (25–150)', o_freeze: 'Gel de streak', o_cosmetic: 'Thème d’anneaux', o_ai: 'Messages Sweep AI', o_pro: '3 jours de Pro (Gratuit seulement)', o_lucky: 'Badge secret',
      intention: 'Intention : {v}', quest: 'Retour {d}/3', quest_t: 'Content de te revoir.', quest_sub: 'On reprend où tu en étais. D’ici 5 jours de marché :',
      qs_review: 'Faire une revue', qs_plan: 'Plan avant l’ouverture', qs_sweep: 'Balayer une journée', quest_done_t: 'Tu es de retour.', quest_done_sub: 'Ton streak récupère {n} jours.', quest_done_sub0: 'Bon retour dans le jeu.',
      themes: 'Thèmes des anneaux', th: { ring_default: 'Sweep', ring_aurora: 'Aurore', ring_ember: 'Braise', ring_mono: 'Mono', ring_violet: 'Violet', ring_ocean: 'Océan' },
      wd: ['', 'lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi'],
      tpl: { best_slot: 'Tes trades entre {start} et {end} ont un R moyen de {r}R, ton meilleur créneau (global : {all}R).', best_setup: '« {setup} » est ton meilleur setup : {r}R en moyenne sur {n} trades.',
        emotion: 'Quand tu te sens « {emotion} » avant d’entrer, tes trades font {r}R en moyenne. Une pause vaut la peine la prochaine fois.', best_day: 'Le {wd} est ton meilleur jour : {r}R en moyenne sur {n} trades.',
        plan_effect: 'Avec un plan avant l’ouverture : {with}R par trade. Sans : {without}R.', compliance: 'Trades dans ton plan : {in_plan}R. Hors plan : {off_plan}R. Tu restes dans ton plan {pct} % du temps.',
        beginner: 'Tu as journalisé {trades} trades, {plans} plans et {reviews} revues. À 20 trades avec un stop, ton premier vrai edge apparaîtra ici.' } },
    es: { weekly: 'Resumen semanal', open_chest: 'Abrir tu cofre', w_title: 'Tu semana', w_swept: 'Días barridos', w_streak: 'Racha', w_missions: 'Misiones',
      reveal_t: 'Edge Reveal', reveal_tap: 'Toca para revelar tu descubrimiento de la semana', reveal_locked: 'Un Edge Reveal al mes en Gratis. Cada semana con Pro.', unlock: 'Desbloquear con Pro', another: 'Otro reveal',
      q_best: 'Mejor decisión de la semana', q_fix: 'Un patrón a corregir', q_int: 'Intención para la próxima semana', save_go: 'Guardar y abrir el cofre',
      chest_t: 'Tu cofre', chest_key: 'Con una llave: un cofre más rico', chest_open: 'Abrir', odds: 'Contenido posible', close: 'Listo',
      it_xp: '+{v} XP', it_freeze: '+1 congelador de racha', it_cosmetic: 'Tema de anillos: {v}', it_ai: '+{v} mensajes de Sweep AI hoy', it_pro: '{v} días de Pro', it_badge: 'Insignia secreta: Suertudo',
      o_xp: 'XP extra (25–150)', o_freeze: 'Congelador de racha', o_cosmetic: 'Tema de anillos', o_ai: 'Mensajes de Sweep AI', o_pro: '3 días de Pro (solo Gratis)', o_lucky: 'Insignia secreta',
      intention: 'Intención: {v}', quest: 'Regreso {d}/3', quest_t: 'Qué bueno verte de nuevo.', quest_sub: 'Retomamos donde lo dejaste. En 5 días de mercado:',
      qs_review: 'Hacer una revisión', qs_plan: 'Plan antes de la apertura', qs_sweep: 'Barrer un día', quest_done_t: 'Estás de vuelta.', quest_done_sub: 'Tu racha recupera {n} días.', quest_done_sub0: 'Bienvenido de nuevo al juego.',
      themes: 'Temas de anillos', th: { ring_default: 'Sweep', ring_aurora: 'Aurora', ring_ember: 'Brasa', ring_mono: 'Mono', ring_violet: 'Violeta', ring_ocean: 'Océano' },
      wd: ['', 'lunes', 'martes', 'miércoles', 'jueves', 'viernes'],
      tpl: { best_slot: 'Tus trades entre {start} y {end} promedian {r}R, tu mejor franja (global: {all}R).', best_setup: '«{setup}» es tu mejor setup: {r}R de media en {n} trades.',
        emotion: 'Cuando te sientes «{emotion}» antes de entrar, tus trades promedian {r}R. Vale la pena una pausa la próxima vez.', best_day: 'El {wd} es tu mejor día: {r}R de media en {n} trades.',
        plan_effect: 'Con plan antes de la apertura: {with}R por trade. Sin plan: {without}R.', compliance: 'Trades dentro del plan: {in_plan}R. Fuera: {off_plan}R. Sigues tu plan el {pct} % del tiempo.',
        beginner: 'Registraste {trades} trades, {plans} planes y {reviews} revisiones. Con 20 trades con stop, tu primer edge real aparecerá aquí.' } },
  };
  const wt = (k, p) => { const g = (o) => k.split('.').reduce((a, x) => (a == null ? a : a[x]), o); let s = g(W_T[L()]); if (s == null) s = g(W_T.en); if (s == null) s = k; return typeof s === 'string' && p ? s.replace(/\{(\w+)\}/g, (m, x) => (p[x] != null ? p[x] : m)) : s; };
  const THEMES = { ring_aurora: ['#4C8DFF', '#4FD1C5', '#2B6CB0'], ring_ember: ['#E0A84F', '#F2C98A', '#B9822F'], ring_mono: ['#F2F2F3', '#A1A1AA', '#5F5F66'], ring_violet: ['#8B7CFF', '#B6A9FF', '#5D4ED8'], ring_ocean: ['#2F80ED', '#56CCF2', '#1B4F9C'] };
  function applyTheme(id) {
    const r = document.documentElement.style, c = THEMES[id];
    if (!c) { ['--g-plan', '--g-exec', '--g-rev'].forEach((v) => r.removeProperty(v)); return; }
    r.setProperty('--g-plan', c[0]); r.setProperty('--g-exec', c[1]); r.setProperty('--g-rev', c[2]);
  }
  const fmtR = (v) => (v > 0 ? '+' : '') + Number(v).toLocaleString(loc(), { maximumFractionDigits: 2 });
  function revealText(rv) {
    if (!rv || rv.locked) return '';
    if (rv.texts && rv.texts[L()]) return rv.texts[L()];
    const d = Object.assign({}, rv.data);
    for (const k of ['r', 'all', 'with', 'without', 'in_plan', 'off_plan']) if (d[k] != null) d[k] = fmtR(d[k]);
    if (d.weekday) d.wd = wt('wd')[d.weekday] || '';
    if (d.emotion) d.emotion = t('emo.' + d.emotion) !== 'emo.' + d.emotion ? t('emo.' + d.emotion) : d.emotion;
    return wt('tpl.' + rv.key, d);
  }

  /* weekly recap: 4 screens */
  const WK = { step: 0, data: null, items: null };
  async function openWeekly(step) {
    WK.step = step || 0; WK.items = null;
    openSheet(`${head(wt('weekly'))}<div class="wk-body"><div class="skel" style="height:240px;border-radius:18px"></div></div>`, { cls: 'wk-sheet' });
    try { WK.data = await apiJSON('api/game/weekly'); } catch (e) { return; }
    if (G.weekly && (G.weekly.open || WK.data.open)) G.weekly.seen = true;   // opened (the server marks it too): the routine card stops offering it
    if (WK.data.done && !WK.data.chest_opened) WK.step = Math.max(WK.step, 3);
    renderWk();
  }
  const WQ = {
    en: { sh_btn: 'Share my week', sh_pay: 'Add my payouts received', sh_t: '{name}’s week', sh_t0: 'My week', b_streak: 'Swept-day streak', b_streak_1: '{n} day in a row', b_streak_v: '{n} days in a row', b_disc: 'Discipline this week', b_swept: 'Swept days', b_swept_v: '{a} of {b} days traded', b_habit: 'Your best habit', b_habit_v: '« {q} » — yes {y} times out of {n}', b_work: 'For next week', b_work_v: 'Aim for a « yes » to « {q} » on every trade.', b_pay: 'Payouts received this week', b_nodisc: 'Answer the checklist on your trades to get a discipline score.', recap_t: 'Your week', net: 'Net P&L', trades: 'Trades', wr: 'Win rate', inplan: 'In your plan', best: 'Best day', worst: 'Worst day', to_q: 'Analyse my week', q_t: 'Your week, in a few answers', h_best: 'Your best day: {d}, {v}.', q_worst: 'Worst day: {d}, {v}. What happened?', q_rule: 'A rule for next week', h_rule: 'One sentence you will follow, e.g. « Stop after 2 losses ».', q_grade: 'Rate your week (process, not P&L)', n_nostop: '{n} trade{s} without a stop.', n_off: '{n} trade{s} out of your plan.', n_emo: 'Most frequent emotion on your losing trades: {e}.', n_setup: 'Best setup: {a}. Weakest: {b}.', n_fees: 'Slippage and fees: {v}.', fix_nostop: 'Hint: {n} trade{s} without a stop this week.', fix_emo: 'Hint: « {e} » came back on your losing trades.' },
    fr: { sh_btn: 'Partager ma semaine', sh_pay: 'Ajouter mes payouts reçus', sh_t: 'La semaine de {name}', sh_t0: 'Ma semaine', b_streak: 'Streak de journées balayées', b_streak_1: '{n} jour d’affilée', b_streak_v: '{n} jours d’affilée', b_disc: 'Discipline de la semaine', b_swept: 'Journées balayées', b_swept_v: '{a} sur {b} jours tradés', b_habit: 'Ta meilleure habitude', b_habit_v: '« {q} » — oui {y} fois sur {n}', b_work: 'Pour la semaine prochaine', b_work_v: 'Vise un « oui » à « {q} » sur chaque trade.', b_pay: 'Payouts reçus cette semaine', b_nodisc: 'Réponds à la checklist de tes trades pour avoir un score de discipline.', recap_t: 'Ta semaine', net: 'P&L net', trades: 'Trades', wr: 'Taux de réussite', inplan: 'Dans ton plan', best: 'Meilleur jour', worst: 'Pire jour', to_q: 'Analyser ma semaine', q_t: 'Ta semaine, en quelques réponses', h_best: 'Ton meilleur jour : {d}, {v}.', q_worst: 'Pire jour : {d}, {v}. Qu’est-ce qui s’est passé ?', q_rule: 'Une règle pour la semaine prochaine', h_rule: 'Une phrase que tu vas suivre, ex. « J’arrête après 2 pertes ».', q_grade: 'Note ta semaine (le processus, pas le P&L)', n_nostop: '{n} trade{s} sans stop.', n_off: '{n} trade{s} hors de ton plan.', n_emo: 'Émotion la plus fréquente sur tes pertes : {e}.', n_setup: 'Meilleur setup : {a}. Plus faible : {b}.', n_fees: 'Glissement et frais : {v}.', fix_nostop: 'Indice : {n} trade{s} sans stop cette semaine.', fix_emo: 'Indice : « {e} » est revenu sur tes pertes.' },
    es: { sh_btn: 'Compartir mi semana', sh_pay: 'Añadir mis payouts recibidos', sh_t: 'La semana de {name}', sh_t0: 'Mi semana', b_streak: 'Racha de días barridos', b_streak_1: '{n} día seguido', b_streak_v: '{n} días seguidos', b_disc: 'Disciplina de la semana', b_swept: 'Días barridos', b_swept_v: '{a} de {b} días operados', b_habit: 'Tu mejor hábito', b_habit_v: '« {q} » — sí {y} veces de {n}', b_work: 'Para la próxima semana', b_work_v: 'Apunta a un « sí » en « {q} » en cada operación.', b_pay: 'Payouts recibidos esta semana', b_nodisc: 'Responde la checklist de tus operaciones para tener un puntaje de disciplina.', recap_t: 'Tu semana', net: 'P&L neto', trades: 'Operaciones', wr: 'Tasa de acierto', inplan: 'En tu plan', best: 'Mejor día', worst: 'Peor día', to_q: 'Analizar mi semana', q_t: 'Tu semana, en pocas respuestas', h_best: 'Tu mejor día: {d}, {v}.', q_worst: 'Peor día: {d}, {v}. ¿Qué pasó?', q_rule: 'Una regla para la próxima semana', h_rule: 'Una frase que vas a seguir, ej. « Paro tras 2 pérdidas ».', q_grade: 'Valora tu semana (el proceso, no el P&L)', n_nostop: '{n} operaci{s} sin stop.', n_off: '{n} operaci{s} fuera de tu plan.', n_emo: 'Emoción más frecuente en tus pérdidas: {e}.', n_setup: 'Mejor setup: {a}. Más débil: {b}.', n_fees: 'Deslizamiento y comisiones: {v}.', fix_nostop: 'Pista: {n} operaci{s} sin stop esta semana.', fix_emo: 'Pista: « {e} » volvió en tus pérdidas.' } };
  const wq = (k, v) => { let x = (WQ[LANG] || WQ.en)[k] || k; if (v) for (const [a, b] of Object.entries(v)) x = x.split('{' + a + '}').join(String(b)); if (v && 'n' in v) x = x.split('{s}').join(LANG === 'es' ? (+v.n > 1 ? 'ones' : 'ón') : (+v.n > 1 ? 's' : '')); return x; };
  /** the week's recap (brief 01 step 5): discipline, swept days on traded days, best habit, one point to work on, real payouts
   *  received. No P&L here: simulated profit is never shown as money earned. */
  function weekBrief(mon, summary) {
    const m = mon || (() => { const d = new Date(); d.setDate(d.getDate() - ((d.getDay() + 6) % 7)); return d.toISOString().slice(0, 10); })();
    const add = (k, n) => { const d = new Date(k + 'T12:00:00'); d.setDate(d.getDate() + n); return d.toISOString().slice(0, 10); };
    const tr = (S.trades || []).filter((x) => !x.demo && x.date >= m && x.date <= add(m, 4));
    const traded = new Set(tr.map((x) => x.date)).size;
    const ds = tr.map((x) => (typeof tDisc === 'function' ? tDisc(x) : null)).filter((v) => v != null);
    const disc = ds.length ? Math.round(ds.reduce((a, v) => a + v, 0) / ds.length) : null;
    const qs = ((S.settings && S.settings.questions) || []), qText = (id) => { const q = qs.find((x) => x.id === id); const t0 = q ? q.text : id; return typeof tr0 === 'function' ? tr0(t0) : t0; };
    const per = {}; tr.forEach((x) => Object.entries(x.discipline || {}).forEach(([k, v]) => { if (v !== 'y' && v !== 'n') return; const o = per[k] || (per[k] = { y: 0, n: 0 }); o[v === 'y' ? 'y' : 'n']++; }));
    const rows = Object.entries(per).map(([k, o]) => ({ k, y: o.y, n: o.y + o.n, rate: o.y / (o.y + o.n) })).filter((r) => r.n >= 2);
    const byK = (a, b) => (a.k < b.k ? -1 : a.k > b.k ? 1 : 0);   // same order as the « Your week » email (game/weekly-mail.php)
    const best = rows.slice().sort((a, b) => b.rate - a.rate || b.n - a.n || byK(a, b))[0] || null;
    const work = rows.filter((r) => r.y < r.n).sort((a, b) => a.rate - b.rate || b.n - a.n || byK(a, b))[0] || null;
    const M2 = window.SweepMoney, sun = add(m, 6);
    const pay = (S.payouts || []).filter((p) => (M2 ? M2.pState(p) === 'paid' : p.status === 'paid')).filter((p) => { const d = M2 ? M2.pPaidOn(p) : (p.payment_date || p.date); return d && d >= m && d <= sun; })
      .reduce((a, p) => a + (M2 ? M2.pNet(p) : (p.net_c || p.amount_c || 0)), 0);
    const sm = summary || {};
    return { traded, swept: Math.min(sm.swept || 0, traded || sm.swept || 0), streak: sm.streak || 0, disc, best: best && { q: qText(best.k), y: best.y, n: best.n },
      work: work && (!best || work.k !== best.k) ? { q: qText(work.k) } : null, payouts: pay };
  }
  const tr0 = (x) => (typeof tr === 'function' ? tr(x) : x);
  /** French: no-break spaces inside « » and before ? : ! (a lone « » » never starts a line) — like the « Your week » email */
  const nbFr = (x) => (LANG === 'fr' ? String(x).replace(/« /g, '«\u00a0').replace(/ ([»?:!])/g, '\u00a0$1') : x);
  function weekRecap(mon) {
    const m = mon || (() => { const d = new Date(); d.setDate(d.getDate() - ((d.getDay() + 6) % 7)); return d.toISOString().slice(0, 10); })();
    const add = (k, n) => { const d = new Date(k + 'T12:00:00'); d.setDate(d.getDate() + n); return d.toISOString().slice(0, 10); };
    const sun = add(m, -1), fri = add(m, 4);
    // Sunday-evening trades belong to Monday's session
    const tr = (S.trades || []).filter((x) => !x.demo && x.date >= sun && x.date <= fri).map((x) => (x.date === sun ? Object.assign({}, x, { date: m }) : x));
    const net = (x) => (typeof tNet === 'function' ? tNet(x) : (x.pnl_c || 0) - (x.fees_c || 0));
    const days = {}; tr.forEach((x) => { days[x.date] = (days[x.date] || 0) + net(x); });
    const dayList = Object.entries(days).map(([k, v]) => ({ k, net: v, label: new Date(k + 'T12:00:00').toLocaleDateString(loc(), { weekday: 'long' }), short: new Date(k + 'T12:00:00').toLocaleDateString(loc(), { weekday: 'short' }) }));
    const best = dayList.length ? dayList.slice().sort((a, b) => b.net - a.net)[0] : null, worst = dayList.length > 1 ? dayList.slice().sort((a, b) => a.net - b.net)[0] : null;
    const n = tr.length, wins = tr.filter((x) => net(x) > 0).length, total = tr.reduce((a, x) => a + net(x), 0);
    const noStop = tr.filter((x) => x.stop == null || x.stop === '').length;
    const off = tr.filter((x) => x.stop == null || x.stop === '' || x.rules_followed === 'no' || x.rules_followed === 'partial').length;
    const emo = {}; tr.filter((x) => net(x) < 0).forEach((x) => ((x.emo && Array.isArray(x.emo.before)) ? x.emo.before : []).forEach((e) => { emo[e] = (emo[e] || 0) + 1; }));
    const topEmo = Object.entries(emo).sort((a, b) => b[1] - a[1])[0];
    const emoName = topEmo ? (t('emo.' + topEmo[0]) || topEmo[0]) : '';
    const set = {}; tr.forEach((x) => { const k = (x.setup || '').trim(); if (k) set[k] = (set[k] || 0) + net(x); });
    const sets = Object.entries(set).sort((a, b) => b[1] - a[1]);
    const slip = tr.reduce((a, x) => a + (typeof x.pnl_calc_c === 'number' && typeof x.real_pnl_c === 'number' ? x.pnl_c - x.pnl_calc_c : 0) - (x.fees_c || 0), 0);
    const notes = [];
    if (noStop) notes.push(wq('n_nostop', { n: noStop }));
    if (off && off !== noStop) notes.push(wq('n_off', { n: off }));
    if (topEmo && topEmo[1] > 1) notes.push(wq('n_emo', { e: esc(emoName) }));
    if (sets.length > 1) notes.push(wq('n_setup', { a: esc(sets[0][0]), b: esc(sets[sets.length - 1][0]) }));
    if (slip < 0) notes.push(wq('n_fees', { v: money(slip) }));
    const f = (k) => new Date(k + 'T12:00:00').toLocaleDateString(loc(), { day: 'numeric', month: 'short' });
    return { range: `${f(m)} – ${f(fri)}`, n, net: total, wr: n ? (100 * wins) / n : 0, inPlan: n - off, best, worst, notes,
      fixHint: noStop ? wq('fix_nostop', { n: noStop }) : topEmo ? wq('fix_emo', { e: esc(emoName) }) : '' };
  }
  function renderWk(dir = 1) {
    const box = document.querySelector('#gSheet .wk-body'); if (!box || !WK.data) return;
    const d = WK.data, s = d.summary || { days: [], swept: 0, streak: 0, missions: {} };
    const dots = `<div class="wk-dots">${[0, 1, 2, 3].map((i) => `<i class="${i <= WK.step ? 'on' : ''}"></i>`).join('')}</div>`;
    let h = '';
    if (WK.step === 0) {
      const r = weekRecap(d.week), b = weekBrief(d.week, s);
      h = `<h3>${wq('recap_t')}</h3><p class="muted wk-range">${r.range}</p>
        <div class="wk-sum wk-brief">
          <div><small>${wq('b_streak')}</small><b>${wq(b.streak === 1 ? 'b_streak_1' : 'b_streak_v', { k: b.streak }).split('{n}').join(b.streak)}</b></div>
          <div><small>${wq('b_disc')}</small><b class="${b.disc != null && b.disc >= 80 ? 'pos' : ''}">${b.disc != null ? b.disc + '\u202f%' : '—'}</b></div>
          <div><small>${wq('b_swept')}</small><b>${wq('b_swept_v', { a: b.swept, b: b.traded })}</b></div>
        </div>
        <div class="wk-week">${s.days.map((x) => `<span class="${x.swept ? 'swept' : ''} ${x.market ? '' : 'off'}"><i>${new Date(x.day + 'T12:00:00').toLocaleDateString(loc(), { weekday: 'short' })}</i>${miniRings(x.rings || { plan: 0, execution: 0, review: 0 })}</span>`).join('')}</div>
        <ul class="wk-notes wk-habits">
          ${b.best ? `<li><b>${wq('b_habit')}</b><span>${esc(nbFr(wq('b_habit_v', { q: b.best.q, y: b.best.y, n: b.best.n })))}</span></li>` : b.disc == null ? `<li><span>${wq('b_nodisc')}</span></li>` : ''}
          ${b.work ? `<li><b>${wq('b_work')}</b><span>${esc(nbFr(wq('b_work_v', { q: b.work.q })))}</span></li>` : ''}
          ${b.payouts > 0 ? `<li><b>${wq('b_pay')}</b><span class="pos">${money(b.payouts)}</span></li>` : ''}
        </ul>
        <div class="wk-share">${b.payouts > 0 ? `<div class="g-sound wk-sh-pay"><span><b>${wq('sh_pay')}</b></span><label class="sw"><input type="checkbox" data-wk-pay aria-label="${esc(wq('sh_pay'))}"><i></i></label></div>` : ''}
          <button type="button" class="btn wk-sh" data-g="share" data-k="week">${svg('share')}${wq('sh_btn')}</button></div>
        <button type="button" class="btn primary g-big" data-g="wk-next">${wq('to_q')}</button>`;
    } else if (WK.step === 1) {
      const r = weekRecap(d.week), prev = d.answers || {};
      const qa = (k, label, hint, rows = 2) => `<label class="g-f"><span>${label}</span>${hint ? `<small class="wk-hint">${hint}</small>` : ''}<textarea rows="${rows}" maxlength="300" data-wq="${k}">${esc(prev[k] || '')}</textarea></label>`;
      h = `<h3>${wq('q_t')}</h3>
        ${qa('best', wt('q_best'), r.best ? wq('h_best', { d: r.best.label, v: money(r.best.net) }) : '')}
        ${r.worst && r.worst.net < 0 ? qa('worst', wq('q_worst', { d: r.worst.label, v: money(r.worst.net) }), '') : ''}
        ${qa('fix', wt('q_fix'), r.fixHint)}
        ${qa('rule', wq('q_rule'), wq('h_rule'))}
        ${qa('intention', wt('q_int'), '')}
        <div class="g-f"><span>${wq('q_grade')}</span><div class="g-dots wk-grade">${[1, 2, 3, 4, 5].map((n) => `<button type="button" class="${+prev.grade === n ? 'on' : ''}" data-g="wk-grade" data-v="${n}">${n}</button>`).join('')}</div></div>
        <button type="button" class="btn primary g-big" data-g="wk-save">${wt('save_go')}</button>`;
    } else if (WK.step === 1) {
      h = `<label class="g-f"><span>${wt('q_best')}</span><textarea rows="2" maxlength="300" data-wq="best"></textarea></label>
        <label class="g-f"><span>${wt('q_fix')}</span><textarea rows="2" maxlength="300" data-wq="fix"></textarea></label>
        <label class="g-f"><span>${wt('q_int')}</span><textarea rows="2" maxlength="300" data-wq="intention"></textarea></label>
        <button type="button" class="btn primary g-big" data-g="wk-save">${wt('save_go')}</button>`;
    } else if (WK.step === 2) {
      const rv = d.reveal;
      h = `<h3>${wt('reveal_t')}</h3>${!rv ? `<p class="muted">${esc(wt('tpl.beginner', { trades: 0, plans: 0, reviews: 0 }))}</p>` : rv.locked
        ? `<div class="wk-card locked"><span class="g-medal r-none big">${svg('lock')}</span><p>${wt('reveal_locked')}</p><button type="button" class="btn" data-g="locked">${wt('unlock')}</button></div>`
        : `<button type="button" class="wk-card ${rv.revealed ? 'flipped' : ''}" data-g="wk-flip" data-v="${rv.id}"><span class="wk-back">${svg('spark')}<b>${wt('reveal_tap')}</b></span><span class="wk-front"><span class="g-kick">${wt('reveal_t')}</span><p>${esc(revealText(rv))}</p></span></button>
           ${d.can_second ? `<button type="button" class="link" data-g="wk-second">${wt('another')}</button>` : ''}`}
        <button type="button" class="btn primary g-big" data-g="wk-next">${t('next')}</button>`;
    } else {
      const items = WK.items;
      h = `<h3>${wt('chest_t')}</h3><div class="wk-chest ${items ? 'open' : ''}">${chestSvg()}</div>
        ${items ? `<ul class="wk-items">${items.map((it, i) => `<li style="--i:${i}">${itemLabel(it)}</li>`).join('')}</ul><button type="button" class="btn primary g-big" data-g="close">${wt('close')}</button>`
          : `${d.keys ? `<p class="wk-key">${svg('star')} ${wt('chest_key')}</p>` : ''}<button type="button" class="btn primary g-big" data-g="wk-chest">${wt('chest_open')}</button>`}
        <details class="wk-odds"><summary>${wt('odds')}</summary><table>${[['xp', 100, 100], ...Object.entries(d.odds || {}).map(([k, v]) => [k, v[0], v[1]])].map(([k, a, b]) => `<tr><td>${wt('o_' + (k === 'ai_credits' ? 'ai' : k === 'pro_days' ? 'pro' : k))}</td><td>${a} %</td><td>${b} %</td></tr>`).join('')}</table></details>`;
    }
    box.innerHTML = dots + `<div class="wk-step">${h}</div>`;
    const st = box.querySelector('.wk-step');
    if (!reduced()) st.animate([{ opacity: 0, transform: `translateX(${dir * 28}px)` }, { opacity: 1, transform: 'none' }], { duration: 340, easing: 'cubic-bezier(.32,.72,0,1)' });
  }
  const chestSvg = () => `<svg viewBox="0 0 120 120" aria-hidden="true"><rect class="ch-glow" x="10" y="10" width="100" height="100" rx="50"/><g class="ch-lid"><rect x="28" y="30" width="64" height="22" rx="8"/></g><rect class="ch-body" x="28" y="54" width="64" height="40" rx="8"/><rect class="ch-lock" x="54" y="62" width="12" height="16" rx="3"/><line class="ch-wick" x1="60" y1="94" x2="60" y2="108"/></svg>`;
  function itemLabel(it) {
    if (it.type === 'xp') return `${svg('star')}<b>${wt('it_xp', { v: it.value })}</b>`;
    if (it.type === 'freeze') return `${svg('snow')}<b>${wt('it_freeze')}</b>`;
    if (it.type === 'cosmetic') return `<i class="wk-sw" style="--a:${(THEMES[it.value] || [])[0]};--b:${(THEMES[it.value] || [])[1]}"></i><b>${wt('it_cosmetic', { v: wt('th.' + it.value) })}</b>`;
    if (it.type === 'ai_credits') return `${svg('spark')}<b>${wt('it_ai', { v: it.value })}</b>`;
    if (it.type === 'pro_days') return `${svg('flag')}<b>${wt('it_pro', { v: it.value })}</b>`;
    return `${svg('q')}<b>${wt('it_badge')}</b>`;
  }
  async function wkChest() {
    const el = document.querySelector('#gSheet .wk-chest');
    if (el && !reduced()) el.animate([{ transform: 'rotate(0)' }, { transform: 'rotate(-6deg)' }, { transform: 'rotate(6deg)' }, { transform: 'rotate(-4deg)' }, { transform: 'rotate(0)' }], { duration: 600, easing: 'ease-in-out' });
    buzz([10, 30, 10]);
    try { const r = await apiJSON('api/game/chest', { method: 'POST', body: {} }); WK.items = r.items || []; if (r.cosmetics) G.cos = r.cosmetics; } catch (e) { WK.items = []; }
    setTimeout(() => { renderWk(0); chime(); load(true); }, reduced() ? 0 : 520);
  }

  /* ring themes (Settings) */
  function themesHtml() {
    const c = G.cos; if (!c) return '';
    return `<div class="sec-h" style="margin-top:18px"><h2>${wt('themes')}</h2></div><div class="wk-themes">${c.all.map((id) => {
      const own = c.owned.includes(id), col = (typeof themeCols === 'function' && themeCols(id)) || THEMES[id] || ['var(--pos)', 'color-mix(in srgb,var(--pos) 55%,#fff)', 'color-mix(in srgb,var(--pos) 78%,#000)'];
      return `<button type="button" class="wk-theme ${c.equipped === id ? 'on' : ''} ${own ? '' : 'lock'}" ${own ? `data-g="theme" data-v="${id}"` : 'disabled'}><span class="wk-ring" style="--a:${col[0]};--b:${col[1]};--c:${col[2]}"></span><small>${own ? esc(typeof themeName === 'function' ? themeName(id) : wt('th.' + id)) : svg('lock')}</small></button>`;
    }).join('')}</div>`;
  }

  /* comeback quest */
  function questPill() {
    const q = G.quest; if (!q || q.done) return '';
    const n = Object.values(q.steps).filter(Boolean).length;
    return `<button type="button" class="gc-pill" data-g="quest">${svg('fire')}<span><small>${wt('quest_t')}</small><b>${wt('quest', { d: n })}</b></span></button>`;
  }
  function questSheet() {
    const q = G.quest; if (!q) return;
    openSheet(`<div class="g-cel"><span class="g-medal r-common big">${svg('fire')}</span><h2>${wt('quest_t')}</h2><p>${wt('quest_sub')}</p>
      <ul class="wk-qsteps">${['review', 'plan', 'sweep'].map((k) => `<li class="${q.steps[k] ? 'ok' : ''}">${svg(q.steps[k] ? 'sweep' : 'target')}<span>${wt('qs_' + k)}</span></li>`).join('')}</ul>
      <div class="g-acts"><button type="button" class="btn primary" data-g="close">${t('continue')}</button></div></div>`, { cls: 'g-celsheet' });
  }

  /* ───────────── V2 step 3: monthly Wrapped, reminders text, payout ready ───────────── */
  const WR_T = {
    en: { pill: 'Your {m} Wrapped', s1: 'Your {m}', s1b: 'days swept out of {n} market days', s2: 'Best streak of the month', s2b: 'days in a row', s3: 'Signature setup', s3b: '{n} trades · {pct} % inside your plan',
      s4: 'Golden time slot', s4b: '{r}R on average over {n} trades', s5: 'Dominant emotion', s5b: '{n} trades · {r}R on average', s6: 'Unlocked this month', s6b: '{b} badges · {n} journey steps',
      s7: 'Your rank', s7b: 'Level {l} · +{xp} XP this month', s8: 'That was {m}.', share: 'Share my month', locked: 'Unlock the full Wrapped with Pro', none: 'Not enough data yet',
      archive: 'Your Wrapped', card_t: '{m} swept', card_s: '{n} days swept · best streak {s}', tap: 'Tap to continue',
      pay_t: 'Ready for payout', pay_s: 'Your account meets its payout rules. Well played.',
      n: { 'g_plan.title': 'Your plan of the day is waiting.', 'g_plan.body': 'Two minutes before the open.', 'g_review.title': '60 seconds to sweep your day.', 'g_review.body': 'Journal and review while it is fresh.',
        'g_streak.title': 'Your {n}-day streak can still be saved.', 'g_streak.body': 'A review is all it takes.', 'g_weekly.title': 'Your week is ready.', 'g_weekly.body': 'Your streak, your discipline and your swept days, in one place.',
        'g_intention.title': 'New missions tomorrow.', 'g_intention.body': 'Your intention: {intention}', 'g_wrapped.title': 'Your monthly Wrapped is ready.', 'g_wrapped.body': 'A look back at your month, in one minute.' } },
    fr: { pill: 'Ton Wrapped de {m}', s1: 'Ton mois de {m}', s1b: 'journées balayées sur {n} jours de marché', s2: 'Meilleur streak du mois', s2b: 'jours de suite', s3: 'Setup signature', s3b: '{n} trades · {pct} % dans ton plan',
      s4: 'Créneau d’or', s4b: '{r}R en moyenne sur {n} trades', s5: 'Émotion dominante', s5b: '{n} trades · {r}R en moyenne', s6: 'Débloqué ce mois-ci', s6b: '{b} badges · {n} étapes du parcours',
      s7: 'Ton rang', s7b: 'Niveau {l} · +{xp} XP ce mois-ci', s8: 'C’était {m}.', share: 'Partager mon mois', locked: 'Débloque le Wrapped complet avec Pro', none: 'Pas encore assez de données',
      archive: 'Tes Wrapped', card_t: '{m} balayé', card_s: '{n} journées balayées · meilleur streak {s}', tap: 'Touche pour continuer',
      pay_t: 'Prêt pour le payout', pay_s: 'Ton compte respecte ses règles de payout. Bien joué.',
      n: { 'g_plan.title': 'Ton plan du jour t’attend.', 'g_plan.body': 'Deux minutes avant l’ouverture.', 'g_review.title': '60 secondes pour balayer ta journée.', 'g_review.body': 'Journalise et fais ta revue tant que c’est frais.',
        'g_streak.title': 'Ton streak de {n} jours est encore sauvable.', 'g_streak.body': 'Une revue suffit.', 'g_weekly.title': 'Ta semaine est prête.', 'g_weekly.body': 'Ton streak, ta discipline et tes journées balayées, au même endroit.',
        'g_intention.title': 'Nouvelles missions demain.', 'g_intention.body': 'Ton intention : {intention}', 'g_wrapped.title': 'Ton Wrapped du mois est prêt.', 'g_wrapped.body': 'Ton mois en une minute.' } },
    es: { pill: 'Tu Wrapped de {m}', s1: 'Tu {m}', s1b: 'días barridos de {n} días de mercado', s2: 'Mejor racha del mes', s2b: 'días seguidos', s3: 'Setup insignia', s3b: '{n} trades · {pct} % dentro de tu plan',
      s4: 'Franja de oro', s4b: '{r}R de media en {n} trades', s5: 'Emoción dominante', s5b: '{n} trades · {r}R de media', s6: 'Desbloqueado este mes', s6b: '{b} insignias · {n} pasos del recorrido',
      s7: 'Tu rango', s7b: 'Nivel {l} · +{xp} XP este mes', s8: 'Eso fue {m}.', share: 'Compartir mi mes', locked: 'Desbloquea el Wrapped completo con Pro', none: 'Aún no hay suficientes datos',
      archive: 'Tus Wrapped', card_t: '{m} barrido', card_s: '{n} días barridos · mejor racha {s}', tap: 'Toca para continuar',
      pay_t: 'Listo para el payout', pay_s: 'Tu cuenta cumple sus reglas de payout. Bien jugado.',
      n: { 'g_plan.title': 'Tu plan del día te espera.', 'g_plan.body': 'Dos minutos antes de la apertura.', 'g_review.title': '60 segundos para barrer tu día.', 'g_review.body': 'Registra y revisa mientras está fresco.',
        'g_streak.title': 'Tu racha de {n} días aún se puede salvar.', 'g_streak.body': 'Basta con una revisión.', 'g_weekly.title': 'Tu semana está lista.', 'g_weekly.body': 'Tu racha, tu disciplina y tus días barridos, en un solo lugar.',
        'g_intention.title': 'Nuevas misiones mañana.', 'g_intention.body': 'Tu intención: {intention}', 'g_wrapped.title': 'Tu Wrapped del mes está listo.', 'g_wrapped.body': 'Tu mes en un minuto.' } },
  };
  Object.assign(WR_T.en, { yshare: 'Share my year', ypill: 'Your {y}', y1: 'Your {y}', y1b: 'days swept this year', y3: 'Bosses beaten', y3b: 'No boss beaten this year: next year.', y4: 'Chapters completed', y4b: 'journey chapters', y7b: 'Level {l} · {t} league', y8: 'That was {y}.', ycard: '{y} swept', ycard_s: '{n} days swept · best streak {s}',
    dc: 'Discord', dc_link: 'Link my Discord account', dc_linked: 'Linked: {n}', dc_share: 'Share my big moments in the community channel', dc_share_d: 'Boss beaten, new rank, crew goal. Never P&L or amounts.', dc_unlink: 'Unlink', dc_err: 'Discord link failed, try again.' });
  Object.assign(WR_T.fr, { yshare: 'Partager mon année', ypill: 'Ton année {y}', y1: 'Ton année {y}', y1b: 'journées balayées cette année', y3: 'Boss vaincus', y3b: 'Aucun boss vaincu cette année : l’an prochain.', y4: 'Chapitres terminés', y4b: 'chapitres du parcours', y7b: 'Niveau {l} · Ligue {t}', y8: 'C’était {y}.', ycard: '{y} balayée', ycard_s: '{n} journées balayées · meilleur streak {s}',
    dc: 'Discord', dc_link: 'Lier mon compte Discord', dc_linked: 'Lié : {n}', dc_share: 'Partager mes grands moments dans le salon de la communauté', dc_share_d: 'Boss vaincu, nouveau rang, objectif du crew. Jamais de P&L ni de montants.', dc_unlink: 'Délier', dc_err: 'La liaison Discord a échoué, réessaie.' });
  Object.assign(WR_T.es, { yshare: 'Compartir mi año', ypill: 'Tu {y}', y1: 'Tu {y}', y1b: 'días barridos este año', y3: 'Jefes vencidos', y3b: 'Ningún jefe vencido este año: el próximo.', y4: 'Capítulos completados', y4b: 'capítulos del recorrido', y7b: 'Nivel {l} · Liga {t}', y8: 'Así fue {y}.', ycard: '{y} barrido', ycard_s: '{n} días barridos · mejor racha {s}',
    dc: 'Discord', dc_link: 'Vincular mi cuenta de Discord', dc_linked: 'Vinculado: {n}', dc_share: 'Compartir mis grandes momentos en el canal de la comunidad', dc_share_d: 'Jefe vencido, nuevo rango, objetivo del crew. Nunca P&L ni montos.', dc_unlink: 'Desvincular', dc_err: 'Falló la vinculación con Discord, inténtalo de nuevo.' });
  const wrt = (k, p) => { let s = (WR_T[L()] || WR_T.en)[k]; if (s == null) s = WR_T.en[k] || k; if (typeof s === 'string' && p) s = s.replace(/\{(\w+)\}/g, (m, x) => (p[x] != null ? p[x] : m)); return L() === 'fr' && typeof s === 'string' ? s.replace(/\bde ([aeiouyàâéèêh])/gi, 'd’$1') : s; };   // « de octobre » → « d’octobre »
  if (window.SweepNotify && SweepNotify.strings) { try { SweepNotify.strings({ en: WR_T.en.n, fr: WR_T.fr.n, es: WR_T.es.n }); } catch (e) { /* older notify module */ } }
  const monthName = (m) => new Date(m + '-15T12:00:00').toLocaleDateString(loc(), { month: 'long' });

  async function openWrapped(month) {
    let st; try { st = await apiJSON('api/game/wrapped'); } catch (e) { return; }
    const it = (st.items || []).find((x) => !month || x.month === month); if (!it) return;
    G.wr = it; const d = it.data, free = st.plan === 'free', M = d.kind === 'year' ? String(d.year) : monthName(d.month);
    const lockH = `<div class="wr-lock">${svg('lock')}<b>${wrt('locked')}</b><button type="button" class="btn" data-g="locked">${t('v2.locked_ch')}</button></div>`;
    const big = (v, sub) => `<b class="wr-big" data-count="${v}">${v}</b><p>${sub}</p>`;
    const Y = d.year;
    const screens = d.kind === 'year' ? [
      `<span class="g-kick">${esc(wrt('y1', { y: Y }))}</span>${big(d.swept, wrt('y1b'))}`,
      `<span class="g-kick">${wrt('s2')}</span><span class="wr-candle">${CANDLE()}</span>${big(d.best_streak, wrt('s2b'))}`,
      free ? lockH : `<span class="g-kick">${wrt('y3')}</span>${d.bosses.length ? `<div class="wr-medals">${d.bosses.slice(0, 6).map((b) => `<span class="gb-art-w">${bossArt(b)}</span>`).join('')}</div><p>${d.bosses.map((b) => esc(bossName(b))).join(' · ')}</p>` : `<p>${wrt('y3b')}</p>`}`,
      free ? lockH : `<span class="g-kick">${wrt('y4')}</span>${big(d.chapters, wrt('y4b'))}`,
      free ? lockH : d.signature ? `<span class="g-kick">${wrt('s3')}</span><b class="wr-word">${esc(d.signature.setup)}</b>` : `<span class="g-kick">${wrt('s3')}</span><p>${wrt('none')}</p>`,
      free ? lockH : d.gold_slot ? `<span class="g-kick">${wrt('s4')}</span><b class="wr-word gold">${d.gold_slot.start}–${d.gold_slot.end}</b><p>${wrt('s4b', { r: fmtR(d.gold_slot.r), n: d.gold_slot.n })}</p>` : `<span class="g-kick">${wrt('s4')}</span><p>${wrt('none')}</p>`,
      `<span class="g-kick">${wrt('s7')}</span><span class="g-medal r-epic big">${CANDLE()}</span><b class="wr-word">${esc(rankName(d.rank))}</b><p>${wrt('y7b', { l: d.level, t: typeof lgt === 'function' ? lgt('tiers.' + (d.league_tier || 1)) : '' })}</p>`,
      `<b class="wr-word">${esc(wrt('y8', { y: Y }))}</b><p>${wrt('ycard_s', { n: d.swept, s: d.best_streak })}</p><button type="button" class="btn primary g-big" data-g="share" data-k="wrapped" data-v="${d.month}">${svg('share')}${wrt('yshare')}</button>`,
    ] : [
      `<span class="g-kick">${esc(wrt('s1', { m: M }))}</span>${big(d.swept, wrt('s1b', { n: d.market_days }))}`,
      `<span class="g-kick">${wrt('s2')}</span><span class="wr-candle">${CANDLE()}</span>${big(d.best_streak, wrt('s2b'))}`,
      free ? lockH : d.signature ? `<span class="g-kick">${wrt('s3')}</span><b class="wr-word">${esc(d.signature.setup)}</b><p>${wrt('s3b', d.signature)}</p>` : `<span class="g-kick">${wrt('s3')}</span><p>${wrt('none')}</p>`,
      free ? lockH : d.gold_slot ? `<span class="g-kick">${wrt('s4')}</span><b class="wr-word gold">${d.gold_slot.start}–${d.gold_slot.end}</b><p>${wrt('s4b', { r: fmtR(d.gold_slot.r), n: d.gold_slot.n })}</p>` : `<span class="g-kick">${wrt('s4')}</span><p>${wrt('none')}</p>`,
      free ? lockH : d.emotion ? `<span class="g-kick">${wrt('s5')}</span><b class="wr-word">${esc(t('emo.' + d.emotion.emotion) !== 'emo.' + d.emotion.emotion ? t('emo.' + d.emotion.emotion) : d.emotion.emotion)}</b><p>${wrt('s5b', { n: d.emotion.n, r: d.emotion.r != null ? fmtR(d.emotion.r) : '—' })}</p>` : `<span class="g-kick">${wrt('s5')}</span><p>${wrt('none')}</p>`,
      free ? lockH : `<span class="g-kick">${wrt('s6')}</span><div class="wr-medals">${(d.badges || []).slice(0, 6).map((b) => medal(b, 'rare')).join('')}</div><p>${wrt('s6b', { b: (d.badges || []).length, n: d.nodes })}</p>`,
      `<span class="g-kick">${wrt('s7')}</span><span class="g-medal r-epic big">${CANDLE()}</span><b class="wr-word">${esc(rankName(d.rank))}</b><p>${wrt('s7b', { l: d.level, xp: d.xp.toLocaleString(loc()) })}</p>`,
      `<b class="wr-word">${esc(wrt('s8', { m: M }))}</b><p>${wrt('card_s', { n: d.swept, s: d.best_streak })}</p><button type="button" class="btn primary g-big" data-g="share" data-k="wrapped" data-v="${d.month}">${svg('share')}${wrt('share')}</button>`,
    ];
    const ov = document.createElement('div');
    ov.className = 'wr'; ov.setAttribute('data-noi18n', ''); ov.setAttribute('role', 'dialog');
    ov.innerHTML = `<div class="wr-bars">${screens.map(() => '<i><s></s></i>').join('')}</div><button type="button" class="wr-x" aria-label="Close">${svg('x')}</button>
      <div class="wr-stage">${screens.map((h, i) => `<section class="wr-s s${i}">${h}</section>`).join('')}</div><small class="wr-tap">${wrt('tap')}</small>`;
    document.body.append(ov); document.body.classList.add('evp-lock');
    let i = 0, timer = 0;
    const go = (n) => {
      i = Math.max(0, Math.min(screens.length - 1, n));
      ov.querySelectorAll('.wr-s').forEach((s, k) => s.classList.toggle('on', k === i));
      ov.querySelectorAll('.wr-bars i').forEach((b, k) => { b.classList.toggle('done', k < i); b.classList.toggle('on', k === i); });
      const num = ov.querySelector('.wr-s.on .wr-big');
      if (num && !reduced()) { const to = +num.dataset.count; const t0 = performance.now(); const step = (now) => { const p = Math.min(1, (now - t0) / 700); num.textContent = Math.round(to * (1 - Math.pow(1 - p, 3))); if (p < 1) requestAnimationFrame(step); }; requestAnimationFrame(step); }
      clearTimeout(timer); if (i < screens.length - 1) timer = setTimeout(() => go(i + 1), 5200);
      buzz(4);
    };
    const close = () => { clearTimeout(timer); ov.classList.add('out'); document.body.classList.remove('evp-lock'); setTimeout(() => ov.remove(), 260); };
    ov.addEventListener('click', (e) => {
      if (e.target.closest('.wr-x')) return close();
      if (e.target.closest('[data-g]')) return;
      const x = e.clientX / innerWidth; go(x < 0.3 ? i - 1 : i + 1);
    });
    requestAnimationFrame(() => { ov.classList.add('in'); go(0); });
    apiJSON('api/game/wrapped/viewed', { method: 'POST', body: { month: d.month } }).catch(() => {});
    if (G.wrapped) G.wrapped.new = false;
  }
  function wrappedPill() {
    const w = G.wrapped; if (!w) return '';
    return `<button type="button" class="gc-pill wr-pill ${w.new ? 'new' : ''}" data-g="wrapped" data-v="${w.month}">${svg('spark')}<span><small>Wrapped</small><b>${esc(/-AN$/.test(w.month) ? wrt('ypill', { y: w.month.slice(0, 4) }) : wrt('pill', { m: monthName(w.month) }))}</b></span></button>`;
  }
  async function wrappedArchive() {
    try { const st = await apiJSON('api/game/wrapped'); G.wrList = st.items || []; } catch (e) { G.wrList = []; }
    const el = document.getElementById('gBdg'); if (el) { el._h = null; paintSections(); }
  }
  const archiveHtml = () => (G.wrList && G.wrList.length ? `<div class="sec-h" style="margin-top:18px"><h2>${wrt('archive')}</h2></div><div class="wr-arch">${G.wrList.map((x) => `<button type="button" class="wr-ai" data-g="wrapped" data-v="${x.month}"><b>${esc(/-AN$/.test(x.month) ? x.month.slice(0, 4) : monthName(x.month))}</b><small>${x.data.swept} ${svg('sweep')}</small></button>`).join('')}</div>` : '');

  /* payout readiness at 100 %: the gold moment */
  function payoutReady() {
    return new Promise((res) => {
      const ov = document.createElement('div');
      ov.className = 'g-sweep gp-gold'; ov.setAttribute('data-noi18n', '');
      const c = 2 * Math.PI * 70;
      ov.innerHTML = `<div class="g-sw-bg"></div><div class="g-sw-c"><div class="gp-stage"><svg class="g-sw-svg" viewBox="0 0 200 200"><circle cx="100" cy="100" r="70" class="gp-track"/><circle cx="100" cy="100" r="70" class="gp-arc" stroke-dasharray="${c}" stroke-dashoffset="${c}" transform="rotate(-90 100 100)"/></svg><span class="gp-cand">${CANDLE()}</span></div>
        <h2 class="g-sw-t">${wrt('pay_t')}</h2><p class="gp-sub">${wrt('pay_s')}</p>
        <div class="g-sw-acts"><button type="button" class="btn" data-g="share" data-k="payout">${svg('share')}${t('share')}</button><button type="button" class="btn primary" data-g="sw-close">${t('continue')}</button></div></div>`;
      document.body.append(ov);
      const close = () => { ov.classList.add('out'); setTimeout(() => { ov.remove(); res(); }, 260); };
      ov.addEventListener('click', (e) => { if (e.target.closest('[data-g="sw-close"]') || e.target.classList.contains('g-sw-bg')) close(); });
      ov.classList.add('in'); buzz([20, 40, 30]); chime();
      const arc = ov.querySelector('.gp-arc');
      if (reduced()) arc.setAttribute('stroke-dashoffset', '0');
      else arc.animate([{ strokeDashoffset: c }, { strokeDashoffset: 0 }], { duration: 1200, easing: 'cubic-bezier(.32,.72,0,1)', fill: 'forwards' });
    });
  }

  /* ───────────── V3: seasons and pass ───────────── */
  const SS_T = {
    en: { season: 'Season {n}', tier: 'Tier {t}', ends: 'Ends in {d} days', ends1: 'Ends tomorrow', free: 'Free', pro: 'Pro', claim: 'Claim', to_next: '{p} XP to tier {t}', max: 'Pass complete',
      unlock: 'Pro unlocks every tier, including the ones you already reached.', r_xp: '+{v} XP', r_freeze: 'Streak freeze', r_key: 'Chest key', r_ai: '+{v} AI messages', r_cosmetic: 'Ring theme', r_badge: 'Season badge', new: 'New season',
      sname: { Liquidity: 'Liquidity', Momentum: 'Momentum', Patience: 'Patience', Precision: 'Precision', Edge: 'Edge', Flow: 'Flow', Focus: 'Focus', Clarity: 'Clarity', Balance: 'Balance', Resolve: 'Resolve', Discipline: 'Discipline', Mastery: 'Mastery' } },
    fr: { season: 'Saison {n}', tier: 'Palier {t}', ends: 'Se termine dans {d} jours', ends1: 'Se termine demain', free: 'Gratuit', pro: 'Pro', claim: 'Réclamer', to_next: '{p} XP avant le palier {t}', max: 'Pass terminé',
      unlock: 'Pro débloque chaque palier, y compris ceux déjà atteints.', r_xp: '+{v} XP', r_freeze: 'Gel de streak', r_key: 'Clé de coffre', r_ai: '+{v} messages IA', r_cosmetic: 'Thème d’anneaux', r_badge: 'Badge de saison', new: 'Nouvelle saison',
      sname: { Liquidity: 'Liquidité', Momentum: 'Momentum', Patience: 'Patience', Precision: 'Précision', Edge: 'Edge', Flow: 'Flow', Focus: 'Focus', Clarity: 'Clarté', Balance: 'Équilibre', Resolve: 'Détermination', Discipline: 'Discipline', Mastery: 'Maîtrise' } },
    es: { season: 'Temporada {n}', tier: 'Nivel {t}', ends: 'Termina en {d} días', ends1: 'Termina mañana', free: 'Gratis', pro: 'Pro', claim: 'Reclamar', to_next: '{p} XP para el nivel {t}', max: 'Pase completo',
      unlock: 'Pro desbloquea cada nivel, incluidos los que ya alcanzaste.', r_xp: '+{v} XP', r_freeze: 'Congelador de racha', r_key: 'Llave de cofre', r_ai: '+{v} mensajes IA', r_cosmetic: 'Tema de anillos', r_badge: 'Insignia de temporada', new: 'Nueva temporada',
      sname: { Liquidity: 'Liquidez', Momentum: 'Momentum', Patience: 'Paciencia', Precision: 'Precisión', Edge: 'Ventaja', Flow: 'Flujo', Focus: 'Enfoque', Clarity: 'Claridad', Balance: 'Equilibrio', Resolve: 'Determinación', Discipline: 'Disciplina', Mastery: 'Maestría' } },
  };
  const sst = (k, p) => { const g = (o) => k.split('.').reduce((a, x) => (a == null ? a : a[x]), o); let s = g(SS_T[L()]); if (s == null) s = g(SS_T.en); if (s == null) s = k; return typeof s === 'string' && p ? s.replace(/\{(\w+)\}/g, (m, x) => (p[x] != null ? p[x] : m)) : s; };
  const SEASON_PAL = [['#4C8DFF', '#7FD8FF', '#2F5FD0'], ['#5B8CFF', '#A08BFF', '#3C4FD8'], ['#4FC3B0', '#9BE6D5', '#2A8C7E'], ['#E0A84F', '#F5D59A', '#A97A2E'], ['#7C9CFF', '#C7D2FF', '#4D63C9'], ['#56CCF2', '#A7E9FF', '#2D8FB5'],
    ['#8B7CFF', '#D1C9FF', '#5D4ED8'], ['#F2F2F3', '#B9BCC4', '#6C7080'], ['#6FA8FF', '#B5D3FF', '#3B6BD1'], ['#4C8DFF', '#E0A84F', '#2E6BE0'], ['#3D7BFF', '#88B4FF', '#1D4BB8'], ['#E0B565', '#FFF1CC', '#B68A2E']];
  const seasonNum = (m) => (+m.slice(0, 4) - 2026) * 12 + (+m.slice(4, 6)) - 10 + 1;
  // seasonal ring themes: ring_sYYYYMM (season), ring_eYYYYMM (Elite exclusive)
  const origApply = applyTheme;
  applyTheme = function (id) {
    const m = /^ring_([se])(\d{6})$/.exec(id || '');
    if (!m) return origApply(id);
    const p = SEASON_PAL[(Math.max(1, seasonNum(m[2])) - 1) % 12], c = m[1] === 'e' ? [p[0], '#E0B565', p[2]] : p;
    const r = document.documentElement.style; r.setProperty('--g-plan', c[0]); r.setProperty('--g-exec', c[1]); r.setProperty('--g-rev', c[2]);
  };
  const themeCols = (id) => { const m = /^ring_([se])(\d{6})$/.exec(id || ''); if (!m) return THEMES[id]; const p = SEASON_PAL[(Math.max(1, seasonNum(m[2])) - 1) % 12]; return m[1] === 'e' ? [p[0], '#E0B565', p[2]] : p; };
  const themeName = (id) => { const m = /^ring_([se])(\d{6})$/.exec(id || ''); return m ? `${sst('season', { n: seasonNum(m[2]) })}${m[1] === 'e' ? ' Elite' : ''}` : wt('th.' + id); };

  function seasonPill() {
    const s = G.season; if (!s) return '';
    return `<button type="button" class="gc-pill ss-pill ${s.claimable ? 'has' : ''}" data-g="season">${svg('flag')}<span><small>${esc(sst('season', { n: s.number }))} · ${esc(sst('sname.' + s.name))}</small><b>${sst('tier', { t: s.tier })}</b></span></button>`;
  }
  const rwIcon = (r) => r.type === 'xp' ? svg('star') : r.type === 'freeze' ? svg('snow') : r.type === 'key' ? svg('target') : r.type === 'ai_credits' ? svg('spark') : r.type === 'badge' ? svg('flag') : `<i class="wk-sw" style="--a:${(themeCols(r.value) || [])[0]};--b:${(themeCols(r.value) || [])[1]}"></i>`;
  const rwLabel = (r) => sst(r.type === 'ai_credits' ? 'r_ai' : 'r_' + r.type, { v: r.value }) + (r.type === 'cosmetic' ? ` · ${themeName(r.value)}` : '');
  async function openSeason() {
    openSheet(`${head(sst('season', { n: G.season ? G.season.number : '' }))}<div class="ss-body"><div class="skel" style="height:300px;border-radius:18px"></div></div>`, { cls: 'ss-sheet' });
    try { [G.ss, G.mapFull] = await Promise.all([apiJSON('api/game/season'), apiJSON('api/game/map').catch(() => G.mapFull)]); } catch (e) { return; }
    renderSeason();
  }
  function renderSeason(flash) {
    const s = G.ss, box = document.querySelector('#gSheet .ss-body'); if (!s || !box) return;
    const days = Math.max(1, Math.ceil((s.ends_at * 1000 - Date.now()) / 86400000));
    const inTier = s.points % s.per_tier, next = Math.min(30, s.tier + 1);
    const cell = (t, track) => {
      const r = t[track]; if (!r) return '<div class="ss-cell empty"></div>';
      const reached = t.tier <= s.tier, lockedPro = track === 'premium' && !s.premium;
      const st = r.claimed ? 'claimed' : reached && !lockedPro ? 'ready' : 'locked';
      return `<button type="button" class="ss-cell ${track} ${st} ${flash === `${t.tier}${track}` ? 'flash' : ''}" ${st === 'ready' ? `data-g="ss-claim" data-v="${t.tier}" data-k="${track}"` : lockedPro && reached ? 'data-g="locked"' : 'disabled'} title="${esc(rwLabel(r))}">
        <span class="ss-ic">${rwIcon(r)}</span><small>${esc(rwLabel(r))}</small>${st === 'claimed' ? `<i class="ss-ok">${svg('sweep')}</i>` : lockedPro ? `<i class="ss-lk">${svg('lock')}</i>` : ''}</button>`;
    };
    box.innerHTML = `<div class="ss-head"><div><span class="g-kick">${esc(sst('sname.' + s.name))}</span><b>${sst('tier', { t: s.tier })}<small> / 30</small></b></div><span class="ss-ends">${days <= 1 ? sst('ends1') : sst('ends', { d: days })}</span></div>
      <span class="g-bar big"><i style="width:${s.tier >= 30 ? 100 : (inTier / s.per_tier) * 100}%"></i></span><small class="muted">${s.tier >= 30 ? sst('max') : sst('to_next', { p: s.per_tier - inTier, t: next })}</small>
      <div class="ss-track"><div class="ss-labels"><span>${sst('free')}</span><span class="pro">${sst('pro')}</span></div><div class="ss-cols">${s.tiers.map((t) => `<div class="ss-col ${t.tier <= s.tier ? 'reached' : ''} ${t.tier === s.tier ? 'cur' : ''}"><span class="ss-n">${t.tier}</span>${cell(t, 'free')}${cell(t, 'premium')}</div>`).join('')}</div></div>
      ${s.premium ? '' : `<div class="ss-up"><p>${sst('unlock')}</p><button type="button" class="btn primary" data-g="locked">${t('v2.locked_ch')}</button></div>`}`;
    if (G.mapFull) box.insertAdjacentHTML('beforeend', `<div class="ss-journey"><h4>${esc(t('v2.journey'))}</h4><div class="gm-map">${mapHtml()}</div></div>`);
    const cur = box.querySelector('.ss-col.cur'); if (cur) cur.scrollIntoView({ inline: 'center', block: 'nearest', behavior: 'auto' });
  }
  async function ssClaim(tier, track) {
    try {
      const r = await apiJSON('api/game/season/claim', { method: 'POST', body: { tier: +tier, track } });
      G.ss = r.season; renderSeason(`${tier}${track}`); buzz([8, 20, 8]); chime();
      for (const it of r.items || []) await xpFloat(0, rwLabel(it));
      if (G.season) { G.season.claimable = Math.max(0, (G.season.claimable || 1) - 1); paint(); }
    } catch (e) { /* refused: nothing changes */ }
  }

  /* ───────────── V3: social profile + weekly leagues ───────────── */
  const LG_T = {
    en: { tiers: { 1: 'Bronze', 2: 'Silver', 3: 'Gold', 4: 'Platinum', 5: 'Diamond' }, league: '{t} league', rank: '{r} of {n}', ends: 'Ends in {d} d', social: 'Social', handle: 'Public handle', handle_ph: 'e.g. mateo_fx',
      join: 'Take part in weekly leagues', join_d: 'Only your handle, an initial and this week’s XP are visible. Never P&L, trades or accounts.', save: 'Save', saved: 'Saved',
      e_handle_format: '3 to 20 letters, digits, _ . -', e_handle_taken: 'This handle is taken', e_handle_refused: 'Pick another handle', e_handle_required: 'Choose a handle first',
      up: 'Promotion zone', down: 'Relegation zone', report: 'Report this handle', reported: 'Thanks, we will look at it.', you: 'You', how: 'Ranking = XP earned this week, from discipline only.',
      res_t: 'League results', res_p: 'Promoted to {t}', res_d: 'Back to {t}', res_s: 'You stay in {t}', res_r: 'You finished {r} of {n}.', open: 'Open the league' },
    fr: { tiers: { 1: 'Bronze', 2: 'Argent', 3: 'Or', 4: 'Platine', 5: 'Diamant' }, league: 'Ligue {t}', rank: '{r} sur {n}', ends: 'Fin dans {d} j', social: 'Social', handle: 'Pseudo public', handle_ph: 'ex. mateo_fx',
      join: 'Participer aux ligues hebdomadaires', join_d: 'Seuls ton pseudo, une initiale et ton XP de la semaine sont visibles. Jamais de P&L, de trades ni de comptes.', save: 'Enregistrer', saved: 'Enregistré',
      e_handle_format: '3 à 20 lettres, chiffres, _ . -', e_handle_taken: 'Ce pseudo est déjà pris', e_handle_refused: 'Choisis un autre pseudo', e_handle_required: 'Choisis d’abord un pseudo',
      up: 'Zone de promotion', down: 'Zone de relégation', report: 'Signaler ce pseudo', reported: 'Merci, on va regarder.', you: 'Toi', how: 'Classement = XP gagnée cette semaine, seulement par la discipline.',
      res_t: 'Résultats de la ligue', res_p: 'Promu en {t}', res_d: 'Retour en {t}', res_s: 'Tu restes en {t}', res_r: 'Tu as fini {r} sur {n}.', open: 'Voir la ligue' },
    es: { tiers: { 1: 'Bronce', 2: 'Plata', 3: 'Oro', 4: 'Platino', 5: 'Diamante' }, league: 'Liga {t}', rank: '{r} de {n}', ends: 'Termina en {d} d', social: 'Social', handle: 'Alias público', handle_ph: 'p. ej. mateo_fx',
      join: 'Participar en las ligas semanales', join_d: 'Solo se ven tu alias, una inicial y tu XP de la semana. Nunca P&L, trades ni cuentas.', save: 'Guardar', saved: 'Guardado',
      e_handle_format: '3 a 20 letras, números, _ . -', e_handle_taken: 'Este alias ya existe', e_handle_refused: 'Elige otro alias', e_handle_required: 'Primero elige un alias',
      up: 'Zona de ascenso', down: 'Zona de descenso', report: 'Reportar este alias', reported: 'Gracias, lo revisaremos.', you: 'Tú', how: 'Clasificación = XP ganada esta semana, solo por disciplina.',
      res_t: 'Resultados de la liga', res_p: 'Ascendido a {t}', res_d: 'De vuelta a {t}', res_s: 'Sigues en {t}', res_r: 'Terminaste {r} de {n}.', open: 'Ver la liga' },
  };
  const lgt = (k, p) => { const g = (o) => k.split('.').reduce((a, x) => (a == null ? a : a[x]), o); let s = g(LG_T[L()]); if (s == null) s = g(LG_T.en); if (s == null) s = k; return typeof s === 'string' && p ? s.replace(/\{(\w+)\}/g, (m, x) => (p[x] != null ? p[x] : m)) : s; };
  const ord = (n) => (L() === 'fr' ? (n === 1 ? '1er' : n + 'e') : L() === 'es' ? n + 'º' : n + (n % 10 === 1 && n % 100 !== 11 ? 'st' : n % 10 === 2 && n % 100 !== 12 ? 'nd' : n % 10 === 3 && n % 100 !== 13 ? 'rd' : 'th'));
  function leaguePill() {
    const l = G.league; if (!l) return '';
    return `<button type="button" class="gc-pill lg-pill t${l.tier}" data-g="league"><span class="lg-dot"></span><span><small>${esc(lgt('league', { t: lgt('tiers.' + l.tier) }))}</small><b>${esc(lgt('rank', { r: ord(l.rank), n: l.of }))}</b></span></button>`;
  }
  async function openLeague() {
    openSheet(`${head(esc(lgt('league', { t: lgt('tiers.' + (G.league ? G.league.tier : 1)) })))}<div class="lg-body"><div class="skel" style="height:320px;border-radius:18px"></div></div>`, { cls: 'lg-sheet' });
    let d; try { d = await apiJSON('api/game/league'); } catch (e) { return; }
    const box = document.querySelector('#gSheet .lg-body'); if (!box || !d.group) return;
    const g = d.group, n = g.members.length, days = Math.max(1, Math.ceil((g.ends_at * 1000 - Date.now()) / 86400000));
    box.innerHTML = `<div class="lg-top"><span class="lg-badge t${g.tier}">${svg('shield')}</span><div><b>${esc(lgt('tiers.' + g.tier))}</b><small>${lgt('ends', { d: days })} · ${n}</small></div></div>
      <p class="muted lg-how">${lgt('how')}</p>
      <ol class="lg-list">${g.members.map((m, i) => {
        const zone = i < g.promote ? 'up' : i >= n - g.relegate ? 'down' : '';
        return `${i === 0 && g.promote ? `<li class="lg-sep">${lgt('up')} ↑</li>` : ''}${i === g.promote && g.promote ? '<li class="lg-sep line"></li>' : ''}${i === n - g.relegate && g.relegate ? `<li class="lg-sep down">${lgt('down')} ↓</li>` : ''}
        <li class="lg-row ${zone} ${m.me ? 'me' : ''}" style="--i:${i}"><span class="lg-r">${i + 1}</span><span class="lg-av">${esc(m.initial)}</span><b>${esc(m.handle)}${m.me ? ` <i>${lgt('you')}</i>` : ''}</b><span class="lg-xp">${m.xp.toLocaleString(loc())} XP</span>
        ${m.me ? '' : `<button type="button" class="lg-more" data-g="lg-report" data-v="${m.ref}" aria-label="${lgt('report')}" title="${lgt('report')}">⋯</button>`}</li>`;
      }).join('')}</ol>`;
    const me = box.querySelector('.lg-row.me'); if (me) me.scrollIntoView({ block: 'center' });
  }
  async function socialHtml() {
    let p = G.social; if (!p) { try { p = G.social = await apiJSON('api/game/social'); } catch (e) { return ''; } }
    return p;
  }
  function socialCard() {
    const p = G.social; if (!p) return '';
    return `<div class="sec-h"><h2>${lgt('social')}</h2></div><div class="surface pad lg-social">
      <label class="g-f"><span>${lgt('handle')}</span><div class="lg-hrow"><input data-lg-handle value="${esc(p.handle || '')}" placeholder="${lgt('handle_ph')}" maxlength="20" autocomplete="off" autocapitalize="off" spellcheck="false"><button type="button" class="btn" data-g="lg-save">${lgt('save')}</button></div></label>
      <small class="lg-err" hidden></small>
      ${G.dc && G.dc.enabled ? (G.dc.linked
        ? `<div class="dc-row"><span class="dc-logo">${svg('hand')}</span><b>${esc(wrt('dc_linked', { n: G.dc.name || 'Discord' }))}</b><button type="button" class="link" data-g="dc-unlink">${wrt('dc_unlink')}</button></div>
           <div class="g-sound"><span><b>${wrt('dc_share')}</b><small class="muted">${wrt('dc_share_d')}</small></span><label class="sw"><input type="checkbox" data-dc-share ${G.dc.share ? 'checked' : ''}><i></i></label></div>`
        : `<a class="btn dc-link" href="api/game/discord/start">${wrt('dc_link')}</a>`) : ''}
      <button type="button" class="btn cr-open" data-g="social">${svg('hand')}${typeof crt === 'function' ? crt('social') : 'Crew'}</button>
      <div class="g-sound"><span><b>${lgt('join')}</b><small class="muted">${lgt('join_d')}</small></span><label class="sw"><input type="checkbox" data-lg-opt ${p.league_opt_in ? 'checked' : ''}><i></i></label></div></div>`;
  }
  async function saveSocial(body) {
    const err = document.querySelector('.lg-err');
    try {
      const r = await apiJSON('api/game/social', { method: 'POST', body });
      G.social = r.profile; if (err) err.hidden = true; toast(lgt('saved')); load(true);
      const el = document.getElementById('gBdg'); if (el) { el._h = null; paintSections(); }
    } catch (e) {
      const code = (e && e.data && e.data.error) || (e && e.message) || '';
      if (err) { err.textContent = lgt('e_' + code) !== 'e_' + code ? lgt('e_' + code) : lgt('e_handle_format'); err.hidden = false; }
      const box = document.querySelector('[data-lg-opt]'); if (box && body.league_opt_in) box.checked = false;
    }
  }

  /* ───────────── V3: crews + accountability buddy ───────────── */
  const CR_T = {
    en: { social: 'Crew & buddy', crew: 'Crew', buddy: 'Buddy', join_t: 'Join a crew', code_ph: 'Invite code', join: 'Join', create_t: 'Create a crew', name_ph: 'Crew name', create: 'Create', pro_only: 'Creating a crew is a Pro feature. Joining is free.',
      need_handle: 'Choose a public handle in Settings → Social first.', week: 'This week', goal: '{d} / {g} days swept', streak_w: '{n}-week streak', factor: 'Weekly goal', per: '× members', invite: 'Invite', copied: 'Invite link copied', leave: 'Leave the crew',
      feed: 'Crew feed', ev: { created: '{h} created the crew', joined: '{h} joined', left: '{h} left', swept: '{h} swept the day', boss: '{h} beat {b}', streak: '{h}: {n}-day streak', rank: '{h} is now {r}', goal_met: 'Weekly goal reached!' },
      b_none: 'Pick one trader to keep each other on track. They see your rings and streak, never your trades.', b_handle: 'Their handle', b_invite: 'Invite', b_sent: 'Invitation sent to {h}', b_cancel: 'Cancel',
      b_in: '{h} wants to be your buddy', b_accept: 'Accept', b_decline: 'Decline', b_cheer: 'Cheer them on', b_cheered: 'Cheered today', b_end: 'End the buddy link', b_streak: '{n}-day streak',
      crew_goal: 'Crew goal reached', crew_goal_s: '{n}: the whole crew earned a chest key.', join_link: 'Join {code}?',
      e: { code_invalid: 'This code does not exist', crew_full: 'This crew is full (5)', already_in_crew: 'You are already in a crew', name_invalid: 'Pick another name (3-40 characters)', upgrade_required: 'Creating a crew is a Pro feature',
        handle_required: 'Choose a public handle first', handle_unknown: 'No trader with this handle', they_have_buddy: 'They already have a buddy', already_buddy: 'You already have a buddy' },
      n: { 'buddy_invite.title': '{handle} wants to be your buddy', 'buddy_invite.body': 'Open Sweep to accept.', 'buddy_cheer.title': '{handle} is cheering you on', 'buddy_cheer.body': 'You can do it. Sweep your day.', 'buddy_swept.title': '{handle} swept the day', 'buddy_swept.body': 'Your turn.' } },
    fr: { social: 'Crew et buddy', crew: 'Crew', buddy: 'Buddy', join_t: 'Rejoindre un crew', code_ph: 'Code d’invitation', join: 'Rejoindre', create_t: 'Créer un crew', name_ph: 'Nom du crew', create: 'Créer', pro_only: 'Créer un crew est une fonction Pro. Rejoindre est gratuit.',
      need_handle: 'Choisis d’abord un pseudo public dans Réglages → Social.', week: 'Cette semaine', goal: '{d} / {g} journées balayées', streak_w: 'Streak de {n} semaines', factor: 'Objectif hebdo', per: '× membres', invite: 'Inviter', copied: 'Lien d’invitation copié', leave: 'Quitter le crew',
      feed: 'Fil du crew', ev: { created: '{h} a créé le crew', joined: '{h} a rejoint le crew', left: '{h} est parti', swept: '{h} a balayé sa journée', boss: '{h} a battu {b}', streak: '{h} : streak de {n} jours', rank: '{h} est maintenant {r}', goal_met: 'Objectif de la semaine atteint !' },
      b_none: 'Choisis un trader pour vous garder sur la bonne voie. Il voit tes anneaux et ton streak, jamais tes trades.', b_handle: 'Son pseudo', b_invite: 'Inviter', b_sent: 'Invitation envoyée à {h}', b_cancel: 'Annuler',
      b_in: '{h} veut être ton buddy', b_accept: 'Accepter', b_decline: 'Refuser', b_cheer: 'Encourager', b_cheered: 'Encouragé aujourd’hui', b_end: 'Terminer le lien buddy', b_streak: 'Streak de {n} jours',
      crew_goal: 'Objectif du crew atteint', crew_goal_s: '{n} : tout le crew gagne une clé de coffre.', join_link: 'Rejoindre {code} ?',
      e: { code_invalid: 'Ce code n’existe pas', crew_full: 'Ce crew est complet (5)', already_in_crew: 'Tu es déjà dans un crew', name_invalid: 'Choisis un autre nom (3 à 40 caractères)', upgrade_required: 'Créer un crew est une fonction Pro',
        handle_required: 'Choisis d’abord un pseudo public', handle_unknown: 'Aucun trader avec ce pseudo', they_have_buddy: 'Cette personne a déjà un buddy', already_buddy: 'Tu as déjà un buddy' },
      n: { 'buddy_invite.title': '{handle} veut être ton buddy', 'buddy_invite.body': 'Ouvre Sweep pour accepter.', 'buddy_cheer.title': '{handle} t’encourage', 'buddy_cheer.body': 'Tu peux le faire. Balaye ta journée.', 'buddy_swept.title': '{handle} a balayé sa journée', 'buddy_swept.body': 'À ton tour.' } },
    es: { social: 'Crew y buddy', crew: 'Crew', buddy: 'Buddy', join_t: 'Unirse a un crew', code_ph: 'Código de invitación', join: 'Unirse', create_t: 'Crear un crew', name_ph: 'Nombre del crew', create: 'Crear', pro_only: 'Crear un crew es una función Pro. Unirse es gratis.',
      need_handle: 'Primero elige un alias público en Ajustes → Social.', week: 'Esta semana', goal: '{d} / {g} días barridos', streak_w: 'Racha de {n} semanas', factor: 'Objetivo semanal', per: '× miembros', invite: 'Invitar', copied: 'Enlace copiado', leave: 'Salir del crew',
      feed: 'Actividad del crew', ev: { created: '{h} creó el crew', joined: '{h} se unió', left: '{h} salió', swept: '{h} barrió su día', boss: '{h} venció a {b}', streak: '{h}: racha de {n} días', rank: '{h} ahora es {r}', goal_met: '¡Objetivo semanal logrado!' },
      b_none: 'Elige a un trader para mantenerse en el camino. Ve tus anillos y tu racha, nunca tus trades.', b_handle: 'Su alias', b_invite: 'Invitar', b_sent: 'Invitación enviada a {h}', b_cancel: 'Cancelar',
      b_in: '{h} quiere ser tu buddy', b_accept: 'Aceptar', b_decline: 'Rechazar', b_cheer: 'Animar', b_cheered: 'Animado hoy', b_end: 'Terminar el vínculo', b_streak: 'Racha de {n} días',
      crew_goal: 'Objetivo del crew logrado', crew_goal_s: '{n}: todo el crew gana una llave de cofre.', join_link: '¿Unirse a {code}?',
      e: { code_invalid: 'Este código no existe', crew_full: 'Este crew está completo (5)', already_in_crew: 'Ya estás en un crew', name_invalid: 'Elige otro nombre (3-40 caracteres)', upgrade_required: 'Crear un crew es una función Pro',
        handle_required: 'Primero elige un alias público', handle_unknown: 'Ningún trader con este alias', they_have_buddy: 'Ya tiene un buddy', already_buddy: 'Ya tienes un buddy' },
      n: { 'buddy_invite.title': '{handle} quiere ser tu buddy', 'buddy_invite.body': 'Abre Sweep para aceptar.', 'buddy_cheer.title': '{handle} te anima', 'buddy_cheer.body': 'Puedes hacerlo. Barre tu día.', 'buddy_swept.title': '{handle} barrió su día', 'buddy_swept.body': 'Te toca.' } },
  };
  const crt = (k, p) => { const g = (o) => k.split('.').reduce((a, x) => (a == null ? a : a[x]), o); let s = g(CR_T[L()]); if (s == null) s = g(CR_T.en); if (s == null) s = k; return typeof s === 'string' && p ? s.replace(/\{(\w+)\}/g, (m, x) => (p[x] != null ? p[x] : m)) : s; };
  if (window.SweepNotify && SweepNotify.strings) { try { SweepNotify.strings({ en: CR_T.en.n, fr: CR_T.fr.n, es: CR_T.es.n }); } catch (e) { /* older module */ } }
  const SC = { tab: 'crew', d: null, code: '' };
  function socialPill() {
    const c = G.crew, b = G.buddy;
    if (c) return `<button type="button" class="gc-pill cr-pill" data-g="social">${svg('hand')}<span><small>${esc(c.name)}</small><b>${crt('goal', { d: c.done, g: c.goal })}</b></span></button>`;
    if (b && b.incoming) return `<button type="button" class="gc-pill cr-pill has" data-g="social" data-v="buddy">${svg('hand')}<span><small>${crt('buddy')}</small><b>${esc(crt('b_in', { h: b.handle }))}</b></span></button>`;
    if (b && b.status === 'active') return `<button type="button" class="gc-pill cr-pill" data-g="social" data-v="buddy">${svg('hand')}<span><small>${crt('buddy')}</small><b>${esc(b.handle)}</b></span></button>`;
    return '';
  }
  async function openSocial(tab) {
    if (tab) SC.tab = tab;
    openSheet(`${head(crt('social'))}<div class="seg cr-tabs"><button type="button" data-g="sc-tab" data-v="crew" class="${SC.tab === 'crew' ? 'on' : ''}">${crt('crew')}</button><button type="button" data-g="sc-tab" data-v="buddy" class="${SC.tab === 'buddy' ? 'on' : ''}">${crt('buddy')}</button></div><div class="cr-body"><div class="skel" style="height:260px;border-radius:18px"></div></div>`, { cls: 'cr-sheet' });
    try { SC.d = await apiJSON('api/game/crew'); } catch (e) { return; }
    renderSocial();
  }
  const memberRow = (m) => `<li class="cr-m ${m.me ? 'me' : ''}"><span class="lg-av">${esc(m.initial)}</span><span class="cr-mid"><b>${esc(m.handle)}</b><small>${esc(rankName(m.rank))} · ${t('lvl', { n: m.level })}${m.boss ? ' · ' + esc(bossName(m.boss)) : ''}</small></span>${m.rings ? miniRings(m.rings) : ''}<span class="cr-st">${CANDLE()}<b>${m.streak}</b></span></li>`;
  function renderSocial() {
    const box = document.querySelector('#gSheet .cr-body'), d = SC.d; if (!box || !d) return;
    document.querySelectorAll('#gSheet [data-g=sc-tab]').forEach((b) => b.classList.toggle('on', b.dataset.v === SC.tab));
    const hint = `<p class="cr-err" hidden></p>`;
    if (SC.tab === 'crew') {
      const c = d.crew;
      if (!c) {
        box.innerHTML = `${d.has_handle ? '' : `<p class="g-hint">${crt('need_handle')}</p>`}
          <section class="surface pad cr-card"><h3>${crt('join_t')}</h3><div class="lg-hrow"><input data-cr-code value="${esc(SC.code)}" placeholder="${crt('code_ph')}" autocapitalize="characters" maxlength="12"><button type="button" class="btn primary" data-g="cr-join">${crt('join')}</button></div></section>
          <section class="surface pad cr-card"><h3>${crt('create_t')}</h3>${d.can_create ? `<div class="lg-hrow"><input data-cr-name placeholder="${crt('name_ph')}" maxlength="40"><button type="button" class="btn" data-g="cr-create">${crt('create')}</button></div>` : `<p class="muted">${crt('pro_only')}</p><button type="button" class="btn" data-g="locked">${t('v2.locked_ch')}</button>`}</section>${hint}`;
        return;
      }
      const pct = Math.min(100, (c.week.done / Math.max(1, c.week.goal)) * 100);
      box.innerHTML = `<div class="cr-head"><div><b>${esc(c.name)}</b><small>${c.members.length}/${c.max}${c.streak_weeks ? ' · ' + crt('streak_w', { n: c.streak_weeks }) : ''}</small></div><button type="button" class="btn sm" data-g="cr-invite" data-v="${esc(c.code)}">${svg('share')}${crt('invite')}</button></div>
        <div class="cr-goal ${c.week.met ? 'met' : ''}"><span class="g-kick">${crt('week')}</span><b>${crt('goal', { d: c.week.done, g: c.week.goal })}</b><span class="g-bar big"><i style="width:${pct}%"></i></span>
          ${c.owner ? `<div class="cr-factor"><small>${crt('factor')} (${crt('per').replace('× ', '× ')})</small><div class="seg">${[2, 3, 4, 5].map((f) => `<button type="button" class="${c.factor === f ? 'on' : ''}" data-g="cr-goal" data-v="${f}">${f}×</button>`).join('')}</div></div>` : ''}</div>
        <ul class="cr-members">${c.members.map(memberRow).join('')}</ul>
        <h3 class="cr-h">${crt('feed')}</h3><ul class="cr-feed">${c.feed.map((e) => `<li><span>${esc(crt('ev.' + e.type, { h: e.handle, b: e.data.boss ? bossName(e.data.boss) : '', n: e.data.n || '', r: e.data.rank ? rankName(e.data.rank) : '' }))}</span><small>${new Date(e.at * 1000).toLocaleDateString(loc(), { weekday: 'short', hour: 'numeric', minute: '2-digit' })}</small>
          <div class="cr-rx">${d.emoji.map((em) => `<button type="button" class="${e.reactions[em] && e.reactions[em].mine ? 'on' : ''}" data-g="cr-react" data-v="${e.id}" data-k="${em}">${em}${e.reactions[em] ? `<i>${e.reactions[em].n}</i>` : ''}</button>`).join('')}</div></li>`).join('')}</ul>
        <button type="button" class="link cr-leave" data-g="cr-leave">${crt('leave')}</button>`;
      return;
    }
    const b = d.buddy;
    if (!b) box.innerHTML = `${d.has_handle ? '' : `<p class="g-hint">${crt('need_handle')}</p>`}<section class="surface pad cr-card"><p class="muted" style="margin:0 0 12px">${crt('b_none')}</p><div class="lg-hrow"><input data-bd-handle placeholder="${crt('b_handle')}" autocapitalize="off" spellcheck="false" maxlength="20"><button type="button" class="btn primary" data-g="bd-invite">${crt('b_invite')}</button></div></section>${hint}`;
    else if (b.status === 'pending' && b.incoming) box.innerHTML = `<section class="surface pad cr-card"><h3>${esc(crt('b_in', { h: b.card.handle }))}</h3><div class="g-acts"><button type="button" class="btn" data-g="bd-respond" data-v="0">${crt('b_decline')}</button><button type="button" class="btn primary" data-g="bd-respond" data-v="1">${crt('b_accept')}</button></div></section>`;
    else if (b.status === 'pending') box.innerHTML = `<section class="surface pad cr-card"><p style="margin:0 0 10px">${esc(crt('b_sent', { h: b.card.handle }))}</p><button type="button" class="link" data-g="bd-end">${crt('b_cancel')}</button></section>`;
    else box.innerHTML = `<section class="surface cr-bcard"><span class="lg-av big">${esc(b.card.initial)}</span><b>${esc(b.card.handle)}</b><small>${esc(rankName(b.card.rank))} · ${crt('b_streak', { n: b.card.streak })}</small>
        ${b.card.rings ? `<div class="cr-brings">${miniRings(b.card.rings)}</div>` : ''}<button type="button" class="btn primary g-big" data-g="bd-cheer" ${b.cheered ? 'disabled' : ''}>${b.cheered ? crt('b_cheered') : crt('b_cheer')}</button></section>
      <button type="button" class="link cr-leave" data-g="bd-end">${crt('b_end')}</button>`;
  }
  async function scPost(path, body) {
    try { const r = await apiJSON(path, { method: 'POST', body: body || {} }); SC.d = Object.assign(SC.d || {}, r); renderSocial(); load(true); buzz(6); return r; }
    catch (e) { const code = e && e.data && e.data.error; const el = document.querySelector('#gSheet .cr-err'); if (el) { el.textContent = crt('e.' + code) !== 'e.' + code ? crt('e.' + code) : String(code || ''); el.hidden = false; } else if (code) toast(crt('e.' + code)); }
  }
  // invite links: …/#crew/CODE opens the join card
  const crewLink = () => { const m = /^#crew\/([A-Z0-9]{6,12})$/i.exec(location.hash); if (m && on()) { SC.code = m[1].toUpperCase(); SC.tab = 'crew'; history.replaceState(null, '', '#dashboard'); setTimeout(() => openSocial('crew'), 600); } };
  addEventListener('hashchange', crewLink); setTimeout(crewLink, 1500);

  // back from Discord: one toast, then a clean address
  setTimeout(() => { const m = /[?&]discord=(linked|error)/.exec(location.search); if (!m) return; if (m[1] === 'error') toast(wrt('dc_err')); history.replaceState(null, '', location.pathname + location.hash); }, 1200);


  /* ───────────── progressive reveal: the « new » moment ───────────── */
  const UN_T = {
    en: { kick: 'Unlocked', missions: ['Weekly missions', 'Three goals every Monday, picked from your own weak spots. All three done: a chest key.'],
      weekly: ['Weekly recap and chest', 'Every Friday after the close: your week, a truth from your own trades, and a chest to open.'],
      boss: ['Bosses', 'Sweep now spots a bad habit in your trades and turns it into a boss. Every clean day lands a hit.'],
      season: ['Seasons', 'Each month is a season with 30 tiers. Your discipline XP moves you up; claim the rewards.'],
      league: ['Weekly leagues', 'Optional: compete on discipline XP with other traders. Only your handle shows, never your P&L.'],
      social: ['Crew and buddy', 'Optional: a small crew with a shared weekly goal, or one buddy to keep each other on track.'] },
    fr: { kick: 'Débloqué', missions: ['Missions hebdomadaires', 'Trois objectifs chaque lundi, choisis selon tes points faibles. Les trois faits : une clé de coffre.'],
      weekly: ['Bilan de la semaine et coffre', 'Chaque vendredi après la clôture : ta semaine, une vérité tirée de tes trades, et un coffre à ouvrir.'],
      boss: ['Les boss', 'Sweep repère maintenant une mauvaise habitude dans tes trades et la transforme en boss. Chaque journée propre lui porte un coup.'],
      season: ['Les saisons', 'Chaque mois est une saison de 30 paliers. Ton XP de discipline te fait monter ; réclame tes récompenses.'],
      league: ['Ligues hebdomadaires', 'Facultatif : affronte d’autres traders sur l’XP de discipline. Seul ton pseudo s’affiche, jamais ton P&L.'],
      social: ['Crew et buddy', 'Facultatif : un petit crew avec un objectif commun, ou un buddy pour vous garder sur la bonne voie.'] },
    es: { kick: 'Desbloqueado', missions: ['Misiones semanales', 'Tres objetivos cada lunes según tus puntos débiles. Las tres completas: una llave de cofre.'],
      weekly: ['Resumen semanal y cofre', 'Cada viernes tras el cierre: tu semana, una verdad de tus operaciones y un cofre.'],
      boss: ['Jefes', 'Sweep detecta un mal hábito en tus operaciones y lo convierte en jefe. Cada día limpio le quita vida.'],
      season: ['Temporadas', 'Cada mes es una temporada de 30 niveles. Tu XP de disciplina te hace subir.'],
      league: ['Ligas semanales', 'Opcional: compite en XP de disciplina. Solo se ve tu alias, nunca tu P&L.'],
      social: ['Crew y buddy', 'Opcional: un pequeño crew con un objetivo común, o un buddy.'] },
  };
  const unt = (f) => (UN_T[L()] || UN_T.en)[f] || UN_T.en[f];
  const UN_IC = { missions: 'target', weekly: 'star', boss: 'shield', season: 'flag', league: 'shield', social: 'hand' };


  /* ───────────── Progression: every game feature in one place (what is open, what unlocks next, your collection) ───────────── */
  const HUB_T = {
    en: { title: 'Progression', now: 'Your shortcuts', soon: 'Coming up', col: 'Your collection', badges: 'Badges', themes: 'Ring themes', wrapped: 'Your Wrapped', open_in: 'In Settings',
      lock: { missions: 'After your 1st swept day', weekly: 'After 2 swept days', boss: 'At level 3 or after 10 trades', season: 'After 7 days', league: 'After 7 days', social: 'After 7 days' } },
    fr: { title: 'Progression', now: 'Tes raccourcis', soon: 'À débloquer', col: 'Ta collection', badges: 'Badges', themes: 'Thèmes d’anneaux', wrapped: 'Tes Wrapped', open_in: 'Dans Réglages',
      lock: { missions: 'Après ta 1re journée balayée', weekly: 'Après 2 journées balayées', boss: 'Au niveau 3 ou après 10 trades', season: 'Après 7 jours', league: 'Après 7 jours', social: 'Après 7 jours' } },
    es: { title: 'Progreso', now: 'Tus accesos', soon: 'Por desbloquear', col: 'Tu colección', badges: 'Insignias', themes: 'Temas de anillos', wrapped: 'Tus Wrapped', open_in: 'En Ajustes',
      lock: { missions: 'Tras tu 1.er día barrido', weekly: 'Tras 2 días barridos', boss: 'Nivel 3 o tras 10 operaciones', season: 'Tras 7 días', league: 'Tras 7 días', social: 'Tras 7 días' } },
  };
  const hbt = (k) => k.split('.').reduce((a, x) => (a == null ? a : a[x]), HUB_T[L()]) ?? k.split('.').reduce((a, x) => (a == null ? a : a[x]), HUB_T.en);
  function stepsHtml() {
    const M = G.mapFull; if (!M || !M.chapters) return '';
    const ch = M.chapters.find((c) => !c.done && !c.locked) || M.chapters.find((c) => !c.done) || M.chapters[M.chapters.length - 1];
    if (!ch) return '';
    const nextId = M.next && M.next.id, done = ch.nodes.filter((n) => n.done).length;
    const rows = ch.nodes.map((n) => {
      const st = n.done ? 'done' : n.id === nextId ? 'next' : n.soon ? 'soon' : 'todo';
      const sub = n.done ? '' : n.soon ? t('v2.soon') : (n.target > 1 ? `${n.progress} / ${n.target} · ` : '') + nodeDesc(n.id);
      return `<button type="button" class="gc-step ${st}" data-g="node" data-v="${esc(n.id)}" ${ch.locked ? 'disabled' : ''}>
        <span class="gc-step-ic">${n.done ? svg('sweep') : st === 'next' ? '<i></i>' : ''}</span>
        <span class="gc-step-t"><b>${esc(nodeName(n.id))}</b>${sub ? `<small>${esc(sub)}</small>` : ''}</span>
        ${st === 'next' ? `<span class="gc-step-go">${t('v2.go')}</span>` : svg('chev')}</button>`;
    }).join('');
    return `<div class="gc-steps-h"><h4>${t('v2.journey')}</h4><span class="muted">${t('v2.chapter', { n: ch.pos })} · ${esc(t('v2.ch.' + ch.n))} · ${done}/${ch.nodes.length}</span></div>
      <span class="g-bar gc-steps-bar"><i style="width:${(done / Math.max(1, ch.nodes.length)) * 100}%"></i></span>
      <div class="gc-step-list">${rows}</div>
      <button type="button" class="link gc-steps-all" data-g="map">${t('v2.journey')} ›</button>`;
  }
  function openHub() {
    const locked = Object.keys(UN_T.en).filter((k) => k !== 'kick' && G.unlocked && !G.unlocked.includes(k));
    const pills = (G.allPills || []).join('');
    openSheet(`${head(hbt('title'))}<div class="gc-hubwrap">
      <div class="gc-steps"><div class="skel" style="height:210px;border-radius:16px"></div></div>
      ${pills ? `<h4>${hbt('now')}</h4><div class="gc-hub">${pills}</div>` : ''}
      ${locked.length ? `<h4>${hbt('soon')}</h4><div class="gc-hub">${locked.map((k) => `<div class="gc-pill locked">${svg('lock')}<span><small>${esc(hbt('lock.' + k))}</small><b>${esc(unt(k)[0])}</b></span></div>`).join('')}</div>` : ''}
      <h4>${hbt('col')}</h4><div class="gc-hubcol"><div class="skel" style="height:160px;border-radius:16px"></div></div></div>`, { cls: 'gc-hubsheet' });
    // « Your journey »: the steps of the current chapter, the next one highlighted, each opening what it is about
    const drawSteps = () => { const box = document.querySelector('#gSheet .gc-steps'); if (box) box.innerHTML = stepsHtml(); };
    if (G.mapFull) setTimeout(drawSteps, 60);
    apiJSON('api/game/map').then((m) => { G.mapFull = m; drawSteps(); }).catch(() => { const box = document.querySelector('#gSheet .gc-steps'); if (box) box.remove(); });
    // the collection (badges, themes, social) is heavy: it fills once the sheet has finished sliding in
    const fill = () => { const c = document.querySelector('#gSheet .gc-hubcol'); if (c) c.innerHTML = badgesHtml(); };
    if (G.prog) setTimeout(fill, 340);
    else if (!G.progLoading) { G.progLoading = true; Promise.all([loadProgress(), new Promise((r) => setTimeout(r, 340))]).then(fill).finally(() => { G.progLoading = false; }); }
  }

  /* ───────────── events ───────────── */
  document.addEventListener('click', (e) => {
    const b = e.target.closest && e.target.closest('[data-g]');
    if (!b) return;
    const a = b.dataset.g, v = b.dataset.v;
    if (a === 'plan') { closeSheet(true); openPlan(G.detailDay && document.getElementById('gSheet') ? G.detailDay.day : null); }
    else if (a === 'add') { if (typeof openTicket === 'function') openTicket(null); }
    else if (a === 'plan-skip') { try { localStorage.setItem(skipKey, PL.day); } catch (x) { /* private mode */ } const then = PL.then; PL.then = null; closeSheet(true); if (then) setTimeout(then, 60); }
    else if (a === 'journal') { const d = G.detailDay && b.closest('#gSheet') ? G.detailDay : G.today; closeSheet(true); openJournal(d); }
    else if (a === 'review') { const d = G.detailDay && b.closest('#gSheet') ? G.detailDay : G.today; closeSheet(true); openReview(d.day); }
    else if (a === 'detail' || a === 'swept') openDetail(G.today);
    else if (a === 'yday') { G.detailDay = G.yesterday; openDetail(G.yesterday); }
    else if (a === 'dayoff') dayOff();
    else if (a === 'close') closeSheet();
    else if (a === 'close-nav') closeSheet(true);
    else if (a === 'progress-go') location.hash = '#analytics';
    else if (a === 'map') openMap();
    else if (a === 'exec-why') execWhy(G.detailDay || G.today);
    else if (a === 'detail-back') openDetail(G.detailDay || G.today);
    else if (a === 'weekly') openWeekly();
    else if (a === 'season') openSeason();
    else if (a === 'dc-unlink') apiJSON('api/game/discord/unlink', { method: 'POST', body: {} }).then((r) => { G.dc = r; const el = document.getElementById('gBdg'); if (el) { el._h = null; paintSections(); } }).catch(() => {});
    else if (a === 'hub') openHub();
    else if (a === 'wn-ok') { G.wnOpen = false; closeSheet(); }
    else if (a === 'league') { closeSheet(true); openLeague(); }
    else if (a === 'social') { closeSheet(true); openSocial(v || null); }
    else if (a === 'sc-tab') { SC.tab = v; renderSocial(); }
    else if (a === 'cr-join') { const i = document.querySelector('[data-cr-code]'); scPost('api/game/crew/join', { code: i ? i.value : '' }); }
    else if (a === 'cr-create') { const i = document.querySelector('[data-cr-name]'); scPost('api/game/crew/create', { name: i ? i.value : '' }); }
    else if (a === 'cr-goal') scPost('api/game/crew/goal', { factor: +v });
    else if (a === 'cr-react') scPost('api/game/crew/react', { id: +v, emoji: b.dataset.k });
    else if (a === 'cr-leave') { if (confirm(crt('leave') + ' ?')) scPost('api/game/crew/leave'); }
    else if (a === 'cr-invite') { const url = location.origin + location.pathname + '#crew/' + v; if (navigator.share) navigator.share({ title: 'Sweep', text: SC.d && SC.d.crew ? SC.d.crew.name : 'Sweep', url }).catch(() => {}); else { navigator.clipboard && navigator.clipboard.writeText(url); toast(crt('copied')); } }
    else if (a === 'bd-invite') { const i = document.querySelector('[data-bd-handle]'); scPost('api/game/buddy/invite', { handle: i ? i.value : '' }); }
    else if (a === 'bd-respond') scPost('api/game/buddy/respond', { accept: v === '1' });
    else if (a === 'bd-end') { if (confirm(crt('b_end') + ' ?')) scPost('api/game/buddy/end'); }
    else if (a === 'bd-cheer') scPost('api/game/buddy/cheer');
    else if (a === 'lg-save') { const i = document.querySelector('[data-lg-handle]'); saveSocial({ handle: i ? i.value.trim() : '' }); }
    else if (a === 'lg-report') { if (confirm(lgt('report') + ' ?')) apiJSON('api/game/report', { method: 'POST', body: { type: 'handle', id: v } }).then(() => toast(lgt('reported'))).catch(() => {}); }
    else if (a === 'ss-claim') ssClaim(v, b.dataset.k);
    else if (a === 'wrapped') { closeSheet(true); openWrapped(v); }
    else if (a === 'quest') questSheet();
    else if (a === 'wk-next') { WK.step = Math.min(3, WK.step + 1); renderWk(1); }
    else if (a === 'wk-flip') { if (!b.classList.contains('flipped')) { b.classList.add('flipped'); buzz(8); apiJSON('api/game/reveal/flip', { method: 'POST', body: { id: +v, lang: L() } }).then((r) => { if (r.texts && WK.data.reveal) { WK.data.reveal.texts = r.texts; WK.data.reveal.revealed = true; const p = b.querySelector('.wk-front p'); if (p) p.textContent = revealText(WK.data.reveal); } }).catch(() => {}); } }
    else if (a === 'wk-second') apiJSON('api/game/reveal/second').then((r) => { if (r.reveal) { WK.data.reveal = r.reveal; renderWk(0); } }).catch(() => {});
    else if (a === 'wk-grade') { WK.grade = +v; b.parentElement.querySelectorAll('button').forEach((x) => x.classList.toggle('on', x === b)); buzz(5); }
    else if (a === 'wk-save') { const q = { grade: WK.grade || (WK.data.answers || {}).grade || '' }; document.querySelectorAll('#gSheet [data-wq]').forEach((x) => { q[x.dataset.wq] = x.value; }); apiJSON('api/game/weekly', { method: 'POST', body: q }).then((r) => { WK.data.done = true; WK.data.answers = q; if (r.celebrations) queue(r.celebrations); WK.step = 2; renderWk(1); }).catch(() => {}); }
    else if (a === 'wk-chest') wkChest();
    else if (a === 'theme') apiJSON('api/game/cosmetics', { method: 'POST', body: { id: v } }).then((r) => { G.cos = r; G.cosmetic = r.equipped; applyTheme(r.equipped); const el = document.getElementById('gBdg'); if (el) { el._h = null; } paintSections(); buzz(6); }).catch(() => {});
    else if (a === 'boss') bossSheet(v);
    else if (a === 'missions') missionsSheet();
    else if (a === 'node') nodeSheet(v);
    else if (a === 'map-back') { const box = document.querySelector('#gSheet .g-in'); if (box) { box.innerHTML = `${head(t('v2.journey'))}<div class="gm-map">${mapHtml()}</div>`; } }
    else if (a === 'node-go') nodeGo(v);
    else if (a === 'reroll') apiJSON('api/game/missions/reroll', { method: 'POST', body: { id: +v } }).then((r) => { G.missions = r.missions; paint(); }).catch(() => {});
    else if (a === 'locked') { apiJSON('api/game/share', { method: 'POST', body: { kind: 'locked_tap' } }).catch(() => {}); if (window.SweepBilling && SweepBilling.paywall) { closeSheet(true); SweepBilling.paywall('generic'); } }
    else if (a === 'bias') { PL.bias = v; refreshPlan(); }
    else if (a === 'setup') { PL.setups.has(v) ? PL.setups.delete(v) : PL.setups.add(v); b.classList.toggle('on'); b.classList.remove('g-sug'); }
    else if (a === 'setup-new') { const box = b.closest('.g-setups').querySelector('.g-setup-add'); box.hidden = false; const i = box.querySelector('input'); i.focus(); }
    else if (a === 'setup-add') addPlanSetup(b.closest('.g-setups'));
    else if (a === 'same-plan') { const lp = lastPlan(PL.day); if (lp) { PL.bias = lp.pre.bias === 'no_trade' ? null : lp.pre.bias; PL.setups = new Set(lp.pre.setups || []); PL.max_loss = String(lp.pre.max_loss || '').replace(/[^0-9.]/g, ''); PL.max_trades = lp.pre.max_trades || ''; refreshPlan(); buzz(6); } }
    else if (a === 'save-plan') savePlan();
    else if (a === 'j-setup') jEdit((d) => { d.setup = v; });
    else if (a === 'j-emo') {
      // several emotions per trade; an older trade may hold a single emotion as text: it becomes a list
      b.classList.toggle('on');   // instant feedback, the sheet is then redrawn from the saved trade
      jEdit((d) => { d.emo = d.emo && typeof d.emo === 'object' ? d.emo : {}; const cur = d.emo.before; const s = new Set(Array.isArray(cur) ? cur : (typeof cur === 'string' && cur ? [cur] : [])); s.has(v) ? s.delete(v) : s.add(v); d.emo.before = [...s]; });
    }
    else if (a === 'j-rules') jEdit((d) => { d.rules_followed = v; });
    else if (a === 'j-next') jNext(false);
    else if (a === 'j-skip') jNext(true);
    else if (a === 'r-score') { RV.score = +v; b.parentElement.querySelectorAll('button').forEach((x) => x.classList.toggle('on', x === b)); buzz(5); }
    else if (a === 'save-review') saveReview();
    else if (a === 'share') shareCard(b.dataset.k, b.dataset.k === 'week' ? (document.querySelector('#gSheet [data-wk-pay]:checked') ? 'pay' : '') : v);
    else if (a === 'badge') badgeInfo(v);
    else if (a === 'ob-goal') { OB.goal = v; obUpdate(); buzz(5); }
    else if (a === 'ob-style') { OB.style = v; obUpdate(); buzz(5); }
    else if (a === 'ob-inst') { OB.inst.has(v) ? OB.inst.delete(v) : OB.inst.add(v); obUpdate(); }
    else if (a === 'ob-next') obNext();
    else if (a === 'ob-skip') obClose();
    else if (a === 'ob-mission') obClose(v);
  });
  const main_g_reset = () => { const m = document.getElementById('main'); if (m) m._g = null; };
  function refreshPlan() {
    document.querySelectorAll('#gSheet [data-gp]').forEach((i) => { PL[i.dataset.gp] = i.value; });
    const el = document.querySelector('#gSheet .g-in'); if (el) el.innerHTML = planHtml();
  }
  document.addEventListener('input', (e) => {
    const i = e.target.closest && e.target.closest('#gSheet [data-gp]');
    if (i) PL[i.dataset.gp] = i.value;
    const s = e.target.closest && e.target.closest('#gSheet [data-g-setup]');
    if (s) { const id = JN.ids[JN.i]; editDoc('trades', id, (d) => { d.setup = s.value.trim(); }, { delay: 600 }); }
  });
  document.addEventListener('change', (e) => {
    const dcs = e.target.closest && e.target.closest('[data-dc-share]');
    if (dcs) { apiJSON('api/game/discord/share', { method: 'POST', body: { on: dcs.checked } }).then((r) => { G.dc = r; }).catch(() => {}); return; }
    const o = e.target.closest && e.target.closest('[data-lg-opt]');
    if (o) { const i = document.querySelector('[data-lg-handle]'); saveSocial({ handle: i ? i.value.trim() : '', league_opt_in: o.checked }); return; }
    const s = e.target.closest && e.target.closest('[data-g-sound]');
    if (s) { G.profile.sound = s.checked; apiJSON('api/game/sound', { method: 'POST', body: { on: s.checked } }).catch(() => {}); if (s.checked) chime(); }
  });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && document.getElementById('gSheet')) { e.stopPropagation(); closeSheet(); } }, true);
  document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'visible') load(); });
  // the old Progress page now lives in Insights and Settings
  const legacy = () => { if (/^#progress/.test(location.hash)) location.replace('#analytics'); };
  addEventListener('hashchange', legacy); legacy();

  // after every app render: today card on Overview, Progression page, first load
  if (typeof render === 'function') {
    const appRender = render;
    render = function () {
      const out = appRender.apply(this, arguments);
      try { paint(); if (on() && !G.today && !G.busy) load(true); } catch (e) { console.error('[Sweep game]', e); }
      return out;
    };
  }
  paint();
  window.SweepGame = { refresh: () => load(true), openPlan, openReview, weekBrief,
    // the plan first (once a day) before a new trade — used by the screenshot way of adding a trade too
    state: () => ({ today: G.today || null, yesterday: G.yesterday || null, profile: G.profile || null, weekly: G.weekly || null }),   // for the « Your routine » card on Today (weekly: the week's recap, brief 01 step 5)
    planFirst: (then) => { if (!document.getElementById('gSheet') && planGateNeeded()) { openPlan(G.today.day, { then }); return true; } return false; }, openJournal: () => openJournal(), openGoal: () => openGoalQuestions(), t,
    next: () => { try { return progNext(); } catch (e) { return null; } },
    summary: () => (G.profile ? { rank: rankName(G.profile.rank), level: G.profile.level, streak: G.profile.streak.current, best: G.profile.streak.best, valid: G.profile.streak.today_valid } : null),
    open: (k, v) => ({ hub: openHub, map: openMap, missions: missionsSheet, season: openSeason, league: openLeague, social: () => openSocial(v), weekly: openWeekly, plan: openPlan, review: openReview, wrapped: () => openWrapped(v) })[k]?.() };
})();

