import sys
import os
import threading
# from ovsvmlib.core import Message
# from ovsvmlib import BaseWorker
#from servers.serverkafka.kafka import KafkaWorker
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import qInstallMessageHandler,QThread
from servers.servermap.server import start_background_server
from servers.thread import start_data_server

from models.system_model import SystemModel
from services.audio_service import AudioService
from services.map_service import MapService
from controllers.system_controller import SystemController
from views.dashboard_view import DashboardView
from utils.helpers import message_handler



os.environ["QT_QPA_PLATFORM"] = "xcb"
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu --no-sandbox --log-level=3"
os.environ["QT_MULTIMEDIA_PREFERRED_PLUGINS"] = "pulseaudio"

qInstallMessageHandler(message_handler)


# def kernel(msg: Message):
#     print(msg.value)

if __name__ == "__main__":
    start_background_server()
    print("SERVER CHIAMATO")
    app = QApplication(sys.argv)
    
    # Inizializzazione MVC
    model = SystemModel()
    audio_service = AudioService()
    map_service = MapService()
    # Avvio sorgente dati scelta da config.json
    data_thread, data_worker = start_data_server()
    
    # Prima creiamo la View (senza controller)
    # Poi creiamo il controller con riferimento alla View
    # Infine colleghiamo model -> view

    # Kafka thread
    #kafka_thread = QThread()
    # creo un thread Qt vuoto che rappresenta il secondo filo di esecuzione separato dal thread della GUI
    #kafka_worker = KafkaWorker()
    # creo il worker
 
    #kafka_worker.moveToThread(kafka_thread)
    # sposto il worker nel nuovo thread, il worker non eseguirà più i suoi slot nel thread GUI

    # quando parte il thread esegue run()
   # kafka_thread.started.connect(kafka_worker.run)

    

    controller = SystemController(model, audio_service, map_service,data_worker = data_worker)  # Temporaneo
    view = DashboardView(controller)
    controller.view = view  # Collega la view al controller
    
    # Collega model -> view per gli aggiornamenti automatici
    model.add_observer(view)
    data_thread.start()
    
    view.show()
    print("Main thread:", threading.current_thread().name)

    #Kafka -> Controller
    #kafka_worker.message_received.connect(controller. on_kafka_message)

    #kafka_thread.start()

    # chiusura 

    def cleanup():

        print("CHIUSURA SORGENTE DATI")

        data_worker.stop()
        data_thread.requestInterruption()
        data_thread.quit()
        data_thread.wait()


    app.aboutToQuit.connect(
        cleanup
    )



    sys.exit(app.exec())
    