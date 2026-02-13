# Etapa 3: Crosswalk e Imputação Hierárquica (O*NET -> ESCO -> ISCO-08 -> COD)

Esta etapa realiza a tradução dos índices de impacto da IA (gerados na Etapa 2) da classificação americana (O*NET/SOC) para a classificação brasileira (COD), passando pelo padrão internacional (ISCO-08).

## Metodologia Final (Híbrida e Hierárquica)

Para garantir 100% de cobertura das ocupações brasileiras e máxima precisão, utilizamos uma abordagem em 4 estágios:

### 1. Crosswalk O*NET -> ISCO-08 (via ESCO)
Utilizamos a tabela oficial de correspondência da Comissão Europeia (**ESCO-O*NET Crosswalk**) como ponte primária.
- **Match Direto:** Quando o arquivo ESCO forneceu o código ISCO-08 diretamente.
- **Fallback Robusto:** Para casos onde o ESCO fornecia apenas URIs sem código explícito, utilizamos a cadeia tradicional `SOC 2018 -> SOC 2010 -> ISCO-08` para não perder dados.
- **Agregação:** Como o mapeamento é N:N, os índices foram agregados pela média ponderada pelo volume de uso da Anthropic.

### 2. Mapeamento ISCO-08 -> COD (Brasil)
Integração direta baseada na estrutura COD do IBGE, que é derivada da ISCO-08.
- **Resultado Inicial:** Cobertura de **66.9%** das ocupações brasileiras (match direto de 4 dígitos).

### 3. Imputação Hierárquica (Preenchimento de Lacunas)
Para os 33.1% das ocupações sem match direto, aplicamos a lógica de imputação baseada na estrutura da árvore ocupacional:
- **Nível 3 (Pai):** Se não há dado para "Gerente de Filial" (1346), usa-se a média do subgrupo "Gerentes de Serviços Profissionais" (134). (**23.7%** dos casos)
- **Nível 2 (Avô):** Se não há dado no subgrupo, usa-se a média do Grande Grupo (ex: "Diretores e Gerentes"). (**6.0%** dos casos)

### 4. Imputação de Zeros (Ocupações Elementares)
Para as **3.4%** das ocupações restantes (geralmente trabalhos manuais/elementares como "Carregadores de água" ou "Vendedores ambulantes") que não possuem dados nem nos níveis superiores da base Anthropic:
- Assumimos **Impacto = 0.0** (Automação e Augmentation nulos).
- Justificativa: Baixíssima exposição tecnológica a LLMs e ausência de dados de uso.

## Resultados Finais

O arquivo final `outputs/cod_automation_augmentation_index_final.csv` contém índices para **todas as 435 ocupações** da estrutura COD.

| Método de Obtenção do Dado | Ocupações | % do Total |
| :--- | :--- | :--- |
| **Match Direto (Alta Precisão)** | 291 | **66.9%** |
| **Média do Subgrupo (Estimativa)** | 103 | 23.7% |
| **Média do Grande Grupo (Estimativa)** | 26 | 6.0% |
| **Imputação Zero (Sem Exposição)** | 15 | 3.4% |

**Total:** 100% de Cobertura.

## Estrutura de Arquivos
- `src/01_crosswalk_esco_method.py`: Crosswalk internacional (O*NET -> ISCO).
- `src/02_map_to_cod.py`: Mapeamento para estrutura brasileira.
- `src/03_hierarchical_imputation.py`: Algoritmo de preenchimento hierárquico.
- `outputs/cod_automation_augmentation_index_final.csv`: Tabela pronta para análise com a PNAD.
