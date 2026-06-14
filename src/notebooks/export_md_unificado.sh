#!/usr/bin/env bash
# Exporta notebooks (1a–3b) para GFM e gera um único .md em _export_md/.
# Uso: cd src/notebooks && ./export_md_unificado.sh

set -euo pipefail
cd "$(dirname "$0")"

OUT="_export_md"
mkdir -p "$OUT"

NOTEBOOKS=(
  etapa_1a_preparacao_dados_ilo_pnadc.ipynb
  etapa_1b_analise_dados_ilo_pnadc.ipynb
  etapa_2a_preparacao_dados_did_caged_ilo.ipynb
  etapa_2b_analise_did_caged_ilo.ipynb
  etapa_2c_resultados.ipynb
  etapa_3a_preparacao_dados_did_municipio_conectividade.ipynb
  etapa_3b_analise_did_municipio_conectividade.ipynb
)

for f in "${NOTEBOOKS[@]}"; do
  echo "Render: $f"
  quarto render "$f" --to gfm --no-execute
done

for f in "${NOTEBOOKS[@]}"; do
  base="${f%.ipynb}"
  cp "_output/${base}.md" "$OUT/"
  if [[ -d "_output/${base}_files" ]]; then
    rm -rf "$OUT/${base}_files"
    cp -R "_output/${base}_files" "$OUT/"
  fi
done

UNI="$OUT/notebooks_etapas_1a_3b_unificado.md"
{
  echo "# Compilação unificada — etapas 1a a 3b"
  echo ""
  echo "_Gerado com Quarto (\`quarto render … --to gfm --no-execute\`). As figuras usam caminhos relativos às pastas \`*_files\` neste mesmo diretório._"
  echo ""
  for f in "${NOTEBOOKS[@]}"; do
    base="${f%.ipynb}"
    echo ""
    echo "---"
    echo ""
    echo "<!-- fonte: ${f} -->"
    echo ""
    cat "$OUT/${base}.md"
  done
} > "$UNI"

echo "Concluído: $UNI ($(wc -l < "$UNI" | tr -d ' ') linhas)"
