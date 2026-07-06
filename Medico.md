> **Diabetify · Documentazione** — [README](README.md) · [Paziente](Paziente.md) · **Medico** · [Amministratore](Admin.md) · [Sistema](Sistema.md)

# Attore Medico (Diabetologo)

Il medico è il professionista sanitario responsabile della cura del paziente. Attraverso
l'applicazione può consultare i dati clinici, gestire le terapie, aggiornare la scheda del
paziente e leggere gli alert e i messaggi che lo riguardano. Coerentemente con la
specifica ([Details.MD](Details.MD) §1.2), qualsiasi medico può accedere ai dati di
qualsiasi paziente: non esiste un vincolo di proprietà, ma ogni operazione viene tracciata
insieme al suo autore.

## Requisiti implementati

| Requisito | Descrizione |
|-----------|-------------|
| RF-8 (UC-8) | Gestione e prescrizione della terapia (creazione, modifica, sospensione) |
| RF-9 (UC-9) | Visualizzazione dei dati clinici, in dettaglio e in forma aggregata (settimana/mese) |
| RF-10 (UC-10) | Aggiornamento dell'anamnesi e dei fattori di rischio |
| RF-15 | Tracciabilità: ogni visualizzazione o modifica genera una voce di audit |
| RF-13 / RF-14 | Lettura degli alert automatici (lato lettura; la generazione è dell'attore [Sistema](Sistema.md)) |
| RF-7 | Lettura dei messaggi dei pazienti e risposta |
| RNF-1 | Applicazione delle soglie glicemiche (80–130 prima dei pasti, ≤180 dopo) |
| RNF-2 | Registro delle operazioni non modificabile (append-only) |

## Scelte progettuali

- Gli alert (RF-13/14) sono qui solo **consultati**: il componente che li genera appartiene
  all'attore [Sistema](Sistema.md).
- L'andamento glicemico aggregato (RF-9) è presentato in **forma tabellare**; una
  rappresentazione grafica è un possibile sviluppo futuro.
- La messaggistica (RF-7) comprende sia la lettura sia la risposta al paziente.

## Backend

### Componenti di autorizzazione e tracciabilità

- [backend/app/security.py](backend/app/security.py) — configurazione di sicurezza
  condivisa: chiave e algoritmo del token, hashing delle password e creazione del JWT.
- [backend/app/dependencies.py](backend/app/dependencies.py) — `get_current_user`
  (decodifica e valida il token), `require_doctor` (guardia di ruolo) e `registra_audit`
  (scrittura append-only del registro, RF-15/RNF-2).

### Endpoint (`/medico`, protetti da `require_doctor`)

Il router è [backend/app/routers/medico.py](backend/app/routers/medico.py).

| Metodo e path | Requisito | Note |
|---|---|---|
| `GET /medico/me` | — | Profilo del medico autenticato |
| `GET /medico/pazienti` | RF-9 | Elenco pazienti con n. alert aperti e ultima glicemia |
| `GET /medico/pazienti/{id}` | RF-9, RF-15 | Scheda completa (registra audit) |
| `GET /medico/pazienti/{id}/glicemie` | RF-9, RF-15 | Dettaglio con filtri `da`/`a` e campo `fuori_soglia` |
| `GET /medico/pazienti/{id}/glicemie/aggregato?periodo=settimana\|mese` | RF-9, RNF-1 | Media, minimo, massimo e n. fuori soglia per periodo |
| `GET /medico/pazienti/{id}/sintomi` · `/patologie-concomitanti` · `/terapie-parallele` | RF-5 | Sola lettura |
| `GET /medico/pazienti/{id}/assunzioni` | RF-6/11 | Confronto tra prescritto e assunto |
| `GET /medico/pazienti/{id}/terapie` | RF-8 | Elenco terapie |
| `POST /medico/pazienti/{id}/terapie` | RF-8, RF-15 | Nuova prescrizione (`doctor_id` dal token) |
| `PUT /medico/terapie/{id}` | RF-8, RF-15 | Modifica o sospensione |
| `PUT /medico/pazienti/{id}/anamnesi` | RF-10, RF-15 | Aggiornamento anamnesi |
| `GET /medico/notifiche` · `PATCH .../letta` · `PATCH .../risolta` | RF-13/14 | Inbox alert e gestione stato |
| `GET /medico/messaggi` · `POST /medico/messaggi` · `PATCH .../letto` | RF-7 | Messaggi ricevuti e risposta |

L'aggregazione glicemica è delegata al servizio condiviso
[backend/app/services/glicemia.py](backend/app/services/glicemia.py), che raggruppa le
rilevazioni per settimana (lunedì–domenica) o per mese applicando le soglie di dominio.

### Modifiche a file esistenti

- [backend/app/schemas.py](backend/app/schemas.py): aggiunti `AnamnesiUpdate` e
  `MedicoPazienteListItem`.
- [backend/app/routers/auth.py](backend/app/routers/auth.py): il login usa ora il modulo
  `security` condiviso (comportamento invariato).
- [backend/seed.py](backend/seed.py): dati clinici di esempio per il paziente di test, così
  l'interfaccia mostra contenuti reali.

## Frontend

L'area medico si trova in [frontend/src/pages/doctor/](frontend/src/pages/doctor/) e usa il
client API autenticato [lib/api.ts](frontend/src/lib/api.ts), i tipi condivisi
[lib/types.ts](frontend/src/lib/types.ts) e i componenti riusabili
[components/ui/](frontend/src/components/ui/).

- `DoctorLayout` — intestazione con nome del medico, navigazione (Pazienti, Notifiche,
  Messaggi) e contatori dei non letti.
- `PatientListPage` — elenco pazienti con ricerca e indicatore di alert.
- `PatientDetailPage` — scheda a quattro sezioni: anamnesi (RF-10), glicemie in tabella e
  aggregato (RF-9), terapie con creazione/sospensione e assunzioni (RF-8), sintomi e
  patologie in sola lettura (RF-5).
- `NotifichePage` — inbox degli alert con stato letta/risolta.
- `MessaggiPage` — lettura e risposta ai messaggi dei pazienti (RF-7).

Le rotte sono annidate sotto `/doctor` in [frontend/src/App.tsx](frontend/src/App.tsx) e
protette da `ProtectedRoute` con ruolo `doctor`.

## Verifica

Il comportamento è verificato dai test in
[backend/tests/test_medico.py](backend/tests/test_medico.py): elenco pazienti, creazione e
modifica di una terapia, aggiornamento dell'anamnesi, aggregazione glicemica e scrittura
del registro audit. Le guardie di ruolo sono coperte in
[test_auth_e_guardie.py](backend/tests/test_auth_e_guardie.py). L'interfaccia è verificata
dalla build di produzione (`npm run build`).

## Note e limiti

- La rappresentazione dell'andamento glicemico è tabellare; un grafico è un'estensione
  possibile.
- Gli alert mostrati provengono dall'attore [Sistema](Sistema.md), che li genera secondo le
  regole cliniche di dominio.
