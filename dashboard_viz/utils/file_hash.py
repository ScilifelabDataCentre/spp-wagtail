"""File hashing utilities for dashboard data uploads."""

import hashlib
from pathlib import Path
from typing import BinaryIO


def calculate_file_hash(file_obj: BinaryIO | object) -> str:
    """Return a SHA-256 hex digest for a file-like object or Django ``FieldFile``."""
    hasher = hashlib.sha256()

    if hasattr(file_obj, "chunks"):
        for chunk in file_obj.chunks():
            hasher.update(chunk)
        if hasattr(file_obj, "seek"):
            file_obj.seek(0)
        return hasher.hexdigest()

    if hasattr(file_obj, "read"):
        position = file_obj.tell() if hasattr(file_obj, "tell") else None
        while True:
            chunk = file_obj.read(65536)
            if not chunk:
                break
            hasher.update(chunk)
        if position is not None:
            file_obj.seek(position)
        elif hasattr(file_obj, "seek"):
            file_obj.seek(0)
        return hasher.hexdigest()

    if hasattr(file_obj, "path") and file_obj.path:
        with Path(file_obj.path).open("rb") as handle:
            while True:
                chunk = handle.read(65536)
                if not chunk:
                    break
                hasher.update(chunk)
        return hasher.hexdigest()

    raise TypeError("Unsupported file type for hashing.")
