"""Runs the full FORESIGHT pipeline end-to-end from raw data to risk scores.

    python src/run_all.py

Runs generate_data.py (only if data/raw is empty), then pipeline.py,
forecast.py, and risk.py in order. Each module is also runnable standalone.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"

if __name__ == "__main__":
    steps = ["generate_data.py", "pipeline.py", "forecast.py", "risk.py"]
    for step in steps:
        if step == "generate_data.py" and (RAW / "sales_daily.csv").exists():
            print(f"== Skipping {step} (raw data already present) ==")
            continue
        print(f"\n== Running {step} ==")
        result = subprocess.run([sys.executable, f"src/{step}"], cwd=ROOT)
        if result.returncode != 0:
            print(f"Step {step} failed - stopping.")
            sys.exit(result.returncode)

    print("\nAll done. Optional charts: python reports/make_eda_charts.py")
    print("Dashboard: streamlit run app/dashboard.py")
    print("Scoring service: uvicorn service.main:app --reload --port 8000")
