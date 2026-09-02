from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw


def garantir_placeholders(raiz: Path) -> None:
    pasta = raiz / 'placeholders'
    pasta.mkdir(parents=True, exist_ok=True)
    _png_silhueta(pasta / 'player.png', (36, 48, 72, 255), pessoa=True)
    _png_silhueta(pasta / 'team.png', (22, 101, 52, 255), pessoa=False)


def _png_silhueta(destino: Path, cor: tuple[int, int, int, int], *, pessoa: bool) -> None:
    if destino.exists() and destino.stat().st_size > 80:
        return
    img = Image.new('RGBA', (256, 256), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    if pessoa:
        draw.ellipse((88, 28, 168, 108), fill=cor)
        draw.rounded_rectangle((68, 118, 188, 236), radius=40, fill=cor)
    else:
        draw.polygon([(128, 24), (220, 56), (220, 150), (128, 232), (36, 150), (36, 56)], fill=cor)
    img.save(destino, format='PNG')
