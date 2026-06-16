import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import qInstallMessageHandler
from server import start_background_server

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

if __name__ == "__main__":
    start_background_server()
    app = QApplication(sys.argv)
    
    # Inizializzazione
    model = SystemModel()
    audio_service = AudioService()
    map_service = MapService()
    
    # Prima creiamo la View (senza controller)
    # Poi creiamo il controller con riferimento alla View
    # Infine colleghiamo model -> view
    controller = SystemController(model, audio_service, map_service, None)  # Temporaneo
    view = DashboardView(controller)
    controller.view = view  # Collega la view al controller
    
    # Collega model -> view per gli aggiornamenti automatici
    model.add_observer(view)
    
    view.show()
    sys.exit(app.exec())