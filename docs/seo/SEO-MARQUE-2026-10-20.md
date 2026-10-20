# SEO de marque : « make it sweep » et « sweep trading » (suivi du brief du 19 oct., 20 oct. 2026)

## Fait sur le site (session Site, 20 oct.)

- **Pages légales hors des résultats** :
  - `noindex, follow` sur les Conditions, la Confidentialité et les Risques, en EN, FR et ES ;
  - retirées du sitemap ;
  - toujours liées dans le pied de page, et pas bloquées dans `robots.txt`.
  - Il n'y a pas d'autre page purement légale : ni mentions, ni cookies. La page Sécurité et confidentialité est une page produit : elle reste indexée.
- **« Make it Sweep » en texte visible** :
  - le pied de page, sur toutes les pages : « Sweep · Make it Sweep — le journal de trading gratuit… » ;
  - la réponse de la FAQ de l'accueil, qui commence par « Sweep (Make it Sweep, makeitsweep.com) est un journal de trading gratuit… ». Les données `FAQPage` suivent toutes seules, puisqu'elles viennent du même texte ;
  - la page À propos : « Sweep — ou Make it Sweep, d'après notre domaine — … », puis l'origine du nom, avec un lien vers l'accueil (« journal de trading Sweep ») et vers le guide du sweep.
- **Le logo** : le lien pointe vers l'accueil de la langue, avec l'`aria-label` « Sweep — Make it Sweep, accueil » (EN « home », ES « inicio »). C'est un SVG décoratif avec le mot « sweep » en texte : pas d'`alt`.
- **Données structurées** :
  - `WebSite` est seulement sur l'accueil, en EN, FR et ES, avec `name: Sweep` et `alternateName` (« Make it Sweep », « makeitsweep », « Sweep trading journal »).
  - L'`url` reste la racine dans les 3 langues : Google lit le nom d'un site au niveau du domaine, pas d'un dossier `/fr/`.
  - `Organization` reste sur chaque page, avec `alternateName` et `sameAs` (Instagram, TikTok, Facebook).
- **Title de l'accueil et `og:site_name`** : inchangés, déjà conformes.
- **Le guide « liquidity sweep »** : `/liquidity-sweep`, en EN, FR et ES.
  - **L'adresse `/guides/liquidity-sweep` n'est pas possible** : un dossier `guides/` ferait rediriger la page `/guides` vers lui.
  - **La page `/liquidity-sweep-setup` d'hier devient ce guide**, avec une redirection 301 depuis l'ancienne adresse. Deux pages sur le même sujet se seraient fait concurrence.
  - **Contenu** :
    - la réponse directe sous le H1 ;
    - côté acheteurs et côté vendeurs ;
    - où se trouve la liquidité ;
    - un sweep étape par étape, avec le schéma ;
    - sweep ou cassure de structure ;
    - les erreurs fréquentes ;
    - le Sweep Setup pour le pratiquer ;
    - comment le journaliser dans Sweep (setup « Sweep », étiquettes, Edge Reveal, le coach) ;
    - « Pourquoi on s'appelle Sweep » ;
    - 6 questions.
  - **Données** : `Article`, `FAQPage` et `BreadcrumbList` (Accueil › Guides › Liquidity sweep). Mention « contenu éducatif, pas un conseil financier ».
  - **Liens vers le guide** : le lexique (« Liquidity sweep », « PDH / PDL »), la page À propos, la routine du journal, les fiches NQ et MNQ, le hub Guides et `llms.txt`.
  - **Liens depuis le guide** : les fonctionnalités, l'accueil et 2 termes du lexique (PDH / PDL, R multiple).
- **Ce que je n'ai pas fait** : la petite ligne « Make it Sweep. » sous le bouton du bloc de fin de l'accueil. Elle ferait doublon avec la promesse « Ton edge, enfin au même endroit » ; le pied de page et la FAQ suffisent.

## À faire par Mateo (hors du site)

1. **Search Console** :
   - inspection de `/`, `/fr/` et `/es/`, puis « Demander une indexation » ;
   - inspection de `/terms`, `/privacy` et `/risk` (et leurs versions FR et ES) pour accélérer leur retrait ;
   - renvoyer `https://makeitsweep.com/sitemap.xml` ;
   - demander l'indexation de `/liquidity-sweep`.
2. **Suivi** : dans Performances, les requêtes qui contiennent « sweep », page par page, à 2 puis 4 semaines.
3. **Bing Webmaster Tools** : le sitemap. IndexNow est déjà envoyé à chaque mise en ligne.
4. **Liens externes avec le nom** (le levier le plus fort) :
   - les bios Instagram, TikTok et Facebook : « Sweep — trading journal · makeitsweep.com » ;
   - le site de Déclic, avec l'ancre « Sweep trading journal » ;
   - LinkedIn, Crunchbase, Product Hunt, AlternativeTo, SaaSHub ;
   - la description du serveur Discord.
   - Toujours vers l'accueil.
   - Dès que LinkedIn ou Crunchbase existent, la session Site les ajoute à `sameAs`.
5. **Google Business Profile** : seulement si l'adresse de Laval reçoit vraiment des clients.
