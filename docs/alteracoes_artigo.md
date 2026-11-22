# Propostas de atualiza??o do artigo

Este documento organiza, se??o por se??o, o texto atual registrado na documenta??o do protocolo e uma proposta para o manuscrito. O manuscrito edit?vel n?o est? neste reposit?rio; antes de substituir texto literalmente, conferir os trechos atuais com a vers?o submetida pelos autores. As contagens de cr?ticas seguem em processamento e ficam como `[N]`.

## Resumo / Abstract

**Texto atual (descri??o do protocolo anterior):** ?A pesquisa analisa avalia??es cr?ticas coletadas na Google Play para apps identificados por cinco termos de busca (T1?T5).?

**Texto proposto ? Resumo:** ?Este estudo analisa avalia??es p?blicas de apps de finan?as pessoais e educa??o financeira identificados por seis strings de busca (S1?S6) na Google Play e na App Store, no Brasil, nos Estados Unidos, na Espanha e no M?xico. Consideram-se cr?ticas as avalia??es com nota at? 3 e sentimento negativo ou neutro. A an?lise usa LeIA para portugu?s, VADER para ingl?s e `pysentimiento` para espanhol. Antes do compartilhamento, nomes de pessoas, marcas, lugares e identificadores diretos s?o censurados. A base final cont?m [N] avalia??es cr?ticas.?

**Texto proposto ? Abstract:** ?This study analyzes public reviews of personal finance and financial education apps identified through six search strings (S1?S6) in Google Play and the App Store in Brazil, the United States, Spain, and Mexico. Critical reviews are those rated 3 or below and classified as negative or neutral. Sentiment is assessed with LeIA for Portuguese, VADER for English, and `pysentimiento` for Spanish. Personal names, app brands, other organizations, places, and direct identifiers are redacted before sharing. The final corpus contains [N] critical reviews.?

## 3 Metodologia ? item 2

**Texto atual (descri??o do protocolo anterior):** ?As avalia??es foram coletadas na Google Play; a App Store foi usada para busca e triagem dos aplicativos.?

**Texto proposto:** ?As avalia??es p?blicas foram coletadas na Google Play e na App Store para os aplicativos eleg?veis dispon?veis nas duas lojas. A Google Play foi consultada pelo `google-play-scraper`. Nos mercados internacionais, foram coletadas avalia??es de 1 a 3 estrelas, com limite de at? 1.000 avalia??es por nota e por aplicativo. Para a App Store, adotou-se o feed RSS p?blico de avalia??es da Apple, limitado ?s 500 avalia??es mais recentes por aplicativo. A App Store foi mantida como fonte de avalia??es por decis?o da pesquisadora. Essa escolha amplia a compara??o entre plataformas, mas o limite do feed restringe a cobertura temporal e o uso dos dados deve ser avaliado ? luz dos termos e condi??es da Apple.?

## 3.1 ? tabela de strings

**Texto atual (descri??o do protocolo anterior):** ?A busca utilizou cinco termos, identificados como T1?T5.? A tabela e a reda??o exatas do manuscrito devem ser conferidas, pois n?o est?o no reposit?rio.

**Texto proposto:** ?Foram utilizadas seis strings de busca (S1?S6), sem buscas por nome de marca. As strings foram traduzidas para ingl?s nos Estados Unidos e para espanhol na Espanha e no M?xico, preservando a inten??o de busca.?

| ID | Brasil (pt) | Estados Unidos (en) | Espanha e M?xico (es) |
| --- | --- | --- | --- |
| S1 | finan?as | finance | finanzas |
| S2 | organizador de finan?as | finance organizer | organizador de finanzas |
| S3 | educador de finan?as | finance educator | educador de finanzas |
| S4 | aplicativos financeiros | financial apps | aplicaciones financieras |
| S5 | ia para finan?as | ai for finance | ia para finanzas |
| S6 | organizador financeiro com ia | ai financial organizer | organizador financiero con ia |

## 3.1 ? Coleta das avalia??es

**Texto atual (descri??o do protocolo anterior):** ?Foram coletadas avalia??es da Google Play. A App Store foi utilizada somente para identificar e parear aplicativos.?

**Texto proposto:** ?As avalia??es foram coletadas para os apps eleg?veis da amostra pareada. Na Google Play, os mercados internacionais incluem avalia??es de 1, 2 e 3 estrelas, at? 1.000 por nota e por app. Na App Store, as avalia??es v?m do feed RSS p?blico da Apple, limitado ?s 500 mais recentes por app. A App Store foi mantida como fonte de reviews por decis?o da pesquisadora. O feed oferece um recorte recente e limitado, n?o o hist?rico completo; al?m disso, a interpreta??o dos termos da Apple constitui um risco que deve ser discutido com a orienta??o.?

## 3.1 ? Crit?rio de sentimento

**Texto atual (descri??o do protocolo anterior):** ?Foram consideradas cr?ticas as avalia??es de nota at? 3 com sentimento negativo.?

**Texto proposto:** ?Foram consideradas cr?ticas as avalia??es com nota ? 3 e sentimento negativo ou neutro. Para portugu?s, utilizou-se o LeIA; para ingl?s, o VADER. Em ambos, avalia??es com compound < 0,05 foram mantidas, enquanto avalia??es com compound ? 0,05 foram descartadas. Para espanhol, utilizou-se `pysentimiento`, mantendo-se os r?tulos `NEG` e `NEU` e descartando-se `POS`. Assim, somente avalia??es positivas s?o removidas pelo crit?rio de sentimento. Avalia??es sem texto n?o interrompem o processamento.?

## 4.1 ?tica

**Texto atual (descri??o do protocolo anterior):** ?Dados dos avaliadores foram removidos e nomes pessoais foram censurados antes do compartilhamento.?

**Texto proposto:** ?Foram coletadas avalia??es publicamente acess?veis. Nome, foto e identificador do avaliador n?o s?o inclu?dos nos arquivos de an?lise. No passo de prepara??o para compartilhamento, regras e o modelo multil?ngue `Davlan/bert-base-multilingual-cased-ner-hrl` substituem pessoas por `[NOME]`, marcas dos apps da amostra por `[APP]`, outras empresas por `[MARCA]` e lugares por `[LOCAL]`. Regras adicionais substituem e-mails, telefones, CPFs, URLs e identificadores com @ por `[EMAIL]`, `[PHONE]`, `[CPF]`, `[URL]` e `[HANDLE]`. Marcas que coincidem com palavras gen?ricas, como ?era? e ?wallet?, s?o ignoradas pela lista de marcas de apps. A reda??o autom?tica pode falhar e n?o garante anonimiza??o absoluta; os resultados compartilhados passam por uma checagem de vazamentos. O uso do feed RSS da Apple tamb?m requer avalia??o dos termos e condi??es aplic?veis.?

## 5 Validade interna e externa

**Texto atual (descri??o do protocolo anterior):** ?A an?lise se limita ? Google Play e a avalia??es negativas; os resultados podem n?o representar todos os usu?rios.?

**Texto proposto:** ?A validade externa ? limitada pelas fontes e pelas regras de coleta. A App Store oferece at? 500 avalia??es recentes por app, enquanto, fora do Brasil, a Google Play ? coletada apenas para notas de 1 a 3, at? 1.000 avalia??es por nota e por app. As plataformas, per?odos cobertos e volumes s?o, portanto, desiguais. Os mercados tamb?m diferem em idioma e contexto; avalia??es em espanhol n?o necessariamente identificam o pa?s de resid?ncia do autor. A classifica??o autom?tica de sentimento pode errar, e a censura de entidades pode deixar identificadores residuais ou substituir termos indevidamente. Os resultados descrevem relatos p?blicos classificados como negativos ou neutros e n?o representam todos os usu?rios nem permitem inferir inten??o ou causalidade. A App Store foi mantida como fonte por decis?o da pesquisadora; a interpreta??o dos termos da Apple deve ser reconhecida como limita??o metodol?gica e ?tica.?

## Pend?ncias antes de fechar o manuscrito

- Conferir os ?textos atuais? acima com a vers?o efetiva do manuscrito e substituir as descri??es provis?rias por cita??es fi?is.
- Inserir os valores finais no lugar de `[N]` depois que a gera??o das contagens terminar.
- Confirmar com a orienta??o como descrever e avaliar o risco associado aos termos e condi??es da Apple para o uso do RSS.
- Verificar a consist?ncia das tradu??es e a terminologia de avalia??o/review em cada se??o e idioma.
