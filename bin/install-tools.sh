#!/usr/bin/env bash
# Otrace Tool Installer
# Menginstall semua tool keamanan yang opsional secara otomatis
# Menggunakan multiple fallback methods

set -euo pipefail

echo "=== Otrace Tool Installer ==="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

installed=0
failed=0
skipped=0

check_installed() {
    command -v "$1" >/dev/null 2>&1
}

install_status() {
    local tool="$1"
    local method="$2"
    local success="$3"
    
    if [ "$success" = "true" ]; then
        echo -e "${GREEN}✓${NC} $tool ($method)"
        ((installed++))
    else
        echo -e "${YELLOW}⚠${NC} $tool - tidak bisa install otomatis"
        ((skipped++))
    fi
}

# Method 1: Homebrew
try_brew() {
    local cmd="brew"
    if check_installed "$cmd"; then
        echo "Menggunakan Homebrew..."
        return 0
    fi
    return 1
}

# Method 2: pip3
try_pip() {
    local cmd="pip3"
    if check_installed "$cmd"; then
        echo "Menggunakan pip3..."
        return 0
    fi
    return 1
}

# Method 3: Download from GitHub
try_download() {
    local url="$1"
    local dest="$2"
    
    if check_installed curl; then
        echo "Downloading $dest..."
        curl -L "$url" -o "/tmp/$dest.tar.gz" 2>/dev/null && return 0
    fi
    return 1
}

# Install function with multiple fallbacks
install_tool() {
    local tool="$1"
    local brew_formula="$2"
    local pip_package="$3"
    local github_url="$4"
    local binary_name="${5:-$tool}"
    
    echo -n "Installing $tool... "
    
    # Try brew first
    if try_brew; then
        if brew install "$brew_formula" 2>/dev/null && check_installed "$binary_name"; then
            install_status "$tool" "brew" "true"
            return
        fi
    fi
    
    # Try pip3
    if try_pip; then
        if pip3 install "$pip_package" 2>/dev/null && check_installed "$binary_name"; then
            install_status "$tool" "pip3" "true"
            return
        fi
    fi
    
    # Try direct download
    if [ -n "$github_url" ]; then
        if try_download "$github_url" "$tool"; then
            echo "Download failed, try manual install"
        fi
    fi
    
    install_status "$tool" "manual" "false"
}

echo ""
echo "Checking current installation..."
echo ""

# Check what's already installed
for tool in nmap sqlmap nikto john hydra metasploit aircrack-ng tshark autopsy ghidra jadx; do
    if check_installed "$tool"; then
        echo -e "${GREEN}✓${NC} $tool sudah terpasang"
    fi
done

echo ""
echo "Installing missing tools..."
echo ""

# Install each tool
install_tool "nmap" "nmap" "" "" "nmap"
install_tool "sqlmap" "" "sqlmap" "" "sqlmap"
install_tool "nikto" "nikto" "" "" "nikto"
install_tool "john" "john" "" "" "john"
install_tool "hydra" "hydra" "" "" "hydra"
install_tool "metasploit" "metasploit" "" "" "msfconsole"
install_tool "aircrack-ng" "aircrack-ng" "" "" "aircrack-ng"
install_tool "tshark" "wireshark" "" "" "tshark"
install_tool "autopsy" "autopsy" "" "" "autopsy"
install_tool "ghidra" "ghidra" "" "" "ghidra"
install_tool "jadx" "jadx" "" "" "jadx"

echo ""
echo "=== Installation Summary ==="
echo "Installed: $installed"
echo "Skipped (need manual install): $skipped"
echo ""

# Verify final status
echo "Final tool status:"
./bin/otrace tools 2>&1 | grep -E "^(nmap|sqlmap|nikto|john|hydra|metasploit|aircrack|tshark|autopsy|ghidra|jadx)" || true

echo ""
echo "Selesai! Jalankan './bin/otrace doctor' untuk verifikasi."
