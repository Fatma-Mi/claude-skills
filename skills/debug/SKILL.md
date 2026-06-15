---
name: debug
description: Corrige un bug via workflow strict TDD-debug (test de reproduction, cause racine, correctif minimal, non-régression). Agnostique au langage et au framework.
when_to_use: Quand l'utilisateur signale un bug, un comportement inattendu, une exception, un test qui échoue, ou demande "corrige", "debug", "fix", "ça plante", "ça ne marche pas".
argument-hint: <description du bug | message d'erreur | étapes de reproduction>
allowed-tools: Read Grep Glob Edit Write Bash(pytest *) Bash(ruff *) Bash(mypy *) Bash(npm test*) Bash(npm run *) Bash(tsc *) Bash(eslint *) Bash(go test*) Bash(go vet*) Bash(git diff*) Bash(git status*) Bash(git log*)
---

Analyse et corrige le bug décrit ci-dessous : $ARGUMENTS

## Contexte du dépôt
- État du working tree : !`git status --short`
- 5 derniers commits : !`git log -5 --oneline`

## Workflow strict à suivre dans cet ordre

0. **Reformuler le problème** dans tes propres mots avant toute investigation :
   - Comportement observé
   - Comportement attendu
   - Chemin de reproduction (si connu)
   - Inconnues
   Si un de ces éléments manque ou est ambigu → demander à l'utilisateur avant de continuer. Ne pas deviner.
1. **Écrire un test qui reproduit le bug** — le test DOIT échouer avant tout correctif.
2. **Tracer le flux d'exécution** concerné fichier par fichier (lire intégralement les fonctions impliquées, pas seulement les noms).
   Si l'un de ces signaux indique une **régression** :
   - L'utilisateur mentionne « ça marchait avant », « depuis X », « après le merge / le déploiement »
   - Un test qui passait échoue maintenant
   - Le contexte du dépôt (5 derniers commits) montre des changements sur un fichier du flux

   → Inspecter `git diff -- <fichier>` pour voir le contenu des changements. Si le déclencheur n'apparaît pas dans les 5 derniers commits, lancer aussi `git log -20 --oneline -- <fichier>` ciblé sur le fichier du flux pour remonter plus loin.
3. **Proposer 2-3 hypothèses** classées par probabilité. Pour chacune :
   - L'hypothèse en une phrase
   - Preuves qui la **confirmeraient**
   - Preuves qui l'**invalideraient**
   - Niveau de confiance : **haute / moyenne / faible**
   Si toutes les hypothèses sont à confiance faible → s'arrêter et demander plus d'informations (logs, données, repro précise).
4. **Tester les hypothèses** dans l'ordre de probabilité décroissante (lecture du code, exécution ciblée, inspection de données). Réajuster le classement à mesure que les preuves s'accumulent.
5. **Identifier la cause racine** confirmée par les preuves — pas le symptôme. Demander "pourquoi" jusqu'à ce que la chaîne causale soit explicite.
6. **Expliciter le lien causal** entre la cause racine et le symptôme observé : *pourquoi* cette cause produit-elle ce symptôme exact ? Référencer les fichiers/lignes qui prouvent le lien.
7. **Évaluer la portée de l'impact** — où ailleurs dans le code la même cause pourrait se manifester ? Utiliser **Grep** pour chercher les occurrences du même pattern (appels de la fonction fautive sans garde, usages du champ obsolète, autres call-sites du code corrigé, etc.) et lister explicitement les autres call-sites concernés.
8. **Implémenter le correctif MINIMAL** — pas de refactoring opportuniste, pas de nettoyage adjacent, pas d'abstraction introduite.
9. **Vérifier que le test de reproduction passe** maintenant.
10. **Lancer la suite de tests complète** pour vérifier l'absence de régression.
11. **Lancer lint et typecheck** du projet (ex: `ruff`, `eslint`, `tsc --noEmit`, `mypy`, `go vet`…). Détecter la commande via les fichiers de config (`package.json` scripts, `pyproject.toml`, `Makefile`, etc.). Si aucun outil n'est configuré, le dire et passer.
12. **Évaluer le niveau de confiance global** du diagnostic (haute / moyenne / faible) avec justification.
13. **Documenter** : cause racine + correctif appliqué (en commentaire si non-évident, sinon dans le message de commit).

## Règles strictes

- **Ne pas refactorer** le code existant. Correctif minimal uniquement.
- **Ne pas ajouter** de logging, validation, ou gestion d'erreur supplémentaire au-delà du strict nécessaire.
- **Ne pas deviner** la cause : la prouver via lecture du code, exécution du test, ou inspection des données.
- **Ne pas masquer** le symptôme (try/catch englobant, valeur par défaut silencieuse) sans avoir compris la cause racine.
- **Ne pas modifier plusieurs choses en même temps** ("débogage mitraillette") en espérant qu'une marche. Un changement → un test → vérification, puis seulement passer au suivant.
- Si la cause racine est dans une dépendance externe non modifiable, le dire explicitement et proposer un contournement minimal documenté.

## Quand demander clarification supplémentaire

- Plusieurs interprétations possibles du comportement attendu → demander la spec ou un exemple.
- Le périmètre du correctif touche une zone large (> 3 fichiers) → confirmer le scope avant de modifier.

## Format de sortie

```
## Reformulation
- Comportement observé : <ce qui se passe>
- Comportement attendu : <ce qui devrait se passer>
- Reproduction : <étapes ou "non reproductible">
- Inconnues : <ce qui reste flou>

## Reproduction
- Test écrit : <chemin:ligne>
- Statut initial : ÉCHEC (message d'erreur)

## Trace du flux
1. <fichier:ligne> — <ce qui s'y passe>
2. ...

## Hypothèses
1. **<la plus probable>**
   - Confirmerait : <preuve attendue>
   - Invaliderait : <preuve contraire>
   - Confiance : <haute | moyenne | faible>
2. <alternative> — mêmes 3 sous-champs
3. <alternative moins probable> — mêmes 3 sous-champs

## Résultat du test des hypothèses
- Hypothèse confirmée : <numéro + nom> — preuves : <fichier:ligne | sortie de test | données observées>
- Hypothèses écartées : <numéro + nom + preuve qui l'a invalidée>

## Cause racine
<explication causale en 2-4 phrases, confirmée par les preuves>

## Lien causal
<phrase reliant la cause au symptôme : "Parce que <cause> à <fichier:ligne>, <effet intermédiaire>, ce qui se manifeste comme <symptôme observé>">

## Portée de l'impact
- Pattern recherché (Grep) : `<requête utilisée>`
- Call-sites concernés :
  - <fichier:ligne> — <ce qui est affecté>
  - <fichier:ligne> — <ce qui est affecté>
  (ou "aucun autre call-site identifié")

## Correctif
- Fichier modifié : <chemin:ligne>
- Diff appliqué : <résumé en 1-2 lignes>

## Vérification
- Test de reproduction : PASSE
- Suite complète : <X passés / Y échoués> (lister les échecs s'il y en a)
- Lint : <PASSE | échecs listés | non configuré>
- Typecheck : <PASSE | échecs listés | non configuré>

## Niveau de confiance global
<haute | moyenne | faible> — <justification courte>

## Documentation
<phrase prête pour le message de commit ou le commentaire inline>
```

Si une étape ne peut pas être complétée (ex: pas de framework de test dans le projet, suite trop longue à exécuter), le dire explicitement et proposer une alternative — ne pas sauter l'étape silencieusement.
