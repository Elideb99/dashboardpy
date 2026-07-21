import os
from datetime import datetime
from PyQt6.QtCore import Qt 
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QSizePolicy
from PyQt6.QtGui import QPixmap, QPainter, QPainterPath, QColor, QPen

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
        self.state_icon = None
        self.swarm_label= None
    
    def scale(self, v):
        return max(1, int(v * self.ui_scale))
    
    def fs(self, px):
        return f"{self.scale(px)}px"
    
    def create(self, main_layout):
     header_frame = QFrame()
     header_frame.setStyleSheet("background-color: #0F1521; border-radius: 8px;")
     header_frame.setMinimumHeight(self.scale(95))
     header_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
 
     header_layout = QHBoxLayout(header_frame)
     header_layout.setContentsMargins(self.scale(20), self.scale(10),
                                     self.scale(20), self.scale(10))
     header_layout.setSpacing(self.scale(15))

     self._create_logo(header_layout)
     self._create_titles(header_layout)

     header_layout.addStretch(1)

     datetime_container = self._create_datetime_widget()
     header_layout.addWidget(datetime_container)

     header_layout.addStretch(1)

     state_container = self._create_state_widget()
     header_layout.addWidget(state_container)

     swarm_container = self._create_swarm_widget()
     header_layout.addWidget(swarm_container)

     main_layout.addWidget(header_frame)

    def _create_swarm_widget(self):
     """Crea il riquadro dello stato dello sciame sismico"""

     container = QFrame()
     container.setStyleSheet("background-color: #1C2B40; border-radius: 8px;")
     container.setMinimumWidth(self.scale(210))
     container.setMinimumHeight(self.scale(50))
     container.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

     layout = QVBoxLayout(container)
     layout.setContentsMargins(
        self.scale(14),
        self.scale(8),
        self.scale(14),
        self.scale(8)
     )
     layout.setSpacing(self.scale(4))

     caption = QLabel("SCIAME SISMICO:")
     caption.setStyleSheet(
        f"font-size: {self.fs(15)}; color: #a0c4e8; "
        f"font-weight: bold; letter-spacing: 1px;"
     )
     layout.addWidget(caption)

     self.swarm_label = QLabel("N.D.")
     self.swarm_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
     layout.addWidget(self.swarm_label)

     self.update_swarm_state("N.D.", "#53565A")

     return container


    def update_swarm_state(self, state, color="#53565A", tooltip=""):
     """Aggiorna il riquadro dello sciame sismico"""

     if not self.swarm_label:
        return

     self.swarm_label.setText(state)
     self.swarm_label.setToolTip(tooltip)

     self.swarm_label.setStyleSheet(f"""
        background-color: {color};
        color: white;
        font-weight: bold;
        font-size: {self.fs(14)};
        border-radius: {self.scale(6)}px;
        padding: {self.scale(2)}px {self.scale(10)}px;
     """)
    
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

    def _create_datetime_widget(self):
     """Card data/ora in stile mockup: data+giorno sopra, ora+UTC sotto"""
     container = QFrame()
     container.setStyleSheet("background-color: #1C2B40; border-radius: 8px;")
     container.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
     container.setMinimumHeight(self.scale(50))
     container.setMinimumWidth(self.scale(260))

     layout = QHBoxLayout(container)
     layout.setContentsMargins(self.scale(16), self.scale(6), self.scale(16), self.scale(6))
     layout.setSpacing(self.scale(14))
     layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

     icon_size = self.scale(24)

     # ── Icona calendario ──────────────────────────────────────
     cal_icon = QLabel()
     calendar_path = os.path.join(os.path.dirname(__file__), "..", "..", "icons", "calendario.png")
     if os.path.exists(calendar_path):
        pix = QPixmap(calendar_path).scaled(icon_size, icon_size,
            Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        cal_icon.setPixmap(pix)
     else:
        cal_icon.setText("📅")
        cal_icon.setStyleSheet(f"font-size: {self.fs(20)};")
     layout.addWidget(cal_icon)

     # ── Blocco data (data + giorno settimana) ─────────────────

     data_block = QVBoxLayout()
     data_block.setSpacing(0)

     self.data_label = QLabel(datetime.now().strftime("%d/%m/%Y"))
     self.data_label.setStyleSheet(f"font-size: {self.fs(18)};color: white;")

     self.data_utc_label = QLabel(datetime.utcnow().strftime("%d/%m/%Y") + " UTC")
     self.data_utc_label.setStyleSheet(f"font-size: {self.fs(13)}; font-family: monospace; color: #7E8CA3;")

     data_block.addWidget(self.data_label)
     data_block.addWidget(self.data_utc_label)
     layout.addLayout(data_block)

     # ── Separatore verticale ───────────────────────────────────
     sep = QFrame()
     sep.setFrameShape(QFrame.Shape.VLine)
     sep.setStyleSheet("color: #2A3B52;")
     layout.addWidget(sep)

     # ── Icona orologio ─────────────────────────────────────────
     clock_icon = QLabel()
     clock_path = os.path.join(os.path.dirname(__file__), "..", "..", "icons", "orario.png")
     if os.path.exists(clock_path):
        pix = QPixmap(clock_path).scaled(icon_size, icon_size,
            Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        clock_icon.setPixmap(pix)
     else:
        clock_icon.setText("🕐")
        clock_icon.setStyleSheet(f"font-size: {self.fs(20)};")
     layout.addWidget(clock_icon)

     # ── Blocco ora (ora locale + UTC) ──────────────────────────
     ora_block = QVBoxLayout()
     ora_block.setSpacing(0)

     self.ora_label = QLabel(datetime.now().strftime("%H:%M:%S"))
     self.ora_label.setStyleSheet(f"font-size: {self.fs(18)}; font-weight: bold; font-family: monospace; color: white;")

     self.utc_label = QLabel(datetime.utcnow().strftime("%H:%M:%S") + " UTC")
     self.utc_label.setStyleSheet(f"font-size: {self.fs(13)}; font-family: monospace; color: #7E8CA3;")

     ora_block.addWidget(self.ora_label)
     ora_block.addWidget(self.utc_label)
     layout.addLayout(ora_block)


     return container





    def _create_state_widget(self):
     """Crea il widget dello stato sistema: icona + etichetta + pillola colorata"""

     container = QFrame()
     container.setStyleSheet("background-color: #1C2B40; border-radius: 8px;")
     container.setMinimumWidth(self.scale(170))
     container.setMinimumHeight(self.scale(50))
     container.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

     outer = QHBoxLayout(container)
     outer.setContentsMargins(
        self.scale(14),
        self.scale(8),
        self.scale(14),
        self.scale(8)
     )
     outer.setSpacing(self.scale(10))
     outer.setAlignment(Qt.AlignmentFlag.AlignVCenter)

     self.state_icon = QLabel()
     icon_size = self.scale(24)
     self.state_icon.setPixmap(self._draw_shield_icon("#53565A", icon_size))
     outer.addWidget(self.state_icon)

     text_block = QVBoxLayout()
     text_block.setSpacing(self.scale(4))
     text_block.setContentsMargins(0, 0, 0, 0)

     caption = QLabel("STATO SISTEMA:")
     caption.setStyleSheet(
        f"font-size: {self.fs(15)}; color: #a0c4e8; "
        f"font-weight: bold; letter-spacing: 1px;"
     )
     text_block.addWidget(caption)

     self.state_label = QLabel("N.D.")
     self.state_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
     text_block.addWidget(self.state_label)

     outer.addLayout(text_block)

     self.update_state("N.D.", "#53565A")

     return container

    def _apply_state_style(self, color):
     """Applica lo sfondo colorato + testo bianco alla pillola di stato"""

     self.state_label.setStyleSheet(f"""
        background-color: {color};
        color: white;
        font-weight: bold;
        font-size: {self.fs(14)};
        border-radius: {self.scale(6)}px;
        padding: {self.scale(2)}px {self.scale(10)}px;
     """)

     self._current_color = color

     if hasattr(self, "state_icon") and self.state_icon:
        self.state_icon.setPixmap(self._draw_shield_icon(color))
     # ─── STATO SISTEMA basato sull'ultimo evento sismico ──────────
    def update_state_from_event(self, magnitudo=None, timestamp=None):
     if magnitudo is None:
        self.update_state("N.D.", "#53565A")
        if self.state_label:
            self.state_label.setToolTip("")
        return

     if magnitudo >= 3.0:
        stato, colore = "ALLARME", "#c62828"
     elif magnitudo >= 2.0:
        stato, colore = "ATTENZIONE", "#f9a825"
     else:
        stato, colore = "NORMALE", "#2e7d32"

     self.update_state(stato, colore)

     if timestamp and self.state_label:
        self.state_label.setToolTip(f"Ultimo evento rilevante: {timestamp}")

    def update_state(self, state, color):
     self.state_label.setText(state)
     self._apply_state_style(color)
    
   
    def update_clock(self, time_str, utc_time, date_str=None, date_utc_str=None):
     self.ora_label.setText(time_str)
     self.utc_label.setText(f"{utc_time} UTC")
     if date_str:
        self.data_label.setText(date_str)
     if date_utc_str:
        self.data_utc_label.setText(f"{date_utc_str} UTC")
        
    
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
     self.data_label.setStyleSheet(f"font-size: {td}; color: white; font-family: monospace;")
     self.data_utc_label.setStyleSheet(f"font-size: {td}; color: #a0c4e8; font-family: monospace;")  # AGGIUNTO
     self.ora_label.setStyleSheet(f"font-size: {td}; color: white; font-family: monospace;")
     self.utc_label.setStyleSheet(f"font-size: {td}; color: #a0c4e8; font-family: monospace;")

     # Logo resize
     logo_path = os.path.join(os.path.dirname(__file__), "..", "..", "icons", "ingvlogo.png")
     if os.path.exists(logo_path):
        pixmap = QPixmap(logo_path)
        self.logo_label.setPixmap(
            pixmap.scaled(ls, ls,
                          Qt.AspectRatioMode.KeepAspectRatio,
                          Qt.TransformationMode.SmoothTransformation)
        )

    def _draw_shield_icon(self, color, size=None):
     """Disegna un'icona a scudo colorata dinamicamente (nessun file esterno)"""
     if size is None:
        size = self.scale(24)

     pixmap = QPixmap(size, size)
     pixmap.fill(Qt.GlobalColor.transparent)

     painter = QPainter(pixmap)
     painter.setRenderHint(QPainter.RenderHint.Antialiasing)

     w, h = size, size
     path = QPainterPath()
     # Punto in alto al centro
     path.moveTo(w * 0.5, h * 0.05)
     # Lato destro verso il basso
     path.cubicTo(w * 0.85, h * 0.15, w * 0.95, h * 0.20, w * 0.95, h * 0.20)
     path.lineTo(w * 0.95, h * 0.55)
     path.cubicTo(w * 0.95, h * 0.78, w * 0.75, h * 0.92, w * 0.5, h * 0.98)
     path.cubicTo(w * 0.25, h * 0.92, w * 0.05, h * 0.78, w * 0.05, h * 0.55)
     path.lineTo(w * 0.05, h * 0.20)
     path.cubicTo(w * 0.05, h * 0.20, w * 0.15, h * 0.15, w * 0.5, h * 0.05)
     path.closeSubpath()

     painter.setPen(QPen(QColor("white"), max(1, size * 0.04)))
     painter.setBrush(QColor(color))
     painter.drawPath(path)

     # Segno di spunta al centro (facoltativo, stile "sicurezza attiva")
     check = QPainterPath()
     check.moveTo(w * 0.30, h * 0.52)
     check.lineTo(w * 0.45, h * 0.68)
     check.lineTo(w * 0.72, h * 0.35)
     painter.setPen(QPen(QColor("white"), max(1.5, size * 0.07),
                         Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap,
                         Qt.PenJoinStyle.RoundJoin))
     painter.drawPath(check)

     painter.end()
     return pixmap