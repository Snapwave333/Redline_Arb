#!/bin/bash
set -e

# Create macOS .icns icon from PNG logo
# Requires ImageMagick (brew install imagemagick) or macOS built-in sips

# Prefer branding PNG if available, otherwise fall back to known repo assets
INPUT_PNG="Redline_Arbitrage_Branding_Suite/Redline_Arbitrage_Branding/logos/horizontal.png"
if [ ! -f "$INPUT_PNG" ]; then
    if [ -f "GitHub_README_Assets/social_preview.png" ]; then
        INPUT_PNG="GitHub_README_Assets/social_preview.png"
        echo "Branding PNG not found, using GitHub_README_Assets/social_preview.png as source."
    elif [ -f "mobile_web_app/public/RL_full.png" ]; then
        INPUT_PNG="mobile_web_app/public/RL_full.png"
        echo "Branding PNG not found, using mobile_web_app/public/RL_full.png as source."
    else
        echo "Error: No suitable PNG source found for icon generation."
        exit 1
    fi
fi

OUTPUT_ICNS="Redline_Arbitrage_Branding_Suite/Redline_Arbitrage_Branding/icons/Redline_Arbitrage.icns"
# Also produce a copy in build for local consumption if branding path doesn't exist
BUILD_ICNS="build/Redline_Arbitrage.icns"

# Prepare output directories
mkdir -p "$(dirname "$OUTPUT_ICNS")"
mkdir -p "$(dirname "$BUILD_ICNS")"

# Use a workspace-local iconset directory
TEMP_DIR="$PWD/build/icon.iconset"

# Clean up any existing files
rm -f "$OUTPUT_ICNS" "$BUILD_ICNS"
rm -rf "$TEMP_DIR"

# Create iconset directory
mkdir -p "$TEMP_DIR"

# Check if ImageMagick is available
if command -v magick &> /dev/null; then
    echo "Using ImageMagick to create iconset..."

    # Create different sizes for iconset
    magick "$INPUT_PNG" -resize 16x16 "$TEMP_DIR/icon_16x16.png"
    magick "$INPUT_PNG" -resize 32x32 "$TEMP_DIR/icon_16x16@2x.png"
    magick "$INPUT_PNG" -resize 32x32 "$TEMP_DIR/icon_32x32.png"
    magick "$INPUT_PNG" -resize 64x64 "$TEMP_DIR/icon_32x32@2x.png"
    magick "$INPUT_PNG" -resize 128x128 "$TEMP_DIR/icon_128x128.png"
    magick "$INPUT_PNG" -resize 256x256 "$TEMP_DIR/icon_128x128@2x.png"
    magick "$INPUT_PNG" -resize 256x256 "$TEMP_DIR/icon_256x256.png"
    magick "$INPUT_PNG" -resize 512x512 "$TEMP_DIR/icon_256x256@2x.png"
    magick "$INPUT_PNG" -resize 512x512 "$TEMP_DIR/icon_512x512.png"
    magick "$INPUT_PNG" -resize 1024x1024 "$TEMP_DIR/icon_512x512@2x.png"

elif command -v sips &> /dev/null; then
    echo "Using macOS sips to create iconset..."

    # Create different sizes using sips
    sips -z 16 16 "$INPUT_PNG" --out "$TEMP_DIR/icon_16x16.png"
    sips -z 32 32 "$INPUT_PNG" --out "$TEMP_DIR/icon_16x16@2x.png"
    sips -z 32 32 "$INPUT_PNG" --out "$TEMP_DIR/icon_32x32.png"
    sips -z 64 64 "$INPUT_PNG" --out "$TEMP_DIR/icon_32x32@2x.png"
    sips -z 128 128 "$INPUT_PNG" --out "$TEMP_DIR/icon_128x128.png"
    sips -z 256 256 "$INPUT_PNG" --out "$TEMP_DIR/icon_128x128@2x.png"
    sips -z 256 256 "$INPUT_PNG" --out "$TEMP_DIR/icon_256x256.png"
    sips -z 512 512 "$INPUT_PNG" --out "$TEMP_DIR/icon_256x256@2x.png"
    sips -z 512 512 "$INPUT_PNG" --out "$TEMP_DIR/icon_512x512.png"
    sips -z 1024 1024 "$INPUT_PNG" --out "$TEMP_DIR/icon_512x512@2x.png"

else
    echo "Error: Neither ImageMagick (magick) nor macOS sips found."
    echo "Install ImageMagick with: brew install imagemagick"
    exit 1
fi

# Convert iconset to icns
if command -v iconutil &> /dev/null; then
    echo "Converting iconset to .icns..."
    iconutil -c icns "$TEMP_DIR" -o "$OUTPUT_ICNS"
    # Also write a copy to build for scripts that expect a local path
    cp "$OUTPUT_ICNS" "$BUILD_ICNS" || true
    echo "Created: $OUTPUT_ICNS"
else
    echo "Error: iconutil not found. This script must be run on macOS."
    exit 1
fi

# Clean up
rm -rf "$TEMP_DIR"

echo "macOS icon creation complete!"
