from PyQt6.QtCore import QObject, pyqtSignal
from ovsvmlib import BaseWorker
from ovsvmlib.core import Message
import threading


class KafkaWorker(QObject):

    message_received = pyqtSignal(object)
    swarm_message_received = pyqtSignal(object)

    # Inizializza il worker Kafka e il relativo stato di esecuzione.
    def __init__(self):
        super().__init__()
        self.running = True
        self._wrk = None

    # Avvia la connessione a Kafka e inoltra i messaggi al segnale corretto.
    def run(self):
        self._wrk = BaseWorker()
        self._wrk.kafka_connect(['kafkacluster.int.ov.ingv.it:9095'])

        # Smista ogni messaggio ricevuto in base al topic Kafka.
        def on_message(msg: Message):
            if not self.running:
                return

            print(f"\n[KAFKA TOPIC] {msg.topic}")

            if "swarms" in msg.topic:
                self.swarm_message_received.emit(msg)
            else:
                self.message_received.emit(msg)

        self._wrk.process_messages(
            ['replay.events', 'strongmotions', 'eew_events', 'replay.swarms'],
            on_data=on_message
        )

        print("KAFKA THREAD STOPPED")

    # Arresta in modo sicuro l'elaborazione dei messaggi Kafka.
    def stop(self):
        self.running = False

        if self._wrk is not None:
            try:
                self._wrk.stop_processing()
            except Exception as e:
                print(f"Errore chiusura worker: {e}")

        print("STOP KAFKA WORKER")