"""
Data quality logic for the Bronze ingestion layer.

This module is split into two layers deliberately:

1. is_quarantined()         -> pure Python, no Spark dependency.
                                Testable instantly in CI with pytest,
                                no Java or Spark cluster needed.

2. flag_quarantined_records() -> PySpark wrapper, used inside Databricks
                                notebooks to apply the same logic across
                                an entire DataFrame at scale.

Both functions enforce the exact same business rules — kept in sync
by always updating both together.
"""

try:
    from pyspark.sql import functions as F
    PYSPARK_AVAILABLE = True
except ImportError:
    PYSPARK_AVAILABLE = False


def is_quarantined(amount, time, class_label,
                    min_amount: float = 0.0,
                    max_amount: float = 1_000_000.0,
                    max_time: float = 172_800.0) -> bool:
    """
    Pure Python quality check for a single record.
    Returns True if the record should be quarantined.

    Rules:
    - amount, time, or class_label is missing
    - amount is negative or above max_amount
    - time is beyond max_time (48 hours in seconds, dataset-specific)
    """
    if amount is None or time is None or class_label is None:
        return True
    if amount < min_amount or amount > max_amount:
        return True
    if time > max_time:
        return True
    return False


def flag_quarantined_records(df,
                              min_amount: float = 0.0,
                              max_amount: float = 1_000_000.0,
                              max_time: float = 172_800.0):
    """
    PySpark wrapper — applies the same quality rules as is_quarantined()
    across an entire DataFrame, adding a new "_is_quarantined" column.

    Runs only in Databricks (or any environment with PySpark installed).
    """
    if not PYSPARK_AVAILABLE:
        raise EnvironmentError(
            "PySpark not available. "
            "flag_quarantined_records() must run in Databricks."
        )

    return df.withColumn(
        "_is_quarantined",
        (
            F.col("Amount").isNull() |
            F.col("Time").isNull() |
            F.col("Class").isNull() |
            (F.col("Amount") < min_amount) |
            (F.col("Amount") > max_amount) |
            (F.col("Time") > max_time)
        )
    )