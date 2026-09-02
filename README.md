<div align="center">

# ⚽ Escalação Brasileirão

**Monte o seu time com jogadores de qualquer clube da Série A**

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.2-092E20?style=for-the-badge&logo=django&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)

[🎬 Demonstração](#-demonstração) ·
[🚀 Instalação](#-instalação-e-execução) ·
[🌐 Rotas](#-rotas)

</div>

---

## 📋 Sobre o projeto

Aplicação Django em que o usuário monta a própria escalação em um campo de futebol
vertical, no padrão visual dos aplicativos de fantasy game. O time não pertence a um
clube específico: cada jogador é cadastrado com o clube da Série A a que pertence, então
é possível ter um atacante do Flamengo ao lado de um meia do Palmeiras.

Projeto desenvolvido para a disciplina **Programação Backend (Python/Django)**.

---

## ✨ Funcionalidades

| Recurso | Descrição |
|---------|-----------|
| **Times** | Crie quantos times quiser, cada um com nome, cartoleiro e formação |
| **7 formações** | `3-4-3`, `3-5-2`, `4-3-3`, `4-4-2`, `4-5-1`, `5-3-2` e `5-4-1` |
| **20 clubes** | Todos os clubes da Série A, com escudo, sigla e cores próprias |
| **Catálogo de jogadores** | Busca no elenco da Série A ao escalar; lista completa em `/atletas/` |
| **API Futebol** | Com chave, sincroniza a artilharia oficial do Brasileirão |
| **Campo interativo** | Vagas livres são clicáveis e já abrem o formulário na posição certa |
| **Estatísticas** | Gols, assistências e posse de bola por atleta, com totais do time |
| **Notícias** | Publique notícias vinculadas a cada jogador |
| **CRUD completo** | Criar, editar e excluir pelo site, sem precisar do painel admin |

### Validação por formação

Cada formação define quantas vagas existem por posição. Ao tentar escalar um jogador
em uma posição sem vaga, o formulário recusa o cadastro e explica o motivo — por
exemplo, um quarto zagueiro em um `4-3-3`, ou um lateral em um `3-5-2`, que não usa
laterais.

---

## 🎬 Demonstração

Tutorial visual da aplicação: lista de times, campo interativo em 4-3-3 e o formulário
de jogador. Sem narração — só o app em uso.

<video src="docs/assets/demo-escalacao.mp4" poster="docs/assets/demo-campo.png" width="100%" controls playsinline>
</video>

[Assistir o tutorial (MP4)](docs/assets/demo-escalacao.mp4)

### Lista de times

Tela inicial com os times criados, formação, escudos empilhados e progresso da escalação.

![Lista de times](docs/assets/demo-lista-times.png)

### Campo interativo

Escalação no gramado, com jogadores de clubes diferentes da Série A, estatísticas e elenco ao lado.

![Campo da escalação](docs/assets/demo-campo.png)

### Cadastro e edição de jogador

Formulário de CRUD pelo site: clube, posição, gols, assistências e capitão — sem usar o admin.

![Formulário de jogador](docs/assets/demo-formulario-jogador.png)

---

## 🚀 Instalação e execução

```bash
# 1. Clone o repositório
git clone https://github.com/rafaeljs08/escalacao-brasileirao.git
cd escalacao-brasileirao

# 2. Crie e ative o ambiente virtual
python -m venv venv
# Windows
venv\Scripts\Activate.ps1
# Linux / macOS
source venv/bin/activate

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Aplique as migrações
python manage.py migrate

# 5. Cadastre os 20 clubes, o catálogo de jogadores, os escudos e um time de exemplo
python manage.py seed_brasileirao

# 6. (Opcional) Sincronize a artilharia oficial da API Futebol
#    Cadastre a chave em https://dash.api-futebol.com.br/cadastrar
cp .env.example .env   # edite API_FUTEBOL_KEY
python manage.py sync_api_futebol

# 7. (Opcional) Crie um superusuário para acessar o admin
python manage.py createsuperuser

# 8. Inicie o servidor
python manage.py runserver
```

Acesse **http://127.0.0.1:8000/**

---

## 🌐 Rotas

| URL | Método | Descrição |
|-----|--------|-----------|
| `/` | `GET` | Lista os times criados |
| `/time/novo/` | `GET` / `POST` | Cria um time e escolhe a formação |
| `/time/<id>/` | `GET` | Campo com a escalação, estatísticas e notícias |
| `/time/<id>/editar/` | `GET` / `POST` | Edita nome, cartoleiro e formação |
| `/time/<id>/excluir/` | `GET` / `POST` | Exclui o time |
| `/time/<id>/jogador/novo/` | `GET` / `POST` | Escala um jogador |
| `/time/<id>/jogador/<id>/editar/` | `GET` / `POST` | Edita um jogador |
| `/time/<id>/jogador/<id>/excluir/` | `GET` / `POST` | Remove um jogador |
| `/time/<id>/jogador/<id>/noticia/nova/` | `GET` / `POST` | Publica uma notícia |
| `/atletas/` | `GET` | Catálogo de jogadores da Série A, com filtro por clube e posição |
| `/atletas.json` | `GET` | JSON usado pela busca no formulário de escalação |
| `/admin/` | `GET` / `POST` | Painel administrativo |

---

## 🔌 API Futebol

A lista oficial de atletas vem de [API Futebol](https://www.api-futebol.com.br/documentacao)
(`https://api.api-futebol.com.br/v1`). Toda chamada exige o header
`Authorization: Bearer SUA_API_KEY`. Sem a chave o app **não quebra**: o comando
`seed_brasileirao` já carrega um catálogo local dos 20 clubes da Série A.

A API **não publica elenco completo** de cada time no plano comum. O que dá para
puxar de verdade:

| Endpoint | O que entra no catálogo |
|----------|-------------------------|
| `GET /campeonatos/10/artilharia` | Goleadores da Série A (nome, clube, posição, gols) |
| `GET /partidas/{id}` | Titulares e reservas da rodada (`--com-escalacoes`) |

```bash
# Só o catálogo local (não precisa de chave)
python manage.py sync_api_futebol

# Artilharia oficial (gasta 1 requisição)
API_FUTEBOL_KEY=live_xxx python manage.py sync_api_futebol

# Artilharia + escalações da última rodada (várias requisições)
API_FUTEBOL_KEY=live_xxx python manage.py sync_api_futebol --com-escalacoes
```

A chave fica em variável de ambiente ou no arquivo `.env` (veja `.env.example`).
Nunca coloque a chave no frontend: as chamadas saem só do `manage.py`.

---

## 🗄 Modelo de dados

### `Clube`
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `nome` | CharField(60) | Nome do clube (único) |
| `sigla` | CharField(3) | Sigla exibida no escudo |
| `cidade` / `estado` | CharField | Localização |
| `cor_primaria` / `cor_secundaria` | CharField(7) | Cores em hexadecimal |
| `escudo` | CharField(200) | Caminho do SVG gerado |

### `Escalacao`
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `nome` | CharField(60) | Nome do time |
| `torcedor` | CharField(60) | Nome do cartoleiro (opcional) |
| `formacao` | CharField(10) | Uma das 7 formações disponíveis |

### `Jogador`
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `escalacao` | ForeignKey | Time a que pertence |
| `clube` | ForeignKey | Clube da Série A |
| `nome` | CharField(60) | Nome do jogador |
| `posicao` | CharField(3) | `GOL`, `ZAG`, `LAT`, `MEI` ou `ATA` |
| `numero` | PositiveSmallInteger | Camisa, de 1 a 99 |
| `gols` / `assistencias` | PositiveInteger | Estatísticas da temporada |
| `posse_bola` | Decimal | Percentual de 0 a 100 |
| `foto` | URLField | Endereço de uma imagem (opcional) |
| `capitao` | Boolean | Marca o capitão do time |

### `Noticia`
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `jogador` | ForeignKey | Jogador citado |
| `titulo` | CharField(160) | Manchete |
| `resumo` | TextField(400) | Texto da notícia |
| `data_publicacao` | DateField | Preenchida automaticamente |

### `AtletaCatalogo`
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `api_id` | PositiveInteger | ID do atleta na API Futebol (opcional) |
| `nome` | CharField(80) | Nome popular |
| `clube` | ForeignKey | Clube da Série A |
| `posicao` | CharField(3) | `GOL`, `ZAG`, `LAT`, `MEI` ou `ATA` |
| `numero` | PositiveSmallInteger | Camisa, quando a API informa |
| `gols` | PositiveInteger | Gols na temporada (artilharia) |
| `fonte` | CharField | `local`, `artilharia` ou `escalacao` |

---

## 🎨 Interface

- **Campo vertical** desenhado em CSS e SVG, com círculo central, grandes e pequenas
  áreas, marcas de pênalti, arcos e escanteios
- **Linhas táticas** ancoradas ao gramado: o ataque fica abaixo da grande área
  adversária e o goleiro dentro da própria área
- **Escala por container query**, então os cards dos jogadores acompanham a largura do
  campo em qualquer tela
- **Tipografia** Sora nos títulos e Inter no texto
- **Layout responsivo**: duas colunas no desktop, empilhado no celular

Os escudos dos 20 clubes são gerados como SVG a partir das cores e da sigla de cada
time pelo comando `seed_brasileirao`, sem depender de arquivos externos.

---

## 📁 Estrutura

```
escalacao-brasileirao/
├── manage.py
├── requirements.txt
├── docs/assets/
│   ├── demo-escalacao.mp4         # Tutorial visual do app
│   ├── demo-lista-times.png
│   ├── demo-campo.png
│   └── demo-formulario-jogador.png
├── core/                          # Configuração do projeto
│   ├── settings.py
│   └── urls.py
└── futebol/                       # App da escalação
    ├── models.py                  # Clube, Escalacao, Jogador, Noticia, AtletaCatalogo
    ├── catalogo.py                # Importação local e da API Futebol
    ├── forms.py                   # Validação de vagas por formação
    ├── views.py                   # CRUD, campo e catálogo
    ├── urls.py
    ├── admin.py
    ├── data/catalogo_local.py     # Elenco de fallback (sem chave)
    ├── services/api_futebol.py    # Cliente HTTPS da API Futebol
    ├── management/commands/
    │   ├── seed_brasileirao.py    # Clubes, escudos, catálogo e time de exemplo
    │   └── sync_api_futebol.py    # Artilharia / escalações oficiais
    ├── static/futebol/
    │   ├── css/app.css            # Design system
    │   ├── css/campo.css          # Campo de futebol
    │   ├── js/catalogo.js         # Busca de jogadores no formulário
    │   └── img/clubes/            # Escudos SVG
    └── templates/futebol/
```

---

## 🛠 Stack

| Tecnologia | Uso |
|------------|-----|
| **Python 3.11+** | Linguagem |
| **Django 5.2** | Framework web |
| **requests** | Cliente HTTP da API Futebol |
| **SQLite** | Banco de dados |
| **HTML + CSS** | Interface, sem dependência de framework front-end |

---

## 👨‍💻 Autor

**Rafael Junqueira**

Trabalho da disciplina **Programação Backend (Python/Django)**

<div align="center">

*Desenvolvido com Django · 2026*

</div>
