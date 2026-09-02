from __future__ import annotations

import hashlib
from pathlib import Path

from futebol.assetsmgr.validator import validate_image


def hash_arquivo(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cache_hit(path: Path, url: str, url_conhecida: str, hash_conhecido: str) -> bool:
    if not path.exists():
        return False
    checagem = validate_image(path)
    if not checagem.get('valid'):
        return False
    if url_conhecida and url_conhecida == url and hash_conhecido:
        return hash_arquivo(path) == hash_conhecido
    if path.stat().st_size < 80:
        return False
    return True
