"""API-Football (api-sports). Só ativa com API_FOOTBALL_KEY — sem chave, o provider recua."""

from __future__ import annotations

from django.utils.text import slugify

from futebol.assetsmgr import config as cfg
from futebol.assetsmgr.http import JsonClient
from futebol.assetsmgr.providers.base import PlayerRecord, TeamRecord

POSICAO = {
    'Goalkeeper': 'GOL',
    'Defender': 'ZAG',
    'Midfielder': 'MEI',
    'Attacker': 'ATA',
}


class ApiFootballProvider:
    name = 'api_football'

    def __init__(self, client: JsonClient | None = None):
        self.client = client or JsonClient()
        self._teams: list[TeamRecord] | None = None
        self._players: list[PlayerRecord] | None = None

    def available(self) -> bool:
        return bool(cfg.api_football_key())

    def _headers(self) -> dict[str, str]:
        return {'x-apisports-key': cfg.api_football_key()}

    def get_teams(self) -> list[TeamRecord]:
        if self._teams is not None:
            return self._teams
        url = f'{cfg.api_football_base()}/teams'
        payload = self.client.get_json(url, params={'league': 71, 'season': cfg.season()}, headers=self._headers())
        saida: list[TeamRecord] = []
        for item in payload.get('response') or []:
            time = (item or {}).get('team') or {}
            if not time.get('id'):
                continue
            nome = str(time.get('name') or '')
            saida.append(TeamRecord(
                id=int(time['id']),
                name=nome,
                short_name=str(time.get('code') or '')[:3].upper(),
                slug=slugify(nome),
                logo_url=str(time.get('logo') or ''),
                source=self.name,
            ))
        self._teams = saida
        return saida

    def get_players(self) -> list[PlayerRecord]:
        if self._players is not None:
            return self._players
        url = f'{cfg.api_football_base()}/players'
        saida: list[PlayerRecord] = []
        pagina = 1
        while pagina <= 40:
            payload = self.client.get_json(
                url,
                params={'league': 71, 'season': cfg.season(), 'page': pagina},
                headers=self._headers(),
            )
            for item in payload.get('response') or []:
                jogador = (item or {}).get('player') or {}
                estat = ((item or {}).get('statistics') or [{}])[0]
                time = (estat.get('team') or {})
                posicao = (estat.get('games') or {}).get('position') or ''
                if not jogador.get('id'):
                    continue
                nome = str(jogador.get('name') or '')
                saida.append(PlayerRecord(
                    id=int(jogador['id']),
                    name=nome,
                    slug=slugify(nome),
                    team_id=int(time.get('id') or 0),
                    position=POSICAO.get(str(posicao), 'MEI'),
                    photo_url=str(jogador.get('photo') or ''),
                    source=self.name,
                ))
            paging = payload.get('paging') or {}
            atual = int(paging.get('current') or pagina)
            total = int(paging.get('total') or atual)
            if atual >= total:
                break
            pagina += 1
        self._players = saida
        return saida

    def get_team_logo(self, team: TeamRecord) -> str | None:
        if team.source == self.name and team.logo_url:
            return team.logo_url
        chave = (team.short_name or team.name).casefold()
        for candidato in self.get_teams():
            if (candidato.short_name or '').casefold() == chave or candidato.name.casefold() == team.name.casefold():
                return candidato.logo_url or None
        return None

    def get_player_image(self, player: PlayerRecord) -> str | None:
        if player.source == self.name:
            return player.photo_url or None
        chave = slugify(player.name)
        for candidato in self.get_players():
            if slugify(candidato.name) == chave:
                return candidato.photo_url or None
        return None
