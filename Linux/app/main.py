import os
import sys
from PyQt6.QtWidgets import QApplication
from app.main_window import MainWindow

def main():
    # Windows high-DPI scaling configuration for crisp text rendering
    if sys.platform == 'win32':
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception as dpi_err:
            print(f"[!] Warning: DPI awareness setup failed: {dpi_err}")
            
    app = QApplication(sys.argv)
    
    # Load and apply stylesheet
    qss_path = os.path.join(os.path.dirname(__file__), "styles.qss")
    if os.path.exists(qss_path):
        try:
            with open(qss_path, "r", encoding="utf-8") as f:
                app.setStyleSheet(f.read())
        except Exception as qss_err:
            print(f"[!] Warning: Could not load stylesheet: {qss_err}")
            
    # Initialize DB first to ensure setting tables exist
    import db_manager
    db_manager.init_db()

    # Check if safety guidelines have been accepted
    if not db_manager.is_safety_accepted():
        from app.safety_dialog import SafetyDialog
        dialog = SafetyDialog()
        if dialog.exec() == SafetyDialog.DialogCode.Accepted:
            db_manager.mark_safety_accepted()
        else:
            sys.exit(0)

    # Instantiate and show main dashboard window
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
