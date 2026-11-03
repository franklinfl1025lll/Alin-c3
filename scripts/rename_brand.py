#!/usr/bin/env python3
"""Rename the whole board brand (caiyu / Caiyu / CaiYu / 菜鱼狗) in one shot.

Usage:
    python scripts/rename_brand.py --to mydog --zh 我的狗 --dry-run
    python scripts/rename_brand.py --to mydog --zh 我的狗 --author "我的DIY"

Renames directories, files, identifiers, Kconfig symbols, NVS namespaces,
web asset names and user-visible strings. Run it from the project root, then
rebuild to verify.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

SKIP_DIRS = {".git", "build", "managed_components", "releases", "components", "__pycache__", ".vscode"}
SKIP_FILES = {"sdkconfig", "sdkconfig.old", "dependencies.lock"}
TEXT_SUFFIXES = {
    ".c", ".cc", ".cpp", ".h", ".hpp", ".py", ".txt", ".md", ".json", ".txt",
    ".html", ".css", ".js", ".svg", ".yml", ".yaml", ".cmake", ".csv", ".sh",
    ".defaults", ".projbuild", ".gitignore", ".clang-format", "",
}


def build_pairs(old: str, new: str, zh: str, zh_old: str, author: str, author_old: str):
    """Longest / most specific patterns first so nothing gets half-replaced."""
    cap = new[:1].upper() + new[1:]
    pairs = [
        (author_old, author),
        (zh_old, zh),
        (old + "-c3", new + "-c3"),
        ("CAIYU", new.upper()),
        ("CaiYu", cap),
        ("Caiyu", cap),
        ("caiyu", new),
    ]
    return pairs


def is_text(path: Path) -> bool:
    return path.suffix.lower() in TEXT_SUFFIXES or path.name in {".gitignore", ".clang-format"}


def iter_repo(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            yield Path(dirpath) / name


def rename_paths(root: Path, old: str, new: str, dry_run: bool):
    name_pairs = [(old + "-c3", new + "-c3"), (old, new)]
    renames = []
    for path in sorted(root.rglob("*"), key=lambda p: len(str(p)), reverse=True):
        rel = path.relative_to(root)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        new_name = path.name
        for src, dst in name_pairs:  # file/dir names only use the lowercase tiers
            new_name = new_name.replace(src, dst)
        if new_name != path.name:
            renames.append((path, path.with_name(new_name)))
    for src, dst in renames:
        print(("would rename " if dry_run else "rename ") + str(src.relative_to(root)) + " -> " + dst.name)
        if not dry_run:
            src.rename(dst)
    return renames


def rewrite_contents(root: Path, pairs, dry_run: bool):
    changed = 0
    for path in iter_repo(root):
        if not is_text(path) or path.name in SKIP_FILES:
            continue
        if path.resolve() == Path(__file__).resolve():
            continue  # keep this script's own defaults usable for the next rename
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        original = text
        for old, new in pairs:
            if old and old in text:
                text = text.replace(old, new)
        if text != original:
            rel = path.relative_to(root)
            hits = sum(original.count(o) for o, _ in pairs if o)
            print(("would rewrite " if dry_run else "rewrite ") + str(rel) + " (" + str(hits) + " hits)")
            changed += 1
            if not dry_run:
                path.write_text(text, encoding="utf-8")
    return changed


def main():
    parser = argparse.ArgumentParser(description="Rename the caiyu brand across the firmware")
    parser.add_argument("--to", required=True, help="new lowercase English prefix, e.g. mydog")
    parser.add_argument("--zh", required=True, help="new Chinese display name, e.g. 我的狗")
    parser.add_argument("--author", default="", help="author line used on the web console")
    parser.add_argument("--from", dest="old", default="caiyu", help="current prefix (default: caiyu)")
    parser.add_argument("--zh-from", dest="zh_old", default="菜鱼狗", help="current Chinese name")
    parser.add_argument("--author-from", dest="author_old", default="菜鱼的DIY")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not args.to.islower() or not args.to.isalnum():
        print("--to must be lowercase alphanumeric (it becomes directory/file names)", file=sys.stderr)
        return 2

    root = Path(__file__).resolve().parent.parent
    pairs = build_pairs(args.old, args.to, args.zh, args.zh_old, args.author, args.author_old)

    rename_paths(root, args.old, args.to, args.dry_run)
    changed = rewrite_contents(root, pairs, args.dry_run)
    print(("DRY RUN: " if args.dry_run else "") + str(changed) + " files rewritten")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
