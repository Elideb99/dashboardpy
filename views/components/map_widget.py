
import os
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QSizePolicy, QPushButton, QHBoxLayout, QWidget
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage
from PyQt6.QtCore import QUrl, pyqtSignal
from servers.thread import load_map_filters


class MapPage(QWebEnginePage):
    zone_clicked = pyqtSignal(str)

    def acceptNavigationRequest(self, url, nav_type, is_main_frame):
        if url.scheme() == 'app' and url.host() == 'tab':
            zona = url.path().strip('/').replace('-', ' ')
            self.zone_clicked.emit(zona)
            return False
        return super().acceptNavigationRequest(url, nav_type, is_main_frame)


class MapWidget:
    """VIEW: Gestisce il widget della mappa Leaflet"""

    _BASE_MIN_HEIGHT = 400

    def __init__(self, parent, ui_scale):
        self.parent   = parent
        self.ui_scale = ui_scale
        self.frame    = None
        self.webview  = None
        self.map_page = None
        self.on_loaded_callback = None
        self.on_filter_callback = None
        self._filter_buttons = {}
        self._active_filter = "24h"

    def scale(self, v):
        return max(1, int(v * self.ui_scale))


    def create(self):
     # ── carica filtri da config ──────────────────────────────
     filtri_cfg     = load_map_filters()
     filtri         = [(o["key"], o["label"]) for o in filtri_cfg["options"]]
     default_filter = filtri_cfg.get("default", filtri[0][0])

     self.frame = QFrame()
     self.frame.setFrameShape(QFrame.Shape.NoFrame)
     self.frame.setStyleSheet("border: none;")
     self.frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

     layout = QVBoxLayout()
     layout.setContentsMargins(0, 0, 0, 0)
     layout.setSpacing(0)

     # --- BARRA FILTRI ---
     btn_bar = QWidget()
     btn_bar.setFixedHeight(self.scale(36))
     btn_bar.setStyleSheet("background-color: #1C2B40; border: none;")
     btn_layout = QHBoxLayout()
     btn_layout.setContentsMargins(self.scale(8), self.scale(4), self.scale(8), self.scale(4))
     btn_layout.setSpacing(self.scale(6))

     btn_style = f"""
        QPushButton {{
            background-color: #1C2B40;
            color: #a0c4e8;
            font-size: {self.scale(13)}px;
            font-weight: bold;
            border: 1px solid #2A4A7D;
            border-radius: {self.scale(3)}px;
            padding: {self.scale(2)}px {self.scale(12)}px;
        }}
        QPushButton:hover {{
            background-color: #2A4A7D;
            color: white;
        }}
        QPushButton:checked {{
            background-color: #4A90E2;
            color: white;
            border: 1px solid #6aabff;
        }}
     """

     self._filter_buttons = {}
     self._active_filter  = default_filter   # ← usa il default dal config

     for key, label in filtri:               # ← usa i filtri dal config
        btn = QPushButton(label)
        btn.setCheckable(True)
        btn.setStyleSheet(btn_style)
        btn.clicked.connect(lambda checked, k=key: self._on_filter_clicked(k))
        btn_layout.addWidget(btn)
        self._filter_buttons[key] = btn

     btn_layout.addStretch()
     btn_bar.setLayout(btn_layout)

     # attiva il pulsante default
     if default_filter in self._filter_buttons:
        self._filter_buttons[default_filter].setChecked(True)

     # --- WEBVIEW ---
     self.webview = QWebEngineView()
     self.map_page = MapPage(self.webview)
     self.webview.setPage(self.map_page)
     self.webview.setUrl(QUrl("http://127.0.0.1:8000/map.html"))
     self.webview.settings().setAttribute(
         self.webview.settings().WebAttribute.WebGLEnabled, False
     )
     self.webview.loadFinished.connect(self._on_load_finished)

     layout.addWidget(btn_bar)
     layout.addWidget(self.webview)
     self.frame.setLayout(layout)

     self._apply_min_height()

    
    def _apply_min_height(self):
        h = min(int(200 * self.ui_scale), 1600)
        self.frame.setMinimumHeight(h)

    def update_height(self, ui_scale):
        self.ui_scale = ui_scale
        self._apply_min_height()

    def set_on_loaded(self, callback):
        self.on_loaded_callback = callback

    def _on_load_finished(self, ok):

     if not ok:
        # Controlla se è un falso negativo da navigazione intercettata
        url = self.webview.url().toString()
        if url.startswith('http://127.0.0.1:8000'):
            # La mappa è ancora lì, ignora l'errore
            return
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

    def set_on_filter(self, callback):
     self.on_filter_callback = callback

    def _on_filter_clicked(self, key):
     self._active_filter = key
     for k, btn in self._filter_buttons.items():
        btn.setChecked(k == key)
     if hasattr(self, 'on_filter_callback') and self.on_filter_callback:
        self.on_filter_callback(key)