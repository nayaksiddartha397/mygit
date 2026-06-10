#!/usr/bin/env python3
"""
mygit - A simplified Git implementation from scratch.
Content-addressed storage using SHA-1, blobs/trees/commits, and a staging index.
"""

import sys
import os
import argparse

# Make sure commands and core are importable
sys.path.insert(0, os.path.dirname(__file__))

from commands.init     import cmd_init
from commands.add      import cmd_add
from commands.commit   import cmd_commit
from commands.log      import cmd_log
from commands.diff     import cmd_diff
from commands.status   import cmd_status
from commands.branch   import cmd_branch
from commands.checkout import cmd_checkout


def main():
    parser = argparse.ArgumentParser(
        prog="mygit",
        description="A simplified Git implementation from scratch.",
    )
    subparsers = parser.add_subparsers(dest="command", metavar="<command>")
    subparsers.required = True

    # init
    p_init = subparsers.add_parser("init", help="Initialize a new mygit repository")
    p_init.set_defaults(func=cmd_init)

    # add
    p_add = subparsers.add_parser("add", help="Stage file(s) to the index")
    p_add.add_argument("files", nargs="+", metavar="<file>", help="Files to stage")
    p_add.set_defaults(func=cmd_add)

    # commit
    p_commit = subparsers.add_parser("commit", help="Create a commit from the index")
    p_commit.add_argument("-m", "--message", required=True, help="Commit message")
    p_commit.set_defaults(func=cmd_commit)

    # log
    p_log = subparsers.add_parser("log", help="Show commit history")
    p_log.add_argument("-n", "--count", type=int, default=None, metavar="N",
                       help="Limit to N commits")
    p_log.set_defaults(func=cmd_log)

    # diff
    p_diff = subparsers.add_parser("diff", help="Show working-tree vs last commit diff")
    p_diff.add_argument("file", nargs="?", metavar="<file>",
                        help="Specific file to diff (default: all tracked files)")
    p_diff.set_defaults(func=cmd_diff)

    # status
    p_status = subparsers.add_parser("status", help="Show working-tree status")
    p_status.set_defaults(func=cmd_status)

    # branch
    p_branch = subparsers.add_parser("branch", help="List or create branches")
    p_branch.add_argument("name", nargs="?", metavar="<name>",
                          help="Name of new branch (omit to list branches)")
    p_branch.set_defaults(func=cmd_branch)

    # checkout
    p_checkout = subparsers.add_parser("checkout", help="Switch to a branch")
    p_checkout.add_argument("name", metavar="<branch>", help="Branch name to check out")
    p_checkout.set_defaults(func=cmd_checkout)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
