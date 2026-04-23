# Model Results & Comparison

This document compares four model specifications against a naive benchmark.
All out-of-sample evaluation is on the test period **January 2023 – March 2026** (39 observations).
The naive benchmark predicts $\pi_t = \pi_{t-1}$ (this month's inflation = last month's).

---

## Model Specifications

| Model | Variables | Rationale |
|-------|-----------|-----------|
| **A – Baseline** | CPI lag 1 + EUR/CHF + Oil | Original specification |
| **B – Parsimonious** | CPI lag 1 + IPI | Replace oil with import prices |
| **C – No EUR/CHF** | CPI lag 1 + Oil + IPI | Test IPI alongside oil |
| **D – Minimal** | CPI lag 1 + Oil | Drop EUR/CHF entirely |

All models estimated with OLS and heteroskedasticity-robust standard errors (HC3).
Train period: June 1999 – December 2022 (283 observations).

---

## Coefficient Estimates

| Variable | A | B | C | D |
|----------|---|---|---|---|
| Intercept | 0.027 | 0.036** | 0.037** | 0.025 |
| CPI lag 1 | 0.966*** | 0.947*** | 0.946*** | 0.964*** |
| EUR/CHF Δ (lag 1) | 1.146 | — | — | — |
| Oil log-diff (lag 2) | 0.378** | — | -0.065 | 0.395** |
| Import Price log-diff (lag 1) | — | 10.481*** | 11.014*** | — |

*\*\*\* p<0.01, \*\* p<0.05. HC3 robust standard errors.*

**Key observations:**
- Once the IPI enters (Models B, C), oil becomes insignificant (p=0.71 in C) — consistent with moderate collinearity between the two (r=0.589).
- EUR/CHF is never individually significant, but its removal worsens out-of-sample performance (A vs D).
- The IPI is strongly significant in-sample but does not improve out-of-sample accuracy.

---

## In-Sample Fit (Training Period 1999–2022)

| Metric | A | B | C | D |
|--------|---|---|---|---|
| R² | 0.9223 | **0.9264** | **0.9264** | 0.9219 |
| Adj. R² | 0.9214 | **0.9258** | 0.9256 | 0.9213 |
| F-statistic | 1216.8 | **1812.5** | 1198.3 | 1714.3 |

Models B and C achieve higher R² in-sample due to the IPI's strong explanatory power. Model B has the highest F-statistic, reflecting the most efficient use of degrees of freedom.

---

## Out-of-Sample Performance (Test Period 2023–2026)

| Metric | A | B | C | D | Naive |
|--------|---|---|---|---|-------|
| RMSE (pp) | **0.2056** | 0.2119 | 0.2126 | 0.2084 | 0.2177 |
| MAE (pp) | 0.1648 | **0.1615** | **0.1618** | 0.1663 | 0.1725 |
| Theil's U2 | **0.9444** | 0.9730 | 0.9765 | 0.9569 | 1.000 |
| Beats naive by | **5.6%** | 2.7% | 2.3% | 4.3% | — |

All four models outperform the naive benchmark. **Model A achieves the best RMSE and Theil's U2**, despite EUR/CHF being individually insignificant. This illustrates a key principle: statistical significance in-sample does not equal out-of-sample relevance.

The IPI improves in-sample fit (higher R²) but reduces out-of-sample accuracy — a textbook bias-variance tradeoff. The IPI likely overfits to historical patterns that do not persist in the test period.

---

## Latest Forecast: April 2026

| Model | Forecast | 95% CI |
|-------|----------|--------|
| A – Baseline | **+0.155%** | [-0.381%, +0.691%] |

The preferred model (A) forecasts Swiss CPI YoY inflation at +0.155% for April 2026, well within the SNB's 0–2% target band.

---

## Conclusion

**Model A (CPI lag 1 + EUR/CHF + Oil) is the preferred specification** based on out-of-sample RMSE and Theil's U2.

Key findings:
- EUR/CHF, although statistically insignificant, contributes to forecast accuracy (A beats D by 1.3pp in Theil's U2)
- The IPI captures import price dynamics but introduces overfitting over the 2023–2026 test period
- Oil and IPI carry overlapping information (r=0.589); including both renders oil redundant
- All models beat the naive benchmark, validating the OLS approach over a simple AR(1)

A natural extension would be a **regime-dependent model** that activates the IPI only during high-inflation periods.