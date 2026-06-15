---
name: plan
description: Planifie une fonctionnalité ou un projet avant de coder — explore plusieurs options d'architecture, les compare dans une matrice de décision, produit un document technique et un ADR (Architecture Decision Record) au format standard, puis découpe en sous-tâches ordonnées prêtes à implémenter en TDD. Agnostique au langage et au framework.
when_to_use: Quand l'utilisateur veut concevoir une fonctionnalité ou un projet avant de l'écrire, demande "planifie", "conçois", "explore les options d'architecture", "rédige un ADR", "compare les approches", "découpe cette feature en tâches", ou décrit un besoin non trivial sans encore savoir comment l'implémenter. Précède l'implémentation (le code est ensuite écrit tâche par tâche dans la conversation, couvert par /write-tests, corrigé par /debug).
argument-hint: <description de la fonctionnalité ou du projet à concevoir + contraintes connues (volume, deadline, stack)>
allowed-tools: Read Grep Glob Write
---

Conçois et planifie la fonctionnalité ou le projet avant toute implémentation : $ARGUMENTS

## Principe

Structurer la réflexion **avant** de coder. La sortie de ce skill n'est pas du code de production : ce sont des **décisions documentées** (options comparées, ADR, doc technique, découpage). L'implémentation vient après, validée, tâche par tâche. Ne jamais sauter à l'écriture de code applicatif tant que le plan n'est pas validé par l'utilisateur.

## Workflow

Copier cette checklist dans la première réponse et la cocher au fur et à mesure :

```
Plan progress:
- [ ] 1. Cadrer le besoin et les contraintes
- [ ] 2. Explorer 3 options d'architecture
- [ ] 3. Comparer dans une matrice de décision + recommander
- [ ] 4. Rédiger l'ADR pour l'option retenue
- [ ] 5. Produire le document technique + découpage en sous-tâches
- [ ] 6. Attendre validation du plan
- [ ] 7. Récapitulatif de handoff vers l'implémentation
```

### 1. Cadrer

Reformuler le besoin en une phrase. Lister les **contraintes connues** (volume, latence cible, deadline / nombre de sprints, taille d'équipe, stack imposée), les **inconnues**, et le **hors scope** — ce que la feature ne couvre explicitement pas, pour éviter que le plan gonfle. Si une contrainte structurante manque (volume, deadline, stack), demander avant d'explorer — elle change le choix d'architecture.

Si le projet existe, lire le code pertinent (`Grep`/`Glob`/`Read`) pour ancrer les options dans le projet réel, pas dans le vide. Lecture dirigée par trois questions : comment une fonctionnalité similaire est-elle déjà structurée ? quels patterns la base de code utilise-t-elle déjà ? qu'est-ce que le changement toucherait ? Si le projet est neuf (rien à lire), se baser uniquement sur les contraintes énoncées et le dire.

### 2. Explorer 3 options

Trois options **réellement distinctes** (pas trois variantes de la même idée). **L'option 1 est toujours la version la plus simple qui pourrait marcher** — garde-fou contre l'abstraction prématurée : si la matrice montre qu'elle suffit, on économise des semaines ; si elle ne suffit pas, la matrice prouve pourquoi au lieu de le supposer.

Pour chacune :
- Diagramme de composants en ASCII
- Avantages / inconvénients — **spécifiques à ce contexte, pas génériques** (« scalable » ne dit rien ; « tient les 10K/h avec un seul worker » dit tout)
- Complexité d'implémentation (faible / moyenne / élevée)
- Réversibilité — si on se trompe, difficulté à en changer plus tard (faible / moyenne / élevée)
- Technologies recommandées
- Coût infrastructure **et opérationnel** estimé (ordre de grandeur) — toute techno ajoutée (Redis, queue, etc.) doit être opérée, monitorée et mise à jour après la livraison ; ce coût se paie en continu

### 3. Comparer et recommander

Matrice de décision sur des critères pertinents au besoin (typiquement : performance/latence, scalabilité, maintenabilité, complexité, coût infra, réversibilité, time-to-market). Puis **une recommandation justifiée** au regard des contraintes de l'étape 1 — pas un « ça dépend » : les contraintes ont été collectées à l'étape 1, il faut trancher.

Clore la recommandation par **« Ce qui me ferait changer d'avis »** : les facteurs qui, s'ils étaient différents, feraient basculer vers une autre option (ex. « si le volume passe à 1M/h, l'option C devient la bonne »). Le skill tranche, mais affiche ses conditions de validité.

### 4. ADR

Rédiger l'ADR de l'option retenue au format standard (voir Format de sortie), **dans la conversation** à ce stade — le fichier n'est écrit qu'après validation (étape 6). Chemin cible : convention existante du projet si détectée via `Glob` (`docs/adr/`, `doc/decisions/`, etc.), sinon `docs/adr/ADR-XXX-<titre-kebab>.md` par défaut. Statut initial : **Proposé**.

### 5. Document technique + découpage

- Résumé exécutif (3 lignes max)
- Architecture cible : composants + flux de données
- Critères d'acceptation (quand est-ce « fait » ?)
- Risques identifiés + mitigations
- **Découpage en sous-tâches ordonnées** : chaque tâche a une description en 1 ligne, les fichiers à créer/modifier, ses dépendances (quelles tâches avant), un critère de « done », une estimation (S/M/L)

Comme l'ADR, ce document est rédigé dans la conversation à ce stade ; il sera écrit en fichier `docs/plans/<nom-kebab>.md` après validation (étape 6).

La **sous-tâche 1 du découpage est toujours « définir ou vérifier les types/contrats »** (types, interfaces, signatures) — on s'accorde sur la forme avant d'écrire le fond. Si le projet a déjà des contrats typés, cette tâche consiste à vérifier qu'ils couvrent la feature et à ajouter ce qui manque ; son critère de « done » est « contrats compilent / validés », et elle peut être estimée S.

### 6. Attendre validation

Présenter le plan complet (matrice + ADR + doc + découpage), puis **s'arrêter**. Ne définir aucune interface, n'écrire aucun code **ni aucun fichier** tant que l'utilisateur n'a pas validé ou ajusté — on ne pollue pas le repo avec des plans refusés.

**Après validation**, écrire les deux artefacts durables en Markdown :
1. l'ADR → `docs/adr/ADR-XXX-<titre-kebab>.md` (ou la convention du projet)
2. le document technique + backlog → `docs/plans/<nom-kebab>.md` — y ajouter une colonne **Statut** (`à faire` / `en cours` / `fait`) au tableau des sous-tâches : ce fichier devient la source de vérité de l'avancement, mis à jour à chaque sous-tâche terminée

Le reste (cadrage, options, matrice, handoff) reste en conversation : les alternatives rejetées sont déjà résumées dans la section « Alternatives considérées » de l'ADR.

### 7. Récapitulatif de handoff vers l'implémentation

Le plan étant validé et les fichiers écrits, l'implémentation se fait **tâche par tâche, en TDD** : pour chaque sous-tâche, **Claude écrit le code dans la conversation** (sur demande de l'utilisateur, ex. « implémente la sous-tâche 1 »), puis `/write-tests` écrit et lance les tests associés jusqu'au vert, et `/debug` intervient seulement si quelque chose casse. Tests verts avant de passer à la sous-tâche suivante. Ne jamais générer toute la feature d'un bloc.

Après les premières tâches, repasser sur les **cas limites** non couverts (utilisateur/entité inexistant, ressource désactivée, payload trop gros, rate limiting, échec en aval, doublon) et les ajouter au backlog de tâches.

Clore le skill par le récapitulatif de handoff (Phase 2 du format de sortie) : fichiers écrits, convention de test du projet, et la prochaine commande exacte à taper.

## Limites strictes

- **Pas de code applicatif avant validation du plan** (étape 6).
- **Pas d'option « de remplissage ».** Si une seule architecture est réellement viable vu les contraintes, le dire et le justifier plutôt que d'inventer deux alternatives bidon.
- **Estimations honnêtes.** S/M/L et coûts sont des ordres de grandeur ; ne pas les présenter comme des engagements chiffrés précis.

## Quand demander clarification

- Besoin trop vague pour cadrer une architecture (« fais un système de notifs » sans canaux, volume, ni contexte).
- Contrainte structurante absente (volume, deadline, stack) qui ferait basculer la recommandation.
- La demande est en réalité un petit changement local sans enjeu d'architecture → ce skill est surdimensionné, proposer d'implémenter directement (éventuellement couvert par `/write-tests`).

## Format de sortie

### Phase 1 — Plan (avant validation)

```
## Cadrage
- Besoin : <une phrase>
- Contraintes : <volume / latence / deadline / équipe / stack>
- Hors scope : <ce qui est explicitement exclu, ou "rien d'exclu">
- Inconnues : <liste, ou "aucune">

## Options d'architecture

### Option 1 — <nom> (la plus simple viable)
<diagramme ASCII>
- Avantages : ...
- Inconvénients : ...
- Complexité : faible | moyenne | élevée
- Réversibilité : faible | moyenne | élevée
- Techno : ...
- Coût infra + opérationnel : ...

### Option 2 — <nom>
...

### Option 3 — <nom>
...

## Matrice de décision
| Critère | Option 1 | Option 2 | Option 3 |
|---------|----------|----------|----------|
| Latence | ... | ... | ... |
| Scalabilité | ... | ... | ... |
| Maintenabilité | ... | ... | ... |
| Complexité | ... | ... | ... |
| Coût infra | ... | ... | ... |
| Réversibilité | ... | ... | ... |
| Time-to-market | ... | ... | ... |

**Recommandation :** <option> — <justification au regard des contraintes>

**Ce qui me ferait changer d'avis :**
- <facteur qui, s'il était différent, ferait basculer vers une autre option>
- ...

## ADR-XXX — <titre de la décision>
**Date :** <aujourd'hui>
**Statut :** Proposé

### Contexte
<pourquoi cette décision est nécessaire>

### Décision
<ce qui est choisi et pourquoi>

### Alternatives considérées
- **<option rejetée>** : Rejeté — <raison>
- ...

### Conséquences
**Positif :** <...>
**Négatif :** <...>

## Document technique
- **Résumé exécutif :** <3 lignes max>
- **Architecture cible :** <composants + flux>
- **Critères d'acceptation :** <liste>
- **Risques & mitigations :** <liste>

## Découpage en sous-tâches
| # | Tâche | Fichiers | Dépendances | Done | Est. |
|---|-------|----------|-------------|------|------|
| 1 | Définir/vérifier les types et contrats | <fichiers> | aucune | contrats compilent/validés | S |
| 2 | <1 ligne> | <fichiers> | #1 | <critère> | S/M/L |
| 3 | ... | ... | ... | ... | ... |

→ En attente de validation du plan.
```

### Phase 2 — Récapitulatif de handoff (après validation)

Affiché en conversation (pas de fichier dédié — le contenu durable vit déjà dans les deux fichiers) :

```
## Handoff implémentation
- ADR : <docs/adr/ADR-XXX-....md — écrit>
- Document technique + backlog : <docs/plans/....md — écrit, source de vérité de l'avancement>
- Convention de test du projet : <runner détecté (pytest, vitest...) ou convention spécifique (datasets, evaluate.py...)>

## Prochaine étape
Tape : « implémente la sous-tâche 1 » — j'écris le code, puis /write-tests couvre et valide.
Boucle : une sous-tâche → tests verts → mettre à jour le statut du backlog dans docs/plans/....md → la suivante. /debug si régression.
Dans une session future : « reprends docs/plans/....md, implémente la sous-tâche N » suffit — le fichier porte tout le contexte.
```
