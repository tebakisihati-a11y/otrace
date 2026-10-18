"""Isolation guard: Otrace must never disturb 9router."""

import socket
import subprocess
import time
import urllib.request
import urllib.error
import ssl

from .config import (
    PROTECTED_PORTS,
    PROTECTED_HOSTS,
    PROTECTED_CMD_SUBSTRINGS,
    NINE_ROUTER_APP,
    NINE_ROUTER_MITM,
)


class IsolationError(Exception):
    pass


def _http_ok(url: str, timeout: float = 3.0) -> bool:
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
            return 200 <= r.status < 300
    except Exception:
        return False


def nine_router_health() -> dict:
    app_ok = _http_ok(NINE_ROUTER_APP)
    mitm_ok = _http_ok(NINE_ROUTER_MITM)
    return {"app_ok": app_ok, "mitm_ok": mitm_ok, "healthy": app_ok and mitm_ok}


def port_listening(port: int, host: str = "127.0.0.1") -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1.0)
    try:
        s.connect((host, port))
        return True
    except Exception:
        return False
    finally:
        s.close()


def assert_safe_port(port: int):
    if port in PROTECTED_PORTS:
        raise IsolationError(f"Port {port} dilindungi (9router). Pilih port lain.")
    for lo, hi in [(3000, 8888)]:
        if lo <= port <= hi:
            raise IsolationError(f"Port {port} berada di band cf-autopilot (3000-8888); hindari.")
    if port < 1024 and port not in (0,):
        raise IsolationError(f"Port {port} sistem; butuh root & berisiko. Gunakan port >=1024.")


def assert_safe_command(cmd):
    """Reject commands that look like they touch 9router internals."""
    joined = " ".join(str(x) for x in cmd) if isinstance(cmd, (list, tuple)) else str(cmd)
    low = joined.lower()
    for sub in PROTECTED_CMD_SUBSTRINGS:
        if sub.lower() in low:
            # allow our own health checks that contain the URL strings? We build those separately.
            raise IsolationError(
                f"Perintah mengandung pola terlindung '{sub}' — dibatalkan untuk melindungi 9router.\n"
                f"Perintah: {joined[:200]}"
            )


def hosts_file_intact() -> bool:
    """Verify 9router's /etc/hosts entries still present (we never edit the file)."""
    try:
        content = open("/etc/hosts").read()
    except Exception:
        return False
    return all(h in content for h in PROTECTED_HOSTS)


def snapshot() -> dict:
    h = nine_router_health()
    return {
        "health": h,
        "hosts_intact": hosts_file_intact(),
        "protected_ports_listening": {p: port_listening(p) for p in PROTECTED_PORTS},
        "ts": time.time(),
    }


def verify_unchanged(before: dict, after: dict) -> tuple:
    problems = []
    if before["health"] != after["health"]:
        problems.append(f"kesehatan 9router berubah: {before['health']} -> {after['health']}")
    if before["hosts_intact"] != after["hosts_intact"] or not after["hosts_intact"]:
        problems.append("entri /etc/hosts 9router tidak intact")
    for p in PROTECTED_PORTS:
        if before["protected_ports_listening"].get(p) != after["protected_ports_listening"].get(p):
            problems.append(f"status port terlindung {p} berubah")
    return (len(problems) == 0, problems)


def preflight(strict: bool = True) -> dict:
    before = snapshot()
    if strict and not before["health"]["healthy"]:
        raise IsolationError(
            "9router tidak sehat sebelum Otrace jalan. Pulihkan dulu: bash ~/.9router/mitmctl.sh status"
        )
    if not before["hosts_intact"]:
        raise IsolationError("/etc/hosts 9router tidak intact — Otrace menolak jalan.")
    return before


def postflight(before: dict) -> tuple:
    after = snapshot()
    ok, problems = verify_unchanged(before, after)
    return ok, problems, after