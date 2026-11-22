# Protocolo de apoio ? codifica??o qualitativa

Atualizado em 22/11/2026 para o protocolo com seis strings de busca, quatro mercados e avalia??es da Google Play e da App Store. As contagens de avalia??es cr?ticas ainda est?o sendo geradas; use `[N]` quando precisar indicar uma contagem.

## Base de trabalho

A an?lise usa avalia??es com nota ? 3 e sentimento negativo ou neutro, em c?pias redigidas do passo 7. A base inclui portugu?s (Brasil), ingl?s (Estados Unidos) e espanhol (Espanha e M?xico). Preserve os campos de m?scara do app, loja, mercado, idioma, nota, data e, quando dispon?vel, compound. O compound n?o ? a regra de classifica??o para o espanhol.

- **Google Play:** fora do Brasil, a coleta inclui notas de 1 a 3 estrelas, limitada a at? 1.000 avalia??es por nota e por app.
- **App Store:** feed RSS p?blico da Apple, com at? 500 avalia??es mais recentes por app. A App Store ? mantida como fonte de avalia??es por decis?o da pesquisadora; considerar o risco de interpreta??o dos termos da Apple.
- **Sentimento:** LeIA para portugu?s e VADER para ingl?s; ficam reviews com compound < 0,05. No espanhol, `pysentimiento` mant?m r?tulos `NEG` e `NEU`. S? avalia??es positivas saem. Review sem texto n?o deve quebrar o processamento.
- **Censura:** nomes de pessoas, marcas de apps, outras empresas, lugares e identificadores diretos s?o substitu?dos por marcadores no passo 7.

As seis buscas e os crit?rios de sele??o est?o em `docs/pipeline_explicativo.md`. As strings s?o S1?S6, com vers?es traduzidas para ingl?s e espanhol.

## Cuidados de validade

A App Store cont?m no m?ximo 500 avalia??es recentes por app; esse recorte n?o equivale ao hist?rico completo. Para Google Play nos mercados internacionais, a coleta tem limite pr?prio por nota. Compare lojas e pa?ses considerando essas diferen?as, e prefira propor??es ou compara??es por app quando forem adequadas.

O classificador de sentimento e o NER podem errar, especialmente em texto curto, ir?nico, multil?ngue ou sem contexto. No espanhol, a decis?o de cr?tica usa o r?tulo de `pysentimiento`; n?o compare diretamente o compound de idiomas diferentes como se fosse uma escala id?ntica. Os resultados descrevem avalia??es coletadas e n?o representam necessariamente todos os usu?rios.

A App Store ? mantida como fonte de reviews por decis?o da pesquisadora. A utiliza??o do RSS p?blico envolve risco relacionado aos termos e condi??es da Apple, que deve ser discutido com a orienta??o.

## Decis?o anal?tica

O artigo-base prop?e modelagem de t?picos com BERTopic, An?lise Tem?tica Reflexiva conforme Braun e Clarke, codifica??o dedutiva pela ontologia de dark patterns de Gray et al. e categoriza??o de falhas recorrentes. Os autores devem definir se o recorte principal ser? dark UX, elicita??o de requisitos ou uma an?lise em duas camadas. A escolha deve ser registrada antes da codifica??o.

A IA pode ajudar a organizar evid?ncias, sugerir c?digos e resumir padr?es. Ela n?o substitui a interpreta??o dos pesquisadores e n?o demonstra que um app pratica um dark pattern.

- Reclama??es sobre bugs, pre?o, recursos ausentes ou suporte podem ser codificadas como falhas ou experi?ncias relatadas.
- Sugira um dark pattern apenas quando a avalia??o descrever uma intera??o enganosa ou coercitiva concreta.
- Se faltar evid?ncia, use `insufficient_evidence` ou `not_a_dark_pattern`.
- N?o generalize para todos os usu?rios, n?o infira causalidade e n?o atribua pr?ticas a apps espec?ficos com base em relatos isolados.

## Censura e uso respons?vel

O passo 7 combina regras e o modelo `Davlan/bert-base-multilingual-cased-ner-hrl`. Os marcadores s?o `[NOME]` para pessoas, `[APP]` para marcas dos apps da amostra, `[MARCA]` para outras empresas, `[LOCAL]` para lugares, `[EMAIL]`, `[PHONE]`, `[CPF]`, `[URL]` e `[HANDLE]` para identificadores diretos. Marcas gen?ricas que tamb?m s?o palavras comuns, como ?era? e ?wallet?, s?o ignoradas pela lista de marcas de apps.

A reda??o autom?tica n?o encontra todo dado pessoal. Revise uma amostra e n?o tente reidentificar avaliadores ou apps. Nunca envie a chave de m?scaras, `appId`, t?tulo real do app ou dados identific?veis a um modelo externo. Use c?pias redigidas, preserve as m?scaras e a loja, e inclua o idioma e o mercado na an?lise.

## Fluxo de trabalho

1. **Preparar e congelar a base.** Guarde c?pias datadas dos arquivos de avalia??es cr?ticas por mercado e loja. Remova duplicatas exatas, documentando a opera??o. Se juntar lojas, preserve a coluna `store`; preserve tamb?m o mercado e o idioma.
2. **Modelar t?picos com BERTopic.** Registre embeddings, par?metros e semente. Decida se os mercados/idiomas ser?o modelados juntos ou separados e justifique a escolha. Inspecione t?picos e outliers; n?o selecione o modelo apenas por uma m?trica autom?tica.
3. **Inspecionar t?picos e exemplos.** Revise palavras-chave e avalia??es representativas. Use sugest?es de IA como ponto de partida; pesquisadores revisam os exemplos e registram memorandos anal?ticos.
4. **Construir o codebook.** Combine c?digos dedutivos da ontologia de Gray et al. com c?digos emergentes de falhas recorrentes. Documente nome, descri??o, crit?rios de inclus?o e exclus?o e exemplos.
5. **Codificar e revisar.** Para cada sugest?o, mantenha evid?ncia textual curta e justificativa. Pesquisadores revisam sugest?es, discutem diverg?ncias e atualizam o codebook e os memorandos. N?o alegue codifica??o independente por dois pesquisadores se ela n?o ocorreu.
6. **Sintetizar.** Apresente temas, subtemas, frequ?ncias descritivas do corpus, exemplos parafraseados, diferen?as entre lojas/mercados quando sustentadas e limita??es. N?o escreva contagens finais at? a base ser consolidada; use `[N]` como marcador provis?rio.

## Formato de sa?da por avalia??o

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
  "evidence": "trecho curto da avalia??o redigida",
  "rationale": "por que o trecho sustenta o c?digo",
  "dark_pattern_evidence": "explicit / insufficient / none",
  "needs_human_review": true
}
```

Para avalia??es em espanhol, registre `sentiment_label` como `NEG`, `NEU` ou `POS`; n?o trate `compound` como crit?rio de inclus?o. Evite for?ar avalia??es a caber em uma categoria. Permita mais de um c?digo quando houver problemas distintos e separe tema de falha de dark pattern.

## Prompt de trabalho para IA

> Analise somente as avalia??es redigidas fornecidas neste lote. Elas s?o avalia??es p?blicas de apps de finan?as pessoais e educa??o financeira, coletadas na Google Play ou na App Store, em portugu?s, ingl?s ou espanhol, e filtradas para nota at? 3 e sentimento negativo ou neutro. Para cada avalia??o, proponha c?digos descritivos de falha ou experi?ncia relatada. Separadamente, proponha um mapeamento ? ontologia de dark patterns de Gray et al. (2024), nos n?veis alto, meso e baixo, apenas quando o texto trouxer evid?ncia de intera??o enganosa ou coercitiva. N?o deduza interface, inten??o da empresa ou comportamentos que n?o estejam descritos. Se houver apenas bug, recurso ausente, pre?o ou atendimento ruim, registre como falha ou experi?ncia e use `not_a_dark_pattern` ou `insufficient_evidence`. Preserve m?scara, loja, mercado e idioma. Em espanhol, preserve o r?tulo `NEG`, `NEU` ou `POS`; o filtro manteve somente `NEG` e `NEU`. Responda em JSON conforme o esquema deste protocolo, com evid?ncia curta no idioma original. Ao final, liste ambiguidades e padr?es provis?rios que exigem leitura humana. N?o apresente sugest?es como temas finais: elas dependem da an?lise dos pesquisadores.

## Refer?ncias

- Braun, V.; Clarke, V. (2006). *Using thematic analysis in psychology*. [DOI](https://doi.org/10.1191/1478088706qp063oa).
- Braun, V.; Clarke, V. (2019). *Reflecting on reflexive thematic analysis*. [DOI](https://doi.org/10.1080/2159676X.2019.1628806).
- Gray, C. M.; Santos, C.; Bielova, N.; Mildner, T. (2024). *An Ontology of Dark Patterns Knowledge*. [Artigo CHI 2024](https://doi.org/10.1145/3613904.3642436) ? [Ontologia e materiais](https://ontology.darkpatternsresearchandimpact.com/).
- Maalej, W.; Nabil, H. (2015). *Bug report, feature request, or simply praise? On automatically classifying app reviews*. RE 2015, IEEE.
