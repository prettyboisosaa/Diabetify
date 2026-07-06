"""
Test delle funzionalita' del MEDICO: terapie (RF-8), anamnesi (RF-10),
visualizzazione dati (RF-9) e tracciabilita' (RF-15).
"""

import unittest
from decimal import Decimal

from tests.base import DBTestCase
from app.routers import medico
from app.schemas import TerapiaCreate, TerapiaUpdate, AnamnesiUpdate
from app.models import AuditLog, Terapia


class TestMedico(DBTestCase):
    def test_lista_pazienti(self):
        risultato = medico.lista_pazienti(db=self.db)
        self.assertEqual(len(risultato), 1)
        self.assertEqual(risultato[0].cognome, "Bianchi")

    def test_crea_terapia_e_audit(self):  # RF-8 + RF-15
        payload = TerapiaCreate(
            patient_id=self.pat_profile.id,
            farmaco="Insulina",
            assunzioni_giornaliere=3,
            quantita=Decimal("10"),
            unita="UI",
            indicazioni="Prima dei pasti",
        )
        terapia = medico.crea_terapia(
            patient_id=self.pat_profile.id, payload=payload, db=self.db, current=self.doc_user
        )
        self.assertEqual(terapia.farmaco, "Insulina")
        self.assertEqual(terapia.doctor_id, self.doc_profile.id)
        # RF-15: l'operazione e' tracciata
        log = self.db.query(AuditLog).filter(AuditLog.azione == "CREAZIONE_TERAPIA").first()
        self.assertIsNotNone(log)
        self.assertEqual(log.operator_id, self.doc_user.id)

    def test_modifica_terapia_disattiva(self):  # RF-8
        payload = TerapiaUpdate(is_active=False, indicazioni="Sospesa")
        terapia = medico.modifica_terapia(
            terapia_id=self.terapia.id, payload=payload, db=self.db, current=self.doc_user
        )
        self.assertFalse(terapia.is_active)
        self.assertEqual(terapia.indicazioni, "Sospesa")

    def test_aggiorna_anamnesi(self):  # RF-10
        payload = AnamnesiUpdate(fattori_rischio="Fumo", comorbita="Ipertensione")
        paziente = medico.aggiorna_anamnesi(
            patient_id=self.pat_profile.id, payload=payload, db=self.db, current=self.doc_user
        )
        self.assertEqual(paziente.fattori_rischio, "Fumo")
        log = self.db.query(AuditLog).filter(AuditLog.azione == "AGGIORNAMENTO_ANAMNESI").first()
        self.assertIsNotNone(log)

    def test_scheda_paziente_traccia_visualizzazione(self):  # RF-9 + RF-15
        medico.scheda_paziente(patient_id=self.pat_profile.id, db=self.db, current=self.doc_user)
        log = self.db.query(AuditLog).filter(AuditLog.azione == "VISUALIZZAZIONE_SCHEDA").first()
        self.assertIsNotNone(log)
        self.assertEqual(log.target_paziente_id, self.pat_profile.id)

    def test_glicemie_aggregate_vuoto(self):  # RF-9 (nessuna rilevazione -> lista vuota)
        risultato = medico.glicemie_aggregate(
            patient_id=self.pat_profile.id, periodo="settimana", db=self.db, current=self.doc_user
        )
        self.assertEqual(risultato, [])


if __name__ == "__main__":
    unittest.main()
