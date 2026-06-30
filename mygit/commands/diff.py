"""
commands/diff.py  —  mygit diff [<file>]

Compare the working tree against the last commit.
If no commit exists, compare against an empty baseline.

Output is a unified diff (like `git diff`) with ANSI colour.
"""

import os
import sys
import difflib
import datetime

from core.objects import find_repo_root, read_blob, read_tree, read_commit
from core.refs    import read_head_sha
from core.index   import load_ignore_patterns, is_ignored

RED    = "\033[31m"
GREEN  = "\033[32m"
CYAN   = "\033[36m"
BOLD   = "\033[1m"
RESET  = "\033[0m"


_NO_COLOR = os.environ.get("NO_COLOR") or os.name == "nt"


def _c(code: str, text: str) -> str:
    return text if _NO_COLOR else f"{code}{text}{RESET}"


def _colorize_diff(lines):
    """Apply red/green colouring to unified diff lines."""
    for line in lines:
        if line.startswith("+++") or line.startswith("---"):
            yield _c(BOLD, line)
        elif line.startswith("+"):
            yield _c(GREEN, line)
        elif line.startswith("-"):
            yield _c(RED, line)
        elif line.startswith("@@"):
            yield _c(CYAN, line)
        else:
            yield line


def _get_committed_tree(repo_root: str) -> dict[str, str]:
    """Return {rel_path: blob_sha} for the latest commit, or {} if no commits."""
    sha = read_head_sha(repo_root)
    if sha is None:
        return {}
    commit = read_commit(sha, repo_root)
    tree_entries = read_tree(commit["tree"], repo_root)
    return {name: blob_sha for _mode, name, blob_sha in tree_entries}


def _diff_file(rel_path: str, old_sha: str | None, abs_path: str, repo_root: str) -> list[str]:
    """Return unified diff lines for one file."""
    if old_sha:
        old_bytes = read_blob(old_sha, repo_root)
        old_lines = old_bytes.decode(errors="replace").splitlines(keepends=True)
        from_label = f"a/{rel_path}"
    else:
        old_lines  = []
        from_label = "/dev/null"

    if os.path.exists(abs_path):
        with open(abs_path, "rb") as f:
            new_bytes = f.read()
        new_lines = new_bytes.decode(errors="replace").splitlines(keepends=True)
        to_label  = f"b/{rel_path}"
    else:
        new_lines = []
        to_label  = "/dev/null"

    diff = list(difflib.unified_diff(
        old_lines, new_lines,
        fromfile=from_label,
        tofile=to_label,
    ))
    return diff


def cmd_diff(args) -> None:
    try:
        repo_root = find_repo_root()
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

    committed = _get_committed_tree(repo_root)
    cwd       = os.getcwd()


    if args.file:
        abs_path = os.path.abspath(args.file)
        rel_path = os.path.relpath(abs_path, repo_root).replace(os.sep, "/")
        files_to_diff = [(rel_path, abs_path)]
    else:

        all_rel = set(committed.keys())
        ignore_patterns = load_ignore_patterns(repo_root)
        # Walk working tree
        for dirpath, dirnames, filenames in os.walk(repo_root):
            dirnames[:] = [d for d in dirnames if d != ".mygit"]
            for fname in filenames:
                fp  = os.path.join(dirpath, fname)
                rel = os.path.relpath(fp, repo_root).replace(os.sep, "/")
                if not is_ignored(rel, ignore_patterns):
                    all_rel.add(rel)
        files_to_diff = [(r, os.path.join(repo_root, r)) for r in sorted(all_rel)]

    any_diff = False
    for rel_path, abs_path in files_to_diff:
        old_sha = committed.get(rel_path)
        diff_lines = _diff_file(rel_path, old_sha, abs_path, repo_root)
        if diff_lines:
            any_diff = True
            print(_c(BOLD, f"diff --mygit a/{rel_path} b/{rel_path}"))
            for line in _colorize_diff(diff_lines):
                print(line, end="")
            print()

    if not any_diff:
        print("No differences found — working tree matches the last commit.")
