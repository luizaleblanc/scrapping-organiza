# Protocolo de apoio à codificação qualitativa

## Base de trabalho

Usar `data/processed/reviews_critical.csv`, gerado pelo filtro de nota e sentimento. No momento da conferência, há 23.897 linhas, 36 IDs mascarados de apps e uma avaliação sem texto; excluir essa linha vazia da interpretação, registrando a exclusão. O corpus é bilíngue (`pt` e `en`) e contém apenas avaliações Google Play com nota até 3 e sentimento neutro/negativo. Logo, os achados descrevem relatos críticos, não a experiência de toda a base de usuários.

Antes da análise definitiva, reconciliar a divergência entre os 155 apps registrados em `outputs/funnel_metrics.json` e os 156 IDs em `data/processed/apps_screening.csv`.

## Método indicado pelo artigo-base

O artigo propõe modelagem de tópicos com BERTopic, inspeção dos tópicos, seguida de Análise Temática Reflexiva conforme Braun e Clarke (2006, 2019), codificação dedutiva pela ontologia de dark patterns de Gray et al. (2024) e categorização das falhas recorrentes. Também menciona inspeção manual dos tópicos e codificação por dois pesquisadores como mitigação de validade.

O artigo fornecido parece ser um manuscrito em desenvolvimento: o resumo contém marcadores de resultados pendentes e as referências têm itens de verificação. Tratar seus resultados como plano metodológico, não como achados já publicados.

## Uso responsável de IA

Usar IA como apoio para organizar evidências, sugerir códigos e resumir padrões; não como substituta da interpretação da pesquisadora nem como prova de que um app pratica um dark pattern. Reclamações sobre bugs, preço, recursos ausentes ou suporte devem ser codificadas como falhas/experiências relatadas. Só sugerir um dark pattern quando a avaliação descreve uma interação enganosa ou coerciva concreta. Caso falte evidência, marcar `insufficient_evidence` ou `not_a_dark_pattern`.

Fazer a análise em lotes manejáveis, preservando `app_mask_id`, idioma, nota e escore de sentimento. Não incluir `appId`, título do app ou arquivo de mapeamento privado no material enviado ao modelo. Rever o texto para identificar e ocultar e-mails, telefones ou outros dados pessoais que o próprio usuário possa ter escrito na avaliação.

## Fluxo de trabalho

1. **Preparar e congelar a base.** Guardar uma cópia datada do CSV filtrado; remover apenas linhas sem conteúdo e duplicatas exatas, documentando quantidades.
2. **Modelar tópicos com BERTopic.** Registrar versão do modelo de embeddings, idioma(s), parâmetros e semente; experimentar configurações justificadas e inspecionar tópicos/outliers. Avaliar coerência `c_v` quando a configuração linguística e o pré-processamento permitirem; não escolher modelo apenas por um escore automático.
3. **Inspecionar tópicos e exemplos.** Para cada tópico relevante, revisar palavras-chave e avaliações representativas nos idiomas originais. Usar IA para propor um rótulo descritivo e possíveis interpretações; a pesquisadora revisa os exemplos e escreve memorandos analíticos.
4. **Construir o codebook iterativo.** Combinar códigos dedutivos da ontologia Gray et al. (níveis alto, meso e baixo) com códigos emergentes para falhas recorrentes de apps financeiros. Definir nome, descrição, critérios de inclusão/exclusão e exemplos de cada código.
5. **Codificar e revisar.** A IA pode sugerir códigos por avaliação ou trecho, sempre com evidência textual curta e justificativa. Pesquisadores revisam as sugestões, discutem divergências e atualizam o codebook/memorandos. Registrar exclusões e casos ambíguos. Não alegar codificação independente por dois pesquisadores se ela não ocorreu.
6. **Sintetizar.** Apresentar temas, subtemas, frequência apenas como descrição do corpus, exemplos anonimizados, diferenças de idioma/app quando sustentadas e limitações. Não generalizar para todos os usuários nem inferir causalidade a partir de avaliações.

## Formato de saída por avaliação

```json
{
  "app_mask_id": "APP_001",
  "lang": "pt",
  "score": 2,
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

Não forçar cada avaliação em um padrão Gray. Permitir múltiplos códigos quando a avaliação relatar problemas distintos. Distinguir `tema de falha` de `dark pattern`.

## Prompt de trabalho para IA

> Analise somente as avaliações fornecidas neste lote. Elas são avaliações públicas de apps de finanças pessoais, já filtradas para nota até 3 e sentimento neutro/negativo. Para cada avaliação, proponha códigos descritivos de falha/experiência relatada e, separadamente, um mapeamento à ontologia de dark patterns de Gray et al. (2024), nos níveis alto, meso e baixo, apenas quando o texto trouxer evidência de interação enganosa ou coerciva. Não deduza a interface, intenção da empresa ou comportamento que não esteja descrito. Se houver apenas bug, recurso ausente, preço ou atendimento ruim, registre isso como falha/experiência e use `not_a_dark_pattern` ou `insufficient_evidence`. Preserve os identificadores mascarados. Responda em JSON conforme o esquema deste protocolo, mantendo o idioma original e uma evidência curta por código. Ao final, liste ambiguidades, padrões recorrentes provisórios e exemplos que exigem leitura humana. Não apresente os resultados como temas finais: eles são sugestões para análise temática reflexiva e revisão por pesquisadores.

## Referências

- Braun, V.; Clarke, V. (2006). *Using thematic analysis in psychology*. [DOI](https://doi.org/10.1191/1478088706qp063oa).
- Braun, V.; Clarke, V. (2019). *Reflecting on reflexive thematic analysis*. [DOI](https://doi.org/10.1080/2159676X.2019.1628806).
- Gray, C. M.; Santos, C.; Bielova, N.; Mildner, T. (2024). *An Ontology of Dark Patterns Knowledge*. [Artigo CHI 2024](https://doi.org/10.1145/3613904.3642436) · [Ontologia e materiais](https://ontology.darkpatternsresearchandimpact.com/).
