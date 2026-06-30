"""
commands/checkout.py  —  mygit checkout <branch>

1. Reads the branch tip commit.
2. Reads its tree.
3. Writes all files from the tree into the working directory.
4. Points HEAD at the branch.
5. Updates the index to match the checked-out tree.
"""

import os
import sys

from core.objects import find_repo_root, read_commit, read_tree, read_blob
from core.index   import write_index
from core.refs    import (
    read_head_ref, read_branch_sha,
    point_head_to_branch, list_branches,
)


def cmd_checkout(args) -> None:
    try:
        repo_root = find_repo_root()
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

    branch = args.name

    current = read_head_ref(repo_root)
    if current == branch:
        print(f"Already on branch '{branch}'.")
        return


    if branch not in list_branches(repo_root):
        print(f"error: branch '{branch}' not found.", file=sys.stderr)
        sys.exit(1)

    branch_sha = read_branch_sha(branch, repo_root)
    if branch_sha is None:
        print(f"error: branch '{branch}' has no commits.", file=sys.stderr)
        sys.exit(1)

    commit      = read_commit(branch_sha, repo_root)
    tree_sha    = commit["tree"]
    tree_entries = read_tree(tree_sha, repo_root)

    new_index: dict[str, str] = {}
    for _mode, rel_path, blob_sha in tree_entries:
        abs_path = os.path.join(repo_root, rel_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        data = read_blob(blob_sha, repo_root)
        with open(abs_path, "wb") as f:
            f.write(data)
        new_index[rel_path] = blob_sha

    write_index(new_index, repo_root)
    point_head_to_branch(branch, repo_root)

    print(f"Switched to branch '{branch}'.")
    print(f"  {len(tree_entries)} file(s) checked out from commit {branch_sha[:7]}.")
