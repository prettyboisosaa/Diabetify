"""
Router dell'attore PAZIENTE.

Copre i requisiti lato paziente:
  RF-4 (UC-4)  Registrazione rilevazioni glicemiche
  RF-5 (UC-5)  Registrazione sintomi, patologie concomitanti, terapie parallele
  RF-6 (UC-6)  Registrazione assunzione farmaci
  RF-7 (UC-7)  Comunicazione col proprio medico di riferimento
  RF-9 (self)  Consultazione dei propri dati e delle terapie prescritte
  RF-12/13     Lettura di solleciti/alert automatici (sola lettura in questa fase)

Regole di scope:
  - Glicemie e assunzioni sono voci di LOG: solo creazione + lettura (immutabili).
  - Sintomi/patologie/terapie parallele sono un DIARIO: creabili e modificabili.
  - Il paziente opera SEMPRE e solo sui propri dati: `patient_id` deriva dal JWT.

L'intero router e' protetto da `require_patient`.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_patient
from app.services.glicemia import aggrega_glicemie
from app.services.sistema import verifica_glicemia
from app.models import (
    User,
    DoctorProfile,
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
    PatientProfileResponse,
    RilevazioneGlicemicaCreate,
    RilevazioneGlicemicaResponse,
    GlicemiaAggregata,
    TerapiaResponse,
    AssunzioneCreate,
    AssunzioneResponse,
    SintomoCreate,
    SintomoUpdate,
    SintomoResponse,
    PatologiaConcomitanteCreate,
    PatologiaConcomitanteUpdate,
    PatologiaConcomitanteResponse,
    TerapiaParallelaCreate,
    TerapiaParallelaUpdate,
    TerapiaParallelaResponse,
    MessaggioPazienteCreate,
    MessaggioResponse,
    NotificaResponse,
)

router = APIRouter(
    prefix="/paziente",
    tags=["Paziente"],
    dependencies=[Depends(require_patient)],  # tutto il router e' gated su ruolo paziente
)


# =========================================================
# HELPER: applica un update parziale a una voce del diario
# =========================================================
def _applica_update(oggetto, payload) -> None:
    """Applica i soli campi forniti (PATCH-like) a un oggetto ORM."""
    for campo, valore in payload.model_dump(exclude_unset=True).items():
        setattr(oggetto, campo, valore)


# =========================================================
# PROFILO PAZIENTE
# =========================================================
@router.get("/me", response_model=PatientProfileResponse)
def profilo_paziente(current: User = Depends(require_patient)):
    """Restituisce il profilo del paziente attualmente autenticato."""
    return current.patient_profile


# =========================================================
# GLICEMIE (RF-4) - immutabili
# =========================================================
@router.post(
    "/glicemie",
    response_model=RilevazioneGlicemicaResponse,
    status_code=status.HTTP_201_CREATED,
)
def registra_glicemia(
    payload: RilevazioneGlicemicaCreate,
    db: Session = Depends(get_db),
    current: User = Depends(require_patient),
):
    """RF-4: il paziente registra una rilevazione (valore + prima/dopo pasto)."""
    rilevazione = RilevazioneGlicemica(
        patient_id=current.patient_profile.id,
        valore=payload.valore,
        momento=payload.momento,
    )
    db.add(rilevazione)
    db.commit()
    db.refresh(rilevazione)

    # RF-14 (event-driven): il Sistema verifica subito la soglia e, se superata,
    # notifica il medico di riferimento con severita' variabile.
    verifica_glicemia(db, rilevazione)

    return rilevazione


@router.get("/glicemie", response_model=list[RilevazioneGlicemicaResponse])
def mie_glicemie(
    db: Session = Depends(get_db),
    current: User = Depends(require_patient),
):
    """Elenco delle proprie rilevazioni (con `fuori_soglia` calcolato)."""
    return (
        db.query(RilevazioneGlicemica)
        .filter(RilevazioneGlicemica.patient_id == current.patient_profile.id)
        .order_by(RilevazioneGlicemica.timestamp.desc())
        .all()
    )


@router.get("/glicemie/aggregato", response_model=list[GlicemiaAggregata])
def mie_glicemie_aggregate(
    periodo: str = Query("settimana", pattern="^(settimana|mese)$"),
    db: Session = Depends(get_db),
    current: User = Depends(require_patient),
):
    """RF-9 (self): andamento aggregato settimana/mese delle proprie glicemie."""
    rilevazioni = (
        db.query(RilevazioneGlicemica)
        .filter(RilevazioneGlicemica.patient_id == current.patient_profile.id)
        .order_by(RilevazioneGlicemica.timestamp.asc())
        .all()
    )
    return aggrega_glicemie(rilevazioni, periodo)


# =========================================================
# TERAPIE PRESCRITTE (sola lettura) + ASSUNZIONI (RF-6)
# =========================================================
@router.get("/terapie", response_model=list[TerapiaResponse])
def mie_terapie(
    db: Session = Depends(get_db),
    current: User = Depends(require_patient),
):
    """Terapie prescritte dal medico (sola lettura): dicono cosa assumere."""
    return (
        db.query(Terapia)
        .filter(Terapia.patient_id == current.patient_profile.id)
        .order_by(Terapia.data_inizio.desc())
        .all()
    )


@router.post(
    "/assunzioni",
    response_model=AssunzioneResponse,
    status_code=status.HTTP_201_CREATED,
)
def registra_assunzione(
    payload: AssunzioneCreate,
    db: Session = Depends(get_db),
    current: User = Depends(require_patient),
):
    """
    RF-6: il paziente registra l'assunzione di un farmaco, collegandola a una
    terapia prescritta. Si verifica che la terapia appartenga al paziente.
    """
    terapia = (
        db.query(Terapia)
        .filter(
            Terapia.id == payload.terapia_id,
            Terapia.patient_id == current.patient_profile.id,
        )
        .first()
    )
    if terapia is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Terapia non trovata tra le tue prescrizioni.",
        )

    assunzione = Assunzione(
        patient_id=current.patient_profile.id,
        terapia_id=payload.terapia_id,
        farmaco=payload.farmaco,
        quantita_assunta=payload.quantita_assunta,
        unita=payload.unita,
    )
    db.add(assunzione)
    db.commit()
    db.refresh(assunzione)
    return assunzione


@router.get("/assunzioni", response_model=list[AssunzioneResponse])
def mie_assunzioni(
    db: Session = Depends(get_db),
    current: User = Depends(require_patient),
):
    """Elenco delle proprie assunzioni registrate."""
    return (
        db.query(Assunzione)
        .filter(Assunzione.patient_id == current.patient_profile.id)
        .order_by(Assunzione.timestamp.desc())
        .all()
    )


# =========================================================
# DIARIO CLINICO (RF-5) - sintomi / patologie / terapie parallele (editabile)
# =========================================================

# ----- Sintomi -----
@router.get("/sintomi", response_model=list[SintomoResponse])
def miei_sintomi(db: Session = Depends(get_db), current: User = Depends(require_patient)):
    return (
        db.query(Sintomo)
        .filter(Sintomo.patient_id == current.patient_profile.id)
        .order_by(Sintomo.data_inizio.desc())
        .all()
    )


@router.post("/sintomi", response_model=SintomoResponse, status_code=status.HTTP_201_CREATED)
def crea_sintomo(
    payload: SintomoCreate,
    db: Session = Depends(get_db),
    current: User = Depends(require_patient),
):
    """RF-5: segnala un sintomo indicandone il periodo."""
    sintomo = Sintomo(patient_id=current.patient_profile.id, **payload.model_dump())
    db.add(sintomo)
    db.commit()
    db.refresh(sintomo)
    return sintomo


@router.put("/sintomi/{sintomo_id}", response_model=SintomoResponse)
def modifica_sintomo(
    sintomo_id: int,
    payload: SintomoUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(require_patient),
):
    """RF-5: aggiorna un sintomo (es. chiuderlo impostando la data di fine)."""
    sintomo = _get_voce_o_404(db, Sintomo, sintomo_id, current.patient_profile.id)
    _applica_update(sintomo, payload)
    db.commit()
    db.refresh(sintomo)
    return sintomo


# ----- Patologie concomitanti -----
@router.get("/patologie-concomitanti", response_model=list[PatologiaConcomitanteResponse])
def mie_patologie(db: Session = Depends(get_db), current: User = Depends(require_patient)):
    return (
        db.query(PatologiaConcomitante)
        .filter(PatologiaConcomitante.patient_id == current.patient_profile.id)
        .order_by(PatologiaConcomitante.data_inizio.desc())
        .all()
    )


@router.post(
    "/patologie-concomitanti",
    response_model=PatologiaConcomitanteResponse,
    status_code=status.HTTP_201_CREATED,
)
def crea_patologia(
    payload: PatologiaConcomitanteCreate,
    db: Session = Depends(get_db),
    current: User = Depends(require_patient),
):
    patologia = PatologiaConcomitante(
        patient_id=current.patient_profile.id, **payload.model_dump()
    )
    db.add(patologia)
    db.commit()
    db.refresh(patologia)
    return patologia


@router.put(
    "/patologie-concomitanti/{patologia_id}",
    response_model=PatologiaConcomitanteResponse,
)
def modifica_patologia(
    patologia_id: int,
    payload: PatologiaConcomitanteUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(require_patient),
):
    patologia = _get_voce_o_404(
        db, PatologiaConcomitante, patologia_id, current.patient_profile.id
    )
    _applica_update(patologia, payload)
    db.commit()
    db.refresh(patologia)
    return patologia


# ----- Terapie parallele -----
@router.get("/terapie-parallele", response_model=list[TerapiaParallelaResponse])
def mie_terapie_parallele(db: Session = Depends(get_db), current: User = Depends(require_patient)):
    return (
        db.query(TerapiaParallela)
        .filter(TerapiaParallela.patient_id == current.patient_profile.id)
        .order_by(TerapiaParallela.data_inizio.desc())
        .all()
    )


@router.post(
    "/terapie-parallele",
    response_model=TerapiaParallelaResponse,
    status_code=status.HTTP_201_CREATED,
)
def crea_terapia_parallela(
    payload: TerapiaParallelaCreate,
    db: Session = Depends(get_db),
    current: User = Depends(require_patient),
):
    tp = TerapiaParallela(patient_id=current.patient_profile.id, **payload.model_dump())
    db.add(tp)
    db.commit()
    db.refresh(tp)
    return tp


@router.put(
    "/terapie-parallele/{terapia_id}",
    response_model=TerapiaParallelaResponse,
)
def modifica_terapia_parallela(
    terapia_id: int,
    payload: TerapiaParallelaUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(require_patient),
):
    tp = _get_voce_o_404(db, TerapiaParallela, terapia_id, current.patient_profile.id)
    _applica_update(tp, payload)
    db.commit()
    db.refresh(tp)
    return tp


def _get_voce_o_404(db: Session, Model, voce_id: int, patient_id: int):
    """Carica una voce del diario assicurandosi che appartenga al paziente."""
    voce = (
        db.query(Model)
        .filter(Model.id == voce_id, Model.patient_id == patient_id)
        .first()
    )
    if voce is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Voce non trovata.",
        )
    return voce


# =========================================================
# MESSAGGI (RF-7) - lettura + invio al proprio medico
# =========================================================
@router.get("/messaggi", response_model=list[MessaggioResponse])
def miei_messaggi(
    db: Session = Depends(get_db),
    current: User = Depends(require_patient),
):
    """Messaggi ricevuti (es. risposte del medico), dal piu' recente."""
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
def invia_messaggio_al_medico(
    payload: MessaggioPazienteCreate,
    db: Session = Depends(get_db),
    current: User = Depends(require_patient),
):
    """
    RF-7: il paziente invia una comunicazione al proprio medico di riferimento.
    Il destinatario e' ricavato da PatientProfile.doctor_id (non scelto dall'utente).
    """
    doctor_id = current.patient_profile.doctor_id
    if doctor_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nessun medico di riferimento associato al tuo profilo.",
        )

    # Risale allo User del medico (il messaggio collega utenti, non profili)
    medico = db.query(DoctorProfile).filter(DoctorProfile.id == doctor_id).first()
    if medico is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Medico di riferimento non valido.",
        )

    messaggio = Messaggio(
        mittente_id=current.id,
        destinatario_id=medico.user_id,
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
    current: User = Depends(require_patient),
):
    """Segna come letto un messaggio ricevuto dal paziente."""
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


# =========================================================
# NOTIFICHE (RF-12/13) - sola lettura + gestione stato
# =========================================================
@router.get("/notifiche", response_model=list[NotificaResponse])
def mie_notifiche(
    solo_aperte: bool = Query(False, description="Solo notifiche non risolte"),
    db: Session = Depends(get_db),
    current: User = Depends(require_patient),
):
    """
    Solleciti/alert automatici destinati al paziente (RF-12 completamento
    assunzioni, RF-13 dimenticanza farmaci). Sola lettura: la generazione e'
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
    current: User = Depends(require_patient),
):
    notifica = _get_notifica_del_paziente_o_404(db, notifica_id, current.id)
    if notifica.letta_at is None:
        notifica.letta_at = datetime.utcnow()
        db.commit()
        db.refresh(notifica)
    return notifica


@router.patch("/notifiche/{notifica_id}/risolta", response_model=NotificaResponse)
def segna_notifica_risolta(
    notifica_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(require_patient),
):
    notifica = _get_notifica_del_paziente_o_404(db, notifica_id, current.id)
    now = datetime.utcnow()
    if notifica.letta_at is None:
        notifica.letta_at = now
    notifica.risolta_at = now
    db.commit()
    db.refresh(notifica)
    return notifica


def _get_notifica_del_paziente_o_404(
    db: Session, notifica_id: int, paziente_user_id: int
) -> Notifica:
    """Carica una notifica assicurandosi che sia indirizzata a questo paziente."""
    notifica = (
        db.query(Notifica)
        .filter(
            Notifica.id == notifica_id,
            Notifica.destinatario_id == paziente_user_id,
        )
        .first()
    )
    if notifica is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notifica non trovata.",
        )
    return notifica
