from flask import Flask, render_template, jsonify
import sqlite3
from datetime import datetime
import subprocess
import os
import sys

app = Flask(__name__)

# ========== FONCTIONS DE RÉCUPÉRATION DES DONNÉES (AVEC GESTION DES ERREURS) ==========
def get_prices():
    """Récupère les derniers prix (1 par crypto)."""
    try:
        conn = sqlite3.connect("crypto.db")
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
    """Récupère les derniers RSI (1 par crypto)."""
    try:
        conn = sqlite3.connect("crypto.db")
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
    """Récupère les corrélations avec BTC (sans doublons)."""
    try:
        conn = sqlite3.connect("crypto.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT symbol1, correlation, timeframe
            FROM correlations
            WHERE symbol2 = 'BTC'
            GROUP BY symbol1  -- Évite les doublons
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
    """Récupère les news + sentiment pour le dashboard."""
    try:
        conn = sqlite3.connect("crypto.db")
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
    """Récupère les corrélations news/RSI (sans doublons, 1 entrée par crypto)."""
    try:
        conn = sqlite3.connect("crypto.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT symbol, avg_polarity, avg_impact, rsi, correlation, sentiment_trend
            FROM news_rsi_correlation
            GROUP BY symbol  -- Évite les doublons
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
    """Récupère l'historique des prix pour une crypto (7 derniers jours)."""
    try:
        conn = sqlite3.connect("crypto.db")
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
            "labels": [row[0][:16] for row in reversed(data)],  # YYYY-MM-DD HH:MM
            "data": [row[1] for row in reversed(data)]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/rsi/<symbol>")
def get_rsi_history(symbol):
    """Récupère l'historique du RSI pour une crypto (7 derniers jours)."""
    try:
        conn = sqlite3.connect("crypto.db")
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
            "labels": [row[0][:16] for row in reversed(data)],  # YYYY-MM-DD HH:MM
            "data": [row[1] for row in reversed(data)]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/news_sentiment/<symbol>")
def get_news_sentiment_history(symbol):
    """Récupère l'historique du sentiment des news pour une crypto (7 derniers jours)."""
    try:
        conn = sqlite3.connect("crypto.db")
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
            "labels": [row[0][:16] for row in reversed(data)],  # YYYY-MM-DD HH:MM
            "polarity": [row[1] for row in reversed(data)],
            "impact": [row[2] for row in reversed(data)]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/top_impact_news")
def get_top_impact_news():
    """Récupère les 5 news les plus impactantes (toutes cryptos) avec un résumé."""
    try:
        conn = sqlite3.connect("crypto.db")
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
    """Relance l'orchestrateur et rafraîchit les données."""
    try:
        script_path = os.path.join(os.path.dirname(__file__), "orchestrator_full.py")
        print(f"🔄 Exécution de l'orchestrateur: {script_path}")  # Debug

        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            timeout=60,
            cwd=os.path.dirname(__file__)  # 👈 Exécute dans le bon répertoire
        )

        print(f"📝 Sortie: {result.stdout}")  # Debug
        print(f"❌ Erreurs: {result.stderr}")  # Debug

        if result.returncode == 0:
            return jsonify({
                "status": "success",
                "message": "Données rafraîchies avec succès !",
                "output": result.stdout
            })
        else:
            return jsonify({
                "status": "error",
                "message": f"Erreur dans l'orchestrateur (code {result.returncode})",
                "stdout": result.stdout,
                "stderr": result.stderr
            }), 500

    except subprocess.TimeoutExpired:
        return jsonify({
            "status": "error",
            "message": "Timeout: l'orchestrateur a mis trop de temps (>60s)"
        }), 500
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Erreur inattendue: {str(e)}"
        }), 500

if __name__ == "__main__":
    #local
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
    # online
    gunicorn_app = app