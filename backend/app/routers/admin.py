"""
Router dell'attore AMMINISTRATORE (Responsabile del Servizio).

Copre:
  RF-2 (UC-1)  Inserimento utenti iniziali (medici e pazienti) con credenziali
  RF-3 (UC-2)  Associazione paziente <-> medico di riferimento
  RF-15        Consultazione del registro audit (inalterabile)
  Extra        Modifica anagrafiche, reset password

Tutto il router e' protetto da `require_admin`.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin
from app.security import get_password_hash
from app.models import User, UserRole, DoctorProfile, PatientProfile, AuditLog
from app.schemas import (
    RegistrazioneMedicoRequest,
    RegistrazionePazienteRequest,
    UserWithProfileResponse,
    DoctorProfileResponse,
    PatientProfileResponse,
    AssociazioneMedico,
    AnagraficaUpdate,
    PasswordReset,
    AuditLogResponse,
    MessageResponse,
)

router = APIRouter(
    prefix="/admin",
    tags=["Amministratore"],
    dependencies=[Depends(require_admin)],
)


# =========================================================
# HELPER
# =========================================================
def _email_gia_usata(db: Session, email: str, escludi_user_id: Optional[int] = None) -> bool:
    """True se l'email e' gia' associata a un altro utente."""
    q = db.query(User).filter(User.email == email)
    if escludi_user_id is not None:
        q = q.filter(User.id != escludi_user_id)
    return q.first() is not None


def _get_utente_o_404(db: Session, user_id: int) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utente non trovato.")
    return user


# =========================================================
# CREAZIONE UTENTI (RF-2 / UC-1)
# =========================================================
@router.post(
    "/medici",
    response_model=UserWithProfileResponse,
    status_code=status.HTTP_201_CREATED,
)
def crea_medico(payload: RegistrazioneMedicoRequest, db: Session = Depends(get_db)):
    """RF-2: crea le credenziali e il profilo di un medico."""
    if _email_gia_usata(db, payload.user.email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email gia' registrata.")

    user = User(
        email=payload.user.email,
        password_hash=get_password_hash(payload.user.password),
        role=UserRole.DOCTOR,
        is_active=True,
    )
    db.add(user)
    db.flush()  # ottiene user.id

    profilo = DoctorProfile(
        user_id=user.id,
        nome=payload.profile.nome,
        cognome=payload.profile.cognome,
    )
    db.add(profilo)
    db.commit()
    db.refresh(user)
    return user


@router.post(
    "/pazienti",
    response_model=UserWithProfileResponse,
    status_code=status.HTTP_201_CREATED,
)
def crea_paziente(payload: RegistrazionePazienteRequest, db: Session = Depends(get_db)):
    """RF-2: crea le credenziali e il profilo di un paziente (con medico opzionale)."""
    if _email_gia_usata(db, payload.user.email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email gia' registrata.")

    # Se indicato, verifica che il medico di riferimento esista (RF-3)
    if payload.doctor_id is not None:
        if db.query(DoctorProfile).filter(DoctorProfile.id == payload.doctor_id).first() is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Medico di riferimento non valido.")

    user = User(
        email=payload.user.email,
        password_hash=get_password_hash(payload.user.password),
        role=UserRole.PATIENT,
        is_active=True,
    )
    db.add(user)
    db.flush()

    profilo = PatientProfile(
        user_id=user.id,
        doctor_id=payload.doctor_id,
        nome=payload.profile.nome,
        cognome=payload.profile.cognome,
        fattori_rischio=payload.profile.fattori_rischio,
        patologie_pregresse=payload.profile.patologie_pregresse,
        comorbita=payload.profile.comorbita,
    )
    db.add(profilo)
    db.commit()
    db.refresh(user)
    return user


# =========================================================
# ELENCHI
# =========================================================
@router.get("/utenti", response_model=list[UserWithProfileResponse])
def lista_utenti(db: Session = Depends(get_db)):
    """Elenco di tutti gli utenti con il relativo profilo."""
    return db.query(User).order_by(User.id).all()


@router.get("/medici", response_model=list[DoctorProfileResponse])
def lista_medici(db: Session = Depends(get_db)):
    """Elenco dei profili medico (utile per le associazioni RF-3)."""
    return db.query(DoctorProfile).order_by(DoctorProfile.cognome).all()


@router.get("/pazienti", response_model=list[PatientProfileResponse])
def lista_pazienti(db: Session = Depends(get_db)):
    """Elenco dei profili paziente."""
    return db.query(PatientProfile).order_by(PatientProfile.cognome).all()


# =========================================================
# ASSOCIAZIONE PAZIENTE-MEDICO (RF-3 / UC-2)
# =========================================================
@router.put("/pazienti/{patient_id}/medico", response_model=PatientProfileResponse)
def associa_medico(
    patient_id: int,
    payload: AssociazioneMedico,
    db: Session = Depends(get_db),
):
    """RF-3: assegna o cambia il medico di riferimento del paziente."""
    paziente = db.query(PatientProfile).filter(PatientProfile.id == patient_id).first()
    if paziente is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paziente non trovato.")

    if payload.doctor_id is not None:
        if db.query(DoctorProfile).filter(DoctorProfile.id == payload.doctor_id).first() is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Medico non valido.")

    paziente.doctor_id = payload.doctor_id
    db.commit()
    db.refresh(paziente)
    return paziente


# =========================================================
# MODIFICA ANAGRAFICA + RESET PASSWORD (extra)
# =========================================================
@router.put("/utenti/{user_id}/anagrafica", response_model=UserWithProfileResponse)
def modifica_anagrafica(
    user_id: int,
    payload: AnagraficaUpdate,
    db: Session = Depends(get_db),
):
    """Aggiorna email (User) e nome/cognome (profilo medico o paziente)."""
    user = _get_utente_o_404(db, user_id)

    if payload.email is not None and payload.email != user.email:
        if _email_gia_usata(db, payload.email, escludi_user_id=user.id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email gia' registrata.")
        user.email = payload.email

    # Il profilo puo' essere medico o paziente (l'admin non ha profilo)
    profilo = user.doctor_profile or user.patient_profile
    if profilo is not None:
        if payload.nome is not None:
            profilo.nome = payload.nome
        if payload.cognome is not None:
            profilo.cognome = payload.cognome

    db.commit()
    db.refresh(user)
    return user


@router.post("/utenti/{user_id}/reset-password", response_model=MessageResponse)
def reset_password(
    user_id: int,
    payload: PasswordReset,
    db: Session = Depends(get_db),
):
    """Imposta una nuova password per l'utente (hash bcrypt)."""
    user = _get_utente_o_404(db, user_id)
    user.password_hash = get_password_hash(payload.password)
    db.commit()
    return {"message": "Password aggiornata con successo."}


# =========================================================
# REGISTRO AUDIT (RF-15) - sola consultazione
# =========================================================
@router.get("/audit-logs", response_model=list[AuditLogResponse])
def registro_audit(
    paziente_id: Optional[int] = Query(None, description="Filtra per paziente"),
    db: Session = Depends(get_db),
):
    """RF-15: consultazione del registro inalterabile delle operazioni dei medici."""
    q = db.query(AuditLog)
    if paziente_id is not None:
        q = q.filter(AuditLog.target_paziente_id == paziente_id)
    return q.order_by(AuditLog.timestamp.desc()).all()
