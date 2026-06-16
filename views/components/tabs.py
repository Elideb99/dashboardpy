from PyQt6.QtWidgets import QTabWidget, QTextEdit, QVBoxLayout

class TabsView:
    """VIEW: Gestisce i tab dei log"""
    
    def __init__(self, parent, ui_scale, on_tab_changed_callback):
        self.parent = parent
        self.ui_scale = ui_scale
        self.on_tab_changed_callback = on_tab_changed_callback
        self.tabs = None
        self.tab_logs = {}
    
    def scale(self, v):
        return max(1, int(v * self.ui_scale))
    
    def fs(self, px):
        return f"{self.scale(px)}px"
    
    def create(self, parent_layout):
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.tabBar().setExpanding(True)
        
        # Stile tabs
        tab_font_size = self.fs(16)
        tab_min_height = self.scale(35)
        tab_padding_h = self.scale(15)
        tab_margin_top = self.scale(20)
        
        self.tabs.tabBar().setStyleSheet(f"""
        QTabBar::tab {{
            background-color: #213B64;
            color: white;
            font-weight: bold;
            font-size: {tab_font_size};
            min-height: {tab_min_height}px;
            padding-left: {tab_padding_h}px;
            padding-right: {tab_padding_h}px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            margin-right: {self.scale(2)}px;
            margin-top: {tab_margin_top}px;
        }}
        QTabBar::tab:hover {{
            background-color: #2A4A7D;
        }}
        QTabBar::tab:selected {{
            font-size: {tab_font_size};
            font-weight: bold;
            padding-left: {tab_padding_h}px;
            padding-right: {tab_padding_h}px;
            border-radius: 6px;
            color: white;
            background-color: #2A4A7D;
            border: {self.scale(2)}px solid #4A90E2;
            margin-top: {tab_margin_top}px;
        }}
        """)
        
        # Crea i tab per ogni zona
        zone_tabs = [
            ("GENERALE", "#ffffff"),
            ("CAMPI FLEGREI", "#3DDC84"),
            ("VESUVIO", "#3DDC84"),
            ("ISCHIA", "#3DDC84"),
        ]
        
        log_font_size = self.fs(17)
        for nome_tab, color_testo in zone_tabs:
            text_edit = QTextEdit()
            text_edit.setReadOnly(True)
            text_edit.setStyleSheet(
                f"font-family: monospace; "
                f"background-color: #1e1e1e; "
                f"color: {color_testo}; "
                f"font-size: {log_font_size};"
            )
            self.tab_logs[nome_tab] = text_edit
            self.tabs.addTab(text_edit, nome_tab)
        
        self.tabs.currentChanged.connect(self._on_tab_changed)
        parent_layout.addWidget(self.tabs, 1)
    
    def _on_tab_changed(self, index):
        tab_name = self.tabs.tabText(index)
        self.on_tab_changed_callback(tab_name)
    
    def update_logs(self, zone, logs):
        """Aggiorna i log per una zona specifica"""
        if zone in self.tab_logs:
            self.tab_logs[zone].clear()
            for log in logs:
                self.tab_logs[zone].append(log)
            scroll = self.tab_logs[zone].verticalScrollBar()
            scroll.setValue(scroll.maximum())
    
    def add_log(self, zone, message):
        """Aggiunge un singolo log (usato per aggiornamenti incrementali)"""
        if zone in self.tab_logs:
            self.tab_logs[zone].append(message)
            scroll = self.tab_logs[zone].verticalScrollBar()
            scroll.setValue(scroll.maximum())