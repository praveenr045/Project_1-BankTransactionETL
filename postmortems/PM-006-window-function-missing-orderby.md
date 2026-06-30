# PM-006 — Window function row_number() missing ORDER BY

**Date:** 2026-06
**Severity:** High — pipeline failure (strict mode)
             Critical — silent data corruption (permissive mode)
**Layer:** Gold notebook — build_fact_transactions()

## What broke
Gold notebook Cell 6 failed with:

Window function row_number() requires window to be ordered,
please add ORDER BY clause.
For example SELECT row_number()(value_expr)
OVER (PARTITION BY window_partition ORDER BY window_ordering)

## Root cause
row_number() was used inside a Window.partitionBy() without
a corresponding .orderBy() clause:

  F.row_number().over(
      Window.partitionBy("amount_bucket")
      # No orderBy — non-deterministic
  )

row_number() assigns sequential integers to rows within
a partition. Without orderBy, Spark has no basis for
deciding which row gets number 1, 2, 3 etc.
The result is non-deterministic — different on every run.

## Why this is dangerous in production
On older Spark versions this executes without error but
produces different results on every run:
- Run 1: row 5432 gets rank 1 in "small" bucket
- Run 2: row 2891 gets rank 1 in "small" bucket
- Same data, same code, different output every time

Gold tables would be silently corrupted with each pipeline
run. Dashboards would show fluctuating numbers for no
apparent reason. Extremely hard to debug.

Newer Databricks runtimes (our version) made this strict —
throws an explicit error instead of silently corrupting.
This is the correct behaviour.

## Window functions that REQUIRE orderBy
- row_number()  → sequential integer per partition
- rank()        → same rank for ties, gaps after
- dense_rank()  → same rank for ties, no gaps
- lag()         → previous row value
- lead()        → next row value
- ntile()       → divide partition into N buckets

## Window functions that do NOT require orderBy
- avg()         → average over partition
- sum()         → sum over partition
- count()       → count over partition
- min()         → minimum over partition
- max()         → maximum over partition

## Fix
Replaced row_number() approach with avg() window function
which is deterministic and does not require orderBy:

  F.when(
      F.col("Amount") > F.avg("Amount").over(
          Window.partitionBy("amount_bucket")
      ),
      True
  ).otherwise(False)
  .alias("is_above_bucket_average")

## Prevention
Rule: before using any ranking window function, ask:
"What determines the order within each partition?"
If the answer is unclear, the window spec is incomplete.
Always add .orderBy() explicitly for ranking functions.