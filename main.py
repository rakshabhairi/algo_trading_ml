import sys
import yfinance as yf
import pandas as pd
from datetime import datetime

from strategies.strategies import generate_signals, compute_indicators
from ml.model import run_ml_model
from utils.google_sheets import (
    connect_to_gsheet,
    log_trade,
    log_ml_predictions,
    log_model_accuracy,
    log_pl_summary,
)

TICKERS = ["RELIANCE.NS", "INFY.NS", "TCS.NS"]
PERIOD = "6mo"
INTERVAL = "1d"
SHEET_NAME = "AlgoTradingLog"
CREDENTIALS_FILE = "credentials.json"

try:
    sheet = connect_to_gsheet(CREDENTIALS_FILE, SHEET_NAME)
except Exception as e:
    print(f"[ERROR] Google Sheets connection failed: {e}")
    sys.exit(1)

for ticker in TICKERS:
    print(f"\n📈 Processing {ticker}...")

    data = yf.download(ticker, period=PERIOD, interval=INTERVAL, auto_adjust=True)
    if data.empty:
        print(f"[ERROR] No data for {ticker}")
        continue

    data.reset_index(inplace=True)
    data.columns = [col[0] if isinstance(col, tuple) else col for col in data.columns]

    try:
        signals_df = generate_signals(data)
        signals_df.dropna(inplace=True)
    except Exception as e:
        print(f"[ERROR] Signal generation failed for {ticker}: {e}")
        continue

    if signals_df.empty:
        print(f"⚠️ No signals generated for {ticker}")
        continue

    print(f"✅ {len(signals_df)} signals generated.")

    trade_rows = []
    for _, row in signals_df.iterrows():
        trade_rows.append(
            [
                ticker,
                row["Date"].strftime("%Y-%m-%d")
                if isinstance(row["Date"], pd.Timestamp)
                else row["Date"],
                round(row["Close"], 2),
                round(row["RSI"], 2),
                round(row["MA20"], 2),
                round(row["MA50"], 2),
                row["Signal"],
            ]
        )

    try:
        log_trade(sheet, trade_rows)
        print(f"✅ Logged {len(trade_rows)} trades for {ticker}.")
    except Exception as e:
        print(f"[ERROR] Logging trades for {ticker} failed: {e}")

    try:
        data = compute_indicators(data)
        data["Signal"] = None
        data.loc[data["RSI"] < 30, "Signal"] = "BUY"
        data.loc[data["RSI"] > 70, "Signal"] = "SELL"
        data_ml = data[data["Signal"].notna()]
    except Exception as e:
        print(f"[ERROR] Failed to compute indicators for ML: {e}")
        continue

    try:
        predictions, accuracy = run_ml_model(data_ml)
        log_model_accuracy(
            sheet,
            "DecisionTreeClassifier",
            round(accuracy * 100, 2),
            datetime.now().strftime("%Y-%m-%d"),
        )
        log_ml_predictions(sheet, ticker, predictions, original_data_df=data_ml)
    except Exception as e:
        print(f"[ERROR] ML prediction failed for {ticker}: {e}")
        accuracy = 0

    try:
        accuracy_value = round(accuracy * 100, 2) if accuracy else 0.0
        log_pl_summary(sheet, [ticker, 0, 0, 0, accuracy_value, 0.0])
    except Exception as e:
        print(f"[ERROR] Summary log failed for {ticker}: {e}")

print("\n🎯 All tickers processed.")
