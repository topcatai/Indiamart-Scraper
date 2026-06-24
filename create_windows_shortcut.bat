@echo off
:: Windows Desktop Shortcut Creator for IndiaMART Lead Scraper
:: Created by Antigravity

setlocal enabledelayedexpansion

echo ==========================================================
echo       IndiaMART Lead Scraper Shortcut Creator
echo ==========================================================
echo.

set "TARGET_EXE=%~dp0dist\IndiaMartScraper\IndiaMartScraper.exe"
set "ICON_FILE=%~dp0app\assets\icon.png"

if not exist "!TARGET_EXE!" (
    echo [!] Warning: The compiled executable was not found at:
    echo     !TARGET_EXE!
    echo.
    echo     Please make sure to run the build script first:
    echo     python build_windows.py
    echo.
    echo     Creating shortcut anyway. It will become active once built.
    echo.
)

echo [*] Creating Desktop Shortcut...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut(\"$([Environment]::GetFolderPath('Desktop'))\IndiaMART Lead Scraper.lnk\"); $Shortcut.TargetPath = '%TARGET_EXE%'; $Shortcut.WorkingDirectory = '%~dp0dist\IndiaMartScraper'; $Shortcut.IconLocation = '%ICON_FILE%'; $Shortcut.Description = 'Launch IndiaMART Lead Scraper Desktop App'; $Shortcut.Save();"

if %ERRORLEVEL% equ 0 (
    echo [+] Success: 'IndiaMART Lead Scraper' shortcut has been created on your Desktop!
    echo     You can now double-click it to start the program without a terminal window.
) else (
    echo [!] Error: Failed to create the Desktop shortcut.
)

echo.
echo ==========================================================
