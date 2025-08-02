import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score

def run_ml_model(df: pd.DataFrame):
    df = df.copy()

    # Use indicator names consistent with your other modules
    required_cols = ['RSI', 'MA20', 'MA50', 'Signal']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"[ERROR] Missing required column: {col}")

    # Map Signal to numeric label
    df['Signal_Label'] = df['Signal'].map({'BUY': 1, 'SELL': 0})
    df = df.dropna(subset=['Signal_Label'])

    if df.shape[0] < 10:
        raise ValueError("Not enough data for ML model (need at least 10 rows).")

    X = df[['RSI', 'MA20', 'MA50']]
    y = df['Signal_Label']

    X = X.reset_index(drop=True)
    y = y.reset_index(drop=True)
    df = df.reset_index(drop=True)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

    if X_test.empty or y_test.empty:
        raise ValueError("Test set is empty. Cannot evaluate model.")

    model = DecisionTreeClassifier(random_state=42)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    # Map predicted labels back to BUY/SELL
    predicted_signal = pd.Series(y_pred).map({1: 'BUY', 0: 'SELL'}).values

    # If Date not present, fill with index
    if 'Date' not in df.columns:
        df['Date'] = df.index.astype(str)

    predictions_df = df.loc[X_test.index].copy()
    predictions_df['Predicted_Signal'] = predicted_signal

    return predictions_df[['Date', 'RSI', 'MA20', 'MA50', 'Predicted_Signal']], accuracy
