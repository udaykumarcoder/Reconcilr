"""
Builds the human-readable markdown report -- the actual portfolio artifact.
Anyone (technical or not) should be able to open this and understand what
happened to their data and why some rows didn't make it into the final file.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.reconcile import ReconciliationStats


def build_report(
    stats: ReconciliationStats,
    monthly: pd.DataFrame,
    category_pivot: pd.DataFrame,
    benchmark_results: dict,
    profile_summary: str,
    output_path: Path,
) -> None:
    lines: list[str] = []
    lines.append("# Order Reconciliation Report\n")

    lines.append("## Source volumes\n")
    lines.append(f"- Orders read: **{stats.orders_in}**")
    lines.append(f"- Order-item rows read: **{stats.order_items_in}**")
    lines.append(f"- Payment rows read: **{stats.payments_in}**\n")

    lines.append("## Reconciliation outcome\n")
    lines.append(f"- Orders successfully reconciled: **{stats.orders_after_join}**")
    lines.append(
        f"- Orders dropped (no matching order-item record): "
        f"**{stats.orders_dropped_no_items}**"
    )
    lines.append(
        f"- Orders dropped (no matching payment record): "
        f"**{stats.orders_dropped_no_payment}**\n"
    )
    pct_kept = (
        round(100 * stats.orders_after_join / stats.orders_in, 1) if stats.orders_in else 0
    )
    lines.append(f"**{pct_kept}%** of orders were reconciled cleanly end to end.\n")

    lines.append("## Monthly order volume & revenue\n")
    lines.append(monthly.to_markdown(index=False))
    lines.append("")

    lines.append("## Revenue by state x product category (top rows)\n")
    lines.append(category_pivot.head(10).to_markdown())
    lines.append("")

    lines.append("## Performance: Pandas vs Polars (same merge step)\n")
    lines.append(f"- Pandas: **{benchmark_results['pandas_seconds']}s**")
    if benchmark_results["polars_seconds"] is not None:
        lines.append(f"- Polars: **{benchmark_results['polars_seconds']}s**")
    else:
        lines.append("- Polars: not installed, skipped")
    lines.append("")

    lines.append("## Profiling snapshot (reconciliation step)\n")
    lines.append("```")
    lines.append(profile_summary)
    lines.append("```")

    output_path.write_text("\n".join(lines), encoding="utf-8")
