---
name: ship
description: Commit et push propre des changements en cours, avec tests et lint exécutés avant le commit. Message au format conventional commits (`type(scope): description`). Agnostique au langage : détecte les commandes test/lint depuis le manifeste du projet. Ne push jamais si les tests échouent.
when_to_use: Quand l'utilisateur demande de committer et pousser ses changements, de "ship", de "finaliser ce travail", ou avant une PR. Exemples — "ship ça", "commit + push", "envoie sur la branche". Pour un commit local sans push, voir l'arrêt après l'étape 5.
argument-hint: [type|type(scope)|"message complet"]
disable-model-invocation: true
allowed-tools: Bash(git:*) Bash(npm:*) Bash(pnpm:*) Bash(yarn:*) Bash(npx:*) Bash(pytest:*) Bash(python:*) Bash(python3:*) Bash(go:*) Bash(cargo:*) Bash(ruff:*) Bash(eslint:*) Bash(flake8:*) Bash(mypy:*) Bash(prettier:*) Bash(black:*) Bash(rubocop:*) Bash(make:*) Read Grep Glob
---

Effectue un commit et push propre des changements en cours.

Argument fourni par l'utilisateur : `$ARGUMENTS`

## Étapes

1. **Lecture initiale en parallèle** (un seul tour, plusieurs appels Bash) :
   - `git status` (**sans `-uall`** — peut causer des problèmes mémoire sur gros repos)
   - `git diff --stat`
   - `git diff`
   - `git log --oneline -10` (pour repérer la convention en place : langue, format de scope, niveau de détail)

2. **Analyser les fichiers non-trackés** : signaler ceux qui semblent importants (code source, config, tests) ou suspects (`.env`, secrets, dumps, binaires lourds). **Ne jamais stager** un fichier qui ressemble à un secret (`.env`, `*_KEY=…`, clés privées) sauf justification explicite de l'utilisateur.

3. **Lancer les tests** : détecter la commande depuis le manifeste du projet — **jamais inventée**.
   - `package.json` → script `test` (`npm test`, `pnpm test`, `yarn test`)
   - `pyproject.toml` / `requirements.txt` → `pytest`
   - `go.mod` → `go test ./...`
   - `Cargo.toml` → `cargo test`
   - `Gemfile` → `bundle exec rspec`
   - `Makefile` avec cible `test` → `make test`
   - **Aucune commande détectée** → passer silencieusement.

4. **Lancer le linter** : détecter de la même façon (`eslint`, `ruff check`, `flake8`, `golangci-lint`, `cargo clippy`, `rubocop`, `prettier --check`…).
   - **Aucun lint détecté** → passer silencieusement.

5. **Si tests et lint passent** (ou non configurés) :
   - **S'aligner sur la convention** repérée à l'étape 1 (`git log --oneline -10`) : langue, format de scope, niveau de détail.
   - **Détecter la langue** des descriptions depuis les derniers commits (français, anglais, autre). **Ne pas hardcoder** — suivre ce qui domine. Si aucun commit existant, utiliser la langue de l'utilisateur.
   - **Rédiger le message** au format `type(scope): description`.
     - Types : `feat`, `fix`, `docs`, `refactor`, `test`, `chore`.
     - **Scope** — par ordre de priorité :
       1. Si `$ARGUMENTS` fournit un scope explicite → l'utiliser.
       2. Si la branche courante (`git branch --show-current`) matche `[A-Z]+-[0-9]+` (ticket Jira/Linear/…) → extraire le ticket en majuscules comme scope (`feature/do-14156-foo` → `DO-14156`).
       3. Sinon → inférer depuis les fichiers touchés (sous-dossier principal, underscores → tirets).
       4. Si plusieurs scopes touchés sans dominante → omettre le scope (`feat: …`).
     - Description courte (≤ 72 caractères), impératif, sans majuscule, sans point final, dans la langue détectée ci-dessus.
     - Si `$ARGUMENTS` fournit déjà un message complet → l'utiliser après validation du format.
   - **Confirmer** avec l'utilisateur (message + liste des fichiers à stager) avant de poursuivre.
   - **Stager explicitement** les fichiers approuvés : `git add <fichier1> <fichier2>` — **jamais** `git add .` ni `git add -A`.
   - **Commit** :
     ```bash
     git commit -m "$(cat <<'EOF'
     type(scope): description
     EOF
     )"
     ```
   - **Push** : `git push` (ou `git push -u origin HEAD` si pas de tracking). **Jamais** `--force` sans demande explicite. **Jamais** push direct sur `main`/`master` sans confirmation.

6. **Si tests ou lint échouent** :
   - Identifier la cause (bug code vs config).
   - Proposer un correctif à l'utilisateur ; ne pas modifier sans confirmation.
   - Reprendre à l'étape 3.

## Règles d'arrêt

- **Jamais de push si les tests ou le lint échouent** sans correctif validé et re-validation au vert.
- En cas d'erreur git (pre-commit hook échoue, conflit) → ne **jamais** `--amend` ni `--no-verify` sans demande explicite ; corriger la cause et créer un **nouveau** commit.
- Si aucun changement à committer → s'arrêter avec `✓ Rien à commiter.`
