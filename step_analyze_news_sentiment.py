from db_utils import get_db_connection
from textblob import TextBlob
from datetime import datetime

def analyze_news_sentiment():
    """Analyse le sentiment des news."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS news_sentiment (
            id TEXT PRIMARY KEY,
            news_id TEXT NOT NULL,
            symbol TEXT NOT NULL,
            polarity REAL NOT NULL,
            subjectivity REAL NOT NULL,
            impact_score REAL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(news_id) REFERENCES crypto_news(id)
        )
    """)

    cursor.execute("""
        SELECT id, symbol, title, content
        FROM crypto_news
        WHERE id NOT IN (SELECT news_id FROM news_sentiment)
    """)
    news_list = cursor.fetchall()

    if not news_list:
        print("⚠️ Aucune news à analyser.")
        conn.close()
        return

    for news_id, symbol, title, content in news_list:
        text = f"{title} {content}"
        analysis = TextBlob(text)
        polarity = analysis.sentiment.polarity
        subjectivity = analysis.sentiment.subjectivity
        impact_score = min(100, abs(polarity) * 100 * (1 + subjectivity))

        cursor.execute(
            "INSERT INTO news_sentiment (id, news_id, symbol, polarity, subjectivity, impact_score) VALUES (?, ?, ?, ?, ?, ?)",
            (f"{news_id}-sentiment", news_id, symbol, polarity, subjectivity, impact_score)
        )
        sentiment = "🟢 Positif" if polarity > 0.1 else "🔴 Négatif" if polarity < -0.1 else "🟡 Neutre"
        print(f"📊 {symbol}: {title[:40]}... → {sentiment} (Polarity: {polarity:.2f}, Impact: {impact_score:.0f}/100)")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    analyze_news_sentiment()