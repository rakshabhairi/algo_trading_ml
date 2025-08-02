import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

REQUIRED_SHEETS = {
    "Trades": ["Ticker", "Date", "Close", "RSI", "MA20", "MA50", "Signal"],
    "MLPredictions": ["Date", "Ticker", "RSI", "MACD", "Volume", "Predicted", "Actual", "Correct"],
    "ModelAccuracy": ["Model", "Accuracy (%)", "Date"],
    "PLSummary": ["Ticker", "Total Trades", "Winning Trades", "Win Ratio (%)", "Model Accuracy (%)", "Total Profit"],
}

def connect_to_gsheet(credentials_file, sheet_name):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_file(credentials_file, scopes=scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open(sheet_name)

    for tab_name, headers in REQUIRED_SHEETS.items():
        try:
            worksheet = spreadsheet.worksheet(tab_name)
        except gspread.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title=tab_name, rows="1000", cols=str(len(headers)))
            worksheet.append_row(headers)
        else:
            existing_headers = worksheet.row_values(1)
            if existing_headers != headers:
                worksheet.delete_rows(1)
                worksheet.insert_row(headers, index=1)
    return spreadsheet

def log_trade(sheet, trades):
    try:
        ws = sheet.worksheet("Trades")
        ws.append_rows(trades)
    except Exception as e:
        print(f"[ERROR] Failed to log trades batch: {e}")

def log_ml_predictions(sheet, ticker, predictions_df, original_data_df=None):
    try:
        ws = sheet.worksheet("MLPredictions")
        if original_data_df is not None:
            if 'Volume' not in predictions_df.columns or predictions_df['Volume'].isnull().all():
                predictions_df = predictions_df.merge(original_data_df[['Date', 'Volume']], on='Date', how='left')
        if 'Volume' not in predictions_df.columns:
            predictions_df['Volume'] = ""
        if 'Actual_Signal' not in predictions_df.columns:
            predictions_df['Actual_Signal'] = ""
        if 'Correct' not in predictions_df.columns:
            predictions_df['Correct'] = False

        rows = []
        for _, row in predictions_df.iterrows():
            date_str = pd.to_datetime(row["Date"]).strftime("%Y-%m-%d")
            volume_str = str(row.get("Volume", ""))
            predicted = row.get("Predicted_Signal", "")
            actual = row.get("Actual_Signal", "")
            correct_flag = row.get("Correct", False)

            correct_display = ""
            if isinstance(correct_flag, (bool, int)):
                correct_display = "✅" if bool(correct_flag) else ""
            elif isinstance(correct_flag, str):
                if correct_flag.lower() in ["true", "yes", "1", "✅"]:
                    correct_display = "✅"

            macd_val = row.get("MACD", 0)
            macd_display = round(macd_val, 4) if isinstance(macd_val, (float, int)) else 0.0

            rows.append([
                date_str,
                ticker,
                round(row.get("RSI", 0), 2),
                macd_display,
                volume_str,
                predicted,
                actual,
                correct_display,
            ])

        ws.append_rows(rows)
        print(f"✅ Logged {len(rows)} ML prediction rows for {ticker}")
    except Exception as e:
        print(f"[ERROR] Failed to log ML predictions: {e}")

def log_model_accuracy(sheet, model_name, accuracy, date):
    try:
        ws = sheet.worksheet("ModelAccuracy")
        records = ws.get_all_records()
        for idx, record in enumerate(records, start=2):
            if record.get("Model") == model_name and record.get("Date") == date:
                ws.delete_rows(idx)
                break
        ws.append_row([model_name, accuracy, date])
    except Exception as e:
        print(f"[ERROR] Failed to log model accuracy: {e}")

def log_pl_summary(sheet, summary_data):
    try:
        ws = sheet.worksheet("PLSummary")
        trades_ws = sheet.worksheet("Trades")

        ticker = summary_data[0]
        all_trades = trades_ws.get_all_records()
        trades = [t for t in all_trades if t.get("Ticker") == ticker]
        trades.sort(key=lambda x: x.get("Date") or "")

        total_trades = 0
        winning_trades = 0
        total_profit = 0.0
        open_buy_price = None

        for trade in trades:
            signal = str(trade.get("Signal", "")).strip().upper()
            close = trade.get("Close")
            if close in [None, '', 'N/A']:
                continue
            try:
                price = float(close)
            except (TypeError, ValueError):
                continue

            print(f"Processing trade: Signal={signal}, Price={price}, OpenBuyPrice={open_buy_price}")
            if signal == "BUY" and open_buy_price is None:
                open_buy_price = price
                print(f"Opened BUY at {price}")
            elif signal == "SELL" and open_buy_price is not None:
                profit = price - open_buy_price
                total_profit += profit
                total_trades += 1
                if profit > 0:
                    winning_trades += 1
                print(f"Closed SELL at {price} with profit {profit}")
                open_buy_price = None

        win_ratio = round((winning_trades / total_trades) * 100, 2) if total_trades > 0 else 0.0
        accuracy_value = float(summary_data[4]) if isinstance(summary_data[4], (int, float)) else 0.0

        final_data = [
            ticker,
            total_trades,
            winning_trades,
            win_ratio,
            round(accuracy_value, 2),
            round(total_profit, 2),
        ]

        records = ws.get_all_records()
        for idx, row in enumerate(records, start=2):
            if row.get("Ticker") == ticker:
                ws.delete_rows(idx)
                break

        ws.append_row(final_data)

        print(f"PL Summary for {ticker}: {final_data}")
    except Exception as e:
        print(f"[ERROR] Failed to log PL summary: {e}")
