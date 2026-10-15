/*
 * Sweep — « Your coach » (brief 03 step 2): one voice that speaks right after each action, from the rules that already
 * exist (no AI: instant, free, every plan). Short, firm and kind: a number when there is one, and one thing to do.
 *  · The plan: one sentence, live at the bottom of the plan sheet while it is filled in.
 *  · Each trade: what was right, the one thing to improve with its fix, where the session stands. On the trade's page,
 *    in the « saved » message, and on Today (the coach card under the routine, in place of « Get started » and the
 *    rings tip).
 * The rules mirror the server's (game/game.php, recomputeDay: no_stop, plan_no_trade, against_bias, setup_not_in_plan,
 * over_max_loss, over_max_trades, the checklist), plus the trade's automatic flags (app.js detectFlags) and two habits
 * read from the day's trades: a re-entry less than 10 minutes after a loss, the size raised after 2 wins in a row.
 * Nothing is saved and nothing is blocked: the trader always decides.
 */
(function () {
  'use strict';
  if (typeof S === 'undefined' || typeof render !== 'function') return;
  const L = (typeof LANG !== 'undefined' && ['fr', 'es'].includes(LANG)) ? LANG : 'en';
  const T = {
    en: {
      askT: 'Answer your coach', askN: '{k} of {n}', aPlan: 'Was this trade in your plan?', aStop: 'Did you respect your stop?', aSize: 'Did you respect your max size?',
      aWhy: 'What pushed you to enter?', aEmo: 'Your emotion before entering?', aLesson: 'Your lesson, in one sentence', aLessonPh: 'What you do again, or what you change.', yes: 'Yes', no: 'No', fullT: 'Full review · {x} of 4',
      wkT: 'Your week', stT: 'What works for you', stSub: 'Your last 4 weeks · {n} trades', strong: 'Your strength', leak: 'Your leak', rule: 'Your rule', ruleW: 'Your rule for next week',
      sPlan: 'In your plan: {a} % winning trades over {n} (off plan: {b} % over {m}).', sSetup: 'Your best setup: “{s}”, {a} % winning trades over {n}.',
      sSlot: 'Your best time: {s}, {a} % winning trades over {n}.', sClean: '{k} of {n} sessions without a mistake.',
      sNone: 'Not enough trades yet to tell what works: 5 in the same situation are needed.',
      lk: '{w}: {k} of {n} trades{c}.', lk1: '{w}: 1 of {n} trades{c}.', lkNone: 'No leak: not one mistake over {n} trades.',
      prT: 'Your progress', prLine: '{w} weeks ago: {a} % · {l}: {b} %', prNow: 'this week', prLast: 'last week', prAgo: '{w} weeks ago', prHelp: '% of trades without this mistake, week by week',
      slot: (h, m, h2, m2) => `${h}:${m}–${h2}:${m2}`,
      lim: { dll75: '{a}: {p} % of your daily limit used ({u} of {l}). Keep your size, or stop.', dll100: '{a}: daily limit reached ({l}). Your session is over on this account.',
        dd75: '{a}: {p} % of the drawdown used, {r} of room left. Trade smaller.', dd100: '{a}: drawdown limit reached. Check the account’s status with your firm.' },
      bTitle: 'Before this trade',
      bMax: 'Max loss reached ({m}): your session is over. This trade will be out of your plan.',
      bDone: 'Your {m} planned trades are done: this one will be out of your plan.',
      bWait: 'Your last loss was {n} min ago: wait {r} more min before entering.',
      bLoss2: '{n} losses in a row: take a 15-minute break before this trade.',
      bSize: '{n} contracts: your maximum is {m}.',
      bUp: 'After {w} wins in a row, keep your size ({c}).',
      bOpen: 'The first 5 minutes of the open: wait for your setup.',
      bNoPlan: 'No plan for this session: take 30 seconds before this trade.',
      bLeft: 'you have {m} left before your max loss', bLeftAcc: 'you have {m} left before the daily limit of {a}', bCount: 'trade {n} of {m}',
      o: { revenge: 'Your trades taken less than 10 min after a loss: {a} on average over {n} (the others: {b}).',
        loss2d: 'After 2 losses in a row, your average loss doubles: {b} → {a}.', loss2m: 'After 2 losses in a row, your average loss goes from {b} to {a}.',
        size_up: 'When you raise the size after wins: {a} on average over {n} trades.', open5: 'Your trades in the first 5 minutes: {a} on average over {n}.' },
      why: { over_max_loss: 'Why: the worst days come from the trades taken to win back a loss.', over_max_trades: 'Why: past your number, you trade fatigue, not setups.', revenge: 'Why: right after a loss, emotion picks the trade, not your plan.', addloser: 'Why: adding to a loser turns a small loss into the one that ends the account.', no_stop: 'Why: without a stop, one trade can take the whole account.', risklimit: 'Why: an account is lost a little too much risk at a time.', oversized: 'Why: a bigger size makes every tick heavier, and decisions worse.', size_up: 'Why: after wins you feel sure; the market has not changed.', against_bias: 'Why: your bias was decided calm, before the open: trust it.', setup_not_in_plan: 'Why: only a setup you repeat can be measured and improved.', open5: 'Why: the first minutes are the wildest, and your entries there are your worst.', plan_no_trade: 'Why: you decided calm not to trade; the urge came later.', no_plan: 'Why: the plan is your decision made calm, before the market pushes you.', rules_no: 'Why: the checklist is your filter against impulsive entries.', rules_partial: 'Why: the checklist is your filter against impulsive entries.' },
      pNoMaxNew: 'To start, 2 trades max: fewer trades, more discipline.', ai: 'Go further with Sweep AI',
      habit: 'This week: {h}, {k} of {n} {w}.', habit0: 'This week: {h}.', today: 'today', yday: 'yesterday', on: 'on {d}',
      h: { over_max_loss: 'stop at your max loss', over_max_trades: 'no more trades than planned', revenge: 'a 10-minute break after a loss', addloser: 'never add to a loser', no_stop: 'a stop on every trade', risklimit: 'the risk within your limit', oversized: 'stay at your size', size_up: 'the same size after wins', against_bias: 'trade with your bias', setup_not_in_plan: 'only your plan’s setups', open5: 'no trade before 9:35', plan_no_trade: 'a planned day off stays one', no_plan: 'your plan before your first trade', rules_no: 'your checklist before each entry', rules_partial: 'your checklist before each entry' },
      dayT: 'Your day', ruleT: 'Rule for tomorrow', ruleD: 'Rule of the day', rulePh: 'Suggested: {r}',
      lClean1: 'Your trade was in your plan. That is exactly the discipline.', lClean: '{n} trades, all in your plan. That is exactly the discipline.',
      lMix: '{k} of {n} trades without a mistake. What cost you the most: {w}{c}.', lOff: 'No trade today: your plan held.',
      w: { revenge: 'going back in less than 10 minutes after a loss', over_max_loss: 'trading after your max loss', over_max_trades: 'going past your number of trades', addloser: 'adding to a loser', no_stop: 'the stop not respected', risklimit: 'a risk above your limit', oversized: 'a size above your maximum', size_up: 'raising the size after wins', against_bias: 'trading against your bias', setup_not_in_plan: 'a setup outside your plan', open5: 'entering in the first 5 minutes', plan_no_trade: 'trading on a planned day off', no_plan: 'trading without a plan', rules_no: 'your checklist', rules_partial: 'your checklist' },
      r: { over_max_loss: 'Max loss reached: I close the platform.', over_max_trades: '{m} trades max, not one more.', revenge: 'After a loss: a 10-minute break before the next trade.', addloser: 'Never add to a losing trade.', no_stop: 'A stop set before each entry, never moved.', risklimit: 'Each trade’s risk fits my limit.', oversized: 'Never more than {m} contracts.', size_up: 'The same size after wins.', against_bias: 'Only in the direction of my bias.', setup_not_in_plan: 'Only the setups of my plan.', open5: 'No trade before 9:35.', plan_no_trade: 'A planned day off stays a day off.', no_plan: 'My plan before my first trade.', rules_no: 'Every point of my checklist before I enter.', rules_partial: 'Every point of my checklist before I enter.', clean: 'Same plan, same discipline.' },
      title: 'Your coach', last: 'Last trade · {t}', thisT: 'This trade', fix: 'To improve',
      inPlan: 'In your plan', stopOk: 'stop respected', sizeOk: 'size within your max', chkOk: 'checklist followed',
      none: 'Nothing to fix on this trade. Do exactly the same again.',
      f: {
        over_max_loss: ['Taken after your max loss of the day ({m}).', 'Once the max loss is hit, you close the platform.'],
        over_max_trades: ['Trade {n} for {m} planned.', 'Once your max is reached, the session is over.'],
        revenge: ['Taken {n} min after a loss.', 'After a loss, wait 10 minutes and reread your plan before going back in.'],
        addloser: ['You added to a losing position.', 'Your stop decides, not hope: never add to a loser.'],
        no_stop: ['Stop not respected.', 'Set your stop before you enter, and don’t move it.'],
        risklimit: ['Risk above your limit.', 'Cut the size so your stop fits your risk.'],
        oversized: ['{n} contracts, your maximum is {m}.', 'Stay at your size, even when you feel sure.'],
        size_up: ['Size raised to {n} after {w} wins in a row.', 'After wins, keep the same size: that is where overconfidence costs.'],
        against_bias: ['Against your bias ({b}).', 'If the market goes against your bias, wait or pass: no trade against your plan.'],
        setup_not_in_plan: ['Setup “{s}” is not in your plan.', 'Take only your plan’s setups; add this one tomorrow if it earns it.'],
        open5: ['Taken in the first 5 minutes of the open.', 'Let the open pass: wait for your setup after 9:35.'],
        plan_no_trade: ['You had planned not to trade.', 'A planned day off is a rule too.'],
        no_plan: ['No plan for this session.', 'Make your plan before the next trade: 30 seconds.'],
        rules_no: ['Your checklist was not followed.', 'Reread your checklist before each entry.'],
        rules_partial: ['Checklist partly followed.', 'Take the next entry only if every point is ticked.'],
      },
      bias: { bullish: 'bullish', bearish: 'bearish' },
      maxHit: 'Max loss reached ({m}): your session is over for today.',
      loss2: '{n} losses in a row: take a 15-minute break before the next trade.',
      done: '{n} of {m} planned trades: your session is done.',
      left: 'You have {m} left before your max loss.',
      leftAcc: 'You have {m} left before the daily limit of {a}.',
      count: 'Trade {n} of {m} planned.',
      pOff: 'No trading today: that is a trader’s decision, not a failure.',
      pAbove: 'Max loss {m}: above the daily limit of {a} ({l}).',
      pNoSetup: 'No setup chosen: I won’t be able to tell you if you follow your plan.',
      pNoMax: 'Set a max number of trades: that is what stops overtrading.',
      pOk: 'Clear plan: max loss {m}, {n} trades max. At the limit, you stop.',
      pNeed: 'Pick your bias and your max loss: that is your rule for the day.',
      planT: 'Your plan', noPlan: 'Before your session: your plan. Then I tell you, trade by trade, if you follow it.',
      first: 'After your first trade, I tell you what was right and the one thing to improve.',
    },
    fr: {
      askT: 'Réponds au coach', askN: '{k} sur {n}', aPlan: 'Ce trade était-il dans ton plan ?', aStop: 'As-tu respecté ton stop ?', aSize: 'As-tu respecté ta taille max ?',
      aWhy: 'Qu’est-ce qui t’a poussé à entrer ?', aEmo: 'Ton émotion avant d’entrer ?', aLesson: 'Ta leçon, en une phrase', aLessonPh: 'Ce que tu refais, ou ce que tu changes.', yes: 'Oui', no: 'Non', fullT: 'Revue complète · {x} sur 4',
      wkT: 'Ta semaine', stT: 'Ce qui fonctionne pour toi', stSub: 'Tes 4 dernières semaines · {n} trades', strong: 'Ta force', leak: 'Ta fuite', rule: 'Ta règle', ruleW: 'Ta règle pour la semaine prochaine',
      sPlan: 'Dans ton plan : {a} % de trades gagnants sur {n} (hors plan : {b} % sur {m}).', sSetup: 'Ton meilleur setup : « {s} », {a} % de trades gagnants sur {n}.',
      sSlot: 'Ton meilleur moment : {s}, {a} % de trades gagnants sur {n}.', sClean: '{k} séances sur {n} sans erreur.',
      sNone: 'Pas encore assez de trades pour dire ce qui fonctionne : il en faut 5 dans une même situation.',
      lk: '{w} : {k} trades sur {n}{c}.', lk1: '{w} : 1 trade sur {n}{c}.', lkNone: 'Aucune fuite : pas une erreur sur {n} trades.',
      prT: 'Ta progression', prLine: 'Il y a {w} semaines : {a} % · {l} : {b} %', prNow: 'cette semaine', prLast: 'la semaine dernière', prAgo: 'il y a {w} semaines', prHelp: '% des trades sans cette erreur, semaine par semaine',
      slot: (h, m, h2, m2) => `${+h} h ${m}–${+h2} h ${m2}`.replace(/ h 00/g, ' h'),
      lim: { dll75: '{a} : {p} % de ta limite du jour utilisés ({u} sur {l}). Garde ta taille, ou arrête-toi.', dll100: '{a} : limite du jour atteinte ({l}). Ta séance est finie sur ce compte.',
        dd75: '{a} : {p} % du drawdown utilisés, il te reste {r} de marge. Trade plus petit.', dd100: '{a} : limite de drawdown atteinte. Vérifie le statut du compte auprès de ta firme.' },
      bTitle: 'Avant ce trade',
      bMax: 'Perte max atteinte ({m}) : ta séance est finie. Ce trade sera hors plan.',
      bDone: 'Tes {m} trades prévus sont faits : celui-ci sera hors plan.',
      bWait: 'Ta dernière perte date de {n} min : attends encore {r} min avant d’entrer.',
      bLoss2: '{n} pertes de suite : fais une pause de 15 minutes avant ce trade.',
      bSize: '{n} contrats : ton maximum est {m}.',
      bUp: 'Après {w} gains de suite, garde ta taille ({c}).',
      bOpen: 'Les 5 premières minutes de l’ouverture : attends ton setup.',
      bNoPlan: 'Pas de plan pour cette séance : prends 30 secondes avant ce trade.',
      bLeft: 'il te reste {m} avant ta perte max', bLeftAcc: 'il te reste {m} avant la limite du jour de {a}', bCount: 'trade {n} sur {m}',
      o: { revenge: 'Tes trades pris moins de 10 min après une perte : {a} en moyenne sur {n} (les autres : {b}).',
        loss2d: 'Après 2 pertes de suite, ta perte moyenne double : {b} → {a}.', loss2m: 'Après 2 pertes de suite, ta perte moyenne passe de {b} à {a}.',
        size_up: 'Quand tu montes la taille après des gains : {a} en moyenne sur {n} trades.', open5: 'Tes trades des 5 premières minutes : {a} en moyenne sur {n}.' },
      why: { over_max_loss: 'Pourquoi : les pires journées viennent des trades pris pour se refaire.', over_max_trades: 'Pourquoi : au-delà de ton nombre, tu trades la fatigue, pas des setups.', revenge: 'Pourquoi : juste après une perte, c’est l’émotion qui choisit le trade, pas ton plan.', addloser: 'Pourquoi : ajouter à un perdant transforme une petite perte en celle qui ferme le compte.', no_stop: 'Pourquoi : sans stop, un seul trade peut emporter tout le compte.', risklimit: 'Pourquoi : un compte se perd un peu trop de risque à la fois.', oversized: 'Pourquoi : une taille plus grosse rend chaque tick plus lourd, et tes décisions moins bonnes.', size_up: 'Pourquoi : après des gains, tu te sens sûr de toi ; le marché, lui, n’a pas changé.', against_bias: 'Pourquoi : ton biais a été décidé à froid, avant l’ouverture : fais-lui confiance.', setup_not_in_plan: 'Pourquoi : seul un setup que tu répètes peut être mesuré et amélioré.', open5: 'Pourquoi : les premières minutes sont les plus agitées, et tes entrées y sont les moins bonnes.', plan_no_trade: 'Pourquoi : tu as décidé à froid de ne pas trader ; l’envie est venue après.', no_plan: 'Pourquoi : le plan, c’est ta décision prise à froid, avant que le marché te pousse.', rules_no: 'Pourquoi : la checklist est ton filtre contre les entrées impulsives.', rules_partial: 'Pourquoi : la checklist est ton filtre contre les entrées impulsives.' },
      pNoMaxNew: 'Pour commencer, 2 trades max : moins de trades, plus de discipline.', ai: 'Aller plus loin avec Sweep AI',
      habit: 'Cette semaine : {h}, {k} sur {n} {w}.', habit0: 'Cette semaine : {h}.', today: 'aujourd’hui', yday: 'hier', on: '{d}',
      h: { over_max_loss: 't’arrêter à ta perte max', over_max_trades: 'pas plus de trades que prévu', revenge: '10 minutes de pause après une perte', addloser: 'jamais d’ajout à un perdant', no_stop: 'un stop sur chaque trade', risklimit: 'le risque dans ta limite', oversized: 'rester à ta taille', size_up: 'la même taille après des gains', against_bias: 'trader dans le sens de ton biais', setup_not_in_plan: 'seulement les setups de ton plan', open5: 'pas de trade avant 9 h 35', plan_no_trade: 'respecter un jour sans trading', no_plan: 'ton plan avant ton premier trade', rules_no: 'ta checklist avant chaque entrée', rules_partial: 'ta checklist avant chaque entrée' },
      dayT: 'Ta journée', ruleT: 'Règle de demain', ruleD: 'Règle du jour', rulePh: 'Proposée : {r}',
      lClean1: 'Ton trade était dans ton plan. C’est exactement ça, la discipline.', lClean: '{n} trades, tous dans ton plan. C’est exactement ça, la discipline.',
      lMix: '{k} trades sur {n} sans erreur. Ce qui t’a coûté le plus : {w}{c}.', lOff: 'Pas de trade aujourd’hui : ton plan a tenu.',
      w: { revenge: 'revenir moins de 10 minutes après une perte', over_max_loss: 'trader après ta perte max', over_max_trades: 'dépasser ton nombre de trades', addloser: 'ajouter à un perdant', no_stop: 'le stop non respecté', risklimit: 'un risque au-dessus de ta limite', oversized: 'une taille au-dessus de ton maximum', size_up: 'monter la taille après des gains', against_bias: 'trader contre ton biais', setup_not_in_plan: 'un setup hors de ton plan', open5: 'entrer dans les 5 premières minutes', plan_no_trade: 'trader un jour prévu sans trading', no_plan: 'trader sans plan', rules_no: 'ta checklist', rules_partial: 'ta checklist' },
      r: { over_max_loss: 'Perte max atteinte : je ferme la plateforme.', over_max_trades: '{m} trades max, pas un de plus.', revenge: 'Après une perte : 10 minutes de pause avant le trade suivant.', addloser: 'Jamais d’ajout à un trade perdant.', no_stop: 'Un stop placé avant chaque entrée, jamais déplacé.', risklimit: 'Le risque de chaque trade tient dans ma limite.', oversized: 'Jamais plus de {m} contrats.', size_up: 'La même taille après des gains.', against_bias: 'Seulement dans le sens de mon biais.', setup_not_in_plan: 'Seulement les setups de mon plan.', open5: 'Pas de trade avant 9 h 35.', plan_no_trade: 'Un jour prévu sans trading reste sans trading.', no_plan: 'Mon plan avant mon premier trade.', rules_no: 'Chaque point de ma checklist avant d’entrer.', rules_partial: 'Chaque point de ma checklist avant d’entrer.', clean: 'Même plan, même discipline.' },
      title: 'Ton coach', last: 'Dernier trade · {t}', thisT: 'Ce trade', fix: 'À améliorer',
      inPlan: 'Dans ton plan', stopOk: 'stop respecté', sizeOk: 'taille respectée', chkOk: 'checklist suivie',
      none: 'Rien à corriger sur ce trade. Refais exactement pareil.',
      f: {
        over_max_loss: ['Pris après ta perte max du jour ({m}).', 'Ta perte max atteinte, tu fermes la plateforme.'],
        over_max_trades: ['{n}ᵉ trade pour {m} prévus.', 'Ton nombre max atteint, la séance est finie.'],
        revenge: ['Pris {n} min après une perte.', 'Après une perte, attends 10 minutes et relis ton plan avant de revenir.'],
        addloser: ['Tu as ajouté à une position perdante.', 'Ton stop décide, pas l’espoir : on n’ajoute jamais à un perdant.'],
        no_stop: ['Stop non respecté.', 'Place ton stop avant d’entrer et ne le bouge pas.'],
        risklimit: ['Risque au-dessus de ta limite.', 'Réduis la taille pour que ton stop tienne dans ton risque.'],
        oversized: ['{n} contrats, ton maximum est {m}.', 'Reste à ta taille, même quand tu es sûr de toi.'],
        size_up: ['Taille montée à {n} après {w} gains de suite.', 'Après des gains, garde la même taille : c’est là que l’excès de confiance coûte.'],
        against_bias: ['À l’inverse de ton biais ({b}).', 'Si le marché contredit ton biais, tu attends ou tu passes : pas de trade contre ton plan.'],
        setup_not_in_plan: ['Setup « {s} » hors de ton plan.', 'Ne prends que les setups de ton plan ; ajoute celui-ci demain s’il le mérite.'],
        open5: ['Pris dans les 5 premières minutes de l’ouverture.', 'Laisse passer l’ouverture : attends ton setup après 9 h 35.'],
        plan_no_trade: ['Tu avais prévu de ne pas trader.', 'Un jour sans trading prévu se respecte comme une règle.'],
        no_plan: ['Pas de plan pour cette séance.', 'Fais ton plan avant le prochain trade : 30 secondes.'],
        rules_no: ['Ta checklist n’est pas respectée.', 'Relis ta checklist avant chaque entrée.'],
        rules_partial: ['Checklist suivie en partie.', 'Prends la prochaine entrée seulement si chaque point est coché.'],
      },
      bias: { bullish: 'haussier', bearish: 'baissier' },
      maxHit: 'Perte max atteinte ({m}) : ta séance est finie pour aujourd’hui.',
      loss2: '{n}ᵉ perte de suite : fais une pause de 15 minutes avant le prochain trade.',
      done: '{n} trades sur {m} prévus : ta séance est faite.',
      left: 'Il te reste {m} avant ta perte max.',
      leftAcc: 'Il te reste {m} avant la limite du jour de {a}.',
      count: 'Trade {n} sur {m} prévus.',
      pOff: 'Pas de trading aujourd’hui : c’est une décision de trader, pas un échec.',
      pAbove: 'Perte max {m} : au-dessus de la limite du jour de {a} ({l}).',
      pNoSetup: 'Pas de setup choisi : je ne pourrai pas te dire si tu respectes ton plan.',
      pNoMax: 'Fixe un nombre max de trades : c’est ce qui coupe l’overtrading.',
      pOk: 'Plan clair : perte max {m}, {n} trades max. À la limite, tu t’arrêtes.',
      pNeed: 'Choisis ton biais et ta perte max : c’est ta règle du jour.',
      planT: 'Ton plan', noPlan: 'Avant ta séance : ton plan. Ensuite, je te dis trade par trade si tu le respectes.',
      first: 'Après ton premier trade, je te dis ce qui était bien et la seule chose à améliorer.',
    },
    es: {
      askT: 'Responde a tu coach', askN: '{k} de {n}', aPlan: '¿Esta operación estaba en tu plan?', aStop: '¿Respetaste tu stop?', aSize: '¿Respetaste tu tamaño máximo?',
      aWhy: '¿Qué te empujó a entrar?', aEmo: '¿Tu emoción antes de entrar?', aLesson: 'Tu lección, en una frase', aLessonPh: 'Lo que repites, o lo que cambias.', yes: 'Sí', no: 'No', fullT: 'Revisión completa · {x} de 4',
      wkT: 'Tu semana', stT: 'Lo que funciona para ti', stSub: 'Tus últimas 4 semanas · {n} operaciones', strong: 'Tu fortaleza', leak: 'Tu fuga', rule: 'Tu regla', ruleW: 'Tu regla para la próxima semana',
      sPlan: 'Dentro de tu plan: {a} % de operaciones ganadoras en {n} (fuera del plan: {b} % en {m}).', sSetup: 'Tu mejor setup: « {s} », {a} % de operaciones ganadoras en {n}.',
      sSlot: 'Tu mejor momento: {s}, {a} % de operaciones ganadoras en {n}.', sClean: '{k} de {n} sesiones sin error.',
      sNone: 'Aún no hay suficientes operaciones para saber qué funciona: hacen falta 5 en una misma situación.',
      lk: '{w}: {k} de {n} operaciones{c}.', lk1: '{w}: 1 de {n} operaciones{c}.', lkNone: 'Ninguna fuga: ni un error en {n} operaciones.',
      prT: 'Tu progreso', prLine: 'Hace {w} semanas: {a} % · {l}: {b} %', prNow: 'esta semana', prLast: 'la semana pasada', prAgo: 'hace {w} semanas', prHelp: '% de operaciones sin este error, semana a semana',
      slot: (h, m, h2, m2) => `${h}:${m}–${h2}:${m2}`,
      lim: { dll75: '{a}: {p} % de tu límite diario usado ({u} de {l}). Mantén tu tamaño, o para.', dll100: '{a}: límite diario alcanzado ({l}). Tu sesión terminó en esta cuenta.',
        dd75: '{a}: {p} % del drawdown usado, te quedan {r} de margen. Opera más pequeño.', dd100: '{a}: límite de drawdown alcanzado. Verifica el estado de la cuenta con tu firma.' },
      bTitle: 'Antes de esta operación',
      bMax: 'Pérdida máxima alcanzada ({m}): tu sesión terminó. Esta operación quedará fuera de tu plan.',
      bDone: 'Tus {m} operaciones previstas están hechas: esta quedará fuera de tu plan.',
      bWait: 'Tu última pérdida fue hace {n} min: espera {r} min más antes de entrar.',
      bLoss2: '{n} pérdidas seguidas: haz una pausa de 15 minutos antes de esta operación.',
      bSize: '{n} contratos: tu máximo es {m}.',
      bUp: 'Tras {w} ganancias seguidas, mantén tu tamaño ({c}).',
      bOpen: 'Los 5 primeros minutos de la apertura: espera tu setup.',
      bNoPlan: 'Sin plan para esta sesión: tómate 30 segundos antes de esta operación.',
      bLeft: 'te quedan {m} antes de tu pérdida máxima', bLeftAcc: 'te quedan {m} antes del límite diario de {a}', bCount: 'operación {n} de {m}',
      o: { revenge: 'Tus operaciones tomadas menos de 10 min después de una pérdida: {a} de media en {n} (las demás: {b}).',
        loss2d: 'Tras 2 pérdidas seguidas, tu pérdida media se duplica: {b} → {a}.', loss2m: 'Tras 2 pérdidas seguidas, tu pérdida media pasa de {b} a {a}.',
        size_up: 'Cuando subes el tamaño tras ganancias: {a} de media en {n} operaciones.', open5: 'Tus operaciones de los 5 primeros minutos: {a} de media en {n}.' },
      why: { over_max_loss: 'Por qué: los peores días vienen de las operaciones para recuperar una pérdida.', over_max_trades: 'Por qué: pasado tu número, operas el cansancio, no setups.', revenge: 'Por qué: justo después de una pérdida, la emoción elige la operación, no tu plan.', addloser: 'Por qué: añadir a una perdedora convierte una pérdida pequeña en la que cierra la cuenta.', no_stop: 'Por qué: sin stop, una sola operación puede llevarse toda la cuenta.', risklimit: 'Por qué: una cuenta se pierde con un poco de riesgo de más cada vez.', oversized: 'Por qué: un tamaño mayor hace cada tick más pesado, y tus decisiones peores.', size_up: 'Por qué: tras ganancias te sientes seguro; el mercado no ha cambiado.', against_bias: 'Por qué: tu sesgo se decidió en frío, antes de la apertura: confía en él.', setup_not_in_plan: 'Por qué: solo un setup que repites puede medirse y mejorarse.', open5: 'Por qué: los primeros minutos son los más agitados, y tus entradas ahí son las peores.', plan_no_trade: 'Por qué: decidiste en frío no operar; las ganas vinieron después.', no_plan: 'Por qué: el plan es tu decisión en frío, antes de que el mercado te empuje.', rules_no: 'Por qué: la checklist es tu filtro contra las entradas impulsivas.', rules_partial: 'Por qué: la checklist es tu filtro contra las entradas impulsivas.' },
      pNoMaxNew: 'Para empezar, 2 operaciones máx.: menos operaciones, más disciplina.', ai: 'Ir más lejos con Sweep AI',
      habit: 'Esta semana: {h}, {k} de {n} {w}.', habit0: 'Esta semana: {h}.', today: 'hoy', yday: 'ayer', on: 'el {d}',
      h: { over_max_loss: 'parar en tu pérdida máxima', over_max_trades: 'no más operaciones de las previstas', revenge: '10 minutos de pausa tras una pérdida', addloser: 'nunca añadir a una perdedora', no_stop: 'un stop en cada operación', risklimit: 'el riesgo dentro de tu límite', oversized: 'mantener tu tamaño', size_up: 'el mismo tamaño tras ganancias', against_bias: 'operar en el sentido de tu sesgo', setup_not_in_plan: 'solo los setups de tu plan', open5: 'ninguna operación antes de las 9:35', plan_no_trade: 'respetar un día sin operar', no_plan: 'tu plan antes de tu primera operación', rules_no: 'tu checklist antes de cada entrada', rules_partial: 'tu checklist antes de cada entrada' },
      dayT: 'Tu día', ruleT: 'Regla para mañana', ruleD: 'Regla del día', rulePh: 'Propuesta: {r}',
      lClean1: 'Tu operación estaba dentro de tu plan. Eso es exactamente la disciplina.', lClean: '{n} operaciones, todas dentro de tu plan. Eso es exactamente la disciplina.',
      lMix: '{k} de {n} operaciones sin error. Lo que más te costó: {w}{c}.', lOff: 'Sin operaciones hoy: tu plan se mantuvo.',
      w: { revenge: 'volver menos de 10 minutos después de una pérdida', over_max_loss: 'operar después de tu pérdida máxima', over_max_trades: 'pasar tu número de operaciones', addloser: 'añadir a una perdedora', no_stop: 'el stop no respetado', risklimit: 'un riesgo por encima de tu límite', oversized: 'un tamaño por encima de tu máximo', size_up: 'subir el tamaño tras ganancias', against_bias: 'operar contra tu sesgo', setup_not_in_plan: 'un setup fuera de tu plan', open5: 'entrar en los 5 primeros minutos', plan_no_trade: 'operar un día previsto sin operar', no_plan: 'operar sin plan', rules_no: 'tu checklist', rules_partial: 'tu checklist' },
      r: { over_max_loss: 'Pérdida máxima alcanzada: cierro la plataforma.', over_max_trades: '{m} operaciones máx., ni una más.', revenge: 'Tras una pérdida: 10 minutos de pausa antes de la siguiente operación.', addloser: 'Nunca añadir a una operación perdedora.', no_stop: 'Un stop puesto antes de cada entrada, nunca movido.', risklimit: 'El riesgo de cada operación cabe en mi límite.', oversized: 'Nunca más de {m} contratos.', size_up: 'El mismo tamaño tras ganancias.', against_bias: 'Solo en el sentido de mi sesgo.', setup_not_in_plan: 'Solo los setups de mi plan.', open5: 'Ninguna operación antes de las 9:35.', plan_no_trade: 'Un día previsto sin operar sigue sin operar.', no_plan: 'Mi plan antes de mi primera operación.', rules_no: 'Cada punto de mi checklist antes de entrar.', rules_partial: 'Cada punto de mi checklist antes de entrar.', clean: 'Mismo plan, misma disciplina.' },
      title: 'Tu coach', last: 'Última operación · {t}', thisT: 'Esta operación', fix: 'A mejorar',
      inPlan: 'Dentro de tu plan', stopOk: 'stop respetado', sizeOk: 'tamaño respetado', chkOk: 'checklist cumplida',
      none: 'Nada que corregir en esta operación. Repite exactamente lo mismo.',
      f: {
        over_max_loss: ['Tomada después de tu pérdida máxima del día ({m}).', 'Alcanzada la pérdida máxima, cierras la plataforma.'],
        over_max_trades: ['Operación {n} para {m} previstas.', 'Alcanzado tu máximo, la sesión termina.'],
        revenge: ['Tomada {n} min después de una pérdida.', 'Tras una pérdida, espera 10 minutos y relee tu plan antes de volver.'],
        addloser: ['Añadiste a una posición perdedora.', 'Tu stop decide, no la esperanza: nunca añadas a una perdedora.'],
        no_stop: ['Stop no respetado.', 'Pon tu stop antes de entrar y no lo muevas.'],
        risklimit: ['Riesgo por encima de tu límite.', 'Reduce el tamaño para que tu stop quepa en tu riesgo.'],
        oversized: ['{n} contratos, tu máximo es {m}.', 'Mantén tu tamaño, incluso cuando estés seguro.'],
        size_up: ['Tamaño subido a {n} tras {w} ganancias seguidas.', 'Tras ganancias, mantén el mismo tamaño: ahí es donde cuesta el exceso de confianza.'],
        against_bias: ['Contra tu sesgo ({b}).', 'Si el mercado contradice tu sesgo, espera o pasa: nada contra tu plan.'],
        setup_not_in_plan: ['Setup « {s} » fuera de tu plan.', 'Toma solo los setups de tu plan; añade este mañana si lo merece.'],
        open5: ['Tomada en los 5 primeros minutos de la apertura.', 'Deja pasar la apertura: espera tu setup después de las 9:35.'],
        plan_no_trade: ['Habías previsto no operar.', 'Un día sin operar previsto es también una regla.'],
        no_plan: ['Sin plan para esta sesión.', 'Haz tu plan antes de la próxima operación: 30 segundos.'],
        rules_no: ['Tu checklist no se cumplió.', 'Relee tu checklist antes de cada entrada.'],
        rules_partial: ['Checklist cumplida en parte.', 'Toma la próxima entrada solo si cada punto está marcado.'],
      },
      bias: { bullish: 'alcista', bearish: 'bajista' },
      maxHit: 'Pérdida máxima alcanzada ({m}): tu sesión terminó por hoy.',
      loss2: '{n} pérdidas seguidas: haz una pausa de 15 minutos antes de la próxima operación.',
      done: '{n} de {m} operaciones previstas: tu sesión está hecha.',
      left: 'Te quedan {m} antes de tu pérdida máxima.',
      leftAcc: 'Te quedan {m} antes del límite diario de {a}.',
      count: 'Operación {n} de {m} previstas.',
      pOff: 'Sin operar hoy: es una decisión de trader, no un fracaso.',
      pAbove: 'Pérdida máx. {m}: por encima del límite diario de {a} ({l}).',
      pNoSetup: 'Ningún setup elegido: no podré decirte si respetas tu plan.',
      pNoMax: 'Fija un número máx. de operaciones: es lo que corta el overtrading.',
      pOk: 'Plan claro: pérdida máx. {m}, {n} operaciones máx. En el límite, paras.',
      pNeed: 'Elige tu sesgo y tu pérdida máx.: es tu regla del día.',
      planT: 'Tu plan', noPlan: 'Antes de tu sesión: tu plan. Luego te digo, operación por operación, si lo respetas.',
      first: 'Tras tu primera operación, te digo qué estuvo bien y la única cosa a mejorar.',
    },
  }[L];
  // (a percentage never leaves its number: « 89 % » with a narrow no-break space in fr / es, « 89% » in en)
  const fill = (s, v) => String(s).replace(/\{(\w+)\}/g, (_, k) => (v && v[k] != null ? v[k] : '')).replace(/ %/g, L === 'en' ? '%' : '\u202f%');
  const esc2 = (s) => String(s == null ? '' : s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
  const usd = (c) => (typeof money === 'function' ? money(Math.abs(c), { sign: false, dec: 0 }) : '$' + Math.round(Math.abs(c) / 100));
  const cents = (v) => { const n = parseFloat(String(v == null ? '' : v).replace(/[^0-9.]/g, '')); return isFinite(n) && n > 0 ? Math.round(n * 100) : 0; };
  const net = (t) => (typeof tNet === 'function' ? tNet(t) : (t.pnl_c || 0) - (t.fees_c || 0));
  const min = (hm) => { const m = /^(\d{1,2}):(\d{2})/.exec(hm || ''); return m ? +m[1] * 60 + +m[2] : null; };
  const timeOf = (t) => (typeof tradeTimeOf === 'function' ? tradeTimeOf(t) : t.entry_time) || t.entry_time || '';
  // the session the routine card shows (the game's day), so both cards speak of the same day
  const today = () => { const st = window.SweepGame && SweepGame.state && SweepGame.state(), d = st && st.today && st.today.day; return d || (typeof todayStr === 'function' ? todayStr() : new Date().toISOString().slice(0, 10)); };

  /** the session's trades, as the server counts them: real trades of the day, copies on other accounts counted once */
  function dayTrades(day) {
    const seen = new Set(), out = [];
    (S.trades || []).filter((t) => t.date === day && !t.demo).sort((a, b) => (timeOf(a) || '99:99').localeCompare(timeOf(b) || '99:99') || String(a.created_at || '').localeCompare(String(b.created_at || ''))).forEach((t) => {
      if (t.copy_group) { if (seen.has(t.copy_group)) return; seen.add(t.copy_group); }
      out.push(t);
    });
    return out;
  }
  function planOf(day) {
    const j = typeof getDoc === 'function' ? getDoc('journals', day) : null, pre = (j && j.pre) || {};
    const bias = ['bullish', 'bearish', 'neutral', 'no_trade'].includes(pre.bias) ? pre.bias : null, ml = cents(pre.max_loss);
    return { bias, maxLoss: ml, maxTrades: parseInt(pre.max_trades, 10) || 0, setups: (pre.setups || []).map((s) => String(s).trim().toLowerCase()).filter(Boolean), valid: !!bias && (bias === 'no_trade' || ml > 0) };
  }
  /** the tightest daily loss limit of the trader's active accounts (the same as the plan sheet's hint) */
  function accountLimit() {
    const a = (S.accounts || []).filter((x) => !x.demo && x.status !== 'archived' && x.status !== 'closed' && x.rules && x.rules.dll_c > 0).sort((x, y) => x.rules.dll_c - y.rules.dll_c)[0];
    return a ? { c: a.rules.dll_c, name: a.name || '' } : null;
  }
  const stopAnswer = (t) => { const d = t.discipline || {}; for (const k of ['stop', 'risk', 'defined_risk', 'stop_respected']) if (d[k] === 'y' || d[k] === 'n') return d[k]; return null; };
  function rulesOf(t) {   // the checklist, as the server reads it (rules_followed first, otherwise the « no » answers)
    if (['yes', 'partial', 'no'].includes(t.rules_followed)) return t.rules_followed;
    const v = Object.values(t.discipline || {}).filter((x) => x === 'y' || x === 'n'); if (!v.length) return null;
    const n = v.filter((x) => x === 'n').length; return n === 0 ? 'yes' : n * 2 < v.length ? 'partial' : 'no';
  }

  /** the trader's own numbers, from all his real trades (cached): how each situation goes for him */
  let oCache = { k: '', v: null };
  const avg = (a) => (a.length ? a.reduce((s, x) => s + x, 0) / a.length : 0);
  function own() {
    const k = (S.trades || []).length + '|' + (S.trades || []).reduce((m, t) => (t.updated_at > m ? t.updated_at : m), '');
    if (oCache.k === k) return oCache.v;
    const b = { all: [], revenge: [], loss2: [], up: [], open5: [] };
    [...new Set((S.trades || []).filter((t) => !t.demo).map((t) => t.date))].forEach((d) => {
      const list = dayTrades(d);
      list.forEach((t, i) => {
        const n = net(t), p = list[i - 1], q = list[i - 2]; b.all.push(n);
        if (p && net(p) < 0) { const a = min(p.exit_time || timeOf(p)), e = min(timeOf(t)); if (a != null && e != null && e >= a && e - a < 10) b.revenge.push(n); }
        if (p && q && net(p) < 0 && net(q) < 0) b.loss2.push(n);
        if (p && q && net(p) > 0 && net(q) > 0 && +t.contracts > +p.contracts) b.up.push(n);
        const e = min(timeOf(t)); if (e != null && e >= 570 && e < 575) b.open5.push(n);
      });
    });
    oCache = { k, v: b }; return b;
  }
  const sgn = (c) => (typeof money === 'function' ? money(Math.round(c), { dec: 0 }) : usd(c));
  /** one sentence with his own number for a situation, only when his sample says it costs him (else '') */
  function ownLine(kind) {
    const o = own(), all = o.all;
    if (kind === 'revenge' || kind === 'size_up' || kind === 'open5') {
      const s = o[kind === 'size_up' ? 'up' : kind], rest = all.length - s.length;
      if (s.length < (kind === 'size_up' ? 3 : 5) || !rest) return '';
      const a = avg(s), others = (all.reduce((x, y) => x + y, 0) - s.reduce((x, y) => x + y, 0)) / rest;
      if (a >= others) return '';
      return fill(T.o[kind], { a: sgn(a), n: s.length, b: sgn(others) });
    }
    if (kind === 'loss2') {
      const l2 = o.loss2.filter((x) => x < 0), la = all.filter((x) => x < 0);
      if (l2.length < 3 || la.length < 5) return '';
      const a = Math.abs(avg(l2)), b = Math.abs(avg(la)); if (!b || a / b < 1.15) return '';
      return fill(a / b >= 1.8 ? T.o.loss2d : T.o.loss2m, { a: usd(a), b: usd(b) });
    }
    return '';
  }

  /** what the coach says about one trade: { good: [labels], fix: [problem, advice, code, values] | null, all: [codes], ses: session(), n, time } */
  function tradeNote(t) {
    if (!t) return null;
    const day = t.date, list = dayTrades(day), key = t.copy_group || t.id;
    let i = list.findIndex((x) => (x.copy_group || x.id) === key); if (i < 0) { list.push(t); i = list.length - 1; }
    const p = planOf(day), flags = t.auto_flags || [];
    let before = 0; for (let k = 0; k < i; k++) before += net(list[k]);
    const prev = list[i - 1], issues = [];
    const add = (code, v) => issues.push([code, v || {}]);
    if (p.valid && p.maxLoss && before <= -p.maxLoss) add('over_max_loss', { m: usd(p.maxLoss) });
    if (p.valid && p.maxTrades && i >= p.maxTrades) add('over_max_trades', { n: i + 1, m: p.maxTrades });
    if (prev && net(prev) < 0) { const a = min(prev.exit_time || timeOf(prev)), b = min(timeOf(t)); if (a != null && b != null && b >= a && b - a < 10) add('revenge', { n: b - a }); }
    if (flags.includes('addloser')) add('addloser');
    if (stopAnswer(t) === 'n' || flags.includes('stop')) add('no_stop');
    if (flags.includes('risklimit')) add('risklimit');
    const maxC = +(S.settings && S.settings.max_contracts) || 0;
    if (flags.includes('oversized') && maxC) add('oversized', { n: t.contracts, m: maxC });
    if (prev && i >= 2 && net(prev) > 0 && net(list[i - 2]) > 0 && +t.contracts > +prev.contracts) { let w = 0; for (let k = i - 1; k >= 0 && net(list[k]) > 0; k--) w++; add('size_up', { n: t.contracts, w }); }
    if (p.valid && ((p.bias === 'bullish' && t.direction === 'short') || (p.bias === 'bearish' && t.direction === 'long'))) add('against_bias', { b: T.bias[p.bias] });
    if (p.valid && p.setups.length && t.setup && !p.setups.includes(String(t.setup).trim().toLowerCase())) add('setup_not_in_plan', { s: t.setup });
    { const e = min(timeOf(t)); if (e != null && e >= 570 && e < 575 && ownLine('open5')) add('open5'); }
    if (p.valid && p.bias === 'no_trade') add('plan_no_trade');
    if (!p.valid) add('no_plan');
    const r = rulesOf(t); if (r === 'no') add('rules_no'); else if (r === 'partial') add('rules_partial');
    // what was right (the plan, the stop, the size, the checklist), never more than two
    const planBad = issues.some(([c]) => ['over_max_loss', 'over_max_trades', 'against_bias', 'setup_not_in_plan', 'plan_no_trade', 'no_plan'].includes(c));
    const good = [];
    if (p.valid && !planBad) good.push(T.inPlan);
    if (!issues.some(([c]) => c === 'no_stop') && (stopAnswer(t) === 'y' || (t.stop != null && t.stop !== ''))) good.push(T.stopOk);
    if (maxC && +t.contracts && +t.contracts <= maxC && !issues.some(([c]) => ['oversized', 'size_up'].includes(c))) good.push(T.sizeOk);
    if (r === 'yes') good.push(T.chkOk);
    const fix = issues.length ? [fill(T.f[issues[0][0]][0], issues[0][1]), T.f[issues[0][0]][1], issues[0][0], issues[0][1]] : null;
    return { good: good.slice(0, 2), fix, all: issues.map(([c]) => c), ses: session(day, i, list, p), n: i + 1, time: timeOf(t) };
  }
  /** where the session stands right after the trade number i of the day (the last one when i is left out):
   *  { t: sentence, stop: true when the coach tells him to stop or pause } */
  function session(day, i, list, p) {
    list = list || dayTrades(day); p = p || planOf(day); if (i == null) i = list.length - 1; if (i < 0) return { t: '', stop: false };
    let after = 0; for (let k = 0; k <= i; k++) after += net(list[k]);
    const say = (t, stop, code) => ({ t, stop: !!stop, code: code || '' });
    if (p.valid && p.maxLoss && after <= -p.maxLoss) return say(fill(T.maxHit, { m: usd(p.maxLoss) }), true);
    if (p.valid && p.maxTrades && i + 1 >= p.maxTrades) return say(fill(T.done, { n: i + 1, m: p.maxTrades }), true);   // done: no « next trade » to pause before
    let losses = 0; for (let k = i; k >= 0 && net(list[k]) < 0; k--) losses++;
    if (losses >= 2) return say(fill(T.loss2, { n: losses }), true, 'loss2');
    if (p.valid && p.maxLoss) return say(fill(T.left, { m: usd(p.maxLoss + after) }));
    const lim = accountLimit(); if (lim && lim.c + after > 0) return say(fill(T.leftAcc, { m: usd(lim.c + after), a: lim.name }));
    if (p.valid && p.maxTrades) return say(fill(T.count, { n: i + 1, m: p.maxTrades }));
    return say('');
  }
  /** one sentence about a plan: { bias, maxLoss (cents), maxTrades, setups (count) } */
  function planNote(x) {
    if (!x.bias) return T.pNeed;
    if (x.bias === 'no_trade') return T.pOff;
    if (!x.maxLoss) return T.pNeed;
    const lim = accountLimit();
    if (lim && x.maxLoss > lim.c) return fill(T.pAbove, { m: usd(x.maxLoss), a: lim.name, l: usd(lim.c) });
    if (starting()) { if (!x.maxTrades) return T.pNoMaxNew; }   // starting out: simple goals (max loss, number of trades), no setups asked
    else { if (!x.setups) return T.pNoSetup; if (!x.maxTrades) return T.pNoMax; }
    return fill(T.pOk, { m: usd(x.maxLoss), n: x.maxTrades });
  }

  /** the lesson of a session: how many trades without a mistake, what cost the most, and the rule that answers it */
  function dayLesson(day) {
    const list = dayTrades(day); if (!list.length) return { text: T.lOff, rule: '', code: null, n: 0 };
    const notes = list.map(tradeNote), clean = notes.filter((c) => !c.fix).length;
    if (clean === list.length) return { text: list.length === 1 ? T.lClean1 : fill(T.lClean, { n: list.length }), rule: T.r.clean, code: 'clean', n: list.length };
    const by = {}; notes.forEach((c, k) => { if (!c.fix) return; const x = by[c.fix[2]] || (by[c.fix[2]] = { n: 0, c: 0 }); x.n++; x.c += net(list[k]); });
    const order = Object.keys(T.f);   // the coach's own order breaks a tie
    const [code, x] = Object.entries(by).sort((a, b) => b[1].n - a[1].n || a[1].c - b[1].c || order.indexOf(a[0]) - order.indexOf(b[0]))[0];
    const m = code === 'over_max_trades' ? planOf(day).maxTrades : +(S.settings && S.settings.max_contracts) || '';
    return { text: fill(T.lMix, { k: clean, n: list.length, w: T.w[code], c: x.c < 0 ? ` (${typeof money === 'function' ? money(x.c, { dec: 0 }) : usd(x.c)})` : '' }), rule: fill(T.r[code], { m }), code, n: list.length };
  }
  /** the rule a new plan starts with: what the last review (within a week) said for the next session, or the coach's */
  function ruleFor(day) {
    const wk = new Date(day + 'T12:00:00'); wk.setDate(wk.getDate() - 7); const from = wk.toISOString().slice(0, 10);
    const j = (S.journals || []).filter((x) => x.id < day && x.id >= from && !x.demo && x.post && x.post.reviewed_at).sort((a, b) => b.id.localeCompare(a.id))[0];
    if (!j) return '';
    const own = String(j.post.tomorrow || '').split('\n').map((x) => x.trim()).find(Boolean);
    return String(own || dayLesson(j.id).rule || '').slice(0, 160);
  }

  /** the habit of the week: the rule broken most often the week before (a new trader: this week's days before today),
   *  the same on every device (computed, never stored); then how the last session with trades went: { text } | null */
  const iso = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
  let hCache = { k: '', v: null };
  function habit(day) {
    const last = (a) => (a || []).reduce((m, x) => (x.updated_at > m ? x.updated_at : m), '');   // a trade or a plan changed: computed again
    const key = [day, (S.trades || []).length, last(S.trades), (S.journals || []).length, last(S.journals), JSON.stringify((S.settings || {}).max_contracts || '')].join('|');
    if (hCache.k === key) return hCache.v;
    hCache = { k: key, v: habitOf(day) }; return hCache.v;
  }
  function habitOf(day) {
    const d0 = new Date(day + 'T12:00:00'), mon = new Date(d0); mon.setDate(d0.getDate() - ((d0.getDay() + 6) % 7));
    const prevMon = new Date(mon); prevMon.setDate(mon.getDate() - 7);
    const days = (from, to) => [...new Set((S.trades || []).filter((t) => !t.demo && t.date >= from && t.date < to).map((t) => t.date))].sort();
    const count = (list) => { const by = {}; list.forEach((x) => dayTrades(x).forEach((t) => { const c = tradeNote(t); if (c.fix) by[c.fix[2]] = (by[c.fix[2]] || 0) + 1; })); return by; };
    let by = count(days(iso(prevMon), iso(mon)));
    if (!Object.keys(by).length) by = count(days(iso(mon), day));   // no week before: this week, the days before today
    const order = Object.keys(T.f), top = Object.entries(by).sort((a, b) => b[1] - a[1] || order.indexOf(a[0]) - order.indexOf(b[0]))[0];
    if (!top) return null;
    const code = top[0], same = (c) => c === code || (code.startsWith('rules_') && String(c).startsWith('rules_'));
    const last = days(iso(mon), iso(new Date(d0.getTime() + 86400000))).pop();   // this week's last session with trades (today included)
    if (!last) return { text: fill(T.habit0, { h: T.h[code] }) };
    const list = dayTrades(last), k = list.filter((t) => !tradeNote(t).all.some(same)).length;
    const yd = new Date(d0); yd.setDate(d0.getDate() - 1);
    const w = last === day ? T.today : last === iso(yd) ? T.yday : fill(T.on, { d: typeof fdate === 'function' ? fdate(last, { weekday: 'long' }) : last });
    return { text: fill(T.habit, { h: T.h[code], k, n: list.length, w }) };
  }

  // the tone follows the experience given at the start (brief 03): a trader starting out gets the why, and simple goals
  const starting = () => !!(S.me && S.me.experience === 'new');

  /** before a trade, in the two add forms (live): the signal of the moment with his own number, then what is left.
   *  x: { form: 'manual' | 'shot', account, date, qty, time ('HH:MM', empty = now) } → html ('' when there is nothing to say) */
  function beforeHtml(x) {
    if (!x || !(S.accounts || []).some((a) => !a.demo)) return '';
    const day = x.date || today(), list = dayTrades(day), p = planOf(day);
    let sum = 0; list.forEach((t) => { sum += net(t); });
    const nowHm = typeof nowET === 'function' && day === (typeof todayStr === 'function' ? todayStr() : day) ? nowET().slice(11, 16) : '';
    const at = min(x.time || nowHm), last = list[list.length - 1], qty = +x.qty || 0, maxC = +(S.settings && S.settings.max_contracts) || 0;
    let sig = '', mine = '', stop = false;
    let losses = 0; for (let k = list.length - 1; k >= 0 && net(list[k]) < 0; k--) losses++;
    let wins = 0; for (let k = list.length - 1; k >= 0 && net(list[k]) > 0; k--) wins++;
    const gap = last && net(last) < 0 && at != null ? at - (min(last.exit_time || timeOf(last)) ?? at + 1) : null;
    if (p.valid && p.maxLoss && sum <= -p.maxLoss) { sig = fill(T.bMax, { m: usd(p.maxLoss) }); stop = true; }
    else if (p.valid && p.maxTrades && list.length >= p.maxTrades) { sig = fill(T.bDone, { m: p.maxTrades }); stop = true; }
    else if (gap != null && gap >= 0 && gap < 10) { sig = fill(T.bWait, { n: gap, r: 10 - gap }); mine = ownLine('revenge'); stop = true; }
    else if (losses >= 2) { sig = fill(T.bLoss2, { n: losses }); mine = ownLine('loss2'); stop = true; }
    else if (x.form === 'shot' && maxC && qty > maxC) sig = fill(T.bSize, { n: qty, m: maxC });   // (the manual form says it already)
    else if (wins >= 2 && last && qty > +last.contracts) { sig = fill(T.bUp, { w: wins, c: last.contracts }); mine = ownLine('size_up'); }
    else if (at != null && at >= 570 && at < 575) { sig = T.bOpen; mine = ownLine('open5'); }
    else if (!p.valid) sig = T.bNoPlan;
    const bud = [];
    if (p.valid && p.maxLoss && sum > -p.maxLoss) bud.push(fill(T.bLeft, { m: usd(p.maxLoss + sum) }));
    else if (!p.valid && x.form === 'shot' && typeof riskBudget === 'function') { const r = riskBudget(x.account, day); const a = r && (S.accounts || []).find((y) => y.id === x.account); if (r) bud.push(fill(T.bLeftAcc, { m: usd(r.left), a: (a && a.name) || '' })); }
    if (p.valid && p.maxTrades && list.length < p.maxTrades) bud.push(fill(T.bCount, { n: list.length + 1, m: p.maxTrades }));
    if (!sig && !bud.length) return '';
    const b = bud.join(' · ').replace(/^./, (m) => m.toUpperCase());
    return `<div class="co-before ${stop ? 'co-stop' : ''}" data-noi18n aria-live="polite"><span class="co-ic">${IC}</span><div><b>${T.title}</b> · <span>${T.bTitle}</span>${sig ? `<p class="co-sig">${esc2(sig)}</p>` : ''}${mine ? `<p class="co-own">${esc2(mine)}</p>` : ''}${b ? `<p class="co-bud">${esc2(b)}</p>` : ''}</div></div>`;
  }

  /** the accounts at 75 % or more of their daily loss limit or of their drawdown, as their own page shows them (acctState):
   *  [{ a, kind: 'dll' | 'dd', level: 75 | 100, pct, used, limit, left, fresh (crossed by today's trades) }], the worst first */
  function limits() {
    const out = []; if (typeof acctState !== 'function') return out;
    (S.accounts || []).filter((a) => !a.demo && a.status !== 'archived' && a.status !== 'closed' && a.rules).forEach((a) => {
      let st = null; try { st = acctState(a); } catch (e) { return; }
      if (!st) return;
      const dll = +a.rules.dll_c || 0, td = +st.today || 0;
      if (dll > 0 && td < 0) { const used = -td, pct = used / dll; if (pct >= 0.75) out.push({ a, kind: 'dll', level: pct >= 1 ? 100 : 75, pct: Math.round(Math.min(pct, 1) * 100), used, limit: dll, left: Math.max(0, dll - used), fresh: true }); }
      const dd = +a.rules.dd_c || 0;
      if (dd > 0 && st.buffer != null) {
        const left = Math.max(0, st.buffer), pct = st.breached ? 1 : 1 - left / dd, before = 1 - Math.max(0, st.buffer - Math.min(0, td)) / dd;   // before today's losses
        if (pct >= 0.75) out.push({ a, kind: 'dd', level: pct >= 1 ? 100 : 75, pct: Math.round(Math.min(pct, 1) * 100), used: dd - left, limit: dd, left, fresh: td < 0 && before < (pct >= 1 ? 1 : 0.75) });
      }
    });
    return out.sort((x, y) => y.level - x.level || (x.kind === 'dll' ? -1 : 1));
  }
  const limitLine = (x) => fill(T.lim[x.kind + x.level], { a: x.a.name || '', p: x.pct, u: usd(x.used), l: usd(x.limit), r: usd(x.left) });
  /* the bell, once per account, kind, level and day (the server keeps it once too): only a level crossed by today's trades */
  const sentKey = (x) => `sw.propAlert.${x.a.id}.${x.kind}.${x.level}.${today()}`;
  function alertLimits() {
    if (S.mode !== 'server' || typeof apiJSON !== 'function') return;
    limits().filter((x) => x.fresh).forEach((x) => {
      try { if (sessionStorage.getItem(sentKey(x))) return; sessionStorage.setItem(sentKey(x), '1'); } catch (e) { /* private mode: the server dedupes */ }
      apiJSON('api/notifications/prop-alert', { method: 'POST', body: { account: x.a.id, kind: x.kind, level: x.level, pct: x.pct, used_c: Math.round(x.used), limit_c: Math.round(x.limit), left_c: Math.round(x.left) } })
        .then(() => { if (window.SweepNotify && SweepNotify.refresh) setTimeout(() => SweepNotify.refresh(), 300); }).catch(() => { /* the coach card says it anyway */ });
    });
  }
  let limKey = '';
  function watchLimits() {   // after the trades or the accounts change (a save, a sync, the first load)
    const k = [(S.trades || []).length, (S.trades || []).reduce((m, t) => (t.updated_at > m ? t.updated_at : m), ''), (S.accounts || []).reduce((m, a) => (a.updated_at > m ? a.updated_at : m), ''), today()].join('|');
    if (k === limKey) return; limKey = k; setTimeout(() => { try { alertLimits(); } catch (e) { /* never blocks */ } }, 800);
  }

  /* ── what works for you (brief 03 step 4): over a span of days, 1 strength, 1 leak, 1 rule, with the samples ── */
  const PLAN_CODES = ['over_max_loss', 'over_max_trades', 'against_bias', 'setup_not_in_plan', 'plan_no_trade', 'no_plan'];
  const isoD = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
  const addDays = (day, n) => { const d = new Date(day + 'T12:00:00'); d.setDate(d.getDate() + n); return isoD(d); };
  const mondayOf = (day) => { const d = new Date(day + 'T12:00:00'); d.setDate(d.getDate() - ((d.getDay() + 6) % 7)); return isoD(d); };
  /** the real trades of the days from..to (to excluded), each with what the coach says about it */
  function span(from, to) {
    const days = [...new Set((S.trades || []).filter((t) => !t.demo && t.date >= from && t.date < to).map((t) => t.date))].sort();
    const rows = []; days.forEach((d) => dayTrades(d).forEach((t) => rows.push({ t, c: tradeNote(t), day: d })));
    return { days, rows };
  }
  const rate = (rows) => (rows.length ? Math.round(rows.filter((r) => net(r.t) > 0).length / rows.length * 100) : 0);
  function strength(sp) {
    const R = sp.rows, all = rate(R), cands = [];
    const inPlan = R.filter((r) => planOf(r.day).valid && !r.c.all.some((x) => PLAN_CODES.includes(x))), off = R.filter((r) => !inPlan.includes(r));
    if (inPlan.length >= 5 && off.length >= 5) cands.push({ gap: rate(inPlan) - rate(off), n: Math.min(inPlan.length, off.length), text: fill(T.sPlan, { a: rate(inPlan), n: inPlan.length, b: rate(off), m: off.length }) });
    const group = (key) => { const m = new Map(); R.forEach((r) => { const k = key(r.t); if (k) { if (!m.has(k)) m.set(k, []); m.get(k).push(r); } }); return [...m.entries()].filter(([, v]) => v.length >= 5); };
    const best = (g, tpl, label) => { if (g.length < 2) return; const [k, v] = g.sort((a, b) => rate(b[1]) - rate(a[1]) || b[1].length - a[1].length)[0]; cands.push({ gap: rate(v) - all, n: v.length, text: fill(tpl, { s: label(k), a: rate(v), n: v.length }) }); };
    best(group((t) => String(t.setup || '').trim()), T.sSetup, (k) => k);
    best(group((t) => { const e = min(timeOf(t)); return e == null ? '' : String(Math.floor(e / 30) * 30); }), T.sSlot, (k) => { const a = +k, b = a + 30, p = (x) => String(x).padStart(2, '0'); return T.slot(p(Math.floor(a / 60)), p(a % 60), p(Math.floor(b / 60)), p(b % 60)); });
    const top = cands.filter((x) => x.gap >= 5).sort((a, b) => b.gap * Math.sqrt(b.n) - a.gap * Math.sqrt(a.n))[0];
    if (top) return top.text;
    const clean = sp.days.filter((d) => R.filter((r) => r.day === d).every((r) => !r.c.fix)).length;
    if (clean && sp.days.length >= 3) return fill(T.sClean, { k: clean, n: sp.days.length });
    return T.sNone;
  }
  function leakOf(sp) {
    const by = {}; sp.rows.forEach((r) => { if (!r.c.fix) return; const k = r.c.fix[2], x = by[k] || (by[k] = { n: 0, c: 0 }); x.n++; x.c += net(r.t); });
    const order = Object.keys(T.f), top = Object.entries(by).sort((a, b) => b[1].n - a[1].n || a[1].c - b[1].c || order.indexOf(a[0]) - order.indexOf(b[0]))[0];
    return top ? { code: top[0], n: top[1].n, c: top[1].c } : null;
  }
  const ruleFor2 = (code, sp) => fill(T.r[code] || T.r.clean, { m: code === 'over_max_trades' ? (sp.days.map((d) => planOf(d).maxTrades).filter(Boolean).pop() || '') : +(S.settings && S.settings.max_contracts) || '' });
  /** progress per habit, week by week (the last 5 weeks): % of trades without the habit's mistake */
  const HABITS = { no_stop: ['no_stop'], over_max_loss: ['over_max_loss'], over_max_trades: ['over_max_trades'], revenge: ['revenge'], setup_not_in_plan: ['setup_not_in_plan'], oversized: ['oversized', 'size_up'], no_plan: ['no_plan'] };
  function progress(day) {
    const mon = mondayOf(day || today()), weeks = [4, 3, 2, 1, 0].map((k) => addDays(mon, -7 * k));
    const W = weeks.map((m) => ({ mon: m, rows: span(m, addDays(m, 7)).rows }));
    const out = [];
    Object.entries(HABITS).forEach(([key, codes]) => {
      const pts = W.map((w) => (w.rows.length ? { mon: w.mon, n: w.rows.length, pct: Math.round(w.rows.filter((r) => !r.c.all.some((x) => codes.includes(x))).length / w.rows.length * 100) } : { mon: w.mon, n: 0, pct: null }));
      const had = pts.filter((x) => x.pct != null), miss = W.reduce((s, w) => s + w.rows.filter((r) => r.c.all.some((x) => codes.includes(x))).length, 0);
      if (had.length >= 2 && miss) out.push({ key, label: T.h[key], pts, first: had[0], last: had[had.length - 1], miss });
    });
    return out.sort((a, b) => b.miss - a.miss).slice(0, 4);
  }
  const prLine = (h) => { const ago = (m) => Math.round((new Date(mondayOf(today()) + 'T12:00:00') - new Date(m + 'T12:00:00')) / 6048e5);
    const wl = ago(h.last.mon), l = wl === 0 ? T.prNow : wl === 1 ? T.prLast : fill(T.prAgo, { w: wl });
    return fill(T.prLine, { w: ago(h.first.mon), a: h.first.pct, l, b: h.last.pct }).replace(/^./, (m) => m.toUpperCase()); };
  const bars = (h) => `<span class="co-bars" aria-hidden="true">${h.pts.map((x) => `<i class="${x.pct == null ? 'none' : ''}" style="--h:${x.pct == null ? 6 : Math.max(8, x.pct)}%"></i>`).join('')}</span>`;
  const row = (label, text) => `<p class="co-row"><b>${label}</b><span>${esc2(text)}</span></p>`;
  let wCache = { k: '', v: '' };
  const tradesKey = () => [(S.trades || []).length, (S.trades || []).reduce((m, t) => (t.updated_at > m ? t.updated_at : m), ''), (S.journals || []).reduce((m, x) => (x.updated_at > m ? x.updated_at : m), ''), today()].join('|');
  /** the Friday recap (weekly sheet, step 0): the week, in % and counts (the sheet shows one dollar amount: the payouts) */
  function weekHtml(mon) {
    const k = 'w' + mon + tradesKey(); if (wCache.k === k) return wCache.v;
    const sp = span(mon, addDays(mon, 7)); let v = '';
    if (sp.rows.length) {
      const lk = leakOf(sp), hp = lk && progress(addDays(mon, 4)).find((h) => (HABITS[h.key] || []).includes(lk.code));
      v = `<div class="co-week" data-noi18n><div class="co-h"><span class="co-ic">${IC}</span><b>${T.title}</b><small>${T.wkT}</small></div>
        ${row(T.strong, strength(sp))}${row(T.leak, lk ? fill(lk.n === 1 ? T.lk1 : T.lk, { w: T.w[lk.code], k: lk.n, n: sp.rows.length, c: '' }).replace(/^./, (m) => m.toUpperCase()) : fill(T.lkNone, { n: sp.rows.length }))}
        ${row(T.ruleW, ruleFor2(lk ? lk.code : 'clean', sp))}${hp && hp.first.mon !== hp.last.mon ? `<p class="co-own">${esc2(prLine(hp))}</p>` : ''}</div>`;
    }
    wCache = { k, v }; return v;
  }
  /** the Stats page, at the top: the last 4 weeks, then the progress per habit */
  let sCache = { k: '', v: '' };
  function statsHtml() {
    const k = 's' + tradesKey(); if (sCache.k === k) return sCache.v;
    const to = addDays(today(), 1), sp = span(addDays(to, -28), to); let v = '';
    if (sp.rows.length) {
      const lk = leakOf(sp), pr = progress(today());
      v = `<section class="surface co co-stats" data-noi18n><div class="co-h"><span class="co-ic">${IC}</span><b>${T.stT}</b><small>${esc2(fill(T.stSub, { n: sp.rows.length }))}</small></div>
        ${row(T.strong, strength(sp))}${row(T.leak, lk ? fill(lk.n === 1 ? T.lk1 : T.lk, { w: T.w[lk.code], k: lk.n, n: sp.rows.length, c: lk.c < 0 ? ` (${sgn(lk.c)})` : '' }).replace(/^./, (m) => m.toUpperCase()) : fill(T.lkNone, { n: sp.rows.length }))}
        ${row(T.rule, ruleFor2(lk ? lk.code : 'clean', sp))}
        ${pr.length ? `<div class="co-prog"><p class="co-prog-h"><b>${T.prT}</b><small>${T.prHelp}</small></p>${pr.map((h) => `<div class="co-pr"><span class="co-pr-t"><b>${esc2(h.label.replace(/^./, (m) => m.toUpperCase()))}</b><small>${esc2(prLine(h))}</small></span>${bars(h)}</div>`).join('')}</div>` : ''}
        ${aiMore('ai-review', '')}</section>`;
    }
    sCache = { k, v }; return v;
  }
  function paintStats() {
    if (!/^#analytics/.test(location.hash || '')) return;
    const first = document.querySelector('#main .ikpis'); if (!first) return;
    const host = first.parentElement && first.parentElement.id !== 'main' ? first.parentElement : first;   // before the Pro lock: the coach is for every plan
    const html = statsHtml(); let el = document.querySelector('#main .co-stats');
    if (!html) { if (el) el.remove(); return; }
    if (el && el._h === html && el.nextElementSibling === host) return;
    const tmp = document.createElement('div'); tmp.innerHTML = html; const fresh = tmp.firstElementChild; fresh._h = html;
    if (el) el.remove(); host.before(fresh);
  }

  /* ── how it reads ── */
  const IC = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3a4 4 0 0 1 4 4v1a4 4 0 0 1-8 0V7a4 4 0 0 1 4-4z"/><path d="M5 21a7 7 0 0 1 14 0"/></svg>';
  const OK = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12.5l4.2 4.2L19 7"/></svg>';
  function noteHtml(c) {
    const good = c.good.length ? `<p class="co-ok">${OK}<span>${esc2(c.good.join(', ').replace(/^./, (m) => m.toUpperCase()))}.</span></p>` : '';
    const why = c.fix && starting() && T.why[c.fix[2]] ? `<span class="co-why">${esc2(T.why[c.fix[2]])}</span>` : '';
    const mine = c.fix && ['revenge', 'size_up', 'open5'].includes(c.fix[2]) ? ownLine(c.fix[2]) : '';
    const fix = c.fix ? `<p class="co-fix"><b>${T.fix}</b><span>${esc2(c.fix[0])}</span><span class="co-do">${esc2(c.fix[1])}</span>${mine ? `<span class="co-own">${esc2(mine)}</span>` : ''}${why}</p>` : `<p class="co-fix co-none"><span>${esc2(T.none)}</span></p>`;
    const l2 = c.ses.code === 'loss2' ? ownLine('loss2') : '';
    return good + fix + (c.ses.t ? `<p class="co-ses ${c.ses.stop ? 'co-stop' : ''}">${esc2(c.ses.t)}</p>` : '') + (l2 ? `<p class="co-own">${esc2(l2)}</p>` : '');
  }
  // Today: a card of its own; the trade's page: a block inside the result card (not a card in a card)
  const card = (sub, body, cls) => `<section class="${cls === 'co-trade' ? '' : 'surface '}co ${cls || ''}" data-noi18n aria-live="polite"><div class="co-h"><span class="co-ic">${IC}</span><b>${T.title}</b>${sub ? `<small>${esc2(sub)}</small>` : ''}</div>${body}</section>`;

  /* Today: the coach card, right under the routine (it is not inside it: the routine is rebuilt when the game state moves) */
  // Sweep AI goes further from what the coach said, at the same place (the app's own button: shown only when Sweep AI is
  // on, its plan limits and paywall unchanged)
  const aiMore = (act, attrs) => (typeof aiBtn === 'function' ? `<div class="co-ai">${aiBtn(act, esc2(T.ai), attrs)}</div>` : '');
  const ruleLine = (label, r) => `<p class="co-rule"><b>${label}</b><span>${esc2(r)}</span></p>`;
  function todayHtml() {
    if (!(S.accounts || []).some((a) => !a.demo)) return '';
    const day = today(), list = dayTrades(day), jt = typeof getDoc === 'function' && getDoc('journals', day);
    if (jt && jt.post && jt.post.reviewed_at && (list.length || jt.pre)) {   // the day is reviewed: its lesson, and the rule for tomorrow
      const l = dayLesson(day), own = String(jt.post.tomorrow || '').split('\n').map((x) => x.trim()).find(Boolean);
      return card(T.dayT, `<p class="co-ses">${esc2(l.text)}</p>${(own || l.rule) ? ruleLine(T.ruleT, own || l.rule) : ''}${list.length ? aiMore('ai-day', `data-v="${esc2(day)}"`) : ''}`, 'co-today');
    }
    if (list.length) { const c = tradeNote(list[list.length - 1]); return card(fill(T.last, { t: c.time || '' }), noteHtml(c), 'co-today'); }
    const nx = (window.SweepNextSession && SweepNextSession()) || day, p = planOf(nx), j = typeof getDoc === 'function' && getDoc('journals', nx);
    const first = !(S.trades || []).some((t) => !t.demo);
    if (p.valid) { const pre = (j && j.pre) || {}; return card(T.planT, `${pre.rule ? ruleLine(T.ruleD, pre.rule) : ''}<p class="co-ses">${esc2(planNote({ bias: p.bias, maxLoss: p.maxLoss, maxTrades: p.maxTrades, setups: (pre.setups || []).length }))}</p>${first ? `<p class="co-ses muted">${esc2(T.first)}</p>` : ''}`, 'co-today'); }
    return card('', `<p class="co-ses">${esc2(T.noPlan)}</p>`, 'co-today');
  }
  function paintToday() {
    if (!/^#?(dashboard)?$/.test((location.hash || '').replace(/^#/, ''))) return;
    const host = document.querySelector('#main .nav-dash .d-today'); if (!host) return;
    let html = todayHtml(); const hb = html && habit(today()), lim = html ? limits() : [];
    // (replaced by a function: an amount like « $1,000 » must not read as « $1 », the first group)
    if (lim.length) html = html.replace(/<\/div>/, (m) => `${m}<p class="co-ses co-stop co-lim">${esc2(limitLine(lim[0]))}</p>`);   // right under the coach's title
    if (hb) html = html.replace(/<\/section>$/, () => `<p class="co-habit">${esc2(hb.text)}</p></section>`);
    // inside the routine card, between its figures and its 3 steps: it folds with them (brief of 15 Oct.)
    const put = (x) => { const rt = host.querySelector(':scope > .nav-rt'), st = rt && rt.querySelector(':scope > .nav-rt-steps'), hp = rt && rt.querySelector(':scope > .nav-rt-help-t');
      if (st) { if (x.nextElementSibling !== st) st.before(x); } else if (rt) { if (x.parentElement !== rt) (hp ? hp.before(x) : rt.append(x)); } else if (x.parentElement !== host) host.prepend(x); };
    let el = host.querySelector('.co-today');
    if (!html) { if (el) el.remove(); return; }
    if (el && el._h === html) { put(el); return; }
    const tmp = document.createElement('div'); tmp.innerHTML = html; const fresh = tmp.firstElementChild; fresh._h = html;
    if (el) el.replaceWith(fresh); put(fresh);
  }
  /* the trade's page: the coach right under its result (sample trades: the questions only, not the coach's verdict) */
  const tradeCard = (t) => (!t || t.demo ? '' : card(T.thisT, noteHtml(tradeNote(t)) + aiMore('ai-feedback', `data-id="${esc2(t.id)}"`), 'co-trade'));
  function paintTrade() {   // (fallback: the page draws these blocks itself, app.js vTrade)
    const m = /^#trade\/([^/?]+)/.exec(location.hash || ''); if (!m) return;
    const t = typeof getDoc === 'function' && getDoc('trades', decodeURIComponent(m[1])); const head = document.querySelector('#main .th-head');
    if (!t || !head) return;
    if (!document.querySelector('#main .co-trade') && !t.demo) { const tmp = document.createElement('div'); tmp.innerHTML = tradeCard(t); if (tmp.firstElementChild) head.after(tmp.firstElementChild); }
    if (!document.querySelector('#main .co-ask')) paintAsk(t);
  }
  /* the trade's page (brief 03 step 5): « Answer your coach », 2 or 3 questions aimed at this trade, in place of « Review x
   * of 4 »; the full review (checklist, emotions, notes, screenshots) stays one tap away, folded (open or not: kept per trade).
   * The buttons are the app's own (data-act set / toggle, data-bind): the answers go to the same fields. */
  const emoT = (k) => { const d = L !== 'en' && window['I18N_' + L.toUpperCase()]; return (d && d[k]) || k; };
  let fullOpen; try { fullOpen = new Set(JSON.parse(sessionStorage.getItem('sw.coFull') || '[]')); } catch (e) { fullOpen = new Set(); }
  function askHtml(t) {
    const c = tradeNote(t), qs = ((S.settings && S.settings.questions) || []).filter((q) => q.active), has = (id) => qs.some((q) => q.id === id);
    const d = t.discipline || {}, emo = (t.emo && t.emo.before) || [], rv = t.review || {}, id = esc2(t.id), items = [];
    const yn = (k, label) => { items.push({ ok: !!d[k], h: `<div class="co-q"><span>${esc2(label)}</span><div class="seg yn">${[['y', T.yes], ['n', T.no]].map(([v, l]) => `<button class="${v} ${d[k] === v ? 'on' : ''}" data-act="set" data-col="trades" data-id="${id}" data-path="discipline.${k}" data-v="${v}">${l}</button>`).join('')}</div></div>` }); };
    if (has('plan')) yn('plan', T.aPlan);
    const code = c.fix && c.fix[2];
    if ((code === 'no_stop' || code === 'risklimit') && has('stop')) yn('stop', T.aStop);
    else if ((code === 'oversized' || code === 'size_up') && has('size')) yn('size', T.aSize);
    else {
      const set = code ? ['Frustrated', 'Trying to recover a loss', 'Impulsive', 'FOMO', 'Calm'] : ['Calm', 'Confident', 'FOMO', 'Frustrated', 'Hesitant'];
      items.push({ ok: emo.length > 0, h: `<div class="co-q"><span>${esc2(code ? T.aWhy : T.aEmo)}</span><div class="chips">${set.map((k) => `<button class="chip ${emo.includes(k) ? 'on' : ''}" data-act="toggle" data-col="trades" data-id="${id}" data-path="emo.before" data-v="${esc2(k)}">${esc2(emoT(k))}</button>`).join('')}</div></div>` });
    }
    items.push({ ok: !!String(rv.lesson || '').trim(), h: `<label class="co-q co-q-l"><span>${esc2(T.aLesson)}</span><textarea rows="2" data-bind="trades|${id}|review.lesson" placeholder="${esc2(c.fix ? c.fix[1] : T.aLessonPh)}">${esc2(rv.lesson || '')}</textarea></label>` });
    return `<section class="surface co co-ask" data-noi18n><div class="co-h"><span class="co-ic">${IC}</span><b>${T.askT}</b><small>${fill(T.askN, { k: items.filter((x) => x.ok).length, n: items.length })}</small></div>${items.map((x) => x.h).join('')}</section>`;
  }
  const fullLabel = (x) => fill(T.fullT, { x });
  // (the full review's open state: kept per trade while the tab lives)
  document.addEventListener('toggle', (e) => {
    const d = e.target; if (!d.matches || !d.matches('details.co-full') || !d.dataset.id) return;
    d.open ? fullOpen.add(d.dataset.id) : fullOpen.delete(d.dataset.id);
    try { sessionStorage.setItem('sw.coFull', JSON.stringify([...fullOpen].slice(-50))); } catch (x) { /* private mode */ }
  }, true);
  /* (fallback, a trade page drawn before this module loaded: the same blocks put in place afterwards) */
  function paintAsk(t) {
    const main = document.getElementById('main'), prog = main && main.querySelector('.rprog'), tm = main && main.querySelector('.tr-main'); if (!prog || !tm) return;
    const steps = [...tm.querySelectorAll(':scope > .rstep')];
    let full = tm.querySelector(':scope > details.co-full');
    if (!full && steps.length) {
      full = document.createElement('details'); full.className = 'co-full'; full.dataset.id = t.id; full.open = fullOpen.has(t.id);
      full.innerHTML = '<summary data-noi18n></summary>'; steps[0].before(full); steps.forEach((x) => full.append(x));
    }
    if (full) { const s = full.querySelector(':scope > summary'), x = fill(T.fullT, { x: prog.querySelectorAll('.rprog-steps a.ok').length }); if (s.textContent !== x) s.textContent = x; }
    prog.hidden = true;
    const html = askHtml(t); let el = main.querySelector('.co-ask');
    if (el && el._h === html) return;
    if (el && el.contains(document.activeElement) && document.activeElement.tagName === 'TEXTAREA') return;   // typing his lesson: never redrawn under the fingers
    const tmp = document.createElement('div'); tmp.innerHTML = html; const fresh = tmp.firstElementChild; fresh._h = html;
    if (el) el.replaceWith(fresh); else prog.after(fresh);
  }
  // the « Review » tab of the trade's page goes to the coach's questions (the full review is folded under them)
  document.addEventListener('click', (e) => {
    const b = e.target.closest && e.target.closest('.nav-tnav [data-tn="2"]'), ask = document.querySelector('#main .co-ask'); if (!b || !ask) return;
    e.stopPropagation();
    b.parentElement.querySelectorAll('button').forEach((x) => { x.classList.toggle('on', x === b); x.setAttribute('aria-selected', x === b); });
    const bar = b.parentElement, y = ask.getBoundingClientRect().top + scrollY - (bar.offsetHeight + (window.SW_MQ && window.SW_MQ.matches ? 70 : 20));
    scrollTo({ top: Math.max(0, y), behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
  }, true);

  /* the plan sheet: one sentence, live, above the error line and the button */
  function paintPlan() {
    const sh = document.querySelector('#gSheet.g-plan, #gSheet .g-plan') && document.getElementById('gSheet'); if (!sh || !sh.querySelector('[data-g="save-plan"]')) return;
    const err = sh.querySelector('#gErr'); if (!err) return;
    const b = sh.querySelector('[data-g="bias"].on'), ml = sh.querySelector('[data-gp="max_loss"]'), mt = sh.querySelector('[data-gp="max_trades"]');
    const txt = planNote({ bias: b ? b.dataset.v : null, maxLoss: cents(ml && ml.value), maxTrades: parseInt(mt && mt.value, 10) || 0, setups: sh.querySelectorAll('.g-setups .chip.on').length });
    let el = sh.querySelector('.co-plan');
    if (!el) { el = document.createElement('p'); el.className = 'co-plan'; el.setAttribute('data-noi18n', ''); el.setAttribute('aria-live', 'polite'); err.before(el); }
    const html = `<span class="co-ic">${IC}</span><span><b>${T.title}</b> · ${esc2(txt)}</span>`;
    if (el._h !== html) { el.innerHTML = html; el._h = html; }
  }
  function paintReview() {
    const sh = document.getElementById('gSheet'); if (!sh || !sh.querySelector('[data-gr="tomorrow"]')) return;
    const err = sh.querySelector('#gErr'), ta = sh.querySelector('[data-gr="tomorrow"]'); if (!err) return;
    const l = dayLesson(sh.dataset.day || today());
    if (l.rule && !ta.placeholder) ta.placeholder = fill(T.rulePh, { r: l.rule });
    let el = sh.querySelector('.co-plan'); if (!el) { el = document.createElement('p'); el.className = 'co-plan co-rv'; el.setAttribute('data-noi18n', ''); err.before(el); }
    const html = `<span class="co-ic">${IC}</span><span><b>${T.title}</b> · ${esc2(l.text)}</span>`;
    if (el._h !== html) { el.innerHTML = html; el._h = html; }
  }
  document.addEventListener('input', (e) => { if (e.target.closest && e.target.closest('#gSheet')) paintPlan(); });
  document.addEventListener('click', (e) => { if (e.target.closest && e.target.closest('#gSheet')) setTimeout(paintPlan, 0); });

  /* the « saved » message of ONE new trade carries the coach's most useful line (not its copies on other accounts,
   * not an import of several trades: their messages stay as they are) */
  let fresh = null;
  if (typeof window.put === 'function') {
    const p0 = window.put;
    window.put = function (col, doc) {
      try {
        if (col === 'trades' && doc && !doc.demo && !(S.trades || []).some((x) => x.id === doc.id)) {
          const copy = doc.copy_group && (S.trades || []).some((x) => x.copy_group === doc.copy_group);
          const now = Date.now();   // new trades a few milliseconds apart = an import or a batch, not one trade saved by hand
          if (!copy) fresh = fresh && now - fresh.last < 300 ? Object.assign(fresh, { many: true, last: now }) : { id: doc.id, at: now, last: now };
        }
      } catch (e) { /* never blocks a save */ }
      return p0.apply(this, arguments);
    };
  }
  if (typeof window.toast === 'function') {
    const t0 = window.toast;
    window.toast = function (msg, opts) {
      try {
        if (fresh && fresh.many) fresh = null;
        if (fresh && Date.now() - fresh.at < 2500 && typeof msg === 'string') {
          const t = getDoc('trades', fresh.id); fresh = null;
          const c = t && tradeNote(t);
          const lim = t && limits().find((x) => x.a.id === t.account_id && x.fresh);
          const line = lim ? limitLine(lim) : c && (c.ses.stop ? c.ses.t : c.fix ? c.fix[0] : c.ses.t);   // an account at its limit, then stop or pause, then the one thing to improve
          if (line) return t0.call(this, msg + ' · ' + line, Object.assign({}, opts, { ms: 5000 }));
        }
      } catch (e) { /* the message stays as it was */ }
      return t0.apply(this, arguments);
    };
  }

  const paint = () => { try { paintToday(); paintTrade(); paintPlan(); paintReview(); paintStats(); watchLimits(); } catch (e) { /* the coach never blocks the app */ } };
  // the bell's words for these alerts (one type, four keys: daily limit or drawdown, 75 % or 100 %)
  const N = {
    en: { 'prop_dll75.title': 'Daily limit: {pct}% used', 'prop_dll75.body': '{account}: ${used} of ${limit}. Keep your size, or stop here.',
      'prop_dll100.title': 'Daily limit reached', 'prop_dll100.body': '{account}: ${limit} lost today. Your session is over on this account.',
      'prop_dd75.title': 'Drawdown: {pct}% used', 'prop_dd75.body': '{account}: ${left} of room left before the limit. Trade smaller until it comes back.',
      'prop_dd100.title': 'Drawdown limit reached', 'prop_dd100.body': '{account}: the account’s max loss is reached. Check its status with your firm.' },
    fr: { 'prop_dll75.title': 'Limite du jour : {pct} % utilisés', 'prop_dll75.body': '{account} : {used} $ sur {limit} $. Garde ta taille, ou arrête-toi ici.',
      'prop_dll100.title': 'Limite du jour atteinte', 'prop_dll100.body': '{account} : {limit} $ perdus aujourd’hui. Ta séance est finie sur ce compte.',
      'prop_dd75.title': 'Drawdown : {pct} % utilisés', 'prop_dd75.body': '{account} : il reste {left} $ de marge avant la limite. Trade plus petit jusqu’à ce qu’elle remonte.',
      'prop_dd100.title': 'Limite de drawdown atteinte', 'prop_dd100.body': '{account} : la perte max du compte est atteinte. Vérifie son statut auprès de ta firme.' },
    es: { 'prop_dll75.title': 'Límite diario: {pct} % usado', 'prop_dll75.body': '{account}: {used} $ de {limit} $. Mantén tu tamaño, o para aquí.',
      'prop_dll100.title': 'Límite diario alcanzado', 'prop_dll100.body': '{account}: {limit} $ perdidos hoy. Tu sesión terminó en esta cuenta.',
      'prop_dd75.title': 'Drawdown: {pct} % usado', 'prop_dd75.body': '{account}: quedan {left} $ de margen antes del límite. Opera más pequeño hasta que se recupere.',
      'prop_dd100.title': 'Límite de drawdown alcanzado', 'prop_dd100.body': '{account}: se alcanzó la pérdida máxima de la cuenta. Verifica su estado con tu firma.' },
  };
  const reg = () => { if (window.SweepNotify && SweepNotify.strings) { try { SweepNotify.strings(N); } catch (e) { /* older module */ } return true; } return false; };
  if (!reg()) setTimeout(reg, 1500);
  const appRender = window.render;
  window.render = function () { const out = appRender.apply(this, arguments); paint(); return out; };
  new window.SweepMO(paint).observe(document.body, { childList: true, subtree: true });
  window.SweepCoach = { trade: tradeNote, session, plan: planNote, today: todayHtml, lesson: dayLesson, ruleFor, habit, before: beforeHtml, own: ownLine, limits, weekHtml, statsHtml, progress,
    tradeCard, askHtml, fullOpen: (id) => fullOpen.has(id), fullLabel };
})();
