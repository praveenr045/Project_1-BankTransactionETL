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

def configure_adls_oauth(spark, storage_account: str, 
                          client_id: str,
                          client_secret: str, 
                          tenant_id: str) -> None:
    """
    Configures Spark session to authenticate against
    ADLS Gen2 using OAuth Service Principal credentials.

    Must be called in every notebook before any ADLS
    read or write operation. Spark config does not
    persist between notebook sessions.
    """
    base = f"{storage_account}.dfs.core.windows.net"

    spark.conf.set(f"fs.azure.account.auth.type.{base}", "OAuth")
    spark.conf.set(
        f"fs.azure.account.oauth.provider.type.{base}",
        "org.apache.hadoop.fs.azurebfs.oauth2.ClientCredsTokenProvider"
    )
    spark.conf.set(f"fs.azure.account.oauth2.client.id.{base}", client_id)
    spark.conf.set(f"fs.azure.account.oauth2.client.secret.{base}", client_secret)
    spark.conf.set(
        f"fs.azure.account.oauth2.client.endpoint.{base}",
        f"https://login.microsoftonline.com/{tenant_id}/oauth2/token"
    )

    print(f"ADLS OAuth configured for: {storage_account}")