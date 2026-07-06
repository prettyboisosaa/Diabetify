> **Diabetify · Documentazione** — [README](README.md) · [Paziente](Paziente.md) · [Medico](Medico.md) · [Amministratore](Admin.md) · [Sistema](Sistema.md)

# Diabetify — Dettaglio dei file del progetto

Riferimento riassuntivo di ogni file del progetto, organizzato per area e funzione. Per una
panoramica generale e le istruzioni di avvio si veda il [README](README.md); per la specifica
dei requisiti [Details.MD](Details.MD).

**Stack**: Backend FastAPI + SQLAlchemy 2 + SQLite · Frontend React 19 + Vite + TypeScript (CSS Modules).
**Attori**: Paziente, Medico, Amministratore, Sistema (timer). Documenti per attore:
[Paziente.md](Paziente.md), [Medico.md](Medico.md), [Admin.md](Admin.md), [Sistema.md](Sistema.md).

## Struttura ad albero (essenziale)
```
Diabetify/
├── README.md                  # Panoramica e avvio del progetto
├── Details.MD                 # Specifica requisiti (RF/RNF/UC)
├── Medico.md · Paziente.md · Admin.md · Sistema.md · file_details.md
├── requirements.txt           # Dipendenze Python
├── backend/
│   ├── main.py · init_db.py · seed.py · run_sistema.py
│   ├── app/
│   │   ├── database.py · models.py · schemas.py · security.py · dependencies.py
│   │   ├── routers/  auth.py · medico.py · paziente.py · admin.py · sistema.py
│   │   └── services/ glicemia.py · sistema.py
│   └── tests/        base.py + test_*.py (unittest)
└── frontend/
    ├── index.html · vite.config.ts · tsconfig*.json · package.json
    └── src/
        ├── main.tsx · App.tsx · index.css
        ├── lib/       auth · api · types · medico · paziente · admin · format
        ├── components/ ProtectedRoute · ui/
        ├── styles/    theme.css · data.module.css
        └── pages/     Login · doctor/ · patient/ · admin/
```

---

# BACKEND

## Entrypoint, configurazione e script
| File | Ruolo |
|------|-------|
| [backend/main.py](backend/main.py) | Crea l'app FastAPI, configura la CORS e include i 5 router (auth, medico, paziente, admin, sistema). Espone `GET /` di health-check. |
| [backend/app/database.py](backend/app/database.py) | Engine SQLite (`diabetify.db`), `SessionLocal` e la dependency `get_db()` (una sessione per richiesta). |
| [backend/init_db.py](backend/init_db.py) | Crea fisicamente le tabelle da `Base.metadata` (`python init_db.py`). |
| [backend/seed.py](backend/seed.py) | Popola i 3 utenti di test (admin/medico/paziente) e dati clinici demo per Luca Bianchi (glicemie, terapia, assunzioni, sintomo, messaggio, notifiche). Idempotente. |
| [backend/run_sistema.py](backend/run_sistema.py) | Script standalone dell'attore Sistema: esegue una volta i controlli temporali (RF-12/13). Schedulabile via cron (RNF-3). |
| [backend/requirements.txt](requirements.txt) | Dipendenze (fastapi, uvicorn, SQLAlchemy, pydantic, PyJWT, passlib, bcrypt, python-multipart). |

## Nucleo dati e sicurezza
| File | Ruolo |
|------|-------|
| [backend/app/models.py](backend/app/models.py) | Tutti i modelli ORM ed enum. Entità: `User`, `DoctorProfile`, `PatientProfile` (con anamnesi), `RilevazioneGlicemica`, `Terapia`, `Assunzione`, `Sintomo`, `PatologiaConcomitante`, `TerapiaParallela`, `Messaggio`, `Notifica`, `AuditLog`. Enum: ruoli, momento pasto, unità, gravità, tipo/severità notifica. |
| [backend/app/schemas.py](backend/app/schemas.py) | Schemi Pydantic a strati (`Base→Create/Update→Response`). Validatori riusabili (complessità password, coerenza date), campo calcolato `fuori_soglia` (RNF-1), costanti soglie. Include schemi per tutti gli attori. |
| [backend/app/security.py](backend/app/security.py) | Configurazione sicurezza condivisa: `SECRET_KEY`/`ALGORITHM`, hashing bcrypt (`get_password_hash`/`verify_password`), `create_access_token` (JWT). |
| [backend/app/dependencies.py](backend/app/dependencies.py) | Dependency trasversali: `get_current_user` (decodifica JWT), guardie di ruolo `require_doctor`/`require_patient`/`require_admin`, e `registra_audit` (RF-15, append-only). |

## Services (logica di dominio riusabile)
| File | Ruolo |
|------|-------|
| [backend/app/services/glicemia.py](backend/app/services/glicemia.py) | `e_fuori_soglia` (RNF-1) e `aggrega_glicemie` (media/min/max/n° fuori soglia per settimana o mese, RF-9). Usato sia dal medico sia dal paziente. |
| [backend/app/services/sistema.py](backend/app/services/sistema.py) | Motore dell'attore Sistema: `severita_da_glicemia` e `verifica_glicemia` (RF-14), `assunzione_coerente` (RF-11), `esegui_controlli` (RF-12 solleciti + RF-13 mancata aderenza ≥3 giorni), con idempotenza. |

## Routers (endpoint HTTP)
| File | Prefisso | Requisiti | Endpoint principali |
|------|----------|-----------|---------------------|
| [auth.py](backend/app/routers/auth.py) | — | RF-1 | `POST /login` (OAuth2, restituisce JWT + ruolo). |
| [medico.py](backend/app/routers/medico.py) | `/medico` | RF-8/9/10/15, RF-7/13/14 (lettura) | `me`, `pazienti`, scheda + glicemie (dettaglio/aggregato), sintomi/patologie/parallele/assunzioni, terapie (CRUD), anamnesi, notifiche, messaggi. Audit su viste e modifiche. |
| [paziente.py](backend/app/routers/paziente.py) | `/paziente` | RF-4/5/6/7, RF-9(self), RF-12/13(lettura) | `me`, glicemie (POST/GET/aggregato, con hook RF-14), terapie (lettura) + assunzioni, diario (sintomi/patologie/parallele CRUD), messaggi al medico, notifiche. |
| [admin.py](backend/app/routers/admin.py) | `/admin` | RF-2/3/15 + extra | crea medici/pazienti, elenchi, associazione paziente-medico, modifica anagrafica, reset password, registro audit. |
| [sistema.py](backend/app/routers/sistema.py) | `/sistema` | RF-11/12/13 | `POST /esegui-controlli` (trigger dei controlli temporali, riservato all'admin). |

## Tests (`backend/tests/`, framework `unittest` stdlib)
Testano le **singole funzionalità** chiamando direttamente service, funzioni dei router e schemi su un DB
SQLite in memoria (nessuna dipendenza esterna: né pytest né httpx).
| File | Copre |
|------|-------|
| [tests/base.py](backend/tests/base.py) | Classe base `DBTestCase`: DB in memoria + dati minimi (admin, medico, paziente, terapia). |
| [tests/test_auth_e_guardie.py](backend/tests/test_auth_e_guardie.py) | Login/JWT (RF-1): hash password, token valido/non valido/scaduto, account disattivato; guardie di ruolo (403). |
| [tests/test_medico.py](backend/tests/test_medico.py) | Lista pazienti, crea/modifica terapia (RF-8), anamnesi (RF-10), tracciabilità audit (RF-15), aggregato (RF-9). |
| [tests/test_paziente.py](backend/tests/test_paziente.py) | Glicemie + alert event-driven (RF-4/14), assunzioni valide/invalide (RF-6), diario chiudibile (RF-5), messaggio al medico (RF-7). |
| [tests/test_admin.py](backend/tests/test_admin.py) | Crea utenti + email duplicata (RF-2), associazione paziente-medico (RF-3), anagrafica, reset password, audit (RF-15). |
| [tests/test_sistema.py](backend/tests/test_sistema.py) | Soglie/aggregazione (RNF-1/RF-9), coerenza (RF-11), alert glicemia (RF-14), solleciti/aderenza + idempotenza (RF-12/13). |
| [tests/test_schemi.py](backend/tests/test_schemi.py) | Validazione schemi: complessità password (RNF-2), `fuori_soglia`, validatore periodo diario (RF-5). |

**Esecuzione**: dalla cartella `backend/` → `../.venv/bin/python -m unittest discover -s tests -t . -v`
(39 test, tutti verdi).

---

# FRONTEND

## Entrypoint e configurazione
| File | Ruolo |
|------|-------|
| [frontend/index.html](frontend/index.html) | Pagina radice, monta `/src/main.tsx`. |
| [frontend/src/main.tsx](frontend/src/main.tsx) | Bootstrap React (StrictMode), importa `theme.css` e `index.css`. |
| [frontend/src/App.tsx](frontend/src/App.tsx) | Tabella delle rotte: `/login` + aree annidate `/doctor`, `/patient`, `/admin`, ciascuna sotto il proprio layout e `ProtectedRoute`. `RootRedirect` instrada in base al ruolo. |
| [frontend/src/index.css](frontend/src/index.css) | Reset/base globale. |
| `vite.config.ts` · `tsconfig*.json` · `package.json` | Configurazione Vite/TypeScript e dipendenze (react, react-dom, react-router-dom). |

## `lib/` — client API e utilità
| File | Ruolo |
|------|-------|
| [lib/auth.ts](frontend/src/lib/auth.ts) | Login (`fetch` form-urlencoded), gestione token/ruolo in `localStorage`, `getToken`/`getRole`/`isAuthenticated`/`logout`. |
| [lib/api.ts](frontend/src/lib/api.ts) | Wrapper `fetch` autenticato (`apiGet/apiPost/apiPut/apiPatch`): allega `Bearer`, gestisce errori e 401→logout. |
| [lib/types.ts](frontend/src/lib/types.ts) | Tipi di dominio condivisi (Glicemia, Terapia, Assunzione, Sintomo, Notifica, UserWithProfile, AuditLog, …). |
| [lib/medico.ts](frontend/src/lib/medico.ts) | Tipi/funzioni API dell'area medico (una per endpoint `/medico`). |
| [lib/paziente.ts](frontend/src/lib/paziente.ts) | Tipi input + funzioni API dell'area paziente (`/paziente`). |
| [lib/admin.ts](frontend/src/lib/admin.ts) | Funzioni API dell'area admin (`/admin`) + trigger `/sistema/esegui-controlli`. |
| [lib/format.ts](frontend/src/lib/format.ts) | Formattazione date/orari in italiano. |

## Componenti e stili condivisi
| File | Ruolo |
|------|-------|
| [components/ProtectedRoute.tsx](frontend/src/components/ProtectedRoute.tsx) | Guardia di rotta lato client per ruolo (redirect a login o alla dashboard corretta). |
| [components/ui/index.tsx](frontend/src/components/ui/index.tsx) | Libreria UI riusabile: `Card`, `Button`, `Badge`, `Field`, `Loading`, `ErrorBox`, `Empty`. |
| [components/ui/ui.module.css](frontend/src/components/ui/ui.module.css) | Stili dei componenti UI (sui token di theme.css). |
| [styles/theme.css](frontend/src/styles/theme.css) | Design token: colori brand/severità, raggi, ombre, scala di spaziatura 4/8px. |
| [styles/data.module.css](frontend/src/styles/data.module.css) | Stili di pagina condivisi (header, tabelle, tab, form, notifiche, stat-tile) usati da tutte le aree. |

## Pagine — Autenticazione
| File | Ruolo |
|------|-------|
| [pages/Login.tsx](frontend/src/pages/Login.tsx) + [Login.module.css](frontend/src/pages/Login.module.css) | Schermata di login (RF-1). |

## Pagine — Area MEDICO (`pages/doctor/`)
| File | Ruolo |
|------|-------|
| [DoctorLayout.tsx](frontend/src/pages/doctor/DoctorLayout.tsx) (+ .module.css) | Shell con nav (Pazienti · Notifiche · Messaggi) e badge non letti. |
| [PatientListPage.tsx](frontend/src/pages/doctor/PatientListPage.tsx) | Elenco pazienti con ricerca e indicatore alert (RF-9). |
| [PatientDetailPage.tsx](frontend/src/pages/doctor/PatientDetailPage.tsx) | Scheda paziente a tab; orchestra le sezioni. |
| [sections/AnamnesiSection.tsx](frontend/src/pages/doctor/sections/AnamnesiSection.tsx) | RF-10: modifica anamnesi/fattori di rischio. |
| [sections/GlicemieSection.tsx](frontend/src/pages/doctor/sections/GlicemieSection.tsx) | RF-9: tabella dettaglio + aggregato settimana/mese. |
| [sections/TerapieSection.tsx](frontend/src/pages/doctor/sections/TerapieSection.tsx) | RF-8: terapie (crea/sospendi) + assunzioni del paziente. |
| [sections/ClinicaSection.tsx](frontend/src/pages/doctor/sections/ClinicaSection.tsx) | RF-5 (lettura): sintomi/patologie/terapie parallele. |
| [NotifichePage.tsx](frontend/src/pages/doctor/NotifichePage.tsx) | RF-13/14: inbox alert con stato letta/risolta. |
| [MessaggiPage.tsx](frontend/src/pages/doctor/MessaggiPage.tsx) | RF-7: messaggi ricevuti + risposta. |

## Pagine — Area PAZIENTE (`pages/patient/`)
| File | Ruolo |
|------|-------|
| [PatientLayout.tsx](frontend/src/pages/patient/PatientLayout.tsx) (+ .module.css) | Shell con nav (Home · Glicemie · Terapie · Diario · Messaggi · Notifiche). |
| [DashboardPage.tsx](frontend/src/pages/patient/DashboardPage.tsx) | Riepilogo (ultima glicemia, terapie attive, avvisi) + azioni rapide. |
| [GlicemiePage.tsx](frontend/src/pages/patient/GlicemiePage.tsx) | RF-4: inserimento + storico + aggregato. |
| [TerapiePage.tsx](frontend/src/pages/patient/TerapiePage.tsx) | RF-6: terapie prescritte + registrazione assunzioni. |
| [DiarioPage.tsx](frontend/src/pages/patient/DiarioPage.tsx) | RF-5: sintomi/patologie/terapie parallele (crea + chiudi). |
| [MessaggiPage.tsx](frontend/src/pages/patient/MessaggiPage.tsx) | RF-7: scrive al proprio medico + legge le risposte. |
| [NotifichePage.tsx](frontend/src/pages/patient/NotifichePage.tsx) | RF-12/13: solleciti/avvisi (lettura + stato). |

## Pagine — Area AMMINISTRATORE (`pages/admin/`)
| File | Ruolo |
|------|-------|
| [AdminLayout.tsx](frontend/src/pages/admin/AdminLayout.tsx) (+ .module.css) | Shell con nav (Utenti · Crea utente · Registro audit · Controlli sistema). |
| [UtentiPage.tsx](frontend/src/pages/admin/UtentiPage.tsx) | Elenco utenti; modifica anagrafica, reset password, associazione medico (RF-3). |
| [CreaUtentePage.tsx](frontend/src/pages/admin/CreaUtentePage.tsx) | RF-2: creazione medico/paziente. |
| [AuditLogPage.tsx](frontend/src/pages/admin/AuditLogPage.tsx) | RF-15: consultazione registro audit (filtro per paziente). |
| [ControlliSistemaPage.tsx](frontend/src/pages/admin/ControlliSistemaPage.tsx) | Trigger dei controlli di Sistema (RF-11/12/13) con riepilogo. |

---

# Come eseguire

```bash
# 1) Backend (dalla cartella backend/)
python init_db.py && python seed.py
uvicorn main:app --reload            # http://localhost:8000  ·  /docs per l'API

# 2) Frontend (dalla cartella frontend/)
npm install && npm run dev           # http://localhost:5173

# 3) Test (dalla cartella backend/)
python -m unittest discover -s tests -t . -v

# 4) Controlli di Sistema on-demand (dalla cartella backend/)
python run_sistema.py
```
Credenziali di test: **admin@diabetify.it/Admin2026!** · **dottore@diabetify.it/Medico2026!** ·
**paziente@diabetify.it/Paziente2026!**

# Mappa requisiti → dove sono realizzati
| Requisito | File principali |
|-----------|-----------------|
| RF-1 login | `auth.py`, `security.py`, `dependencies.py`, `lib/auth.ts`, `Login.tsx` |
| RF-2/3 admin | `admin.py`, `pages/admin/*` |
| RF-4/5/6/7 paziente | `paziente.py`, `pages/patient/*` |
| RF-8/9/10 medico | `medico.py`, `pages/doctor/*` |
| RF-11/12/13/14 sistema | `services/sistema.py`, `sistema.py`, `run_sistema.py` |
| RF-15 audit | `dependencies.py` (registra), `admin.py` (consulta), `AuditLogPage.tsx` |
| RNF-1 soglie | `services/glicemia.py`, `schemas.py` |
| RNF-2 sicurezza | `security.py`, `schemas.py` (password), audit append-only |
| RNF-3 24/7 | `run_sistema.py` (cron) + trigger `sistema.py` |
