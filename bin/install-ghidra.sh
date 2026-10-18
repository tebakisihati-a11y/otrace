#!/bin/bash
# Install ghidra — download and extract to ~/ghidra
set -e

GHIDRA_VERSION="12.1.4"
GHIDRA_URL="https://github.com/NationalSecurityAgency/ghidra/releases/download/Ghidra_${GHIDRA_VERSION}_build/ghidra_${GHIDRA_VERSION}_PUBLIC_20260921.zip"
INSTALL_DIR="$HOME/ghidra"

echo "Downloading Ghidra ${GHIDRA_VERSION}..."
curl -sL -o /tmp/ghidra.zip "$GHIDRA_URL"

echo "Extracting..."
rm -rf "$INSTALL_DIR"
unzip -q /tmp/ghidra.zip -d /tmp/
mv /tmp/ghidra_${GHIDRA_VERSION}_PUBLIC "$INSTALL_DIR"

echo "Ghidra installed to $INSTALL_DIR"
echo "Run: ghidra <target>"
