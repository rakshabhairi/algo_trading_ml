import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)

def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """
    Calculate the Relative Strength Index (RSI) for a given DataFrame.

    Parameters:
        df (pd.DataFrame): Input DataFrame with a 'Close' column.
        period (int): Period for RSI calculation (default is 14).

    Returns:
        pd.DataFrame: DataFrame with 'RSI' column added.
    """
    if 'Close' not in df.columns:
        raise ValueError("Missing 'Close' column in DataFrame for RSI calculation.")

    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()

    rs = avg_gain / avg_loss
    rs = rs.replace([float('inf'), -float('inf')], 0).fillna(0)

    df['RSI'] = 100 - (100 / (1 + rs))
    return df


def add_moving_averages(df: pd.DataFrame, short_window: int = 20, long_window: int = 50) -> pd.DataFrame:
    """
    Add short and long-term moving averages to a DataFrame.

    Parameters:
        df (pd.DataFrame): Input DataFrame with a 'Close' column.
        short_window (int): Window for the short-term moving average (default 20).
        long_window (int): Window for the long-term moving average (default 50).

    Returns:
        pd.DataFrame: DataFrame with 'MA20' and 'MA50' columns added.
    """
    if 'Close' not in df.columns:
        raise ValueError("Missing 'Close' column in DataFrame for moving average calculation.")

    df[f'MA{short_window}'] = df['Close'].rolling(window=short_window, min_periods=short_window).mean()
    df[f'MA{long_window}'] = df['Close'].rolling(window=long_window, min_periods=long_window).mean()
    return df
