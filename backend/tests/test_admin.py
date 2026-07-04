"""
Test delle funzionalita' dell'AMMINISTRATORE: creazione utenti (RF-2),
associazione paziente-medico (RF-3), modifica anagrafica, reset password,
consultazione audit (RF-15).
"""

import unittest

from fastapi import HTTPException

from tests.base import DBTestCase
from app.routers import admin, medico
from app.schemas import (
    RegistrazioneMedicoRequest,
    RegistrazionePazienteRequest,
    UserCreateByAdmin,
    DoctorProfileBase,
    PatientProfileBase,
    AssociazioneMedico,
    AnagraficaUpdate,
    PasswordReset,
)
from app.security import verify_password
from app.models import User, UserRole


class TestAdmin(DBTestCase):
    def test_crea_medico(self):  # RF-2
        payload = RegistrazioneMedicoRequest(
            user=UserCreateByAdmin(email="nuovo.medico@test.it", role=UserRole.DOCTOR, password="Medico2026!!aa"),
            profile=DoctorProfileBase(nome="Anna", cognome="Verdi"),
        )
        user = admin.crea_medico(payload=payload, db=self.db)
        self.assertEqual(user.role, UserRole.DOCTOR)
        self.assertIsNotNone(user.doctor_profile)
        self.assertEqual(user.doctor_profile.cognome, "Verdi")

    def test_crea_medico_email_duplicata_400(self):  # RF-2 (email univoca)
        payload = RegistrazioneMedicoRequest(
            user=UserCreateByAdmin(email="doc@test.it", role=UserRole.DOCTOR, password="Medico2026!!aa"),
            profile=DoctorProfileBase(nome="X", cognome="Y"),
        )
        with self.assertRaises(HTTPException) as ctx:
            admin.crea_medico(payload=payload, db=self.db)
        self.assertEqual(ctx.exception.status_code, 400)

    def test_crea_paziente_con_medico(self):  # RF-2 + RF-3
        payload = RegistrazionePazienteRequest(
            user=UserCreateByAdmin(email="nuovo.paziente@test.it", role=UserRole.PATIENT, password="Paziente2026!!aa"),
            profile=PatientProfileBase(nome="Mario", cognome="Neri"),
            doctor_id=self.doc_profile.id,
        )
        user = admin.crea_paziente(payload=payload, db=self.db)
        self.assertEqual(user.role, UserRole.PATIENT)
        self.assertEqual(user.patient_profile.doctor_id, self.doc_profile.id)

    def test_associa_e_rimuove_medico(self):  # RF-3
        # Rimuove l'associazione
        p = admin.associa_medico(
            patient_id=self.pat_profile.id, payload=AssociazioneMedico(doctor_id=None), db=self.db
        )
        self.assertIsNone(p.doctor_id)
        # La riassegna
        p = admin.associa_medico(
            patient_id=self.pat_profile.id, payload=AssociazioneMedico(doctor_id=self.doc_profile.id), db=self.db
        )
        self.assertEqual(p.doctor_id, self.doc_profile.id)

    def test_associa_medico_inesistente_400(self):  # RF-3 (validazione)
        with self.assertRaises(HTTPException) as ctx:
            admin.associa_medico(
                patient_id=self.pat_profile.id, payload=AssociazioneMedico(doctor_id=999), db=self.db
            )
        self.assertEqual(ctx.exception.status_code, 400)

    def test_modifica_anagrafica(self):
        user = admin.modifica_anagrafica(
            user_id=self.doc_user.id,
            payload=AnagraficaUpdate(cognome="Rossi-Bianchi", email="doc2@test.it"),
            db=self.db,
        )
        self.assertEqual(user.email, "doc2@test.it")
        self.assertEqual(user.doctor_profile.cognome, "Rossi-Bianchi")

    def test_reset_password(self):
        admin.reset_password(
            user_id=self.pat_user.id, payload=PasswordReset(password="NuovaPass2026!!"), db=self.db
        )
        aggiornato = self.db.query(User).filter(User.id == self.pat_user.id).first()
        self.assertTrue(verify_password("NuovaPass2026!!", aggiornato.password_hash))

    def test_registro_audit(self):  # RF-15
        # Genera un'operazione tracciata da parte del medico
        medico.scheda_paziente(patient_id=self.pat_profile.id, db=self.db, current=self.doc_user)
        logs = admin.registro_audit(paziente_id=None, db=self.db)
        self.assertGreaterEqual(len(logs), 1)


if __name__ == "__main__":
    unittest.main()
