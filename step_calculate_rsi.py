import sqlite3
import pandas as pd
import numpy as np
from indicators import rsi
from datetime import datetime
# -*- coding: utf-8 -*-
import sys
import io

# Compatibilité Windows/UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def calculate_rsi(window=14):
    """Calcule le RSI pour toutes les cryptos."""
    conn = sqlite3.connect("crypto.db")
    cursor = conn.cursor()

    # Crée la table des indicateurs si elle n'existe pas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS indicators (
            id TEXT PRIMARY KEY,
            symbol TEXT NOT NULL,
            rsi REAL,
            timestamp DATETIME NOT NULL
        )
    """)

    # Récupère les données pour chaque crypto
    for symbol in ["BTC", "ETH", "SOL", "AAVE", "XRP", "VET"]:
        query = f"""
            SELECT price, timestamp
            FROM prices
            WHERE symbol = '{symbol}'
            ORDER BY timestamp
        """
        df = pd.read_sql(query, conn)
        if len(df) < window:
            print(f"⚠️ Pas assez de données pour {symbol} (nécessite {window} points).")
            continue

        # Calcule le RSI
        prices_array = np.array(df["price"])
        rsi_values = rsi(prices_array, period=14)  # 👈 Même résultat, sans dépendance
        df["RSI"] = rsi_values
        last_rsi = df["RSI"].iloc[-1]
        last_timestamp = df["timestamp"].iloc[-1]

        # Sauvegarde en base
        cursor.execute(
            "INSERT OR REPLACE INTO indicators (id, symbol, rsi, timestamp) VALUES (?, ?, ?, ?)",
            (f"{symbol}-{last_timestamp.replace(' ', '').replace(':', '')}-{datetime.now().strftime('%S')}", symbol, last_rsi, last_timestamp)
        )
        print(f"📊 RSI {symbol}: {last_rsi:.2f} (à {last_timestamp})")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    calculate_rsi()