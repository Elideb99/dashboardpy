import random
from datetime import datetime

def compute_ui_scale(screen_width: int, dpi: float = 96.0, device_pixel_ratio: float = 1.0) -> float:
    """
    Scala UI per schermi 30-50".

    La larghezza in pixel logici (screen_width / device_pixel_ratio) viene
    confrontata con la base 1920 px; il DPI fisico corregge il risultato
    perché un 4K da 32" e un 4K da 50" hanno la stessa risoluzione ma
    densità molto diverse → su 50" i widget non devono essere più grandi.

    Parametri
    ----------
    screen_width        : pixel totali orizzontali riportati da Qt
    dpi                 : physicalDotsPerInchX() dello schermo
    device_pixel_ratio  : devicePixelRatio() dello schermo (HiDPI factor del SO)

    Riferimento: 1920 px logici a 96 DPI → scala 1.0
    """
    
    logical_width = screen_width / device_pixel_ratio

    scale_res = logical_width / 1920.0


    REFERENCE_DPI = 96.0
    dpi_factor = (dpi / REFERENCE_DPI) ** 0.4   # esponente < 1: correzione morbida

    raw = scale_res * dpi_factor

    return max(0.8, min(raw, 4.0))


def message_handler(mode, context, message):
    parole_da_ignorare = [
        "Vulkan", "vulkan", "GPUInfo", "pipewire",
        "PulseAudioService", "va-", "symbolsresolver",
        "No audio device", "Connection refused"
    ]
    if any(word in message for word in parole_da_ignorare):
        return
    print(message)


def get_random_event():
    mag  = round(random.uniform(1.0, 4.8), 1)
    zone = random.choice(["Vesuvio", "Campi Flegrei", "Ischia"])
    zone_filter = {
        "Campi Flegrei": "CAMPI FLEGREI",
        "Vesuvio":       "VESUVIO",
        "Ischia":        "ISCHIA",
    }
    return mag, zone, zone_filter[zone]