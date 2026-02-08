# Etapa 2: Anthropic Economic Index (V4 - Jan 2026)

Esta etapa replica a metodologia da Anthropic para classificar ocupações O*NET entre **Automation** (Substituição) e **Augmentation** (Complementariedade), utilizando os dados mais recentes do relatório de Janeiro de 2026.

## Metodologia

Os modos de colaboração humano-IA identificados pela Anthropic foram agrupados da seguinte forma:

- **Automation (Automação):**
  - `directive`: Usuário delega a tarefa completa.
  - `feedback loop`: Automação com ciclos de feedback.
- **Augmentation (Aprimoramento):**
  - `learning`: Uso para aprendizado e busca de informação.
  - `task iteration`: Refinamento colaborativo.
  - `validation`: Solicitação de feedback sobre o trabalho.

Os dados foram processados tanto para a plataforma **Claude.ai** (consumidor/acadêmico) quanto para a **1P API** (enterprise), revelando a dualidade de uso reportada pela Anthropic.

## Estrutura de Arquivos

- `config/settings.py`: Configurações de caminhos e constantes metodológicas.
- `src/01_process_anthropic_data.py`: Script principal de processamento e agregação.
- `src/utils/aggregation.py`: Utilitários para cálculo de índices e médias ponderadas.
- `outputs/onet_automation_augmentation_index.csv`: Tabela final com os índices por ocupação SOC 6-digit.

## Como Executar

1. Certifique-se de ter os dados brutos no diretório `EconomicIndex/release_2026_01_15/data/intermediate/`. Caso sejam apenas ponteiros LFS, o script de processamento tentará verificar.
2. Execute o script:
   ```bash
   python3 etapa2_anthropic_index/src/01_process_anthropic_data.py
   ```

## Resultados

A tabela final (`outputs/onet_automation_augmentation_index.csv`) contém os shares e o índice de automação (`automation_index`) para cada ocupação, onde:
- **Índice > 0:** Predomínio de Automação.
- **Índice < 0:** Predomínio de Augmentation.

Esta tabela será utilizada na Etapa 3 para realizar o crosswalk O*NET → ISCO-08 e analisar o impacto no mercado de trabalho brasileiro.
