# Claude Skills

Skills réutilisables pour [Claude Code](https://docs.claude.com/en/docs/claude-code) — agnostiques au langage et au framework.

## Skills disponibles

- **review** — Revue de code stricte des fichiers modifiés. Couvre qualité (clarté, types, code mort, complexité, tests) et sécurité (secrets, validation, injection, dépendances).
- **write-tests** — Écrit des tests unitaires, d'intégration ou de régression pour le code ciblé, exécute le runner (pytest, vitest, jest, go test…) et corrige jusqu'au vert. Détecte les conventions du projet avant d'écrire.
- **ship** — Commit et push propre des changements en cours, avec tests et lint exécutés avant le commit. Message au format conventional commits. Ne push jamais si les tests échouent.
- **explain** — Explique en détail un fichier, une fonction, un module ou une plage de lignes. Structure la réponse en sections (vue d'ensemble, flux, dépendances, points d'attention, suggestions). Lecture seule.
- **debug** — Corrige un bug via un workflow strict TDD-debug : test de reproduction qui échoue, hypothèses classées par probabilité, cause racine prouvée, correctif minimal, vérification non-régression + lint/typecheck.
- **refactor** — Restructure du code existant sans changer son comportement, par étapes atomiques : plan validé d'abord, tests de capture du comportement actuel, une transformation par commit, tests + lint + typecheck verts entre chaque étape.
- **plan** — Planifie une fonctionnalité ou un projet avant de coder : explore plusieurs options d'architecture, les compare dans une matrice de décision, produit un document technique + un ADR (Architecture Decision Record), puis découpe en sous-tâches ordonnées prêtes à implémenter en TDD.

## Installation

### Windows (PowerShell)
```powershell
git clone https://github.com/Fatma-Mi/claude-skills.git
Copy-Item -Recurse claude-skills\skills\* $env:USERPROFILE\.claude\skills\
```

### macOS / Linux
```bash
git clone https://github.com/Fatma-Mi/claude-skills.git
cp -r claude-skills/skills/* ~/.claude/skills/
```

### Mise à jour
```powershell
cd claude-skills
git pull
Copy-Item -Recurse -Force skills\* $env:USERPROFILE\.claude\skills\
```

## Utilisation

Une fois installé, invoque un skill avec `/<nom>` dans Claude Code.

### `/review` — revue de code
- `/review` — tous les fichiers modifiés
- `/review <chemin>` — restreindre à un fichier ou dossier
- `/review py` — restreindre à un type/extension
- `/review HEAD~3..HEAD` — revue d'une plage de commits

### `/write-tests` — génération de tests
- `/write-tests <chemin>` — tester un fichier ou dossier
- `/write-tests <symbole>` — tester une fonction/classe précise
- `/write-tests HEAD~1..HEAD` — couvrir les changements récents

### `/ship` — commit + push
- `/ship` — détecte type/scope automatiquement
- `/ship feat` — forcer le type
- `/ship "fix(api): corrige le parsing"` — message complet imposé

### `/explain` — comprendre du code
- `/explain <chemin>` — expliquer un fichier
- `/explain <symbole>` — expliquer une fonction/classe
- `/explain "fichier.py:42-80"` — expliquer une plage de lignes

### `/debug` — corriger un bug
- `/debug <description du bug>` — décrire le comportement observé
- `/debug "<message d'erreur>"` — partir d'une exception ou stacktrace
- `/debug <étapes de reproduction>` — fournir le chemin de repro

### `/refactor` — restructurer sans changer le comportement
- `/refactor <chemin>` — restructurer un fichier ou dossier
- `/refactor <symbole>` — restructurer une fonction/classe précise
- `/refactor "découpe ce module en deux"` — décrire la restructuration voulue

### `/plan` — concevoir avant de coder
- `/plan <description de la fonctionnalité>` — explorer les options, produire le doc technique + l'ADR
- `/plan "<besoin + contraintes (volume, deadline, stack)>"` — cadrer avec les contraintes connues

## Contribuer

PR bienvenues. Conventions :
- Chaque skill vit dans `skills/<nom>/` avec un `SKILL.md` (obligatoire).
- Le frontmatter du `SKILL.md` doit contenir `description` (avec mots-clés de déclenchement) et `argument-hint` si le skill accepte des arguments.
- Garder les skills **génériques** : un skill spécifique à un projet a sa place dans le `.claude/skills/` du dépôt concerné, pas ici.
