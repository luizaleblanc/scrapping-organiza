# Instruções para o Claude

## Fluxo do artigo
1. No início de cada tarefa, leia [docs/checklist_artigo.md](docs/checklist_artigo.md) e [docs/guia_artigo/guia_metodologia_reviews.md](docs/guia_artigo/guia_metodologia_reviews.md).
2. Trabalhe no próximo item `[ ]` e faça as duas trilhas: **(A)**, o código em `src/` com as contagens em `outputs/funnel_metrics*.json`, e **(B)**, o texto em `artigo/secoes/*.tex`.
3. No LaTeX, use apenas números lidos de `outputs/`. Nunca invente valores; quando um número ainda não existir, escreva `[N]` e um `% TODO`.
4. Ao terminar, marque o item no checklist (`[x]` ou `[~]`) e cite o script ou o arquivo `.tex` correspondente.
5. Termine sugerindo uma mensagem de commit atômico para cada item concluído.

## Regras
- Nunca execute `git commit` nem `git push`. A pesquisadora faz os próprios commits.
- Nunca coloque nomes de pessoas, nomes reais de apps ou identificadores em `artigo/` ou `data/publico/`. Use apenas as máscaras `APP_xxx`.
- Não edite o guia, que é a referência fixa.
