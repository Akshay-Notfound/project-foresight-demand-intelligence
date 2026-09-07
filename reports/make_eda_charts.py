"""Generates labelled PNG charts for the EDA memo and executive readout."""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
OUT = Path(__file__).resolve().parent
plt.rcParams.update({"figure.dpi": 150, "font.size": 10})


def seasonality_chart(master):
    monthly = master.groupby(master["date"].dt.month)["units_sold"].sum()
    fig, ax = plt.subplots(figsize=(6, 3.5))
    ax.bar(monthly.index, monthly.values, color="#4C51BF")
    ax.set_xlabel("Month")
    ax.set_ylabel("Total units sold")
    ax.set_title("Monthly demand seasonality — all SKUs")
    ax.set_xticks(range(1, 13))
    fig.tight_layout()
    fig.savefig(OUT / "chart_seasonality.png")
    plt.close(fig)


def category_revenue_chart(master):
    cat_rev = master.groupby("category")["revenue"].sum().sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(6, 3.5))
    ax.barh(cat_rev.index, cat_rev.values / 1e7, color="#2CA02C")
    ax.set_xlabel("Revenue (₹ crore)")
    ax.set_title("Revenue by category")
    fig.tight_layout()
    fig.savefig(OUT / "chart_category_revenue.png")
    plt.close(fig)


def forecast_vs_baseline_chart():
    backtest = pd.read_csv(PROCESSED / "backtest_results.csv")
    fig, ax = plt.subplots(figsize=(6, 3.5))
    ax.plot(range(len(backtest)), backtest["wape_baseline"], marker="o",
            label="Seasonal-naive baseline", color="#e0a800")
    ax.plot(range(len(backtest)), backtest["wape_model"], marker="o",
            label="FORESIGHT model", color="#4C51BF")
    ax.set_xlabel("Backtest fold (rolling origin)")
    ax.set_ylabel("WAPE (lower is better)")
    ax.set_title("Model vs. baseline — rolling-origin backtest")
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUT / "chart_backtest.png")
    plt.close(fig)


def risk_grid_chart():
    risk = pd.read_csv(PROCESSED / "risk_scores.csv")
    colors = {"Reorder Now": "#d62728", "Watch / Volatile": "#e0a800",
              "Markdown / Clear": "#6f42c1", "Healthy": "#2ca02c"}
    fig, ax = plt.subplots(figsize=(6, 5))
    for q, grp in risk.groupby("quadrant"):
        ax.scatter(grp["overstock_risk"], grp["stockout_risk"],
                   s=(grp["value_at_stake"] / risk["value_at_stake"].max() * 300 + 20),
                   color=colors.get(q, "gray"), label=q, alpha=0.7, edgecolor="white")
    ax.axvline(0.5, color="gray", linestyle="--", linewidth=1)
    ax.axhline(0.15, color="gray", linestyle="--", linewidth=1)
    ax.set_xlabel("Overstock risk →")
    ax.set_ylabel("Stockout risk ↑")
    ax.set_title("Decisioning grid — every SKU, sized by ₹ at stake")
    ax.legend(loc="upper right", fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "chart_risk_grid.png")
    plt.close(fig)


if __name__ == "__main__":
    master = pd.read_csv(PROCESSED / "master.csv", parse_dates=["date"])
    seasonality_chart(master)
    category_revenue_chart(master)
    forecast_vs_baseline_chart()
    risk_grid_chart()
    print("Charts written to", OUT)
