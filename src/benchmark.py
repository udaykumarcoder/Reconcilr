"""
Benchmark the reconciliation merge step: Pandas vs Polars, plus a cProfile
snapshot of the pandas path. This is what turns "I cleaned some data" into
"I can justify a tool choice with numbers."
"""
from __future__ import annotations

import cProfile
import io
import pstats
import time
from pathlib import Path

import pandas as pd

try:
    import polars as pl
    POLARS_AVAILABLE = True
except ImportError:
    POLARS_AVAILABLE = False


def benchmark_merge(orders_path: Path, items_path: Path) -> dict:
    """Time the same orders/order_items merge in Pandas and (if installed) Polars."""
    results: dict = {}

    start = time.perf_counter()
    orders_pd = pd.read_csv(orders_path)
    items_pd = pd.read_csv(items_path)
    agg_pd = items_pd.groupby("order_id", as_index=False)["price"].sum()
    _ = orders_pd.merge(agg_pd, on="order_id", how="left")
    results["pandas_seconds"] = round(time.perf_counter() - start, 4)

    if POLARS_AVAILABLE:
        start = time.perf_counter()
        orders_pl = pl.read_csv(orders_path)
        items_pl = pl.read_csv(items_path)
        agg_pl = items_pl.group_by("order_id").agg(pl.col("price").sum())
        _ = orders_pl.join(agg_pl, on="order_id", how="left")
        results["polars_seconds"] = round(time.perf_counter() - start, 4)
    else:
        results["polars_seconds"] = None

    return results


def profile_reconciliation(func, *args, **kwargs) -> str:
    """Run `func` under cProfile and return a short human-readable summary
    of the top time-consuming calls."""
    profiler = cProfile.Profile()
    profiler.enable()
    func(*args, **kwargs)
    profiler.disable()

    stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stream).sort_stats("cumulative")
    stats.print_stats(8)
    return stream.getvalue()
