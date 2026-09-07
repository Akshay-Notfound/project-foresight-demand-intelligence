"""
generate_data.py — Simulates NorthBay Living's raw extracts.

Per the engagement brief (Section 05): "Data is provided — generating it is
not your job." No raw extracts were supplied with this brief, so this script
creates a realistic, deliberately-imperfect stand-in with the exact schema
described in Appendix A (sales_daily, sku_master, calendar,
inventory_snapshots), including missing values, duplicates, and label
inconsistencies that the pipeline (src/pipeline.py) must handle.

Run once: python src/generate_data.py
Writes CSVs to data/raw/. Seeded for reproducibility.
"""
import numpy as np
import pandas as pd
from pathlib import Path

RNG = np.random.default_rng(42)
RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)

START = pd.Timestamp("2024-01-01")
END = pd.Timestamp("2025-12-31")
DATES = pd.date_range(START, END, freq="D")

CATEGORIES = {
    "Furnishings": ["Sofas", "Chairs", "Tables"],
    "Decor": ["Wall Art", "Rugs", "Lighting"],
    "Small Appliances": ["Kettles", "Blenders", "Heaters"],
}

N_SKUS = 200


def make_sku_master():
    rows = []
    for i in range(1, N_SKUS + 1):
        sku_id = f"SKU{i:04d}"
        cat = RNG.choice(list(CATEGORIES.keys()), p=[0.4, 0.35, 0.25])
        subcat = RNG.choice(CATEGORIES[cat])
        launch_date = START + pd.Timedelta(days=int(RNG.integers(0, 500)))
        unit_cost = round(float(RNG.uniform(150, 4500)), 2)
        list_price = round(unit_cost * RNG.uniform(1.6, 2.8), 2)
        # inject a few label inconsistencies on purpose
        if RNG.random() < 0.03:
            cat = cat.lower()
        rows.append([sku_id, cat, subcat, launch_date, unit_cost, list_price])
    df = pd.DataFrame(rows, columns=["sku_id", "category", "subcategory", "launch_date",
                                      "unit_cost", "list_price"])
    # a couple of exact duplicate rows, as real extracts have
    df = pd.concat([df, df.sample(3, random_state=1)], ignore_index=True)
    return df


def make_calendar():
    df = pd.DataFrame({"date": DATES})
    df["week"] = df["date"].dt.isocalendar().week.astype(int)
    df["month"] = df["date"].dt.month
    df["season"] = df["month"] % 12 // 3 + 1
    df["season"] = df["season"].map({1: "Winter", 2: "Spring", 3: "Summer", 4: "Autumn"})
    # simple India-ish holiday set + a promo calendar
    holidays = pd.to_datetime(["2024-01-26", "2024-08-15", "2024-10-02", "2024-11-01",
                                "2024-12-25", "2025-01-26", "2025-08-15", "2025-10-02",
                                "2025-11-01", "2025-12-25"])
    df["is_holiday"] = df["date"].isin(holidays).astype(int)
    df["promo_event"] = ""
    for start, name in [("2024-06-15", "Summer Sale"), ("2024-10-15", "Festive Sale"),
                         ("2024-11-25", "Black Friday"), ("2025-01-01", "New Year Sale"),
                         ("2025-06-15", "Summer Sale"), ("2025-10-15", "Festive Sale"),
                         ("2025-11-25", "Black Friday")]:
        rng_start = pd.Timestamp(start)
        mask = (df["date"] >= rng_start) & (df["date"] < rng_start + pd.Timedelta(days=7))
        df.loc[mask, "promo_event"] = name
    return df


def make_sales_and_inventory(sku_master, calendar):
    sales_rows = []
    inv_rows = []
    cal = calendar.set_index("date")
    for _, sku in sku_master.drop_duplicates("sku_id").iterrows():
        sku_id = sku["sku_id"]
        base = RNG.uniform(2, 40)  # base daily demand
        trend = RNG.uniform(-0.0005, 0.001)
        weekly_amp = RNG.uniform(0.1, 0.4)
        seasonal_amp = RNG.uniform(0.1, 0.5)
        noise_sd = base * RNG.uniform(0.15, 0.35)
        launch = sku["launch_date"]
        on_hand = RNG.uniform(50, 400)
        lead_time = int(RNG.integers(7, 30))
        reorder_point = round(base * lead_time * RNG.uniform(0.8, 1.3), 0)
        on_order = 0
        dead_stock = RNG.random() < 0.08  # ~8% dead SKUs
        # ~18% of SKUs are chronically under-planned by NorthBay's current
        # process (the client's actual complaint): replenishment is delayed
        # or undersized, so they run down toward stockout.
        under_planned = RNG.random() < 0.18
        # ~10% are systematically over-ordered - cash sitting in slow stock.
        over_planned = (not under_planned) and RNG.random() < 0.12

        for d in DATES:
            if d < launch:
                continue
            t = (d - launch).days
            dow = d.dayofweek
            week_factor = 1 + weekly_amp * np.sin(2 * np.pi * dow / 7)
            month = d.month
            season_factor = 1 + seasonal_amp * np.sin(2 * np.pi * (month - 1) / 12)
            promo = cal.loc[d, "promo_event"] != ""
            holiday = cal.loc[d, "is_holiday"] == 1
            demand = base * (1 + trend * t) * week_factor * season_factor
            if dead_stock:
                demand *= max(0, 1 - t / 400)
            if promo:
                demand *= RNG.uniform(1.4, 2.2)
            if holiday:
                demand *= RNG.uniform(0.6, 1.3)
            demand = max(0, demand + RNG.normal(0, noise_sd))
            units_sold = int(round(demand))

            # simulate stockouts capping sales at on_hand
            units_sold = min(units_sold, max(0, int(on_hand)))
            unit_price = sku["list_price"] * (0.85 if promo else 1.0)
            revenue = round(units_sold * unit_price, 2)

            sales_rows.append([d, sku_id, units_sold, revenue, round(unit_price, 2),
                                int(promo)])

            # crude inventory simulation
            on_hand -= units_sold
            if on_order > 0 and t % lead_time == 0:
                on_hand += on_order
                on_order = 0
            if on_hand < reorder_point and on_order == 0:
                if under_planned:
                    # reorders late and undersized - this is the client's
                    # actual pain point: chronic near-stockout.
                    if RNG.random() < 0.4:
                        on_order = reorder_point * RNG.uniform(0.4, 0.8)
                elif over_planned:
                    on_order = reorder_point * RNG.uniform(3.0, 5.0)
                else:
                    on_order = reorder_point * RNG.uniform(1.5, 2.5)
            on_hand = max(on_hand, 0)

            if d.day in (1, 8, 15, 22):  # periodic snapshot, not daily
                inv_rows.append([d, sku_id, round(on_hand, 0), round(on_order, 0),
                                  lead_time, reorder_point])

    sales = pd.DataFrame(sales_rows, columns=["date", "sku_id", "units_sold", "revenue",
                                               "unit_price", "promo_flag"])
    inv = pd.DataFrame(inv_rows, columns=["date", "sku_id", "on_hand_units", "on_order_units",
                                           "lead_time_days", "reorder_point"])

    # inject realistic messiness: missing values, dupes, bad labels
    miss_idx = sales.sample(frac=0.01, random_state=2).index
    sales.loc[miss_idx, "revenue"] = np.nan
    sales = pd.concat([sales, sales.sample(50, random_state=3)], ignore_index=True)
    neg_idx = sales.sample(20, random_state=4).index
    sales.loc[neg_idx, "units_sold"] = -1  # bad sentinel value

    return sales, inv


if __name__ == "__main__":
    sku_master = make_sku_master()
    calendar = make_calendar()
    sales, inv = make_sales_and_inventory(sku_master, calendar)

    sku_master.to_csv(RAW / "sku_master.csv", index=False)
    calendar.to_csv(RAW / "calendar.csv", index=False)
    sales.to_csv(RAW / "sales_daily.csv", index=False)
    inv.to_csv(RAW / "inventory_snapshots.csv", index=False)

    print(f"sku_master: {sku_master.shape}")
    print(f"calendar: {calendar.shape}")
    print(f"sales_daily: {sales.shape}")
    print(f"inventory_snapshots: {inv.shape}")
