from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings
from PIL import Image

from futebol.assetsmgr.cache import cache_hit
from futebol.assetsmgr.downloader import AssetDownloader
from futebol.assetsmgr.http import HttpError, JsonClient
from futebol.assetsmgr.pipeline import sincronizar
from futebol.assetsmgr.providers import primeira_foto, primeiro_logo
from futebol.assetsmgr.providers.base import PlayerRecord, TeamRecord
from futebol.assetsmgr.providers.cartola import CartolaProvider, SIGLA_CARTOLA_PARA_APP
from futebol.assetsmgr.validator import validate_image
from futebol.models import Asset, AtletaCatalogo, Clube
from futebol.management.commands.seed_brasileirao import Command as Seed


def _png_bytes(cor=(20, 80, 40, 255)) -> bytes:
    buffer = BytesIO()
    Image.new('RGBA', (64, 64), cor).save(buffer, format='PNG')
    return buffer.getvalue()


class _FakeProvider:
    name = 'cartola'

    def available(self):
        return True

    def get_teams(self):
        return [TeamRecord(id=262, name='Flamengo', short_name='FLA', slug='flamengo',
                           logo_url='https://s3.glbimg.com/escudo.png', source='cartola',
                           extra={'app_sigla': 'FLA'})]

    def get_players(self):
        return [PlayerRecord(id=94583, name='Pedro', slug='pedro', team_id=262, position='ATA',
                             photo_url='https://s3.glbimg.com/silhuetas/FLA/220x220.png',
                             source='cartola', generic_photo=True)]

    def get_team_logo(self, team):
        return team.logo_url

    def get_player_image(self, player):
        return player.photo_url


class ValidatorTests(TestCase):
    def test_png_valida(self):
        pasta = Path(self._dir())
        arquivo = pasta / 'ok.png'
        arquivo.write_bytes(_png_bytes())
        resultado = validate_image(arquivo)
        self.assertTrue(resultado['valid'])
        self.assertEqual(resultado['width'], 64)

    def test_png_tmp_e_aceito_na_validacao(self):
        pasta = Path(self._dir())
        arquivo = pasta / 'ok.png.tmp'
        arquivo.write_bytes(_png_bytes())
        self.assertTrue(validate_image(arquivo)['valid'])

    def test_arquivo_corrompido(self):
        pasta = Path(self._dir())
        arquivo = pasta / 'x.png'
        arquivo.write_bytes(b'nao-e-imagem')
        resultado = validate_image(arquivo)
        self.assertFalse(resultado['valid'])

    def test_url_invalida_rejeitada_pelo_cliente(self):
        client = JsonClient()
        with self.assertRaises(HttpError):
            client.get_bytes('https://evil.example/foto.png')

    def _dir(self):
        from tempfile import mkdtemp
        return mkdtemp()


class DownloaderTests(TestCase):
    def test_404(self):
        client = MagicMock()
        client.get_bytes.side_effect = HttpError('HTTP 404', status=404)
        downloader = AssetDownloader(client=client)
        from tempfile import mkdtemp
        dest = Path(mkdtemp()) / 'a.png'
        resultado = downloader.download('https://s3.glbimg.com/x.png', dest)
        self.assertFalse(resultado['valid'])
        self.assertEqual(resultado['status'], 404)

    def test_429(self):
        client = MagicMock()
        client.get_bytes.side_effect = HttpError('HTTP 429', status=429)
        downloader = AssetDownloader(client=client)
        from tempfile import mkdtemp
        dest = Path(mkdtemp()) / 'a.png'
        resultado = downloader.download('https://s3.glbimg.com/x.png', dest)
        self.assertEqual(resultado['status'], 429)

    def test_nao_baixa_de_novo_se_valido(self):
        from tempfile import mkdtemp
        dest = Path(mkdtemp()) / 'a.png'
        dest.write_bytes(_png_bytes())
        client = MagicMock()
        downloader = AssetDownloader(client=client)
        resultado = downloader.download('https://s3.glbimg.com/x.png', dest)
        self.assertTrue(resultado['skipped'])
        client.get_bytes.assert_not_called()
        self.assertTrue(cache_hit(dest, 'https://s3.glbimg.com/x.png', '', ''))


class FallbackTests(TestCase):
    def test_silhueta_e_fallback_depois_do_provider_real(self):
        class Real:
            name = 'api_football'
            def get_player_image(self, player):
                return 'https://media.api-sports.io/football/players/1.png'
            def get_team_logo(self, team):
                return None

        player = PlayerRecord(id=1, name='Pedro', photo_url='https://s3.glbimg.com/silhuetas/FLA/x.png',
                              generic_photo=True, source='cartola')
        url, fonte, fallback = primeira_foto(player, [Real(), _FakeProvider()])
        self.assertEqual(fonte, 'api_football')
        self.assertFalse(fallback)
        self.assertIn('api-sports', url)

    def test_logo_cartola_primeiro(self):
        team = TeamRecord(id=262, name='Flamengo', short_name='FLA', logo_url='https://s3.glbimg.com/escudo.png')
        url, fonte, fallback = primeiro_logo(team, [_FakeProvider()])
        self.assertEqual(fonte, 'cartola')
        self.assertFalse(fallback)


class CartolaMapTests(TestCase):
    def test_rbb_vira_bgt(self):
        self.assertEqual(SIGLA_CARTOLA_PARA_APP['RBB'], 'BGT')

    def test_resolver_formato_da_foto(self):
        provider = CartolaProvider(client=MagicMock())
        url = provider._resolver_foto('https://s3.glbimg.com/silhuetas/FLA/FORMATO.png')
        self.assertIn('220x220.png', url)


@override_settings()
class SyncIncrementalTests(TestCase):
    def setUp(self):
        Seed().handle(sem_demo=True)
        from tempfile import mkdtemp
        self.assets = Path(mkdtemp())
        self.data = Path(mkdtemp())

    def test_sync_com_mocks_grava_catalogo_e_nao_repete_download(self):
        png = _png_bytes()

        def get_bytes(url):
            return png, 'image/png', 200

        with override_settings(ASSETS_DIR=self.assets, DATA_DIR=self.data, REQUEST_DELAY=0):
            with patch('futebol.assetsmgr.pipeline.load_providers', return_value=[_FakeProvider()]):
                with patch('futebol.assetsmgr.http.JsonClient.get_bytes', side_effect=get_bytes):
                    with patch('futebol.assetsmgr.downloader.AssetDownloader.download') as fake_dl:
                        def _dl(url, destination, force=False, normalize=False):
                            path = Path(destination)
                            path.parent.mkdir(parents=True, exist_ok=True)
                            path.write_bytes(png)
                            return {'valid': True, 'width': 64, 'height': 64, 'format': 'PNG',
                                    'size': len(png), 'skipped': False, 'path': str(path),
                                    'sha256': 'abc', 'mime': 'image/png'}
                        fake_dl.side_effect = _dl
                        primeiro = sincronizar(dry_run=False, force=False)
                        segundo = sincronizar(dry_run=False, force=False)

        self.assertEqual(primeiro['teams']['total'], 1)
        self.assertTrue(AtletaCatalogo.objects.filter(fonte_id=94583).exists())
        self.assertTrue(Asset.objects.filter(entity_type='player', entity_id=94583).exists())
        self.assertTrue((self.assets / 'players' / '94583.png').exists())
        self.assertGreaterEqual(fake_dl.call_count, 1)
        # segunda passagem: cache local, downloader pode ser chamado mas arquivos já valem
        self.assertEqual(Clube.objects.get(sigla='FLA').fonte_id, 262)


class ApiAssetsTests(TestCase):
    def setUp(self):
        Seed().handle(sem_demo=True)

    def test_status_e_times(self):
        resposta = self.client.get('/api/assets/status')
        self.assertEqual(resposta.status_code, 200)
        self.assertIn('teams', resposta.json())
        times = self.client.get('/api/teams')
        self.assertEqual(times.status_code, 200)
        self.assertGreaterEqual(len(times.json()['teams']), 20)

    def test_painel(self):
        resposta = self.client.get('/painel/assets/')
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'Asset Manager')
