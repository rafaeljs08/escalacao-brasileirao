"""Sportmonks. Só ativa com SPORTMONKS_TOKEN — sem token, o provider recua."""

from __future__ import annotations

from django.utils.text import slugify

from futebol.assetsmgr import config as cfg
from futebol.assetsmgr.http import JsonClient
from futebol.assetsmgr.providers.base import PlayerRecord, TeamRecord


class SportmonksProvider:
    name = 'sportmonks'

    def __init__(self, client: JsonClient | None = None):
        self.client = client or JsonClient()

    def available(self) -> bool:
        return bool(cfg.sportmonks_token())

    def get_teams(self) -> list[TeamRecord]:
        url = f'{cfg.sportmonks_base()}/teams'
        payload = self.client.get_json(url, params={'api_token': cfg.sportmonks_token()})
        saida: list[TeamRecord] = []
        for item in payload.get('data') or []:
            if not isinstance(item, dict) or not item.get('id'):
                continue
            nome = str(item.get('name') or '')
            saida.append(TeamRecord(
                id=int(item['id']),
                name=nome,
                short_name=str(item.get('short_code') or '')[:3].upper(),
                slug=slugify(nome),
                logo_url=str(item.get('image_path') or ''),
                source=self.name,
            ))
        return saida

    def get_players(self) -> list[PlayerRecord]:
        return []

    def get_team_logo(self, team: TeamRecord) -> str | None:
        return team.logo_url or None

    def get_player_image(self, player: PlayerRecord) -> str | None:
        return player.photo_url or None
