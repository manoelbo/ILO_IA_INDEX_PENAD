# Bick Calibration Receipt

> Status: calibration complete; remaining 223 rows are blocked pending explicit user approval.

## Runtime and integrity

- Model: `gpt-5.6-sol`
- Reasoning effort: `max`
- Model fallback: disabled
- Semantic workers: four fresh contexts, one active at a time
- Authoritative inputs: unchanged at the final calibration checkpoint
- Claude audit outputs read: no

## Source version gate

The stored file is **Federal Reserve Bank of St. Louis Working Paper 2024-027F, revised 27 October 2025**. The frozen BibLaTeX entry records Working Paper `2024-027` with date `2024`. All four rows therefore carry `PDF_VERSION_MISMATCH`; substantive support was judged separately against the stored 2025 revision and its own pagination.

## Calibration table

| Row | Claim | Type | Verdict | Printed pages | PDF pages | Confidence | Issues |
|---|---|---|---|---|---|---|---|
| `ROW-0001` | `CLM-001` | `DIRECT` | `OVERSTATED` | front cover and title page (unnumbered); pp. 6–7 | 1–2, 8–9 | `HIGH` | WRONG_POPULATION (MAJOR), GENERALIZATION_OVERCLAIM (MAJOR), WRONG_PERIOD (MINOR), PDF_VERSION_MISMATCH (MINOR) |
| `ROW-0002` | `CLM-002` | `DIRECT` | `SUPPORTED` | capa e folha de rosto sem numeração; pp. 9–10 | 1–2, 11–12 | `HIGH` | PDF_VERSION_MISMATCH (MINOR) |
| `ROW-0003` | `CLM-003` | `DIRECT` | `SUPPORTED` | front matter (unnumbered) and p. 9 | 1-2, 11 | `HIGH` | PDF_VERSION_MISMATCH (MAJOR) |
| `ROW-0004` | `CLM-004` | `AUTHOR_INFERENCE` | `PARTIALLY_SUPPORTED` | Cover (unnumbered); main-text pp. 1–2 | 1, 3–4 | `HIGH` | AUTHOR_INFERENCE_UNSUPPORTED (MINOR), PDF_VERSION_MISMATCH (MAJOR) |

Full temporary table: [`calibration_table.tsv`](calibration_table.tsv)

## ROW-0001 / CLM-001

- **Claim (PT-BR):** Estima-se que 32,1% dos trabalhadores dos Estados Unidos já integravam ferramentas de IA às suas rotinas até o final de 2024.
- **Verdict:** `OVERSTATED` (`HIGH` confidence)
- **Evidence (PT-BR):** A revisão armazenada informa diretamente que 32,1% dos trabalhadores da amostra RPS declararam usar IA generativa no trabalho, com base nas ondas de agosto e novembro de 2024. A nota da Figura 1 restringe a amostra ‘For Work’ a respondentes empregados de 18 a 64 anos (N = 6.935). O percentual está correto, mas a redação da dissertação amplia a população para todos os trabalhadores dos Estados Unidos, troca IA generativa por ferramentas de IA em geral e descreve uso autorrelatado como integração às rotinas.
- **Anchor:** “32.1% of workers used genAI at work”
- **Printed pages:** front cover and title page (unnumbered); pp. 6–7
- **Physical PDF pages:** 1–2, 8–9
- **Locator:** Cover metadata and title page; Section 3, second paragraph; Figure 1a and notes
- **Source version:** Federal Reserve Bank of St. Louis Working Paper 2024-027F, revision dated October 27, 2025 (`PDF_VERSION_MISMATCH`)
- **Direct evidence vs inference (PT-BR):** A fonte declara diretamente o percentual de uso autorrelatado de IA generativa no trabalho. A extensão a todos os trabalhadores dos Estados Unidos, a referência a ferramentas de IA em geral e a formulação de que elas já estavam integradas às rotinas são generalizações da dissertação, não descrições equivalentes declaradas pela fonte.
- **Evidence file:** [`evidence_pages/ROW-0001.pdf`](evidence_pages/ROW-0001.pdf)
- **Structured issues:**
  - `WRONG_POPULATION` / `MAJOR` — A redação não informa a restrição etária e apresenta o percentual como se abrangesse todos os trabalhadores dos Estados Unidos; a fonte não inclui trabalhadores com 65 anos ou mais nessa estimativa. Action: `NARROW_CLAIM`.
  - `GENERALIZATION_OVERCLAIM` / `MAJOR` — ‘Ferramentas de IA’ amplia IA generativa para IA em geral, enquanto ‘integravam às suas rotinas’ sugere regularidade que a medida de 32,1% não exige; parte desse total não havia usado a tecnologia na semana anterior. Action: `REWRITE_CLAIM`.
  - `WRONG_PERIOD` / `MINOR` — A expressão ‘até o final de 2024’ pode ser lida como uma estimativa de encerramento do ano, mas o valor exato combina duas ondas específicas e não é uma medição de dezembro de 2024. Action: `NARROW_CLAIM`.
  - `PDF_VERSION_MISMATCH` / `MINOR` — O registro BibLaTeX reproduzido identifica o trabalho como de 2024 e número 2024-027, enquanto o PDF armazenado se apresenta como revisão 2024-027F de 2025 e sugere citação com ano 2025. Action: `MANUAL_REVIEW`.
- **Recommended revision (PT-BR):** Nas ondas de agosto e novembro de 2024 da RPS, 32,1% dos respondentes empregados de 18 a 64 anos nos Estados Unidos declararam usar IA generativa no trabalho.

## ROW-0002 / CLM-002

- **Claim (PT-BR):** O ritmo de adoção de ferramentas de IA nos Estados Unidos era comparável ao do computador pessoal na década de 1980.
- **Verdict:** `SUPPORTED` (`HIGH` confidence)
- **Evidence (PT-BR):** A revisão armazenada compara explicitamente a adoção no trabalho. Dois anos após o lançamento do ChatGPT, a taxa de adoção de IA generativa no trabalho era 32,1%; três anos após o lançamento do IBM PC, a taxa de adoção de computadores no trabalho era 25,1%. O corpo do texto caracteriza essas taxas como semelhantes. Assim, a afirmação é sustentada quando lida no escopo dos trabalhadores já estabelecido pelo trecho da dissertação.
- **Anchor:** “We find similar work adoption rates for genAI”
- **Printed pages:** capa e folha de rosto sem numeração; pp. 9–10
- **Physical PDF pages:** 1–2, 11–12
- **Locator:** Capa e folha de rosto; Section 3.2, Figure 2 e primeiro parágrafo da p. 10
- **Source version:** Federal Reserve Bank of St. Louis Working Paper 2024-027F (October 2025 revision) (`PDF_VERSION_MISMATCH`)
- **Direct evidence vs inference (PT-BR):** Trata-se de evidência direta no corpo do artigo: os autores afirmam que as taxas de adoção de IA generativa e de computadores no trabalho são semelhantes e apresentam os respectivos valores. Não é necessário atribuir ao artigo uma inferência externa.
- **Evidence file:** [`evidence_pages/ROW-0002.pdf`](evidence_pages/ROW-0002.pdf)
- **Structured issues:**
  - `PDF_VERSION_MISMATCH` / `MINOR` — A entrada BibLaTeX identifica o trabalho como Bick, Blandin e Deming (2024), Working Paper 2024-027, mas o PDF armazenado é a revisão 2024-027F de outubro de 2025 e traz 27 de outubro de 2025 como data do manuscrito e 2025 na citação sugerida. A divergência bibliográfica não altera o suporte substantivo desta afirmação. Action: `KEEP`.
- **Recommended revision (PT-BR):** Manter a afirmação substantiva e alinhar a entrada bibliográfica à revisão efetivamente armazenada, registrando a versão de outubro de 2025. Para máxima precisão, explicitar que a comparação se refere à adoção de IA generativa no trabalho.

## ROW-0003 / CLM-003

- **Claim (PT-BR):** A difusão das ferramentas de IA nos Estados Unidos era superior, em termos populacionais, à da internet.
- **Verdict:** `SUPPORTED` (`HIGH` confidence)
- **Evidence (PT-BR):** A capa e a folha de rosto identificam o arquivo armazenado como Federal Reserve Bank of St. Louis Working Paper 2024-027F, revisão de 27 de outubro de 2025, em divergência com a entrada BibLaTeX congelada, que registra 2024-027 e data 2024. No mérito substantivo, a página impressa 9 informa que 21% dos adultos dos EUA tinham acesso à internet dois anos após o marco histórico adotado e qualifica esse ritmo de adoção geral como substancialmente mais lento que o da IA generativa, cuja adoção geral em 2024 era de cerca de 45%.
- **Anchor:** “substantially slower than the adoption of genAI”
- **Printed pages:** front matter (unnumbered) and p. 9
- **Physical PDF pages:** 1-2, 11
- **Locator:** Cover and title page; Section 3.2, Figure 2 and accompanying paragraph
- **Source version:** Federal Reserve Bank of St. Louis Working Paper 2024-027F (October 2025 revision) (`PDF_VERSION_MISMATCH`)
- **Direct evidence vs inference (PT-BR):** Evidência direta: os autores comparam explicitamente a adoção geral da IA generativa com a da internet e qualificam a adoção da internet como substancialmente mais lenta; não é necessária inferência adicional da autora da dissertação.
- **Evidence file:** [`evidence_pages/ROW-0003.pdf`](evidence_pages/ROW-0003.pdf)
- **Structured issues:**
  - `PDF_VERSION_MISMATCH` / `MAJOR` — A entrada BibLaTeX congelada registra o Working Paper 2024-027 com data 2024, mas a capa do PDF armazenado identifica o Working Paper 2024-027F, com revisão em outubro de 2025, e a folha de rosto fixa a data em 27 de outubro de 2025. Action: `MANUAL_REVIEW`.
- **Recommended revision (PT-BR):** Manter a afirmação substantiva, preferencialmente usando 'IA generativa' e explicitando a janela comparável após o marco de lançamento; antes da circulação, reconciliar a entrada bibliográfica com o Working Paper 2024-027F revisado em 27 de outubro de 2025 ou anexar a versão exata descrita na referência congelada.

## ROW-0004 / CLM-004

- **Claim (PT-BR):** A combinação do alcance ocupacional com a velocidade de difusão justifica tratar essa geração de inteligência artificial como um problema econômico, e não apenas tecnológico.
- **Verdict:** `PARTIALLY_SUPPORTED` (`HIGH` confidence)
- **Evidence (PT-BR):** No texto principal, o artigo informa que cerca de 32% dos trabalhadores usavam genAI no trabalho, compara a velocidade de adoção laboral à do computador pessoal e afirma que o ritmo semelhante sugere potencial de disrupção. Também discute efeitos macroeconômicos, variação ocupacional e ganhos de produtividade. Esses elementos sustentam as premissas e tornam razoável a inferência de relevância econômica, mas o texto principal não formula o contraste normativo entre problema econômico e problema meramente tecnológico. A capa identifica o arquivo armazenado como Working Paper 2024-027F, revisão de outubro de 2025, divergente do registro bibliográfico congelado de 2024.
- **Anchor:** “has the potential to be similarly disruptive”
- **Printed pages:** Cover (unnumbered); main-text pp. 1–2
- **Physical PDF pages:** 1, 3–4
- **Locator:** Cover metadata block (source identity only); Section 1 (Introduction; substantive evidence)
- **Source version:** Federal Reserve Bank of St. Louis Working Paper 2024-027F, October 2025 revision (`PDF_VERSION_MISMATCH`)
- **Direct evidence vs inference (PT-BR):** Evidência direta no texto principal: prevalência entre trabalhadores, comparação da velocidade de adoção com o computador pessoal, discussão de efeitos macroeconômicos e potencial de disrupção. Inferência do autor da dissertação: converter esses achados no enquadramento contrastivo de 'problema econômico, e não apenas tecnológico'.
- **Evidence file:** [`evidence_pages/ROW-0004.pdf`](evidence_pages/ROW-0004.pdf)
- **Factual premises supported:** `YES`
- **Inference reasonably follows:** `YES`
- **Source explicitly states inference:** `NO`
- **Inference assessment (PT-BR):** As premissas factuais são sustentadas pelo texto principal: o artigo documenta o alcance entre trabalhadores, compara a velocidade de adoção à do computador pessoal, discute efeitos macroeconômicos e afirma que o ritmo semelhante sugere potencial de disrupção. A inferência de relevância econômica é, portanto, razoável. Contudo, a fonte não afirma explicitamente que a genAI deve ser tratada como um problema econômico em oposição a um problema apenas tecnológico; essa formulação é uma interpretação do autor da dissertação.
- **Structured issues:**
  - `AUTHOR_INFERENCE_UNSUPPORTED` / `MINOR` — A fonte não formula explicitamente o contraste segundo o qual essa combinação justifica tratar a genAI como um problema econômico, e não apenas tecnológico. Essa é uma síntese interpretativa razoável, mas pertence ao autor da dissertação e deve ser sinalizada como tal. Action: `REWRITE_CLAIM`.
  - `PDF_VERSION_MISMATCH` / `MAJOR` — O registro BibLaTeX congelado identifica o relatório como 2024-027 e atribui data de 2024, enquanto o PDF efetivamente auditado é a revisão 2024-027F, datada de 27 de outubro de 2025. O conteúdo foi julgado na versão armazenada, mas a identidade bibliográfica precisa ser reconciliada. Action: `MANUAL_REVIEW`.
- **Recommended revision (PT-BR):** Diante desse alcance entre trabalhadores e da rapidez de difusão, esta dissertação trata a genAI como um fenômeno de relevância econômica, além de tecnológica.

## Calibration summary

- Verdicts: `OVERSTATED` = 1, `PARTIALLY_SUPPORTED` = 1, `SUPPORTED` = 2
- Structured issues: 8
- Source-version issues: 4 of 4 rows
- Claims needing a new source: 0
- Direct claims: three; author inference: one
- The author-inference row supports its factual premises and a reasonable economic interpretation, but the contrastive wording belongs to the dissertation author rather than the cited source.

## Evidence-page manifest

| Row | Evidence path | SHA-256 | Extracted pages | Source PDF indices |
|---|---|---|---:|---|
| `ROW-0001` | `evidence_pages/ROW-0001.pdf` | `674023066f8296e030c24daea6dd20c0007f4d2919aecdd3810d9a42cb190498` | 4 | 1–2, 8–9 |
| `ROW-0002` | `evidence_pages/ROW-0002.pdf` | `779bd65f1df4422a2d064bf28f2dfe0bb166ea4c86f2f58a61f6c4db6c040069` | 4 | 1–2, 11–12 |
| `ROW-0003` | `evidence_pages/ROW-0003.pdf` | `084225aaf0e08c6746b887262f6718d84cb1c1c6b4ab5028b052e1f286c8932d` | 3 | 1-2, 11 |
| `ROW-0004` | `evidence_pages/ROW-0004.pdf` | `43622a782a4eeb70589dba6ef2aa6a9f0b60b57fb557fce3d71b595e71ca62c3` | 3 | 1, 3–4 |

## Gate

No row after `ROW-0004` has been audited. The controller must stop here until explicit user approval is received.
