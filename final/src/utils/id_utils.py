import hashlib
from pathlib import Path
from typing import Dict


def sha1_hex(data: bytes) -> str:
    return hashlib.sha1(data).hexdigest()


def file_sha1(path: str | Path) -> str:
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def stable_chunk_id(parts: Dict[str, str]) -> str:
    ordered = [str(parts.get(k, "")) for k in sorted(parts.keys())]
    joined = "|".join(ordered).encode("utf-8")
    return sha1_hex(joined)
