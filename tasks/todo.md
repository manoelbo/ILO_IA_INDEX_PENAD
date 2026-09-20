# TODO — Replication Package V2

Plano completo: `tasks/plan.md`. **Leia a seção "LEIA ISTO PRIMEIRO" e a §1 (Verdade de campo)
antes de começar qualquer tarefa.**

Regras: não edite `Replication Package/V1/` · não escolha especificação depois de ver p-valor ·
registre toda decisão em `Replication Package/V2/DECISIONS.md`.

**Checkpoints bloqueantes: A, B, F.** Nesses, pare e reporte. Os demais (C, D, E, G, H) você
cumpre, registra e segue.

**Decisões já fechadas pelo autor (25/07/2026) — não reabrir:**
1. Corte = **2026-05**. Sem esperar junho. 65 competências, 195 arquivos.
2. **Checkpoint C não bloqueia** — seguir direto qualquer que seja o delta.
3. **Painel PNADc de 16 trimestres fica fora** desta rodada.

---

## Fase 0 — Ambiente e congelamento

- [ ] **T1** Provisionar ambiente Python da V2 (`V2/pyproject.toml`, versões exatas) — S
- [ ] **T2** Provisionar ambiente R (`fixest`, `HonestDiD`, `data.table`) — XS
- [ ] **T3** Verificar a V1 a partir de `V1/`, escrever `V1/FROZEN.md`, corrigir `V2/README.md` — S

### ✅ CHECKPOINT A — Fundação · **BLOQUEANTE**
- [ ] Ambientes provisionados e versionados
- [ ] V1 reproduz de `V1/` e está congelada
- [ ] ≥15 GiB livres confirmados
- [ ] **PARAR se a fundação estiver quebrada**

---

## Fase 1 — Ingestão do vintage

- [ ] **T4** Inventário do FTP — corte **já fixado em 2026-05**, 195 arquivos — S
- [ ] **T5** Downloader com retomada, tentativas e SHA-256 (~3 GB, 10–20 min) — M
- [ ] **T6** Parser de competência com validação de domínio (UTF-8, `;`, decimal vírgula) — M
- [ ] **T7** Construir MOV + FOR − EXC, particionado por `competenciamov` — M
- [ ] **T8** Reconciliação V1 vs V2 (delta de 2021 deve ser ~+8%) — M
- [ ] **T9** Curva de completude + continuidade das variáveis + regra de janela — M

### ✅ CHECKPOINT B — Vintage congelado · **BLOQUEANTE**
- [ ] 195 arquivos com hash e manifesto completo
- [ ] Movimentações sem buracos, `peso` ∈ {+1, −1}
- [ ] Delta de ~+8% em 2021 confirmado — **se não for, o parser está errado: PARAR**
- [ ] Regra de janela decidida e registrada — **se T9b mostrar diferencial >1 p.p. entre tratado e
      controle, PARAR e reportar antes de escolher**

---

## Fase 2 — Painel analítico

- [ ] **T10** Congelar o crosswalk por hash (não raspar o site do MTE) — S
- [ ] **T11** Reproduzir a classificação de tratamento atual (0/31/31/13/95/266/193) — S
- [ ] **T12** Painel nacional CBO4 × mês, com missingness corrigida — M
- [ ] **T13** Painel enriquecido CBO4 × CNAE × mês — guardar `secao` **e** `divisao` — S
- [ ] **T14** ★ **GATE** — rodar o modelo antigo no painel novo e medir o delta — M

### ✅ CHECKPOINT C — ★ Medição de referência · **NÃO bloqueante**
- [ ] Painéis construídos, sem salário em célula de fluxo zero
- [ ] Delta por outcome quantificado, com mudança de sinal/significância declarada
- [ ] Resultado no **topo** de `RECONCILIACAO.md`, repetido no `COMPARACAO_V1_V2.md`
- [ ] **SEGUIR direto para a Fase 3**, qualquer que seja o delta (autorizado pelo autor)

---

## Fase 3 — Tratamento

- [ ] **T15** Quatro variantes de gradiente (A base, B ponderada, C só DP-tarefa, D rótulos) — M

### ✅ CHECKPOINT D — Tratamento
- [ ] Variantes comparadas; principal e sensibilidades declaradas **antes** de estimar

---

## Fase 4 — Núcleo econométrico

- [ ] **T16** Módulo de estimação: PPML principal, sem controles contemporâneos; efeitos fixos e
      clusterização como **parâmetros**, não fixos no código — M
- [ ] **T17** Event study balanceado −23…+23, sem agrupamento de caudas — M
- [ ] **T18** Escada de controles, amostras e medida de exposição (efeitos fixos no nível 1) — M
- [ ] **T18b** Escada de efeitos fixos: nível 1 e 2 co-principais · nível 3 como diagnóstico ·
      clusterização bidirecional CBO4 × **divisão** CNAE — M

### ✅ CHECKPOINT E — Núcleo
- [ ] PPML converge; convenção única de janela
- [ ] Escada de controles completa (T18)
- [ ] Níveis 1 e 2 lado a lado, com a diferença entre eles comentada
- [ ] **Tabela de coexistência tratado/controle publicada ANTES dos coeficientes de nível 2 e 3**
- [ ] Nível 3 enquadrado como diagnóstico de suporte, não como teste de robustez

---

## Fase 5 — Diagnóstico

- [ ] **T19** Pretrends sobre o modelo e a amostra exatos — M
- [ ] **T20** HonestDiD em R: maior M para o qual o intervalo exclui zero — M
- [ ] **T21** Multiplicidade: p nominal e p ajustado lado a lado — M
- [ ] **T22** Falsificação: placebo temporal dez/2021 + placebo de grupo — M

### ✅ CHECKPOINT F — Diagnóstico · **BLOQUEANTE**
- [ ] Três testes de pretrend nomeados distintamente
- [ ] **Placebo temporal nacional não significativo a 5%** — se for significativo, o desenho não se
      sustenta: PARAR e reportar. Não ajustar especificação para consertar o placebo.

---

## Fase 6 — Mecanismos

- [ ] **T23** ★ Decomposição de desligamentos (31 demissão / 40 pedido / 43+45 fim contrato) — M
- [ ] **T24** Proxy de estoque por saldo acumulado normalizado — S
- [ ] **T25** Salário-hora via `horascontratuais` (validar continuidade antes) — S
- [ ] **T26** Porte (`tamestabjan`) e falsificação público vs privado — S
- [ ] **T27** Sensibilidade da medida: vintage 2023, discordância GPT-4o vs Gemini, Anthropic — M

### ✅ CHECKPOINT G — Mecanismos
- [ ] Todo exercício com tabela de suporte e p ajustado

> **NÃO IMPLEMENTAR:** admissões por primeiro emprego (P2.2 original). A variável morre entre
> abr e jul/2021 — 99% viram "Tipo Ignorado" 18 meses antes do evento. Ver `plan.md` §1.6.

---

## Fase 7 — Empacotamento

- [ ] **T28** Contratos semânticos + validação de `results/reference` por manifesto — M
- [ ] **T29** `run_replication.py` que **re-estima tudo**, não renderiza CSV congelado — M
- [ ] **T30** Suíte de testes (10 gates, incluindo a camada de construção) — M
- [ ] **T31** Replicação cruzada Python ↔ R a seis decimais — M
- [ ] **T32** `COMPARACAO_V1_V2.md` — S

### ✅ CHECKPOINT H — Pacote pronto
- [ ] Suíte passa · replicação cruzada concorda · comparação V1/V2 completa
- [ ] **Entregar. O texto da dissertação é uma rodada separada.**

---

## Fora de escopo — não implementar

- Texto da dissertação (rodada separada)
- Painel PNADc de 16 trimestres
- Admissões por primeiro emprego (variável morre em 2021)
- Validação de difusão via Google Trends (adiada para a rodada do texto — convida a garimpo de
  data de corte e não muda nenhuma estimativa)
- Extensão Anatel / conectividade municipal
- Atualização da Seção 3 / PNADc 2026 Q1
- RAIS
- Base dos Dados paga (uso gratuito só como validação opcional até 2025-11)

Se surgir uma questão nova que exija decisão do autor durante a execução: **pare, registre em
`V2/DECISIONS.md` e pergunte.** Não escolha por conta própria.
