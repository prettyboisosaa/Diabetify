from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import Token
# Le costanti/utility di sicurezza vivono ora in app.security (condivise con le dependency)
from app.security import verify_password, create_access_token

router = APIRouter(tags=["Autenticazione"])


# =========================================================
# ENDPOINT DI LOGIN (Generazione JWT) - RF-1, UC-3
# =========================================================
@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    Endpoint standard OAuth2 per l'autenticazione.
    Accetta 'username' (che per noi e' l'email) e 'password' come form-data.
    Restituisce un JWT valido contenente l'ID e il ruolo dell'utente.
    """
    # 1. Cerchiamo l'utente nel database tramite l'email
    user = db.query(User).filter(User.email == form_data.username).first()

    # 2. Se l'utente non esiste o la password e' sbagliata, lanciamo un 401
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o password non corrette",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Controllo se l'account e' stato disattivato dall'amministratore
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Questo account e' stato disattivato.",
        )

    # 4. Prepariamo il payload del JWT con i dati che serviranno a React.
    #    La scadenza (exp) viene aggiunta da create_access_token.
    token_payload = {
        "sub": user.email,        # Subject standard (l'email dell'utente)
        "id": user.id,            # ID dell'utente nel database
        "role": user.role.value,  # Ruolo: "admin", "doctor", o "patient"
    }

    # 5. Firmiamo il token e lo restituiamo nel formato standard OAuth2
    encoded_jwt = create_access_token(token_payload)
    return {"access_token": encoded_jwt, "token_type": "bearer", "role": user.role.value}
