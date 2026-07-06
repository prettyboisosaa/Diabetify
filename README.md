# Diabetify

Sistema di telemedicina per il monitoraggio e la gestione di pazienti affetti da
**diabete di tipo 2**. Il progetto è stato sviluppato per il corso di *Ingegneria del
Software* e realizza l'analisi dei requisiti descritta in [Details.MD](Details.MD),
coprendo i quattro attori del dominio: **Paziente**, **Medico**, **Amministratore** e
**Sistema** (automatismi temporizzati).

## Indice
- [Panoramica](#panoramica)
- [Stack tecnologico](#stack-tecnologico)
- [Funzionalità per attore](#funzionalità-per-attore)
- [Struttura del progetto](#struttura-del-progetto)
- [Prerequisiti](#prerequisiti)
- [Installazione e avvio](#installazione-e-avvio)
- [Test](#test)
- [Credenziali di prova](#credenziali-di-prova)
- [Documentazione](#documentazione)
- [Note e limiti](#note-e-limiti)

## Panoramica

L'applicazione permette al paziente di registrare i propri parametri clinici (glicemie,
sintomi, assunzione di farmaci) e di comunicare con il proprio medico; al medico di
consultare i dati, gestire le terapie e aggiornare la scheda clinica; all'amministratore
di inserire gli utenti iniziali e le associazioni paziente–medico. Un componente di
sistema esegue controlli automatici (coerenza terapeutica, solleciti e alert) secondo le
regole cliniche di dominio.

L'accesso è protetto da autenticazione con token JWT e differenziato per ruolo.

## Stack tecnologico

| Livello | Tecnologie |
|---------|-----------|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2, SQLite, PyJWT, passlib/bcrypt |
| Frontend | React 19, TypeScript, Vite, React Router, CSS Modules |
| Test | `unittest` (libreria standard di Python) |

## Funzionalità per attore

- **Paziente** — registrazione glicemie (RF-4), diario di sintomi/patologie/terapie
  parallele (RF-5), registrazione assunzioni (RF-6), messaggi al medico (RF-7),
  consultazione dei propri dati e degli avvisi. Dettagli in [Paziente.md](Paziente.md).
- **Medico** — gestione terapie (RF-8), visualizzazione dati clinici in dettaglio e
  aggregati (RF-9), aggiornamento anamnesi (RF-10), lettura di alert e messaggi, con
  tracciamento delle operazioni (RF-15). Dettagli in [Medico.md](Medico.md).
- **Amministratore** — inserimento utenti iniziali (RF-2), associazione paziente–medico
  (RF-3), consultazione del registro audit (RF-15). Dettagli in [Admin.md](Admin.md).
- **Sistema** — verifica di coerenza terapeutica (RF-11), solleciti (RF-12), alert di
  mancata aderenza (RF-13) e di glicemia fuori soglia (RF-14). Dettagli in
  [Sistema.md](Sistema.md).

## Struttura del progetto

```
Diabetify/
├── README.md                  # questo file
├── Details.MD                 # specifica dei requisiti (RF/RNF/UC)
├── Medico.md · Paziente.md · Admin.md · Sistema.md
├── file_details.md            # descrizione di ogni singolo file
├── requirements.txt           # dipendenze Python
├── backend/                   # API FastAPI + logica + test
│   ├── main.py · init_db.py · seed.py · run_sistema.py
│   └── app/  (models, schemas, security, dependencies, routers/, services/)
└── frontend/                  # applicazione React
    └── src/  (lib/, components/, styles/, pages/)
```

La descrizione puntuale di ciascun file è in [file_details.md](file_details.md).

## Prerequisiti

- **Python 3.12** (o versione compatibile 3.11+)
- **Node.js 20+** e **npm** (per Vite 8)

## Installazione e avvio

Il backend e il frontend sono due processi separati.

### 1. Backend

```bash
# dalla cartella radice del progetto
python -m venv .venv
source .venv/bin/activate            # su Windows: .venv\Scripts\activate
pip install -r requirements.txt

cd backend
python init_db.py                    # crea il database SQLite
python seed.py                       # inserisce utenti e dati di esempio
uvicorn main:app --reload            # avvia l'API su http://localhost:8000
```

La documentazione interattiva dell'API (Swagger) è disponibile su
`http://localhost:8000/docs`.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev                          # avvia l'app su http://localhost:5173
```

## Test

La suite di test copre le singole funzionalità del backend (logica di dominio, servizi,
schemi e regole di autorizzazione) usando un database SQLite in memoria.

```bash
cd backend
python -m unittest discover -s tests -t . -v
```

Sono presenti **39 test**, organizzati per attore (`tests/test_*.py`). Maggiori dettagli
nella sezione dedicata di [file_details.md](file_details.md).

## Credenziali di prova

Create dallo script `seed.py`:

| Ruolo | Email | Password |
|-------|-------|----------|
| Amministratore | `admin@diabetify.it` | `Admin2026!` |
| Medico | `dottore@diabetify.it` | `Medico2026!` |
| Paziente | `paziente@diabetify.it` | `Paziente2026!` |

## Documentazione

| Documento | Contenuto |
|-----------|-----------|
| [Details.MD](Details.MD) | Specifica dei requisiti (attori, RF, RNF, casi d'uso) |
| [Medico.md](Medico.md) | Attore Medico: scelte, endpoint, interfaccia |
| [Paziente.md](Paziente.md) | Attore Paziente |
| [Admin.md](Admin.md) | Attore Amministratore |
| [Sistema.md](Sistema.md) | Attore Sistema (automatismi) |
| [file_details.md](file_details.md) | Descrizione di ogni file del progetto |

## Note e limiti

- Le comunicazioni "via email" previste dai requisiti (RF-7, RF-13, RF-14) sono
  realizzate come **notifiche e messaggi in-app**, senza invio SMTP reale.
- Il monitoraggio continuo richiesto da RNF-3 è ottenuto con lo script
  `backend/run_sistema.py`, pensato per essere schedulato (es. cron); nel prototipo i
  controlli sono anche avviabili manualmente dall'amministratore.
- Trattandosi di un progetto didattico, la chiave di firma dei token è definita nel
  codice: in un contesto reale andrebbe spostata in una variabile d'ambiente.
