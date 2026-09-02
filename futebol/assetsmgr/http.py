"""Cliente HTTP respeitoso: timeout, retry, backoff, 429 e allowlist de hosts."""

from __future__ import annotations

import logging
import time
from typing import Any
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from futebol.assetsmgr import config as cfg

logger = logging.getLogger('assetsmgr.http')

USER_AGENT = 'EscalacaoBrasileirao-AssetManager/1.0 (academic; respectful-sync)'


def host_permitido(url: str) -> bool:
    host = (urlparse(url).hostname or '').lower()
    if not host:
        return False
    return any(host == permitido or host.endswith('.' + permitido) for permitido in cfg.allowed_hosts())


class HttpError(RuntimeError):
    def __init__(self, mensagem: str, status: int | None = None):
        super().__init__(mensagem)
        self.status = status


def sessao() -> requests.Session:
    retry = Retry(
        total=cfg.max_retries(),
        backoff_factor=1,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({'GET', 'HEAD'}),
        raise_on_status=False,
    )
    session = requests.Session()
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('https://', adapter)
    session.mount('http://', adapter)
    session.headers.update({'User-Agent': USER_AGENT, 'Accept': '*/*'})
    return session


class JsonClient:
    def __init__(self, session: requests.Session | None = None):
        self.session = session or sessao()
        self._ultimo = 0.0

    def _aguardar(self) -> None:
        delay = cfg.request_delay()
        if delay <= 0:
            return
        decorrido = time.monotonic() - self._ultimo
        if decorrido < delay:
            time.sleep(delay - decorrido)

    def get_json(self, url: str, params: dict | None = None, headers: dict | None = None) -> Any:
        if not host_permitido(url):
            raise HttpError(f'Host não permitido: {urlparse(url).hostname}')
        self._aguardar()
        try:
            resposta = self.session.get(
                url,
                params=params,
                headers=headers,
                timeout=cfg.timeout(),
                allow_redirects=True,
            )
        except requests.RequestException as exc:
            raise HttpError(f'Falha de rede: {exc}') from exc
        finally:
            self._ultimo = time.monotonic()

        if resposta.status_code == 404:
            raise HttpError('Não encontrado', status=404)
        if resposta.status_code == 403:
            raise HttpError('Acesso negado (403)', status=403)
        if resposta.status_code == 429:
            raise HttpError('Rate limit (429)', status=429)
        if not resposta.ok:
            raise HttpError(f'HTTP {resposta.status_code}', status=resposta.status_code)
        return resposta.json()

    def get_bytes(self, url: str) -> tuple[bytes, str, int]:
        if not host_permitido(url):
            raise HttpError(f'Host não permitido: {urlparse(url).hostname}')
        self._aguardar()
        try:
            resposta = self.session.get(url, timeout=cfg.timeout(), allow_redirects=True)
        except requests.RequestException as exc:
            raise HttpError(f'Falha de rede: {exc}') from exc
        finally:
            self._ultimo = time.monotonic()

        if resposta.status_code in {403, 404, 429}:
            raise HttpError(f'HTTP {resposta.status_code}', status=resposta.status_code)
        if not resposta.ok:
            raise HttpError(f'HTTP {resposta.status_code}', status=resposta.status_code)
        tipo = (resposta.headers.get('Content-Type') or '').split(';')[0].strip().lower()
        return resposta.content, tipo, resposta.status_code
