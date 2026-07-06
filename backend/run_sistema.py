"""
Script standalone dell'attore SISTEMA.

Esegue i controlli temporali di aderenza terapeutica (RF-12/RF-13) una volta.
Pensato per essere schedulato da cron/systemd-timer (RNF-3, monitoraggio 24/7):

    # esempio crontab: ogni ora
    0 * * * * cd /path/backend && ../.venv/bin/python run_sistema.py
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.services.sistema import esegui_controlli


def main():
    db = SessionLocal()
    try:
        risultato = esegui_controlli(db)
        print(f"✅ Controlli eseguiti. Notifiche create: {risultato['notifiche_create']}")
        for riga in risultato["dettaglio"]:
            print(f"   - {riga}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
