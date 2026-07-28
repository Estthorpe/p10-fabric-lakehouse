"""
Ingrifoods scenario data generator - P10 Fabric Lakehouse
Clarivance Analytics Group

Deterministic synthetic data for a UK food distribution business.
Seeded with realistic source-system data quality defects.

Run:  python generate_ingrifoods_data.py
Out:  data/raw/{products,depots,orders,deliveries}.csv
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

SEED = 20260728
rng = np.random.default_rng(SEED)

OUT = Path("data/raw")
OUT.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------- products

CATALOGUE = {
    "Ambient": [
        "Basmati Rice 5kg",
        "Penne Pasta 500g",
        "Chopped Tomatoes 400g",
        "Olive Oil 1L",
        "Baked Beans 415g",
        "Sunflower Oil 2L",
        "Caster Sugar 1kg",
        "Plain Flour 1.5kg",
        "Instant Coffee 200g",
        "Long Life Milk 1L",
    ],
    "Chilled": [
        "Cheddar Block 2kg",
        "Greek Yoghurt 500g",
        "Salted Butter 250g",
        "Free Range Eggs 12",
        "Double Cream 300ml",
        "Cheddar Slices 400g",
        "Chicken Breast 1kg",
        "Pork Sausages 400g",
        "Smoked Bacon 300g",
        "Fresh Orange Juice 1L",
    ],
    "Frozen": [
        "Garden Peas 1kg",
        "Frozen Chips 2kg",
        "Chicken Goujons 1kg",
        "Vanilla Ice Cream 2L",
        "Cod Fillets 800g",
        "Mixed Berries 500g",
        "Frozen Pizza 12in",
        "Yorkshire Puddings 24",
        "Prawns 400g",
        "Frozen Sweetcorn 1kg",
    ],
    "Produce": [
        "Maris Piper Potatoes 10kg",
        "Carrots 5kg",
        "Iceberg Lettuce x12",
        "Vine Tomatoes 2kg",
        "Braeburn Apples 5kg",
        "Bananas 6kg",
        "Red Onions 5kg",
        "Broccoli 3kg",
        "Cucumbers x12",
        "Bell Peppers 3kg",
    ],
    "Bakery": [
        "White Bloomer 800g",
        "Wholemeal Loaf 800g",
        "Bagels x6",
        "Croissants x8",
        "Baguette 250g",
        "Seeded Rolls x12",
        "Crumpets x12",
        "Pain au Chocolat x6",
        "Tortilla Wraps x8",
        "Sourdough 500g",
    ],
}

ZONE = {
    "Ambient": "AMBIENT",
    "Bakery": "AMBIENT",
    "Chilled": "CHILLED",
    "Produce": "CHILLED",
    "Frozen": "FROZEN",
}
SHELF = {
    "Ambient": (180, 540),
    "Bakery": (2, 7),
    "Chilled": (7, 28),
    "Produce": (3, 14),
    "Frozen": (180, 365),
}

rows = []
pid = 1
for category, items in CATALOGUE.items():
    lo, hi = SHELF[category]
    for name in items:
        cost = round(float(rng.uniform(0.80, 14.50)), 2)
        rows.append(
            {
                "product_id": f"P{pid:04d}",
                "product_name": name,
                "category": category,
                "temperature_zone": ZONE[category],
                "unit_cost": cost,
                "unit_price": round(cost * float(rng.uniform(1.18, 1.62)), 2),
                "shelf_life_days": int(rng.integers(lo, hi + 1)),
            }
        )
        pid += 1
products = pd.DataFrame(rows)

# ------------------------------------------------------------------ depots

DEPOTS = [
    ("Manchester", "North West"),
    ("Birmingham", "West Midlands"),
    ("Leeds", "Yorkshire"),
    ("Bristol", "South West"),
    ("Glasgow", "Scotland"),
    ("Newcastle", "North East"),
    ("Nottingham", "East Midlands"),
    ("Southampton", "South East"),
    ("Cardiff", "Wales"),
    ("Sheffield", "Yorkshire"),
    ("Liverpool", "North West"),
    ("Norwich", "East of England"),
]
depots = pd.DataFrame(
    [
        {
            "depot_id": f"D{i:03d}",
            "depot_name": f"Ingrifoods {city}",
            "city": city,
            "region": region,
            "capacity_pallets": int(rng.integers(400, 2200)),
            "opened_date": (
                pd.Timestamp("2009-01-01")
                + pd.Timedelta(days=int(rng.integers(0, 5200)))
            ).date(),
        }
        for i, (city, region) in enumerate(DEPOTS, start=1)
    ]
)

# ------------------------------------------------------------------ orders

N_ORDERS = 6000
START = pd.Timestamp("2025-07-01")
END = pd.Timestamp("2026-06-30")
span_days = (END - START).days

order_ids = [f"ORD{i:06d}" for i in range(1, N_ORDERS + 1)]
customers = [f"CUST{i:04d}" for i in range(1, 481)]

# seasonality: heavier volume Nov/Dec, lighter Jan/Feb
day_offsets = rng.integers(0, span_days + 1, size=N_ORDERS)
order_dt = [
    START
    + pd.Timedelta(
        days=int(d), hours=int(rng.integers(6, 20)), minutes=int(rng.integers(0, 60))
    )
    for d in day_offsets
]

lines_per_order = rng.integers(1, 6, size=N_ORDERS)
price_lookup = dict(zip(products["product_id"], products["unit_price"]))

order_rows = []
for oid, odt, n_lines in zip(order_ids, order_dt, lines_per_order):
    depot = f"D{int(rng.integers(1, 13)):03d}"
    cust = customers[int(rng.integers(0, len(customers)))]
    lead = int(rng.integers(1, 8))
    chosen = rng.choice(products["product_id"].values, size=int(n_lines), replace=False)
    for ln, prod in enumerate(chosen, start=1):
        order_rows.append(
            {
                "order_id": oid,
                "order_line_id": f"{oid}-{ln:02d}",
                "customer_id": cust,
                "depot_id": depot,
                "product_id": prod,
                "order_datetime": odt,
                "requested_delivery_date": (odt + pd.Timedelta(days=lead)).date(),
                "quantity": int(rng.integers(1, 61)),
                "unit_price": price_lookup[prod],
            }
        )
orders = pd.DataFrame(order_rows)

# -------------------------------------------------------------- deliveries

order_header = (
    orders.groupby("order_id")
    .agg(
        depot_id=("depot_id", "first"),
        order_datetime=("order_datetime", "first"),
        requested=("requested_delivery_date", "first"),
    )
    .reset_index()
)

delivered_mask = rng.random(len(order_header)) < 0.92
delivered = order_header[delivered_mask].reset_index(drop=True)

STATUSES = np.array(
    ["DELIVERED"] * 88 + ["FAILED"] * 5 + ["RETURNED"] * 4 + ["PARTIAL"] * 3
)

del_rows = []
for i, r in delivered.iterrows():
    dispatched = pd.Timestamp(r["requested"]) + pd.Timedelta(
        hours=int(rng.integers(4, 11)), minutes=int(rng.integers(0, 60))
    )
    transit = pd.Timedelta(minutes=int(rng.integers(35, 400)))
    del_rows.append(
        {
            "delivery_id": f"DEL{i + 1:06d}",
            "order_id": r["order_id"],
            "depot_id": r["depot_id"],
            "vehicle_id": f"VH{int(rng.integers(1, 141)):03d}",
            "dispatched_at": dispatched,
            "delivered_at": dispatched + transit,
            "status": str(rng.choice(STATUSES)),
            "temperature_breach_flag": bool(rng.random() < 0.037),
            "distance_km": round(float(rng.uniform(3.5, 210.0)), 1),
        }
    )
deliveries = pd.DataFrame(del_rows)

# ============================================================ DEFECT SEEDING
# Realistic source-system defects. Not documented in the repo by design -
# these are to be discovered through EDA, not read from a comment.

# 1 - orphan depot references in orders
idx = rng.choice(orders.index, size=124, replace=False)
orders.loc[idx, "depot_id"] = rng.choice(["D014", "D017", "D099"], size=124)

# 2 - duplicated order lines
dupes = orders.loc[rng.choice(orders.index, size=83, replace=False)].copy()
orders = pd.concat([orders, dupes], ignore_index=True)

# 3 - non-positive quantities
idx = rng.choice(orders.index, size=64, replace=False)
orders.loc[idx, "quantity"] = rng.choice([0, -1, -5, -12], size=64)

# 4 - missing requested delivery dates
idx = rng.choice(orders.index, size=211, replace=False)
orders.loc[idx, "requested_delivery_date"] = np.nan

# 5 - price drift away from the product master
idx = rng.choice(orders.index, size=307, replace=False)
orders.loc[idx, "unit_price"] = (
    orders.loc[idx, "unit_price"] * rng.uniform(0.55, 1.75, size=307)
).round(2)

# 6 - deliveries that predate their own dispatch
idx = rng.choice(deliveries.index, size=47, replace=False)
deliveries.loc[idx, "delivered_at"] = deliveries.loc[
    idx, "dispatched_at"
] - pd.Timedelta(hours=3)

# 7 - deliveries against orders that do not exist
ghosts = deliveries.loc[rng.choice(deliveries.index, size=33, replace=False)].copy()
ghosts["delivery_id"] = [f"DEL9{i:05d}" for i in range(1, 34)]
ghosts["order_id"] = [f"ORD99{i:04d}" for i in range(1, 34)]
deliveries = pd.concat([deliveries, ghosts], ignore_index=True)

# 8 - status conformance drift
idx = rng.choice(deliveries.index, size=290, replace=False)
deliveries.loc[idx, "status"] = rng.choice(
    ["delivered", "Delivered", " DELIVERED", "DELIVERED ", "failed"], size=290
)

# 9 - breach flag missing on frozen-capable runs
idx = rng.choice(deliveries.index, size=96, replace=False)
deliveries["temperature_breach_flag"] = deliveries["temperature_breach_flag"].astype(
    object
)
deliveries.loc[idx, "temperature_breach_flag"] = np.nan

# 10 - negative distances
idx = rng.choice(deliveries.index, size=14, replace=False)
deliveries.loc[idx, "distance_km"] = -deliveries.loc[idx, "distance_km"]

# 11 - duplicated product keys in the master
products = pd.concat([products, products.iloc[[7, 31]]], ignore_index=True)

# 12 - negative margin products
products.loc[[3, 22, 41], "unit_price"] = (
    products.loc[[3, 22, 41], "unit_cost"] * 0.88
).round(2)

# 13 - city conformance drift in the depot master
depots.loc[2, "city"] = " leeds"
depots.loc[7, "city"] = "SOUTHAMPTON"

# ------------------------------------------------------------------- write

for name, df in [
    ("products", products),
    ("depots", depots),
    ("orders", orders),
    ("deliveries", deliveries),
]:
    df.to_csv(OUT / f"{name}.csv", index=False)
    print(f"{name:<12} {len(df):>7,} rows  {len(df.columns)} cols")
