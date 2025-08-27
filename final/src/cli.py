from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Dict

from src.pipeline.ingest import IngestItem, run_ingest
from src.utils.config import load_config
from src.store.chroma_store import ChromaStore


def cmd_ingest(args: argparse.Namespace) -> None:
    items = [
        IngestItem(subject=args.subject, semester=args.semester, book_title=args.book_title, source_path=args.path)
    ]
    run_ingest(items)


def cmd_delete(args: argparse.Namespace) -> None:
    cfg = load_config()
    store = ChromaStore(cfg["storage"]["chroma_path"])
    where: Dict[str, Any] = {}
    for key in ["subject", "semester", "book_title", "source_path"]:
        val = getattr(args, key)
        if val:
            where[key] = val
    if args.modality:
        where["modality"] = args.modality
    # delete both collections
    store.delete_text(where=where or None)
    store.delete_image(where=where or None)


def cmd_list(args: argparse.Namespace) -> None:
    cfg = load_config()
    store = ChromaStore(cfg["storage"]["chroma_path"])
    # Chroma doesn't expose list directly; use where + query on dummy vector workaround is non-ideal.
    # For simplicity, we will just print a message instructing to query via admin API.
    print("Use admin API /items to list entries with filters.")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Vector DB ingestion CLI")
    sub = p.add_subparsers(dest="cmd")

    ing = sub.add_parser("ingest", help="Ingest a PDF")
    ing.add_argument("--subject", required=True)
    ing.add_argument("--semester", required=True)
    ing.add_argument("--book_title", required=True)
    ing.add_argument("--path", required=True, help="Path to PDF")
    ing.set_defaults(func=cmd_ingest)

    dele = sub.add_parser("delete", help="Delete items by filters")
    dele.add_argument("--subject")
    dele.add_argument("--semester")
    dele.add_argument("--book_title")
    dele.add_argument("--source_path")
    dele.add_argument("--modality", choices=["text", "image"])
    dele.set_defaults(func=cmd_delete)

    ls = sub.add_parser("list", help="List items (use admin API)")
    ls.set_defaults(func=cmd_list)

    return p


def main() -> None:
    p = build_parser()
    args = p.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        p.print_help()


if __name__ == "__main__":
    main()
