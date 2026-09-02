"""Configuração do Asset Manager — URLs e tokens só entram por settings/env."""

from __future__ import annotations

from pathlib import Path

from django.conf import settings


def season() -> int:
    return int(getattr(settings, 'ASSET_SEASON', 2026))


def assets_dir() -> Path:
    return Path(getattr(settings, 'ASSETS_DIR', settings.BASE_DIR / 'assets'))


def data_dir() -> Path:
    return Path(getattr(settings, 'DATA_DIR', settings.BASE_DIR / 'data'))


def logs_dir() -> Path:
    return Path(getattr(settings, 'ASSET_LOGS_DIR', settings.BASE_DIR / 'logs'))


def timeout() -> float:
    return float(getattr(settings, 'REQUEST_TIMEOUT', 15))


def max_retries() -> int:
    return int(getattr(settings, 'MAX_RETRIES', 3))


def request_delay() -> float:
    return float(getattr(settings, 'REQUEST_DELAY', 0.5))


def provider_order() -> list[str]:
    bruto = getattr(settings, 'ASSET_PROVIDERS', 'cartola,api_football,sportmonks,fallback')
    return [item.strip() for item in str(bruto).split(',') if item.strip()]


def allowed_hosts() -> tuple[str, ...]:
    extra = getattr(settings, 'ASSET_ALLOWED_HOSTS', '')
    padrao = (
        'api.cartola.globo.com',
        's3.glbimg.com',
        's.glbimg.com',
        's.sde.globo.com',
        'media.api-sports.io',
        'v3.football.api-sports.io',
        'api.sportmonks.com',
        'cdn.sportmonks.com',
    )
    extras = tuple(h.strip() for h in str(extra).split(',') if h.strip())
    return padrao + extras


def cartola_base() -> str:
    return str(getattr(settings, 'CARTOLA_BASE_URL', 'https://api.cartola.globo.com')).rstrip('/')


def cartola_photo_format() -> str:
    return str(getattr(settings, 'CARTOLA_PHOTO_FORMAT', '220x220.png'))


def api_football_base() -> str:
    return str(getattr(settings, 'API_FOOTBALL_BASE_URL', 'https://v3.football.api-sports.io')).rstrip('/')


def api_football_key() -> str:
    return str(getattr(settings, 'API_FOOTBALL_KEY', '') or '').strip()


def sportmonks_base() -> str:
    return str(getattr(settings, 'SPORTMONKS_BASE_URL', 'https://api.sportmonks.com/v3/football')).rstrip('/')


def sportmonks_token() -> str:
    return str(getattr(settings, 'SPORTMONKS_TOKEN', '') or '').strip()
