"""
Generates a clean 1000-row sample from the full creditcard.csv
Verifies data integrity before saving.
Run once: python src/utils/generate_sample_data.py
"""
import pandas as pd

# Read full dataset
print("Reading full dataset...")
df = pd.read_csv("data/raw/creditcard.csv")
print(f"Full dataset: {len(df):,} rows")

# Verify source is clean
print("\n=== Source data verification ===")
print(f"Null Amount : {df['Amount'].isnull().sum()}")
print(f"Null Time   : {df['Time'].isnull().sum()}")
print(f"Null Class  : {df['Class'].isnull().sum()}")
print(f"Class values: {sorted(df['Class'].unique())}")

# Take first 1000 rows — these have smallest Time values
# which safely fall under our 172800 threshold
sample = df.head(1000).copy()

# Final check
assert sample["Class"].isnull().sum() == 0, "Class has nulls!"
assert sample["Time"].isnull().sum() == 0, "Time has nulls!"
assert sample["Amount"].isnull().sum() == 0, "Amount has nulls!"
assert set(sample["Class"].unique()).issubset({0, 1}), "Unexpected Class values!"
assert sample["Time"].max() < 172800, f"Time too large: {sample['Time'].max()}"

sample.to_csv("data/raw/transactions_sample.csv", index=False)
print(f"\n✅ Clean sample saved: {len(sample)} rows")
print(f"Time range  : {sample['Time'].min():.1f} → {sample['Time'].max():.1f}")
print(f"Amount range: {sample['Amount'].min():.2f} → {sample['Amount'].max():.2f}")
print(f"Class values: {sorted(sample['Class'].unique())}")