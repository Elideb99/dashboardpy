import json
import time
from PyQt6.QtCore import QObject, pyqtSignal


class FakeKafkaMessage:
    # imita l'oggetto messaggio di Kafka (che espone .value) così il resto del codice
    # (on_kafka_message) può trattare i dati "rigiocati" da file esattamente come quelli live
    def __init__(self, value):
        self.value = value


class KafkaReplayWorker(QObject):
    message_received = pyqtSignal(object)   # stessa firma del segnale del KafkaWorker reale

    def __init__(self, file_path, delay_seconds=0.2):
        super().__init__()
        self.file_path = file_path
        self.delay_seconds = delay_seconds   # pausa tra un messaggio e l'altro, per simulare l'arrivo "dal vivo"
        self._running = True

    def run(self):
        # legge il file di registrazione (creato da KafkaRecorder) riga per riga ed emette ogni messaggio
        with open(self.file_path, "r", encoding="utf-8") as f:
            for line in f:
                if not self._running:
                    break

                record = json.loads(line)
                msg = FakeKafkaMessage(record["value"])

                self.message_received.emit(msg)

                time.sleep(self.delay_seconds)

    def stop(self):
        self._running = False