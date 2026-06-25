import requests
import time
import threading
from PyQt6.QtCore import QObject, pyqtSignal



class SerenadeWorker(QObject):

    message_received = pyqtSignal(object) # emette la lista di eventi JSON
    error_occurred   = pyqtSignal(str)  # emette errori (opzionale ma utile)


    def __init__(self, config):
        super().__init__()
        self.url = config["base_url"] + config["endpoint"]
        self.params = config["params"]
        self.refresh = config["refresh"]
        self._running = False

    def run(self):
        """
        Stesso slot di KafkaWorker: viene chiamato da thread.started.
        Loop di polling con sleep interrompibile.
        """
        print("SERENADE THREAD START:", threading.current_thread().name)
        self._running = True

        while self._running:
            try:
                r = requests.get(
                    self.url,
                    params=self.params,
                    timeout=10
                )
                r.raise_for_status()
                eventi = r.json()
                self.message_received.emit(eventi)

            except Exception as e:
                print("Errore Serenade:", e)
                self.error_occurred.emit(str(e))

            # sleep a pezzi: controlla _running ogni secondo
            # invece di bloccare per tutti i `refresh` secondi
            for _ in range(self.refresh):
                if not self._running:
                    break
                time.sleep(1)

        print("SERENADE THREAD STOPPED")

    def stop(self):
        self._running = False
        print("STOP SERENADE WORKER")



    # def get_events(self):

    #     try:

    #         r = requests.get(
    #             self.url,
    #             params=self.params
    #         )

    #         return r.json()


    #     except Exception as e:

    #         print(
    #             "Errore Serenade:",
    #             e
    #         )

    #         return []