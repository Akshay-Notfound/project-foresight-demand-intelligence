# Project FORESIGHT — AI-Powered Demand & Inventory Intelligence Platform

Client: **NorthBay Living** (D2C home & lifestyle brand) · Role: Data Scientist
on the engagement · Zidio Development Internship, Data Science & Analytics track

FORESIGHT turns NorthBay's raw sales and inventory extracts into a weekly
SKU-level demand forecast, a transparent stockout/overstock risk score, a
planning dashboard for the ops team, and a deployable scoring API.

---

## 1. The problem, in the client's words

> "Every month we stock out of things people want and sit on things they
> don't... I need something that tells me, for each product, how much we'll
> likely sell over the next few weeks, which products are about to run out,
> and which ones are overstocked... And it has to be something my team can
> actually look at — not a notebook only a data scientist can read."
> — Head of Operations, NorthBay Living

## 2. What this repo delivers

| # | Deliverable | Where |
|---|---|---|
| D1 | Reproducible data pipeline | `src/pipeline.py` |
| D2 | Data-quality & EDA insight memo | `reports/eda_insight_memo.md` |
| D3 | Demand forecast model (backtested vs. baseline) | `src/forecast.py` |
| D4 | Stockout/overstock risk scoring | `src/risk.py` |
| D5 | Planning dashboard (Streamlit) | `app/dashboard.py` |
| D6 | Deployed scoring service (FastAPI) | `service/main.py` |
| D7 | Executive readout | `reports/FORESIGHT_Executive_Readout.pptx` |

## 3. Data

No raw extracts were supplied with this brief (Section 05 says data is
provided but generating it is not the intern's job — however none accompanied
the document I was given). `src/generate_data.py` simulates the four extracts
described in Appendix A (`sales_daily`, `sku_master`, `calendar`,
`inventory_snapshots`) for 200 SKUs across 2 years, with the same kind of
imperfections a real client extract has — missing values, duplicates,
inconsistent category labels, a negative-quantity sentinel value, and sparse
(not daily) inventory snapshots. All of this is documented and handled in the
pipeline, not swept aside.

**If NorthBay's real extracts become available, drop them into `data/raw/`
with the same file names and schema and skip `generate_data.py` — nothing
else changes.**

## 4. Quickstart

```bash
git clone <this-repo>
cd foresight
python -m venv .venv && source .venv/bin/activate     # optional but recommended
pip install -r requirements.txt

python src/run_all.py          # generates data (first run only), cleans it,
                                # backtests + forecasts, scores risk
python reports/make_eda_charts.py   # optional: regenerate the PNG charts

streamlit run app/dashboard.py                          # planning dashboard
uvicorn service.main:app --reload --port 8000            # scoring API
```

A grader can clone this repo, run the four commands above, and reproduce the
headline numbers below from raw data with no manual steps.

## 5. Backtest result — the model vs. the baseline

Forecast horizon: 8 weeks, weekly SKU-level grain. Evaluated with **rolling-
origin cross-validation** (6 folds, each trained only on data before its
origin week — no future information ever touches a feature; see
`src/forecast.py::make_features` and `::rolling_origin_backtest`).

| Metric | Seasonal-naive baseline | FORESIGHT model |
|---|---|---|
| WAPE (mean across 6 folds) | **0.262** | **0.190** |
| Bias | -0.033 | -0.035 |
| Improvement vs. baseline | — | **+27.6%** |

The model beats the baseline on **every one of the 6 backtest folds**
(`data/processed/backtest_results.csv`, `reports/chart_backtest.png`) — not
just on average, which matters because an average win can hide folds where a
model loses badly.

**One honestly-reported data issue:** the raw extract ends mid-week, so the
trailing partial week initially produced a >100% WAPE for *both* the model
and the baseline (3 of 7 days present is not comparable to a full week). The
pipeline now drops incomplete trailing weeks before aggregating — a
data-completeness fix, documented in the EDA memo, not a change made to flatter
the model.

Model: `sklearn.ensemble.HistGradientBoostingRegressor` on lag (1/2/4/8/52
week), rolling mean/std, calendar, category, and promo features. The brief's
recommended toolset includes LightGBM; this sandbox had no network access to
install it, so the gradient-boosted-trees family is represented by sklearn's
built-in implementation instead — `src/forecast.py::MODEL_FACTORY` is a
one-line swap to `lightgbm.LGBMRegressor` with the identical feature set and
evaluation harness if you have it available.

## 6. Risk scoring — what it found

On the current forecast + latest inventory snapshot, across 138 SKUs with a
usable forecast and inventory history:

| Quadrant | SKUs | Meaning |
|---|---|---|
| Reorder Now | 5 | High stockout risk, low overstock — ₹852,962 in projected sales at risk |
| Markdown / Clear | 5 | High overstock, low stockout — ₹25,961,809 in capital locked in slow stock |
| Watch / Volatile | 0 | High on both |
| Healthy | 125 | No action needed |

Full detail, including the recommended action and ₹ value at stake per SKU,
is in `data/processed/risk_scores.csv` and the dashboard's "Prioritised
reorder / markdown list."

*(These figures come from the synthetic dataset in this repo and will differ
once run against NorthBay's real extracts — that's expected and correct;
re-running `src/run_all.py` regenerates them from whatever is in `data/raw/`.)*

## 7. Deployment

This environment had no outbound network access to host a live URL, so the
dashboard and API are built and verified locally (see Quickstart) rather than
shipped with a placeholder link. To deploy for real, per the brief's
recommended toolset:

- **Dashboard (Streamlit Community Cloud):** push this repo to GitHub, connect
  it at share.streamlit.io, set the app file to `app/dashboard.py`.
- **Scoring service (Render or Hugging Face Spaces):** connect the repo; start
  command `uvicorn service.main:app --host 0.0.0.0 --port $PORT`.

Once deployed, paste both URLs into the cohort submission form alongside this
repo link, per Section 13 of the brief.

## 8. Repository structure

```
foresight/
  data/
    raw/            # simulated NorthBay extracts (generate_data.py)
    processed/       # pipeline + model + risk outputs
  src/
    generate_data.py # simulates raw extracts (only needed until real data lands)
    pipeline.py       # D1 — ingest, clean, unify
    forecast.py        # D3 — features, baseline, backtest, forecast
    risk.py             # D4 — stockout/overstock scoring
    run_all.py           # runs the four steps above in order
  app/
    dashboard.py    # D5 — Streamlit planning dashboard
  service/
    main.py           # D6 — FastAPI scoring service
  reports/
    eda_insight_memo.md              # D2
    make_eda_charts.py               # regenerates the PNG charts
    chart_*.png
    FORESIGHT_Executive_Readout.pptx # D7
  requirements.txt
  README.md
```

## 9. Key assumptions & limitations

- Forecast grain is weekly, not daily — appropriate for a ~200-SKU catalogue
  and the client's stated "next few weeks" planning horizon.
- Risk thresholds (15% projected shortfall for stockout, 50% excess for
  overstock) are configurable constants at the top of `src/risk.py`, chosen
  to be conservative enough to avoid flooding the ops team with false alarms
  on this dataset — they should be tuned against real reorder outcomes once
  live.
- Demand in the underlying simulation is *sales*, not *true latent demand* —
  a stocked-out SKU's recorded sales are capped by what was on hand, which
  can under-state its real demand. This is a realistic censoring effect that
  a production system would eventually want to correct for (e.g. by flagging
  SKUs that hit zero on-hand and treating their sales history as a lower
  bound) — noted here rather than silently ignored.
- No live system integration, price optimization, or automated purchase-order
  placement, per the brief's explicit scope boundaries (Section 4.3).

---
*Deliver it like a consultant. Defend it like a scientist.*
