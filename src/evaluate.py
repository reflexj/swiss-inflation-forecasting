"""
evaluate.py
-----------
Evaluates the OLS model on the test set and produces diagnostic plots.

Run:
    python src/evaluate.py

Output:
    results/figures/forecast_vs_actual.png
    results/figures/residuals.png
    results/figures/residuals_hist.png
    results/evaluation_metrics.csv
"""

import os
import yaml
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from sklearn.metrics import mean_absolute_error, mean_squared_error

# ── Paths ────────────────────────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS  = os.path.join(ROOT, "results")
FIGURES  = os.path.join(RESULTS, "figures")
os.makedirs(FIGURES, exist_ok=True)

with open(os.path.join(ROOT, "config.yaml"), "r") as f:
    CONFIG = yaml.safe_load(f)

# ── Plot style ────────────────────────────────────────────────────────────────
plt.rcParams.update({
    "figure.dpi": 150,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.3,
    "font.size": 10,
})
SNB_RED  = "#C8102E"
SNB_GREY = "#6B6B6B"


# ── 1. Load predictions ───────────────────────────────────────────────────────
def load_predictions() -> pd.DataFrame:
    path = os.path.join(RESULTS, "predictions.csv")
    df = pd.read_csv(path, parse_dates=["date"])
    df["residual"] = df["CPI_YoY"] - df["CPI_YoY_predicted"]
    return df


def load_full_dataset() -> pd.DataFrame:
    path = os.path.join(ROOT, "data", "processed", "dataset.csv")
    return pd.read_csv(path, parse_dates=["date"])


# ── 2. Metrics ────────────────────────────────────────────────────────────────
def compute_metrics(df: pd.DataFrame) -> dict:
    actual    = df["CPI_YoY"]
    predicted = df["CPI_YoY_predicted"]

    mae  = mean_absolute_error(actual, predicted)
    rmse = np.sqrt(mean_squared_error(actual, predicted))
    # Mean Absolute Percentage Error (skip near-zero actuals)
    mask = actual.abs() > 0.05
    mape = (((actual[mask] - predicted[mask]) / actual[mask]).abs().mean()) * 100

    metrics = {"MAE": round(mae, 4), "RMSE": round(rmse, 4), "MAPE": round(mape, 2)}

    print("\nOut-of-sample evaluation metrics:")
    print(f"  MAE:  {mae:.4f} pp   (mean absolute error in percentage points)")
    print(f"  RMSE: {rmse:.4f} pp   (penalises large errors more)")
    print(f"  MAPE: {mape:.2f}%     (relative error)")

    metrics_df = pd.DataFrame([metrics])
    metrics_df.to_csv(os.path.join(RESULTS, "evaluation_metrics.csv"), index=False)
    return metrics


# ── 3. Plot: Forecast vs Actual ───────────────────────────────────────────────
def plot_forecast(df_full: pd.DataFrame, df_test: pd.DataFrame) -> None:
    train_end  = pd.to_datetime(CONFIG["model"]["train_end"])
    test_start = pd.to_datetime(CONFIG["model"]["test_start"])

    fig, ax = plt.subplots(figsize=(12, 5))

    # Full actual series in grey
    ax.plot(df_full["date"], df_full["CPI_YoY"],
            color=SNB_GREY, linewidth=1.2, label="Actual CPI YoY", zorder=2)

    # Test period forecast in red
    ax.plot(df_test["date"], df_test["CPI_YoY_predicted"],
            color=SNB_RED, linewidth=1.8, linestyle="--",
            label="OLS Forecast (test period)", zorder=3)

    # Shade train/test regions
    ax.axvspan(df_full["date"].min(), train_end,
               alpha=0.04, color="steelblue", label="Training period")
    ax.axvspan(test_start, df_full["date"].max(),
               alpha=0.07, color=SNB_RED, label="Test period")

    # 0-line
    ax.axhline(0, color="black", linewidth=0.6, linestyle=":")

    ax.set_title("Swiss CPI Inflation: OLS Forecast vs Actual", fontsize=13, fontweight="bold")
    ax.set_ylabel("YoY Inflation (%)")
    ax.set_xlabel("")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.legend(loc="upper left", fontsize=9)

    plt.tight_layout()
    path = os.path.join(FIGURES, "forecast_vs_actual.png")
    plt.savefig(path)
    plt.close()
    print(f"Saved plot -> {path}")


# ── 4. Plot: Residuals over time ──────────────────────────────────────────────
def plot_residuals(df_test: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(10, 4))

    ax.bar(df_test["date"], df_test["residual"],
           color=[SNB_RED if r < 0 else "steelblue" for r in df_test["residual"]],
           width=25, alpha=0.8)
    ax.axhline(0, color="black", linewidth=0.8)

    ax.set_title("Forecast Residuals (Actual − Predicted)", fontsize=12, fontweight="bold")
    ax.set_ylabel("Residual (pp)")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.xticks(rotation=45, ha="right")

    plt.tight_layout()
    path = os.path.join(FIGURES, "residuals.png")
    plt.savefig(path)
    plt.close()
    print(f"Saved plot -> {path}")


# ── 5. Plot: Residuals histogram ──────────────────────────────────────────────
def plot_residuals_hist(df_test: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(6, 4))

    ax.hist(df_test["residual"], bins=20, color="steelblue",
            edgecolor="white", alpha=0.85)
    ax.axvline(0, color=SNB_RED, linewidth=1.5, linestyle="--")

    mean_res = df_test["residual"].mean()
    ax.axvline(mean_res, color=SNB_GREY, linewidth=1.2,
               linestyle="--", label=f"Mean residual: {mean_res:.3f}")

    ax.set_title("Distribution of Forecast Residuals", fontsize=12, fontweight="bold")
    ax.set_xlabel("Residual (pp)")
    ax.set_ylabel("Frequency")
    ax.legend(fontsize=9)

    plt.tight_layout()
    path = os.path.join(FIGURES, "residuals_hist.png")
    plt.savefig(path)
    plt.close()
    print(f"Saved plot -> {path}")


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    df_test = load_predictions()
    df_full = load_full_dataset()

    compute_metrics(df_test)
    plot_forecast(df_full, df_test)
    plot_residuals(df_test)
    plot_residuals_hist(df_test)

    print("\nEvaluation complete.")
    print("Check results/figures/ for plots.")