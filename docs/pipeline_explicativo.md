# Pipeline de coleta, triagem e publica??o

Atualizado em 22/11/2026.

## Escopo

O pipeline identifica apps de finan?as pessoais e educa??o financeira, coleta avalia??es p?blicas das lojas Google Play e App Store e prepara uma amostra de cr?ticas para an?lise. O crit?rio de cr?tica ? nota ? 3 e sentimento negativo ou neutro. As contagens ainda est?o sendo geradas; onde uma contagem de cr?ticas for necess?ria, usa-se `[N]`.

A an?lise abrange Brasil, Estados Unidos, Espanha e M?xico. O Brasil usa `data/brasil/`. Os mercados internacionais usam `data/mercados_internacionais/estados_unidos/`, `data/mercados_internacionais/espanha/` e `data/mercados_internacionais/mexico/`. A vari?vel `MARKET` seleciona `br` (padr?o), `us`, `es` ou `mx`. Estados Unidos usam ingl?s; Espanha e M?xico usam espanhol.

## Strings de busca e sele??o de apps

As mesmas seis inten??es de busca s?o usadas nos mercados, com tradu??es para ingl?s e espanhol. N?o s?o feitas buscas por nomes de marcas para compor a amostra.

| ID | Brasil (pt) | Estados Unidos (en) | Espanha e M?xico (es) |
| --- | --- | --- | --- |
| S1 | finan?as | finance | finanzas |
| S2 | organizador de finan?as | finance organizer | organizador de finanzas |
| S3 | educador de finan?as | finance educator | educador de finanzas |
| S4 | aplicativos financeiros | financial apps | aplicaciones financieras |
| S5 | ia para finan?as | ai for finance | ia para finanzas |
| S6 | organizador financeiro com ia | ai financial organizer | organizador financiero con ia |

A triagem aplica os crit?rios em cascata; o primeiro crit?rio que falha define o motivo registrado. Inclui-se a categoria Finance/Finan?as. A categoria Educa??o s? ? aceita quando o t?tulo ou o desenvolvedor indicam educa??o financeira. Excluem-se conflito de interesse, bancos e contas digitais, maquininhas, carteiras e meios de pagamento, trading, cripto e investimentos, ferramentas empresariais, cr?dito e empr?stimos, sinais de exclus?o na descri??o oficial, apps sem avalia??es, apps sem atualiza??o nos ?ltimos 12 meses e apps sem disponibilidade nas duas lojas. As listas audit?veis est?o em `src/config.py`.

A verifica??o de disponibilidade procura cada app eleg?vel na outra loja pelo nome e aplica as mesmas regras. Pares semelhantes, mas n?o id?nticos, podem ser revisados manualmente. Essa busca adicional verifica disponibilidade e n?o acrescenta termos ? tabela de strings.

## Coleta das avalia??es

A coleta ? feita somente para apps eleg?veis inclu?dos na amostra pareada entre as lojas.

| Fonte | Brasil | Mercados internacionais |
| --- | --- | --- |
| Google Play | Avalia??es acess?veis pelo `google-play-scraper` | Somente 1, 2 e 3 estrelas; at? 1.000 avalia??es por nota por app |
| App Store | Feed RSS p?blico da Apple; at? 500 avalia??es mais recentes por app | Feed RSS p?blico da Apple; at? 500 avalia??es mais recentes por app |

A App Store ? mantida como fonte de avalia??es por decis?o da pesquisadora, al?m de seu uso na busca e na verifica??o de disponibilidade. O RSS limita a amostra ?s avalia??es mais recentes e pode n?o representar todo o hist?rico. O uso dos dados tamb?m envolve risco de interpreta??o dos termos e condi??es da Apple; a pesquisadora deve confirmar com a orienta??o se o uso previsto ? permitido.

Espanha e M?xico podem retornar avalia??es em espanhol que n?o correspondem exclusivamente ao pa?s da loja. Os resultados devem ser interpretados por idioma e mercado de coleta, sem presumir que cada avalia??o identifica a resid?ncia do autor.

## Sentimento e defini??o de cr?tica

Primeiro, ret?m-se notas ? 3. Em seguida, classifica-se o sentimento:

- **Portugu?s:** LeIA. Ficam avalia??es com compound < `C.POSITIVE_COMPOUND` (0,05).
- **Ingl?s:** VADER. Aplica-se o mesmo corte, compound < 0,05.
- **Espanhol:** `pysentimiento`. Ficam os r?tulos `NEG` e `NEU`; o r?tulo `POS` ? descartado.

Portanto, a defini??o final ? nota ? 3 e sentimento negativo ou neutro. S? avalia??es positivas s?o removidas pelo crit?rio de sentimento. Compound igual a 0,05 j? ? positivo e sai. No espanhol, o valor compound ? apenas refer?ncia num?rica; a decis?o ? feita pelo r?tulo. Uma avalia??o sem texto n?o deve interromper o processamento.

## Etapas do pipeline

1. **Busca e triagem (01?03):** consulta as seis strings nas duas lojas e aplica crit?rios de elegibilidade.
2. **Disponibilidade e pareamento (03b?04):** procura apps eleg?veis na outra loja e forma a amostra comum, com revis?o manual de pares amb?guos.
3. **Coleta e anonimiza??o inicial (05 e 05b):** coleta avalia??es das duas lojas para os apps da amostra e remove identificadores do perfil do avaliador.
4. **Filtro de sentimento (06):** mant?m nota ? 3 e sentimento negativo ou neutro conforme idioma.
5. **C?pias redigidas (07):** censura dados pessoais, nomes, empresas, marcas e lugares no texto, e reduz a data ao dia.
6. **Publica??o (08b):** verifica todos os arquivos antes de gerar a pasta p?blica particionada por pa?s, loja e m?scara de app.

Para buscas, coleta e filtragem internacionais, defina `MARKET=us`, `MARKET=es` ou `MARKET=mx`. A gera??o p?blica ? executada sem um mercado selecionado para reunir os pa?ses. Os comandos detalhados e depend?ncias est?o no README.

## Censura no passo 7

O passo 7 usa regras determin?sticas e o modelo NER multil?ngue `Davlan/bert-base-multilingual-cased-ner-hrl`. Os marcadores s?o:

| Entidade | Marcador |
| --- | --- |
| Pessoa | `[NOME]` |
| Marca de um app da amostra | `[APP]` |
| Outra empresa ou organiza??o | `[MARCA]` |
| Lugar | `[LOCAL]` |
| E-mail | `[EMAIL]` |
| Telefone | `[PHONE]` |
| CPF | `[CPF]` |
| URL | `[URL]` |
| Identificador com @ | `[HANDLE]` |

As regras tamb?m capturam nomes escritos em express?es como ?meu nome ?? e assinaturas. Uma lista de marcas de apps compara os textos ?s marcas da amostra. Termos que tamb?m s?o palavras comuns, como ?era? e ?wallet?, s?o exclu?dos dessa lista para evitar substitui??es indevidas. A censura autom?tica ? conservadora, mas pode deixar identificadores n?o previstos; revise uma amostra antes de compartilhar.

## Pasta p?blica versionada

`data/publico/` ? a ?nica pasta de dados versionada. A etapa `src/08b_build_public_criticas.py` gera:

```text
data/publico/<pa?s>/apps.csv
 data/publico/<pa?s>/<google_play|app_store>/APP_xxx.csv
```

`apps.csv` cont?m apenas a m?scara `APP_xxx`, a categoria e o n?mero de cr?ticas. Cada arquivo por loja cont?m avalia??es de uma m?scara e tem no m?ximo 1.500 linhas, para que o GitHub possa exibi-lo como tabela. Pa?ses: `brasil`, `estados_unidos`, `espanha` e `mexico`.

Antes de gravar, a fun??o de checagem recusa os dados se encontrar marca de app, e-mail, URL, @, telefone, CPF ou data com hora. A etapa valida as tabelas antes de gravar os arquivos p?blicos. Os antigos `data/publico/reviews_criticas_*.csv` deixam de existir; a estrutura atual ? por pa?s, loja e m?scara.

A chave que relaciona `APP_xxx` a um app real fica em `data/chave_apps_mascarados_NAO_COMPARTILHAR/` e nunca deve ser publicada. As pastas de coleta, trabalho e modelos n?o s?o a sa?da p?blica.

## Validade e limita??es

- **Cobertura desigual das lojas:** a App Store disponibiliza at? 500 avalia??es mais recentes por app. Nos mercados internacionais, a coleta da Google Play se limita a notas 1?3 e at? 1.000 avalia??es por nota por app.
- **Termos da Apple:** a App Store permanece como fonte por decis?o da pesquisadora; a conformidade do uso do feed RSS deve ser confirmada com a orienta??o.
- **Classifica??o autom?tica:** sentimento e censura podem cometer erros. No espanhol, o classificador ? `pysentimiento`, e os resultados usam os r?tulos negativos e neutros.
- **Escopo das avalia??es:** cr?ticas p?blicas n?o representam necessariamente a experi?ncia de todos os usu?rios. Os textos permitem analisar relatos, n?o inferir causalidade ou inten??o do desenvolvedor.
- **Censura:** a reda??o reduz risco de identifica??o, mas n?o garante anonimiza??o absoluta. N?o tente reidentificar usu?rios ou apps.
