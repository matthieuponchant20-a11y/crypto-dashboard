import sqlite3
import os

# ✅ Chemin RELATIF au projet (persistant sur Render)
DB_PATH = "crypto.db"  # 👈 Fichier dans le même dossier que app.py

def get_db_connection():
    """Retourne une connexion à la base de données (chemin relatif)."""
    # Crée le fichier s'il n'existe pas
    if not os.path.exists(DB_PATH):
        open(DB_PATH, 'a').close()  # Crée un fichier vide
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn