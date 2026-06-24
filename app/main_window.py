import os
from PyQt6.QtWidgets import QMainWindow, QSplitter, QWidget, QHBoxLayout, QMessageBox, QApplication, QDialog, QVBoxLayout, QDialogButtonBox, QLabel, QLineEdit, QCalendarWidget, QPushButton
from PyQt6.QtCore import QUrl, Qt, QDate, QRegularExpression
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage, QWebEngineScript
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtGui import QKeySequence, QShortcut, QRegularExpressionValidator

from app.sidebar import Sidebar
from app.status_bar import StatusBar
from app.js_bridge import JSBridge
from app.scrape_worker import ScrapeWorker
from app.log_console import LogConsole
import config

class PlaceholderLineEdit(QLineEdit):
    def __init__(self, placeholder="DD-MM-YYYY", parent=None):
        super().__init__(parent)
        self._placeholder = placeholder
        self.setPlaceholderText(self._placeholder)

    def focusInEvent(self, event):
        self.setPlaceholderText("")
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        if not self.text():
            self.setPlaceholderText(self._placeholder)
        super().focusOutEvent(event)

class StartDateDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Enter Start Date")
        self.setObjectName("startDateDialog")
        self.resize(420, 280)
        
        self.setStyleSheet("""
            QDialog#startDateDialog {
                background-color: #15162b;
                color: #ffffff;
                border: 1px solid #2d2f52;
                border-radius: 8px;
            }
            QLabel {
                color: #ffffff;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Label text
        label = QLabel("Date of the first contact received in IndiaMART\n(or the oldest contact in Lead Manager):")
        label.setStyleSheet("font-weight: bold; color: #ffffff; font-size: 13px;")
        layout.addWidget(label)
        
        # Reason label
        reason_label = QLabel(
            "We need this date to start scraping from your oldest lead to the current date "
            "and avoid wasting time checking empty periods before your account was active.\n\n"
            "This date will be saved in the database; you will not be prompted for it again."
        )
        reason_label.setWordWrap(True)
        reason_label.setStyleSheet("color: #8f94fb; font-size: 11px; font-style: italic; line-height: 1.4;")
        layout.addWidget(reason_label)
        
        # Horizontal layout for the date text field and calendar button
        date_layout = QHBoxLayout()
        
        self.date_input = PlaceholderLineEdit("DD-MM-YYYY", self)
        
        # Regex to validate DD-MM-YYYY format (allow digits and dashes while typing)
        regex = QRegularExpression(r"^\d{0,2}-?\d{0,2}-?\d{0,4}$")
        self.date_input.setValidator(QRegularExpressionValidator(regex, self))
        
        self.date_input.setStyleSheet("""
            QLineEdit {
                background-color: #1e1f38;
                color: #ffffff;
                border: 1px solid #2d2f52;
                border-radius: 4px;
                padding: 8px;
                font-size: 13px;
            }
        """)
        date_layout.addWidget(self.date_input)
        
        # Calendar dropdown button
        self.calendar_btn = QPushButton("📅", self)
        self.calendar_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e1f38;
                color: #ffffff;
                border: 1px solid #2d2f52;
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #27294d;
                border-color: #4e54c8;
            }
        """)
        self.calendar_btn.clicked.connect(self.show_calendar)
        date_layout.addWidget(self.calendar_btn)
        
        layout.addLayout(date_layout)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            self
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        
        # Style buttons
        buttons.setStyleSheet("""
            QPushButton {
                background-color: #1e1f38;
                color: #ffffff;
                border: 1px solid #2d2f52;
                border-radius: 4px;
                padding: 6px 14px;
            }
            QPushButton:hover {
                background-color: #27294d;
                border-color: #4e54c8;
            }
        """)
        layout.addWidget(buttons)
 
    def show_calendar(self):
        dialog = QDialog(self)
        dialog.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        dialog.setStyleSheet("""
            QDialog {
                border: 1px solid #4e54c8;
                background-color: #15162b;
                border-radius: 6px;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(4, 4, 4, 4)
        
        calendar = QCalendarWidget(dialog)
        calendar.setGridVisible(False)
        calendar.setStyleSheet("""
            QCalendarWidget QWidget {
                background-color: #15162b;
                color: #ffffff;
                font-size: 11px;
            }
            QCalendarWidget QNodeToAnimate {
                background-color: #15162b;
            }
            QCalendarWidget QAbstractItemView:enabled {
                color: #ffffff;
                background-color: #15162b;
                selection-background-color: #4e54c8;
                selection-color: #ffffff;
            }
            QCalendarWidget QAbstractItemView:disabled {
                color: #444444;
            }
            QCalendarWidget QToolButton {
                color: #ffffff;
                background-color: #1e1f38;
                border: none;
                border-radius: 3px;
                padding: 4px;
            }
            QCalendarWidget QToolButton:hover {
                background-color: #27294d;
            }
            QCalendarWidget QMenu {
                background-color: #15162b;
                color: #ffffff;
            }
            QCalendarWidget QSpinBox {
                background-color: #1e1f38;
                color: #ffffff;
                border: 1px solid #2d2f52;
            }
        """)
        
        calendar.setMaximumDate(QDate.currentDate())
        calendar.setMinimumDate(QDate(2000, 1, 1))
        
        current_text = self.date_input.text().strip()
        if current_text:
            try:
                d, m, y = map(int, current_text.split("-"))
                calendar.setSelectedDate(QDate(y, m, d))
            except:
                pass
                
        layout.addWidget(calendar)
        
        def on_date_selected():
            qdate = calendar.selectedDate()
            self.date_input.setText(f"{qdate.day():02d}-{qdate.month():02d}-{qdate.year()}")
            dialog.accept()
            
        calendar.clicked.connect(on_date_selected)
        
        # Position the popup directly below the date_input
        local_bottom_left = self.date_input.rect().bottomLeft()
        global_pos = self.date_input.mapToGlobal(local_bottom_left)
        global_pos.setY(global_pos.y() + 4)
        
        dialog.move(global_pos)
        dialog.adjustSize()
        dialog.exec()
 
    def accept(self):
        text = self.date_input.text().strip()
        import datetime
        try:
            parsed = datetime.datetime.strptime(text, "%d-%m-%Y").date()
            if parsed > datetime.date.today():
                QMessageBox.warning(self, "Invalid Date", "The date cannot be in the future.")
                return
            super().accept()
        except:
            QMessageBox.warning(self, "Invalid Date", "Please enter a valid date in DD-MM-YYYY format.")
 
    def get_date(self):
        text = self.date_input.text().strip()
        import datetime
        return datetime.datetime.strptime(text, "%d-%m-%Y").date()

class CustomWebEnginePage(QWebEnginePage):
    def __init__(self, profile, parent=None):
        super().__init__(profile, parent)
        self.parent_window = parent

    def javaScriptConsoleMessage(self, level, message, line, sourceID):
        if self.parent_window and hasattr(self.parent_window, 'log_console'):
            self.parent_window.log_console.append_log(f"[Browser Console] {message} (Line: {line})")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(config.GUI_WINDOW_TITLE)
        
        # 1. Size window dynamically based on screen resolution (90% of available screen size)
        screen = QApplication.primaryScreen()
        if screen:
            geom = screen.availableGeometry()
            width = int(geom.width() * 0.90)
            height = int(geom.height() * 0.90)
            self.resize(width, height)
            
            # Center on screen
            x = (geom.width() - width) // 2
            y = (geom.height() - height) // 2
            self.move(x, y)
        else:
            self.resize(config.GUI_WINDOW_WIDTH, config.GUI_WINDOW_HEIGHT)

        # 2. Setup Persistent Profile & Anti-detection Script
        self.setup_web_profile()

        # 3. Setup central container with layout
        central_widget = QWidget(self)
        central_layout = QVBoxLayout(central_widget)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)
        self.setCentralWidget(central_widget)

        # Setup Guide Banner
        self.setup_guide_banner(central_layout)

        # Setup splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        central_layout.addWidget(splitter)

        # 4. Sidebar (Left panel)
        self.sidebar = Sidebar(self)
        self.sidebar.setMinimumWidth(0) # Allow shrinking to zero
        splitter.addWidget(self.sidebar)

        # 5. Web Engine View (Middle panel)
        self.web_view = QWebEngineView(self)
        self.web_page = CustomWebEnginePage(self.profile, self)
        self.web_view.setPage(self.web_page)
        splitter.addWidget(self.web_view)

        # 6. Log Console (Right panel)
        self.log_console = LogConsole(self)
        self.log_console.setMinimumWidth(0) # Allow shrinking to zero
        splitter.addWidget(self.log_console)

        # Set ratio: 260px sidebar, log console 300px, remainder for browser
        init_width = self.width()
        splitter.setSizes([260, init_width - 560, 300])

        # Enable panel collapsing
        splitter.setCollapsible(0, True)  # Sidebar can collapse
        splitter.setCollapsible(1, False) # Web browser cannot collapse
        splitter.setCollapsible(2, True)  # Log console can collapse

        # 7. Zoom Shortcuts Setup
        self.setup_zoom_shortcuts()

        # 8. Status Bar
        self.status_bar = StatusBar(self)
        self.setStatusBar(self.status_bar)

        # 6. JS Bridge setup (attached to web page)
        self.js_bridge = JSBridge(self.web_page)

        # 7. Connect Sidebar control signals
        self.sidebar.start_clicked.connect(self.start_scraping)
        self.sidebar.pause_clicked.connect(self.pause_scraping)
        self.sidebar.retry_clicked.connect(self.start_retry)

        # Scrape worker instance variable
        self.scrape_worker = None
        self.is_paused = False

        # Load target site
        self.status_bar.show_message(f"Loading {config.START_URL}...")
        self.log_console.append_log("Application UI initialized.")
        self.log_console.append_log("Persistent profile session directory verified.")
        self.log_console.append_log(f"Navigating browser to: {config.START_URL}")
        self.web_view.load(QUrl(config.START_URL))

        # Periodic timer to scan all contacts count if not already scanned
        self.web_page.loadFinished.connect(self.on_load_finished)

    def setup_web_profile(self):
        # Create user profile storage folder
        os.makedirs(config.GUI_SESSION_DIR, exist_ok=True)
        
        # Create persistent profile
        self.profile = QWebEngineProfile("indiamart_gui_profile", self)
        self.profile.setPersistentStoragePath(os.path.abspath(config.GUI_SESSION_DIR))
        self.profile.setCachePath(os.path.abspath(os.path.join(config.GUI_SESSION_DIR, "cache")))
        self.profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies)

        # Inject anti-detection headers script
        script = QWebEngineScript()
        script.setSourceCode("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            window.chrome = {
                runtime: {},
                loadTimes: function() {},
                csi: function() {},
                app: {}
            };
        """)
        script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
        script.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
        script.setRunsOnSubFrames(True)
        self.profile.scripts().insert(script)

    def on_load_finished(self, ok):
        if ok:
            self.status_bar.show_message("Website loaded successfully. Log in if needed.")
            self.log_console.append_log("Browser loaded target URL successfully.")
            # Scan total contacts count from UI
            self.scan_ui_contact_count()
        else:
            self.status_bar.show_message("Failed to load IndiaMART page.")
            self.log_console.append_log("Browser failed to load IndiaMART page.")

    def scan_ui_contact_count(self):
        # Helper check to read total contacts
        script = """
        (function() {
            var el = document.querySelector('.allCntText');
            return el ? el.innerText : null;
        })()
        """
        def cb(val):
            if val:
                import re
                match = re.search(r'\d+[,.\d]*', val)
                if match:
                    count = int(match.group().replace(',', '').replace('.', ''))
                    self.sidebar.update_all_contacts(count)
        self.web_page.runJavaScript(script, cb)

    def check_lead_manager_visible(self, callback):
        from app.js_bridge import JS_UTILS
        sel = config.LEFT_PANE_SCROLL_CONTAINER.replace('"', '\\"')
        script = JS_UTILS + f"""
        (function() {{
            try {{
                var el = _utils.getElement("{sel}");
                if (el !== null) return true;
                
                var cards = _utils.getElement("xpath=//div[contains(@class, 'lftcntctnew')]") || document.querySelector('.lftcntctnew');
                if (cards !== null) return true;
                
                var filterBtn = document.querySelector('#filterCTA');
                if (filterBtn !== null) return true;
            }} catch (e) {{}}
            return false;
        }})()
        """
        self.web_page.runJavaScript(script, callback)

    def start_scraping(self):
        if self.scrape_worker and self.scrape_worker.isRunning():
            if self.is_paused:
                self.is_paused = False
                self.scrape_worker.resume()
                self.sidebar.set_scraping_state(True)
                self.status_bar.show_message("Scraping resumed...")
                self.log_console.append_log("Scraping process resumed by user.")
            return

        def proceed_callback(is_lead_manager):
            if not is_lead_manager:
                QMessageBox.warning(self, "Action Required", 
                                    "Please log in to IndiaMART and load your Lead Manager page first.")
                return

            import db_manager
            import datetime
            
            # Check if initial start date already saved, or if previous scraping progress exists
            max_lead_date = db_manager.get_max_lead_date()
            initial_date_str = db_manager.get_initial_start_date()
            last_completed = db_manager.get_last_completed_period()
            
            selected_date = None
            
            if max_lead_date:
                selected_date = max_lead_date.replace(day=1)
                self.log_console.append_log(f"Resuming scraping from month of last scraped lead in database: {selected_date}")
            elif last_completed:
                try:
                    last_date = datetime.datetime.strptime(last_completed, "%Y-%m-%d").date()
                    if last_date.month == 12:
                        selected_date = last_date.replace(year=last_date.year + 1, month=1, day=1)
                    else:
                        selected_date = last_date.replace(month=last_date.month + 1, day=1)
                    self.log_console.append_log(f"Resuming scraping from last completed period: {selected_date}")
                except:
                    pass
            elif initial_date_str:
                try:
                    selected_date = datetime.datetime.strptime(initial_date_str, "%Y-%m-%d").date()
                    self.log_console.append_log(f"Resuming scraping from saved initial start date: {selected_date}")
                except:
                    pass
            
            # If no saved date or progress, prompt the user (only happens on first-time run)
            if not selected_date:
                dialog = StartDateDialog(self)
                if dialog.exec() != QDialog.DialogCode.Accepted:
                    self.log_console.append_log("Scraping cancelled: Start date is mandatory.")
                    return
                    
                selected_date = dialog.get_date()
                db_manager.set_initial_start_date(selected_date.strftime("%Y-%m-%d"))
                self.log_console.append_log(f"Saved initial start date to database: {selected_date}")

            self.is_paused = False
            self.scrape_worker = ScrapeWorker(self.js_bridge)
            self.scrape_worker.start_date_override = selected_date
            self.scrape_worker.retry_mode = False
            
            self.scrape_worker.lead_scraped.connect(self.on_lead_scraped)
            self.scrape_worker.status_message.connect(self.on_status_message)
            self.scrape_worker.all_contacts_found.connect(self.sidebar.update_all_contacts)
            self.scrape_worker.finished.connect(self.on_scrape_finished)
            self.scrape_worker.manual_filter_needed.connect(self.show_manual_filter_alert, Qt.ConnectionType.BlockingQueuedConnection)
            self.scrape_worker.log_message.connect(self.log_console.append_log)

            # Update GUI buttons
            self.sidebar.set_scraping_state(True)
            self.log_console.append_log("Initiating background scraping worker thread...")
            self.scrape_worker.start()

        self.check_lead_manager_visible(proceed_callback)

    def pause_scraping(self):
        if self.scrape_worker and self.scrape_worker.isRunning():
            self.is_paused = True
            self.scrape_worker.pause()
            self.sidebar.set_scraping_state(False)
            self.log_console.append_log("Scraping process paused by user request.")
            # Make sure start button is enabled to resume
            self.sidebar.start_btn.setEnabled(True)

    def start_retry(self):
        if self.scrape_worker and self.scrape_worker.isRunning():
            return

        def proceed_callback(is_lead_manager):
            if not is_lead_manager:
                QMessageBox.warning(self, "Action Required", 
                                    "Please log in to IndiaMART and load your Lead Manager page first.")
                return

            self.is_paused = False
            self.scrape_worker = ScrapeWorker(self.js_bridge)
            self.scrape_worker.retry_mode = True
            
            self.scrape_worker.lead_scraped.connect(self.on_lead_scraped)
            self.scrape_worker.status_message.connect(self.on_status_message)
            self.scrape_worker.finished.connect(self.on_scrape_finished)
            self.scrape_worker.manual_filter_needed.connect(self.show_manual_filter_alert, Qt.ConnectionType.BlockingQueuedConnection)
            self.scrape_worker.log_message.connect(self.log_console.append_log)

            self.sidebar.set_scraping_state(True)
            self.log_console.append_log("Initiating failed contacts retry thread...")
            self.scrape_worker.start()

        self.check_lead_manager_visible(proceed_callback)

    def on_lead_scraped(self, lead_data):
        self.sidebar.refresh_stats()

    def on_status_message(self, msg):
        self.status_bar.show_message(msg)

    def show_manual_filter_alert(self, start_date_str, end_date_str):
        from PyQt6.QtCore import QEventLoop
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Manual Date Filter Required")
        dialog.setWindowModality(Qt.WindowModality.NonModal) # Modeless dialog!
        dialog.resize(450, 300)
        
        dialog.setStyleSheet("""
            QDialog {
                background-color: #15162b;
                color: #ffffff;
                border: 1px solid #2d2f52;
                border-radius: 8px;
            }
            QLabel {
                color: #ffffff;
                font-size: 13px;
            }
            QPushButton {
                background-color: #1e1f38;
                color: #ffffff;
                border: 1px solid #2d2f52;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #27294d;
                border-color: #4e54c8;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Guide Header
        header = QLabel("Action Required: Apply Date Filter Manually")
        header.setStyleSheet("font-weight: bold; font-size: 15px; color: #ffc107;")
        layout.addWidget(header)
        
        # Instruction text (using HTML breaks for RichText rendering)
        instructions = (
            f"The calendar automation encountered an issue.<br><br>"
            f"<b>Please manually apply the custom date filter on the website:</b><br>"
            f"1. Click the Filter Icon (<b>#filterCTA</b>) at the top of the IndiaMART page.<br>"
            f"2. Go to the <b>'Filters'</b> tab and click the <b>'Date'</b> dropdown.<br>"
            f"3. Select <b>'Custom Date'</b>.<br>"
            f"4. Set the range: <b>{start_date_str}</b> to <b>{end_date_str}</b><br>"
            f"5. Click the <b>'Apply'</b> button.<br><br>"
            f"<i>(The browser behind this dialog is interactive. You can click on it now.)</i>"
        )
        label = QLabel()
        label.setTextFormat(Qt.TextFormat.RichText)
        label.setText(instructions)
        label.setWordWrap(True)
        layout.addWidget(label)
        
        # Button layout
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        resume_btn = QPushButton("Done, Resume Scraping")
        resume_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_layout.addWidget(resume_btn)
        
        layout.addLayout(btn_layout)
        
        # Setup event loop
        loop = QEventLoop()
        resume_btn.clicked.connect(loop.quit)
        dialog.finished.connect(lambda result: loop.quit())
        
        # Position dialog over the main window center
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()
        
        # Block the worker thread slot call by running the local event loop
        # This keeps the main GUI loop responsive to clicks/scrolls
        loop.exec()
        dialog.close()

    def on_scrape_finished(self):
        self.sidebar.set_scraping_state(False)
        self.sidebar.refresh_stats()
        self.status_bar.show_message("Scraping operation finished.")
        self.log_console.append_log("Background thread execution completed.")
        self.is_paused = False

    def closeEvent(self, event):
        if self.scrape_worker and self.scrape_worker.isRunning():
            self.scrape_worker.stop()
            self.scrape_worker.wait()
        event.accept()

    def setup_zoom_shortcuts(self):
        # Keyboard zoom shortcuts
        self.shortcut_zoom_in = QShortcut(QKeySequence("Ctrl++"), self)
        self.shortcut_zoom_in.activated.connect(self.zoom_in)

        self.shortcut_zoom_in_alt = QShortcut(QKeySequence("Ctrl+="), self)
        self.shortcut_zoom_in_alt.activated.connect(self.zoom_in)

        self.shortcut_zoom_out = QShortcut(QKeySequence("Ctrl+-"), self)
        self.shortcut_zoom_out.activated.connect(self.zoom_out)

        self.shortcut_zoom_reset = QShortcut(QKeySequence("Ctrl+0"), self)
        self.shortcut_zoom_reset.activated.connect(self.zoom_reset)

        # Mouse wheel zoom filter setup
        self.web_view.installEventFilter(self)
        if self.web_view.focusProxy():
            self.web_view.focusProxy().installEventFilter(self)

    def zoom_in(self):
        factor = self.web_page.zoomFactor()
        self.web_page.setZoomFactor(min(5.0, factor + 0.1))
        self.status_bar.show_message(f"Zoom level: {int(self.web_page.zoomFactor() * 100)}%")

    def zoom_out(self):
        factor = self.web_page.zoomFactor()
        self.web_page.setZoomFactor(max(0.25, factor - 0.1))
        self.status_bar.show_message(f"Zoom level: {int(self.web_page.zoomFactor() * 100)}%")

    def zoom_reset(self):
        self.web_page.setZoomFactor(1.0)
        self.status_bar.show_message("Zoom level reset to 100%")

    def eventFilter(self, watched, event):
        # Handle child additions dynamically to install filter on focusProxy
        if event.type() == event.Type.ChildAdded:
            child = event.child()
            if child:
                child.installEventFilter(self)
        
        # Capture mouse wheel events when Ctrl key is pressed
        if event.type() == event.Type.Wheel:
            if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                delta = event.angleDelta().y()
                if delta > 0:
                    self.zoom_in()
                else:
                    self.zoom_out()
                return True
        return super().eventFilter(watched, event)

    def setup_guide_banner(self, layout):
        self.guide_banner = QWidget(self)
        self.guide_banner.setObjectName("guideBanner")
        self.guide_banner.setFixedHeight(40) # Sleek, compact top bar height
        self.guide_banner.setStyleSheet("""
            QWidget#guideBanner {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #15162b, stop:1 #1e1f38);
                border-bottom: 2px solid #2d2f52;
            }
            QLabel {
                color: #ffffff;
                font-size: 12px;
            }
            QLabel#guideSteps {
                font-weight: 500;
            }
            QLabel#statusBadge {
                border-radius: 10px;
                padding: 3px 10px;
                font-weight: bold;
                font-size: 11px;
            }
        """)
        
        banner_layout = QHBoxLayout(self.guide_banner)
        banner_layout.setContentsMargins(15, 0, 15, 0)
        banner_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        # Left side: Icon & Steps description
        self.guide_steps = QLabel(
            "💡 <b>Guide:</b> 1. Log In to IndiaMART below "
            "➜ 2. Click <b>'Lead Manager'</b> or <b>'Messages'</b> on their sidebar "
            "➜ 3. Click <b>'Start Scrape'</b> on your left"
        )
        self.guide_steps.setObjectName("guideSteps")
        banner_layout.addWidget(self.guide_steps)
        
        banner_layout.addStretch()
        
        # Right side: Dynamic status badge
        self.status_badge = QLabel("🔴 Waiting for Lead Manager")
        self.status_badge.setObjectName("statusBadge")
        self.status_badge.setStyleSheet("""
            background-color: #e63946;
            color: #ffffff;
            border: 1px solid #ff4d6d;
            border-radius: 10px;
            padding: 3px 10px;
        """)
        banner_layout.addWidget(self.status_badge)
        
        layout.addWidget(self.guide_banner)
        
        # Setup periodic timer (every 2.5 seconds) to check status dynamically
        from PyQt6.QtCore import QTimer
        self.guide_timer = QTimer(self)
        self.guide_timer.timeout.connect(self.check_guide_status)
        self.guide_timer.start(2500)

    def check_guide_status(self):
        # Only scan if scraper is not currently running
        if self.scrape_worker and self.scrape_worker.isRunning():
            self.status_badge.setText("🟢 SCRAPING ACTIVE")
            self.status_badge.setStyleSheet("""
                background-color: #2a9d8f;
                color: #ffffff;
                border: 1px solid #48cae4;
                border-radius: 10px;
                padding: 3px 10px;
            """)
            return
            
        self.check_lead_manager_visible(self.update_guide_status)
        
    def update_guide_status(self, is_visible):
        if is_visible:
            self.status_badge.setText("🟢 Lead Manager Detected - Ready")
            self.status_badge.setStyleSheet("""
                background-color: #2a9d8f;
                color: #ffffff;
                border: 1px solid #48cae4;
                border-radius: 10px;
                padding: 3px 10px;
            """)
        else:
            self.status_badge.setText("🔴 Waiting for Lead Manager")
            self.status_badge.setStyleSheet("""
                background-color: #e63946;
                color: #ffffff;
                border: 1px solid #ff4d6d;
                border-radius: 10px;
                padding: 3px 10px;
            """)
