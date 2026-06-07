import os
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import sys
import io
import time
from db_utils import get_db_connection  # 👈 Importe la fonction

# Compatibilité Windows/UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

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
    """Parse un flux RSS avec gestion des erreurs."""
    try:
        response = requests.get(
            url,
            timeout=15,  # ✅ Timeout augmenté
            headers={'User-Agent': 'Mozilla/5.0'}  # ✅ Évite le blocage anti-bot
        )
        response.raise_for_status()  # ✅ Vérifie les erreurs HTTP
        root = ET.fromstring(response.content)
        items = []
        for item in root.findall('.//item'):
            items.append({
                'title': item.find('title').text if item.find('title') is not None else "",
                'link': item.find('link').text if item.find('link') is not None else "",
                'pubDate': item.find('pubDate').text if item.find('pubDate') is not None else "",
                'description': item.find('description').text if item.find('description') is not None else ""
            })
        return items
    except Exception as e:
        print(f"⚠️ Erreur lors du parsing de {url}: {e}")
        return []  # ✅ Retourne une liste vide au lieu de planter

def fetch_crypto_news_rss(days=7):
    conn = get_db_connection()  # ✅ Utilise le chemin persistant
    cursor = conn.cursor()

    #DEBUG 
    print(f"📁 Répertoire courant: {os.getcwd()}")
    print(f"📁 Chemin de la base: {get_db_connection().execute('PRAGMA database_list').fetchall()}")
    #DEBUG 

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
        try:
            print(f"📰 Récupération des news depuis {feed['name']}...")
            parsed_feed = parse_rss(feed["url"])
            if not parsed_feed:  # ✅ Si le parsing échoue, passe au suivant
                continue

            for entry in parsed_feed:
                news_symbols = []
                for symbol in SYMBOLS:
                    if (symbol.lower() in (entry['title'] or "").lower() or
                        symbol.lower() in (entry['description'] or "").lower()):
                        news_symbols.append(symbol)

                if not news_symbols:
                    continue

                # Gestion de la date
                try:
                    published_at = datetime.strptime(
                        entry['pubDate'],
                        '%a, %d %b %Y %H:%M:%S %z'
                    ).replace(tzinfo=None)
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
                        news_id,
                        symbol,
                        entry['title'],
                        feed["name"],
                        entry['link'],
                        entry['description'][:2000],
                        published_at
                    ))
                    print(f"✅ News: {entry['title'][:50]}... ({symbol})")

        except Exception as e:
            print(f"⚠️ Erreur avec {feed['name']}: {e}")  # ✅ Ne bloque pas l'orchestration
            continue

    conn.commit()
    conn.close()
    print("✅ Récupération des news terminée.")

if __name__ == "__main__":
    fetch_crypto_news_rss(days=7)