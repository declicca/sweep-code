# Brief pour la session App : savoir quelle page du site amène chaque inscrit (21 oct. 2026)

**À qui** : la session App. Travaille en autonomie : livre une fois, avec les tests, puis demande une seule fois l'accord pour déployer. Ne touche pas au code du site.

## Le problème

Chaque bouton d'inscription du site porte la page d'où il part, dans son adresse :

`https://app.makeitsweep.com/?signup=1&utm_source=site&utm_medium=<page>&utm_campaign=<campagne>`

- `utm_medium` : le nom de la page (`home`, `pricing`, `pass-prop-firm-evaluation`, `prop-firm-gameplan-month-1`, `sweep-vs-tradezella`…), ou `prop-firm` pour les pages des firmes ;
- `utm_campaign` : `oct-update`, ou le nom de la firme ou de la paire pour les pages des firmes (`topstep`, `topstep-vs-apex`…).

`auth.html` envoie déjà `utm_source`, `utm_medium` et `utm_campaign` dans le corps de `api/auth/register` (ligne 351). Mais :

1. **`save_signup_attribution()`** (`api.php`, vers la ligne 565) ne lit que le témoin `sweep_utm`. Le site ne l'écrit que dans un cas : le visiteur est arrivé avec des balises dans son adresse (une publication Instagram ou TikTok) **et** il a accepté les témoins. Un trader venu de Google n'a donc rien : `users.utm_*` reste vide, et Admin › Attribution le range dans `no-tag:…`.
2. **L'événement `signup_completed`** garde `utm_source` et `utm_campaign`, mais pas `utm_medium`. La page est donc perdue aussi là.
3. **Admin › Attribution** (`api/admin/attribution`) regroupe par `utm_content`. Les liens du site n'en ont pas.

Résultat : aujourd'hui, on ne sait pas si les pages SEO (plan de 90 jours, réussir une évaluation, comparatifs, pages des firmes…) amènent des inscrits.

## Ce qu'il faut faire

1. **À l'inscription, quand le témoin `sweep_utm` manque** (ou ne contient aucune balise), enregistrer les balises du corps : `utm_source`, `utm_medium`, `utm_campaign`, avec le même nettoyage (`$tag`). Quand le témoin existe, il garde la priorité (premier contact).
2. **`signup_completed`** : ajouter `utm_medium`.
3. **Admin › Attribution** : pour `utm_source = site`, une ligne par page (`site · <utm_medium>`, et `<utm_campaign>` quand `utm_medium = prop-firm`), avec les mêmes colonnes qu'aujourd'hui (inscrits, activés, 3 jours de trading, jour 7, jour 14). Les lignes des publications (`utm_content`) ne changent pas.

Pas de question de consentement : ce sont les balises du lien sur lequel le trader a cliqué. Aucun témoin n'est écrit.

## Tests

- Inscription **sans** témoin, avec les balises dans le corps : `users.utm_medium` = la page.
- Inscription **avec** le témoin `sweep_utm` : les balises du témoin gagnent.
- Balises invalides ou trop longues : nettoyées comme aujourd'hui.
- Admin › Attribution : une ligne `site · pass-prop-firm-evaluation` après une inscription venue de cette page.

## Côté site

Rien à changer : les liens portent déjà ces balises sur toutes les pages, dans les 3 langues.
