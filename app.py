from flask import Flask, render_template, jsonify
from datetime import datetime
import subprocess
import os
import sys
from db_utils import get_db_connection, get_db_path  # 👈 Ajoute get_db_path
from init_db import init_db

app = Flask(__name__)

# ========== INITIALISATION DE LA BASE ==========
init_db()  # Crée les tables

# ========== FONCTIONS DE RÉCUPÉRATION DES DONNÉES ==========
def get_prices():
    """Récupère les derniers prix (1 par crypto)."""
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
    """Récupère les derniers RSI (1 par crypto)."""
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
    """Récupère les corrélations avec BTC."""
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
    """Récupère les news + sentiment."""
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
    """Récupère les corrélations news/RSI."""
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
    """Relance l'orchestrateur manuellement."""
    try:
        script_path = os.path.join(os.path.dirname(__file__), "orchestrator_full.py")
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            timeout=60,
            cwd=os.path.dirname(__file__)
        )

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

@app.route("/debug/db")
def debug_db():
    """Affiche le contenu de la base pour le débogage (compatible JSON)."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Liste des tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [table[0] for table in cursor.fetchall()]

        results = {}
        for table in tables:
            # Compte les lignes
            cursor.execute(f"SELECT COUNT(*) FROM {table};")
            count = cursor.fetchone()[0]

            # Récupère les noms des colonnes
            cursor.execute(f"PRAGMA table_info({table});")
            columns = [col[1] for col in cursor.fetchall()]  # Noms des colonnes

            # Échantillon de données (converti en dict)
            sample = []
            if count > 0:
                cursor.execute(f"SELECT * FROM {table} LIMIT 2;")
                for row in cursor.fetchall():
                    # Convertit sqlite3.Row en dict
                    sample.append(dict(zip(columns, row)))

            results[table] = {
                "count": count,
                "columns": columns,
                "sample": sample  # 👈 Maintenant en format JSON
            }

        conn.close()
        return jsonify(results)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/debug/path")
def debug_path():
    """Affiche le chemin de la base et son statut pour le débogage."""
    db_path = get_db_path()
    return jsonify({
        "db_path": db_path,  # Chemin absolu de la base
        "cwd": os.getcwd(),  # Répertoire courant du processus
        "db_exists": os.path.exists(db_path),  # La base existe-t-elle ?
        "db_size": os.path.getsize(db_path) if os.path.exists(db_path) else 0  # Taille en octets
    })

# ========== DÉMARRAGE DU SERVEUR ==========
if __name__ == "__main__":
    # 👇 VÉRIFIE LE CHEMIN AVANT DE DÉMARRER
    print(f"📁 Répertoire courant: {os.getcwd()}")
    print(f"📁 Chemin de la base: {get_db_path()}")

    # Exécute l'orchestrateur
    print("🚀 Exécution de l'orchestrateur...")
    script_path = os.path.join(os.path.dirname(__file__), "orchestrator_full.py")

    result = subprocess.run(
        [sys.executable, script_path],
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='ignore',
        timeout=120,
        cwd=os.path.dirname(__file__)  # 👈 Force le répertoire
    )

    # 👇 AFFICHE LES LOGS DE L'ORCHESTRATEUR
    print(f"📝 Sortie orchestrateur:\n{result.stdout}")
    if result.stderr:
        print(f"❌ Erreurs orchestrateur:\n{result.stderr}")

    # 👇 VÉRIFIE QUE LA BASE EST REMPLIE
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [table[0] for table in cursor.fetchall()]
    print(f"📊 Tables dans la base: {tables}")

    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table};")
        count = cursor.fetchone()[0]
        print(f"📌 {table}: {count} lignes")  # 👈 Doit afficher > 0 !
    conn.close()

    # Démarre Flask
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)