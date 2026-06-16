import os
from datetime import datetime
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QSizePolicy
from PyQt6.QtGui import QPixmap

class HeaderView:
    """VIEW: Gestisce l'header con logo, titoli, data/ora (con icone) e stato"""
    
    def __init__(self, parent, ui_scale):
        self.parent = parent
        self.ui_scale = ui_scale
        self.logo_label = None
        self.title1 = None
        self.title2 = None
        self.data_label = None
        self.ora_label = None
        self.state_label = None
    
    def scale(self, v):
        return max(1, int(v * self.ui_scale))
    
    def fs(self, px):
        return f"{self.scale(px)}px"
    
    def create(self, main_layout):
        header_frame = QFrame()
        header_frame.setStyleSheet("background-color: #1C2B40; border-radius: 8px;")
        header_frame.setMinimumHeight(self.scale(95))
        header_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(self.scale(20), self.scale(5),
                                         self.scale(20), self.scale(5))
        header_layout.setSpacing(self.scale(15))

        # ── Logo ──────────────────────────────────────────────────
        self._create_logo(header_layout)

        # ── Titoli ────────────────────────────────────────────────
        self._create_titles(header_layout)

        # ── Data/ora con icone ────────────────────────────────────
        datetime_container = self._create_datetime_widget()
        header_layout.addStretch(1)
        header_layout.addWidget(datetime_container)
        header_layout.addStretch(1)

        # ── Stato sistema ─────────────────────────────────────────
        state_container = self._create_state_widget()
        header_layout.addWidget(state_container)

        main_layout.addWidget(header_frame)
    
    def _create_logo(self, layout):
        self.logo_label = QLabel()
        logo_size = self.scale(100)
        logo_path = os.path.join(os.path.dirname(__file__), "..", "..", "icons", "ingvlogo.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            pixmap = pixmap.scaled(logo_size, logo_size,
                                   Qt.AspectRatioMode.KeepAspectRatio,
                                   Qt.TransformationMode.SmoothTransformation)
            self.logo_label.setPixmap(pixmap)
        else:
            self.logo_label.setText("🌋")
            self.logo_label.setStyleSheet(f"font-size: {self.fs(70)};")
        self.logo_label.setStyleSheet(f"margin-right: {self.scale(20)}px;")
        self.logo_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        layout.addWidget(self.logo_label)
    
    def _create_titles(self, layout):
        titles_layout = QVBoxLayout()
        titles_layout.setSpacing(0)
        titles_layout.setContentsMargins(0, 0, 0, 0)

        self.title1 = QLabel("OSSERVATORIO VESUVIANO")
        self.title1.setStyleSheet(f"font-size: {self.fs(30)}; font-weight: bold;")
        self.title1.setWordWrap(True)

        self.title2 = QLabel("DASHBOARD-SIMULATORE")
        self.title2.setStyleSheet(f"font-size: {self.fs(24)}; color: #cccccc;")
        self.title2.setWordWrap(True)

        titles_layout.addWidget(self.title1)
        titles_layout.addWidget(self.title2)
        layout.addLayout(titles_layout, 2)
    
    # def _create_datetime_widget(self):
    #     """Crea il widget data/ora con icone (IDENTICO ALL'ORIGINALE)"""
    #     datetime_container = QFrame()
    #     datetime_container.setStyleSheet("background-color: #213B64; border-radius: 6px;")
    #     datetime_container.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
    #     datetime_container.setMinimumHeight(self.scale(35))

    #     datetime_layout = QHBoxLayout(datetime_container)
    #     datetime_layout.setSpacing(self.scale(12))
    #     datetime_layout.setContentsMargins(self.scale(15), 0, self.scale(15), 0)
    #     datetime_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

    #     icon_size = self.scale(28)

    #     # ── Data con icona calendario ─────────────────────────────
    #     data_layout = QHBoxLayout()
    #     data_layout.setSpacing(self.scale(8))
    #     data_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

    #     data_icon = QLabel()
    #     calendar_path = os.path.join(os.path.dirname(__file__), "..", "..", "icons", "calendario.png")
    #     if os.path.exists(calendar_path):
    #         cal_pix = QPixmap(calendar_path).scaled(icon_size, icon_size,
    #             Qt.AspectRatioMode.KeepAspectRatio,
    #             Qt.TransformationMode.SmoothTransformation)
    #         data_icon.setPixmap(cal_pix)
    #     else:
    #         data_icon.setText("📅")
    #         data_icon.setStyleSheet(f"font-size: {self.fs(22)};")

    #     self.data_label = QLabel(datetime.now().strftime("%d/%m/%Y"))
    #     self.data_label.setStyleSheet(f"font-size: {self.fs(24)}; font-weight: bold;")
    #     data_layout.addWidget(data_icon)
    #     data_layout.addWidget(self.data_label)

    #     # ── Separatore ───────────────────────────────────────────
    #     separator = QLabel("|")
    #     separator.setStyleSheet(f"font-size: {self.fs(24)}; color: #4A90E2; font-weight: bold;")
    #     separator.setAlignment(Qt.AlignmentFlag.AlignCenter)

    #     # ── Ora con icona orologio ────────────────────────────────
    #     ora_layout = QHBoxLayout()
    #     ora_layout.setSpacing(self.scale(8))
    #     ora_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

    #     self.utc_label=QLabel()
    #     self.utc_label.setStyleSheet("font-size: 14px; color: #a0c4e8;")
    #     ora_layout.addWidget(self.utc_label)


    #     ora_icon = QLabel()
    #     clock_path = os.path.join(os.path.dirname(__file__), "..", "..", "icons", "orario.png")
    #     if os.path.exists(clock_path):
    #         clk_pix = QPixmap(clock_path).scaled(icon_size, icon_size,
    #             Qt.AspectRatioMode.KeepAspectRatio,
    #             Qt.TransformationMode.SmoothTransformation)
    #         ora_icon.setPixmap(clk_pix)
    #     else:
    #         ora_icon.setText("🕐")
    #         ora_icon.setStyleSheet(f"font-size: {self.fs(22)};")

    #     self.ora_label = QLabel(datetime.now().strftime("%H:%M:%S"))
    #     self.ora_label.setStyleSheet(f"font-size: {self.fs(24)}; font-family: monospace; font-weight: bold;")
    #     ora_layout.addWidget(ora_icon)
    #     ora_layout.addWidget(self.ora_label)

    #     datetime_layout.addLayout(data_layout)
    #     datetime_layout.addWidget(separator)
    #     datetime_layout.addLayout(ora_layout)

    #     return datetime_container

    # def _create_datetime_widget(self):
    #  """Crea il widget data/ora con icone"""
    #  datetime_container = QFrame()
    #  datetime_container.setStyleSheet("background-color: #213B64; border-radius: 6px;")
    #  datetime_container.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
    #  datetime_container.setMinimumHeight(self.scale(35))

    #  datetime_layout = QHBoxLayout(datetime_container)
    #  datetime_layout.setSpacing(self.scale(12))
    #  datetime_layout.setContentsMargins(self.scale(15), 0, self.scale(15), 0)
    #  datetime_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

    #  icon_size = self.scale(28)

    #  # ── Data con icona calendario ─────────────────────────────
    #  data_layout = QHBoxLayout()
    #  data_layout.setSpacing(self.scale(8))
    #  data_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

    #  data_icon = QLabel()
    #  calendar_path = os.path.join(os.path.dirname(__file__), "..", "..", "icons", "calendario.png")
    #  if os.path.exists(calendar_path):
    #     cal_pix = QPixmap(calendar_path).scaled(icon_size, icon_size,
    #         Qt.AspectRatioMode.KeepAspectRatio,
    #         Qt.TransformationMode.SmoothTransformation)
    #     data_icon.setPixmap(cal_pix)
    #  else:
    #     data_icon.setText("📅")
    #     data_icon.setStyleSheet(f"font-size: {self.fs(22)};")

    #  self.data_label = QLabel(datetime.now().strftime("%d/%m/%Y"))
    #  self.data_label.setStyleSheet(f"font-size: {self.fs(24)}; font-weight: bold;")
    #  data_layout.addWidget(data_icon)
    #  data_layout.addWidget(self.data_label)

    #  # ── Separatore ───────────────────────────────────────────
    #  separator1 = QLabel("|")
    #  separator1.setStyleSheet(f"font-size: {self.fs(24)}; color: #4A90E2; font-weight: bold;")
    #  separator1.setAlignment(Qt.AlignmentFlag.AlignCenter)

    #  # ── Ora ITALIANA con icona orologio ─────────────────────
    #  ora_layout = QHBoxLayout()
    #  ora_layout.setSpacing(self.scale(8))
    #  ora_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

    #  ora_icon = QLabel()
    #  clock_path = os.path.join(os.path.dirname(__file__), "..", "..", "icons", "orario.png")
    #  if os.path.exists(clock_path):
    #     clk_pix = QPixmap(clock_path).scaled(icon_size, icon_size,
    #         Qt.AspectRatioMode.KeepAspectRatio,
    #         Qt.TransformationMode.SmoothTransformation)
    #     ora_icon.setPixmap(clk_pix)
    #  else:
    #     ora_icon.setText("🕐")
    #     ora_icon.setStyleSheet(f"font-size: {self.fs(22)};")

    #  self.ora_label = QLabel(datetime.now().strftime("%H:%M:%S"))
    #  self.ora_label.setStyleSheet(f"font-size: {self.fs(24)}; font-family: monospace; font-weight: bold;")
    #  ora_layout.addWidget(ora_icon)
    #  ora_layout.addWidget(self.ora_label)

    #  # ── Separatore tra ora ITA e UTC ────────────────────────
    #  separator2 = QLabel("-")
    #  separator2.setStyleSheet(f"font-size: {self.fs(24)}; color: #4A90E2; font-weight: bold;")
    #  separator2.setAlignment(Qt.AlignmentFlag.AlignCenter)

    #  # ── Ora UTC con icona internet ──────────────────────────
    #  utc_layout = QHBoxLayout()
    #  utc_layout.setSpacing(self.scale(8))
    #  utc_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

    #  utc_icon = QLabel()
    #  internet_path = os.path.join(os.path.dirname(__file__), "..", "..", "icons", "internet.png")
    #  if os.path.exists(internet_path):
    #     internet_pix = QPixmap(internet_path).scaled(icon_size, icon_size,
    #         Qt.AspectRatioMode.KeepAspectRatio,
    #         Qt.TransformationMode.SmoothTransformation)
    #     utc_icon.setPixmap(internet_pix)
    #  else:
    #     utc_icon.setText("🌐")
    #     utc_icon.setStyleSheet(f"font-size: {self.fs(22)};")

    #  self.utc_label = QLabel(datetime.utcnow().strftime("%H:%M:%S"))
    #  self.utc_label.setStyleSheet(f"font-size: {self.fs(24)}; font-family: monospace; font-weight: bold; color: #a0c4e8;")
    #  utc_layout.addWidget(utc_icon)
    #  utc_layout.addWidget(self.utc_label)

    #  # ── Assemblaggio finale ──────────────────────────────────
    #  datetime_layout.addLayout(data_layout)
    #  datetime_layout.addWidget(separator1)
    #  datetime_layout.addLayout(ora_layout)
    #  datetime_layout.addWidget(separator2)
    #  datetime_layout.addLayout(utc_layout)

    # return datetime_container

    def _create_datetime_widget(self):
     """Crea il widget data/ora con icone"""
     datetime_container = QFrame()
     datetime_container.setStyleSheet("background-color: #213B64; border-radius: 6px;")
     datetime_container.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
     datetime_container.setMinimumHeight(self.scale(35))

     datetime_layout = QHBoxLayout(datetime_container)
     datetime_layout.setSpacing(self.scale(12))
     datetime_layout.setContentsMargins(self.scale(15), 0, self.scale(15), 0)
     datetime_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

     icon_size = self.scale(28)

     # ── Data ITALIANA con icona calendario ─────────────────────
     data_layout = QHBoxLayout()
     data_layout.setSpacing(self.scale(8))
     data_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

     data_icon = QLabel()
     calendar_path = os.path.join(os.path.dirname(__file__), "..", "..", "icons", "calendario.png")
     if os.path.exists(calendar_path):
        cal_pix = QPixmap(calendar_path).scaled(icon_size, icon_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation)
        data_icon.setPixmap(cal_pix)
     else:
        data_icon.setText("📅")
        data_icon.setStyleSheet(f"font-size: {self.fs(22)};")

     self.data_label = QLabel(datetime.now().strftime("%d/%m/%Y"))
     self.data_label.setStyleSheet(f"font-size: {self.fs(24)}; font-weight: bold;")
     data_layout.addWidget(data_icon)
     data_layout.addWidget(self.data_label)

     # ── Separatore 1 ─────────────────────────────────────────
    #  separator1 = QLabel("-")
    #  separator1.setStyleSheet(f"font-size: {self.fs(24)}; color: #4A90E2; font-weight: bold;")
    #  separator1.setAlignment(Qt.AlignmentFlag.AlignCenter)

     # ── Data UTC con icona internet ──────────────────────────
     data_utc_layout = QHBoxLayout()
     data_utc_layout.setSpacing(self.scale(8))
     data_utc_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

     data_utc_icon = QLabel()
     internet_path = os.path.join(os.path.dirname(__file__), "..", "..", "icons", "internet.png")
     if os.path.exists(internet_path):
        internet_pix = QPixmap(internet_path).scaled(icon_size, icon_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation)
        data_utc_icon.setPixmap(internet_pix)
     else:
        data_utc_icon.setText("🌐")
        data_utc_icon.setStyleSheet(f"font-size: {self.fs(22)};")

     self.data_utc_label = QLabel(datetime.utcnow().strftime("%d/%m/%Y"))
     self.data_utc_label.setStyleSheet(f"font-size: {self.fs(24)}; font-weight: bold; color: #a0c4e8;")
     data_utc_layout.addWidget(data_utc_icon)
     data_utc_layout.addWidget(self.data_utc_label)

     # ── Separatore 2 ─────────────────────────────────────────
     separator2 = QLabel("|")
     separator2.setStyleSheet(f"font-size: {self.fs(24)}; color: #4A90E2; font-weight: bold;")
     separator2.setAlignment(Qt.AlignmentFlag.AlignCenter)

     # ── Ora ITALIANA con icona orologio ─────────────────────
     ora_layout = QHBoxLayout()
     ora_layout.setSpacing(self.scale(8))
     ora_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

     ora_icon = QLabel()
     clock_path = os.path.join(os.path.dirname(__file__), "..", "..", "icons", "orario.png")
     if os.path.exists(clock_path):
        clk_pix = QPixmap(clock_path).scaled(icon_size, icon_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation)
        ora_icon.setPixmap(clk_pix)
     else:
        ora_icon.setText("🕐")
        ora_icon.setStyleSheet(f"font-size: {self.fs(22)};")

     self.ora_label = QLabel(datetime.now().strftime("%H:%M:%S"))
     self.ora_label.setStyleSheet(f"font-size: {self.fs(24)}; font-family: monospace; font-weight: bold;")
     ora_layout.addWidget(ora_icon)
     ora_layout.addWidget(self.ora_label)

     # ── Separatore 3 ─────────────────────────────────────────
    #  separator3 = QLabel("-")
    #  separator3.setStyleSheet(f"font-size: {self.fs(24)}; color: #4A90E2; font-weight: bold;")
    #  separator3.setAlignment(Qt.AlignmentFlag.AlignCenter)

     # ── Ora UTC con icona internet ──────────────────────────
     utc_layout = QHBoxLayout()
     utc_layout.setSpacing(self.scale(8))
     utc_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

     utc_icon = QLabel()
     # Riutilizziamo internet.png anche per l'ora UTC (o usiamo un'altra icona)
     if os.path.exists(internet_path):
        utc_pix = QPixmap(internet_path).scaled(icon_size, icon_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation)
        utc_icon.setPixmap(utc_pix)
     else:
        utc_icon.setText("🕐")
        utc_icon.setStyleSheet(f"font-size: {self.fs(22)};")

     self.utc_label = QLabel(datetime.utcnow().strftime("%H:%M:%S"))
     self.utc_label.setStyleSheet(f"font-size: {self.fs(24)}; font-family: monospace; font-weight: bold; color: #a0c4e8;")
     utc_layout.addWidget(utc_icon)
     utc_layout.addWidget(self.utc_label)

     # ── Assemblaggio finale ──────────────────────────────────
     datetime_layout.addLayout(data_layout)
     #datetime_layout.addWidget(separator1)
     datetime_layout.addLayout(data_utc_layout)
     datetime_layout.addWidget(separator2)
     datetime_layout.addLayout(ora_layout)
     #datetime_layout.addWidget(separator3)
     datetime_layout.addLayout(utc_layout)

     return datetime_container





    
    
    def _create_state_widget(self):
        """Crea il widget dello stato sistema (IDENTICO ALL'ORIGINALE)"""
        state_container = QFrame()
        state_container.setStyleSheet("background-color: #213B64; border-radius: 6px;")
        state_container.setMinimumWidth(self.scale(200))
        state_container.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        state_layout = QHBoxLayout(state_container)
        state_layout.setContentsMargins(self.scale(15), self.scale(2),
                                        self.scale(15), self.scale(2))
        state_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.state_label = QLabel('STATO: <span style="color: #2e7d32;">NORMALE</span>')
        self.state_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.state_label.setStyleSheet(f"font-size: {self.fs(20)}; font-weight: bold;")
        self.state_label.setWordWrap(True)
        state_layout.addWidget(self.state_label)

        return state_container
    
    # ─── UI UPDATE METHODS ───────────────────────────────────────
    def update_state(self, state, color):
        """Aggiorna il testo dello stato con il colore"""
        self.state_label.setText(f'STATO: <span style="color: {color};">{state}</span>')
    
    def update_clock(self, time_str, utc_time, date_str=None, date_utc_str=None):
        """Aggiorna l'orologio"""
        self.ora_label.setText(f"{time_str} UTC+1")
        self.utc_label.setText(f"{utc_time} UTC")

        if date_str:
         self.data_label.setText(date_str)
        if date_utc_str:
         self.data_utc_label.setText(date_utc_str)
        
    
    def update_date(self, date_str):
        """Aggiorna la data"""
        self.data_label.setText(date_str)
    
    def resize(self, width):
     """Gestisce il resize dell'header"""
     if width >= 3840:
        t1, t2, td, ts, ls = "48px", "36px", "36px", "30px", 160
     elif width >= 2560:
        t1, t2, td, ts, ls = "38px", "28px", "30px", "24px", 130
     elif width >= 1920:
        t1, t2, td, ts, ls = "30px", "24px", "24px", "20px", 100
     elif width >= 1400:
        t1, t2, td, ts, ls = "26px", "20px", "20px", "17px", 85
     else:
        t1, t2, td, ts, ls = "20px", "15px", "16px", "15px", 60

     self.title1.setStyleSheet(f"font-size: {t1}; font-weight: bold; color: white;")
     self.title2.setStyleSheet(f"font-size: {t2}; color: #cccccc;")
     self.data_label.setStyleSheet(f"font-size: {td}; color: white; font-weight: bold;")
     self.data_utc_label.setStyleSheet(f"font-size: {td}; color: #a0c4e8; font-weight: bold;")  # AGGIUNTO
     self.ora_label.setStyleSheet(f"font-size: {td}; color: white; font-family: monospace;")
     self.utc_label.setStyleSheet(f"font-size: {td}; color: #a0c4e8; font-family: monospace;")
     self.state_label.setStyleSheet(f"font-size: {ts}; font-weight: bold;")

     # Logo resize
     logo_path = os.path.join(os.path.dirname(__file__), "..", "..", "icons", "ingvlogo.png")
     if os.path.exists(logo_path):
        pixmap = QPixmap(logo_path)
        self.logo_label.setPixmap(
            pixmap.scaled(ls, ls,
                          Qt.AspectRatioMode.KeepAspectRatio,
                          Qt.TransformationMode.SmoothTransformation)
        )