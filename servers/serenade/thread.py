import threading
import time

from .serenade import Serenade


class SerenadeThread(threading.Thread):

    # Inizializza il thread e il client Serenade.
    def __init__(self, config):
        super().__init__()
        self.client = Serenade(config)
        self.running = True

    # Esegue il polling periodico del servizio Serenade.
    def run(self):
        while self.running:
            events = self.client.get_events()
            print("Eventi Serenade:", len(events))
            # Qui possono essere inviati i dati alla GUI.
            time.sleep(self.client.refresh)