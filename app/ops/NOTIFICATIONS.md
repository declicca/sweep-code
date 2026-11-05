# Tout ce que Sweep envoie à un trader (brief 02, partie 10, 14 oct. 2026)

La liste complète des notifications et des courriels : déclencheur, canal, fréquence maximale. À tenir à jour à chaque
nouveau type (code : `notify/listeners.php` pour les types de la cloche, `push/web-push.php`, `mail/mail-auto.php` et `mail/mail-auto-texts.php`).

## La règle : 2 notifications par jour au plus

- **Au plus 2 notifications par jour (jour de New York) qui alertent le trader**, tous types confondus, célébrations
  comprises (`Notify::DAILY_MAX`, `notify/notify.php` ; `config.php` › `notifications.daily_limit` peut seulement baisser).
- **Au-delà**, une notification d'information arrive **discrète** : dans la liste de la cloche, déjà lue, sans pastille,
  sans toast ni push (`quiet`). Un **rappel** (plan, revue, streak, semaine, intention, Wrapped) n'est **pas envoyé** : il
  attend le prochain passage (la semaine, le lendemain à son heure ; les autres passent leur tour).
- **Exception : les alertes prop firm** (`prop_alerts` : la limite du jour ou le drawdown d'un compte à 75 % puis 100 %,
  les règles d'une firme qui changent). Elles répondent au trade que le trader vient d'enregistrer, ou à ses comptes ; jamais
  plafonnées ni comptées (brief 03, étape 3). Jamais sur le téléphone.
- **Sur le téléphone** (push) : les rappels de la cloche (plan, revue, semaine, streak), donc dans les mêmes 2 par jour, plus
  les messages automatiques (section 5). Jamais pendant la séance (9 h 30 – 16 h ET) sauf les alertes de compte, jamais avant
  l'heure choisie par le trader, jamais quand il est dans l'app. **Heures calmes à l'heure du téléphone** (5 nov.) : rien de
  21 h à 7 h sur l'horloge de l'appareil (fuseau envoyé par l'app), sauf le rappel du plan (son heure est choisie) et les
  alertes de compte.

## 1. La cloche (dans l'app) — `notifications`

| Type | Catégorie | Déclencheur | Au plus |
|---|---|---|---|
| `g_plan` « Ton plan du jour t'attend. » (sur le téléphone, depuis le 5 nov., la ligne nomme l'annonce importante du jour : « Annonce importante aujourd’hui : CPI à 8 h 30. Prévois-la dans ton plan. ») | Séries | Jour de marché, de l'heure du trader (8 h 45 par défaut, 7 h à 9 h 15) à 9 h 30 ET ; plan pas fait ; Sweep utilisé dans les 14 jours | 1 / jour · **push** |
| `g_review` « 60 secondes pour balayer ta journée. » | Séries | Jour de marché, de l'heure du trader (16 h 30 par défaut, 16 h à 20 h 45) à 21 h ; revue pas faite ; un trade ou un plan | 1 / jour · **push** |
| `g_weekly` « Ta semaine est prête. » | Accomplissements | Le bilan de la semaine prêt (dernier jour de bourse, après sa revue ou 17 h), de l'heure du trader (17 h par défaut) à 21 h, jusqu'au dimanche ; pas déjà ouvert | 1 / semaine · **push** |
| `g_streak` « Ton streak de N jours est encore sauvable. » | Séries | Jour de marché, dès 19 h 30 (21 h avant le 5 nov.), streak de 3 jours et plus pas encore validé | 1 / jour · **push** |
| `g_intention` « Nouvelles missions demain. » | Accomplissements | Dimanche dès 18 h, une revue de la semaine existe | 1 / semaine |
| `g_wrapped` « Ton Wrapped du mois est prêt. » | Accomplissements | Le 1er du mois, hors séance, le Wrapped du mois passé existe | 1 / mois |
| `trial_ending` | Compte et données | Essai Pro (ou accès anticipé) : 10 puis 2 jours avant la fin, sans abonnement | 2 en tout |
| `wow_journal`, `wow_plans`, `wow_reviews`, `wow_days` | Accomplissements (célébration dès 100) | Une étape franchie (10, 50, 100… trades journalisés, plans, revues ; 30, 100, 365 jours) ; au premier passage, les étapes déjà franchies sont notées sans envoi | 1 par étape |
| `wow_clean_week` | Accomplissements (célébration) | La première semaine verrouillée de 3 trades et plus, tous dans le plan | 1 en tout |
| `wow_best_month` | Accomplissements (célébration) | Le 1er : le mois passé est le meilleur mois de discipline (mois de 10 jours de marché et plus). **Corrigé le 14 oct.** : avant, chaque mois avec des données était annoncé « meilleur » | 1 / mois |
| `money_month` « La réalité du mois » | Nouveautés (célébration) | Le 1er dès 8 h, s'il s'est passé quelque chose dans Mon argent | 1 / mois |
| `chart_ready` | Nouveautés | Les bougies d'une séance prêtes (tâche `chart`, toutes les heures, hors séance), dans les 48 h | 1 / séance |
| `fb_planned`, `fb_in_progress`, `fb_declined`, `fb_shipped` (célébration) | Nouveautés | Un administrateur change le statut d'une suggestion du trader | 1 par statut |
| `buddy_invite`, `buddy_cheer`, `buddy_swept` | Accomplissements | Un buddy invite, encourage, balaie sa journée | invitation : 1 par buddy ; encouragement et journée balayée : 1 / jour |
| `sync_found` | Compte et données | Un add-on de synchro trouve de nouveaux comptes | 1 / plateforme / jour |
| `prop_limit` (`prop_dll75`, `prop_dll100`, `prop_dd75`, `prop_dd100`) | Alertes prop firm | L'app, après un trade : limite du jour ou drawdown à 75 % puis 100 % | 1 par compte, sorte et niveau / séance · **hors plafond** |
| `g_lock` « Journée fermée : ta limite est atteinte. » (1er nov., brief avance 4) | Alertes prop firm | Serveur (`recomputeDay`), au moment où la perte max ou les trades max du jour sont atteints (trade saisi, copié ou synchronisé) | 1 / séance · **hors plafond** · **push** (`lock`, sans heure) |
| `rules_changed` | Alertes prop firm | Les règles d'une firme changent (vérification du lundi) | 1 par compte et version · **hors plafond** |
| `test_normal`, `test_celebration` | — | Bouton de test d'un administrateur | à la demande |

Chaque catégorie se coupe dans Réglages › Notifications. Les célébrations s'affichent en toast (une par ouverture de l'app).

## 2. Le téléphone (push) — `push/web-push.php`

- **Activer** : Réglages › Notifications › « Sur cet appareil » › « Activer les notifications ». Sur iPhone (iOS 16.4 et
  plus), seulement depuis Sweep ajouté à l'écran d'accueil ; l'app explique comment. Android et ordinateur : tout navigateur
  qui le permet.
- **4 interrupteurs** (5 nov.) : Ma routine (plan, revue, semaine, streak ; les heures des 3 rappels dessous), Mes comptes
  (Gardien, journée fermée, payout possible, objectif atteint), Mes progrès, Nouveautés et abonnement (`WP_GROUPS`).
- **Les rappels** : `g_plan`, `g_review`, `g_weekly`, `g_streak` (tableau ci-dessus), l'heure des trois premiers au choix
- **La journée fermée** : `g_lock` (push `lock`), envoyée au moment du verrou, pendant la séance aussi ; son interrupteur, sans heure
  (heure de New York, par quart d'heure ; l'heure vaut aussi pour la cloche). Envoyés par la tâche `game` (toutes les
  15 minutes) seulement, pas quand le trader ouvre l'app. Texte de la cloche, dans la langue de l'appareil ; un toucher ouvre
  Aujourd'hui.
- **Clés** : `sweep-private/push-config.php`, faites une fois sur le serveur par `ops/push-keys.php` (jamais dans git).
  Sans ce fichier, le bloc n'apparaît pas et rien ne part. Admin › Santé : « Notifications sur le téléphone ».
- Un appareil que le service push dit disparu (404, 410) est oublié ; 10 appareils au plus par trader.

## 3. Les courriels de Sweep — `notify/mail.php`

| Courriel | À qui | Déclencheur | Au plus |
|---|---|---|---|
| Réinitialisation du mot de passe | trader | « Mot de passe oublié » ; lien valable 1 h | 3 / heure / adresse |
| « Ta semaine du … » | trader | Dès 17 h 30 ET le dernier jour de bourse, si le bilan n'a pas été ouvert dans l'app ; lien d'arrêt dans le courriel | 1 / semaine |
| Feedback reçu | support | Chaque suggestion envoyée | 10 / jour / trader |
| Tâche planifiée en échec | support | Une tâche reste rouge plus d'un cycle | 1 par incident |
| Préréglages pas vérifiés depuis 8 jours | support | Vérification des firmes en retard | 1 / jour |
| Nouvelle erreur de l'app | support | Une erreur pas vue depuis 7 jours | 10 / jour |

## 4. Les courriels automatiques — `mail/mail-auto.php`

Envoyés par notre serveur (courriels maison, étape 5, 4 nov. ; Loops retiré). Chaque événement a son courriel dans
**Admin › Courriels › Automatisations** : texte EN / FR / ES modifiable, allumé ou éteint, un test, ses statistiques.
Les textes de départ sont dans `mail/mail-auto-texts.php` (posés une fois, jamais réécrits ensuite). Marketing : respecte la
désinscription et le plafond par heure ; sur le compte (abonnement, paiement refusé, parrainage) : envoyé à tous.
Éteints au départ : `profileCompleted`, `firstAccountAdded`, `firstPlanSaved`, `firstTradeLogged` (le soir du jour 1 les couvre).

| Événement | Déclencheur | Au plus |
|---|---|---|
| `signedUp`, `profileCompleted`, `firstAccountAdded`, `firstPlanSaved`, `firstTradeLogged`, `firstPayoutLogged` | L'action dans l'app (`firstPlanSaved` : le premier plan enregistré, ajouté le 27 oct. ; un trader qui avait déjà des plans est marqué, jamais prévenu) | 1 en tout chacun |
| `tradesMilestone` (10, 50, 100) | Le 10e, 50e, 100e trade | 1 par étape |
| `subscriptionStarted`, `paymentFailed`, `subscriptionCanceled`, `referralRewarded` | Stripe, le parrainage | à chaque fois |
| `inactive3d`, `inactive7d`, `inactive14d`, `inactive30d` | 3, 7, 14, 30 jours sans revenir dans l'app (dès 7 h 30 ET) ; **`inactive3d` ajouté le 14 oct.** | 1 par absence et par étape ; un retour recommence le compte |
| `proTrialDaysLeft` (30, 10, 3), `proTrialEnded` | La fin de l'essai Pro, sans paiement (jamais l'équipe Discord ni un trader qui paie) | 1 par étape |

Le passage du jour envoie au plus une absence et une étape d'essai par trader.

### Le soir du jour 1 : « Ta séance de demain en 30 secondes » (brief activation, étape E, 27 oct.)

L'automatisation `day1Evening` : **18 h 30 heure de New York** le jour de l'inscription (ou le lendemain si l'inscription
a lieu après 18 h), seulement si aucun plan n'est enregistré ; abandonnée 6 h après l'heure prévue.
Le trader qui a déjà fait son plan ne reçoit rien. Ton : une seule action, aucun reproche.

- **FR** — Objet : « Ta séance de demain en 30 secondes » · Texte : « Salut {first}, prépare ta séance de demain ce
  soir : ton biais (haussier ou baissier), tes niveaux et ta perte max du jour. 30 secondes, et demain matin tu sais exactement ce que tu
  risques. » · Bouton : « Faire mon plan »
- **EN** — Subject: “Tomorrow’s session in 30 seconds” · Text: “Hi {first}, get tomorrow’s session ready tonight: your
  bias (bullish or bearish), your levels and your max loss for the day. 30 seconds, and tomorrow morning you know exactly what you risk.” ·
  Button: “Make my plan”
- **ES** — Asunto: «Tu sesión de mañana en 30 segundos» · Texto: «Hola {first}, prepara esta noche tu sesión de mañana:
  tu sesgo (alcista o bajista), tus niveles y tu pérdida máxima del día. 30 segundos, y mañana por la mañana sabes exactamente lo que
  arriesgas.» · Botón: «Hacer mi plan»

Le lien du bouton : `https://app.makeitsweep.com/#dashboard` (« Faire mon plan » est le bouton bleu de la routine le soir).

### Le retour doux (3 et 7 jours)

Automatisations `inactive3d` et `inactive7d`. Un seul courriel par absence et par étape (Sweep s'en charge).
Ton : aucune culpabilité, pas de chiffre de pertes, une seule action.

- **FR, 3 jours** — Objet : « Ta discipline t'attend » · Texte : « Salut {first}, ta discipline t'attend : reprends là
  où tu étais. Ton prochain plan prend 30 secondes. » · Bouton : « Ouvrir Sweep »
- **FR, 7 jours** — Objet : « Reprends là où tu étais » · Texte : « Salut {first}, une semaine sans journal, ça arrive.
  Rien n'est perdu : tes trades, tes comptes et ta progression t'attendent. Une revue suffit pour repartir. » · Bouton :
  « Reprendre »
- **EN, 3 days** — Subject: “Your discipline is waiting” · Text: “Hi {first}, your discipline is waiting: pick up where
  you left off. Your next plan takes 30 seconds.” · Button: “Open Sweep”
- **EN, 7 days** — Subject: “Pick up where you left off” · Text: “Hi {first}, a week without journaling happens. Nothing
  is lost: your trades, your accounts and your progress are waiting. One review is enough to get going again.” · Button:
  “Get back to it”
- **ES, 3 días** — Asunto: «Tu disciplina te espera» · Texto: «Hola {first}, tu disciplina te espera: retoma donde lo
  dejaste. Tu próximo plan toma 30 segundos.» · Botón: «Abrir Sweep»
- **ES, 7 días** — Asunto: «Retoma donde lo dejaste» · Texto: «Hola {first}, una semana sin diario pasa. Nada se
  pierde: tus operaciones, tus cuentas y tu progreso te esperan. Basta una revisión para volver.» · Botón: «Retomar»

## 5. Dans l'app seulement (pas des notifications)

Toasts de confirmation et « Annuler » ; célébrations du jeu (une fenêtre par visite pour les grands moments, 2 petits toasts
au plus puis « N nouveautés ») ; bandeau « nouvelle version » ; bannière et rappel de fin d'essai ; « Déconnecté ». Ils
apparaissent seulement quand le trader est dans l'app.

## 6. Le téléphone d'abord (5 nov., brief « Notifications ») — `push/push-auto.php`

Chaque message automatique a trois sorties : le téléphone, le courriel (même clé, section 4) et, pour une alerte de compte,
la cloche. Chaque notification part **éteinte** : Admin › Courriels › une automatisation › « Sur le téléphone » (texte EN / FR /
ES, interrupteur, chiffres sur 30 jours : envoyées, ouvertes, courriels de relais partis, courriels évités).

| Message | Canal | Interrupteur |
|---|---|---|
| `day1Evening`, `inactive3d`, `inactive7d`, `referralRewarded` | téléphone d'abord, courriel 24 h plus tard s'il n'a pas été ouvert et que le trader n'est pas revenu | Ma routine / Mes progrès |
| `firstTradeLogged`, `tradesMilestone`, `firstPayoutLogged` | idem, seulement quand le trader n'est pas dans l'app (dans l'app : le courriel comme avant) | Mes progrès |
| `proTrialDaysLeft`, `proTrialEnded`, `subscriptionStarted`, `paymentFailed` | téléphone et courriel en même temps | Nouveautés et abonnement |
| `inactive14d`, `inactive30d`, `subscriptionCanceled`, `signedUp`, `phoneInstall`… | courriel seulement | — |
| `payoutReady` (une fois par cycle de payout), `goalReached` (avec ce qui reste), `evalPassed` (une fois par compte) | téléphone + cloche (`pa_alert`, alertes prop firm), pendant la séance aussi, hors des 5 de la semaine | Mes comptes |
| `feedbackShipped` « Tu l'as demandé, c'est fait » | téléphone et courriel en même temps | Mes progrès |
| `weekOne` « Une semaine de Sweep », `featureDiscover` (fonction à découvrir) | téléphone d'abord, courriel 24 h plus tard (le courriel allumé déclenche l'envoi) | Mes progrès |
| `nps30`, `months3` (questions longues) | courriel seulement | — |
| `news` la nouveauté du mois | téléphone seulement, envoyée à la main par Mateo, une fois par 28 jours au plus | Nouveautés et abonnement |

Garde-fous (le téléphone seulement) : 2 par jour avec les rappels de la cloche (sinon le lendemain, 2 fois au plus, puis le
courriel), **5 par semaine** (alertes de compte à part), heures calmes et séance comme plus haut, **fatigue** (les 4 dernières
d'un groupe ignorées : 1 par semaine au plus jusqu'à une ouverture), **30 jours d'absence** : plus rien. Une notification qui ne
part pas libère son courriel tout de suite. Ouverture : le service worker appelle `api/p/o/<jeton>`. Envoi : `mail/send-cron.php`
(chaque minute), aucune nouvelle ligne cron.

**Sweep sur le téléphone** : code QR sur ordinateur (Réglages › Notifications, et une ligne de la routine une fois qu'un trade
est journalisé, « Plus tard » = 7 jours), qui ouvre `/?i=qr` et montre l'installation sur le téléphone ; courriel `phoneInstall`
au jour 3 (un trade, aucun téléphone abonné ; éteint au départ) ; sur téléphone, à la première alerte du Gardien ou première
journée fermée vue dans l'app, « Reçois cette alerte sur ton téléphone » (une fois chacune, jamais entre le premier trade et la
revue, jamais à moins de 7 jours d'une autre proposition). Admin › Métriques : la part des traders actifs avec l'app installée
et avec les notifications.

