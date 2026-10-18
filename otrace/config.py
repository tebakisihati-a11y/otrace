"""Configuration & paths for Otrace."""

import os
from pathlib import Path

HOME = Path.home()
OTRACE_HOME = HOME / ".otrace"
RUNS_DIR = OTRACE_HOME / "runs"
LOGS_DIR = OTRACE_HOME / "logs"
SCOPE_FILE = OTRACE_HOME / "scope.txt"
CONFIG_FILE = OTRACE_HOME / "config.env"

# Ports / endpoints we must NEVER touch (9router).
PROTECTED_PORTS = {443, 20128}
# Port band used by cf-autopilot (avoid).
AVOID_PORT_BANDS = [(3000, 8888)]
# Preferred Otrace service port (if ever needed).
OTRACE_SERVICE_PORT = 18765

# 9router endpoints for health checks.
NINE_ROUTER_APP = "http://127.0.0.1:20128/api/health"
NINE_ROUTER_MITM = "https://127.0.0.1/_mitm_health"

# Domains 9router pins in /etc/hosts — Otrace must never rewrite these.
PROTECTED_HOSTS = {
    "daily-cloudcode-pa.googleapis.com",
    "cloudcode-pa.googleapis.com",
    "runtime.us-east-1.kiro.dev",
    "q.us-east-1.amazonaws.com",
    "codewhisperer.us-east-1.amazonaws.com",
}

# Commandline substrings that indicate we might be touching 9router internals.
PROTECTED_CMD_SUBSTRINGS = [
    "9router",
    ".9router/",
    "server.js",            # 9router MITM server.js
    "cloudflared",          # 9router tunnel
    ":20128",
    "com.9router",
]

DEFAULT_TIMEOUT = 300  # seconds per tool invocation


def ensure_dirs():
    for d in (OTRACE_HOME, RUNS_DIR, LOGS_DIR):
        d.mkdir(parents=True, exist_ok=True)
    if not CONFIG_FILE.exists():
        CONFIG_FILE.write_text(
            "# Otrace config (edit freely)\n"
            "OTRACE_DEFAULT_TIMEOUT=300\n"
            "OTRACE_SCOPE_REQUIRED=1\n"
        )
    if not SCOPE_FILE.exists():
        SCOPE_FILE.write_text(
            "# Daftar target yang Anda miliki / punya izin tertulis (satu per baris).\n"
            "# Contoh: 192.168.1.0/24\n"
            "# Contoh: example.com\n"
        )


def load_config():
    ensure_dirs()
    cfg = {
        "OTRACE_DEFAULT_TIMEOUT": str(DEFAULT_TIMEOUT),
        "OTRACE_SCOPE_REQUIRED": "1",
    }
    for line in CONFIG_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        cfg[k.strip()] = v.strip().strip('"').strip("'")
    # env overrides
    for k in list(cfg):
        if k in os.environ:
            cfg[k] = os.environ[k]
    return cfg


def is_protected_port(port: int) -> bool:
    if port in PROTECTED_PORTS:
        return True
    for lo, hi in AVOID_PORT_BANDS:
        if lo <= port <= hi:
            return True
    return False