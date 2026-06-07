import sqlite3

def init_db():
    """Crée TOUTES les tables et colonnes nécessaires."""
    conn = sqlite3.connect("crypto.db")
    cursor = conn.cursor()

    # ========== TABLES PRINCIPALES ==========
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
            timeframe TEXT DEFAULT '1h',
            UNIQUE(symbol, timestamp, timeframe)
        )
    """)

    # Table des corrélations (avec la colonne timeframe)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS correlations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol1 TEXT NOT NULL,
            symbol2 TEXT NOT NULL,
            correlation REAL NOT NULL,
            timeframe TEXT DEFAULT '1h',
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(symbol1, symbol2, timestamp, timeframe)
        )
    """)

    # Table des news
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

    # Table news_sentiment (NOUVELLE TABLE MANQUANTE)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS news_sentiment (
            id TEXT PRIMARY KEY,
            news_id TEXT NOT NULL,
            polarity REAL NOT NULL,
            subjectivity REAL NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(news_id) REFERENCES crypto_news(id)
        )
    """)

    # Table news_rsi_correlation (avec avg_polarity)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS news_rsi_correlation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            news_id TEXT NOT NULL,
            symbol TEXT NOT NULL,
            rsi REAL NOT NULL,
            correlation REAL NOT NULL,
            avg_polarity REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(news_id) REFERENCES crypto_news(id)
        )
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("✅ Base de données initialisée avec TOUTES les tables et colonnes.")