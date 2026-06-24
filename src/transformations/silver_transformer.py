"""
Silver layer transformation logic.

Responsibilities:
1. Filter out quarantined records from Bronze
2. Deduplicate using a unique row key
3. Enrich columns — derive meaningful fields from raw ones
4. Cast columns to correct types
5. Add silver-layer audit metadata

This module contains pure PySpark logic.
All functions accept and return DataFrames — no I/O here.
I/O (reading/writing Delta tables) happens in the notebook.
"""

try:
    from pyspark.sql import DataFrame
    from pyspark.sql import functions as F
    from pyspark.sql.types import TimestampType
    PYSPARK_AVAILABLE = True
except ImportError:
    PYSPARK_AVAILABLE = False

def filter_quarantined(df) -> "DataFrame":
    """
    Removes records flagged as quarantined in Bronze.
    Only clean records flow into Silver.
    """
    if not PYSPARK_AVAILABLE:
        raise EnvironmentError("PySpark required")

    before = df.count()
    df_clean = df.filter(F.col("_is_quarantined") == False)
    after = df_clean.count()

    print(f"Quarantine filter: {before:,} → {after:,} rows")
    print(f"Removed          : {before - after:,} quarantined records")

    return df_clean

def deduplicate(df, 
                partition_cols: list,
                order_col: str) -> "DataFrame":
    """
    Removes duplicate records using window function.
    Keeps the most recent record per partition.

    Args:
        partition_cols : columns that define a unique record
                         e.g. ["Time", "Amount", "Class"]
        order_col      : column to order by when picking
                         which duplicate to keep
                         e.g. "_ingestion_timestamp"
    """
    if not PYSPARK_AVAILABLE:
        raise EnvironmentError("PySpark required")

    from pyspark.sql.window import Window

    before = df.count()

    window = Window \
        .partitionBy(*partition_cols) \
        .orderBy(F.col(order_col).desc())

    df_deduped = df \
        .withColumn("_row_num", F.row_number().over(window)) \
        .filter(F.col("_row_num") == 1) \
        .drop("_row_num")

    after = df_deduped.count()

    print(f"Deduplication: {before:,} → {after:,} rows")
    print(f"Duplicates removed: {before - after:,}")

    return df_deduped

def enrich_columns(df) -> "DataFrame":
    """
    Derives meaningful columns from raw Bronze fields.

    New columns added:
    - transaction_id : unique ID per record
    - amount_bucket  : categorises transaction by size
    - is_fraud       : boolean version of Class column
    - ingest_hour    : hour of ingestion for time analysis
    """
 
    if not PYSPARK_AVAILABLE:
        raise EnvironmentError("PySpark required")
    
    df_enriched = (
         df
        # Unique transaction ID — hash of key fields
        .withColumn(
            "transaction_id",
            F.sha2(
                F.concat_ws("|",
                    F.col("Time").cast("string"),
                    F.col("Amount").cast("string"),
                    F.col("V1").cast("string"),
                    F.col("_source_file")
                ), 256
            )
        )
        # Human-readable fraud flag
        .withColumn(
            "is_fraud",
            F.when(F.col("Class") == 1, True).otherwise(False)
        )
        # Amount bucket for analytics
        .withColumn(
            "amount_bucket",
            F.when(F.col("Amount") < 10,    "micro")
             .when(F.col("Amount") < 100,   "small")
             .when(F.col("Amount") < 1000,  "medium")
             .when(F.col("Amount") < 10000, "large")
             .otherwise("very_large")
        )
        # Hour of ingestion for time-based analysis
        .withColumn(
            "ingest_hour",
            F.hour(F.col("_ingestion_timestamp"))
        )
    )

    return df_enriched

def silver_metadata_columns(df, pipeline_run_id: str):

    """
    Adds Silver-specific audit columns.
    These are separate from Bronze audit columns.
    """
    
    if not PYSPARK_AVAILABLE:
        raise EnvironmentError("PySpark required")

    return(
        df.withColumn(
            "_silver_processed_timestamp", F.current_timestamp()
        )
        .withColumn(
            "_silver_pipeline_run_id", pipeline_run_id
        )
        .withColumn(
            "_silver_version", F.lit("1.0")
        )
    )

def select_silver_columns(df):

    """
    Selects and orders final Silver columns.
    Drops Bronze-specific internal columns that
    Silver consumers don't need.
    Keeps all audit columns for lineage.
    """
      
    if not PYSPARK_AVAILABLE:
        raise EnvironmentError("PySpark required")
    
    #Business columns
    df_selected = df.select(
        "transaction_id",
        "Time",
        "Amount",
        "Class",
        "is_fraud",
        "amount_bucket",

        #Columns V1...V28
        *[f"V{i}" for i in range(1,29)],

        #Bronze audit columns for lineage
        "_ingestion_timestamp",
        "_ingestion_date",
        "_pipeline_run_id",
        "_source_file",
        "_is_quarantined",

        # Silver audit columns
        "_silver_processed_timestamp",
        "_silver_pipeline_run_id",
        "_silver_version",
        "ingest_hour"
    )
    return df_selected