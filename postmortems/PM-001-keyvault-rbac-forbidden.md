# PM-001 — Key Vault secrets creation blocked by RBAC

**Date:** 23-06-2026
**Step:** 16.2 — Adding secrets to Azure Key Vault

## What broke
Received "Forbidden" error when trying to create secrets
in Key Vault kv-bank-etl-dev01.

Error: The operation is not allowed by RBAC.
Action: Microsoft.KeyVault/vaults/secrets/setSecret/action

## Root cause
Key Vault was created with Azure RBAC permission model.
Even as the resource creator, you need an explicit role
assignment to manage secrets — creation does not
automatically grant secret management rights.

## Fix
Assigned "Key Vault Secrets Officer" role to own Azure
account via IAM → Add role assignment on the Key Vault.
Waited 2-3 minutes for RBAC propagation before retrying.

## Prevention
When creating Key Vault, either:
Option A → Switch permission model to "Vault access policy"
           which grants creator full access automatically.
Option B → Immediately assign Key Vault Secrets Officer
           role after creation before attempting any
           secret operations.