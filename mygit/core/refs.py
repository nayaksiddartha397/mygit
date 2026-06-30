"""
core/refs.py

Helpers for reading and writing Git references.

HEAD contains either:
  - A symbolic ref:  "ref: refs/heads/main"
  - A detached SHA:  "a3f5c1..."

Branch files (.mygit/refs/heads/<name>) contain a bare commit SHA.
"""

import os

# ---------------------------------------------------------------------------
# HEAD
# ---------------------------------------------------------------------------

def head_path(repo_root: str) -> str:
    return os.path.join(repo_root, ".mygit", "HEAD")

# answers which branch am i currently
def read_head_ref(repo_root: str) -> str:
    """
    Return the current branch name (e.g. 'main'), or the detached SHA.
    """
    with open(head_path(repo_root), "r") as f:
        content = f.read().strip()
    if content.startswith("ref: "):
        # symbolic ref — return just the branch name
        ref = content[5:]          # e.g. "refs/heads/main"
        return ref.split("/")[-1]  # e.g. "main"
    return content  # detached HEAD — bare SHA


def read_head_sha(repo_root: str) -> str | None:
    """
    Resolve HEAD to a commit SHA.  Returns None if there are no commits yet.
    """
    with open(head_path(repo_root), "r") as f:
        content = f.read().strip()
    if content.startswith("ref: "):
        ref_file = os.path.join(repo_root, ".mygit", content[5:])
        if not os.path.exists(ref_file):
            return None
        with open(ref_file, "r") as f:
            sha = f.read().strip()
        return sha or None
    return content or None


def write_head_sha(sha: str, repo_root: str) -> None:
    """
    Write sha into whichever file HEAD currently points to.
    If HEAD is a symbolic ref, update the branch file.
    If HEAD is detached, update HEAD directly.
    """
    with open(head_path(repo_root), "r") as f:
        content = f.read().strip()
    if content.startswith("ref: "):
        ref_file = os.path.join(repo_root, ".mygit", content[5:])
        os.makedirs(os.path.dirname(ref_file), exist_ok=True)
        with open(ref_file, "w") as f:
            f.write(sha + "\n")
    else:
        with open(head_path(repo_root), "w") as f:
            f.write(sha + "\n")


def point_head_to_branch(branch: str, repo_root: str) -> None:
    """Make HEAD a symbolic ref pointing to the given branch."""
    with open(head_path(repo_root), "w") as f:
        f.write(f"ref: refs/heads/{branch}\n")


# ---------------------------------------------------------------------------
# Branch refs
# ---------------------------------------------------------------------------


# Returns Branch
def branch_path(branch: str, repo_root: str) -> str:
    return os.path.join(repo_root, ".mygit", "refs", "heads", branch)


def read_branch_sha(branch: str, repo_root: str) -> str | None:
    path = branch_path(branch, repo_root)
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        return f.read().strip() or None


def write_branch_sha(branch: str, sha: str, repo_root: str) -> None:
    path = branch_path(branch, repo_root)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(sha + "\n")


def list_branches(repo_root: str) -> list[str]:
    heads_dir = os.path.join(repo_root, ".mygit", "refs", "heads")
    if not os.path.isdir(heads_dir):
        return []
    return sorted(os.listdir(heads_dir))
