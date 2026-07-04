"""
Router dell'attore SISTEMA (Timer).

Espone il trigger manuale dei controlli temporali (RF-12/RF-13). In produzione
gli stessi controlli verrebbero eseguiti periodicamente da un cron/scheduler
(RNF-3, 24/7) tramite lo script run_sistema.py.

Il trigger e' riservato all'amministratore (Responsabile del Servizio), che
sovrintende al funzionamento del sistema.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin
from app.services.sistema import esegui_controlli

router = APIRouter(prefix="/sistema", tags=["Sistema"], dependencies=[Depends(require_admin)])


@router.post("/esegui-controlli")
def trigger_controlli(db: Session = Depends(get_db)):
    """
    RF-12/RF-13: esegue i controlli di aderenza terapeutica e genera i solleciti
    (al paziente) e gli alert di mancata aderenza (al medico). Idempotente.
    Restituisce il riepilogo delle notifiche create.
    """
    return esegui_controlli(db)
