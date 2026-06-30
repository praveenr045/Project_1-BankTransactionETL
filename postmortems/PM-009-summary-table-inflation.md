# PM-009 — Gold summary table inflated by append mode

**Date:** 2026-06
**Severity:** Critical — wrong numbers silently shown on dashboards
**Layer:** Gold notebook — Cell 10 summary table write
**Detection:** Manual diagnostic check — no automatic error thrown

## What broke
Gold summary table showed 559,900 total transactions after
2 pipeline runs. Silver source contains 279,950 transactions.
Inflation: 279,950 (exactly 100% — doubled on every run).

Dashboard KPIs showing double the real transaction volume.
No error was thrown at any point — pure silent corruption.

## Root cause
Summary table was written with mode("append") instead of
mode("overwrite").

append mode on an aggregation table:
- Run 1: writes 9 summary rows (279,950 transactions)
- Run 2: appends 9 more rows (279,950 again)
- Run 3: appends 9 more rows (279,950 again)
- Total after 3 runs: 27 rows, 839,850 "transactions"

Every re-run multiplies the reported numbers.
Analysts and business users see wrong KPIs with no warning.

## Why this is dangerous in banking/finance
Financial reporting with inflated transaction counts:
- Regulatory reports show incorrect volumes
- Fraud rate calculations become wrong
- Risk exposure appears larger than reality
- Could trigger false regulatory alerts
- In extreme cases, could lead to incorrect capital
  reserve calculations

## Detection
Only detected because we manually compared:
  Gold summary total vs Silver source total
  559,900 ≠ 279,950 → 100% inflation confirmed

In production without reconciliation checks this could
go undetected for days or weeks until an analyst
noticed unexpectedly high transaction volumes.

## Fix
Three-part fix applied:

Part 1 — Cleared inflated data:
  DELETE FROM delta.`/gold/gold_summary/` WHERE 1=1
  Rewrote with mode("overwrite") — 9 rows, correct totals.

Part 2 — Added validate_summary_totals() function:
  src/transformations/gold_transformer.py
  Compares Gold summary total to Silver source after
  every write. Raises ValueError if they diverge.
  Tolerance = 0.0 for financial data (exact match required).

Part 3 — Reconciliation runs automatically after every write:
  Cell 10 calls validate_summary_totals() immediately
  after writing. Pipeline fails loudly if mismatch detected.
  Silent corruption is now impossible.

## Rule for aggregation tables
Summary and aggregation tables must ALWAYS use:
  mode("overwrite") — replaces entire table each run

Never use:
  mode("append") — only correct for raw ingestion (Bronze)

Memory aid:
  Bronze  → append  (keep all raw records forever)
  Silver  → merge   (upsert — update or insert)
  Gold    → overwrite for summaries, merge for fact tables

## Prevention
Added reconciliation check as mandatory final step in
every Gold notebook. Any divergence between Gold totals
and Silver source raises an immediate exception — the
pipeline fails loudly rather than writing wrong data.

"Fail loudly or succeed correctly — never silently corrupt"