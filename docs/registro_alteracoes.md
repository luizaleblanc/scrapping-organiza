# Registro de alterações — 22/11/2026

O que mudou no pipeline a partir do commit `2c90359`, arquivo por arquivo, e por quê.
Motivação geral: pedido do orientador para coletar também em **inglês e espanhol**, a volta
ao critério do artigo (**negativo ou neutro**) e a proteção dos avaliadores (**censura de nomes
de pessoas, marcas e lugares**).

## Decisões de protocolo

| Tema | Antes | Agora |
|---|---|---|
| Idiomas e países | Só Brasil (pt) | Brasil (pt), EUA (en), Espanha e México (es) |
| Strings de busca | S1–S6 em português | As mesmas S1–S6, traduzidas para inglês e espanhol |
| Fonte das reviews | Google Play e App Store | Igual (App Store mantida como fonte, decisão da pesquisadora) |
| Volume fora do Brasil | — | Google Play: só 1 a 3 estrelas, até 1.000 por nota por app. App Store: 500 mais recentes |
| Sentimento | Só negativas (compound ≤ −0,05) | **Negativas ou neutras** (compound < 0,05), como no artigo. Espanhol: `pysentimiento`, rótulos NEG ou NEU |
| Censura do texto | E-mail, telefone, CPF, URL, @ | Isso mais `[NOME]` (pessoas), `[APP]` (marcas da amostra), `[MARCA]` (outras empresas) e `[LOCAL]` (lugares) |
| Dados no GitHub | Duas tabelas grandes com as críticas do Brasil | Tabelas pequenas por país, loja e app, só com máscaras `APP_xxx` |

## Alterações por arquivo

### Configuração

**`src/config.py`**
- Variável `MARKET` (`br`, `us`, `es`, `mx`). Sem ela, vale o Brasil e o protocolo original.
- Strings traduzidas (`STRINGS_EN`, `STRINGS_ES`) e categorias em espanhol ("Finanzas", "Educación").
- Termos de exclusão em inglês e espanhol, aplicados só fora do Brasil (bancos, carteiras,
  investimento, crédito, adiantamento de salário).
- `EXCLUDE_INTERNATIONAL_APPS`: exclusão manual registrada de 3 apps fora do escopo
  (empréstimo, consultoria de investimentos, conta em dólar).
- Pastas: Brasil em `data/brasil/`, mercados em `data/mercados_internacionais/<país>/`.
- Corte de sentimento: `POSITIVE_COMPOUND = 0.05` (descarta só as positivas).

**`.gitignore`**
- Só `data/publico/` vai para o GitHub. Ficam fora a chave das máscaras, as pastas de trabalho
  (com nomes de apps) e as reviews brutas (texto sem censura e data com hora).

**`requirements.txt`**
- `pysentimiento` (sentimento em espanhol) e `transformers` (reconhecimento de nomes).

### Busca e triagem (passos 1 a 4)

**`src/01_search_google_play.py`**
- Usa o idioma e o país do mercado.
- Plano B quando a biblioteca `google-play-scraper` falha na busca (bug ao ler o resultado em
  destaque): lê a página pública de busca da Play Store.

**`src/02_search_app_store.py`**
- Usa o país do mercado.

**`src/03_clean_stores.py`**, **`src/03b_check_other_store.py`**, **`src/04_cross_store_dedup.py`**
- Usam idioma e país do mercado.
- Nos mercados internacionais, não gravam arquivos de apps excluídos. Os motivos de
  exclusão ficam em `outputs/funnel_metrics_<país>.json`.

### Coleta, sentimento e censura (passos 5 a 7)

**`src/05_scrape_google_play_reviews.py`**
- Lê a amostra do mercado (`amostra_coleta.csv`).
- Fora do Brasil, pede à loja só as reviews de 1, 2 e 3 estrelas.
- A chave de máscaras só cresce: os apps do Brasil nunca perdem a máscara.

**`src/05b_scrape_app_store_reviews.py`**
- Lê a amostra do mercado e usa o país dele no feed da Apple.

**`src/06_filter_sentiment.py`**
- Critério negativo ou neutro.
- Espanhol com `pysentimiento`.
- Correção: reviews sem texto quebravam o modelo (no pandas 3, `astype(str)` mantém o vazio).

**`src/07_build_ai_share.py`**
- Gera só as cópias das **críticas** (a cópia de todas as reviews não era usada).
- Aplica a censura de marcas dos apps e de nomes, marcas e lugares.

**`src/review_redaction.py`**
- Regra para nomes que o próprio avaliador escreve ("meu nome é…", "my name is…",
  "me llamo…", "Att.").
- `redact_person_names`: modelo multilíngue `Davlan/bert-base-multilingual-cased-ner-hrl`
  troca pessoas, empresas e lugares por `[NOME]`, `[MARCA]` e `[LOCAL]`. Sempre cobre a
  palavra inteira e analisa reviews longas em pedaços.
- `brand_regex` e `redact_brands`: trocam as marcas dos apps da amostra por `[APP]`, sem
  diferenciar maiúsculas e acentos. Marcas que também são palavras comuns ("era", "wallet")
  não entram na lista.

### Dados públicos (passos 8 e 8b)

**`src/08_build_public_data.py`**
- Deixa de copiar as críticas. Continua gerando funil e amostra do Brasil.

**`src/08b_build_public_criticas.py`** (novo; antes `08b_build_public_international.py`)
- Gera `data/publico/<país>/apps.csv` (só `APP_xxx`, categoria e nº de críticas) e
  `data/publico/<país>/<google_play|app_store>/APP_xxx.csv` (até 1.500 linhas por arquivo,
  para o GitHub mostrar como tabela), para Brasil, EUA, Espanha e México.
- **Não grava nada** se sobrar marca de app, e-mail, URL, @, telefone, CPF ou data com hora.

### Etapas novas para outros idiomas

**`src/09_build_other_languages.py`**: junta os mercados e conta as reviews por idioma.

**`src/09b_build_market_samples.py`**: monta a lista de apps a coletar em cada país
(elegíveis nas duas lojas, menos os recusados na validação e na exclusão manual).

**`src/10_build_country_folders.py`**: gera `criticas.csv` e `apps_elegiveis.csv` de cada país
(pastas de trabalho, fora do git) e `apps_em_varios_paises.csv` (apps presentes em mais de um país).

### Documentação

**`README.md`**, **`docs/pipeline_explicativo.md`**, **`docs/protocolo_codificacao_qualitativa.md`**
- Passos novos, comandos por mercado, critério negativo ou neutro, censura e novas pastas.

## Dados

| Pasta | No GitHub? | Conteúdo |
|---|---|---|
| `data/publico/` | Sim | Funil, amostra e críticas por país, loja e app, só com máscaras e censura |
| `data/brasil/` | Não | Busca, triagem, reviews e críticas do Brasil (com nomes de apps) |
| `data/mercados_internacionais/` | Não | O mesmo para EUA, Espanha e México |
| `data/chave_apps_mascarados_NAO_COMPARTILHAR/` | Não | Chave `APP_xxx` → app real |

**Apps na amostra de cada país:** Brasil 40, EUA 24, Espanha 11 e México 14. 12 apps aparecem
em mais de um país.

## Situação em 22/11/2026, 19h50

- A coleta dos EUA, da Espanha e do México e a censura do Brasil estão em andamento. As
  críticas públicas ainda **não** foram regeneradas.
- Os arquivos `data/publico/reviews_criticas_*.csv` do GitHub ainda são a versão antiga:
  só negativas, com 3 nomes censurados por regra. Eles serão substituídos pelas tabelas por
  país, loja e app.
- O commit `104806a` ("censura qualquer nome de pessoa") também trouxe todas as mudanças de
  mercados, coleta, sentimento e documentação, não só a censura. E o commit `e325ee3` diz
  "negativas ou neutras", mas os arquivos dele ainda são a versão só com negativas.
- Os testes em `tests/` e o arquivo `docs/alteracoes_artigo.md` estão sendo feitos à parte
  (Codex).
