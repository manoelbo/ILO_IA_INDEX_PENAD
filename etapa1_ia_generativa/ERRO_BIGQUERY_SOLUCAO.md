# 🔧 ERRO IDENTIFICADO: Permissões do BigQuery

## Problema
```
403 Access Denied: User does not have permission to query table
```

## Causa
O projeto "dissertacao-ia-br" não tem permissões configuradas corretamente para acessar o BigQuery.

## Solução - Siga estes passos:

### 1. Ativar a API do BigQuery
```bash
gcloud services enable bigquery.googleapis.com --project=dissertacao-ia-br
```

### 2. Verificar se o billing está ativado
Acesse: https://console.cloud.google.com/billing/projects

- Se não tiver billing vinculado, vincule uma conta de cobrança
- BigQuery tem 1TB/mês grátis, então esta query não custará nada

### 3. Aceitar termos de uso do BigQuery
Acesse: https://console.cloud.google.com/bigquery?project=dissertacao-ia-br

- Na primeira vez, o BigQuery pedirá para aceitar os termos
- Clique em "Aceitar" ou "Accept"

### 4. Verificar se está usando o projeto correto
```bash
gcloud config get-value project
# Deve retornar: dissertacao-ia-br

# Se não estiver, configure:
gcloud config set project dissertacao-ia-br
```

### 5. Tentar novamente com reauth
Após fazer os passos acima, execute:
```bash
cd etapa1_ia_generativa/src
python 01_download_pnad.py --reauth
```

---

## Alternativa: Verificar Project ID correto

Execute este comando para listar seus projetos:
```bash
gcloud projects list
```

Verifique se "dissertacao-ia-br" aparece na lista. Se não, você pode ter criado com outro nome.

---

## AGUARDANDO RESOLUÇÃO

Após seguir estes passos, me avise que posso continuar! 🚀
