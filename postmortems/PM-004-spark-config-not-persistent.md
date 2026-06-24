# PM-004 — Spark OAuth config does not persist between notebooks

**Date:** 2026-06
**Severity:** Low — expected behaviour, not a bug
**Layer:** Silver notebook — Cell 4 reading Bronze

## What broke
Silver notebook Cell 4 threw KeyProviderException when
reading Bronze Delta table from ADLS:

Failure to initialize configuration for storage account
sadatabanketldev01.dfs.core.windows.net:
Invalid configuration value detected for fs.azure.account.key

## Root cause
Spark session configuration set via spark.conf.set() in
one notebook does NOT carry over to another notebook.
Each Databricks notebook runs in its own execution context.
The OAuth config added in the Bronze notebook was completely
invisible to the Silver notebook session.

This is expected Databricks behaviour — not a bug.

## Fix
Added the full ADLS OAuth configuration block to every
notebook that accesses ADLS paths. This block must always
appear after the config cell (so cfg is available) and
before any ADLS read or write operation.

## Rule going forward
Every notebook in this project that touches ADLS must have
the OAuth config cell. Standard position is Cell 4, after
config is loaded in Cell 3.

Template:
client_id     = dbutils.secrets.get(scope, key)
client_secret = dbutils.secrets.get(scope, key)
tenant_id     = dbutils.secrets.get(scope, key)
spark.conf.set(fs.azure.account.auth.type..., "OAuth")
spark.conf.set(fs.azure.account.oauth.provider.type..., ...)
spark.conf.set(fs.azure.account.oauth2.client.id..., ...)
spark.conf.set(fs.azure.account.oauth2.client.secret..., ...)
spark.conf.set(fs.azure.account.oauth2.client.endpoint..., ...)

## Prevention
Create a reusable configure_adls_oauth() function in
src/utils/ that any notebook can call in one line.
Implement this in the next refactor pass.