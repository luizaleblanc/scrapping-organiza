# Checklist do artigo (análise + escrita)

Atualizado em 23/11/2026. Segue [guia_metodologia_reviews.md](guia_artigo/guia_metodologia_reviews.md).

Legenda: `[x]` feito · `[~]` parcial · `[ ]` falta. Cada item tem **(A)** análise no código e **(B)** texto em `artigo/`. Ao concluir um item, marque-o aqui e cite o script ou o arquivo `.tex` correspondente.

## Etapa 0: busca, triagem e coleta (já feitas)

- [x] (A) Busca com 6 strings nas duas lojas e triagem por critérios ([src/01–04](../src/)).
- [x] (A) Coleta: BR com 223.688 (GP) + 5.467 (AS) avaliações de 40 apps; também US, ES e MX ([outputs/](../outputs/)).
- [x] (A) Mascaramento `APP_xxx` e redação de dados pessoais ([src/07](../src/07_build_ai_share.py), [src/review_redaction.py](../src/review_redaction.py)).
- [x] (B) Seção "Seleção de apps e coleta" em [`artigo/secoes/metodologia.tex`](../artigo/secoes/metodologia.tex) (com referências em [`artigo/referencias.bib`](../artigo/referencias.bib)).
- [x] (B) Declarar os Termos de Serviço e a ética da coleta (Google Play e Apple RSS): parágrafo "Termos de serviço e considerações éticas" em [`artigo/secoes/metodologia.tex`](../artigo/secoes/metodologia.tex), com dados públicos sem autenticação, intervalo entre requisições, limites de volume, uso acadêmico, minimização dos dados e a ambiguidade dos termos declarada como limitação

## Etapa 1: Pré-processamento

- [x] (A) Remover avaliações com ≤ 3 palavras e anotar a regra de "unidade" (`MIN_WORDS = 3`; unidade = palavra separada por espaço via `str.split()`; [src/config.py](../src/config.py), [src/06_filter_sentiment.py](../src/06_filter_sentiment.py), [tests/test_review_rules.py](../tests/test_review_rules.py)).
- [x] (A) Remover duplicatas exatas e textos vazios, com o N removido registrado no funil ([src/06_filter_sentiment.py](../src/06_filter_sentiment.py)).
- [x] (A) Converter para minúsculas, sem stopwords nem stemming (`content_clean` em [src/06_filter_sentiment.py](../src/06_filter_sentiment.py); sentimento roda sobre o texto original para preservar maiúsculas no LeIA/VADER).
- [x] (A) Registrar N0 → N1 em `outputs/funnel_metrics*.json` (todos os 4 mercados concluídos em [outputs/](../outputs/): `278.046 → 201.087`; BR `150.284` GP / `5.136` AS; US `21.952` / `6.451`; ES `6.876` / `866`; MX `7.327` / `2.195`).
- [x] (B) Parágrafo de pré-processamento (redigido com Tabela `tab:preprocessamento` em [`artigo/secoes/metodologia.tex`](../artigo/secoes/metodologia.tex) e documentado em [`docs/instrucoes_artigo.md`](instrucoes_artigo.md)).
- [x] O pré-processamento roda antes do filtro ([src/06_filter_sentiment.py](../src/06_filter_sentiment.py), [`artigo/secoes/metodologia.tex`](../artigo/secoes/metodologia.tex), [`docs/instrucoes_artigo.md`](instrucoes_artigo.md)).

## Etapa 2: Sentimento e filtro

- [x] (A) Ferramenta por idioma: LeIA (pt), VADER (en), pysentimiento (es) ([src/06](../src/06_filter_sentiment.py)).
- [x] (A) Limiar declarado: compound < 0,05; para es, os rótulos NEG/NEU.
- [x] (A) Regra de **interseção**: nota ≤ 3 **E** sentimento negativo ou neutro.
- [x] (A) Contagens pós-pré-processamento: BR `22.316` GP / `2.020` AS; US `12.188` / `1.398`; ES `6.305` / `282`; MX `6.735` / `519` (total `51.763` críticas em [outputs/](../outputs/)).
- [x] (A) N que o filtro só por estrelas reteria (`stars_only_le_3` em [src/06](../src/06_filter_sentiment.py): BR `31.507` GP / `2.595` AS; US `21.952` / `2.574`; ES `6.876` / `299`; MX `7.327` / `545`; total `73.675`).
- [x] (A) Checagem manual de 100 avaliações com a taxa de erro ([`data/checagem_manual_sentimento_100.csv`](../data/checagem_manual_sentimento_100.csv), [src/06b_manual_sentiment_check.py](../src/06b_manual_sentiment_check.py), `06b_manual_sentiment_check` em [outputs/funnel_metrics.json](../outputs/funnel_metrics.json): `seed=42`, erro global `40,0%` [40/100]; apenas `12,0%` de falsos positivos entre críticas [6/50; precisão `88,0%`] vs. `68,0%` de falsos negativos entre removidas positivas [34/50]; por idioma: `pt` `32,35%`, `es` `36,36%`, `en` `51,52%`).
- [x] (B) Parágrafo de sentimento com a frase de limitação (concluído com Tabela `tab:sentimento`, taxa de erro da checagem manual e referências em [`artigo/secoes/metodologia.tex`](../artigo/secoes/metodologia.tex)).

## Etapa 3: BERTopic

- [x] Decidir se cada mercado ou idioma é modelado separadamente ou em conjunto (decisão: **separado por idioma** — `pt`, `en`, `es` — com deduplicação de `6.300` duplicatas exatas ES/MX na Google Play; opção `--juntos` mantida em [src/11_bertopic.py](../src/11_bertopic.py); documentado em [`artigo/secoes/metodologia.tex`](../artigo/secoes/metodologia.tex) e [`docs/instrucoes_artigo.md`](instrucoes_artigo.md)).
- [x] (A) Script [src/11_bertopic.py](../src/11_bertopic.py) com embeddings multilíngues (`paraphrase-multilingual-MiniLM-L12-v2`) e `random_state=42` (testado em [tests/test_review_rules.py](../tests/test_review_rules.py); dependências em [requirements.txt](../requirements.txt)).
- [x] (A) Hiperparâmetros e versões salvos em [`outputs/funnel_metrics.json`](../outputs/funnel_metrics.json) (`11_bertopic_pt`, `11_bertopic_en`, `11_bertopic_es`).
- [x] (A) Exportar tópicos, palavras-chave, avaliações representativas, mapa e matriz (`data/topicos/{pt,en,es}/`: `review_topics.csv`, `topic_info.csv`, `representative_docs.csv`, `intertopic_map.html`, `similarity_matrix.html`).
- [x] (A) Coerência c_v por tópico (`roder2015_numpy`, 10 palavras-chave: `pt` `0,4689` [116 tópicos], `en` `0,4664` [98 tópicos], `es` `0,4594` [46 tópicos]; gravado em `topic_info.csv` e [`outputs/funnel_metrics.json`](../outputs/funnel_metrics.json)).
- [x] (B) Parágrafo do BERTopic (redigido com Tabela `tab:bertopic` e referências `grootendorst2022`, `egger2022`, `roder2015` em [`artigo/secoes/metodologia.tex`](../artigo/secoes/metodologia.tex) e [`artigo/referencias.bib`](../artigo/referencias.bib)).

## Etapa 4: Inspeção dos tópicos

- [x] (A) Outliers (−1) removidos e N registrado (`23.225` outliers: `pt` `13.824` [56,81%], `en` `6.526` [48,03%], `es` `2.875` [38,12%] → `N3 = 22.237`; [src/11_bertopic.py](../src/11_bertopic.py), [`outputs/funnel_metrics.json`](../outputs/funnel_metrics.json)).
- [x] (A) Clusters < 15 removidos, com n e c_v média (`0` clusters / `0` avaliações devido a `min_cluster_size = 15` no HDBSCAN → `N4 = 22.237`; [`outputs/funnel_metrics.json`](../outputs/funnel_metrics.json)).
- [~] (A) Planilha de triagem com decisão e motivo (`data/topicos/{pt,en,es}/triagem_topicos.csv` geradas com `116`, `98` e `46` tópicos e 3 exemplos cada; colunas `decisao`, `categoria_exclusao` e `motivo` em branco aguardando triagem humana).
- [ ] Definir as categorias de exclusão conforme a pergunta de pesquisa.
- [ ] (A) Revisão por um segundo pesquisador e concordância.
- [ ] (A) Funil fechando até N5.
- [~] (B) Parágrafo e tabela do funil (redigidos até `N4` com Tabela `tab:funil` em [`artigo/secoes/metodologia.tex`](../artigo/secoes/metodologia.tex); exclusões temáticas e `N5` ficam como `[N]` + `% TODO` até concluir a triagem humana).

## Etapa 5: Análise temática

- [ ] Definir o referencial dedutivo (dark UX, requisitos ou duas camadas; ver o [protocolo](protocolo_codificacao_qualitativa.md)).
- [ ] (A) Exportar o corpus com `[T_ID, R_ID]`.
- [ ] (A) Codificação indutiva, depois dedutiva, e consolidação em equipe.
- [ ] (A) Tabela de temas com tema, códigos, n, % e exemplo.
- [ ] (B) Parágrafo da análise temática.

## Etapa 6: Resultados e limitações

- [ ] (A) Prevalência de temas por app e gráficos.
- [ ] (B) Resultados por tema, com citações rastreáveis.
- [ ] (B) Limitações (RSS limitado a 500 avaliações; ES/MX sem garantia de país; filtro; BERTopic; codificação).

## Reprodutibilidade (antes de submeter)

- [ ] Funil fechando em todas as etapas.
- [ ] Semente e hiperparâmetros registrados.
- [ ] Material suplementar pronto.
- [ ] Nenhum nome de pessoa ou app real em `artigo/` nem em `data/publico/`.
