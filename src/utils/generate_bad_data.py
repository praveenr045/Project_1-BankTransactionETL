import pandas as pd
import numpy as np

df = pd.read_csv("data/raw/transactions_sample.csv")

bad_rows = []

# Defect 1 — NULL amounts (5 rows)
null_rows = df.sample(5).copy()
null_rows["Amount"] = np.nan
bad_rows.append(null_rows)

# Defect 2 — Negative amounts (3 rows)
neg_rows = df.sample(3).copy()
neg_rows["Amount"] = -50.00
bad_rows.append(neg_rows)

# Defect 3 — Duplicate rows (10 rows)
dup_rows = df.sample(10).copy()
bad_rows.append(dup_rows)

# Defect 4 — Outlier amounts (2 rows)
outlier_rows = df.sample(2).copy()
outlier_rows["Amount"] = 999999999.99
bad_rows.append(outlier_rows)

# Defect 5 — Future timestamps (2 rows)
future_rows = df.sample(2).copy()
future_rows["Time"] = 99999999999.0
bad_rows.append(future_rows)

# ── FIX: explicitly reset Time to valid small values
#    for clean rows so they don't trip the time threshold
good_rows = df.sample(50).copy()
good_rows["Time"] = np.random.uniform(0, 1000, size=len(good_rows))
good_rows["Amount"] = np.random.uniform(1, 500, size=len(good_rows))

corrupt_df = pd.concat(
    [good_rows] + bad_rows,
    ignore_index=True
)

corrupt_df = corrupt_df.sample(frac=1).reset_index(drop=True)

output_path = "data/bad_data/transactions_corrupt.csv"
corrupt_df.to_csv(output_path, index=False)

total   = len(corrupt_df)
defects = total - 50
print(f"Generated {total} rows — {defects} defective, 50 clean")
print(f"Saved to: {output_path}")