# Histórico

## 4.6
- Importação com tela de conferência de colunas: colunas reconhecidas automaticamente ficam em dourado (★ nos seletores);
  escolha de colunas de busca, exibição, cargo, agrupamento, imagem e ano antes de importar. A mesma tela está na aba da fonte.
- Versão do app gravada nos dados; aviso se os dados vierem de versão mais nova.
- Suíte de testes de navegador em `tests/` (73 verificações) e código formatado para o git.

## 4.5
- Altura ajustável, maximizar/enquadrar (F), regiões recolhíveis, atalhos M/D/L/F, ícones sempre visíveis em telas de toque.
- Cada fonte CSV numa chave própria do IndexedDB: gravação principal de ~1,6 KB (antes ~14 MB com 95 mil linhas) e recarga mais rápida.

## 4.4
- Controles dos cartões condensados na barra de título (estilo janela); recolher cartão; alça de largura.

## 4.3 — revisão de 52 itens
- Perda de dados: leitura/gravação do armazenamento, conflito entre abas, lixeira, desfazer após a mesa crescer, ids regenerados,
  backup, tabela sem cabeçalho.
- Fontes e busca: limites de importação ampliados (80 MB, 500 mil linhas), `Fran[cis]co`, nome+sobrenome, número de linha real
  do arquivo, cache de cargo, reagrupar/renomear sem perder vínculos.
- Cartões e ligações: ligar linhas do mesmo cartão, clique simples não liga, duplicatas recusadas, rótulo inverso, "alterada por",
  organizar com largura real, voltar ao quadro de origem, excluir/renomear quadro, roda rola e Ctrl+roda dá zoom.

## 4.2 / 4.1 / 4.0
- 4.2: painel de propriedades, fonte e ligações do cartão. 4.1: tipos de cartão e barra de ferramentas.
  4.0: motor de busca e ligações do Palantír integrado ao 3.8.

## 3.8
- Correções do protótipo 3.7.
