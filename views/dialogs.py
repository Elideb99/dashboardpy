from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtGui import QIcon


class AlarmDialog(QMessageBox):
    """VIEW: Dialogo di allarme sismico"""

    def __init__(self, parent, ui_scale, magnitudo, zona):
        super().__init__(parent)
        self.ui_scale  = ui_scale
        self.magnitudo = magnitudo
        self.zona      = zona

        self.setWindowTitle("ALLARME SISMICO")
        self.setIcon(QMessageBox.Icon.NoIcon)

        self._setup_content()
        self._setup_style()

        self.setStandardButtons(QMessageBox.StandardButton.Ok)
        ok_button = self.button(QMessageBox.StandardButton.Ok)
        ok_button.setIcon(QIcon())


        self.setMinimumSize(self.scale(500), self.scale(300))

    def scale(self, v):
        return max(1, int(v * self.ui_scale))

    def fs(self, px):
        return f"{self.scale(px)}px"

    def _setup_content(self):
        self.setText(
            f"<div style='text-align: center;'>"
            f"<h2 style='color: #d32f2f; margin: {self.scale(20)}px;'>ALLARME SISMICO</h2>"
            f"<hr>"
            f"<p style='font-size: {self.fs(18)}; margin: {self.scale(20)}px;'>"
            f"<b>Zona:</b> {self.zona}</p>"
            f"<p style='font-size: {self.fs(18)}; margin: {self.scale(10)}px;'>"
            f"<b>Magnitudo:</b> "
            f"<b style='color: #ff0000; font-size: {self.fs(24)};'>M{self.magnitudo}</b></p>"
            f"</div>"
        )

    def _setup_style(self):
        btn_fs  = self.fs(16)
        btn_pad = self.scale(8)
        btn_pad2 = self.scale(20)
        btn_mh  = self.scale(35)

        self.setStyleSheet(f"""
            QMessageBox {{
                font-size: {btn_fs};
                min-width:  {self.scale(450)}px;
                min-height: {self.scale(250)}px;
            }}
            QLabel {{
                font-size: {btn_fs};
                min-width:  {self.scale(400)}px;
            }}
            QPushButton {{
                font-size:    {btn_fs};
                padding:      {btn_pad}px {btn_pad2}px;
                min-width:    {self.scale(100)}px;
                min-height:   {btn_mh}px;
                background-color: #c62828;
                color:        white;
                border-radius: {self.scale(5)}px;
            }}
            QPushButton:hover {{
                background-color: #b71c1c;
            }}
        """)