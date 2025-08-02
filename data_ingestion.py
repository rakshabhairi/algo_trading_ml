import yfinance as yf
import pandas as pd
import time
import logging

# Setup logging once (avoid duplicate logs if imported)
logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)

def fetch_data(
    tickers, 
    period='6mo', 
    interval='1d', 
    retries=3, 
    delay=2, 
    start_date=None, 
    end_date=None
):
    """
    Fetch historical stock data from Yahoo Finance.

    Parameters:
        tickers (list): List of ticker symbols (e.g., ['RELIANCE.NS', 'TCS.NS'])
        period (str): Time period (e.g., '6mo', '1y') — ignored if start_date provided
        interval (str): Data frequency (e.g., '1d', '1h')
        retries (int): Retry attempts on failure
        delay (int): Seconds to wait between retries
        start_date (str): Optional start date (YYYY-MM-DD)
        end_date (str): Optional end date (YYYY-MM-DD)

    Returns:
        dict: {ticker: DataFrame with 'Date', 'Open', 'High', 'Low', 'Close', 'Volume'}
    """
    data = {}
    required_cols = {"Close", "Open", "High", "Low", "Volume"}

    for ticker in tickers:
        logger.info(f"📥 Fetching data for {ticker}...")

        for attempt in range(1, retries + 1):
            try:
                df = yf.download(
                    ticker,
                    period=None if start_date else period,
                    start=start_date,
                    end=end_date,
                    interval=interval,
                    progress=False,
                    auto_adjust=True,
                    threads=False
                )

                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)

                logger.debug(f"[DEBUG] Attempt {attempt} — {ticker}: {df.shape[0]} rows")

                if df is not None and not df.empty and required_cols.issubset(df.columns):
                    df = df.reset_index()
                    
                    # Ensure 'Date' column exists; yfinance may use 'index' for dates
                    if 'Date' not in df.columns:
                        if 'index' in df.columns:
                            df.rename(columns={'index': 'Date'}, inplace=True)
                        elif 'datetime' in df.columns:
                            df.rename(columns={'datetime': 'Date'}, inplace=True)
                        else:
                            df.insert(0, 'Date', pd.date_range(end=pd.Timestamp.today(), periods=len(df)))

                    # Ensure consistent column order and truncate unwanted columns
                    df = df[["Date", "Open", "High", "Low", "Close", "Volume"]]
                    data[ticker] = df

                    if df.shape[0] < 100:
                        logger.warning(f"⚠️ {ticker} has only {df.shape[0]} records (less than expected 120+).")
                    logger.info(f"✅ Success: {ticker} - {df.shape[0]} rows")
                    break

                else:
                    logger.warning(f"⚠️ Attempt {attempt}: Incomplete data for {ticker}. Retrying in {delay}s...")
                    time.sleep(delay)

            except Exception as e:
                logger.error(f"❌ Attempt {attempt}: Failed to fetch {ticker}: {e}")
                time.sleep(delay)

        else:
            logger.error(f"❌ Skipping {ticker} after {retries} failed attempts.")

        time.sleep(1)  # Avoid rate limits

    return data
