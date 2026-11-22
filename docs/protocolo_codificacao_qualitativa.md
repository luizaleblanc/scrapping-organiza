# Protocolo de apoio à codificação qualitativa

Atualizado em 22/11/2026 para a rodada atual (6 strings de busca, 40 apps presentes nas duas lojas, reviews da Google Play e da App Store).

## Base de trabalho

A análise usa os dois arquivos de reviews críticas (nota até 3 e sentimento negativo ou neutro pelo LeIA, escore < 0,05; nomes de pessoas censurados), em versão redigida:

| Arquivo | Loja | Linhas | Apps | Nota 1 / 2 / 3 | Sem texto |
| --- | --- | --- | --- | --- | --- |
| `data/brasil/google_play_store/reviews_para_ia/reviews_critical_redacted.csv` | Google Play | 19.454 | 36 de 40 | 10.999 / 3.870 / 4.585 | 0 |
| `data/brasil/app_store/reviews_para_ia/reviews_critical_redacted.csv` | App Store | 1.834 | 25 de 40 | 1.244 / 292 / 298 | 0 |

- **Idioma:** todo o corpus está em português (`pt`), loja Brasil. O corpus bilíngue da rodada anterior não vale mais.
- **Apps sem reviews críticas:** 4 apps na Google Play e 15 na App Store. São apps pequenos, sem nenhuma review com nota até 3 e texto negativo. Eles ficam fora desta análise, e isso deve constar no artigo.
- **Volume desigual:** a App Store traz no máximo 500 avaliações recentes por app; a Google Play traz o histórico completo. Comparações entre lojas devem ser feitas por app ou em proporção, nunca em números absolutos.
- **Concentração:** um único app tem 48% das reviews da Google Play (identificável pelo volume de linhas). Relate os achados com e sem ele, ou pondere por app.
- **Escopo:** os achados descrevem relatos críticos, não a experiência de toda a base de usuários.

Os detalhes da coleta, dos critérios e do funil estão em `docs/pipeline_explicativo.md`.

## Decisão pendente do artigo (seção 3.2)

Antes de codificar, os autores precisam escolher o recorte:

- **Recorte A (Dark UX):** codificação dedutiva pela ontologia de Gray et al. (2024). Bugs e falhas de sincronização são excluídos na inspeção manual.
- **Recorte B (elicitação de requisitos):** codificação pela taxonomia de Maalej e Nabil (2015). Bugs entram como categoria.
- **Opção híbrida:** coletar e filtrar uma única vez e codificar em duas camadas, com dark patterns para o artigo principal e falhas funcionais para o relatório de requisitos do MVP.

O esquema de saída abaixo já separa as duas camadas (`issue_codes` e `gray_ontology`), então serve a qualquer das três opções.

## Método indicado pelo artigo-base

O artigo propõe:

1. modelagem de tópicos com BERTopic e inspeção dos tópicos;
2. Análise Temática Reflexiva, conforme Braun e Clarke (2006, 2019);
3. codificação dedutiva pela ontologia de dark patterns de Gray et al. (2024);
4. categorização das falhas recorrentes.

Como mitigação de validade, o artigo prevê inspeção manual dos tópicos e codificação por dois pesquisadores.

## Uso responsável de IA

A IA serve para organizar evidências, sugerir códigos e resumir padrões. Ela não substitui a interpretação dos pesquisadores e não serve como prova de que um app pratica um dark pattern.

- Reclamações sobre bugs, preço, recursos ausentes ou suporte são codificadas como falhas ou experiências relatadas.
- Um dark pattern só é sugerido quando a avaliação descreve uma interação enganosa ou coercitiva concreta.
- Se faltar evidência, use `insufficient_evidence` ou `not_a_dark_pattern`.

Envie ao modelo apenas os arquivos de `data/brasil/google_play_store/reviews_para_ia/` e `data/brasil/app_store/reviews_para_ia/`, em lotes manejáveis. Preserve `app_mask_id`, a loja, a nota e o escore de sentimento. Nunca envie `appId`, título do app ou o mapeamento de `data/chave_apps_mascarados_NAO_COMPARTILHAR/`.

A redação automática não pega todo dado pessoal. Revise uma amostra antes de enviar.

## Fluxo de trabalho

1. **Preparar e congelar a base.** Guarde uma cópia datada dos dois CSVs de críticas. Remova as duplicatas exatas, documentando as quantidades. Acrescente a coluna `store` (`google_play` ou `app_store`) se as lojas forem analisadas juntas.
2. **Modelar tópicos com BERTopic.**
   - Registre o modelo de embeddings (multilíngue ou específico para português), os parâmetros e a semente.
   - Rode as lojas juntas, com `store` como metadado, ou separadas. Registre a escolha.
   - Inspecione os tópicos e os outliers. Avalie a coerência `c_v` quando o pré-processamento permitir, mas não escolha o modelo só pelo escore.
   - Teste o efeito do app dominante, com e sem ele.
3. **Inspecionar tópicos e exemplos.** Para cada tópico relevante, revise as palavras-chave e as avaliações representativas. A IA pode propor rótulos e interpretações. Os pesquisadores revisam os exemplos e escrevem memorandos analíticos.
4. **Construir o codebook iterativo.** Combine os códigos dedutivos da ontologia de Gray et al. (níveis alto, meso e baixo) com códigos emergentes de falhas recorrentes em apps financeiros e de educação financeira. Cada código tem nome, descrição, critérios de inclusão e exclusão e exemplos.
5. **Codificar e revisar.** A IA pode sugerir códigos por avaliação ou trecho, sempre com uma evidência textual curta e uma justificativa. Os pesquisadores revisam as sugestões, discutem divergências e atualizam o codebook e os memorandos. Registre exclusões e casos ambíguos. Não alegue codificação independente por dois pesquisadores se ela não ocorreu.
6. **Sintetizar.** Apresente:
   - temas e subtemas;
   - frequências, apenas como descrição do corpus;
   - exemplos parafraseados (seção 4.1 do artigo);
   - diferenças entre lojas e entre apps, quando sustentadas;
   - limitações.

   Não generalize para todos os usuários nem infira causalidade a partir de avaliações. Não atribua práticas a apps específicos: os resultados são agregados.

## Formato de saída por avaliação

```json
{
  "app_mask_id": "APP_0XX",
  "store": "google_play",
  "lang": "pt",
  "score": 2,
  "compound": -0.42,
  "issue_codes": ["..."],
  "gray_ontology": {
    "high_level": "... ou null",
    "meso_level": "... ou null",
    "low_level": "... ou null"
  },
  "evidence": "trecho curto da própria avaliação",
  "rationale": "por que o trecho sustenta o código",
  "dark_pattern_evidence": "explicit / insufficient / none",
  "needs_human_review": true
}
```

- Não force cada avaliação a caber num padrão de Gray.
- Permita vários códigos quando a avaliação relatar problemas distintos.
- Separe "tema de falha" de "dark pattern".

## Prompt de trabalho para IA

> Analise somente as avaliações fornecidas neste lote. Elas são avaliações públicas, em português, de apps brasileiros de finanças pessoais e educação financeira, coletadas na Google Play e na App Store e já filtradas para nota até 3 e sentimento negativo. Para cada avaliação, proponha códigos descritivos de falha ou experiência relatada. Separadamente, proponha um mapeamento à ontologia de dark patterns de Gray et al. (2024), nos níveis alto, meso e baixo, apenas quando o texto trouxer evidência de interação enganosa ou coercitiva. Não deduza a interface, a intenção da empresa ou comportamentos que não estejam descritos. Se houver apenas bug, recurso ausente, preço ou atendimento ruim, registre isso como falha ou experiência e use `not_a_dark_pattern` ou `insufficient_evidence`. Preserve os identificadores mascarados e a loja. Responda em JSON, conforme o esquema deste protocolo, com uma evidência curta por código, no idioma original. Ao final, liste ambiguidades, padrões recorrentes provisórios e exemplos que exigem leitura humana. Não apresente os resultados como temas finais: são sugestões para a análise temática reflexiva e para a revisão dos pesquisadores.

## Referências

- Braun, V.; Clarke, V. (2006). *Using thematic analysis in psychology*. [DOI](https://doi.org/10.1191/1478088706qp063oa).
- Braun, V.; Clarke, V. (2019). *Reflecting on reflexive thematic analysis*. [DOI](https://doi.org/10.1080/2159676X.2019.1628806).
- Gray, C. M.; Santos, C.; Bielova, N.; Mildner, T. (2024). *An Ontology of Dark Patterns Knowledge*. [Artigo CHI 2024](https://doi.org/10.1145/3613904.3642436) · [Ontologia e materiais](https://ontology.darkpatternsresearchandimpact.com/).
- Maalej, W.; Nabil, H. (2015). *Bug report, feature request, or simply praise? On automatically classifying app reviews*. RE 2015, IEEE.
