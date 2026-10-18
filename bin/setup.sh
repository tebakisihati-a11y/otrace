#!/usr/bin/env bash
# Otrace Complete Setup Script
# Menginstall semua dependencies yang diperlukan

set -euo pipefail

echo "=========================================="
echo "  Otrace Complete Setup"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

STEP=0
total_steps=5

next_step() {
    ((STEP++))
    echo ""
    echo -e "${BLUE}[Step $STEP/$total_steps]${NC} $1"
    echo "-------------------------------------------"
}

check_cmd() {
    command -v "$1" >/dev/null 2>&1
}

# Step 1: Check prerequisites
next_step "Checking prerequisites..."

if ! check_cmd python3; then
    echo -e "${RED}ERROR: python3 not found${NC}"
    echo "Install Python 3.12+ from https://www.python.org/downloads/"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
echo "✓ Python $PYTHON_VERSION"

if ! check_cmd pip3; then
    echo -e "${YELLOW}WARNING: pip3 not found, installing...${NC}"
    curl https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py
    python3 /tmp/get-pip.py
fi
echo "✓ pip3 ready"

if ! check_cmd git; then
    echo -e "${YELLOW}WARNING: git not found${NC}"
    echo "Install git: https://git-scm.com/download/mac"
fi

# Step 2: Install Python dependencies
next_step "Installing Python dependencies..."

pip3 install --user sqlmap 2>&1 | tail -3
echo "✓ sqlmap installed"

# Create symlinks for Python-installed tools
mkdir -p ~/bin
if [ -f "/Library/Frameworks/Python.framework/Versions/3.12/bin/sqlmap" ]; then
    ln -sf "/Library/Frameworks/Python.framework/Versions/3.12/bin/sqlmap" ~/bin/sqlmap
    echo "✓ sqlmap symlink created"
fi

# Add ~/bin to PATH if not already there
if [[ ":$PATH:" != *":$HOME/bin:"* ]]; then
    echo "export PATH=\"\$HOME/bin:\$PATH\"" >> ~/.zshrc
    echo "export PATH=\"\$HOME/bin:\$PATH\"" >> ~/.bash_profile 2>/dev/null || true
    echo "✓ Added ~/bin to PATH (restart terminal or run: source ~/.zshrc)"
fi

# Step 3: Check/install Homebrew
next_step "Checking Homebrew..."

if check_cmd brew; then
    echo "✓ Homebrew already installed"
else
    echo -e "${YELLOW}Homebrew not found. Installing...${NC}"
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Add to PATH
    if [[ -d /opt/homebrew/bin ]]; then
        echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
        eval "$(/opt/homebrew/bin/brew shellenv)"
    elif [[ -d /usr/local/Homebrew/bin ]]; then
        echo 'eval "$(/usr/local/Homebrew/bin/brew shellenv)"' >> ~/.zprofile
        eval "$(/usr/local/Homebrew/bin/brew shellenv)"
    fi
    echo "✓ Homebrew installed"
fi

# Step 4: Install tools via Homebrew
next_step "Installing security tools via Homebrew..."

tools_to_install="nmap nikto john the-ripper aircrack-ng wireshark macports jadx ghidra"
already_installed=()
to_install=()

for tool in $tools_to_install; do
    case $tool in
        "john") actual="john-the-ripper" ;;
        "wireshark") actual="tshark" ;;
        *) actual=$tool ;;
    esac
    
    if check_cmd $tool || check_cmd $actual; then
        already_installed+=("$tool")
    else
        to_install+=("$tool")
    fi
done

if [ ${#already_installed[@]} -gt 0 ]; then
    echo "✓ Already installed: ${already_installed[*]}"
fi

if [ ${#to_install[@]} -gt 0 ]; then
    echo "Installing: ${to_install[*]}"
    brew install "${to_install[@]}" 2>&1 | tail -20
    echo "✓ Tools installed"
else
    echo "All tools already installed!"
fi

# Step 5: Verification
next_step "Verifying installation..."

echo ""
echo "Tool Status:"
echo "------------"

declare -A tool_map=(
    ["nmap"]="nmap"
    ["sqlmap"]="sqlmap"
    ["nikto"]="nikto"
    ["john"]="john"
    ["hydra"]="hydra"
    ["metasploit"]="msfconsole"
    ["aircrack"]="aircrack-ng"
    ["tshark"]="tshark"
    ["autopsy"]="autopsy"
    ["ghidra"]="ghidra"
    ["jadx"]="jadx"
)

for tool in "${!tool_map[@]}"; do
    cmd="${tool_map[$tool]}"
    if check_cmd "$cmd"; then
        version=$($cmd --version 2>&1 | head -1 | grep -oE '[0-9]+\.[0-9]+(\.[0-9]+)?' | head -1)
        echo -e "  ${GREEN}✓${NC} $tool ($cmd) $version"
    else
        echo -e "  ${YELLOW}⚠${NC} $tool - not installed"
    fi
done

echo ""
echo "=========================================="
echo -e "${GREEN}Setup complete!${NC}"
echo ""
echo "Run './bin/otrace doctor' to verify everything works."
echo "Or visit: https://tebakisihati-a11y.github.io/otrace/"
echo "=========================================="
