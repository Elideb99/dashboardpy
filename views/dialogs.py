from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtGui import QIcon


class AlarmDialog(QMessageBox):
    """VIEW: gestisce il popup di allarme sismico."""

    # Inizializza il dialogo con magnitudo, zona e scala grafica.
    def __init__(self, parent, ui_scale, magnitudo, zona):
        super().__init__(parent)

        self.ui_scale = ui_scale
        self.magnitudo = magnitudo
        self.zona = zona

        self.setWindowTitle("ALLARME SISMICO")
        self.setIcon(QMessageBox.Icon.NoIcon)

        self._setup_content()
        self._setup_style()

        # Rimuove i pulsanti standard del QMessageBox.
        self.setStandardButtons(
            QMessageBox.StandardButton.NoButton
        )

        self.setMinimumSize(
            self.scale(500),
            self.scale(300)
        )

    # Gestisce la chiusura del dialogo tramite il pulsante della finestra.
    def closeEvent(self, event):
        self.accept()
        event.accept()

    # Ridimensiona un valore in base alla scala dell'interfaccia.
    def scale(self, v):
        return max(1, int(v * self.ui_scale))

    # Converte una dimensione in pixel adattandola alla scala grafica.
    def fs(self, px):
        return f"{self.scale(px)}px"

    # Imposta il contenuto testuale del popup di allarme.
    def _setup_content(self):
        self.setText(
            f"<div style='text-align: center;'>"
            f"<h2 style='color: #d32f2f; margin: {self.scale(20)}px;'>"
            f"ALLARME SISMICO"
            f"</h2>"
            f"<hr>"
            f"<p style='font-size: {self.fs(18)}; "
            f"margin: {self.scale(20)}px;'>"
            f"<b>Zona:</b> {self.zona}</p>"
            f"<p style='font-size: {self.fs(18)}; "
            f"margin: {self.scale(10)}px;'>"
            f"<b>Magnitudo:</b> "
            f"<b style='color: #ff0000; "
            f"font-size: {self.fs(24)};'>"
            f"M{self.magnitudo}</b></p>"
            f"</div>"
        )

    # Applica lo stile grafico al popup e ai suoi componenti.
    def _setup_style(self):
        btn_fs = self.fs(16)
        btn_pad = self.scale(8)
        btn_pad2 = self.scale(20)
        btn_mh = self.scale(35)

        self.setStyleSheet(
            f"""
            QMessageBox {{
                font-size: {btn_fs};
                min-width: {self.scale(450)}px;
                min-height: {self.scale(250)}px;
            }}

            QLabel {{
                font-size: {btn_fs};
                min-width: {self.scale(400)}px;
            }}

            QPushButton {{
                font-size: {btn_fs};
                padding: {btn_pad}px {btn_pad2}px;
                min-width: {self.scale(100)}px;
                min-height: {btn_mh}px;
                background-color: #c62828;
                color: white;
                border-radius: {self.scale(5)}px;
            }}

            QPushButton:hover {{
                background-color: #b71c1c;
            }}
            """
        )