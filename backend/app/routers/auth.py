from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import jwt
from passlib.context import CryptContext

from app.database import get_db
from app.models import User
from app.schemas import Token

# =========================================================
# CONFIGURAZIONE SICUREZZA
# =========================================================
# NOTA: Per un progetto d'esame va bene tenerla qui, in produzione si usa un .env
SECRET_KEY = "SUPER_SECRET_DIABETIFY_KEY_FOR_UNIVERSITY_PROJECT_2026"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120  # Il token scade dopo 2 ore

# Inizializziamo il contesto per la gestione delle password
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter(tags=["Autenticazione"])

# Utility per verificare che la password in chiaro corrisponda all'hash nel DB
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


# =========================================================
# ENDPOINT DI LOGIN (Generazione JWT)
# =========================================================
@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    """
    Endpoint standard OAuth2 per l'autenticazione.
    Accetta 'username' (che per noi è l'email) e 'password' come form-data.
    Restituisce un JWT valido contenente l'ID e il ruolo dell'utente.
    """
    # 1. Cerchiamo l'utente nel database tramite l'email
    user = db.query(User).filter(User.email == form_data.username).first()
    
    # 2. Se l'utente non esiste o la password è sbagliata, lanciamo un 401
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o password non corrette",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 3. Controllo se l'account è disattivato dall'amministratore
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Questo account è stato disattivato."
        )

    # 4. Calcoliamo la scadenza del token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.now(timezone.utc) + access_token_expires
    
    # 5. Prepariamo il payload del JWT con i dati che serviranno a React
    token_payload = {
        "sub": user.email,       # Subject standard (l'email dell'utente)
        "id": user.id,           # ID dell'utente nel database
        "role": user.role.value, # Ruolo: "admin", "doctor", o "patient"
        "exp": expire            # Timestamp di scadenza
    }
    
    # 6. Firmiamo il token usando la nostra chiave segreta
    encoded_jwt = jwt.encode(token_payload, SECRET_KEY, algorithm=ALGORITHM)
    
    # 7. Restituiamo il token al frontend nel formato standard
    return {"access_token": encoded_jwt, "token_type": "bearer", "role": user.role.value}