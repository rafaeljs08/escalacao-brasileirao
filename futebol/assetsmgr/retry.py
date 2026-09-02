"""Backoff e decisão de retry — sem contornar bloqueios, só 429/5xx."""

from __future__ import annotations


def backoff_segundos(tentativa: int, base: float = 1.0, teto: float = 30.0) -> float:
    """Exponential backoff: base * 2^tentativa, limitado."""
    if tentativa < 0:
        return base
    return min(teto, base * (2 ** tentativa))


def deve_repetir(status: int | None) -> bool:
    """404/403 não repetem. 429 e erros de servidor, sim."""
    if status in {403, 404}:
        return False
    return status in {429, 500, 502, 503, 504, None}
