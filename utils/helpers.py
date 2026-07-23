from datetime import datetime

def compute_ui_scale(screen_width: int, dpi: float = 96.0, device_pixel_ratio: float = 1.0) -> float:
    # riporta la larghezza fisica a larghezza "logica" (indipendente dal device pixel ratio)
    logical_width = screen_width / device_pixel_ratio

    scale_res = logical_width / 1920.0   # 1920px = riferimento base per scala 1.0


    REFERENCE_DPI = 96.0
    dpi_factor = (dpi / REFERENCE_DPI) ** 0.4   # esponente < 1: correzione morbida

    raw = scale_res * dpi_factor

    return max(0.8, min(raw, 4.0))   # clamp tra 0.8x e 4.0x



def message_handler(mode, context, message):
    # filtro per i log di Qt/sistema: scarta righe di rumore note (driver GPU, audio, ecc.)
    parole_da_ignorare = [
        "Vulkan", "vulkan", "GPUInfo", "pipewire",
        "PulseAudioService", "va-", "symbolsresolver",
        "No audio device", "Connection refused"
    ]
    if any(word in message for word in parole_da_ignorare):
        return
    print(message)


def chiave_data(entry):
    """UNICA regola di ordinamento temporale per stringa.

    Normalizza la 'T' perché come carattere vale più dello spazio: senza replace,
    '2026-06-25T04:13:11' risulterebbe MAGGIORE di '2026-06-25 23:59:59'.
    Usata anche da tabs.py, così la ★ e l'etichetta 'ultimo:' non possono divergere."""
    return str(entry.get("data") or "").replace("T", " ")


def seleziona_rappresentante(revisioni):
    """La revisione più recente che porta una magnitudo: quella è la definitiva.

    Una preliminare più alta non vince (Md3.60 delle 02:17:52 non deve coprire
    la Md3.58 delle 02:17:53), e nemmeno una revisione successiva che arriva
    senza magnitudo. Se nessuna revisione ha magnitudo, resta la più recente
    in assoluto e la riga mostra n.d."""
    validi = [r for r in revisioni if isinstance(r, dict)]
    if not validi:
        return None

    con_mag = [r for r in validi if r.get("magnitudine") is not None]
    return max(con_mag or validi, key=chiave_data)   # preferisce le revisioni con magnitudo, altrimenti tutte


def raggruppa_per_evento(logs):
    """Raggruppa i log per event_id, restituendo per ciascun gruppo il rappresentante
    (ultima revisione con magnitudo) e la data dell'ultimo aggiornamento ricevuto."""
    gruppi = {}
    ordine = []   # mantiene l'ordine di prima apparizione dei gruppi, prima del sort finale per data

    for entry in logs:
        if not isinstance(entry, dict):
            continue
        event_id = entry.get("event_id")
        # eventi senza event_id restano ognuno nel proprio gruppo singolo (chiave basata su id() dell'oggetto)
        chiave = event_id if event_id is not None else f"__single_{id(entry)}"
        if chiave not in gruppi:
            gruppi[chiave] = []
            ordine.append(chiave)
        gruppi[chiave].append(entry)

    risultato = []
    for chiave in ordine:
        revisioni = gruppi[chiave]
        risultato.append({
            "chiave": chiave,
            "rappresentante": seleziona_rappresentante(revisioni),
            "revisioni": revisioni,
            # NB: stessa chiave del rappresentante, altrimenti il "★ ultimo:" in tabella
            # potrebbe indicare una riga diversa da quella evidenziata nella tendina
            "data_ultimo_aggiornamento": max(revisioni, key=chiave_data).get("data", ""),
        })

    risultato.sort(key=lambda g: (g["data_ultimo_aggiornamento"] or "").replace("T", " "),
                   reverse=True)
    return risultato


def evento_piu_recente(logs):
    """Ritorna il rappresentante del gruppo di eventi più recente (per ultimo aggiornamento ricevuto), o None."""
    gruppi = raggruppa_per_evento(logs)
    return gruppi[0]["rappresentante"] if gruppi else None



def parse_event_datetime(date_str):
    """Converte una stringa data (con o senza millisecondi, con 'T' o spazio) in datetime, o None."""
    if not date_str:
        return None
    s = str(date_str).replace("T", " ").strip()
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(s[:26] if "." in s else s[:19], fmt)
        except ValueError:
            continue   # prova il formato successivo
    return None


def seleziona_ultima_scossa(logs, tolleranza_secondi=2):
    """Individua l'evento sismico più recente, raggruppando le revisioni ravvicinate
    (entro tolleranza_secondi) e scegliendo tra queste l'ultima magnitudo nota.
    Usato per lo stato del sistema, dove event_id può non essere stabile tra revisioni."""
    validi = [e for e in logs if isinstance(e, dict) and e.get("data")]
    if not validi:
        return None

    con_tempo = [(parse_event_datetime(e.get("data")), e) for e in validi]
    con_tempo = [(dt, e) for dt, e in con_tempo if dt is not None]

    if not con_tempo:
        # fallback: nessuna data parsabile, ordina comunque per stringa grezza
        return max(validi, key=chiave_data)

    con_tempo.sort(key=lambda t: t[0], reverse=True)
    riferimento = con_tempo[0][0]   # istante dell'evento più recente in assoluto

    # raggruppa tutti gli eventi entro la tolleranza dall'evento più recente (stessa scossa, revisioni multiple)
    cluster = [e for dt, e in con_tempo if abs((riferimento - dt).total_seconds()) <= tolleranza_secondi]

    return seleziona_rappresentante(cluster)