"""
forecast.py
-----------
Uses the fitted OLS model to forecast CPI inflation one month ahead,
using the most recent available data.

Run:
    python src/forecast.py

Output:
    Prints the forecast to the console
    Saves to results/next_month_forecast.csv
"""

import os
import yaml
import numpy as np
import pandas as pd
import statsmodels.api as sm

# ── Paths ────────────────────────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED = os.path.join(ROOT, "data", "processed")
RESULTS   = os.path.join(ROOT, "results")

with open(os.path.join(ROOT, "config.yaml"), "r") as f:
    CONFIG = yaml.safe_load(f)


# ── 1. Re-fit model on ALL available data ────────────────────────────────────
def fit_full_model(df: pd.DataFrame):
    """
    For forecasting, we train on ALL data (not just up to train_end).
    More data = better coefficient estimates.
    """
    target       = CONFIG["target"]["name"]
    feature_names = [f["name"] for f in CONFIG["features"]]

    y = df[target]
    X = sm.add_constant(df[feature_names])

    model = sm.OLS(y, X).fit(cov_type="HC3")
    return model, feature_names


# ── 2. Build the forecast row ─────────────────────────────────────────────────
def build_forecast_row(df: pd.DataFrame) -> pd.Series:
    """
    Constructs the feature vector for the next month forecast
    using the most recent available observations.
    """
    feature_names = [f["name"] for f in CONFIG["features"]]
    row = {}

    for feat in CONFIG["features"]:
        name      = feat["name"]
        source    = feat["source"]
        lag       = feat.get("lag", 0)
        transform = feat.get("transform", "none")

        # The most recent row already has lags applied from preprocess.py
        # We just need the latest value of each feature
        row[name] = df[name].iloc[-1]

    return pd.Series(row)


# ── 3. Make forecast ──────────────────────────────────────────────────────────
def make_forecast():
    # Load processed dataset
    df = pd.read_csv(os.path.join(PROCESSED, "dataset.csv"), parse_dates=["date"])

    last_date     = df["date"].iloc[-1]
    forecast_date = last_date + pd.DateOffset(months=1)

    print(f"Last data point:  {last_date.strftime('%B %Y')}")
    print(f"Forecasting:      {forecast_date.strftime('%B %Y')}")
    print()

    # Fit on all data
    model, feature_names = fit_full_model(df)

    # Build feature vector from most recent row
    forecast_row = build_forecast_row(df)
    X_new = sm.add_constant(
        pd.DataFrame([forecast_row[feature_names]]),
        has_constant="add"
    )

    # Point forecast
    forecast_value = model.predict(X_new)[0]

    # Prediction interval (in-sample RMSE as uncertainty estimate)
    residuals = model.resid
    rmse = np.sqrt((residuals ** 2).mean())
    ci_lower = forecast_value - 1.96 * rmse
    ci_upper = forecast_value + 1.96 * rmse

    # ── Print results ──────────────────────────────────────────────────────
    print("=" * 50)
    print(f"  Forecast for {forecast_date.strftime('%B %Y')}")
    print("=" * 50)
    print(f"  CPI YoY (predicted):  {forecast_value:+.3f}%")
    print(f"  95% interval:         [{ci_lower:+.3f}%, {ci_upper:+.3f}%]")
    print()
    print("  Input values used:")
    for name, val in forecast_row[feature_names].items():
        print(f"    {name:<20} {val:.4f}")
    print()

    # Last known actual for context
    last_actual = df["CPI_YoY"].iloc[-1]
    change = forecast_value - last_actual
    direction = "▲" if change > 0 else "▼"
    print(f"  Last known CPI YoY ({last_date.strftime('%b %Y')}): {last_actual:+.3f}%")
    print(f"  Predicted change:    {direction} {abs(change):.3f} pp")
    print("=" * 50)

    # ── Save ──────────────────────────────────────────────────────────────
    result = pd.DataFrame([{
        "forecast_date":    forecast_date.strftime("%Y-%m-%d"),
        "CPI_YoY_forecast": round(forecast_value, 4),
        "ci_lower_95":      round(ci_lower, 4),
        "ci_upper_95":      round(ci_upper, 4),
        "last_known_date":  last_date.strftime("%Y-%m-%d"),
        "last_known_CPI":   round(last_actual, 4),
    }])

    path = os.path.join(RESULTS, "next_month_forecast.csv")
    result.to_csv(path, index=False)
    print(f"\nSaved forecast -> {path}")

    return forecast_value


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    make_forecast()