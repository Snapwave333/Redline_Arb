#!/bin/bash
set -e

# Generate SHA256 checksums for release artifacts
# Usage: ./generate_checksums.sh [directory]

CHECKSUM_DIR=${1:-"release_assets"}
OUTPUT_FILE="${CHECKSUM_DIR}/checksums.txt"

echo "Generating checksums for files in: $CHECKSUM_DIR"

# Create checksums file
echo "# SHA256 Checksums for Redline Arbitrage Release" > "$OUTPUT_FILE"
echo "# Generated on $(date -u '+%Y-%m-%d %H:%M:%S UTC')" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# Find all relevant files and generate checksums
find "$CHECKSUM_DIR" -type f \( \
    -name "*.exe" -o \
    -name "*.dmg" -o \
    -name "*.zip" -o \
    -name "*.deb" -o \
    -name "*.rpm" -o \
    -name "*.AppImage" \
\) -not -name "checksums.txt*" | sort | while read -r file; do
    if [[ -f "$file" ]]; then
        if command -v sha256sum &> /dev/null; then
            checksum=$(sha256sum "$file" | cut -d' ' -f1)
        else
            checksum=$(shasum -a 256 "$file" | cut -d' ' -f1)
        fi
        filename=$(basename "$file")
        echo "SHA256 ($filename) = $checksum" >> "$OUTPUT_FILE"
    fi
done

echo "" >> "$OUTPUT_FILE"
echo "# Verify with: sha256sum -c checksums.txt" >> "$OUTPUT_FILE"

echo "Checksums generated: $OUTPUT_FILE"
cat "$OUTPUT_FILE"
