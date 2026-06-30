"""
commands/init.py  —  mygit init

Creates the .mygit directory skeleton:

    .mygit/
    ├── objects/
    ├── refs/
    │   └── heads/
    └── HEAD          (ref: refs/heads/main)
"""

import os
import sys


def cmd_init(args) -> None:
    repo_root = os.getcwd()
    mygit_dir = os.path.join(repo_root, ".mygit")

    if os.path.exists(mygit_dir):
        print(f"Reinitialized existing mygit repository in {mygit_dir}")
        return

    # Create directory tree.    Make objects, refs directory
    for d in [
        os.path.join(mygit_dir, "objects"),          
        os.path.join(mygit_dir, "refs", "heads"),
    ]:
        os.makedirs(d, exist_ok=True)       # use the d above to makedirs

    # HEAD → symbolic ref to main branch
    with open(os.path.join(mygit_dir, "HEAD"), "w") as f:
        f.write("ref: refs/heads/main\n")

    # Default config (author name/email used in commits)
    config_path = os.path.join(mygit_dir, "config")
    with open(config_path, "w") as f:
        f.write("[user]\n")
        f.write("    name = Unnamed User\n")
        f.write("    email = user@example.com\n")

    print(f"Initialized empty mygit repository in {mygit_dir}")
    print("Tip: edit .mygit/config to set your name and email.")
