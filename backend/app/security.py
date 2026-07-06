"""
Configurazione e utility di sicurezza CONDIVISE.

Prima queste costanti vivevano dentro `routers/auth.py`; le abbiamo estratte qui
cosi' che sia il router di login sia la dependency `get_current_user`
(in `dependencies.py`) usino ESATTAMENTE la stessa chiave e lo stesso algoritmo,
evitando import circolari e disallineamenti nella firma/verifica del JWT.
"""

from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext


# =========================================================
# CONFIGURAZIONE JWT
# =========================================================
# NOTA: per un progetto d'esame va bene tenerla qui; in produzione si usa un .env
SECRET_KEY = "SUPER_SECRET_DIABETIFY_KEY_FOR_UNIVERSITY_PROJECT_2026"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120  # Il token scade dopo 2 ore

# Contesto passlib per l'hashing/verifica delle password (bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# =========================================================
# UTILITY PASSWORD
# =========================================================
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica che la password in chiaro corrisponda all'hash salvato nel DB."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Restituisce l'hash bcrypt di una password in chiaro."""
    return pwd_context.hash(password)


# =========================================================
# UTILITY TOKEN
# =========================================================
def create_access_token(payload: dict) -> str:
    """
    Firma un JWT aggiungendo automaticamente la scadenza (`exp`).
    Il `payload` deve contenere almeno `sub` (email), `id` e `role`.
    """
    to_encode = payload.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode["exp"] = expire
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
