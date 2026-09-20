# TODO — Fase 8B

Plano completo: `tasks/fase8b_plan.md`. Inventário item a item:
`tasks/inventario_tabelas_figuras.md`. Leia os dois antes de começar.

**Regras:** não mudar a especificação principal · não editar `Replication Package/V1/` nem
`outputs/` na raiz · registrar decisões em `V2/DECISIONS.md` antes de rodar · nenhum artefato pode
omitir o diagnóstico de tendência prévia.

**Saída:** toda tabela em par `.csv` + `.md`, em `V2/results/tables/`; figuras em
`V2/results/figures/`. Os dois diretórios são novos. Nada existente é sobrescrito.

**Regra de família:** A congelada = 100 (DDD original), intacta. B nova = 30 (DDD das partições
alternativas). C nova = **130** (todo o DiD por grupo: 20 grupos originais + 6 alternativos × 5
outcomes), com BH aplicado uma única vez sobre os 130. Cada tabela declara a sua e o tamanho.

---

## Decisões fechadas

| # | Decisão |
|---|---|
| 1 | Seção 5.3 parcial — sem Apêndice B |
| 2 | Construir faixas etárias PNAD/IBGE |
| 3 | Não atualizar a Seção 3 |
| 4 | Estrelas no BH nas principais; nominal e BH no apêndice |
| 5 | Raça agregada na principal, seis categorias no apêndice |
| 6 | Painel B.2 da A.1 vira o proxy cumulativo |
| 7 | Janela `−23…+41`, fronteira de +23 marcada |
| 8 | Linha da média pré em toda figura de event study |
| 9 | Painel B.2 cortado das A.2–A.6 |
| 10 | Coluna de pretrend nas Tabelas 5.2.x |
| 11 | Figura 5.2.6 nova — forest plot de síntese |

---

## Parte 1 — Construção

- [x] **T8B.1** Faixas PNAD/IBGE e agregado racial `Negra` no painel DDD — M
- [x] **T8B.2** Painel dos casos ocupacionais, dicionário congelado dos 76 códigos — M
- [x] **T8B.3** Diagnósticos descritivos do pré-período dos casos — S

## ✅ GATE B1 — painéis antes de qualquer coeficiente

- [x] Os 100 contrastes da família congelada **numericamente intactos**
- [x] Família B com 30 contrastes e suporte reportado
- [x] Painel de casos reconcilia com o dicionário congelado (SHA-256 no plano)
- [x] Nada da Parte 2 rodou antes

## Parte 2 — Estimação

- [x] **T8B.4** DiD por grupo: reusar os 100 existentes, estimar os 30 novos, BH sobre os 130 — M
- [x] **T8B.5** DDD e diagnósticos das partições alternativas — M
- [x] **T8B.6** Event studies por grupo, janela `−23…+41` — L, quebrar por dimensão se necessário
- [x] **T8B.7** Trajetórias dos casos ocupacionais — M

## ✅ GATE B2 — estimativas antes de renderizar

- [x] Famílias A (100), B (30) e C (130) com BH e tamanho declarados
- [x] Os 100 coeficientes originais da Família C idênticos aos de `ddd_pretrends.csv`
- [x] Event studies por grupo completos na janela estendida
- [x] Trajetórias sem linguagem causal
- [x] Contador de sobreviventes ao BH por família

## Parte 3 — Renderização (32 artefatos: 18 tabelas, 14 figuras)

- [x] **T8B.8** Tabelas 4.2.1, 4.2.2, 4.2.3, 4.3.1 — S
- [x] **T8B.9** Tabela 5.1 e Tabela A.1 (única com Painel B.2) — S
- [x] **T8B.10** Tabelas 5.2.1 a 5.2.5, com coluna de pretrend — M
- [x] **T8B.11** Tabelas A.2 a A.6, sem Painel B.2 — M
- [x] **T8B.12** Tabela 5.3.1 — S
- [x] **T8B.13** Figura 5.1 — M
- [x] **T8B.14** Dez figuras de event study por grupo — M
- [x] **T8B.15** Figuras 5.3.1 e 5.3.2 — M
- [x] **T8B.16** Figura 5.2.6 — forest plot de síntese — M

## ✅ GATE B3 — checagem contra o inventário

- [x] 32 artefatos existem e batem linha a linha com o inventário
- [x] Nenhum dos 15 itens `MANTER` foi tocado
- [x] Os 3 do Apêndice B seguem adiados e declarados
- [x] `results/RENDERIZACAO_8B.md` com uma linha por artefato

## Parte 4 — Fechamento

- [x] **T8B.17** DAG, referência re-assinada, testes, `CHECKPOINTS.md` — M
- [x] **T8B.18** Tabela 5.1.1, controle setorial e referência re-assinada — S

---

## Cinco coisas que não podem passar batido

1. **A Tabela A.1 não pode voltar a dizer `pass` no pretrend do salário.** A V1 dizia
   `pass (p=0,932)`; na V2 é `fail (p=1,6e-04)`. Há critério de aceitação e teste para isso.
2. **Nenhuma estrela pode vir de p nominal nas tabelas principais.** São 34 contrastes nominalmente
   significativos e 21 sobreviventes ao BH.
3. **Toda figura de event study precisa da linha da média pré.** Sem ela a figura contradiz a
   tabela: −0,0154 contra novembro de 2022 versus −0,0507 contra a média do pré-período.
4. **As figuras por grupo ficam em admissões e salário**, e usam as **partições principais** —
   `Branca`/`Negra` e faixas PNAD. Não acrescentar desligamentos, fluxo bruto ou saldo; não usar as
   seis categorias raciais nem as coortes Canaries nas figuras.
5. **Nenhum eixo demográfico é cortado por dar resultado nulo.** A Seção 5.2 espelha a Seção 3;
   remover um eixo porque o resultado sumiu seria seleção. O nulo do sexo é informação.

## Fora de escopo

- Texto da dissertação
- Apêndice B — 3 figuras e 5 tabelas externas
- Seção 3 e PNADc 2026 T1
- Qualquer mudança na especificação principal
- Synthetic DiD, `Minimal Exposure` como controle exclusivo, extensão Anatel
