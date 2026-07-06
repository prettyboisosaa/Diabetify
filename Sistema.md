> **Diabetify · Documentazione** — [README](README.md) · [Paziente](Paziente.md) · [Medico](Medico.md) · [Amministratore](Admin.md) · **Sistema**

# Attore Sistema (Timer / automatismi)

Il Sistema è un attore autonomo che esegue controlli automatici sui dati inseriti dagli
utenti: verifica la coerenza tra terapie e assunzioni, invia solleciti ai pazienti e segnala
ai medici le situazioni critiche (mancata aderenza e glicemie fuori soglia). A differenza
degli altri attori non ha un'interfaccia propria: agisce dietro le quinte e i suoi avvisi
compaiono nelle inbox di medico e paziente.

## Requisiti implementati

| Requisito | Descrizione |
|-----------|-------------|
| RF-11 | Verifica della coerenza tra le assunzioni registrate e le terapie prescritte |
| RF-12 | Sollecito al paziente a completare le assunzioni della giornata |
| RF-13 | Avviso di mancata aderenza (al paziente per la dimenticanza, al medico dopo più giorni) |
| RF-14 | Segnalazione al medico delle glicemie fuori soglia, con gravità variabile |
| RNF-3 | Monitoraggio continuo (ottenuto tramite esecuzione schedulabile) |

## Scelte progettuali

Il Sistema è realizzato con un approccio **a eventi più esecuzione periodica**:

- **A evento**: quando il paziente registra una glicemia, il controllo di soglia (RF-14)
  viene eseguito immediatamente.
- **Periodico**: i controlli che dipendono dal tempo (solleciti RF-12 e aderenza RF-13)
  sono raccolti in un'unica funzione, richiamabile da un endpoint o dallo script
  `run_sistema.py`, pensato per essere schedulato (per esempio con cron) e soddisfare
  così RNF-3.

Gli avvisi sono realizzati come **notifiche in-app**, senza invio di email reali. La
creazione delle notifiche è **idempotente**: la stessa segnalazione non viene duplicata se
è già presente e non ancora risolta nella giornata.

## Regola di aderenza

- Un'assunzione è **coerente** (RF-11) se è riferita a una terapia attiva e ha farmaco,
  quantità e unità pari a quelli prescritti.
- Un giorno è **non aderente** per una terapia se le assunzioni coerenti registrate sono
  meno di quelle giornaliere previste.
- Se un giorno è incompleto, il paziente riceve un sollecito (RF-12); se i giorni
  consecutivi non aderenti sono almeno tre, il medico riceve un avviso di mancata aderenza
  (RF-13).
- Per le glicemie (RF-14) la gravità è `warning` oltre soglia e `critical` per gli
  scostamenti marcati.

## Backend

- [backend/app/services/sistema.py](backend/app/services/sistema.py) — logica del Sistema:
  `severita_da_glicemia` e `verifica_glicemia` (RF-14), `assunzione_coerente` (RF-11) ed
  `esegui_controlli` (RF-12/13).
- [backend/app/routers/sistema.py](backend/app/routers/sistema.py) — endpoint
  `POST /sistema/esegui-controlli`, riservato all'amministratore, che avvia i controlli
  periodici.
- [backend/run_sistema.py](backend/run_sistema.py) — script equivalente eseguibile da riga
  di comando, adatto alla schedulazione.
- [backend/app/routers/paziente.py](backend/app/routers/paziente.py) — richiama
  `verifica_glicemia` subito dopo la registrazione di una glicemia (controllo a evento).

Il controllo di soglia riusa il servizio condiviso
[backend/app/services/glicemia.py](backend/app/services/glicemia.py).

## Interazione con l'interfaccia

Il Sistema non ha pagine proprie. La sua presenza è visibile attraverso:

- il pulsante di avvio dei controlli in `ControlliSistemaPage` (area
  [Amministratore](Admin.md)), che mostra un riepilogo degli avvisi generati;
- le notifiche prodotte, che compaiono nelle inbox di [Medico](Medico.md) e
  [Paziente](Paziente.md).

## Verifica

I test in [backend/tests/test_sistema.py](backend/tests/test_sistema.py) coprono le soglie e
l'aggregazione, la coerenza delle assunzioni, la generazione dell'avviso di glicemia fuori
soglia e i controlli di aderenza, verificando anche che una seconda esecuzione non produca
duplicati (idempotenza).

## Note e limiti

- Il monitoraggio 24/7 (RNF-3) è realizzato con l'esecuzione schedulabile di
  `run_sistema.py`; in un contesto reale si userebbe uno scheduler dedicato.
- Le soglie di gravità sono valori ragionevoli definiti nel servizio e facilmente
  parametrizzabili.
