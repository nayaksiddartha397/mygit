"""
commands/status.py  —  mygit status

Reports three categories:
  • Changes staged for commit   — in index but different from last commit tree
  • Changes not staged          — in index but working-tree file differs from index blob
  • Untracked files             — on disk, not in index, not ignored
"""

import os
import sys
import hashlib

from core.objects import find_repo_root, read_commit, read_tree, read_blob
from core.index   import read_index, load_ignore_patterns, is_ignored
from core.refs    import read_head_sha, read_head_ref

GREEN  = "\033[32m"
RED    = "\033[31m"
CYAN   = "\033[36m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

_NO_COLOR = os.environ.get("NO_COLOR") or os.name == "nt"


def _c(code, text):
    return text if _NO_COLOR else f"{code}{text}{RESET}"


def _sha_of_file(path: str) -> str | None:
    """Compute the blob SHA of a file on disk without writing it."""
    try:
        with open(path, "rb") as f:
            data = f.read()
    except OSError:
        return None
    header = f"blob {len(data)}\0".encode()
    return hashlib.sha1(header + data).hexdigest()


def cmd_status(args) -> None:
    try:
        repo_root = find_repo_root()
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

    branch   = read_head_ref(repo_root)
    head_sha = read_head_sha(repo_root)
    index    = read_index(repo_root)
    ignore   = load_ignore_patterns(repo_root)

    # Build committed tree map
    committed: dict[str, str] = {}
    if head_sha:
        commit = read_commit(head_sha, repo_root)
        for _mode, name, sha in read_tree(commit["tree"], repo_root):
            committed[name] = sha

    # ---- Staged changes (index vs committed tree) -------------------------
    staged_new      = []
    staged_modified = []
    staged_deleted  = []

    for rel_path, idx_sha in sorted(index.items()):
        committed_sha = committed.get(rel_path)
        if committed_sha is None:
            staged_new.append(rel_path)
        elif committed_sha != idx_sha:
            staged_modified.append(rel_path)

    for rel_path in committed:
        if rel_path not in index:
            staged_deleted.append(rel_path)

    # ---- Unstaged changes (working tree vs index) -------------------------
    unstaged_modified = []
    unstaged_deleted  = []

    for rel_path, idx_sha in sorted(index.items()):
        abs_path = os.path.join(repo_root, rel_path)
        if not os.path.exists(abs_path):
            unstaged_deleted.append(rel_path)
        else:
            disk_sha = _sha_of_file(abs_path)
            if disk_sha != idx_sha:
                unstaged_modified.append(rel_path)

    # ---- Untracked files --------------------------------------------------
    untracked = []
    for dirpath, dirnames, filenames in os.walk(repo_root):
        dirnames[:] = [d for d in dirnames if d != ".mygit"]
        for fname in filenames:
            fp  = os.path.join(dirpath, fname)
            rel = os.path.relpath(fp, repo_root).replace(os.sep, "/")
            if rel not in index and not is_ignored(rel, ignore):
                untracked.append(rel)
    untracked.sort()

    # ---- Print ------------------------------------------------------------
    print(f"On branch {_c(BOLD, branch)}")
    if head_sha is None:
        print("No commits yet")
    print()

    has_something = False

    if staged_new or staged_modified or staged_deleted:
        has_something = True
        print(_c(BOLD, "Changes staged for commit:"))
        print("  (use 'mygit commit -m \"msg\"' to commit)")
        for f in staged_new:
            print(_c(GREEN, f"        new file:   {f}"))
        for f in staged_modified:
            print(_c(GREEN, f"        modified:   {f}"))
        for f in staged_deleted:
            print(_c(GREEN, f"        deleted:    {f}"))
        print()

    if unstaged_modified or unstaged_deleted:
        has_something = True
        print(_c(BOLD, "Changes not staged for commit:"))
        print("  (use 'mygit add <file>' to update what will be committed)")
        for f in unstaged_modified:
            print(_c(RED, f"        modified:   {f}"))
        for f in unstaged_deleted:
            print(_c(RED, f"        deleted:    {f}"))
        print()

    if untracked:
        has_something = True
        print(_c(BOLD, "Untracked files:"))
        print("  (use 'mygit add <file>' to include in commit)")
        for f in untracked:
            print(_c(RED, f"        {f}"))
        print()

    if not has_something:
        print("nothing to commit, working tree clean")
