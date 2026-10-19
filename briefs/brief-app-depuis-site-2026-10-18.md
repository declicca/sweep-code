# Brief pour la session App, venant du site (18 oct. 2026)

Décisions de Mateo du 18 oct. Le site les affiche déjà (commit du site du 18 oct., pas encore en ligne au moment d'écrire ce brief). L'app doit suivre pour que le site et l'app disent la même chose.

## 1. La lecture des captures dans Free : 3 par jour

**Décision** : « Lecture des captures. Maximum 3 par jour. » Un trader Free peut faire lire une capture par Sweep AI, au plus 3 fois par jour.

**Ce que dit le site** :
- tableau des tarifs, ligne « Saisie avec l'IA (mots ou capture) » : Free « 3 par jour », Pro ✓, Elite ✓ ;
- carte Free : « Vrais graphiques CME et saisie avec l'IA, 3 par jour » ;
- page du journal gratuit : « Saisie avec l'IA, en mots simples ou à partir d'une capture, 3 fois par jour ».

**Ce que fait l'app aujourd'hui (lu dans `origin/main`)** :
- `billing/billing-core.php`, `sb_ai_consume()` : la tâche `trade_import` (capture) a le genre `import` (`sai_kind()`, `ai/ai-core.php`). Sur Free, `ai_import` vaut `false`, donc la capture est refusée (`upgrade_required`) ;
- la saisie en mots (`trade_parse`) compte déjà sur `ai_daily` (3 par jour sur Free) : rien à changer ;
- `receipt_scan` (reçus de dépenses) a aussi le genre `import`. Les dépenses font partie de Mon argent (Pro et Elite), donc le scan des reçus reste réservé à Pro et Elite.

**À faire** (proposition) :
- une limite quotidienne propre aux captures pour Free (par exemple `ai_import_daily` = 3 ; `null` pour Pro et Elite), remise à zéro à minuit, heure de New York, comme `ai_daily` ; elle ne s'applique qu'à `trade_import`. `receipt_scan` reste refusé sur Free ;
- une capture refusée pour quota renvoie `quota` avec `reset_at`, et le message en 3 langues dit « 3 captures par jour avec Free, sans limite avec Pro » ;
- une capture qui échoue (réseau, fournisseur) est rendue, comme `sb_ai_refund()` le fait déjà ;
- textes à aligner :
  - la page des forfaits (`f_ai_import`, Free) : « 3 par jour » au lieu de « — » ;
  - les avantages de Pro (`b_ai_import`, « Import IA depuis captures et relevés ») : garder, puisque Pro est sans limite ;
  - la fin d'essai (`fw_z_shots`, « La lecture des captures : tu saisis tes trades à la main ») et la liste de ce qui est perdu (`'shots'` dans `sb_pro_used()`, `billing-core.php`, ligne ~496) : la lecture des captures n'est plus perdue en passant à Free, seulement limitée à 3 par jour ;
  - le guide de Sweep AI (`ASK_GUIDE`, `ai/chat.php`), s'il parle des forfaits.

## 2. Quantower partout

**Décision** : « Quantower partout ». Le site cite maintenant Quantower partout où il citait la synchro NinjaTrader 8 : accueil, fonctionnalités, FAQ, page Importer (une carte Quantower avec les étapes de la feuille « Connecter Quantower »), comparatifs, page du journal gratuit, kit de presse, `llms.txt`.

**Dans l'app, encore NinjaTrader 8 seulement** (`src/ux.js`, section 30) :
- `tipImport` : « Sur NinjaTrader 8 ? Connecte-le une fois : tes trades arrivent seuls, plus besoin d'importer. »
- `tipAcct` : « Tu trades sur NinjaTrader 8 ? Connecte-le : tes comptes sont trouvés et tes trades arrivent seuls. »

`CONTEXTE-APP.md` dit d'attendre que les traders confirment que l'add-on marche. La décision de Mateo du 18 oct. lève cette attente : ces invitations peuvent nommer les deux plateformes (« Sur NinjaTrader 8 ou Quantower ? »), en 3 langues.

## 3. Rithmic et Tradovate : « prévue plus tard »

**Décision** : « Synchro Rithmic et Tradovate prévue pour plus tard. » Le site ne dit plus « en développement » mais « prévue plus tard » (EN « planned for later », ES « prevista para más adelante »). L'app ne dit « en développement » nulle part (vérifié dans `src`, `ai`, `billing`) : rien à faire, sauf si un nouveau texte en parle.
