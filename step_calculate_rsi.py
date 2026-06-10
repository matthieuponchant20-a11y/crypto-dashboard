from db_utils import get_db_connection
from indicators import rsi
import pandas as pd
import numpy as np
from datetime import datetime

def calculate_rsi(window=14):
    """Calcule le RSI pour toutes les cryptos."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS indicators (
            id TEXT PRIMARY KEY,
            symbol TEXT NOT NULL,
            rsi REAL,
            timestamp DATETIME NOT NULL
        )
    """)

    for symbol in ["BTC", "ETH", "SOL", "AAVE", "XRP", "VET"]:
        cursor.execute(f"SELECT price, timestamp FROM prices WHERE symbol = '{symbol}' ORDER BY timestamp")
        df = pd.read_sql(f"SELECT price, timestamp FROM prices WHERE symbol = '{symbol}' ORDER BY timestamp", conn)
        if len(df) < window:
            print(f"⚠️ Pas assez de données pour {symbol}.")
            continue

        prices_array = np.array(df["price"])
        rsi_values = rsi(prices_array, period=14)
        df["RSI"] = rsi_values
        last_rsi = df["RSI"].iloc[-1]
        last_timestamp = df["timestamp"].iloc[-1]

        cursor.execute(
            "INSERT OR REPLACE INTO indicators (id, symbol, rsi, timestamp) VALUES (?, ?, ?, ?)",
            (f"{symbol}-{last_timestamp.replace(' ', '').replace(':', '')}", symbol, last_rsi, last_timestamp)
        )
        print(f"📊 RSI {symbol}: {last_rsi:.2f} (à {last_timestamp})")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    calculate_rsi()