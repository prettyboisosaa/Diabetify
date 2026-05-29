from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Il database sarà un singolo file chiamato "diabetify.db" nella root del backend
SQLALCHEMY_DATABASE_URL = "sqlite:///./diabetify.db"

# create_engine si occupa della connessione fisica
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}  # Necessario solo per SQLite in ambienti async
)

# Questa è la fabbrica delle sessioni (le transazioni per leggere/scrivere)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Questa funzione (Dependency) serve a FastAPI per darti una sessione pulita a ogni chiamata API
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()