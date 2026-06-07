import sqlite3
import os

# ✅ Chemin ABSOLU (même pour tous les processus)
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "crypto.db")

def get_db_path():
    """Retourne le chemin ABSOLU de la base."""
    return DB_PATH

def get_db_connection():
    """Retourne une connexion à la base."""
    db_path = get_db_path()
    # Crée le fichier s'il n'existe pas
    if not os.path.exists(db_path):
        open(db_path, 'a').close()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn