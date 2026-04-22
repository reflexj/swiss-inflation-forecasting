"""
compare_models.py
-----------------
Compares multiple model specifications against each other and the naive benchmark.

Models tested:
  A: CPI_lag1 + EUR/CHF + oil_price          (baseline)
  B: CPI_lag1 + import_price                 (parsimonious)
  C: CPI_lag1 + oil_price + import_price     (no EUR/CHF)

Run:
    python src/compare_models.py
"""

import os
import yaml
import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.metrics import mean_absolute_error, mean_squared_error

ROOT      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED = os.path.join(ROOT, "data", "processed")
RESULTS   = os.path.join(ROOT, "results")

# ── Model definitions (inline, no separate config files needed) ──────────────
MODELS = {
    "A – Baseline (CPI_lag1 + EUR/CHF + Oil)": [
        "CPI_lag1", "EUR_CHF", "oil_price"
    ],
    "B – Parsimonious (CPI_lag1 + IPI)": [
        "CPI_lag1", "import_price"
    ],
    "C – No EUR/CHF (CPI_lag1 + Oil + IPI)": [
        "CPI_lag1", "oil_price", "import_price"
    ],
    "D – Minimal (CPI_lag1 + Oil)": [
        "CPI_lag1", "oil_price"
    ],
}

TRAIN_END  = "2022-12-01"
TEST_START = "2023-01-01"
TARGET     = "CPI_YoY"


def run_model(label: str, feature_names: list, df: pd.DataFrame) -> dict:
    # Drop rows where ANY of the required columns is NaN
    cols_needed = [TARGET] + feature_names
    df_clean = df.dropna(subset=cols_needed).copy()

    train = df_clean[df_clean["date"] <= TRAIN_END]
    test  = df_clean[df_clean["date"] >= TEST_START]

    if len(train) < 50 or len(test) < 10:
        return {"error": f"Not enough data (train={len(train)}, test={len(test)})"}

    # Fit OLS on train
    y_train = train[TARGET]
    X_train = sm.add_constant(train[feature_names])
    model   = sm.OLS(y_train, X_train).fit(cov_type="HC3")

    # Predict on test
    X_test = sm.add_constant(test[feature_names], has_constant="add")
    y_pred = model.predict(X_test)
    y_true = test[TARGET].values

    mae  = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))

    # ── Naive benchmark on EXACT SAME test rows ──────────────────────────────
    # For each test row, find the previous row in df_clean and use its CPI_YoY
    test_dates   = test["date"].values
    naive_preds  = []
    naive_trues  = []

    for i, row in test.iterrows():
        prev = df_clean[df_clean["date"] < row["date"]]
        if len(prev) == 0:
            continue
        naive_preds.append(prev[TARGET].iloc[-1])
        naive_trues.append(row[TARGET])

    naive_rmse = np.sqrt(mean_squared_error(naive_trues, naive_preds))
    theils_u2  = rmse / naive_rmse

    # Multicollinearity check
    corr_oil_ipi = None
    if "oil_price" in feature_names and "import_price" in feature_names:
        corr_oil_ipi = round(train["oil_price"].corr(train["import_price"]), 3)

    return {
        "r2":           round(model.rsquared, 4),
        "adj_r2":       round(model.rsquared_adj, 4),
        "f_stat":       round(model.fvalue, 1),
        "f_pvalue":     round(model.f_pvalue, 6),
        "mae":          round(mae, 4),
        "rmse":         round(rmse, 4),
        "naive_rmse":   round(naive_rmse, 4),
        "theils_u2":    round(theils_u2, 4),
        "beats_naive":  round((1 - theils_u2) * 100, 1),
        "n_train":      int(model.nobs),
        "n_test":       len(test),
        "coefs":        pd.DataFrame({
                            "coef":    model.params.round(4),
                            "p_value": model.pvalues.round(4),
                        }),
        "corr_oil_ipi": corr_oil_ipi,
    }


if __name__ == "__main__":
    # Load full dataset once
    df = pd.read_csv(
        os.path.join(PROCESSED, "dataset.csv"), parse_dates=["date"]
    )

    print("=" * 70)
    print("MODEL COMPARISON — Swiss CPI Inflation Forecasting")
    print(f"Train: up to {TRAIN_END}  |  Test: {TEST_START} onwards")
    print("=" * 70)

    results = {}
    for label, features in MODELS.items():
        # Check features exist in dataset
        missing = [f for f in features if f not in df.columns]
        if missing:
            print(f"\n  SKIP {label}: missing columns {missing}")
            continue

        print(f"\n{'─'*70}")
        print(f"Model {label}")
        print(f"{'─'*70}")
        r = run_model(label, features, df)

        if "error" in r:
            print(f"  ERROR: {r['error']}")
            continue

        results[label] = r
        print(f"  Train obs: {r['n_train']}  |  Test obs: {r['n_test']}")
        print(f"  R²={r['r2']}  Adj.R²={r['adj_r2']}  F={r['f_stat']} (p={r['f_pvalue']})")
        print(f"  RMSE={r['rmse']}  MAE={r['mae']}")
        print(f"  Naive RMSE={r['naive_rmse']}  Theil's U2={r['theils_u2']}  "
              f"({'beats' if r['beats_naive'] > 0 else 'loses to'} naive by {abs(r['beats_naive'])}%)")
        if r["corr_oil_ipi"] is not None:
            print(f"  Corr(oil_price, import_price) = {r['corr_oil_ipi']}")
        print(f"\n  Coefficients:")
        print(r["coefs"].to_string())

    # ── Summary table ─────────────────────────────────────────────────────────
    print(f"\n\n{'='*70}")
    print("SUMMARY TABLE")
    print(f"{'='*70}")
    summary = pd.DataFrame({
        label: {
            "R²":          r["r2"],
            "Adj. R²":     r["adj_r2"],
            "F-stat":      r["f_stat"],
            "RMSE (OOS)":  r["rmse"],
            "MAE (OOS)":   r["mae"],
            "Naive RMSE":  r["naive_rmse"],
            "Theil's U2":  r["theils_u2"],
            "Beats naive": f"{r['beats_naive']}%",
        }
        for label, r in results.items()
    }).T
    print(summary.to_string())

    path = os.path.join(RESULTS, "model_comparison.csv")
    summary.to_csv(path)
    print(f"\nSaved -> {path}")