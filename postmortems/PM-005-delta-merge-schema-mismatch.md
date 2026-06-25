# PM-005 — Delta MERGE schema mismatch on fact_transactions

**Date:** 2026-06
**Severity:** High — pipeline failure, no data written
**Layer:** Gold notebook — Cell 8 MERGE operation
**Error code:** DELTA_MERGE_UNRESOLVED_EXPRESSION

## What broke
Gold notebook Cell 8 failed on MERGE with:

Cannot resolve transaction_amount in UPDATE clause
given columns source.transaction_id, source.txn_amount...

SQLSTATE: 42601

## Root cause
The fact_transactions Delta table was created on first run
with column name "transaction_amount".

On second run, Cell 6 was modified to alias the same
column as "txn_amount" instead.

Delta MERGE's whenMatchedUpdateAll() maps source to target
columns by exact name match. When source has "txn_amount"
but target expects "transaction_amount", the expression
cannot be resolved and the entire MERGE fails.

No data was written — Delta's ACID guarantee means the
table remained in its previous valid state.

## Why this matters in production
This error typically surfaces at 2am when a nightly
pipeline run fails after a developer renamed a column
without checking the existing target schema first.
The on-call engineer must:
1. Identify the mismatched column names
2. Decide: revert rename or evolve schema
3. Fix and re-run before business hours

## Fix Option A — Revert accidental rename
Correct fix when rename was a mistake.
Revert Cell 6 column alias back to original name:
  F.col("Amount").alias("transaction_amount")
Re-run MERGE — succeeds immediately.

## Fix Option B — Intentional schema evolution
Correct fix when rename is deliberate and intentional.
Step 1: ALTER the existing Delta table first:
  ALTER TABLE delta.`/path/fact_transactions/`
  RENAME COLUMN transaction_amount TO txn_amount
Step 2: Re-run MERGE — source and target now match.

## Fix applied
Option A — reverted column name to transaction_amount.
MERGE completed successfully after revert.

## Prevention
1. Never rename columns in transformation code without
   first checking the existing target Delta table schema:
   spark.read.format("delta").load(path).printSchema()

2. Add a schema validation step before every MERGE:
   compare source.columns with target.columns explicitly
   and raise a clear error if mismatch detected.

3. In production, schema changes must go through a
   migration script, not an ad-hoc code change.
   Treat Gold table schemas like database schemas —
   change them deliberately, never accidentally.

## Key learning
Delta Lake's ACID guarantee protected data integrity —
the existing table was untouched despite the failed MERGE.
This is one of Delta Lake's most important production
advantages over plain Parquet files.