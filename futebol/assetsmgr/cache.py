from __future__ import annotations

import hashlib
from pathlib import Path

from futebol.assetsmgr.validator import validate_image


def hash_arquivo(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cache_hit(path: Path, url: str, url_conhecida: str = '', hash_conhecido: str = '') -> bool:
    """Arquivo local vale se existir, for imagem válida e a URL/hash não tiverem mudado."""
    if not path.exists() or not path.is_file():
        return False
    checagem = validate_image(path)
    if not checagem.get('valid'):
        return False
    if path.stat().st_size < 80:
        return False
    if url_conhecida and url and url_conhecida != url:
        return False
    if hash_conhecido and hash_arquivo(path) != hash_conhecido:
        return False
    return True
