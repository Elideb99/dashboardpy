    
import sys
import os
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
import argparse
from pathlib import Path
from replay_worker import ReplayFileWorker
from utils.config_loader import load_config


os.environ["QT_QPA_PLATFORM"] = "xcb"
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu --no-sandbox --log-level=3"
os.environ["QT_MULTIMEDIA_PREFERRED_PLUGINS"] = "pulseaudio"

qInstallMessageHandler(message_handler)

def parse_arguments():
     parser = argparse.ArgumentParser(
        description="Dashboard di monitoraggio sismico"
     )

     parser.add_argument(
        "--replay",
        action="store_true",
        help="Avvia il progetto usando i file Kafka registrati"
     )

     return parser.parse_args()

if __name__ == "__main__":
    args = parse_arguments()

    start_background_server()
    app = QApplication(sys.argv)

    model = SystemModel()
    audio_service = AudioService()
    map_service = MapService()

    if args.replay:
        print("[AVVIO] Modalità replay Kafka")

        BASE_DIR = Path(__file__).resolve().parent

        data_worker = ReplayFileWorker([
            str(
                BASE_DIR
                / "test_data"
                / "kafka_recordings"
                / "kafka_20260708_114405.jsonl"
            ),
            str(
                BASE_DIR
                / "test_data"
                / "kafka_recordings"
                / "kafka_20260708_125410.jsonl"
            ),
            #  str(
            #     BASE_DIR
            #     / "test_data"
            #     / "kafka_recordings"
            #     / "kafka_20260715_090312.jsonl"
            # ),
            
        ])

        data_thread = QThread()
        data_worker.moveToThread(data_thread)
        data_thread.started.connect(data_worker.run)

    else:
        print("[AVVIO] Modalità normale da config.ini")

        config = load_config()
        data_thread, data_worker = start_data_server(config)

    controller = SystemController(
        model,
        audio_service,
        map_service,
        data_worker=data_worker,
        data_thread=data_thread,
    )

    view = DashboardView(controller)
    controller.view = view

    model.add_observer(view)

    #data_thread.start()
    view.show()

    def cleanup():
        print("CHIUSURA SORGENTE DATI")

        data_worker.stop()
        data_thread.requestInterruption()
        data_thread.quit()
        data_thread.wait()

    app.aboutToQuit.connect(cleanup)

    sys.exit(app.exec())
