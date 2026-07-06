"""
Test di autenticazione (RF-1) e delle guardie di ruolo.
"""

import unittest

from fastapi import HTTPException

from tests.base import DBTestCase
from app.security import create_access_token, verify_password
from app.dependencies import (
    get_current_user,
    require_doctor,
    require_patient,
    require_admin,
)


class TestAutenticazione(DBTestCase):
    def _token(self, user):
        return create_access_token({"sub": user.email, "id": user.id, "role": user.role.value})

    def test_password_hash_verificabile(self):
        self.assertTrue(verify_password("Medico2026!!aa", self.doc_user.password_hash))
        self.assertFalse(verify_password("sbagliata", self.doc_user.password_hash))

    def test_token_valido_restituisce_utente(self):
        token = self._token(self.doc_user)
        user = get_current_user(token=token, db=self.db)
        self.assertEqual(user.id, self.doc_user.id)
        self.assertEqual(user.email, "doc@test.it")

    def test_token_non_valido_solleva_401(self):
        with self.assertRaises(HTTPException) as ctx:
            get_current_user(token="token.finto.rotto", db=self.db)
        self.assertEqual(ctx.exception.status_code, 401)

    def test_utente_disattivato_solleva_400(self):
        self.doc_user.is_active = False
        self.db.commit()
        token = self._token(self.doc_user)
        with self.assertRaises(HTTPException) as ctx:
            get_current_user(token=token, db=self.db)
        self.assertEqual(ctx.exception.status_code, 400)


class TestGuardieRuolo(DBTestCase):
    def test_require_doctor_ok_e_403(self):
        self.assertIs(require_doctor(self.doc_user), self.doc_user)
        for utente in (self.pat_user, self.admin_user):
            with self.assertRaises(HTTPException) as ctx:
                require_doctor(utente)
            self.assertEqual(ctx.exception.status_code, 403)

    def test_require_patient_ok_e_403(self):
        self.assertIs(require_patient(self.pat_user), self.pat_user)
        with self.assertRaises(HTTPException) as ctx:
            require_patient(self.doc_user)
        self.assertEqual(ctx.exception.status_code, 403)

    def test_require_admin_ok_e_403(self):
        self.assertIs(require_admin(self.admin_user), self.admin_user)
        with self.assertRaises(HTTPException) as ctx:
            require_admin(self.pat_user)
        self.assertEqual(ctx.exception.status_code, 403)


if __name__ == "__main__":
    unittest.main()
