# 🔧 SOLUÇÃO DEFINITIVA: Erro 403 BigQuery + basedosdados

## O Problema
```
403 Access Denied: User does not have permission to query table 
basedosdados:br_ibge_pnad_continua.microdados
```

## ⚠️ O que está FALTANDO

Mesmo com API e billing ativados, faltam **3 coisas essenciais**:

1. **Role IAM `BigQuery User`** no seu projeto
2. **Aceitar os Termos de Serviço** via interface web
3. **Primeira autorização** com o basedosdados

---

## 🚀 PASSO A PASSO

### PASSO 1: Adicionar Role BigQuery User

Abra o terminal e execute:

```bash
# Primeiro, verifique seu email autenticado
gcloud config list account --format="value(core.account)"

# Adicione a role BigQuery User ao seu usuário
gcloud projects add-iam-policy-binding dissertacao-ia-br \
  --member="user:SEU_EMAIL@gmail.com" \
  --role="roles/bigquery.user"
```

**OU via Console:**
1. Acesse: https://console.cloud.google.com/iam-admin/iam?project=dissertacao-ia-br
2. Clique em **Grant Access** (Conceder Acesso)
3. Adicione seu email como **Principal**
4. Selecione o role: **BigQuery > BigQuery User**
5. Clique em **Save**

---

### PASSO 2: Aceitar Termos de Serviço (CRÍTICO!)

**Este é o passo que você provavelmente NÃO fez:**

1. Acesse: https://console.cloud.google.com/bigquery?project=dissertacao-ia-br

2. No painel do BigQuery, execute esta query simples:
   ```sql
   SELECT 1
   ```

3. **Se aparecer qualquer diálogo** de:
   - "Enable BigQuery API" → Aceite
   - "Accept Terms of Service" → Aceite
   - "Enable billing for queries" → Aceite

4. **IMPORTANTE**: Também acesse o dataset público do basedosdados:
   - Na barra de pesquisa do BigQuery Explorer, digite: `basedosdados`
   - Clique em "Add" quando aparecer o projeto `basedosdados`
   - Tente fazer preview de qualquer tabela
   - **Aceite qualquer diálogo que aparecer**

---

### PASSO 3: Testar Autenticação

Abra um terminal e execute:

```bash
# Renovar credenciais (importante!)
gcloud auth application-default login

# Confirme que está usando o projeto correto
gcloud config set project dissertacao-ia-br
```

---

### PASSO 4: Testar com Script Simples

Antes de rodar o pipeline completo, teste com:

```bash
cd /Users/manebrasil/Documents/Projects/Dissetação\ Mestrado/etapa1_ia_generativa
python -c "
import basedosdados as bd
print('Testando conexão...')
df = bd.read_table(
    dataset_id='br_ibge_pnad_continua',
    table_id='microdados',
    billing_project_id='dissertacao-ia-br',
    limit=10,
    use_bqstorage_api=False
)
print('SUCESSO!')
print(df.head())
"
```

---

## 🆘 SE AINDA NÃO FUNCIONAR: Criar Novo Projeto

Se após todos os passos ainda der erro, crie um projeto novo limpo:

### Opção A: Via Terminal
```bash
# Criar novo projeto
gcloud projects create mestrado-pnad-2026 --name="Mestrado PNAD"

# Ativar BigQuery API
gcloud services enable bigquery.googleapis.com --project=mestrado-pnad-2026

# Linkar billing (substitua BILLING_ACCOUNT_ID pelo seu)
gcloud billing accounts list  # para ver os IDs
gcloud billing projects link mestrado-pnad-2026 --billing-account=BILLING_ACCOUNT_ID

# Definir como projeto padrão
gcloud config set project mestrado-pnad-2026

# Re-autenticar
gcloud auth application-default login
```

### Opção B: Via Console (mais fácil)
1. Acesse: https://console.cloud.google.com/projectcreate
2. Nome: `mestrado-pnad-2026`
3. Após criar, vá em Billing e vincule uma conta
4. Acesse BigQuery e aceite os termos
5. Atualize o `config/settings.py` com o novo Project ID

---

## 📋 Checklist Final

- [ ] BigQuery API está ativada
- [ ] Billing está vinculado ao projeto
- [ ] Role `BigQuery User` está atribuída ao seu usuário
- [ ] Você acessou BigQuery pelo Console e executou uma query
- [ ] Você adicionou e visualizou o projeto `basedosdados` no BigQuery Explorer
- [ ] Você executou `gcloud auth application-default login` recentemente
- [ ] O `GCP_PROJECT_ID` no `config/settings.py` está correto

---

## 🔍 Comandos de Diagnóstico

```bash
# Ver projeto atual
gcloud config get-value project

# Ver conta autenticada
gcloud auth list

# Ver roles do projeto
gcloud projects get-iam-policy dissertacao-ia-br --format=json | grep -A2 "manebrasil"

# Testar BigQuery diretamente (sem basedosdados)
bq query --use_legacy_sql=false "SELECT 1"

# Ver se API está ativada
gcloud services list --enabled --project=dissertacao-ia-br | grep bigquery
```

---

## ⏱️ Próximo Passo

Após seguir este guia, execute:

```bash
cd /Users/manebrasil/Documents/Projects/Dissetação\ Mestrado/etapa1_ia_generativa/src
python 01_download_pnad.py --reauth
```

---

**Data:** 2026-01-11
**Status:** Aguardando resolução
