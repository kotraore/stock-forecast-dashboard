#!/usr/bin/env python3
"""Fetch market data, run simple forecasts, and emit JSON for the dashboard."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd
import yfinance as yf
from prophet import Prophet

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DEFAULT_TICKERS = [
    "AAPL",
    "MSFT",
    "GOOGL",
    "AMZN",
    "META",
    "TSLA",
    "SNOW",
    "COIN",
    "NET",
    "MDB",
    "BTG",
    "BTO.TO",
    "GC=F",   # Gold futures
    "SI=F",   # Silver futures
    "HG=F",   # Copper futures
    "LIT",    # Lithium ETF proxy
]


def fetch_history(ticker: str, period: str = "6mo") -> pd.DataFrame:
    df = yf.download(ticker, period=period, interval="1d", auto_adjust=True, progress=False)
    if df.empty:
        raise ValueError(f"No data returned for {ticker}")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.reset_index(inplace=True)
    df.rename(columns={"Date": "ds", "Close": "y"}, inplace=True)
    return df[["ds", "y"]]


def forecast(df: pd.DataFrame, horizon_days: int = 7) -> Prophet:
    model = Prophet(daily_seasonality=False, weekly_seasonality=True, yearly_seasonality=True)
    model.fit(df)
    future = model.make_future_dataframe(periods=horizon_days)
    forecast_df = model.predict(future)
    return forecast_df


def compute_insights(ticker: str, hist: pd.DataFrame, fc: pd.DataFrame, horizon_days: int) -> dict:
    latest_price = hist["y"].iloc[-1]
    future_block = fc.tail(horizon_days)
    predicted = future_block["yhat"].tolist()
    next_day_price = predicted[0] if predicted else latest_price
    next_day_pct = (next_day_price - latest_price) / latest_price if latest_price else 0.0
    pct_change = (predicted[-1] - latest_price) / latest_price if latest_price else 0.0

    recent = hist["y"].tail(5)
    momentum = (recent.iloc[-1] - recent.iloc[0]) / recent.iloc[0]
    risk = float(hist["y"].pct_change().std()) * math.sqrt(252)

    signal = "watch"
    if pct_change > 0.05 and momentum > 0:
        signal = "bullish"
    elif pct_change < -0.05 and momentum < 0:
        signal = "bearish"

    return {
        "ticker": ticker,
        "latest_price": round(float(latest_price), 2),
        "forecast": [round(float(x), 2) for x in predicted],
        "next_day_price": round(float(next_day_price), 2),
        "next_day_pct": round(float(next_day_pct) * 100, 2),
        "pct_change_7d": round(float(pct_change) * 100, 2),
        "momentum_5d": round(float(momentum) * 100, 2),
        "annualized_vol": round(risk * 100, 2),
        "signal": signal,
    }


def main(tickers: List[str], days: int) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    snapshots: List[dict] = []
    for ticker in tickers:
        try:
            hist = fetch_history(ticker)
            fc = forecast(hist, horizon_days=days)
            info = compute_insights(ticker, hist, fc, horizon_days=days)
            history_block = hist.tail(60).copy()
            history_block["ds"] = history_block["ds"].dt.strftime("%Y-%m-%d")
            info["history"] = history_block.to_dict(orient="records")
            info["forecast_dates"] = fc.tail(days)["ds"].dt.strftime("%Y-%m-%d").tolist()
            snapshots.append(info)
            print(f"✔ {ticker}: latest {info['latest_price']} → {info['forecast'][-1]} ({info['pct_change_7d']}%)")
        except Exception as exc:  # noqa: BLE001
            print(f"✖ {ticker}: {exc}")

    payload = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "tickers": tickers,
        "snapshots": snapshots,
    }
    out_file = DATA_DIR / "summary.json"
    out_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"\nWrote {out_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch stock data and create forecast JSON")
    parser.add_argument("--tickers", nargs="*", default=DEFAULT_TICKERS, help="Ticker symbols")
    parser.add_argument("--days", type=int, default=7, help="Forecast horizon")
    args = parser.parse_args()
    main(args.tickers, args.days)
