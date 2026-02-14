# Material suplementar em formato “livro” (Jupyter Book 2)

Este diretório é o **projeto Jupyter Book 2** (MyST). Os notebooks e a pasta `data/` reais ficam em **`notebook/`**. Aqui em `docs/book/`, os arquivos `etapa_1a_preparacao_dados_ilos_pnadc.ipynb` e `data` são **symlinks** para `../../notebook/...`. **Não remova nem substitua por cópias** — isso quebraria os paths e duplicaria fonte.

## Estrutura

- **`myst.yml`** — Configuração do projeto e **índice (TOC)** (`project.toc`).
- **`index.md`** — Página inicial do livro.
- **`etapa_1a_preparacao_dados_ilos_pnadc.ipynb`**, **`data`** — Symlinks para `../../notebook/`.

## Ver o “livro” no navegador (site local)

No terminal, **a partir desta pasta** (`docs/book/`):

```bash
cd docs/book
jupyter-book start
```

Na primeira vez o Jupyter Book pode baixar o tema (book-theme). Depois ele informa a URL (ex.: **http://localhost:3000**). Abra no navegador.

Para parar o servidor: `Ctrl+C`.

## Adicionar novos notebooks ao “livro”

1. Coloque o `.ipynb` em **`notebook/`** (fonte única).
2. Crie um **symlink** em `docs/book/`: `ln -sf ../../notebook/seu_novo_notebook.ipynb docs/book/seu_novo_notebook.ipynb`
3. Adicione no TOC em **`myst.yml`** → `project.toc`:
   ```yaml
   - file: seu_novo_notebook.ipynb
   ```
4. Rode de novo `jupyter-book start`. O symlink `data` em `docs/book/` já atende a todos os notebooks que usam `data/`.

## Exportar para PDF/Word (opcional)

A partir de `docs/book/`:

```bash
jupyter-book build myst.yml --pdf
# ou --docx
```

(O PDF exige LaTeX instalado.)
