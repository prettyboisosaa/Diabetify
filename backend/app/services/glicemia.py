"""
Servizio condiviso per l'analisi delle rilevazioni glicemiche.

L'aggregazione settimana/mese e la regola clinica RNF-1 vivono qui cosi' che sia
il router medico (RF-9) sia il router paziente (auto-visualizzazione) usino
ESATTAMENTE lo stesso calcolo, senza duplicazioni.
"""

from calendar import monthrange
from datetime import date, timedelta

from app.models import RilevazioneGlicemica, MomentoGlicemia
from app.schemas import (
    GlicemiaAggregata,
    SOGLIA_PRIMA_PASTO_MIN,
    SOGLIA_PRIMA_PASTO_MAX,
    SOGLIA_DOPO_PASTO_MAX,
)


def e_fuori_soglia(valore: int, momento: MomentoGlicemia) -> bool:
    """Regola clinica RNF-1 (stessa logica del computed_field dello schema)."""
    if momento == MomentoGlicemia.PRIMA_PASTO:
        return valore < SOGLIA_PRIMA_PASTO_MIN or valore > SOGLIA_PRIMA_PASTO_MAX
    return valore > SOGLIA_DOPO_PASTO_MAX


def _chiave_periodo(d: date, periodo: str) -> tuple[date, date]:
    """
    Dato un giorno, restituisce (inizio, fine) del periodo che lo contiene.
    - settimana: lunedi' -> domenica (ISO)
    - mese: primo -> ultimo giorno del mese
    """
    if periodo == "settimana":
        inizio = d - timedelta(days=d.weekday())  # lunedi'
        fine = inizio + timedelta(days=6)          # domenica
    else:  # "mese"
        inizio = d.replace(day=1)
        ultimo_giorno = monthrange(d.year, d.month)[1]
        fine = d.replace(day=ultimo_giorno)
    return inizio, fine


def aggrega_glicemie(
    rilevazioni: list[RilevazioneGlicemica],
    periodo: str,
) -> list[GlicemiaAggregata]:
    """
    Raggruppa le rilevazioni per settimana o mese e calcola, per ogni periodo,
    media/minimo/massimo/n. misurazioni/n. fuori soglia (RF-9, RNF-1).

    Il raggruppamento e' fatto in memoria: piu' portabile delle funzioni
    data-specifiche di SQLite e sufficiente per i volumi di un progetto d'esame.
    """
    gruppi: dict[date, list[RilevazioneGlicemica]] = {}
    intervalli: dict[date, tuple[date, date]] = {}
    for r in rilevazioni:
        giorno = r.timestamp.date()
        inizio, fine = _chiave_periodo(giorno, periodo)
        gruppi.setdefault(inizio, []).append(r)
        intervalli[inizio] = (inizio, fine)

    risultato: list[GlicemiaAggregata] = []
    for inizio in sorted(gruppi.keys()):
        valori = [r.valore for r in gruppi[inizio]]
        num_fuori = sum(
            1 for r in gruppi[inizio] if e_fuori_soglia(r.valore, r.momento)
        )
        p_inizio, p_fine = intervalli[inizio]
        risultato.append(
            GlicemiaAggregata(
                periodo_inizio=p_inizio,
                periodo_fine=p_fine,
                media=round(sum(valori) / len(valori), 1),
                minimo=min(valori),
                massimo=max(valori),
                num_misurazioni=len(valori),
                num_fuori_soglia=num_fuori,
            )
        )
    return risultato
