# Etapa 2: Índice Anthropic de Automação vs. Aumentação

Este projeto recria o índice de automação vs. aumentação da Anthropic para ocupações O*NET-SOC (6 dígitos).

## Objetivo
Gerar uma tabela com scores de automação e aumentação que possa ser usada em um crosswalk futuro para ISCO-08 e PNAD.

## Dados Utilizados
- Anthropic Economic Index (Release 2025-03-27)
- O*NET Task Statements

## Metodologia
- **Automação**: Soma dos ratios `directive` e `feedback_loop`.
- **Aumentação**: Soma dos ratios `validation`, `task_iteration` e `learning`.
- Os scores são calculados para cada tarefa e depois agregados por ocupação (SOC 6-dígitos) através da média simples.

## Estrutura de Pastas
- `config/`: Configurações de caminhos e constantes.
- `src/`: Scripts de processamento.
- `src/utils/`: Funções auxiliares.
- `data/processed/`: Tabelas resultantes.
- `outputs/`: Logs, tabelas e figuras.

## Como Executar
1. Instale as dependências: `pip install -r requirements.txt`
2. Execute o script principal: `python src/01_process_anthropic_data.py`

## Tabela Resultante
O arquivo final é salvo em `data/processed/anthropic_index_soc6.csv`.
