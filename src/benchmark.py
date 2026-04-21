"""
benchmark.py
------------
Compares the OLS model against a naive benchmark:
    Naive: pi(t) = pi(t-1)   [this month = last month]

Metrics: MAE, RMSE, Theil's U2
    U2 < 1 → OLS beats the benchmark
    U2 = 1 → no difference
    U2 > 1 → benchmark is better

Run:
    python src/benchmark.py
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# ── Paths ────────────────────────────────────────────────────────────────────
ROOT    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
FIGURES = os.path.join(RESULTS, "figures")
os.makedirs(FIGURES, exist_ok=True)

plt.rcParams.update({
    "figure.dpi": 150,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.3,
})
SNB_RED  = "#C8102E"
SNB_BLUE = "steelblue"
SNB_GREY = "#6B6B6B"


# ── 1. Load predictions ───────────────────────────────────────────────────────
def load_data():
    # OLS predictions (already computed by model.py)
    pred_path = os.path.join(RESULTS, "predictions.csv")
    df = pd.read_csv(pred_path, parse_dates=["date"])

    # Naive benchmark: predicted = previous month's actual
    # We need the full dataset to get the lag
    full_path = os.path.join(ROOT, "data", "processed", "dataset.csv")
    df_full   = pd.read_csv(full_path, parse_dates=["date"])

    # Merge lagged actual into test set
    df_full["naive_forecast"] = df_full["CPI_YoY"].shift(1)
    df = df.merge(df_full[["date", "naive_forecast"]], on="date", how="left")

    return df


# ── 2. Compute metrics ────────────────────────────────────────────────────────
def compute_metrics(df: pd.DataFrame) -> pd.DataFrame:
    actual  = df["CPI_YoY"]
    ols     = df["CPI_YoY_predicted"]
    naive   = df["naive_forecast"]

    def mae(a, b):  return (a - b).abs().mean()
    def rmse(a, b): return np.sqrt(((a - b) ** 2).mean())

    mae_ols   = mae(actual, ols)
    mae_naive = mae(actual, naive)
    rmse_ols  = rmse(actual, ols)
    rmse_naive= rmse(actual, naive)
    theils_u2 = rmse_ols / rmse_naive

    print("\n" + "=" * 52)
    print(f"  {'Metric':<18} {'OLS':>10} {'Naive':>10}")
    print("  " + "-" * 40)
    print(f"  {'MAE':<18} {mae_ols:>10.4f} {mae_naive:>10.4f}")
    print(f"  {'RMSE':<18} {rmse_ols:>10.4f} {rmse_naive:>10.4f}")
    print("  " + "-" * 40)
    print(f"  Theil's U2:        {theils_u2:.4f}")
    if theils_u2 < 1:
        improvement = (1 - theils_u2) * 100
        print(f"  → OLS beats naive by {improvement:.1f}% (RMSE)")
    elif theils_u2 > 1:
        print(f"  → Naive beats OLS — consider revising the model")
    else:
        print(f"  → Models are equivalent")
    print("=" * 52)

    results = pd.DataFrame([{
        "MAE_OLS":    round(mae_ols, 4),
        "MAE_Naive":  round(mae_naive, 4),
        "RMSE_OLS":   round(rmse_ols, 4),
        "RMSE_Naive": round(rmse_naive, 4),
        "Theils_U2":  round(theils_u2, 4),
    }])
    results.to_csv(os.path.join(RESULTS, "benchmark_comparison.csv"), index=False)
    return results


# ── 3. Plot ───────────────────────────────────────────────────────────────────
def plot_comparison(df: pd.DataFrame) -> None:
    fig, axes = plt.subplots(2, 1, figsize=(12, 8))

    # ── Top: Forecast lines ──
    ax = axes[0]
    ax.plot(df["date"], df["CPI_YoY"],
            color=SNB_GREY, linewidth=1.5, label="Actual", zorder=3)
    ax.plot(df["date"], df["CPI_YoY_predicted"],
            color=SNB_RED, linewidth=1.5, linestyle="--", label="OLS Model", zorder=2)
    ax.plot(df["date"], df["naive_forecast"],
            color=SNB_BLUE, linewidth=1.5, linestyle=":", label="Naive Benchmark", zorder=2)
    ax.axhline(0, color="black", linewidth=0.6, linestyle=":")
    ax.set_title("OLS vs Naive Benchmark: Forecast Comparison", fontsize=12, fontweight="bold")
    ax.set_ylabel("YoY Inflation (%)")
    ax.legend(fontsize=9)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha="right")

    # ── Bottom: Absolute errors ──
    ax2 = axes[1]
    ols_err   = (df["CPI_YoY"] - df["CPI_YoY_predicted"]).abs()
    naive_err = (df["CPI_YoY"] - df["naive_forecast"]).abs()

    ax2.plot(df["date"], ols_err,
             color=SNB_RED, linewidth=1.2, label=f"OLS |error|")
    ax2.plot(df["date"], naive_err,
             color=SNB_BLUE, linewidth=1.2, linestyle=":", label=f"Naive |error|")
    ax2.fill_between(df["date"], ols_err, naive_err,
                     where=(ols_err < naive_err), alpha=0.15, color=SNB_RED,
                     label="OLS better")
    ax2.fill_between(df["date"], ols_err, naive_err,
                     where=(ols_err >= naive_err), alpha=0.15, color=SNB_BLUE,
                     label="Naive better")
    ax2.set_title("Absolute Forecast Error by Month", fontsize=12, fontweight="bold")
    ax2.set_ylabel("Absolute Error (pp)")
    ax2.legend(fontsize=9)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha="right")

    plt.tight_layout()
    path = os.path.join(FIGURES, "benchmark_comparison.png")
    plt.savefig(path)
    plt.close()
    print(f"\nSaved plot -> {path}")


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    df = load_data()
    compute_metrics(df)
    plot_comparison(df)