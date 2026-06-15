---
name: explain
description: Explique en détail un fichier, une fonction, un module, une plage de lignes — ou la vue d'ensemble des changements d'une branche depuis sa divergence (plage git / nom de branche). Structure la réponse selon le périmètre. Agnostique au langage. Lecture seule — ne modifie aucun fichier.
when_to_use: Quand l'utilisateur veut comprendre du code existant, demande "explique-moi", "comment marche X", "que fait cette fonction", "à quoi sert ce module", "walk me through this code", ou "qu'est-ce que ma branche apporte / résume mes changements depuis la divergence". Utile pour onboarding, code review, ou avant un refactor/merge.
argument-hint: [chemin|symbole|"plage de lignes"|branche|plage-git]
allowed-tools: Read Grep Glob Bash(git:*)
---

Explique en détail : `$ARGUMENTS`

## Posture

- **Lecture seule** : ne modifie jamais le code. Si l'utilisateur veut corriger, il invoque `/review` ou édite lui-même.
- **Pas d'invention** : si une partie n'est pas claire à la lecture, le dire explicitement plutôt que deviner.
- **Adapter au niveau** : si l'utilisateur précise un niveau (débutant, expert, etc.), ajuster vocabulaire et profondeur. Sinon, viser un développeur familier avec le langage mais découvrant ce code.

## Déterminer le périmètre

Identifier d'abord le **type** de périmètre demandé :

- **Code** (chemin de fichier/dossier, symbole, plage de lignes) → mode « explication de code » (5 sections ci-dessous).
- **Branche ou plage git** (nom de branche existant, ou forme `A...B` / `A..B` / `HEAD~N`) → mode « vue d'ensemble de branche » (format alternatif en fin de fichier). Pour un simple nom de branche, comparer avec la forme **3 points** `<branche>...HEAD` afin d'isoler ce que la branche courante apporte depuis le merge-base. Si le périmètre est vide et que l'intention semble être « mes changements », détecter la cible (suivi amont, sinon `develop`/`main`) ou demander.

En cas d'ambiguïté entre un nom de fichier et un nom de branche, demander.

## Règles de lecture

- **Lire intégralement** le périmètre indiqué via `Read` (ou `git diff` pour une plage) avant d'expliquer. Pas lu = pas commenté.
- **Tracer les dépendances** : pour chaque import/appel important, ouvrir le fichier cible (au moins une lecture rapide) pour confirmer le comportement réel — pas de supposition basée sur le nom.
- **Si le code est long** (> 200 lignes) : focaliser sur les parties les plus **complexes** ou **surprenantes**. Survoler le reste avec un résumé.
- **Si le périmètre n'est pas clair** (juste un nom de fichier vague, plage incohérente) : demander clarification avant d'expliquer.

## Structure de l'explication

Suivre cette structure dans l'ordre :

### 1. Vue d'ensemble
Que fait ce code en **2-3 phrases**. Le résumé qu'un collègue donnerait au stand-up. Pas de jargon inutile.

### 2. Flux d'exécution
Étape par étape, **que se passe-t-il à l'exécution** ? Numéroter les étapes principales. Mentionner les branches/conditions importantes. Pour une fonction : entrée → traitement → sortie. Pour un module : ordre d'initialisation, points d'entrée.

### 3. Dépendances
Quels autres fichiers/modules/services sont impliqués ?
- Imports internes (autres fichiers du repo)
- Imports externes (libs tierces) — mentionner uniquement celles qui jouent un rôle non-trivial
- I/O externe : BD, HTTP, fichiers, queue, env vars

### 4. Points d'attention
Ce qu'il faut **savoir** ou **se méfier** :
- Cas limites traités (et ceux qui semblent pas l'être)
- Choix surprenants ou non-évidents (pourquoi tel pattern, telle structure de données)
- Bugs potentiels visibles à l'œil nu (sans aller jusqu'à un audit `/review`)
- Effets de bord (mutations, écritures BD, logs critiques)

### 5. Suggestions
Comment ce code **pourrait** être amélioré, **sans le modifier** :
- Lisibilité, nommage, complexité réductible
- Tests manquants (cas limites visibles non couverts)
- Couplages à découper, abstractions à introduire
- Format : 2-4 suggestions concrètes, pas une thèse.

## Quand demander clarification

- Périmètre ambigu (`/explain api` → quel fichier ? quel dossier ?)
- Code trop large (> 1000 lignes) sans focus : proposer un sous-périmètre.
- Concept inconnu mentionné par l'utilisateur (`/explain le système de cache`) : demander où chercher.

## Format de sortie

```
## Vue d'ensemble
<2-3 phrases>

## Flux d'exécution
1. ...
2. ...
3. ...

## Dépendances
- <fichier/module> — <rôle>
- ...

## Points d'attention
- <observation factuelle>
- ...

## Suggestions
- <amélioration concrète>
- ...
```

Si le code est trop court ou trivial pour cette structure (ex: une fonction de 5 lignes), condenser en un paragraphe + une ou deux suggestions. Pas de remplissage artificiel.

## Format de sortie — vue d'ensemble de branche

Quand le périmètre est une branche / plage git, ne pas appliquer les 5 sections par fichier. Lister les fichiers via `git diff --name-status <plage>` et les commits via `git log --oneline <cible>..HEAD`, lire le diff des fichiers porteurs de logique (ignorer lockfiles et fichiers générés), puis synthétiser :

```
## Vue d'ensemble
<2-4 phrases — ce que la branche apporte (besoin/ticket, type : feature/fix/refactor/outillage)>

## Périmètre
- Cible : <branche> — merge-base : <sha court>
- <nb> commit(s), <nb> fichier(s) (A:<n> M:<n> D:<n>)

## Ce qui change, par thème
- **<thème>** (`fichiers`) — <ce que ça apporte ; distinguer cœur de logique vs support/config/tests>
- ...

## Points d'attention
- <changements à fort impact, dépendances ajoutées, surface du diff cohérente ou non, zones sans tests>

## Pour aller plus loin
- `/explain <fichier>` — pour le détail d'un fichier clé
- `/review <plage>` — pour une revue critique avant merge
```

Si la branche n'apporte aucun changement par rapport à la cible, le dire et s'arrêter.
