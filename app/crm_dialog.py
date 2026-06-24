from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices, QFont

class CRMDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("CRM Integration (Premium)")
        self.setFixedSize(450, 320)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self.setStyleSheet("""
            QDialog {
                background-color: #1a1a2e;
                border: 2px solid #d4af37;
                border-radius: 8px;
            }
            QLabel {
                color: #e0e0e0;
            }
            QPushButton {
                background-color: #162447;
                color: #ffffff;
                border: 1px solid #0f4c75;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1f4068;
                border-color: #3282b8;
            }
            QPushButton#closeBtn {
                background-color: #333333;
                border: 1px solid #555555;
            }
            QPushButton#closeBtn:hover {
                background-color: #444444;
            }
            QPushButton#primaryBtn {
                background-color: #d4af37;
                color: #1a1a2e;
                border: 1px solid #b8901c;
            }
            QPushButton#primaryBtn:hover {
                background-color: #ebd582;
            }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title_label = QLabel("✨ CRM Integration Sync")
        title_font = QFont("Segoe UI", 16, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #d4af37;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Description
        desc_label = QLabel(
            "Directly connect your IndiaMART lead pipeline to standard CRM platforms:\n\n"
            "• Zoho CRM / Creator\n"
            "• HubSpot\n"
            "• Salesforce\n"
            "• LeadSquared / Custom APIs\n\n"
            "This is a premium addon service. Contact us to establish instant automatic sync."
        )
        desc_label.setWordWrap(True)
        desc_label.setFont(QFont("Segoe UI", 10))
        layout.addWidget(desc_label)

        # Buttons Layout
        btn_layout = QHBoxLayout()
        
        # WhatsApp button
        whatsapp_btn = QPushButton("Request WhatsApp Integration")
        whatsapp_btn.setObjectName("primaryBtn")
        whatsapp_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        whatsapp_btn.clicked.connect(self.open_whatsapp)
        btn_layout.addWidget(whatsapp_btn)

        # Email button
        email_btn = QPushButton("Contact via Email")
        email_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        email_btn.clicked.connect(self.open_email)
        btn_layout.addWidget(email_btn)
        
        layout.addLayout(btn_layout)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.setObjectName("closeBtn")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.reject)
        layout.addWidget(close_btn)

        self.setLayout(layout)

    def open_whatsapp(self):
        # Prefilled WhatsApp message
        text = "Hello! I am interested in the Premium CRM Integration for the IndiaMART Lead Scraper application."
        url = QUrl(f"https://wa.me/919999999999?text={QUrl.toPercentEncoding(text)}")
        QDesktopServices.openUrl(url)

    def open_email(self):
        # Mailto link
        subject = "IndiaMART Scraper - CRM Integration Inquiry"
        body = "Hello,\n\nI am interested in setting up the Premium CRM Integration for the IndiaMART Lead Scraper app.\n\nMy CRM Platform: [Zoho/HubSpot/Salesforce/Other]\nContact Number: "
        url = QUrl(f"mailto:support@example.com?subject={QUrl.toPercentEncoding(subject)}&body={QUrl.toPercentEncoding(body)}")
        QDesktopServices.openUrl(url)
