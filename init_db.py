import sqlite3

def init_db():
    """Crée toutes les tables nécessaires si elles n'existent pas."""
    conn = sqlite3.connect("crypto.db")
    cursor = conn.cursor()

    # Table des prix
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            price REAL NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(symbol, timestamp)
        )
    """)

    # Table des indicateurs (RSI, MACD, etc.)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS indicators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            rsi REAL,
            macd REAL,
            signal REAL,
            histogram REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(symbol, timestamp)
        )
    """)

    # Table des corrélations
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS correlations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol1 TEXT NOT NULL,
            symbol2 TEXT NOT NULL,
            correlation REAL NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(symbol1, symbol2, timestamp)
        )
    """)

    # Table des news (déjà créée dans step_fetch_crypto_news_rss.py)
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

    # Table des corrélations news/RSI
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS news_rsi_correlation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            news_id TEXT NOT NULL,
            symbol TEXT NOT NULL,
            rsi REAL NOT NULL,
            correlation REAL NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(news_id) REFERENCES crypto_news(id)
        )
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("✅ Base de données initialisée avec toutes les tables.")