"""
dashboard.py — D5: Planning dashboard for NorthBay's ops team.

Run with:  streamlit run app/dashboard.py
Reads the outputs of src/pipeline.py, src/forecast.py, src/risk.py from
data/processed/. Re-run those three scripts first (or `python src/run_all.py`)
whenever the raw data changes.
"""
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"

st.set_page_config(page_title="FORESIGHT — NorthBay Planning", layout="wide")


@st.cache_data
def load_data():
    risk = pd.read_csv(PROCESSED / "risk_scores.csv")
    weekly = pd.read_csv(PROCESSED / "weekly_history.csv", parse_dates=["week_start"])
    forecast = pd.read_csv(PROCESSED / "forecast.csv", parse_dates=["week_start"])
    return risk, weekly, forecast


def empty_state(msg):
    st.info(msg)


try:
    risk, weekly, forecast = load_data()
except FileNotFoundError:
    st.title("FORESIGHT — Planning Dashboard")
    empty_state(
        "No processed data found yet. Run the pipeline first:\n\n"
        "```\npython src/pipeline.py\npython src/forecast.py\npython src/risk.py\n```"
    )
    st.stop()

st.title("📦 FORESIGHT — NorthBay Living Planning Dashboard")
st.caption("Weekly SKU-level demand forecast, stockout/overstock risk, and reorder guidance.")

# ---- Sidebar filters ----
st.sidebar.header("Filters")
categories = ["All"] + sorted(risk["category"].dropna().unique().tolist())
cat_choice = st.sidebar.selectbox("Category", categories)
sku_search = st.sidebar.text_input("Search SKU ID")
quadrant_choice = st.sidebar.multiselect(
    "Risk quadrant", sorted(risk["quadrant"].unique().tolist()),
    default=sorted(risk["quadrant"].unique().tolist())
)

filtered = risk.copy()
if cat_choice != "All":
    filtered = filtered[filtered["category"] == cat_choice]
if sku_search:
    filtered = filtered[filtered["sku_id"].str.contains(sku_search, case=False)]
if quadrant_choice:
    filtered = filtered[filtered["quadrant"].isin(quadrant_choice)]

if filtered.empty:
    empty_state("No SKUs match the current filters. Try widening your selection.")
    st.stop()

# ---- KPI row ----
c1, c2, c3, c4 = st.columns(4)
c1.metric("SKUs in view", len(filtered))
c2.metric("Reorder now", int((filtered["quadrant"] == "Reorder Now").sum()))
c3.metric("Markdown / clear", int((filtered["quadrant"] == "Markdown / Clear").sum()))
c4.metric("Capital at stake (₹)", f"{filtered['value_at_stake'].sum():,.0f}")

st.divider()

# ---- Decisioning grid ----
st.subheader("Decisioning view")
fig = px.scatter(
    filtered, x="overstock_risk", y="stockout_risk", size="value_at_stake",
    color="quadrant", hover_name="sku_id",
    hover_data={"recommended_action": True, "value_at_stake": ":,.0f"},
    color_discrete_map={
        "Reorder Now": "#d62728", "Watch / Volatile": "#e0a800",
        "Markdown / Clear": "#6f42c1", "Healthy": "#2ca02c",
    },
    labels={"overstock_risk": "Overstock risk →", "stockout_risk": "Stockout risk ↑"},
)
fig.add_vline(x=0.5, line_dash="dash", line_color="gray")
fig.add_hline(y=0.15, line_dash="dash", line_color="gray")
st.plotly_chart(fig, use_container_width=True)

st.divider()

# ---- Prioritised action list ----
st.subheader("Prioritised reorder / markdown list")
priority = (
    filtered[filtered["quadrant"] != "Healthy"]
    .sort_values("value_at_stake", ascending=False)
    [["sku_id", "category", "quadrant", "recommended_action", "stockout_risk",
      "overstock_risk", "value_at_stake"]]
)
if priority.empty:
    empty_state("No SKUs currently need action - everything in this view is healthy.")
else:
    st.dataframe(
        priority.style.format({"stockout_risk": "{:.0%}", "overstock_risk": "{:.0%}",
                                "value_at_stake": "₹{:,.0f}"}),
        use_container_width=True, hide_index=True,
    )

st.divider()

# ---- Forecast vs actual for a chosen SKU ----
st.subheader("Forecast vs actual — pick a SKU")
sku_options = sorted(filtered["sku_id"].unique().tolist())
chosen_sku = st.selectbox("SKU", sku_options)

hist = weekly[weekly["sku_id"] == chosen_sku].sort_values("week_start")
fc = forecast[forecast["sku_id"] == chosen_sku].sort_values("week_start")

if hist.empty:
    empty_state("No history available for this SKU.")
else:
    hist_tail = hist.tail(26)
    fig2 = px.line(hist_tail, x="week_start", y="units_sold", labels={"units_sold": "Units / week"})
    fig2.data[0].name = "Actual"
    fig2.data[0].showlegend = True
    if not fc.empty:
        fig2.add_scatter(x=fc["week_start"], y=fc["units_sold"], mode="lines+markers",
                          name="Forecast", line=dict(dash="dash", color="#6f42c1"))
    st.plotly_chart(fig2, use_container_width=True)

st.caption("Source: Project FORESIGHT pipeline (src/pipeline.py → forecast.py → risk.py). "
           "Backtest WAPE vs. baseline is reported in reports/eda_insight_memo.md and the README.")
