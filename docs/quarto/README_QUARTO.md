# Relatório em PDF/HTML com Quarto

Este diretório contém a **configuração do Quarto** para gerar relatórios em HTML e PDF a partir dos notebooks. Os notebooks-fonte ficam em **`notebook/`** (não use symlinks aqui; o render usa caminho relativo).

## Instalação do Quarto

O Quarto não vem com o Python. Instale separadamente:

- **macOS:** `brew install quarto` (pode pedir senha de administrador)
- Ou baixe o instalador em: https://quarto.org/docs/get-started/

Para PDF, instale TinyTeX: `quarto install tinytex`

Depois confira: `quarto check`

## Como gerar o relatório

No terminal, **a partir desta pasta** (`docs/quarto/`):

```bash
cd docs/quarto
quarto render ../../notebook/etapa_1a_preparacao_dados_ilos_pnadc.ipynb
```

- Com o notebook fora do projeto, o Quarto pode escrever HTML/PDF ao lado do notebook em `notebook/`. Se quiser tudo em um só lugar, mova para `docs/quarto/_output/`.
- Só HTML (sem LaTeX): `quarto render ../../notebook/etapa_1a_preparacao_dados_ilos_pnadc.ipynb --to html`

A configuração está em `_quarto.yml` (sumário, numeração de seções, margens do PDF).
