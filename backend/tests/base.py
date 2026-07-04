"""
Base condivisa dei test.

Strategia (semplice e senza dipendenze esterne): usiamo `unittest` (stdlib) e un
database SQLite IN MEMORIA ricreato ad ogni test. Le funzionalita' vengono testate
chiamando DIRETTAMENTE le funzioni dei service e dei router (che sono normali
funzioni Python: i default `Depends(...)` vengono semplicemente sovrascritti
passando gli argomenti espliciti). Cosi' non servono ne' pytest ne' httpx.
"""

import os
import sys
import unittest
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Rende importabile il package `app` quando i test girano dalla cartella backend/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import (
    Base,
    User,
    UserRole,
    DoctorProfile,
    PatientProfile,
    Terapia,
    UnitaMisura,
)
from app.security import get_password_hash


class DBTestCase(unittest.TestCase):
    """
    Prepara un DB in memoria e una sessione, con dati minimi di partenza:
    - 1 amministratore
    - 1 medico (Mario Rossi) con profilo
    - 1 paziente (Luca Bianchi) associato al medico
    - 1 terapia attiva (Metformina 500 mg, 2 assunzioni/die)
    """

    def setUp(self):
        # StaticPool + un'unica connessione: il DB in memoria resta condiviso
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.db = self.Session()
        self._seed()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)

    def _seed(self):
        # --- Amministratore ---
        self.admin_user = User(
            email="admin@test.it",
            password_hash=get_password_hash("Admin2026!!aa"),
            role=UserRole.ADMIN,
            is_active=True,
        )
        # --- Medico ---
        self.doc_user = User(
            email="doc@test.it",
            password_hash=get_password_hash("Medico2026!!aa"),
            role=UserRole.DOCTOR,
            is_active=True,
        )
        # --- Paziente ---
        self.pat_user = User(
            email="pat@test.it",
            password_hash=get_password_hash("Paziente2026!!aa"),
            role=UserRole.PATIENT,
            is_active=True,
        )
        self.db.add_all([self.admin_user, self.doc_user, self.pat_user])
        self.db.flush()

        self.doc_profile = DoctorProfile(
            user_id=self.doc_user.id, nome="Mario", cognome="Rossi"
        )
        self.db.add(self.doc_profile)
        self.db.flush()

        self.pat_profile = PatientProfile(
            user_id=self.pat_user.id,
            doctor_id=self.doc_profile.id,
            nome="Luca",
            cognome="Bianchi",
        )
        self.db.add(self.pat_profile)
        self.db.flush()

        self.terapia = Terapia(
            patient_id=self.pat_profile.id,
            doctor_id=self.doc_profile.id,
            farmaco="Metformina",
            assunzioni_giornaliere=2,
            quantita=Decimal("500"),
            unita=UnitaMisura.MG,
            indicazioni="Dopo i pasti",
            is_active=True,
        )
        self.db.add(self.terapia)
        self.db.commit()
