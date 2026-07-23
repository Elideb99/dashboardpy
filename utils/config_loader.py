from configparser import ConfigParser
from pathlib import Path

# config.ini si aspetta un livello sopra la cartella di questo modulo (root del progetto)
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config.ini"


def load_config():
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"File config.ini non trovato: {CONFIG_PATH}"
        )

    config = ConfigParser()
    config.read(CONFIG_PATH, encoding="utf-8")

    return config