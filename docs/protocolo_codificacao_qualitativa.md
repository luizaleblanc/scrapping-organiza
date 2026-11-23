# Protocolo de apoio à codificação qualitativa

Atualizado em 22/11/2026 para o protocolo com seis strings de busca, quatro mercados e avaliações da Google Play e da App Store. As contagens de avaliações críticas ainda estão sendo geradas; use `[N]` sempre que precisar indicar uma contagem.

## Base de trabalho

A análise usa as avaliações com nota ≤ 3 e sentimento negativo ou neutro, nas cópias redigidas do passo 7. A base inclui português (Brasil), inglês (Estados Unidos) e espanhol (Espanha e México). Preserve os campos de máscara do app, loja, mercado, idioma, nota, data e, quando houver, o *compound*. No espanhol, o *compound* não é a regra de classificação.

- **Google Play:** fora do Brasil, a coleta inclui só as notas de 1 a 3 estrelas, com até 1.000 avaliações por nota e por app.
- **App Store:** feed RSS público da Apple, com até 500 avaliações mais recentes por app. A App Store é mantida como fonte de avaliações por decisão da pesquisadora, considerando o risco de interpretação dos termos da Apple.
- **Sentimento:** LeIA para o português e VADER para o inglês, mantendo as avaliações com *compound* < 0,05. No espanhol, o `pysentimiento` mantém os rótulos `NEG` e `NEU`. Só as avaliações positivas saem. Uma avaliação sem texto não deve interromper o processamento.
- **Censura:** no passo 7, nomes de pessoas, marcas de apps, outras empresas, lugares e identificadores diretos são substituídos por marcadores.

As seis buscas e os critérios de seleção estão em `docs/pipeline_explicativo.md`. As strings são S1–S6, com versões traduzidas para o inglês e o espanhol.

## Cuidados de validade

A App Store fornece no máximo 500 avaliações recentes por app, um recorte que não equivale ao histórico completo. Nos mercados internacionais, a Google Play também tem um limite próprio por nota. Ao comparar lojas e países, leve essas diferenças em conta e prefira proporções ou comparações por app quando fizer sentido.

O classificador de sentimento e o NER podem errar, principalmente em textos curtos, irônicos, multilíngues ou sem contexto. No espanhol, a decisão de crítica usa o rótulo do `pysentimiento`, então não compare diretamente o *compound* de idiomas diferentes como se fosse a mesma escala. Os resultados descrevem as avaliações coletadas e não representam necessariamente todos os usuários.

A App Store é mantida como fonte de avaliações por decisão da pesquisadora. O uso do RSS público envolve um risco relacionado aos termos e condições da Apple, que deve ser discutido com a orientação.

## Decisão analítica

O artigo-base propõe:

- modelagem de tópicos com BERTopic;
- Análise Temática Reflexiva, conforme Braun e Clarke;
- codificação dedutiva pela ontologia de dark patterns de Gray et al.;
- categorização de falhas recorrentes.

Os autores devem definir se o foco principal será dark UX, elicitação de requisitos ou uma análise em duas camadas, e registrar essa escolha antes da codificação.

A IA pode ajudar a organizar evidências, sugerir códigos e resumir padrões. Ela não substitui a interpretação dos pesquisadores e não demonstra que um app pratica um dark pattern.

- Reclamações sobre bugs, preço, recursos ausentes ou suporte podem ser codificadas como falhas ou experiências relatadas.
- Sugira um dark pattern só quando a avaliação descrever uma interação enganosa ou coercitiva concreta.
- Se faltar evidência, use `insufficient_evidence` ou `not_a_dark_pattern`.
- Não generalize para todos os usuários, não infira causalidade e não atribua práticas a apps específicos com base em relatos isolados.

## Censura e uso responsável

O passo 7 combina regras e o modelo `Davlan/bert-base-multilingual-cased-ner-hrl`. Os marcadores são:

- `[NOME]` para pessoas;
- `[APP]` para marcas dos apps da amostra;
- `[MARCA]` para outras empresas;
- `[LOCAL]` para lugares;
- `[EMAIL]`, `[PHONE]`, `[CPF]`, `[URL]` e `[HANDLE]` para identificadores diretos.

Marcas que também são palavras comuns, como “era” e “wallet”, são ignoradas pela lista de marcas de apps.

A censura automática não encontra todos os dados pessoais. Revise uma amostra e não tente reidentificar avaliadores ou apps. Nunca envie a chave de máscaras, o `appId`, o título real do app ou dados identificáveis a um modelo externo. Use as cópias redigidas, preserve as máscaras e a loja, e inclua o idioma e o mercado na análise.

## Fluxo de trabalho

1. **Preparar e congelar a base.** Guarde cópias datadas dos arquivos de avaliações críticas por mercado e loja. Remova as duplicatas exatas e documente a operação. Se juntar as lojas, preserve a coluna `store`, além do mercado e do idioma.
2. **Modelar tópicos com BERTopic.** Registre os embeddings, os parâmetros e a semente. Decida se os mercados e idiomas serão modelados juntos ou separados e justifique a escolha. Inspecione os tópicos e os outliers, sem escolher o modelo só por uma métrica automática.
3. **Inspecionar tópicos e exemplos.** Revise as palavras-chave e as avaliações representativas. As sugestões da IA são só um ponto de partida: os pesquisadores revisam os exemplos e registram memorandos analíticos.
4. **Construir o codebook.** Combine os códigos dedutivos da ontologia de Gray et al. com os códigos que surgirem das falhas recorrentes. Documente, para cada código, nome, descrição, critérios de inclusão e exclusão e exemplos.
5. **Codificar e revisar.** Para cada sugestão, guarde uma evidência textual curta e a justificativa. Os pesquisadores revisam as sugestões, discutem as divergências e atualizam o codebook e os memorandos. Não declare que houve codificação independente por dois pesquisadores se isso não aconteceu.
6. **Sintetizar.** Apresente os temas, subtemas, frequências descritivas do corpus, exemplos parafraseados, diferenças entre lojas e mercados (quando sustentadas pelos dados) e as limitações. Não escreva contagens finais antes de a base estar consolidada; use `[N]` como marcador provisório.

## Formato de saída por avaliação

```json
{
  "app_mask_id": "APP_0XX",
  "store": "google_play",
  "market": "br",
  "lang": "pt",
  "score": 2,
  "compound": -0.42,
  "sentiment_label": null,
  "issue_codes": ["..."],
  "gray_ontology": {
    "high_level": "... ou null",
    "meso_level": "... ou null",
    "low_level": "... ou null"
  },
  "evidence": "trecho curto da avaliação redigida",
  "rationale": "por que o trecho sustenta o código",
  "dark_pattern_evidence": "explicit / insufficient / none",
  "needs_human_review": true
}
```

Para as avaliações em espanhol, registre `sentiment_label` como `NEG`, `NEU` ou `POS` e não use o `compound` como critério de inclusão. Não force uma avaliação a caber em uma categoria. Permita mais de um código quando houver problemas distintos, e separe a falha relatada do dark pattern.

## Prompt de trabalho para IA

> Analise somente as avaliações redigidas fornecidas neste lote. Elas são avaliações públicas de apps de finanças pessoais e educação financeira, coletadas na Google Play ou na App Store, em português, inglês ou espanhol, e filtradas para nota até 3 e sentimento negativo ou neutro. Para cada avaliação, proponha códigos descritivos da falha ou experiência relatada. Separadamente, proponha um mapeamento para a ontologia de dark patterns de Gray et al. (2024), nos níveis alto, meso e baixo, apenas quando o texto trouxer evidência de interação enganosa ou coercitiva. Não deduza a interface, a intenção da empresa nem comportamentos que não estejam descritos. Se houver apenas bug, recurso ausente, preço ou atendimento ruim, registre como falha ou experiência e use `not_a_dark_pattern` ou `insufficient_evidence`. Preserve a máscara, a loja, o mercado e o idioma. Em espanhol, preserve o rótulo `NEG`, `NEU` ou `POS`; o filtro manteve somente `NEG` e `NEU`. Responda em JSON conforme o esquema deste protocolo, com a evidência curta no idioma original. Ao final, liste as ambiguidades e os padrões provisórios que exigem leitura humana. Não apresente as sugestões como temas finais, porque elas dependem da análise dos pesquisadores.

## Referências

- Braun, V.; Clarke, V. (2006). *Using thematic analysis in psychology*. [DOI](https://doi.org/10.1191/1478088706qp063oa).
- Braun, V.; Clarke, V. (2019). *Reflecting on reflexive thematic analysis*. [DOI](https://doi.org/10.1080/2159676X.2019.1628806).
- Gray, C. M.; Santos, C.; Bielova, N.; Mildner, T. (2024). *An Ontology of Dark Patterns Knowledge*. [Artigo CHI 2024](https://doi.org/10.1145/3613904.3642436) · [Ontologia e materiais](https://ontology.darkpatternsresearchandimpact.com/).
- Maalej, W.; Nabil, H. (2015). *Bug report, feature request, or simply praise? On automatically classifying app reviews*. RE 2015, IEEE.
