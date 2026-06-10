from db_utils import get_db_connection
from datetime import datetime

def correlate_news_rsi():
    """Calcule l'impact des news sur le RSI."""
    conn = get_db_connection()
    cursor = conn.cursor()

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
        # Récupère le RSI
        cursor.execute("SELECT rsi FROM indicators WHERE symbol = ? ORDER BY timestamp DESC LIMIT 1", (symbol,))
        rsi_data = cursor.fetchone()
        if not rsi_data:
            print(f"⚠️ Pas de RSI pour {symbol}")
            continue
        rsi = rsi_data[0]

        # Récupère les news récentes
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

        avg_polarity = sum(row[0] for row in sentiment_data) / len(sentiment_data)
        avg_impact = sum(row[1] for row in sentiment_data) / len(sentiment_data)

        if avg_polarity > 0.1:
            sentiment_trend = "Positive"
        elif avg_polarity < -0.1:
            sentiment_trend = "Negative"
        else:
            sentiment_trend = "Neutral"

        if avg_polarity > 0.3 and rsi < 40:
            correlation = 1.0
        elif avg_polarity < -0.3 and rsi > 60:
            correlation = 1.0
        elif avg_polarity > 0.1 and rsi < 50:
            correlation = 0.7
        elif avg_polarity < -0.1 and rsi > 50:
            correlation = 0.7
        else:
            correlation = 0.3

        cursor.execute(
            "INSERT OR REPLACE INTO news_rsi_correlation (id, symbol, avg_polarity, avg_impact, rsi, correlation, sentiment_trend) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (f"{symbol}-{datetime.now().strftime('%Y%m%d%H%M%S%f')}", symbol, avg_polarity, avg_impact, rsi, correlation, sentiment_trend)
        )
        print(f"🔗 {symbol}: Sentiment={sentiment_trend}, RSI={rsi:.2f} → Corrélation={correlation:.2f}")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    correlate_news_rsi()