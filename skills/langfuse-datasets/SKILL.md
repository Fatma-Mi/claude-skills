---
name: langfuse-datasets
description: Gestion COLLABORATIVE des datasets Langfuse à plusieurs collègues en même temps — créer/lister/lire un dataset, créer/modifier/supprimer des items (input + expected output), avec contrôle de concurrence optimiste basé sur la version (updated_at) pour qu'un collègue n'écrase pas le travail d'un autre. Utiliser quand l'utilisateur veut créer un dataset, ajouter/modifier/supprimer des cas (input/expected output), ou travailler à plusieurs sur les mêmes datasets Langfuse.
allowed-tools:
  - Bash(.venv/Scripts/python .claude/skills/langfuse-datasets/scripts/datasets.py *)
---

# Langfuse Datasets — édition collaborative

Skill dédié au travail **à plusieurs collègues en même temps** sur les datasets
Langfuse : création de dataset, création/modification/suppression d'items
(`input` + `expected output`), avec un **verrou optimiste** pour éviter qu'un
collègue écrase le travail d'un autre.

> Ce skill se concentre sur l'écriture concurrente des datasets
> (création, édition et suppression d'items).

## Outils du skill

Toutes les opérations passent par un **seul** helper, `scripts/datasets.py`,
qui s'appuie sur le **SDK Python** (`langfuse>=4`, déjà installé dans `.venv`) et
ajoute la logique de concurrence. Un seul point d'entrée = une interface
cohérente et un seul format pour le jeton de version (lecture comme écriture).

| Opération                         | Outil               |
|-----------------------------------|---------------------|
| Créer / lister / lire un dataset  | `datasets.py`    |
| Créer / modifier un item          | `datasets.py`    |
| Supprimer un item                 | `datasets.py`    |
| Supprimer un **dataset entier**   | ❌ API impossible → **UI Langfuse seulement** |

## Pré-requis

- `.venv` du projet activé/disponible (le helper s'exécute via `.venv/Scripts/python`).
- Un fichier `.env.langfuse` (clés nues, gitignoré) avec :
  `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST`, et
  `LANGFUSE_USER` (ton nom — sert à la traçabilité `created_by`/`edited_by`).
- **Tous les collègues pointent leurs clés vers le MÊME projet Langfuse** — c'est
  ce qui rend le travail commun possible : chacun voit et modifie les mêmes
  datasets en temps réel. Chacun peut avoir ses propres clés (recommandé pour
  l'audit) tant qu'elles sont dans le même projet.

Toujours invoquer le helper ainsi :

```bash
.venv/Scripts/python .claude/skills/langfuse-datasets/scripts/datasets.py <commande> [options]
```

Ajouter `--json` pour une sortie machine, `--env <fichier>` pour un autre `.env`.

> ⚠️ `--json` et `--env` sont des **options globales** : les placer **avant** la
> sous-commande, sinon argparse les rejette (stdout vide).
> ✅ `datasets.py --json item-get --id X`
> ❌ `datasets.py item-get --id X --json`

## Le modèle de concurrence (à comprendre avant tout)

Langfuse n'a **pas** de numéro de version monotone. On utilise `updated_at`
(horodatage renvoyé par l'API) comme **jeton de version** :

1. On **lit** l'item (`item-get` / `dataset-show`) → on note sa `version`.
2. Pour **modifier**, on repasse cette version via `--expect-version <version>` :
   - version serveur **identique** → personne n'a touché → écriture appliquée ;
   - version serveur **différente** → un collègue a modifié entre-temps →
     **CONFLIT** : le script affiche la diff et **n'écrit pas** (sortie code 2).

C'est exactement « le script retourne la version ; si identique c'est bon, si
elle a changé on alerte ». C'est du **contrôle optimiste** (compare-and-set).

> **Limite honnête** : il reste une micro-fenêtre entre la relecture et
> l'écriture (l'API n'offre pas de compare-and-swap atomique). Suffisant pour
> une petite équipe. Pour **zéro collision possible**, préfixer les `id` par
> collègue (voir convention ci-dessous).

### Convention d'`id` recommandée

Les items sont **upsertés sur leur `id`** (unique au niveau projet). Choisir un
`id` **stable et déterministe** :

- Travail vraiment partagé sur les mêmes cas → `id` métier (`cas-01`, `dossier-A12`)
  + **toujours** utiliser `--expect-version` pour modifier.
- Pour éliminer tout risque d'écrasement → préfixer par collègue :
  `fatma__cas-01`, `omar__cas-01`. Chacun ne touche que ses items.

Modifier un item = **ré-`item-set` avec le même `id`** (pas de commande update
séparée : l'upsert s'en charge).

## Recettes

### Créer un dataset
```bash
.venv/Scripts/python .claude/skills/langfuse-datasets/scripts/datasets.py \
  dataset-create --name "mon-dataset" --description "à quoi il sert"
```
Idempotent : relancer sur un nom existant ne casse rien.

### Lister les datasets / voir le contenu d'un dataset
```bash
... datasets.py datasets
... datasets.py dataset-show --name "mon-dataset"   # liste id + version de chaque item
```

### Créer un item (input + expected output)
```bash
... datasets.py item-set --dataset "mon-dataset" --id cas-01 \
    --input '{"question":"âge du patient ?"}' \
    --expected-output '{"field":"age","value":42}'
```
`--input` / `--expected-output` acceptent : du **JSON inline**, un **`@chemin/fichier.json`**,
ou du **texte brut**. Sur Windows/PowerShell, préférer `@fichier.json` pour éviter
les galères de guillemets.

### Metadata & traçabilité (ne pas l'oublier !)

Le `metadata` d'un item est **important** pour un dataset partagé : il porte la
**traçabilité** et l'**intention** de l'item. Le script l'alimente automatiquement.

- **`created_by` / `edited_by`** : injectés automatiquement à chaque `item-set`
  depuis `LANGFUSE_USER` (`.env.langfuse`). `created_by` est posé à la création
  et **préservé** ensuite ; `edited_by` est mis à jour à chaque modification.
- **`--description "…"`** : courte phrase sur **ce que l'item teste** (auto-doc).
- **`--review-status {draft|reviewed|approved}`** : statut de revue ; pose aussi
  `reviewed_by`. Utile pour le suivi à plusieurs (« items pas encore relus »).
- **`--metadata '{...}'`** : JSON libre, fusionné avec les champs ci-dessus.

```bash
# création tracée + description
... datasets.py item-set --dataset "mon-dataset" --id cas-01 \
    --input @in.json --expected-output @out.json \
    --description "cas limite : dose vs concentration"
# -> metadata: {created_by, description}

# passage en revue (après lecture de la version)
... datasets.py item-set --dataset "mon-dataset" --id cas-01 \
    --input @in.json --expected-output @out.json \
    --review-status reviewed --expect-version "<version>"
# -> metadata: {..., review_status: "reviewed", reviewed_by, edited_by}
```

> Si `LANGFUSE_USER` n'est pas défini, le script **avertit** mais n'échoue pas
> (la traçabilité est simplement omise).

### Créer un item avec une IMAGE (ou audio/pdf) en input
```bash
... datasets.py item-set --dataset "mon-dataset" --id ordo-01 \
    --input-media-inline "ordonnance.jpg" \
    --expected-output '{"nom":"Metformine"}'
```
`--input-media-inline` encode le fichier en `data:<mime>;base64,...` et le stocke
**directement dans l'input** — ça marche sans config serveur. Formats :
`.jpg/.jpeg/.png/.webp/.gif`, `.pdf`, `.mp3/.wav`
(type MIME déduit de l'extension, sinon `--input-media-type image/jpeg`).
`--expected-output` est optionnel ici (à remplir plus tard).

> Contrepartie : l'image vit dans le champ input → item **plus lourd**
> (~+33 % vs binaire). Convient aux petites images / petits volumes.
> Alternative sans upload : mettre une **URL d'image externe** dans `--input`
> (l'UI la rend si le format est reconnu).

### Modifier un item EN SÉCURITÉ (flux collaboratif)
```bash
# 1. lire la version actuelle
... datasets.py item-get --id cas-01
# 2. modifier en passant la version lue
... datasets.py item-set --dataset "mon-dataset" --id cas-01 \
    --input @cas-01.input.json --expected-output @cas-01.expected.json \
    --expect-version "2026-06-15T12:28:13.520000+00:00"
```
Si un collègue a modifié l'item entre-temps → **CONFLIT** (code 2), aucune
écriture. On relit (`item-get`), on intègre, on réessaie avec la nouvelle version.

### Supprimer un item (avec vérif optionnelle)
```bash
... datasets.py item-delete --id cas-01 --expect-version "<version-lue>"
```

## Règles de comportement pour l'agent

1. **Documentation first** : si un doute sur une capacité de l'API/SDK, vérifier
   dans le code du SDK (`.venv/.../langfuse`) ou la doc officielle avant
   d'affirmer. Ne pas inventer de flags.
2. **Jamais d'écrasement silencieux à plusieurs** : pour toute *modification*
   d'un item existant, lire d'abord la version puis utiliser `--expect-version`.
   N'utiliser `--allow-overwrite` que si l'utilisateur l'a explicitement demandé
   et travaille seul.
3. **Confirmer les suppressions** : la suppression d'item est **irréversible**.
   Confirmer avec l'utilisateur, et la suppression d'un dataset entier se fait
   **dans l'UI** (impossible via API).
4. **Sur conflit (code 2)** : ne pas réessayer en force. Montrer la diff à
   l'utilisateur, relire l'item, proposer la fusion, puis réécrire avec la
   version à jour.
5. **Toujours rapporter la `version`** renvoyée après une écriture, pour que le
   collègue puisse enchaîner sa prochaine modification.
6. **Coordination** : si plusieurs collègues éditent les mêmes cas, rappeler la
   convention d'`id` (préfixe par collègue) pour éviter les conflits répétés.
