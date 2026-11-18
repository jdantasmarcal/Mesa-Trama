# Mesa do Pesquisador

Mural de cartões para pesquisa em fontes paleográficas e demográficas (recenseamentos, batismos): importe CSVs, busque
pessoas com grafias aproximadas, monte fogos e famílias em cartões, ligue pessoas entre si (mesma pessoa, compadrio,
parentesco…) e organize tudo em quadros.

É **um único arquivo** (`index.html`), sem servidor e sem dependências: abra com duplo clique no navegador. Os dados ficam
no navegador (IndexedDB). Use **Exportar backup** na página inicial para guardar cópias.

## Recursos principais
- Importação de CSV/TSV (UTF‑8, UTF‑16, Windows‑1252; até 500 mil linhas) com **tela de conferência de colunas**
  (reconhecidas automaticamente em dourado).
- Busca tolerante a grafias antigas (ph/f, y/i, z/s…), abreviaturas desdobradas `Fran[cis]co`, nome e sobrenome em
  colunas separadas, busca por cargo.
- Cartões de pessoa/fogo, anotação, comentário, link, imagem, pendências, tabela, coluna e quadro, com controles na barra
  de título (recolher, ligar, duplicar, cor, enquadrar, tirar), largura/altura ajustáveis e regiões recolhíveis.
- Ligações entre pessoas com tipo, certeza (firme/hipótese), situação e assinatura de quem criou e alterou.
- Vários projetos e quadros, lixeira, desfazer/refazer, backup e importação do formato do Palantír.

## Atalhos
Com um cartão selecionado: **M** recolhe · **D** duplica · **L** liga · **F** enquadra · **Delete** tira ·
**Esc** limpa a seleção · **Ctrl+Z / Ctrl+Y** desfaz/refaz. Roda do mouse rola; **Ctrl + roda** dá zoom.

## Privacidade
Nada é enviado a servidor algum. **Não versione CSVs, imagens dos documentos nem backups**: o `.gitignore` já os exclui.
Os dados ficam separados por endereço do navegador: abrir o app por outro caminho (ex.: outro `file:///` ou outro
domínio) começa vazio. Para mudar de lugar, exporte o backup num e importe no outro.

## Testes
```
pip install -r tests/requirements.txt
playwright install chromium
python tests/run_tests.py          # tudo, inclusive CSV de 95 mil linhas
python tests/run_tests.py --fast   # sem o CSV grande
python tests/run_tests.py --only janelas
```
Os CSVs de teste são gerados na hora, com dados inventados.

## Limites conhecidos
Sem login, colaboração ou nuvem (exigiriam servidor). Testado em Chromium; Firefox e Safari não foram testados.
