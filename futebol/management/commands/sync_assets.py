from django.core.management.base import BaseCommand

from futebol.assetsmgr.pipeline import sincronizar


class Command(BaseCommand):
    help = 'Sincroniza clubes, jogadores e imagens (Cartola / providers configurados).'

    def add_arguments(self, parser):
        parser.add_argument('--teams', action='store_true')
        parser.add_argument('--players', action='store_true')
        parser.add_argument('--assets', action='store_true')
        parser.add_argument('--validate', action='store_true')
        parser.add_argument('--missing', action='store_true')
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--force', action='store_true')

    def handle(self, *args, **options):
        seletivos = any(options[k] for k in ('teams', 'players', 'assets', 'validate', 'missing'))
        relatorio = sincronizar(
            teams=options['teams'] or not seletivos,
            players=options['players'] or not seletivos,
            assets=options['assets'] or options['missing'] or not seletivos,
            validate=options['validate'] or not seletivos,
            missing_only=options['missing'],
            dry_run=options['dry_run'],
            force=options['force'],
            stdout=self.stdout,
        )
        if relatorio.get('downloads', {}).get('failed'):
            self.stderr.write(self.style.ERROR('Sync terminou com erros de download.'))
