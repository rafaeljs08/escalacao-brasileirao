# Origem e limites de uso dos assets

Este módulo **não gera retratos**. Ele baixa, valida e organiza imagens
já publicadas por fontes configuráveis.

## Providers (ordem padrão)

1. **Cartola FC** (`CARTOLA_BASE_URL`, público, sem chave)
   - Clubes e atletas: `GET /atletas/mercado`
   - Escudos: maior PNG publicado em `escudos` (`60x60`, depois `45x45` / `30x30`).
     A API de 2026 **não** publica SVG.
   - Nomes: em 2026 `nome`/`abreviacao` vêm como sigla (`FLA`); o sistema usa o
     `slug` (`flamengo`) para gravar o nome real.
   - Fotos: campo `foto`. Na temporada 2026 a API tem devolvido **silhuetas**
     (`…/silhuetas/{SIGLA}/FORMATO.png`), não retratos. O sistema marca isso
     como `FALLBACK` e tenta o próximo provider antes de gravar a silhueta.
2. **API-Football** (`API_FOOTBALL_BASE_URL` + `API_FOOTBALL_KEY`)
   - Desligado se a chave estiver vazia. Não inventamos IDs nem URLs.
   - Liga 71 (Série A), temporada `ASSET_SEASON`.
3. **Sportmonks** (`SPORTMONKS_BASE_URL` + `SPORTMONKS_TOKEN`)
   - Idem: só roda com token. Sem token o provider não busca jogadores.
4. **Fallback local**
   - `assets/placeholders/player.png` e `team.png`
   - Escudos SVG gerados pelo `seed_brasileirao` quando não há logo remoto

## Temporada 2026 vs seed acadêmico

O seed da disciplina mantém Ceará, Fortaleza, Juventude e Sport.
O Cartola 2026 lista **Athletico-PR, Coritiba, Chapecoense e Remo** no lugar
desses quatro. O Asset Manager **cria** esses clubes na sincronização para
não descartar atletas da temporada atual. Os quatro do seed continuam no
banco (úteis no CRUD da disciplina) e ficam sem elenco Cartola.

RB Bragantino chega como `RBB` e é mapeado para a sigla do app `BGT`.

## O que fica gravado

Cada arquivo em `assets/teams/{id}.png` (ou `.svg` se a fonte publicar SVG)
e `assets/players/{id}.png` tem um registro em `Asset` (URL, hash SHA-256,
provider, status, `fallback_used`). O ID do arquivo é o ID do provider,
nunca o nome.

Catálogo JSON: `data/teams.json`, `data/players.json`, `data/assets.json`.
Relatório: `data/sync_report.json`.
Logs: `logs/download.log`, `logs/missing.log`.

Sincronização incremental: se o mesmo ID, a mesma URL e o mesmo hash ainda
valem, o arquivo **não** é baixado de novo. Se a URL mudar, o download vai
para um `.tmp`, valida, e só então substitui o arquivo antigo.

## Licença e republicação

- Dados e imagens do Cartola / Globo seguem os termos do Cartola FC e da Globo.
  Disponibilidade pública **não** implica permissão de redistribuição comercial.
- API-Football e Sportmonks têm contratos próprios; use só com a chave da sua conta.
- Antes de publicar o site fora do contexto acadêmico, revise os termos de cada fonte.
- O campo `provider` + `url` existem para auditoria.

## Comandos

```bash
python sync.py --dry-run
python sync.py --teams
python sync.py --players
python sync.py --assets
python sync.py --validate
python sync.py --missing
python sync.py --force
python manage.py sync_assets --dry-run
```

Painel: `/painel/assets/` (filtros, paginação, dry-run).
API: `/api/teams`, `/api/teams/{id}`, `/api/teams/{id}/logo`,
`/api/players`, `/api/players/{id}`, `/api/players/{id}/image`,
`/api/assets/status`, `/api/assets/missing`, `/api/sync/status`.
