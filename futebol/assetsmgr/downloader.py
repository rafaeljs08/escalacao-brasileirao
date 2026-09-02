from __future__ import annotations

import hashlib
import logging
from pathlib import Path

from futebol.assetsmgr.http import HttpError, JsonClient
from futebol.assetsmgr.validator import normalizar_png, validate_image

logger = logging.getLogger('assetsmgr.download')

MIME_EXT = {
    'image/png': '.png',
    'image/jpeg': '.jpg',
    'image/jpg': '.jpg',
    'image/webp': '.webp',
    'image/gif': '.gif',
    'image/svg+xml': '.svg',
}


class AssetDownloader:
    def __init__(self, client: JsonClient | None = None):
        self.client = client or JsonClient()

    def download(self, url: str, destination: str | Path, *, force: bool = False, normalize: bool = False) -> dict:
        destino = Path(destination)
        if destino.exists() and not force:
            checagem = validate_image(destino)
            if checagem.get('valid'):
                return {**checagem, 'skipped': True, 'path': str(destino)}

        tmp = destino.with_suffix(destino.suffix + '.tmp')
        try:
            corpo, mime, _status = self.client.get_bytes(url)
        except HttpError as exc:
            logger.error('download falhou %s: %s', url, exc)
            return {'valid': False, 'error': str(exc), 'status': exc.status}

        if mime and not mime.startswith('image/') and mime not in MIME_EXT:
            return {'valid': False, 'error': f'content-type inválido: {mime}'}

        destino.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_bytes(corpo)
        checagem = validate_image(tmp)
        if not checagem.get('valid'):
            tmp.unlink(missing_ok=True)
            return checagem

        if normalize and destino.suffix.lower() != '.svg':
            png = destino.with_suffix('.png')
            checagem = normalizar_png(tmp, png)
            tmp.unlink(missing_ok=True)
            destino = png
        else:
            tmp.replace(destino)

        sha = hashlib.sha256(destino.read_bytes()).hexdigest()
        return {**checagem, 'skipped': False, 'path': str(destino), 'sha256': sha, 'mime': mime}
