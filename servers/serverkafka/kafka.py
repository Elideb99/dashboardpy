from PyQt6.QtCore import QObject, pyqtSignal
from ovsvmlib import BaseWorker
from ovsvmlib.core import Message
import threading

# kafkaworker che processa il messaggio e rimane in ascolto e quando arriva
# un nuovo evento esegue on_message
# non viene elaborato nulla il worker si limita ad inviare il messaggio al thread della gui 
# il controller riceve il messaggio in self. kafka_worker ecc 
# ogni volta che arriva un messaggio viene eseguito on_kafka_message
# il controller filtra il json -> aggiorna il model 
# il model notifica gli observer
# le view si aggiornano

# il worker che processa i messaggi 


   

class KafkaWorker(QObject):

    message_received = pyqtSignal(object)
    swarm_message_received = pyqtSignal(object)   # ← nuovo segnale dedicato

    def __init__(self):
        super().__init__()
        self.running = True
        self._wrk = None

    def run(self):
        self._wrk = BaseWorker()
        self._wrk.kafka_connect(['kafkacluster.int.ov.ingv.it:9095'])

        def on_message(msg: Message):
            if not self.running:
                return

            print(f"\n[KAFKA TOPIC] {msg.topic}")

            # smistamento in base al topic
            if "swarms" in msg.topic:
                self.swarm_message_received.emit(msg)
            else:
                self.message_received.emit(msg)

        self._wrk.process_messages(
            ['replay.events', 'strongmotions', 'eew_events', 'replay.swarms'],
            on_data=on_message
        )

        print("KAFKA THREAD STOPPED")

    def stop(self):
        self.running = False
        if self._wrk is not None:
            try:
                self._wrk.stop_processing()
            except Exception as e:
                print(f"Errore chiusura worker: {e}")
        print("STOP KAFKA WORKER")