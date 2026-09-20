# TODO — Fase 8A

Plano completo: `tasks/fase8a_plan.md`. Leia "LEIA ISTO PRIMEIRO" e a seção de contexto antes de
começar.

**Regras:** não escolher especificação por p-valor nem por resultado de pretrend · não editar
`Replication Package/V1/` · registrar decisões em `V2/DECISIONS.md` antes de rodar · esta fase
**não constrói dados novos**, só diagnostica o que já existe.

**Decisões fechadas:** referência = **novembro de 2022** (já é o que a V2 usa) · sem tocar no texto
da dissertação · Fase 8B só depois do Gate 8A.

---

## Parte 1 — Diagnósticos

- [x] **T8A.1** Pretrend na amostra 2022-01 **+ teste de poder com leads pareados na amostra
      completa** — M
      → `pretrend_sample_2022.csv`, `pretrend_power_check.csv`
      → **resultado: `violation_not_specific_to_2021` nos cinco outcomes**
- [x] **T8A.2** Pretrend no nível 2 (CNAE × mês), lado a lado com o nível 1 — M
      → `pretrend_level2.csv` · 10 modelos, 10 falham
- [x] **T8A.3** Pretrend na exposição contínua e no controle ampliado com `Minimal Exposure` — S
      → `pretrend_ladder_variants.csv` · 10 modelos, 10 falham
- [x] **T8A.4** Pretrend do DDD + pretrend por grupo + poder por grupo — M
      → `ddd_pretrends.csv` · 100 contrastes · DDD: 2 passam, 5 aviso, 93 falham
- [x] **T8A.5** Especificação com controle de tendência pré — M
      → `pretrend_control_specification.csv` · três especificações × cinco outcomes
- [x] **T8A.6** Pretrend do salário restrito a CBOs com cobertura salarial completa — S
      → `pretrend_wage_balanced_coverage.csv` · 333 de 341 CBOs retidas, continua falhando

## Parte 2 — Correções da V2

- [x] **T8A.7** Estimar os quatro horizontes longos — M
      → `long_run_horizon_estimates.csv` · reconcilia com o estático em 5,8e-05
- [x] **T8A.8** Corrigir o enquadramento do HonestDiD no README e no COMPARACAO — S
      → mais `tests/test_estimand_framing.py`, que falha se a justaposição voltar
- [x] **T8A.9** Acrescentar DeltaSD ao lado de DeltaRM — M
      → `R/honest_did_sd.R`, idempotente, não recalcula o DeltaRM

---

## ✅ GATE 8A — **BLOQUEANTE**

- [x] Seis diagnósticos com artefato
- [x] Teste de poder reportado **junto** com o resultado da amostra de 2022, nunca separado
      (garantido por teste: as colunas do poder vivem no mesmo arquivo)
- [x] Quatro horizontes estimados e reconciliando com o coeficiente estático
- [x] HonestDiD com janela e estimando declarados nos dois documentos
- [x] `DIAGNOSTICO_PRETRENDS.md` com a tabela única: especificação × outcome × 3 testes × veredito
- [x] `DECISIONS.md` atualizado, **sem recomendar mudança de especificação principal**
- [ ] **PARAR e entregar ao autor**

---

## O que o Gate 8A concluiu

1. **A hipótese da pandemia não se sustenta.** Restringir a amostra a 2022 não muda nada: os
   p-valores da amostra de 2022 são praticamente idênticos aos da amostra completa com os mesmos
   leads. A violação está dentro de 2022.
2. **Nenhuma das 51 células diagnosticadas passa.** Amostra de 2022, nível 2, nível 2 bidirecional,
   exposição contínua, `Minimal Exposure` como controle e cobertura salarial completa: todas
   falham.
3. **Onde a hipótese mais fraca do DDD é defensável, não há heterogeneidade.** Os sete contrastes
   DDD que sobrevivem ao diagnóstico são todos de salário e todos têm coeficiente perto de zero
   com p ajustado bem acima de 0,05.
4. **O efeito salarial não está concentrado no fim da janela.** Os quatro horizontes são estáveis.
   A distância entre o coeficiente estático e a média pós do event study vem da normalização em
   novembro de 2022, não da janela.
5. **Controlar pela tendência prévia não anula os coeficientes** — ao contrário de Humlum e
   Vestergaard (2025). Eles ficam praticamente iguais e mais precisos.

---

## Fora de escopo nesta fase

- Texto da dissertação
- Geração de tabelas e figuras (Fase 8B)
- DiD por grupo completo com ajuste de multiplicidade (só o diagnóstico da T8A.4)
- Casos ocupacionais da Seção 5.3
- Faixas etárias PNAD
- Synthetic DiD e `Minimal Exposure` como controle exclusivo
