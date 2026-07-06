import sys
import os
from datetime import datetime, date, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models import (
    User,
    UserRole,
    DoctorProfile,
    PatientProfile,
    RilevazioneGlicemica,
    MomentoGlicemia,
    Terapia,
    UnitaMisura,
    Assunzione,
    Sintomo,
    GravitaSintomo,
    Messaggio,
    Notifica,
    TipoNotifica,
    SeveritaNotifica,
)
# Riusiamo l'hashing centralizzato in app.security
from app.security import get_password_hash


def seed_utenti(db: Session):
    """Crea i tre utenti di test (admin, medico, paziente) se non esistono."""
    # 1. AMMINISTRATORE
    admin_email = "admin@diabetify.it"
    if not db.query(User).filter(User.email == admin_email).first():
        db.add(User(
            email=admin_email,
            password_hash=get_password_hash("Admin2026!"),
            role=UserRole.ADMIN,
            is_active=True,
        ))
        print(f"✅ Creato Admin: {admin_email} (Password: Admin2026!)")

    # 2. MEDICO
    doc_email = "dottore@diabetify.it"
    if not db.query(User).filter(User.email == doc_email).first():
        doc_user = User(
            email=doc_email,
            password_hash=get_password_hash("Medico2026!"),
            role=UserRole.DOCTOR,
            is_active=True,
        )
        db.add(doc_user)
        db.flush()  # ottiene l'id senza commit definitivo
        db.add(DoctorProfile(user_id=doc_user.id, nome="Mario", cognome="Rossi"))
        print(f"✅ Creato Medico: {doc_email} (Password: Medico2026!)")

    # 3. PAZIENTE
    pat_email = "paziente@diabetify.it"
    if not db.query(User).filter(User.email == pat_email).first():
        pat_user = User(
            email=pat_email,
            password_hash=get_password_hash("Paziente2026!"),
            role=UserRole.PATIENT,
            is_active=True,
        )
        db.add(pat_user)
        db.flush()

        # Associa il paziente al medico di riferimento (RF-3)
        medico = db.query(DoctorProfile).first()
        db.add(PatientProfile(
            user_id=pat_user.id,
            doctor_id=medico.id if medico else None,
            nome="Luca",
            cognome="Bianchi",
            fattori_rischio="Fumatore occasionale",
            patologie_pregresse="Nessuna",
            comorbita="Ipertensione lieve",
        ))
        print(f"✅ Creato Paziente: {pat_email} (Password: Paziente2026!)")

    db.commit()


def seed_dati_clinici(db: Session):
    """
    Popola dati clinici di esempio per il paziente di test, cosi' che la UI del
    medico abbia contenuti reali (glicemie fuori/entro soglia, una terapia con
    relative assunzioni, sintomi, un messaggio e alcune notifiche/alert).
    Idempotente: si aggancia solo se non ci sono gia' glicemie per il paziente.
    """
    paziente = (
        db.query(PatientProfile)
        .filter(PatientProfile.nome == "Luca", PatientProfile.cognome == "Bianchi")
        .first()
    )
    medico = db.query(DoctorProfile).first()
    if paziente is None or medico is None:
        print("⚠️  Paziente/medico di test assenti: salto i dati clinici.")
        return

    # Evita duplicazioni se il seed viene rilanciato
    if db.query(RilevazioneGlicemica).filter(
        RilevazioneGlicemica.patient_id == paziente.id
    ).first():
        print("ℹ️  Dati clinici gia' presenti: nessuna aggiunta.")
        return

    oggi = datetime.utcnow()

    # --- Rilevazioni glicemiche (RF-4): mix di valori entro e fuori soglia ---
    # (giorni_fa, valore, momento)
    campioni = [
        (6, 110, MomentoGlicemia.PRIMA_PASTO),   # ok
        (6, 165, MomentoGlicemia.DOPO_PASTO),    # ok (<=180)
        (5, 95,  MomentoGlicemia.PRIMA_PASTO),   # ok
        (5, 205, MomentoGlicemia.DOPO_PASTO),    # fuori soglia (>180)
        (4, 142, MomentoGlicemia.PRIMA_PASTO),   # fuori soglia (>130)
        (3, 88,  MomentoGlicemia.PRIMA_PASTO),   # ok
        (2, 190, MomentoGlicemia.DOPO_PASTO),    # fuori soglia
        (1, 120, MomentoGlicemia.PRIMA_PASTO),   # ok
        (0, 70,  MomentoGlicemia.PRIMA_PASTO),   # fuori soglia (<80)
    ]
    for giorni_fa, valore, momento in campioni:
        db.add(RilevazioneGlicemica(
            patient_id=paziente.id,
            valore=valore,
            momento=momento,
            timestamp=oggi - timedelta(days=giorni_fa, hours=1),
        ))

    # --- Terapia prescritta dal medico (RF-8) ---
    terapia = Terapia(
        patient_id=paziente.id,
        doctor_id=medico.id,
        farmaco="Metformina",
        assunzioni_giornaliere=2,
        quantita=Decimal("500"),
        unita=UnitaMisura.MG,
        indicazioni="Dopo i pasti principali",
        data_inizio=oggi - timedelta(days=6),
        is_active=True,
    )
    db.add(terapia)
    db.flush()  # per avere terapia.id nelle assunzioni

    # --- Assunzioni registrate dal paziente (RF-6) ---
    for giorni_fa in (2, 1, 0):
        db.add(Assunzione(
            patient_id=paziente.id,
            terapia_id=terapia.id,
            farmaco="Metformina",
            quantita_assunta=Decimal("500"),
            unita=UnitaMisura.MG,
            timestamp=oggi - timedelta(days=giorni_fa, hours=2),
        ))

    # --- Sintomo segnalato (RF-5) ---
    db.add(Sintomo(
        patient_id=paziente.id,
        descrizione="Spossatezza",
        gravita=GravitaSintomo.MODERATA,
        data_inizio=date.today() - timedelta(days=3),
        note="Soprattutto nel pomeriggio.",
    ))

    # --- Messaggio dal paziente al medico (RF-7) ---
    db.add(Messaggio(
        mittente_id=paziente.user_id,
        destinatario_id=medico.user_id,
        oggetto="Dubbio sul dosaggio",
        corpo="Buongiorno dottore, devo assumere la metformina anche a colazione?",
        inviato_at=oggi - timedelta(days=1, hours=3),
    ))

    # --- Notifiche/alert verso il medico (RF-13/14) ---
    db.add(Notifica(
        destinatario_id=medico.user_id,
        paziente_riferimento_id=paziente.id,
        tipo=TipoNotifica.GLICEMIA_FUORI_SOGLIA,
        severita=SeveritaNotifica.CRITICAL,
        messaggio="Glicemia post-prandiale di 205 mg/dL registrata dal paziente Luca Bianchi.",
        creato_at=oggi - timedelta(days=5, hours=1),
    ))
    db.add(Notifica(
        destinatario_id=medico.user_id,
        paziente_riferimento_id=paziente.id,
        tipo=TipoNotifica.MANCATA_ADERENZA,
        severita=SeveritaNotifica.WARNING,
        messaggio="Il paziente Luca Bianchi non ha registrato assunzioni per piu' giorni.",
        creato_at=oggi - timedelta(days=4),
    ))

    # --- Notifica/sollecito verso il PAZIENTE (RF-12/13) ---
    db.add(Notifica(
        destinatario_id=paziente.user_id,
        paziente_riferimento_id=paziente.id,
        tipo=TipoNotifica.SOLLECITO_ASSUNZIONE,
        severita=SeveritaNotifica.INFO,
        messaggio="Ricordati di registrare l'assunzione della metformina di oggi.",
        creato_at=oggi - timedelta(hours=4),
    ))

    db.commit()
    print("✅ Dati clinici di esempio inseriti per Luca Bianchi.")


def seed_data():
    db: Session = SessionLocal()
    print("🌱 Popolamento database in corso...")
    try:
        seed_utenti(db)
        seed_dati_clinici(db)
        print("🎉 Database popolato con successo!")
    except Exception as e:
        db.rollback()
        print(f"❌ Errore durante il seeding: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()
