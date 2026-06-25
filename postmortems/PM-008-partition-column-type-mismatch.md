# PM-008 — Delta schema enforcement blocked type change on date_key

**Date:** 2026-06
**Severity:** High — pipeline failure (Delta caught it)
             Critical — silent corruption if Delta not used
**Layer:** Gold notebook — Cell 9 write dim_date

## What broke
Cell 9 failed when writing dim_date with date_key
cast from DateType to StringType:

DELTA_FAILED_TO_MERGE_FIELDS:
Failed to merge fields 'date_key' and 'date_key'.
DateType vs StringType schema conflict on overwrite.
SQLSTATE: 22005

## Root cause
dim_date was first written with date_key as DateType.
On second run, date_key was cast to StringType before
writing. Delta Lake detected the schema change and
refused to overwrite with a different type.

## Why Delta Lake's behaviour here is correct
If Delta allowed silent type changes:
- date_key StringType in dim_date
- date_key DateType in fact_transactions
- JOIN between fact and dim on date_key would require
  implicit casting on every query
- Partition pruning would fail silently on string keys
- Date range filters would stop working correctly
- Analytics queries would return wrong results or
  do full table scans instead of partition scans

Delta's schema enforcement prevented all of this by
refusing the write outright.

## What would have happened with plain Parquet
Plain Parquet has no schema enforcement on write.
The StringType version would have silently overwritten
the DateType version. Every downstream query joining
fact to dim_date would have required implicit casting.
Partition pruning would have silently stopped working.
Compute costs would increase, query times would grow.
No error would ever be thrown — pure silent corruption.

## Fix Option A — Remove accidental cast (applied)
Removed the erroneous .cast("string") from the
dim_date preparation step. Used original df_dim_date
with DateType preserved throughout.

## Fix Option B — Intentional schema evolution
If type change is genuinely required, use:
  .option("overwriteSchema", "true")
This is an explicit opt-in — use deliberately,
never as a workaround for an unexpected error.

## Key learning
Delta Lake's schema enforcement is not an obstacle —
it is a safety net. When Delta refuses a write due to
schema mismatch, the correct response is to investigate
why the schema changed, not to force overwriteSchema.

Always treat schema enforcement errors as signals that
something changed unexpectedly upstream. Investigate
before overriding.

## Prevention
Add a schema validation step before every Gold write:

  expected_types = {"date_key": "date", "year": "int"}
  actual_types   = dict(df.dtypes)
  for col, expected in expected_types.items():
      assert actual_types[col] == expected, \
          f"Schema mismatch: {col} is {actual_types[col]},
            expected {expected}"