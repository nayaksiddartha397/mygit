"""
core/index.py

The index (staging area) maps relative file paths to their blob SHA.

On-disk format (simple text, one entry per line):
    <sha_hex> <relative_path>

Example:
    a3f5c1... src/main.py
    9d2b44... README.md

The index lives at .mygit/index.
"""

import os
import fnmatch

# ---------------------------------------------------------------------------
# Index path
# ---------------------------------------------------------------------------

def index_path(repo_root: str) -> str:
    return os.path.join(repo_root, ".mygit", "index")


# ---------------------------------------------------------------------------
# Read / write
# ---------------------------------------------------------------------------

def read_index(repo_root: str) -> dict[str, str]:
    """Returns {relative_path: sha_hex}.  Empty dict if index doesn't exist."""
    path = index_path(repo_root)
    if not os.path.exists(path):
        return {}
    index: dict[str, str] = {}
    with open(path, "r") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line:
                continue
            sha, rel_path = line.split(" ", 1)
            index[rel_path] = sha
    return index


def write_index(index: dict[str, str], repo_root: str) -> None:
    """Persist {relative_path: sha_hex} to disk."""
    path = index_path(repo_root)
    with open(path, "w") as f:
        for rel_path, sha in sorted(index.items()):
            f.write(f"{sha} {rel_path}\n")


def stage_file(rel_path: str, sha: str, repo_root: str) -> None:
    """Add or update a single entry in the index."""
    idx = read_index(repo_root)
    idx[rel_path] = sha
    write_index(idx, repo_root)


def unstage_file(rel_path: str, repo_root: str) -> None:
    idx = read_index(repo_root)
    idx.pop(rel_path, None)
    write_index(idx, repo_root)


# ---------------------------------------------------------------------------
# .mygitignore support
# ---------------------------------------------------------------------------

def load_ignore_patterns(repo_root: str) -> list[str]:
    """Read .mygitignore and return a list of glob patterns."""
    ignore_file = os.path.join(repo_root, ".mygitignore")
    if not os.path.exists(ignore_file):
        return []
    patterns = []
    with open(ignore_file, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                patterns.append(line)
    return patterns


def is_ignored(rel_path: str, patterns: list[str]) -> bool:
    """Return True if rel_path matches any ignore pattern.

    Supports:
    - Glob patterns:       *.pyc, build/*.o
    - Directory patterns:  cache/  (trailing slash → match anything inside)
    - Bare names:          __pycache__  (match anywhere in path)
    """
    basename = os.path.basename(rel_path)
    # Normalise to forward slashes
    rel_path = rel_path.replace(os.sep, "/")

    for pattern in patterns:
        pat = pattern.rstrip("/")
        is_dir_pattern = pattern.endswith("/")

        # 1. Exact or glob match on the full relative path
        if fnmatch.fnmatch(rel_path, pat):
            return True

        # 2. Basename-only match  (e.g. "*.pyc" matches "src/foo.pyc")
        if fnmatch.fnmatch(basename, pat):
            return True

        # 3. Directory prefix match  (e.g. "cache/" matches "cache/temp.txt")
        if is_dir_pattern:
            if rel_path.startswith(pat + "/") or rel_path == pat:
                return True

        # 4. Any path component match  (e.g. "__pycache__" matches "src/__pycache__/x.pyc")
        parts = rel_path.split("/")
        for part in parts[:-1]:   # directory components only
            if fnmatch.fnmatch(part, pat):
                return True

    return False
