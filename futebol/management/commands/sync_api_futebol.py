from django.core.management.base import BaseCommand, CommandError

from futebol.catalogo import carregar_catalogo_local, importar_artilharia, importar_escalacao
from futebol.models import AtletaCatalogo, Clube
from futebol.services import api_futebol


class Command(BaseCommand):
    help = (
        'Sincroniza o catálogo de jogadores do Brasileirão Série A. '
        'Sem chave, usa o elenco local. Com API_FUTEBOL_KEY, busca a artilharia '
        'em https://api.api-futebol.com.br/v1 e, opcionalmente, as escalações.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--com-escalacoes',
            action='store_true',
            help='Também lê titulares/reservas das últimas rodadas (gasta mais requisições).',
        )
        parser.add_argument(
            '--rodadas',
            type=int,
            default=1,
            help='Quantas rodadas recentes consultar com --com-escalacoes (padrão: 1).',
        )
        parser.add_argument(
            '--somente-api',
            action='store_true',
            help='Não recarrega o catálogo local; só chama a API.',
        )

    def handle(self, *args, **options):
        if not Clube.objects.exists():
            raise CommandError('Cadastre os clubes primeiro: python manage.py seed_brasileirao')

        if not options['somente_api']:
            criados = carregar_catalogo_local()
            self.stdout.write(f'Catálogo local: {criados} atletas novos.')

        if not api_futebol.tem_chave():
            self.stdout.write(self.style.WARNING(
                'API_FUTEBOL_KEY não definida. O app usa o catálogo local. '
                'Chave gratuita em https://dash.api-futebol.com.br/cadastrar'
            ))
            self.stdout.write(self.style.SUCCESS(
                f'{AtletaCatalogo.objects.count()} atletas no catálogo.'
            ))
            return

        try:
            artilharia = api_futebol.fetch_artilharia()
        except api_futebol.ApiFutebolError as exc:
            raise CommandError(str(exc)) from exc

        novos, atualizados = importar_artilharia(artilharia)
        self.stdout.write(
            f'Artilharia da API Futebol: {novos} novos, {atualizados} atualizados '
            f'({len(artilharia)} goleadores na resposta).'
        )

        if options['com_escalacoes']:
            try:
                ids = api_futebol.ids_partidas_recentes(limite_rodadas=max(1, options['rodadas']))
            except api_futebol.ApiFutebolError as exc:
                raise CommandError(str(exc)) from exc

            novos_esc = atualizados_esc = 0
            for partida_id in ids:
                try:
                    partida = api_futebol.fetch_partida(partida_id)
                except api_futebol.ApiFutebolError as exc:
                    self.stderr.write(f'Partida {partida_id}: {exc}')
                    continue
                n, a = importar_escalacao(api_futebol.atletas_da_escalacao(partida))
                novos_esc += n
                atualizados_esc += a
            self.stdout.write(
                f'Escalações ({len(ids)} partidas): {novos_esc} novos, {atualizados_esc} atualizados.'
            )

        self.stdout.write(self.style.SUCCESS(
            f'{AtletaCatalogo.objects.count()} atletas no catálogo.'
        ))
