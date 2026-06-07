import sqlite3

def init_db():
    """Crée TOUTES les tables et colonnes nécessaires pour ton app."""
    conn = sqlite3.connect("crypto.db")
    cursor = conn.cursor()

    # ========== 1. TABLE PRICES ==========
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            price REAL NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(symbol, timestamp)
        )
    """)

    # ========== 2. TABLE INDICATORS ==========
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS indicators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            rsi REAL,
            macd REAL,
            signal REAL,
            histogram REAL,
            timeframe TEXT DEFAULT '1h',
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(symbol, timestamp, timeframe)
        )
    """)

    # ========== 3. TABLE CORRELATIONS ==========
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

    # ========== 4. TABLE CRYPTO_NEWS ==========
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

    # ========== 5. TABLE NEWS_SENTIMENT ==========
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS news_sentiment (
            id TEXT PRIMARY KEY,
            news_id TEXT NOT NULL,
            polarity REAL NOT NULL,
            subjectivity REAL NOT NULL,
            impact_score REAL, 
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(news_id) REFERENCES crypto_news(id)
        )
    """)

    # ========== 6. TABLE NEWS_RSI_CORRELATION ==========
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS news_rsi_correlation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            news_id TEXT NOT NULL,
            symbol TEXT NOT NULL,
            rsi REAL NOT NULL,
            correlation REAL NOT NULL,
            avg_polarity REAL,
            avg_impact REAL,
            sentiment_trend REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(news_id) REFERENCES crypto_news(id)
        )
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("✅ Base de données initialisée avec TOUTES les colonnes manquantes.")