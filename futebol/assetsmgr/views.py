from __future__ import annotations

import json
import mimetypes
from pathlib import Path

from django.core.paginator import Paginator
from django.db.models import Q
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods

from futebol.assetsmgr import config as cfg
from futebol.assetsmgr.placeholders import garantir_placeholders
from futebol.assetsmgr.pipeline import sincronizar
from futebol.models import Asset, AtletaCatalogo, Clube


def _relatorio() -> dict:
    caminho = cfg.data_dir() / 'sync_report.json'
    if not caminho.exists():
        return {}
    try:
        return json.loads(caminho.read_text(encoding='utf-8'))
    except json.JSONDecodeError:
        return {}


def _player_payload(atleta: AtletaCatalogo) -> dict:
    return {
        'id': atleta.fonte_id or atleta.pk,
        'name': atleta.nome,
        'team': {'id': atleta.clube.fonte_id or atleta.clube_id, 'name': atleta.clube.nome},
        'position': atleta.get_posicao_display(),
        'photo': atleta.foto_publica(),
        'source': atleta.foto_fonte or atleta.fonte,
        'status': atleta.foto_status,
        'fallback_used': atleta.foto_status == 'fallback',
    }


@require_GET
def api_teams(request):
    clubes = Clube.objects.all()
    return JsonResponse({'teams': [
        {
            'id': c.fonte_id or c.pk,
            'name': c.nome,
            'short_name': c.sigla,
            'slug': c.slug,
            'logo': c.escudo_publico(),
            'source': c.logo_fonte,
        }
        for c in clubes
    ]})


@require_GET
def api_team_detail(request, pk):
    clube = get_object_or_404(Clube, fonte_id=pk) if Clube.objects.filter(fonte_id=pk).exists() else get_object_or_404(Clube, pk=pk)
    return JsonResponse({
        'id': clube.fonte_id or clube.pk,
        'name': clube.nome,
        'short_name': clube.sigla,
        'logo': clube.escudo_publico(),
        'source': clube.logo_fonte,
        'local_logo_path': clube.logo_local,
    })


@require_GET
def api_team_logo(request, pk):
    clube = Clube.objects.filter(fonte_id=pk).first() or get_object_or_404(Clube, pk=pk)
    return redirect(clube.escudo_publico())


@require_GET
def api_players(request):
    qs = AtletaCatalogo.objects.select_related('clube')
    clube = request.GET.get('team')
    if clube:
        qs = qs.filter(Q(clube__fonte_id=clube) | Q(clube_id=clube))
    return JsonResponse({'players': [_player_payload(a) for a in qs[:800]]})


@require_GET
def api_player_detail(request, pk):
    atleta = AtletaCatalogo.objects.filter(fonte_id=pk).select_related('clube').first()
    if atleta is None:
        atleta = get_object_or_404(AtletaCatalogo.objects.select_related('clube'), pk=pk)
    return JsonResponse(_player_payload(atleta))


@require_GET
def api_player_image(request, pk):
    atleta = AtletaCatalogo.objects.filter(fonte_id=pk).first() or get_object_or_404(AtletaCatalogo, pk=pk)
    return redirect(atleta.foto_publica())


@require_GET
def api_assets_status(request):
    return JsonResponse({
        'teams': Clube.objects.count(),
        'players': AtletaCatalogo.objects.count(),
        'assets': Asset.objects.count(),
        'ok': Asset.objects.filter(status='ok').count(),
        'missing': Asset.objects.filter(status='missing').count(),
        'invalid': Asset.objects.filter(status='invalid').count(),
        'fallback': Asset.objects.filter(status='fallback').count(),
        'last_sync': _relatorio(),
    })


@require_GET
def api_assets_missing(request):
    faltando = Asset.objects.exclude(status__in=['ok', 'fallback'])
    return JsonResponse({'missing': [
        {
            'entity_type': a.entity_type,
            'entity_id': a.entity_id,
            'asset_type': a.asset_type,
            'status': a.status,
            'provider': a.provider,
        }
        for a in faltando
    ]})


@require_GET
def api_sync_status(request):
    return JsonResponse(_relatorio() or {'status': 'never'})


@require_GET
def servir_arquivo(request, kind: str, filename: str):
    if kind not in {'teams', 'players', 'placeholders'}:
        raise Http404()
    if Path(filename).name != filename or '..' in filename:
        raise Http404()
    caminho = cfg.assets_dir() / kind / filename
    if not caminho.exists():
        garantir_placeholders(cfg.assets_dir())
        fallback = 'player.png' if kind == 'players' else 'team.png'
        caminho = cfg.assets_dir() / 'placeholders' / fallback
    if not caminho.exists():
        raise Http404()
    tipo, _ = mimetypes.guess_type(str(caminho))
    return FileResponse(caminho.open('rb'), content_type=tipo or 'application/octet-stream')


@require_http_methods(['GET', 'POST'])
def painel_assets(request):
    mensagem = ''
    if request.method == 'POST':
        acao = request.POST.get('acao')
        if acao == 'sync':
            sincronizar(stdout=None)
            mensagem = 'Sincronização concluída.'
        elif acao == 'validate':
            sincronizar(teams=False, players=False, assets=False, validate=True)
            mensagem = 'Validação concluída.'
        elif acao == 'missing':
            sincronizar(missing_only=True)
            mensagem = 'Download dos ausentes disparado.'
        elif acao == 'dry':
            sincronizar(dry_run=True, stdout=None)
            mensagem = 'Dry-run concluído — nenhum arquivo foi baixado.'

    busca = (request.GET.get('q') or '').strip()
    status = (request.GET.get('status') or '').strip()
    clube_id = (request.GET.get('clube') or '').strip()
    qs = AtletaCatalogo.objects.select_related('clube').order_by('clube__nome', 'nome')
    if busca:
        qs = qs.filter(nome__icontains=busca)
    if status:
        qs = qs.filter(foto_status=status)
    if clube_id.isdigit():
        qs = qs.filter(clube_id=int(clube_id))
    pagina = Paginator(qs, 50).get_page(request.GET.get('page'))

    return render(request, 'futebol/assets_painel.html', {
        'mensagem': mensagem,
        'total_clubes': Clube.objects.count(),
        'total_jogadores': AtletaCatalogo.objects.count(),
        'fotos_ok': AtletaCatalogo.objects.filter(foto_status='ok').count(),
        'fotos_ausentes': AtletaCatalogo.objects.filter(foto_status='missing').count(),
        'fotos_fallback': AtletaCatalogo.objects.filter(foto_status='fallback').count(),
        'escudos': Clube.objects.exclude(logo_local='').count(),
        'invalidos': Asset.objects.filter(status='invalid').count(),
        'ultimo_sync': _relatorio(),
        'atletas': pagina,
        'pagina': pagina,
        'busca': busca,
        'status_atual': status,
        'clube_atual': int(clube_id) if clube_id.isdigit() else '',
        'clubes': Clube.objects.all(),
        'status_opcoes': AtletaCatalogo.FOTO_STATUS,
    })
