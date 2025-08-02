import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)

def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if 'Close' not in df.columns:
        raise ValueError("[ERROR] 'Close' column missing")

    df['MA20'] = df['Close'].rolling(window=20, min_periods=20).mean()
    df['MA50'] = df['Close'].rolling(window=50, min_periods=50).mean()

    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=14, min_periods=14).mean()
    avg_loss = loss.rolling(window=14, min_periods=14).mean()
    rs = avg_gain / avg_loss
    rs = rs.replace([float('inf'), -float('inf')], 0).fillna(0)
    df['RSI'] = 100 - (100 / (1 + rs))

    short_ema = df['Close'].ewm(span=12, adjust=False).mean()
    long_ema = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = short_ema - long_ema

    if 'Volume' not in df.columns:
        df['Volume'] = 0

    df = df.dropna(subset=['MA20', 'MA50', 'RSI']).reset_index(drop=True)
    logging.info(f"MACD sample values:\n{df['MACD'].head()}")
    return df

def generate_signals(df: pd.DataFrame) -> pd.DataFrame:
    df = compute_indicators(df)

    if 'Date' not in df.columns:
        if isinstance(df.index, pd.DatetimeIndex):
            df['Date'] = df.index
        else:
            df['Date'] = pd.date_range(start=0, periods=len(df), freq='D')

    df['Signal'] = ""
    num_rsi_below_30 = (df['RSI'] < 30).sum()
    num_rsi_above_70 = (df['RSI'] > 70).sum()
    logging.info(f"Days with RSI < 30: {num_rsi_below_30}, RSI > 70: {num_rsi_above_70}")

    for idx, row in df.iterrows():
        if row['RSI'] < 30:
            df.at[idx, 'Signal'] = 'BUY'
        elif row['RSI'] > 70:
            df.at[idx, 'Signal'] = 'SELL'

    signals = df[df['Signal'] != ''].copy()
    signals['Date'] = pd.to_datetime(signals['Date']).dt.strftime("%Y-%m-%d")
    signals['Close'] = signals['Close'].round(2)
    signals['RSI'] = signals['RSI'].round(2)
    signals['MA20'] = signals['MA20'].round(2)
    signals['MA50'] = signals['MA50'].round(2)
    signals['MACD'] = signals['MACD'].round(4)
    if 'Volume' in signals.columns:
        signals['Volume'] = signals['Volume'].fillna(0)

    if signals.empty:
        logging.info("No signals generated.")

    return signals[['Date', 'Close', 'RSI', 'MA20', 'MA50', 'MACD', 'Volume', 'Signal']]
