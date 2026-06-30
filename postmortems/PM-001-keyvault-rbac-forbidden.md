# PM-001 — Key Vault RBAC forbidden errors

**Date:** 2026-06-23
**Severity:** Medium
**Layer:** Infrastructure setup

## Issue 1 — Personal account blocked from creating secrets 

### What broke
Received "Forbidden" error when trying to create secrets
in Key Vault kv-bank-etl-dev01 via Azure Portal.

Error code: Forbidden
Action: Microsoft.KeyVault/vaults/secrets/setSecret/action

### Root cause
Key Vault was created with Azure RBAC permission model.
Even as the resource creator, you need an explicit role
assignment to manage secrets — creation does not
automatically grant secret management rights.

### Fix
Assigned "Key Vault Secrets Officer" role to own Azure
account via:
Key Vault → Access control (IAM) → Add role assignment
→ Key Vault Secrets Officer → select own account

Waited 2-3 minutes for RBAC propagation before retrying.

### Prevention
When creating Key Vault, immediately assign yourself
"Key Vault Secrets Officer" role before attempting
any secret operations. RBAC propagation takes 2-3
minutes — always wait before retrying.

---

## Issue 2 — Databricks identity blocked from reading secrets

### What broke
After successfully adding secrets, notebook threw:
Py4JJavaError: PERMISSION_DENIED on dbutils.secrets.get()

Full error:
DatabricksServiceHttpClientException: PERMISSION_DENIED
Invalid permissions on the specified KeyVault
Caller: name=AzureDatabricks;appId=2ff814a6-...
Action: Microsoft.KeyVault/vaults/secrets/getSecret/action

### Root cause
Databricks uses its own managed identity (AzureDatabricks
app) to call Key Vault at notebook runtime — completely
separate from your personal Azure account.
Both identities need Key Vault access independently.
Fixing personal account access does not fix Databricks
runtime access.

### Fix
Assigned "Key Vault Secrets User" role to AzureDatabricks
managed identity via:
Key Vault → Access control (IAM) → Add role assignment
→ Key Vault Secrets User → search "AzureDatabricks"
→ select it → assign

Waited 2-3 minutes for RBAC propagation before retrying.

### Prevention
Whenever creating a Databricks-backed Key Vault secret
scope, always grant BOTH:
- Your personal account → Key Vault Secrets Officer
- AzureDatabricks app  → Key Vault Secrets User

Do this immediately after Key Vault creation, before
writing any notebook code that calls dbutils.secrets.get()

### Outcome
After both role assignments, Cell 4 (OAuth config) ran
successfully:
ADLS OAuth configuration set successfully
Storage account : sadatabanketldev01
Client ID       : [REDACTED — stored in Key Vault]
Tenant ID       : [REDACTED — stored in Key Vault]