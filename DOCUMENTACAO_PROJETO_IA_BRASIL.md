# Documentação do Projeto: Impacto da IA Generativa no Mercado de Trabalho Brasileiro

Este documento descreve detalhadamente o pipeline de dados, a metodologia e os resultados encontrados no projeto de análise da exposição e impacto (automação vs. aprimoramento) da Inteligência Artificial Generativa no Brasil. O objetivo é fornecer contexto completo para que outros modelos de IA possam compreender o trabalho realizado até o momento.

---

## 1. Visão Geral do Projeto

O projeto está estruturado em quatro etapas principais que transformam dados brutos de uso de IA e classificações ocupacionais globais em insights específicos para a realidade socioeconômica brasileira, utilizando a PNAD Contínua (IBGE) como base demográfica.

---

## 2. Etapa 1: Exposição à IA Generativa (ILO + PNAD)

**Objetivo:** Medir a exposição potencial das ocupações brasileiras à IA Generativa com base no índice da Organização Internacional do Trabalho (ILO).

### Metodologia
- **Dados Demográficos:** PNAD Contínua (IBGE), utilizando o 2º Trimestre de 2025.
- **Índice de Exposição:** GenAI Exposure Index (Gmyrek et al., 2025 - ILO).
- **Processamento:**
  1. Download via BigQuery (projeto `dissertacao-ia-br`).
  2. Limpeza e filtragem (18-65 anos).
  3. **Crosswalk COD-ISCO:** Mapeamento da Classificação de Ocupações para Pesquisas Domiciliares (COD) para a International Standard Classification of Occupations (ISCO-08).
  4. Cálculo de estatísticas ponderadas pelo peso amostral da PNAD.

### Principais Achados
- **Exposição Média Brasil:** 0.281 (ligeiramente abaixo da média global de 0.30).
- **Cobertura:** 99.1% das observações da PNAD receberam um score.
- **Perfil dos Mais Expostos:** Mulheres, brancos, trabalhadores formais, mais jovens e com maior nível de escolaridade.
- **Correlação com Renda:** R² de 0.551 (correlação positiva forte: ocupações de maior renda são mais expostas).

---

## 3. Etapa 2: Anthropic Economic Index (AEI V4)

**Objetivo:** Classificar o impacto da IA entre Automação (Substituição) e Aprimoramento (Augmentation) usando dados reais de uso do Claude.

### Metodologia
- **Fonte:** Anthropic Economic Index (Relatório de Janeiro de 2026).
- **Categorização de Uso:**
    - **Automation (Automação):** Tarefas onde o usuário delega a execução (`directive`, `feedback loop`).
    - **Augmentation (Aprimoramento):** Tarefas onde a IA atua como assistente ou parceiro (`learning`, `task iteration`, `validation`).
- **Métricas:**
    - `automation_share`: % de tarefas automatizáveis.
    - `augmentation_share`: % de tarefas passíveis de aprimoramento.
    - `automation_index`: (Automation - Augmentation). Valores positivos indicam tendência à automação; negativos indicam tendência ao aprimoramento.

---

## 4. Etapa 3: Crosswalk e Imputação Hierárquica

**Objetivo:** Traduzir os índices da Anthropic (baseados no padrão americano O*NET/SOC) para o padrão brasileiro (COD).

### Metodologia Híbrida
Para garantir 100% de cobertura, foi utilizada uma estratégia em cascata:
1. **Match Direto (66.9%):** Via tabela oficial ESCO (Comissão Europeia) e crosswalk SOC -> ISCO.
2. **Imputação Nível 3 (23.7%):** Média do subgrupo ocupacional pai.
3. **Imputação Nível 2 (6.0%):** Média do grande grupo ocupacional.
4. **Imputação Zero (3.4%):** Ocupações elementares/manuais sem dados de uso (Impacto = 0).

**Resultado:** Cobertura total das 435 ocupações da estrutura COD.

---

## 5. Etapa 4: Análise de Automação vs. Aprimoramento no Brasil

**Objetivo:** Analisar como a dualidade Automação/Aprimoramento se distribui no mercado brasileiro.

### Análise de Resultados e Visualizações
1. **Distribuição por Grande Grupo:**
   - Ocupações administrativas e cognitivas (Grupos 1-4) apresentam altos níveis de ambos, mas com maior `automation_share`.
   - Ocupações de suporte administrativo são o "núcleo" da automação.
2. **Relação Salário vs. Impacto:**
   - O scatterplot `salario_vs_ia_index.png` mostra que ocupações de alta renda tendem a ter maior potencial de aprimoramento, enquanto certas funções administrativas de renda média-alta têm maior risco de automação.
3. **Heterogeneidade Regional:**
   - O Sudeste e o Sul apresentam maior concentração de ocupações com alto `automation_index`, refletindo a estrutura de serviços e TIC dessas regiões.

---

## 6. Principais Achados (Resumo Executivo)

1. **Dualidade do Impacto:** A maioria das ocupações brasileiras não enfrenta apenas automação pura, mas um mix. No entanto, o setor de **Apoio Administrativo** é o mais vulnerável à substituição (Score ILO 0.553).
2. **Barreira do Trabalho Manual:** Grupos como construção, agropecuária e ocupações elementares têm exposição baixíssima ( < 0.15), servindo como um "piso" de proteção tecnológica no curto prazo.
3. **Desigualdade de Gênero:** Mulheres estão sobre-representadas em ocupações de alta exposição (G3 e G4 do gradiente ILO), principalmente em funções administrativas e de serviços especializados.
4. **Viés de Habilidade (Skill-Bias):** Existe uma correlação positiva clara entre renda e exposição. A IA generativa no Brasil afeta hoje o topo e o meio da pirâmide salarial, transformando tarefas cognitivas complexas.
5. **Robustez do Crosswalk:** A estratégia de imputação hierárquica permitiu que 100% da força de trabalho representada na PNAD fosse analisada sob a ótica da Anthropic, eliminando pontos cegos na pesquisa.

---

## 7. Estrutura de Código e Dados

- `etapa1_ia_generativa/`: Scripts de download, limpeza PNAD e índice ILO.
- `etapa2_anthropic_index/`: Processamento dos dados brutos da Anthropic V4.
- `etapa3_crosswalk_onet_isco08/`: Algoritmos de mapeamento e imputação.
- `etapa4_automation_augmentation_analysis/`: Geração de tabelas finais, relatórios PDF e visualizações avançadas.

---
*Documento gerado em 08 de Fevereiro de 2026 para fins de sumarização e transferência de contexto entre agentes de IA.*
