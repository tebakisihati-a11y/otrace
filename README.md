# Otrace — Cyber Security Tool Orchestrator

Orchestrasi tool keamanan siber gratis dengan isolasi, scheduling, dan laporan otomatis.

## Fitur

- **14 Tool Security**: nmap, sqlmap, nikto, hydra, john, aircrack-ng, tshark, jadx, ghidra, openvas, metasploit, autopsy, ssh, gvm
- **Isolasi Aman**: Blockir `/etc/hosts`, cloudflared, port 443/20128 (9router guard)
- **Scope Management**: CIDR, wildcard, exact match
- **Scheduling**: Cron-based automatic scans
- **Reports**: JSON, Markdown, SARIF, CSV
- **Plugin System**: Extensible tool wrappers

## Instalasi

### Prerequisites

- Python 3.10+
- Podman (untuk tool wrappers)
- pip3

### Setup

```bash
# Clone repository
git clone https://github.com/tebakisihati-a11y/otrace.git
cd otrace

# Install Python dependencies (minimal)
pip3 install -e .

# Install tool wrappers (Podman-based)
./bin/install-tools.sh

# Install ghidra (manual, ~540MB)
./bin/install-ghidra.sh
```

### Tool Wrappers (Podman)

Tool dijalankan via Podman container agar isolated dan reproducible:

| Tool | Wrapper | Status |
|------|---------|--------|
| nmap | `~/bin/nmap` | ✅ Working |
| sqlmap | `~/bin/sqlmap` | ✅ Working |
| nikto | `~/bin/nikto` | ✅ Working |
| hydra | `~/bin/hydra` | ✅ Working |
| john | `~/bin/john` | ✅ Working |
| aircrack-ng | `~/bin/aircrack-ng` | ✅ Working |
| tshark | `~/bin/tshark` | ✅ Working |
| jadx | `~/bin/jadx` | ✅ Working |
| ghidra | `~/bin/ghidra` | ✅ Working |
| ssh | `/usr/bin/ssh` | ✅ Native |
| openvas | Manual install | ⚠️ |
| metasploit | Manual install | ⚠️ |
| autopsy | Manual install | ⚠️ |
| gvm | Manual install | ⚠️ |

## Penggunaan

### CLI

```bash
# Scan target
python3 -m otrace scan --target 192.168.1.0/24 --tools nmap,nikto

# Scheduled scan
python3 -m otrace schedule --cron "0 2 * * *" --target example.com --tools nmap

# Generate report
python3 -m otrace report --run-id <run-id> --format json,markdown

# List tools
python3 -m otrace tools --list
```

### Web UI

Buka `index.html` di browser untuk dashboard visual.

## Keamanan

- **9router Guard**: Never modify `/etc/hosts`, never touch ports 443/20128
- **Command Injection Prevention**: `assert_safe_command()` validates all tool commands
- **Port Protection**: `assert_safe_port()` blocks protected ports
- **Isolation**: Tool wrappers run in isolated Podman containers

## Testing

```bash
python3 -m pytest -v
```

## License

MIT