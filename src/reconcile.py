"""
Reconciler: takes the cleaned per-source DataFrames and joins them into one
trustworthy, order-level dataset. This is the part a plain "CSV cleaner"
doesn't do -- combining sources that were never designed to fit together.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(slots=True)
class ReconciliationStats:
    orders_in: int
    order_items_in: int
    payments_in: int
    orders_after_join: int
    orders_dropped_no_items: int
    orders_dropped_no_payment: int


def reconcile(
    orders: pd.DataFrame,
    order_items: pd.DataFrame,
    payments: pd.DataFrame,
    customers: pd.DataFrame,
    products: pd.DataFrame,
) -> tuple[pd.DataFrame, ReconciliationStats]:

    orders_in = len(orders)

    # order_items can have multiple rows per order (multiple products) ->
    # aggregate to order level first (groupby), so the join stays 1 row per order.
    items_agg = (
        order_items.groupby("order_id", as_index=False)
        .agg(
            total_price=("price", "sum"),
            total_freight=("freight_value", "sum"),
            n_items=("product_id", "count"),
        )
    )

    # payments: an order can have multiple payment installments -> sum them,
    # and keep the most common payment_type per order.
    payments_agg = (
        payments.groupby("order_id", as_index=False)
        .agg(total_paid=("payment_value", "sum"))
    )
    payment_type = (
        payments.groupby("order_id")["payment_type"]
        .agg(lambda s: s.value_counts().idxmax())
        .reset_index()
    )
    payments_agg = payments_agg.merge(payment_type, on="order_id", how="left")

    merged = orders.merge(items_agg, on="order_id", how="left")
    orders_dropped_no_items = merged["total_price"].isna().sum()

    merged = merged.merge(payments_agg, on="order_id", how="left")
    orders_dropped_no_payment = merged["total_paid"].isna().sum()

    merged = merged.merge(customers, on="customer_id", how="left")

    # products live at the item level (one product per item row), so bring in
    # the dominant category per order for a readable summary column.
    item_products = order_items.merge(products, on="product_id", how="left")
    dominant_category = (
        item_products.groupby("order_id")["product_category_name"]
        .agg(lambda s: s.value_counts().idxmax() if not s.empty else "unknown")
        .reset_index()
        .rename(columns={"product_category_name": "dominant_category"})
    )
    merged = merged.merge(dominant_category, on="order_id", how="left")

    # drop orders we couldn't reconcile (no matching items or payment record --
    # these are the ones a real business would want flagged, not silently kept)
    reconciled = merged.dropna(subset=["total_price", "total_paid"]).copy()

    # DatetimeIndex + resample: monthly order volume, useful in the report
    reconciled["order_purchase_timestamp"] = pd.to_datetime(
        reconciled["order_purchase_timestamp"], errors="coerce"
    )

    stats = ReconciliationStats(
        orders_in=orders_in,
        order_items_in=len(order_items),
        payments_in=len(payments),
        orders_after_join=len(reconciled),
        orders_dropped_no_items=int(orders_dropped_no_items),
        orders_dropped_no_payment=int(orders_dropped_no_payment),
    )

    return reconciled, stats


def monthly_volume(reconciled: pd.DataFrame) -> pd.DataFrame:
    """Time-series reshape: order count and revenue by month."""
    ts = reconciled.set_index("order_purchase_timestamp")
    monthly = ts.resample("MS").agg(
        order_count=("order_id", "count"),
        revenue=("total_paid", "sum"),
    )
    return monthly.reset_index()


def category_by_state_pivot(reconciled: pd.DataFrame) -> pd.DataFrame:
    """pivot/melt demo: revenue by state x category, wide format for the report."""
    long_form = reconciled.groupby(
        ["customer_state", "dominant_category"], as_index=False
    )["total_paid"].sum()
    wide = long_form.pivot(index="customer_state", columns="dominant_category", values="total_paid")
    return wide.fillna(0)
