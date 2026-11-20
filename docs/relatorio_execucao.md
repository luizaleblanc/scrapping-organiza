# Relatório de execução — análise de avaliações financeiras

**Projeto:** coleta e análise de avaliações de aplicativos de finanças pessoais para apoiar a pesquisa aplicada ao Organiza AI.  
**Referência metodológica principal:** `Organiza_Article.pdf`, fornecido pela pesquisadora.  
**Data dos números consultados:** 20/11/2026.

## 1. Objetivo e escopo

A primeira fase da pesquisa analisa aplicativos comerciais de finanças pessoais e orçamento a partir de avaliações públicas de usuários. O Organiza AI é o contexto aplicado da pesquisa, mas não é o objeto da coleta de avaliações.

A busca foi configurada para duas regiões: termos em português na Google Play brasileira (`pt`, `br`) e termos em inglês na Google Play dos Estados Unidos (`en`, `us`). Portanto, a amostra é internacional e inclui resultados brasileiros; não representa apenas o mercado brasileiro.

## 2. Método alinhado ao artigo

O artigo descreve mineração de avaliações públicas da Google Play com `google-play-scraper`, seleção de avaliações com nota de até 3 estrelas e classificação de sentimento por idioma: VADER para inglês e LeIA, adaptação do VADER para português, para português. A análise posterior prevê modelagem de tópicos com BERTopic e análise temática reflexiva.

O código atual implementa as etapas de busca, triagem, coleta e filtro de nota/sentimento. O LeIA já está disponível em `vendor/LeIA`, a partir do repositório citado no artigo: [rafjaa/LeIA](https://github.com/rafjaa/LeIA). A coleta usa a biblioteca [google-play-scraper](https://github.com/JoMingyu/google-play-scraper), também citada no artigo.

O filtro guarda avaliações com nota `<= 3` e escore composto `<= 0.05` (neutro ou negativo). O VADER é usado nas avaliações marcadas como inglês; o LeIA, nas marcadas como português. A coleta permite apenas campos necessários à análise e descarta nome, foto e identificador individual da avaliação.

## 3. Buscas configuradas

O arquivo `src/config.py` contém 12 buscas de aplicativos, executadas individualmente com até 30 resultados por termo:

| Região | Termos |
|---|---|
| EUA / inglês | `budget planner`; `expense tracker`; `personal finance`; `AI money assistant`; `money manager` |
| Brasil / português | `finanças pessoais`; `organizador financeiro`; `controle de gastos`; `orçamento pessoal`; `aplicativo de controle financeiro`; `IA para finanças`; `organizador financeiro com IA` |

As buscas bibliográficas sobre scraping/mineração de avaliações estão separadas no código e não são enviadas à Google Play. `educador de finanças` não foi incluído na busca principal de apps porque tende a retornar educação financeira que pode não satisfazer o critério de aplicativo de orçamento/controle pessoal.

## 4. Pipeline implementado

1. `src/01_search_apps.py` — busca resultados e consolida aplicativos repetidos.
2. `src/02_screen_apps.py` — aplica critérios automáticos (categoria, avaliações, atualização recente e correspondência aproximada na App Store) e deixa foco em orçamento pessoal e B2C para decisão manual.
3. `src/03_scrape_reviews.py` — coleta avaliações apenas dos apps aprovados manualmente, salva progresso por app e mantém os campos anonimizados permitidos.
4. `src/04_filter_sentiment.py` — filtra nota e sentimento com VADER/LeIA e atualiza as métricas.

Durante a coleta, alguns apps tinham contagem de avaliações nos metadados ligeiramente superior ao número de textos que a Google Play disponibilizou. O script foi ajustado para reconhecer o fim da paginação, salvar o que estava acessível e continuar para o próximo app. A execução concluída mostrou `Apps: 100%`, com 38 apps processados.

## 5. Resultados registrados

O arquivo `outputs/funnel_metrics.json` registra a execução:

| Métrica | Valor registrado |
|---|---:|
| Linhas de resultados de busca | 348 |
| Apps únicos na métrica de busca | 155 |
| Termos configurados | 12 |
| Apps aprovados automaticamente | 50 |
| Avaliações coletadas | 162.092 |
| Removidas pelo filtro de nota | 124.844 |
| Removidas pelo filtro de sentimento | 13.351 |
| Avaliações críticas finais | 23.897 |
| Críticas em inglês | 16.410 |
| Críticas em português | 7.487 |

Os 38 apps aprovados nos critérios automáticos e nas duas decisões manuais foram coletados. O resultado filtrado está em `data/processed/reviews_critical.csv`; a base coletada está em `data/processed/reviews_anonymized.csv`.

**Ponto de reconciliação:** o JSON registra 155 apps únicos e 155 triados, mas o arquivo atual `data/processed/apps_screening.csv` contém 156 IDs distintos. Antes de publicar números finais, atualize/reconcilie as métricas do funil com o CSV atual. Os números das avaliações e do filtro acima são os valores registrados no JSON da execução concluída.

## 6. Concorrentes brasileiros

Foi criado `outputs/concorrentes_brasileiros.md` como mapa inicial de concorrentes e referências de produto, incluindo Oinc. Oinc está documentado como concorrente, mas não consta na amostra atual de 38 apps coletados; o próprio mapa recomenda buscá-lo nominalmente e triá-lo na próxima rodada. A presença no mapa competitivo não significa inclusão na amostra de pesquisa.

## 7. Arquivos principais

- `src/config.py` — termos, idioma/região, caminhos e parâmetros da coleta.
- `src/01_search_apps.py` a `src/04_filter_sentiment.py` — pipeline executável.
- `data/raw/apps_candidates.csv` — candidatos descobertos.
- `data/processed/apps_screening.csv` — triagem e decisões manuais.
- `data/processed/reviews_anonymized.csv` — avaliações coletadas com campos permitidos.
- `data/processed/reviews_critical.csv` — avaliações selecionadas por nota e sentimento.
- `data/private/app_mapping.csv` e `data/private/review_checkpoint.json` — mapeamento e retomada local da coleta; não devem ser publicados.
- `outputs/funnel_metrics.json` — contagens registradas no funil.
- `outputs/concorrentes_brasileiros.md` — pesquisa competitiva inicial.

## 8. Próximos passos

1. Reconciliar os 155 apps registrados nas métricas com os 156 IDs do CSV de triagem.
2. Reexecutar nominalmente a busca por Oinc e pelos demais concorrentes previstos no mapa, aplicar os critérios de elegibilidade e documentar inclusões/exclusões.
3. Se a etapa analítica do artigo ainda não foi executada, modelar tópicos com BERTopic, avaliar coerência e conduzir a análise temática reflexiva prevista.
4. Registrar parâmetros, versões de dependências e data de execução para tornar o resultado reproduzível.

## 9. Execução local

Com o ambiente virtual ativo na pasta do projeto:

```powershell
python src/01_search_apps.py
python src/02_screen_apps.py
# preencher as decisões manuais na triagem
python -u src/03_scrape_reviews.py
python -u src/04_filter_sentiment.py
```

Os arquivos brutos, anonimizados, de mapeamento e checkpoint são artefatos locais de pesquisa; revisar o plano de compartilhamento e as permissões aplicáveis antes de versioná-los ou distribuí-los.
