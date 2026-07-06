# Review del progetto

> **Progetto:** Diabetify — Sistema di telemedicina per la gestione del diabete di tipo 2
> **Contesto:** Progetto universitario (Ingegneria del Software, Università di Verona)
> **Data review:** 2026-07-03

---

## Panoramica

### Scopo del progetto
Diabetify è una piattaforma di **telemedicina** pensata per il monitoraggio continuo dei pazienti affetti da **diabete di tipo 2** e la collaborazione con il personale medico. Gli obiettivi funzionali completi sono definiti nei documenti [README.MD](README.MD) e [Details.MD](Details.MD), che elencano attori, requisiti funzionali (RF-1…RF-15), requisiti non funzionali (RNF-1…RNF-3) e casi d'uso (UC-1…UC-14).

Il sistema prevede tre attori umani — **Paziente**, **Diabetologo/Medico**, **Responsabile del servizio (Admin)** — più un **attore di sistema** temporizzato per gli automatismi (alert, solleciti, controlli di aderenza).

### Tecnologie principali
- **Backend:** Python, **FastAPI**, **SQLAlchemy 2.0** (ORM), **SQLite** come database, **Pydantic v2** per la validazione, **PyJWT** + **passlib/bcrypt** per autenticazione e hashing password.
- **Frontend:** **React 19**, **TypeScript**, **Vite** come build tool, **react-router-dom v7** per il routing.
- **Comunicazione:** REST/JSON tra frontend (`http://localhost:5173`) e backend (`http://localhost:8000`).

### Tipo di applicazione
Applicazione web **full-stack client-server**, composta da una **SPA React** (client) e una **API REST FastAPI** (server) con persistenza su file SQLite. Al momento il progetto è a uno stadio di **MVP iniziale**: sono presenti l'infrastruttura completa e il flusso di autenticazione, mentre la maggior parte delle funzionalità di dominio è modellata ma non ancora esposta via API.

---

## Struttura del repository

```
Diabetify/
├── README.MD                  # Descrizione progetto + istruzioni di avvio
├── Details.MD                 # Analisi requisiti: attori, RF/RNF, casi d'uso
├── .gitignore                 # Ignora node_modules, venv, db, requirements.txt (root)
├── requirements.txt           # (generato da questa review) dipendenze Python complete
├── review.md                  # (questo documento)
│
├── backend/
│   ├── main.py                # Entrypoint FastAPI: app, CORS, include router auth
│   ├── requirements.txt        # Manifest dipendenze backend (INCOMPLETO, vedi §Problemi)
│   ├── init_db.py             # Script: crea le tabelle nel DB SQLite
│   ├── seed.py                # Script: popola 3 utenti demo (admin/medico/paziente)
│   ├── diabetify.db           # Database SQLite (versionato nel repo)
│   └── app/
│       ├── database.py        # Engine SQLAlchemy, SessionLocal, dependency get_db
│       ├── models.py          # Modelli ORM (tutte le entità di dominio)
│       ├── schemas.py         # Schemi Pydantic (validazione I/O, mappati sui RF)
│       └── routers/
│           └── auth.py        # Endpoint POST /login (JWT)
│
└── frontend/
    ├── package.json           # Dipendenze e script npm (dev, build, lint, preview)
    ├── vite.config.ts         # Config Vite con plugin React
    ├── index.html             # HTML root della SPA
    ├── tsconfig*.json         # Configurazioni TypeScript
    ├── eslint.config.js       # Configurazione ESLint
    └── src/
        ├── main.tsx           # Bootstrap React (createRoot)
        ├── App.tsx            # Definizione delle route
        ├── index.css / styles/theme.css
        ├── lib/auth.ts        # Client login + gestione token/ruolo in localStorage
        ├── components/
        │   └── ProtectedRoute.tsx   # Guardia di rotta basata sul ruolo
        └── pages/
            ├── Login.tsx + Login.module.css   # Pagina di login (completa)
            ├── DoctorHome.tsx    # Placeholder (7 righe)
            ├── PatientHome.tsx   # Placeholder (7 righe)
            └── AdminHome.tsx     # Placeholder (7 righe)
```

### File più importanti
- [backend/app/models.py](backend/app/models.py) — cuore del dominio: definisce tutte le entità e le relazioni.
- [backend/app/schemas.py](backend/app/schemas.py) — contratto dati dell'API, con validazioni e mappatura esplicita ai requisiti.
- [backend/app/routers/auth.py](backend/app/routers/auth.py) — unico endpoint operativo oltre alla root.
- [frontend/src/App.tsx](frontend/src/App.tsx) e [frontend/src/lib/auth.ts](frontend/src/lib/auth.ts) — routing per ruolo e logica di autenticazione lato client.

---

## Architettura e flusso

### Organizzazione del backend
Il backend segue un'architettura **a livelli** tipica di FastAPI:

1. **Livello dati / ORM** ([database.py](backend/app/database.py), [models.py](backend/app/models.py)) — `create_engine` su `sqlite:///./diabetify.db` con `check_same_thread=False`; `SessionLocal` come factory di sessioni; `get_db()` è la *dependency* che fornisce una sessione per richiesta.
2. **Livello di validazione / contratto** ([schemas.py](backend/app/schemas.py)) — schemi Pydantic v2 con `ConfigDict(from_attributes=True, use_enum_values=True)` per serializzare gli oggetti ORM, validatori riusabili (es. complessità password, coerenza `data_fine ≥ data_inizio`) e `computed_field` per la logica di dominio (es. `fuori_soglia` sulla glicemia).
3. **Livello di presentazione / routing** ([routers/auth.py](backend/app/routers/auth.py), [main.py](backend/main.py)) — router FastAPI inclusi nell'app principale.

### Componenti principali del modello dati
[models.py](backend/app/models.py) definisce un modello ricco e coerente con i requisiti:
- **`User`** — credenziali ed `email`, `password_hash`, `role` (enum `admin`/`doctor`/`patient`), `is_active`.
- **`DoctorProfile`** / **`PatientProfile`** — anagrafiche; il paziente ha `doctor_id` (RF-3, associazione paziente-medico) e i campi di anamnesi `fattori_rischio`, `patologie_pregresse`, `comorbita` (RF-10).
- **`RilevazioneGlicemica`** — valore in mg/dL e `momento` prima/dopo pasto (RF-4).
- **`Terapia`** / **`Assunzione`** — prescrizione medica e assunzione dichiarata dal paziente, con tipi numerici allineati per il confronto di aderenza (RF-6, RF-8, RF-11).
- **`Sintomo`**, **`PatologiaConcomitante`**, **`TerapiaParallela`** — dati clinici accessori con periodo di validità (RF-5).
- **`Messaggio`** — comunicazione paziente↔medico (RF-7).
- **`Notifica`** — alert di sistema con `tipo` e `severita` (RF-12, RF-13, RF-14).
- **`AuditLog`** — tracciabilità delle operazioni dei medici (RF-15).

### Come comunicano i componenti
1. Il frontend invia le credenziali in **form-urlencoded** (`username`+`password`) a `POST /login` — vedi [auth.ts](frontend/src/lib/auth.ts).
2. Il backend verifica l'utente, controlla la password con bcrypt e restituisce un **JWT** firmato (HS256) contenente `sub`, `id`, `role`, `exp` — vedi [auth.py](backend/app/routers/auth.py).
3. Il client memorizza `access_token` e `role` in `localStorage` e reindirizza alla home del ruolo.
4. `ProtectedRoute` legge il ruolo da `localStorage` per autorizzare l'accesso alle rotte `/doctor`, `/patient`, `/admin`.

### Entrypoint e punti di esecuzione
- **Backend:** `uvicorn main:app` — l'oggetto `app` è in [backend/main.py](backend/main.py). Documentazione interattiva automatica su `/docs` (Swagger) e `/redoc`.
- **Frontend:** [frontend/src/main.tsx](frontend/src/main.tsx) monta `<App />` tramite `createRoot`; dev server avviato con `npm run dev` (Vite).
- **Script di supporto:** [init_db.py](backend/init_db.py) crea le tabelle, [seed.py](backend/seed.py) inserisce gli utenti demo.

---

## Dipendenze

### Backend (runtime)
Librerie principali effettivamente utilizzate dal codice:

| Libreria | Uso |
|---|---|
| `fastapi` | Framework API, routing, dependency injection |
| `uvicorn` | Server ASGI di esecuzione |
| `SQLAlchemy` | ORM e accesso al database |
| `pydantic` / `pydantic_core` | Validazione e serializzazione degli schemi |
| `email-validator` (+ `dnspython`) | Validazione del tipo `EmailStr` in `schemas.py` |
| `PyJWT` | Firma/decodifica del JWT (`import jwt` in `auth.py`) |
| `passlib` + `bcrypt` | Hashing e verifica delle password |
| `python-multipart` | Parsing del form-data richiesto da `OAuth2PasswordRequestForm` |
| `starlette`, `anyio`, `h11`, `click`, `idna`, `typing_extensions`, ecc. | Dipendenze transitive di FastAPI/Uvicorn |

> **Nota importante:** il manifest esistente [backend/requirements.txt](backend/requirements.txt) **non include** `PyJWT`, `passlib`, `bcrypt` e `python-multipart`, benché siano indispensabili all'esecuzione (vedi §Problemi). Il file [requirements.txt](requirements.txt) alla root, generato con questa review, le aggiunge.

### Frontend (runtime)
Da [frontend/package.json](frontend/package.json):
- `react` ^19.2.6, `react-dom` ^19.2.6 — libreria UI.
- `react-router-dom` ^7.16.0 — routing SPA.

### Frontend (sviluppo)
Strumenti di sviluppo, non necessari in produzione: `vite`, `@vitejs/plugin-react`, `typescript`, `typescript-eslint`, `eslint` + plugin (`eslint-plugin-react-hooks`, `eslint-plugin-react-refresh`), `@types/*`, `globals`.

### Dipendenze opzionali
- **`VITE_API_URL`** (variabile d'ambiente, non una dipendenza pacchetto) — consente di puntare il frontend a un backend diverso da `http://localhost:8000`.

---

## Come si avvia

### Prerequisiti
- **Python 3.9+** (il codice usa `datetime.timezone`, type hints moderni; `exceptiongroup` è richiesto per Python < 3.11).
- **Node.js 20+** e **npm** per il frontend.

### Backend
Dalla cartella `backend/` (consigliato un virtual environment):

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: .\venv\Scripts\Activate.ps1

# installa le dipendenze (usare il requirements.txt completo alla root del progetto)
pip install -r ../requirements.txt

python init_db.py               # crea le tabelle in diabetify.db
python seed.py                  # popola gli utenti demo
uvicorn main:app --reload       # avvia l'API su http://localhost:8000
```

Documentazione interattiva: `http://localhost:8000/docs`.

**Credenziali demo** (da [seed.py](backend/seed.py)):

| Ruolo | Email | Password |
|---|---|---|
| Admin | `admin@diabetify.it` | `Admin2026!` |
| Medico | `dottore@diabetify.it` | `Medico2026!` |
| Paziente | `paziente@diabetify.it` | `Paziente2026!` |

> Il database `diabetify.db` è già presente nel repository, quindi `init_db.py`/`seed.py` sono necessari solo per ricostruirlo da zero.

### Frontend
Dalla cartella `frontend/`:

```bash
cd frontend
npm install
npm run dev                     # dev server su http://localhost:5173
```

Build di produzione: `npm run build` (esegue `tsc -b && vite build`), anteprima con `npm run preview`.

### Variabili d'ambiente
- `VITE_API_URL` (frontend, opzionale) — URL del backend; default `http://localhost:8000`. Si imposta in `frontend/.env.local`.

---

## Analisi del codice

### Backend

**[backend/main.py](backend/main.py)** — Crea l'istanza `FastAPI`, configura il middleware CORS e include il router di autenticazione. Espone `GET /` come health-check. *Nota:* la lista `origins` (localhost:5173, ecc.) è definita ma **non usata**: il middleware imposta `allow_origins=["*"]` (vedi §Problemi).

**[backend/app/database.py](backend/app/database.py)** — Configura l'engine SQLAlchemy su SQLite, la factory `SessionLocal` e la dependency `get_db()` con pattern `yield`/`finally` per la chiusura pulita della sessione. Definisce anche un `declarative_base()` che però **non è usato** (i modelli usano il `Base` dichiarato in `models.py`).

**[backend/app/models.py](backend/app/models.py)** — Definisce il proprio `Base` e tutte le entità di dominio con le rispettive relazioni SQLAlchemy (`relationship`, `back_populates`, chiavi esterne). Sono presenti enum tipizzati (`UserRole`, `MomentoGlicemia`, `UnitaMisura`, `GravitaSintomo`, `TipoNotifica`, `SeveritaNotifica`). Il modello copre l'intero spettro dei requisiti, incluse le entità per gli automatismi (`Notifica`) e la tracciabilità (`AuditLog`).

**[backend/app/schemas.py](backend/app/schemas.py)** — Livello di contratto molto curato:
- Base comune `ORMBase` con `from_attributes` e `use_enum_values`.
- Validatori riusabili: complessità password (min 12 caratteri, maiuscola/minuscola/cifra/carattere speciale), coerenza `data_fine ≥ data_inizio`.
- Separazione tra schemi di *creazione*, *update* e *response* per ogni entità.
- Logica di dominio incapsulata: costanti soglie glicemiche (RNF-1: 80–130 prima pasto, ≤180 dopo pasto) e `computed_field fuori_soglia`.
- Schemi compositi (`UserWithProfileResponse`, `RegistrazionePazienteRequest`) per ridurre i round-trip.
- Ogni sezione è commentata con il requisito di riferimento (RF-x), a testimonianza di un design guidato dai requisiti.

**[backend/app/routers/auth.py](backend/app/routers/auth.py)** — Implementa `POST /login` seguendo lo standard OAuth2 (`OAuth2PasswordRequestForm`): cerca l'utente per email, verifica la password con `passlib`/bcrypt, controlla `is_active`, genera un JWT HS256 con scadenza a 120 minuti. La `SECRET_KEY` è hardcoded (accettabile per un progetto d'esame, ma da spostare in `.env` — vedi §Problemi).

**[backend/init_db.py](backend/init_db.py)** e **[backend/seed.py](backend/seed.py)** — Script eseguibili standalone; entrambi manipolano `sys.path` per risolvere gli import. `seed.py` è idempotente (controlla l'esistenza dell'utente prima di inserirlo) e usa `db.flush()` per ottenere gli ID prima del commit, associando il paziente al medico (RF-3).

### Frontend

**[frontend/src/App.tsx](frontend/src/App.tsx)** — Definisce le rotte con `BrowserRouter`. `RootRedirect` instrada l'utente autenticato alla home del suo ruolo, altrimenti a `/login`. Le rotte protette sono avvolte in `ProtectedRoute`.

**[frontend/src/lib/auth.ts](frontend/src/lib/auth.ts)** — Client di autenticazione: invia le credenziali come `x-www-form-urlencoded`, memorizza token e ruolo in `localStorage`, ed espone helper `getToken`, `getRole`, `isAuthenticated`, `logout`.

**[frontend/src/components/ProtectedRoute.tsx](frontend/src/components/ProtectedRoute.tsx)** — Guardia di rotta: reindirizza al login se non autenticato e alla home corretta se il ruolo non corrisponde. La verifica è **solo lato client** (legge `localStorage`), quindi non costituisce una vera autorizzazione di sicurezza.

**[frontend/src/pages/Login.tsx](frontend/src/pages/Login.tsx)** — Pagina di login completa e curata dal punto di vista UX/accessibilità: markup semantico (`<main>`, `<form>`, `<label>` associati), stati di submit, gestione errori con `role="alert"`, disabilitazione del pulsante durante l'invio. Stili isolati via CSS Module.

**[frontend/src/pages/DoctorHome.tsx](frontend/src/pages/DoctorHome.tsx), [PatientHome.tsx](frontend/src/pages/PatientHome.tsx), [AdminHome.tsx](frontend/src/pages/AdminHome.tsx)** — **Placeholder** di 7 righe ciascuno (`<h1>Sei un dottore</h1>`, ecc.). Le funzionalità di dominio lato client non sono ancora implementate.

### Pattern e scelte architetturali evidenti
- **Design guidato dai requisiti:** schemi ed entità commentati con i codici RF/RNF, mappatura 1:1 con [Details.MD](Details.MD).
- **Separazione netta model/schema/router** nel backend.
- **Autenticazione stateless** basata su JWT e routing per ruolo lato client.
- **Autenticazione OAuth2 standard** compatibile con Swagger UI.

---

## Problemi o punti da migliorare

### Bug / blocchi all'esecuzione
1. **[CRITICO] Dipendenze mancanti nel manifest.** [backend/requirements.txt](backend/requirements.txt) non elenca `PyJWT`, `passlib`, `bcrypt` e `python-multipart`, tutte usate/necessarie a [auth.py](backend/app/routers/auth.py):
   - `import jwt` → richiede **PyJWT**;
   - `from passlib.context import CryptContext` con schema `bcrypt` → richiede **passlib** e **bcrypt**;
   - `OAuth2PasswordRequestForm` → FastAPI richiede **python-multipart** per il parsing del form, altrimenti l'endpoint solleva un errore all'avvio.

   Installando solo il manifest esistente, l'app **non parte** o il login **fallisce**. Il file [requirements.txt](requirements.txt) generato con questa review risolve il problema.

2. **CORS incoerente / non sicuro.** In [main.py](backend/main.py) la lista `origins` è definita ma ignorata: il middleware usa `allow_origins=["*"]` **insieme** a `allow_credentials=True`. Questa combinazione è rifiutata dai browser (con credenziali non è ammesso il wildcard) e, in produzione, è troppo permissiva. Va usata la lista esplicita `origins`.

### Debolezze strutturali / di sicurezza
3. **`SECRET_KEY` hardcoded** in [auth.py](backend/app/routers/auth.py). Accettabile per l'esame ma da esternalizzare in una variabile d'ambiente/`.env` (come già annotato nel commento del codice). RNF-2 richiede protezione dei dati sensibili.
4. **Nessun endpoint protetto lato backend.** Esiste solo `POST /login`: non c'è ancora una dependency che decodifichi il JWT e imponga i ruoli. Di conseguenza le autorizzazioni sono **solo lato client** (`ProtectedRoute` legge `localStorage`, facilmente aggirabile). RF-9 (visualizzazione dati) e RF-15 (audit log) non sono ancora applicati.
5. **JWT in `localStorage`.** Esposto a XSS; per dati sanitari (RNF-2) sarebbe preferibile un cookie `HttpOnly`. Il client inoltre non verifica la scadenza (`exp`) del token prima di usarlo.
6. **`diabetify.db` versionato nel repository.** Un database binario non dovrebbe stare sotto version control; andrebbe generato con `init_db.py`/`seed.py` e ignorato da git. Da notare che la [.gitignore](.gitignore) della root ignora `diabetify.db` e `requirements.txt`, ma il DB in `backend/` risulta comunque tracciato (aggiunto prima della regola o forzato).
7. **`declarative_base()` duplicato e inutilizzato** in [database.py](backend/app/database.py) (i modelli usano il `Base` di `models.py`): rimuoverlo per evitare ambiguità.

### Funzionalità non ancora implementate
8. Rispetto ai requisiti di [Details.MD](Details.MD), è coperto solo **RF-1 (parziale: login)**. Non sono implementati gli endpoint per: registrazione utenti da admin (RF-2, UC-1/2), rilevazioni glicemiche (RF-4), sintomi/patologie (RF-5), assunzioni (RF-6), messaggi (RF-7), gestione terapie (RF-8), visualizzazione e aggregazione dati (RF-9), aggiornamento anamnesi (RF-10), né gli **automatismi di sistema** (RF-11…RF-14: coerenza terapeutica, solleciti, alert aderenza, glicemia fuori soglia) e la **tracciabilità** (RF-15). Gli schemi e i modelli per queste funzioni esistono già, quindi il lavoro è principalmente di implementazione dei router.
9. **Frontend incompleto:** le home dei tre ruoli sono placeholder; manca l'invio del token `Authorization: Bearer` nelle chiamate successive al login.

### Qualità / testing
10. **Nessun test** presente (unit, integration o E2E) né configurazione di test. Per un progetto d'esame sarebbe utile almeno testare il login e le validazioni Pydantic.

### Miglioramenti consigliati (priorità)
- **Alta:** correggere il manifest delle dipendenze (già fatto con `requirements.txt`); implementare la dependency di verifica JWT + protezione dei router; sistemare il CORS.
- **Media:** esternalizzare `SECRET_KEY`; rimuovere `diabetify.db` dal versionamento; implementare i router CRUD per RF-2…RF-10.
- **Bassa:** aggiungere test; implementare gli automatismi di sistema (RF-11…RF-14) tramite un job schedulato; completare le UI dei tre ruoli.

---

## Conclusione

Diabetify è un progetto **ben impostato e coerente con l'analisi dei requisiti**: il modello dati e gli schemi Pydantic sono completi, tipizzati e mappati puntualmente sui requisiti funzionali, il che denota un buon lavoro di progettazione a monte. Lo stack tecnologico (FastAPI + SQLAlchemy + SQLite lato server, React 19 + Vite + TypeScript lato client) è moderno e appropriato.

Allo stato attuale, però, l'implementazione è un **MVP limitato al flusso di autenticazione**: l'unico endpoint attivo è il login e le viste dei ruoli sono placeholder. La quasi totalità della logica di dominio (RF-2…RF-15) è modellata ma non ancora esposta. Il punto più urgente è il **manifest delle dipendenze incompleto**, che impedisce l'avvio con il solo `backend/requirements.txt`; questo è stato risolto con il [requirements.txt](requirements.txt) completo allegato a questa review. Seguono, per importanza, la protezione degli endpoint tramite verifica del JWT e la correzione della configurazione CORS.

La base è solida: il completamento consiste soprattutto nell'implementare i router CRUD (già supportati da modelli e schemi esistenti), gli automatismi di sistema e le interfacce dei tre ruoli.
