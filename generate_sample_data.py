"""
Creates small synthetic CSV files with the SAME column names as the real
Olist dataset, deliberately messy (nulls, duplicates, orphan rows), so you
can build and run the whole pipeline today. Swap in the real Kaggle files
into data/raw/ later -- no code changes needed.
"""
import numpy as np
import pandas as pd
from pathlib import Path

rng = np.random.default_rng(42)
RAW = Path("data/raw")
RAW.mkdir(parents=True, exist_ok=True)

N_ORDERS = 500
STATES = ["SP", "RJ", "MG", "BA", "sp", "rj", None]  # mixed case + missing on purpose
STATUSES = ["delivered", "shipped", "invoiced", "processing", "canceled", "unknown_status"]
CATEGORIES = ["electronics", "furniture", "toys", "beauty", None]

order_ids = [f"ord_{i:05d}" for i in range(N_ORDERS)]
customer_ids = [f"cust_{i % 400:05d}" for i in range(N_ORDERS)]  # some repeat customers

orders = pd.DataFrame({
    "order_id": order_ids,
    "customer_id": customer_ids,
    "order_status": rng.choice(STATUSES, N_ORDERS, p=[0.5, 0.15, 0.1, 0.1, 0.1, 0.05]),
    "order_purchase_timestamp": pd.to_datetime("2024-01-01") + pd.to_timedelta(
        rng.integers(0, 300, N_ORDERS), unit="D"
    ),
    "order_delivered_customer_date": pd.to_datetime("2024-01-05") + pd.to_timedelta(
        rng.integers(0, 310, N_ORDERS), unit="D"
    ),
})
# inject some duplicate rows + a few missing timestamps
orders = pd.concat([orders, orders.sample(5, random_state=1)], ignore_index=True)
orders.loc[orders.sample(10, random_state=2).index, "order_purchase_timestamp"] = None

# order_items: multiple items per order, and a few orphan orders with NO items on purpose
item_rows = []
for oid in order_ids[:-15]:  # last 15 orders deliberately get no items
    n_items = rng.integers(1, 4)
    for _ in range(n_items):
        item_rows.append({
            "order_id": oid,
            "product_id": f"prod_{rng.integers(0, 60):05d}",
            "price": round(float(rng.uniform(10, 500)), 2),
            "freight_value": round(float(rng.uniform(5, 40)), 2),
        })
order_items = pd.DataFrame(item_rows)
# inject a few negative/missing prices (bad data)
order_items.loc[order_items.sample(8, random_state=3).index, "price"] = None
order_items.loc[order_items.sample(4, random_state=4).index, "freight_value"] = -5.0

# payments: a few orders deliberately missing a payment record
payment_rows = []
for oid in order_ids[:-25]:
    n_installments = rng.integers(1, 3)
    for _ in range(n_installments):
        payment_rows.append({
            "order_id": oid,
            "payment_type": rng.choice(["credit_card", "boleto", "voucher", "  credit_card  "]),
            "payment_value": round(float(rng.uniform(10, 400)), 2),
        })
payments = pd.DataFrame(payment_rows)

customers = pd.DataFrame({
    "customer_id": sorted(set(customer_ids)),
})
customers["customer_city"] = rng.choice(["sao paulo", "Rio de Janeiro", " Belo Horizonte", None], len(customers))
customers["customer_state"] = rng.choice(STATES, len(customers))

products = pd.DataFrame({
    "product_id": [f"prod_{i:05d}" for i in range(60)],
    "product_category_name": rng.choice(CATEGORIES, 60),
})

orders.to_csv(RAW / "olist_orders_dataset.csv", index=False)
order_items.to_csv(RAW / "olist_order_items_dataset.csv", index=False)
payments.to_csv(RAW / "olist_order_payments_dataset.csv", index=False)
customers.to_csv(RAW / "olist_customers_dataset.csv", index=False)
products.to_csv(RAW / "olist_products_dataset.csv", index=False)

print(f"Sample data written to {RAW.resolve()}")
