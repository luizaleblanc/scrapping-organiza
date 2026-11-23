# Propostas de atualização do artigo

Este documento compara, seção por seção, o texto atual do protocolo com o texto proposto para o manuscrito.

- O manuscrito editável não está neste repositório. Antes de substituir qualquer trecho, confira o texto atual com a versão submetida pelos autores.
- As contagens de avaliações críticas ainda estão sendo geradas e aparecem como `[N]`.

## Resumo / Abstract

**Texto atual (descrição do protocolo anterior):**
> A pesquisa analisa avaliações críticas coletadas na Google Play para apps identificados por cinco termos de busca (T1–T5).

**Texto proposto (Resumo):**
> Este estudo analisa avaliações públicas de apps de finanças pessoais e educação financeira identificados por seis strings de busca (S1–S6) na Google Play e na App Store, no Brasil, nos Estados Unidos, na Espanha e no México. Consideram-se críticas as avaliações com nota até 3 e sentimento negativo ou neutro. O sentimento é classificado com o LeIA em português, o VADER em inglês e o `pysentimiento` em espanhol. Antes do compartilhamento, nomes de pessoas, marcas, lugares e identificadores diretos são censurados. A base final contém [N] avaliações críticas.

**Texto proposto (Abstract):**
> This study analyzes public reviews of personal finance and financial education apps identified through six search strings (S1–S6) in Google Play and the App Store in Brazil, the United States, Spain, and Mexico. Critical reviews are those rated 3 or below and classified as negative or neutral. Sentiment is assessed with LeIA for Portuguese, VADER for English, and `pysentimiento` for Spanish. Personal names, app brands, other organizations, places, and direct identifiers are redacted before sharing. The final corpus contains [N] critical reviews.

## 3 Metodologia: item 2

**Texto atual (descrição do protocolo anterior):**
> As avaliações foram coletadas na Google Play; a App Store foi usada para busca e triagem dos aplicativos.

**Texto proposto:**
> As avaliações públicas foram coletadas na Google Play e na App Store, para os aplicativos elegíveis disponíveis nas duas lojas. Na Google Play, a coleta foi feita com o `google-play-scraper`. Nos mercados internacionais, foram coletadas avaliações de 1 a 3 estrelas, com limite de 1.000 avaliações por nota e por aplicativo. Na App Store, usou-se o feed RSS público de avaliações da Apple, que fornece apenas as 500 avaliações mais recentes de cada aplicativo. A App Store foi mantida como fonte de avaliações por decisão da pesquisadora. Essa escolha amplia a comparação entre plataformas, mas o limite do feed restringe a cobertura temporal. O uso desses dados deve ser avaliado à luz dos termos e condições da Apple.

## 3.1 Strings de busca

**Texto atual (descrição do protocolo anterior):**
> A busca utilizou cinco termos, identificados como T1–T5.

A tabela e a redação exatas do manuscrito precisam ser conferidas, porque não estão no repositório.

**Texto proposto:**
> Foram utilizadas seis strings de busca (S1–S6), sem buscas por nome de marca. As strings foram traduzidas para o inglês, nos Estados Unidos, e para o espanhol, na Espanha e no México, preservando a intenção de busca.

| ID | Brasil (pt) | Estados Unidos (en) | Espanha e México (es) |
| --- | --- | --- | --- |
| S1 | finanças | finance | finanzas |
| S2 | organizador de finanças | finance organizer | organizador de finanzas |
| S3 | educador de finanças | finance educator | educador de finanzas |
| S4 | aplicativos financeiros | financial apps | aplicaciones financieras |
| S5 | ia para finanças | ai for finance | ia para finanzas |
| S6 | organizador financeiro com ia | ai financial organizer | organizador financiero con ia |

## 3.1 Coleta das avaliações

**Texto atual (descrição do protocolo anterior):**
> Foram coletadas avaliações da Google Play. A App Store foi utilizada somente para identificar e parear aplicativos.

**Texto proposto:**
> As avaliações foram coletadas para os apps elegíveis da amostra pareada. Na Google Play, os mercados internacionais incluem apenas avaliações de 1, 2 e 3 estrelas, até 1.000 por nota e por app. Na App Store, as avaliações vêm do feed RSS público da Apple, limitado às 500 mais recentes por app. A App Store foi mantida como fonte de avaliações por decisão da pesquisadora. O feed oferece um recorte recente e limitado, e não o histórico completo. Além disso, a interpretação dos termos da Apple é um risco que deve ser discutido com a orientação.

## 3.1 Critério de sentimento

**Texto atual (descrição do protocolo anterior):**
> Foram consideradas críticas as avaliações de nota até 3 com sentimento negativo.

**Texto proposto:**
> Foram consideradas críticas as avaliações com nota ≤ 3 e sentimento negativo ou neutro. Para o português, utilizou-se o LeIA; para o inglês, o VADER. Nos dois casos, foram mantidas as avaliações com *compound* < 0,05 e descartadas as com *compound* ≥ 0,05. Para o espanhol, utilizou-se o `pysentimiento`: foram mantidos os rótulos `NEG` e `NEU` e descartado o rótulo `POS`. Assim, o critério de sentimento remove somente as avaliações positivas. Avaliações sem texto não interrompem o processamento.

## 4.1 Ética

**Texto atual (descrição do protocolo anterior):**
> Dados dos avaliadores foram removidos e nomes pessoais foram censurados antes do compartilhamento.

**Texto proposto:**
> Foram coletadas apenas avaliações publicamente acessíveis. Nome, foto e identificador do avaliador não entram nos arquivos de análise. Na preparação para o compartilhamento, regras e o modelo multilíngue `Davlan/bert-base-multilingual-cased-ner-hrl` substituem:
>
> - pessoas por `[NOME]`;
> - marcas dos apps da amostra por `[APP]`;
> - outras empresas por `[MARCA]`;
> - lugares por `[LOCAL]`.
>
> Regras adicionais substituem e-mails, telefones, CPFs, URLs e identificadores com @ por `[EMAIL]`, `[PHONE]`, `[CPF]`, `[URL]` e `[HANDLE]`. Marcas que coincidem com palavras genéricas, como “era” e “wallet”, são ignoradas pela lista de marcas. A censura automática pode falhar e não garante anonimização absoluta; por isso, os resultados compartilhados passam por uma checagem de vazamentos. O uso do feed RSS da Apple também exige a avaliação dos termos e condições aplicáveis.

## 5 Validade interna e externa

**Texto atual (descrição do protocolo anterior):**
> A análise se limita à Google Play e a avaliações negativas; os resultados podem não representar todos os usuários.

**Texto proposto:**
> A validade externa é limitada pelas fontes e pelas regras de coleta:
>
> - **Volumes desiguais entre plataformas.** A App Store fornece até 500 avaliações recentes por app. Fora do Brasil, a Google Play é coletada apenas para notas de 1 a 3, até 1.000 avaliações por nota e por app. Por isso, as plataformas diferem em período coberto e em volume.
> - **Diferenças entre mercados.** Os mercados diferem em idioma e contexto, e uma avaliação em espanhol não indica necessariamente o país de residência do autor.
> - **Erros automáticos.** A classificação de sentimento pode errar, e a censura de entidades pode deixar identificadores residuais ou substituir termos indevidamente.
> - **Alcance das conclusões.** Os resultados descrevem relatos públicos classificados como negativos ou neutros. Eles não representam todos os usuários nem permitem inferir intenção ou causalidade.
> - **Termos da Apple.** A App Store foi mantida como fonte por decisão da pesquisadora, e a interpretação dos termos da Apple deve ser reconhecida como limitação metodológica e ética.

## Pendências antes de fechar o manuscrito

- [ ] Conferir os “textos atuais” acima com a versão efetiva do manuscrito e trocar as descrições provisórias por citações fiéis.
- [ ] Substituir `[N]` pelos valores finais quando as contagens terminarem.
- [ ] Confirmar com a orientação como descrever e avaliar o risco dos termos e condições da Apple para o uso do RSS.
- [ ] Verificar a consistência das traduções e da terminologia (avaliação ou review) em cada seção e idioma.
