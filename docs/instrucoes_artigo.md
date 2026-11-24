# Instruções e documentação metodológica para o artigo (Etapa 0 / Fases 1–2 e Etapa 1)

Atualizado em 23/11/2026. Este documento consolida tudo o que foi executado no código e redigido em LaTeX para a **Etapa 0 (Fases 1 e 2)** (busca, triagem, pareamento, coleta, anonimização, redação e Termos de Serviço) e a **Etapa 1** (pré-processamento), servindo de referência auditável para continuar a escrita e fechar o manuscrito.

> **Referências de base**
> - Guia metodológico (fixo, não editar): [guia_metodologia_reviews.md](guia_artigo/guia_metodologia_reviews.md)
> - Checklist de progresso: [checklist_artigo.md](checklist_artigo.md)
> - Texto LaTeX em produção: [artigo/secoes/metodologia.tex](../artigo/secoes/metodologia.tex) e [artigo/referencias.bib](../artigo/referencias.bib)
> - Fonte única de números: `outputs/funnel_metrics*.json`

---

## 1. Convenções de escrita (baseadas no artigo-base)

Para manter unidade estilística com o artigo-base (*Padrões Enganosos em Aplicativos de Finanças Pessoais: Uma Análise de Avaliações de Usuários*), siga estas convenções ao expandir ou revisar qualquer seção em `artigo/`:

1. **Tom e voz:** português acadêmico formal, objetivo e conciso (estilo SBC). Alternar primeira pessoa do plural nas decisões metodológicas (*definimos*, *coletamos*, *retemos*, *adotamos*) com construções impessoais na descrição de procedimentos (*são registrados*, *são removidas*). Evitar adjetivos valorativos e transições longas.
2. **Estrutura interna das subseções:** abrir blocos temáticos com cabeçalhos em negrito inline (`\textbf{Strings de busca.}`, `\textbf{Critérios de elegibilidade.}`, `\textbf{Coleta das avaliações.}`), usar listas numeradas `(1)`–`(6)` para critérios e tabelas com `booktabs` (`\toprule`, `\midrule`, `\bottomrule`).
3. **Citações e notas de rodapé:** usar `biblatex` com estilo `authoryear` (`\textcite{...}` para citação narrativa e `\parencite{...}` para parênteses). URLs de bibliotecas, APIs e modelos vão em `\footnote{\url{...}}`. Toda referência, número e afirmação deve ser conferida nas fontes originais antes da submissão.
4. **Formatação numérica (pt-BR):** separador de milhar com ponto (`223.688`), separador decimal com vírgula (`0{,}05` no modo matemático; `68{,}5\%`). Nunca inventar números: todo dado vem de `outputs/funnel_metrics*.json`; valores ainda não gerados ficam como `[N]` acompanhados de `% TODO`.
5. **Privacidade e anonimização absoluta:** jamais incluir nomes de pessoas, nomes comerciais de aplicativos da amostra, `appId`, `trackId`, `bundleId` ou nomes de desenvolvedores em `artigo/` ou `data/publico/`. Usar somente máscaras `APP_xxx` e parafrasear qualquer trecho citado no artigo.

---

## 2. Fases 1 e 2 — Busca, triagem, coleta, privacidade e Termos de Serviço

### 2.1. O que foi executado e onde está no código

| Etapa | Scripts | Métricas (`outputs/funnel_metrics*.json`) | Texto no artigo |
|---|---|---|---|
| Busca nas duas lojas (S1–S6, top 30) | `src/01_search_google_play.py`, `src/02_search_app_store.py`, `src/config.py` | `01_google_play_search`, `02_app_store_search` | `artigo/secoes/metodologia.tex` (`\subsection{Seleção dos aplicativos e coleta}`, Tabela `tab:strings`) |
| Deduplicação intraloja e triagem em cascata | `src/03_clean_stores.py`, `src/rules.py`, `src/text_norm.py` | `03_clean_google_play_store`, `03_clean_app_store` | `\subsection{Seleção dos aplicativos e coleta}` (critérios `(1)`–`(6)`) |
| Verificação cruzada de disponibilidade | `src/03b_check_other_store.py` | `03b_availability_check` | `\subsection{Seleção dos aplicativos e coleta}` |
| Pareamento 1:1 entre lojas e validação internacional | `src/04_cross_store_dedup.py`, `src/09b_build_market_samples.py` | `04_cross_store`, `09b_amostras_outros_idiomas`, `10_pastas_por_pais` | `\subsection{Seleção dos aplicativos e coleta}` (Tabela `tab:coleta`) |
| Coleta de avaliações (Google Play + App Store) | `src/05_scrape_google_play_reviews.py`, `src/05b_scrape_app_store_reviews.py` | `05_reviews`, `05b_app_store_reviews` | `\subsection{Seleção dos aplicativos e coleta}` (Tabela `tab:coleta`) |
| Mascaramento `APP_xxx`, redação e verificação contra vazamentos | `src/05_*.py`, `src/07_build_ai_share.py`, `src/review_redaction.py`, `src/08b_build_public_criticas.py` | `05_reviews.redactions_this_run`, `05b_app_store_reviews.redactions`, `07_ai_share` | `\subsection{Seleção dos aplicativos e coleta}` (*Anonimização, mascaramento e redação de dados*) |
| Termos de Serviço e ética | Protocolo + revisão pendente | — | `\subsection{Seleção dos aplicativos e coleta}` (*Termos de serviço e considerações éticas*, com `% TODO`) |

### 2.2. Strings de busca (S1–S6)

Buscas executadas em **22/11/2026** (corte de recência de 12 meses: **22/11/2025**), individualmente, sem consultas por marca, limitadas aos **30 primeiros resultados** por termo em cada loja:

| ID | Brasil (`pt`) | Estados Unidos (`en`) | Espanha e México (`es`) |
|---|---|---|---|
| S1 | `finanças` | `finance` | `finanzas` |
| S2 | `organizador de finanças` | `finance organizer` | `organizador de finanzas` |
| S3 | `educador de finanças` | `finance educator` | `educador de finanzas` |
| S4 | `aplicativos financeiros` | `financial apps` | `aplicaciones financieras` |
| S5 | `ia para finanças` | `ai for finance` | `ia para finanzas` |
| S6 | `organizador financeiro com ia` | `ai financial organizer` | `organizador financiero con ia` |

### 2.3. Critérios de elegibilidade e motivos de exclusão

A triagem (`src/rules.py`) aplica regras em cascata (a primeira falha registra o motivo):

1. **Conflito de interesse:** exclui o aplicativo em desenvolvimento no contexto aplicado da pesquisa (`0` removidos).
2. **Categoria:** aceita `Finanças` (`Finance` / `Finanzas`) e, na categoria `Educação` (`Education` / `Educación`), apenas aplicativos cujo título ou desenvolvedor indiquem explicitamente educação financeira (excluídos cursos/simulados de certificação profissional e *trading*). Produtividade, jogos e outras categorias são excluídos (`224` removidos no total: `180` outras categorias + `44` produtividade/jogos).
3. **Escopo funcional direto ao consumidor:** exclui, via listas auditáveis em `src/config.py` (ampliadas com equivalentes em inglês e espanhol fora do Brasil), bancos/contas digitais/maquininhas (`108`), carteiras digitais/pagamentos/remessas (`55`), *trading*/cripto/corretoras/investimentos (`127`), ferramentas B2B/contabilidade/crédito (`48`) e sinais na descrição oficial (`9`).
4. **Avaliações:** exige ao menos uma avaliação registrada (`93` removidos sem avaliações).
5. **Recência:** exige data de atualização válida nos últimos 12 meses (`0` sem data; `23` desatualizados).
6. **Disponibilidade nas duas lojas:** exige presença tanto na Google Play quanto na App Store no mesmo mercado. Aplicativos elegíveis em apenas uma loja são checados na loja complementar (`src/03b_check_other_store.py`) e submetidos às mesmas regras. O pareamento 1:1 (`src/04_cross_store_dedup.py`) segue quatro camadas (`exact`, `exact_title`, `normalized_brand`, `fuzzy_review` com aprovação humana obrigatória; `0` pares pendentes).

Total de exclusões intraloja: **687** (`290` Google Play + `397` App Store). Na validação manual dos mercados internacionais (`src/09b_build_market_samples.py`), foram removidos **4** aplicativos fora do escopo (`1` EUA, `1` Espanha, `2` México).

### 2.4. Funil verificado de busca, triagem e coleta bruta ($N_0$)

| Mercado (idioma) | Ocorr. GP / AS | Únicos GP / AS | Elegíveis GP (busca + check) | Elegíveis AS (busca + check) | Pares 2 lojas | Amostra final | Aval. GP ($N_0$) | Aval. AS ($N_0$) | Total ($N_0$) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Brasil (`pt`) | 180 / 170 | 98 / 147 | 58 (51 + 7) | 64 (46 + 18) | 40 | 40 | 223.688 | 5.467 | 229.155 |
| Estados Unidos (`en`) | 163 / 165 | 115 / 138 | 36 (25 + 11) | 42 (35 + 7) | 25 | 24 | 23.638 | 6.664 | 30.302 |
| Espanha (`es`) | 145 / 138 | 101 / 123 | 24 (24 + 0) | 35 (28 + 7) | 12 | 11 | 7.441 | 901 | 8.342 |
| México (`es`) | 144 / 141 | 106 / 122 | 34 (30 + 4) | 29 (24 + 5) | 16 | 14 | 7.911 | 2.336 | 10.247 |
| **Total** | **632 / 614** | **—** | **—** | **—** | **93** | **89** (67 distintos; 12 em >1 mercado) | **262.678** | **15.368** | **278.046** |

**Regras de coleta e limitações inerentes à fonte:**
- **Google Play (`google-play-scraper`, `Sort.NEWEST`):** no Brasil, todo o histórico acessível (`max_per_app = all`); fora do Brasil (EUA, Espanha, México), apenas notas de 1 a 3 estrelas filtradas na origem, limitadas a até 1.000 avaliações por nota e por aplicativo (máximo de 3.000 por aplicativo).
- **App Store (Apple RSS público `customerreviews`, `sortby=mostrecent`):** mantida como fonte por decisão das autoras (divergindo de Alsebayel et al., 2025), limitada tecnicamente a 10 páginas $\times$ 50 = até **500 avaliações mais recentes** por aplicativo, concatenando título e corpo.
- **Geografia em espanhol:** as lojas de Espanha e México podem retornar avaliações em espanhol oriundas de outros países; analisar sempre por mercado de coleta e idioma, sem inferir residência do avaliador.

### 2.5. Anonimização, mascaramento e redação de dados

- **Ingestão (`src/05`, `src/05b`):** política de *allowlist* retém apenas `app_mask_id`, `content`, `score`, `lang` e `at` (descartando nome do autor, foto, link e identificador da avaliação).
- **Mascaramento (`APP_xxx`):** sorteio criptograficamente aleatório (`secrets.SystemRandom`), nunca alfabético; mesma máscara reaproveitada entre lojas e países; chave armazenada exclusivamente em `data/chave_apps_mascarados_NAO_COMPARTILHAR/` (fora do git).
- **Redação camada 1 — regras determinísticas (`src/review_redaction.py`):** substitui `[EMAIL]`, `[URL]`, `[CPF]`, `[PHONE]`, `[POSSIBLE_PHONE_OR_NUMBER]`, `[HANDLE]` e nomes autodeclarados (`[NOME]`).
- **Redação camada 2 — marcas e NER (`src/07_build_ai_share.py`, `src/review_redaction.py`):** regex insensível a caixa/acentos troca marcas dos apps da amostra por `[APP]` (excluindo palavras genéricas de uso cotidiano); modelo multilíngue `Davlan/bert-base-multilingual-cased-ner-hrl` (limiar $\ge 0{,}6$, expansão para palavra inteira, blocos de até 800 caracteres) troca pessoas (`[NOME]`), outras empresas (`[MARCA]`) e lugares (`[LOCAL]`); datas truncadas ao dia (`AAAA-MM-DD`).
- **Trava contra vazamentos (`src/08b_build_public_criticas.py`):** bloqueia a geração de `data/publico/` se detectar marcas residuais, e-mail, URL, `@`, telefone, CPF ou hora na data.
- **Publicação do artigo:** trechos citados no texto devem ser parafraseados para evitar busca reversa.

### 2.6. Termos de Serviço (pendência com a orientação)

- Declarado em `artigo/secoes/metodologia.tex` com base em Krotov et al. (2020) e Alsebayel et al. (2025).
- **Pendência aberta (`% TODO` no LaTeX):** confirmar com a orientação (i) a verificação formal dos Termos de Serviço da Google Play Store e (ii) se o uso do *feed* RSS público da Apple App Store permanece autorizado ou se exige ajuste frente aos Termos e Condições da Apple. Quando confirmado, atualizar o parágrafo e trocar `[~]` por `[x]` em `docs/checklist_artigo.md`.

---

## 3. Etapa 1 — Pré-processamento

### 3.1. Decisões metodológicas e implementação

Implementada em **`src/06_filter_sentiment.py`** (função `preprocess(df)`), com parâmetros centralizados em **`src/config.py`** (`MIN_WORDS = 3`, `SEED = 42`) e validada por testes unitários em **`tests/test_review_rules.py`**:

1. **Ordem no pipeline (decisão fechada):** o pré-processamento executa **antes** da análise de sentimento e do filtro por estrelas, alinhado ao [guia metodológico](guia_artigo/guia_metodologia_reviews.md) e ao funil $N_0 \to N_1 \to N_2$.
   - *Detalhe técnico importante:* a classificação de sentimento (LeIA / VADER / `pysentimiento`) continua recebendo o texto **original** (`content`) das avaliações sobreviventes a $N_1$, pois LeIA e VADER utilizam letras maiúsculas como intensificadores de polaridade; já a deduplicação exata e as etapas subsequentes (BERTopic) utilizam o texto normalizado em minúsculas (`content_clean`).
2. **Preservação do dado bruto:** `reviews_anonymized.csv` permanece intacto; todo o pré-processamento opera sobre cópia em memória.
3. **Remoção de textos vazios:** descartam-se avaliações cujo texto, após remoção de espaços nas extremidades (`strip()`), fica vazio (`removed_empty`).
4. **Definição de "unidade" e corte de extensão:** define-se **unidade textual** como **palavra separada por espaços em branco** (`str.split()`). Avaliações com **3 ou menos palavras** ($\le 3$, `MIN_WORDS = 3`) são removidas (`removed_short_le_3_words`), mantendo-se apenas relatos com 4 ou mais palavras.
5. **Normalização sem destruição lexical:** gera-se `content_clean` convertendo o texto para minúsculas e colapsando espaços múltiplos em espaço simples (`str.lower().str.split().str.join(" ")`), **sem remoção de *stopwords* e sem *stemming***, preservando o contexto semântico necessário para os *embeddings* do BERTopic.
6. **Remoção de duplicatas exatas:** dentro de cada loja e mercado, ordenam-se os registros cronologicamente (`sort_values("at")`) e removem-se duplicatas exatas em `content_clean`, mantendo-se a ocorrência mais antiga (`keep="first"`) (`removed_exact_duplicates`).
7. **Registro auditável do funil ($N_0 \to N_1$):** cada execução grava `n0_collected`, `removed_empty`, `removed_short_le_3_words`, `removed_exact_duplicates` e `n1_after_preprocessing` em `outputs/funnel_metrics*.json` sob `06_sentiment_google_play.preprocessing` e `06_sentiment_app_store.preprocessing`.

### 3.2. Contagens finais do pré-processamento ($N_0 \to N_1$)

Todos os quatro mercados consolidados em `outputs/funnel_metrics*.json`:

| Mercado / Loja | Coleta bruta ($N_0$) | Vazias | Curtas ($\le 3$ pal.) | Duplicatas exatas | Após pré-proc. ($N_1$) |
|---|---:|---:|---:|---:|---:|
| Brasil — Google Play | 223.688 | 158 | 67.507 | 5.739 | 150.284 |
| Brasil — App Store | 5.467 | 0 | 315 | 16 | 5.136 |
| **Subtotal Brasil** | **229.155** | **158** | **67.822** | **5.755** | **155.420** |
| EUA — Google Play | 23.638 | 2 | 1.664 | 20 | 21.952 |
| EUA — App Store | 6.664 | 0 | 212 | 1 | 6.451 |
| **Subtotal EUA** | **30.302** | **2** | **1.876** | **21** | **28.403** |
| Espanha — Google Play | 7.441 | 5 | 556 | 4 | 6.876 |
| Espanha — App Store | 901 | 0 | 33 | 2 | 866 |
| **Subtotal Espanha** | **8.342** | **5** | **589** | **6** | **7.742** |
| México — Google Play | 7.911 | 5 | 575 | 4 | 7.327 |
| México — App Store | 2.336 | 0 | 137 | 4 | 2.195 |
| **Subtotal México** | **10.247** | **5** | **712** | **8** | **9.522** |
| **Total geral** | **278.046** | **170** | **70.999** | **5.790** | **201.087** |

### 3.3. Contagens finais da Etapa 2 — Sentimento e filtro de criticidade ($N_1 \to N_2$)

Geradas na mesma execução de `src/06_filter_sentiment.py` (regra de interseção: nota $\le 3$ **e** sentimento negativo ou neutro; LeIA em `pt`, VADER em `en`, `pysentimiento` em `es`):

| Mercado / Loja | $N_1$ | Pos. (%) | Neu. (%) | Neg. (%) | Só estrelas ($\le 3$) | Rem. nota $> 3$ | Rem. pos. | Críticas ($N_2$) | Amostra checagem (`seed=42`) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Brasil — GP | 150.284 | 68,50% (102.945) | 10,52% (15.804) | 20,98% (31.535) | 31.507 | 118.777 | 9.191 | **22.316** | 100 críticas + 100 pos. |
| Brasil — AS | 5.136 | 50,31% (2.584) | 7,50% (385) | 42,19% (2.167) | 2.595 | 2.541 | 575 | **2.020** | 100 críticas + 100 pos. |
| EUA — GP\* | 21.952 | 44,48% (9.764) | 18,43% (4.046) | 37,09% (8.142) | 21.952 | 0 | 9.764 | **12.188** | 100 críticas + 100 pos. |
| EUA — AS | 6.451 | 71,48% (4.611) | 7,81% (504) | 20,71% (1.336) | 2.574 | 3.877 | 1.176 | **1.398** | 100 críticas + 100 pos. |
| Espanha — GP\* | 6.876 | 8,30% (571) | 25,12% (1.727) | 66,58% (4.578) | 6.876 | 0 | 571 | **6.305** | 100 críticas + 100 pos. |
| Espanha — AS | 866 | 55,77% (483) | 11,43% (99) | 32,79% (284) | 299 | 567 | 17 | **282** | 100 críticas + 17 pos. |
| México — GP\* | 7.327 | 8,08% (592) | 25,07% (1.837) | 66,85% (4.898) | 7.327 | 0 | 592 | **6.735** | 100 críticas + 100 pos. |
| México — AS | 2.195 | 62,60% (1.374) | 11,75% (258) | 25,65% (563) | 545 | 1.650 | 26 | **519** | 100 críticas + 26 pos. |
| **Total geral** | **201.087** | **—** | **—** | **—** | **73.675** | **127.412** | **21.912** | **51.763** | **—** |

\*Nos mercados internacionais, a Google Play foi coletada apenas para notas de 1 a 3 estrelas (`removed_by_score_gt_3 = 0`). Além disso, observou-se na execução que `mx/google_play` compartilha grande parte das avaliações em espanhol já presentes em `es/google_play` (apenas 456 textos únicos novos em `mx/google_play` além dos 6.876 de `es/google_play`); considerar deduplicação entre ES e MX caso o BERTopic seja rodado por idioma (`es`).

---

## 4. Próximos passos imediatos (para continuidade do artigo)

1. **Obrigatório antes do BERTopic (Passo 0 de `prompt_codex.md`):** como `src/06_filter_sentiment.py` agora aplica o pré-processamento antes do filtro de criticidade, reexecutar `src/07_build_ai_share.py` (para `br`, `us`, `es` e `mx`) e em seguida `python src/08b_build_public_criticas.py` (sem `MARKET`), atualizando as cópias redigidas (`reviews_critical_redacted.csv`) e `data/publico/` com o novo $N_2$ (`51.763` avaliações críticas no total).
2. **Checagem manual de sentimento (Etapa 2):** preencher a coluna `e_critica_de_fato (s/n)` nos arquivos `checagem_manual_sentimento.csv` (`seed=42`, já gerados para todos os 4 mercados e 2 lojas), calcular a taxa de erro e substituir `[N]\%` na subseção *Análise de sentimento e filtro de criticidade* em `artigo/secoes/metodologia.tex`.
3. **Etapa 3 (BERTopic):** seguir `docs/guia_artigo/prompt_codex.md`, lembrando de verificar a sobreposição entre Espanha e México na Google Play ao consolidar o corpus em espanhol (`es`).
4. **Pendências de orientação:** confirmar a verificação formal dos Termos de Serviço (Google Play e Apple RSS) e fechar as decisões em aberto da Etapa 3 (modelagem por idioma vs. conjunta) e Etapa 5 (referencial dedutivo).
