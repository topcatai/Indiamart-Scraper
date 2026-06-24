import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, 
                             QFrame, QFileDialog, QMessageBox, QScrollArea)
from PyQt6.QtCore import pyqtSignal, Qt
import db_manager
from app.crm_dialog import CRMDialog

class Sidebar(QWidget):
    start_clicked = pyqtSignal()
    pause_clicked = pyqtSignal()
    retry_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.all_contacts_count = 0

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Scroll Area for sidebar
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setObjectName("sidebarScroll")
        scroll_area.setMinimumWidth(0)
        
        scroll_content = QWidget()
        scroll_content.setObjectName("scrollAreaWidgetContents")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(15, 15, 15, 15)
        scroll_layout.setSpacing(10)

        # Title Label
        title_lbl = QLabel("IndiaMART Lead Scraper")
        title_lbl.setStyleSheet("color: #ffffff; font-size: 15px; font-weight: bold; margin-bottom: 10px;")
        scroll_layout.addWidget(title_lbl)

        # ------------------ STATS SECTION ------------------
        scroll_layout.addWidget(self._create_header("Dashboard"))

        # All Contacts
        self.card_all, self.val_all = self._create_stat_card("ALL CONTACTS", "0", "valAll")
        scroll_layout.addWidget(self.card_all)

        # Scraped
        self.card_scraped, self.val_scraped = self._create_stat_card("SCRAPED LEADS", "0", "valScraped")
        scroll_layout.addWidget(self.card_scraped)

        # Failed
        self.card_failed, self.val_failed = self._create_stat_card("FAILED / SKIPPED", "0", "valFailed")
        scroll_layout.addWidget(self.card_failed)

        # Pending
        self.card_pending, self.val_pending = self._create_stat_card("PENDING SCRAPE", "0", "valPending")
        scroll_layout.addWidget(self.card_pending)

        # ------------------ CONTROLS SECTION ------------------
        scroll_layout.addWidget(self._create_header("Controls"))

        self.start_btn = QPushButton("Start Scrape")
        self.start_btn.setObjectName("startBtn")
        self.start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.start_btn.clicked.connect(self.start_clicked.emit)
        scroll_layout.addWidget(self.start_btn)

        self.pause_btn = QPushButton("Pause Scrape")
        self.pause_btn.setObjectName("pauseBtn")
        self.pause_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.pause_btn.setEnabled(False)
        self.pause_btn.clicked.connect(self.pause_clicked.emit)
        scroll_layout.addWidget(self.pause_btn)

        self.retry_btn = QPushButton("Retry Failed")
        self.retry_btn.setObjectName("retryBtn")
        self.retry_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.retry_btn.clicked.connect(self.retry_clicked.emit)
        scroll_layout.addWidget(self.retry_btn)

        # ------------------ EXPORTS SECTION ------------------
        scroll_layout.addWidget(self._create_header("Exports"))

        csv_btn = QPushButton("Export to CSV")
        csv_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        csv_btn.clicked.connect(self.export_csv)
        scroll_layout.addWidget(csv_btn)

        excel_btn = QPushButton("Export to Excel")
        excel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        excel_btn.clicked.connect(self.export_excel)
        scroll_layout.addWidget(excel_btn)

        # ------------------ PREMIUM SECTION ------------------
        scroll_layout.addWidget(self._create_header("Integrations"))

        crm_btn = QPushButton("🔌 Connect CRM")
        crm_btn.setObjectName("crmBtn")
        crm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        crm_btn.clicked.connect(self.open_crm_dialog)
        scroll_layout.addWidget(crm_btn)

        # ------------------ SUPPORT SECTION ------------------
        scroll_layout.addWidget(self._create_header("Support"))

        report_btn = QPushButton("🐞 Report an Error")
        report_btn.setObjectName("reportBtn")
        report_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        report_btn.clicked.connect(self.report_error)
        scroll_layout.addWidget(report_btn)

        scroll_layout.addStretch()
        
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

        # Init stats
        self.refresh_stats()

    def _create_header(self, text):
        lbl = QLabel(text)
        lbl.setProperty("class", "section-header")
        lbl.setContentsMargins(0, 10, 0, 5)
        return lbl

    def _create_stat_card(self, title, init_value, val_object_name):
        frame = QFrame()
        frame.setProperty("class", "stat-card")
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(2)

        title_lbl = QLabel(title)
        title_lbl.setProperty("class", "stat-title")
        
        val_lbl = QLabel(init_value)
        val_lbl.setObjectName(val_object_name)
        val_lbl.setProperty("class", "stat-value")

        layout.addWidget(title_lbl)
        layout.addWidget(val_lbl)

        return frame, val_lbl

    def update_all_contacts(self, count):
        if count is not None:
            self.all_contacts_count = count
            self.val_all.setText(f"{count:,}")
            self.refresh_stats()

    def refresh_stats(self):
        try:
            scraped = db_manager.get_scraped_count()
            failed = db_manager.get_failed_count()
            self.val_scraped.setText(f"{scraped:,}")
            self.val_failed.setText(f"{failed:,}")

            if self.all_contacts_count > 0:
                pending = max(0, self.all_contacts_count - scraped - failed)
                self.val_pending.setText(f"{pending:,}")
            else:
                self.val_pending.setText("-")
        except Exception as e:
            print(f"[!] Error refreshing stats in GUI: {e}")

    def export_csv(self):
        try:
            db_manager.export_to_formats()
            QMessageBox.information(self, "Export Complete", 
                                    f"CSV file exported successfully to:\n{os.path.abspath(db_manager.config.CSV_PATH)}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export CSV: {e}")

    def export_excel(self):
        try:
            db_manager.export_to_formats()
            QMessageBox.information(self, "Export Complete", 
                                    f"Excel file exported successfully to:\n{os.path.abspath(db_manager.config.EXCEL_PATH)}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export Excel: {e}")

    def open_crm_dialog(self):
        dialog = CRMDialog(self)
        dialog.exec()

    def set_scraping_state(self, is_scraping):
        self.start_btn.setEnabled(not is_scraping)
        self.pause_btn.setEnabled(is_scraping)
        self.retry_btn.setEnabled(not is_scraping)

    def report_error(self):
        from PyQt6.QtCore import QUrl
        from PyQt6.QtGui import QDesktopServices
        url = QUrl(db_manager.config.CODEBERG_ISSUES_URL)
        QDesktopServices.openUrl(url)
