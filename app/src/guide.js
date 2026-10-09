/*
 * Sweep — first-run guidance and help.
 *  1. Welcome tour (coach marks on the real interface), once, after the first account exists; replayable in Settings.
 *  2. A tip the first time each page is opened (one card, dismissible, links to the full guide).
 *  3. « Get started » checklist on Today: 7 steps detected automatically from the trader's data.
 *  4. Help center: searchable articles for every feature, with « do it now » buttons. Opens from the « ? » in the header.
 * State is kept on the device (localStorage); nothing here can block the app.
 */
(function () {
  'use strict';
  if (typeof render !== 'function') return;
  const KEY = 'sw.guide';
  const st = (() => { try { return JSON.parse(localStorage.getItem(KEY) || '{}'); } catch (e) { return {}; } })();
  st.tips = st.tips || {}; st.visited = st.visited || {};
  const save = () => { try { localStorage.setItem(KEY, JSON.stringify(st)); } catch (e) { /* private mode */ } };
  const L = () => (['fr', 'es'].includes(LANG) ? LANG : 'en');
  const reduced = () => matchMedia('(prefers-reduced-motion: reduce)').matches;
  const shown = (e) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== 'hidden'; };
  // selectors are tried in the order given (first one that is visible wins), not in document order
  const vis = (sel) => { for (const one of sel.split(',')) { const e = [...document.querySelectorAll(one.trim())].find(shown); if (e) return e; } return null; };
  const busy = () => !!document.querySelector('.evp.open, #tkSlide.open, .nt-modal, .g-sweep, .wr, .gd-tour, #gOnb, .g-onb');
  const ic = (p) => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">${p}</svg>`;
  const I = {
    help: ic('<circle cx="12" cy="12" r="9"/><path d="M9.6 9.3a2.5 2.5 0 0 1 4.8.9c0 1.7-2.4 2.2-2.4 3.6M12 17h.01"/>'),
    x: ic('<path d="M6 6l12 12M18 6L6 18"/>'), check: ic('<path d="M5 12.5l4.2 4.2L19 7"/>'), arrow: ic('<path d="M9 6l6 6-6 6"/>'), back: ic('<path d="M15 6l-6 6 6 6"/>'),
    search: ic('<circle cx="11" cy="11" r="6.5"/><path d="M20 20l-4.2-4.2"/>'), bulb: ic('<path d="M9 18h6M10 21h4M12 3a6 6 0 0 0-3.6 10.8c.7.6 1.1 1.4 1.1 2.2h5c0-.8.4-1.6 1.1-2.2A6 6 0 0 0 12 3z"/>'),
    play: ic('<path d="M8 5.5v13l10.5-6.5z"/>'),
  };

  /* ───────────── strings ───────────── */
  const T = {
    fr: { help: 'Guide et aide', search: 'Rechercher dans le guide…', none: 'Aucun article ne correspond.', back: 'Guide', doit: 'Le faire maintenant', next: 'Suivant', prev: 'Retour', skip: 'Passer', done: 'C’est parti',
      tip: 'Astuce', readmore: 'Lire le guide', gotit: 'Compris', start_t: 'Bien démarrer', start_s: '{d} sur {n} étapes', start_done: 'Tu maîtrises les bases. Bravo !', hide: 'Masquer', how: 'Comment ?',
      replay: 'Revoir la visite guidée', retips: 'Réafficher les astuces des pages', open: 'Ouvrir le guide', tips_back: 'Les astuces réapparaîtront sur chaque page.', guide_sec: 'Guide et aide',
      guide_d: 'Tout ce qu’il faut savoir pour tirer le maximum de Sweep.', contact: 'Une question sans réponse ? Écris-nous à hello@makeitsweep.com ou via la page Feedback.',
      cats: { start: 'Pour commencer', daily: 'Ta routine quotidienne', progress: 'Progression et jeu', social: 'Social', prop: 'Comptes prop et payouts', tools: 'Outils', data: 'Données et réglages' } },
    en: { help: 'Guide & help', search: 'Search the guide…', none: 'No article matches.', back: 'Guide', doit: 'Do it now', next: 'Next', prev: 'Back', skip: 'Skip', done: 'Let’s go',
      tip: 'Tip', readmore: 'Read the guide', gotit: 'Got it', start_t: 'Get started', start_s: '{d} of {n} steps', start_done: 'You know the basics. Well done!', hide: 'Hide', how: 'How?',
      replay: 'Replay the guided tour', retips: 'Show page tips again', open: 'Open the guide', tips_back: 'Tips will show again on each page.', guide_sec: 'Guide & help',
      guide_d: 'Everything you need to get the most out of Sweep.', contact: 'Question not answered? Write to hello@makeitsweep.com or use the Feedback page.',
      cats: { start: 'Getting started', daily: 'Your daily routine', progress: 'Progress and game', social: 'Social', prop: 'Prop accounts and payouts', tools: 'Tools', data: 'Data and settings' } },
    es: { help: 'Guía y ayuda', search: 'Buscar en la guía…', none: 'Ningún artículo coincide.', back: 'Guía', doit: 'Hacerlo ahora', next: 'Siguiente', prev: 'Atrás', skip: 'Saltar', done: 'Vamos',
      tip: 'Consejo', readmore: 'Leer la guía', gotit: 'Entendido', start_t: 'Primeros pasos', start_s: '{d} de {n} pasos', start_done: 'Ya dominas lo básico. ¡Bravo!', hide: 'Ocultar', how: '¿Cómo?',
      replay: 'Ver de nuevo la visita guiada', retips: 'Mostrar de nuevo los consejos', open: 'Abrir la guía', tips_back: 'Los consejos volverán a aparecer en cada página.', guide_sec: 'Guía y ayuda',
      guide_d: 'Todo lo que necesitas para sacar el máximo de Sweep.', contact: '¿Pregunta sin respuesta? Escríbenos a hello@makeitsweep.com o usa la página Feedback.',
      cats: { start: 'Para empezar', daily: 'Tu rutina diaria', progress: 'Progreso y juego', social: 'Social', prop: 'Cuentas prop y payouts', tools: 'Herramientas', data: 'Datos y ajustes' } },
  };
  const t = (k, p) => { let s = k.split('.').reduce((a, x) => (a == null ? a : a[x]), T[L()]); if (s == null) s = k.split('.').reduce((a, x) => (a == null ? a : a[x]), T.en); if (typeof s === 'string' && p) s = s.replace(/\{(\w+)\}/g, (m, x) => (p[x] != null ? p[x] : m)); return s; };
  const pick = (o) => (o ? o[L()] || o.en : '');

  /* ───────────── actions ───────────── */
  const go = (h) => () => { closeHelp(); location.hash = h; };
  const ACT = {
    add: () => { closeHelp(); if (typeof openTicket === 'function') openTicket(); },
    plan: () => { closeHelp(); if (window.SweepGame) SweepGame.openPlan(); },
    review: () => { closeHelp(); if (window.SweepGame) SweepGame.openReview(); },
    accounts: go('#accounts'), analytics: go('#analytics'), calendar: go('#calendar'), journal: go('#journal'), payouts: go('#payouts'), news: go('#news'), settings: go('#settings'), feedback: go('#feedback'), referral: go('#referral'),
    ask: () => { closeHelp(); if (typeof askToggle === 'function') { try { askToggle(true); return; } catch (e) { /* fallback */ } } const b = vis('.ask-fab, [class*="ask-fab"]'); if (b) b.click(); },
  };

  /* ───────────── articles ───────────── */
  // body: paragraphs; lines starting with "• " become a list
  const A = [
    { id: 'whatsnew', cat: 'start', title: { fr: 'Nouveautés d’octobre 2026', en: 'What’s new, October 2026', es: 'Novedades de octubre de 2026' }, act: 'add', actl: { fr: 'Ajouter un trade', en: 'Add a trade', es: 'Añadir operación' },
      body: { fr: ['• Ajouter un trade : la capture d’écran d’abord (colle, dépose ou choisis-la), avec « Saisir à la main » et « Importer un CSV » juste en dessous. Plusieurs captures d’un coup = plusieurs trades.', '• Lignes de trade : touche pour ouvrir. Sur téléphone, glisse à gauche pour Supprimer, ou glisse loin pour supprimer d’un coup ; « Annuler » pendant 5 s.', '• Ta routine du jour : se plie et se déplie ; chaque étape faite ferme son anneau.', '• Partage : « Journée réussie » et « Ma discipline », sans montants, avec ton nom.', '• Comptes : glisse-dépose (ordinateur) ou « Modifier l’ordre » (téléphone) ; « Ajouter un compte » en haut ; compte « déjà en cours » avec son solde et son plus haut solde ; frais de la firme ajoutés à tes dépenses quand le prix est connu.', '• Payouts et dépenses : « + Ajouter un payout » et « + Ajouter une dépense » en haut de leur liste.', '• Tire vers le bas pour actualiser (téléphone). Ajoute Sweep à ton écran d’accueil pour l’ouvrir comme une app.'],
        en: ['• Add a trade: the screenshot first (paste, drop or choose it), with « Enter by hand » and « Import CSV » right under it. Several screenshots at once = several trades.', '• Trade rows: tap to open. On phone, swipe left for Delete, or swipe far to delete at once; « Undo » for 5 s.', '• Your routine today: opens and closes; each step done closes its ring.', '• Sharing: « Day swept » and « My discipline », no amounts, with your name.', '• Accounts: drag and drop (computer) or « Reorder » (phone); « Add account » on top; an account « already running » with its balance and highest balance; the firm’s fees added to your expenses when the price is known.', '• Payouts and expenses: « + Add payout » and « + Add expense » on top of their list.', '• Pull down to refresh (phone). Add Sweep to your home screen to open it like an app.'],
        es: ['• Añadir una operación: primero la captura (pégala, suéltala o elígela), con « Introducir a mano » e « Importar CSV » justo debajo. Varias capturas a la vez = varias operaciones.', '• Filas de operaciones: toca para abrir. En el teléfono, desliza a la izquierda para Eliminar, o desliza lejos para eliminar de una vez; « Deshacer » durante 5 s.', '• Tu rutina de hoy: se abre y se cierra; cada paso hecho cierra su anillo.', '• Compartir: « Día completado » y « Mi disciplina », sin montos, con tu nombre.', '• Cuentas: arrastrar y soltar (ordenador) o « Cambiar el orden » (teléfono); « Añadir cuenta » arriba; una cuenta « ya en curso » con su saldo y su saldo más alto; las comisiones de la firma en tus gastos cuando se conoce el precio.', '• Payouts y gastos: « + Añadir un payout » y « + Añadir un gasto » arriba de su lista.', '• Desliza hacia abajo para actualizar (teléfono). Añade Sweep a tu pantalla de inicio para abrirlo como una app.'] } },
    { id: 'import', cat: 'start', title: { fr: 'Importer tes trades depuis ta plateforme', en: 'Import your trades from your platform', es: 'Importar tus operaciones desde tu plataforma' },
      body: {
        fr: ['Importer une journée complète prend moins d’une minute : exporte tes exécutions de ta plateforme en fichier CSV, puis dépose-le dans Sweep (Trades → Importer).', '• Tradovate et les plateformes qui l’utilisent : onglet Reports → Orders (ou Performance), choisis la journée, puis Download / Export CSV.', '• TopstepX / ProjectX : onglet Trades, choisis la période, puis Export (CSV).', '• Rithmic (R|Trader Pro) : fenêtre Order History, choisis la date, puis Export.', '• Autre plateforme : n’importe quel export CSV de tes exécutions ou de tes trades fonctionne ; Sweep reconnaît les colonnes. Les noms de menus peuvent changer selon la version.', 'Après l’import, Sweep regroupe les exécutions en trades, calcule ton P&L avec les frais et te propose de journaliser chaque trade. Tes trades déjà présents ne sont pas dupliqués.'],
        en: ['Importing a full day takes less than a minute: export your executions from your platform as a CSV file, then drop it into Sweep (Trades → Import).', '• Tradovate and the platforms built on it: Reports tab → Orders (or Performance), pick the day, then Download / Export CSV.', '• TopstepX / ProjectX: Trades tab, pick the period, then Export (CSV).', '• Rithmic (R|Trader Pro): Order History window, pick the date, then Export.', '• Another platform: any CSV export of your executions or trades works; Sweep recognizes the columns. Menu names can change between versions.', 'After the import, Sweep groups executions into trades, computes your P&L with fees and offers to journal each trade. Trades already in Sweep are not duplicated.'],
        es: ['Importar una jornada completa toma menos de un minuto: exporta tus ejecuciones de tu plataforma en CSV y suéltalo en Sweep (Operaciones → Importar).', '• Tradovate y las plataformas basadas en ella: pestaña Reports → Orders (o Performance), elige el día y luego Download / Export CSV.', '• TopstepX / ProjectX: pestaña Trades, elige el periodo y luego Export (CSV).', '• Rithmic (R|Trader Pro): ventana Order History, elige la fecha y luego Export.', '• Otra plataforma: cualquier exportación CSV de tus ejecuciones u operaciones funciona; Sweep reconoce las columnas. Los nombres de menú pueden variar.', 'Tras importar, Sweep agrupa las ejecuciones en operaciones, calcula tu P&L con comisiones y te propone registrar cada operación. Las operaciones ya presentes no se duplican.'] } },
    { id: 'start', cat: 'start', title: { fr: 'Bien démarrer en 5 minutes', en: 'Get started in 5 minutes', es: 'Empieza en 5 minutos' }, act: 'add', actl: { fr: 'Ajouter un trade', en: 'Add a trade', es: 'Añadir una operación' },
      body: { fr: ['Sweep t’aide à devenir un trader régulier : on récompense le processus, jamais le profit. Voici le chemin le plus rapide :', '• Ajoute ton compte (prop firm ou personnel). Un préréglage remplit ses règles.', '• Avant l’ouverture, fais ton plan du jour (2 minutes).', '• Ajoute tes trades en touchant le graphique, puis réponds à la checklist de discipline.', '• Après la séance, fais ta revue du jour (60 secondes).', '• Les 3 anneaux se ferment : ta journée est balayée et ton streak avance.', 'La checklist « Bien démarrer » sur Aujourd’hui te guide étape par étape.'],
        en: ['Sweep helps you become a consistent trader: we reward the process, never the profit. The fastest path:', '• Add your account (prop firm or personal). A preset fills its rules.', '• Before the open, make your plan of the day (2 minutes).', '• Add your trades by tapping the chart, then answer the discipline checklist.', '• After the session, do your daily review (60 seconds).', '• The 3 rings close: your day is swept and your streak moves on.', 'The « Get started » checklist on Today walks you through each step.'],
        es: ['Sweep te ayuda a ser un trader constante: premiamos el proceso, nunca la ganancia. El camino más rápido:', '• Añade tu cuenta (prop firm o personal). Un preajuste completa sus reglas.', '• Antes de la apertura, haz tu plan del día (2 minutos).', '• Añade tus operaciones tocando el gráfico y responde la checklist de disciplina.', '• Después de la sesión, haz tu revisión del día (60 segundos).', '• Los 3 anillos se cierran: tu día queda barrido y tu racha avanza.', 'La checklist « Primeros pasos » de Hoy te guía paso a paso.'] } },
    { id: 'rings', cat: 'daily', title: { fr: 'Les 3 anneaux et « balayer ta journée »', en: 'The 3 rings and sweeping your day', es: 'Los 3 anillos y barrer tu día' }, act: 'plan', actl: { fr: 'Faire mon plan', en: 'Make my plan', es: 'Hacer mi plan' },
      body: { fr: ['Chaque jour de marché a trois étapes, ta routine du jour :', '• Plan : ton plan du jour (biais et perte max ; les setups sont facultatifs).', '• Respecter ton plan : tes trades du jour, ou un jour sans trade si c’était ton plan.', '• Revue : ta revue faite après la séance.', 'Faire une étape ferme son anneau. Les trois faits = journée réussie : ta série continue et ton XP tombe.', 'Comment tu l’as fait (plan fait après ton premier trade, trade hors de ton plan) reste visible dans chaque étape : c’est ton score de discipline qui le reflète, pas tes anneaux.', 'Sur ordinateur et téléphone, touche « Ta routine du jour » pour ouvrir ou fermer les trois étapes ; ta discipline, ta série et ton niveau restent visibles.'],
        en: ['Each market day has three steps, your routine of the day:', '• Plan: your plan of the day (bias and max loss; setups are optional).', '• Trade your plan: your trades of the day, or a day without trades if that was your plan.', '• Review: your review after the session.', 'Doing a step closes its ring. All three = day swept: your streak goes on and your XP lands.', 'How you did it (a plan made after your first trade, a trade outside your plan) stays visible in each step: your discipline score reflects it, not your rings.', 'On computer and phone, tap « Your routine today » to open or close the three steps; your discipline, streak and level stay in view.'],
        es: ['Cada día de mercado tiene tres pasos, tu rutina del día:', '• Plan: tu plan del día (sesgo y pérdida máx.; los setups son opcionales).', '• Respetar tu plan: tus operaciones del día, o un día sin operar si ese era tu plan.', '• Revisión: tu revisión después de la sesión.', 'Hacer un paso cierra su anillo. Los tres = día completado: tu racha sigue y tu XP llega.', 'Cómo lo hiciste (plan hecho después de tu primera operación, operación fuera de tu plan) queda visible en cada paso: lo refleja tu puntuación de disciplina, no tus anillos.', 'En ordenador y teléfono, toca « Tu rutina de hoy » para abrir o cerrar los tres pasos; tu disciplina, racha y nivel siguen visibles.'] } },
    { id: 'add', cat: 'daily', title: { fr: 'Ajouter un trade avec le graphique', en: 'Add a trade with the chart', es: 'Añadir una operación con el gráfico' }, act: 'add', actl: { fr: 'Ajouter un trade', en: 'Add a trade', es: 'Añadir operación' },
      body: { fr: ['Touche le bouton + (ou la touche N sur ordinateur), puis choisis l’instrument et la date : le graphique de la séance apparaît.', '• Touche la bougie d’entrée : le prix et l’heure se remplissent, puis la pastille passe à Sortie, Stop, Objectif.', '• « Aimanter » colle le prix au haut, bas, ouverture ou clôture de la bougie.', '• Glisse les lignes de stop et d’objectif du doigt.', '• Tu peux aussi taper les prix : les lignes bougent toutes seules.', 'Pas envie de tout saisir ? Log with AI : décris ton trade en mots ou envoie une capture.', 'Les graphiques sont disponibles 24 h après la séance : pour un trade d’aujourd’hui, saisis les prix, le graphique s’ajoutera demain.'],
        en: ['Tap + (or press N on a computer), then pick the instrument and date: the session chart appears.', '• Tap the entry candle: price and time fill in, then the pill moves to Exit, Stop, Target.', '• « Snap » sticks the price to the candle’s high, low, open or close.', '• Drag the stop and target lines with your finger.', '• You can also type prices: the lines move on their own.', 'Don’t want to type everything? Log with AI: describe your trade in words or send a screenshot.', 'Charts are ready 24 h after the session: for a trade from today, type the prices and the chart joins tomorrow.'],
        es: ['Toca + (o pulsa N en el ordenador) y elige el instrumento y la fecha: aparece el gráfico de la sesión.', '• Toca la vela de entrada: precio y hora se completan, luego pasa a Salida, Stop, Objetivo.', '• « Imantar » pega el precio al máximo, mínimo, apertura o cierre.', '• Arrastra las líneas de stop y objetivo con el dedo.', 'Los gráficos están disponibles 24 h después de la sesión.'] } },
    { id: 'checklist', cat: 'daily', title: { fr: 'La checklist de discipline', en: 'The discipline checklist', es: 'La checklist de disciplina' }, act: 'settings', actl: { fr: 'Modifier ma checklist', en: 'Edit my checklist', es: 'Editar mi checklist' },
      body: { fr: ['Après chaque trade, réponds Oui, Non ou N/A à tes questions : plan respecté, risque, stop, taille, perte max du jour.', 'C’est elle qui ferme l’anneau Exécution et nourrit tes analyses (trades dans le plan contre hors plan).', 'Choisis tes questions et leur libellé d’infraction dans Réglages.'],
        en: ['After each trade, answer Yes, No or N/A to your questions: plan followed, risk, stop, size, daily max loss.', 'It closes the Execution ring and feeds your analytics (in-plan versus off-plan trades).', 'Choose your questions and their violation label in Settings.'],
        es: ['Después de cada operación, responde Sí, No o N/A a tus preguntas: plan, riesgo, stop, tamaño, pérdida máxima.', 'Cierra el anillo de Ejecución y alimenta tus análisis.'] } },
    { id: 'plan', cat: 'daily', title: { fr: 'Le plan du jour', en: 'The plan of the day', es: 'El plan del día' }, act: 'plan', actl: { fr: 'Faire mon plan', en: 'Make my plan', es: 'Hacer mi plan' },
      body: { fr: ['Avant tes trades : ton biais, ta perte max du jour, et si tu veux ton nombre de trades max, tes niveaux clés et tes setups (facultatifs).', 'Un trade compte « dans ton plan » s’il va dans le sens de ton biais, utilise un de tes setups (si tu en as choisi), arrive avant ta perte max et ton nombre max, et que tu n’as pas répondu « non » à ta checklist.', 'L’heure où tu enregistres ton plan est gardée : fais-le avant ton premier trade pour qu’il compte à l’heure.', 'Le garde-fou t’avertit si tu dépasses ta perte max.'],
        en: ['Before your trades: your bias, your max loss for the day, and if you like your max number of trades, key levels and setups (optional).', 'A trade counts « in your plan » when it goes the way of your bias, uses one of your setups (if you chose some), comes before your max loss and max number of trades, and you did not answer « no » to your checklist.', 'The time you save your plan is kept: make it before your first trade so it counts as on time.', 'The guardrail warns you if you go past your max loss.'],
        es: ['Antes de operar: tu sesgo, tu pérdida máx. del día y, si quieres, tu número máx. de operaciones, niveles clave y setups (opcionales).', 'Una operación cuenta « en tu plan » si va en el sentido de tu sesgo, usa uno de tus setups (si elegiste), llega antes de tu pérdida máx. y tu número máx., y no respondiste « no » a tu checklist.', 'Se guarda la hora en que guardas tu plan: hazlo antes de tu primera operación para que cuente a tiempo.', 'El aviso te alerta si pasas tu pérdida máx.'] } },
    { id: 'review', cat: 'daily', title: { fr: 'La revue du jour', en: 'The daily review', es: 'La revisión del día' }, act: 'review', actl: { fr: 'Faire ma revue', en: 'Do my review', es: 'Hacer mi revisión' },
      body: { fr: ['Après la séance : note ta journée, ce qui a marché, ce qui a coincé, ta leçon et ton focus pour demain.', 'La revue ferme le 3e anneau. Une journée sans trade se revoit aussi : c’est souvent la meilleure décision.'],
        en: ['After the session: grade your day, what worked, what didn’t, your lesson and tomorrow’s focus.', 'The review closes the 3rd ring. A day without trades can be reviewed too: it is often the best decision.'],
        es: ['Después de la sesión: califica tu día, lo que funcionó, lo que no, tu lección y tu foco de mañana.', 'La revisión cierra el 3.er anillo.'] } },
    { id: 'streak', cat: 'progress', title: { fr: 'Streak et gels', en: 'Streak and freezes', es: 'Racha y congeladores' },
      body: { fr: ['Ton streak compte les jours de marché valides d’affilée. Un jour est valide quand ton exécution est respectée et ta revue faite.', 'Un gel protège ton streak un jour manqué : 1 par semaine en Free, 2 en Pro, 3 en Elite. Tu peux aussi déclarer un jour de repos.', 'Streak perdu ? Une quête de retour te permet d’en récupérer la moitié.'],
        en: ['Your streak counts valid market days in a row. A day is valid when your execution is respected and your review is done.', 'A freeze protects your streak on a missed day: 1 per week on Free, 2 on Pro, 3 on Elite. You can also declare a day off.', 'Lost your streak? A comeback quest gives half of it back.'],
        es: ['Tu racha cuenta los días de mercado válidos seguidos.', 'Un congelador protege tu racha un día perdido: 1 por semana en Gratis, 2 en Pro, 3 en Elite.'] } },
    { id: 'xp', cat: 'progress', title: { fr: 'XP, niveaux, rangs et badges', en: 'XP, levels, ranks and badges', es: 'XP, niveles, rangos e insignias' }, act: 'settings', actl: { fr: 'Voir mes badges', en: 'See my badges', es: 'Ver mis insignias' },
      body: { fr: ['Chaque bonne habitude rapporte de l’XP : plan, journal, revue, journée balayée, missions.', 'L’XP fait monter ton niveau et ton rang : Recrue, Apprenti, Discipliné, Constant, Aguerri, Maître, Sweeper.', 'Plus de 35 badges, dont des secrets. Ils sont dans Réglages, et chaque déblocage est partageable.'],
        en: ['Every good habit earns XP: plan, journal, review, swept day, missions.', 'XP raises your level and rank: Rookie, Apprentice, Disciplined, Consistent, Seasoned, Master, Sweeper.', 'Over 35 badges, some secret. They live in Settings, and every unlock can be shared.'],
        es: ['Cada buen hábito da XP: plan, diario, revisión, día barrido, misiones.', 'El XP sube tu nivel y tu rango.'] } },
    { id: 'map', cat: 'progress', title: { fr: 'Le parcours en chapitres', en: 'The chapter journey', es: 'El recorrido por capítulos' },
      body: { fr: ['Cinq chapitres te mènent de tes premiers pas jusqu’au payout. Chaque étape se valide toute seule quand tu la réalises.', 'Ouvre Progression pour voir ta prochaine étape.'],
        en: ['Five chapters take you from your first steps to payout. Each step completes on its own when you do it.', 'Open Progression to see your next step.'],
        es: ['Cinco capítulos te llevan de tus primeros pasos al payout.'] } },
    { id: 'missions', cat: 'progress', title: { fr: 'Missions, coffre et bilan de la semaine', en: 'Missions, chest and weekly recap', es: 'Misiones, cofre y resumen semanal' },
      body: { fr: ['Chaque lundi, 3 missions choisies selon tes points faibles. Les trois terminées : une clé de coffre.', 'Du vendredi 17 h au dimanche : ton bilan de la semaine, ton Edge Reveal (une vérité tirée de tes propres trades), 3 questions et ton coffre.', 'Le coffre contient de l’XP et parfois des gels, des thèmes d’anneaux ou des jours de Pro. Les probabilités sont affichées.'],
        en: ['Every Monday, 3 missions picked from your weak spots. All three done: a chest key.', 'From Friday 5 pm to Sunday: your weekly recap, your Edge Reveal (a truth from your own trades), 3 questions and your chest.', 'The chest holds XP and sometimes freezes, ring themes or Pro days. Odds are shown.'],
        es: ['Cada lunes, 3 misiones según tus puntos débiles. Las tres completas: una llave de cofre.', 'Del viernes 17 h al domingo: tu resumen semanal, tu Edge Reveal y tu cofre.'] } },
    { id: 'boss', cat: 'progress', title: { fr: 'Les boss', en: 'Bosses', es: 'Los jefes' },
      body: { fr: ['Sweep repère une mauvaise habitude dans tes 20 derniers jours (revenge, FOMO à l’ouverture, oversize, stop déplacé…) et la transforme en boss de 10 points de vie.', 'Chaque journée propre lui retire 1 point. Une rechute lui en rend 1, sans jamais te coûter d’XP ni ton streak.', 'Bats-le : 500 XP et un badge épique.'],
        en: ['Sweep spots a bad habit in your last 20 days (revenge, opening FOMO, oversize, moved stop…) and turns it into a 10-HP boss.', 'Each clean day takes 1 HP. A relapse gives 1 back, never costing XP or your streak.', 'Beat it: 500 XP and an epic badge.'],
        es: ['Sweep detecta un mal hábito en tus últimos 20 días y lo convierte en un jefe de 10 puntos de vida.', 'Cada día limpio le quita 1 punto.'] } },
    { id: 'season', cat: 'progress', title: { fr: 'Saisons et Wrapped', en: 'Seasons and Wrapped', es: 'Temporadas y Wrapped' },
      body: { fr: ['Chaque mois est une saison avec 30 paliers : ton XP du mois te fait avancer. Réclame tes récompenses en touchant les cases prêtes.', 'Le 1er du mois, ton Wrapped raconte ton mois en story. Un Wrapped annuel arrive en décembre.'],
        en: ['Each month is a season with 30 tiers: your XP of the month moves you up. Claim rewards by tapping the ready cells.', 'On the 1st, your Wrapped tells your month as a story. A yearly Wrapped arrives in December.'],
        es: ['Cada mes es una temporada con 30 niveles. El día 1, tu Wrapped cuenta tu mes.'] } },
    { id: 'social', cat: 'social', title: { fr: 'Ligues, crews et buddy', en: 'Leagues, crews and buddy', es: 'Ligas, crews y buddy' }, act: 'settings', actl: { fr: 'Choisir mon pseudo', en: 'Pick my handle', es: 'Elegir mi alias' },
      body: { fr: ['Tout est optionnel. Choisis d’abord un pseudo public dans Réglages → Social.', '• Ligues : classement hebdomadaire par XP de discipline, de Bronze à Diamant.', '• Crews : 3 à 5 traders, un objectif commun de journées balayées.', '• Buddy : un partenaire qui voit tes anneaux et ton streak.', 'Personne ne voit jamais tes trades, ton P&L ou tes comptes.'],
        en: ['Everything is optional. First pick a public handle in Settings → Social.', '• Leagues: weekly ranking by discipline XP, Bronze to Diamond.', '• Crews: 3 to 5 traders, a shared goal of swept days.', '• Buddy: a partner who sees your rings and streak.', 'Nobody ever sees your trades, P&L or accounts.'],
        es: ['Todo es opcional. Primero elige un alias en Ajustes → Social.', 'Nadie ve nunca tus operaciones, tu P&L ni tus cuentas.'] } },
    { id: 'accounts', cat: 'prop', title: { fr: 'Comptes prop, règles et payout', en: 'Prop accounts, rules and payout', es: 'Cuentas prop, reglas y payout' }, act: 'accounts', actl: { fr: 'Voir mes comptes', en: 'See my accounts', es: 'Ver mis cuentas' },
      body: { fr: ['Ajoute chaque compte avec un préréglage (Topstep, Apex, Take Profit Trader, Lucid, MyFundedFutures) : objectif, drawdown, perte quotidienne, consistance et jours minimum se remplissent. Vérifie-les toujours sur le site de ta firme.', 'Un trade peut être copié sur plusieurs comptes en une fois.', 'Le compteur « prêt pour le payout » te montre où tu en es. Note tes payouts et tes dépenses pour voir ton vrai bilan.'],
        en: ['Add each account with a preset (Topstep, Apex, Take Profit Trader, Lucid, MyFundedFutures): target, drawdown, daily loss, consistency and minimum days fill in. Always check them on your firm’s site.', 'A trade can be copied to several accounts at once.', 'The « ready for payout » meter shows where you stand. Log payouts and expenses to see your real result.'],
        es: ['Añade cada cuenta con un preajuste: objetivo, drawdown, pérdida diaria, consistencia y días mínimos. Verifícalos siempre en el sitio de tu firma.'] } },
    { id: 'ai', cat: 'tools', title: { fr: 'Sweep AI', en: 'Sweep AI', es: 'Sweep AI' }, act: 'ask', actl: { fr: 'Poser une question', en: 'Ask a question', es: 'Hacer una pregunta' },
      body: { fr: ['Ask Sweep répond à tes questions sur tes propres données : « quel est mon meilleur setup ? », « pourquoi mes vendredis sont mauvais ? ».', '« Avis de l’IA » commente un trade. Log with AI remplit un trade à partir de mots ou d’une capture.', 'Sweep AI n’est jamais un conseil financier.'],
        en: ['Ask Sweep answers questions about your own data: « what is my best setup? », « why are my Fridays bad? ».', '« AI review » comments on a trade. Log with AI fills a trade from words or a screenshot.', 'Sweep AI is never financial advice.'],
        es: ['Ask Sweep responde sobre tus propios datos. Sweep AI nunca es un consejo financiero.'] } },
    { id: 'analytics', cat: 'tools', title: { fr: 'Stats et calendrier', en: 'Stats and calendar', es: 'Stats y calendario' }, act: 'analytics', actl: { fr: 'Ouvrir les stats', en: 'Open Stats', es: 'Abrir Stats' },
      body: { fr: ['Les analyses comparent tes trades par setup, heure, jour, émotion, et dans le plan contre hors plan. Change la période en haut.', 'Le calendrier montre chaque jour de marché, avec les nouvelles économiques. Touche un jour pour voir son journal.'],
        en: ['Analytics compare your trades by setup, hour, day, emotion, and in-plan versus off-plan. Change the period at the top.', 'The calendar shows every market day, with economic news. Tap a day to see its journal.'],
        es: ['Los análisis comparan tus operaciones por setup, hora, día y emoción.'] } },
    { id: 'notif', cat: 'data', title: { fr: 'Notifications et rappels', en: 'Notifications and reminders', es: 'Notificaciones y recordatorios' }, act: 'settings', actl: { fr: 'Régler mes notifications', en: 'Set my notifications', es: 'Ajustar notificaciones' },
      body: { fr: ['La cloche regroupe tes rappels et tes célébrations : plan à 8 h 45, revue à 16 h 30, streak à sauver à 21 h, bilan de la semaine le vendredi.', 'Jamais pendant les heures de marché, 2 rappels par jour au maximum. Chaque catégorie se désactive dans Réglages.'],
        en: ['The bell gathers reminders and celebrations: plan at 8:45, review at 4:30 pm, streak to save at 9 pm, weekly recap on Friday.', 'Never during market hours, 2 reminders a day at most. Each category can be turned off in Settings.'],
        es: ['La campana reúne recordatorios y celebraciones. Nunca durante el horario de mercado.'] } },
    { id: 'data', cat: 'data', title: { fr: 'Tes données', en: 'Your data', es: 'Tus datos' }, act: 'settings', actl: { fr: 'Exporter mes données', en: 'Export my data', es: 'Exportar mis datos' },
      body: { fr: ['Tout est privé par défaut. « Tout exporter (ZIP) » dans Réglages te donne une sauvegarde réimportable, des tableurs et tes captures.', 'Tu peux supprimer ton compte et toutes tes données en tout temps.', 'Une idée, un bug ? La page Feedback : tu suivras son statut jusqu’à « Tu l’as demandé, on l’a construit ».'],
        en: ['Everything is private by default. « Export everything (ZIP) » in Settings gives you a re-importable backup, spreadsheets and your screenshots.', 'You can delete your account and all your data at any time.', 'An idea, a bug? The Feedback page: you will follow its status up to « You asked, we built it ».'],
        es: ['Todo es privado por defecto. « Exportar todo (ZIP) » en Ajustes te da una copia, hojas de cálculo y tus capturas.'] } },
  ];
  const art = (id) => A.find((a) => a.id === id);

  /* ───────────── help center (own sheet, works everywhere) ───────────── */
  let helpEl = null;
  function closeHelp() { if (!helpEl) return; const el = helpEl; helpEl = null; el.classList.remove('open'); setTimeout(() => el.remove(), 280); document.body.classList.remove('gd-lock'); }
  function openHelp(id) {
    closeHelp();
    const el = document.createElement('div'); el.className = 'gd-help-ov'; el.setAttribute('data-noi18n', ''); el.setAttribute('role', 'dialog');
    el.innerHTML = `<div class="gd-bg" data-gd="close"></div><div class="gd-panel"><span class="gd-grab"></span><div class="gd-body"></div></div>`;
    document.body.append(el); helpEl = el; document.body.classList.add('gd-lock');
    requestAnimationFrame(() => el.classList.add('open'));
    id ? showArticle(id) : showIndex('');
  }
  function showIndex(q) {
    const b = helpEl && helpEl.querySelector('.gd-body'); if (!b) return;
    const ql = q.trim().toLowerCase();
    const match = (a) => !ql || (pick(a.title) + ' ' + pick(a.body).join(' ')).toLowerCase().includes(ql);
    const cats = Object.keys(T.en.cats);
    const list = cats.map((c) => { const items = A.filter((a) => a.cat === c && match(a)); return items.length ? `<h4>${t('cats.' + c)}</h4><div class="gd-list">${items.map((a) => `<button type="button" class="gd-item" data-gd="art" data-v="${a.id}"><span>${esc(pick(a.title))}</span>${I.arrow}</button>`).join('')}</div>` : ''; }).join('');
    b.innerHTML = `<div class="gd-head"><h2>${t('help')}</h2><button type="button" class="gd-x" data-gd="close" aria-label="Close">${I.x}</button></div>
      <p class="gd-lead">${t('guide_d')}</p>
      <label class="gd-search">${I.search}<input type="search" data-gd-q value="${esc(q)}" placeholder="${t('search')}" autocomplete="off"></label>
      ${list || `<p class="muted">${t('none')}</p>`}<p class="gd-contact">${t('contact')}</p>`;
    const inp = b.querySelector('[data-gd-q]'); if (q) { inp.focus(); inp.setSelectionRange(q.length, q.length); }
  }
  function showArticle(id) {
    const a = art(id), b = helpEl && helpEl.querySelector('.gd-body'); if (!a || !b) return;
    let html = '', inList = false;
    for (const p of pick(a.body)) {
      if (p.startsWith('• ')) { if (!inList) { html += '<ul>'; inList = true; } html += `<li>${esc(p.slice(2))}</li>`; }
      else { if (inList) { html += '</ul>'; inList = false; } html += `<p>${esc(p)}</p>`; }
    }
    if (inList) html += '</ul>';
    b.innerHTML = `<div class="gd-head"><button type="button" class="gd-backbtn" data-gd="index">${I.back}<span>${t('back')}</span></button><button type="button" class="gd-x" data-gd="close" aria-label="Close">${I.x}</button></div>
      <article class="gd-art"><span class="gd-kick">${t('cats.' + a.cat)}</span><h2>${esc(pick(a.title))}</h2>${html}</article>
      ${a.act ? `<button type="button" class="btn primary gd-do" data-gd="act" data-v="${a.act}">${esc(pick(a.actl) || t('doit'))}</button>` : ''}`;
    b.scrollTop = 0;
  }

  const seenAnim = new Set();   // what already played its entrance during this visit

  /* ───────────── « Get started » checklist on Today ───────────── */
  let prof = null, profAt = 0, profP = null;
  async function counters() {
    if (prof && Date.now() - profAt < 60000) return prof;
    if (profP) return profP;   // already asked: two paints at the same moment share one request
    profP = (async () => {
      try { const r = await apiJSON('api/game/profile'); prof = (r && (r.counters || (r.profile && r.profile.counters))) || {}; profAt = Date.now(); } catch (e) { prof = prof || {}; }
      profP = null; return prof;
    })();
    return profP;
  }
  const real = (a) => (a || []).filter((x) => !x.demo);
  async function steps() {
    const c = await counters();
    const tr = real(S.trades), jr = real(S.journals);
    const filled = (o) => o && Object.values(o).some((v) => v != null && String(v).trim() !== '' && v !== false);
    return [   // three steps, the core loop: a trade, a review, a swept day (the account exists already)
      { id: 'trade', ok: tr.length > 0, t: { fr: 'Ajouter ton premier trade (graphique ou en mots)', en: 'Log your first trade (chart or words)', es: 'Registrar tu primera operación (gráfico o palabras)' }, act: 'add', a: 'add' },
      /* (« Do your daily review » merged into « Complete your first day »: the review is what closes the day) */
      { id: 'swept', ok: (c.swept || 0) > 0, t: { fr: 'Réussir ta première journée : Plan, Exécution, Revue', en: 'Complete your first day: Plan, Execution, Review', es: 'Completar tu primer día: Plan, Ejecución, Revisión' }, act: 'plan', a: 'rings' },
    ];
  }
  async function paintStart() {
    if (route().v !== 'dashboard' || st.hideStart || !real(S.accounts).length) return;   // before the first account, the app's own setup card leads
    const main = document.getElementById('main'); if (!main) return;
    const s = await steps(), done = s.filter((x) => x.ok).length;
    if (done === s.length) { if (!st.startCelebrated) { st.startCelebrated = true; st.hideStart = true; save(); if (typeof toast === 'function') toast(t('start_done')); } const old = main.querySelector('.gd-start'); if (old) old.remove(); return; }
    let el = main.querySelector('.gd-start');
    const html = `<div class="gd-st-h"><div><b>${t('start_t')}</b><small>${t('start_s', { d: done, n: s.length })}</small></div><button type="button" class="gd-x sm" data-gd="st-hide" aria-label="${t('hide')}">${I.x}</button></div>
      <span class="gd-bar"><i style="width:${(done / s.length) * 100}%"></i></span>
      <ol class="gd-steps">${s.map((x) => `<li class="${x.ok ? 'ok' : ''}"><span class="gd-ck">${x.ok ? I.check : ''}</span><span class="gd-st-t">${esc(pick(x.t))}</span>
        ${x.ok ? '' : `<span class="gd-st-a">${x.act ? `<button type="button" class="btn sm primary" data-gd="act" data-v="${x.act}">${t('doit')}</button>` : ''}<button type="button" class="link" data-gd="art" data-v="${x.a}">${t('how')}</button></span>`}</li>`).join('')}</ol>`;
    if (!el) {
      el = document.createElement('section'); el.className = 'surface gd-start' + (seenAnim.has('start') ? ' gd-still' : ''); el.setAttribute('data-noi18n', '');
      seenAnim.add('start');
      // at the top of the routine card when there is one (same place as nav.js A4, so the card is placed once and never jumps)
      const rt = main.querySelector('.nav-rt:not(.ph)'), rh = rt && rt.querySelector('.nav-rt-h');
      const dayCard = main.querySelector('.nav-dash .d-today'), today = main.querySelector('.g-today');
      if (rh) { rh.after(el); el.classList.add('nav-start-in'); } else if (dayCard) dayCard.after(el); else if (today) today.after(el); else main.prepend(el);
    }
    else if (!el.closest('.nav-rt')) { const dayCard = main.querySelector('.nav-dash .d-today'); if (dayCard && el.previousElementSibling !== dayCard) dayCard.after(el); }   // inside the routine card it stays where it is (no back-and-forth)
    if (el._h !== html) { el.innerHTML = html; el._h = html; }
  }

  /* ───────────── header « ? » and Settings section ───────────── */
  function paintChrome() {
    // help lives in the avatar menu and in search (no extra header button)
    document.querySelectorAll('.gd-hbtn').forEach((b) => b.remove());
    // help is in the avatar menu and in search: no extra section in Settings

  }

  /* ───────────── events ───────────── */
  document.addEventListener('click', (e) => {
    const b = e.target.closest && e.target.closest('[data-gd]'); if (!b) return;
    const a = b.dataset.gd, v = b.dataset.v;
    if (a === 'open') openHelp();
    else if (a === 'close') closeHelp();
    else if (a === 'index') showIndex('');
    else if (a === 'art') { if (!helpEl) openHelp(v); else showArticle(v); }
    else if (a === 'act' && ACT[v]) ACT[v]();
    else if (a === 'st-hide') { st.hideStart = true; save(); const el = b.closest('.gd-start'); if (el) el.remove(); }
  });
  document.addEventListener('input', (e) => { if (e.target.matches && e.target.matches('[data-gd-q]')) showIndex(e.target.value); });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && helpEl) closeHelp(); });
  addEventListener('resize', () => { try { paintChrome(); } catch (e) { /* layout */ } });

  const appRender = render;
  render = function () {
    const out = appRender.apply(this, arguments);
    try {
      const v = route().v;
      if (v === 'analytics' && !st.visited.analytics) { st.visited.analytics = true; save(); }
      paintChrome(); paintStart();
    } catch (e) { /* guidance never blocks the app */ }
    return out;
  };
  // after the first load, Overview shortcuts no longer replay their entrance on each re-render
  setTimeout(() => document.body.classList.add('gc-settled'), 1800);
  window.SweepGuide = { open: openHelp, article: openHelp };
  setTimeout(() => { try { paintChrome(); paintStart(); } catch (e) { /* first paint */ } }, 1200);
})();
