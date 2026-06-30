# mygit

A simplified, fully working implementation of Git — built completely from scratch in Python with **zero external dependencies**. It uses the same content-addressed object model as real Git: SHA-1 hashed blobs, trees, and commits, compressed with zlib, stored under `.mygit/objects/`.

```
mygit init
mygit add .
mygit commit -m "first commit"
mygit log
```

---

## Table of Contents

- [Features](#features)
- [How it works](#how-it-works)
- [Fork and clone](#fork-and-clone)
- [Setup — macOS](#setup--macos)
- [Setup — Linux](#setup--linux)
- [Setup — Windows](#setup--windows)
- [Run with Docker (any OS)](#run-with-docker-any-os)
- [Command reference](#command-reference)
- [.mygitignore](#mygitignore)
- [Project structure](#project-structure)
- [Example workflow](#example-workflow)
- [Limitations](#limitations)
- [Contributing](#contributing)
- [License](#license)

---

## Features

- Content-addressed object storage (every object's filename **is** its SHA-1 hash)
- Automatic deduplication — identical file content is only ever stored once
- zlib-compressed object storage
- Staging area (index) separate from commits
- Full commit history as a linked parent chain
- Branching (`mygit branch`) and switching (`mygit checkout`)
- Unified diffs (`mygit diff`) with colored output
- Three-way status reporting — staged / unstaged / untracked (`mygit status`)
- `.mygitignore` support with glob, directory, and path-component patterns
- No external dependencies — pure Python standard library only

---

## How it works

```
Working Tree          Index (Staging)          Object Store (.mygit/objects/)
─────────────         ───────────────          ──────────────────────────────
README.md  ──add──▶  README.md: a2beefd ──▶  blob a2beefd... (zlib compressed)
src/app.py ──add──▶  src/app.py: bdcee3f ──▶  blob bdcee3f...

                          │ commit
                          ▼
                      tree 941b6fb
                        README.md  → a2beefd
                        src/app.py → bdcee3f
                          │
                          ▼
                      commit 386641f
                        tree:   941b6fb
                        parent: (none — root commit)
                        author: Jane Smith
                        message: Initial commit
                          │
                          ▼
                      refs/heads/main → 386641f
                      HEAD → ref: refs/heads/main
```

Every object's filename in `.mygit/objects/` is its own SHA-1 hash. Identical content always produces the identical hash — so two identical files are automatically stored only once, and any change to a file produces a completely different hash, giving integrity-checking for free.

---

## Fork and clone

1. Click **Fork** at the top right of this repository on GitHub — this creates your own copy under your account.
2. Clone your fork to your computer:

```bash
git clone https://github.com/YOUR_USERNAME/mygit.git
cd mygit
```

(Replace `YOUR_USERNAME` with your actual GitHub username.)

You now have the full source on your machine and can run it directly, or follow the OS-specific setup below to install it as a global `mygit` command.

---

## Setup — macOS

**Requirements:** Python 3.10+ (check with `python3 --version`)

```bash
# 1. Make the entry script executable
chmod +x mygit.py

# 2. Create a global wrapper command
sudo nano /usr/local/bin/mygit
```

Paste the following, replacing the path with the actual location of your cloned repo:

```bash
#!/bin/bash
python3 /Users/YOUR_USERNAME/mygit/mygit.py "$@"
```

Save with `Ctrl+O`, exit with `Ctrl+X`, then:

```bash
sudo chmod +x /usr/local/bin/mygit
```

Test it:

```bash
mygit --help
```

> On Apple Silicon Macs, `/usr/local/bin` may not be on your `PATH` by default if you're using Homebrew's `/opt/homebrew` prefix. If `mygit` isn't found, add this to `~/.zshrc`:
> ```bash
> export PATH="/usr/local/bin:$PATH"
> ```
> then run `source ~/.zshrc`.

---

## Setup — Linux

**Requirements:** Python 3.10+ (check with `python3 --version`)

```bash
# 1. Make the entry script executable
chmod +x mygit.py

# 2. Create a global wrapper command
sudo nano /usr/local/bin/mygit
```

Paste, replacing the path with your actual clone location:

```bash
#!/bin/bash
python3 /home/YOUR_USERNAME/mygit/mygit.py "$@"
```

Save and exit, then:

```bash
sudo chmod +x /usr/local/bin/mygit
```

Test it:

```bash
mygit --help
```

**Alternative — shell alias** (no sudo required):

```bash
echo "alias mygit='python3 $(pwd)/mygit.py'" >> ~/.bashrc
source ~/.bashrc
```

(Use `~/.zshrc` instead if you're on zsh.)

---

## Setup — Windows

**Requirements:** Python 3.10+ — install from [python.org](https://python.org) and check **"Add Python to PATH"** during install. Verify with:

```powershell
python --version
```

**1. Clone or unzip the project** to a folder, e.g. `C:\mygit\`

**2. Create a global wrapper command.** Open PowerShell **as Administrator**:

```powershell
notepad C:\Windows\System32\mygit.bat
```

Paste, replacing the path with your actual project location:

```bat
@echo off
python C:\mygit\mygit.py %*
```

Save and close Notepad.

**3. Test it** — open a new PowerShell window:

```powershell
mygit --help
```

> If `mygit.py` is nested inside a subfolder (e.g. `C:\mygit\mygit\mygit.py` from a zip extraction), make sure the `.bat` file points at the exact full path to `mygit.py`. Use `Get-ChildItem C:\mygit\ -Recurse -Filter "mygit.py"` in PowerShell to find it if unsure.

---

## Run with Docker (any OS)

No Python installation needed at all — works identically on macOS, Linux, and Windows.

```bash
# Build the image
docker build -t mygit .

# Run it interactively
docker run -it mygit
```

**To use it on your real project files**, mount your project folder into the container:

```bash
# macOS / Linux
docker run -it -v $(pwd)/myproject:/workspace mygit

# Windows PowerShell
docker run -it -v C:\path\to\myproject:/workspace mygit
```

Any `.mygit` folder created inside the container will persist on your real filesystem.

**Use the pre-built image (if published to Docker Hub):**

```bash
docker run -it YOUR_DOCKERHUB_USERNAME/mygit
```

---

## Command reference

After setup, `mygit` works exactly like `git` for the supported subset of commands.

| Command | Description |
|---|---|
| `mygit init` | Initialize a new repository in the current directory |
| `mygit add <file> [...]` | Stage one or more files (supports globs and directories) |
| `mygit commit -m "<message>"` | Commit everything currently staged |
| `mygit status` | Show staged, unstaged, and untracked changes |
| `mygit log [-n N]` | Show commit history, optionally limited to N commits |
| `mygit diff [<file>]` | Show a unified diff vs the last commit |
| `mygit branch [<name>]` | List branches, or create a new branch at HEAD |
| `mygit checkout <branch>` | Switch to a branch, restoring its files |

### init

```bash
mkdir my-project && cd my-project
mygit init
```

Creates `.mygit/` with `objects/`, `refs/heads/`, `HEAD`, and `config`. Edit `.mygit/config` to set your name and email:

```ini
[user]
    name = Your Name
    email = you@example.com
```

### add

```bash
mygit add README.md            # single file
mygit add src/main.py src/utils.py
mygit add .                    # everything, recursively
mygit add "*.py"               # glob (quote to avoid shell expansion)
```

### commit

```bash
mygit commit -m "Initial commit"
```

### status

```bash
mygit status
```

### log

```bash
mygit log
mygit log -n 5
```

### diff

```bash
mygit diff
mygit diff README.md
```

### branch

```bash
mygit branch              # list, * marks current
mygit branch feature-x    # create new branch at current HEAD
```

### checkout

```bash
mygit checkout feature-x
mygit checkout main
```

> Unlike real Git, `checkout` does not warn you about uncommitted changes before switching — commit your work first.

---

## .mygitignore

Create a `.mygitignore` file in your repo root:

```
# Comments start with #
*.pyc
*.log
build/
dist/
__pycache__
.env
secret*.txt
```

Ignored files are skipped by `add` and excluded from `diff` and `status`.

---

## Project structure

```
mygit/
├── mygit.py              ← CLI entry point
├── Dockerfile
├── .dockerignore
├── .gitignore
├── README.md
├── commands/
│   ├── init.py
│   ├── add.py
│   ├── commit.py
│   ├── log.py
│   ├── diff.py
│   ├── status.py
│   ├── branch.py
│   └── checkout.py
└── core/
    ├── objects.py         ← blob / tree / commit object store
    ├── index.py            ← staging area + .mygitignore
    └── refs.py             ← HEAD and branch ref helpers
```

What gets created inside a repo after `init` and a few commits:

```
.mygit/
├── HEAD                  ← "ref: refs/heads/main"
├── config                ← your name and email
├── index                 ← staging area
├── objects/
│   └── af/5626b7...      ← compressed objects, named by SHA-1
└── refs/
    └── heads/
        ├── main
        └── feature-x
```

---

## Example workflow

```bash
mkdir my-app && cd my-app
mygit init

# set identity
nano .mygit/config

echo "*.pyc"        > .mygitignore
echo "__pycache__/" >> .mygitignore

echo "# My App" > README.md
mkdir src
echo "def main(): print('hello')" > src/app.py

mygit add .
mygit status
mygit commit -m "Initial commit"

echo "def helper(): return 42" >> src/app.py
mygit diff
mygit add src/app.py
mygit commit -m "Add helper function"

mygit log

mygit branch feature-login
mygit checkout feature-login
echo "def login(): pass" >> src/app.py
mygit add src/app.py
mygit commit -m "Add login stub"

mygit checkout main
mygit log -n 2
```

---

## Limitations

This is a learning project, not a production tool. It does not implement:

- Merging or rebasing
- Remote repositories (push/pull/clone/fetch)
- File permissions, symlinks, or submodules
- Conflict resolution
- Detached HEAD safety checks before checkout (uncommitted changes can be silently overwritten)

The object format (`"<type> <size>\0<content>"`, zlib-compressed, split into two-character subfolders) mirrors real Git's design closely enough to demonstrate the underlying concepts.

---

## Contributing

Issues and pull requests are welcome. Possible next steps if you want to extend it: `mygit log --oneline`, `mygit diff --staged`, `mygit rm`, `mygit show <sha>`, or — the big one — `mygit merge`.

---

## License

MIT — free to use, modify, and learn from.