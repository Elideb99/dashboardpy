from PyQt6.QtCore import QObject, pyqtSignal
from ovsvmlib import BaseWorker
from ovsvmlib.core import Message
import threading


# il worker che processa i messaggi 

class KafkaWorker(QObject):

    # signal verso la GUI / controller
    message_received = pyqtSignal(object)
    


    def __init__(self):

        super().__init__()
        self.running = True
        self._wrk = None


    def run(self): 
        """
        Questo metodo deve essere eseguito in un QThread.
        """

        print("KAFKA THREAD START:", threading.current_thread().name)

        # Istanza di BaseWorker da OVSVMLib, cioè il consumer di Kafka
        self._wrk = BaseWorker()

        # Connessione al cluster Kafka, cioè si collega al server 
        self._wrk.kafka_connect([
            'kafkacluster.int.ov.ingv.it:9095'
        ])


        # Callback chiamata da OVSVMLib ad ogni messaggio
        # definisce il callback per i messaggi in arrivo 
        def on_message(msg: Message):

            if not self.running:
                return

            # debug cioè stampa il messaggio, lo commento poichè ho filtrato il messaggio e reso leggibile
            #print(f"\n\nMESSAGGIO ARRIVATO: topic:{msg.topic}, class: {msg.message_class}, value: {msg.value} ")

            # NON toccare la GUI qui, emette il segnale per la GUI (thread-safe)
            self.message_received.emit(msg)

        # Loop bloccante (consumer Kafka) poichè significa-> rimani qui ad aspettare messaggi per sempre 
        # topic
        self._wrk.process_messages(
            #'waves.flegrei.IV.CSTH',
            ['events', 'replay.events', 'swarms', 'strongmotions', 'eew_events'],            
            on_data=on_message
        )

        print("KAFKA THREAD STOPPED")

    def stop(self):
     self.running = False

     if self._wrk is not None:
        try:
            self._wrk.stop_processing()  # ← questo sblocca process_messages che stava aspettando kafka
        except Exception as e:
            print(f"Errore chiusura worker: {e}")

     print("STOP KAFKA WORKER")

     #process_messages() -> stop_processing() -> esce dal loop -> thread termina

   

    