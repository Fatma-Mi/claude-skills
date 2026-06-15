---
name: write-tests
description: Écrit des tests unitaires, d'intégration ou de régression pour le code ciblé, exécute le runner (pytest, vitest, jest, go test…) et corrige jusqu'au vert. Agnostique au langage et au framework — détecte les conventions du projet avant d'écrire.
when_to_use: Quand l'utilisateur demande d'ajouter des tests, de tester une fonction/module/fichier, de couvrir un cas limite, ou d'écrire un test de régression sur un bug fix. Exemples — "écris les tests pour X", "ajoute des tests", "il manque la couverture sur Y", "teste cette fonction".
argument-hint: [chemin|symbole|plage-git]
allowed-tools: Read Grep Glob Write Edit Bash
---

Écris des tests complets pour : `$ARGUMENTS`

## Conventions du projet

Détecter avant d'écrire — ne jamais imposer un style étranger au repo :
- **Framework de test** : lire le manifeste (`package.json`, `pyproject.toml`, `go.mod`…) pour identifier le runner et la commande d'exécution.
- **Emplacement & nommage** : lire 1-2 tests existants pour la convention (colocalisés vs `tests/`, suffixe `.test.*` / `_test.*` / `test_*`).
- **Style d'assertion** : `describe/it`, `test()`, `assert`, AAA, GWT — copier le style en place.
- **Conventions d'import** : repérer les alias de path (`@/`, `~/`, `src/`…) dans le code testé et les utiliser à l'identique dans les tests ; pas de chemins relatifs si le repo utilise des alias.
- **Langue des descriptions** : suivre la langue du repo (anglais si les tests existants sont en anglais).
- Si aucun test n'existe dans le repo, demander le framework cible avant d'inventer.

## Principes

- **Tester le comportement, pas l'implémentation** : asserter sur les sorties observables et les effets de bord publics ; ne pas verrouiller l'état interne ni l'ordre d'appels non significatif. Un test doit survivre à un refactor qui préserve le comportement.

## Couvrir obligatoirement

- **Happy path** : cas normal, sortie attendue.
- **Cas limites** : valeurs nulles (`null`/`None`/`undefined`), vides (`""`, `[]`, `{}`), max.
- **Cas d'erreur** : exceptions, promesses rejetées.
- **Si applicable** : concurrence, timeouts.

## Après écriture

1. Lancer la commande de test du projet (dérivée du manifeste, jamais inventée).
2. Si un test échoue :
   - Bug dans le code testé → corriger l'implémentation (confirmer avec l'utilisateur si le comportement public change).
   - Mauvaise assertion → corriger le test.
3. Boucler jusqu'à ce que tous les tests du périmètre passent.
4. Rapporter : tests ajoutés, cas couverts, exécution (pass/fail), éventuels `skip` avec justification.
