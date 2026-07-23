import json
import time

from servers.serverkafka.kafka import KafkaWorker


class _Msg:
    """Contenitore leggero per valore e topic di un messaggio replay."""

    __slots__ = ("value", "topic")

    # Inizializza il messaggio con contenuto e topic.
    def __init__(self, value, topic):
        self.value = value
        self.topic = topic


# Verifica se il valore rappresenta un messaggio di sciame.
def _e_sciame(value):
    return isinstance(value, dict) and "swarm_id" in value


# Verifica se il valore rappresenta un evento sismico.
def _e_evento(value):
    if isinstance(value, list):
        return any(
            isinstance(b, dict) and b.get("name") == "event"
            for b in value
        )

    return False


class ReplayFileWorker(KafkaWorker):
    """Riproduce da file i messaggi Kafka registrati."""

    # Inizializza il worker con uno o più file e l'intervallo di replay.
    def __init__(self, files, intervallo_ms=800):
        super().__init__()

        self.files = (
            [files]
            if isinstance(files, str)
            else list(files)
        )
        self.intervallo_ms = intervallo_ms
        self.running = True

    # Legge i file e inoltra eventi e sciami ai segnali corretti.
    def run(self):
        pausa = self.intervallo_ms / 1000.0
        n_ev = 0
        n_sw = 0

        for percorso in self.files:
            print(f"[REPLAY FILE] leggo {percorso}")

            try:
                f = open(percorso, encoding="utf-8")
            except FileNotFoundError:
                print(
                    f"[REPLAY FILE] file non trovato: {percorso}"
                )
                continue

            with f:
                for riga in f:
                    if not self.running:
                        print("[REPLAY FILE] interrotto")
                        return

                    riga = riga.strip()

                    if not riga:
                        continue

                    record = json.loads(riga)
                    value = record.get("value", record)
                    topic = record.get("topic")

                    if _e_sciame(value):
                        self.swarm_message_received.emit(
                            _Msg(
                                value,
                                topic or "replay.swarms"
                            )
                        )
                        n_sw += 1

                    elif _e_evento(value):
                        self.message_received.emit(
                            _Msg(
                                value,
                                topic or "replay.events"
                            )
                        )
                        n_ev += 1

                    # Ignora eventuali messaggi non riconosciuti.
                    if pausa:
                        time.sleep(pausa)

        print(
            f"[REPLAY FILE] finito: "
            f"{n_ev} eventi, {n_sw} sciami"
        )

    # Interrompe il replay del file.
    def stop(self):
        self.running = False
        print("[REPLAY FILE] stop")