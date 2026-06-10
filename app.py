from flask import Flask, render_template, jsonify
import os
from db_utils import get_db_connection
from init_db import init_db

# Importe les fonctions des scripts (plus de subprocess !)
from step_fetch_historical_data import fetch_historical_data
from step_fetch_crypto_news_rss import fetch_crypto_news_rss
from step_analyze_news_sentiment import analyze_news_sentiment
from step_calculate_rsi import calculate_rsi
from step_calculate_correlations import calculate_correlations
from step_correlate_news_rsi import correlate_news_rsi

app = Flask(__name__)

# Variable pour éviter de recharger les données à chaque requête
first_request_done = False

# ========== FONCTIONS DE RÉCUPÉRATION DES DONNÉES ==========
def get_prices():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT symbol, price, MAX(timestamp) as timestamp
            FROM prices
            GROUP BY symbol
            ORDER BY timestamp DESC
        """)
        prices = cursor.fetchall()
        conn.close()
        return prices
    except Exception as e:
        print(f"❌ Erreur dans get_prices(): {e}")
        return []

def get_rsi():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT symbol, rsi, MAX(timestamp) as timestamp
            FROM indicators
            GROUP BY symbol
            ORDER BY timestamp DESC
        """)
        rsi_data = cursor.fetchall()
        conn.close()
        return rsi_data
    except Exception as e:
        print(f"❌ Erreur dans get_rsi(): {e}")
        return []

def get_correlations():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT symbol1, correlation, timeframe
            FROM correlations
            WHERE symbol2 = 'BTC'
            GROUP BY symbol1
            ORDER BY timestamp DESC
            LIMIT 6
        """)
        correlations = cursor.fetchall()
        conn.close()
        return correlations
    except Exception as e:
        print(f"❌ Erreur dans get_correlations(): {e}")
        return []

def get_news_data():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                cn.id, cn.symbol, cn.title, cn.url, cn.source,
                ns.polarity, ns.impact_score, cn.published_at
            FROM crypto_news cn
            JOIN news_sentiment ns ON cn.id = ns.news_id
            ORDER BY cn.published_at DESC
            LIMIT 20
        """)
        news_data = cursor.fetchall()
        conn.close()
        return news_data
    except Exception as e:
        print(f"❌ Erreur dans get_news_data(): {e}")
        return []

def get_news_rsi_correlation():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT symbol, avg_polarity, avg_impact, rsi, correlation, sentiment_trend
            FROM news_rsi_correlation
            GROUP BY symbol
            ORDER BY MAX(timestamp) DESC
            LIMIT 6
        """)
        correlations = cursor.fetchall()
        conn.close()
        return correlations
    except Exception as e:
        print(f"❌ Erreur dans get_news_rsi_correlation(): {e}")
        return []

# ========== ROUTES FLASK ==========
@app.route("/")
def dashboard():
    prices = get_prices()
    rsi_data = get_rsi()
    correlations = get_correlations()
    news_data = get_news_data()
    news_rsi_correlations = get_news_rsi_correlation()
    return render_template(
        "dashboard.html",
        prices=prices,
        rsi_data=rsi_data,
        correlations=correlations,
        news_data=news_data,
        news_rsi_correlations=news_rsi_correlations
    )

@app.route("/api/prices/<symbol>")
def get_price_history(symbol):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT timestamp, price
            FROM prices
            WHERE symbol = ?
            ORDER BY timestamp DESC
            LIMIT 7
        """, (symbol,))
        data = cursor.fetchall()
        conn.close()
        return jsonify({
            "labels": [row[0][:16] for row in reversed(data)],
            "data": [row[1] for row in reversed(data)]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/rsi/<symbol>")
def get_rsi_history(symbol):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT timestamp, rsi
            FROM indicators
            WHERE symbol = ?
            ORDER BY timestamp DESC
            LIMIT 7
        """, (symbol,))
        data = cursor.fetchall()
        conn.close()
        return jsonify({
            "labels": [row[0][:16] for row in reversed(data)],
            "data": [row[1] for row in reversed(data)]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/news_sentiment/<symbol>")
def get_news_sentiment_history(symbol):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT cn.published_at, ns.polarity, ns.impact_score
            FROM news_sentiment ns
            JOIN crypto_news cn ON ns.news_id = cn.id
            WHERE cn.symbol = ?
            ORDER BY cn.published_at DESC
            LIMIT 7
        """, (symbol,))
        data = cursor.fetchall()
        conn.close()
        return jsonify({
            "labels": [row[0][:16] for row in reversed(data)],
            "polarity": [row[1] for row in reversed(data)],
            "impact": [row[2] for row in reversed(data)]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/top_impact_news")
def get_top_impact_news():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT cn.id, cn.symbol, cn.title, cn.url, cn.source,
                   ns.polarity, ns.impact_score, cn.published_at,
                   p.price as current_price,
                   p2.price as previous_price,
                   (p.price - p2.price) / p2.price * 100 as price_change_pct
            FROM crypto_news cn
            JOIN news_sentiment ns ON cn.id = ns.news_id
            JOIN prices p ON cn.symbol = p.symbol
            JOIN prices p2 ON cn.symbol = p2.symbol
            WHERE p.timestamp = (
                SELECT MAX(timestamp) FROM prices WHERE symbol = cn.symbol
            )
            AND p2.timestamp = (
                SELECT MAX(timestamp) FROM prices
                WHERE symbol = cn.symbol AND timestamp < p.timestamp
            )
            ORDER BY cn.published_at DESC
            LIMIT 20
        """)
        news_data = cursor.fetchall()

        impact_news = []
        for row in news_data:
            news_id, symbol, title, url, source, polarity, impact_score, published_at, current_price, previous_price, price_change_pct = row
            if price_change_pct is None:
                continue

            global_impact = impact_score * (1 + abs(price_change_pct) / 100)
            sentiment = "positif" if polarity > 0.1 else "négatif" if polarity < -0.1 else "neutre"
            price_trend = "hausse" if price_change_pct > 0 else "baisse"
            summary = (
                f"News {sentiment} sur {symbol} avec un impact de {impact_score:.0f}/100. "
                f"La crypto a connu une {price_trend} de {abs(price_change_pct):.2f}% "
                f"après cette news (prix actuel: {current_price:.6f} €)."
            )

            impact_news.append({
                "id": news_id,
                "symbol": symbol,
                "title": title,
                "url": url,
                "source": source,
                "polarity": polarity,
                "impact_score": impact_score,
                "price_change_pct": price_change_pct,
                "global_impact": global_impact,
                "summary": summary,
                "published_at": published_at
            })

        impact_news.sort(key=lambda x: x["global_impact"], reverse=True)
        top_5 = impact_news[:5]
        conn.close()
        return jsonify(top_5)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/refresh")
def refresh_data():
    """Rafraîchit manuellement les données."""
    try:
        init_db()
        fetch_historical_data(days=7)
        fetch_crypto_news_rss(days=7)
        analyze_news_sentiment()
        calculate_rsi()
        calculate_correlations()
        correlate_news_rsi()
        return jsonify({"status": "success", "message": "Données rafraîchies !"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ========== DÉMARRAGE DU SERVEUR ==========
if __name__ == "__main__":
    # 👇 EXÉCUTE LE PEUPLEMENT AVANT DE DÉMARRER FLASK
    print("🚀 Chargement des données...")
    try:
        init_db()
        fetch_historical_data(days=7)
        fetch_crypto_news_rss(days=7)
        analyze_news_sentiment()
        calculate_rsi()
        calculate_correlations()
        correlate_news_rsi()
        print("✅ Données chargées avec succès !")
    except Exception as e:
        print(f"❌ Erreur lors du chargement: {e}")

    # Démarre Flask
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)