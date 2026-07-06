"""
Servizio dell'attore SISTEMA (Timer / automatismi).

Implementa i controlli automatici:
  RF-11  Verifica coerenza tra assunzioni registrate e terapie prescritte
  RF-12  Sollecito al paziente a completare le assunzioni della giornata
  RF-13  Alert di mancata aderenza (>=3 giorni consecutivi) al medico
  RF-14  Segnalazione glicemia fuori soglia al medico, con severita' variabile

Approccio (deciso con l'utente): event-driven + trigger.
  - `verifica_glicemia` viene chiamata SUBITO quando il paziente registra una
    glicemia (hook in routers/paziente.py) -> RF-14.
  - `esegui_controlli` racchiude i controlli TEMPORALI (RF-12/RF-13) ed e'
    invocata dall'endpoint POST /sistema/esegui-controlli e dallo script
    run_sistema.py (cron-abile, RNF-3).

Tutte le creazioni di notifiche sono IDEMPOTENTI: non si duplica una notifica
equivalente non risolta gia' presente nello stesso giorno.
"""

from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models import (
    PatientProfile,
    DoctorProfile,
    RilevazioneGlicemica,
    MomentoGlicemia,
    Terapia,
    Assunzione,
    Notifica,
    TipoNotifica,
    SeveritaNotifica,
)
from app.services.glicemia import e_fuori_soglia

# Numero di giorni consecutivi non aderenti che fa scattare l'alert al medico (RF-13)
GIORNI_NON_ADERENZA = 3


# =========================================================
# HELPER: confini temporali e idempotenza
# =========================================================
def _inizio_giorno(g: date) -> datetime:
    return datetime(g.year, g.month, g.day)


def _esiste_notifica_giorno(
    db: Session,
    destinatario_id: int,
    tipo: TipoNotifica,
    paziente_id: int | None,
    giorno: date,
) -> bool:
    """True se esiste gia' una notifica dello stesso tipo/paziente creata `giorno`."""
    inizio = _inizio_giorno(giorno)
    fine = inizio + timedelta(days=1)
    return (
        db.query(Notifica)
        .filter(
            Notifica.destinatario_id == destinatario_id,
            Notifica.tipo == tipo,
            Notifica.paziente_riferimento_id == paziente_id,
            Notifica.creato_at >= inizio,
            Notifica.creato_at < fine,
        )
        .first()
        is not None
    )


def _medico_di(paziente: PatientProfile, db: Session) -> DoctorProfile | None:
    """Restituisce il DoctorProfile di riferimento del paziente, se presente."""
    if paziente.doctor_id is None:
        return None
    return db.query(DoctorProfile).filter(DoctorProfile.id == paziente.doctor_id).first()


# =========================================================
# RF-14: glicemia fuori soglia (event-driven)
# =========================================================
def severita_da_glicemia(valore: int, momento: MomentoGlicemia) -> SeveritaNotifica:
    """
    Severita' in base a quanto il valore e' oltre le soglie cliniche (RNF-1).
    Presuppone che il valore sia gia' fuori soglia.
    """
    if momento == MomentoGlicemia.PRIMA_PASTO:
        if valore < 54 or valore > 250:
            return SeveritaNotifica.CRITICAL
        return SeveritaNotifica.WARNING
    # dopo pasto
    if valore > 250:
        return SeveritaNotifica.CRITICAL
    return SeveritaNotifica.WARNING


def verifica_glicemia(db: Session, rilevazione: RilevazioneGlicemica) -> Notifica | None:
    """
    RF-14: se la rilevazione e' fuori soglia, notifica il medico di riferimento
    con severita' variabile. Ogni rilevazione e' un evento distinto (nessuna
    idempotenza per giorno qui).
    """
    if not e_fuori_soglia(rilevazione.valore, rilevazione.momento):
        return None

    paziente = (
        db.query(PatientProfile)
        .filter(PatientProfile.id == rilevazione.patient_id)
        .first()
    )
    if paziente is None:
        return None
    medico = _medico_di(paziente, db)
    if medico is None:
        return None  # nessun medico a cui inviare

    severita = severita_da_glicemia(rilevazione.valore, rilevazione.momento)
    momento_txt = "prima del pasto" if rilevazione.momento == MomentoGlicemia.PRIMA_PASTO else "dopo il pasto"
    notifica = Notifica(
        destinatario_id=medico.user_id,
        paziente_riferimento_id=paziente.id,
        tipo=TipoNotifica.GLICEMIA_FUORI_SOGLIA,
        severita=severita,
        messaggio=(
            f"Glicemia fuori soglia ({rilevazione.valore} mg/dL, {momento_txt}) "
            f"per il paziente {paziente.nome} {paziente.cognome}."
        ),
    )
    db.add(notifica)
    db.commit()
    return notifica


# =========================================================
# RF-11: coerenza assunzione / terapia
# =========================================================
def assunzione_coerente(assunzione: Assunzione, terapia: Terapia) -> bool:
    """
    RF-11: un'assunzione e' coerente se riferita a una terapia ATTIVA e con
    farmaco, quantita' e unita' pari a quelli prescritti.
    """
    return (
        terapia.is_active
        and assunzione.farmaco == terapia.farmaco
        and Decimal(assunzione.quantita_assunta) == Decimal(terapia.quantita)
        and assunzione.unita == terapia.unita
    )


def _assunzioni_coerenti_del_giorno(db: Session, terapia: Terapia, giorno: date) -> int:
    """Numero di assunzioni COERENTI registrate per la terapia in un dato giorno."""
    inizio = _inizio_giorno(giorno)
    fine = inizio + timedelta(days=1)
    assunzioni = (
        db.query(Assunzione)
        .filter(
            Assunzione.terapia_id == terapia.id,
            Assunzione.timestamp >= inizio,
            Assunzione.timestamp < fine,
        )
        .all()
    )
    return sum(1 for a in assunzioni if assunzione_coerente(a, terapia))


def _giorno_aderente(db: Session, terapia: Terapia, giorno: date) -> bool:
    """Un giorno e' aderente se le assunzioni coerenti sono >= a quelle prescritte."""
    return _assunzioni_coerenti_del_giorno(db, terapia, giorno) >= terapia.assunzioni_giornaliere


# =========================================================
# RF-12 / RF-13: controlli temporali (trigger / cron)
# =========================================================
def esegui_controlli(db: Session, oggi: date | None = None) -> dict:
    """
    Esegue i controlli temporali su tutte le terapie attive e crea le notifiche
    necessarie (idempotenti). Restituisce un riepilogo delle notifiche generate.
    """
    if oggi is None:
        oggi = date.today()

    create: list[str] = []
    terapie = db.query(Terapia).filter(Terapia.is_active.is_(True)).all()

    for terapia in terapie:
        paziente = (
            db.query(PatientProfile)
            .filter(PatientProfile.id == terapia.patient_id)
            .first()
        )
        if paziente is None:
            continue

        # --- RF-12: giornata odierna incompleta -> sollecito al paziente ---
        if not _giorno_aderente(db, terapia, oggi):
            if not _esiste_notifica_giorno(
                db, paziente.user_id, TipoNotifica.SOLLECITO_ASSUNZIONE, paziente.id, oggi
            ):
                db.add(Notifica(
                    destinatario_id=paziente.user_id,
                    paziente_riferimento_id=paziente.id,
                    tipo=TipoNotifica.SOLLECITO_ASSUNZIONE,
                    severita=SeveritaNotifica.INFO,
                    messaggio=(
                        f"Ricordati di completare le assunzioni di {terapia.farmaco} "
                        f"previste per oggi ({terapia.assunzioni_giornaliere}/die)."
                    ),
                ))
                create.append(f"sollecito -> paziente {paziente.id} ({terapia.farmaco})")

        # --- RF-13: >=3 giorni consecutivi non aderenti -> alert al medico ---
        giorni_non_aderenti = 0
        for scarto in range(GIORNI_NON_ADERENZA):
            if not _giorno_aderente(db, terapia, oggi - timedelta(days=scarto)):
                giorni_non_aderenti += 1
            else:
                break

        if giorni_non_aderenti >= GIORNI_NON_ADERENZA:
            medico = _medico_di(paziente, db)
            if medico is not None and not _esiste_notifica_giorno(
                db, medico.user_id, TipoNotifica.MANCATA_ADERENZA, paziente.id, oggi
            ):
                db.add(Notifica(
                    destinatario_id=medico.user_id,
                    paziente_riferimento_id=paziente.id,
                    tipo=TipoNotifica.MANCATA_ADERENZA,
                    severita=SeveritaNotifica.WARNING,
                    messaggio=(
                        f"Il paziente {paziente.nome} {paziente.cognome} non segue la "
                        f"terapia con {terapia.farmaco} da almeno {GIORNI_NON_ADERENZA} giorni."
                    ),
                ))
                create.append(f"mancata_aderenza -> medico di paziente {paziente.id} ({terapia.farmaco})")

    db.commit()
    return {"notifiche_create": len(create), "dettaglio": create}
