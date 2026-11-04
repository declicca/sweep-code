# Tâches planifiées de Sweep (cPanel → Cron Jobs)

Brief 02, étape 0. Six tâches tournent en arrière-plan. Chacune écrit sa dernière exécution dans la table `cron_runs` (début, fin, durée, succès ou erreur, résumé) : **Admin › Santé** montre une ligne par tâche, en bleu (OK), or (en retard : aucun succès depuis deux cycles + 10 min) ou rouge (échec, bloquée, ou jamais exécutée). Une tâche rouge depuis plus d'un cycle envoie **un seul** courriel à l'adresse de support (`support_email` de `config.php`, sinon hello@makeitsweep.com), puis plus rien tant qu'elle n'est pas revenue à la normale. La vérification passe à la fin de la tâche du jeu (toutes les 15 min) et, au plus une fois par heure, pendant l'utilisation de l'app (au cas où c'est la tâche du jeu qui s'est arrêtée).

Dans cPanel → **Cron Jobs**, mets ton courriel dans « Cron Email », puis ajoute ces 6 lignes (la commande exacte de chaque tâche est aussi dans Admin › Santé, « Ligne cPanel ») :

| Tâche | Fréquence | Ligne cPanel (fréquence + commande) |
|---|---|---|
| Jeu, rappels, courriel « Ta semaine » (`game`) | toutes les 15 min | `*/15 * * * *` `/usr/local/bin/php /home/matnsabc/app.makeitsweep.com/game/cron.php >/dev/null 2>&1` |
| Graphiques des trades (`chart`) | toutes les heures | `0 * * * *` `/usr/local/bin/php /home/matnsabc/app.makeitsweep.com/chart/cron.php >/dev/null 2>&1` |
| Vérification des règles des firmes (`presets`) | le lundi à 5 h | `0 5 * * 1` `/usr/local/bin/php /home/matnsabc/app.makeitsweep.com/presets/cron.php >/dev/null 2>&1` |
| Sauvegarde (`backup`) | chaque jour à 3 h 30 | `30 3 * * *` `/usr/local/bin/php /home/matnsabc/app.makeitsweep.com/ops/backup.php` |
| Test de restauration (`restore_test`) | le lundi à 6 h | `0 6 * * 1` `/usr/local/bin/php /home/matnsabc/app.makeitsweep.com/ops/restore-test.php` |
| Courriels : campagnes et automatiques (`mail`) | chaque minute | `* * * * *` `/usr/local/bin/php /home/matnsabc/app.makeitsweep.com/mail/send-cron.php >/dev/null 2>&1` |

Les heures sont celles du serveur. La tâche `mail` envoie la file chaque minute ; les courriels automatiques du jour (absences, essai Pro) se préparent une fois par jour, dès 7 h 30 à New York (`America/New_York`, heure d'été comprise), et le soir du premier jour à 18 h 30 à New York : peu importe le fuseau du serveur (étape 5 des courriels maison : l'ancienne tâche `emails`, `loops/cron.php`, est retirée). La sauvegarde et le test de restauration gardent leur sortie : cPanel l'envoie par courriel (la sauvegarde n'écrit rien quand tout va bien ; le test de restauration envoie son rapport chaque semaine, c'est la preuve que les sauvegardes se restaurent).

## Ce que chaque tâche écrit

| Tâche | Succès (`cron_runs.note`) | Échec (`cron_runs.error`, rouge) |
|---|---|---|
| `game` | « N player(s) » ; aussi : verrouillage des journées, streaks, ligues, Wrapped, rappels (2 notifications par jour au plus ; le plan, la revue et le bilan de la semaine aussi sur le téléphone, à l'heure du trader, si `sweep-private/push-config.php` existe : `ops/push-keys.php`), « La réalité du mois » le 1er, courriel « Ta semaine » le vendredi dès 17 h 30 ET, fin d'essai. Une erreur sur un trader est écrite dans le journal d'erreurs et la tâche continue. | une erreur fatale (message + fichier:ligne) |
| `chart` | « N day(s) downloaded, N cached », ou « disabled or no Databento key » (sans clé, rien à faire) | une erreur fatale |
| `presets` | « N firm(s) checked » (le détail par firme : Admin › Préréglages). Seule la vérification complète compte : `--dry-run`, `--firm=` et `--rollback` ne sont pas enregistrés. | une erreur fatale |
| `backup` | le nom de la sauvegarde, « + off-site copy » ou « (no off-site copy) » | pas de phrase secrète, base introuvable, dossier impossible à créer, intégrité, envoi hors serveur raté… (le message exact) |
| `mail` | « N sent · N queued · N of N this hour », précédé des automatiques du jour quand ils passent (« 3 daily », « daily: nothing due », « 1 day-one evening ») | une erreur fatale ; une campagne mise en pause toute seule (rebonds, plaintes) est écrite sur la campagne, dans Admin › Courriels |
| `restore_test` | intégrité et nombres (traders, documents) de la copie restaurée et de la base en production | aucune sauvegarde trouvée, sauvegarde illisible, intégrité, sauvegarde de plus de 36 h |

Une tâche démarrée et jamais terminée depuis plus d'une heure (ou d'un cycle) passe en rouge « Bloquée ».

## Pas de tâche planifiée (à la demande)

- **Calendrier économique** : récupéré par l'app quand une page en a besoin (table `econ_sync`, un jour à la fois).
- **Nettoyage** : sessions expirées et tentatives de connexion de plus de 24 h, effacées pendant l'utilisation de l'app (`api.php`).
- **Alerte « préréglages pas vérifiés depuis 8 jours »** : pendant l'utilisation de l'app, au plus une fois par heure (`pr_watchdog`).

## Vérifier à la main (terminal cPanel)

```
/usr/local/bin/php /home/matnsabc/app.makeitsweep.com/presets/cron.php --dry-run    # sans rien changer
/usr/local/bin/php /home/matnsabc/app.makeitsweep.com/ops/restore-test.php          # rapport immédiat (compte comme une exécution)
crontab -l                                                                          # les lignes réellement en place
```
