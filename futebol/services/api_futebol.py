"""Cliente da API Futebol (https://api.api-futebol.com.br/v1).

Auth: header ``Authorization: Bearer <chave>``.
Brasileirão Série A: ``campeonato_id = 10``.

O plano gratuito não publica um endpoint de elenco completo. Os atletas
vêm da artilharia e, quando a chave permite, das escalações das partidas.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urljoin

import requests
from django.conf import settings

BASE_URL = "https://api.api-futebol.com.br/v1/"
CAMPEONATO_SERIE_A = 10
TIMEOUT = 25

# Siglas da API → siglas dos 20 clubes do seed (CLUBES em seed_brasileirao).
SIGLA_API_PARA_CLUBE = {
    "CAM": "CAM",
    "ATL": "CAM",
    "BAH": "BAH",
    "BOT": "BOT",
    "RBB": "BGT",
    "BGT": "BGT",
    "BRA": "BGT",
    "CEA": "CEA",
    "CEAR": "CEA",
    "COR": "COR",
    "CRU": "CRU",
    "FLA": "FLA",
    "FLU": "FLU",
    "FOR": "FOR",
    "GRE": "GRE",
    "INT": "INT",
    "JUV": "JUV",
    "MIR": "MIR",
    "PAL": "PAL",
    "SAN": "SAN",
    "SAO": "SAO",
    "SPO": "SPT",
    "SPT": "SPT",
    "SCR": "SPT",
    "VAS": "VAS",
    "VIT": "VIT",
}

POSICAO_API_PARA_APP = {
    "G": "GOL",
    "GOL": "GOL",
    "ZAD": "ZAG",
    "ZAE": "ZAG",
    "ZAG": "ZAG",
    "LAD": "LAT",
    "LAE": "LAT",
    "LAT": "LAT",
    "VOL": "MEI",
    "MEC": "MEI",
    "MEI": "MEI",
    "SA": "ATA",
    "ATA": "ATA",
    "PD": "ATA",
    "PE": "ATA",
    "CA": "ATA",
}


class ApiFutebolError(RuntimeError):
    pass


def campeonato_id() -> int:
    return int(getattr(settings, "API_FUTEBOL_CAMPEONATO_ID", CAMPEONATO_SERIE_A))


def api_key() -> str:
    return (getattr(settings, "API_FUTEBOL_KEY", "") or "").strip()


def tem_chave() -> bool:
    return bool(api_key())


def _headers() -> dict[str, str]:
    key = api_key()
    if not key:
        raise ApiFutebolError(
            "Defina API_FUTEBOL_KEY no ambiente (cadastro em https://dash.api-futebol.com.br)."
        )
    return {
        "Authorization": f"Bearer {key}",
        "Accept": "application/json",
    }


def get(path: str, params: dict[str, Any] | None = None) -> Any:
    url = urljoin(BASE_URL, path.lstrip("/"))
    try:
        response = requests.get(url, headers=_headers(), params=params, timeout=TIMEOUT)
    except requests.RequestException as exc:
        raise ApiFutebolError(f"Falha de rede ao chamar {url}: {exc}") from exc

    if response.status_code == 401:
        raise ApiFutebolError("Chave da API Futebol inválida ou expirada (HTTP 401).")
    if response.status_code == 403:
        raise ApiFutebolError("Acesso negado a este endpoint no seu plano (HTTP 403).")
    if response.status_code == 429:
        raise ApiFutebolError("Limite de requisições da API Futebol atingido (HTTP 429).")
    if not response.ok:
        raise ApiFutebolError(f"API Futebol retornou HTTP {response.status_code} em {url}.")
    return response.json()


def posicao_sigla(bloco: Any) -> str:
    """A API devolve posicao como objeto {nome, sigla} ou como lista vazia."""
    if isinstance(bloco, dict):
        return str(bloco.get("sigla") or "").upper()
    return ""


def mapear_posicao(sigla_api: str, fallback: str = "MEI") -> str:
    return POSICAO_API_PARA_APP.get((sigla_api or "").upper(), fallback)


def mapear_sigla_clube(sigla_api: str) -> str | None:
    return SIGLA_API_PARA_CLUBE.get((sigla_api or "").upper())


def fetch_tabela(campeonato: int | None = None) -> list[dict[str, Any]]:
    cid = campeonato or campeonato_id()
    data = get(f"campeonatos/{cid}/tabela")
    if not isinstance(data, list):
        raise ApiFutebolError("Resposta inesperada em /tabela.")
    return data


def fetch_artilharia(campeonato: int | None = None) -> list[dict[str, Any]]:
    cid = campeonato or campeonato_id()
    data = get(f"campeonatos/{cid}/artilharia")
    if not isinstance(data, list):
        raise ApiFutebolError("Resposta inesperada em /artilharia.")
    return data


def fetch_rodadas(campeonato: int | None = None) -> list[dict[str, Any]]:
    cid = campeonato or campeonato_id()
    data = get(f"campeonatos/{cid}/rodadas")
    if not isinstance(data, list):
        raise ApiFutebolError("Resposta inesperada em /rodadas.")
    return data


def fetch_rodada(rodada: int, campeonato: int | None = None) -> dict[str, Any]:
    cid = campeonato or campeonato_id()
    data = get(f"campeonatos/{cid}/rodadas/{rodada}")
    if not isinstance(data, dict):
        raise ApiFutebolError(f"Resposta inesperada em /rodadas/{rodada}.")
    return data


def fetch_partida(partida_id: int) -> dict[str, Any]:
    data = get(f"partidas/{partida_id}")
    if not isinstance(data, dict):
        raise ApiFutebolError(f"Resposta inesperada em /partidas/{partida_id}.")
    return data


def ids_partidas_recentes(limite_rodadas: int = 1) -> list[int]:
    """Ids das partidas das últimas rodadas já realizadas."""
    rodadas = fetch_rodadas()
    candidatas = [r for r in rodadas if isinstance(r, dict) and r.get("rodada")]
    candidatas.sort(key=lambda r: int(r.get("rodada") or 0), reverse=True)

    ids: list[int] = []
    usadas = 0
    for rodada in candidatas:
        status = str(rodada.get("status") or "").lower()
        if status in {"agendada", "agendado"}:
            continue
        detalhe = fetch_rodada(int(rodada["rodada"]))
        for partida in detalhe.get("partidas") or []:
            if isinstance(partida, dict) and partida.get("partida_id"):
                ids.append(int(partida["partida_id"]))
        usadas += 1
        if usadas >= limite_rodadas:
            break
    return ids


def atletas_da_escalacao(partida: dict[str, Any]) -> list[dict[str, Any]]:
    """Extrai titulares e reservas das duas equipes de uma partida."""
    saida: list[dict[str, Any]] = []
    escalacoes = partida.get("escalacoes") or {}
    if not isinstance(escalacoes, dict):
        return saida

    times = {
        "mandante": partida.get("time_mandante") or {},
        "visitante": partida.get("time_visitante") or {},
    }
    for lado, time in times.items():
        bloco = escalacoes.get(lado) or {}
        if not isinstance(bloco, dict):
            continue
        for papel in ("titulares", "reservas"):
            lista = bloco.get(papel) or []
            if not isinstance(lista, list):
                continue
            for item in lista:
                if not isinstance(item, dict):
                    continue
                atleta = item.get("atleta") or {}
                if not isinstance(atleta, dict) or not atleta.get("atleta_id"):
                    continue
                saida.append(
                    {
                        "atleta": atleta,
                        "time": time if isinstance(time, dict) else {},
                        "camisa": item.get("camisa"),
                        "posicao": item.get("posicao"),
                    }
                )
    return saida
