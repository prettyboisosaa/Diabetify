"""
Router dell'attore MEDICO / Diabetologo.

Copre i requisiti lato medico:
  RF-8  (UC-8)  Gestione e prescrizione terapia
  RF-9  (UC-9)  Visualizzazione dati clinici (dettaglio + aggregato)
  RF-10 (UC-10) Aggiornamento anamnesi / fattori di rischio
  RF-15         Tracciabilita' di ogni visualizzazione/modifica
  RF-13/14      Lettura degli alert automatici (sola lettura in questa fase)
  RF-7          Lettura e risposta ai messaggi dei pazienti

Nota di dominio (Details.MD): QUALSIASI medico puo' vedere/aggiornare QUALSIASI
paziente. Non c'e' quindi un controllo di proprieta' sul paziente; il sistema
traccia pero' l'autore di ogni operazione tramite AuditLog (RF-15).

L'intero router e' protetto da `require_doctor`: ogni endpoint richiede un JWT
valido con ruolo DOCTOR.
"""

from datetime import date, datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import (
    require_doctor,
    registra_audit,
    AZIONE_VISUALIZZA_SCHEDA,
    AZIONE_VISUALIZZA_GLICEMIE,
    AZIONE_CREA_TERAPIA,
    AZIONE_MODIFICA_TERAPIA,
    AZIONE_AGGIORNA_ANAMNESI,
)
from app.services.glicemia import aggrega_glicemie
from app.models import (
    User,
    PatientProfile,
    RilevazioneGlicemica,
    Terapia,
    Assunzione,
    Sintomo,
    PatologiaConcomitante,
    TerapiaParallela,
    Messaggio,
    Notifica,
)
from app.schemas import (
    DoctorProfileResponse,
    PatientProfileResponse,
    MedicoPazienteListItem,
    AnamnesiUpdate,
    RilevazioneGlicemicaResponse,
    GlicemiaAggregata,
    TerapiaCreate,
    TerapiaUpdate,
    TerapiaResponse,
    AssunzioneResponse,
    SintomoResponse,
    PatologiaConcomitanteResponse,
    TerapiaParallelaResponse,
    MessaggioCreate,
    MessaggioResponse,
    NotificaResponse,
)

router = APIRouter(
    prefix="/medico",
    tags=["Medico"],
    dependencies=[Depends(require_doctor)],  # tutto il router e' gated su ruolo medico
)


# =========================================================
# HELPER INTERNI
# =========================================================
def _get_paziente_o_404(db: Session, patient_id: int) -> PatientProfile:
    """Carica un paziente per id oppure solleva 404."""
    paziente = (
        db.query(PatientProfile).filter(PatientProfile.id == patient_id).first()
    )
    if paziente is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paziente non trovato.",
        )
    return paziente


# =========================================================
# PROFILO MEDICO
# =========================================================
@router.get("/me", response_model=DoctorProfileResponse)
def profilo_medico(current: User = Depends(require_doctor)):
    """Restituisce il profilo del medico attualmente autenticato."""
    return current.doctor_profile


# =========================================================
# PAZIENTI & DATI CLINICI (RF-9 + RF-15)
# =========================================================
@router.get("/pazienti", response_model=list[MedicoPazienteListItem])
def lista_pazienti(db: Session = Depends(get_db)):
    """
    Elenco di TUTTI i pazienti (RF-9: qualsiasi medico vede qualsiasi paziente),
    arricchito con n. notifiche aperte e ultimo valore glicemico per la lista.
    """
    pazienti = db.query(PatientProfile).all()

    risultato: list[MedicoPazienteListItem] = []
    for p in pazienti:
        # Ultima glicemia registrata (per uno sguardo d'insieme in lista)
        ultima = (
            db.query(RilevazioneGlicemica)
            .filter(RilevazioneGlicemica.patient_id == p.id)
            .order_by(RilevazioneGlicemica.timestamp.desc())
            .first()
        )
        # Notifiche del paziente ancora non risolte (verso qualunque medico)
        num_aperte = (
            db.query(Notifica)
            .filter(
                Notifica.paziente_riferimento_id == p.id,
                Notifica.risolta_at.is_(None),
            )
            .count()
        )
        risultato.append(
            MedicoPazienteListItem(
                id=p.id,
                nome=p.nome,
                cognome=p.cognome,
                doctor_id=p.doctor_id,
                num_notifiche_aperte=num_aperte,
                ultima_glicemia=ultima.valore if ultima else None,
            )
        )
    return risultato


@router.get("/pazienti/{patient_id}", response_model=PatientProfileResponse)
def scheda_paziente(
    patient_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(require_doctor),
):
    """Scheda completa del paziente (anagrafica + anamnesi). Tracciata (RF-15)."""
    paziente = _get_paziente_o_404(db, patient_id)
    registra_audit(db, current.id, AZIONE_VISUALIZZA_SCHEDA, patient_id)
    return paziente


@router.get(
    "/pazienti/{patient_id}/glicemie",
    response_model=list[RilevazioneGlicemicaResponse],
)
def glicemie_paziente(
    patient_id: int,
    da: Optional[date] = Query(None, description="Data inizio (inclusa)"),
    a: Optional[date] = Query(None, description="Data fine (inclusa)"),
    db: Session = Depends(get_db),
    current: User = Depends(require_doctor),
):
    """
    Rilevazioni glicemiche in dettaglio (RF-9), filtrabili per intervallo.
    Il campo `fuori_soglia` e' calcolato dallo schema (RNF-1). Tracciata (RF-15).
    """
    _get_paziente_o_404(db, patient_id)

    q = db.query(RilevazioneGlicemica).filter(
        RilevazioneGlicemica.patient_id == patient_id
    )
    if da is not None:
        q = q.filter(RilevazioneGlicemica.timestamp >= datetime(da.year, da.month, da.day))
    if a is not None:
        # fine giornata inclusa
        fine = datetime(a.year, a.month, a.day) + timedelta(days=1)
        q = q.filter(RilevazioneGlicemica.timestamp < fine)

    rilevazioni = q.order_by(RilevazioneGlicemica.timestamp.desc()).all()
    registra_audit(db, current.id, AZIONE_VISUALIZZA_GLICEMIE, patient_id)
    return rilevazioni


@router.get(
    "/pazienti/{patient_id}/glicemie/aggregato",
    response_model=list[GlicemiaAggregata],
)
def glicemie_aggregate(
    patient_id: int,
    periodo: str = Query("settimana", pattern="^(settimana|mese)$"),
    db: Session = Depends(get_db),
    current: User = Depends(require_doctor),
):
    """
    Andamento glicemico AGGREGATO per settimana o mese (RF-9).
    Per ogni periodo: media, minimo, massimo, n. misurazioni, n. fuori soglia.
    """
    _get_paziente_o_404(db, patient_id)

    rilevazioni = (
        db.query(RilevazioneGlicemica)
        .filter(RilevazioneGlicemica.patient_id == patient_id)
        .order_by(RilevazioneGlicemica.timestamp.asc())
        .all()
    )
    # Nessun audit qui: e' una vista derivata di dati gia' tracciati alla lettura.
    return aggrega_glicemie(rilevazioni, periodo)


@router.get(
    "/pazienti/{patient_id}/sintomi",
    response_model=list[SintomoResponse],
)
def sintomi_paziente(patient_id: int, db: Session = Depends(get_db)):
    """Sintomi segnalati dal paziente (RF-5, sola lettura per il medico)."""
    _get_paziente_o_404(db, patient_id)
    return (
        db.query(Sintomo)
        .filter(Sintomo.patient_id == patient_id)
        .order_by(Sintomo.data_inizio.desc())
        .all()
    )


@router.get(
    "/pazienti/{patient_id}/patologie-concomitanti",
    response_model=list[PatologiaConcomitanteResponse],
)
def patologie_concomitanti_paziente(patient_id: int, db: Session = Depends(get_db)):
    """Patologie concomitanti del paziente (RF-5, sola lettura)."""
    _get_paziente_o_404(db, patient_id)
    return (
        db.query(PatologiaConcomitante)
        .filter(PatologiaConcomitante.patient_id == patient_id)
        .order_by(PatologiaConcomitante.data_inizio.desc())
        .all()
    )


@router.get(
    "/pazienti/{patient_id}/terapie-parallele",
    response_model=list[TerapiaParallelaResponse],
)
def terapie_parallele_paziente(patient_id: int, db: Session = Depends(get_db)):
    """Terapie parallele dichiarate dal paziente (RF-5, sola lettura)."""
    _get_paziente_o_404(db, patient_id)
    return (
        db.query(TerapiaParallela)
        .filter(TerapiaParallela.patient_id == patient_id)
        .order_by(TerapiaParallela.data_inizio.desc())
        .all()
    )


@router.get(
    "/pazienti/{patient_id}/assunzioni",
    response_model=list[AssunzioneResponse],
)
def assunzioni_paziente(patient_id: int, db: Session = Depends(get_db)):
    """
    Assunzioni farmaci registrate dal paziente (RF-6): utili al medico per il
    confronto visivo con la terapia prescritta (RF-11 lato lettura).
    """
    _get_paziente_o_404(db, patient_id)
    return (
        db.query(Assunzione)
        .filter(Assunzione.patient_id == patient_id)
        .order_by(Assunzione.timestamp.desc())
        .all()
    )


# =========================================================
# TERAPIE (RF-8 / UC-8)
# =========================================================
@router.get(
    "/pazienti/{patient_id}/terapie",
    response_model=list[TerapiaResponse],
)
def terapie_paziente(patient_id: int, db: Session = Depends(get_db)):
    """Elenco delle terapie prescritte al paziente."""
    _get_paziente_o_404(db, patient_id)
    return (
        db.query(Terapia)
        .filter(Terapia.patient_id == patient_id)
        .order_by(Terapia.data_inizio.desc())
        .all()
    )


@router.post(
    "/pazienti/{patient_id}/terapie",
    response_model=TerapiaResponse,
    status_code=status.HTTP_201_CREATED,
)
def crea_terapia(
    patient_id: int,
    payload: TerapiaCreate,
    db: Session = Depends(get_db),
    current: User = Depends(require_doctor),
):
    """
    RF-8: il medico prescrive una nuova terapia.
    `doctor_id` deriva dal JWT (autore della prescrizione). Tracciata (RF-15).
    """
    _get_paziente_o_404(db, patient_id)

    # L'id del paziente nell'URL e' la fonte di verita': ignoriamo eventuali
    # discrepanze nel body e usiamo il path param.
    terapia = Terapia(
        patient_id=patient_id,
        doctor_id=current.doctor_profile.id,
        farmaco=payload.farmaco,
        assunzioni_giornaliere=payload.assunzioni_giornaliere,
        quantita=payload.quantita,
        unita=payload.unita,
        indicazioni=payload.indicazioni,
    )
    db.add(terapia)
    db.commit()
    db.refresh(terapia)

    registra_audit(db, current.id, AZIONE_CREA_TERAPIA, patient_id)
    return terapia


@router.put("/terapie/{terapia_id}", response_model=TerapiaResponse)
def modifica_terapia(
    terapia_id: int,
    payload: TerapiaUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(require_doctor),
):
    """
    RF-8: il medico modifica una prescrizione esistente (anche disattivandola
    tramite `is_active`). Tracciata (RF-15).
    """
    terapia = db.query(Terapia).filter(Terapia.id == terapia_id).first()
    if terapia is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Terapia non trovata.",
        )

    # Applica solo i campi effettivamente forniti (PATCH-like)
    dati = payload.model_dump(exclude_unset=True)
    for campo, valore in dati.items():
        setattr(terapia, campo, valore)

    db.commit()
    db.refresh(terapia)

    registra_audit(db, current.id, AZIONE_MODIFICA_TERAPIA, terapia.patient_id)
    return terapia


# =========================================================
# ANAMNESI (RF-10 / UC-10)
# =========================================================
@router.put(
    "/pazienti/{patient_id}/anamnesi",
    response_model=PatientProfileResponse,
)
def aggiorna_anamnesi(
    patient_id: int,
    payload: AnamnesiUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(require_doctor),
):
    """
    RF-10: il medico aggiorna fattori di rischio, patologie pregresse e
    comorbita' del paziente. Tracciata (RF-15).
    """
    paziente = _get_paziente_o_404(db, patient_id)

    dati = payload.model_dump(exclude_unset=True)
    for campo, valore in dati.items():
        setattr(paziente, campo, valore)

    db.commit()
    db.refresh(paziente)

    registra_audit(db, current.id, AZIONE_AGGIORNA_ANAMNESI, patient_id)
    return paziente


# =========================================================
# NOTIFICHE (RF-13/14) - sola lettura + gestione stato
# =========================================================
@router.get("/notifiche", response_model=list[NotificaResponse])
def lista_notifiche(
    solo_aperte: bool = Query(False, description="Solo notifiche non risolte"),
    db: Session = Depends(get_db),
    current: User = Depends(require_doctor),
):
    """
    Alert automatici destinati al medico (RF-13 mancata aderenza, RF-14 glicemia
    fuori soglia). In questa fase il medico li LEGGE soltanto: la generazione e'
    dell'attore Sistema.
    """
    q = db.query(Notifica).filter(Notifica.destinatario_id == current.id)
    if solo_aperte:
        q = q.filter(Notifica.risolta_at.is_(None))
    return q.order_by(Notifica.creato_at.desc()).all()


@router.patch("/notifiche/{notifica_id}/letta", response_model=NotificaResponse)
def segna_notifica_letta(
    notifica_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(require_doctor),
):
    """Segna una notifica come letta (imposta `letta_at` se non gia' presente)."""
    notifica = _get_notifica_del_medico_o_404(db, notifica_id, current.id)
    if notifica.letta_at is None:
        notifica.letta_at = datetime.utcnow()
        db.commit()
        db.refresh(notifica)
    return notifica


@router.patch("/notifiche/{notifica_id}/risolta", response_model=NotificaResponse)
def segna_notifica_risolta(
    notifica_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(require_doctor),
):
    """Segna una notifica come risolta (imposta `risolta_at` e, se serve, `letta_at`)."""
    notifica = _get_notifica_del_medico_o_404(db, notifica_id, current.id)
    now = datetime.utcnow()
    if notifica.letta_at is None:
        notifica.letta_at = now
    notifica.risolta_at = now
    db.commit()
    db.refresh(notifica)
    return notifica


def _get_notifica_del_medico_o_404(
    db: Session, notifica_id: int, medico_user_id: int
) -> Notifica:
    """Carica una notifica assicurandosi che sia indirizzata a questo medico."""
    notifica = (
        db.query(Notifica)
        .filter(
            Notifica.id == notifica_id,
            Notifica.destinatario_id == medico_user_id,
        )
        .first()
    )
    if notifica is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notifica non trovata.",
        )
    return notifica


# =========================================================
# MESSAGGI (RF-7) - lettura + risposta
# =========================================================
@router.get("/messaggi", response_model=list[MessaggioResponse])
def messaggi_ricevuti(
    db: Session = Depends(get_db),
    current: User = Depends(require_doctor),
):
    """Messaggi ricevuti dai pazienti (RF-7), dal piu' recente."""
    return (
        db.query(Messaggio)
        .filter(Messaggio.destinatario_id == current.id)
        .order_by(Messaggio.inviato_at.desc())
        .all()
    )


@router.post(
    "/messaggi",
    response_model=MessaggioResponse,
    status_code=status.HTTP_201_CREATED,
)
def rispondi_messaggio(
    payload: MessaggioCreate,
    db: Session = Depends(get_db),
    current: User = Depends(require_doctor),
):
    """
    Il medico invia una risposta/comunicazione a un utente (paziente).
    `mittente_id` deriva dal JWT.
    """
    destinatario = (
        db.query(User).filter(User.id == payload.destinatario_id).first()
    )
    if destinatario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Destinatario non trovato.",
        )

    messaggio = Messaggio(
        mittente_id=current.id,
        destinatario_id=payload.destinatario_id,
        oggetto=payload.oggetto,
        corpo=payload.corpo,
    )
    db.add(messaggio)
    db.commit()
    db.refresh(messaggio)
    return messaggio


@router.patch("/messaggi/{messaggio_id}/letto", response_model=MessaggioResponse)
def segna_messaggio_letto(
    messaggio_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(require_doctor),
):
    """Segna come letto un messaggio ricevuto dal medico."""
    messaggio = (
        db.query(Messaggio)
        .filter(
            Messaggio.id == messaggio_id,
            Messaggio.destinatario_id == current.id,
        )
        .first()
    )
    if messaggio is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Messaggio non trovato.",
        )
    if messaggio.letto_at is None:
        messaggio.letto_at = datetime.utcnow()
        db.commit()
        db.refresh(messaggio)
    return messaggio
