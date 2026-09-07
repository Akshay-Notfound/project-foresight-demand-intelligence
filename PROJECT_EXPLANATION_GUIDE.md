# Project FORESIGHT — Complete Explanation & Defense Guide

**Client:** NorthBay Living (D2C Home & Lifestyle Brand)  
**Role:** Data Science & Supply Chain Analytics Engagement Lead  
**Program:** Zidio Development Internship — Data Science & Analytics Track  
**GitHub Repository:** [https://github.com/Akshay-Notfound/project-foresight-demand-intelligence](https://github.com/Akshay-Notfound/project-foresight-demand-intelligence)  
**Live Planning Dashboard:** [https://project-foresight-demand-intelligence.streamlit.app](https://project-foresight-demand-intelligence.streamlit.app)  

---

## 1. Executive Summary & 30-Second Elevator Pitch

> *"Project FORESIGHT is an AI-powered demand forecasting and autonomous inventory intelligence platform built for NorthBay Living, a fast-growing D2C home and lifestyle brand. By transforming fragmented sales, inventory snapshots, and catalogue extracts into weekly SKU-level demand forecasts using Gradient Boosted Decision Trees, FORESIGHT achieves a **+29.4% error reduction** over baseline models across a strict 6-fold rolling-origin backtest. The platform connects directly to an automated 2x2 stockout/overstock risk matrix, an interactive Streamlit operations dashboard, and a production FastAPI scoring microservice — protecting **₹1.0M in sales from stockouts** and identifying **₹26.3M of working capital trapped in excess inventory**."*

---

## 2. Business Problem & Financial Stakes

NorthBay Living operates ~200 active SKUs across multiple home categories (Decor, Furnishings, Kitchenware, Small Appliances). Prior to FORESIGHT, the ops team relied on static spreadsheets, simple historical averages, and intuition, causing two critical financial bottlenecks:

```
                  ┌─────────────────────────────────────────────────────────┐
                  │                 THE INVENTORY DILEMMA                   │
                  └───────────────────────────┬─────────────────────────────┘
                                              │
                    ┌─────────────────────────┴─────────────────────────┐
                    ▼                                                   ▼
       🚨 STOCKOUT SHORTFALLS                               ⏳ OVERSTOCK ACCUMULATION
 • Fast-moving products run out of stock              • Slow-turning products sit in warehouses
   before replenishment orders arrive.                  for months, accumulating storage costs.
 • Results in immediate lost revenue &                • Locks up scarce working capital and risks
   degraded customer trust.                             product obsolescence.
 • ₹1,002,671 in projected sales at risk.            • ₹26,307,779 in trapped working capital.
```

---

## 3. System Architecture & Pipeline Workflow

```
[Raw Data Ingestion]
   ├── sales_daily.csv (93k+ transactions)
   ├── sku_master.csv (200 SKUs, prices, lead times)
   ├── calendar.csv (Promo flags, holidays)
   └── inventory_snapshots.csv (Sparse on-hand stock)
            │
            ▼
[Data Engineering & Hygiene Pipeline (src/pipeline.py)]
   ├── Deduplication of transactions & SKU IDs
   ├── Negative quantity sentinel value removal (-999 error codes)
   ├── Missing revenue imputation (units_sold * unit_price)
   ├── Forward-fill inventory snapshots across non-reporting days
   └── Incomplete trailing week cutoff removal
            │
            ▼
[Weekly Aggregation & Feature Store]
   ├── Weekly SKU demand series (units_sold, revenue)
   ├── Multi-period lag features (1, 2, 4, 8, 52 weeks)
   ├── Rolling moving averages & volatility (4w, 12w rolling mean & std)
   └── Calendar & promotional signals (promo_flag, is_holiday, month)
            │
            ▼
[Demand Forecasting Engine (src/forecast.py)]
   ├── HistGradientBoostingRegressor (Gradient Boosted Decision Trees)
   ├── 6-Fold Rolling-Origin Cross-Validation (Zero lookahead leakage)
   └── 8-Week Forward SKU Demand Projections (WAPE = 0.185 vs 0.262 baseline)
            │
            ▼
[2x2 Inventory Risk Scoring Engine (src/risk.py)]
   ├── Stockout Shortfall Probability vs Overstock Excess Ratio
   └── 4 Quadrants: Reorder Now | Markdown / Clear | Watch | Healthy
            │
            ▼
[Production Operational Interfaces]
   ├── 📊 Streamlit Interactive Planning Dashboard (app/dashboard.py)
   ├── 🔌 FastAPI Real-Time Scoring Microservice (service/main.py)
   └── 📑 Executive Readout Slide Deck (reports/FORESIGHT_Executive_Readout.pptx)
```

---

## 4. In-Depth Component Breakdown

### 4.1 Data Pipeline & Hygiene (`src/pipeline.py`)
- **Deduplication:** Dropped duplicate transactions and redundant SKU master records.
- **Sentinel Filtering:** Removed `-999` negative quantity values that represented data-entry artifacts rather than legitimate return codes.
- **Imputation:** Recovered missing revenue entries via unit price multiplication.
- **Inventory Forward-Fill:** Handled sparse (non-daily) inventory snapshots by forward-filling inventory positions up to the transaction date without leaking future snapshot counts.
- **Trailing Week Hygiene:** Filtered out partial cutoff weeks at the end of the history to prevent artificially skewed demand dips.

---

### 4.2 Machine Learning & Backtesting Rigor (`src/forecast.py`)

#### Grain & Horizon:
- **Grain:** Weekly SKU level (optimal for supply chain planning vs. noisy daily intermittency).
- **Horizon:** 8 weeks forward.

#### Model Architecture:
- `sklearn.ensemble.HistGradientBoostingRegressor` (Gradient Boosted Decision Trees), natively capable of non-linear feature interactions and missing-value handling.

#### Feature Matrix:
1. **Demand Lags:** $t-1, t-2, t-4, t-8$ weeks + $t-52$ week (yearly seasonal baseline).
2. **Rolling Windows:** 4-week and 12-week moving averages and rolling standard deviations.
3. **Calendar Signals:** Month of year, week number, active promotional campaign flags, and holiday indicators.
4. **Categorical Encodings:** Product category hierarchies.

#### Backtesting Methodology:
Evaluated using **Rolling-Origin Cross-Validation** (6 folds). In each fold, the model was trained *only* on data available prior to the origin cutoff date:

$$\text{Fold } k \text{ Train: } [\text{Week}_1 \dots \text{Week}_{\text{origin}_k}] \longrightarrow \text{Test: } [\text{Week}_{\text{origin}_k + 1} \dots \text{Week}_{\text{origin}_k + 8}]$$

#### Performance Comparison:

$$\text{WAPE} = \frac{\sum |y - \hat{y}|}{\sum y}$$

| Metric | Seasonal-Naive Baseline | FORESIGHT Model | Improvement |
|---|---|---|---|
| **Mean WAPE (6 Folds)** | **0.262 (26.2%)** | **0.185 (18.5%)** | **+29.4% Error Reduction** |
| **Forecast Bias** | -0.033 | -0.027 | Lower overall systematic skew |
| **Fold Win Rate** | — | **6 / 6 Folds (100%)** | Consistent across all time periods |

---

### 4.3 2x2 Risk Decisioning Framework (`src/risk.py`)

We compute two distinct risk scores for each SKU:

$$\text{Stockout Risk} = \max\left(0, \frac{\text{Projected 8-wk Demand} - (\text{On Hand} + \text{On Order})}{\text{Projected 8-wk Demand}}\right)$$

$$\text{Overstock Risk} = \max\left(0, \frac{(\text{On Hand} + \text{On Order}) - \text{Projected 8-wk Demand}}{\text{Projected 8-wk Demand}}\right)$$

#### The 4 Decision Quadrants:

| Quadrant | Criteria | Portfolio Impact | Recommended Operational Action |
|---|---|---|---|
| 🚨 **Reorder Now** | Stockout Risk $\ge 15\%$, Overstock $< 50\%$ | 5 SKUs · ₹1,002,671 at risk | Expedite purchase orders; reorder immediately to avoid stockouts before lead time. |
| 🟣 **Markdown / Clear** | Overstock Risk $\ge 50\%$, Stockout $< 15\%$ | 5 SKUs · ₹26,307,779 locked | Launch targeted promotional markdowns or bundled discounts to release capital. |
| 🟡 **Watch / Volatile** | High on both thresholds | 0 SKUs | Investigate demand spikes, supply bottlenecks, or irregular replenishment cycles. |
| 🟢 **Healthy** | Low on both thresholds | 125 SKUs | Maintain regular replenishment cycles; no manual intervention required. |

---

### 4.4 Operations Planning Dashboard (`app/dashboard.py`)

Built with Streamlit and Plotly, providing 5 distinct modules:
1. **Executive Decision Matrix:** Interactive 2x2 scatter matrix with dynamic threshold sliders and category exposure breakdowns.
2. **Priority Reorder & Markdown Queue:** Calculates exact suggested PO units and estimated reorder costs with a one-click **"Export PO Worklist (CSV)"** button.
3. **SKU Intelligence & What-If Sandbox:** Visualizes historical actuals vs forward forecast with $p_{10}-p_{90}$ confidence intervals. Includes live sliders to simulate promo demand lift and supplier lead-time shocks.
4. **Model Performance & Backtest Audit:** Displays 6-fold validation bars and automated data hygiene logs.
5. **API Microservice Explorer:** Live testing playground for ERP integration.

---

### 4.5 Production Scoring Microservice (`service/main.py`)

FastAPI REST microservice deployed on Render:
- `GET /score/{sku_id}` $\rightarrow$ Returns real-time forecast, risk quadrant, weeks of supply, and value at stake.
- `POST /score/batch` $\rightarrow$ Accepts bulk arrays of SKUs for batch inventory planning.
- `GET /health` $\rightarrow$ Health check endpoint for uptime monitoring.

---

## 5. Frequently Asked Questions (Viva / Interview Defense)

### Q1: Why did you choose WAPE instead of RMSE or MAPE?
> **Answer:** *"MAPE (Mean Absolute Percentage Error) divides errors by actuals, which explodes to infinity or produces undefined errors whenever weekly SKU sales are zero. RMSE heavily penalizes high-volume SKUs and fails to provide a business-friendly percentage. WAPE (Weighted Absolute Percentage Error) weights errors by total sales volume, remaining stable with intermittent zero-sales weeks while directly reflecting financial loss."*

### Q2: Why is the forecasting grain weekly instead of daily?
> **Answer:** *"Daily D2C transaction data is zero-inflated and noisy due to day-of-week shopping fluctuations. Aggregating to a weekly grain smooths out high-frequency noise while matching the real-world operational rhythm of NorthBay's suppliers, whose lead times span 10 to 30 days."*

### Q3: How did you ensure zero data leakage in the time-series model?
> **Answer:** *"We used a strict rolling-origin cross-validation structure across 6 folds. For every fold, all lag features, rolling moving averages, and category encodings were generated strictly using data from weeks prior to the fold origin date. Future sales were never accessible during feature engineering."*

### Q4: How does the system handle new client data in production?
> **Answer:** *"The codebase is fully modular. Dropping new raw extracts into `data/raw/` and running `python src/run_all.py` automatically executes data cleaning, re-trains the model, re-runs backtests, recalculates the risk matrix, and updates both the Streamlit dashboard and FastAPI service without modifying any code."*

---

## 6. Project Links & Deliverable Checklist

- **GitHub Repository:** [https://github.com/Akshay-Notfound/project-foresight-demand-intelligence](https://github.com/Akshay-Notfound/project-foresight-demand-intelligence)
- **Live Streamlit Dashboard:** [https://project-foresight-demand-intelligence.streamlit.app](https://project-foresight-demand-intelligence.streamlit.app)
- **FastAPI Documentation:** [https://foresight-scoring-api.onrender.com/docs](https://foresight-scoring-api.onrender.com/docs)
- **Executive Readout Deck:** `reports/FORESIGHT_Executive_Readout.pptx`
- **Data Quality & EDA Memo:** `reports/eda_insight_memo.md`
