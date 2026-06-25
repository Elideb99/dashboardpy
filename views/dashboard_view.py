from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QApplication
from PyQt6.QtGui import QIcon

from views.components.header import HeaderView
from views.components.tabs import TabsView
from views.components.map_widget import MapWidget
from views.components.controls import ControlsView
from views.dialogs import AlarmDialog
from utils.helpers import compute_ui_scale



class DashboardView(QMainWindow):
    """VIEW: Gestisce l'interfaccia utente"""
    
    def __init__(self, controller):
        super().__init__()
        
        self.controller = controller # memorizza il riferimento al controller
        # dashboard_view.py  →  __init__
        screen = QApplication.primaryScreen()
        self.ui_scale = compute_ui_scale(
        screen.geometry().width(),
        dpi=screen.physicalDotsPerInchX(),
        device_pixel_ratio=screen.devicePixelRatio()
        ) # calcola il fattore di scala
        
        self.setWindowTitle("Sala di Monitoraggio - Simulatore")
        self.setMinimumSize(900, 600) # dimensione minima
        self.setStyleSheet("background-color: #1C2B40; color: #ffffff;")
        # applica uno stile css alla finestra

        self.tabs_view = None
        self.header = None
        self.map_widget = None
        self.controls = None
        
        self._setup_ui()
        self._setup_timers()
    
    def scale(self, v):
        return max(1, int(v * self.ui_scale))
    
    def _setup_ui(self):
        central = QWidget()
        main_layout = QVBoxLayout() # crea un layout verticale per organizzare i componenti
        main_layout.setContentsMargins(self.scale(15), self.scale(15), self.scale(15), self.scale(15))
        main_layout.setSpacing(self.scale(15))
        
        # Header- barra superiore
        self.header = HeaderView(self, self.ui_scale)
        self.header.create(main_layout)
        
        # Body
        body = QHBoxLayout()
        body.setSpacing(self.scale(15))
        
        # Left panel
        left_panel = QVBoxLayout()
        self.tabs_view = TabsView(self, self.ui_scale, self.controller.on_tab_changed)
        self.tabs_view.create(left_panel)
        
        # Controls
        #collega i controlli ai pulsanti
        self.controls = ControlsView(self, self.ui_scale)
        self.controls.create(left_panel)
        self.controls.set_controller(self.controller)
        
        # Map
        self.map_widget = MapWidget(self, self.ui_scale)
        self.map_widget.create()
        self.map_widget.set_on_loaded(self.controller.on_map_loaded)
        self.controller.map_service.set_webview(self.map_widget.webview)
        
        # Layout ratios
        # if self.ui_scale >= 2.5:
        #     ratio_left, ratio_right = 4, 6
        # elif self.ui_scale >= 1.8:
        #     ratio_left, ratio_right = 4, 6
        # elif self.ui_scale >= 1.5:
        #     ratio_left, ratio_right = 5, 5 #5:5
        # else:
        #     ratio_left, ratio_right = 6, 4 #6:4
        # Layout ratios - mappa e log sempre 50:50
        if self.ui_scale >= 2.5:
         ratio_left, ratio_right = 4, 6
        elif self.ui_scale >= 1.5:
         ratio_left, ratio_right = 5, 5
        else:
         ratio_left, ratio_right = 5, 5  # mai più largo dei log

        base_font_px = max(12, int(14 * self.ui_scale))
        self.setStyleSheet(
        f"background-color: #1C2B40; color: #ffffff; font-size: {base_font_px}px;"
        )
        
        body.addLayout(left_panel, ratio_left) # aggiungi pannello sx e dx
        body.addWidget(self.map_widget.frame, ratio_right)
        
        main_layout.addLayout(body)
        central.setLayout(main_layout)
        self.setCentralWidget(central)
    
    def _setup_timers(self):
        # Clock timer
        self.clock_timer = QTimer()
        self.clock_timer.timeout.connect(self._update_clock)
        self.clock_timer.start(1000)
        
        # Event time timer
        self.event_timer = QTimer()
        self.event_timer.timeout.connect(self._update_event_title)
        self.event_timer.start(1000)
        
        # Map queue timer
        self.queue_timer = QTimer() # timer per processare gli aggiornamenti in coda
        self.queue_timer.timeout.connect(self.controller.process_pending_updates)
        self.queue_timer.start(100)
    
    # ─── UI UPDATE METHODS ───────────────────────────────────
    def update_ui(self):
        """Aggiorna tutta l'UI in base al model"""
        # self.header.update_state(self.controller.model.status.value, 
        #                          self.controller.model.get_status_color())
        self._update_logs()
    
    def _update_logs(self):
        """Aggiorna i tab dei log"""
        for zone, logs in self.controller.model.tab_logs.items():
            if zone in self.tabs_view.tab_logs:
                self.tabs_view.update_logs(zone, logs)
    
    def _update_clock(self):
     """Aggiorna orologio e data con ora locale e UTC"""
     local_time = self.controller.get_current_time()
     utc_time = self.controller.get_utc_time()
     local_date = self.controller.get_current_date()
     utc_date = self.controller.get_current_date_utc()
     self.header.update_clock(local_time, utc_time, local_date, utc_date)
    
    def _update_event_title(self):
        """Aggiorna il titolo con il tempo dall'ultimo evento"""
        time_str = self.controller.get_time_since_last_event()
        if time_str:
            self.setWindowTitle(f"Sala di Monitoraggio - Ultimo evento: {time_str}")
    
    def flash_title(self):
        """Lampeggia il titolo"""
        original = self.windowTitle()
        for i in range(4):
            QTimer.singleShot(i * 300, lambda: self.setWindowTitle("ALLARME!"))
            QTimer.singleShot(i * 300 + 150, lambda: self.setWindowTitle(original))
        QTimer.singleShot(1200, self._update_event_title)
    
    def show_alarm_popup(self, magnitudo, zona):
        """Mostra popup allarme con lo stile originale"""
        dialog = AlarmDialog(self, self.ui_scale, magnitudo, zona)
        dialog.exec()
    
    def reset_window_title(self):
        """Resetta il titolo"""
        self.setWindowTitle("Sala di Monitoraggio - Simulatore") # ripristina il titolo originale
    
    def resizeEvent(self, event):
        """Gestisce il resize"""
        super().resizeEvent(event)
        self.header.resize(self.width()) # aggiorna l'altezza della mappa in base alla scala
        if self.map_widget:
            self.map_widget.update_height(self.ui_scale)
            self.controller.refresh_map() # richiede un refresh della mappa