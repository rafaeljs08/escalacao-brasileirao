from __future__ import annotations

import logging
import shutil
from pathlib import Path

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.text import slugify

from futebol.assetsmgr import config as cfg
from futebol.assetsmgr.cache import cache_hit, hash_arquivo
from futebol.assetsmgr.catalog_json import agora, gravar_json
from futebol.assetsmgr.downloader import AssetDownloader
from futebol.assetsmgr.filelog import log_download, log_missing
from futebol.assetsmgr.placeholders import garantir_placeholders
from futebol.assetsmgr.providers import load_providers, primeiro_logo, primeira_foto
from futebol.assetsmgr.providers.base import PlayerRecord, TeamRecord
from futebol.assetsmgr.providers.cartola import CLUBES_EXTRA
from futebol.assetsmgr.validator import validate_image
from futebol.models import Asset, AtletaCatalogo, Clube

logger = logging.getLogger('assetsmgr.sync')


def _relativo(path: Path) -> str:
    try:
        return str(path.relative_to(cfg.assets_dir())).replace('\\', '/')
    except ValueError:
        return path.name


def _sigla_app(team: TeamRecord) -> str:
    return str((team.extra or {}).get('app_sigla') or team.short_name or '').upper()[:3]


def _garantir_clube(team: TeamRecord) -> Clube | None:
    """Associa o time do provider a um Clube do app, criando os da temporada atual se faltarem."""
    sigla = _sigla_app(team)
    if not sigla:
        return None
    clube = Clube.objects.filter(fonte_id=team.id).first()
    if clube:
        return clube
    clube = Clube.objects.filter(sigla=sigla).first()
    if clube:
        return clube
    extra = CLUBES_EXTRA.get(sigla, {})
    nome = (extra.get('nome') or team.name or sigla)[:60]
    clube = Clube.objects.filter(nome=nome).first()
    if clube:
        return clube
    from futebol.management.commands.seed_brasileirao import escudo_svg

    primaria = extra.get('cor_primaria') or '#166534'
    secundaria = extra.get('cor_secundaria') or '#f8fafc'
    destino = Path(settings.BASE_DIR) / 'futebol/static/futebol/img/clubes'
    destino.mkdir(parents=True, exist_ok=True)
    arquivo = f'{sigla.lower()}.svg'
    (destino / arquivo).write_text(escudo_svg(sigla, primaria, secundaria), encoding='utf-8')
    return Clube.objects.create(
        nome=nome,
        sigla=sigla,
        cidade=extra.get('cidade') or '—',
        estado=(extra.get('estado') or 'BR')[:2],
        cor_primaria=primaria,
        cor_secundaria=secundaria,
        escudo=f'futebol/img/clubes/{arquivo}',
        slug=team.slug or slugify(nome),
        fonte_id=team.id,
        logo_url=team.logo_url or '',
    )


def _destino_logo(raiz: Path, team: TeamRecord, url: str | None) -> Path:
    if url and url.lower().split('?')[0].endswith('.svg'):
        return raiz / 'teams' / f'{team.id}.svg'
    return raiz / 'teams' / f'{team.id}.png'


def _asset_existente(entity_type: str, entity_id: int, asset_type: str) -> Asset | None:
    return Asset.objects.filter(
        entity_type=entity_type, entity_id=entity_id, asset_type=asset_type,
    ).first()


def _gravar_asset(**kwargs) -> Asset:
    kwargs['updated_at'] = timezone.now()
    obj, _ = Asset.objects.update_or_create(
        entity_type=kwargs.pop('entity_type'),
        entity_id=kwargs.pop('entity_id'),
        asset_type=kwargs.pop('asset_type'),
        defaults=kwargs,
    )
    return obj


class SyncReport(dict):
    def to_json(self) -> Path:
        return gravar_json('sync_report.json', self)


def sincronizar(
    *,
    teams: bool = True,
    players: bool = True,
    assets: bool = True,
    validate: bool = True,
    missing_only: bool = False,
    dry_run: bool = False,
    force: bool = False,
    stdout=None,
) -> dict:
    def log(msg: str) -> None:
        logger.info(msg)
        if stdout:
            if getattr(stdout, 'ending', None) is None:
                stdout.write(msg + '\n')
            else:
                stdout.write(msg)

    raiz = cfg.assets_dir()
    garantir_placeholders(raiz)
    (raiz / 'teams').mkdir(parents=True, exist_ok=True)
    (raiz / 'players').mkdir(parents=True, exist_ok=True)
    cfg.logs_dir().mkdir(parents=True, exist_ok=True)

    providers = load_providers()
    nomes = ', '.join(p.name for p in providers)
    log(f'[OK] Providers ativos: {nomes}')

    times: list[TeamRecord] = []
    jogadores: list[PlayerRecord] = []
    if teams or players:
        for provider in providers:
            if provider.name == 'fallback':
                continue
            try:
                lote_t = provider.get_teams()
                lote_j = provider.get_players()
            except Exception as exc:  # noqa: BLE001 — provider isolado não pode derrubar o sync
                log(f'[WARN] Provider {provider.name} falhou: {exc}')
                continue
            if lote_t and not times:
                times = lote_t
            if lote_j and not jogadores:
                jogadores = lote_j
            if times and jogadores:
                break

    if teams:
        log(f'[OK] Clubes encontrados: {len(times)}')
        if not dry_run:
            for team in times:
                clube = _garantir_clube(team)
                if not clube:
                    continue
                clube.fonte_id = team.id
                clube.slug = team.slug or slugify(clube.nome)
                clube.logo_url = team.logo_url
                clube.save(update_fields=['fonte_id', 'slug', 'logo_url'])

    if players:
        log(f'[OK] Jogadores encontrados: {len(jogadores)}')
        if not dry_run:
            for player in jogadores:
                team = next((t for t in times if t.id == player.team_id), None)
                clube = _garantir_clube(team) if team else None
                if not clube:
                    continue
                defaults = {
                    'nome': player.name[:80],
                    'slug': player.slug or slugify(player.name),
                    'clube': clube,
                    'posicao': player.position or 'MEI',
                    'foto_url': player.photo_url,
                    'fonte': 'cartola' if player.source == 'cartola' else player.source,
                }
                obj = AtletaCatalogo.objects.filter(fonte_id=player.id).first()
                if obj is None:
                    obj = AtletaCatalogo.objects.filter(nome=player.name, clube=clube).first()
                if obj is None:
                    try:
                        with transaction.atomic():
                            AtletaCatalogo.objects.create(fonte_id=player.id, **defaults)
                    except IntegrityError:
                        log(f'[WARN] jogador duplicado ignorado: {player.name} ({clube.sigla})')
                else:
                    obj.fonte_id = player.id
                    for chave, valor in defaults.items():
                        setattr(obj, chave, valor)
                    obj.save()

    fotos_encontradas = 0
    fotos_baixadas = 0
    escudos_encontrados = 0
    escudos_baixados = 0
    ausentes = 0
    erros = 0
    downloader = AssetDownloader()
    url_cache: dict[str, Path] = {}

    if assets or missing_only:
        for team in times:
            url, fonte, fallback = primeiro_logo(team, providers)
            destino = _destino_logo(raiz, team, url)
            if url:
                escudos_encontrados += 1
            if dry_run:
                estado = 'existia' if destino.exists() else ('baixaria' if url else 'ausente')
                log(f'  escudo {team.short_name}: {estado} [{fonte or "-"}]')
                continue
            if missing_only and destino.exists() and validate_image(destino).get('valid'):
                continue
            anterior = _asset_existente('team', team.id, 'logo')
            resultado = _baixar_ou_copiar(
                downloader, url, destino, url_cache, force=force, normalize=False,
                url_conhecida=anterior.url if anterior else '',
                hash_conhecido=anterior.sha256 if anterior else '',
            )
            status, rel = _aplicar_resultado(resultado, fallback)
            if resultado.get('error'):
                erros += 1
                ausentes += 1
                log_missing(f'team {team.id} {team.name}: {resultado.get("error")}')
            elif resultado.get('skipped'):
                log_download(f'team {team.id} cache {destino.name}')
            elif resultado.get('valid'):
                escudos_baixados += 1
                log_download(f'team {team.id} {fonte} -> {destino.name}')
            clube = _garantir_clube(team)
            if clube and rel:
                clube.logo_local = rel
                clube.logo_fonte = fonte
                clube.save(update_fields=['logo_local', 'logo_fonte'])
            _gravar_asset(
                entity_type='team', entity_id=team.id, asset_type='logo',
                url=url or '', local_path=rel, provider=fonte,
                sha256=resultado.get('sha256') or '',
                size=int(resultado.get('size') or 0),
                mime=resultado.get('mime') or '',
                width=resultado.get('width'), height=resultado.get('height'),
                status=status, fallback_used=fallback or fonte == 'fallback',
            )

        fotos_dry = 0
        for player in jogadores:
            url, fonte, fallback = primeira_foto(player, providers)
            destino = raiz / 'players' / f'{player.id}.png'
            if url:
                fotos_encontradas += 1
            if dry_run:
                estado = 'existia' if destino.exists() else ('baixaria' if url else 'ausente')
                if fotos_dry < 8:
                    log(f'  foto {player.id} {player.name}: {estado} [{fonte or "-"}]{" FALLBACK" if fallback else ""}')
                fotos_dry += 1
                continue
            if missing_only and destino.exists() and validate_image(destino).get('valid'):
                continue
            anterior = _asset_existente('player', player.id, 'photo')
            resultado = _baixar_ou_copiar(
                downloader, url, destino, url_cache, force=force, normalize=True,
                url_conhecida=anterior.url if anterior else '',
                hash_conhecido=anterior.sha256 if anterior else '',
            )
            if not resultado.get('valid'):
                origem = raiz / 'placeholders' / 'player.png'
                if origem.exists():
                    shutil.copyfile(origem, destino)
                    resultado = {**validate_image(destino), 'sha256': hash_arquivo(destino), 'skipped': False}
                    fonte = 'fallback'
                    fallback = True
                    url = ''
            status, rel = _aplicar_resultado(resultado, fallback)
            if resultado.get('error') and status == 'error':
                erros += 1
                log_missing(f'player {player.id} {player.name}: {resultado.get("error")}')
            if status in {'missing', 'invalid', 'error'}:
                ausentes += 1
                log_missing(f'player {player.id} {player.name} status={status}')
            elif not resultado.get('skipped'):
                fotos_baixadas += 1
                log_download(f'player {player.id} {fonte} -> {destino.name}')
            atleta = AtletaCatalogo.objects.filter(fonte_id=player.id).first()
            if atleta:
                atleta.foto_url = url or ''
                atleta.foto_local = rel
                atleta.foto_fonte = fonte
                atleta.foto_status = 'fallback' if fallback else ('ok' if status == 'ok' else status)
                atleta.save(update_fields=['foto_url', 'foto_local', 'foto_fonte', 'foto_status'])
            _gravar_asset(
                entity_type='player', entity_id=player.id, asset_type='photo',
                url=url or '', local_path=rel, provider=fonte,
                sha256=resultado.get('sha256') or '',
                size=int(resultado.get('size') or 0),
                mime=resultado.get('mime') or '',
                width=resultado.get('width'), height=resultado.get('height'),
                status=status, fallback_used=fallback,
            )
        if dry_run and fotos_dry > 8:
            log(f'  ... {fotos_dry - 8} fotos adicionais omitidas no log')

    if validate and not dry_run:
        for pasta, tipo in (('teams', 'logo'), ('players', 'photo')):
            for arquivo in (raiz / pasta).glob('*'):
                if arquivo.suffix == '.tmp':
                    continue
                checagem = validate_image(arquivo)
                if not checagem.get('valid'):
                    ausentes += 1
                    log(f'[WARN] inválido: {arquivo.name} ({checagem.get("error")})')

    times_json = [
        {
            'id': t.id,
            'name': t.name,
            'short_name': t.short_name,
            'slug': t.slug,
            'logo_url': t.logo_url,
            'local_logo_path': f'teams/{t.id}.svg' if (t.logo_url or '').lower().split('?')[0].endswith('.svg') else f'teams/{t.id}.png',
            'source': t.source,
            'updated_at': agora(),
        }
        for t in times
    ]
    players_json = [
        {
            'id': p.id,
            'name': p.name,
            'slug': p.slug,
            'team_id': p.team_id,
            'position': p.position,
            'photo_url': p.photo_url,
            'local_photo_path': f'players/{p.id}.png',
            'source': p.source,
            'fallback_used': p.generic_photo,
            'updated_at': agora(),
        }
        for p in jogadores
    ]
    if not dry_run:
        gravar_json('teams.json', times_json)
        gravar_json('players.json', players_json)
        gravar_json('assets.json', {
            'season': cfg.season(),
            'generated_at': agora(),
            'teams': times_json,
            'players': players_json,
        })

    relatorio = {
        'season': cfg.season(),
        'dry_run': dry_run,
        'providers': [p.name for p in providers],
        'teams': {'total': len(times), 'success': escudos_encontrados, 'missing': max(len(times) - escudos_encontrados, 0)},
        'players': {
            'total': len(jogadores),
            'photos_found': fotos_encontradas,
            'photos_missing': max(len(jogadores) - fotos_encontradas, 0),
        },
        'downloads': {'success': fotos_baixadas + escudos_baixados, 'failed': erros, 'missing_assets': ausentes},
        'generated_at': agora(),
    }
    if not dry_run:
        gravar_json('sync_report.json', relatorio)

    log(f'[OK] Escudos encontrados: {escudos_encontrados}')
    log(f'[OK] Escudos baixados: {escudos_baixados}')
    log(f'[OK] Fotos encontradas: {fotos_encontradas}')
    log(f'[OK] Fotos baixadas: {fotos_baixadas}')
    log(f'[WARN] Assets ausentes: {ausentes}')
    log(f'[ERROR] Downloads com erro: {erros}')
    return relatorio


def _baixar_ou_copiar(
    downloader,
    url,
    destino: Path,
    url_cache: dict[str, Path],
    *,
    force: bool,
    normalize: bool,
    url_conhecida: str = '',
    hash_conhecido: str = '',
) -> dict:
    if not url:
        return {'valid': False, 'error': 'sem URL'}
    if not force and cache_hit(destino, url, url_conhecida, hash_conhecido):
        return {**validate_image(destino), 'skipped': True, 'path': str(destino), 'sha256': hash_arquivo(destino)}
    if url in url_cache and url_cache[url].exists():
        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(url_cache[url], destino)
        return {**validate_image(destino), 'skipped': False, 'path': str(destino), 'sha256': hash_arquivo(destino)}
    resultado = downloader.download(url, destino, force=True, normalize=normalize)
    if resultado.get('valid') and resultado.get('path'):
        url_cache[url] = Path(resultado['path'])
    return resultado


def _aplicar_resultado(resultado: dict, fallback: bool) -> tuple[str, str]:
    path = resultado.get('path') or ''
    rel = _relativo(Path(path)) if path else ''
    if resultado.get('valid'):
        return ('fallback' if fallback else 'ok'), rel
    if resultado.get('error'):
        return 'error', rel
    return 'missing', rel
