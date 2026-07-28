# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.5
#   kernel_info:
#     name: synapse_pyspark
#   kernelspec:
#     display_name: synapse_pyspark
#     name: synapse_pyspark
# ---

# %% microsoft={"language": "python", "language_group": "synapse_pyspark"}
from pyspark.sql import functions as F
from datetime import datetime

BATCH_ID = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
RAW = "Files/raw"
TABLES = ["products", "depots", "orders", "deliveries"]

for name in TABLES:
    df = (spark.read
          .option("header", "true")
          .option("inferSchema", "false")   # bronze preserves the source verbatim
          .csv(f"{RAW}/{name}.csv"))

    df = (df
          .withColumn("_ingested_at", F.current_timestamp())
          .withColumn("_source_file", F.lit(f"{name}.csv"))
          .withColumn("_ingest_batch", F.lit(BATCH_ID)))

    (df.write
       .mode("overwrite")
       .format("delta")
       .saveAsTable(f"bronze_{name}"))

    print(f"bronze_{name:<12} {df.count():>7,} rows")

# %% microsoft={"language": "python", "language_group": "synapse_pyspark"}
for name in TABLES:
    n = spark.sql(f"SELECT COUNT(*) AS n FROM bronze_{name}").collect()[0]["n"]
    print(f"bronze_{name:<12} {n:>7,}")
