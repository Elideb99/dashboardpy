"""Gestione allarmi basati su magnitudo per eventi sismici automatici."""

# NB: elenco degli autori "umani" — coerente con SystemModel.is_manuale() nel model,
# che fa una distinzione automatico/manuale analoga: se una delle due liste cambia,
# verificare se va aggiornata anche l'altra per restare allineate.
MANUAL_AUTHORS = {"Turnista", "Laboratorio di Sismologia"}
DEFAULT_THRESHOLD = 3.0


def is_automatic(evento: dict) -> bool:
    """True se l'evento non è ancora stato revisionato da un operatore umano."""
    return evento.get("author") not in MANUAL_AUTHORS


def should_alarm(evento: dict, soglia: float = DEFAULT_THRESHOLD) -> bool:
    """True se l'evento è automatico e la sua magnitudo supera la soglia."""
    if not is_automatic(evento):
        return False
    mag = evento.get("magnitudine")
    return mag is not None and mag >= soglia