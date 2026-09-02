"""Provider Cartola FC — endpoints públicos, sem autenticação."""

from __future__ import annotations

import re
from urllib.parse import urljoin

from django.utils.text import slugify

from futebol.assetsmgr import config as cfg
from futebol.assetsmgr.http import JsonClient
from futebol.assetsmgr.providers.base import PlayerRecord, TeamRecord

POSICAO_CARTOLA = {
    1: 'GOL',
    2: 'LAT',
    3: 'ZAG',
    4: 'MEI',
    5: 'ATA',
}

# Sigla Cartola → sigla dos clubes do seed acadêmico.
SIGLA_CARTOLA_PARA_APP = {
    'RBB': 'BGT',
}


class CartolaProvider:
    name = 'cartola'

    def __init__(self, client: JsonClient | None = None):
        self.client = client or JsonClient()
        self._mercado: dict | None = None

    def available(self) -> bool:
        return bool(cfg.cartola_base())

    def _url(self, caminho: str) -> str:
        return urljoin(cfg.cartola_base() + '/', caminho.lstrip('/'))

    def mercado(self) -> dict:
        if self._mercado is None:
            self._mercado = self.client.get_json(self._url('atletas/mercado'))
            if not isinstance(self._mercado, dict):
                self._mercado = {}
        return self._mercado

    def get_teams(self) -> list[TeamRecord]:
        clubes = self.mercado().get('clubes') or {}
        saida: list[TeamRecord] = []
        for item in clubes.values():
            if not isinstance(item, dict) or not item.get('id'):
                continue
            escudos = item.get('escudos') or {}
            logo = escudos.get('60x60') or escudos.get('45x45') or ''
            sigla = str(item.get('abreviacao') or '').upper()
            nome = str(item.get('nome') or item.get('nome_fantasia') or sigla)
            slug = str(item.get('slug') or slugify(nome))
            saida.append(TeamRecord(
                id=int(item['id']),
                name=nome,
                short_name=sigla,
                slug=slug,
                logo_url=str(logo),
                source=self.name,
                extra={'app_sigla': SIGLA_CARTOLA_PARA_APP.get(sigla, sigla)},
            ))
        saida.sort(key=lambda t: t.name)
        return saida

    def get_players(self) -> list[PlayerRecord]:
        mercado = self.mercado()
        atletas = mercado.get('atletas') or []
        times = {t.id: t for t in self.get_teams()}
        saida: list[PlayerRecord] = []
        for item in atletas:
            if not isinstance(item, dict):
                continue
            if item.get('posicao_id') == 6:
                continue
            atleta_id = item.get('atleta_id')
            if not atleta_id:
                continue
            foto = self._resolver_foto(str(item.get('foto') or ''))
            nome = str(item.get('apelido') or item.get('nome') or '').strip()
            saida.append(PlayerRecord(
                id=int(atleta_id),
                name=nome,
                slug=str(item.get('slug') or slugify(nome)),
                team_id=int(item.get('clube_id') or 0),
                position=POSICAO_CARTOLA.get(int(item.get('posicao_id') or 0), 'MEI'),
                photo_url=foto,
                source=self.name,
                generic_photo=self._eh_silhueta(foto),
                extra={
                    'nome_completo': str(item.get('nome') or ''),
                    'status_id': item.get('status_id'),
                    'team_sigla': times.get(int(item.get('clube_id') or 0)).short_name if times.get(int(item.get('clube_id') or 0)) else '',
                },
            ))
        return saida

    def get_team_logo(self, team: TeamRecord) -> str | None:
        return team.logo_url or None

    def get_player_image(self, player: PlayerRecord) -> str | None:
        return player.photo_url or None

    def _resolver_foto(self, url: str) -> str:
        if not url:
            return ''
        formato = cfg.cartola_photo_format()
        return re.sub(r'FORMATO\.png', formato, url, flags=re.I)

    def _eh_silhueta(self, url: str) -> bool:
        return 'silhuetas' in (url or '').lower()
