# Stock Forecast Dashboard

A read-only web dashboard that publishes daily market snapshots and forecasts (with a focus on startup tickers) using GitHub Pages. Data is refreshed by a scheduled GitHub Action that runs the forecasting pipeline and pushes JSON artifacts for the front end to consume.

## Project Structure

```
stock-forecast-dashboard/
├── data/                  # Generated JSON/CSV snapshots served by the dashboard
├── scripts/               # Python tools for ingest, forecasting, scoring
├── frontend/              # Static dashboard (HTML/JS/CSS) deployed via Pages
├── .github/workflows/     # Automation (data refresh, lint, deploy)
└── README.md
```

## Goals

- **Daily pipeline** pulls price history, computes indicators, runs a simple Prophet-based forecast, and ranks startups by momentum / sentiment.
- **Static dashboard** lets anyone enter a ticker symbol and view the latest snapshot + forecast (read-only, no auth).
- **Suggestions** surface interesting early-stage companies (e.g., low market cap, high growth rate) and annotate them with qualitative signals.

## Getting Started

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the data pipeline locally:
   ```bash
   python scripts/fetch_and_forecast.py --tickers AAPL MSFT
   ```

3. Start a local server for the dashboard:
   ```bash
   cd frontend
   npm install # (optional if you add a build system)
   npm run dev
   ```

4. Configure GitHub Actions secrets (if any paid APIs are used) and enable Pages for the `frontend` build output (or the repo root for a static site).

## Roadmap

- [ ] Implement `scripts/fetch_and_forecast.py` using `yfinance` + Prophet
- [ ] Generate `data/summary.json` with per-ticker stats + forecasts
- [ ] Build dashboard UI (search box, sparkline, forecast chart, recommendations)
- [ ] Add GitHub Action (`daily-update.yml`) to run every morning UTC and commit new data
- [ ] Add GitHub Pages deploy workflow for the frontend

## Disclaimer

This project is for educational purposes only. Forecasts are experimental and **not** financial advice.

## Deployment

This repo is wired for a fully automated, read-only dashboard:

- `Deploy Dashboard` workflow packages `frontend/` plus `data/` and publishes it to GitHub Pages whenever you push changes.
- `Refresh Forecast Data` workflow runs daily at 07:00 UTC (and on-demand) to pull prices, rebuild forecasts, and commit the refreshed `data/summary.json` back to `main`.

Once the repo is on GitHub with Pages enabled, you’ll have a live URL where you can type any tracked ticker and immediately see the latest snapshot + 7‑day outlook.

## Local Preview

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/fetch_and_forecast.py  # refresh data locally
python -m http.server 8080           # then open frontend/index.html
```

(While serving locally, the dashboard will pull `data/summary.json` directly from your working tree.)
