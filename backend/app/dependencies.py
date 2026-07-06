"""
Dependency FastAPI TRASVERSALI per l'autorizzazione e la tracciabilita'.

- get_current_user : decodifica il JWT -> carica lo User dal DB (RF-1/RNF-2)
- require_doctor    : guardia di ruolo per gli endpoint del medico
- registra_audit    : helper append-only per il log delle operazioni (RF-15)

Molti schemi in `schemas.py` assumono che gli id (patient_id, doctor_id,
mittente_id...) derivino "dal token JWT": e' qui che quel token viene verificato.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import jwt

from app.database import get_db
from app.models import User, UserRole, AuditLog
from app.schemas import TokenData
from app.security import SECRET_KEY, ALGORITHM


# Lo schema OAuth2: punta all'endpoint di login (che non ha prefix -> "login").
# Serve anche a Swagger per mostrare il pulsante "Authorize".
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


# =========================================================
# COSTANTI AZIONI DI AUDIT (RF-15)
# =========================================================
# Stringhe tipizzate per evitare typo sparsi nei router.
AZIONE_VISUALIZZA_SCHEDA = "VISUALIZZAZIONE_SCHEDA"
AZIONE_VISUALIZZA_GLICEMIE = "VISUALIZZAZIONE_GLICEMIE"
AZIONE_CREA_TERAPIA = "CREAZIONE_TERAPIA"
AZIONE_MODIFICA_TERAPIA = "MODIFICA_TERAPIA"
AZIONE_AGGIORNA_ANAMNESI = "AGGIORNAMENTO_ANAMNESI"


# =========================================================
# AUTENTICAZIONE
# =========================================================
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Decodifica e valida il JWT, quindi restituisce lo User corrispondente.
    Solleva 401 se il token e' assente/scaduto/malformato o l'utente non esiste,
    400 se l'account e' stato disattivato.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenziali non valide o sessione scaduta",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # jwt.decode verifica automaticamente la firma e la scadenza (exp)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str | None = payload.get("sub")
        role: str | None = payload.get("role")
        if email is None:
            raise credentials_exception
        # TokenData e' gia' definito in schemas.py: lo usiamo per coerenza
        token_data = TokenData(email=email, role=role)
    except jwt.PyJWTError:
        raise credentials_exception

    user = db.query(User).filter(User.email == token_data.email).first()
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Questo account e' stato disattivato.",
        )

    return user


# =========================================================
# GUARDIA DI RUOLO: MEDICO
# =========================================================
def require_doctor(current_user: User = Depends(get_current_user)) -> User:
    """
    Consente l'accesso solo agli utenti con ruolo DOCTOR.
    Verifica anche l'esistenza del profilo medico (necessario per doctor_id).
    """
    if current_user.role != UserRole.DOCTOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accesso riservato ai medici.",
        )
    if current_user.doctor_profile is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Profilo medico non configurato.",
        )
    return current_user


# =========================================================
# GUARDIA DI RUOLO: PAZIENTE
# =========================================================
def require_patient(current_user: User = Depends(get_current_user)) -> User:
    """
    Consente l'accesso solo agli utenti con ruolo PATIENT.
    Verifica anche l'esistenza del profilo paziente (necessario per patient_id).
    """
    if current_user.role != UserRole.PATIENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accesso riservato ai pazienti.",
        )
    if current_user.patient_profile is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Profilo paziente non configurato.",
        )
    return current_user


# =========================================================
# GUARDIA DI RUOLO: AMMINISTRATORE (Responsabile del Servizio)
# =========================================================
def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Consente l'accesso solo agli utenti con ruolo ADMIN."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accesso riservato agli amministratori.",
        )
    return current_user


# =========================================================
# TRACCIABILITA' DELLE OPERAZIONI (RF-15)
# =========================================================
def registra_audit(
    db: Session,
    operator_id: int,
    azione: str,
    target_paziente_id: int | None = None,
) -> None:
    """
    Registra in modo APPEND-ONLY un'operazione sensibile del medico.
    I log non vengono mai aggiornati/cancellati (RNF-2: log inalterabili).
    Committa autonomamente per garantire la persistenza anche se la richiesta
    prosegue con altre operazioni.
    """
    log = AuditLog(
        operator_id=operator_id,
        azione=azione,
        target_paziente_id=target_paziente_id,
    )
    db.add(log)
    db.commit()
