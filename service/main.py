"""
service/main.py — D6: Deployed scoring service.

Returns forecast + risk for a given SKU (or a batch). Run locally with:
    uvicorn service.main:app --reload --port 8000
Then: GET http://localhost:8000/score/SKU0001
      POST http://localhost:8000/score/batch  {"sku_ids": ["SKU0001","SKU0002"]}

Deploy (free tiers, per the brief's recommended toolset):
  - Render: connect the repo, set start command `uvicorn service.main:app
    --host 0.0.0.0 --port $PORT`, add requirements.txt.
  - Hugging Face Spaces (Docker SDK): same start command in a Dockerfile.
This code is deployment-ready; it does not ship with a live URL because
this environment has no outbound network access to host one - see README
"Deployment" section for the exact steps and what to paste into the
submission form once hosted.
"""
from pathlib import Path
from typing import List, Optional

import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"

app = FastAPI(
    title="FORESIGHT Scoring Service",
    description="Forecast + stockout/overstock risk for NorthBay Living SKUs.",
    version="1.0.0",
)

_risk_cache: Optional[pd.DataFrame] = None
_forecast_cache: Optional[pd.DataFrame] = None


def get_data():
    global _risk_cache, _forecast_cache
    if _risk_cache is None:
        risk_path = PROCESSED / "risk_scores.csv"
        fc_path = PROCESSED / "forecast.csv"
        if not risk_path.exists() or not fc_path.exists():
            raise HTTPException(
                status_code=503,
                detail="Scoring data not found. Run: python src/pipeline.py && "
                       "python src/forecast.py && python src/risk.py",
            )
        _risk_cache = pd.read_csv(risk_path)
        _forecast_cache = pd.read_csv(fc_path, parse_dates=["week_start"])
    return _risk_cache, _forecast_cache


class BatchRequest(BaseModel):
    sku_ids: List[str]


class SkuScore(BaseModel):
    sku_id: str
    category: Optional[str] = None
    forecast_next_8_weeks: List[dict]
    stockout_risk: Optional[float] = None
    overstock_risk: Optional[float] = None
    quadrant: Optional[str] = None
    recommended_action: Optional[str] = None
    value_at_stake: Optional[float] = None


def _score_one(sku_id: str, risk: pd.DataFrame, forecast: pd.DataFrame) -> SkuScore:
    sku_fc = forecast[forecast["sku_id"] == sku_id].sort_values("week_start")
    sku_risk_rows = risk[risk["sku_id"] == sku_id]

    if sku_fc.empty and sku_risk_rows.empty:
        raise HTTPException(status_code=404, detail=f"Unknown SKU '{sku_id}'.")

    fc_payload = [
        {"week_start": row["week_start"].strftime("%Y-%m-%d"),
         "forecast_units": round(float(row["units_sold"]), 1)}
        for _, row in sku_fc.iterrows()
    ]

    if sku_risk_rows.empty:
        return SkuScore(sku_id=sku_id, forecast_next_8_weeks=fc_payload)

    r = sku_risk_rows.iloc[0]
    return SkuScore(
        sku_id=sku_id,
        category=r.get("category"),
        forecast_next_8_weeks=fc_payload,
        stockout_risk=round(float(r["stockout_risk"]), 4),
        overstock_risk=round(float(r["overstock_risk"]), 4),
        quadrant=r["quadrant"],
        recommended_action=r["recommended_action"],
        value_at_stake=round(float(r["value_at_stake"]), 2),
    )


@app.get("/")
def root():
    return {"service": "FORESIGHT Scoring Service", "status": "ok",
            "docs": "/docs", "example": "/score/SKU0001"}


@app.get("/score/{sku_id}", response_model=SkuScore)
def score_sku(sku_id: str):
    risk, forecast = get_data()
    return _score_one(sku_id, risk, forecast)


@app.post("/score/batch", response_model=List[SkuScore])
def score_batch(req: BatchRequest):
    if not req.sku_ids:
        raise HTTPException(status_code=400, detail="sku_ids must not be empty.")
    risk, forecast = get_data()
    results = []
    for sku_id in req.sku_ids:
        try:
            results.append(_score_one(sku_id, risk, forecast))
        except HTTPException:
            results.append(SkuScore(sku_id=sku_id, forecast_next_8_weeks=[]))
    return results
