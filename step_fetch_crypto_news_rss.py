from db_utils import get_db_connection
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import time

CRYPTOS = ["bitcoin", "ethereum", "solana", "aave", "ripple", "vechain"]
SYMBOLS = ["BTC", "ETH", "SOL", "AAVE", "XRP", "VET"]
RSS_FEEDS = [
    {"name": "CoinDesk", "url": "https://www.coindesk.com/feed"},
    {"name": "CoinTelegraph", "url": "https://cointelegraph.com/feed"},
    {"name": "CoinTribune", "url": "https://www.cointribune.com/feed"}, 
    {"name": "JournalDuCoin", "url": "https://journalducoin.com/feed/"}, 
    {"name": "CryptoNews", "url": "https://cryptonews.com/fr/feed/"}
]

def parse_rss(url):
    try:
        response = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        root = ET.fromstring(response.content)
        items = []
        for item in root.findall('.//item'):
            items.append({
                'title': item.find('title').text or "",
                'link': item.find('link').text or "",
                'pubDate': item.find('pubDate').text or "",
                'description': item.find('description').text or ""
            })
        return items
    except Exception as e:
        print(f"⚠️ Erreur RSS {url}: {e}")
        return []

def fetch_crypto_news_rss(days=7):
    conn = get_db_connection()
    cursor = conn.cursor()

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
        try:
            print(f"📰 Récupération depuis {feed['name']}...")
            items = parse_rss(feed["url"])
            if not items:
                continue

            for entry in items:
                news_symbols = [
                    symbol for symbol in SYMBOLS
                    if symbol.lower() in (entry['title'] or "").lower()
                    or symbol.lower() in (entry['description'] or "").lower()
                ]
                if not news_symbols:
                    continue

                try:
                    published_at = datetime.strptime(entry['pubDate'], '%a, %d %b %Y %H:%M:%S %z').replace(tzinfo=None)
                except (ValueError, TypeError):
                    published_at = datetime.now()

                if published_at < start_date:
                    continue

                for symbol in news_symbols:
                    news_id = f"{symbol}-{hash(entry['link'])}"
                    cursor.execute("""
                        INSERT OR IGNORE INTO crypto_news
                        (id, symbol, title, source, url, content, published_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        news_id, symbol, entry['title'], feed['name'],
                        entry['link'], entry['description'][:2000], published_at
                    ))
                    print(f"✅ News: {entry['title'][:50]}... ({symbol})")

        except Exception as e:
            print(f"⚠️ Erreur avec {feed['name']}: {e}")

    conn.commit()
    conn.close()
    print("✅ News récupérées.")

if __name__ == "__main__":
    fetch_crypto_news_rss(days=7)