"""
commands/log.py  —  mygit log [-n N]

Walk the commit chain starting from HEAD, printing each commit's
SHA, author, date, and message — similar to `git log --oneline` extended.
"""

import os
import sys
import datetime

from core.objects import find_repo_root, read_commit
from core.refs    import read_head_sha, read_head_ref


YELLOW  = "\033[33m"
CYAN    = "\033[36m"
GREEN   = "\033[32m"
RESET   = "\033[0m"
BOLD    = "\033[1m"

_NO_COLOR = os.environ.get("NO_COLOR") or os.name == "nt"


def _c(code: str, text: str) -> str:
    return text if _NO_COLOR else f"{code}{text}{RESET}"


def cmd_log(args) -> None:
    try:
        repo_root = find_repo_root()
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

    sha = read_head_sha(repo_root)
    if sha is None:
        print("No commits yet.")
        return

    branch = read_head_ref(repo_root)
    limit  = args.count
    count  = 0        

    while sha:
        if limit is not None and count >= limit:
            break

        commit = read_commit(sha, repo_root)
        ts     = datetime.datetime.fromtimestamp(commit["timestamp"])
        date   = ts.strftime("%a %b %d %H:%M:%S %Y")


        decoration = ""
        if count == 0:
            decoration = f" {_c(CYAN, f'(HEAD -> {branch})')}"
        print(_c(YELLOW, f"commit {sha}") + decoration)
        print(f"Author: {commit['author']}")
        print(f"Date:   {date}")
        print()

        for line in commit["message"].splitlines():
            print(f"    {line}")
        print()

        sha   = commit.get("parent")
        count += 1

    if count == 0:
        print("No commits found.")
