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
| 1 | `python src/01_search_google_play.py` | Busca as 6 strings na Google Play | `data/google_play_store/busca_e_triagem/search_hits.csv` |
| 2 | `python src/02_search_app_store.py` | Busca as 6 strings na App Store | `data/app_store/busca_e_triagem/search_hits.csv` |
| 3 | `python src/03_clean_stores.py` | Aplica os critérios nas duas lojas e deduplica | `apps_eligible.csv` e `apps_excluded_audit.csv` em cada pasta |
| 3b | `python src/03b_check_other_store.py` | Critério 4: procura cada elegível na outra loja pelo nome (mesma marca e mesmas regras) | acrescenta a `apps_eligible.csv` com `discovery_source = availability_check` |
| 4 | `python src/04_cross_store_dedup.py` | Mantém só apps presentes nas duas lojas | `data/apps_nas_duas_lojas/apps_both_stores.csv` |
| 5 | `python src/05_scrape_google_play_reviews.py --no-reuse` | Coleta e anonimiza reviews da Google Play **só dos apps de `apps_both_stores.csv`** (excluídos nunca são coletados) | `data/google_play_store/reviews/reviews_anonymized.csv` |
| 5b | `python src/05b_scrape_app_store_reviews.py` | Coleta e anonimiza avaliações da App Store dos mesmos apps (feed RSS, até 500 por app) | `data/app_store/reviews/reviews_anonymized.csv` |
| 6 | `python src/06_filter_sentiment.py` | Mantém nota ≤ 3 e sentimento negativo/neutro (as duas lojas) | `data/<loja>/reviews/reviews_critical.csv` |
| 7 | `python src/07_build_ai_share.py` | Gera cópias redigidas para uso com IA (as duas lojas) | `data/<loja>/reviews_para_ia/*.csv` |

**Revisão manual (entre os passos 4 e 5):** pares parecidos, mas não idênticos, entre as
lojas ficam em `data/apps_nas_duas_lojas/manual_match_decisions.csv`. Preencha a coluna
`decision` com `yes` (mesmo app) ou `no` e rode o passo 4 de novo. Sem `yes`, o par não
entra na amostra.

**Passo 5:** pode demorar mais de uma hora. Se cair, rode de novo e ele continua de onde
parou. Reviews já coletadas em 20/11/2026 são reaproveitadas; use `--no-reuse` para
coletar tudo de novo ou `--max-per-app 20` para um teste rápido.

Os passos 1 e 2 refazem a busca e podem trazer resultados diferentes. Para reproduzir a
amostra atual, comece pelo passo 3.

## Pastas

```
data/
├── google_play_store/
│   ├── busca_e_triagem/                          busca, elegíveis e excluídos com motivo
│   ├── reviews/                                  reviews anonimizadas e críticas (não versionado)
│   └── reviews_para_ia/                          cópias redigidas para IA (não versionado)
├── app_store/
│   ├── busca_e_triagem/
│   ├── reviews/
│   └── reviews_para_ia/
├── apps_nas_duas_lojas/                          amostra final, loja única, revisão manual
└── chave_apps_mascarados_NAO_COMPARTILHAR/     mapeamento APP_001 -> appId (não versionado)
outputs/funnel_metrics.json                       contagens de cada etapa do funil
src/                                              scripts do pipeline (01 a 07)
docs/pipeline_explicativo.md                      explicação completa do pipeline e das decisões
docs/protocolo_codificacao_qualitativa.md         protocolo da análise (BERTopic, Gray, prompt para IA)
vendor/LeIA/                                      analisador de sentimento em português
arquivo_rodadas_anteriores/                       tudo de rodadas antigas (somente consulta)
├── dados/                                        buscas e pipeline anterior (38 apps)
├── scripts_antigos/                              scripts que não fazem mais parte do pipeline
└── documentos_rodada_20261120/                   relatório e protocolo da rodada antiga
```

## Ética

Só avaliações públicas. Nome, foto e ID do avaliador nunca são gravados. E-mails,
telefones, CPFs, URLs e @menções no texto são substituídos. Os apps aparecem mascarados
(`APP_001`…), e o mapeamento fica em `data/chave_apps_mascarados_NAO_COMPARTILHAR/`. A redação por regex não pega todo
dado pessoal; revise antes de compartilhar.

## Licença

O código deste repositório está sob a [licença MIT](LICENSE) © 2026 Luiza Ferraz Leblanc.

A licença cobre só o código. Não cobre:
- **Dados das lojas:** títulos, descrições e metadados dos apps em `data/` pertencem às respectivas lojas e desenvolvedores e são usados aqui para fins de pesquisa.
- **Avaliações de usuários:** não fazem parte do repositório e não são redistribuídas.
- **LeIA** (`vendor/LeIA`): é baixado à parte e segue a licença do próprio projeto ([rafjaa/LeIA](https://github.com/rafjaa/LeIA)).
