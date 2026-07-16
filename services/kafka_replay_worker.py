import json
import time
from PyQt6.QtCore import QObject, pyqtSignal


class FakeKafkaMessage:
    def __init__(self, value):
        self.value = value


class KafkaReplayWorker(QObject):
    message_received = pyqtSignal(object)

    def __init__(self, file_path, delay_seconds=0.2):
        super().__init__()
        self.file_path = file_path
        self.delay_seconds = delay_seconds
        self._running = True

    def run(self):
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