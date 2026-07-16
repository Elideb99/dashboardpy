"""
Sorgente di REPLAY da file: sostituisce il KafkaWorker per testare la dashboard
con le registrazioni salvate, SENZA connettersi a Kafka.

È un KafkaWorker a tutti gli effetti (lo eredita), quindi:
  - il tuo isinstance(self.data_worker, KafkaWorker) nel Controller resta vero
  - i due segnali (message_received / swarm_message_received) si collegano da soli
  - NON devi toccare il Controller

Smista ogni riga del file sul segnale giusto, riconoscendo il tipo dal
CONTENUTO (quindi funziona anche sui file originali, senza il campo 'topic'):
  - lista con un blocco 'event'  -> message_received        (una scossa)
  - dict con 'swarm_id'          -> swarm_message_received  (uno sciame)

USO — nel punto dove crei il data_worker (di solito in main.py):

    # invece di:  data_worker = KafkaWorker(...)
    from replay_worker import ReplayFileWorker
    data_worker = ReplayFileWorker([
        "test_data/kafka_recordings/kafka_20260708_114405.jsonl",
        "test_data/kafka_recordings/kafka_20260708_125410.jsonl",
    ])

Il resto del setup (moveToThread, thread.started.connect(data_worker.run),
thread.start()) resta identico a come lo fai già per il KafkaWorker.
"""

import json
import time

from servers.serverkafka.kafka import KafkaWorker


class _Msg:
    """Oggetto minimo con .value e .topic, come i messaggi di ovsvmlib."""
    __slots__ = ("value", "topic")

    def __init__(self, value, topic):
        self.value = value
        self.topic = topic


def _e_sciame(value):
    return isinstance(value, dict) and "swarm_id" in value


def _e_evento(value):
    if isinstance(value, list):
        return any(isinstance(b, dict) and b.get("name") == "event" for b in value)
    return False


class ReplayFileWorker(KafkaWorker):
    """
    files          : percorso singolo o lista di percorsi .jsonl, riprodotti in ordine
    intervallo_ms  : pausa tra un messaggio e l'altro (0 = il più veloce possibile).
                     Un valore piccolo (20-40 ms) lascia respirare la GUI e ti fa
                     vedere lo sciame evolvere.
    """

    def __init__(self, files, intervallo_ms=800):
        super().__init__()
        self.files = [files] if isinstance(files, str) else list(files)
        self.intervallo_ms = intervallo_ms
        self.running = True

    def run(self):
        pausa = self.intervallo_ms / 1000.0
        n_ev = n_sw = 0

        for percorso in self.files:
            print(f"[REPLAY FILE] leggo {percorso}")
            try:
                f = open(percorso, encoding="utf-8")
            except FileNotFoundError:
                print(f"[REPLAY FILE] file non trovato: {percorso}")
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
                        self.swarm_message_received.emit(_Msg(value, topic or "replay.swarms"))
                        n_sw += 1
                    elif _e_evento(value):
                        self.message_received.emit(_Msg(value, topic or "replay.events"))
                        n_ev += 1
                    # altri tipi di messaggio: ignorati

                    if pausa:
                        time.sleep(pausa)

        print(f"[REPLAY FILE] finito: {n_ev} eventi, {n_sw} sciami")

    def stop(self):
        self.running = False
        print("[REPLAY FILE] stop")
