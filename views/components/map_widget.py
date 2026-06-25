import os
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QSizePolicy
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl



class MapWidget:
    """VIEW: Gestisce il widget della mappa Leaflet"""

    # Altezza minima a scala 1.0 (schermo 1920 px / 96 dpi).
    # Tutto il resto si ottiene moltiplicando per ui_scale.
    _BASE_MIN_HEIGHT = 400   # px a scala 1.0

    def __init__(self, parent, ui_scale):
        self.parent   = parent
        self.ui_scale = ui_scale
        self.frame    = None
        self.webview  = None
        self.on_loaded_callback = None

    def scale(self, v):
        return max(1, int(v * self.ui_scale))

    # def create(self):
    #     self.frame = QFrame()
    #     self.frame.setFrameShape(QFrame.Shape.Box)
    #     self.frame.setStyleSheet("border: 1px solid #ccc;")

    #     layout   = QVBoxLayout()
    #     layout.setContentsMargins(0, 0, 0, 0)   # niente padding interno
    #     self.webview = QWebEngineView()
    #     # self.webview.setUrl(QUrl("http://127.0.0.1:8000/map.html"))
    #     # self.webview.settings().setAttribute(
    #     #     self.webview.settings().WebAttribute.WebGLEnabled, False
    #     # )
    #     base_dir = os.path.dirname(os.path.abspath(__file__))
    #     map_path = os.path.join(base_dir, "servers" ,"servermap", "map.html")
    #     self.webview.setUrl(QUrl.fromLocalFile(map_path))

    #     self.webview.loadFinished.connect(self._on_load_finished)
    #     layout.addWidget(self.webview)
    #     self.frame.setLayout(layout)

    #     self._apply_min_height()

    def create(self):
     self.frame = QFrame()
     self.frame.setFrameShape(QFrame.Shape.Box)
     self.frame.setStyleSheet("border: 1px solid #ccc;")
     self.frame.setSizePolicy(
        QSizePolicy.Policy.Expanding,
        QSizePolicy.Policy.Expanding   # ← si espande in altezza
    )

     layout = QVBoxLayout()
     layout.setContentsMargins(0, 0, 0, 0)
     self.webview = QWebEngineView()
    
     # Usa il server HTTP invece del file locale
     self.webview.setUrl(QUrl("http://127.0.0.1:8000/map.html"))
     self.webview.settings().setAttribute(
        self.webview.settings().WebAttribute.WebGLEnabled, False
     )
    
     self.webview.loadFinished.connect(self._on_load_finished)
     layout.addWidget(self.webview)
     self.frame.setLayout(layout)

     self._apply_min_height()


    # def _apply_min_height(self):
    #     """
    #     Altezza minima = BASE * ui_scale, con un tetto ragionevole
    #     in modo che su schermi 8K non occupi l'intera display.
    #     """
    #     h = min(int(self._BASE_MIN_HEIGHT * self.ui_scale), 1600)
    #     self.frame.setMinimumHeight(h)

    def _apply_min_height(self):
     h = min(int(200 * self.ui_scale), 1600)  # era 400, ora 200
     self.frame.setMinimumHeight(h)

    def update_height(self, ui_scale):
        self.ui_scale = ui_scale
        self._apply_min_height()

    def set_on_loaded(self, callback):
        self.on_loaded_callback = callback

    def _on_load_finished(self, ok):
       # print("Mappa caricata" if ok else "Errore mappa")
        if self.on_loaded_callback:
            self.on_loaded_callback(ok)

    def refresh(self):
        if self.webview:
            self.webview.page().runJavaScript("""
                if (typeof refreshMapView !== 'undefined') {
                    refreshMapView();
                } else if (typeof map !== 'undefined' && map) {
                    setTimeout(function() { map.invalidateSize(); }, 100);
                }
            """)