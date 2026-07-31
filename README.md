# Order Data Reconciliation Pipeline

## The business problem (real, not invented)

A small e-commerce seller pulls data from several places that were never designed
to talk to each other:

- an **orders export** (order status, timestamps, customer link)
- an **order items / payments export** (prices, freight, payment installments)
- a **customers export** (location, IDs)
- a **products export** (category, dimensions, weight)

Each file has its own quirks: missing values, duplicate IDs, inconsistent date
formats, category names that need translating, and rows that simply don't line
up with the others. Small businesses hit this constantly with supplier and
marketplace exports (Amazon Seller Central, Shopify, supplier price lists, etc.) —
it's one of the most common "just clean it for me" asks freelancers and data
people get.

This project builds a **reconciliation pipeline**: it ingests several messy,
differently-shaped sources, reconciles them into one trustworthy dataset, and
produces a report a non-technical business owner could read — not just a
cleaned CSV, but a paper trail of what was wrong and what was done about it.

## Dataset

**Olist Brazilian E-Commerce dataset** (real, anonymized commercial data,
~100k orders, 2016–2018): https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce

Download it (free Kaggle login), unzip, and drop these files into `data/raw/`:
- `olist_orders_dataset.csv`
- `olist_order_items_dataset.csv`
- `olist_order_payments_dataset.csv`
- `olist_customers_dataset.csv`
- `olist_products_dataset.csv`

**Don't want to wait for the download?** Run `python generate_sample_data.py`
first — it creates small synthetic files with the *same column names* but
deliberately injected messiness (nulls, dupes, mixed date formats), so the
whole pipeline runs end-to-end today. Swap in the real Kaggle files later;
no code changes needed, same schema.

## Architecture

```
                    ┌─────────────────────┐
                    │   data/raw/*.csv     │   (4-5 independent sources)
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │   SourceAdapter      │   one class per source
                    │   (base class, OOP)  │   - reads in chunks (generator)
                    │                      │   - retries flaky reads (@retry)
                    │                      │   - validates + raises custom
                    │                      │     exceptions on bad rows
                    └──────────┬──────────┘
                               │  clean per-source DataFrame
                    ┌──────────▼──────────┐
                    │   Reconciler         │   merges/joins sources on keys
                    │                      │   - groupby, merge, pivot/melt
                    │                      │   - resolves conflicts (e.g.
                    │                      │     duplicate order rows)
                    └──────────┬──────────┘
                               │  one trusted dataset
                    ┌──────────▼──────────┐
                    │   Reporter           │   before/after row counts,
                    │                      │   % nulls fixed, rows rejected
                    │                      │   + why → markdown report
                    └──────────┬──────────┘
                               │
              ┌────────────────┴────────────────┐
              ▼                                 ▼
     data/output/reconciled.parquet   data/output/report.md
```

Everything runs through a single CLI entry point: `pipeline.py`.

## What each Python concept from your curriculum is doing here

| Concept | File | Role |
|---|---|---|
| `@dataclass(slots=True)` | `src/config.py` | Per-source config (column mapping, key column, date format) |
| Custom exception hierarchy | `src/exceptions.py` | `SchemaMismatchError`, `MissingKeyColumnError`, etc. — caught, logged, never crash the whole run |
| Decorator with args | `src/adapters.py` | `@retry(times=3, delay=1)` wraps each file read, simulating a flaky export |
| Generators / `yield from` | `src/adapters.py` | `read_in_chunks()` streams large CSVs without loading fully into memory |
| Context managers | `src/adapters.py` | `open_source()` wraps file handling, logs duration on exit |
| OOP + inheritance | `src/adapters.py` | `SourceAdapter` base class, one subclass per source |
| Type hints + mypy | everywhere | Run `mypy src/` to check |
| Pandas: fillna/interpolate/dedup | `src/adapters.py` | Per-source cleaning before merge |
| Pandas: merge/groupby/pivot/melt | `src/reconcile.py` | Joining sources, resolving conflicts, reshaping for report |
| DatetimeIndex / resample | `src/reconcile.py` | Normalizing timestamps, order-volume-over-time summary |
| Pandas vs Polars benchmark | `src/benchmark.py` | Times the merge step in both, records result in report |
| Profiling | `src/benchmark.py` | `cProfile`/`timeit` on the reconciliation step |

## Running it

```bash
pip install -r requirements.txt
python generate_sample_data.py      # only if you don't have the real Kaggle files yet
python pipeline.py --input data/raw --output data/output
```

Output:
- `data/output/reconciled.parquet` — the clean, joined dataset
- `data/output/report.md` — the data-quality report (open this first)

## Design decisions worth explaining in an interview

- **Why Parquet, not CSV, for output?** Preserves dtypes, much smaller/faster
  for downstream consumers.
- **Why a report, not just a clean file?** A clean file with no paper trail is
  a black box. The report is what makes the pipeline *trustworthy* — you can
  see exactly what was assumed or discarded.
- **Why generators for reading?** The real Kaggle files are ~100k rows each;
  this is small enough to fit in memory, but the pattern is what you'd need
  the moment a source is 10x bigger — it's future-proofing, and it's explainable.
- **Why Pandas vs Polars benchmark?** Shows you understand there's a
  performance tradeoff and can justify a tool choice with numbers, not vibes.





pip install -r requirements.txt
python generate_sample_data.py
python pipeline.py --input data/raw --output data/output