import re
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    computed_field,
    field_validator,
)

from app.models import (
    UserRole,
    MomentoGlicemia,
    UnitaMisura,
    GravitaSintomo,
    TipoNotifica,
    SeveritaNotifica,
)


# =========================================================
# BASE COMUNE per gli schemi che leggono da SQLAlchemy
# =========================================================

class ORMBase(BaseModel):
    """Base con configurazione Pydantic v2 per leggere oggetti ORM."""
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


# =========================================================
# VALIDATOR RIUSABILI
# =========================================================

_PASSWORD_PATTERN_MSG = (
    "Password deve contenere almeno una maiuscola, una minuscola, "
    "una cifra e un carattere speciale"
)


def _validate_password_complessa(v: str) -> str:
    if (
        not re.search(r"[A-Z]", v)
        or not re.search(r"[a-z]", v)
        or not re.search(r"\d", v)
        or not re.search(r"[^A-Za-z0-9]", v)
    ):
        raise ValueError(_PASSWORD_PATTERN_MSG)
    return v


# =========================================================
# UTENTE & AUTENTICAZIONE (RF-1, RF-2, UC-3)
# =========================================================

class UserBase(BaseModel):
    email: EmailStr
    role: UserRole


class UserCreateByAdmin(UserBase):
    """Creazione utente da parte dell'Amministratore (RF-2). Il role e' scelto dall'admin."""
    password: str = Field(..., min_length=12, max_length=128)

    @field_validator("password")
    @classmethod
    def password_complessa(cls, v: str) -> str:
        return _validate_password_complessa(v)


class UserSelfRegister(BaseModel):
    """Auto-registrazione: role NON esposto, forzato a PATIENT lato logica."""
    email: EmailStr
    password: str = Field(..., min_length=12, max_length=128)

    @field_validator("password")
    @classmethod
    def password_complessa(cls, v: str) -> str:
        return _validate_password_complessa(v)


# Alias di compatibilita' con il vecchio nome
UserCreate = UserCreateByAdmin


class UserResponse(ORMBase, UserBase):
    id: int
    is_active: bool


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: UserRole


class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[UserRole] = None


# =========================================================
# PROFILI (Medico e Paziente) - RF-2, RF-3, RF-10
# =========================================================

class DoctorProfileBase(BaseModel):
    nome: str = Field(..., min_length=1, max_length=100)
    cognome: str = Field(..., min_length=1, max_length=100)


class DoctorProfileCreate(DoctorProfileBase):
    user_id: int


class DoctorProfileResponse(ORMBase, DoctorProfileBase):
    id: int
    user_id: int


class PatientProfileBase(BaseModel):
    nome: str = Field(..., min_length=1, max_length=100)
    cognome: str = Field(..., min_length=1, max_length=100)
    fattori_rischio: Optional[str] = Field(None, max_length=2000)
    patologie_pregresse: Optional[str] = Field(None, max_length=2000)
    comorbita: Optional[str] = Field(None, max_length=2000)


class PatientProfileCreate(PatientProfileBase):
    user_id: int
    doctor_id: Optional[int] = None


class PatientProfileUpdate(BaseModel):
    """RF-10: il medico aggiorna anamnesi del paziente. Tutti i campi opzionali."""
    fattori_rischio: Optional[str] = Field(None, max_length=2000)
    patologie_pregresse: Optional[str] = Field(None, max_length=2000)
    comorbita: Optional[str] = Field(None, max_length=2000)
    doctor_id: Optional[int] = None


class PatientProfileResponse(ORMBase, PatientProfileBase):
    id: int
    user_id: int
    doctor_id: Optional[int] = None


class AnamnesiUpdate(BaseModel):
    """
    RF-10 / UC-10: il medico aggiorna SOLO l'anamnesi del paziente.
    A differenza di PatientProfileUpdate non espone `doctor_id`
    (l'associazione paziente-medico e' competenza dell'Amministratore, RF-3).
    Tutti i campi sono opzionali: si aggiornano solo quelli forniti.
    """
    fattori_rischio: Optional[str] = Field(None, max_length=2000)
    patologie_pregresse: Optional[str] = Field(None, max_length=2000)
    comorbita: Optional[str] = Field(None, max_length=2000)


class MedicoPazienteListItem(ORMBase):
    """
    Riga sintetica per l'elenco pazienti lato medico (RF-9).
    Arricchisce il profilo con qualche dato aggregato utile a colpo d'occhio.
    """
    id: int
    nome: str
    cognome: str
    doctor_id: Optional[int] = None
    num_notifiche_aperte: int = 0
    ultima_glicemia: Optional[int] = None


# Composito per ridurre round-trip lato frontend
class UserWithProfileResponse(UserResponse):
    doctor_profile: Optional[DoctorProfileResponse] = None
    patient_profile: Optional[PatientProfileResponse] = None


# UC-1 atomico: creazione utente + profilo in unica request
class RegistrazionePazienteRequest(BaseModel):
    user: UserCreateByAdmin
    profile: PatientProfileBase
    doctor_id: Optional[int] = None


class RegistrazioneMedicoRequest(BaseModel):
    user: UserCreateByAdmin
    profile: DoctorProfileBase


# --- Operazioni amministrative (RF-2, RF-3, extra) ---

class AssociazioneMedico(BaseModel):
    """RF-3 / UC-2: l'admin assegna (o rimuove) il medico di riferimento."""
    doctor_id: Optional[int] = None


class AnagraficaUpdate(BaseModel):
    """L'admin corregge l'anagrafica di un utente. Campi opzionali."""
    nome: Optional[str] = Field(None, min_length=1, max_length=100)
    cognome: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None


class PasswordReset(BaseModel):
    """L'admin imposta una nuova password per un utente."""
    password: str = Field(..., min_length=12, max_length=128)

    @field_validator("password")
    @classmethod
    def password_complessa(cls, v: str) -> str:
        return _validate_password_complessa(v)


# =========================================================
# RILEVAZIONI GLICEMICHE (RF-4, RF-14, RNF-1)
# =========================================================

# Soglie cliniche (RNF-1)
SOGLIA_PRIMA_PASTO_MIN = 80
SOGLIA_PRIMA_PASTO_MAX = 130
SOGLIA_DOPO_PASTO_MAX = 180


class RilevazioneGlicemicaBase(BaseModel):
    valore: int = Field(..., gt=0, lt=600, description="Valore glicemia in mg/dL")
    momento: MomentoGlicemia


class RilevazioneGlicemicaCreate(RilevazioneGlicemicaBase):
    """patient_id deriva dal token JWT del paziente."""
    pass


class RilevazioneGlicemicaResponse(ORMBase, RilevazioneGlicemicaBase):
    id: int
    patient_id: int
    timestamp: datetime

    @computed_field  # type: ignore[misc]
    @property
    def fuori_soglia(self) -> bool:
        # Confronta con stringa perche' use_enum_values=True serializza l'enum a str
        if self.momento == MomentoGlicemia.PRIMA_PASTO.value:
            return (
                self.valore < SOGLIA_PRIMA_PASTO_MIN
                or self.valore > SOGLIA_PRIMA_PASTO_MAX
            )
        return self.valore > SOGLIA_DOPO_PASTO_MAX


class GlicemiaAggregata(BaseModel):
    """RF-9: andamento aggregato settimanale/mensile."""
    periodo_inizio: date
    periodo_fine: date
    media: float
    minimo: int
    massimo: int
    num_misurazioni: int
    num_fuori_soglia: int


# =========================================================
# TERAPIE (RF-8, RF-11)
# =========================================================

class TerapiaBase(BaseModel):
    farmaco: str = Field(..., min_length=1, max_length=200)
    assunzioni_giornaliere: int = Field(..., gt=0, le=24)
    quantita: Decimal = Field(..., gt=0, max_digits=10, decimal_places=3)
    unita: UnitaMisura
    indicazioni: Optional[str] = Field(None, max_length=500)


class TerapiaCreate(TerapiaBase):
    patient_id: int  # doctor_id dal token JWT del medico


class TerapiaUpdate(BaseModel):
    """RF-8: il medico modifica una prescrizione esistente."""
    farmaco: Optional[str] = Field(None, min_length=1, max_length=200)
    assunzioni_giornaliere: Optional[int] = Field(None, gt=0, le=24)
    quantita: Optional[Decimal] = Field(None, gt=0, max_digits=10, decimal_places=3)
    unita: Optional[UnitaMisura] = None
    indicazioni: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class TerapiaResponse(ORMBase, TerapiaBase):
    id: int
    patient_id: int
    doctor_id: int
    data_inizio: datetime
    is_active: bool


# =========================================================
# ASSUNZIONI (RF-6, RF-11)
# =========================================================

class AssunzioneBase(BaseModel):
    farmaco: str = Field(..., min_length=1, max_length=200)
    quantita_assunta: Decimal = Field(..., gt=0, max_digits=10, decimal_places=3)
    unita: UnitaMisura


class AssunzioneCreate(AssunzioneBase):
    terapia_id: int
    # patient_id deriva dal token JWT


class AssunzioneResponse(ORMBase, AssunzioneBase):
    id: int
    patient_id: int
    terapia_id: int
    timestamp: datetime


# =========================================================
# SINTOMI (RF-5)
# =========================================================

class SintomoBase(BaseModel):
    descrizione: str = Field(..., min_length=1, max_length=300)
    gravita: Optional[GravitaSintomo] = None
    data_inizio: date
    data_fine: Optional[date] = None
    note: Optional[str] = Field(None, max_length=2000)

    @field_validator("data_fine")
    @classmethod
    def fine_dopo_inizio(cls, v: Optional[date], info) -> Optional[date]:
        inizio = info.data.get("data_inizio")
        if v is not None and inizio is not None and v < inizio:
            raise ValueError("data_fine non puo' essere precedente a data_inizio")
        return v


class SintomoCreate(SintomoBase):
    pass  # patient_id da JWT


class SintomoUpdate(BaseModel):
    descrizione: Optional[str] = Field(None, min_length=1, max_length=300)
    gravita: Optional[GravitaSintomo] = None
    data_inizio: Optional[date] = None
    data_fine: Optional[date] = None
    note: Optional[str] = Field(None, max_length=2000)


class SintomoResponse(ORMBase, SintomoBase):
    id: int
    patient_id: int


# =========================================================
# PATOLOGIE CONCOMITANTI (RF-5)
# =========================================================

class PatologiaConcomitanteBase(BaseModel):
    descrizione: str = Field(..., min_length=1, max_length=300)
    data_inizio: date
    data_fine: Optional[date] = None
    note: Optional[str] = Field(None, max_length=2000)

    @field_validator("data_fine")
    @classmethod
    def fine_dopo_inizio(cls, v: Optional[date], info) -> Optional[date]:
        inizio = info.data.get("data_inizio")
        if v is not None and inizio is not None and v < inizio:
            raise ValueError("data_fine non puo' essere precedente a data_inizio")
        return v


class PatologiaConcomitanteCreate(PatologiaConcomitanteBase):
    pass


class PatologiaConcomitanteUpdate(BaseModel):
    """RF-5: il paziente aggiorna una patologia concomitante (es. data fine)."""
    descrizione: Optional[str] = Field(None, min_length=1, max_length=300)
    data_inizio: Optional[date] = None
    data_fine: Optional[date] = None
    note: Optional[str] = Field(None, max_length=2000)


class PatologiaConcomitanteResponse(ORMBase, PatologiaConcomitanteBase):
    id: int
    patient_id: int


# =========================================================
# TERAPIE PARALLELE (RF-5)
# =========================================================

class TerapiaParallelaBase(BaseModel):
    farmaco: str = Field(..., min_length=1, max_length=200)
    posologia: Optional[str] = Field(None, max_length=500)
    data_inizio: date
    data_fine: Optional[date] = None
    note: Optional[str] = Field(None, max_length=2000)

    @field_validator("data_fine")
    @classmethod
    def fine_dopo_inizio(cls, v: Optional[date], info) -> Optional[date]:
        inizio = info.data.get("data_inizio")
        if v is not None and inizio is not None and v < inizio:
            raise ValueError("data_fine non puo' essere precedente a data_inizio")
        return v


class TerapiaParallelaCreate(TerapiaParallelaBase):
    pass


class TerapiaParallelaUpdate(BaseModel):
    """RF-5: il paziente aggiorna una terapia parallela (es. data fine, posologia)."""
    farmaco: Optional[str] = Field(None, min_length=1, max_length=200)
    posologia: Optional[str] = Field(None, max_length=500)
    data_inizio: Optional[date] = None
    data_fine: Optional[date] = None
    note: Optional[str] = Field(None, max_length=2000)


class TerapiaParallelaResponse(ORMBase, TerapiaParallelaBase):
    id: int
    patient_id: int


# =========================================================
# MESSAGGI (RF-7)
# =========================================================

class MessaggioCreate(BaseModel):
    destinatario_id: int
    oggetto: str = Field(..., min_length=1, max_length=200)
    corpo: str = Field(..., min_length=1, max_length=5000)
    # mittente_id dal JWT


class MessaggioPazienteCreate(BaseModel):
    """
    RF-7: il paziente scrive al PROPRIO medico di riferimento. Il destinatario
    non e' esposto: viene ricavato server-side da PatientProfile.doctor_id.
    """
    oggetto: str = Field(..., min_length=1, max_length=200)
    corpo: str = Field(..., min_length=1, max_length=5000)


class MessaggioResponse(ORMBase):
    id: int
    mittente_id: int
    destinatario_id: int
    oggetto: str
    corpo: str
    inviato_at: datetime
    letto_at: Optional[datetime] = None


# =========================================================
# NOTIFICHE (RF-12, RF-13, RF-14) - solo lettura: create dal sistema
# =========================================================

class NotificaResponse(ORMBase):
    id: int
    destinatario_id: int
    paziente_riferimento_id: Optional[int] = None
    tipo: TipoNotifica
    severita: SeveritaNotifica
    messaggio: str
    creato_at: datetime
    letta_at: Optional[datetime] = None
    risolta_at: Optional[datetime] = None


# =========================================================
# AUDIT LOG (RF-15) - solo lettura, riservato all'admin
# =========================================================

class AuditLogResponse(ORMBase):
    id: int
    operator_id: int
    azione: str
    target_paziente_id: Optional[int] = None
    timestamp: datetime


# =========================================================
# RISPOSTA GENERICA
# =========================================================

class MessageResponse(BaseModel):
    message: str


# Re-export utili per i router
__all__ = [
    # Utente / auth
    "UserBase", "UserCreate", "UserCreateByAdmin", "UserSelfRegister",
    "UserResponse", "UserWithProfileResponse",
    "LoginRequest", "Token", "TokenData",
    # Profili
    "DoctorProfileBase", "DoctorProfileCreate", "DoctorProfileResponse",
    "PatientProfileBase", "PatientProfileCreate", "PatientProfileUpdate",
    "PatientProfileResponse", "AnamnesiUpdate", "MedicoPazienteListItem",
    "RegistrazionePazienteRequest", "RegistrazioneMedicoRequest",
    "AssociazioneMedico", "AnagraficaUpdate", "PasswordReset",
    # Glicemia
    "RilevazioneGlicemicaBase", "RilevazioneGlicemicaCreate",
    "RilevazioneGlicemicaResponse", "GlicemiaAggregata",
    # Terapia
    "TerapiaBase", "TerapiaCreate", "TerapiaUpdate", "TerapiaResponse",
    # Assunzione
    "AssunzioneBase", "AssunzioneCreate", "AssunzioneResponse",
    # Sintomo / patologie / terapie parallele
    "SintomoBase", "SintomoCreate", "SintomoUpdate", "SintomoResponse",
    "PatologiaConcomitanteBase", "PatologiaConcomitanteCreate",
    "PatologiaConcomitanteUpdate", "PatologiaConcomitanteResponse",
    "TerapiaParallelaBase", "TerapiaParallelaCreate",
    "TerapiaParallelaUpdate", "TerapiaParallelaResponse",
    # Messaggi / notifiche / audit
    "MessaggioCreate", "MessaggioPazienteCreate", "MessaggioResponse",
    "NotificaResponse", "AuditLogResponse",
    # Generici
    "MessageResponse", "ORMBase",
    # Costanti dominio
    "SOGLIA_PRIMA_PASTO_MIN", "SOGLIA_PRIMA_PASTO_MAX", "SOGLIA_DOPO_PASTO_MAX",
]
