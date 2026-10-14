# Tout ce que Sweep envoie à un trader (brief 02, partie 10, 14 oct. 2026)

La liste complète des notifications et des courriels : déclencheur, canal, fréquence maximale. À tenir à jour à chaque
nouveau type (code : `notify/listeners.php` pour les types de la cloche, `push/web-push.php`, `loops/loops.php`).

## La règle : 2 notifications par jour au plus

- **Au plus 2 notifications par jour (jour de New York) qui alertent le trader**, tous types confondus, célébrations
  comprises (`Notify::DAILY_MAX`, `notify/notify.php` ; `config.php` › `notifications.daily_limit` peut seulement baisser).
- **Au-delà**, une notification d'information arrive **discrète** : dans la liste de la cloche, déjà lue, sans pastille,
  sans toast ni push (`quiet`). Un **rappel** (plan, revue, streak, semaine, intention, Wrapped) n'est **pas envoyé** : il
  attend le prochain passage (la semaine, le lendemain à son heure ; les autres passent leur tour).
- **Exception : les alertes prop firm** (`prop_alerts` : la limite du jour ou le drawdown d'un compte à 75 % puis 100 %,
  les règles d'une firme qui changent). Elles répondent au trade que le trader vient d'enregistrer, ou à ses comptes ; jamais
  plafonnées ni comptées (brief 03, étape 3). Jamais sur le téléphone.
- **Sur le téléphone** (push) : seulement 3 rappels, ceux de la cloche, donc dans les mêmes 2 par jour. Jamais pendant la
  séance (9 h 30 – 16 h ET), jamais avant l'heure choisie par le trader, jamais quand il est dans l'app.

## 1. La cloche (dans l'app) — `notifications`

| Type | Catégorie | Déclencheur | Au plus |
|---|---|---|---|
| `g_plan` « Ton plan du jour t'attend. » | Séries | Jour de marché, de l'heure du trader (8 h 45 par défaut, 7 h à 9 h 15) à 9 h 30 ET ; plan pas fait ; Sweep utilisé dans les 14 jours | 1 / jour · **push** |
| `g_review` « 60 secondes pour balayer ta journée. » | Séries | Jour de marché, de l'heure du trader (16 h 30 par défaut, 16 h à 20 h 45) à 21 h ; revue pas faite ; un trade ou un plan | 1 / jour · **push** |
| `g_weekly` « Ta semaine est prête. » | Accomplissements | Le bilan de la semaine prêt (dernier jour de bourse, après sa revue ou 17 h), de l'heure du trader (17 h par défaut) à 21 h, jusqu'au dimanche ; pas déjà ouvert | 1 / semaine · **push** |
| `g_streak` « Ton streak de N jours est encore sauvable. » | Séries | Jour de marché, dès 21 h, streak de 3 jours et plus pas encore validé | 1 / jour |
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
| `rules_changed` | Alertes prop firm | Les règles d'une firme changent (vérification du lundi) | 1 par compte et version · **hors plafond** |
| `test_normal`, `test_celebration` | — | Bouton de test d'un administrateur | à la demande |

Chaque catégorie se coupe dans Réglages › Notifications. Les célébrations s'affichent en toast (une par ouverture de l'app).

## 2. Le téléphone (push) — `push/web-push.php`

- **Activer** : Réglages › Notifications › « Sur cet appareil » › « Activer les notifications ». Sur iPhone (iOS 16.4 et
  plus), seulement depuis Sweep ajouté à l'écran d'accueil ; l'app explique comment. Android et ordinateur : tout navigateur
  qui le permet.
- **Les 3 rappels** : `g_plan`, `g_review`, `g_weekly` (tableau ci-dessus), chacun avec son interrupteur et son heure
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

## 4. Les courriels automatiques (Loops) — `loops/`

Sweep envoie des événements ; les courriels se rédigent et s'activent dans Loops (sans clé, rien ne part).

| Événement | Déclencheur | Au plus |
|---|---|---|
| `signedUp`, `profileCompleted`, `firstAccountAdded`, `firstTradeLogged`, `firstPayoutLogged` | L'action dans l'app | 1 en tout chacun |
| `tradesMilestone` (10, 50, 100) | Le 10e, 50e, 100e trade | 1 par étape |
| `subscriptionStarted`, `paymentFailed`, `subscriptionCanceled`, `referralRewarded` | Stripe, le parrainage | à chaque fois |
| `inactive3d`, `inactive7d`, `inactive14d`, `inactive30d` | 3, 7, 14, 30 jours sans revenir dans l'app (dès 7 h 30 ET) ; **`inactive3d` ajouté le 14 oct.** | 1 par absence et par étape ; un retour recommence le compte |
| `proTrialDaysLeft` (30, 10, 3), `proTrialEnded` | La fin de l'essai Pro, sans paiement (jamais l'équipe Discord ni un trader qui paie) | 1 par étape |

Le passage du jour envoie au plus une absence et une étape d'essai par trader.

### Le retour doux (3 et 7 jours) : texte à mettre dans Loops

Déclencheurs dans Loops : `inactive3d` et `inactive7d`. Un seul courriel par absence et par étape (Sweep s'en charge).
Ton : aucune culpabilité, pas de chiffre de pertes, une seule action.

- **FR, 3 jours** — Objet : « Ta discipline t'attend » · Texte : « Salut {firstName}, ta discipline t'attend : reprends là
  où tu étais. Ton prochain plan prend 30 secondes. » · Bouton : « Ouvrir Sweep »
- **FR, 7 jours** — Objet : « Reprends là où tu étais » · Texte : « Salut {firstName}, une semaine sans journal, ça arrive.
  Rien n'est perdu : tes trades, tes comptes et ta progression t'attendent. Une revue suffit pour repartir. » · Bouton :
  « Reprendre »
- **EN, 3 days** — Subject: “Your discipline is waiting” · Text: “Hi {firstName}, your discipline is waiting: pick up where
  you left off. Your next plan takes 30 seconds.” · Button: “Open Sweep”
- **EN, 7 days** — Subject: “Pick up where you left off” · Text: “Hi {firstName}, a week without journaling happens. Nothing
  is lost: your trades, your accounts and your progress are waiting. One review is enough to get going again.” · Button:
  “Get back to it”
- **ES, 3 días** — Asunto: «Tu disciplina te espera» · Texto: «Hola {firstName}, tu disciplina te espera: retoma donde lo
  dejaste. Tu próximo plan toma 30 segundos.» · Botón: «Abrir Sweep»
- **ES, 7 días** — Asunto: «Retoma donde lo dejaste» · Texto: «Hola {firstName}, una semana sin diario pasa. Nada se
  pierde: tus operaciones, tus cuentas y tu progreso te esperan. Basta una revisión para volver.» · Botón: «Retomar»

## 5. Dans l'app seulement (pas des notifications)

Toasts de confirmation et « Annuler » ; célébrations du jeu (une fenêtre par visite pour les grands moments, 2 petits toasts
au plus puis « N nouveautés ») ; bandeau « nouvelle version » ; bannière et rappel de fin d'essai ; « Déconnecté ». Ils
apparaissent seulement quand le trader est dans l'app.
