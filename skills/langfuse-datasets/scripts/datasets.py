#!/usr/bin/env python
"""Gestion collaborative des datasets Langfuse (CRUD + verrou optimiste).

Ce helper s'appuie sur le SDK Python (`langfuse>=4`) pour couvrir tout le cycle
de vie d'un dataset et de ses items, et ajoute un contrôle de concurrence
OPTIMISTE pour le travail à plusieurs.

Modèle de version
-----------------
Langfuse n'a pas de numéro de version monotone. On utilise `updated_at`
(horodatage renvoyé par l'API) comme JETON DE VERSION.

  1. `item-get` / `dataset-show` affichent l'`id` + la `version` de chaque item.
  2. Pour modifier sans risque : on passe `--expect-version <version-lue>`.
     - version actuelle == version attendue  -> personne n'a touché -> écriture OK
     - version actuelle != version attendue  -> un collègue a modifié -> CONFLIT,
       on affiche la diff et on N'ÉCRIT PAS (code de sortie 2).

Limite honnête : il reste une micro-fenêtre TOCTOU entre la relecture et
l'écriture (l'API n'offre pas de compare-and-swap atomique). Acceptable pour
une petite équipe ; pour zéro collision, préfixer les `id` par collègue.

Usage (toujours via le venv du projet) :
    .venv/Scripts/python .claude/skills/langfuse-datasets/scripts/datasets.py <commande> [options]

Commandes :
    datasets                              Liste tous les datasets
    dataset-create   --name N [--description D] [--metadata J]
    dataset-show     --name N [--limit L] Liste les items (id + version)
    item-get         --id ID
    item-set         --dataset N --id ID (--input J | --input-media-inline FICHIER)
                     [--expected-output J] [--input-media-type MIME]
                     [--metadata J] [--expect-version V] [--allow-overwrite]
    item-delete      --id ID [--expect-version V]

J = JSON inline ('{"k":"v"}'), ou '@chemin/fichier.json', ou texte brut.
V = jeton de version (la chaîne `version` affichée par get/show).

Options globales : --env <fichier> (défaut .env.langfuse), --json (sortie machine).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path


def eprint(*a):
    print(*a, file=sys.stderr)


def load_env(env_file: str) -> None:
    from dotenv import load_dotenv

    p = Path(env_file)
    if not p.exists():
        eprint(f"[!] Fichier d'environnement introuvable : {env_file}")
        eprint("    Crée .env.langfuse avec LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY / LANGFUSE_HOST")
        sys.exit(1)
    load_dotenv(dotenv_path=p, override=True)
    missing = [k for k in ("LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY", "LANGFUSE_HOST") if not os.getenv(k)]
    if missing:
        eprint(f"[!] Variables manquantes dans {env_file} : {', '.join(missing)}")
        sys.exit(1)


def client():
    from langfuse import Langfuse

    return Langfuse(
        public_key=os.environ["LANGFUSE_PUBLIC_KEY"],
        secret_key=os.environ["LANGFUSE_SECRET_KEY"],
        host=os.environ["LANGFUSE_HOST"],
    )


def parse_value(raw):
    """Interprète une valeur d'argument : @fichier -> contenu, sinon JSON, sinon texte brut."""
    if raw is None:
        return None
    if isinstance(raw, str) and raw.startswith("@"):
        path = Path(raw[1:])
        if not path.exists():
            eprint(f"[!] Fichier introuvable : {path}")
            sys.exit(1)
        raw = path.read_text(encoding="utf-8")
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return raw  # texte brut accepté


def version_of(item) -> str | None:
    ua = getattr(item, "updated_at", None)
    if ua is None:
        return None
    return ua.isoformat() if isinstance(ua, datetime) else str(ua)


def same_version(a: str | None, b: str | None) -> bool:
    if a is None or b is None:
        return a == b
    if a == b:
        return True
    # comparaison tolérante aux formats d'horodatage
    try:
        return datetime.fromisoformat(a.replace("Z", "+00:00")) == datetime.fromisoformat(
            b.replace("Z", "+00:00")
        )
    except ValueError:
        return False


def get_item_or_none(lf, item_id):
    from langfuse.api.core.api_error import ApiError

    try:
        return lf.api.dataset_items.get(item_id)
    except ApiError as e:
        if getattr(e, "status_code", None) == 404:
            return None
        raise


def emit(obj, as_json):
    if as_json:
        print(json.dumps(obj, ensure_ascii=False, indent=2, default=str))
    return obj


# --------------------------------------------------------------------------- #
# Média (images / audio / pdf) -> encodé base64 inline dans l'item
# --------------------------------------------------------------------------- #
_MEDIA_TYPES = {
    ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
    ".webp": "image/webp", ".gif": "image/gif",
    ".pdf": "application/pdf",
    ".mp3": "audio/mpeg", ".mpeg": "audio/mpeg", ".wav": "audio/wav",
    ".txt": "text/plain",
}


def guess_content_type(path):
    return _MEDIA_TYPES.get(Path(path).suffix.lower())


def file_to_data_uri(file_path, content_type):
    """Encode un fichier en data URI base64 (`data:<mime>;base64,...`) à stocker
    TEL QUEL dans le champ input de l'item. Attention : alourdit l'item (~+33 %)."""
    import base64

    if not Path(file_path).exists():
        eprint(f"[!] Fichier média introuvable : {file_path}")
        sys.exit(1)
    if content_type is None:
        content_type = guess_content_type(file_path)
    if content_type is None:
        eprint(f"[!] Type de média indéterminé pour {file_path}. Précise --input-media-type.")
        sys.exit(1)
    data = Path(file_path).read_bytes()
    return f"data:{content_type};base64," + base64.b64encode(data).decode()


# --------------------------------------------------------------------------- #
# Commandes
# --------------------------------------------------------------------------- #
def cmd_datasets(lf, args):
    res = lf.api.datasets.list(limit=args.limit)
    rows = [{"name": d.name, "description": d.description, "version": version_of(d)} for d in res.data]
    if args.json:
        emit(rows, True)
    else:
        if not rows:
            print("(aucun dataset)")
        for r in rows:
            print(f"- {r['name']:<40} {r['description'] or ''}")
    return rows


def cmd_dataset_create(lf, args):
    d = lf.api.datasets.create(
        name=args.name,
        description=args.description,
        metadata=parse_value(args.metadata),
    )
    out = {"name": d.name, "id": d.id, "version": version_of(d)}
    if args.json:
        emit(out, True)
    else:
        print(f"[OK] dataset '{d.name}' créé/présent  (version {out['version']})")
    return out


def cmd_dataset_show(lf, args):
    res = lf.api.dataset_items.list(dataset_name=args.name, limit=args.limit)
    rows = [
        {"id": it.id, "status": str(it.status), "version": version_of(it), "input": it.input}
        for it in res.data
    ]
    if args.json:
        emit(rows, True)
    else:
        print(f"Dataset '{args.name}' — {len(rows)} item(s) :")
        for r in rows:
            print(f"  {r['id']:<32} [{r['status']:<8}] version={r['version']}")
    return rows


def cmd_item_get(lf, args):
    it = get_item_or_none(lf, args.id)
    if it is None:
        eprint(f"[!] Item introuvable : {args.id}")
        sys.exit(1)
    out = {
        "id": it.id,
        "dataset": it.dataset_name,
        "status": str(it.status),
        "version": version_of(it),
        "input": it.input,
        "expected_output": it.expected_output,
        "metadata": it.metadata,
    }
    if args.json:
        emit(out, True)
    else:
        print(f"id      : {out['id']}")
        print(f"dataset : {out['dataset']}")
        print(f"status  : {out['status']}")
        print(f"version : {out['version']}   <-- à passer en --expect-version pour modifier")
        print(f"input            : {json.dumps(out['input'], ensure_ascii=False)}")
        print(f"expected_output  : {json.dumps(out['expected_output'], ensure_ascii=False)}")
    return out


def current_user() -> str | None:
    """Nom de l'utilisateur courant (traçabilité), lu depuis LANGFUSE_USER."""
    u = os.getenv("LANGFUSE_USER")
    return u.strip() if u and u.strip() else None


def build_item_metadata(current, args) -> dict | None:
    """Metadata de l'item : conserve l'existant, fusionne --metadata, puis injecte
    la traçabilité — `created_by` à la création, `edited_by` à la modification
    (`created_by` est PRÉSERVÉ). Ajoute `description` et `review_status`/`reviewed_by`
    si fournis."""
    meta: dict = {}
    if current is not None and isinstance(getattr(current, "metadata", None), dict):
        meta = dict(current.metadata)  # repart de l'existant -> préserve created_by
    extra = parse_value(args.metadata)
    if isinstance(extra, dict):
        meta.update(extra)

    user = current_user()
    if user is None:
        eprint("[i] LANGFUSE_USER non défini dans .env.langfuse -> traçabilité (created_by/edited_by) ignorée.")

    if current is None:  # création
        if user:
            meta.setdefault("created_by", user)
    else:  # modification
        if user:
            meta["edited_by"] = user

    if getattr(args, "description", None) is not None:
        meta["description"] = args.description
    if getattr(args, "review_status", None) is not None:
        meta["review_status"] = args.review_status
        if user:
            meta["reviewed_by"] = user

    return meta or None


def cmd_item_set(lf, args):
    if not args.input and not args.input_media_inline:
        eprint("[!] Fournis --input (texte/JSON) ou --input-media-inline (image/audio/pdf en base64).")
        sys.exit(1)

    current = get_item_or_none(lf, args.id) if args.id else None
    current_version = version_of(current) if current else None

    # --- contrôle de concurrence optimiste ---
    if args.expect_version is not None:
        if current is None:
            eprint("[CONFLIT] L'item attendu n'existe plus (supprimé par un collègue ?).")
            eprint(f"          version attendue : {args.expect_version}")
            sys.exit(2)
        if not same_version(current_version, args.expect_version):
            eprint("[CONFLIT] L'item a été modifié par un collègue depuis ta lecture.")
            eprint(f"          version attendue : {args.expect_version}")
            eprint(f"          version actuelle : {current_version}")
            eprint("          --- input actuel côté serveur ---")
            eprint(json.dumps(current.input, ensure_ascii=False, indent=2))
            eprint("          --- expected_output actuel côté serveur ---")
            eprint(json.dumps(current.expected_output, ensure_ascii=False, indent=2))
            eprint("Relis l'item (item-get), intègre les changements, puis réessaie")
            eprint("avec la nouvelle --expect-version.")
            sys.exit(2)
    elif current is not None and not args.allow_overwrite:
        eprint(f"[!] L'item '{args.id}' existe déjà (version {current_version}).")
        eprint("    Pour modifier en sécurité : --expect-version " + str(current_version))
        eprint("    Pour écraser sans vérifier : --allow-overwrite (déconseillé à plusieurs)")
        sys.exit(2)

    # input : média base64 inline, ou valeur classique (JSON/@fichier/texte)
    if args.input_media_inline:
        input_value = file_to_data_uri(args.input_media_inline, args.input_media_type)
    else:
        input_value = parse_value(args.input)

    metadata = build_item_metadata(current, args)

    it = lf.api.dataset_items.create(
        dataset_name=args.dataset,
        id=args.id,
        input=input_value,
        expected_output=parse_value(args.expected_output),
        metadata=metadata,
    )
    out = {"id": it.id, "dataset": it.dataset_name, "version": version_of(it),
           "previous_version": current_version}
    if args.json:
        emit(out, True)
    else:
        action = "modifié" if current else "créé"
        print(f"[OK] item '{it.id}' {action}  (version {out['version']})")
        if current_version:
            print(f"     version précédente : {current_version}")
    return out


def cmd_item_delete(lf, args):
    if args.expect_version is not None:
        current = get_item_or_none(lf, args.id)
        if current is None:
            eprint(f"[!] Item déjà absent : {args.id} (rien à supprimer).")
            sys.exit(0)
        if not same_version(version_of(current), args.expect_version):
            eprint("[CONFLIT] L'item a changé depuis ta lecture — suppression annulée.")
            eprint(f"          version attendue : {args.expect_version}")
            eprint(f"          version actuelle : {version_of(current)}")
            sys.exit(2)
    lf.api.dataset_items.delete(args.id)
    out = {"id": args.id, "deleted": True}
    if args.json:
        emit(out, True)
    else:
        print(f"[OK] item '{args.id}' supprimé")
    return out


def build_parser():
    p = argparse.ArgumentParser(description="Gestion collaborative des datasets Langfuse")
    p.add_argument("--env", default=".env.langfuse", help="Fichier d'environnement (défaut .env.langfuse)")
    p.add_argument("--json", action="store_true", help="Sortie JSON machine")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("datasets", help="Liste tous les datasets")
    s.add_argument("--limit", type=int, default=100)
    s.set_defaults(func=cmd_datasets)

    s = sub.add_parser("dataset-create", help="Crée un dataset")
    s.add_argument("--name", required=True)
    s.add_argument("--description")
    s.add_argument("--metadata")
    s.set_defaults(func=cmd_dataset_create)

    s = sub.add_parser("dataset-show", help="Liste les items d'un dataset (id + version)")
    s.add_argument("--name", required=True)
    s.add_argument("--limit", type=int, default=100)
    s.set_defaults(func=cmd_dataset_show)

    s = sub.add_parser("item-get", help="Lit un item (affiche sa version)")
    s.add_argument("--id", required=True)
    s.set_defaults(func=cmd_item_get)

    s = sub.add_parser("item-set", help="Crée ou modifie un item (input + expected output)")
    s.add_argument("--dataset", required=True)
    s.add_argument("--id", help="id stable de l'item (upsert). Omis = nouvel id auto.")
    s.add_argument("--input", help="JSON, @fichier.json, ou texte brut")
    s.add_argument("--input-media-inline", dest="input_media_inline",
                   help="Fichier image/audio/pdf encodé en base64 stocké DIRECTEMENT "
                        "dans l'input. Alourdit l'item.")
    s.add_argument("--input-media-type", dest="input_media_type",
                   help="Type MIME du média si non déduit de l'extension (ex: image/jpeg)")
    s.add_argument("--expected-output", dest="expected_output",
                   help="JSON, @fichier.json, ou texte brut (optionnel)")
    s.add_argument("--metadata", help="JSON libre fusionné dans le metadata de l'item")
    s.add_argument("--description", help="Courte description : ce que l'item teste (-> metadata)")
    s.add_argument("--review-status", dest="review_status",
                   choices=["draft", "reviewed", "approved"],
                   help="Statut de revue (-> metadata.review_status + reviewed_by)")
    s.add_argument("--expect-version", dest="expect_version",
                   help="Version lue avant modification (verrou optimiste)")
    s.add_argument("--allow-overwrite", action="store_true",
                   help="Écrase un item existant sans vérifier la version (déconseillé)")
    s.set_defaults(func=cmd_item_set)

    s = sub.add_parser("item-delete", help="Supprime un item")
    s.add_argument("--id", required=True)
    s.add_argument("--expect-version", dest="expect_version",
                   help="Version lue avant suppression (verrou optimiste)")
    s.set_defaults(func=cmd_item_delete)

    return p


def main():
    args = build_parser().parse_args()
    load_env(args.env)
    lf = client()
    try:
        args.func(lf, args)
    finally:
        try:
            lf.flush()
        except Exception:
            pass


if __name__ == "__main__":
    main()
