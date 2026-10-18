# Otrace — Powerful Cybersecurity Suite (9router-safe)

CLI yang menggabungkan 14+ tools keamanan siber ke dalam satu alur kerja konsisten, dengan jaminan **tidak mengganggu 9router**.

## Features Baru v2.0

- **Report Generator** — Output JSON, Markdown, SARIF (GitHub), dan CSV untuk setiap run
- **CIDR Scope** — Scope checking support subnet notation (192.168.1.0/24)
- **Plugin System** — Tambah tool kustom dengan plugin JSON
- **Scheduled Scans** — Jadwalkan scan otomatis dengan cron
- **Progress Streaming** — Output tool ditampilkan real-time ke console
- **CI/CD** — GitHub Actions untuk test & lint otomatis
- **Premium UI** — Halaman web modern dengan dark mode support

## Tools Terintegrasi

| Tool | Kategori | Status Default |
|------|----------|----------------|
| nmap | Recon | Opsional |
| sqlmap | Web | Opsional |
| nikto | Web | Opsional |
| ssh | Access | Pre-installed |
| john | Password | Opsional |
| hydra | Password | Opsional |
| metasploit | Exploit | Opsional |
| openvas/gvm | Vulnerability | Opsional |
| aircrack-ng | Wireless | Opsional |
| tshark | Network | Opsional |
| autopsy | Forensics | Opsional |
| ghidra | Reverse | Opsional |
| jadx | Reverse | Opsional |

## Instalasi

```bash
cd "/Volumes/MORVEXA-CLOUD/SHARED-DATA/iCloud-Drive/Free cloud Host/otrace"
chmod +x bin/otrace
./bin/otrace doctor
```

Opsional: symlink ke PATH
```bash
ln -s "$(pwd)/bin/otrace" /usr/local/bin/otrace
```

## Penggunaan

```bash
# Basic commands
otrace doctor                       # Cek environment & isolasi
otrace tools                        # Daftar tool & status
otrace runs                         # Lihat riwayat scan
otrace isolate                      # Verifikasi isolasi 9router

# Scope management (CIDR support)
otrace scope --add 192.168.1.0/24  # Tambah subnet ke scope
otrace scope --remove 10.0.0.1     # Hapus dari scope
otrace scope                        # Lihat scope saat ini

# Scan commands
otrace scan 192.168.1.10           # Pipeline: nmap + nikto + sqlmap
otrace recon 192.168.1.10          # Nmap saja
otrace web http://target           # Nikto + SQLmap
otrace vuln 192.168.1.10           # OpenVAS/GVM scan

# Specialized tools
otrace crack hashes.txt            # John the Ripper
otrace reverse app.apk             # Ghidra + JADX
otrace forensics disk.img          # Autopsy (+ --pcap)
otrace wireless capture.cap        # Aircrack-ng
otrace exploit --cmd "version; exit" # Metasploit

# Reports & output
otrace report <run_id>             # Tampilkan report
otrace runs                        # Daftar semua run

# Scheduling
otrace schedule add --name daily --target 192.168.1.0/24 --cmd scan --cron "0 2 * * *"
otrace schedule list
otrace schedule run --name daily

# Plugins
otrace plugin example              # Buat template plugin
otrace plugin install ./my-plugin.json
otrace plugin list
```

## Output Format

Setiap run menghasilkan 4 format report di `~/.otrace/runs/<run_id>/`:

- **report.json** — Data terstruktur untuk parsing
- **report.md** — Ringkasan human-readable
- **report.sarif.json** — Format SARIF untuk GitHub Code Scanning
- **report.csv** — Tabel untuk spreadsheet

## Isolasi 9router

1. **Port terlindungi**: 443 dan 20128 tidak pernah di-bind/di-scan
2. **Band 3000-8888**: Dihindari (cf-autopilot)
3. **/etc/hosts**: Tidak pernah ditulis
4. **Pre-flight & post-flight**: Cek kesehatan 9router sebelum & sesudah
5. **State terpisah**: `~/.otrace` (bukan `~/.9router`)

## Plugin System

Buat plugin kustom di `~/.otrace/plugins/`:

```json
{
  "name": "mytool",
  "description": "Tool kustom",
  "tools": [{
    "key": "mytool",
    "bin": ["mytool"],
    "cat": "custom",
    "desc": "Deskripsi tool",
    "install": "pip3 install mytool",
    "builder": "lambda a: ['mytool', a['target']]"
  }]
}
```

Lalu load:
```bash
otrace plugin install ./my-plugin.json
otrace plugin reload
```

## Testing

```bash
# Jalankan semua tests
python3 otrace/tests/test_isolation.py
python3 otrace/tests/test_scope.py
python3 otrace/tests/test_tools.py

# Atau dengan pytest (opsional)
pip3 install pytest
pytest otrace/tests/ -v
```

## CI/CD

GitHub Actions otomatis jalan saat push ke main:
- Run tests di Python 3.9-3.12
- Flake8 linting
- Security checks

## Struktur File

```
otrace/
├── otrace.py          # Main CLI
├── tools.py           # Tool registry & wrappers
├── isolation.py       # 9router guard
├── config.py          # Config & paths
├── reports.py         # Report generator (JSON/MD/SARIF/CSV)
├── scope.py           # CIDR-aware scope checking
├── scheduler.py       # Scheduled scan support
├── plugins.py         # Plugin system
└── tests/
    ├── test_isolation.py
    ├── test_scope.py
    └── test_tools.py
```

## Keamanan & Etika

Gunakan hanya pada sistem yang Anda miliki atau punya izin tertulis. Otrace menolak target 9router dan tidak akan menyentuh layanan lokal yang dilindungi.