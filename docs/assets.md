# Origem e limites de uso dos assets

Este módulo **não gera retratos**. Ele baixa, valida e organiza imagens
já publicadas por fontes configuráveis.

## Providers (ordem padrão)

1. **Cartola FC** (`CARTOLA_BASE_URL`, público, sem chave)
   - Clubes e atletas: `GET /atletas/mercado`
   - Escudos: URLs `escudos.60x60` devolvidas pela API (PNG no CDN da Globo)
   - Fotos: campo `foto`. Na temporada 2026 a API tem devolvido **silhuetas**
     (`…/silhuetas/{SIGLA}/FORMATO.png`), não retratos. O sistema marca isso
     como `FALLBACK` e tenta o próximo provider antes de gravar a silhueta.
2. **API-Football** (`API_FOOTBALL_BASE_URL` + `API_FOOTBALL_KEY`)
   - Desligado se a chave estiver vazia. Não inventamos IDs nem URLs.
3. **Sportmonks** (`SPORTMONKS_BASE_URL` + `SPORTMONKS_TOKEN`)
   - Idem: só roda com token.
4. **Fallback local**
   - `assets/placeholders/player.png` e `team.png`
   - Escudos SVG gerados pelo `seed_brasileirao` quando não há logo remoto

## O que fica gravado

Cada arquivo em `assets/teams/{id}.png` e `assets/players/{id}.png` tem um
registro em `Asset` (URL, hash SHA-256, provider, status, `fallback_used`).
O catálogo JSON está em `data/teams.json`, `data/players.json`, `data/assets.json`
e o relatório em `data/sync_report.json`.

O ID do arquivo é o ID do provider (Cartola `atleta_id` / `clube_id`), nunca o nome.

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

Painel: `/painel/assets/`
API: `/api/teams`, `/api/players`, `/api/assets/status`
