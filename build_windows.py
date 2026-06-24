import subprocess
import sys
import os

def build():
    print("[*] Checking for PyInstaller installation...")
    try:
        import PyInstaller
        print("[+] PyInstaller is already installed.")
    except ImportError:
        print("[!] Error: PyInstaller is not installed in your Python environment.")
        print("    Offline builds require PyInstaller to be pre-installed.")
        sys.exit(1)

            
    # PyInstaller command parameters
    # On Windows, path separator for add-data is semicolon ';'
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name=IndiaMartScraper",
        "--add-data=app/styles.qss;app",
        "--add-data=app/assets/icon.png;app/assets",
        "--clean",
        "app/main.py"
    ]
    
    print(f"[*] Executing PyInstaller command: {' '.join(cmd)}")
    try:
        subprocess.check_call(cmd)
        print("\n" + "="*50)
        print("[+] Windows build completed successfully!")
        print("Output directory: dist/IndiaMartScraper/")
        print("="*50)
    except Exception as e:
        print(f"[!] Build process failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    build()
