from textblob import TextBlob
from datetime import datetime
# -*- coding: utf-8 -*-
import sys
import io
from db_utils import get_db_connection  # 👈 Importe la fonction

# Compatibilité Windows/UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def analyze_news_sentiment():
    """Analyse le sentiment des news et calcule un score d'impact par crypto."""
    conn = get_db_connection()  # ✅ Utilise le chemin persistant
    cursor = conn.cursor()

    # Crée la table des sentiments
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS news_sentiment (
            id TEXT PRIMARY KEY,
            news_id TEXT NOT NULL,
            symbol TEXT NOT NULL,
            polarity REAL NOT NULL,  
            subjectivity REAL NOT NULL,  
            impact_score REAL,  
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (news_id) REFERENCES crypto_news(id)
        )
    """)

    # Récupère les news non analysées
    cursor.execute("""
        SELECT id, symbol, title, content
        FROM crypto_news
        WHERE id NOT IN (SELECT news_id FROM news_sentiment)
    """)
    news_list = cursor.fetchall()

    if not news_list:
        print("⚠️ Aucune nouvelle news à analyser.")
        conn.close()
        return

    for news_id, symbol, title, content in news_list:
        text = f"{title} {content}"
        analysis = TextBlob(text)
        polarity = analysis.sentiment.polarity
        subjectivity = analysis.sentiment.subjectivity

        # Calcule un score d'impact (0-100)
        # Plus la news est extrême (polarity proche de ±1) ET subjective, plus l'impact est fort
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