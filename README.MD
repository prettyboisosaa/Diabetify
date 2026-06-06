# Diabetify


Diabetify è un sistema di **telemedicina per la gestione del diabete di tipo 2**, pensato per supportare il monitoraggio continuo dei pazienti e migliorare la collaborazione con il personale medico.

L'obiettivo principale è offrire una piattaforma digitale sicura che permetta:

- ai **pazienti** di registrare in autonomia rilevazioni glicemiche, sintomi, patologie concomitanti e assunzione di farmaci, mantenendo un canale di comunicazione diretto con il proprio diabetologo;
- ai **medici (diabetologi)** di consultare i dati clinici dei pazienti (in forma dettagliata o aggregata), prescrivere o modificare le terapie, aggiornare l'anamnesi e ricevere notifiche tempestive in caso di anomalie;
- al **responsabile del servizio** di gestire l'inserimento iniziale di anagrafiche e credenziali e di associare ciascun paziente al medico di riferimento;
- al **sistema stesso** di operare in modo automatico 24/7, verificando l'aderenza terapeutica, segnalando glicemie fuori soglia (80–130 mg/dL prima dei pasti, ≤180 mg/dL due ore dopo i pasti) e inviando alert e promemoria.

## Cosa Abbiamo Intenzione di Fare

Vogliamo realizzare un sistema completo che copra l'intero ciclo di cura del paziente diabetico, partendo dai requisiti definiti in [Details.MD](Details.MD). In particolare, il progetto svilupperà:

1. **Autenticazione e profilazione** differenziata per pazienti, medici e amministratori.
2. **Modulo paziente** per la registrazione di:
   - rilevazioni glicemiche (prima/dopo i pasti),
   - sintomi e patologie concomitanti,
   - assunzione di insulina e farmaci antidiabetici orali,
   - comunicazioni via email con il medico di riferimento.
3. **Modulo medico** per:
   - prescrizione e modifica delle terapie (farmaco, dosaggi, orari, indicazioni),
   - visualizzazione di dati e andamenti settimanali/mensili,
   - aggiornamento dell'anamnesi e dei fattori di rischio (fumo, alcol, obesità, comorbidità).
4. **Automatismi di sistema** per:
   - verifica della coerenza tra terapia prescritta e assunzioni dichiarate,
   - alert al paziente per dimenticanze e al medico per mancata aderenza (>3 giorni),
   - segnalazione automatica di glicemie fuori soglia con diversi livelli di gravità.
5. **Tracciabilità e sicurezza**: log inalterabili di ogni operazione svolta dai medici sui dati dei pazienti e protezione dei dati sanitari sensibili.

Per il dettaglio completo di attori, requisiti funzionali (RF-1 ... RF-15), requisiti non funzionali e casi d'uso (UC-1 ... UC-14) si rimanda al documento [Details.MD](Details.MD).

---

## Come Scaricare il Progetto

### Prerequisiti

Prima di scaricare il progetto assicurati di avere installato:

- **Git** ([download](https://git-scm.com/downloads))
- Un editor di codice (consigliato: **Visual Studio Code**)

### 1. Clonare il repository

Apri un terminale (PowerShell su Windows, Terminal su macOS/Linux) e posizionati nella cartella in cui vuoi scaricare il progetto, poi esegui:

```bash
git clone https://github.com/prettyboisosaa/Diabetify
```
### 2. Entrare nella cartella del progetto

```bash
cd Diabetify
```

### 3. (Alternativa) Download manuale come ZIP

Se non vuoi usare Git puoi scaricare il progetto come archivio:

1. Apri la pagina del repository nel browser.
2. Clicca su **Code → Download ZIP**.
3. Estrai l'archivio nella cartella desiderata.

### 4. Aprire il progetto

Apri la cartella `Diabetify` con il tuo editor preferito, ad esempio:

```bash
code .
```

### 5. Mantenere il progetto aggiornato

Per ricevere gli ultimi aggiornamenti, dalla cartella del progetto esegui:

```bash
git pull
```

---

## Come Eseguire il Backend

### 1. Posizionarsi nella cartella backend

Dalla root del progetto:

```powershell
cd backend
```

### 2. Attivare il virtual environment

Su Windows (PowerShell):

```powershell
.\venv\Scripts\Activate.ps1
```

> Se PowerShell blocca lo script con un errore di execution policy, esegui una sola volta:
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
> ```

Una volta attivato, il prompt mostrerà `(venv)` all'inizio della riga.

### 3. Avviare il server FastAPI con Uvicorn

```powershell
uvicorn main:app --reload
```

Il flag `--reload` riavvia automaticamente il server a ogni modifica del codice (utile in sviluppo).

### 4. Testare gli endpoint con Swagger UI

Apri il browser all'indirizzo:

```
http://localhost:8000/docs
```

Da qui puoi consultare la documentazione interattiva di tutti gli endpoint e provarli direttamente (Swagger UI).

> In alternativa, la documentazione in stile ReDoc è disponibile su `http://localhost:8000/redoc`.

---

## Come Eseguire il Frontend

Il frontend è un'app **React 19 + Vite + TypeScript** che comunica con il backend FastAPI. Per il login l'app si aspetta che il backend sia in esecuzione su `http://localhost:8000` (vedi sezione precedente).

### Prerequisiti

- **Node.js 20+** ([download](https://nodejs.org/)) — verifica con `node -v`
- **npm** (incluso con Node)

### 1. Posizionarsi nella cartella frontend

Dalla root del progetto:

```powershell
cd frontend
```

### 2. Installare le dipendenze

La prima volta (e ogni volta che `package.json` cambia):

```powershell
npm install
```

### 3. Avviare il server di sviluppo Vite

```powershell
npm run dev
```

Vite stamperà nel terminale l'URL locale, di norma:

```
http://localhost:5173
```

> Se la porta 5173 è già occupata, Vite ne userà automaticamente un'altra (es. 5174) e lo segnalerà nel log.

### 4. Aprire l'app

Vai su `http://localhost:5173` nel browser: vedrai la **pagina di login**. Effettuato l'accesso con un utente del DB, l'app reindirizza automaticamente alla home corrispondente al ruolo (`/doctor`, `/patient` o `/admin`).

> Per resettare la sessione e tornare al login, apri DevTools (F12) → **Application** → **Local Storage** → rimuovi le chiavi `diabetify_token` e `diabetify_role`.

### 5. (Opzionale) Configurare un URL backend diverso

Di default il frontend chiama `http://localhost:8000`. Per puntare a un altro host, crea un file `frontend/.env.local`:

```
VITE_API_URL=http://altro-host:8000
```

e riavvia `npm run dev`.

### 6. Build di produzione

Per generare i file statici ottimizzati in `frontend/dist/`:

```powershell
npm run build
npm run preview   # serve localmente la build per verifica
```

---

