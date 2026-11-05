<?php
declare(strict_types=1);
if (PHP_SAPI !== 'cli' && realpath((string) ($_SERVER['SCRIPT_FILENAME'] ?? '')) === realpath(__FILE__)) { http_response_code(404); exit; }
/**
 * Sweep — the phone notification of each message (push/push-auto.php), as it starts: Admin › Emails changes the text and
 * switches it on (every one starts off: Mateo reads the texts first).
 *  ch:    push       the phone first; its email (same key, mail/mail-auto.php) 24 h later, only when the notification was not
 *                    opened and the trader did not come back;
 *         push_away  the same, only when the trader is not in the app at that moment (in the app: the email as before);
 *         both       the phone and the email at once (the account and its money);
 *         only       the phone alone (no email exists);
 *         alert      the phone alone, an account alert: also in the bell (prop firm alerts), never in the week's 5, allowed
 *                    during the session.
 *  group: the switch of Settings › Notifications › On this device (push/web-push.php WP_GROUPS).
 *  url:   what a tap opens ({account}: the account's page).
 *  text:  [title, line] per language, {values} of the event; 60 characters at most for the title.
 */
return [
    'day1Evening' => ['ch' => 'push', 'group' => 'routine', 'url' => '#dashboard', 'text' => [
        'en' => ['Tomorrow starts tonight', '30 seconds for your plan: bias, levels and max loss.'],
        'fr' => ['Demain se prépare ce soir', '30 secondes pour ton plan : biais, niveaux et perte max.'],
        'es' => ['Mañana se prepara esta noche', '30 segundos para tu plan: sesgo, niveles y pérdida máxima.']]],
    'inactive3d' => ['ch' => 'push', 'group' => 'routine', 'url' => '#dashboard', 'text' => [
        'en' => ['Your discipline is waiting', 'Pick up where you left off: your next plan takes 30 seconds.'],
        'fr' => ['Ta discipline t’attend', 'Reprends là où tu étais : ton prochain plan prend 30 secondes.'],
        'es' => ['Tu disciplina te espera', 'Retoma donde lo dejaste: tu próximo plan toma 30 segundos.']]],
    'inactive7d' => ['ch' => 'push', 'group' => 'routine', 'url' => '#dashboard', 'text' => [
        'en' => ['Pick up where you left off', 'Your trades, accounts and progress are waiting. One review is enough.'],
        'fr' => ['Reprends là où tu étais', 'Tes trades, tes comptes et ta progression t’attendent. Une revue suffit.'],
        'es' => ['Retoma donde lo dejaste', 'Tus operaciones, cuentas y progreso te esperan. Basta una revisión.']]],
    'firstTradeLogged' => ['ch' => 'push_away', 'group' => 'progress', 'url' => '#dashboard', 'text' => [
        'en' => ['First trade journaled', 'Tonight, close your day in 2 taps.'],
        'fr' => ['Premier trade journalisé', 'Ce soir, ferme ta journée en 2 touchers.'],
        'es' => ['Primera operación registrada', 'Esta noche, cierra tu día en 2 toques.']]],
    'tradesMilestone' => ['ch' => 'push_away', 'group' => 'progress', 'url' => '#analytics', 'text' => [
        'en' => ['{milestone} trades journaled', 'Your journal has real data now. See what it says in Stats.'],
        'fr' => ['{milestone} trades journalisés', 'Ton journal a maintenant de vraies données. Vois ce qu’il dit dans Stats.'],
        'es' => ['{milestone} operaciones registradas', 'Tu diario ya tiene datos reales. Mira lo que dice en Estadísticas.']]],
    'firstPayoutLogged' => ['ch' => 'push_away', 'group' => 'progress', 'url' => '#payouts', 'text' => [
        'en' => ['First payout recorded', 'My money now shows what trading really pays you.'],
        'fr' => ['Premier payout enregistré', 'Mon argent montre maintenant ce que le trading te rapporte vraiment.'],
        'es' => ['Primer payout registrado', 'Mi dinero muestra ahora lo que el trading te paga de verdad.']]],
    'referralRewarded' => ['ch' => 'push', 'group' => 'progress', 'url' => '#referral', 'text' => [
        'en' => ['A free month for you', 'A trader you invited now uses Sweep. The month is already on your account.'],
        'fr' => ['Un mois gratuit pour toi', 'Un trader que tu as invité utilise maintenant Sweep. Le mois est déjà sur ton compte.'],
        'es' => ['Un mes gratis para ti', 'Un trader que invitaste ya usa Sweep. El mes ya está en tu cuenta.']]],
    'proTrialDaysLeft' => ['ch' => 'both', 'group' => 'news', 'url' => '#plan', 'text' => [
        'en' => ['{days} days left in your Pro trial', 'Keep Pro, or move to Free on your own: nothing is charged.'],
        'fr' => ['Plus que {days} jours d’essai Pro', 'Garde Pro, ou passe à Free tout seul : rien n’est facturé.'],
        'es' => ['Quedan {days} días de tu prueba Pro', 'Mantén Pro, o pasa a Free solo: no se cobra nada.']]],
    'proTrialEnded' => ['ch' => 'both', 'group' => 'news', 'url' => '#plan', 'text' => [
        'en' => ['Your Pro trial is over', 'You are on Free: your journal and accounts are all kept.'],
        'fr' => ['Ton essai Pro est terminé', 'Tu es sur Free : ton journal et tes comptes sont tous gardés.'],
        'es' => ['Tu prueba Pro terminó', 'Estás en Free: tu diario y tus cuentas se conservan.']]],
    'subscriptionStarted' => ['ch' => 'both', 'group' => 'news', 'url' => '#plan', 'text' => [
        'en' => ['Welcome to Sweep {plan}', 'Your subscription is active. Thank you for backing Sweep.'],
        'fr' => ['Bienvenue dans Sweep {plan}', 'Ton abonnement est actif. Merci de soutenir Sweep.'],
        'es' => ['Bienvenido a Sweep {plan}', 'Tu suscripción está activa. Gracias por apoyar Sweep.']]],
    'paymentFailed' => ['ch' => 'both', 'group' => 'news', 'url' => '#plan', 'text' => [
        'en' => ['Your payment did not go through', 'Update your card to keep {plan}: it takes a minute.'],
        'fr' => ['Ton paiement n’est pas passé', 'Mets ta carte à jour pour garder {plan} : ça prend une minute.'],
        'es' => ['Tu pago no se procesó', 'Actualiza tu tarjeta para mantener {plan}: toma un minuto.']]],
    'pauseEnding' => ['ch' => 'both', 'group' => 'news', 'url' => '#plan', 'text' => [
        'en' => ['{plan} resumes in 3 days', 'Your pause ends and Stripe bills again. Everything you logged is still there.'],
        'fr' => ['{plan} reprend dans 3 jours', 'Ta pause se termine et Stripe facture de nouveau. Tout ce que tu as journalisé est là.'],
        'es' => ['{plan} se reanuda en 3 días', 'Tu pausa termina y Stripe cobra de nuevo. Todo lo que registraste sigue ahí.']]],
    // the account's moments (push/push-auto.php pa_account_moments, after each trade): no email
    'payoutReady' => ['ch' => 'alert', 'group' => 'accounts', 'url' => '#account/{id}', 'icon' => 'star',
        'name' => ['en' => 'Payout possible', 'fr' => 'Payout possible', 'es' => 'Payout posible'],
        'when' => ['en' => 'A funded account meets every payout condition of its firm (once per payout cycle)', 'fr' => 'Un compte financé remplit toutes les conditions de payout de sa firme (une fois par cycle de payout)', 'es' => 'Una cuenta fondeada cumple todas las condiciones de payout de su firma (una vez por ciclo de payout)'],
        'text' => [
        'en' => ['{account} can ask for a payout', 'Every payout condition of your firm is met. Record your request in Sweep.'],
        'fr' => ['{account} peut demander un payout', 'Toutes les conditions de payout de ta firme sont remplies. Note ta demande dans Sweep.'],
        'es' => ['{account} puede pedir un payout', 'Se cumplen todas las condiciones de payout de tu firma. Registra tu solicitud en Sweep.']]],
    'goalReached' => ['ch' => 'alert', 'group' => 'accounts', 'url' => '#account/{id}', 'icon' => 'star',
        'name' => ['en' => 'Profit target reached', 'fr' => 'Objectif de profit atteint', 'es' => 'Objetivo de beneficio alcanzado'],
        'when' => ['en' => 'An evaluation reaches its profit target, with conditions still to meet (once per account)', 'fr' => 'Une évaluation atteint son objectif de profit, avec des conditions encore à remplir (une fois par compte)', 'es' => 'Una evaluación alcanza su objetivo de beneficio, con condiciones aún por cumplir (una vez por cuenta)'],
        'text' => [
        'en' => ['{account}: profit target reached', 'Still to meet: {left}.'],
        'fr' => ['{account} : objectif de profit atteint', 'Il reste à remplir : {left}.'],
        'es' => ['{account}: objetivo de beneficio alcanzado', 'Falta cumplir: {left}.']]],
    'evalPassed' => ['ch' => 'alert', 'group' => 'accounts', 'url' => '#account/{id}', 'icon' => 'trophy',
        'name' => ['en' => 'Evaluation passed', 'fr' => 'Évaluation réussie', 'es' => 'Evaluación superada'],
        'when' => ['en' => 'An evaluation meets its target, its minimum days and its consistency (once per account)', 'fr' => 'Une évaluation remplit son objectif, ses jours minimum et sa consistance (une fois par compte)', 'es' => 'Una evaluación cumple su objetivo, sus días mínimos y su consistencia (una vez por cuenta)'],
        'text' => [
        'en' => ['{account}: evaluation passed', 'Target, days and consistency: all met. Check it with your firm.'],
        'fr' => ['{account} : évaluation réussie', 'Objectif, jours et consistance : tout est rempli. Vérifie auprès de ta firme.'],
        'es' => ['{account}: evaluación superada', 'Objetivo, días y consistencia: todo cumplido. Confírmalo con tu firma.']]],
    // the feedback emails (brief « Courriels de feedback », step 4): « You asked, it's done » both at once, the others phone first
    'feedbackShipped' => ['ch' => 'both', 'group' => 'progress', 'url' => '#feedback', 'text' => [
        'en' => ['You asked, it’s done', 'Your suggestion is now in Sweep. See the reply.'],
        'fr' => ['Tu l’as demandé, c’est fait', 'Ta suggestion est maintenant dans Sweep. Vois la réponse.'],
        'es' => ['Lo pediste, está hecho', 'Tu sugerencia ya está en Sweep. Mira la respuesta.']]],
    'weekOne' => ['ch' => 'push', 'group' => 'progress', 'url' => '#dashboard', 'text' => [
        'en' => ['One week of Sweep', 'What is missing for you? One tap to tell us.'],
        'fr' => ['Une semaine de Sweep', 'Qu’est-ce qui te manque ? Un toucher pour nous le dire.'],
        'es' => ['Una semana de Sweep', '¿Qué te falta? Un toque para decírnoslo.']]],
    'featureDiscover' => ['ch' => 'push', 'group' => 'progress', 'url' => '{feature_link}', 'text' => [
        'en' => ['Have you tried {feature}?', '{feature_button}: it takes a minute.'],
        'fr' => ['As-tu essayé {feature} ?', '{feature_button} : ça prend une minute.'],
        'es' => ['¿Ya probaste {feature}?', '{feature_button}: toma un minuto.']]],
    // Sweep's news: once a month at most, written and sent by Mateo from Admin › Emails
    'news' => ['ch' => 'only', 'group' => 'news', 'url' => '#dashboard',
        'name' => ['en' => 'Sweep news', 'fr' => 'Nouveautés de Sweep', 'es' => 'Novedades de Sweep'],
        'when' => ['en' => 'Sent by hand from this page, once a month at most', 'fr' => 'Envoyée à la main depuis cette page, une fois par mois au plus', 'es' => 'Enviada a mano desde esta página, una vez al mes como máximo'],
        'text' => ['en' => ['', ''], 'fr' => ['', ''], 'es' => ['', '']]],
];
