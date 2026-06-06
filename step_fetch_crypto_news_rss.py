import sqlite3
import requests
import xml.etree.ElementTree as ET
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
def parse_rss(url):
    """Parse un flux RSS sans feedparser (natif Python)."""
    response = requests.get(url, timeout=10)
    root = ET.fromstring(response.content)
    items = []
    for item in root.findall('.//item'):
        title = item.find('title').text if item.find('title') is not None else "No title"
        link = item.find('link').text if item.find('link') is not None else ""
        pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ""
        description = item.find('description').text if item.find('description') is not None else ""
        items.append({
            'title': title,
            'link': link,
            'pubDate': pub_date,
            'description': description
        })
    return items

def fetch_crypto_news_rss(days=7):
    """Récupère les news via les flux RSS."""
    conn = sqlite3.connect("crypto.db")
    cursor = conn.cursor()

    # Création de la table
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
        parsed_feed = parse_rss(feed["url"])  # 👈 Retourne une liste de dicts
        for entry in parsed_feed:  # 👈 entry est un DICT, pas un objet
            # Vérifie si la news concerne une de nos cryptos
            news_symbols = []
            for symbol in SYMBOLS:
                # ✅ Correction : utilise entry['title'] et entry['description']
                if (symbol.lower() in entry['title'].lower() or
                    symbol.lower() in entry['description'].lower()):
                    news_symbols.append(symbol)

            if not news_symbols:
                continue

            # ✅ Correction : utilise entry['pubDate'] et convertis en datetime
            try:
                published_at = datetime.strptime(entry['pubDate'], '%a, %d %b %Y %H:%M:%S %z').replace(tzinfo=None)
            except (ValueError, TypeError):
                published_at = datetime.now().replace(tzinfo=None)

            if published_at < start_date:
                continue

            # ✅ Correction : utilise les clés du dictionnaire
            for symbol in news_symbols:
                # Génère un ID unique (ex: hash du lien + symbol)
                news_id = f"{symbol}-{hash(entry['link'])}"
                cursor.execute("""
                    INSERT OR IGNORE INTO crypto_news
                    (id, symbol, title, source, url, content, published_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    news_id,  # 👈 ID unique
                    symbol,
                    entry['title'],  # ✅ Clé du dictionnaire
                    feed["name"],
                    entry['link'],
                    entry['description'][:2000],  # ✅ Clé du dictionnaire
                    published_at
                ))
                print(f"✅ News: {entry['title'][:50]}... ({symbol})")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    fetch_crypto_news_rss(days=7)