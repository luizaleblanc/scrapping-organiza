# Pipeline de coleta, triagem e publicação

Atualizado em 22/11/2026.

## Escopo

O pipeline identifica apps de finanças pessoais e educação financeira, coleta avaliações públicas da Google Play e da App Store e prepara uma amostra de avaliações críticas para análise. Avaliação crítica é aquela com nota ≤ 3 e sentimento negativo ou neutro. As contagens ainda estão sendo geradas; onde uma contagem de críticas for necessária, usa-se `[N]`.

A análise abrange quatro mercados:

| Mercado | Pasta | Idioma |
| --- | --- | --- |
| Brasil | `data/brasil/` | português |
| Estados Unidos | `data/mercados_internacionais/estados_unidos/` | inglês |
| Espanha | `data/mercados_internacionais/espanha/` | espanhol |
| México | `data/mercados_internacionais/mexico/` | espanhol |

A variável `MARKET` seleciona o mercado: `br` (padrão), `us`, `es` ou `mx`.

## Strings de busca e seleção de apps

Os quatro mercados usam as mesmas seis intenções de busca, traduzidas para o inglês e o espanhol. Não há buscas por nome de marca.

| ID | Brasil (pt) | Estados Unidos (en) | Espanha e México (es) |
| --- | --- | --- | --- |
| S1 | finanças | finance | finanzas |
| S2 | organizador de finanças | finance organizer | organizador de finanzas |
| S3 | educador de finanças | finance educator | educador de finanzas |
| S4 | aplicativos financeiros | financial apps | aplicaciones financieras |
| S5 | ia para finanças | ai for finance | ia para finanzas |
| S6 | organizador financeiro com ia | ai financial organizer | organizador financiero con ia |

A triagem aplica os critérios em cascata, e o primeiro critério que falha define o motivo da exclusão.

- **Incluídos:** apps da categoria Finanças (Finance). Apps da categoria Educação só entram quando o título ou o desenvolvedor indicam educação financeira.
- **Excluídos:**
  - conflito de interesse;
  - bancos e contas digitais;
  - maquininhas de cartão;
  - carteiras e meios de pagamento;
  - trading, cripto e investimentos;
  - ferramentas empresariais;
  - crédito e empréstimos;
  - sinais de exclusão na descrição oficial;
  - apps sem avaliações;
  - apps sem atualização nos últimos 12 meses;
  - apps que não estão disponíveis nas duas lojas.

As listas auditáveis estão em `src/config.py`.

A verificação de disponibilidade procura cada app elegível na outra loja pelo nome e aplica as mesmas regras. Pares parecidos, mas não idênticos, podem ser revisados manualmente. Essa busca só confirma a disponibilidade e não acrescenta termos à tabela de strings.

## Coleta das avaliações

A coleta é feita apenas para os apps elegíveis da amostra pareada entre as lojas.

| Fonte | Brasil | Mercados internacionais |
| --- | --- | --- |
| Google Play | Avaliações acessíveis pelo `google-play-scraper` | Só notas 1, 2 e 3; até 1.000 avaliações por nota e por app |
| App Store | Feed RSS público da Apple; até 500 avaliações mais recentes por app | Feed RSS público da Apple; até 500 avaliações mais recentes por app |

A App Store é usada na busca e na verificação de disponibilidade e, por decisão da pesquisadora, também como fonte de avaliações. Como o RSS fornece só as avaliações mais recentes, a amostra pode não representar todo o histórico. O uso desses dados também envolve um risco de interpretação dos termos e condições da Apple, e a pesquisadora deve confirmar com a orientação se o uso previsto é permitido.

As lojas da Espanha e do México podem trazer avaliações em espanhol que não vêm só daquele país. Por isso, os resultados devem ser lidos por idioma e mercado de coleta, sem presumir que cada avaliação indica o país de residência do autor.

## Sentimento e definição de crítica

O filtro tem duas etapas. Primeiro, ficam só as avaliações com nota ≤ 3. Depois, o sentimento é classificado conforme o idioma:

- **Português:** LeIA. Ficam as avaliações com *compound* < `C.POSITIVE_COMPOUND` (0,05).
- **Inglês:** VADER, com o mesmo corte (*compound* < 0,05).
- **Espanhol:** `pysentimiento`. Ficam os rótulos `NEG` e `NEU`, e o rótulo `POS` é descartado.

A definição final é, portanto, nota ≤ 3 **e** sentimento negativo ou neutro. O critério de sentimento remove só as avaliações positivas; um *compound* igual a 0,05 já conta como positivo e sai. No espanhol, o *compound* é apenas uma referência numérica, e a decisão é tomada pelo rótulo. Uma avaliação sem texto não interrompe o processamento.

## Etapas do pipeline

1. **Busca e triagem (01–03):** consulta as seis strings nas duas lojas e aplica os critérios de elegibilidade.
2. **Disponibilidade e pareamento (03b–04):** procura os apps elegíveis na outra loja e forma a amostra comum, com revisão manual dos pares ambíguos.
3. **Coleta e anonimização inicial (05 e 05b):** coleta as avaliações das duas lojas para os apps da amostra e remove os identificadores do perfil do avaliador.
4. **Filtro de sentimento (06):** mantém as avaliações com nota ≤ 3 e sentimento negativo ou neutro, conforme o idioma.
5. **Cópias redigidas (07):** censura dados pessoais, nomes, empresas, marcas e lugares no texto e reduz a data ao dia.
6. **Publicação (08b):** verifica todos os arquivos antes de gerar a pasta pública, dividida por país, loja e máscara de app.

Para busca, coleta e filtragem internacionais, defina `MARKET=us`, `MARKET=es` ou `MARKET=mx`. A geração pública roda sem mercado selecionado, para reunir todos os países. Os comandos e as dependências estão no README.

## Censura no passo 7

O passo 7 usa regras determinísticas e o modelo NER multilíngue `Davlan/bert-base-multilingual-cased-ner-hrl`. Os marcadores são:

| Entidade | Marcador |
| --- | --- |
| Pessoa | `[NOME]` |
| Marca de um app da amostra | `[APP]` |
| Outra empresa ou organização | `[MARCA]` |
| Lugar | `[LOCAL]` |
| E-mail | `[EMAIL]` |
| Telefone | `[PHONE]` |
| CPF | `[CPF]` |
| URL | `[URL]` |
| Identificador com @ | `[HANDLE]` |

As regras também capturam nomes em expressões como “meu nome é…” e em assinaturas. Uma lista de marcas compara os textos com as marcas dos apps da amostra. Termos que também são palavras comuns, como “era” e “wallet”, ficam fora dessa lista para evitar substituições indevidas. A censura automática é conservadora, mas pode deixar passar identificadores não previstos, por isso convém revisar uma amostra antes de compartilhar.

## Pasta pública versionada

`data/publico/` é a única pasta de dados versionada. A etapa `src/08b_build_public_criticas.py` gera:

```text
data/publico/<país>/apps.csv
data/publico/<país>/<google_play|app_store>/APP_xxx.csv
```

- `apps.csv` contém apenas a máscara `APP_xxx`, a categoria e o número de críticas.
- Cada arquivo por loja contém as avaliações de uma máscara, com no máximo 1.500 linhas, para que o GitHub consiga exibi-lo como tabela.
- Os países são `brasil`, `estados_unidos`, `espanha` e `mexico`.

Antes de gravar, uma função de checagem valida as tabelas e recusa os dados se encontrar marca de app, e-mail, URL, @, telefone, CPF ou data com hora. Os antigos `data/publico/reviews_criticas_*.csv` deixaram de existir; a estrutura atual é por país, loja e máscara.

A chave que relaciona cada `APP_xxx` a um app real fica em `data/chave_apps_mascarados_NAO_COMPARTILHAR/` e nunca deve ser publicada. As pastas de coleta, de trabalho e de modelos não fazem parte da saída pública.

## Validade e limitações

- **Cobertura desigual das lojas:** a App Store fornece até 500 avaliações recentes por app. Nos mercados internacionais, a coleta da Google Play se limita às notas 1 a 3, com até 1.000 avaliações por nota e por app.
- **Termos da Apple:** a App Store continua como fonte por decisão da pesquisadora, e a conformidade do uso do feed RSS deve ser confirmada com a orientação.
- **Classificação automática:** a classificação de sentimento e a censura podem errar. No espanhol, o classificador é o `pysentimiento`, e os resultados usam os rótulos negativo e neutro.
- **Escopo das avaliações:** críticas públicas não representam necessariamente a experiência de todos os usuários. Os textos permitem analisar relatos, mas não inferir causalidade nem intenção do desenvolvedor.
- **Censura:** a redação reduz o risco de identificação, mas não garante anonimização absoluta. Não tente reidentificar usuários ou apps.
