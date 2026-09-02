"""Logs em arquivo: logs/download.log e logs/missing.log."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from futebol.assetsmgr import config as cfg


def _pasta() -> Path:
    pasta = cfg.logs_dir()
    pasta.mkdir(parents=True, exist_ok=True)
    (pasta / '.gitkeep').touch(exist_ok=True)
    return pasta


def _linha(mensagem: str) -> str:
    agora = datetime.now(timezone.utc).isoformat()
    return f'{agora} {mensagem}\n'


def log_download(mensagem: str) -> None:
    caminho = _pasta() / 'download.log'
    with caminho.open('a', encoding='utf-8') as arquivo:
        arquivo.write(_linha(mensagem))


def log_missing(mensagem: str) -> None:
    caminho = _pasta() / 'missing.log'
    with caminho.open('a', encoding='utf-8') as arquivo:
        arquivo.write(_linha(mensagem))
