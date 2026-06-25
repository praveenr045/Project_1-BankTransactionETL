# PM-007 — dim_date dimension contained only 1 row

**Date:** 2026-06
**Severity:** Medium — incorrect analytics, not pipeline failure
**Layer:** Gold notebook — build_dim_date()

## What broke
dim_date Delta table written with only 1 row despite
Silver table containing 284,807 transactions.

Expected: hundreds of rows covering a meaningful date range
Actual  : 1 row — only today's ingestion date

## Root cause
build_dim_date() was built by selecting distinct
_ingestion_date values from the Silver DataFrame:

  df.select("_ingestion_date").distinct()

Since all 284,807 records were ingested in a single
pipeline run today, every record had the same
_ingestion_date value. distinct() correctly collapsed
them to 1 unique date.

## Why this is wrong in production
A data-driven date dimension:
- Only contains dates where transactions actually occurred
- Has gaps on weekends, holidays, low-volume days
- Grows unpredictably based on ingestion schedule
- Breaks time-series queries that need continuous dates
- Causes dashboard charts to show gaps not zeros

## Fix
Replaced data-driven approach with pre-populated
calendar dimension covering 2024-01-01 to 2026-12-31:

Used spark.sql() with sequence() + explode() to generate
one row per calendar day in the range — 1,096 rows total.

Added additional attributes per date:
- season (Winter/Spring/Summer/Autumn)
- is_weekend (true/false)
- month_name, day_name (human readable)

## Result after fix
dim_date rows : 1,096
Coverage      : 2024-01-01 through 2026-12-31
Gaps          : None — every calendar day present

## Key learning
Date dimensions in a star schema must ALWAYS be
pre-populated for the full expected date range.
Never derive a date dimension from the data itself —
it creates implicit dependency on ingestion schedule.

Standard practice: generate date dimension once for
3-5 years, refresh annually by extending the range.