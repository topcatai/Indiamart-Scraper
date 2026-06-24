import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QPushButton, QMessageBox, QLabel
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QFont, QDesktopServices, QClipboard
import db_manager

class LogConsole(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("logConsole")
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # Title Label
        title_lbl = QLabel("Activity Log Console")
        title_lbl.setStyleSheet("color: #8f94fb; font-size: 11px; font-weight: bold; text-transform: uppercase; letter-spacing: 1px;")
        layout.addWidget(title_lbl)

        # Log Text display window
        self.text_display = QTextEdit()
        self.text_display.setMinimumWidth(0)
        self.text_display.setReadOnly(True)
        self.text_display.setFont(QFont("Consolas", 10))
        self.text_display.setStyleSheet("""
            QTextEdit {
                background-color: #0c0d16;
                color: #00ffcc;
                border: 1px solid #25263d;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        layout.addWidget(self.text_display)

        # Submit Log button
        self.submit_btn = QPushButton("📤 Submit Log for Analysis")
        self.submit_btn.setObjectName("submitLogBtn")
        self.submit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.submit_btn.setStyleSheet("""
            QPushButton#submitLogBtn {
                background-color: #1a1b35;
                color: #8f94fb;
                border: 1px solid #2d2f52;
                border-radius: 4px;
                padding: 8px 12px;
                font-weight: bold;
            }
            QPushButton#submitLogBtn:hover {
                background-color: #27294d;
                border-color: #8f94fb;
                color: #ffffff;
            }
        """)
        self.submit_btn.clicked.connect(self.submit_log)
        layout.addWidget(self.submit_btn)

    def append_log(self, text):
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.text_display.append(f"[{timestamp}] {text}")
        # Auto-scroll to bottom
        sb = self.text_display.verticalScrollBar()
        sb.setValue(sb.maximum())

    def submit_log(self):
        log_content = self.text_display.toPlainText()
        if not log_content.strip():
            QMessageBox.warning(self, "Empty Log", "The activity log is currently empty.")
            return

        # 1. Save log locally
        log_filename = "scraper_activity_log.txt"
        try:
            with open(log_filename, "w", encoding="utf-8") as f:
                f.write(log_content)
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save log locally: {e}")
            return

        # 2. Copy log to clipboard
        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(log_content)

        # 3. Inform user and launch Codeberg issues
        QMessageBox.information(
            self,
            "Log Prepared",
            f"1. The activity log has been saved locally as '{log_filename}'.\n"
            f"2. The log content has also been copied to your clipboard.\n\n"
            f"We will now open the Codeberg issue tracker in your browser. "
            f"Please create a new issue and paste the log or upload the '{log_filename}' file.",
            QMessageBox.StandardButton.Ok
        )

        url = QUrl(db_manager.config.CODEBERG_ISSUES_URL)
        QDesktopServices.openUrl(url)
