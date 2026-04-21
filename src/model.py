"""
model.py
--------
Estimates an OLS model for Swiss CPI inflation using the processed dataset.
Train/test split is defined in config.yaml.

Run:
    python src/model.py

Output:
    results/model_summary.txt
    results/coefficients.csv
"""

import os
import yaml
import pandas as pd
import statsmodels.api as sm

# ── Paths ────────────────────────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED = os.path.join(ROOT, "data", "processed")
RESULTS = os.path.join(ROOT, "results")
os.makedirs(RESULTS, exist_ok=True)

with open(os.path.join(ROOT, "config.yaml"), "r") as f:
    CONFIG = yaml.safe_load(f)


# ── 1. Load processed dataset ────────────────────────────────────────────────
def load_data() -> pd.DataFrame:
    path = os.path.join(PROCESSED, "dataset.csv")
    df = pd.read_csv(path, parse_dates=["date"])
    return df


# ── 2. Train/test split ──────────────────────────────────────────────────────
def split(df: pd.DataFrame):
    train_end = pd.to_datetime(CONFIG["model"]["train_end"])
    test_start = pd.to_datetime(CONFIG["model"]["test_start"])

    train = df[df["date"] <= train_end].copy()
    test  = df[df["date"] >= test_start].copy()

    print(f"  Train: {train['date'].min().date()} to {train['date'].max().date()} ({len(train)} obs)")
    print(f"  Test:  {test['date'].min().date()} to {test['date'].max().date()} ({len(test)} obs)")
    return train, test


# ── 3. Fit OLS ───────────────────────────────────────────────────────────────
def fit_ols(train: pd.DataFrame):
    """
    Fits OLS with statsmodels.
    Target:   CPI_YoY
    Features: all other columns except 'date', plus a constant (intercept)
    """
    target = CONFIG["target"]["name"]
    feature_names = [f["name"] for f in CONFIG["features"]]

    y = train[target]
    X = sm.add_constant(train[feature_names])   # adds intercept column 'const'

    model = sm.OLS(y, X).fit(
        cov_type="HC3"   # heteroskedasticity-robust standard errors
    )
    return model, feature_names


# ── 4. Print & save results ──────────────────────────────────────────────────
def save_results(model, feature_names: list) -> None:
    summary_str = model.summary().as_text()

    # Print to console
    print("\n" + "=" * 65)
    print(summary_str)
    print("=" * 65)

    # Save full summary
    summary_path = os.path.join(RESULTS, "model_summary.txt")
    with open(summary_path, "w") as f:
        f.write(summary_str)
    print(f"\nSaved summary -> {summary_path}")

    # Save coefficients as CSV (useful for later analysis)
    coef_df = pd.DataFrame({
        "variable":  ["const"] + feature_names,
        "coef":      model.params.values,
        "std_err":   model.bse.values,
        "t_stat":    model.tvalues.values,
        "p_value":   model.pvalues.values,
        "ci_lower":  model.conf_int()[0].values,
        "ci_upper":  model.conf_int()[1].values,
    })
    coef_path = os.path.join(RESULTS, "coefficients.csv")
    coef_df.to_csv(coef_path, index=False)
    print(f"Saved coefficients -> {coef_path}")


# ── 5. Predict on test set ───────────────────────────────────────────────────
def predict(model, test: pd.DataFrame) -> pd.DataFrame:
    feature_names = [f["name"] for f in CONFIG["features"]]
    X_test = sm.add_constant(test[feature_names], has_constant="add")

    predictions = model.predict(X_test)
    result = test[["date", "CPI_YoY"]].copy()
    result["CPI_YoY_predicted"] = predictions.values

    pred_path = os.path.join(RESULTS, "predictions.csv")
    result.to_csv(pred_path, index=False)
    print(f"Saved predictions -> {pred_path}")
    return result


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Loading data...")
    df = load_data()

    print("Splitting train/test...")
    train, test = split(df)

    print("Fitting OLS model...")
    model, feature_names = fit_ols(train)

    save_results(model, feature_names)
    predictions = predict(model, test)

    print("\nKey metrics on training data:")
    print(f"  R-squared:      {model.rsquared:.4f}")
    print(f"  Adj. R-squared: {model.rsquared_adj:.4f}")
    print(f"  F-statistic:    {model.fvalue:.2f} (p={model.f_pvalue:.4f})")
    print(f"  Observations:   {int(model.nobs)}")

    print("\nNext step: python src/evaluate.py")