"""
Test di validazione degli SCHEMI Pydantic: complessita' password (RNF-2),
campo calcolato `fuori_soglia` (RNF-1), validatore periodo del diario (RF-5).
Non richiede database.
"""

import os
import sys
import unittest
from datetime import date, datetime

# Rende importabile `app` anche eseguendo il file singolarmente
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pydantic import ValidationError

from app.schemas import UserCreateByAdmin, RilevazioneGlicemicaResponse, SintomoBase
from app.models import UserRole


class TestValidazioneSchemi(unittest.TestCase):
    def test_password_debole_rifiutata(self):  # RNF-2
        with self.assertRaises(ValidationError):
            UserCreateByAdmin(email="a@b.it", role=UserRole.DOCTOR, password="tuttominuscolo")

    def test_password_forte_accettata(self):
        u = UserCreateByAdmin(email="a@b.it", role=UserRole.DOCTOR, password="Password2026!!")
        self.assertEqual(u.email, "a@b.it")

    def test_fuori_soglia_computed(self):  # RNF-1
        alta = RilevazioneGlicemicaResponse(
            id=1, patient_id=1, valore=200, momento="dopo_pasto", timestamp=datetime.now()
        )
        self.assertTrue(alta.fuori_soglia)
        norma = RilevazioneGlicemicaResponse(
            id=2, patient_id=1, valore=170, momento="dopo_pasto", timestamp=datetime.now()
        )
        self.assertFalse(norma.fuori_soglia)

    def test_periodo_diario_non_valido(self):  # RF-5 (data_fine < data_inizio)
        with self.assertRaises(ValidationError):
            SintomoBase(descrizione="X", data_inizio=date(2026, 7, 10), data_fine=date(2026, 7, 1))


if __name__ == "__main__":
    unittest.main()
