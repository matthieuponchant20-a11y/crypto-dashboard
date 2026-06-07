import sqlite3
import os
import platform

# ✅ Chemin adaptatif : /tmp sur Render (Linux), .\ sur Windows
def get_db_path():
    if platform.system() == 'Linux':  # Render est sur Linux
        return os.path.join('/tmp', 'crypto.db')
    else:  # Windows ou macOS en local
        return os.path.join(os.getcwd(), 'crypto.db')  # 👈 Dans le dossier du projet

def get_db_connection():
    """Retourne une connexion à la base de données (chemin adaptatif)."""
    db_path = get_db_path()
    # Crée le dossier /tmp si nécessaire (sur Linux)
    if platform.system() == 'Linux':
        os.makedirs('/tmp', exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn