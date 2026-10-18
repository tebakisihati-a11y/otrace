# Otrace Installation Guide

Panduan lengkap menginstall semua tool keamanan untuk Otrace v2.0.

## Quick Start

```bash
cd "/Volumes/MORVEXA-CLOUD/SHARED-DATA/iCloud-Drive/Free cloud Host/otrace"

# Setup otomatis (recommended)
./bin/setup.sh

# Atau manual step-by-step di bawah
```

## Step 1: Install Homebrew (jika belum ada)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Setelah install, tambahkan ke PATH:
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

## Step 2: Install Security Tools

### Via Homebrew (recommended)

```bash
# Install semua tool sekaligus
brew install nmap nikto john the-ripper hydra aircrack-ng wireshark jadx ghidra

# Metasploit (lebih besar, install terpisah)
brew install metasploit

# OpenVAS/GVM (opsional, butuh waktu lama)
brew install gvm
```

### Via pip3 (untuk sqlmap)

```bash
pip3 install --user sqlmap

# Buat symlink ke ~/bin
mkdir -p ~/bin
ln -sf /Library/Frameworks/Python.framework/Versions/3.12/bin/sqlmap ~/bin/sqlmap

# Tambah ke PATH jika belum ada
echo 'export PATH="$HOME/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

## Step 3: Verify Installation

```bash
# Cek status semua tool
./bin/otrace doctor

# Atau daftar tool dengan status
./bin/otrace tools
```

## Tool Status & Alternatif Install

| Tool | Status Default | Cara Install |
|------|---------------|--------------|
| **ssh** | ✅ Pre-installed | Sudah ada di macOS/Linux |
| **sqlmap** | ⚠️ Pip install | `pip3 install sqlmap` |
| **nmap** | ❌ Brew install | `brew install nmap` |
| **nikto** | ❌ Brew install | `brew install nikto` |
| **john** | ❌ Brew install | `brew install john` |
| **hydra** | ❌ Brew install | `brew install hydra` |
| **metasploit** | ❌ Brew install | `brew install metasploit` |
| **aircrack-ng** | ❌ Brew install | `brew install aircrack-ng` |
| **tshark** | ❌ Brew install | `brew install wireshark` |
| **ghidra** | ❌ Manual download | https://ghidra-sre.org/ |
| **jadx** | ❌ Brew install | `brew install jadx` |
| **autopsy** | ❌ Manual download | https://www.autopsy.com/ |
| **openvas/gvm** | ❌ Brew install | `brew install gvm` |

## Manual Download (jika brew tidak tersedia)

### Ghidra
```bash
curl -L "https://github.com/NationalSecurityAgency/ghidra/releases/download/Ghidra_11.1.2_public/ghidra_11.1.2_20240624.zip" -o /tmp/ghidra.zip
unzip /tmp/ghidra.zip -d /opt/
ln -sf /opt/ghidra_11.1.2/ghidraRun /usr/local/bin/ghidra
```

### JADX
```bash
curl -L "https://github.com/skylot/jadx/releases/download/v1.5.0/jadx-1.5.0.zip" -o /tmp/jadx.zip
unzip /tmp/jadx.zip -d /opt/
ln -sf /opt/jadx-1.5.0/bin/jadx /usr/local/bin/jadx
```

### Autopsy
Download dari https://www.autopsy.com/download dan install manual.

## Verifikasi Final

```bash
# Running doctor check
./bin/otrace doctor

# Expected output:
# === OTRACE DOCTOR ===
# Home          : /Users/user/.otrace
# 9router app   : OK
# 9router MITM  : OK
# /etc/hosts    : intact
# port 443      : listening
# port 20128    : listening
# 
# === TOOLS ===
#   nmap         recon      OK /usr/local/bin/nmap
#   sqlmap       web        OK /Library/Frameworks/.../sqlmap
#   ssh          access     OK /usr/bin/ssh
#   ...

# Test dengan scan lokal (hanya jika Anda punya izin)
./bin/otrace scope --add "192.168.1.0/24"
./bin/otrace recon 192.168.1.1
```

## Troubleshooting

### "command not found: brew"
```bash
# Install Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### "command not found: sqlmap" setelah pip install
```bash
# Check location
which sqlmap || find /Library/Frameworks -name "sqlmap" 2>/dev/null

# Create symlink
ln -sf /Library/Frameworks/Python.framework/Versions/3.12/bin/sqlmap ~/bin/sqlmap
export PATH="$HOME/bin:$PATH"
```

### Otrace tidak mendeteksi tool yang sudah terinstall
```bash
# Check PATH
echo $PATH

# Verify binary location
which nmap
which sqlmap

# Update otrace config jika perlu
export PATH="/usr/local/bin:/opt/homebrew/bin:$PATH"
```

## Resources

- [Otrace GitHub](https://github.com/tebakisihati-a11y/otrace)
- [Nmap Download](https://nmap.org/download.html)
- [SQLMap GitHub](https://github.com/sqlmapproject/sqlmap)
- [Ghidra Download](https://ghidra-sre.org/)
- [JADX Release](https://github.com/skylot/jadx/releases)
