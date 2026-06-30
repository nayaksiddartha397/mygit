"""
core/objects.py

Low-level object store for mygit.

Object types
------------
blob   — raw file content
tree   — directory snapshot: list of (mode, name, sha) triples
commit — pointer to a tree + parent + metadata

On-disk format (mirroring real Git)
------------------------------------
Every object is stored at:
    .mygit/objects/<sha[:2]>/<sha[2:]>

The raw bytes written are:
    zlib.compress( "<type> <content_byte_length>\0" + content )

For a blob, content = raw file bytes.
For a tree, content = binary entries (see write_tree / read_tree).
For a commit, content = UTF-8 text with newline-separated fields.
"""

import hashlib
import os
import zlib
import struct

# ---------------------------------------------------------------------------
# Repo root helpers
# ---------------------------------------------------------------------------
# Helps to find the mygit folder no matter in which subFolder we are in

def find_repo_root(start: str = ".") -> str:
    """Walk up until we find a .mygit directory; raise if not found."""
    cur = os.path.abspath(start)
    while True:
        if os.path.isdir(os.path.join(cur, ".mygit")):
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            raise FileNotFoundError(
                "Not a mygit repository (no .mygit directory found)."
            )
        cur = parent


def objects_dir(repo_root: str) -> str:
    return os.path.join(repo_root, ".mygit", "objects")


# ---------------------------------------------------------------------------
# Low-level read / write
# ---------------------------------------------------------------------------

# split SHA-1 such that first 2 char are foldername and last 38 char are filename 
def _object_path(repo_root: str, sha: str) -> str:
    return os.path.join(objects_dir(repo_root), sha[:2], sha[2:])


def write_object(data: bytes, obj_type: str, repo_root: str) -> str:
    """
    Hash and store an object.  Returns the 40-char hex SHA-1.
    Idempotent: if the object already exists it is not rewritten.
    """
    header = f"{obj_type} {len(data)}\0".encode()       # Here obj type is blob and \0 is the sepearator btw header and data
    full = header + data                                # Here Data is like Hello world or content
    sha = hashlib.sha1(full).hexdigest()                # 40 char hexstring
    path = _object_path(repo_root, sha)
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(zlib.compress(full))
    return sha


def read_object(sha: str, repo_root: str) -> tuple[str, bytes]:
    """
    Read an object by SHA.  Returns (type_str, raw_content_bytes).
    """
    path = _object_path(repo_root, sha)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Object not found: {sha}")
    with open(path, "rb") as f:
        raw = zlib.decompress(f.read())
    null_idx = raw.index(b"\0")
    header = raw[:null_idx].decode()
    obj_type, _ = header.split(" ", 1)
    content = raw[null_idx + 1 :]
    return obj_type, content


# ---------------------------------------------------------------------------
# Blob helpers
# ---------------------------------------------------------------------------

def hash_blob(data: bytes, repo_root: str) -> str:
    """Store raw bytes as a blob object."""
    return write_object(data, "blob", repo_root)


def read_blob(sha: str, repo_root: str) -> bytes:
    obj_type, content = read_object(sha, repo_root)
    if obj_type != "blob":
        raise ValueError(f"Expected blob, got {obj_type}")
    return content


# ---------------------------------------------------------------------------
# Tree helpers
# ---------------------------------------------------------------------------
# Binary tree entry format (same as real Git):
#   "<mode> <name>\0<20-byte-binary-sha>"
# We only use mode "100644" (regular file) for simplicity.

_BLOB_MODE = b"100644"


def write_tree(entries: list[tuple[str, str]], repo_root: str) -> str:
    """
    entries: list of (filename, blob_sha_hex)
    Returns the tree SHA.
    """
    # Sort entries by name (Git sorts trees)
    entries_sorted = sorted(entries, key=lambda e: e[0])
    raw = b""
    for name, sha_hex in entries_sorted:
        sha_bin = bytes.fromhex(sha_hex)         #convert hexadecimal into binary
        raw += _BLOB_MODE + b" " + name.encode() + b"\0" + sha_bin
    return write_object(raw, "tree", repo_root)


def read_tree(sha: str, repo_root: str) -> list[tuple[str, str, str]]:
    """
    Returns list of (mode_str, name_str, sha_hex).
    """
    obj_type, content = read_object(sha, repo_root)
    if obj_type != "tree":
        raise ValueError(f"Expected tree, got {obj_type}")
    entries = []
    i = 0
    while i < len(content):
        # find space between mode and name
        sp = content.index(b" ", i)      
        mode = content[i:sp].decode()
        # find null terminator after name
        null = content.index(b"\0", sp + 1)
        name = content[sp + 1 : null].decode()
        sha_bin = content[null + 1 : null + 21]
        sha_hex = sha_bin.hex()
        entries.append((mode, name, sha_hex))
        i = null + 21
    return entries


# ---------------------------------------------------------------------------
# Commit helpers
# ---------------------------------------------------------------------------

def write_commit(
    tree_sha: str,
    message: str,
    author: str,
    timestamp: int,
    parent_sha: str | None,
    repo_root: str,
) -> str:
    """Serialise and store a commit object.  Returns the commit SHA."""
    lines = [f"tree {tree_sha}"]
    if parent_sha:
        lines.append(f"parent {parent_sha}")
    tz = "+0000"
    lines.append(f"author {author} {timestamp} {tz}")
    lines.append(f"committer {author} {timestamp} {tz}")
    lines.append("")
    lines.append(message)
    content = "\n".join(lines).encode()
    return write_object(content, "commit", repo_root)


def read_commit(sha: str, repo_root: str) -> dict:
    """
    Returns a dict with keys:
        tree, parent (may be None), author, committer, timestamp, message
    """
    obj_type, content = read_object(sha, repo_root)
    if obj_type != "commit":
        raise ValueError(f"Expected commit, got {obj_type}")
    text = content.decode()
    # Split header from message at first blank line
    header_part, _, message = text.partition("\n\n")
    result: dict = {"message": message.strip(), "parent": None}
    for line in header_part.splitlines():
        if line.startswith("tree "):
            result["tree"] = line[5:]
        elif line.startswith("parent "):
            result["parent"] = line[7:]
        elif line.startswith("author "):
            # author Name <email> timestamp tz
            tail = line[7:]
            parts = tail.rsplit(" ", 2)
            result["author"] = parts[0]
            result["timestamp"] = int(parts[1])
        elif line.startswith("committer "):
            result["committer"] = line[10:]
    return result
