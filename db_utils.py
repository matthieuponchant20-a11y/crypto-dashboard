import sqlite3
import os

# ✅ Chemin ABSOLU pour Render (persistant)
DB_PATH = "/tmp/crypto.db"  # Sur Render, /tmp est persistant

def get_db_connection():
    """Retourne une connexion à la base de données."""
    # Crée /tmp si nécessaire
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn