"""
risk.py — D4: Stockout / overstock risk scoring and decisioning grid.

For every SKU, combines the forecast (src/forecast.py) with the current
inventory position to produce:
  - stockout_risk in [0, 1]: how much projected stock over the SKU's lead
    time falls short of forecast demand over that same window.
  - overstock_risk in [0, 1]: how much on-hand stock exceeds a forward
    demand window (default 8 weeks).
  - a quadrant (Reorder now / Markdown-Clear / Watch-Volatile / Healthy)
    per the brief's Section 08 decisioning grid.
  - rupee value at stake (lost-sales exposure for stockout, locked capital
    for overstock), using each SKU's list_price / unit_cost.

Transparent, rule-based - no black box, so the ops team can see exactly why
a SKU was flagged (D4 acceptance criteria #3).
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"

STOCKOUT_THRESHOLD = 0.15  # >=15% projected shortfall over lead time triggers a flag
OVERSTOCK_THRESHOLD = 0.5  # >=50% of on-hand stock exceeds an 8-week demand window
FORWARD_WINDOW_WEEKS = 8


def load():
    forecast = pd.read_csv(PROCESSED / "forecast.csv", parse_dates=["week_start"])
    master = pd.read_csv(PROCESSED / "master.csv", parse_dates=["date"])
    return forecast, master


def latest_inventory_and_price(master):
    latest_date = master["date"].max()
    snap = (master.sort_values("date")
            .groupby("sku_id")
            .tail(1)[["sku_id", "category", "on_hand_units", "on_order_units",
                      "lead_time_days", "reorder_point", "unit_price"]])
    sku_econ = (master.groupby("sku_id")
                .agg(unit_cost=("unit_price", lambda s: s.mean() * 0.55),  # proxy if not merged
                     avg_price=("unit_price", "mean"))
                .reset_index())
    return snap, latest_date


def score(forecast, master):
    snap, latest_date = latest_inventory_and_price(master)
    fc_agg = (forecast.groupby("sku_id")
              .agg(fc_total=("units_sold", "sum"),
                   fc_weekly_avg=("units_sold", "mean"))
              .reset_index())

    df = snap.merge(fc_agg, on="sku_id", how="inner")

    lead_time_weeks = df["lead_time_days"] / 7
    demand_over_lead_time = df["fc_weekly_avg"] * lead_time_weeks
    available = df["on_hand_units"] + df["on_order_units"]
    shortfall = (demand_over_lead_time - available).clip(lower=0)
    df["stockout_risk"] = (shortfall / demand_over_lead_time.replace(0, np.nan)).clip(0, 1).fillna(0)

    demand_forward = df["fc_weekly_avg"] * FORWARD_WINDOW_WEEKS
    excess = (df["on_hand_units"] - demand_forward).clip(lower=0)
    df["overstock_risk"] = (excess / df["on_hand_units"].replace(0, np.nan)).clip(0, 1).fillna(0)

    def quadrant(row):
        so, ov = row["stockout_risk"], row["overstock_risk"]
        if so >= STOCKOUT_THRESHOLD and ov >= OVERSTOCK_THRESHOLD:
            return "Watch / Volatile"
        if so >= STOCKOUT_THRESHOLD:
            return "Reorder Now"
        if ov >= OVERSTOCK_THRESHOLD:
            return "Markdown / Clear"
        return "Healthy"

    df["quadrant"] = df.apply(quadrant, axis=1)

    action_map = {
        "Reorder Now": "Raise a replenishment order before stock runs out.",
        "Markdown / Clear": "Promote or discount to free up capital.",
        "Watch / Volatile": "Investigate - demand is erratic; review manually.",
        "Healthy": "No action needed; leave as is.",
    }
    df["recommended_action"] = df["quadrant"].map(action_map)

    # rupee value at stake
    df["stockout_value_at_risk"] = (shortfall * df["unit_price"]).round(2)
    df["overstock_capital_locked"] = (excess * df["unit_price"] * 0.55).round(2)  # cost basis proxy
    df["value_at_stake"] = np.where(
        df["quadrant"] == "Reorder Now", df["stockout_value_at_risk"],
        np.where(df["quadrant"] == "Markdown / Clear", df["overstock_capital_locked"],
                 df[["stockout_value_at_risk", "overstock_capital_locked"]].max(axis=1))
    )

    df["snapshot_date"] = latest_date
    return df


def run():
    forecast, master = load()
    scored = score(forecast, master)
    scored.to_csv(PROCESSED / "risk_scores.csv", index=False)

    impact = {
        "total_stockout_value_at_risk": float(scored["stockout_value_at_risk"].sum()),
        "total_overstock_capital_locked": float(scored["overstock_capital_locked"].sum()),
        "n_reorder_now": int((scored["quadrant"] == "Reorder Now").sum()),
        "n_markdown_clear": int((scored["quadrant"] == "Markdown / Clear").sum()),
        "n_watch_volatile": int((scored["quadrant"] == "Watch / Volatile").sum()),
        "n_healthy": int((scored["quadrant"] == "Healthy").sum()),
    }
    pd.Series(impact).to_json(PROCESSED / "risk_impact_summary.json", indent=2)
    print("Risk impact summary:", impact)
    return scored


if __name__ == "__main__":
    run()
