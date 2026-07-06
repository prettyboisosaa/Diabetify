"""
Test dell'attore SISTEMA: soglie e aggregazione (RNF-1/RF-9), coerenza (RF-11),
alert glicemia (RF-14), controlli di aderenza con idempotenza (RF-12/RF-13).
"""

import unittest
from datetime import datetime, timedelta
from decimal import Decimal

from tests.base import DBTestCase
from app.services.glicemia import e_fuori_soglia, aggrega_glicemie
from app.services.sistema import (
    severita_da_glicemia,
    assunzione_coerente,
    verifica_glicemia,
    esegui_controlli,
)
from app.models import (
    MomentoGlicemia,
    RilevazioneGlicemica,
    Assunzione,
    UnitaMisura,
    Notifica,
    TipoNotifica,
)


class TestSoglieEAggregazione(DBTestCase):
    def test_e_fuori_soglia(self):  # RNF-1
        self.assertFalse(e_fuori_soglia(110, MomentoGlicemia.PRIMA_PASTO))  # 80-130 ok
        self.assertTrue(e_fuori_soglia(140, MomentoGlicemia.PRIMA_PASTO))   # >130
        self.assertTrue(e_fuori_soglia(70, MomentoGlicemia.PRIMA_PASTO))    # <80
        self.assertFalse(e_fuori_soglia(170, MomentoGlicemia.DOPO_PASTO))   # <=180 ok
        self.assertTrue(e_fuori_soglia(190, MomentoGlicemia.DOPO_PASTO))    # >180

    def test_severita(self):  # RF-14
        self.assertEqual(severita_da_glicemia(190, MomentoGlicemia.DOPO_PASTO).value, "warning")
        self.assertEqual(severita_da_glicemia(260, MomentoGlicemia.DOPO_PASTO).value, "critical")
        self.assertEqual(severita_da_glicemia(140, MomentoGlicemia.PRIMA_PASTO).value, "warning")
        self.assertEqual(severita_da_glicemia(300, MomentoGlicemia.PRIMA_PASTO).value, "critical")

    def test_aggregazione(self):  # RF-9
        ora = datetime(2026, 7, 1, 8, 0)  # mercoledi'
        rilevazioni = [
            RilevazioneGlicemica(patient_id=self.pat_profile.id, valore=100, momento=MomentoGlicemia.PRIMA_PASTO, timestamp=ora),
            RilevazioneGlicemica(patient_id=self.pat_profile.id, valore=200, momento=MomentoGlicemia.DOPO_PASTO, timestamp=ora + timedelta(hours=3)),
        ]
        agg = aggrega_glicemie(rilevazioni, "settimana")
        self.assertEqual(len(agg), 1)
        self.assertEqual(agg[0].media, 150.0)
        self.assertEqual(agg[0].num_misurazioni, 2)
        self.assertEqual(agg[0].num_fuori_soglia, 1)  # 200 dopo pasto e' fuori soglia


class TestCoerenza(DBTestCase):
    def test_assunzione_coerente(self):  # RF-11
        coerente = Assunzione(
            patient_id=self.pat_profile.id, terapia_id=self.terapia.id,
            farmaco="Metformina", quantita_assunta=Decimal("500"), unita=UnitaMisura.MG,
        )
        self.assertTrue(assunzione_coerente(coerente, self.terapia))
        # Quantita' diversa -> non coerente
        parziale = Assunzione(
            patient_id=self.pat_profile.id, terapia_id=self.terapia.id,
            farmaco="Metformina", quantita_assunta=Decimal("250"), unita=UnitaMisura.MG,
        )
        self.assertFalse(assunzione_coerente(parziale, self.terapia))


class TestAlertGlicemia(DBTestCase):
    def test_verifica_glicemia_fuori_soglia(self):  # RF-14
        ril = RilevazioneGlicemica(patient_id=self.pat_profile.id, valore=260, momento=MomentoGlicemia.DOPO_PASTO)
        notifica = verifica_glicemia(self.db, ril)
        self.assertIsNotNone(notifica)
        self.assertEqual(notifica.tipo, TipoNotifica.GLICEMIA_FUORI_SOGLIA)
        self.assertEqual(notifica.destinatario_id, self.doc_user.id)

    def test_verifica_glicemia_normale_nessun_alert(self):  # RF-14
        ril = RilevazioneGlicemica(patient_id=self.pat_profile.id, valore=100, momento=MomentoGlicemia.PRIMA_PASTO)
        self.assertIsNone(verifica_glicemia(self.db, ril))


class TestControlliAderenza(DBTestCase):
    def test_solleciti_e_alert_con_idempotenza(self):  # RF-12 + RF-13
        # Nessuna assunzione registrata -> tutti i giorni sono non aderenti
        risultato = esegui_controlli(self.db)
        self.assertGreaterEqual(risultato["notifiche_create"], 2)

        tipi = {n.tipo for n in self.db.query(Notifica).all()}
        self.assertIn(TipoNotifica.SOLLECITO_ASSUNZIONE, tipi)  # RF-12 (al paziente)
        self.assertIn(TipoNotifica.MANCATA_ADERENZA, tipi)      # RF-13 (al medico)

        # Idempotenza: una seconda esecuzione non crea duplicati
        secondo = esegui_controlli(self.db)
        self.assertEqual(secondo["notifiche_create"], 0)


if __name__ == "__main__":
    unittest.main()
