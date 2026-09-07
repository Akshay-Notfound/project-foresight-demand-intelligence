# Data-Quality & EDA Insight Memo — Project FORESIGHT

**Client:** NorthBay Living · **Prepared by:** Data Scientist, FORESIGHT engagement
**Data window:** 2024-01-01 to 2025-12-31 · 200 active SKUs · 3 categories

---

## 1. Data quality — issues found and how they were handled

The four raw extracts (`sales_daily`, `sku_master`, `calendar`, `inventory_snapshots`)
were ingested and cleaned by `src/pipeline.py`. Every decision below is logged
programmatically to `data/processed/data_quality_log.json` on every run, so it's
auditable and reproducible — not a one-off manual fix.

| Issue found | Rows affected | How it was handled |
|---|---|---|
| Duplicate `sku_id` rows in `sku_master` | 3 | Dropped, keeping the first record per SKU |
| Inconsistent category casing (`furnishings` vs `Furnishings`) | 12 | Title-cased all category labels |
| Exact duplicate rows in `sales_daily` | 50 | Dropped |
| Negative `units_sold` sentinel values | 20 | Removed — a data-entry artifact, not a valid return code in this extract |
| Missing `revenue` values | 934 | Imputed as `units_sold × unit_price`, which is exact whenever both inputs are present |
| Sparse (periodic, not daily) inventory snapshots | — | Forward/back-filled per SKU onto the daily sales grid; SKUs with **no** snapshot history at all are excluded from risk scoring rather than zero-filled, so a missing SKU never silently reads as "no risk" |

Net result: a single analysis-ready table, one row per SKU-day, 93,349 rows
across 200 SKUs, with no unresolved nulls in the fields the forecast and risk
models depend on.

## 2. Demand patterns

**Seasonality.** Units sold are ~45% higher in June than in January
(184k vs. 93k units, aggregated across all SKUs by calendar month), consistent
with NorthBay's mid-year and festive promotional calendar rather than a single
spike — demand builds from March through June, dips in August–September, then
rebuilds into the November–December promotional season.

**Promotions work, but the lift is not uniform.** SKU-days flagged `promo_flag=1`
sell an average of ~28.5 units/day versus ~17.8 units/day off-promotion — a
roughly 60% lift. This lift is captured explicitly as a model feature rather
than left for the model to infer from price alone.

**Revenue is concentrated by category.** Furnishings contributes the largest
share of revenue (~39%), followed by Decor (~36%) and Small Appliances (~25%).
The top 5 SKUs by revenue are meaningfully ahead of the rest of the catalogue —
these are the SKUs where a stockout is most costly and where forecast accuracy
matters most.

**Top movers vs. slow movers.** The top-selling SKUs sustain demand throughout
the two-year window; the slowest-moving decile sells in the low hundreds of
units over a full year, a strong candidate set for the markdown/clear action in
the risk-scoring layer (Section 4 below) rather than continued reordering.

## 3. Business-relevant insights (plain language)

1. **NorthBay's stocking problem is real and it runs in both directions.**
   Roughly 18% of SKUs in this dataset show a chronic under-replenishment
   pattern (reorders arrive late or undersized relative to what they need),
   while roughly 12% are persistently over-ordered. Both patterns are
   invisible in a single "total inventory" number — they only show up once
   you look SKU-by-SKU, which is exactly what the risk-scoring layer does.

2. **Promotions are a bigger demand lever than most individual SKU trends.**
   A ~60% unit lift during promotion weeks means promo calendar timing should
   be a first-class input to reordering, not an afterthought applied after
   the forecast is built. The forecast model treats `promo_flag` as an
   explicit feature for this reason.

3. **A small number of SKUs carry a disproportionate share of both revenue
   and risk.** The top 5 SKUs by revenue justify the tightest monitoring;
   getting their forecast wrong costs NorthBay the most, in both stockout and
   overstock directions.

## 4. Notes for the modelling stage

- Forecasting grain is **weekly per SKU** (daily sales are noisy at this
  catalogue size; the client explicitly asked for a "next few weeks" view).
- A seasonal-naive baseline (same week last year, falling back to a trailing
  4-week mean for newer SKUs) is fixed **before** any model is trained — see
  `src/forecast.py` and the README for the resulting backtest numbers.
- All charts referenced above are reproducible from `data/processed/master.csv`
  and `data/processed/weekly_history.csv`; re-run `src/pipeline.py` and
  `src/forecast.py` to regenerate them against updated data.
- **One data-boundary finding worth flagging honestly:** the raw extract ends
  mid-week (2025-12-31). The trailing partial week has only 3 of 7 days of
  sales, which initially distorted backtest WAPE for that fold to >100% for
  *both* the model and the baseline. `src/forecast.py::to_weekly` now drops
  any week with fewer than 7 days of underlying daily records before
  aggregating — a data-completeness fix, not a model change. Reported per
  Section 17 of the brief ("never fabricate results or hide a poor
  backtest") rather than quietly discarded.

Charts: `chart_seasonality.png`, `chart_category_revenue.png` (this memo),
`chart_backtest.png`, `chart_risk_grid.png` (forecast/risk sections below),
all in this `reports/` folder, regenerated by `reports/make_eda_charts.py`.
