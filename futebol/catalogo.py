"""Persistência do catálogo de atletas da Série A."""

from __future__ import annotations

from typing import Any

from .data.catalogo_local import CATALOGO_LOCAL
from .models import AtletaCatalogo, Clube
from .services.api_futebol import mapear_posicao, mapear_sigla_clube, posicao_sigla


def resolver_clube(time: dict[str, Any] | None) -> Clube | None:
    if not isinstance(time, dict):
        return None
    sigla_app = mapear_sigla_clube(str(time.get('sigla') or ''))
    if sigla_app:
        clube = Clube.objects.filter(sigla=sigla_app).first()
        if clube:
            return clube
    nome = str(time.get('nome_popular') or time.get('nome') or '').strip()
    if not nome:
        return None
    clube = Clube.objects.filter(nome__iexact=nome).first()
    if clube:
        return clube
    # API às vezes devolve "Vasco" em vez de "Vasco da Gama".
    return Clube.objects.filter(nome__istartswith=nome).first()


def numero_camisa(valor: Any) -> int | None:
    if valor in (None, ''):
        return None
    try:
        numero = int(str(valor).strip().lstrip('0') or '0')
    except (TypeError, ValueError):
        return None
    if 1 <= numero <= 99:
        return numero
    return None


def gravar_atleta(
    *,
    api_id: int | None,
    nome: str,
    clube: Clube,
    posicao: str,
    numero: int | None,
    gols: int,
    fonte: str,
) -> tuple[AtletaCatalogo, bool]:
    nome = (nome or '').strip()[:80]
    qs = AtletaCatalogo.objects.all()
    obj = None
    if api_id:
        obj = qs.filter(api_id=api_id).first()
    if obj is None:
        obj = qs.filter(nome=nome, clube=clube).first()

    if obj is None:
        obj = AtletaCatalogo.objects.create(
            api_id=api_id,
            nome=nome,
            clube=clube,
            posicao=posicao,
            numero=numero,
            gols=gols or 0,
            fonte=fonte,
        )
        return obj, True

    mudou = False
    if api_id and obj.api_id != api_id:
        obj.api_id = api_id
        mudou = True
    if nome and obj.nome != nome:
        obj.nome = nome
        mudou = True
    if obj.clube_id != clube.pk:
        obj.clube = clube
        mudou = True
    if posicao and (obj.fonte == 'local' or fonte == 'escalacao' or not obj.posicao):
        if obj.posicao != posicao:
            obj.posicao = posicao
            mudou = True
    if numero and obj.numero != numero:
        obj.numero = numero
        mudou = True
    if gols and gols > obj.gols:
        obj.gols = gols
        mudou = True
    if fonte != 'local' and obj.fonte != fonte:
        obj.fonte = fonte
        mudou = True
    if mudou:
        obj.save()
    return obj, False


def carregar_catalogo_local() -> int:
    criados = 0
    clubes = {c.sigla: c for c in Clube.objects.all()}
    for nome, sigla, posicao, numero, gols in CATALOGO_LOCAL:
        clube = clubes.get(sigla)
        if not clube:
            continue
        _, created = gravar_atleta(
            api_id=None,
            nome=nome,
            clube=clube,
            posicao=posicao,
            numero=numero,
            gols=gols,
            fonte='local',
        )
        if created:
            criados += 1
    return criados


def importar_artilharia(itens: list[dict[str, Any]]) -> tuple[int, int]:
    novos = atualizados = 0
    for item in itens:
        if not isinstance(item, dict):
            continue
        atleta = item.get('atleta') or {}
        if not isinstance(atleta, dict):
            continue
        clube = resolver_clube(item.get('time') if isinstance(item.get('time'), dict) else {})
        if not clube:
            continue
        nome = str(atleta.get('nome_popular') or atleta.get('nome') or '').strip()
        if not nome:
            continue
        api_id = atleta.get('atleta_id')
        try:
            api_id = int(api_id) if api_id is not None else None
        except (TypeError, ValueError):
            api_id = None
        posicao = mapear_posicao(posicao_sigla(atleta.get('posicao')))
        try:
            gols = int(item.get('gols') or 0)
        except (TypeError, ValueError):
            gols = 0
        _, created = gravar_atleta(
            api_id=api_id,
            nome=nome,
            clube=clube,
            posicao=posicao,
            numero=None,
            gols=gols,
            fonte='artilharia',
        )
        if created:
            novos += 1
        else:
            atualizados += 1
    return novos, atualizados


def importar_escalacao(itens: list[dict[str, Any]]) -> tuple[int, int]:
    novos = atualizados = 0
    for item in itens:
        atleta = item.get('atleta') or {}
        if not isinstance(atleta, dict):
            continue
        clube = resolver_clube(item.get('time') if isinstance(item.get('time'), dict) else {})
        if not clube:
            continue
        nome = str(atleta.get('nome_popular') or atleta.get('nome') or '').strip()
        if not nome:
            continue
        api_id = atleta.get('atleta_id')
        try:
            api_id = int(api_id) if api_id is not None else None
        except (TypeError, ValueError):
            api_id = None
        posicao = mapear_posicao(posicao_sigla(item.get('posicao') or atleta.get('posicao')))
        _, created = gravar_atleta(
            api_id=api_id,
            nome=nome,
            clube=clube,
            posicao=posicao,
            numero=numero_camisa(item.get('camisa')),
            gols=0,
            fonte='escalacao',
        )
        if created:
            novos += 1
        else:
            atualizados += 1
    return novos, atualizados
