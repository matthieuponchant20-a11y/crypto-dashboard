import pandas as pd
from datetime import datetime, timedelta  # 👈 L'import manquant est ici
# -*- coding: utf-8 -*-
import sys
import io
from db_utils import get_db_connection  # 👈 Importe la fonction

# Compatibilité Windows/UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def calculate_correlations(timeframe="7D"):
    """Calcule les corrélations de chaque crypto avec BTC."""
    conn = get_db_connection()  # ✅ Utilise le chemin persistant
    cursor = conn.cursor()

    # Crée la table des corrélations
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS correlations (
            id TEXT PRIMARY KEY,
            symbol1 TEXT NOT NULL,
            symbol2 TEXT NOT NULL,
            correlation REAL NOT NULL,
            timeframe TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    symbols = ["BTC", "ETH", "SOL", "AAVE", "XRP", "VET"]
    start_date = (datetime.now() - timedelta(days=int(timeframe[:-1]))).strftime('%Y-%m-%d')

    # Récupère les données
    query = f"""
        SELECT symbol, price, timestamp
        FROM prices
        WHERE symbol IN ({','.join(['?']*len(symbols))})
        AND timestamp >= ?
        ORDER BY timestamp
    """
    df = pd.read_sql(query, conn, params=[*symbols, start_date])

    if df.empty:
        print("❌ Pas assez de données. Vérifie que tu as bien exécuté step_fetch_historical_data.py")
        conn.close()
        return

    # Pivote les données
    pivot = df.pivot(index="timestamp", columns="symbol", values="price")

    # Calcule les corrélations avec BTC
    for symbol in symbols:
        if symbol == "BTC":
            continue
        if symbol in pivot.columns and "BTC" in pivot.columns:
            corr = pivot[symbol].corr(pivot["BTC"])
            cursor.execute(
                "INSERT OR REPLACE INTO correlations (id, symbol1, symbol2, correlation, timeframe) VALUES (?, ?, ?, ?, ?)",
                (f"{symbol}-BTC-{timeframe}-{datetime.now().strftime('%Y%m%d%H%M%S%f')}", symbol, "BTC", corr, timeframe)
            )
            print(f"🔗 Corrélation {symbol}/BTC ({timeframe}): {corr:.2f}")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    calculate_correlations(timeframe="7D")