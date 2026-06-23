# PM-002 — PERMISSIVE vs FAILFAST mode in Bronze ingestion

**Date:** 2026-06-23
**Severity:** Low (learning exercise, not a production failure)
**Layer:** Bronze ingestion notebook

## Observation
Deliberately tested two Spark CSV read modes against
transactions_corrupt.csv to understand production behaviour.

## FAILFAST mode behaviour
Changed Cell 6 option from PERMISSIVE to FAILFAST and ran
against corrupt file.

Result: Job threw immediately on first malformed record:
SparkException: Malformed records detected in record parsing.
Stop early and throw an exception.

Cluster showed red error after 12 seconds — no records
written, no partial output.

## PERMISSIVE mode behaviour
Reverted to PERMISSIVE mode and ran same corrupt file.

Result: All 72 rows processed successfully.
12 rows flagged with _is_quarantined = True.
60 rows passed through cleanly.
No exceptions thrown — pipeline completed normally.

## When to use each mode

PERMISSIVE (our Bronze choice):
- Keeps all records including malformed ones
- Nullifies columns that cannot be parsed
- Lets us quarantine and investigate bad records
- Maintains complete audit trail — nothing is lost
- Correct choice for Bronze — ingest everything faithfully

FAILFAST:
- Throws exception on first bad record immediately
- Use when upstream system guarantees perfectly clean data
- Any corruption signals a serious upstream problem
- Correct choice when zero tolerance for bad data

DROPMALFORMED:
- Silently drops bad rows without any error or warning
- Extremely dangerous — you permanently lose records
- No audit trail, no investigation possible
- Never use in any production pipeline layer

## Decision
Bronze always uses PERMISSIVE + _is_quarantined flag pattern.
Bad records are never deleted — they are flagged and kept
for investigation and audit purposes.
Silver layer filters on _is_quarantined = False only,
ensuring only clean records flow downstream.

## Quarantine results on corrupt test file
Total rows      : 72
Quarantined     : 12
Clean passed    : 60
Quarantine rate : 16.67%

## Why 12 and not 22 (the number of injected defects)
The 10 duplicate rows (Defect 3) correctly passed Bronze.
Duplicates have valid column values — they are not bad
records by Bronze standards. Deduplication is Silver
layer responsibility using Delta Lake MERGE operation.