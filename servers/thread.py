
from configparser import ConfigParser

from PyQt6.QtCore import QThread

from servers.serverkafka.kafka import KafkaWorker
from servers.serenade.serenade import SerenadeWorker


def start_data_server(config: ConfigParser):
    """
    Crea il worker Kafka o Serenade in base al file config.ini.

    Il thread viene configurato qui, ma viene avviato nel main.py.
    """

    data_source = config.get(
        "DATA",
        "source",
        fallback="kafka",
    ).strip().lower()

    thread = QThread()

    if data_source == "kafka":
        print("USO KAFKA")

        enabled = config.getboolean(
            "KAFKA",
            "enabled",
            fallback=True,
        )

        if not enabled:
            raise RuntimeError(
                "Kafka è selezionato, ma KAFKA.enabled è false."
            )

        server = config.get(
            "KAFKA",
            "server",
            fallback="localhost:9092",
        ).strip()

        print(f"Kafka server: {server}")

        # Se KafkaWorker non accetta parametri:
        worker = KafkaWorker()


    elif data_source == "serenade":
        print("USO SERENADE")

        enabled = config.getboolean(
            "SERENADE",
            "enabled",
            fallback=True,
        )

        if not enabled:
            raise RuntimeError(
                "Serenade è selezionato, "
                "ma SERENADE.enabled è false."
            )

        serenade_config = {
            "base_url": config.get(
                "SERENADE",
                "base_url",
                fallback="",
            ).strip(),

            "endpoint": config.get(
                "SERENADE",
                "endpoint",
                fallback="/events",
            ).strip(),

            "refresh": config.getint(
                "SERENADE",
                "refresh",
                fallback=10,
            ),

            "params": {
                "date": config.get(
                    "SERENADE",
                    "date",
                    fallback="",
                ).strip(),

                "level": config.get(
                    "SERENADE",
                    "level",
                    fallback="",
                ).strip(),
            },
        }

        worker = SerenadeWorker(serenade_config)

    else:
        raise ValueError(
            f"Sorgente dati non valida: '{data_source}'. "
            "Valori ammessi: kafka, serenade."
        )

    worker.moveToThread(thread)
    thread.started.connect(worker.run)

    # Il thread parte nel main.py tramite data_thread.start()
    return thread, worker



def load_map_filters(config=None):
    """
    Legge i filtri della mappa da config.ini.

    Se config non viene passato, lo carica automaticamente.
    """

    if config is None:
        from utils.config_loader import load_config
        config = load_config()

    default_filter = config.get(
        "MAP_FILTERS",
        "default",
        fallback="24h",
    ).strip()

    raw_options = config.get(
        "MAP_FILTERS",
        "options",
        fallback="24h,48h,7gg,14gg,1mese",
    )

    keys = [
        key.strip()
        for key in raw_options.split(",")
        if key.strip()
    ]

    options = []

    for key in keys:
        label = config.get(
            "MAP_FILTER_LABELS",
            key,
            fallback=key.upper(),
        )

        options.append({
            "key": key,
            "label": label,
        })

    return {
        "default": default_filter,
        "options": options,
    }