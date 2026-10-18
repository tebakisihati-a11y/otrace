#!/usr/bin/env bash
# Install scripts untuk semua optional tools
# Menggunakan multiple methods: pip, direct download, manual

set -euo pipefail

echo "=== Otrace Tool Install Scripts ==="
echo ""

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

check_cmd() {
    command -v "$1" >/dev/null 2>&1
}

# Check existing installations
echo "Checking current tool status..."
echo ""

for tool in nmap sqlmap nikto john hydra metasploit aircrack-ng tshark ghidra jadx; do
    if check_cmd "$tool"; then
        echo -e "${GREEN}✓${NC} $tool: $(which $tool)"
    else
        echo -e "${YELLOW}⚠${NC} $tool: not found"
    fi
done

echo ""
echo "=========================================="
echo "  Installation Methods"
echo "=========================================="
echo ""

# Method 1: pip3 (for Python-based tools)
echo "Method 1: pip3 (recommended for sqlmap)"
echo "-------------------------------------------"
if ! check_cmd sqlmap; then
    echo "Installing sqlmap via pip3..."
    pip3 install --user sqlmap
    
    # Find and symlink
    SQLMAP_PATH=$(find /Library/Frameworks/Python.framework -name "sqlmap" -type f 2>/dev/null | head -1)
    if [ -n "$SQLMAP_PATH" ]; then
        mkdir -p ~/bin
        ln -sf "$SQLMAP_PATH" ~/bin/sqlmap
        echo -e "${GREEN}✓${NC} sqlmap installed at $SQLMAP_PATH"
        echo "  Symlinked to ~/bin/sqlmap"
    fi
else
    echo -e "${GREEN}✓${NC} sqlmap already installed"
fi

echo ""

# Method 2: Direct download for tools without brew
echo "Method 2: Direct download (for tools without package manager)"
echo "-------------------------------------------"

# JADX
if ! check_cmd jadx; then
    echo "Installing JADX..."
    JADX_VERSION="1.5.0"
    JADX_URL="https://github.com/skylot/jadx/releases/download/v${JADX_VERSION}/jadx-${JADX_VERSION}.zip"
    
    cd /tmp
    curl -L "$JADX_URL" -o "jadx.zip" 2>/dev/null
    if [ -f "jadx.zip" ]; then
        unzip -q "jadx.zip" -d /opt/
        ln -sf "/opt/jadx-${JADX_VERSION}/bin/jadx" /usr/local/bin/jadx 2>/dev/null || \
        ln -sf "/opt/jadx-${JADX_VERSION}/bin/jadx" ~/bin/jadx 2>/dev/null || true
        echo -e "${GREEN}✓${NC} JADX installed"
    else
        echo -e "${RED}✗${NC} Failed to download JADX"
    fi
    cd - >/dev/null
else
    echo -e "${GREEN}✓${NC} JADX already installed"
fi

echo ""

# Nmap
if ! check_cmd nmap; then
    echo "Installing Nmap..."
    # Try downloading pre-built binary
    NMAP_URL="https://nmap.org/dist/nmap-7.94-osx-universal-app.dmg"
    cd /tmp
    curl -L "$NMAP_URL" -o "nmap.dmg" 2>/dev/null
    if [ -f "nmap.dmg" ]; then
        hdiutil attach "nmap.dmg" -quiet
        cp -R /Volumes/nmap*/*.app /Applications/ 2>/dev/null || true
        hdiutil detach /Volumes/nmap* -quiet 2>/dev/null || true
        echo -e "${YELLOW}⚠${NC} Nmap DMG downloaded - open /Applications/nmap*.app and drag to Applications"
    else
        echo -e "${YELLOW}⚠${NC} Nmap download failed. Manual install required:"
        echo "  Download: https://nmap.org/download.html"
        echo "  Or: brew install nmap (if brew available)"
    fi
    cd - >/dev/null
else
    echo -e "${GREEN}✓${NC} Nmap already installed"
fi

echo ""

# Nikto
if ! check_cmd nikto; then
    echo "Installing Nikto..."
    echo -e "${YELLOW}⚠${NC} Nikto requires manual installation:"
    echo "  Method 1: brew install nikto"
    echo "  Method 2: git clone https://github.com/sullo/nikto.git /opt/nikto"
    echo "  Method 3: Download from http://cirt.net/nikto"
    
    # Try git clone as fallback
    if check_cmd git; then
        echo "  Trying git clone..."
        if [ ! -d "/opt/nikto" ]; then
            git clone --depth 1 https://github.com/sullo/nikto.git /opt/nikto 2>/dev/null && \
            ln -sf /opt/nikto/nikto /usr/local/bin/nikto 2>/dev/null || true
            if check_cmd nikto; then
                echo -e "${GREEN}✓${NC} Nikto installed via git"
            fi
        fi
    fi
fi

echo ""

# John the Ripper
if ! check_cmd john; then
    echo "Installing John the Ripper..."
    echo -e "${YELLOW}⚠${NC} John requires manual installation:"
    echo "  Method 1: brew install john"
    echo "  Method 2: Download from https://www.openwall.com/john/"
    
    # Try downloading from openwall
    if [ ! -d "/opt/john" ]; then
        cd /tmp
        curl -L "https://www.openwall.com/john/g/john-1.9.0-jumbo-1.tar.xz" -o "john.tar.xz" 2>/dev/null || \
        curl -L "https://github.com/openwall/john/releases/download/rockyou-3.0/john-1.9.0.tar.xz" -o "john.tar.xz" 2>/dev/null
        
        if [ -f "john.tar.xz" ]; then
            tar xJf "john.tar.xz"
            mv john-* /opt/john 2>/dev/null || true
            ln -sf /opt/john/run/john /usr/local/bin/john 2>/dev/null || true
            if check_cmd john; then
                echo -e "${GREEN}✓${NC} John installed"
            fi
        fi
        cd - >/dev/null
    fi
fi

echo ""
echo "=========================================="
echo "  Summary"
echo "=========================================="
echo ""

# Final status check
installed=0
missing=0

for tool in nmap sqlmap nikto john hydra metasploit aircrack-ng tshark ghidra jadx; do
    if check_cmd "$tool"; then
        ((installed++))
    else
        echo -e "${YELLOW}Missing:${NC} $tool"
        ((missing++))
    fi
done

echo ""
echo "Installed: $installed/10"
echo "Missing: $missing/10"
echo ""
echo "To install missing tools:"
echo "  1. Install Homebrew: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
echo "  2. Then: brew install nmap nikto john hydra aircrack-ng wireshark ghidra metasploit"
echo ""
