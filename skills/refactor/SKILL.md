---
name: refactor
description: Restructure du code existant sans changer son comportement, par étapes atomiques validées par des tests à chaque itération. Plan d'abord (analyse + étapes + risques), tests de capture du comportement actuel, une transformation par commit, tests + lint + typecheck verts entre chaque étape. Agnostique au langage et au framework. Utiliser quand l'utilisateur demande "refactore", "nettoie", "extrait une fonction", "sépare les responsabilités", "découpe ce fichier", "supprime cette duplication", "corrige cette N+1", ou veut restructurer sans changer de comportement.
argument-hint: <cible : fichier, fonction, ou description de ce qui doit être restructuré>
allowed-tools: Read Grep Glob Edit Write Bash
---

Restructure le code ciblé sans modifier son comportement observable : $ARGUMENTS

## Principe

Un refactoring change la **forme** du code, pas son **comportement**. Si une étape change ce que le code fait (sortie, side effect, signature publique consommée ailleurs), elle sort du périmètre : soit l'ajouter au plan et obtenir validation, soit basculer dans un autre workflow (`/debug`, ajout de feature). C'est ce qui justifie le filet de tests de capture : sans eux, impossible de prouver que le comportement reste identique.

## Workflow

Copier cette checklist dans la première réponse et la cocher au fur et à mesure :

```
Refactor progress:
- [ ] 1. Analyser la cible
- [ ] 2. Produire un plan d'étapes atomiques
- [ ] 3. Attendre validation du plan
- [ ] 4. Écrire / identifier les tests de capture
- [ ] 5. Vérifier que les tests de capture passent sur le code actuel
- [ ] 6. Pour chaque étape : modifier → tester → lint → typecheck → commit
- [ ] 7. Ajouter des tests unitaires pour les nouvelles unités extraites
```

### 1. Analyser

Lire intégralement la cible. Identifier responsabilités mélangées, dépendances, effets de bord, anti-patterns visibles (N+1, état partagé, signatures incohérentes, duplication).

### 2. Produire un plan

3 à 6 étapes atomiques. Chaque étape : **ce qui change** (une phrase), **risque** (faible / moyen / élevé), **comment valider** (quels tests doivent rester verts).

Une étape qui touche plus de 3 fichiers ou plus de 100 lignes est probablement trop grosse — la découper.

### 3. Attendre validation

Présenter le plan, puis s'arrêter. Ne rien modifier tant que l'utilisateur n'a pas validé ou ajusté.

### 4–5. Tests de capture

Couvrir au minimum : happy path, branches conditionnelles, cas d'erreur, side effects observables. Les tests doivent **passer sur le code non modifié** avant toute transformation. Sans tests verts au départ, le filet de sécurité n'existe pas — refuser de continuer et le dire.

### 6. Boucle par étape

Pour chaque étape du plan :

1. Implémenter uniquement cette étape
2. Lancer la suite de tests → verte
3. Lancer lint et typecheck du projet → verts (détecter la commande via `package.json` scripts, `pyproject.toml`, `Makefile`, etc. ; si rien n'est configuré, le signaler et passer)
4. Commit séparé, format conventionnel : `refactor(scope): <description courte>`

Sur régression : revenir à l'état précédent (`git checkout --` ou `/rewind`), comprendre la cause, redécouper l'étape si nécessaire. Ne jamais « réparer en avançant ».

### 7. Tests post-refactoring

Chaque unité extraite mérite ses tests isolés. Les tests de capture restent comme tests d'intégration sur le point d'entrée d'origine.

## Limites strictes

- **Pas d'amélioration opportuniste** non listée au plan validé. Une N+1 repérée en passant s'ajoute au plan comme étape distincte ; ne la corrige pas discrètement au milieu d'une autre étape — sinon la régression devient illisible.
- **Une responsabilité par étape**. Extraire + renommer + réordonner dans le même commit rend impossible le bisect en cas de bug futur.
- **Pas de changement de signature publique** sans confirmation explicite que les appelants sont aussi mis à jour dans la même étape.

## Quand demander clarification

- Cible ambiguë (juste un nom de dossier, par exemple).
- Aucun test existant + impossibilité d'en écrire (I/O lourd, dépendances externes non mockables) → proposer un harnais minimal ou refuser le refactoring.
- La demande implique en réalité un changement de comportement (perf, feature, fix) → ce n'est pas un refactor, rediriger vers `/debug` ou demander une spec.

## Format de sortie

### Phase 1 — Plan (avant validation)

```
## Analyse
- Cible : <fichier:lignes ou symbole>
- Responsabilités identifiées : <liste>
- Problèmes visibles : <liste>

## Plan
| # | Étape | Risque | Validation |
|---|-------|--------|------------|
| 1 | <atomique> | faible | <tests qui doivent rester verts> |
| 2 | ... | moyen | ... |

## Tests de capture proposés
- <cas>
- ...

→ En attente de validation du plan.
```

### Phase 2 — Étape (après validation, une par message)

```
## Étape N/M : <description>
- Diff : <fichier:lignes> — <résumé en 1-2 lignes>
- Tests de capture : <X/Y passés>
- Lint : <PASSE | échecs listés | non configuré>
- Typecheck : <PASSE | échecs listés | non configuré>
- Commit : <message conventionnel>
```

### Phase 3 — Clôture

```
## Récapitulatif
- Étapes complétées : N/M
- Tests de capture (avant et après) : tous verts
- Nouveaux tests unitaires ajoutés : <liste>
- Améliorations non comportementales appliquées : <liste, ou "aucune">
```
