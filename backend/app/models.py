import enum
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Numeric, DateTime, Date,
    ForeignKey, Enum, Boolean, Text,
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()




class UserRole(str, enum.Enum):
    ADMIN = "admin"
    DOCTOR = "doctor"
    PATIENT = "patient"


class MomentoGlicemia(str, enum.Enum):
    PRIMA_PASTO = "prima_pasto"
    DOPO_PASTO = "dopo_pasto"


class UnitaMisura(str, enum.Enum):
    MG = "mg"
    UI = "UI"            # Unita Internazionali (insulina)
    ML = "ml"
    COMPRESSE = "compresse"


class GravitaSintomo(str, enum.Enum):
    LIEVE = "lieve"
    MODERATA = "moderata"
    GRAVE = "grave"


class TipoNotifica(str, enum.Enum):
    SOLLECITO_ASSUNZIONE = "sollecito_assunzione"          # RF-12
    MANCATA_ADERENZA = "mancata_aderenza"                  # RF-13
    GLICEMIA_FUORI_SOGLIA = "glicemia_fuori_soglia"        # RF-14


class SeveritaNotifica(str, enum.Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"



class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    is_active = Column(Boolean, default=True)

    doctor_profile = relationship("DoctorProfile", uselist=False, back_populates="user")
    patient_profile = relationship("PatientProfile", uselist=False, back_populates="user")
    logs = relationship("AuditLog", back_populates="operator")
    messaggi_inviati = relationship(
        "Messaggio", foreign_keys="Messaggio.mittente_id", back_populates="mittente"
    )
    messaggi_ricevuti = relationship(
        "Messaggio", foreign_keys="Messaggio.destinatario_id", back_populates="destinatario"
    )
    notifiche = relationship("Notifica", back_populates="destinatario")



class DoctorProfile(Base):
    __tablename__ = "doctor_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    nome = Column(String, nullable=False)
    cognome = Column(String, nullable=False)

    user = relationship("User", back_populates="doctor_profile")
    patients = relationship("PatientProfile", back_populates="primary_doctor")



class PatientProfile(Base):
    __tablename__ = "patient_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    doctor_id = Column(Integer, ForeignKey("doctor_profiles.id"), nullable=True)
    nome = Column(String, nullable=False)
    cognome = Column(String, nullable=False)

    # RF-10 Anamnesi (statica)
    fattori_rischio = Column(Text, nullable=True)        # Fumo, alcol, ecc.
    patologie_pregresse = Column(Text, nullable=True)
    comorbita = Column(Text, nullable=True)

    user = relationship("User", back_populates="patient_profile")
    primary_doctor = relationship("DoctorProfile", back_populates="patients")
    glicemie = relationship("RilevazioneGlicemica", back_populates="patient")
    terapie = relationship("Terapia", back_populates="patient")
    sintomi = relationship("Sintomo", back_populates="patient")
    patologie_concomitanti = relationship("PatologiaConcomitante", back_populates="patient")
    terapie_parallele = relationship("TerapiaParallela", back_populates="patient")



class RilevazioneGlicemica(Base):
    __tablename__ = "rilevazioni_glicemiche"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patient_profiles.id"), nullable=False)
    valore = Column(Integer, nullable=False)  # in mg/dL
    momento = Column(Enum(MomentoGlicemia), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    patient = relationship("PatientProfile", back_populates="glicemie")

class Terapia(Base):
    __tablename__ = "terapie"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patient_profiles.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctor_profiles.id"), nullable=False)
    farmaco = Column(String, nullable=False)
    assunzioni_giornaliere = Column(Integer, nullable=False)

    # RF-11: confronto numerico prescritto vs assunto
    quantita = Column(Numeric(10, 3), nullable=False)
    unita = Column(Enum(UnitaMisura), nullable=False)

    indicazioni = Column(String, nullable=True)  # es. "dopo i pasti"
    data_inizio = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    patient = relationship("PatientProfile", back_populates="terapie")
    assunzioni = relationship("Assunzione", back_populates="terapia")


class Assunzione(Base):
    __tablename__ = "assunzioni"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patient_profiles.id"), nullable=False)
    terapia_id = Column(Integer, ForeignKey("terapie.id"), nullable=False)
    farmaco = Column(String, nullable=False)  # snapshot del farmaco, RF-6 esplicito
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    # RF-11: stessi tipi della Terapia per consentire il confronto
    quantita_assunta = Column(Numeric(10, 3), nullable=False)
    unita = Column(Enum(UnitaMisura), nullable=False)

    terapia = relationship("Terapia", back_populates="assunzioni")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    operator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    azione = Column(String, nullable=False)  # es. "VISUALIZZAZIONE_DATI", "MODIFICA_TERAPIA"
    target_paziente_id = Column(Integer, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    operator = relationship("User", back_populates="logs")


class Sintomo(Base):
    __tablename__ = "sintomi"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patient_profiles.id"), nullable=False)
    descrizione = Column(String, nullable=False)         # es. "spossatezza", "nausea"
    gravita = Column(Enum(GravitaSintomo), nullable=True)
    data_inizio = Column(Date, nullable=False)
    data_fine = Column(Date, nullable=True)              # null = ancora in corso
    note = Column(Text, nullable=True)

    patient = relationship("PatientProfile", back_populates="sintomi")


class PatologiaConcomitante(Base):
    __tablename__ = "patologie_concomitanti"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patient_profiles.id"), nullable=False)
    descrizione = Column(String, nullable=False)
    data_inizio = Column(Date, nullable=False)
    data_fine = Column(Date, nullable=True)
    note = Column(Text, nullable=True)

    patient = relationship("PatientProfile", back_populates="patologie_concomitanti")


class TerapiaParallela(Base):
    __tablename__ = "terapie_parallele"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patient_profiles.id"), nullable=False)
    farmaco = Column(String, nullable=False)
    posologia = Column(String, nullable=True)            # descrizione libera
    data_inizio = Column(Date, nullable=False)
    data_fine = Column(Date, nullable=True)
    note = Column(Text, nullable=True)

    patient = relationship("PatientProfile", back_populates="terapie_parallele")


class Messaggio(Base):
    __tablename__ = "messaggi"

    id = Column(Integer, primary_key=True, index=True)
    mittente_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    destinatario_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    oggetto = Column(String, nullable=False)
    corpo = Column(Text, nullable=False)
    inviato_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    letto_at = Column(DateTime, nullable=True)

    mittente = relationship(
        "User", foreign_keys=[mittente_id], back_populates="messaggi_inviati"
    )
    destinatario = relationship(
        "User", foreign_keys=[destinatario_id], back_populates="messaggi_ricevuti"
    )


class Notifica(Base):
    __tablename__ = "notifiche"

    id = Column(Integer, primary_key=True, index=True)
    destinatario_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # paziente di riferimento (es. il paziente con glicemia fuori soglia, anche se la notifica va al medico)
    paziente_riferimento_id = Column(Integer, ForeignKey("patient_profiles.id"), nullable=True)

    tipo = Column(Enum(TipoNotifica), nullable=False)
    severita = Column(Enum(SeveritaNotifica), nullable=False, default=SeveritaNotifica.INFO)
    messaggio = Column(Text, nullable=False)

    creato_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    letta_at = Column(DateTime, nullable=True)
    risolta_at = Column(DateTime, nullable=True)

    destinatario = relationship("User", back_populates="notifiche")
    paziente_riferimento = relationship("PatientProfile")
