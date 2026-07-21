from PyQt6.QtWidgets import QPushButton, QHBoxLayout

class ControlsView:
    """VIEW: Gestisce i pulsanti di controllo"""
    
    def __init__(self, parent, ui_scale):
        self.parent = parent
        self.ui_scale = ui_scale
        self.controller = None  # Verrà settato dopo
    
    def scale(self, v):
        return max(1, int(v * self.ui_scale))
    
    def fs(self, px):
        return f"{self.scale(px)}px"
    
    def create(self, parent_layout):
        layout = QHBoxLayout()
        layout.setSpacing(self.scale(15))
        
        
        parent_layout.addLayout(layout)
    
    def _create_button(self, text, bg_color, hover_color):
        """Crea un pulsante con stile scalabile"""
        button = QPushButton(text)
        
        base_style = f"""
        QPushButton {{
            font-size: {self.fs(14)};
            font-weight: bold;
            min-height: {self.scale(25)}px;
            min-width: {self.scale(160)}px;
            padding: {self.scale(10)}px {self.scale(20)}px;
            border-radius: {self.scale(8)}px;
            color: white;
            background-color: {bg_color};
        }}
        QPushButton:hover {{
            background-color: {hover_color};
        }}
        """
        
        button.setStyleSheet(base_style)
        return button
    
    def set_controller(self, controller):
        """Imposta il controller e collega i pulsanti"""
        self.controller = controller
   