"""
preprocess.py
-------------
Merges raw data sources, builds features from config.yaml,
runs stationarity checks, and saves the final dataset.

Run:
    python src/preprocess.py

Output:
    data/processed/dataset.csv
"""

import os
import yaml
import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller

# ── Paths ────────────────────────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")
PROCESSED = os.path.join(ROOT, "data", "processed")
os.makedirs(PROCESSED, exist_ok=True)

with open(os.path.join(ROOT, "config.yaml"), "r") as f:
    CONFIG = yaml.safe_load(f)


# ── 1. Load raw CSVs ─────────────────────────────────────────────────────────
def load_raw() -> pd.DataFrame:
    """Load and merge all raw CSVs on date. Returns wide-format DataFrame."""
    print("Loading raw data...")

    cpi = pd.read_csv(os.path.join(RAW, "cpi_bfs.csv"), parse_dates=["date"])
    eur = pd.read_csv(os.path.join(RAW, "eurchf_snb.csv"), parse_dates=["date"])
    oil = pd.read_csv(os.path.join(RAW, "oil_fred.csv"), parse_dates=["date"])
    ipi = pd.read_csv(os.path.join(RAW, "import_price_bfs.csv"), parse_dates=["date"])

    # Merge on date (inner join = keep only months where all series exist)
    df = cpi.merge(eur, on="date", how="inner")
    df = df.merge(oil, on="date", how="inner")
    df = df.merge(ipi, on="date", how="inner")
    df = df.sort_values("date").reset_index(drop=True)

    print(f"  Merged dataset: {len(df)} rows, {df['date'].min().date()} to {df['date'].max().date()}")
    return df


# ── 2. Apply transformations ─────────────────────────────────────────────────
def apply_transform(series: pd.Series, transform: str) -> pd.Series:
    """Apply a named transformation to a series."""
    if transform == "none":
        return series
    elif transform == "diff":
        return series.diff()
    elif transform == "log_diff":
        return np.log(series).diff()
    else:
        raise ValueError(f"Unknown transform: '{transform}'. Use: none, diff, log_diff")


# ── 3. Build features from config.yaml ───────────────────────────────────────
def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Reads the features list from config.yaml and constructs each variable.
    Adding a new feature = adding an entry to config.yaml (no code changes needed).
    """
    print("Building features from config.yaml...")

    result = df[["date", "CPI_YoY"]].copy()  # target always included

    for feat in CONFIG["features"]:
        name = feat["name"]
        source = feat["source"]
        lag = feat.get("lag", 0)
        transform = feat.get("transform", "none")

        # ── Derived features (built from existing columns) ──
        if source == "derived":
            if name.startswith("CPI_lag"):
                base = apply_transform(df["CPI_YoY"], transform)
                result[name] = base.shift(lag)

            else:
                raise ValueError(f"Unknown derived feature: '{name}'")

        # ── EUR/CHF from SNB ──
        elif source == "snb":
            base = apply_transform(df["EUR_CHF"], transform)
            result[name] = base.shift(lag)

        # ── Oil price from FRED ──
        elif source == "fred":
            base = apply_transform(df["oil_price"], transform)
            result[name] = base.shift(lag)

        # ── BFS sub-indices (future extension) ──
        elif source == "bfs":
            col = feat.get("column", name)
            if col not in df.columns:
                raise ValueError(f"Column '{col}' not found in merged data.")
            base = apply_transform(df[col], transform)
            result[name] = base.shift(lag)

        # ── Import Price Index from BFS ──
        elif source == "bfs_ipi":
            base = apply_transform(df["import_price"], transform)
            result[name] = base.shift(lag)

        else:
            raise ValueError(f"Unknown source: '{source}'. Use: derived, snb, fred, bfs, bfs_ipi")

        print(f"  + {name:20s} (source={source}, lag={lag}, transform={transform})")

    # Drop rows with NaN (from lags/transforms at the start of the series)
    n_before = len(result)
    result = result.dropna().reset_index(drop=True)
    print(f"  Dropped {n_before - len(result)} rows due to NaN (lags/transforms)")
    print(f"  Final dataset: {len(result)} rows, {result['date'].min().date()} to {result['date'].max().date()}")
    return result


# ── 4. Stationarity checks ────────────────────────────────────────────────────
def check_stationarity(df: pd.DataFrame) -> None:
    """
    Runs ADF test on all numeric columns.
    Prints a warning if a series appears non-stationary (p > 0.05).
    Non-stationary series in OLS can produce spurious regression results.
    """
    print("\nStationarity checks (ADF test, H0: unit root present):")
    print(f"  {'Variable':<22} {'ADF stat':>10} {'p-value':>10} {'Stationary?':>12}")
    print("  " + "-" * 58)

    numeric_cols = [c for c in df.columns if c != "date"]
    warnings = []

    for col in numeric_cols:
        series = df[col].dropna()
        adf_stat, p_value, _, _, _, _ = adfuller(series, autolag="AIC")
        stationary = p_value < 0.05
        flag = "YES" if stationary else "NO  <-- WARNING"
        print(f"  {col:<22} {adf_stat:>10.3f} {p_value:>10.4f} {flag:>12}")
        if not stationary:
            warnings.append(col)

    if warnings:
        print(f"\n  WARNING: {warnings} may be non-stationary.")
        print("  Consider adding 'diff' or 'log_diff' transform in config.yaml.")
    else:
        print("\n  All series appear stationary. Good to proceed.")


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    df_raw = load_raw()
    df_features = build_features(df_raw)
    check_stationarity(df_features)

    path = os.path.join(PROCESSED, "dataset.csv")
    df_features.to_csv(path, index=False)
    print(f"\nSaved processed dataset -> {path}")
    print("Next step: python src/model.py")