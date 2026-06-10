"""
commands/branch.py  —  mygit branch [<name>]

With no argument: list all branches, highlighting the current one.
With <name>:       create a new branch at the current HEAD commit.
"""

import os
import sys

from core.objects import find_repo_root
from core.refs    import (
    read_head_sha, read_head_ref,
    write_branch_sha, list_branches,
)

GREEN = "\033[32m"
RESET = "\033[0m"
_NO_COLOR = os.environ.get("NO_COLOR") or os.name == "nt"


def _c(code, text):
    return text if _NO_COLOR else f"{code}{text}{RESET}"


def cmd_branch(args) -> None:
    try:
        repo_root = find_repo_root()
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.name is None:
        # List branches
        current  = read_head_ref(repo_root)
        branches = list_branches(repo_root)
        if not branches:
            print("No branches yet.")
            return
        for b in branches:
            if b == current:
                print(_c(GREEN, f"* {b}"))
            else:
                print(f"  {b}")
    else:
        # Create new branch
        head_sha = read_head_sha(repo_root)
        if head_sha is None:
            print("error: cannot create a branch before making at least one commit.",
                  file=sys.stderr)
            sys.exit(1)
        branch_name = args.name
        # Check it doesn't already exist
        existing = list_branches(repo_root)
        if branch_name in existing:
            print(f"error: branch '{branch_name}' already exists.", file=sys.stderr)
            sys.exit(1)
        write_branch_sha(branch_name, head_sha, repo_root)
        print(f"Branch '{branch_name}' created at {head_sha[:7]}.")
