from db_utils import get_db_connection
import requests
from datetime import datetime, timedelta
import time

CRYPTOS = {
    "bitcoin": "BTC",
    "ethereum": "ETH",
    "solana": "SOL",
    "aave": "AAVE",
    "ripple": "XRP",
    "vechain": "VET"
}

def fetch_historical_data(days=7):
    """Récupère les prix ACTUELS + historiques depuis CoinGecko."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1️⃣ NETTOIE LES ANCIENNES DONNÉES (>7 jours)
    cursor.execute("DELETE FROM prices WHERE timestamp < datetime('now', '-7 days')")

    # 2️⃣ VÉRIFIE SI LES DONNÉES SONT RÉCENTES (15 min au lieu de 1h)
    cursor.execute("SELECT MAX(timestamp) FROM prices")
    last_update = cursor.fetchone()[0]

    if last_update:
        try:
            last_update = datetime.strptime(last_update, '%Y-%m-%d %H:%M:%S')
            if datetime.now() - last_update < timedelta(minutes=15):
                print("⏭️ Données déjà à jour (moins de 15 min).")
                conn.close()
                return
        except (ValueError, TypeError):
            pass  # Si la date est invalide, on continue

    # 3️⃣ RÉCUPÈRE LES PRIX ACTUELS (1 requête pour TOUTES les cryptos)
    try:
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            "vs_currency": "eur",
            "ids": "bitcoin,ethereum,solana,aave,ripple,vechain",
        }
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        current_data = response.json()

        for coin in current_data:
            symbol = coin["symbol"].upper()
            if symbol in CRYPTOS.values():
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                unique_id = f"{symbol}-current-{timestamp.replace(' ', '').replace(':', '')}"
                cursor.execute(
                    "INSERT OR REPLACE INTO prices (id, symbol, price, volume, timestamp) VALUES (?, ?, ?, ?, ?)",
                    (unique_id, symbol, coin["current_price"], 0, timestamp)  # 👈 Ajoute 0 pour volume
                )
                print(f"✅ Prix ACTUEL pour {symbol}: {coin['current_price']} €")

    except Exception as e:
        print(f"❌ Erreur prix actuels: {e}")

    # 4️⃣ RÉCUPÈRE L'HISTORIQUE (avec gestion des 429)
    for coin_id, symbol in CRYPTOS.items():
        try:
            url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
            params = {"vs_currency": "eur", "days": days, "interval": "daily"}

            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = requests.get(url, params=params, timeout=15)
                    if response.status_code == 429:  # Too Many Requests
                        retry_after = int(response.headers.get("Retry-After", 60))
                        print(f"⚠️ Rate limit pour {symbol}. Attente de {retry_after}s...")
                        time.sleep(retry_after)
                        continue
                    response.raise_for_status()
                    break
                except requests.exceptions.RequestException:
                    if attempt == max_retries - 1:
                        raise
                    time.sleep(12)

            data = response.json()
            if "prices" not in data:
                print(f"❌ Pas de données historiques pour {symbol}.")
                continue

            for timestamp_ms, price in data["prices"]:
                timestamp = datetime.fromtimestamp(timestamp_ms / 1000).strftime('%Y-%m-%d %H:%M:%S')
                unique_id = f"{symbol}-{timestamp.replace(' ', '').replace(':', '')}"
                cursor.execute(
                    "INSERT OR IGNORE INTO prices (id, symbol, price, volume, timestamp) VALUES (?, ?, ?, ?, ?)",
                    (unique_id, symbol, price, 0, timestamp)  # 👈 Ajoute 0 pour volume
                )
            print(f"✅ {len(data['prices'])} points historiques pour {symbol}")
            time.sleep(12)  # Délai entre les requêtes

        except Exception as e:
            print(f"❌ Erreur pour {symbol}: {e}")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    fetch_historical_data(days=7)