from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QApplication

from views.components.header import HeaderView
from views.components.tabs import TabsView
from views.components.map_widget import MapWidget
from views.dialogs import AlarmDialog
from utils.helpers import compute_ui_scale


class DashboardView(QMainWindow):
    """VIEW: gestisce la finestra principale e i componenti dell'interfaccia."""

    # Inizializza la finestra, calcola la scala grafica e crea l'interfaccia.
    def __init__(self, controller):
        super().__init__()

        self.controller = controller

        screen = QApplication.primaryScreen()
        self.ui_scale = compute_ui_scale(
            screen.geometry().width(),
            dpi=screen.physicalDotsPerInchX(),
            device_pixel_ratio=screen.devicePixelRatio()
        )

        self.setWindowTitle("Sala di Monitoraggio - Simulatore")
        self.setMinimumSize(900, 600)
        self.setStyleSheet(
            "background-color: #0F1521; color: #ffffff;"
        )

        self.tabs_view = None
        self.header = None
        self.map_widget = None

        self._setup_ui()
        self._setup_timers()

    # Ridimensiona un valore in base al fattore di scala dell'interfaccia.
    def scale(self, v):
        return max(1, int(v * self.ui_scale))

    # Crea e dispone tutti i componenti grafici della finestra.
    def _setup_ui(self):
        central = QWidget()
        central.setStyleSheet("background-color: #0D1520;")

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(
            self.scale(15),
            self.scale(15),
            self.scale(15),
            self.scale(15)
        )
        main_layout.setSpacing(self.scale(15))

        # Crea l'header superiore.
        self.header = HeaderView(self, self.ui_scale)
        self.header.create(main_layout)

        # Crea il contenitore principale.
        body = QHBoxLayout()
        body.setSpacing(self.scale(15))

        # Crea il pannello sinistro con log e controlli.
        left_panel = QVBoxLayout()

        self.tabs_view = TabsView(
            self,
            self.ui_scale,
            self.controller.on_tab_changed
        )
        self.tabs_view.create(left_panel)


        # Crea e configura la mappa.
        self.map_widget = MapWidget(self, self.ui_scale)
        self.map_widget.create()
        self.map_widget.set_on_loaded(self.controller.on_map_loaded)
        self.map_widget.map_page.zone_clicked.connect(
            self._on_map_zone_clicked
        )
        self.map_widget.map_page.replay_requested.connect(
            self.controller.on_replay_sciame_richiesto
        )
        self.map_widget.set_on_filter(
            self.controller.on_filter_changed
        )

        self.controller.map_service.set_webview(
            self.map_widget.webview
        )

        ratio_left, ratio_right = 5, 5

        base_font_px = max(12, int(14 * self.ui_scale))
        self.setStyleSheet(
            f"background-color: #0D1520; "
            f"color: #ffffff; "
            f"font-size: {base_font_px}px;"
        )

        body.addLayout(left_panel, ratio_left)
        body.addWidget(self.map_widget.frame, ratio_right)

        main_layout.addLayout(body)
        central.setLayout(main_layout)
        self.setCentralWidget(central)

    # Configura i timer usati per orologio, titolo e aggiornamenti della mappa.
    def _setup_timers(self):
        self.clock_timer = QTimer()
        self.clock_timer.timeout.connect(self._update_clock)
        self.clock_timer.start(1000)

        self.event_timer = QTimer()
        self.event_timer.timeout.connect(self._update_event_title)
        self.event_timer.start(1000)

        self.queue_timer = QTimer()
        self.queue_timer.timeout.connect(
            self.controller.process_pending_updates
        )
        self.queue_timer.start(100)

    # Aggiorna l'interfaccia in base ai dati presenti nel modello.
    def update_ui(self):
        self._update_logs()
        self._update_state_from_model()

    # Aggiorna le tabelle dei log visualizzate nelle schede.
    def _update_logs(self):
        self.controller.render_logs_filtrati()

    # Aggiorna l'header usando lo stato determinato dal modello.
    def _update_state_from_model(self):
        evento = self.controller.model.evento_stato

        if evento is None:
            self.header.update_state_from_event(None)
            return

        mag = self._parse_magnitudo(
            evento.get("magnitudine")
        )
        self.header.update_state_from_event(
            mag,
            evento.get("data")
        )

    # Converte una magnitudo testuale in float.
    @staticmethod
    def _parse_magnitudo(mag_raw):
        if mag_raw is None:
            return None

        s = str(mag_raw).strip().upper()

        if s in ("N.D.", "ND", "NA", "N/A", ""):
            return None

        s = s.lstrip("M").strip()

        try:
            return float(s)
        except ValueError:
            return None

    # Aggiorna data e ora locale e UTC mostrate nell'header.
    def _update_clock(self):
        local_time = self.controller.get_current_time()
        utc_time = self.controller.get_utc_time()
        local_date = self.controller.get_current_date()
        utc_date = self.controller.get_current_date_utc()

        self.header.update_clock(
            local_time,
            utc_time,
            local_date,
            utc_date
        )

    # Aggiorna il titolo principale della finestra.
    def _update_event_title(self):
        self.setWindowTitle("Sala di Monitoraggio")


    # Aggiorna header e mappa quando la finestra viene ridimensionata.
    def resizeEvent(self, event):
        super().resizeEvent(event)

        if self.header:
            self.header.resize(self.width())

        if self.map_widget:
            self.map_widget.update_height(
                self.ui_scale
            )
            self.controller.refresh_map()

    # Seleziona la scheda corrispondente alla zona cliccata sulla mappa.
    def _on_map_zone_clicked(self, zona):
        tab_nomi = [
            "GENERALE",
            "CAMPI FLEGREI",
            "VESUVIO",
            "ISCHIA"
        ]

        if zona not in tab_nomi:
            return

        idx_zona = tab_nomi.index(zona)
        self.tabs_view.tabs.setCurrentIndex(
            idx_zona
        )
