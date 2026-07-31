"""
CLI entry point.

Usage:
    python pipeline.py --input data/raw --output data/output
"""
from __future__ import annotations

import argparse
import logging
from pathlib import Path

from src.config import ORDERS, ORDER_ITEMS, PAYMENTS, CUSTOMERS, PRODUCTS
from src.adapters import (
    OrdersAdapter, OrderItemsAdapter, PaymentsAdapter, CustomersAdapter, ProductsAdapter,
)
from src.exceptions import PipelineError
from src.reconcile import reconcile, monthly_volume, category_by_state_pivot
from src.benchmark import benchmark_merge, profile_reconciliation
from src.report import build_report

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("pipeline")


def run(input_dir: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        orders = OrdersAdapter(ORDERS, input_dir).load()
        order_items = OrderItemsAdapter(ORDER_ITEMS, input_dir).load()
        payments = PaymentsAdapter(PAYMENTS, input_dir).load()
        customers = CustomersAdapter(CUSTOMERS, input_dir).load()
        products = ProductsAdapter(PRODUCTS, input_dir).load()
    except PipelineError as exc:
        logger.error("Pipeline aborted while loading sources: %s", exc)
        raise SystemExit(1) from exc

    def do_reconcile():
        return reconcile(orders, order_items, payments, customers, products)

    profile_summary = profile_reconciliation(do_reconcile)
    reconciled, stats = do_reconcile()

    reconciled_path = output_dir / "reconciled.parquet"
    reconciled.to_parquet(reconciled_path, index=False)
    logger.info("Wrote reconciled dataset -> %s (%d rows)", reconciled_path, len(reconciled))

    monthly = monthly_volume(reconciled)
    category_pivot = category_by_state_pivot(reconciled)

    bench = benchmark_merge(input_dir / ORDERS.file_name, input_dir / ORDER_ITEMS.file_name)

    report_path = output_dir / "report.md"
    build_report(stats, monthly, category_pivot, bench, profile_summary, report_path)
    logger.info("Wrote report -> %s", report_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Order data reconciliation pipeline")
    parser.add_argument("--input", type=Path, default=Path("data/raw"))
    parser.add_argument("--output", type=Path, default=Path("data/output"))
    args = parser.parse_args()
    run(args.input, args.output)


if __name__ == "__main__":
    main()
