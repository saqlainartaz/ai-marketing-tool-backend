"""Immutable, content-addressed raw-file storage.

Raw files are sacred: written once under their sha256, never modified
(openmelon material-pool pattern). The interface is S3-shaped so an S3/R2
adapter can replace local disk without touching callers.
"""

import hashlib
import uuid
from pathlib import Path
from typing import Protocol


class RawStorage(Protocol):
    def put(self, client_id: uuid.UUID, sha256: str, data: bytes) -> str:
        """Store immutably; return the storage path. Idempotent per (client, sha)."""
        ...

    def get(self, path: str) -> bytes: ...


def content_address(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class LocalDiskStorage:
    def __init__(self, root: str) -> None:
        self._root = Path(root)

    def put(self, client_id: uuid.UUID, sha256: str, data: bytes) -> str:
        target = self._root / str(client_id) / sha256[:2] / sha256
        if target.exists():
            return str(target)  # immutable: never rewrite
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_suffix(".tmp")
        tmp.write_bytes(data)
        tmp.replace(target)  # atomic publish
        return str(target)

    def get(self, path: str) -> bytes:
        return Path(path).read_bytes()
