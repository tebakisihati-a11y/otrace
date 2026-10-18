# Panduan Instalasi Otrace

## Prerequisites

- Python 3.10+
- Podman (untuk tool wrappers)
- pip3

## Instalasi Cepat

```bash
# Clone repository
git clone https://github.com/tebakisihati-a11y/otrace.git
cd otrace

# Install Python package
pip3 install -e .

# Install semua tool wrappers (Podman-based)
./bin/install-tools.sh

# Install ghidra (manual, ~540MB)
./bin/install-ghidra.sh
```

## Tool Status

| Tool | Metode | Status |
|------|--------|--------|
| nmap | Podman Alpine | ✅ Auto |
| sqlmap | pip3 | ✅ Auto |
| nikto | Perl wrapper | ✅ Auto |
| hydra | Podman Alpine | ✅ Auto |
| john | Podman Alpine | ✅ Auto |
| aircrack-ng | Podman Alpine | ✅ Auto |
| tshark | Podman Alpine (pre-built image) | ✅ Auto |
| jadx | Podman eclipse-temurin (Java 17) | ✅ Auto |
| ghidra | Podman eclipse-temurin (Java 17) | ⚠️ Manual (~540MB) |
| ssh | Native macOS | ✅ |
| openvas | Manual | ⚠️ |
| metasploit | Manual | ⚠️ |
| autopsy | Manual | ⚠️ |
| gvm | Manual | ⚠️ |

## Verifikasi

```bash
# Cek semua tool
python3 -m otrace tools --list

# Cek tool terdeteksi
python3 -c "from otrace.tools import detect_all; import json; print(json.dumps(detect_all(), indent=2))"

# Jalankan tests
python3 -m pytest -v
```

## Troubleshooting

### Podman tidak jalan
```bash
podman machine start
podman machine init  # jika belum ada
```

### Permission denied di ~/bin
```bash
chmod +x ~/bin/*
```

### Tool wrapper gagal
Setiap wrapper adalah script bash di `~/bin/`. Cek manual:
```bash
cat ~/bin/nmap
~/bin/nmap --version
```
