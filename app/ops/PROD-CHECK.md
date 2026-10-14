# Liste de vérification production (brief 02, étape 0)

À refaire après un changement de serveur, de DNS ou de configuration. État au **12 octobre 2026**. Vérifications en ligne : au plus 2 requêtes à la fois, une pause entre elles (le pare-feu du serveur bloque l'IP sinon).

## 0. Tâches planifiées

- **Constaté le 12 oct.** : aucune tâche de Sweep n'était installée (la crontab du compte ne contenait qu'une ligne WordPress de lacstmajo.ca). Pas de sauvegarde, pas de rappels, pas de courriel « Ta semaine », pas de vérification hebdomadaire des firmes.
- **Fait le 12 oct.** : les 5 lignes de `ops/CRON.md` ajoutées (copie de l'ancienne crontab : `~/crontab-backup-2026-10-12.txt`).
- `MAILTO=""` : cPanel n'envoie pas la sortie des tâches. Les échecs se voient dans **Admin › Santé**, et une tâche rouge depuis plus d'un cycle envoie un courriel à l'adresse de support.
- **À vérifier** : Admin › Santé, les 5 lignes en bleu après leur premier passage (le jeu dans le quart d'heure, la sauvegarde après 3 h 30, les firmes et le test de restauration le lundi).

## 1. Courriel « mot de passe oublié » (3 langues, pas en indésirables)

- **Constaté le 12 oct.** (DNS publics, 1.1.1.1 et 8.8.8.8) : DNS chez Cloudflare, **aucun MX, aucun SPF, aucune DKIM**, pas de `mail.makeitsweep.com`, avec pourtant un DMARC `p=quarantine`. La boîte hello@makeitsweep.com (sur le serveur cPanel) ne pouvait rien recevoir, et les courriels de l'app partaient sans authentification.
- **Fait le 12 oct.** (Cloudflare, en « DNS only ») : `A mail → 178.93.238.40`, `MX @ → mail.makeitsweep.com (10)`, `TXT @ → v=spf1 +a +mx ip4:178.93.238.40 ~all`, `TXT default._domainkey →` la clé DKIM de cPanel. cPanel → Email Deliverability : SPF et DKIM « Valid » ; vérifié depuis l'extérieur (clé DKIM identique caractère pour caractère).
- **À faire** : « Mot de passe oublié » vers une adresse Gmail, l'app en FR, puis EN, puis ES ; dans Gmail, ⋮ → Afficher l'original : `SPF: PASS`, `DKIM: PASS`, `DMARC: PASS`, et le courriel dans la boîte de réception. Un courriel envoyé à hello@makeitsweep.com arrive dans le webmail. Le lendemain : certificat de `mail.makeitsweep.com` dans cPanel → SSL/TLS Status (AutoSSL).
- Facultatif : le DMARC envoie ses rapports à `dmarc_rua@onsecureserver.net` (GoDaddy, sans doute un reste de l'achat du domaine) ; `rua=mailto:hello@makeitsweep.com` pour les recevoir.
- Admin › Santé dit si l'envoi passe par la boîte (SMTP) ou par `mail()` de PHP.

## 2. Webhooks Stripe

- Adresse : `https://app.makeitsweep.com/api/billing/webhook` (signature vérifiée ; sans signature : refusée).
- Admin › Santé : Stripe et « Secret du webhook Stripe » réglés ou manquants, mode réel ou test.
- **À faire** (Stripe → Développeurs → Webhooks, en mode test) : envoyer les événements d'abonnement créé, renouvelé (facture payée), annulé et paiement échoué ; chaque envoi doit répondre `200`, et l'abonnement du compte de test changer dans Admin › Traders.
- **Vérifié en local** (brief 02, partie 13, 13 oct.) : `tests/billing_test.php` (le parcours complet, Stripe remplacé par un enregistreur, webhooks signés avec un secret de test) et `tests/e2e_billing.py` (la vraie route publique du webhook : signature refusée, rejouée, abonnement créé puis supprimé ; la carte du jour 50 et la fenêtre du retour à Free dans le navigateur).
- **Parcours en mode test de Stripe, sur le serveur** (clés `sk_test_…` et `whsec_…` du mode test dans `sweep-private/billing-config.php`, ton compte de test dans `test_users` : la facturation ne s'allume que pour lui) :
  1. Page Forfaits (`#plan`, connecté en administrateur) › « Vérification de Stripe » : tout en vert (clé, secret du webhook, prix, coupon).
  2. Avec le compte de test : « Voir les forfaits » → Pro → carte `4242 4242 4242 4242` → retour dans l'app : « Tu es sur Pro » ; Stripe → Webhooks : `checkout.session.completed` et `invoice.paid` à `200`.
  3. « Gérer la facturation » (portail Stripe) → annuler → l'app dit « Pro se termine le … » ; puis, dans Stripe, annuler tout de suite → l'app repasse à Free et la fenêtre « Ton abonnement Pro est terminé » s'ouvre une fois.
  4. Paiement échoué : s'abonner avec la carte `4000 0000 0000 0341`, puis déclencher la facture → bannière « Ton dernier paiement n’a pas passé » ; le forfait reste 7 jours.
  5. Parrainage : le lien d'invitation du compte de test, une inscription depuis un autre appareil (pas la même connexion) → le filleul est en Elite 14 jours ; même connexion → « à vérifier » dans Admin, approuvé → Elite 14 jours.
  6. Feedback : un message depuis la page Feedback → il arrive dans Admin › Feedback et dans la boîte de soutien.

## 3. Restauration d'une sauvegarde

- `sweep-private/backup-config.php` n'existait pas : aucune sauvegarde n'avait jamais été faite. **Créé le 12 oct.** (phrase secrète gardée hors du serveur) ; sauvegarde lancée à la main : OK.
- Le test de restauration (`ops/restore-test.php`, le lundi à 6 h) déchiffre la dernière sauvegarde dans un fichier temporaire, vérifie son intégrité et qu'elle contient les mêmes traders que la base en production, sans jamais toucher à la base en production. Il n'y a pas d'environnement de test en ligne (choix du 9 oct. : local seulement).
- **À faire** : Admin › Santé, ligne « Test de restauration » en bleu après le premier lundi ; prévoir une copie hors du serveur (ligne `s3` de `backup-config.php`, Backblaze B2 ou Cloudflare R2).

## 4. Sweep AI

- `sweep-private/ai-config.php` présent. Admin › Santé : clé réglée ou manquante, budget quotidien global, limite par trader et par jour (avec la facturation, celle de chaque forfait : « Free 3 · Pro 50 · Elite 200 »), dépensé aujourd'hui (jamais la clé elle-même).
- Budget atteint : l'IA répond « budget » (503) ; ce que voit le trader : « Sweep AI avec la vraie clé » ci-dessous.

## Sweep AI avec la vraie clé (brief 02, partie 9)

- **Vérifié en local** (sans clé, réponses simulées : `SWEEP_AI_CHAT_MOCK`) : `tests/ai_chat_test.php` (une réponse et l'écran à ouvrir ; « d'après N trades » compté par Sweep ; le quota du forfait, sa remise à minuit New York ; une panne rend la question ; le budget du jour atteint ; l'IA éteinte) et `tests/e2e_ai.py` (la recherche, la bulle, l'aide quand l'IA ne répond pas).
- **À faire sur le serveur, avec un compte de test Pro ou Elite** (son quota d'IA est utilisé, environ 0,02 $ ; Free n'a que 3 questions par jour : le script s'arrête s'il ne reste pas 20 actions IA) :
  `/usr/local/bin/php /home/matnsabc/app.makeitsweep.com/ops/ai-check.php <nom du compte de test> fr`
  Le script pose 20 questions types de traders (comment ajouter un payout, pourquoi mon compte est rouge, mes pires heures…), une à la fois, et affiche le temps de réponse, la réponse, l'écran proposé, les données citées et ce qu'une bonne réponse doit contenir. Noter chaque réponse 0 (fausse), 1 (en partie) ou 2 (juste) ; un chiffre inventé = 0. Le résumé final donne la médiane et le temps le plus long.
- Le budget du jour atteint se voit dans Admin › Santé (« Clé Sweep AI » : dépensé sur le budget) ; la bulle dit alors « Sweep AI est en pause pour aujourd'hui » et propose les pages et l'aide de la question.


## Notifications sur le téléphone (brief 02, partie 10)

- **Vérifié en local** (clés de test, messages écrits dans un fichier : `SWEEP_PUSH_MOCK`) : `tests/push_test.php` (le chiffrement redonne l'exemple de la RFC 8291 octet pour octet, la signature VAPID, les seules adresses des services push, les heures, 2 notifications par jour, le message ouvert avec la clé du téléphone) et `tests/e2e_push.py` (Réglages, `/sw.js`, l'heure choisie, le message dans la langue du trader, « Désactiver », l'iPhone dans Safari).
- **À faire sur le serveur, une fois** : `/usr/local/bin/php /home/matnsabc/app.makeitsweep.com/ops/push-keys.php` écrit `sweep-private/push-config.php` (lisible par ce seul utilisateur) et affiche seulement la clé publique. Admin › Santé : « Notifications sur le téléphone » passe à « Réglé ». Ne pas relancer avec `--force` : chaque téléphone devrait réactiver ses notifications.
- **Puis sur un vrai téléphone** : Android (Chrome) et iPhone (iOS 16.4+, Sweep ajouté à l'écran d'accueil, ouvert depuis son icône) : Réglages › Notifications › « Activer les notifications », mettre le rappel du plan au quart d'heure qui suit, attendre le passage de la tâche `game` : la notification arrive, un toucher ouvre Aujourd'hui. La tâche `game` (toutes les 15 min) envoie les rappels : rien de plus à installer.

## Partage (brief 02, partie 12)

- **Vérifié en local** : `tests/e2e_share.py` (carte Discipline d'abord, prénom, sans dollar, l'image et ses tailles, la feuille de partage avec le fichier ; la page d'un lien et ses balises ; le profil public) et `tests/profile_test.php`.
- **À faire en ligne, sur un vrai téléphone** : iPhone (Safari et Sweep ajouté à l'écran d'accueil) et Android (Chrome) : Stats › « Partager mes stats » › « Partager » : la feuille de partage s'ouvre avec l'image (sinon, l'image est téléchargée).
- **Les aperçus** : « Créer un lien » sur une carte, puis coller le lien dans un salon Discord, un message X (brouillon) et iMessage : le titre (« Ma discipline · octobre 2026 »), la phrase et l'image large doivent paraître. Puis Réglages › Profil › « Profil public de discipline » : le lien collé montre « Prénom · Discipline sur Sweep » et la phrase des 4 semaines.
