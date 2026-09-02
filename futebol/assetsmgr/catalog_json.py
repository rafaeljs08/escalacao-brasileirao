from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from futebol.assetsmgr import config as cfg


def gravar_json(nome: str, payload: dict | list) -> Path:
    pasta = cfg.data_dir()
    pasta.mkdir(parents=True, exist_ok=True)
    caminho = pasta / nome
    caminho.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    return caminho


def agora() -> str:
    return datetime.now(timezone.utc).isoformat()
