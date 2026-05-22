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

