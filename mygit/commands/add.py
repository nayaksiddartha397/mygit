"""
commands/add.py  —  mygit add <file> [<file> ...]

For each file:
  1. Read its bytes.
  2. Hash + store as a blob object.
  3. Update the index (staging area).

Supports glob expansion and .mygitignore.
Paths are always stored relative to the repo root.
"""

import os
import sys
import glob

from core.objects import find_repo_root, hash_blob
from core.index   import stage_file, load_ignore_patterns, is_ignored


def cmd_add(args) -> None:
    try:
        repo_root = find_repo_root()
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

    ignore_patterns = load_ignore_patterns(repo_root)
    staged_count = 0

    for pattern in args.files:
        matches = glob.glob(pattern, recursive=True)
        if not matches:
            matches = [pattern]

        for filepath in matches:
            abs_path = os.path.abspath(filepath)

            # Must be a regular file
            if not os.path.isfile(abs_path):
                if os.path.isdir(abs_path):
                    for root, dirs, files in os.walk(abs_path):
                        # Skip .mygit itself
                        dirs[:] = [d for d in dirs if d != ".mygit"]
                        for fname in files:
                            fpath = os.path.join(root, fname)
                            _add_single(fpath, repo_root, ignore_patterns)
                            staged_count += 1
                else:
                    print(f"warning: '{filepath}' did not match any files", file=sys.stderr)
                continue

            result = _add_single(abs_path, repo_root, ignore_patterns)
            if result:
                staged_count += 1

    # Evict any previously-staged files that are now ignored
    from core.index import read_index, write_index
    idx = read_index(repo_root)
    evicted = []
    for rel_path in list(idx.keys()):
        if is_ignored(rel_path, ignore_patterns):
            del idx[rel_path]
            evicted.append(rel_path)
    if evicted:
        write_index(idx, repo_root)

    if staged_count:
        print(f"Staged {staged_count} file(s).")
    else:
        print("Nothing staged.")


def _add_single(abs_path: str, repo_root: str, ignore_patterns: list[str]) -> bool:
    """Hash and stage a single file.  Returns True on success."""
    rel_path = os.path.relpath(abs_path, repo_root)

    rel_path = rel_path.replace(os.sep, "/")

    if rel_path.startswith(".mygit/"):
        return False

    if is_ignored(rel_path, ignore_patterns):
        print(f"  ignored: {rel_path}")
        return False

    try:
        with open(abs_path, "rb") as f:
            data = f.read()
    except OSError as e:
        print(f"error: cannot read '{rel_path}': {e}", file=sys.stderr)
        return False

    sha = hash_blob(data, repo_root)
    stage_file(rel_path, sha, repo_root)
    print(f"  staged: {rel_path} ({sha[:7]})")
    return True
