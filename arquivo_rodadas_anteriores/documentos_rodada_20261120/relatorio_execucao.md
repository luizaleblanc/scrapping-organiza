# Relatório de execução — análise de avaliações financeiras

**Projeto:** coleta e análise de avaliações de aplicativos de finanças pessoais para apoiar a pesquisa aplicada ao Organiza AI.  
**Referência metodológica principal:** `Organiza_Article.pdf`, fornecido pela pesquisadora.  
**Data dos números consultados:** 20/11/2026.

## 1. Objetivo e escopo

A primeira fase da pesquisa analisa aplicativos comerciais de finanças pessoais e orçamento a partir de avaliações públicas de usuários. O Organiza AI é o contexto aplicado da pesquisa, mas não é o objeto da coleta de avaliações.

**Escopo de busca atualizado:** a descoberta atual usa somente a frase `gestão pessoal de finanças com IA`, na loja brasileira. Os números históricos abaixo foram gerados com buscas mais amplas e não representam o novo escopo.

## 2. Método alinhado ao artigo

O artigo descreve mineração de avaliações públicas da Google Play com `google-play-scraper`, seleção de avaliações com nota de até 3 estrelas e classificação de sentimento por idioma: VADER para inglês e LeIA, adaptação do VADER para português, para português. A análise posterior prevê modelagem de tópicos com BERTopic e análise temática reflexiva.

O código atual implementa as etapas de busca, triagem, coleta e filtro de nota/sentimento. O LeIA já está disponível em `vendor/LeIA`, a partir do repositório citado no artigo: [rafjaa/LeIA](https://github.com/rafjaa/LeIA). A coleta usa a biblioteca [google-play-scraper](https://github.com/JoMingyu/google-play-scraper), também citada no artigo.

O filtro guarda avaliações com nota `<= 3` e escore composto `<= 0.05` (neutro ou negativo). O VADER é usado nas avaliações marcadas como inglês; o LeIA, nas marcadas como português. A coleta permite apenas campos necessários à análise e descarta nome, foto e identificador individual da avaliação.

## 3. Buscas configuradas

O arquivo `src/config.py` contém uma busca de aplicativos, executada na região brasileira:

| Região | Termos |
|---|---|
| Brasil / português | `gestão pessoal de finanças com IA` |

As buscas bibliográficas sobre scraping/mineração de avaliações estão separadas no código e não são enviadas às lojas. A triagem Apple exige categoria Finance, título aderente e exclui bancos; categorias médicas, Games, Lifestyle e Health & Fitness ficam fora do nicho.

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
| Termos configurados na execução histórica | 12 |
| Apps aprovados automaticamente | 50 |
| Avaliações coletadas | 162.092 |
| Removidas pelo filtro de nota | 124.844 |
| Removidas pelo filtro de sentimento | 13.351 |
| Avaliações críticas finais | 23.897 |
| Críticas em inglês | 16.410 |
| Críticas em português | 7.487 |

Os 38 apps aprovados nos critérios automáticos e nas duas decisões manuais foram coletados. O resultado filtrado está em `data/processed/reviews_critical.csv`; a base coletada está em `data/processed/reviews_anonymized.csv`.

Uma auditoria automatizada confirmou que as avaliações críticas são subconjunto da base completa. O script `src/06_audit_anonymize_reviews.py` redige e-mails, URLs, CPF, telefones, @identificadores e sequências numéricas ambíguas; esta redação também foi aplicada aos CSVs principais a pedido da pesquisadora. As sequências numéricas ambíguas podem incluir números não pessoais. `src/03_scrape_reviews.py` agora aplica a mesma redação antes de salvar novas avaliações. A redação por regex não garante anonimização completa; revisar os arquivos antes de qualquer compartilhamento externo.

**Ponto de reconciliação:** o JSON registra 155 apps únicos e 155 triados, mas o arquivo atual `data/processed/apps_screening.csv` contém 156 IDs distintos. Antes de publicar números finais, atualize/reconcilie as métricas do funil com o CSV atual. Os números das avaliações e do filtro acima são os valores registrados no JSON da execução concluída.

## 6. Concorrentes brasileiros

Foi criado `outputs/concorrentes_brasileiros.md` como mapa inicial de concorrentes e referências de produto, incluindo Oinc. Oinc está documentado como concorrente, mas não consta na amostra atual de 38 apps coletados; o próprio mapa recomenda buscá-lo nominalmente e triá-lo na próxima rodada. A presença no mapa competitivo não significa inclusão na amostra de pesquisa.

Em 20/11/2026, a busca exploratória anterior da Apple usou strings mais amplas e consultas nominais: 700 ocorrências, 416 apps brutos deduplicados e 152 candidatos após a auditoria antiga. **Esses dados foram retirados dos caminhos ativos e arquivados em `data/raw/app_store/previous_scope_20261120/`; não devem ser tratados como resultados da frase de busca atual.** O novo conjunto só existirá após executar novamente a busca e a auditoria.

A nova rotina Apple está implementada em `src/10_scrape_app_store_reviews.py`, `src/11_filter_app_store_sentiment.py` e `src/12_map_app_store_behavior.py`. A coleta usa o RSS público, limitado às páginas disponibilizadas por app, e grava os dados em CSVs separados dos resultados Google Play. Os sinais comportamentais são tags lexicais agregadas por app e indicam temas autorrelatados; servem como apoio exploratório à codificação qualitativa, não como inferências psicológicas individuais. A rotina não foi executada nesta rodada porque a busca antiga foi arquivada e o ambiente local não alcança o endpoint da Apple; execute os comandos no terminal com rede.

## 7. Arquivos principais

- `src/config.py` — termos, idioma/região, caminhos e parâmetros da coleta.
- `src/01_search_apps.py` a `src/04_filter_sentiment.py` — pipeline executável.
- `src/05_search_app_store.py` — descoberta de apps na Apple App Store.
- `src/08_audit_app_store_candidates.py` — auditoria de escopo dos candidatos da App Store e separação de inclusões/exclusões/revisões.
- `src/10_scrape_app_store_reviews.py` a `src/12_map_app_store_behavior.py` — coleta RSS, filtro por sentimento e mapa agregado de sinais comportamentais Apple.
- `src/06_audit_anonymize_reviews.py` — compara a base completa e o subconjunto crítico e gera cópias com redação heurística de identificadores.
- `src/review_redaction.py` — regras reutilizadas para redigir texto durante coleta e preparação dos CSVs.
- `src/07_export_cross_store_matches.py` — exporta apps da Google Play encontrados também pela busca da App Store.
- `data/raw/app_store/search_hits.csv` e `data/raw/app_store/candidates.csv` — resultados da busca da Apple por termo/região e apps deduplicados.
- `data/raw/apps_candidates.csv` — candidatos descobertos.
- `data/processed/apps_screening.csv` — triagem e decisões manuais.
- `data/processed/apps_in_both_stores.csv` — 69 correspondências reportadas pela triagem da Apple; 28 também têm título exato no conjunto de candidatos Apple e 38 pertencem à amostra aprovada atual. Correspondências aproximadas estão marcadas para revisão manual.
- `data/processed/reviews_anonymized.csv` — avaliações coletadas com campos permitidos.
- `data/processed/reviews_critical.csv` — avaliações selecionadas por nota e sentimento.
- `data/processed/ai_share/` — cópias redigidas para revisão antes de análise assistida por IA.
- `outputs/review_csv_audit.json` — métricas agregadas da comparação e redação; sem textos de avaliações.
- `data/private/app_mapping.csv` e `data/private/review_checkpoint.json` — mapeamento e retomada local da coleta; não devem ser publicados.
- `outputs/funnel_metrics.json` — contagens registradas no funil.
- `outputs/concorrentes_brasileiros.md` — pesquisa competitiva inicial.

## 8. Próximos passos

1. Reexecutar a descoberta nas lojas com a frase atual, auditar candidatos e executar coleta/filtro/perfil Apple no terminal com rede.
2. Reconciliar os 155 apps registrados nas métricas históricas com os 156 IDs do CSV de triagem.
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
