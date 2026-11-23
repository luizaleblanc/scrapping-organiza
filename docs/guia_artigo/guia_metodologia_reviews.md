<!-- Guia recebido em 23/11/2026. É a referência metodológica e não deve ser editado. O progresso fica em docs/checklist_artigo.md. -->

# Guia de instruções: análise de avaliações de apps (da Fase 3 em diante)

Baseado em Alsebayel et al. (2025), *"An Ad Posing as Medical Advice": User Accounts of Dark UX in FemTech mHealth Apps* (Proc. ACM HCI, 9(5), MHCI003, seção 3.2). https://doi.org/10.1145/3743736

Cada etapa tem duas trilhas: **(A) Análise de dados**, com o que fazer, e **(B) Redação do artigo**, com o que escrever na metodologia.

## 0. Tabela de funil

| Etapa | N antes | Removidos | N depois |
|---|---|---|---|
| Coleta bruta | – | – | [N0] |
| Pré-processamento | [N0] | [x] | [N1] |
| Filtro de sentimento + estrelas | [N1] | [x] | [N2] |
| Outliers do BERTopic | [N2] | [x] | [N3] |
| Clusters pequenos | [N3] | [x] | [N4] |
| Exclusões temáticas | [N4] | [x] | [N5] |

Referência do artigo original: 600.355 → 400 mil+ → 26.371 → 4.697 (26.371 − 10.968 − 547 − 8.200 − 805 − 459 − 470 − 225 = 4.697).

## Etapa 1: Pré-processamento

**(A)**
1. Manter o dado bruto intacto e trabalhar em uma cópia.
2. Remover avaliações com 3 ou menos unidades de texto, definindo o que é "unidade" (palavra ou token).
3. Converter para minúsculas.
4. Não remover stopwords nem fazer stemming antes do BERTopic.
5. Remover duplicatas exatas e textos vazios.
6. Mascarar apps (`A1…An`) e remover nomes de usuário e imagens.
7. Registrar o N antes e depois de cada passo.

**(B)** "Inicialmente, foram coletadas [N0] avaliações de [n] aplicativos. Removemos [x] avaliações com três ou menos palavras e [y] duplicatas, convertemos o texto para minúsculas e mascaramos os nomes e identificadores dos aplicativos. Restaram [N1] avaliações." Declarar a anonimização e a verificação dos Termos de Serviço.

## Etapa 2: Sentimento e filtro de criticidade

**(A)**
1. Usar uma ferramenta adequada ao idioma (VADER para inglês, LeIA para português ou um modelo multilíngue) e justificar a escolha.
2. Declarar o limiar (VADER: ≥ 0,05 positivo; ≤ −0,05 negativo; entre os dois, neutro).
3. Calcular a distribuição geral e por app.
4. Declarar a regra do filtro e dizer se é interseção ou união.
5. Contar quantas avaliações o filtro só por estrelas reteria e quantas restam com o filtro combinado.
6. Fazer uma checagem manual de amostra (por exemplo, 100 avaliações) e reportar a taxa de erro.

**(B)** "Aplicamos [ferramenta], que classificou [x]% como positivas, [y]% como neutras e [z]% como negativas (limiares: ...). Mantivemos as avaliações de sentimento negativo ou neutro **e** nota ≤ 3. O filtro só por estrelas resultaria em [a]; a combinação resultou em [N2] *avaliações críticas*." Limitação: relatos relevantes podem ter sido excluídos por discrepância entre sentimento e nota.

## Etapa 3: BERTopic

**(A)**
1. Usar as [N2] avaliações críticas.
2. Usar embeddings multilíngues (por exemplo, `paraphrase-multilingual-MiniLM-L12-v2`).
3. Fixar `random_state` no UMAP.
4. Deixar o HDBSCAN definir o número de tópicos.
5. Registrar todos os hiperparâmetros e a versão do BERTopic.
6. Exportar o material suplementar: tópicos, tamanhos, palavras-chave, 3 a 5 avaliações representativas, mapa intertópicos e matriz de similaridade.
7. Calcular a coerência c_v por tópico.

**(B)** "Utilizamos o BERTopic [cit.] com o modelo [X], UMAP e HDBSCAN. O número de tópicos não foi pré-definido. Parâmetros: [...] (semente = 42). O modelo identificou [T] tópicos a partir de [N2] avaliações."

## Etapa 4: Inspeção manual dos tópicos

**(A)**
1. Remover o tópico −1 (outliers) e registrar o n. `reduce_outliers` é opcional e precisa de justificativa.
2. Remover os clusters com menos de 15 avaliações e reportar quantos clusters, quantas avaliações e a c_v média.
3. Fazer a triagem em planilha com as colunas: ID, n, palavras-chave, 3 avaliações representativas, decisão e motivo.
4. Definir as categorias de exclusão conforme a pergunta de pesquisa (por exemplo: usabilidade e pedidos de funcionalidade, não informativas, outros idiomas, fora de escopo, ódio e assédio).
5. Inspecionar o mapa e a matriz para decidir sobre fusões.
6. Pedir a um segundo pesquisador que revise uma amostra e calcular a concordância.
7. Conferir a aritmética do funil.

**(B)** "Removemos [x] outliers e [n] clusters com menos de 15 avaliações (total [y]; c_v média = [z]). Os [m] tópicos restantes foram avaliados [...]. Foram excluídos [categoria] (n = [a]), [...]. O corpus final foi de [N5] avaliações."

## Etapa 5: Análise temática reflexiva

**(A)**
1. Definir o referencial dedutivo antes de codificar.
2. Exportar o corpus com o ID do tópico e o ID da avaliação.
3. Seguir as fases de Braun e Clarke: familiarização; códigos iniciais (indutivos); codificação dedutiva; revisão de temas; nomeação.
4. Consolidar os temas em equipe até o consenso.
5. Montar a tabela com tema, códigos, n, % e exemplo.
6. Identificar as citações por `[T_ID, R_ID]`, editando só capitalização e pontuação.
7. Se houver uma única pessoa codificando, justificar.

**(B)** "Das [N5] avaliações, realizamos análise temática reflexiva [Braun & Clarke] [...]. Do total, [k] ([p]%) foram mapeadas ao referencial."

## Etapa 6: Resultados e limitações

**(A)** Calcular a prevalência de temas por app, a frequência de códigos por tema e o sentimento geral como contexto.

**(B)** Abrir com o sentimento geral e o tamanho do corpus crítico. Para cada tema, apresentar definição, categorias, frequências e 1 a 3 citações. Deixar claro que se trata de percepções dos usuários. Declarar as limitações: plataforma, filtro de sentimento, BERTopic deixando de captar relatos raros, ausência de dados demográficos e codificação feita por uma única pessoa (se for o caso).

## Checklist de reprodutibilidade

- Funil fechando, com semente e hiperparâmetros registrados.
- Regra do filtro e limiar declarados, com ferramenta adequada ao idioma.
- Planilha de triagem com os motivos de exclusão.
- Material suplementar.
- Termos de Serviço e anonimização descritos.
- Checagem manual de amostra reportada.
