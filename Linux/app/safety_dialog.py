from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QCheckBox, QHBoxLayout
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont

class SafetyDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Pre-Launch Safety & Compliance Guidelines")
        self.setFixedSize(520, 420)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self.setStyleSheet("""
            QDialog {
                background-color: #0f101d;
                border: 2px solid #e57373;
                border-radius: 8px;
            }
            QLabel {
                color: #e0e0e0;
                line-height: 1.4;
            }
            QCheckBox {
                color: #ffffff;
                font-weight: bold;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #2d2f52;
                background-color: #15162b;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                background-color: #4caf50;
                border-color: #4caf50;
            }
            QPushButton {
                background-color: #1e1f38;
                color: #ffffff;
                border: 1px solid #2d2f52;
                border-radius: 4px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #27294d;
                border-color: #4e54c8;
            }
            QPushButton:disabled {
                background-color: #111221;
                color: #555770;
                border-color: #1e1f38;
            }
            QPushButton#acceptBtn {
                background-color: #4caf50;
                color: #0f101d;
                border: none;
            }
            QPushButton#acceptBtn:hover {
                background-color: #66bb6a;
            }
            QPushButton#acceptBtn:disabled {
                background-color: #2e4d31;
                color: #718d74;
            }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)

        # Title
        title_label = QLabel("⚠️ Pre-Launch Safety Guidelines")
        title_font = QFont("Segoe UI", 16, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #e57373;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Description
        desc_label = QLabel(
            "Please read and acknowledge the following safety controls enforced by the application:\n\n"
            "• ⏰ **Daylight Scraping Window**: Scraping is restricted to exactly **8 hours per day max**, "
            "running exclusively during daylight hours in your local region (calculated dynamically).\n\n"
            "• 🐢 **Humanized Delays**: Random pauses of **15 to 30 seconds** are enforced between scraping "
            "actions to match manual browsing speeds and bypass bot-detection flags.\n\n"
            "• 📉 **Risk Mitigation**: All historical leads are scraped once and cached in the local database. "
            "Subsequent runs will only scan your current ongoing month, reducing platform traffic.\n\n"
            "• ⚖️ **Compliance Notice**: Automated scraping violates IndiaMART's Terms of Use. Running "
            "this application carries operational risk, including potential paid account suspension."
        )
        desc_label.setWordWrap(True)
        desc_label.setFont(QFont("Segoe UI", 10))
        layout.addWidget(desc_label)

        # Accept Checkbox
        self.checkbox = QCheckBox("I understand the operational risks and accept these safety limits.")
        self.checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
        self.checkbox.stateChanged.connect(self.on_state_changed)
        layout.addWidget(self.checkbox)

        # Buttons layout
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.accept_btn = QPushButton("Proceed to Application")
        self.accept_btn.setObjectName("acceptBtn")
        self.accept_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.accept_btn.setEnabled(False)
        self.accept_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.accept_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def on_state_changed(self, state):
        self.accept_btn.setEnabled(state == 2)
