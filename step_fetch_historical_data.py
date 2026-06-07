import os 
from db_utils import get_db_connection, get_db_path  # 👈 Importe la fonction
import requests
from datetime import datetime, timedelta
import time
# -*- coding: utf-8 -*-
import sys
import io

# Ajoute ça au début de chaque script (après les imports)
print(f"📁 [SCRIPT] Répertoire courant: {os.getcwd()}")
print(f"📁 [SCRIPT] Chemin de la base: {get_db_path()}")

# Compatibilité Windows/UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

CRYPTOS = {
    "bitcoin": "BTC",
    "ethereum": "ETH",
    "solana": "SOL",
    "aave": "AAVE",
    "ripple": "XRP",
    "vechain": "VET"
}

def fetch_historical_data(days=7):  # 👈 7 jours seulement
    """Récupère les prix quotidiens (avec cache et parallélisation légère)."""
    conn = get_db_connection()  # ✅ Utilise le chemin persistant
    cursor = conn.cursor()

    #DEBUG 
    print(f"📁 Répertoire courant: {os.getcwd()}")
    print(f"📁 Chemin de la base: {get_db_connection().execute('PRAGMA database_list').fetchall()}")
    #DEBUG 

    # Vérifie si les données sont récentes (moins de 1 heure)
    cursor.execute("SELECT MAX(timestamp) FROM prices")
    last_update = cursor.fetchone()[0]
    if last_update:
        last_update = datetime.strptime(last_update, '%Y-%m-%d %H:%M:%S')
        if datetime.now() - last_update < timedelta(hours=1):
            print("⏭️ Données déjà à jour (moins de 1h).")
            conn.close()
            return

    # Supprime les données trop anciennes
    cursor.execute("DELETE FROM prices WHERE timestamp < datetime('now', ?);", (f"-{days} days",))

    for coin_id, symbol in CRYPTOS.items():
        try:
            url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
            params = {"vs_currency": "eur", "days": days, "interval": "daily"}
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if "prices" not in data:
                print(f"❌ Pas de données 'prices' pour {symbol}.")
                continue

            for timestamp_ms, price in data["prices"]:
                timestamp = datetime.fromtimestamp(timestamp_ms / 1000).strftime('%Y-%m-%d %H:%M:%S')
                unique_id = f"{symbol}-{timestamp.replace(' ', '').replace(':', '')}"
                cursor.execute(
                    "INSERT OR IGNORE INTO prices (id, symbol, price, volume, timestamp) VALUES (?, ?, ?, ?, ?)",
                    (unique_id, symbol, price, 0, timestamp)
                )
            print(f"✅ {len(data['prices'])} points récupérés pour {symbol}")
            time.sleep(2)  # 👈 2 secondes au lieu de 5

        except requests.exceptions.RequestException as e:
            print(f"❌ Erreur pour {symbol}: {e}")
        except Exception as e:
            print(f"❌ Erreur inattendue pour {symbol}: {e}")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    fetch_historical_data(days=7)  # 👈 7 jours