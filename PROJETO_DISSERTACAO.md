# Projeto de Dissertação: Impacto da IA Generativa no Mercado de Trabalho Brasileiro

## Contexto Geral

**Programa:** Mestrado Profissional em Economia - FGV-EESP  
**Aluno:** Mané  
**Orientação:** A definir

### Título Provisório
"O Impacto Potencial da Inteligência Artificial Generativa sobre o Emprego e a Desigualdade no Mercado de Trabalho Brasileiro"

### Questão-Problema
Quais ocupações e setores no Brasil estão mais expostos ao impacto da IA Generativa? Como essa exposição se correlaciona com as características dos trabalhadores (salário, escolaridade, gênero, raça, formalidade) e quais são as implicações potenciais para a desigualdade de renda no país?

---

## Metodologia Geral

A pesquisa segue uma **abordagem baseada em tarefas (task-based approach)**, dividida em duas fases principais:

### Fase 1: Exposição à IA Generativa (CONCLUÍDA ✅)

**Objetivo:** Mapear a exposição potencial do mercado de trabalho brasileiro à IA Generativa

**Metodologia:**
1. **Índice utilizado:** OIT (Gmyrek et al., 2025) - Generative AI and Jobs: A Refined Global Index of Occupational Exposure
   - Sistema de classificação: **ISCO-08** (International Standard Classification of Occupations)
   - Cobertura: ~450 ocupações detalhadas em 4 dígitos

2. **Integração com dados brasileiros:**
   - Base de dados: **PNAD Contínua (IBGE)** - microdados anuais
   - Sistema de classificação brasileiro: **COD** (Classificação de Ocupações para Pesquisas Domiciliares)
   - Correspondência realizada: **ISCO-08 ↔ COD**
   - Período analisado: 2012-2023

3. **Análise descritiva realizada:**
   - ✅ Distribuição espacial da exposição à IA por região/estado
   - ✅ Perfil demográfico por decis de exposição
   - ✅ Correlação entre exposição e:
     - Rendimento médio
     - Escolaridade
     - Gênero
     - Raça/cor
     - Tipo de vínculo (formal/informal)
     - Setor de atividade econômica

**Resultados:** Base de dados integrada ISCO-08 + PNAD Contínua com análise distributiva completa.

---

### Fase 2: Automation vs. Augmentation (EM ANDAMENTO 🔄)

**Objetivo:** Distinguir entre tarefas que a IA **substitui** (automation) vs. tarefas que a IA **complementa** (augmentation)

**Fundamentação teórica:**
- **Anthropic Economic Index Report** (Setembro 2025)
- Distinção entre 5 modos de colaboração humano-IA:
  
  **Automation (77% uso em API empresarial):**
  - `Directive` = Delegar tarefa completa para IA
  - `Feedback Loops` = Automação com ciclos de feedback
  
  **Augmentation (dominante em uso individual):**
  - `Learning` = Buscar informação/aprendizado
  - `Task Iteration` = Refinamento colaborativo de tarefas
  - `Validation` = Solicitar feedback/validação

**Fonte de dados:** Dataset público da Anthropic
- Repositório: `Anthropic/EconomicIndex` (HuggingFace)
- Sistema de classificação: **O*NET (SOC codes)** - classificação ocupacional dos EUA
- Arquivos-chave:
  - `onet_task_ratings_anthropic.csv` - Classificação de tarefas O*NET
  - `collaboration_modes_by_task.csv` - Modos de colaboração por tarefa
  - `claude_ai_conversations.csv` - Padrões de uso Claude.ai
  - `api_transcripts.csv` - Padrões de uso via API empresarial

---

## TAREFA ATUAL: Recriar Índices Automation vs. Augmentation

### Objetivo Imediato
Processar o dataset da Anthropic para criar **índices quantitativos** de automation/augmentation para cada ocupação O*NET.

### Inputs Disponíveis
1. Dataset completo baixado do HuggingFace: `Anthropic/EconomicIndex`
2. Arquivos CSV com dados brutos sobre:
   - Tarefas por ocupação O*NET
   - Frequência de cada modo de colaboração por tarefa
   - Padrões de uso (Claude.ai vs. API empresarial)

### Outputs Esperados

**Arquivo 1:** `onet_automation_augmentation_index.csv`

Estrutura mínima esperada:
```csv
onet_soc_code,occupation_title,automation_share,augmentation_share,automation_index,dominant_mode,usage_volume
15-1252.00,"Software Developers",0.65,0.35,0.30,"automation",125000
25-1021.00,"Computer Science Teachers",0.35,0.65,-0.30,"augmentation",8500
...
```

**Campos obrigatórios:**
- `onet_soc_code`: Código SOC de 8 dígitos (ex: 15-1252.00)
- `occupation_title`: Título da ocupação
- `automation_share`: % de uso em modos automation (directive + feedback_loops)
- `augmentation_share`: % de uso em modos augmentation (learning + iteration + validation)
- `automation_index`: automation_share - augmentation_share (range: -1 a +1)
  - Positivo = mais automation
  - Negativo = mais augmentation
- `dominant_mode`: "automation" ou "augmentation"
- `usage_volume`: Volume total de uso (para ponderar importância)

**Arquivo 2 (opcional):** `onet_detailed_collaboration_modes.csv`

Detalhar os 5 modos separadamente:
```csv
onet_soc_code,directive_share,feedback_loop_share,learning_share,task_iteration_share,validation_share
15-1252.00,0.45,0.20,0.15,0.12,0.08
...
```

### Metodologia de Cálculo

```python
# Pseudocódigo conceitual

# 1. Carregar dados de modos de colaboração por tarefa
collaboration_data = load("collaboration_modes_by_task.csv")

# 2. Calcular shares de automation e augmentation
automation_share = directive_share + feedback_loop_share
augmentation_share = learning_share + task_iteration_share + validation_share

# 3. Criar índice normalizado
automation_index = automation_share - augmentation_share  # range [-1, +1]

# 4. Classificar modo dominante
dominant_mode = "automation" if automation_index > 0 else "augmentation"

# 5. Agregar ao nível de ocupação O*NET (se dados vierem em nível de tarefa)
# Usar média ponderada por volume de uso
onet_level_index = groupby(onet_soc_code).agg({
    'automation_share': weighted_mean(usage_volume),
    'augmentation_share': weighted_mean(usage_volume),
    'usage_volume': sum
})
```

### Considerações Metodológicas

**Ponderação por fonte:**
- O dataset Anthropic tem dados de **duas fontes**:
  1. Claude.ai (uso individual/acadêmico) - ~50% augmentation
  2. API empresarial - ~77% automation

- **Decisão necessária:** Usar apenas API (mais relevante para mercado de trabalho) ou combinar ambas fontes?
- **Recomendação:** Criar índices separados para cada fonte e depois decidir qual usar ou como combinar

**Granularidade:**
- Verificar se dados estão em nível de **tarefa** ou **ocupação**
- Se forem tarefas, agregar para ocupação O*NET usando volume de uso como peso

**Validação:**
- Comparar com achados do relatório Anthropic:
  - Computer/Mathematical: ~44% uso API (alta automation esperada)
  - Education/Library: ~12% uso API, ~12% Claude.ai (augmentation esperada)
  - Coding: ~36% uso total (automation esperada)

---

## Próximas Etapas (Após Criação dos Índices)

### Etapa 2.1: Correspondência O*NET → ISCO-08
- Usar crosswalk oficial O*NET ↔ ISCO-08
- Transferir índices automation/augmentation para ocupações ISCO-08
- Lidar com correspondências many-to-many (possível necessidade de agregação)

### Etapa 2.2: Integração com Dados Brasileiros
- Aplicar índices ISCO-08 à base PNAD Contínua (já integrada na Fase 1)
- Criar nova análise distributiva considerando automation vs. augmentation:
  - Quais grupos demográficos estão mais expostos a automation?
  - Quais setores apresentam maior potencial de augmentation?
  - Como se relacionam exposição, automation e desigualdade salarial?

### Etapa 2.3: Análise Econômica
- Relacionar padrões automation/augmentation com:
  - Estrutura salarial brasileira
  - Polarização do mercado de trabalho
  - Implicações para políticas públicas

---

## Referências Principais

### Metodologia de Exposição à IA
1. **Gmyrek, P., Berg, J., et al. (2025).** "Generative AI and Jobs: A Refined Global Index of Occupational Exposure." ILO Working Paper.

### Automation vs. Augmentation
2. **Anthropic (2025).** "The Anthropic Economic Index Report." 
   - Dataset: https://huggingface.co/datasets/Anthropic/EconomicIndex
   - Report: 46 páginas de análise detalhada

3. **Brynjolfsson, E., et al. (2023).** "Generative AI at Work." NBER Working Paper.

### Fundamentação Teórica
4. **Acemoglu, D., & Restrepo, P. (2018).** "Low-Skill and High-Skill Automation."
5. **Acemoglu, D., & Autor, D. H. (2011).** "Skills, Tasks and Technologies: Implications for Employment and Earnings." Handbook of Labor Economics.
6. **Autor, D., Levy, F., & Murnane, R. (2003).** "The Skill Content of Recent Technological Change: An Empirical Exploration."

---

## Status do Projeto

| Etapa | Status | Observações |
|-------|--------|-------------|
| Revisão de literatura | ✅ Completo | Principais referências mapeadas |
| Escolha do índice de exposição | ✅ Completo | OIT (ISCO-08) selecionado |
| Integração ISCO-08 + PNAD | ✅ Completo | Base de dados criada |
| Análise descritiva Fase 1 | ✅ Completo | Perfil demográfico mapeado |
| Download dataset Anthropic | 🔄 Em andamento | Dataset disponível |
| Criação índices automation/augmentation | 🔄 **TAREFA ATUAL** | Processamento necessário |
| Correspondência O*NET → ISCO-08 | ⏳ Pendente | Após índices criados |
| Integração automation/augmentation + PNAD | ⏳ Pendente | Fase 2 completa |
| Redação da dissertação | ⏳ Pendente | Início previsto após análises |

---

## Contexto para o Cursor

**O que já foi feito:**
- Fase 1 completa: exposição à IA mapeada para o mercado brasileiro
- Dataset Anthropic baixado e disponível localmente

**O que preciso agora:**
- Processar os CSVs do dataset Anthropic
- Criar índices quantitativos de automation vs. augmentation por ocupação O*NET
- Gerar arquivos CSV prontos para uso futuro

**Próximo passo (futuro):**
- Fazer correspondência O*NET → ISCO-08 → aplicar ao mercado brasileiro
- Mas **por enquanto, foco apenas em criar os índices O*NET**

**Arquivos importantes:**
- `download_anthropic_data.py` - Script de download do dataset
- Dataset local: `./anthropic_economic_index/` (depois do download)
- Output esperado: `onet_automation_augmentation_index.csv`

**Desafios metodológicos esperados:**
1. Entender estrutura exata dos arquivos CSV (colunas, granularidade)
2. Decidir ponderação entre Claude.ai vs. API
3. Agregar dados de tarefas para nível de ocupação (se necessário)
4. Validar resultados contra achados do relatório Anthropic

---

## Notas Adicionais

### Por que O*NET primeiro?
- O dataset da Anthropic usa O*NET (padrão americano)
- Correspondência O*NET → ISCO-08 já existe (crosswalk oficial do Bureau of Labor Statistics)
- Mais eficiente processar dados na classificação original e depois converter

### Limitações conhecidas
- O*NET tem ~1000 ocupações; ISCO-08 tem ~450 (maior granularidade americana)
- Correspondências many-to-many vão exigir decisões de agregação
- Padrões de uso americanos (Anthropic) podem não refletir perfeitamente contexto brasileiro

### Contribuição esperada
- **Empírica:** Primeira análise automation/augmentation para mercado de trabalho brasileiro
- **Metodológica:** Adaptação de índices internacionais para classificação brasileira
- **Política:** Evidências para políticas de qualificação e proteção social

---

**Última atualização:** Janeiro 2026  
**Contato:** Mané - FGV-EESP
