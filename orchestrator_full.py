# -*- coding: utf-8 -*-
import sys
import io

# Force UTF-8 pour la console Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import subprocess
import os
import ctypes

def run_script(script_name):
    """Exécute un script Python avec chemins absolus et gestion des erreurs."""
    # Chemin absolu vers le script
    base_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(base_dir, script_name)

    print(f"🔄 Exécution de {script_path}...")  # Affiche le chemin complet

    try:
        result = subprocess.run(
            [sys.executable, "-X", "utf8", script_path],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            timeout=60,
            cwd=base_dir  # 👈 Exécute dans le bon répertoire
        )
        if result.returncode != 0:
            print(f"❌ ERREUR dans {script_name}:")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            return False
        print(f"✅ {script_name} exécuté avec succès")
        return True
    except Exception as e:
        print(f"❌ Exception dans {script_name}: {str(e)}")
        return False

def main():
    # Force UTF-8 pour la console Windows
    if sys.platform == 'win32':
        try:
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleOutputCP(65001)
        except:
            pass  # Ignore si ça échoue

    print("🚀 Démarrage de l'orchestration complète...")
    print(f"📁 Répertoire courant: {os.getcwd()}")  # Debug

    scripts = [
        "step_fetch_historical_data.py",
        "step_fetch_crypto_news_rss.py",
        "step_analyze_news_sentiment.py",
        "step_calculate_rsi.py",
        "step_calculate_correlations.py",
        "step_correlate_news_rsi.py"
    ]

    for script in scripts:
        if not run_script(script):
            print(f"⚠️ Arrêt de l'orchestration à cause de {script}")
            return

    print("✅ Orchestration terminée : toutes les données sont à jour !")

if __name__ == "__main__":
    main()