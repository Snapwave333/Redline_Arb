@echo off
setlocal enabledelayedexpansion

REM Read version from file
if defined VERSION_OVERRIDE (
  set VERSION=%VERSION_OVERRIDE:v=%
) else (
  for /f %%V in ('python scripts\read_version.py') do set VERSION=%%V
)
set NAME=Redline_Arbitrage_%VERSION%_Windows_x64
set ICON=Redline_Arbitrage_Branding_Suite\Redline_Arbitrage_Branding\icons\Redline_Arbitrage.ico
set ICON_SWITCH=
if exist "%ICON%" (
  set ICON_SWITCH=--icon "%ICON%"
) else (
  echo Icon not found at %ICON%. Proceeding without explicit --icon.
)

rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul

REM Ensure version resource is available in build folder
mkdir build 2>nul
copy /Y version.txt build\version.txt >nul

REM Conditionally include optional asset folders
set BRANDING_SWITCH=
if exist "Redline_Arbitrage_Branding_Suite\Redline_Arbitrage_Branding" (
  set BRANDING_SWITCH=--add-data "Redline_Arbitrage_Branding_Suite\\Redline_Arbitrage_Branding;resources\\branding"
)
set SOCIAL_SWITCH=
if exist "Redline_Arbitrage_Social_Kit" (
  set SOCIAL_SWITCH=--add-data "Redline_Arbitrage_Social_Kit;resources\\social_kit"
)

python -m PyInstaller ^
  --noconfirm --onedir --windowed ^
  --name %NAME% ^
  %ICON_SWITCH% ^
  --add-data "looks/themes;looks/themes" ^
  --add-data "looks/assets;looks/assets" ^
  --add-data "config;config" ^
  %BRANDING_SWITCH% ^
  %SOCIAL_SWITCH% ^
  --version-file build\version.txt ^
  --hidden-import PyQt6.QtSvgWidgets ^
  --hidden-import PyQt6.QtGui ^
  --hidden-import PyQt6.QtWidgets ^
  --hidden-import PyQt6.QtCore ^
  --hidden-import PyQt6.QtNetwork ^
  --hidden-import PyQt6.QtDBus ^
  --hidden-import PyQt6.QtMultimedia ^
  --hidden-import PyQt6.QtMultimediaWidgets ^
  --hidden-import PyQt6.QtOpenGL ^
  --hidden-import PyQt6.QtOpenGLWidgets ^
  --hidden-import PyQt6.QtPdf ^
  --hidden-import PyQt6.QtPdfWidgets ^
  --hidden-import PyQt6.QtPositioning ^
  --hidden-import PyQt6.QtPrintSupport ^
  --hidden-import PyQt6.QtQml ^
  --hidden-import PyQt6.QtQuick ^
  --hidden-import PyQt6.QtQuick3D ^
  --hidden-import PyQt6.QtQuickWidgets ^
  --hidden-import PyQt6.QtRemoteObjects ^
  --hidden-import PyQt6.QtSensors ^
  --hidden-import PyQt6.QtSerialPort ^
  --hidden-import PyQt6.QtSpatialAudio ^
  --hidden-import PyQt6.QtSql ^
  --hidden-import PyQt6.QtStateMachine ^
  --hidden-import PyQt6.QtTest ^
  --hidden-import PyQt6.QtTextToSpeech ^
  --hidden-import PyQt6.QtWebChannel ^
  --hidden-import PyQt6.QtWebSockets ^
  --hidden-import PyQt6.QtXml ^
  --collect-submodules PyQt6 ^
  --collect-data PyQt6 ^
  --exclude-module pytest --exclude-module tests ^
  main.py

echo Done. Output: dist\%NAME%.exe
