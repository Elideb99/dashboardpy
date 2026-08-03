from PyQt6.QtWidgets import QTabWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QHeaderView, QSizePolicy, QLabel, QHBoxLayout, QFrame
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from datetime import datetime, timedelta
from utils.helpers import raggruppa_per_evento, chiave_data,parse_event_datetime


class TabsView:
    """VIEW: Gestisce i tab dei log"""

    COLONNE = ["", "DATA/ORA", "AREA", "MAG", "PROF (km)", "LAT", "LON", "Q"]

    # ── Aspetto delle card in allerta ────────────────────────
    STATI_SCIAME_VISIBILI = ("SCIAME IN CORSO", "SCIAME INIZIATO", "SCIAME TERMINATO")

    # stato -> (colore bordo/badge, colore sfondo card)
    COLORI_SCIAME = {
        "SCIAME IN CORSO":  ("#D32F2F", "#24141A"),   # rosso pieno / viola-rosso scuro
        "SCIAME INIZIATO":  ("#E65100", "#241A14"),   # arancione scuro / arancio bruno
        "SCIAME TERMINATO": ("#2E7D32", "#132219"),   # verde scuro / verde foresta scuro
    }

    COLORE_ALLARME = "#FF1744"   # rosso più acceso di SCIAME IN CORSO, per distinguerli
    SFONDO_ALLARME = "#2E1216"

    # ── Aspetto della revisione più recente dentro la tendina ─
    COLORE_ULTIMA_REVISIONE = "#f9d71c"   # colore della ★
    SFONDO_ULTIMA_REVISIONE = "#1B2942"   # tinta di riga; metti None per toglierla

    def __init__(self, parent, ui_scale, on_tab_changed_callback):
        self.parent = parent
        self.ui_scale = ui_scale
        self.on_tab_changed_callback = on_tab_changed_callback
        self.tabs = None
        self.tab_logs = {}   # contiene QTableWidget invece di QTextEdit
        self.zone_cards = {}
        self._expanded_groups = {}  # zona -> set di gruppo_chiave (event_id) espansi nella tabella
        self._last_logs = {}        # zona -> ultima lista logs ricevuta (serve per ridisegnare dopo un espandi/comprimi)
        self.zone_labels = {}       # zona -> dict di riferimenti ai widget della card (mag, date, ecc.)

        self._swarm_states = {}     # zona -> (state, color, tooltip)
        self._zone_alarms = {}      # zona -> magnitudine della scossa forte
        self._swarm_peaks = {}      # zona -> {"magnitudo":..., "data": datetime} picco sciame corrente

    def scale(self, v):
        return max(1, int(v * self.ui_scale))

    def fs(self, px):
        return f"{self.scale(px)}px"

    @staticmethod
    def _pulisci_nome_tab(testo):
        """Toglie i marker di allerta dal testo del tab per risalire al nome della zona.
        Oggi il testo del tab non viene più decorato, resta come rete di sicurezza."""
        return testo.replace("⚠️ ", "").replace("🚨 ", "")

    def _make_table(self, color_testo):
        # crea e stila una singola tabella dei log (una per tab: GENERALE + 3 zone)
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

        # Colonna pallino: larghezza fissa piccola
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(0, self.scale(14))

        # Data/Ora si adatta al contenuto
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setMinimumSectionSize(self.scale(140))

        # Area si espande
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

        # Altre colonne fisse (Mag, Prof, Lat, Lon, Q)
        for i in range(3, len(self.COLONNE)):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)
            fixed_widths = [55, 70, 75, 75, 35]
            header.resizeSection(i, self.scale(fixed_widths[i-3]))

        # Stile tabella dei log
        font_size = self.scale(15)  # font tabella log
        font_size_header = self.scale(13)
        table.setStyleSheet(f"""
            QTableWidget {{
                background-color: #131D2E;
                alternate-background-color: #0F1521;
                color: {color_testo};
                font-family: monospace;
                font-size: {font_size}px;
                border: none;
                gridline-color: #1E2738;
            }}
            QTableWidget::item {{
                padding-left: {self.scale(3)}px;
                padding-right: {self.scale(3)}px;
            }}
            QHeaderView::section {{
                background-color: #1C2B40;
                color: #a0c4e8;
                font-size: {font_size_header}px;
                font-weight: bold;
                border: none;
                padding: {self.scale(4)}px;
            }}
            QTableWidget::item:selected {{
                background-color: #2A4A7D;
            }}
        """)

        table.cellClicked.connect(lambda row, col, t=table: self._on_cell_clicked(t, row, col))
        return table

    def create(self, parent_layout):
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.tabBar().setExpanding(True)

        # Stile tabs
        tab_font_size = self.fs(16)
        tab_min_height = self.scale(35)
        tab_padding_h = self.scale(15)
        tab_padding_top = self.scale(4)

        self.tabs.setStyleSheet(f"""
            QTabWidget {{
                border: none;
            }}
            QTabWidget::pane {{
                border: none;
                padding-top: {self.scale(3)}px;
                background-color: #0A0E16;
            }}
            QTabWidget::tab-bar {{
                alignment: left;
            }}
        """)

        # stile bottoni tab
        self.tabs.tabBar().setStyleSheet(f"""
            QTabBar {{
                background-color: #0A0E16;
            }}
            QTabBar::tab {{
                background-color: #1C2B40;
                color: white;
                font-weight: bold;
                font-size: {tab_font_size};
                min-height: {tab_min_height}px;
                min-width: {self.scale(80)}px;
                padding-left: {tab_padding_h}px;
                padding-right: {tab_padding_h}px;
                padding-top: {tab_padding_top}px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: {self.scale(2)}px;
            }}
            QTabBar::tab:hover {{
                background-color: #2A4A7D;
            }}
            QTabBar::tab:selected {{
                font-size: {tab_font_size};
                font-weight: bold;
                padding-left: {tab_padding_h}px;
                padding-right: {tab_padding_h}px;
                padding-top: {tab_padding_top}px;
                border-radius: 6px;
                color: white;
                background-color: #2A4A7D;
                border: {self.scale(2)}px solid #4A90E2;
            }}
        """)

        zone_tabs = [
            ("GENERALE",      "#ffffff"),
            ("CAMPI FLEGREI", "#a0c4e8"),
            ("VESUVIO",       "#a0c4e8"),
            ("ISCHIA",        "#a0c4e8"),
        ]

        for nome_tab, color_testo in zone_tabs:
            table = self._make_table(color_testo)
            self.tab_logs[nome_tab] = table
            self.tabs.addTab(table, nome_tab)

        self.tabs.currentChanged.connect(self._on_tab_changed)
        parent_layout.addWidget(self.tabs, 1)

        section_title = QLabel("ULTIMA SCOSSA PER AREA")
        section_title.setStyleSheet(f"""
            color: #ffffff;
            font-size: {self.scale(13)}px;
            font-weight: bold;
            letter-spacing: 1px;
            background: transparent;
            border: none;
            padding-top: {self.scale(8)}px;
            padding-bottom: {self.scale(2)}px;
        """)
        parent_layout.addWidget(section_title)

        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(self.scale(12))

        zone_title_colors = {
            "CAMPI FLEGREI": "#c084fc",
            "VESUVIO":       "#c084fc",
            "ISCHIA":        "#c084fc",
        }

        # costruisce le 3 card di zona (Campi Flegrei, Vesuvio, Ischia) sotto le tabelle
        for zona in ["CAMPI FLEGREI", "VESUVIO", "ISCHIA"]:
            accent = zone_title_colors[zona]

            card = QFrame()
            card.setObjectName("zoneCard")
            card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            card.setMinimumHeight(self.scale(245))

            card.setStyleSheet(f"""
                QFrame#zoneCard {{
                    background-color: #131D2E;
                    border: {self.scale(1)}px solid #27364D;
                    border-top: {self.scale(3)}px solid {accent};
                    border-radius: {self.scale(12)}px;
                }}
            """)

            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(self.scale(20), self.scale(18), self.scale(20), self.scale(18))
            card_layout.setSpacing(self.scale(7))

            # INTESTAZIONE
            header_layout = QHBoxLayout()
            header_layout.setContentsMargins(0, 0, 0, 0)
            header_layout.setSpacing(self.scale(6))

            title = QLabel(f"●  {zona}")
            title.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            title.setStyleSheet(f"""
                color: {accent};
                font-size: {self.scale(15)}px;
                font-weight: bold;
                letter-spacing: 1px;
                background: transparent;
                border: none;
            """)

            # badge scossa forte (mostrato/nascosto in _render_card in base a _zone_alarms)
            alarm_badge = QLabel("")
            alarm_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            alarm_badge.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            alarm_badge.setStyleSheet("QLabel { background-color: transparent; border: none; }")
            alarm_badge.setVisible(False)

            # badge sciame (mostrato/nascosto in _render_card in base a _swarm_states)
            status_badge = QLabel("")
            status_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            status_badge.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            status_badge.setStyleSheet("QLabel { background-color: transparent; border: none; }")
            status_badge.setVisible(False)

            header_layout.addWidget(title)
            header_layout.addStretch()
            header_layout.addWidget(alarm_badge)
            header_layout.addWidget(status_badge)

            # MAGNITUDO CENTRALE
            mag_label = QLabel("M --")
            mag_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            mag_label.setStyleSheet(f"""
                color: #9ca3af;
                font-size: {self.scale(48)}px;
                font-weight: 800;
                background: transparent;
                border: none;
                padding-top: {self.scale(7)}px;
            """)

            subtitle_label = QLabel("Ultima scossa")
            subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            subtitle_label.setStyleSheet(f"""
                color: #8190A6;
                font-size: {self.scale(12)}px;
                font-weight: bold;
                background: transparent;
                border: none;
            """)

            # DATA E PROFONDITÀ
            info_layout = QHBoxLayout()
            info_layout.setContentsMargins(self.scale(4), self.scale(8), self.scale(4), self.scale(5))
            info_layout.setSpacing(self.scale(8))

            date_label = QLabel("Nessun evento")
            date_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            date_label.setStyleSheet(f"""
                color: #C5D1E0;
                font-size: {self.scale(13)}px;
                background: transparent;
                border: none;
            """)

            depth_label = QLabel(" -- km")
            depth_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            depth_label.setStyleSheet(f"""
                color: #C5D1E0;
                font-size: {self.scale(13)}px;
                background: transparent;
                border: none;
            """)

            info_layout.addWidget(date_label, 1)
            info_layout.addWidget(depth_label, 1)

            # LINEA DIVISORIA
            divider = QFrame()
            divider.setObjectName("cardDivider")
            divider.setFrameShape(QFrame.Shape.HLine)
            divider.setFixedHeight(self.scale(1))
            divider.setStyleSheet("""
                QFrame#cardDivider {
                    background-color: #2B3A50;
                    border: none;
                }
            """)

            # PICCO DEL PERIODO (sciame se recente, altrimenti massimo dell'ultimo mese — vedi update_zone_cards)
            peak_layout = QHBoxLayout()
            peak_layout.setContentsMargins(self.scale(2), self.scale(4), self.scale(2), 0)

            peak_title = QLabel("Picco ultimo mese:")
            peak_title.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            peak_title.setStyleSheet(f"""
                color: #8190A6;
                font-size: {self.scale(12)}px;
                font-weight: bold;
                background: transparent;
                border: none;
            """)

            peak_value = QLabel("M --")
            peak_value.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            peak_value.setStyleSheet(f"""
                color: #C5D1E0;
                font-size: {self.scale(15)}px;
                font-weight: bold;
                background: transparent;
                border: none;
            """)

            peak_layout.addWidget(peak_title)
            peak_layout.addStretch()
            peak_layout.addWidget(peak_value)

            card_layout.addLayout(header_layout)
            card_layout.addStretch()
            card_layout.addWidget(mag_label)
            card_layout.addWidget(subtitle_label)
            card_layout.addStretch()
            card_layout.addLayout(info_layout)
            card_layout.addWidget(divider)
            card_layout.addLayout(peak_layout)

            self.zone_cards[zona] = card

            # tiene i riferimenti a tutti i widget della card, per poterli aggiornare senza ricrearli
            self.zone_labels[zona] = {
                "card": card,
                "accent": accent,
                "mag": mag_label,
                "date": date_label,
                "depth": depth_label,
                "status": status_badge,
                "alarm": alarm_badge,
                "peak_title": peak_title,
                "peak_value": peak_value,
                "divider": divider,
            }

            cards_layout.addWidget(card, 1)

        parent_layout.addLayout(cards_layout)

    def _on_tab_changed(self, index):
        tab_name = self._pulisci_nome_tab(self.tabs.tabText(index))
        self.on_tab_changed_callback(tab_name)

    def update_logs(self, zone, logs):
        """Ridisegna la tabella di una zona, raggruppando le revisioni dello stesso evento
        in una riga espandibile (▶/▼), con le revisioni secondarie mostrate solo se espanse."""
        if zone not in self.tab_logs:
            return

        self._last_logs[zone] = logs
        self._expanded_groups.setdefault(zone, set())

        table = self.tab_logs[zone]
        table.setRowCount(0)

        gruppi = raggruppa_per_evento(logs)

        for gruppo in gruppi:
            n_revisioni = len(gruppo["revisioni"])
            espanso = gruppo["chiave"] in self._expanded_groups[zone]

            self._append_row(
                table, gruppo["rappresentante"],
                n_revisioni=n_revisioni, espandibile=(n_revisioni > 1), espanso=espanso,
                gruppo_chiave=gruppo["chiave"],
                data_ultimo_aggiornamento=gruppo["data_ultimo_aggiornamento"]
            )

            if n_revisioni > 1 and espanso:
                # NB: niente slice [1:] qui. Basta escludere il rappresentante,
                # altrimenti quando il rappresentante non è revisioni[0] si perde
                # una riga per strada, ed è sempre la più recente.
                ultima = self._ultima_revisione(gruppo["revisioni"])
                for revisione in gruppo["revisioni"]:
                    if revisione is not gruppo["rappresentante"]:
                        self._append_row(
                            table, revisione, sotto_riga=True,
                            ultima_revisione=(revisione is ultima)
                        )

        table.scrollToTop()

    @staticmethod
    def _ultima_revisione(revisioni):
        # revisione con la data più recente nel gruppo, usata per marcare la ★ tra le sotto-righe
        valide = [r for r in revisioni if isinstance(r, dict) and r.get("data")]
        if not valide:
            return None
        return max(valide, key=chiave_data)

    def _append_row(self, table, entry, n_revisioni=1, espandibile=False,
                    espanso=False, gruppo_chiave=None, sotto_riga=False,
                    data_ultimo_aggiornamento=None, ultima_revisione=False):
        # aggiunge una riga alla tabella: può essere una riga "principale" (rappresentante di un
        # gruppo, eventualmente espandibile) o una "sotto-riga" (una revisione del gruppo espanso)
        row = table.rowCount()
        table.insertRow(row)

        mag = entry.get("magnitudine")
        mag_str = f"Md{mag:.2f}" if mag is not None else "n.d."

        dep = entry.get("profondita_km")
        dep_str = f"{dep:.2f}" if dep is not None else "n.d."

        lat = entry.get("latitudine")
        lon = entry.get("longitudine")
        lat_str = f"{lat:.4f}" if lat is not None else "n.d."
        lon_str = f"{lon:.4f}" if lon is not None else "n.d."

        time_str = entry.get("data", "")
        if len(time_str) >= 19:
            data_part = time_str[:10]
            ora_part = time_str[11:19]
            anno, mese, giorno = data_part.split("-")
            ora_str = f"{giorno}/{mese}/{anno} {ora_part}"   # da ISO (YYYY-MM-DD) a formato italiano
        else:
            ora_str = time_str

        colore_mag = self._colore_magnitudo(mag)

        # colonna 0 (pallino/simbolo): significato diverso a seconda del tipo di riga
        if espandibile:
            simbolo = "▼" if espanso else "▶"
            dot_item = QTableWidgetItem(simbolo)
            dot_item.setForeground(QColor("#a0c4e8"))
            dot_item.setData(Qt.ItemDataRole.UserRole, gruppo_chiave)   # usato da _on_cell_clicked per sapere quale gruppo aprire/chiudere
        elif sotto_riga:
            # ★ = revisione più recente del gruppo, quella che "vale"
            dot_item = QTableWidgetItem("★" if ultima_revisione else "↳")
            dot_item.setForeground(
                QColor(self.COLORE_ULTIMA_REVISIONE) if ultima_revisione else QColor("#5a6b85")
            )
        else:
            dot_item = QTableWidgetItem("●")
            dot_item.setForeground(QColor(colore_mag))

        dot_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        if ultima_revisione and self.SFONDO_ULTIMA_REVISIONE:
            dot_item.setBackground(QColor(self.SFONDO_ULTIMA_REVISIONE))
        table.setItem(row, 0, dot_item)

        # se la riga principale ha più revisioni, aggiunge "(N agg.)" o l'orario dell'ultimo aggiornamento
        ora_display = ora_str
        if espandibile and not sotto_riga:
            entry_data = entry.get("data", "")
            if data_ultimo_aggiornamento and data_ultimo_aggiornamento != entry_data:
                ora_ultimo = data_ultimo_aggiornamento[11:19] if len(data_ultimo_aggiornamento) >= 19 else data_ultimo_aggiornamento
                ora_display = f"{ora_str}  ★({n_revisioni} agg., ultimo: {ora_ultimo})"
            else:
                ora_display = f"{ora_str}  ({n_revisioni} agg.)"

        valori = [
            ora_display,
            entry.get("area_desc", ""),
            mag_str,
            dep_str,
            lat_str,
            lon_str,
            entry.get("qualita", ""),
        ]

        for col, val in enumerate(valori, start=1):
            item = QTableWidgetItem(str(val))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            if col == 3:   # colonna MAG: sempre colorata/bold in base alla magnitudo
                item.setForeground(QColor(colore_mag))
                font = item.font()
                font.setBold(True)
                item.setFont(font)

            if sotto_riga:
                font = item.font()
                # la revisione più recente non va in corsivo: non è una riga "minore"
                font.setItalic(not ultima_revisione)
                if ultima_revisione:
                    font.setBold(True)
                item.setFont(font)

                if col != 3:
                    item.setForeground(
                        QColor("#C5D1E0") if ultima_revisione else QColor("#7E8CA3")
                    )

                if ultima_revisione and self.SFONDO_ULTIMA_REVISIONE:
                    item.setBackground(QColor(self.SFONDO_ULTIMA_REVISIONE))

            table.setItem(row, col, item)

    def _on_cell_clicked(self, table, row, col):
        # click solo sulla colonna 0 (pallino/simbolo ▶/▼) espande/comprime il gruppo cliccato
        if col != 0:
            return
        item = table.item(row, 0)
        if item is None:
            return

        gruppo_chiave = item.data(Qt.ItemDataRole.UserRole)
        if gruppo_chiave is None:
            return   # riga non espandibile (● singolo o sotto-riga): nessuna azione

        zona = next((z for z, t in self.tab_logs.items() if t is table), None)
        if zona is None:
            return

        espansi = self._expanded_groups.setdefault(zona, set())
        if gruppo_chiave in espansi:
            espansi.discard(gruppo_chiave)
        else:
            espansi.add(gruppo_chiave)

        logs = self._last_logs.get(zona, [])
        self.update_logs(zona, logs)   # ridisegna con il nuovo stato espanso/compresso


    def update_zone_cards(self, all_logs, source=None):

        zone = ["CAMPI FLEGREI", "VESUVIO", "ISCHIA"]

        # ─────────────────────────────────────────────────────
        # RIFERIMENTO TEMPORALE GLOBALE
        # ─────────────────────────────────────────────────────
        # calcola "adesso" come la data più recente vista nei dati (non datetime.now()), così
        # il calcolo "ultimo mese" funziona correttamente anche durante un replay di dati vecchi
        date_globali = []

        for evento in all_logs.get("GENERALE", []):
            if not isinstance(evento, dict):
                continue

            data_evento = parse_event_datetime(evento.get("data"))

            if data_evento is not None:
                date_globali.append(data_evento)

        # Considera anche le date degli sciami salvati.
        for dati_sciame in self._swarm_peaks.values():
            if not isinstance(dati_sciame, dict):
                continue

            data_sciame = dati_sciame.get("data")

            if not isinstance(data_sciame, datetime):
                data_sciame = parse_event_datetime(data_sciame)

            if data_sciame is not None:
                date_globali.append(data_sciame)

        # Nel replay il periodo viene calcolato rispetto all'ultimo dato registrato.
        # Nella modalità normale viene calcolato rispetto alla data reale.
        if source == "replay":
          riferimento = max(date_globali) if date_globali else datetime.now()
        else:
          riferimento = datetime.now()

        limite_ultimo_mese = riferimento - timedelta(days=30)

        # ─────────────────────────────────────────────────────
        # AGGIORNAMENTO DELLE TRE CARD
        # ─────────────────────────────────────────────────────
        for zona in zone:
            labels = self.zone_labels[zona]
            logs = all_logs.get(zona, [])

            eventi_validi = [
                evento
                for evento in logs
                if isinstance(evento, dict) and evento.get("data")
            ]

            gruppi = (
                raggruppa_per_evento(eventi_validi)
                if eventi_validi
                else []
            )

            # ─────────────────────────────────────────────────
            # ULTIMA SCOSSA DELLA ZONA
            # ─────────────────────────────────────────────────
            ultimo = None

            if gruppi:
                gruppi_ordinati = sorted(
                    gruppi,
                    key=lambda gruppo: (
                        parse_event_datetime(
                            gruppo.get("data_ultimo_aggiornamento")
                        )
                        or datetime.min
                    ),
                    reverse=True
                )

                # Cerca prima l'evento più recente con magnitudo disponibile.
                ultimo = next(
                    (
                        gruppo["rappresentante"]
                        for gruppo in gruppi_ordinati
                        if gruppo.get("rappresentante", {}).get("magnitudine")
                        is not None
                    ),
                    None
                )

                # Se nessun evento possiede la magnitudo, mostra comunque
                # il rappresentante dell'evento più recente.
                if ultimo is None and gruppi_ordinati:
                    ultimo = gruppi_ordinati[0].get("rappresentante")

            if ultimo is None:
                labels["mag"].setText("M --")
                labels["mag"].setStyleSheet(f"""
                    color: #9ca3af;
                    font-size: {self.scale(48)}px;
                    font-weight: 800;
                    background: transparent;
                    border: none;
                    padding-top: {self.scale(7)}px;
                """)

                labels["date"].setText("Nessun evento")
                labels["depth"].setText(" -- km")

            else:
                try:
                    magnitudo_ultima = float(
                        ultimo.get("magnitudine")
                    )
                except (TypeError, ValueError):
                    magnitudo_ultima = None

                if magnitudo_ultima is not None:
                    labels["mag"].setText(
                        f"M {magnitudo_ultima:.2f}"
                    )

                    labels["mag"].setStyleSheet(f"""
                        color: {self._colore_magnitudo(magnitudo_ultima)};
                        font-size: {self.scale(48)}px;
                        font-weight: 800;
                        background: transparent;
                        border: none;
                        padding-top: {self.scale(7)}px;
                    """)
                else:
                    labels["mag"].setText("M --")
                    labels["mag"].setStyleSheet(f"""
                        color: #9ca3af;
                        font-size: {self.scale(48)}px;
                        font-weight: 800;
                        background: transparent;
                        border: none;
                        padding-top: {self.scale(7)}px;
                    """)

                data_raw = str(ultimo.get("data", ""))

                mesi = {
                    "01": "Gen",
                    "02": "Feb",
                    "03": "Mar",
                    "04": "Apr",
                    "05": "Mag",
                    "06": "Giu",
                    "07": "Lug",
                    "08": "Ago",
                    "09": "Set",
                    "10": "Ott",
                    "11": "Nov",
                    "12": "Dic",
                }

                if len(data_raw) >= 16:
                    data_formattata = (
                        f"{data_raw[8:10]} "
                        f"{mesi.get(data_raw[5:7], data_raw[5:7])} "
                        f"{data_raw[11:16]}"
                    )
                else:
                    data_formattata = data_raw or "Nessun evento"

                labels["date"].setText(f" {data_formattata}")

                profondita = ultimo.get("profondita_km")

                try:
                    profondita = float(profondita)
                except (TypeError, ValueError):
                    profondita = None

                if profondita is not None:
                    labels["depth"].setText(
                        f" {profondita:.2f} km"
                    )
                else:
                    labels["depth"].setText(" -- km")

            # ─────────────────────────────────────────────────
            # PICCO SCIAME O PICCO ULTIMO MESE
            # ─────────────────────────────────────────────────
            # priorità al picco dello sciame se è "recente" (entro l'ultimo mese rispetto al
            # riferimento); altrimenti si ripiega sul massimo degli eventi ordinari dell'ultimo mese
            magnitudo_picco = None
            sciame_recente = False

            dati_sciame = self._swarm_peaks.get(zona)

            if isinstance(dati_sciame, dict):
                try:
                    magnitudo_sciame = float(
                        dati_sciame.get("magnitudo")
                    )
                except (TypeError, ValueError):
                    magnitudo_sciame = None

                data_sciame = dati_sciame.get("data")

                if not isinstance(data_sciame, datetime):
                    data_sciame = parse_event_datetime(data_sciame)

                if (
                    magnitudo_sciame is not None
                    and data_sciame is not None
                    and limite_ultimo_mese <= data_sciame <= riferimento
                ):
                    sciame_recente = True
                    magnitudo_picco = magnitudo_sciame

            if sciame_recente:
                labels["peak_title"].setText("Picco sciame:")

            else:
                labels["peak_title"].setText("Picco ultimo mese:")

                magnitudo_eventi_ultimo_mese = []

                for gruppo in gruppi:
                    rappresentante = gruppo.get(
                        "rappresentante",
                        {}
                    )

                    if not isinstance(rappresentante, dict):
                        continue

                    data_evento = parse_event_datetime(
                        rappresentante.get("data")
                    )

                    if data_evento is None:
                        continue

                    if not (
                        limite_ultimo_mese
                        <= data_evento
                        <= riferimento
                    ):
                        continue

                    try:
                        magnitudo_evento = float(
                            rappresentante.get("magnitudine")
                        )
                    except (TypeError, ValueError):
                        continue

                    magnitudo_eventi_ultimo_mese.append(
                        magnitudo_evento
                    )

                if magnitudo_eventi_ultimo_mese:
                    magnitudo_picco = max(
                        magnitudo_eventi_ultimo_mese
                    )

            # ─────────────────────────────────────────────────
            # VISUALIZZAZIONE DEL PICCO
            # ─────────────────────────────────────────────────
            if magnitudo_picco is not None:
                labels["peak_value"].setText(
                    f"M {magnitudo_picco:.2f}"
                )

                labels["peak_value"].setStyleSheet(f"""
                    color: {self._colore_magnitudo(magnitudo_picco)};
                    font-size: {self.scale(15)}px;
                    font-weight: bold;
                    background: transparent;
                    border: none;
                """)

            else:
                labels["peak_value"].setText("M --")

                labels["peak_value"].setStyleSheet(f"""
                    color: #8190A6;
                    font-size: {self.scale(15)}px;
                    font-weight: bold;
                    background: transparent;
                    border: none;
                """)

    def update_zone_swarm_peak(self, zona, magnitudo, data_sciame=None):
     # memorizza il picco di magnitudo dello sciame corrente per la zona, conservando
     # il valore più alto quando arrivano più comunicati sullo stesso periodo
     if zona not in self.zone_labels:
        return

     try:
        magnitudo = float(magnitudo)
     except (TypeError, ValueError):
        return

     data_dt = parse_event_datetime(data_sciame)

     if data_dt is None:
        return

     precedente = self._swarm_peaks.get(zona)

     if precedente is None:
        self._swarm_peaks[zona] = {
            "magnitudo": magnitudo,
            "data": data_dt
        }
        return

    # Se il nuovo comunicato è più recente, aggiorna il periodo.
     if data_dt > precedente["data"]:
        self._swarm_peaks[zona] = {
            "magnitudo": magnitudo,
            "data": data_dt
        }

    # Se appartiene allo stesso sciame/periodo, conserva il picco maggiore.
     elif data_dt == precedente["data"] and magnitudo > precedente["magnitudo"]:
        precedente["magnitudo"] = magnitudo

    def update_zone_swarm_state(self, zona, state, color, tooltip):
        """Registra lo stato sciame della zona e ridisegna la card."""
        if zona not in self.zone_labels:
            return
        self._swarm_states[zona] = (state, color, tooltip)
        self._render_card(zona)

    def update_zone_alarm(self, zona, mag):
        # mag=None spegne l'allarme della card (vedi SystemController._spegni_allarme_card)
        if zona not in self.zone_labels:
            return
        if mag is None:
            self._zone_alarms.pop(zona, None)
        else:
            self._zone_alarms[zona] = mag
        self._render_card(zona)

    def _render_card(self, zona):
        # ridisegna badge e cornice della card in base allo stato corrente di allarme/sciame
        
        labels = self.zone_labels[zona]
        card = labels["card"]
        accent = labels["accent"]

        mag_allarme = self._zone_alarms.get(zona)
        stato_sciame, colore_sciame, tooltip_sciame = self._swarm_states.get(zona, (None, None, ""))
        sciame_attivo = stato_sciame in self.STATI_SCIAME_VISIBILI

        # ── badge scossa forte ──
        if mag_allarme is not None:
            labels["alarm"].setText(f"ALLARME MAGNITUDO: {mag_allarme:.1f}")
            labels["alarm"].setToolTip(f"Scossa forte rilevata — M{mag_allarme:.2f}")
            labels["alarm"].setStyleSheet(f"""
                QLabel {{
                    background-color: {self.COLORE_ALLARME};
                    color: #FFFFFF;
                    font-size: {self.scale(15)}px;
                    font-weight: bold;
                    border-radius: {self.scale(9)}px;
                    padding: {self.scale(3)}px {self.scale(9)}px;
                }}
            """)
            labels["alarm"].setVisible(True)
        else:
            labels["alarm"].setVisible(False)

        # ── badge sciame ──
        if sciame_attivo:
            colore_stato = colore_sciame or self.COLORI_SCIAME[stato_sciame][0]
            # sostituisce i vecchi colori chiari se passati dal controller
            if colore_sciame in ("#FF9800", "#3DDC84", "#2e7d32", "#c62828"):
                colore_stato = self.COLORI_SCIAME[stato_sciame][0]

            labels["status"].setText(stato_sciame)
            labels["status"].setToolTip(tooltip_sciame or "")
            labels["status"].setStyleSheet(f"""
                QLabel {{
                    background-color: {colore_stato};
                    color: #FFFFFF;
                    font-size: {self.scale(15)}px;
                    font-weight: bold;
                    border-radius: {self.scale(9)}px;
                    padding: {self.scale(3)}px {self.scale(9)}px;
                }}
            """)
            labels["status"].setVisible(True)
        else:
            labels["status"].setVisible(False)

        # ── cornice della card ── priorità: allarme > sciame attivo > normale
        if mag_allarme is not None:
            bordo, sfondo, spessore = self.COLORE_ALLARME, self.SFONDO_ALLARME, 3
        elif sciame_attivo:
            bordo, sfondo = self.COLORI_SCIAME[stato_sciame]
            spessore = 2
        else:
            bordo = sfondo = spessore = None

        if bordo is None:
            card.setStyleSheet(f"""
                QFrame#zoneCard {{
                    background-color: #131D2E;
                    border: {self.scale(1)}px solid #27364D;
                    border-top: {self.scale(3)}px solid {accent};
                    border-radius: {self.scale(12)}px;
                }}
            """)
        else:
            card.setStyleSheet(f"""
                QFrame#zoneCard {{
                    background-color: {sfondo};
                    border: {self.scale(spessore)}px solid {bordo};
                    border-radius: {self.scale(12)}px;
                }}
            """)

        self._render_tab(zona, mag_allarme, sciame_attivo, bordo)

    def _render_tab(self, zona, mag_allarme, sciame_attivo, colore):
        """Propaga l'allerta sul tab: cambia solo il colore del testo,
        il nome del tab resta sempre quello della zona."""
        tab_index = -1
        for i in range(self.tabs.count()):
            if self._pulisci_nome_tab(self.tabs.tabText(i)) == zona:
                tab_index = i
                break
        if tab_index == -1:
            return

        if mag_allarme is not None or sciame_attivo:
            self.tabs.tabBar().setTabTextColor(tab_index, QColor(colore))
        else:
            self.tabs.tabBar().setTabTextColor(tab_index, QColor("#a0c4e8"))



    @staticmethod
    def _colore_magnitudo(mag):
        # soglie coerenti con la legenda della mappa (map.html) e con magnitudo2colore() in JS
        if mag is None:
            return "#6b7280"
        if mag < 1.0:
            return "#3DDC84"
        elif mag < 2.0:
            return "#f9d71c"
        elif mag < 3.0:
            return "#ff9800"
        else:
            return "#e53935"