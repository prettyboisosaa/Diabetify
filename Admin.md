> **Diabetify · Documentazione** — [README](README.md) · [Paziente](Paziente.md) · [Medico](Medico.md) · **Amministratore** · [Sistema](Sistema.md)

# Attore Amministratore (Responsabile del Servizio)

L'amministratore è l'attore di back-office che prepara il sistema all'uso: inserisce le
anagrafiche e le credenziali di medici e pazienti e definisce l'associazione tra ciascun
paziente e il proprio medico di riferimento. Ha inoltre accesso al registro delle
operazioni per finalità di controllo.

## Requisiti implementati

| Requisito | Descrizione |
|-----------|-------------|
| RF-2 (UC-1) | Inserimento degli utenti iniziali (medici e pazienti) con credenziali |
| RF-3 (UC-2) | Associazione di un medico di riferimento a un paziente |
| RF-15 | Consultazione del registro audit (inalterabile) |
| Extra | Modifica delle anagrafiche e reset delle password |

Le funzioni "extra" sono state concordate come estensione ragionevole del ruolo. La
disattivazione degli account non è stata inclusa.

## Backend

Il router è [backend/app/routers/admin.py](backend/app/routers/admin.py), protetto da
`require_admin` ([backend/app/dependencies.py](backend/app/dependencies.py)).

| Metodo e path | Requisito | Note |
|---|---|---|
| `POST /admin/medici` | RF-2 | Crea utente medico e profilo; email univoca; password con hash |
| `POST /admin/pazienti` | RF-2 | Crea utente paziente e profilo, con medico opzionale |
| `GET /admin/utenti` | — | Elenco utenti con profilo |
| `GET /admin/medici` · `GET /admin/pazienti` | RF-3 | Elenchi per l'associazione |
| `PUT /admin/pazienti/{id}/medico` | RF-3 | Assegna, cambia o rimuove il medico di riferimento |
| `PUT /admin/utenti/{id}/anagrafica` | extra | Aggiorna email, nome e cognome |
| `POST /admin/utenti/{id}/reset-password` | extra | Imposta una nuova password |
| `GET /admin/audit-logs?paziente_id=` | RF-15 | Registro delle operazioni, filtrabile per paziente |

Le validazioni segnalano l'email già in uso (400) e i riferimenti inesistenti (404/400). La
creazione degli utenti applica le stesse regole di complessità della password previste per
il resto del sistema. Gli schemi aggiunti in
[backend/app/schemas.py](backend/app/schemas.py) sono `AssociazioneMedico`,
`AnagraficaUpdate` e `PasswordReset`.

## Frontend

L'area amministratore si trova in [frontend/src/pages/admin/](frontend/src/pages/admin/) e
usa il client [lib/admin.ts](frontend/src/lib/admin.ts).

- `AdminLayout` — navigazione (Utenti, Crea utente, Registro audit, Controlli sistema).
- `UtentiPage` — elenco degli utenti; per ciascuno, modifica dell'anagrafica e reset della
  password; per i pazienti, selezione del medico di riferimento (RF-3).
- `CreaUtentePage` — creazione di un medico o di un paziente (RF-2).
- `AuditLogPage` — consultazione del registro audit, con filtro per paziente (RF-15).
- `ControlliSistemaPage` — avvio dei controlli automatici dell'attore
  [Sistema](Sistema.md).

Le rotte sono annidate sotto `/admin` in [frontend/src/App.tsx](frontend/src/App.tsx),
protette da `ProtectedRoute` con ruolo `admin`.

## Verifica

I test in [backend/tests/test_admin.py](backend/tests/test_admin.py) coprono la creazione di
medici e pazienti (compreso il caso di email duplicata), l'associazione paziente–medico, la
modifica dell'anagrafica, il reset della password e la consultazione del registro audit.

## Note e limiti

- L'amministratore non ha un profilo anagrafico proprio: la modifica delle anagrafiche
  riguarda i profili di medici e pazienti.
