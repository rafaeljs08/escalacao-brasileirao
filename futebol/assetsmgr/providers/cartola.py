"""Provider Cartola FC — endpoints públicos, sem autenticação."""

from __future__ import annotations

import re
from urllib.parse import urljoin

from django.utils.text import slugify

from futebol.assetsmgr import config as cfg
from futebol.assetsmgr.http import JsonClient
from futebol.assetsmgr.providers.base import PlayerRecord, TeamRecord
# nome_do_clube / melhor_escudo / CLUBES_EXTRA definidos abaixo.

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

# Em 2026 a API devolve nome/abreviacao iguais à sigla; o slug traz o clube real.
SLUG_PARA_NOME = {
    'atletico-mg': 'Atlético-MG',
    'atletico-pr': 'Athletico-PR',
    'bahia': 'Bahia',
    'botafogo': 'Botafogo',
    'bragantino': 'Bragantino',
    'chapecoense': 'Chapecoense',
    'corinthians': 'Corinthians',
    'coritiba': 'Coritiba',
    'cruzeiro': 'Cruzeiro',
    'flamengo': 'Flamengo',
    'fluminense': 'Fluminense',
    'gremio': 'Grêmio',
    'internacional': 'Internacional',
    'mirassol': 'Mirassol',
    'palmeiras': 'Palmeiras',
    'remo': 'Remo',
    'santos': 'Santos',
    'sao-paulo': 'São Paulo',
    'vasco': 'Vasco da Gama',
    'vitoria': 'Vitória',
}

# Clubes da Série A 2026 que não estão no seed acadêmico (CEA/FOR/JUV/SPT).
CLUBES_EXTRA = {
    'CAP': {
        'nome': 'Athletico-PR',
        'cidade': 'Curitiba',
        'estado': 'PR',
        'cor_primaria': '#c8102e',
        'cor_secundaria': '#111827',
    },
    'CFC': {
        'nome': 'Coritiba',
        'cidade': 'Curitiba',
        'estado': 'PR',
        'cor_primaria': '#166534',
        'cor_secundaria': '#f8fafc',
    },
    'CHA': {
        'nome': 'Chapecoense',
        'cidade': 'Chapecó',
        'estado': 'SC',
        'cor_primaria': '#14532d',
        'cor_secundaria': '#f8fafc',
    },
    'REM': {
        'nome': 'Remo',
        'cidade': 'Belém',
        'estado': 'PA',
        'cor_primaria': '#1d4ed8',
        'cor_secundaria': '#f8fafc',
    },
}


def nome_do_clube(slug: str, sigla: str, bruto: str) -> str:
    return SLUG_PARA_NOME.get(slug) or CLUBES_EXTRA.get(sigla, {}).get('nome') or bruto or sigla


def melhor_escudo(escudos: dict) -> str:
    """Maior PNG disponível; SVG se a API publicar (não inventamos URL)."""
    if not isinstance(escudos, dict):
        return ''
    for chave in ('svg', '100x100', '60x60', '45x45', '30x30'):
        valor = escudos.get(chave)
        if valor:
            return str(valor)
    for valor in escudos.values():
        if valor:
            return str(valor)
    return ''


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
            logo = melhor_escudo(escudos)
            sigla = str(item.get('abreviacao') or '').upper()
            slug = str(item.get('slug') or slugify(item.get('nome') or sigla))
            nome = nome_do_clube(slug, sigla, str(item.get('nome') or item.get('nome_fantasia') or ''))
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
