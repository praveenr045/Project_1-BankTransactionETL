# PM-003 — All 72 records quarantined on corrupt test file

**Date:** 2026-06
**Severity:** Medium (blocked DQ validation testing)
**Layer:** Bronze ingestion — DQ flagging cell

## What broke
Running notebook against transactions_corrupt.csv resulted
in all 72 rows being quarantined, including the 50
intended clean rows. Expected ~12 quarantined.

---

## Occurrence 1 — All rows failing future_time check

### Diagnostic output
Time column stats:
min_time : 9.99999999E10
max_time : 9.99999999E10
avg_time : 9.99999999E10

### Root cause
Defect 5 (future timestamp injection of 99999999999.0)
overwrote the Time column for ALL rows in the file during
pandas concat operation, not just the 2 intended rows.
The small file size meant the injected value dominated
the entire Time column distribution.

### Fix attempt 1
Explicitly reset Time and Amount to valid values for the
50 clean rows using np.random.uniform() before concat.
Result: Still 72 quarantined — new root cause discovered.

---

## Occurrence 2 — Class column null across all 72 rows

### Diagnostic output
Condition-by-condition breakdown:
03_null_class : 72   ← all 72 rows had null Class

### Root cause
generate_bad_data.py reset Time and Amount for clean rows
using np.random.uniform() which returns float64 values.
During pandas concat, mixing float columns (Amount, Time)
with rows containing NaN caused pandas to promote the
entire Class column from int64 to float64, then to NaN
for rows where it could not maintain integer representation.

### Fix attempt 2
Used pandas nullable integer type Int64 (capital I) for
Class column — applied twice, once after reading source
and once after concat to prevent float promotion.
Result: Still 72 quarantined — deeper root cause found.

---

## Occurrence 3 — Source sample file itself was corrupted

### Diagnostic output
Class values : [<NA>]   ← only NA, no 0 or 1
Null Time    : 20       ← should be 0
Null Amount  : 17       ← should be ~5

Source file verification showed:
transactions_sample.csv already had corrupted data before
any defect injection. The manually created sample file
had integrity issues in Class, Time, and Amount columns.

### Root cause
transactions_sample.csv was created manually by copying
rows from creditcard.csv in a text editor. This process
introduced data integrity issues — likely through
copy-paste errors or encoding problems.

### Final fix
Wrote generate_sample_data.py to programmatically
regenerate transactions_sample.csv directly from the
full creditcard.csv with assertions verifying all
columns are clean before saving:

assert sample["Class"].isnull().sum() == 0
assert sample["Time"].isnull().sum() == 0
assert sample["Amount"].isnull().sum() == 0
assert set(sample["Class"].unique()).issubset({0, 1})
assert sample["Time"].max() < 172800

Used df.head(1000) to take first 1000 rows which have
smallest Time values — safely within 172800 threshold.

After regenerating sample, bad data generator ran
successfully and produced verified output:
✅ PASSED — File is safe to upload to ADLS.

---

## Final results — correct quarantine behaviour

Results on transactions_corrupt.csv (72 rows total):

| Defect type        | Injected | Quarantined | Correct |
|--------------------|----------|-------------|---------|
| Null amounts       | 5        | 5           | ✅      |
| Negative amounts   | 3        | 3           | ✅      |
| Outlier amounts    | 2        | 2           | ✅      |
| Future timestamps  | 2        | 2           | ✅      |
| Duplicates         | 10       | 0           | ✅      |
| Clean rows         | 50       | 0           | ✅      |
| **Total**          | **72**   | **12**      | ✅      |

Duplicates correctly pass Bronze — deduplication is
Silver layer responsibility using Delta Lake MERGE.

## Key learnings

1. Always generate test data programmatically, never
   manually. Manual CSV creation introduces silent
   integrity issues that are hard to trace.

2. Always add assertions to data generation scripts
   before saving output — catch problems at source,
   not downstream in Databricks.

3. When debugging unexpected quarantine counts, always
   run condition-by-condition diagnostic breakdown
   rather than guessing. Each condition independently
   counted reveals the exact failure point immediately.

4. pandas int → float promotion during concat is a
   known gotcha. Always verify dtypes after concat
   operations, especially when mixing NaN-containing
   rows with integer columns.