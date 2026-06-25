"""
Gold layer transformation logic.

Builds a star schema from the Silver table:
- fact_transactions  : one row per transaction, all measures
- dim_date           : date dimension
- dim_amount_bucket  : amount category dimension
- dim_fraud_class    : fraud classification dimension

Star schema enables fast analytical queries and is the
standard pattern for data warehouse reporting layers.
"""

try:
    from pyspark.sql import DataFrame
    from pyspark.sql import functions as F
    from pyspark.sql.window import Window
    PYSPARK_AVAILABLE = True
except:
    PYSPARK_AVAILABLE = False


def build_fact_transactions(df) -> "DataFrame":
    """
    Builds the central fact table.
    One row per transaction with all measures and
    foreign keys linking to dimension tables.
    """
    if not PYSPARK_AVAILABLE:
        raise EnvironmentError("PySpark required")
    
    return df.select(
        # unique id column
        "transaction_id",

        # measures
        F.col("Amount").alias("transaction_amount"),
        F.col("Time").alias("transaction_time_seconds"),

        # foreign keys to dimensions
        F.col("full_date").alias("date_key"),
        F.col("amount_bucket").alias("amount_bucket_key"),
        F.col("Class").alias("fraud_class_key"),

        # fraud flag
        F.col("is_fraud"),

        # derived measures
        F.round(F.col("Amount"), 2).alias("amount_rounded"),
        F.when(
            F.col("Amount") > F.avg("Amount")
            .over(Window.partitionBy("amount_bucket")),
            True
            ).otherwise(False)
            .alias("is_above_bucket_average"),

        # Audit lineage
        F.col("_ingestion_timestamp"),
        F.col("_source_file"),
        F.col("_silver_processed_timestamp"),
        F.col("_silver_version"),

    )

def build_dim_date(spark, from_date, to_date) -> "DataFrame":
    """
    Builds date dimension from ingestion timestamps.
    Provides calendar attributes for time-based analysis.
    """
    if not PYSPARK_AVAILABLE:
        raise EnvironmentError("PySpark required")
    
    df_dates = spark.sql(f"""select explode(
        sequence(
        to_date({from_date}),
        to_date({to_date}),
        interval 1 day
        )
    ) as full_date
    """)
    
    return df_dates.select(
        F.col("full_date").alias("date_key"),
        F.col("full_date"),
        F.year(F.col("full_date")).alias("year"),
        F.month(F.col("full_date")).alias("month"),
        F.dayofmonth(F.col("full_date")).alias("day"),
        F.dayofweek(F.col("full_date")).alias("day_of_week"),
        F.quarter(F.col("full_date")).alias("quarter"),
        F.date_format(F.col("full_date"), "MMMM").alias("month_name"),
        F.date_format(F.col("full_date"), "EEEE").alias("day_name"),
        F.when(
            F.dayofweek(F.col("full_date")).isin([1, 7]), 
            True
            ).otherwise(False).alias("is_weekend"),
        F.when(
            F.month("full_date").isin([12, 1, 2]), "Winter"
        )
        .when(F.month("full_date").isin([3, 4, 5]), "Spring"
        )
        .when(F.month("full_date").isin([6, 7, 8]), "Summer"
        ).otherwise("Autumn")
        .alias("season")
    )

def build_dim_amount_bucket(df) -> "DataFrame":
    """
    Builds amount bucket dimension with business
    descriptions for each category.
    """
    if not PYSPARK_AVAILABLE:
        raise EnvironmentError("PySpark required")
    
    return df.select(
        F.col("amount_bucket").alias("amount_bucket_key"),
        F.col("amount_bucket").alias("bucket_name"),
        F.when(
            F.col("amount_bucket") == "micro",
            "Under $10 - typically small retail"
        )
        .when(
            F.col("amount_bucket") == "small",
            "$10-$99 — everyday purchases"
        )
        .when(
            F.col("amount_bucket") == "medium",
            "$100-$999 — significant purchases"
        )
        .when(
            F.col("amount_bucket") == "large",
            "$1000-$9999 — high value transactions"
        )
        .otherwise(
            "$10000+ — very high value, review required"
        )
        .alias("bucket_description"),

        F.when(
            F.col("amount_bucket") == "micro",      1)
            .when(F.col("amount_bucket") == "small",      2)
            .when(F.col("amount_bucket") == "medium",     3)
            .when(F.col("amount_bucket") == "large",      4)
            .otherwise(5).alias("bucket_sort_order")
    ).distinct()

def build_dim_fraud_class(spark) -> "DataFrame":
    """
        Builds fraud classification dimension.
    Static dimension — values defined by business rules.
    """
    if not PYSPARK_AVAILABLE:
        raise EnvironmentError("PySpark required")
    
    data = [
        (0, "Legitimate",  "Transaction verified as legitimate",
         "LOW",    "No action required"),
        (1, "Fraudulent",  "Transaction flagged as fraudulent",
         "CRITICAL", "Immediate review and block required")
        ]
    
    return spark.createDataFrame(
        data,
        ["fraud_class_key", "class_name", "class_description",
         "risk_level", "recommended_action"]
    )
    
def build_gold_summary(df) -> "DataFrame":
    """
    Builds a pre-aggregated summary table for dashboards.
    Answers the most common analytical questions directly.
    """
    if not PYSPARK_AVAILABLE:
        raise EnvironmentError("PySpark required")

    return df.groupBy(
        "full_date",
        "amount_bucket",
        "is_fraud"
    ).agg(
        F.count("transaction_id")
         .alias("transaction_count"),
        F.round(F.sum("Amount"), 2)
         .alias("total_amount"),
        F.round(F.avg("Amount"), 2)
         .alias("avg_amount"),
        F.round(F.max("Amount"), 2)
         .alias("max_amount"),
        F.round(F.min("Amount"), 2)
         .alias("min_amount"),
    ).orderBy("full_date", "amount_bucket")