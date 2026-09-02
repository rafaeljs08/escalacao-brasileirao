from django.contrib import messages
from django.db.models import Count, Prefetch
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import EscalacaoForm, JogadorForm, NoticiaForm
from .models import AtletaCatalogo, Clube, Escalacao, Jogador, Noticia
from .posicoes import (
    FUNCAO_CHOICES,
    FUNCAO_LABEL,
    FUNCOES_DO_SETOR,
    POSICAO_CHOICES,
    POSICAO_LABEL,
    SETOR_PLURAL,
    agrupar_por_clube,
    agrupar_por_setor,
    classe_badge,
)


def _escalacao_completa(pk):
    return get_object_or_404(
        Escalacao.objects.prefetch_related(
            Prefetch('jogadores', queryset=Jogador.objects.select_related('clube')),
            'jogadores__noticias',
        ),
        pk=pk,
    )


def _montar_slot(jogador, posicao):
    return {'jogador': jogador, 'posicao': posicao, 'label': POSICAO_LABEL[posicao]}


def _linha(escalacao, posicao):
    """Slots de uma posição, incluindo vagas ainda não preenchidas."""
    jogadores = escalacao.elenco_por_posicao(posicao)
    vagas = escalacao.vagas_posicao(posicao)
    slots = [_montar_slot(j, posicao) for j in jogadores[:vagas]]
    slots += [_montar_slot(None, posicao) for _ in range(max(vagas - len(slots), 0))]
    return slots


def _linhas_campo(escalacao):
    """Linhas do campo no padrão Cartola: ataque em cima, goleiro embaixo."""
    laterais = _linha(escalacao, 'LAT')
    zagueiros = _linha(escalacao, 'ZAG')
    defesa = laterais[:1] + zagueiros + laterais[1:]

    return [
        {'chave': 'ata', 'slots': _linha(escalacao, 'ATA')},
        {'chave': 'mei', 'slots': _linha(escalacao, 'MEI')},
        {'chave': 'def', 'slots': defesa},
        {'chave': 'gol', 'slots': _linha(escalacao, 'GOL')},
    ]


def _reservas(escalacao):
    """Jogadores cadastrados além das vagas da formação."""
    extras = []
    for posicao in escalacao.vagas:
        vagas = escalacao.vagas_posicao(posicao)
        extras += escalacao.elenco_por_posicao(posicao)[vagas:]
    return extras


def escalacao_lista(request):
    escalacoes = Escalacao.objects.prefetch_related('jogadores').all()
    return render(request, 'futebol/escalacao_lista.html', {
        'escalacoes': escalacoes,
        'total_clubes': Clube.objects.count(),
        'total_catalogo': AtletaCatalogo.objects.count(),
    })


def escalacao_criar(request):
    form = EscalacaoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        escalacao = form.save()
        messages.success(request, f'Time "{escalacao.nome}" criado. Agora escale seus jogadores.')
        return redirect(escalacao)

    return render(request, 'futebol/escalacao_form.html', {
        'form': form,
        'titulo': 'Criar novo time',
        'acao': 'Criar time',
    })


def escalacao_detalhe(request, pk):
    escalacao = _escalacao_completa(pk)
    jogadores = list(escalacao.jogadores.all())

    return render(request, 'futebol/escalacao_detalhe.html', {
        'escalacao': escalacao,
        'linhas': _linhas_campo(escalacao),
        'jogadores': jogadores,
        'elenco_setores': agrupar_por_setor(jogadores),
        'reservas': _reservas(escalacao),
        'total_gols': sum(j.gols for j in jogadores),
        'total_assistencias': sum(j.assistencias for j in jogadores),
        'clubes_representados': len({j.clube_id for j in jogadores}),
    })


def escalacao_editar(request, pk):
    escalacao = get_object_or_404(Escalacao, pk=pk)
    form = EscalacaoForm(request.POST or None, instance=escalacao)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Time atualizado.')
        return redirect(escalacao)

    return render(request, 'futebol/escalacao_form.html', {
        'form': form,
        'escalacao': escalacao,
        'titulo': 'Editar time',
        'acao': 'Salvar alterações',
    })


def escalacao_excluir(request, pk):
    escalacao = get_object_or_404(Escalacao, pk=pk)
    if request.method == 'POST':
        nome = escalacao.nome
        escalacao.delete()
        messages.success(request, f'Time "{nome}" excluído.')
        return redirect('futebol')

    return render(request, 'futebol/confirmar_exclusao.html', {
        'titulo': 'Excluir time',
        'descricao': f'O time "{escalacao.nome}" e todos os seus jogadores serão removidos.',
        'voltar_url': escalacao.get_absolute_url(),
    })


def jogador_criar(request, pk):
    escalacao = get_object_or_404(Escalacao, pk=pk)
    posicao = request.GET.get('posicao')
    inicial = {'posicao': posicao} if posicao in POSICAO_LABEL else {}

    form = JogadorForm(request.POST or None, escalacao=escalacao, initial=inicial)
    if request.method == 'POST' and form.is_valid():
        jogador = form.save(commit=False)
        jogador.escalacao = escalacao
        jogador.save()
        messages.success(request, f'{jogador.nome} escalado como {jogador.get_posicao_display().lower()}.')
        return redirect(escalacao)

    return render(request, 'futebol/jogador_form.html', {
        'form': form,
        'escalacao': escalacao,
        'titulo': 'Escalar jogador',
        'acao': 'Escalar jogador',
        'posicao_inicial': posicao if posicao in POSICAO_LABEL else '',
        'total_catalogo': AtletaCatalogo.objects.count(),
        'clubes': Clube.objects.all(),
        'posicoes': Jogador.POSICAO_CHOICES,
        'funcoes': FUNCAO_CHOICES,
    })


def jogador_editar(request, pk, jogador_pk):
    escalacao = get_object_or_404(Escalacao, pk=pk)
    jogador = get_object_or_404(Jogador, pk=jogador_pk, escalacao=escalacao)

    form = JogadorForm(request.POST or None, escalacao=escalacao, instance=jogador)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'{jogador.nome} atualizado.')
        return redirect(escalacao)

    return render(request, 'futebol/jogador_form.html', {
        'form': form,
        'escalacao': escalacao,
        'jogador': jogador,
        'titulo': 'Editar jogador',
        'acao': 'Salvar alterações',
        'posicao_inicial': jogador.posicao,
        'total_catalogo': AtletaCatalogo.objects.count(),
        'clubes': Clube.objects.all(),
        'posicoes': Jogador.POSICAO_CHOICES,
        'funcoes': FUNCAO_CHOICES,
    })


def jogador_excluir(request, pk, jogador_pk):
    escalacao = get_object_or_404(Escalacao, pk=pk)
    jogador = get_object_or_404(Jogador, pk=jogador_pk, escalacao=escalacao)

    if request.method == 'POST':
        nome = jogador.nome
        jogador.delete()
        messages.success(request, f'{nome} removido da escalação.')
        return redirect(escalacao)

    return render(request, 'futebol/confirmar_exclusao.html', {
        'titulo': 'Remover jogador',
        'descricao': f'{jogador.nome} será removido da escalação "{escalacao.nome}".',
        'voltar_url': escalacao.get_absolute_url(),
    })


def noticia_criar(request, pk, jogador_pk):
    escalacao = get_object_or_404(Escalacao, pk=pk)
    jogador = get_object_or_404(Jogador, pk=jogador_pk, escalacao=escalacao)

    form = NoticiaForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        noticia = form.save(commit=False)
        noticia.jogador = jogador
        noticia.save()
        messages.success(request, 'Notícia publicada.')
        return redirect(escalacao)

    return render(request, 'futebol/noticia_form.html', {
        'form': form,
        'escalacao': escalacao,
        'jogador': jogador,
    })


def noticia_excluir(request, pk, jogador_pk, noticia_pk):
    escalacao = get_object_or_404(Escalacao, pk=pk)
    noticia = get_object_or_404(Noticia, pk=noticia_pk, jogador__pk=jogador_pk, jogador__escalacao=escalacao)

    if request.method == 'POST':
        noticia.delete()
        messages.success(request, 'Notícia removida.')
        return redirect(escalacao)

    return render(request, 'futebol/confirmar_exclusao.html', {
        'titulo': 'Remover notícia',
        'descricao': f'A notícia "{noticia.titulo}" será removida.',
        'voltar_url': escalacao.get_absolute_url(),
    })


def _filtrar_catalogo(request, ordenacao=('-gols', 'nome'), sem=()):
    qs = AtletaCatalogo.objects.select_related('clube').order_by(*ordenacao)
    clube_id = request.GET.get('clube')
    if clube_id:
        qs = qs.filter(clube_id=clube_id)
    posicao = request.GET.get('posicao')
    if 'posicao' not in sem and posicao in POSICAO_LABEL:
        qs = qs.filter(posicao=posicao)
    funcao = request.GET.get('funcao')
    if 'funcao' not in sem and funcao in FUNCAO_LABEL:
        qs = qs.filter(funcao=funcao)
    busca = (request.GET.get('q') or '').strip()
    if busca:
        qs = qs.filter(nome__icontains=busca)
    return qs, busca


def _query_catalogo(request, **overrides):
    dados = request.GET.copy()
    for chave, valor in overrides.items():
        if valor in (None, ''):
            dados.pop(chave, None)
        else:
            dados[chave] = str(valor)
    return dados.urlencode()


def _chips_posicao(request, qs_base):
    totais = {
        linha['posicao']: linha['n']
        for linha in qs_base.order_by().values('posicao').annotate(n=Count('id'))
    }
    return [
        {
            'sigla': sigla,
            'rotulo': SETOR_PLURAL[sigla],
            'classe': sigla.lower(),
            'total': totais.get(sigla, 0),
            'url': _query_catalogo(request, posicao=sigla, funcao=''),
        }
        for sigla, _rotulo in POSICAO_CHOICES
    ]


def _chips_funcao(request, qs_setor, posicao):
    permitidas = set(FUNCOES_DO_SETOR.get(posicao, ()))
    totais: dict[str, int] = {}
    for linha in qs_setor.order_by().values('funcao', 'posicao').annotate(n=Count('id')):
        codigo = linha['funcao'] or linha['posicao']
        totais[codigo] = totais.get(codigo, 0) + linha['n']
    chips = []
    for sigla, rotulo in FUNCAO_CHOICES:
        if sigla not in permitidas:
            continue
        total = totais.get(sigla, 0)
        if total == 0 and request.GET.get('funcao') != sigla:
            continue
        chips.append({
            'sigla': sigla,
            'rotulo': rotulo,
            'classe': classe_badge(sigla),
            'total': total,
            'url': _query_catalogo(request, funcao=sigla),
        })
    return chips


def atletas_catalogo(request):
    agrupar = request.GET.get('agrupar')
    if agrupar not in {'clube', 'posicao'}:
        agrupar = 'posicao'
    qs, busca = _filtrar_catalogo(request, ('nome',))
    atletas = list(qs)
    qs_base, _ = _filtrar_catalogo(request, sem=('posicao', 'funcao'))
    qs_setor, _ = _filtrar_catalogo(request, sem=('funcao',))
    clube_id = request.GET.get('clube')
    posicao = request.GET.get('posicao') if request.GET.get('posicao') in POSICAO_LABEL else ''
    funcao = request.GET.get('funcao') if request.GET.get('funcao') in FUNCAO_LABEL else ''
    clubes = Clube.objects.all()
    clube_atual = clubes.filter(pk=clube_id).first() if clube_id else None

    return render(request, 'futebol/atletas_catalogo.html', {
        'setores': agrupar_por_setor(atletas) if agrupar == 'posicao' else [],
        'clubes_grupos': agrupar_por_clube(atletas) if agrupar == 'clube' else [],
        'agrupar': agrupar,
        'total': len(atletas),
        'total_base': qs_base.count(),
        'clubes': clubes,
        'clube_atual': clube_atual,
        'posicao_atual': posicao,
        'funcao_atual': funcao,
        'busca': busca,
        'posicoes': Jogador.POSICAO_CHOICES,
        'funcoes': FUNCAO_CHOICES,
        'chips_posicao': _chips_posicao(request, qs_base),
        'chips_funcao': _chips_funcao(request, qs_setor, posicao) if posicao else [],
        'url_todos': _query_catalogo(request, posicao='', funcao=''),
        'url_todas_funcoes': _query_catalogo(request, funcao=''),
        'url_agrupar_posicao': _query_catalogo(request, agrupar='posicao'),
        'url_agrupar_clube': _query_catalogo(request, agrupar='clube'),
    })


def catalogo_json(request):
    atletas, _busca = _filtrar_catalogo(request)
    payload = [
        {
            'id': atleta.pk,
            'nome': atleta.nome,
            'clube_id': atleta.clube_id,
            'clube': atleta.clube.sigla,
            'clube_nome': atleta.clube.nome,
            'posicao': atleta.posicao,
            'posicao_label': POSICAO_LABEL.get(atleta.posicao, atleta.posicao),
            'funcao': atleta.funcao or atleta.posicao,
            'funcao_label': atleta.funcao_rotulo(),
            'numero': atleta.numero,
            'gols': atleta.gols,
            'foto': atleta.foto_publica(),
        }
        for atleta in atletas[:80]
    ]
    return JsonResponse({'atletas': payload, 'total': len(payload)})
