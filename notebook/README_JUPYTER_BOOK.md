# Material suplementar em formato “livro” (Jupyter Book 2)

Este diretório está configurado como um **Jupyter Book 2** (MyST): vários notebooks viram um “livro” com sumário e navegação.

## Estrutura

- **`myst.yml`** — Configuração do projeto e **índice (TOC)**. Aqui estão título, descrição e a lista de arquivos (ex.: `index.md`, notebooks).
- **`index.md`** — Página inicial do livro.
- **`_toc.yml`** — Índice no formato antigo; o Jupyter Book 2 usa o TOC que está dentro de `myst.yml` (pode ignorar ou apagar `_toc.yml`).
- **`_config.yml`** — Opções no formato antigo; o Jupyter Book 2 usa principalmente `myst.yml`.

## Ver o “livro” no navegador (site local)

No terminal, a partir da **pasta do projeto** (raiz da dissertação):

```bash
cd notebook
jupyter-book start
```

Na primeira vez o Jupyter Book pode baixar o tema (book-theme). Depois ele informa a URL (ex.: **http://localhost:3000**). Abra no navegador para ver o material com sumário e navegação.

Para parar o servidor: `Ctrl+C` no terminal.

## Adicionar novos notebooks ao “livro”

1. Coloque o `.ipynb` nesta pasta (`notebook/`).
2. Inclua no TOC em **`myst.yml`**, na seção `project.toc`:

```yaml
project:
  toc:
    - file: index.md
    - file: etapa_1a_preparacao_dados_ilos_pnadc.ipynb
    - file: seu_novo_notebook.ipynb   # <-- adicione aqui
```

3. Rode de novo `jupyter-book start` para ver o novo capítulo.

## Exportar para PDF/Word (opcional)

Para gerar PDF ou DOCX a partir dos arquivos do livro:

```bash
cd notebook
jupyter-book build index.md etapa_1a_preparacao_dados_ilos_pnadc.ipynb --pdf
# ou
jupyter-book build index.md etapa_1a_preparacao_dados_ilos_pnadc.ipynb --docx
```

(O PDF exige LaTeX instalado no sistema.)
