# Padrões enganosos em apps de finanças pessoais — pipeline de dados

> Explicação completa do que foi feito, funil e decisões: [docs/pipeline_explicativo.md](docs/pipeline_explicativo.md)

Triagem de apps nas duas lojas, coleta de avaliações públicas da Google Play e filtro
de avaliações críticas (replicação do protocolo de Alsebayel et al., 2025).

**Strings de busca (únicas usadas, nas duas lojas, Brasil, top 30 cada):**
`finanças` · `organizador de finanças` · `educador de finanças` · `aplicativos financeiros` ·
`ia para finanças` · `organizador financeiro com ia`

**Ficam fora:** bancos e contas digitais, maquininhas, carteiras/pagamentos, trading,
cripto e investimentos, ferramentas empresariais/crédito, categorias diferentes de
Finance, apps sem avaliações ou sem atualização há 12 meses, apps presentes em só uma
loja e o Organiza AI. As listas ficam em `src/config.py`; cada exclusão é registrada
com motivo.

Reviews são coletadas **nas duas lojas** (mudança de protocolo em 22/11/2026): Google Play pelo `google-play-scraper` (histórico completo) e App Store pelo feed RSS público de avaliações da Apple (até 500 mais recentes por app).

## Instalação (uma vez)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
git clone https://github.com/rafjaa/LeIA.git vendor/LeIA
```

## Passo a passo

Execute na pasta do projeto, com o ambiente ativado. Defina antes
`$env:PYTHONIOENCODING = "utf-8"` para os acentos aparecerem no terminal.

| # | Comando | O que faz | Saída |
|---|---|---|---|
| 1 | `python src/01_search_google_play.py` | Busca as 6 strings na Google Play | `data/brasil/google_play_store/busca_e_triagem/search_hits.csv` |
| 2 | `python src/02_search_app_store.py` | Busca as 6 strings na App Store | `data/brasil/app_store/busca_e_triagem/search_hits.csv` |
| 3 | `python src/03_clean_stores.py` | Aplica os critérios nas duas lojas e deduplica | `apps_eligible.csv` e `apps_excluded_audit.csv` em cada pasta |
| 3b | `python src/03b_check_other_store.py` | Critério 4: procura cada elegível na outra loja pelo nome (mesma marca e mesmas regras) | acrescenta a `apps_eligible.csv` com `discovery_source = availability_check` |
| 4 | `python src/04_cross_store_dedup.py` | Mantém só apps presentes nas duas lojas | `data/brasil/apps_nas_duas_lojas/apps_both_stores.csv` |
| 5 | `python src/05_scrape_google_play_reviews.py` | Coleta e anonimiza reviews da Google Play **só dos apps de `apps_both_stores.csv`** (excluídos nunca são coletados) | `data/brasil/google_play_store/reviews/reviews_anonymized.csv` |
| 5b | `python src/05b_scrape_app_store_reviews.py` | Coleta e anonimiza avaliações da App Store dos mesmos apps (feed RSS, até 500 por app) | `data/brasil/app_store/reviews/reviews_anonymized.csv` |
| 6 | `python src/06_filter_sentiment.py` | Mantém nota ≤ 3 e sentimento negativo ou neutro, como no artigo (as duas lojas) | `data/<loja>/reviews/reviews_critical.csv` |
| 7 | `python src/07_build_ai_share.py` | Gera as cópias redigidas das críticas, com qualquer nome de pessoa trocado por `[NOME]` (as duas lojas) | `data/<loja>/reviews_para_ia/*.csv` |
| 8 | `python src/08_build_public_data.py` | Gera a única pasta publicada no GitHub, sem nenhum identificador de app | `data/publico/` |

**Revisão manual (entre os passos 4 e 5):** pares parecidos, mas não idênticos, entre as
lojas ficam em `data/brasil/apps_nas_duas_lojas/manual_match_decisions.csv`. Preencha a coluna
`decision` com `yes` (mesmo app) ou `no` e rode o passo 4 de novo. Sem `yes`, o par não
entra na amostra.

**Passo 5:** pode demorar mais de uma hora. Se cair, rode de novo e ele continua de onde
parou. Use `--max-per-app 20` para um teste rápido.

## Outros idiomas: inglês e espanhol (pedido do orientador, 22/11/2026)

As etapas 1 a 4 também rodam nas lojas dos **EUA (inglês)**, da **Espanha** e do
**México (espanhol)**, com as 6 strings traduzidas (`STRINGS_EN` e `STRINGS_ES` em
`src/config.py`). O mercado é escolhido pela variável `MARKET`. Sem ela, vale `br`, e o
protocolo original não muda. Cada mercado grava em `data/mercados_internacionais/<estados_unidos|espanha|mexico>/` (não versionado).
Fora do Brasil entram termos de exclusão equivalentes em inglês e espanhol, além de marcas
de bancos, investimento e crédito que não estavam nas listas em português.

```powershell
$env:PYTHONIOENCODING = "utf-8"
foreach ($m in "us", "es", "mx") {
  $env:MARKET = $m
  python src/01_search_google_play.py; python src/02_search_app_store.py
  python src/03_clean_stores.py; python src/03b_check_other_store.py; python src/04_cross_store_dedup.py
}
Remove-Item Env:MARKET
python src/09_build_other_languages.py
```

| # | Comando | O que faz | Saída |
|---|---|---|---|
| 1–4 | com `$env:MARKET` = `us`, `es` ou `mx` | Busca, triagem e pareamento entre as lojas daquele mercado | `data/mercados_internacionais/<país>/...` (sem arquivos de apps excluídos; os motivos ficam no json) e `outputs/funnel_metrics_<país>.json` |
| 9 | `python src/09_build_other_languages.py` (sem `MARKET`) | Junta os mercados e conta reviews por idioma (até 500 por loja) | `data/brasil/apps_nas_duas_lojas/apps_novos_outros_idiomas.csv` (apps fora da amostra original) e `apps_both_stores_outros_idiomas.csv` (as 40 apps com colunas por idioma) |

**Coleta e críticas por país** (depois de validar os apps novos):

```powershell
python src/09b_build_market_samples.py          # apps encontrados e elegíveis em cada país, menos os recusados na validação
foreach ($m in "us", "es", "mx") {
  $env:MARKET = $m
  python src/05_scrape_google_play_reviews.py   # use --max-per-app 2000 se não quiser o histórico completo
  python src/05b_scrape_app_store_reviews.py
  python src/06_filter_sentiment.py             # espanhol: pysentimiento (critério = rótulo NEG)
  python src/07_build_ai_share.py
}
Remove-Item Env:MARKET
python src/10_build_country_folders.py          # monta os criticas.csv de cada país
```

O resultado fica na raiz de `data/brasil/` e de `data/mercados_internacionais/<país>/` (não versionado),
**só com as críticas**: `apps_elegiveis.csv` (apps do país e quantas críticas cada um teve),
e `criticas.csv` (todas as críticas do país num só arquivo, com as colunas `app` e `loja`).
Apps elegíveis em mais de um país (incluindo o Brasil) ficam em
`data/mercados_internacionais/apps_em_varios_paises.csv`, com as críticas de cada país.
As máscaras `APP_xxx` são as mesmas em todos os países.

A revisão manual dos pares parecidos é feita por mercado, em
`data/mercados_internacionais/<país>/apps_nas_duas_lojas/manual_match_decisions.csv`. Depois, rode o
passo 4 daquele mercado e o passo 9 de novo.

Na Google Play, as reviews são separadas por idioma, não por país: Espanha e México
trazem as mesmas reviews em espanhol. Por isso, conte o espanhol como um grupo só.
No espanhol, o passo 6 usa o `pysentimiento`, porque o VADER só entende inglês. Ele não tem
"compound": a review fica quando o rótulo previsto é NEG ou NEU.

Os passos 1 e 2 refazem a busca e podem trazer resultados diferentes. Para reproduzir a
amostra atual, comece pelo passo 3.

## Pastas

```
data/
├── google_play_store/
│   ├── busca_e_triagem/                          busca, elegíveis e excluídos com motivo (não versionado)
│   ├── reviews/                                  reviews anonimizadas e críticas (não versionado)
│   └── reviews_para_ia/                          cópias redigidas para IA (não versionado)
├── app_store/
│   ├── busca_e_triagem/
│   ├── reviews/
│   └── reviews_para_ia/
├── apps_nas_duas_lojas/                          amostra final, loja única, revisão manual (não versionado)
├── mercados_internacionais/<estados_unidos,espanha,mexico>/   mesma estrutura do Brasil (google_play_store, app_store, apps_nas_duas_lojas), sem excluídos (não versionado)

├── publico/                                      ÚNICA pasta publicada: triagem e reviews críticas anonimizadas
└── chave_apps_mascarados_NAO_COMPARTILHAR/     mapeamento APP_001 -> appId (não versionado)
outputs/funnel_metrics.json                       contagens de cada etapa do funil (não versionado; versão pública em data/publico/funil.json)
src/                                              scripts do pipeline (01 a 10)
docs/pipeline_explicativo.md                      explicação completa do pipeline e das decisões
docs/protocolo_codificacao_qualitativa.md         protocolo da análise (BERTopic, Gray, prompt para IA)
vendor/LeIA/                                      analisador de sentimento em português
```

## Ética

Só avaliações públicas. Nome, foto e ID do avaliador nunca são gravados, e nos arquivos publicados a data fica sem a hora. E-mails,
telefones, CPFs, URLs, @menções e **qualquer nome de pessoa** no texto são substituídos. Os nomes
são detectados por um modelo de reconhecimento de entidades multilíngue (português, inglês e
espanhol; `Davlan/bert-base-multilingual-cased-ner-hrl`) e por regras para "meu nome é…" e assinaturas. Os apps aparecem mascarados
(`APP_001`…), e o mapeamento fica em `data/chave_apps_mascarados_NAO_COMPARTILHAR/`. A redação automática não pega todo
dado pessoal (ex.: número de pedido); revise uma amostra antes de compartilhar.

## Licença

O código deste repositório está sob a [licença MIT](LICENSE) © 2026 Luiza Ferraz Leblanc.

A licença cobre só o código. Não cobre:
- **Dados das lojas:** títulos, descrições e metadados dos apps em `data/` pertencem às respectivas lojas e desenvolvedores e são usados aqui para fins de pesquisa.
- **Dados publicados (`data/publico/`):** só triagem e funil sem identificadores de app, e as reviews críticas (1 a 3 estrelas, sentimento negativo ou neutro) redigidas, sem dados do avaliador e com data sem hora. O texto pertence aos seus autores; não use para identificar pessoas nem apps.
- **LeIA** (`vendor/LeIA`): é baixado à parte e segue a licença do próprio projeto ([rafjaa/LeIA](https://github.com/rafjaa/LeIA)).
