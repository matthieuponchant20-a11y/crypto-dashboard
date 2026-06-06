import sqlite3
import feedparser
from datetime import datetime, timedelta
# -*- coding: utf-8 -*-
import sys
import io

# Compatibilité Windows/UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

CRYPTOS = ["bitcoin", "ethereum", "solana", "aave", "ripple", "vechain"]
SYMBOLS = ["BTC", "ETH", "SOL", "AAVE", "XRP", "VET"]
RSS_FEEDS = [
    {"name": "CoinDesk", "url": "https://coindesk.com/feed"},
    {"name": "CoinTelegraph", "url": "https://cointelegraph.com/feed"},
    {"name": "CryptoNews", "url": "https://cryptonews.com/feed"}
]

def fetch_crypto_news_rss(days=7):
    """Récupère les news via les flux RSS."""
    conn = sqlite3.connect("crypto.db")
    cursor = conn.cursor()

    # Création de la table (sans commentaire dans la requête)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS crypto_news (
            id TEXT PRIMARY KEY,
            symbol TEXT NOT NULL,
            title TEXT NOT NULL,
            source TEXT NOT NULL,
            url TEXT NOT NULL,
            content TEXT,
            published_at DATETIME NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(symbol, url)
        )
    """)

    start_date = datetime.now() - timedelta(days=days)

    for feed in RSS_FEEDS:
        parsed_feed = feedparser.parse(feed["url"])
        for entry in parsed_feed.entries:
            # Vérifie si la news concerne une de nos cryptos
            news_symbols = []
            for symbol in SYMBOLS:
                if symbol.lower() in entry.title.lower() or symbol.lower() in entry.summary.lower():
                    news_symbols.append(symbol)

            if not news_symbols:
                continue

            # Récupère la date de publication
            if hasattr(entry, 'published_parsed'):
                published_at = datetime(*entry.published_parsed[:6])
            else:
                published_at = datetime.now()

            if published_at < start_date:
                continue

            # Insère la news pour chaque crypto concernée
            for symbol in news_symbols:
                cursor.execute("""
                    INSERT OR IGNORE INTO crypto_news
                    (id, symbol, title, source, url, content, published_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    f"{symbol}-{entry.id}",
                    symbol,
                    entry.title,
                    feed["name"],
                    entry.link,
                    entry.summary[:2000] if hasattr(entry, 'summary') else "",
                    published_at
                ))
                print(f"✅ News: {entry.title[:50]}... ({symbol})")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    fetch_crypto_news_rss(days=7)