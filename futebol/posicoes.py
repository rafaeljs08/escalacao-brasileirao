"""Posição na formação (5 setores) vs função tática exata."""

from __future__ import annotations

from django.utils.text import slugify

# Setor da formação — o campo e as vagas usam só estes códigos.
POSICAO_CHOICES = [
    ('GOL', 'Goleiro'),
    ('ZAG', 'Zagueiro'),
    ('LAT', 'Lateral'),
    ('MEI', 'Meia'),
    ('ATA', 'Atacante'),
]

# Função tática exata. Continua mapeada a um setor para a formação.
FUNCAO_CHOICES = [
    ('GOL', 'Goleiro'),
    ('LD', 'Lateral direito'),
    ('LE', 'Lateral esquerdo'),
    ('LAT', 'Lateral'),
    ('ZAG', 'Zagueiro'),
    ('VOL', 'Volante'),
    ('MC', 'Meia central'),
    ('MAT', 'Meia-atacante'),
    ('MD', 'Meia direita'),
    ('ME', 'Meia esquerda'),
    ('MEI', 'Meia'),
    ('PD', 'Ponta direita'),
    ('PE', 'Ponta esquerda'),
    ('SA', 'Segundo atacante'),
    ('CA', 'Centroavante'),
    ('ATA', 'Atacante'),
]

FUNCAO_LABEL = dict(FUNCAO_CHOICES)
POSICAO_LABEL = dict(POSICAO_CHOICES)

FUNCAO_PARA_SETOR = {
    'GOL': 'GOL',
    'LD': 'LAT',
    'LE': 'LAT',
    'LAT': 'LAT',
    'ZAG': 'ZAG',
    'VOL': 'MEI',
    'MC': 'MEI',
    'MAT': 'MEI',
    'MD': 'MEI',
    'ME': 'MEI',
    'MEI': 'MEI',
    'PD': 'ATA',
    'PE': 'ATA',
    'SA': 'ATA',
    'CA': 'ATA',
    'ATA': 'ATA',
}

# Funções que pertencem a cada setor (filtro da vaga no campo).
FUNCOES_DO_SETOR = {
    'GOL': ('GOL',),
    'ZAG': ('ZAG',),
    'LAT': ('LD', 'LE', 'LAT'),
    'MEI': ('VOL', 'MC', 'MAT', 'MD', 'ME', 'MEI'),
    'ATA': ('PD', 'PE', 'SA', 'CA', 'ATA'),
}

SETOR_PLURAL = {
    'GOL': 'Goleiros',
    'ZAG': 'Zagueiros',
    'LAT': 'Laterais',
    'MEI': 'Meias',
    'ATA': 'Atacantes',
}

ORDEM_SETOR = [codigo for codigo, _rotulo in POSICAO_CHOICES]
ORDEM_FUNCAO = {codigo: indice for indice, (codigo, _rotulo) in enumerate(FUNCAO_CHOICES)}


def chave_nome(nome: str) -> str:
    return slugify(nome or '')


def setor_da_funcao(funcao: str, fallback: str = 'MEI') -> str:
    return FUNCAO_PARA_SETOR.get((funcao or '').upper(), fallback)


def classe_badge(funcao_ou_posicao: str) -> str:
    setor = setor_da_funcao(funcao_ou_posicao, funcao_ou_posicao or 'mei')
    return (setor or 'mei').lower()


def codigo_funcao(atleta) -> str:
    return (getattr(atleta, 'funcao', None) or getattr(atleta, 'posicao', '') or 'MEI').upper()


def ordenar_por_posicao(atletas):
    def chave(atleta):
        setor = atleta.posicao if atleta.posicao in ORDEM_SETOR else 'MEI'
        return (
            ORDEM_SETOR.index(setor),
            ORDEM_FUNCAO.get(codigo_funcao(atleta), 99),
            (atleta.nome or '').lower(),
        )

    return sorted(atletas, key=chave)


def agrupar_por_funcao(atletas) -> list[dict]:
    grupos: list[dict] = []
    atual = None
    for atleta in atletas:
        codigo = codigo_funcao(atleta)
        if atual is None or atual['codigo'] != codigo:
            atual = {
                'codigo': codigo,
                'rotulo': FUNCAO_LABEL.get(codigo, codigo),
                'classe': classe_badge(codigo),
                'atletas': [],
            }
            grupos.append(atual)
        atual['atletas'].append(atleta)
    return grupos


def agrupar_por_setor(atletas) -> list[dict]:
    buckets: dict[str, list] = {codigo: [] for codigo in ORDEM_SETOR}
    for atleta in atletas:
        buckets.setdefault(atleta.posicao or 'MEI', []).append(atleta)

    grupos = []
    for codigo in ORDEM_SETOR:
        lista = ordenar_por_posicao(buckets.get(codigo) or [])
        if not lista:
            continue
        grupos.append({
            'sigla': codigo,
            'rotulo': SETOR_PLURAL[codigo],
            'rotulo_um': POSICAO_LABEL[codigo],
            'classe': codigo.lower(),
            'atletas': lista,
            'jogadores': lista,
            'funcoes': agrupar_por_funcao(lista),
            'total': len(lista),
        })
    return grupos


def agrupar_por_clube(atletas) -> list[dict]:
    ordenados = sorted(atletas, key=lambda a: ((a.clube.nome or '').lower(), a.pk))
    grupos: list[dict] = []
    atual = None
    for atleta in ordenados:
        if atual is None or atual['clube'].pk != atleta.clube_id:
            atual = {'clube': atleta.clube, 'atletas': []}
            grupos.append(atual)
        atual['atletas'].append(atleta)
    for grupo in grupos:
        grupo['setores'] = agrupar_por_setor(grupo['atletas'])
        grupo['total'] = len(grupo['atletas'])
    return grupos


def resolver_funcao(nome: str, sigla: str, posicao: str) -> str:
    """Função pesquisada do atleta; senão o setor público do Cartola."""
    from futebol.data.funcoes_conhecidas import FUNCOES_CONHECIDAS

    achado = FUNCOES_CONHECIDAS.get((chave_nome(nome), (sigla or '').upper()))
    if achado:
        return achado
    return (posicao or 'MEI').upper()


def aplicar_funcoes_catalogo(qs=None) -> int:
    """Preenche `funcao` nos atletas do catálogo. Retorna quantos mudaram."""
    from futebol.models import AtletaCatalogo

    atualizados = 0
    consulta = qs if qs is not None else AtletaCatalogo.objects.select_related('clube')
    for atleta in consulta:
        nova = resolver_funcao(atleta.nome, atleta.clube.sigla, atleta.posicao)
        if atleta.funcao != nova:
            atleta.funcao = nova
            atleta.save(update_fields=['funcao'])
            atualizados += 1
    return atualizados
