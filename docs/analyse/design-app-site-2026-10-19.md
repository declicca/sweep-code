# Chantier design : l'app avec le langage du site (19 oct. 2026)

Référence : `website/src/system.css` (lecture seule). Valeurs de l'app relevées dans le navigateur (style calculé), 390 × 844 et 1300 × 850, clair et sombre, avant le chantier.

## Composants : site, app (avant), décision

| Composant | Site | App avant | Décision |
|---|---|---|---|
| Bouton principal | capsule, `--blue-btn` #2F6FE8 plein, ombre fine `0 1px 0 rgba(255,255,255,.14) inset, 0 1px 2px rgba(0,0,0,.16)`, -0,01em, appui `scale(.97)` | 6 définitions empilées : dégradé #2F6FE4 → #2A66D6, reflet `::after`, halo bleu `0 6px 16px -8px`, `filter: brightness` au survol ; `.sb-cta` en #4c82ff à 14 px ; « + » à 15 px en dégradé + halo | Version du site partout (`.btn.primary`, `.tk-save`, `.sb-cta`, « + » de la barre du bas et de la barre latérale, envoi de Sweep AI) ; survol et appui en #2A66DC ; hauteurs de l'app gardées (§8) |
| Bouton secondaire | fond teinté `color-mix(texte 8 %)`, 12 % au survol, sans contour | verre + filet (`--glass-edge`, `--glass-hi`) | Version du site |
| Bouton discret | lien bleu | gris (« Tout voir › ») | Gris gardé : un seul bleu par écran (§8) |
| Carte | `--glass` + `--shadow-2`, rayon 26 | rayon 26, mais en sombre fond transparent (le jeton `--glass` d'app.css valait une couleur, ce qui rendait `background: var(--glass), var(--panel)` invalide) | Un seul verre (`--glass`) et `--shadow-2` |
| Tuile | — (cartes) | rayon 20, fond `--panel` | Rayon 20 gardé (palier du site) |
| Feuille | `--glass-menu`, ombre 3 | `rgba(21,21,24,.86)`, coins 32 sur téléphone, 20 à 26 sur ordinateur | `--glass-menu` (via `--glass-strong`), `--shadow-3`, 32 px partout |
| Sélecteur | piste 6 %, choix `--surface` + `--shadow-1` | piste + filet, choix #1B1B1E + ombre lourde | Version du site |
| Pastille de filtre | `.chip` 6 %, sans filet | `--fill` + filet | Version du site (sans filet) |
| Champ | fond 5 %, filet `--line` intérieur, rayon 10 | #1B1B1E + filet `--hair`, rayon 14 | Fond et filet du site ; rayon 14 gardé (§8) |
| Ligne de liste | — | sans fond | Inchangée |
| Barre du haut | barre de verre | transparente en haut, verre au défilement | Inchangée |
| Barre du bas | `--glass-bar`, `--shadow-3`, sans bordure | `--glass-bar`, filet + bordure 1 px | `--shadow-3`, bordure transparente |

## Jetons, tailles, mouvement

- Jetons du site dans `@layer tokens` (début de `src/app.css`), avec les noms de l'app (`--bg`, `--panel`, `--pos`…) ; les 101 anciennes définitions générales sont retirées. Gardés de l'app pour le contraste : `--faint` #8A8A93 / #66666F, gains #5E98FF (sombre) / #265DC6 (clair), pertes #845C0E (clair).
- Tailles de texte : échelle 11 · 12 · 13 · 14 · 15 · 16 · 17 · 20 · 24 · 28 · 34 · 40 · 56 · 72 · 96 (chaque taille au palier le plus proche, l'égalité va au plus grand).
- Rayons : 10 / 14 / 20 / 26 / 32 et capsule.
- Mouvement : une seule courbe, `--spring` du site (`linear()`), la courbe iOS là où `linear()` n'existe pas ; durées de l'app (150 à 350 ms).

## Captures

Avant / après des 10 écrans (téléphone et ordinateur, clair et sombre) : `livraison/design-app-2026-10-19/`.
