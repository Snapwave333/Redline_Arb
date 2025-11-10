#!/bin/bash
set -e

# Allow CI to override version via tag (e.g., v1.0.0)
if [ -n "$VERSION_OVERRIDE" ]; then
  VERSION=${VERSION_OVERRIDE#v}
else
  VERSION=$(python3 scripts/read_version.py)
fi
NAME="Redline_Arbitrage_${VERSION}_macOS_universal"
ICON="Redline_Arbitrage_Branding_Suite/Redline_Arbitrage_Branding/icons/Redline_Arbitrage.icns"

# Ensure an icon exists (fallback to generated icon if branding suite is missing)
if [ ! -f "$ICON" ]; then
  echo "Icon not found at $ICON. Generating a fallback .icns..."
  chmod +x scripts/create_macos_icon.sh
  scripts/create_macos_icon.sh || true
  if [ -f "build/Redline_Arbitrage.icns" ]; then
    ICON="build/Redline_Arbitrage.icns"
  else
    echo "Warning: No .icns available. Proceeding without explicit --icon."
    ICON=""
  fi
fi

# Clean previous builds
rm -rf build dist

# Ensure version resource is available in build folder
mkdir -p build
cp version.txt build/version.txt

# Build the macOS app bundle
PYI_CMD=(
  python -m PyInstaller
  --noconfirm --onedir --windowed
  --name "$NAME"
  --add-data "looks/themes:looks/themes"
  --add-data "looks/assets:looks/assets"
  --add-data "config:config"
  --version-file build/version.txt
  --hidden-import PyQt6.QtSvgWidgets
  --hidden-import PyQt6.QtGui
  --hidden-import PyQt6.QtWidgets
  --hidden-import PyQt6.QtCore
  --hidden-import PyQt6.QtNetwork
  --hidden-import PyQt6.QtDBus
  --hidden-import PyQt6.QtMultimedia
  --hidden-import PyQt6.QtMultimediaWidgets
  --hidden-import PyQt6.QtOpenGL
  --hidden-import PyQt6.QtOpenGLWidgets
  --hidden-import PyQt6.QtPdf
  --hidden-import PyQt6.QtPdfWidgets
  --hidden-import PyQt6.QtPositioning
  --hidden-import PyQt6.QtPrintSupport
  --hidden-import PyQt6.QtQml
  --hidden-import PyQt6.QtQuick
  --hidden-import PyQt6.QtQuick3D
  --hidden-import PyQt6.QtQuickWidgets
  --hidden-import PyQt6.QtRemoteObjects
  --hidden-import PyQt6.QtSensors
  --hidden-import PyQt6.QtSerialPort
  --hidden-import PyQt6.QtSpatialAudio
  --hidden-import PyQt6.QtSql
  --hidden-import PyQt6.QtStateMachine
  --hidden-import PyQt6.QtTest
  --hidden-import PyQt6.QtTextToSpeech
  --hidden-import PyQt6.QtWebChannel
  --hidden-import PyQt6.QtWebSockets
  --hidden-import PyQt6.QtXml
  --collect-submodules PyQt6
  --collect-data PyQt6
  --exclude-module pytest --exclude-module tests
)

# Optional icon
if [ -n "$ICON" ]; then
  PYI_CMD+=(--icon "$ICON")
fi

# Optional branding/social assets
if [ -d "Redline_Arbitrage_Branding_Suite/Redline_Arbitrage_Branding" ]; then
  PYI_CMD+=(--add-data "Redline_Arbitrage_Branding_Suite/Redline_Arbitrage_Branding:resources/branding")
fi
if [ -d "Redline_Arbitrage_Social_Kit" ]; then
  PYI_CMD+=(--add-data "Redline_Arbitrage_Social_Kit:resources/social_kit")
fi

# Entry point
PYI_CMD+=(main.py)

# Build the macOS app bundle
"${PYI_CMD[@]}"

echo "Done. Output: dist/$NAME.app"

# Create DMG for distribution (optional)
if command -v create-dmg &> /dev/null; then
    echo "Creating DMG..."
    DMG_NAME="Redline_Arbitrage_${VERSION}_macOS_universal.dmg"
    create-dmg \
        --volname "Redline Arbitrage" \
        $( [ -n "$ICON" ] && echo "--volicon \"$ICON\"" ) \
        --window-pos 200 120 \
        --window-size 800 400 \
        --icon-size 100 \
        --icon "${NAME}.app" 200 190 \
        --hide-extension "${NAME}.app" \
        --app-drop-link 600 185 \
        "$DMG_NAME" \
        "dist/"
    echo "DMG created: $DMG_NAME"
else
    echo "create-dmg not found. Install with: brew install create-dmg"
fi
