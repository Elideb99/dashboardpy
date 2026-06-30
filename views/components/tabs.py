from PyQt6.QtWidgets import QTabWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QHeaderView, QSizePolicy
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

class TabsView:
    """VIEW: Gestisce i tab dei log"""

    COLONNE = ["Data/Ora", "Area", "Mag", "Prof (km)", "Lat", "Lon", "Q"]

    def __init__(self, parent, ui_scale, on_tab_changed_callback):
        self.parent = parent
        self.ui_scale = ui_scale
        self.on_tab_changed_callback = on_tab_changed_callback
        self.tabs = None
        self.tab_logs = {}   # ora contiene QTableWidget invece di QTextEdit

    def scale(self, v):
        return max(1, int(v * self.ui_scale))

    def fs(self, px):
        return f"{self.scale(px)}px"

    # def _make_table(self, color_testo):
    #     table = QTableWidget()
    #     table.setColumnCount(len(self.COLONNE))
    #     table.setHorizontalHeaderLabels(self.COLONNE)
    #     table.setRowCount(0)
    #     table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    #     table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    #     table.verticalHeader().setVisible(False)
    #     table.setShowGrid(False)
    #     table.setAlternatingRowColors(True)

    #     # Larghezze colonne
    #     # header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
    #     # header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
    #     header = table.horizontalHeader()
    #     header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    #     header.setMinimumSectionSize(self.scale(60))

    #     # header = table.horizontalHeader()

    #     # # prima colonna bloccata
    #     # header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
    #     # header.resizeSection(0, self.scale(160))

    #     # # tutte le altre
    #     # for i in range(1, len(self.COLONNE)):
    #     #   header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

    #     # # Area allargabile
    #     # header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        


    #     # header.setMinimumSectionSize(self.scale(30))
    #     # col_widths = [
    #     #  self.scale(145),  # Ora      "25/06/2026 23:51:05"
    #     #  self.scale(80),   # Area     (Stretch)
    #     #  self.scale(48),   # Mag      "M-0.1"
    #     #  self.scale(62),   # Prof     "0.90"
    #     #  self.scale(68),   # Lat      "40.8240"
    #     #  self.scale(68),   # Lon      "14.1412"
    #     #  self.scale(28),   # Q        "B"
    #     # ]
    #     # for i, w in enumerate(col_widths):
    #     #  header.setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)
    #     #  header.resizeSection(i, w)

    #     # col_widths = [
    #     # self.scale(145),  # Ora  ← era 75, ora serve più spazio per "26/06/2026 13:02:49"
    #     # self.scale(100),  # Area
    #     # self.scale(55),   # Mag
    #     # self.scale(70),   # Prof
    #     # self.scale(70),   # Lat
    #     # self.scale(70),   # Lon
    #     # self.scale(35),   # Q
    #     # ]
    #     # for i, w in enumerate(col_widths):
    #     #     header.resizeSection(i, w)

    #     # L'ultima colonna si espande per riempire lo spazio
    #     # header.setStretchLastSection(False)
    #     # header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)


    #     font_size = self.scale(13)
    #     table.setStyleSheet(f"""
    #         QTableWidget {{
    #             background-color: #1e1e1e;
    #             alternate-background-color: #252525;
    #             color: {color_testo};
    #             font-family: monospace;
    #             font-size: {font_size}px;
    #             border: none;
    #             gridline-color: #2a2a2a;
    #         }}
    #         QHeaderView::section {{
    #             background-color: #213B64;
    #             color: #a0c4e8;
    #             font-size: {font_size}px;
    #             font-weight: bold;
    #             border: none;
    #             padding: {self.scale(4)}px;
    #         }}
    #         QTableWidget::item {{
    #         padding-left: {self.scale(6)}px;
    #         padding-right: {self.scale(6)}px;
    #     }}
    #         QTableWidget::item:selected {{
    #             background-color: #2A4A7D;
    #         }}
    #     """)

    #     return table

    # def _make_table(self, color_testo):
    #  table = QTableWidget()
    #  table.setColumnCount(len(self.COLONNE))
    #  table.setHorizontalHeaderLabels(self.COLONNE)
    #  table.setRowCount(0)
    #  table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    #  table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    #  table.verticalHeader().setVisible(False)
    #  table.setShowGrid(False)
    #  table.setAlternatingRowColors(True)
    
    #  # IMPOSTA LA LARGHEZZA DELLE COLONNE MANUALMENTE
    # #  header = table.horizontalHeader()
    
    # #  # Larghezze specifiche per ogni colonna (in pixel scalati)
    # #  col_widths = [
    # #     self.scale(160),  # Data/Ora - aumentata per evitare ...
    # #     self.scale(100),  # Area
    # #     self.scale(55),   # Mag
    # #     self.scale(70),   # Prof
    # #     self.scale(75),   # Lat
    # #     self.scale(75),   # Lon
    # #     self.scale(35),   # Q
    # # ]
    
    # #  for i, width in enumerate(col_widths):
    # #     header.setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)
    # #     header.resizeSection(i, width)

    #  header = table.horizontalHeader()
    
    #  # Colonna Data/Ora (indice 0) - si espande per contenere il testo
    #  header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
    
    #  # Altre colonne con larghezza fissa
    #  other_widths = [100, 55, 70, 75, 75, 35]  # Area, Mag, Prof, Lat, Lon, Q
    #  for i, width in enumerate(other_widths, start=1):
    #     header.setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)
    #     header.resizeSection(i, self.scale(width))

    
    
    #  # Opzionale: Permetti all'utente di ridimensionare le colonne
    #  header.setSectionsMovable(True)
    
    #  # STILE per evitare l'ellipsis e gestire il testo
    #  font_size = self.scale(13)
    #  table.setStyleSheet(f"""
    #     QTableWidget {{
    #         background-color: #1e1e1e;
    #         alternate-background-color: #252525;
    #         color: {color_testo};
    #         font-family: monospace;
    #         font-size: {font_size}px;
    #         border: none;
    #         gridline-color: #2a2a2a;
    #     }}
    #     QTableWidget::item {{
    #         padding-left: {self.scale(6)}px;
    #         padding-right: {self.scale(6)}px;
    #         /* Impedisce il taglio del testo */
    #         text-overflow: clip;
    #         overflow: visible;
    #     }}
    #     QHeaderView::section {{
    #         background-color: #213B64;
    #         color: #a0c4e8;
    #         font-size: {font_size}px;
    #         font-weight: bold;
    #         border: none;
    #         padding: {self.scale(4)}px;
    #     }}
    #     QTableWidget::item:selected {{
    #         background-color: #2A4A7D;
    #     }}
    #  """)
    
    #  return table

    def _make_table(self, color_testo):
     table = QTableWidget()
     table.setColumnCount(len(self.COLONNE))
     table.setHorizontalHeaderLabels(self.COLONNE)
     table.setRowCount(0)
     table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
     table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
     table.verticalHeader().setVisible(False)
     table.setShowGrid(False)
     table.setAlternatingRowColors(True)

     header = table.horizontalHeader()
    
     # Data/Ora si adatta al contenuto
     header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
     header.setMinimumSectionSize(self.scale(140))
    
     # Area si espande
     header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
    
     # Altre colonne fisse
     for i in range(2, len(self.COLONNE)):
        header.setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)
        # Larghezze per le altre colonne
        fixed_widths = [55, 70, 75, 75, 35]  # Mag, Prof, Lat, Lon, Q
        header.resizeSection(i, self.scale(fixed_widths[i-2]))

     # Stile
     font_size = self.scale(13)
     table.setStyleSheet(f"""
        QTableWidget {{
            background-color: #1e1e1e;
            alternate-background-color: #252525;
            color: {color_testo};
            font-family: monospace;
            font-size: {font_size}px;
            border: none;
            gridline-color: #2a2a2a;
        }}
        QTableWidget::item {{
            padding-left: {self.scale(6)}px;
            padding-right: {self.scale(6)}px;
        }}
        QHeaderView::section {{
            background-color: #213B64;
            color: #a0c4e8;
            font-size: {font_size}px;
            font-weight: bold;
            border: none;
            padding: {self.scale(4)}px;
        }}
        QTableWidget::item:selected {{
            background-color: #2A4A7D;
        }}
     """)

     return table



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
            min-width: {self.scale(80)}px;
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

        zone_tabs = [
            ("GENERALE",     "#ffffff"),
            ("CAMPI FLEGREI","#3DDC84"),
            ("VESUVIO",      "#3DDC84"),
            ("ISCHIA",       "#3DDC84"),
        ]

        for nome_tab, color_testo in zone_tabs:
            table = self._make_table(color_testo)
            self.tab_logs[nome_tab] = table
            self.tabs.addTab(table, nome_tab)

        self.tabs.currentChanged.connect(self._on_tab_changed)
        parent_layout.addWidget(self.tabs, 1)

    def _on_tab_changed(self, index):
        tab_name = self.tabs.tabText(index)
        self.on_tab_changed_callback(tab_name)

    def update_logs(self, zone, logs):
        """Riceve lista di dict e popola la tabella."""
        if zone not in self.tab_logs:
            return
        table = self.tab_logs[zone]
        table.setRowCount(0)
        for entry in logs:
            if isinstance(entry, dict):
                self._append_row(table, entry)
        table.scrollToBottom()

    def add_log(self, zone, entry):
        """Aggiunge una singola riga (dict)."""
        if zone not in self.tab_logs:
            return
        if isinstance(entry, dict):
            self._append_row(self.tab_logs[zone], entry)
            self.tab_logs[zone].scrollToBottom()

    def _append_row(self, table, entry):
        row = table.rowCount()
        table.insertRow(row)

        mag   = entry.get("magnitudine")
        mag_str = f"M{mag:.1f}" if mag is not None else "n.d."

        dep   = entry.get("profondita_km")
        dep_str = f"{dep:.2f}" if dep is not None else "n.d."

        lat   = entry.get("latitudine")
        lon   = entry.get("longitudine")
        lat_str = f"{lat:.4f}" if lat is not None else "n.d."
        lon_str = f"{lon:.4f}" if lon is not None else "n.d."

        # time_str = entry.get("data", "")
        # ora_str  = time_str[11:19] if len(time_str) >= 19 else time_str

        time_str = entry.get("data", "")
        if len(time_str) >= 19:
         # "2026-06-26T13:02:49" → "26/06/2026 13:02:49"
         data_part = time_str[:10]   # "2026-06-26"
         ora_part  = time_str[11:19] # "13:02:49"
         anno, mese, giorno = data_part.split("-")
         ora_str = f"{giorno}/{mese}/{anno} {ora_part}"
        else:
         ora_str = time_str

        valori = [
            ora_str,
            entry.get("area_desc", ""),
            mag_str,
            dep_str,
            lat_str,
            lon_str,
            entry.get("qualita", ""),
        ]

        # Colore riga per magnitudo
        if mag is not None:
            if mag >= 3.5:
                row_color = QColor("#3d1a1a")   # rosso scuro
            elif mag >= 2.0:
                row_color = QColor("#3d2e0a")   # arancione scuro
            elif mag >= 1.0:
                row_color = QColor("#3d3a0a")   # giallo scuro
            else:
                row_color = None
        else:
            row_color = None

        for col, val in enumerate(valori):
            item = QTableWidgetItem(str(val))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if row_color:
                item.setBackground(row_color)
            table.setItem(row, col, item)