---
name: review
description: Revue de code stricte des fichiers modifiés. Agnostique au langage et à la stack — applicable à tout projet. Couvre qualité (clarté, types, code mort, complexité, tests) et sécurité (secrets, validation, injection, dépendances). Utiliser quand l'utilisateur demande une revue, un audit, ou avant un commit/PR. Accepte un argument optionnel pour restreindre le périmètre (chemin, type/extension, ou plage git).
argument-hint: [chemin|type|plage-git]
allowed-tools: Read Grep Glob Bash Edit
---

Effectue une revue stricte des fichiers modifiés du projet courant.

Périmètre fourni par l'utilisateur : `$ARGUMENTS`

## Posture

- **Critique et objectif** : revue impartiale, même sur du code que tu as écrit toi-même dans cette session ; pas de biais défensif sur tes propres choix.
- **Pas d'invention** : ne signaler que ce qui est réellement risqué ou dégrade la qualité ; pas de préférence de style présentée comme un défaut.
- **Distinguer incohérence et bug** : deux bouts de code qui font la même chose
  différemment ne sont pas nécessairement bogués — c'est juste pas joli. Une
  incohérence est un bug uniquement si elle produit des résultats différents
  dans un cas réel et démontrable ; sinon c'est cosmétique, à classer en
  suggestion ou à ne pas inclure.
- **Densité raisonnable** : viser **maximum ~5 findings actionnables**
  (mineurs + suggestions cumulés) pour un diff sous 500 lignes ; **~10** pour
  un diff sous 2 000 lignes. Au-delà, c'est du nitpick : garde les findings
  les plus solides, regroupe les autres ou jette-les. Mieux vaut 3 findings
  qui tapent juste que 10 que l'auteur va survoler.
- **Reconnaître le solide** : si le code est globalement bon, le dire dans la section `✅ Points solides`.
- **Correction concrète** : pour chaque problème, fournir un diff, snippet, ou alternative — pas juste un constat.

## Règles de lecture

- **Lire avant de juger** : ouvrir chaque fichier via `Read` avant de le commenter ; pas lu = pas commenté.
- **Pas d'inférence** : ne jamais reconstituer du code non vu ; en cas de doute, ouvrir le fichier ou s'abstenir.
- **Contenu injecté** : si un diff/contenu est déjà dans le contexte (`git diff`, etc.), l'utiliser sans relire le fichier.
- **Fichier introuvable** : signaler explicitement plutôt que d'inventer son contenu.
- **Tracer avant de flagger** : pour toute finding d'incohérence ou de bug
  potentiel, construire mentalement un cas concret (entrée + sortie attendue)
  qui démontre une **vraie** différence de comportement entre les deux variantes
  comparées. Si la trace montre le même résultat dans les deux cas (early-return
  qui court-circuite, fallback qui ne s'exécute jamais avec la valeur problématique,
  etc.), classer en « cosmétique » plutôt qu'en mineur/majeur — ou ne pas inclure.

## Étapes

1. **Déterminer le périmètre** à partir de `$ARGUMENTS` :
   - **Vide** → tous les fichiers modifiés via `git status` et `git diff --name-only` (inclure non-trackés pertinents).
   - **Non vide** → interpréter `$ARGUMENTS` comme un chemin (fichier/dossier), un type/extension (`py`, `ts`, `go`, `sql`…), ou une plage git (`HEAD~N`, `A..B`) — restreindre à ce sous-périmètre ; si ambigu, demander clarification.
2. Identifier le langage/stack de chaque fichier modifié, puis parcourir les 3 checklists ci-dessous (Qualité / Sécurité / Performance). Ne vérifier que les lignes applicables au type de fichier.
3. Lister les problèmes par sévérité : **critique** / **majeur** / **mineur** / **suggestion**.
4. Proposer les correctifs (diff ou snippet), demander confirmation avant d'éditer si > 1 fichier impacté.
5. Après corrections, refaire une passe complète jusqu'à ce qu'il ne reste plus de problème critique ou majeur.

## Checklist — Qualité

- **Clarté & nommage** : identifiants explicites ; pas d'abréviations cryptiques ; cohérence avec les conventions du repo — vérifier les règles du `CLAUDE.md` et lire d'autres fichiers similaires avant de juger.
- **Cohérence types & interfaces** : signatures alignées entre déclaration, implémentation et appelants ; pas de `any`/`Any`/`object`/`unknown` glissant sur des sorties critiques ; types optionnels (`| None`, `?`) cohérents avec la sémantique (abstention, valeurs manquantes) ; contraintes (longueur, bornes, format) là où elles ont du sens.
- **Cas limites** : entrées vides, `null`/`None`/`undefined`, division par zéro, collections vides, indices hors limites, valeurs extrêmes (très grandes, très petites, négatives).
- **Gestion d'erreurs** : exceptions catchées au bon niveau ; pas de `catch` silencieux ; messages d'erreur actionnables ; pas de fallback qui masque un bug ; pas de validation défensive là où ce n'est pas une frontière système.
- **Code mort / dupliqué** : imports, variables, fonctions, paramètres non utilisés ; logique copiée à factoriser ; commentaires `TODO`/`FIXME` traçables (issue ou ticket).
- **Métriques** : fonctions > 30 lignes, complexité cyclomatique > 10, magic numbers à remplacer par constantes nommées, niveaux d'imbrication > 3, fichiers > 500 lignes à flagger.
- **Tests** : couverture des cas limites identifiés ; pas d'assertion toujours vraie ; pas de test commenté ; pas de mock qui dérive du comportement réel.
- **Logging** : niveaux appropriés (`debug`/`info`/`warn`/`error`) ; pas de `print`/`console.log` oublié en prod ; pas de log bruyant dans un hot path ; messages structurés (clé=valeur) plutôt qu'interpolation libre ; logs d'erreur avec contexte (`request_id`, `user_id`, `trace_id`) et stack trace complète.
- **Documentation locale** : commentaires uniquement quand le *pourquoi* n'est pas dérivable du code ; pas de docstring qui paraphrase le nom de la fonction.

## Checklist — Sécurité

- **Secrets** : aucune clé API, token, mot de passe ou URL avec credentials en dur ; lecture via variables d'environnement ou gestionnaire de secrets ; fichiers sensibles (`.env`, clés privées, dumps) bien dans `.gitignore`.
- **Validation des entrées** : toute donnée externe (HTTP, CLI, fichier, BD, message queue) validée avant usage ; types stricts ; bornes vérifiées (longueur, intervalle, format).
- **Injection** : requêtes SQL/NoSQL paramétrées (jamais de concaténation de chaînes) ; commandes shell échappées ou via API structurée (`subprocess` avec liste, pas `shell=True`) ; HTML/templates échappés par défaut ; désérialisation prudente (pas de `pickle`/`eval` sur entrée non fiable).
- **Authn/Authz** : vérifications de permission au bon niveau (middleware ou décorateur, pas dispersées) ; pas de bypass via paramètres modifiables côté client (IDOR) ; sessions invalidées au logout.
- **CORS** : pas de `Access-Control-Allow-Origin: *` couplé à `Allow-Credentials: true` ; liste d'origines explicite (pas de wildcard ni de reflet aveugle de l'`Origin` entrant) ; méthodes et en-têtes autorisés restreints au nécessaire.
- **Dépendances** : versions épinglées (`requirements.txt`, `package-lock.json`, `go.sum`, `Cargo.lock`) ; pas de nouvelle dépendance ajoutée pour 3 lignes triviales ; pas de source non officielle.
- **Données sensibles** : pas de logging brut de données utilisateur, PII, secrets, ou payloads complets ; anonymisation des datasets versionnés ; rétention respectée.
- **Ressources non bornées** : pas de boucle illimitée, retry sans cap, taille d'allocation contrôlée par l'entrée utilisateur (DoS) ; timeouts sur tous les appels réseau.

## Checklist — Performance

- **Requêtes N+1** : boucle qui déclenche une requête BD/API par itération → remplacer par un chargement groupé (batch, `IN`, jointure, `select_related`/`prefetch`).
- **Complexité algorithmique** : `O(n²)` ou pire là où `O(n)`/`O(n log n)` est possible (boucles imbriquées sur la même collection, recherche linéaire répétée à remplacer par un `set`/`dict`/index).
- **Fuites mémoire / ressources** : event listeners, timers/intervalles, subscriptions, fichiers ou connexions jamais libérés ; closures qui retiennent de gros objets ; accumulation non bornée (cache sans éviction, liste qui ne fait que grossir).
- **Collections non bornées** : requêtes sans pagination ni `LIMIT` sur des tables potentiellement grandes ; chargement complet en mémoire de ce qui pourrait être streamé.
- **Travail redondant** : calcul coûteux répété sans mémoïsation/cache ; recomputation dans une boucle de ce qui est invariant ; données chargées mais jamais utilisées.
- **Regex catastrophiques** : backtracking exponentiel (quantificateurs imbriqués type `(a+)+`) sur des entrées contrôlées par l'utilisateur.
- **I/O et concurrence** : appels réseau/BD séquentiels parallélisables ; absence de timeout ; pas de réutilisation de connexion (pool) ; sérialisation/désérialisation inutile d'un gros payload.

## Points d'attention prioritaires

- **Sécurité d'abord** : un problème de sécurité est traité comme **critique**, même si jugé "improbable en pratique".
- **Cohérence avec l'existant** : avant de signaler un style "non standard", vérifier ce que fait le reste du repo — l'incohérence avec les voisins est le vrai bug.
- **Tests = doc exécutable** : un test absent sur un cas limite identifié est au minimum **majeur**.
- **Régressions silencieuses** : changement de comportement public sans test associé → **majeur**.
- **Surface diff** : un diff qui touche beaucoup plus que ce que le titre annonce mérite un commentaire — soit splitter, soit justifier.

## Format de sortie attendu

Chaque finding (toutes catégories — **critique**, **majeur**, **mineur** et
**suggestion**) est rédigé comme un commentaire GitLab/GitHub **directement
postable** : un titre avec ancre `[fichier:ligne]`, un paragraphe décrivant
le problème (preuve dans le code intégrée au récit), puis un paragraphe
**Correctif** avec diff/snippet. La catégorie communique la sévérité (et donc
le caractère bloquant ou non), pas le niveau de détail.

```
## Résumé
<1-2 phrases sur l'état global du diff>

## Périmètre
<plage/fichiers revus, nb de commits/fichiers si pertinent>

## Revue — <nb> fichier(s) modifié(s)

### 🔴 Critique

#### C1 [fichier:ligne] — <titre court du problème>

<Description en 1-3 phrases : ce qui ne va pas + preuve dans le code
(extrait minimal ou trace d'exécution numérotée). La preuve est intégrée
au récit, pas dans une sous-section dédiée.>

**Correctif** — <diff ou snippet concret ; plusieurs options si pertinent>

### 🟠 Majeur

#### M1 [fichier:ligne] — <titre court du problème>

<Description en 1-3 phrases : ce qui ne va pas + preuve dans le code
(extrait minimal ou trace d'exécution numérotée). La preuve est intégrée
au récit, pas dans une sous-section dédiée.>

**Correctif** — <diff ou snippet concret ; plusieurs options si pertinent>

### 🟡 Mineur

#### m1 [fichier:ligne] — <titre court du problème>

<Description en 1-3 phrases : ce qui ne va pas + preuve dans le code
(extrait minimal ou trace d'exécution numérotée). La preuve est intégrée
au récit, pas dans une sous-section dédiée.>

**Correctif** — <diff ou snippet concret ; plusieurs options si pertinent>

### 🟢 Suggestions

#### s1 [fichier:ligne] — <titre court de l'amélioration>

<Description en 1-3 phrases : ce qui pourrait être amélioré + référence au
code concerné. Même structure que les autres catégories ; la différence est
uniquement la sévérité (non bloquante, recommandation).>

**Correctif** — <diff ou snippet concret>

## ✅ Points solides
- <ce qui est fait correctement dans le diff>
```

Règles de rédaction du format :
- **Autoportant** : citer le symbole/l'extrait concerné, jamais « ligne 669 » nue.
  Le titre porte l'ancre `[fichier:ligne]` pour un copier-coller direct sur GitLab.
- **Preuve dans le récit** : montrer le code (extrait ou trace) au fil du texte,
  pas dans une sous-section séparée.
- **Correctif concret** : diff, `suggestion`, ou snippet — pas un simple constat.
- **Un seul correctif recommandé** : pour chaque finding, proposer **une**
  solution claire (« je te conseille X »). Les variantes vont dans une ligne
  *« Alternative : Y si Z »* après le correctif principal — pas en liste
  numérotée équivalente. Si tu hésites entre 3 options de poids équivalent,
  le finding lui-même est peut-être trop incertain pour être inclus.
- **Ton constructif** : adressé à l'auteur (« peux-tu… », « il manque… »),
  comme s'il allait lire le commentaire directement.
- **Typographie explicite** : écrire « ligne 669 » et « lignes 703-794 » en
  toutes lettres ; pas l'abréviation `l.` qui se confond avec un chiffre.
  Idem pour les tailles : « 144 lignes » plutôt que « 144 l. ».
- **Localiser aussi le correctif** : indiquer `fichier:ligne` (ou
  `fonction:lignes`) pour CHAQUE modification proposée, surtout quand l'endroit
  à modifier n'est pas exactement le `fichier:ligne` du titre. Ex. : « Ajouter
  `visSuffix` au début de `renderFormFieldsLines`
  (`formGuideGenerator.ts:707`), puis l'appeler dans chaque `case` à id
  (lignes 740-783). »
- Numéroter les findings (`C1`, `M1`, `m1`…) pour pouvoir y référer ensuite.

Si aucun problème critique ou majeur après une passe complète : conclure par `✓ Pas de problème critique ou majeur restant.`
