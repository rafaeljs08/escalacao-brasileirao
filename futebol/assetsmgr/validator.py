from __future__ import annotations

import imghdr
from pathlib import Path
from typing import Any

from PIL import Image, UnidentifiedImageError

MIN_BYTES = 80
MIN_LADO = 16
EXTENSOES = {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.svg'}


def validate_image(path: str | Path) -> dict[str, Any]:
    arquivo = Path(path)
    if not arquivo.exists() or not arquivo.is_file():
        return {'valid': False, 'error': 'arquivo inexistente'}
    nome = arquivo.name.lower()
    if nome.endswith('.tmp') or nome.endswith('.part'):
        nome = nome.rsplit('.', 1)[0]
    ext = Path(nome).suffix
    if ext not in EXTENSOES:
        return {'valid': False, 'error': 'extensão inválida'}
    tamanho = arquivo.stat().st_size
    if tamanho < MIN_BYTES:
        return {'valid': False, 'error': 'arquivo pequeno demais'}

    if arquivo.suffix.lower() == '.svg' or nome.endswith('.svg'):
        texto = arquivo.read_text(encoding='utf-8', errors='ignore')[:400].lower()
        if '<svg' not in texto:
            return {'valid': False, 'error': 'SVG inválido'}
        return {'valid': True, 'width': None, 'height': None, 'format': 'SVG', 'size': tamanho}

    tipo = imghdr.what(arquivo)
    if tipo not in {'png', 'jpeg', 'gif', 'webp'}:
        # Pillow ainda pode abrir; imghdr não conhece todos os webp.
        pass
    try:
        with Image.open(arquivo) as imagem:
            imagem.verify()
        with Image.open(arquivo) as imagem:
            largura, altura = imagem.size
            formato = imagem.format or (tipo or 'UNKNOWN').upper()
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        return {'valid': False, 'error': f'corrompida: {exc}'}

    if largura < MIN_LADO or altura < MIN_LADO:
        return {'valid': False, 'error': 'dimensão abaixo do mínimo'}
    return {
        'valid': True,
        'width': largura,
        'height': altura,
        'format': formato,
        'size': tamanho,
    }


def normalizar_png(origem: Path, destino: Path, lado: int = 256) -> dict[str, Any]:
    """Redimensiona mantendo proporção, fundo transparente, sem distorcer."""
    with Image.open(origem) as imagem:
        rgba = imagem.convert('RGBA')
        rgba.thumbnail((lado, lado), Image.Resampling.LANCZOS)
        canvas = Image.new('RGBA', (rgba.width, rgba.height), (0, 0, 0, 0))
        canvas.paste(rgba, (0, 0), rgba)
        destino.parent.mkdir(parents=True, exist_ok=True)
        canvas.save(destino, format='PNG', optimize=True)
    return validate_image(destino)
