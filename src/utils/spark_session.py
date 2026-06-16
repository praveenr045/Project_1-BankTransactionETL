"""
Reusable Spark session factory.
In Databricks, the session already exists — this returns it directly.
Locally (CI, tests), this would need a local Spark setup, which we
deliberately avoid relying on for unit tests.
"""

from pyspark.sql import SparkSession


def get_spark_session(app_name: str = "BankETL") -> SparkSession:
    """
    Returns the active SparkSession.
    In Databricks notebooks, a SparkSession is always already running —
    this function simply fetches it rather than creating a new one.
    """
    spark = SparkSession.getActiveSession()

    if spark is None:
        raise EnvironmentError(
            "No active SparkSession found. "
            "This function is intended to run inside Databricks, "
            "where a SparkSession is always pre-initialized."
        )

    print(f"Using active SparkSession: {app_name}")
    return spark