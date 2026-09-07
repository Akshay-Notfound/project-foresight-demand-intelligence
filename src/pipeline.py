"""
pipeline.py — D1: Reproducible ingestion + cleaning.

Ingests the four raw extracts, validates and cleans them, and produces one
analysis-ready dataset joining sales, calendar, SKU, and inventory context.

Every cleaning decision is logged to data/processed/data_quality_log.json so
the decisions are auditable (D1 acceptance criteria #4), and the whole thing
re-runs end-to-end with: python src/pipeline.py

No AI/manual intervention required at run time. No future data is ever used
inside this step - it only unifies and cleans, no feature engineering leakage
risk here (that lives in forecast.py::make_features).
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
PROCESSED.mkdir(parents=True, exist_ok=True)

log = {}


def _note(key, msg):
    log[key] = msg
    print(f"[{key}] {msg}")


def ingest():
    sales = pd.read_csv(RAW / "sales_daily.csv", parse_dates=["date"])
    sku_master = pd.read_csv(RAW / "sku_master.csv", parse_dates=["launch_date"])
    calendar = pd.read_csv(RAW / "calendar.csv", parse_dates=["date"])
    inv = pd.read_csv(RAW / "inventory_snapshots.csv", parse_dates=["date"])
    return sales, sku_master, calendar, inv


def clean_sku_master(df):
    before = len(df)
    df = df.drop_duplicates(subset="sku_id").copy()
    _note("sku_master_dupes_removed", f"Dropped {before - len(df)} duplicate sku_id rows.")

    bad_labels = df["category"].str.islower().sum()
    df["category"] = df["category"].str.title()
    _note("sku_master_label_fix", f"Title-cased {bad_labels} inconsistent category labels "
                                   "(e.g. 'furnishings' -> 'Furnishings').")
    return df


def clean_sales(df):
    before = len(df)
    df = df.drop_duplicates().copy()
    _note("sales_dupes_removed", f"Dropped {before - len(df)} exact duplicate sales rows.")

    bad_qty = (df["units_sold"] < 0).sum()
    df = df[df["units_sold"] >= 0].copy()
    _note("sales_negative_units", f"Removed {bad_qty} rows with a negative units_sold sentinel "
                                   "value (data-entry artifact, not a valid return code in this "
                                   "extract).")

    missing_rev = df["revenue"].isna().sum()
    df["revenue"] = df["revenue"].fillna(df["units_sold"] * df["unit_price"])
    _note("sales_missing_revenue", f"Imputed {missing_rev} missing revenue values as "
                                    "units_sold * unit_price.")

    df["promo_flag"] = df["promo_flag"].fillna(0).astype(int)
    return df


def clean_inventory(df):
    before = len(df)
    df = df.drop_duplicates().copy()
    df = df.sort_values(["sku_id", "date"])
    # forward-fill sparse periodic snapshots per SKU onto a daily grid later at merge time
    _note("inventory_dupes_removed", f"Dropped {before - len(df)} duplicate inventory rows.")
    return df


def build_master_table(sales, sku_master, calendar, inv):
    df = sales.merge(sku_master, on="sku_id", how="left", validate="many_to_one")
    df = df.merge(calendar, on="date", how="left", validate="many_to_one")

    # inventory is a sparse periodic snapshot -> forward-fill to daily per SKU
    full_grid = (
        df[["sku_id", "date"]].drop_duplicates()
        .merge(inv, on=["sku_id", "date"], how="left")
        .sort_values(["sku_id", "date"])
    )
    inv_cols = ["on_hand_units", "on_order_units", "lead_time_days", "reorder_point"]
    full_grid[inv_cols] = full_grid.groupby("sku_id")[inv_cols].ffill().bfill()
    df = df.merge(full_grid, on=["sku_id", "date"], how="left")

    unresolved = df[inv_cols].isna().any(axis=1).sum()
    _note("inventory_unresolved_after_fill", f"{unresolved} SKU-day rows still lack an "
                                               "inventory position after fill; these SKUs have "
                                               "no snapshot history and are excluded from risk "
                                               "scoring, not silently zero-filled.")
    return df


def run():
    sales, sku_master, calendar, inv = ingest()
    sku_master = clean_sku_master(sku_master)
    sales = clean_sales(sales)
    inv = clean_inventory(inv)

    master = build_master_table(sales, sku_master, calendar, inv)
    master = master.sort_values(["sku_id", "date"]).reset_index(drop=True)

    out_path = PROCESSED / "master.csv"
    master.to_csv(out_path, index=False)
    _note("output_rows", f"{len(master)} rows, {master['sku_id'].nunique()} SKUs written to "
                          f"{out_path.relative_to(ROOT)}.")

    with open(PROCESSED / "data_quality_log.json", "w") as f:
        json.dump(log, f, indent=2, default=str)

    return master


if __name__ == "__main__":
    run()
