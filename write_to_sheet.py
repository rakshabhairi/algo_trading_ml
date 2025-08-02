import gspread
from google.oauth2.service_account import Credentials
import time
import pandas as pd
from strategies.strategies import generate_signals  # fixed import path
from data.fetch import fetch_data  # renamed function for clarity
import logging

logging.basicConfig(level=logging.INFO)

# Step 1: Setup credentials and connect to Google Sheets
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_file(
    "credentials.json",  # Ensure this file exists and is valid
    scopes=SCOPES
)
client = gspread.authorize(creds)

# Step 2: Open or create spreadsheet and worksheet
SHEET_NAME = "AlgoTradingLog"
WORKSHEET_NAME = "Trades"
EXPECTED_HEADERS = ["Ticker", "Date", "Close", "RSI", "MA20", "MA50", "Signal"]  # aligned with your code

try:
    spreadsheet = client.open(SHEET_NAME)
    try:
        worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
    except gspread.exceptions.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=WORKSHEET_NAME, rows="1000", cols=str(len(EXPECTED_HEADERS)))
        worksheet.append_row(EXPECTED_HEADERS)
        logging.info(f"🆕 Created worksheet: {WORKSHEET_NAME} with headers added.")
except Exception as e:
    logging.error(f"❌ Failed to connect to Google Sheets: {e}")
    raise

# Step 3: Set headers if missing or incorrect
current_headers = worksheet.row_values(1)
if current_headers != EXPECTED_HEADERS:
    worksheet.clear()
    worksheet.insert_row(EXPECTED_HEADERS, index=1)
    logging.info("📌 Headers set or updated.")

# Cache existing rows once
try:
    existing_rows = worksheet.get_all_values()[1:]  # exclude header row
    existing_rows_str = [list(map(str, r)) for r in existing_rows]
except Exception as e:
    logging.error(f"[ERROR] Failed to fetch existing rows from Google Sheets: {e}")
    existing_rows_str = []

def log_signal_row(signal_row):
    try:
        signal_str = list(map(str, signal_row))
        if signal_str not in existing_rows_str:
            worksheet.append_row(signal_row)
            existing_rows_str.append(signal_str)  # Update cache
            logging.info(f"✅ Added signal: {signal_row}")
            time.sleep(1)  # Avoid API rate limits
        else:
            logging.info(f"⚠️ Duplicate skipped: {signal_row}")
    except Exception as e:
        logging.error(f"❌ Error logging signal {signal_row}: {e}")

# Step 4: Run strategy and log signals
tickers = ["RELIANCE.NS", "INFY.NS"]

for ticker in tickers:
    try:
        df = fetch_data([ticker], period='6mo', interval='1d').get(ticker)
    except Exception as e:
        logging.error(f"❌ Failed to fetch data for {ticker}: {e}")
        continue

    if df is None or df.empty:
        logging.warning(f"⚠️ No data for {ticker}. Skipping.")
        continue

    try:
        signals_df = generate_signals(df)
    except Exception as e:
        logging.error(f"❌ Error generating signals for {ticker}: {e}")
        continue

    if signals_df.empty:
        logging.info(f"📭 No signals for {ticker}.")
        continue

    for _, row in signals_df.iterrows():
        try:
            date_value = row["Date"]
            date_str = date_value.strftime("%Y-%m-%d") if hasattr(date_value, "strftime") else str(date_value)
            signal_row = [
                ticker,
                date_str,
                round(row["Close"], 2),
                round(row["RSI"], 2),
                round(row["MA20"], 2),
                round(row["MA50"], 2),
                row["Signal"]
            ]
            log_signal_row(signal_row)
        except Exception as e:
            logging.error(f"❌ Error processing signal row for {ticker}: {e}")

logging.info("✅ All signals logged to Google Sheets.")
