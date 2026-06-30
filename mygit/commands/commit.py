"""
commands/commit.py  —  mygit commit -m "<message>"

Steps:
  1. Read the current index.
  2. Create a tree object from the index entries.
  3. Create a commit object pointing to that tree (and the previous commit).
  4. Advance HEAD (via the current branch ref) to the new commit SHA.
"""

import os
import sys
import time
import configparser

from core.objects import find_repo_root, write_tree, write_commit
from core.index   import read_index
from core.refs    import read_head_sha, write_head_sha


def _read_author(repo_root: str) -> str:
    """Read author name/email from .mygit/config."""
    config_path = os.path.join(repo_root, ".mygit", "config")
    if not os.path.exists(config_path):
        return "Unnamed User <user@example.com>"
    cfg = configparser.ConfigParser()
    cfg.read(config_path)
    name  = cfg.get("user", "name",  fallback="Unnamed User").strip()
    email = cfg.get("user", "email", fallback="user@example.com").strip()
    return f"{name} <{email}>"


def cmd_commit(args) -> None:
    try:
        repo_root = find_repo_root()
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

    index = read_index(repo_root)
    if not index:
        print("error: nothing to commit — the staging area is empty.", file=sys.stderr)
        print("       Use 'mygit add <file>' to stage files first.")
        sys.exit(1)

    entries = list(index.items()) 
    tree_sha = write_tree(entries, repo_root)

    parent_sha = read_head_sha(repo_root)

    if parent_sha:
        from core.objects import read_commit
        prev = read_commit(parent_sha, repo_root)
        if prev["tree"] == tree_sha:
            print("Nothing to commit — working tree is clean (no changes since last commit).")
            return
        
    author    = _read_author(repo_root)
    timestamp = int(time.time())
    message   = args.message.strip()


    commit_sha = write_commit(
        tree_sha   = tree_sha,
        message    = message,
        author     = author,
        timestamp  = timestamp,
        parent_sha = parent_sha,
        repo_root  = repo_root,
    )

    write_head_sha(commit_sha, repo_root)

    short = commit_sha[:7]
    is_root = "" if parent_sha else " (root-commit)"
    print(f"[{_current_branch(repo_root)}{is_root} {short}] {message}")
    print(f"  tree:   {tree_sha[:7]}")
    print(f"  files:  {len(index)}")


def _current_branch(repo_root: str) -> str:
    head_file = os.path.join(repo_root, ".mygit", "HEAD")
    with open(head_file, "r") as f:
        content = f.read().strip()
    if content.startswith("ref: refs/heads/"):
        return content[len("ref: refs/heads/"):]
    return content[:7]  # detached
