from __future__ import annotations

from futebol.assetsmgr import config as cfg
from futebol.assetsmgr.providers.api_football import ApiFootballProvider
from futebol.assetsmgr.providers.base import AssetProvider, PlayerRecord, TeamRecord
from futebol.assetsmgr.providers.cartola import CartolaProvider
from futebol.assetsmgr.providers.fallback import FallbackProvider
from futebol.assetsmgr.providers.sportmonks import SportmonksProvider

REGISTRY = {
    'cartola': CartolaProvider,
    'api_football': ApiFootballProvider,
    'sportmonks': SportmonksProvider,
    'fallback': FallbackProvider,
}


def load_providers() -> list[AssetProvider]:
    saida: list[AssetProvider] = []
    for nome in cfg.provider_order():
        cls = REGISTRY.get(nome)
        if not cls:
            continue
        provider = cls()
        if provider.available():
            saida.append(provider)
    if not any(getattr(p, 'name', '') == 'fallback' for p in saida):
        saida.append(FallbackProvider())
    return saida


def primeiro_logo(team: TeamRecord, providers: list[AssetProvider]) -> tuple[str | None, str, bool]:
    for provider in providers:
        url = provider.get_team_logo(team)
        if url:
            return url, provider.name, provider.name == 'fallback'
    return None, '', True


def primeira_foto(player: PlayerRecord, providers: list[AssetProvider]) -> tuple[str | None, str, bool]:
    """Tenta foto real; se só houver silhueta/placeholder, usa como fallback explícito."""
    genericas: list[tuple[str, str]] = []
    for provider in providers:
        url = provider.get_player_image(player)
        if not url:
            continue
        if 'silhuetas' in url.lower() or 'placeholder' in url.lower():
            genericas.append((url, provider.name))
            continue
        return url, provider.name, False
    if genericas:
        url, nome = genericas[0]
        return url, nome, True
    return None, '', True
