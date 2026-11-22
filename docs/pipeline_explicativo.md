# Pipeline de coleta e triagem — Padrões Enganosos em Apps de Finanças Pessoais

Atualizado em 22/11/2026.

## Resumo

A amostra final tem **40 aplicativos de finanças pessoais e educação financeira presentes nas duas lojas** (Google Play e App Store, Brasil). Eles foram encontrados com 6 strings de busca e triados pelos critérios do artigo. Desses apps foram coletadas **223.688 avaliações da Google Play**, das quais 19.454 ficaram como críticas após o filtro de nota e sentimento. Da App Store vieram **5.467 avaliações** pelo feed público da Apple (até 500 por app), das quais 1.834 ficaram como críticas.

Este pipeline substitui uma rodada anterior, que usava outros termos de busca, trazia bancos, carteiras digitais, jogos e apps de produtividade, e cobria 38 apps. A rodada anterior foi retirada do repositório; o repositório contém só o que vem das 6 strings.

Em 22/11/2026 o protocolo mudou: a App Store, antes usada só para busca e triagem, passou a ser também fonte de avaliações. O texto do artigo precisa acompanhar essa mudança (última seção).

## Strings de busca e critérios

Só estas 6 strings foram buscadas, nas duas lojas, loja Brasil, top 30 resultados cada. Nenhuma busca por nome de marca ou lista de candidatos entra na amostra.

| ID | String |
| --- | --- |
| S1 | finanças |
| S2 | organizador de finanças |
| S3 | educador de finanças |
| S4 | aplicativos financeiros |
| S5 | ia para finanças |
| S6 | organizador financeiro com ia |

Os critérios são aplicados em cascata, com as mesmas regras nas duas lojas. O primeiro critério que falha define o motivo registrado.

| Ordem | Regra | Motivo registrado |
| --- | --- | --- |
| 1 | Organiza AI fora da amostra (conflito de interesse) | `conflict_of_interest_organiza_ai` |
| 2 | Categoria Finance/Finanças; Educação só se título ou desenvolvedor indicarem educação financeira | `wrong_category_productivity_or_game`, `wrong_category_other` |
| 3 | Sem bancos, contas digitais e maquininhas | `excluded_bank_or_card_machine` |
| 4 | Sem carteiras e meios de pagamento ("pix" e "pagamento" só no título) | `excluded_wallet_payment` |
| 5 | Sem trading, ações, cripto, corretoras e investimentos | `excluded_trading_crypto_investment` |
| 6 | Sem ferramentas empresariais, crédito e empréstimo | `excluded_b2b_accounting_credit` |
| 7 | Descrição oficial sem sinais de conta digital, maquininha ou plataforma de trading | `excluded_by_official_description` |
| 8 | Pelo menos uma avaliação (critério 3) | `no_ratings` |
| 9 | Atualizado nos últimos 12 meses (critério 6) | `outdated_over_12_months` |
| 10 | Disponível nas duas lojas (critério 4) | `excluded_single_store_criterion_4` |

As listas de termos ficam em `src/config.py` e podem ser auditadas e ajustadas. As palavras são comparadas inteiras, sem acento e em minúsculas, no título e no desenvolvedor.

## Pipeline passo a passo

São sete etapas, cada uma um script em `src/`. A saída de cada uma alimenta a seguinte.

1. **01 e 02 — Busca.** As 6 strings na Google Play e na App Store (Brasil, top 30). Saída: `search_hits.csv` de cada loja.
2. **03 — Limpeza.** Deduplica dentro de cada loja e aplica os critérios em cascata. Saída: `apps_eligible.csv` e `apps_excluded_audit.csv`, com o motivo de cada exclusão.
3. **03b — Disponibilidade.** Procura cada elegível pelo nome na outra loja. A versão encontrada passa pelas mesmas regras.
4. **04 — Cruzamento.** Pareia os apps das duas lojas em camadas: título e desenvolvedor, título, marca e, por último, revisão manual. Saída: `apps_both_stores.csv`.
5. **05 e 05b — Reviews.** Coleta e anonimiza as reviews da Google Play e da App Store, só dos apps da amostra.
6. **06 — Sentimento.** Mantém as reviews com nota até 3 e sentimento negativo ou neutro (LeIA, escore < 0,05), como no artigo.
7. **07 — Cópias para IA.** Grava as versões redigidas das críticas, com nomes de pessoas censurados, e confere as máscaras.

## Funil por etapa

Dos 98 apps únicos da Google Play e dos 147 da App Store, 40 chegam à amostra final, presentes nas duas lojas.

| Etapa | Google Play | App Store |
| --- | --- | --- |
| Ocorrências nas 6 strings | 180 | 170 |
| Apps únicos | 98 | 147 |
| Fora da categoria (inclui jogos e produtividade) | 7 | 43 |
| Bancos e maquininhas | 13 | 11 |
| Carteiras e pagamentos | 8 | 5 |
| Trading, cripto e investimentos | 6 | 12 |
| Empresariais e crédito | 0 | 4 |
| Descrição oficial (conta digital etc.) | 0 | 4 |
| Sem avaliações | 11 | 15 |
| Desatualizados (mais de 12 meses) | 2 | 7 |
| Elegíveis pelas strings | 51 | 46 |
| Acrescentados pela verificação de disponibilidade | 7 | 18 |
| Só em uma loja (critério 4) | 18 | 24 |
| **Amostra nas duas lojas** | **40** | **40** |

As contagens de cada etapa ficam em `outputs/funnel_metrics.json`.

## Amostra final: 40 apps nas duas lojas

São 35 apps da categoria Finanças e 5 de Educação com foco em educação financeira. Quatro pares foram confirmados por revisão manual: Fortuno, Cofrinho, Spendee e Gastos Diários. Os arquivos de análise usam as máscaras APP_001 a APP_040, sorteadas: a ordem não segue a lista abaixo, e a chave fica só na máquina da pesquisadora.

| App (título na Google Play) | Categoria |
| --- | --- |
| ALL: Controle de Gastos com IA | Finanças |
| Assistente Financeiro IA | Finanças |
| budgi: Finanças com IA | Finanças |
| Cofrinho - Tudo sobre dinheiro | Finanças |
| Cresce+ Controle Financeiro IA | Finanças |
| Desenrola Brasil 3.0 - Guia | Finanças |
| Despesas Finanças Pessoais | Finanças |
| Despezzas: gestão financeira | Finanças |
| Dinzo: Finanças Pessoais e IA | Finanças |
| duofi: dividir contas do casal | Finanças |
| EducaBolso Educação Financeira | Educação |
| Finclass - Aprenda a Investir | Educação |
| Fing: Finanças Pessoais | Finanças |
| Flynow - Finanças Pessoais | Finanças |
| Fortuno: Finanças Pessoais | Finanças |
| Ganhos e Gastos | Finanças |
| Gastos Diários 4 | Finanças |
| Kebo: Gestão Financeira | Finanças |
| Kontto: Finanças Pessoais | Finanças |
| Meus Gastos: Finanças Pessoais | Finanças |
| Minhas Contas e Despesas | Finanças |
| Minhas Economias | Finanças |
| Minhas Finanças: Controle e IA | Finanças |
| Mobills: Finanças Pessoais | Finanças |
| Monee - Finanças & Budget | Finanças |
| Monefy: Dinheiro e despesas | Finanças |
| Monely: Controle Financeiro | Finanças |
| Money Lover Controle de gastos | Finanças |
| Money Pro: Finanças Pessoais | Finanças |
| Oinc - Finanças Pessoais | Finanças |
| Organizze: Controle Financeiro | Finanças |
| Orçamento Fácil - Despesas | Finanças |
| Pierre: IA financeira pessoal | Finanças |
| S1NC: Planejamento Financeiro | Finanças |
| SIA - Educação Financeira | Educação |
| Spendee: Orçamento e Gastos | Finanças |
| Sumlio: Gastos e Orçamento | Finanças |
| Tangram Educação Financeira | Educação |
| Wallet - Finanças Pessoais | Finanças |
| Wealthy \| Finanças com IA | Finanças |

Um único app concentra 48% das reviews da Google Play. Na análise, vale ponderar por app ou relatar os resultados com e sem ele. A lista está em ordem alfabética e sem contagens por app de propósito: com elas, daria para descobrir qual máscara APP_xxx é qual app.

## Coleta de reviews, anonimização e sentimento

As reviews são coletadas só dos 40 apps da amostra; nenhum app excluído entra na coleta. As duas lojas usam a mesma máscara por app (APP_001 a APP_040), então os resultados podem ser comparados por app.

| | Google Play | App Store |
| --- | --- | --- |
| Fonte | biblioteca google-play-scraper | feed RSS público de avaliações da Apple |
| Alcance | todas as reviews disponíveis | até 500 mais recentes por app (limite do feed) |
| Reviews coletadas | 223.688 (40 apps) | 5.467 (38 apps com texto) |
| Com nota ≤ 3 | 33.954 | 2.616 |
| Críticas (nota ≤ 3 e sentimento negativo) | 19.454 | 1.834 |
| Apps no limite de 500 | não se aplica | 6 |
| Apps sem avaliação em texto | nenhum | 2 |

**Anonimização na ingestão.** Nome, foto e ID do avaliador nunca são gravados. Ficam só cinco colunas: app mascarado, texto, nota, idioma e data. No texto, e-mails, telefones, CPFs, URLs e @menções são substituídos por marcadores. No passo 7, qualquer nome de pessoa vira `[NOME]` (modelo de reconhecimento de entidades multilíngue, mais regras para "meu nome é…"). Na App Store, título e corpo da avaliação viram um só texto.

**Sentimento.** As reviews com nota até 3 passam pelo LeIA, adaptação do VADER para o português. Ficam só as negativas, com escore composto até −0,05. Saíram as de texto positivo ou neutro: 14.500 na Google Play e 782 na App Store.

**Cópias para IA.** O passo 7 grava cópias redigidas em `data/brasil/google_play_store/reviews_para_ia/` e `data/brasil/app_store/reviews_para_ia/` e confere que só as 40 máscaras da amostra estão presentes.

## Decisões, correções e problemas encontrados

A rodada anterior trazia ruído que violava os critérios do artigo. As correções abaixo foram feitas entre 20 e 22/11/2026 e estão no código.

| Problema ou decisão | O que foi feito |
| --- | --- |
| Busca antiga usava outros termos e buscas por nome de marca | Substituída pelas 6 strings aprovadas; nenhuma lista de candidatos protege app algum |
| Bancos, maquininhas, carteiras, trading e cripto na amostra | Listas de exclusão em `config.py`; checagem também na descrição oficial (pegou Elysium, Evaro, Merci e Conta Justa) |
| Jogos, produtividade, Book, News, Sports | Excluídos pela categoria (critério 2) |
| Apps de educação financeira na categoria Educação | Aceitos quando título ou desenvolvedor indicam educação financeira; a descrição não basta (deixava entrar Nibble e Economisto) |
| Falsos positivos (Oinc, Fortuno, Meu Assessor, Desenrola) | "pagamentos" e "pix" checados só no título; retirados "corretora de valores", "assessor" e "desenrola" |
| 14 apps da Google Play sem data de atualização | A biblioteca devolvia vazio; a data passou a ser lida do campo "Atualizado em" da página pública, com a origem registrada |
| Critério 4 exigia aparecer nas buscas das duas lojas | Passou a exigir disponibilidade: cada elegível é procurado pelo nome na outra loja, com mesma marca e mesmas regras (S1NC e Oinc entraram assim) |
| Primeiro resultado da busca da Google Play sem identificador | Identificador recuperado da página pública de busca |
| Pares parecidos entre lojas | 11 pares revisados à mão: 4 aceitos, 7 recusados |
| Feed da Apple devolve páginas vazias no meio | Página vazia é refeita até 3 vezes; rodar de novo só acrescenta, sem duplicatas |
| Rodada antiga (outras strings) | Retirada do repositório; todas as reviews foram coletadas de novo, só para os 40 apps |
| Protocolo: App Store só para triagem | Mudado em 22/11/2026: a App Store também é fonte de avaliações |

Uma auditoria independente, feita por um subagente, confirmou que as duas buscas usaram exatamente as 6 strings e que todo app elegível ou excluído veio delas, sem perdas nem duplicatas.

## Pastas e como rodar

Em `data/`, cada loja tem sua pasta com as mesmas três subpastas; a amostra comum fica em `apps_nas_duas_lojas/`.

| Pasta | Conteúdo |
| --- | --- |
| `data/brasil/google_play_store/busca_e_triagem/` | busca, elegíveis e excluídos com motivo |
| `data/brasil/google_play_store/reviews/` | reviews anonimizadas e críticas |
| `data/brasil/google_play_store/reviews_para_ia/` | cópias redigidas para uso com IA |
| `data/brasil/app_store/busca_e_triagem/` | busca, elegíveis e excluídos com motivo |
| `data/brasil/app_store/reviews/` | avaliações anonimizadas e críticas |
| `data/brasil/app_store/reviews_para_ia/` | cópias redigidas para uso com IA |
| `data/brasil/apps_nas_duas_lojas/` | amostra final, apps de uma loja só, verificação de disponibilidade, decisões manuais |
| `data/chave_apps_mascarados_NAO_COMPARTILHAR/` | mapeamento de APP_001 para o app real |
| `outputs/funnel_metrics.json` | contagens de cada etapa do funil |

No PowerShell, na pasta do projeto:

```powershell
.\.venv\Scripts\Activate.ps1
$env:PYTHONIOENCODING = "utf-8"
python src/01_search_google_play.py
python src/02_search_app_store.py
python src/03_clean_stores.py
python src/03b_check_other_store.py
python src/04_cross_store_dedup.py
python src/05_scrape_google_play_reviews.py
python src/05b_scrape_app_store_reviews.py
python src/06_filter_sentiment.py
python src/07_build_ai_share.py
```

Os passos 01 e 02 refazem a busca e podem trazer resultados diferentes; para reproduzir esta amostra, comece pelo 03. Entre o 04 e o 05, os pares parecidos vão para `manual_match_decisions.csv`, onde a coluna `decision` recebe `yes` ou `no`. O 05 leva cerca de 1 hora; se cair, rodar de novo continua de onde parou.

## Limitações e mudanças no artigo

- **Volume desigual entre lojas.** A App Store traz no máximo 500 avaliações recentes por app; a Google Play traz o histórico completo.
- **Concentração.** Um único app tem 48% das reviews da Google Play.
- **Verificação de disponibilidade.** A busca pelo nome na outra loja vai além das 6 strings. Ela serve só ao critério 4, mas deve ser descrita no método.
- **Regras por palavra-chave.** Podem errar; cada exclusão tem motivo registrado para revisão.
- **Termos da Apple.** Confirmar com a orientação se o uso do feed RSS para pesquisa é permitido.

| Seção do artigo | Mudança |
| --- | --- |
| Resumo | Avaliações da Google Play e da App Store |
| 3, Método | Incluir o feed RSS da Apple como fonte |
| 3.1, Strings | Trocar a tabela T1–T5 pelas 6 strings S1–S6 |
| 3.1, Critério 2 | Educação aceita para apps de educação financeira |
| 3.1, Coleta | Duas lojas; limite de 500 na App Store |
| 4.1, Ética | Revisar os termos das duas lojas |
| 5, Validade externa | Android e iOS, com volume desigual |
