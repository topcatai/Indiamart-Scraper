from PyQt6.QtWidgets import QStatusBar, QLabel
from PyQt6.QtCore import Qt

class StatusBar(QStatusBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #a0a5c0; font-family: 'Segoe UI', sans-serif;")
        self.addWidget(self.status_label, 1)

    def show_message(self, message):
        self.status_label.setText(message)
        parent = self.parent()
        if parent and hasattr(parent, 'log_console'):
            parent.log_console.append_log(message)
