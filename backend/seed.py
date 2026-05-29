import sys
import os
from sqlalchemy.orm import Session

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, engine
from app.models import User, UserRole, DoctorProfile, PatientProfile
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def seed_data():
    db: Session = SessionLocal()
    print("🌱 Popolamento utenti di test in corso...")

    try:
        # 1. Creazione AMMINISTRATORE
        admin_email = "admin@diabetify.it"
        if not db.query(User).filter(User.email == admin_email).first():
            admin_user = User(
                email=admin_email,
                password_hash=get_password_hash("Admin2026!"),
                role=UserRole.ADMIN,
                is_active=True
            )
            db.add(admin_user)
            print(f"✅ Creato Admin: {admin_email} (Password: Admin2026!)")

        # 2. Creazione MEDICO
        doc_email = "dottore@diabetify.it"
        if not db.query(User).filter(User.email == doc_email).first():
            doc_user = User(
                email=doc_email,
                password_hash=get_password_hash("Medico2026!"),
                role=UserRole.DOCTOR,
                is_active=True
            )
            db.add(doc_user)
            db.flush() # Ottiene l'ID dell'utente appena inserito senza fare il commit definitivo

            # Crea il profilo medico associato
            doc_profile = DoctorProfile(
                user_id=doc_user.id,
                nome= "Mario",
                cognome="Rossi"
            )
            db.add(doc_profile)
            print(f"✅ Creato Medico: {doc_email} (Password: Medico2026!)")

        # 3. Creazione PAZIENTE
        pat_email = "paziente@diabetify.it"
        if not db.query(User).filter(User.email == pat_email).first():
            pat_user = User(
                email=pat_email,
                password_hash=get_password_hash("Paziente2026!"),
                role=UserRole.PATIENT,
                is_active=True
            )
            db.add(pat_user)
            db.flush()

            # Otteniamo l'id del medico se esiste per associarlo al paziente (RF-3)
            medico = db.query(DoctorProfile).first()

            # Crea il profilo paziente associato
            pat_profile = PatientProfile(
                user_id=pat_user.id,
                doctor_id=medico.id if medico else None,
                nome="Luca",
                cognome="Bianchi",
                fattori_rischio="Fumatore occasionale",
                patologie_pregresse="Nessuna",
                comorbita="Ipertensione lieve"
            )
            db.add(pat_profile)
            print(f"✅ Creato Paziente: {pat_email} (Password: Paziente2026!)")

        db.commit()
        print("🎉 Database popolato con successo!")

    except Exception as e:
        db.rollback()
        print(f"❌ Errore durante il seeding: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()