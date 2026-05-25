import sys
import os

# Aggiungiamo la cartella corrente al path per evitare problemi di importazione
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import engine
from app.models import Base

def init_database():
    print("⏳ Creazione delle tabelle nel database in corso...")
    try:
        # Questo comando prende l'oggetto Base di models.py e crea fisicamente il DB
        Base.metadata.create_all(bind=engine)
        print("✅ Database 'diabetify.db' creato con successo e tabelle generate!")
    except Exception as e:
        print(f"❌ Errore durante la creazione del database: {e}")

if __name__ == "__main__":
    init_database()