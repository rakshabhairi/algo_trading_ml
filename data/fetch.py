# File: data/fetch_data.py

import yfinance as yf
import pandas as pd
import time
import logging

logging.basicConfig(level=logging.INFO)

def fetch_data(tickers, period='6mo', interval='1d', retries=3, delay=2):
    """
    Fetch historical stock data from Yahoo Finance.

    Parameters:
        tickers (list): List of ticker symbols (e.g., ['RELIANCE.NS', 'TCS.NS'])
        period (str): Time period (e.g., '6mo', '1y')
        interval (str): Data frequency (e.g., '1d', '1h')
        retries (int): Retry attempts on failure
        delay (int): Seconds to wait between retries

    Returns:
        dict: {ticker: DataFrame of OHLCV data with 'Date' column}
    """
    data = {}
    required_cols = {"Close", "Open", "High", "Low", "Volume"}

    for ticker in tickers:
        logging.info(f"📥 Fetching data for {ticker}...")

        for attempt in range(1, retries + 1):
            try:
                df = yf.download(
                    ticker,
                    period=period,
                    interval=interval,
                    progress=False,
                    auto_adjust=True,
                    threads=False
                )

                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)

                logging.debug(f"[DEBUG] Attempt {attempt} — {ticker}: {df.shape[0]} rows")

                if df is not None and not df.empty and required_cols.issubset(df.columns):
                    df = df.reset_index()
                    df = df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]
                    data[ticker] = df

                    if df.shape[0] < 100:
                        logging.warning(f"⚠️ {ticker} has only {df.shape[0]} records (less than expected 120+).")

                    logging.info(f"✅ Success: {ticker} - {df.shape[0]} rows")
                    break  # Success

                else:
                    logging.warning(f"⚠️ Attempt {attempt}: Incomplete data for {ticker}. Retrying in {delay}s...")
                    time.sleep(delay)

            except Exception as e:
                logging.error(f"❌ Attempt {attempt}: Failed to fetch {ticker}: {e}")
                time.sleep(delay)

        else:
            logging.error(f"❌ Skipping {ticker} after {retries} failed attempts.")

        time.sleep(1)  # Sleep between tickers to avoid hitting rate limits

    return data
