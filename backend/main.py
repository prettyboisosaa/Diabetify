from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, medico, paziente, admin, sistema

app = FastAPI(title="Diabetify API - Telemedicina")

# Configurazione CORS per permettere a React di comunicare con FastAPI
origins = [
    "http://localhost:5173",  # Porta standard di Vite/React
    "http://127.0.0.1:5173",
    "null",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],  # Permette tutti i metodi (GET, POST, PUT, DELETE)
    allow_headers=["*"],  # Permette tutti gli header (compresi quelli di autorizzazione)
)

# Inclusione delle rotte di autenticazione e dei quattro attori
app.include_router(auth.router)
app.include_router(medico.router)
app.include_router(paziente.router)
app.include_router(admin.router)
app.include_router(sistema.router)

@app.get("/")
def read_root():
    return {"status": "online", "message": "Diabetify API perfettamente funzionante"}