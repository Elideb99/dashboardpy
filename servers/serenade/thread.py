import threading
import time

from .serenade import Serenade



class SerenadeThread(threading.Thread):

    def __init__(self, config):

        super().__init__()

        self.client = Serenade(config)

        self.running = True



    def run(self):

        while self.running:


            events = self.client.get_events()


            print(
                "Eventi Serenade:",
                len(events)
            )


            # qui mandi i dati alla GUI


            time.sleep(
                self.client.refresh
            )