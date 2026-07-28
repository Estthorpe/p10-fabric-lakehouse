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
from functools import reduce

class ContractViolation(Exception):
    """Raised when the aggregate data quality gate is breached."""

RESULTS, QUARANTINE = [], []

def _log(rule_id, description, action, n):
    status = "PASS" if n == 0 else action
    RESULTS.append({"rule": rule_id, "description": description,
                    "action": action, "violations": int(n), "status": status})
    print(f"[{status:<4}] {rule_id:<5} {description:<52} {n:>7,}")

def contract(df, bad, rule_id, description, action="FAIL"):
    """bad = condition selecting the WRONG rows. Zero rows = pass."""
    n = df.filter(bad).count()
    _log(rule_id, description, action, n)
    if n == 0:
        return df
    if action == "WARN":
        return df.withColumn(f"_dq_{rule_id.lower()}", bad)
    QUARANTINE.append(df.filter(bad)
                        .withColumn("_dq_rule", F.lit(rule_id))
                        .withColumn("_dq_reason", F.lit(description)))
    return df.filter(~F.coalesce(bad, F.lit(False)))

def contract_fk(child, child_col, parent, parent_col, rule_id, description):
    pk = parent.select(F.col(parent_col).alias("_pk")).distinct()
    cond = child[child_col] == F.col("_pk")
    n = child.join(pk, cond, "left_anti").count()
    _log(rule_id, description, "FAIL", n)
    if n == 0:
        return child
    QUARANTINE.append(child.join(pk, cond, "left_anti")
                           .withColumn("_dq_rule", F.lit(rule_id))
                           .withColumn("_dq_reason", F.lit(description)))
    return child.join(pk, cond, "left_semi")

def contract_unique(df, key_col, rule_id, description):
    dup_keys = df.groupBy(key_col).count().filter(F.col("count") > 1).select(key_col)
    n = dup_keys.count()
    _log(rule_id, description, "FAIL", n)
    if n == 0:
        return df
    QUARANTINE.append(df.join(dup_keys, key_col, "left_semi")
                        .withColumn("_dq_rule", F.lit(rule_id))
                        .withColumn("_dq_reason", F.lit(description)))
    return df.join(dup_keys, key_col, "left_anti")

def enforce(total_rows, max_quarantine_pct=5.0):
    spark.createDataFrame(RESULTS).show(30, truncate=False)
    q = sum(r["violations"] for r in RESULTS if r["action"] == "FAIL")
    pct = q / total_rows * 100
    print(f"\nquarantined {q:,} of {total_rows:,} ({pct:.2f}%) | threshold {max_quarantine_pct}%")
    if pct > max_quarantine_pct:
        raise ContractViolation(f"quarantine rate {pct:.2f}% exceeds {max_quarantine_pct}%")
    print("GATE PASSED")

print("harness ready")

# %% microsoft={"language": "python", "language_group": "synapse_pyspark"}
RESULTS.clear(); QUARANTINE.clear()

# ── typing + cleansing (register R3, R11, R16) ──────────────────────
s_products = (spark.table("bronze_products")
    .withColumn("unit_cost",       F.col("unit_cost").cast("double"))
    .withColumn("unit_price",      F.col("unit_price").cast("double"))
    .withColumn("shelf_life_days", F.col("shelf_life_days").cast("int")))

s_depots = (spark.table("bronze_depots")
    .withColumn("city",             F.initcap(F.trim(F.col("city"))))
    .withColumn("capacity_pallets", F.col("capacity_pallets").cast("int"))
    .withColumn("opened_date",      F.to_date("opened_date")))

s_orders = (spark.table("bronze_orders")
    .withColumn("order_datetime",          F.to_timestamp("order_datetime"))
    .withColumn("requested_delivery_date", F.to_date("requested_delivery_date"))
    .withColumn("quantity",                F.col("quantity").cast("int"))
    .withColumn("unit_price",              F.col("unit_price").cast("double")))

s_deliveries = (spark.table("bronze_deliveries")
    .withColumn("status",        F.upper(F.trim(F.col("status"))))
    .withColumn("dispatched_at", F.to_timestamp("dispatched_at"))
    .withColumn("delivered_at",  F.to_timestamp("delivered_at"))
    .withColumn("distance_km",   F.col("distance_km").cast("double"))
    .withColumn("temperature_breach_flag",
                F.col("temperature_breach_flag").cast("boolean")))

TOTAL = (s_products.count() + s_depots.count()
         + s_orders.count() + s_deliveries.count())
print(f"typed and cleansed — {TOTAL:,} rows in\n")

# ── remove byte-identical duplicates before gating on real conflicts ─
s_products = s_products.dropDuplicates()
s_orders   = s_orders.dropDuplicates()

# ── contracts ───────────────────────────────────────────────────────
s_products   = contract_unique(s_products, "product_id",
                  "R1", "products.product_id must be unique")

s_products   = contract(s_products, F.col("unit_cost") > F.col("unit_price"),
                  "R2", "products.unit_price must exceed unit_cost")

s_orders     = contract_unique(s_orders, "order_line_id",
                  "R4", "orders.order_line_id must be unique")

s_orders     = contract(s_orders, F.col("requested_delivery_date").isNull(),
                  "R5", "orders.requested_delivery_date is null", action="WARN")

s_orders     = contract(s_orders, F.col("quantity") <= 0,
                  "R6", "orders.quantity must be positive")

s_orders     = contract_fk(s_orders, "depot_id", s_depots, "depot_id",
                  "R7", "orders.depot_id -> depots")
# R8 — order line price must agree with the product master
#      R2 has already removed the 3 negative-margin products, so this now
#      measures genuine drift rather than the cascade from those rows
price_master = s_products.select("product_id",
                                 F.col("unit_price").alias("_master_price"))
s_orders = s_orders.join(price_master, "product_id", "left")

s_orders = contract(
    s_orders,
    F.col("_master_price").isNotNull() &
    (F.round(F.col("unit_price"), 2) != F.round(F.col("_master_price"), 2)),
    "R8", "orders.unit_price disagrees with product master")

# R17 — order lines whose product was withdrawn by R2
#      WARN not FAIL: a withdrawn dimension row must not delete valid facts
s_orders = contract(
    s_orders,
    F.col("_master_price").isNull(),
    "R17", "orders.product_id not present in silver_products", action="WARN")

s_orders = s_orders.drop("_master_price")

s_deliveries = contract_fk(s_deliveries, "order_id", s_orders, "order_id",
                  "R10", "deliveries.order_id -> orders")

s_deliveries = contract(s_deliveries, F.col("temperature_breach_flag").isNull(),
                  "R12", "deliveries.temperature_breach_flag is null")

s_deliveries = contract(s_deliveries, F.col("delivered_at") < F.col("dispatched_at"),
                  "R13", "deliveries.delivered_at before dispatched_at")

s_deliveries = contract(s_deliveries, F.col("distance_km") < 0,
                  "R14", "deliveries.distance_km must not be negative")

# ── write ───────────────────────────────────────────────────────────
if QUARANTINE:
    q = reduce(lambda a, b: a.unionByName(b, allowMissingColumns=True), QUARANTINE)
    q.write.mode("overwrite").option("mergeSchema", "true") \
     .format("delta").saveAsTable("quarantine_silver")
    print(f"\nquarantine_silver {q.count():>7,} rows")

for name, df in [("products", s_products), ("depots", s_depots),
                 ("orders", s_orders), ("deliveries", s_deliveries)]:
    df.write.mode("overwrite").option("mergeSchema", "true") \
      .format("delta").saveAsTable(f"silver_{name}")
    print(f"silver_{name:<12} {df.count():>7,} rows")

# %% microsoft={"language": "python", "language_group": "synapse_pyspark"}
enforce(TOTAL)
