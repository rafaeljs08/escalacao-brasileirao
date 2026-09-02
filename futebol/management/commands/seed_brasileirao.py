from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from futebol.catalogo import carregar_catalogo_local
from futebol.models import AtletaCatalogo, Clube, Escalacao, Jogador

# nome, sigla, cidade, UF, cor primária, cor secundária
CLUBES = [
    ('Atlético-MG', 'CAM', 'Belo Horizonte', 'MG', '#111827', '#f3f4f6'),
    ('Bahia', 'BAH', 'Salvador', 'BA', '#1e40af', '#dc2626'),
    ('Botafogo', 'BOT', 'Rio de Janeiro', 'RJ', '#111827', '#f9fafb'),
    ('Bragantino', 'BGT', 'Bragança Paulista', 'SP', '#b91c1c', '#f8fafc'),
    ('Ceará', 'CEA', 'Fortaleza', 'CE', '#111827', '#f3f4f6'),
    ('Corinthians', 'COR', 'São Paulo', 'SP', '#0f172a', '#e2e8f0'),
    ('Cruzeiro', 'CRU', 'Belo Horizonte', 'MG', '#1d4ed8', '#f8fafc'),
    ('Flamengo', 'FLA', 'Rio de Janeiro', 'RJ', '#b91c1c', '#111827'),
    ('Fluminense', 'FLU', 'Rio de Janeiro', 'RJ', '#14532d', '#7f1d34'),
    ('Fortaleza', 'FOR', 'Fortaleza', 'CE', '#1e3a8a', '#dc2626'),
    ('Grêmio', 'GRE', 'Porto Alegre', 'RS', '#1e40af', '#111827'),
    ('Internacional', 'INT', 'Porto Alegre', 'RS', '#b91c1c', '#f8fafc'),
    ('Juventude', 'JUV', 'Caxias do Sul', 'RS', '#14532d', '#f8fafc'),
    ('Mirassol', 'MIR', 'Mirassol', 'SP', '#ca8a04', '#15803d'),
    ('Palmeiras', 'PAL', 'São Paulo', 'SP', '#166534', '#f8fafc'),
    ('Santos', 'SAN', 'Santos', 'SP', '#f8fafc', '#111827'),
    ('São Paulo', 'SAO', 'São Paulo', 'SP', '#b91c1c', '#111827'),
    ('Sport', 'SPT', 'Recife', 'PE', '#b91c1c', '#111827'),
    ('Vasco da Gama', 'VAS', 'Rio de Janeiro', 'RJ', '#0b0b0b', '#f8fafc'),
    ('Vitória', 'VIT', 'Salvador', 'BA', '#b91c1c', '#111827'),
]

ELENCO_DEMO = [
    ('Léo Jardim', 'Vasco da Gama', 'GOL', 1, 0, 1, 14.0, False),
    ('Wesley', 'Flamengo', 'LAT', 43, 3, 6, 46.0, False),
    ('Gustavo Gómez', 'Palmeiras', 'ZAG', 15, 5, 1, 41.0, True),
    ('Léo Ortiz', 'Flamengo', 'ZAG', 3, 4, 2, 43.0, False),
    ('Alex Sant\u2019Ana', 'Bahia', 'LAT', 6, 2, 5, 44.0, False),
    ('André', 'Fluminense', 'MEI', 7, 3, 4, 58.0, False),
    ('Raphael Veiga', 'Palmeiras', 'MEI', 23, 9, 7, 55.0, False),
    ('Arrascaeta', 'Flamengo', 'MEI', 14, 12, 11, 57.0, False),
    ('Andrés Gómez', 'Vasco da Gama', 'ATA', 11, 5, 1, 48.0, False),
    ('Pedro', 'Flamengo', 'ATA', 9, 15, 4, 39.0, False),
    ('Yuri Alberto', 'Corinthians', 'ATA', 9, 13, 3, 38.0, False),
]

NOTICIAS_DEMO = {
    'Arrascaeta': [
        ('Maestro decide mais uma', 'Uruguaio participou de 23 gols na temporada e lidera o setor criativo.'),
        ('Recorde de assistências', 'Meia chega a 11 passes para gol e se isola na liderança do elenco.'),
    ],
    'Pedro': [
        ('Artilharia em dia', 'Centroavante balançou as redes 15 vezes e mantém média de um gol a cada dois jogos.'),
    ],
    'Gustavo Gómez': [
        ('Liderança na zaga', 'Capitão soma 5 gols de bola parada e comanda a defesa menos vazada.'),
    ],
}


def escudo_svg(sigla, primaria, secundaria):
    """Escudo vetorial gerado a partir das cores e da sigla do clube."""
    texto = '#0b1220' if primaria.lower() in {'#f8fafc', '#ffffff'} else '#ffffff'
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 72" width="64" height="72" role="img">
  <defs>
    <linearGradient id="brilho" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#ffffff" stop-opacity=".28"/>
      <stop offset="55%" stop-color="#ffffff" stop-opacity="0"/>
    </linearGradient>
    <clipPath id="escudo">
      <path d="M32 2 60 12v28c0 16-12 25-28 30C16 65 4 56 4 40V12Z"/>
    </clipPath>
  </defs>
  <g clip-path="url(#escudo)">
    <rect width="64" height="72" fill="{primaria}"/>
    <path d="M-8 44 32 4l12 12-40 40Z" fill="{secundaria}" opacity=".92"/>
    <rect width="64" height="72" fill="url(#brilho)"/>
  </g>
  <path d="M32 2 60 12v28c0 16-12 25-28 30C16 65 4 56 4 40V12Z"
        fill="none" stroke="#ffffff" stroke-opacity=".85" stroke-width="2.5"/>
  <text x="32" y="42" text-anchor="middle" fill="{texto}"
        font-family="Verdana,Geneva,sans-serif" font-size="17" font-weight="bold">{sigla}</text>
</svg>
'''


class Command(BaseCommand):
    help = 'Cria os clubes da Série A, gera os escudos e monta uma escalação de exemplo.'

    def add_arguments(self, parser):
        parser.add_argument('--sem-demo', action='store_true', help='Cria apenas os clubes.')

    def handle(self, *args, **options):
        destino = Path(settings.BASE_DIR) / 'futebol/static/futebol/img/clubes'
        destino.mkdir(parents=True, exist_ok=True)

        for nome, sigla, cidade, uf, primaria, secundaria in CLUBES:
            arquivo = f'{sigla.lower()}.svg'
            (destino / arquivo).write_text(escudo_svg(sigla, primaria, secundaria), encoding='utf-8')
            Clube.objects.update_or_create(
                nome=nome,
                defaults={
                    'sigla': sigla,
                    'cidade': cidade,
                    'estado': uf,
                    'cor_primaria': primaria,
                    'cor_secundaria': secundaria,
                    'escudo': f'futebol/img/clubes/{arquivo}',
                },
            )

        self.stdout.write(self.style.SUCCESS(f'{Clube.objects.count()} clubes da Série A disponíveis.'))

        atletas = carregar_catalogo_local()
        self.stdout.write(self.style.SUCCESS(
            f'Catálogo local: {atletas} atletas novos ({AtletaCatalogo.objects.count()} no total).'
        ))

        if options['sem_demo'] or Escalacao.objects.exists():
            return

        escalacao = Escalacao.objects.create(
            nome='Seleção do Brasileirão',
            torcedor='Time de exemplo',
            formacao='4-3-3',
        )
        for nome, clube, posicao, numero, gols, assist, posse, capitao in ELENCO_DEMO:
            jogador = Jogador.objects.create(
                escalacao=escalacao,
                clube=Clube.objects.get(nome=clube),
                nome=nome,
                posicao=posicao,
                numero=numero,
                gols=gols,
                assistencias=assist,
                posse_bola=posse,
                capitao=capitao,
            )
            for titulo, resumo in NOTICIAS_DEMO.get(nome, []):
                jogador.noticias.create(titulo=titulo, resumo=resumo)

        self.stdout.write(self.style.SUCCESS(
            f'Escalação de exemplo criada com {escalacao.jogadores.count()} jogadores.'
        ))
