# Swiss Inflation Forecast

An extensible OLS model for forecasting Swiss CPI inflation using macroeconomic indicators.

## Methodology

The model follows a reduced-form **Phillips Curve** approach:

$$\pi_t = \alpha + \beta_1 \pi_{t-1} + \beta_2 \Delta e_t + \beta_3 \Delta p_{\text{oil},t} + \varepsilon_t$$

Where:
- $\pi_t$ = Swiss CPI inflation (YoY, from BFS)
- $\pi_{t-1}$ = Lagged inflation (autoregressive term)
- $\Delta e_t$ = Change in EUR/CHF exchange rate
- $\Delta p_{\text{oil},t}$ = Log-change in Brent crude oil price

## Data Sources

| Variable | Source | Frequency |
|---|---|---|
| CPI (LIK) | [BFS](https://www.bfs.admin.ch) | Monthly |
| EUR/CHF | [SNB Data Portal](https://data.snb.ch) | Monthly |
| Brent Oil | [FRED](https://fred.stlouisfed.org) | Monthly |

## Project Structure

```
swiss-inflation-forecast/
├── data/
│   ├── raw/              # Raw downloaded data (not tracked in git)
│   └── processed/        # Merged, cleaned dataset
├── src/
│   ├── fetch_data.py     # Data download from BFS, SNB, FRED
│   ├── preprocess.py     # Cleaning, merging, feature engineering
│   ├── model.py          # OLS estimation
│   └── evaluate.py       # Metrics and plots
├── notebooks/
│   └── exploration.ipynb # EDA
├── results/figures/      # Output charts
├── config.yaml           # Add new variables here
├── .env.example          # API key template
└── requirements.txt
```

## Adding a New Variable

Open `config.yaml` and add an entry under `features`:

```yaml
features:
  - name: "my_new_variable"
    source: "fred"           # "fred", "snb", "bfs", or "derived"
    series_id: "SERIES_ID"   # API series identifier
    lag: 1                   # How many months to lag
    transform: "diff"        # "none", "diff", "log_diff"
    description: "..."
```

No other code changes needed.

## Setup

```bash
# 1. Clone and install
git clone https://github.com/YOUR_USERNAME/swiss-inflation-forecast.git
cd swiss-inflation-forecast
pip install -r requirements.txt

# 2. Set up API key
cp .env.example .env
# Edit .env and add your FRED API key

# 3. Run pipeline
python src/fetch_data.py
python src/preprocess.py
python src/model.py
python src/evaluate.py
```

## Results

*To be filled in after model estimation.*

## References

- Canetg, F. (2025). *Monetary Policy in a New Era*. University of Bern.
- Wooldridge, J. (2020). *Introductory Econometrics*. 7th ed.
- SNB (2024). *Monetary Policy Report*.
