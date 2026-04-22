# Model Results & Comparison

This document compares two model specifications against a naive benchmark.
All out-of-sample evaluation is on the test period **January 2023 – March 2026** (39 observations).

---

## Model Specifications

**Baseline Model (3 variables)**

$$\pi_t = \alpha + \beta_1 \pi_{t-1} + \beta_2 \Delta e_t + \beta_3 \Delta \ln p_{\text{oil},t} + \varepsilon_t$$

**Extended Model (4 variables)**

$$\pi_t = \alpha + \beta_1 \pi_{t-1} + \beta_2 \Delta e_t + \beta_3 \Delta \ln p_{\text{oil},t} + \beta_4 \Delta \ln \text{IPI}_t + \varepsilon_t$$

**Naive Benchmark**

$$\pi_t = \pi_{t-1}$$

---

## Coefficient Estimates

| Variable | Baseline | Extended | Significant? |
|---|---|---|---|
| Intercept | 0.027 | 0.037 | ✅ (extended only) |
| CPI lag 1 | 0.966*** | 0.947*** | ✅ both |
| EUR/CHF Δ (lag 1) | 1.146 | 0.420 | ❌ neither |
| Oil price Δ log (lag 2) | 0.378** | -0.062 | ✅ baseline only |
| Import Price Δ log (lag 1) | — | 10.809*** | ✅ extended only |

*Heteroskedasticity-robust standard errors (HC3). \*\*\* p<0.01, \*\* p<0.05*

**Notable finding:** Adding the Import Price Index (IPI) renders the oil price coefficient insignificant (p=0.72). This suggests the two variables capture overlapping information — import prices already absorb energy price movements, making the oil price redundant once the IPI is included.

---

## In-Sample Fit (Training Period 1999–2022)

| Metric | Baseline | Extended |
|---|---|---|
| R² | 0.9223 | 0.9264 |
| Adj. R² | 0.9214 | 0.9254 |
| F-statistic | 1216.81 | 916.59 |
| Observations | 283 | 283 |

The extended model improves R² marginally (+0.004). However, the F-statistic drops as adding a variable without sufficient improvement penalises the overall fit.

---

## Out-of-Sample Performance (Test Period 2023–2026)

| Metric | Baseline | Extended | Naive Benchmark |
|---|---|---|---|
| MAE (pp) | 0.1648 | **0.1615** | 0.1725 |
| RMSE (pp) | **0.2056** | 0.2114 | 0.2177 |
| Theil's U2 | **0.944** | 0.971 | 1.000 |
| Beats naive by | **5.6%** | 2.9% | — |

Both models outperform the naive benchmark. However, the **baseline model performs better out-of-sample** despite the extended model's superior in-sample fit. This is a classic bias-variance tradeoff: the IPI adds explanatory power in-sample but reduces generalisability out-of-sample.

---

## Latest Forecast: April 2026

| Model | Forecast | 95% CI |
|---|---|---|
| Baseline | +0.155% | [-0.381%, +0.691%] |
| Extended | +0.168% | [-0.355%, +0.692%] |

Both models predict Swiss CPI YoY inflation close to zero for April 2026, well within the SNB's 0–2% target band. The small difference between models (0.013 pp) reflects the minor role of the IPI in a low-inflation environment.

---

## Conclusion

The baseline 3-variable model is preferred for forecasting based on out-of-sample performance. The IPI is statistically significant in-sample and economically meaningful — it captures import price pressures before they feed into consumer prices — but its inclusion does not improve out-of-sample accuracy over the test period.

A natural next step would be to test the IPI's contribution specifically during volatile periods (e.g. 2022–2023) using a **Diebold-Mariano test** or a **regime-dependent model** that activates the IPI only when inflation volatility exceeds a threshold.