import pandas as pd
import numpy as np

# ── Load and immediately fix column types ────────────────
df = pd.read_csv("data/raw/transactions_sample.csv")

# Force Class to nullable integer immediately after reading
# This prevents pandas from promoting it to float during operations
df["Class"] = df["Class"].astype("Int64")

print(f"Source rows: {len(df)}")
print(f"Class nulls in source: {df['Class'].isnull().sum()}")
print(f"Class unique values: {df['Class'].unique()}")

bad_rows = []

# Defect 1 — NULL amounts (5 rows)
null_rows = df.sample(5, random_state=1).copy()
null_rows["Amount"] = np.nan
bad_rows.append(null_rows)

# Defect 2 — Negative amounts (3 rows)
neg_rows = df.sample(3, random_state=2).copy()
neg_rows["Amount"] = -50.00
bad_rows.append(neg_rows)

# Defect 3 — Duplicate rows (10 rows)
dup_rows = df.sample(10, random_state=3).copy()
bad_rows.append(dup_rows)

# Defect 4 — Outlier amounts (2 rows)
outlier_rows = df.sample(2, random_state=4).copy()
outlier_rows["Amount"] = 999999999.99
bad_rows.append(outlier_rows)

# Defect 5 — Future timestamps (2 rows)
future_rows = df.sample(2, random_state=5).copy()
future_rows["Time"] = 99999999999.0
bad_rows.append(future_rows)

# ── Clean rows ───────────────────────────────────────────
good_rows = df.sample(50, random_state=6).copy()
good_rows["Time"]   = np.random.uniform(0, 1000, size=50)
good_rows["Amount"] = np.random.uniform(1, 500,  size=50)
# Class intentionally untouched

# ── Concatenate all rows ─────────────────────────────────
corrupt_df = pd.concat(
    [good_rows] + bad_rows,
    ignore_index=True
)

# ── Force Class back to Int64 after concat ───────────────
# Concat with rows containing NaN in other columns can
# silently promote Class from int to float, then to NaN
corrupt_df["Class"] = corrupt_df["Class"].astype("Int64")

# Shuffle
corrupt_df = corrupt_df.sample(frac=1, random_state=42).reset_index(drop=True)

# ── Final verification before saving ────────────────────
null_class   = corrupt_df["Class"].isnull().sum()
null_amount  = corrupt_df["Amount"].isnull().sum()
null_time    = corrupt_df["Time"].isnull().sum()
neg_amount   = (corrupt_df["Amount"] < 0).sum()
outlier_amt  = (corrupt_df["Amount"] > 1000000).sum()
future_time  = (corrupt_df["Time"] > 172800).sum()

print("\n=== Generated file verification ===")
print(f"Total rows       : {len(corrupt_df)}")
print(f"Clean rows       : 50")
print(f"Defect rows      : {len(corrupt_df) - 50}")
print(f"")
print(f"Null Amount      : {null_amount}   (expected ~5)")
print(f"Null Time        : {null_time}   (expected 0)")
print(f"Null Class       : {null_class}   ← must be 0")
print(f"Negative Amount  : {neg_amount}   (expected ~3)")
print(f"Outlier Amount   : {outlier_amt}   (expected ~2)")
print(f"Future Time      : {future_time}   (expected ~2)")
print(f"")
print(f"Class values     : {corrupt_df['Class'].unique()}")
print(f"Saved to         : data/bad_data/transactions_corrupt.csv")

if null_class > 0:
    print(f"\n❌ FAILED — Class column has {null_class} nulls. Do not upload.")
else:
    print(f"\n✅ PASSED — File is safe to upload to ADLS.")
    corrupt_df.to_csv("data/bad_data/transactions_corrupt.csv", index=False)