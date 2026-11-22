# Padr?es enganosos em apps de finan?as pessoais ? pipeline de dados

Descri??o do protocolo, das decis?es e das sa?das: [docs/pipeline_explicativo.md](docs/pipeline_explicativo.md). As mudan?as propostas para o artigo est?o em [docs/alteracoes_artigo.md](docs/alteracoes_artigo.md).

O projeto busca e tria apps de finan?as pessoais e educa??o financeira nas duas lojas, no Brasil e em tr?s mercados internacionais. As avalia??es p?blicas s?o coletadas na Google Play e na App Store e filtradas para identificar cr?ticas: nota ? 3 e sentimento negativo ou neutro.

## Mercados e buscas

As seis strings S1?S6 s?o traduzidas para cada mercado. O valor padr?o de `MARKET` ? `br`; os mercados adicionais usam `MARKET=us`, `MARKET=es` ou `MARKET=mx`.

| Mercado | Idioma | Pasta |
| --- | --- | --- |
| Brasil (`br`) | Portugu?s | `data/brasil/` |
| Estados Unidos (`us`) | Ingl?s | `data/mercados_internacionais/estados_unidos/` |
| Espanha (`es`) | Espanhol | `data/mercados_internacionais/espanha/` |
| M?xico (`mx`) | Espanhol | `data/mercados_internacionais/mexico/` |

As strings traduzidas preservam a inten??o das seis buscas aprovadas. N?o se usam buscas por marca para formar a amostra. Os crit?rios de inclus?o e exclus?o est?o descritos em [docs/pipeline_explicativo.md](docs/pipeline_explicativo.md).

## Coleta e filtro de avalia??es

A Google Play ? consultada pelo `google-play-scraper`. No Brasil, a coleta segue o alcance dispon?vel da loja. Fora do Brasil, s?o coletadas avalia??es de 1, 2 e 3 estrelas, com limite de at? 1.000 avalia??es por nota e por app.

A App Store usa o feed RSS p?blico de avalia??es da Apple, limitado ?s 500 avalia??es mais recentes por app. A App Store tamb?m ? mantida como fonte de avalia??es, por decis?o da pesquisadora. O uso do feed deve considerar os termos e as condi??es da Apple; essa quest?o ? registrada como risco metodol?gico e ?tico a verificar com a orienta??o.

S?o cr?ticas as avalia??es com nota ? 3 e sentimento negativo ou neutro. Em portugu?s, o LeIA; em ingl?s, o VADER: compound < `POSITIVE_COMPOUND` (0,05). Assim, compound igual ou maior que 0,05 ? classificado como positivo e descartado. Em espanhol, o `pysentimiento` mant?m os r?tulos `NEG` e `NEU`; s? `POS` sai. Avalia??es sem texto s?o aceitas pelo processamento e n?o interrompem a etapa.

## Censura e compartilhamento

No passo 7, regras e o modelo multil?ngue `Davlan/bert-base-multilingual-cased-ner-hrl` censuram pessoas (`[NOME]`), marcas dos apps da amostra (`[APP]`), outras empresas (`[MARCA]`) e lugares (`[LOCAL]`). Regras adicionais substituem e-mails (`[EMAIL]`), telefones (`[PHONE]`), CPFs (`[CPF]`), URLs (`[URL]`) e identificadores com @ (`[HANDLE]`). Marcas gen?ricas que tamb?m s?o palavras comuns, como ?era? e ?wallet?, s?o ignoradas pela lista de marcas de apps.

A ?nica pasta de dados versionada ? `data/publico/`. A etapa `src/08b_build_public_criticas.py` gera nela:

- `data/publico/<pa?s>/apps.csv`, com m?scaras `APP_xxx`, categoria e n?mero de cr?ticas;
- `data/publico/<pa?s>/<google_play|app_store>/APP_xxx.csv`, com at? 1.500 linhas por arquivo para exibi??o tabular no GitHub.

Antes de gravar, a etapa p?blica verifica se restaram marcas de apps, e-mail, URL, @, telefone, CPF ou hora na data. Se encontrar algum desses elementos, interrompe a grava??o. Os antigos arquivos `data/publico/reviews_criticas_*.csv` deixam de existir.

## Ambiente e execu??o

Instale as depend?ncias e o LeIA uma vez:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
git clone https://github.com/rafjaa/LeIA.git vendor/LeIA
```

Execute os scripts a partir da pasta do projeto. Para os mercados internacionais, defina `MARKET` antes das etapas de busca, coleta e filtragem. As etapas de prepara??o e publica??o seguem o fluxo descrito em [docs/pipeline_explicativo.md](docs/pipeline_explicativo.md). A gera??o da pasta p?blica ? feita sem `MARKET`:

```powershell
Remove-Item Env:MARKET -ErrorAction SilentlyContinue
python src/08b_build_public_criticas.py
```

Os scripts de busca podem retornar resultados diferentes em execu??es distintas. A pasta privada `data/chave_apps_mascarados_NAO_COMPARTILHAR/` cont?m a correspond?ncia entre m?scaras e apps reais e n?o deve ser compartilhada.

## ?tica e limites

S?o usadas avalia??es publicamente acess?veis. Nome, foto e identificador do avaliador n?o s?o coletados para os arquivos de an?lise. Texto e entidades pessoais s?o censurados e as datas p?blicas n?o incluem hora. A censura autom?tica pode falhar; n?o envie a chave de m?scaras nem dados identific?veis a servi?os externos. A App Store tem limite de rec?ncia e volume distinto da Google Play, e o uso do feed RSS est? sujeito aos termos da Apple.

## Licen?a

O c?digo deste reposit?rio est? sob a [licen?a MIT](LICENSE) ? 2026 Luiza Ferraz Leblanc. A licen?a n?o cobre os textos das avalia??es nem os dados das lojas. Os resultados p?blicos usam m?scaras e texto censurado; n?o tente reidentificar pessoas ou apps.
