# Specifica dei Requisiti del Sistema di Telemedicina per la Gestione del Diabete di Tipo 2

Il presente documento descrive l'analisi dei requisiti, gli attori e i casi d'uso relativi al sistema di telemedicina per il monitoraggio e la gestione dei pazienti affetti da diabete di tipo 2, basato sulla traccia fornita.

---

## 1. Attori Principali

Gli attori rappresentano le entità (umane o sistemi esterni) che interagiscono con il sistema per raggiungere un determinato obiettivo.

1.  **Paziente**
    * Utente affetto da diabete di tipo 2 che utilizza il sistema per monitorare il proprio stato di salute, registrare parametri biomedici, sintomi e assunzioni farmaceutiche, e comunicare con il proprio medico.
2.  **Diabetologo / Medico**
    * Professionista sanitario responsabile della cura del paziente. Può visualizzare i dati clinici, impostare/modificare le terapie, aggiornare la scheda clinica del paziente e ricevere alert in caso di anomalie. *Nota: Ogni medico può vedere e aggiornare i dati di qualsiasi paziente, ma il sistema traccia l'autore di ogni operazione.*
3.  **Responsabile del Servizio (Amministratore)**
    * Attore di back-office responsabile dell'inserimento dei dati iniziali (anagrafiche e credenziali) di medici e pazienti per consentire l'accesso al sistema, e dell'associazione tra paziente e medico di riferimento.
4.  **Sistema (Attore di Sistema / Timer)** *(Attore secondario/temporizzato)*
    * Il sistema stesso, inteso come entità autonoma che esegue controlli di coerenza, invia promemoria (alert) automatici per le dimenticanze dei farmaci e notifica i medici in caso di mancata aderenza o glicemie fuori soglia.

---

## 2. Requisiti del Sistema

I requisiti sono suddivisi in **Funzionali** (ciò che il sistema deve fare) e **Non Funzionali/Vincoli di Dominio** (proprietà, regole o vincoli del sistema).

### 2.1 Requisiti Funzionali (RF)

#### Gestione Accesso e Profilazione
* **RF-1 (Autenticazione):** Il sistema deve permettere l'accesso sicuro tramite autenticazione (login) differenziata per Pazienti e Medici.
* **RF-2 (Configurazione Iniziale):** Il sistema deve consentire ai Responsabili del Servizio di inserire i dati iniziali di medici e pazienti necessari per l'autenticazione.
* **RF-3 (Associazione Paziente-Medico):** Il sistema deve consentire di specificare un Medico di riferimento per ciascun paziente.

#### Funzionalità Lato Paziente
* **RF-4 (Registrazione Rilevazioni Glicemiche):** Il sistema deve permettere al paziente di memorizzare le rilevazioni giornaliere della glicemia, specificando il momento della misurazione (prima o dopo ogni pasto).
* **RF-5 (Registrazione Sintomi e Patologie Concomitanti):** Il sistema deve permettere al paziente di inserire sintomi (es. spossatezza, nausea, mal di testa), patologie concomitanti e terapie parallele, specificando il periodo associato.
* **RF-6 (Registrazione Assunzione Farmaci):** Il sistema deve permettere al paziente di registrare l'assunzione di insulina e/o farmaci antidiabetici orali, specificando giorno, ora, farmaco e quantità assunta.
* **RF-7 (Comunicazione con il Medico):** Il sistema deve permettere al paziente di inviare email per richieste e domande varie al proprio medico di riferimento.

#### Funzionalità Lato Medico
* **RF-8 (Gestione e Prescrizione Terapia):** Il sistema deve permettere al diabetologo di specificare, aggiungere o modificare la terapia del paziente. Per ogni terapia vanno inseriti: farmaco, numero di assunzioni giornaliere, quantità per assunzione e indicazioni (es. dopo i pasti, lontano dai pasti).
* **RF-9 (Visualizzazione Dati Clinici):** Il sistema deve consentire a qualsiasi medico di visionare i dati dei pazienti, sia in dettaglio che in forma sintetica/aggregata (es. andamento della glicemia settimana per settimana o mese per mese).
* **RF-10 (Aggiornamento Informazioni Paziente / Anamnesi):** Il sistema deve permettere al medico di aggiornare una sezione informativa sul paziente contenente fattori di rischio (fumo, alcol, stupefacenti, obesità), patologie pregresse e comorbidità (es. ipertensione).

#### Logiche di Controllo e Automatismi (Sistema)
* **RF-11 (Verifica Coerenza Terapeutica):** Il sistema deve verificare automaticamente che le assunzioni di farmaci registrate dal paziente siano coerenti con le terapie prescritte dal medico.
* **RF-12 (Gestione Solleciti/Completamento):** Il sistema deve invitare attivamente il paziente a completare gli inserimenti relativi alle assunzioni dei farmaci.
* **RF-13 (Alert Mancata Aderenza Terapeutica):** Il sistema deve generare alert automatici:
    * *Verso il paziente:* in caso di dimenticanza dell'assunzione del farmaco.
    * *Verso il medico:* nel caso in cui il paziente non segua le prescrizioni per più di 3 giorni consecutivi.
* **RF-14 (Segnalazione Glicemia Fuori Soglia):** Il sistema deve segnalare automaticamente ai medici i pazienti che registrano livelli di glicemia oltre le soglie stabilite, applicando diverse modalità di notifica a seconda della gravità.
* **RF-15 (Tracciabilità delle Operazioni):** Il sistema deve registrare storicamente e tenere traccia di quale medico ha effettuato ogni singola operazione di visualizzazione o modifica sui dati di ciascun paziente.

### 2.2 Requisiti Non Funzionali e Vincoli di Dominio (RNF)

* **RNF-1 (Soglie Glicemiche di Dominio):** Il sistema deve integrare le seguenti regole cliniche per l'analisi dei dati:
    * Livello normale prima dei pasti: compreso tra **80 e 130 mg/dL**.
    * Livello normale due ore dopo i pasti: non superiore a **180 mg/dL**.
* **RNF-2 (Sicurezza e Privacy):** Trattandosi di dati sanitari altamente sensibili (iperglicemia, patologie pregresse, dipendenze), l'accesso deve essere strettamente protetto da credenziali e i log di tracciamento medici (RF-15) devono essere inalterabili.
* **RNF-3 (Disponibilità del Servizio):** Il sistema di monitoraggio degli alert deve essere sempre attivo (24/7) per elaborare tempestivamente le rilevazioni e i mancati inserimenti.

---

## 3. Casi d'Uso (Use Cases)

I casi d'uso principali descrivono le macro-interazioni tra gli attori e il sistema.

### Attore: Responsabile del Servizio
* **UC-1: Inserimento Utenti Iniziali**
    * *Descrizione:* L'amministratore inserisce le anagrafiche e i dati di autenticazione per medici e pazienti.
* **UC-2: Associazione Paziente-Medico**
    * *Descrizione:* L'amministratore assegna un medico di riferimento a un determinato paziente.

### Attore: Paziente
* **UC-3: Autenticazione (Login)**
    * *Nota:* Condiviso anche con l'attore Medico.
* **UC-4: Inserimento Rilevazione Glicemica**
    * *Descrizione:* Il paziente inserisce il valore di glicemia indicando se è prima o dopo il pasto.
* **UC-5: Inserimento Sintomi e Patologie Concomitanti**
    * *Descrizione:* Il paziente segnala un malessere o una terapia concomitante indicandone il periodo.
* **UC-6: Registrazione Assunzione Farmaco**
    * *Descrizione:* Il paziente annota di aver assunto l'insulina o il farmaco orale (ora, giorno, quantità).
* **UC-7: Invio Richiesta/Email a Medico di Riferimento**
    * *Descrizione:* Il paziente invia una comunicazione scritta direttamente al proprio diabetologo.

### Attore: Diabetologo / Medico
* **UC-8: Gestione Terapia Farmacologica**
    * *Descrizione:* Il medico inserisce una nuova terapia o modifica una prescrizione esistente (farmaco, dosaggio, orari, indicazioni).
* **UC-9: Visualizzazione Scheda e Andamento Paziente**
    * *Descrizione:* Il medico consulta i dati del paziente, inclusi i grafici o i report sintetici settimanali/mensili della glicemia.
    * *Estensione del sistema:* Include il tracciamento automatico dell'operazione da parte del sistema.
* **UC-10: Aggiornamento Anamnesi e Fattori di Rischio**
    * *Descrizione:* Il medico modifica le note cliniche relative a stili di vita (fumo, alcol), comorbidità o patologie pregresse del paziente.

### Casi d'Uso Automatici (Innescati dal Sistema / Timer)
* **UC-11: Verifica Coerenza e Aderenza Terapeutica**
    * *Descrizione:* Il sistema confronta le assunzioni dichiarate dal paziente con la terapia attiva.
* **UC-12: Invio Alert per Dimenticanza Farmaci**
    * *Descrizione:* Il sistema invia un sollecito al paziente se rileva il mancato inserimento del farmaco.
* **UC-13: Invio Notifica di Mancata Aderenza al Medico**
    * *Descrizione:* Il sistema notifica il medico se il paziente non assume i farmaci per più di 3 giorni consecutivi.
* **UC-14: Segnalazione Glicemia Fuori Soglia**
    * *Descrizione:* Il sistema analizza le rilevazioni e invia una notifica di gravità variabile al medico se i limiti (80-130 o >180 mg/dL) vengono superati.