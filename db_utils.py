import sqlite3
import os

# ✅ Chemin RELATIF au projet (persistant sur Render)
DB_PATH = "crypto.db"

def get_db_connection():
    """Retourne une connexion à la base de données."""
    if not os.path.exists(DB_PATH):
        open(DB_PATH, 'a').close()  # Crée le fichier s'il n'existe pas
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn