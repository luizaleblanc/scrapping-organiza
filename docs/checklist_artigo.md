# Checklist do artigo (análise + escrita)

Atualizado em 23/11/2026. Segue [guia_metodologia_reviews.md](guia_artigo/guia_metodologia_reviews.md).

Legenda: `[x]` feito · `[~]` parcial · `[ ]` falta. Cada item tem **(A)** análise no código e **(B)** texto em `artigo/`. Ao concluir um item, marque-o aqui e cite o script ou o arquivo `.tex` correspondente.

## Fases 1 e 2: busca, triagem e coleta (já feitas)

- [x] (A) Busca com 6 strings nas duas lojas e triagem por critérios ([src/01–04](../src/)).
- [x] (A) Coleta: BR com 223.688 (GP) + 5.467 (AS) avaliações de 40 apps; também US, ES e MX ([outputs/](../outputs/)).
- [x] (A) Mascaramento `APP_xxx` e redação de dados pessoais ([src/07](../src/07_build_ai_share.py), [src/review_redaction.py](../src/review_redaction.py)).
- [ ] (B) Seção "Seleção de apps e coleta" em `artigo/secoes/metodologia.tex`.
- [ ] (B) Declarar a verificação dos Termos de Serviço (Google Play e Apple RSS), que ainda depende de confirmação com a orientação.

## Etapa 1: Pré-processamento

- [ ] (A) Remover avaliações com ≤ 3 palavras e anotar a regra de "unidade". **Ainda não implementado.**
- [ ] (A) Remover duplicatas exatas e textos vazios, com o N removido registrado no funil.
- [ ] (A) Converter para minúsculas, sem stopwords nem stemming.
- [ ] (A) Registrar N0 → N1 em `outputs/funnel_metrics*.json`.
- [ ] (B) Parágrafo de pré-processamento.
- [ ] Decidir se o pré-processamento roda antes ou depois do filtro (o guia o coloca antes).

## Etapa 2: Sentimento e filtro

- [x] (A) Ferramenta por idioma: LeIA (pt), VADER (en), pysentimiento (es) ([src/06](../src/06_filter_sentiment.py)).
- [x] (A) Limiar declarado: compound < 0,05; para es, os rótulos NEG/NEU.
- [x] (A) Regra de **interseção**: nota ≤ 3 **E** sentimento negativo ou neutro.
- [x] (A) Contagens: BR GP 23.811 críticas; BR AS 2.037.
- [ ] (A) Distribuição % pos/neu/neg geral e por app (hoje só há a contagem de removidas).
- [ ] (A) N que o filtro só por estrelas reteria (calculável: total − `removed_by_score_gt_3`).
- [ ] (A) Checagem manual de 100 avaliações com a taxa de erro.
- [ ] (B) Parágrafo de sentimento com a frase de limitação.

## Etapa 3: BERTopic

- [ ] Decidir se cada mercado ou idioma é modelado separadamente ou em conjunto ([protocolo](protocolo_codificacao_qualitativa.md)).
- [ ] (A) Script `src/11_bertopic.py` com embeddings multilíngues e `random_state=42`.
- [ ] (A) Hiperparâmetros e versões salvos em `outputs/`.
- [ ] (A) Exportar tópicos, palavras-chave, avaliações representativas, mapa e matriz.
- [ ] (A) Coerência c_v por tópico.
- [ ] (B) Parágrafo do BERTopic.

## Etapa 4: Inspeção dos tópicos

- [ ] (A) Outliers (−1) removidos e N registrado.
- [ ] (A) Clusters < 15 removidos, com n e c_v média.
- [ ] (A) Planilha de triagem com decisão e motivo.
- [ ] Definir as categorias de exclusão conforme a pergunta de pesquisa.
- [ ] (A) Revisão por um segundo pesquisador e concordância.
- [ ] (A) Funil fechando até N5.
- [ ] (B) Parágrafo e tabela do funil.

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
