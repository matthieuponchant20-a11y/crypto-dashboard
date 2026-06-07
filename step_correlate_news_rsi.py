import os
from datetime import datetime
# -*- coding: utf-8 -*-
import sys
import io
from db_utils import get_db_connection, get_db_path  # 👈 Importe la fonction

# Ajoute ça au début de chaque script (après les imports)
print(f"📁 [SCRIPT] Répertoire courant: {os.getcwd()}")
print(f"📁 [SCRIPT] Chemin de la base: {get_db_path()}")

# Compatibilité Windows/UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def correlate_news_rsi():
    """Calcule l'impact moyen des news sur le RSI pour chaque crypto."""
    conn = get_db_connection()  # ✅ Utilise le chemin persistant
    cursor = conn.cursor()

    #DEBUG 
    print(f"📁 Répertoire courant: {os.getcwd()}")
    print(f"📁 Chemin de la base: {get_db_connection().execute('PRAGMA database_list').fetchall()}")
    #DEBUG 

    # Crée la table des corrélations news/RSI
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS news_rsi_correlation (
            id TEXT PRIMARY KEY,
            symbol TEXT NOT NULL,
            avg_polarity REAL,  
            avg_impact REAL,   
            rsi REAL,           
            correlation REAL,  
            sentiment_trend TEXT,  
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    symbols = ["BTC", "ETH", "SOL", "AAVE", "XRP", "VET"]

    for symbol in symbols:
        # 1. Récupère le RSI actuel
        cursor.execute("""
            SELECT rsi FROM indicators
            WHERE symbol = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (symbol,))
        rsi_data = cursor.fetchone()
        if not rsi_data:
            print(f"⚠️ Pas de RSI pour {symbol}")
            continue
        rsi = rsi_data[0]

        # 2. Récupère les news récentes (7 derniers jours) et leur sentiment
        cursor.execute("""
            SELECT ns.polarity, ns.impact_score
            FROM news_sentiment ns
            JOIN crypto_news cn ON ns.news_id = cn.id
            WHERE cn.symbol = ? AND cn.published_at >= datetime('now', '-7 days')
        """, (symbol,))
        sentiment_data = cursor.fetchall()

        if not sentiment_data:
            print(f"⚠️ Pas de news pour {symbol}")
            continue

        # 3. Calcule la moyenne des polarités et des impacts
        avg_polarity = sum(row[0] for row in sentiment_data) / len(sentiment_data)
        avg_impact = sum(row[1] for row in sentiment_data) / len(sentiment_data)

        # 4. Détermine la tendance du sentiment
        if avg_polarity > 0.1:
            sentiment_trend = "Positive"
        elif avg_polarity < -0.1:
            sentiment_trend = "Negative"
        else:
            sentiment_trend = "Neutral"

        # 5. Calcule la corrélation (0-1)
        # Si les news sont très positives (polarity > 0.3) et que le RSI est bas (< 40), l'impact est fort
        if avg_polarity > 0.3 and rsi < 40:
            correlation = 1.0  # Forte corrélation positive
        elif avg_polarity < -0.3 and rsi > 60:
            correlation = 1.0  # Forte corrélation négative
        elif avg_polarity > 0.1 and rsi < 50:
            correlation = 0.7  # Corrélation modérée
        elif avg_polarity < -0.1 and rsi > 50:
            correlation = 0.7  # Corrélation modérée
        else:
            correlation = 0.3  # Faible corrélation

        # 6. Sauvegarde en base
        cursor.execute(
            "INSERT OR REPLACE INTO news_rsi_correlation (id, symbol, avg_polarity, avg_impact, rsi, correlation, sentiment_trend) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (f"{symbol}-{datetime.now().strftime('%Y%m%d%H%M%S%f')}", symbol, avg_polarity, avg_impact, rsi, correlation, sentiment_trend)
        )
        print(f"🔗 {symbol}: Sentiment={sentiment_trend}, Polarity={avg_polarity:.2f}, RSI={rsi:.2f} → Corrélation={correlation:.2f}")
    conn.commit()
    conn.close()

if __name__ == "__main__":
    correlate_news_rsi()