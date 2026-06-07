import sqlite3
import os

# ✅ Chemin RELATIF au projet (persistant sur Render et en local)
DB_PATH = "crypto.db"  # Fichier dans le même dossier que app.py

def get_db_path():
    """Retourne le chemin absolu de la base de données."""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), DB_PATH)

def get_db_connection():
    """Retourne une connexion à la base de données."""
    db_path = get_db_path()
    # Crée le fichier s'il n'existe pas
    if not os.path.exists(db_path):
        open(db_path, 'a').close()  # Crée un fichier vide
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn