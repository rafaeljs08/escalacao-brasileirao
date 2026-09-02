from django.contrib import messages
from django.db.models import Prefetch
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import EscalacaoForm, JogadorForm, NoticiaForm
from .models import AtletaCatalogo, Clube, Escalacao, Jogador, Noticia

POSICAO_LABEL = dict(Jogador.POSICAO_CHOICES)


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


def _filtrar_catalogo(request, ordenacao=('-gols', 'nome')):
    qs = AtletaCatalogo.objects.select_related('clube').order_by(*ordenacao)
    clube_id = request.GET.get('clube')
    if clube_id:
        qs = qs.filter(clube_id=clube_id)
    posicao = request.GET.get('posicao')
    if posicao in POSICAO_LABEL:
        qs = qs.filter(posicao=posicao)
    busca = (request.GET.get('q') or '').strip()
    if busca:
        qs = qs.filter(nome__icontains=busca)
    return qs, busca


def atletas_catalogo(request):
    qs, busca = _filtrar_catalogo(request, ('clube__nome', '-gols', 'nome'))
    atletas = list(qs)
    clube_id = request.GET.get('clube')
    posicao = request.GET.get('posicao') if request.GET.get('posicao') in POSICAO_LABEL else ''
    clubes = Clube.objects.all()
    clube_atual = clubes.filter(pk=clube_id).first() if clube_id else None

    agrupados = []
    atual = None
    for atleta in atletas:
        if atual is None or atual['clube'].pk != atleta.clube_id:
            atual = {'clube': atleta.clube, 'atletas': []}
            agrupados.append(atual)
        atual['atletas'].append(atleta)

    return render(request, 'futebol/atletas_catalogo.html', {
        'agrupados': agrupados,
        'total': len(atletas),
        'clubes': clubes,
        'clube_atual': clube_atual,
        'posicao_atual': posicao,
        'busca': busca,
        'posicoes': Jogador.POSICAO_CHOICES,
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
            'posicao_label': POSICAO_LABEL[atleta.posicao],
            'numero': atleta.numero,
            'gols': atleta.gols,
            'foto': atleta.foto_publica(),
        }
        for atleta in atletas[:80]
    ]
    return JsonResponse({'atletas': payload, 'total': len(payload)})
