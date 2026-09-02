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


def chave_nome(nome: str) -> str:
    return slugify(nome or '')


def setor_da_funcao(funcao: str, fallback: str = 'MEI') -> str:
    return FUNCAO_PARA_SETOR.get((funcao or '').upper(), fallback)


def classe_badge(funcao_ou_posicao: str) -> str:
    setor = setor_da_funcao(funcao_ou_posicao, funcao_ou_posicao or 'mei')
    return (setor or 'mei').lower()


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
