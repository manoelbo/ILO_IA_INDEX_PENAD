# Relatório em PDF/HTML com Quarto

Este diretório está configurado para gerar um **relatório em HTML e PDF** a partir do notebook usando [Quarto](https://quarto.org).

## Instalação do Quarto

O Quarto não vem com o Python. Instale separadamente:

- **macOS:** `brew install quarto` (pode pedir senha de administrador)  
- Ou baixe o instalador em: https://quarto.org/docs/get-started/

Depois confira: `quarto check`

## Como gerar o relatório

No terminal, a partir da pasta do projeto:

```bash
cd notebook
quarto render etapa_1a_preparacao_dados_ilos_pnadc.ipynb
```

- **HTML** (sempre): sai em `notebook/_output/etapa_1a_preparacao_dados_ilos_pnadc.html`
- **PDF**: só é gerado se você tiver **LaTeX** instalado (ex.: [MacTeX](https://tug.org/mactex/) no Mac).  
  Se não tiver LaTeX, gere só HTML e use o navegador (Arquivo → Imprimir → Salvar como PDF):

```bash
quarto render etapa_1a_preparacao_dados_ilos_pnadc.ipynb --to html
```

A configuração do projeto está em `_quarto.yml` (sumário, numeração de seções, margens do PDF).
