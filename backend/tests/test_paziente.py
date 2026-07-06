"""
Test delle funzionalita' del PAZIENTE: glicemie (RF-4), assunzioni (RF-6),
diario (RF-5), messaggi al medico (RF-7). Verifica anche l'hook event-driven
che genera l'alert glicemia (RF-14).
"""

import unittest
from datetime import date
from decimal import Decimal

from fastapi import HTTPException

from tests.base import DBTestCase
from app.routers import paziente
from app.schemas import (
    RilevazioneGlicemicaCreate,
    AssunzioneCreate,
    SintomoCreate,
    SintomoUpdate,
    MessaggioPazienteCreate,
)
from app.models import Notifica, Messaggio, Sintomo, TipoNotifica


class TestPaziente(DBTestCase):
    def test_registra_glicemia_normale_nessun_alert(self):  # RF-4
        payload = RilevazioneGlicemicaCreate(valore=110, momento="prima_pasto")
        ril = paziente.registra_glicemia(payload=payload, db=self.db, current=self.pat_user)
        self.assertEqual(ril.valore, 110)
        # valore nella norma -> nessuna notifica al medico
        self.assertEqual(self.db.query(Notifica).count(), 0)

    def test_registra_glicemia_fuori_soglia_crea_alert(self):  # RF-4 + RF-14
        payload = RilevazioneGlicemicaCreate(valore=260, momento="dopo_pasto")
        paziente.registra_glicemia(payload=payload, db=self.db, current=self.pat_user)
        notifica = self.db.query(Notifica).filter(
            Notifica.tipo == TipoNotifica.GLICEMIA_FUORI_SOGLIA
        ).first()
        self.assertIsNotNone(notifica)
        self.assertEqual(notifica.destinatario_id, self.doc_user.id)  # va al medico
        self.assertEqual(notifica.severita.value, "critical")  # 260 -> critico

    def test_registra_assunzione_valida(self):  # RF-6
        payload = AssunzioneCreate(
            terapia_id=self.terapia.id, farmaco="Metformina",
            quantita_assunta=Decimal("500"), unita="mg",
        )
        a = paziente.registra_assunzione(payload=payload, db=self.db, current=self.pat_user)
        self.assertEqual(a.terapia_id, self.terapia.id)

    def test_registra_assunzione_terapia_inesistente_404(self):  # RF-6 (validazione)
        payload = AssunzioneCreate(
            terapia_id=999, farmaco="X", quantita_assunta=Decimal("1"), unita="mg",
        )
        with self.assertRaises(HTTPException) as ctx:
            paziente.registra_assunzione(payload=payload, db=self.db, current=self.pat_user)
        self.assertEqual(ctx.exception.status_code, 404)

    def test_diario_sintomo_crea_e_chiude(self):  # RF-5
        creato = paziente.crea_sintomo(
            payload=SintomoCreate(descrizione="Spossatezza", data_inizio=date(2026, 7, 1)),
            db=self.db, current=self.pat_user,
        )
        self.assertIsNone(creato.data_fine)
        chiuso = paziente.modifica_sintomo(
            sintomo_id=creato.id, payload=SintomoUpdate(data_fine=date(2026, 7, 3)),
            db=self.db, current=self.pat_user,
        )
        self.assertEqual(str(chiuso.data_fine), "2026-07-03")

    def test_messaggio_al_medico(self):  # RF-7
        msg = paziente.invia_messaggio_al_medico(
            payload=MessaggioPazienteCreate(oggetto="Domanda", corpo="Posso saltare una dose?"),
            db=self.db, current=self.pat_user,
        )
        self.assertEqual(msg.mittente_id, self.pat_user.id)
        self.assertEqual(msg.destinatario_id, self.doc_user.id)  # medico di riferimento

    def test_messaggio_senza_medico_400(self):  # RF-7 (nessun medico associato)
        self.pat_profile.doctor_id = None
        self.db.commit()
        with self.assertRaises(HTTPException) as ctx:
            paziente.invia_messaggio_al_medico(
                payload=MessaggioPazienteCreate(oggetto="X", corpo="Y"),
                db=self.db, current=self.pat_user,
            )
        self.assertEqual(ctx.exception.status_code, 400)


if __name__ == "__main__":
    unittest.main()
