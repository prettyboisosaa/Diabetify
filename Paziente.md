> **Diabetify · Documentazione** — [README](README.md) · **Paziente** · [Medico](Medico.md) · [Amministratore](Admin.md) · [Sistema](Sistema.md)

# Attore Paziente

Il paziente è l'utente affetto da diabete di tipo 2 che utilizza l'applicazione per
monitorare il proprio stato di salute. Può registrare le rilevazioni glicemiche, annotare
sintomi e patologie, tenere traccia delle assunzioni dei farmaci e comunicare con il
proprio medico di riferimento. Opera sempre e solo sui propri dati: l'identificativo del
paziente è ricavato dal token di autenticazione.

## Requisiti implementati

| Requisito | Descrizione |
|-----------|-------------|
| RF-4 (UC-4) | Registrazione delle rilevazioni glicemiche (valore e momento rispetto al pasto) |
| RF-5 (UC-5) | Registrazione di sintomi, patologie concomitanti e terapie parallele, con periodo |
| RF-6 (UC-6) | Registrazione dell'assunzione dei farmaci, collegata a una terapia prescritta |
| RF-7 (UC-7) | Comunicazione con il proprio medico di riferimento |
| RF-9 | Consultazione dei propri dati e dell'andamento glicemico aggregato |
| RF-12 / RF-13 | Lettura dei solleciti e degli avvisi automatici |

## Scelte progettuali

- Le glicemie e le assunzioni sono voci di **registro**: si possono inserire e consultare,
  ma non modificare a posteriori.
- Il diario clinico (sintomi, patologie, terapie parallele) è invece **modificabile**, in
  particolare per chiudere una voce impostandone la data di fine.
- I solleciti e gli avvisi (RF-12/13) sono solo **letti**: la loro generazione appartiene
  all'attore [Sistema](Sistema.md).
- Il messaggio (RF-7) è indirizzato automaticamente al medico di riferimento indicato nel
  profilo del paziente; l'utente non sceglie il destinatario.

## Backend

Il router è [backend/app/routers/paziente.py](backend/app/routers/paziente.py), protetto da
`require_patient` ([backend/app/dependencies.py](backend/app/dependencies.py)).

| Metodo e path | Requisito | Note |
|---|---|---|
| `GET /paziente/me` | — | Profilo del paziente autenticato |
| `POST /paziente/glicemie` | RF-4, RF-14 | Nuova rilevazione; se fuori soglia avvisa il medico (hook verso il Sistema) |
| `GET /paziente/glicemie` · `/glicemie/aggregato` | RF-9 | Storico e andamento aggregato |
| `GET /paziente/terapie` | RF-6 | Terapie prescritte (sola lettura) |
| `POST /paziente/assunzioni` · `GET /paziente/assunzioni` | RF-6 | Registrazione e storico assunzioni |
| `GET/POST/PUT /paziente/sintomi` | RF-5 | Diario dei sintomi (inserimento e chiusura) |
| `GET/POST/PUT /paziente/patologie-concomitanti` | RF-5 | Patologie concomitanti |
| `GET/POST/PUT /paziente/terapie-parallele` | RF-5 | Terapie parallele |
| `GET /paziente/messaggi` · `POST /paziente/messaggi` · `PATCH .../letto` | RF-7 | Messaggi da/verso il medico |
| `GET /paziente/notifiche` · `PATCH .../letta` · `PATCH .../risolta` | RF-12/13 | Avvisi e gestione stato |

Alla registrazione di una glicemia il router richiama `verifica_glicemia`
([backend/app/services/sistema.py](backend/app/services/sistema.py)): se il valore è fuori
soglia viene generato un avviso per il medico (RF-14). La registrazione di un'assunzione
verifica che la terapia indicata appartenga al paziente. Gli schemi aggiunti in
[backend/app/schemas.py](backend/app/schemas.py) sono `MessaggioPazienteCreate`,
`PatologiaConcomitanteUpdate` e `TerapiaParallelaUpdate`.

## Frontend

L'area paziente si trova in [frontend/src/pages/patient/](frontend/src/pages/patient/) e usa
il client [lib/paziente.ts](frontend/src/lib/paziente.ts).

- `PatientLayout` — navigazione (Home, Glicemie, Terapie, Diario, Messaggi, Notifiche).
- `DashboardPage` — riepilogo con ultima glicemia, terapie attive e avvisi da leggere.
- `GlicemiePage` — inserimento, storico e andamento aggregato (RF-4, RF-9).
- `TerapiePage` — terapie prescritte e registrazione delle assunzioni (RF-6).
- `DiarioPage` — sintomi, patologie e terapie parallele, con inserimento e chiusura (RF-5).
- `MessaggiPage` — invio di messaggi al medico e lettura delle risposte (RF-7).
- `NotifichePage` — solleciti e avvisi in sola lettura (RF-12/13).

Le rotte sono annidate sotto `/patient` in [frontend/src/App.tsx](frontend/src/App.tsx),
protette da `ProtectedRoute` con ruolo `patient`.

## Verifica

I test in [backend/tests/test_paziente.py](backend/tests/test_paziente.py) coprono la
registrazione delle glicemie (con e senza superamento delle soglie), le assunzioni valide e
non valide, la creazione e chiusura di un sintomo e l'invio del messaggio al medico. La
build del frontend (`npm run build`) è priva di errori.

## Note e limiti

- L'andamento glicemico è mostrato in forma tabellare.
- Gli avvisi visualizzati sono prodotti dall'attore [Sistema](Sistema.md).
