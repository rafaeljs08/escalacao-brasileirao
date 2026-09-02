from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase, override_settings

from futebol.catalogo import importar_artilharia, importar_escalacao
from futebol.models import AtletaCatalogo, Clube, Escalacao, Jogador
from futebol.posicoes import agrupar_por_setor, resolver_funcao
from futebol.services.api_futebol import (
    atletas_da_escalacao,
    mapear_posicao,
    mapear_sigla_clube,
    posicao_sigla,
)


class MapeamentoApiTests(TestCase):
    def test_posicao_objeto_e_lista_vazia(self):
        self.assertEqual(posicao_sigla({'nome': 'Atacante', 'sigla': 'ATA'}), 'ATA')
        self.assertEqual(posicao_sigla([]), '')
        self.assertEqual(mapear_posicao('ZAD'), 'ZAG')
        self.assertEqual(mapear_posicao('LAE'), 'LAT')
        self.assertEqual(mapear_posicao('VOL'), 'MEI')
        self.assertEqual(mapear_posicao(''), 'MEI')

    def test_funcao_pesquisada(self):
        self.assertEqual(resolver_funcao('Arrascaeta', 'FLA', 'MEI'), 'MAT')
        self.assertEqual(resolver_funcao('Pedro', 'FLA', 'ATA'), 'CA')
        self.assertEqual(resolver_funcao('Wesley', 'FLA', 'LAT'), 'LD')
        self.assertEqual(resolver_funcao('Jogador Desconhecido', 'FLA', 'ZAG'), 'ZAG')

    def test_agrupa_na_ordem_do_campo(self):
        class Fake:
            def __init__(self, nome, posicao, funcao=''):
                self.nome = nome
                self.posicao = posicao
                self.funcao = funcao

        grupos = agrupar_por_setor([
            Fake('Pedro', 'ATA', 'CA'),
            Fake('Rossi', 'GOL', 'GOL'),
            Fake('Veiga', 'MEI', 'MAT'),
        ])
        self.assertEqual([g['sigla'] for g in grupos], ['GOL', 'MEI', 'ATA'])
        self.assertEqual(grupos[0]['rotulo'], 'Goleiros')
        self.assertEqual(grupos[-1]['funcoes'][0]['rotulo'], 'Centroavante')

    def test_siglas_dos_clubes_do_seed(self):
        self.assertEqual(mapear_sigla_clube('RBB'), 'BGT')
        self.assertEqual(mapear_sigla_clube('SPO'), 'SPT')
        self.assertEqual(mapear_sigla_clube('FLA'), 'FLA')
        self.assertIsNone(mapear_sigla_clube('CAP'))


class CatalogoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_brasileirao', stdout=StringIO())

    def test_seed_carrega_catalogo_dos_20_clubes(self):
        self.assertEqual(Clube.objects.count(), 20)
        self.assertGreaterEqual(AtletaCatalogo.objects.count(), 60)
        self.assertTrue(AtletaCatalogo.objects.filter(nome='Pedro', clube__sigla='FLA').exists())
        self.assertTrue(AtletaCatalogo.objects.filter(nome='Léo Jardim', clube__sigla='VAS').exists())

    def test_pagina_de_atletas(self):
        resposta = self.client.get('/atletas/')
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'Pedro')
        self.assertContains(resposta, 'Flamengo')
        self.assertContains(resposta, 'Goleiros')
        self.assertContains(resposta, 'Atacantes')
        html = resposta.content.decode()
        self.assertLess(html.find('Goleiros'), html.find('Zagueiros'))
        self.assertLess(html.find('Zagueiros'), html.find('Atacantes'))
        self.assertContains(resposta, 'filtro-chip')
        self.assertContains(resposta, 'Por posição')
        goleiros = AtletaCatalogo.objects.filter(posicao='GOL').count()
        self.assertGreater(goleiros, 1)
        self.assertContains(resposta, f'Goleiros <span>{goleiros}</span>', html=False)

    def test_catalogo_agrupa_por_clube_ainda_separa_posicao(self):
        resposta = self.client.get('/atletas/', {'agrupar': 'clube'})
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'Flamengo')
        self.assertContains(resposta, 'Goleiros')
        self.assertContains(resposta, 'Atacantes')

    def test_chip_de_setor_filtra_e_mostra_funcoes(self):
        resposta = self.client.get('/atletas/', {'posicao': 'ATA'})
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'Pedro')
        self.assertContains(resposta, 'Centroavante')
        self.assertContains(resposta, 'setor-ata')
        self.assertNotContains(resposta, 'Léo Jardim')

    def test_elenco_do_time_vem_separado_por_posicao(self):
        time = Escalacao.objects.get(nome='Seleção do Brasileirão')
        resposta = self.client.get(f'/time/{time.pk}/')
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'elenco-setor')
        html = resposta.content.decode()
        self.assertLess(html.find('Goleiros'), html.find('Zagueiros'))
        self.assertLess(html.find('Zagueiros'), html.find('Atacantes'))

    def test_filtro_vazio_mostra_estado_sem_resultado(self):
        resposta = self.client.get('/atletas/', {'q': 'JogadorInexistenteXYZ'})
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'Nenhum jogador com esse filtro')

    def test_json_filtra_por_nome_e_posicao(self):
        resposta = self.client.get('/atletas.json', {'q': 'Arrascaeta', 'posicao': 'MEI'})
        self.assertEqual(resposta.status_code, 200)
        dados = resposta.json()
        self.assertGreaterEqual(dados['total'], 1)
        self.assertEqual(dados['atletas'][0]['nome'], 'Arrascaeta')
        self.assertEqual(dados['atletas'][0]['posicao'], 'MEI')
        self.assertEqual(dados['atletas'][0]['funcao'], 'MAT')

    def test_filtro_por_funcao_tatica(self):
        resposta = self.client.get('/atletas/', {'funcao': 'CA'})
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'Pedro')
        self.assertContains(resposta, 'Centroavante')

    def test_formulario_de_elenco_tem_filtro_de_funcao(self):
        time = Escalacao.objects.create(nome='Teste funções', formacao='4-3-3')
        resposta = self.client.get(f'/time/{time.pk}/jogador/novo/?posicao=ATA')
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'Função tática')
        self.assertContains(resposta, 'catalogo-funcao')
        self.assertContains(resposta, 'Centroavante')

    def test_escalar_pelo_catalogo(self):
        time = Escalacao.objects.create(nome='Teste API', formacao='4-3-3')
        atleta = AtletaCatalogo.objects.get(nome='Pedro', clube__sigla='FLA')
        resposta = self.client.post(f'/time/{time.pk}/jogador/novo/', {
            'catalog_id': atleta.pk,
            'assistencias': 0,
            'posse_bola': 0,
        })
        self.assertEqual(resposta.status_code, 302)
        jogador = Jogador.objects.get(escalacao=time)
        self.assertEqual(jogador.nome, 'Pedro')
        self.assertEqual(jogador.posicao, 'ATA')
        self.assertEqual(jogador.clube.sigla, 'FLA')
        self.assertEqual(jogador.gols, atleta.gols)

    def test_importar_artilharia_ignora_clube_fora_da_serie_a(self):
        palmeiras = Clube.objects.get(sigla='PAL')
        novos, _atualizados = importar_artilharia([
            {
                'atleta': {'atleta_id': 1, 'nome_popular': 'Viveros', 'posicao': []},
                'time': {'nome_popular': 'Athletico-PR', 'sigla': 'CAP'},
                'gols': 10,
            },
            {
                'atleta': {
                    'atleta_id': 2063,
                    'nome_popular': 'Gustavo Gómez',
                    'posicao': {'nome': 'Zagueiro', 'sigla': 'ZAG'},
                },
                'time': {'nome_popular': 'Palmeiras', 'sigla': 'PAL'},
                'gols': 6,
            },
        ])
        self.assertEqual(novos, 0)
        self.assertFalse(AtletaCatalogo.objects.filter(nome='Viveros').exists())
        gomez = AtletaCatalogo.objects.get(nome='Gustavo Gómez', clube=palmeiras)
        self.assertGreaterEqual(gomez.gols, 6)
        self.assertEqual(gomez.api_id, 2063)
        self.assertEqual(gomez.fonte, 'artilharia')

    def test_extrai_atletas_da_escalacao_da_partida(self):
        partida = {
            'time_mandante': {'nome_popular': 'Flamengo', 'sigla': 'FLA'},
            'time_visitante': {'nome_popular': 'Palmeiras', 'sigla': 'PAL'},
            'escalacoes': {
                'mandante': {
                    'titulares': [{
                        'atleta': {'atleta_id': 917, 'nome_popular': 'Pedro'},
                        'camisa': '9',
                        'posicao': {'nome': 'Atacante', 'sigla': 'ATA'},
                    }],
                    'reservas': [],
                },
                'visitante': {'titulares': [], 'reservas': []},
            },
        }
        itens = atletas_da_escalacao(partida)
        self.assertEqual(len(itens), 1)
        novos, _ = importar_escalacao(itens)
        self.assertEqual(novos, 0)
        pedro = AtletaCatalogo.objects.get(api_id=917)
        self.assertEqual(pedro.numero, 9)
        self.assertEqual(pedro.posicao, 'ATA')


class SyncCommandTests(TestCase):
    def test_sync_sem_chave_usa_catalogo_local(self):
        call_command('seed_brasileirao', '--sem-demo', stdout=StringIO())
        saida = StringIO()
        call_command('sync_api_futebol', stdout=saida)
        texto = saida.getvalue()
        self.assertIn('API_FUTEBOL_KEY', texto)
        self.assertGreaterEqual(AtletaCatalogo.objects.count(), 60)

    @override_settings(API_FUTEBOL_KEY='live_teste')
    def test_sync_com_chave_consome_artilharia(self):
        call_command('seed_brasileirao', '--sem-demo', stdout=StringIO())
        payload = [
            {
                'atleta': {
                    'atleta_id': 4242,
                    'nome_popular': 'Artilheiro Teste',
                    'posicao': {'nome': 'Atacante', 'sigla': 'ATA'},
                },
                'time': {'nome_popular': 'Flamengo', 'sigla': 'FLA'},
                'gols': 18,
            }
        ]
        with patch('futebol.services.api_futebol.fetch_artilharia', return_value=payload):
            call_command('sync_api_futebol', stdout=StringIO())
        atleta = AtletaCatalogo.objects.get(api_id=4242)
        self.assertEqual(atleta.nome, 'Artilheiro Teste')
        self.assertEqual(atleta.gols, 18)
        self.assertEqual(atleta.clube.sigla, 'FLA')
