# Prompt para o Codex: Etapas 3 e 4 (BERTopic e preparação da inspeção dos tópicos)

Copie o bloco abaixo e cole no Codex.

---

Você vai continuar a análise de dados de um artigo científico neste repositório. As Etapas 1 e 2 (pré-processamento e filtro de sentimento) já foram feitas. Sua parte são a **Etapa 3 (BERTopic)** e a **preparação da Etapa 4 (inspeção manual dos tópicos)**.

## Leia antes de começar
1. `CLAUDE.md`: as regras do projeto valem para você também.
2. `docs/guia_artigo/guia_metodologia_reviews.md`: a metodologia. Siga as seções "Etapa 3" e "Etapa 4". **Não edite este arquivo.**
3. `docs/checklist_artigo.md`: o que já foi feito e o que falta. Marque os itens que concluir.
4. `docs/pipeline_explicativo.md`: como os dados são organizados (mercados, lojas, máscaras).
5. `src/06_filter_sentiment.py`, `src/07_build_ai_share.py` e `src/config.py`: para seguir o mesmo estilo de código e de caminhos (`C.PATHS`, `MARKET`, `update_metrics`, `write_csv`).

## Regras obrigatórias
- **Nunca rode `git commit` nem `git push`.** Ao final, só sugira as mensagens de commit.
- **Use apenas as cópias redigidas** (`C.PATHS["ai_critical"]` e `C.PATHS["ai_as_critical"]`, geradas pelo `src/07`), nunca `reviews_critical.csv`, que ainda tem nomes sem censura.
- Nunca coloque nomes de pessoas, nomes reais de apps, `appId` ou a chave em `data/chave_apps_mascarados_NAO_COMPARTILHAR/` em `artigo/`, `data/publico/` ou qualquer saída. Use só as máscaras `APP_xxx`.
- Nunca invente números. Os números do LaTeX vêm de `outputs/`; o que não existir fica como `[N]` com um `% TODO`.

## Passo 0: atualizar as cópias redigidas
O `src/06` foi alterado (agora faz o pré-processamento), então as cópias redigidas estão desatualizadas. Rode o `src/07` para cada mercado:
```
MARKET=br python src/07_build_ai_share.py   (repita com us, es e mx)
```
Depois rode `python src/08b_build_public_criticas.py`, sem `MARKET`, para atualizar `data/publico/`.

## Tarefa (A): criar `src/11_bertopic.py`
1. **Entrada:** as cópias redigidas das duas lojas, juntas. Elas têm `app_mask_id`, `content`, `score`, `lang`, `at` e `compound`; acrescente `store` (pelo arquivo de origem) e `market` (pelo `MARKET`). Crie um `review_id` estável (por exemplo, `R00001`, em ordem de mercado, loja, app e data).
2. **Texto:** use `content` em minúsculas, sem remover stopwords e sem stemming. Retire do texto os marcadores de censura (`[NOME]`, `[APP]`, `[MARCA]`, `[LOCAL]` etc.) só para o embedding, para que eles não virem tópicos.
3. **Modelagem:** uma modelagem **separada por idioma** (pt, en, es), como padrão. Deixe uma opção `--juntos` para modelar tudo junto. Essa decisão ainda está em aberto no checklist, então registre o que foi usado.
4. **Modelo:**
   - embeddings `paraphrase-multilingual-MiniLM-L12-v2`;
   - `UMAP(n_neighbors=15, n_components=5, min_dist=0.0, metric="cosine", random_state=42)`;
   - `HDBSCAN(min_cluster_size=15, metric="euclidean", prediction_data=True)`;
   - número de tópicos automático;
   - `CountVectorizer` com stopwords do idioma **só na representação das palavras-chave**, não no embedding.
5. **Salvar em `data/<mercado ou idioma>/topicos/`** (pasta privada, não pública):
   - `review_topics.csv`: `review_id`, as colunas preservadas, `topic` e `probability`;
   - `topic_info.csv`: tópico, n, 10 palavras-chave, c_v;
   - `representative_docs.csv`: 5 avaliações representativas por tópico;
   - `intertopic_map.html` e `similarity_matrix.html` (`visualize_topics`, `visualize_heatmap`).
6. **Coerência c_v por tópico** com `gensim` (`CoherenceModel`, `coherence="c_v"`), usando as 10 palavras-chave.
7. **Métricas:** `update_metrics("11_bertopic_<idioma>", {...})` com: N de entrada, nº de tópicos, n de outliers (tópico −1), clusters com menos de 15 avaliações (quantos e com quantas avaliações), c_v média, todos os hiperparâmetros, a semente e as versões de `bertopic`, `umap-learn`, `hdbscan` e `sentence-transformers`.
8. Inclua as dependências novas no `requirements.txt`.

## Tarefa (A): preparar a Etapa 4
Crie `data/<...>/topicos/triagem_topicos.csv`, excluindo o tópico −1, com as colunas: `topic`, `n`, `palavras_chave`, `exemplo_1`, `exemplo_2`, `exemplo_3`, `c_v`, `decisao` (vazia), `categoria_exclusao` (vazia), `motivo` (vazio).
**Não preencha decisões.** A triagem é humana, e as categorias de exclusão ainda não foram definidas pelas autoras.

## Tarefa (B): texto em LaTeX
Em `artigo/secoes/metodologia.tex`, preencha a subseção `Modelagem de tópicos` seguindo o modelo "(B)" da Etapa 3 do guia, com os números de `outputs/`. Na subseção `Inspeção manual dos tópicos`, escreva só o que já se sabe (outliers e clusters pequenos). As exclusões temáticas ficam como `[N]` e `% TODO`. Adicione a referência do BERTopic (Grootendorst, 2022, arXiv:2203.05794) em `artigo/referencias.bib`.

## Ao terminar
1. Rode `python -m pytest tests` e informe o resultado.
2. Marque no `docs/checklist_artigo.md` o que foi feito (`[x]`) ou feito em parte (`[~]`), citando o script ou o arquivo.
3. Responda com: o que foi feito, os números principais (tópicos por idioma, outliers, c_v média), o que não foi feito e por quê, e uma mensagem de commit atômico para cada item concluído.
