"""Registry & wrappers for the integrated security tools."""

import shutil
import subprocess
import time
from pathlib import Path

from .config import DEFAULT_TIMEOUT, load_config
from .isolation import assert_safe_command, assert_safe_port


# Each tool: key, binary candidates, category, description, install hint, builder(args)->cmd list
TOOLS = [
    {
        "key": "nmap",
        "bin": ["nmap"],
        "cat": "recon",
        "desc": "Port/service/version scanning & NSE scripts",
        "install": "brew install nmap  (atau: apt install nmap)",
        "builder": lambda a: ["nmap", "-sV", "-sC", "--top-ports", "1000"] + (a.get("extra", []) or []) + [a["target"]],
    },
    {
        "key": "sqlmap",
        "bin": ["sqlmap", "sqlmap.py"],
        "cat": "web",
        "desc": "Deteksi & eksploitasi SQL injection",
        "install": "pip3 install sqlmap  (atau git clone sqlmapproject/sqlmap)",
        "builder": lambda a: ["sqlmap", "-u", a["target"], "--batch", "--random-agent"] + (a.get("extra", []) or []),
    },
    {
        "key": "ssh",
        "bin": ["ssh"],
        "cat": "access",
        "desc": "OpenSSH client (remote access / tunneling)",
        "install": "bawaan macOS/Linux",
        "builder": lambda a: ["ssh"] + (a.get("extra", []) or []) + [a["target"]],
    },
    {
        "key": "openvas",
        "bin": ["openvas", "gvm-cli"],
        "cat": "vuln",
        "desc": "OpenVAS vulnerability scanner (via GVM)",
        "install": "brew install gvm  (atau apt install gvm)",
        "builder": lambda a: ["gvm-cli", "socket", "--xml", f'<create_target><name>{a["target"]}</name></create_target>'],
    },
    {
        "key": "john",
        "bin": ["john", "john-the-ripper"],
        "cat": "password",
        "desc": "John the Ripper password cracker",
        "install": "brew install john  (atau apt install john)",
        "builder": lambda a: ["john", a["target"]] + (a.get("extra", []) or []),
    },
    {
        "key": "hydra",
        "bin": ["hydra"],
        "cat": "password",
        "desc": "Network login brute-forcer (parallel)",
        "install": "brew install hydra  (atau apt install hydra)",
        "builder": lambda a: ["hydra"] + (a.get("extra", []) or []) + [a["target"]],
    },
    {
        "key": "metasploit",
        "bin": ["msfconsole", "msfvenom"],
        "cat": "exploit",
        "desc": "Metasploit Framework (exploit dev & payload)",
        "install": "brew install metasploit  (atau apt install metasploit-framework)",
        "builder": lambda a: ["msfconsole", "-q", "-x", a.get("msf_cmd", "version; exit")],
    },
    {
        "key": "gvm",
        "bin": ["gvm", "gvmd"],
        "cat": "vuln",
        "desc": "Greenbone Vulnerability Management (GVM) daemon",
        "install": "brew install gvm  (atau apt install gvm)",
        "builder": lambda a: ["gvm-cli", "--gmp-username", "admin", "help"],
    },
    {
        "key": "nikto",
        "bin": ["nikto", "nikto.pl"],
        "cat": "web",
        "desc": "Web server vulnerability scanner",
        "install": "brew install nikto  (atau apt install nikto)",
        "builder": lambda a: ["nikto", "-h", a["target"]] + (a.get("extra", []) or []),
    },
    {
        "key": "aircrack",
        "bin": ["aircrack-ng", "airmon-ng", "airodump-ng"],
        "cat": "wireless",
        "desc": "Aircrack-ng suite (WEP/WPA cracking)",
        "install": "brew install aircrack-ng  (atau apt install aircrack-ng)",
        "builder": lambda a: ["aircrack-ng", a["target"]] + (a.get("extra", []) or []),
    },
    {
        "key": "wireshark",
        "bin": ["tshark", "wireshark"],
        "cat": "network",
        "desc": "Packet capture & analysis (tshark CLI)",
        "install": "brew install wireshark  (atau apt install tshark)",
        "builder": lambda a: ["tshark", "-r", a["target"]] + (a.get("extra", []) or []),
    },
    {
        "key": "autopsy",
        "bin": ["autopsy"],
        "cat": "forensics",
        "desc": "Digital forensics platform (Autopsy)",
        "install": "brew install autopsy  (atau apt install autopsy)",
        "builder": lambda a: ["autopsy", a["target"]] + (a.get("extra", []) or []),
    },
    {
        "key": "ghidra",
        "bin": ["ghidra", "ghidraRun"],
        "cat": "reverse",
        "desc": "NSA reverse engineering suite (Ghidra)",
        "install": "brew install ghidra  (atau unduh dari ghidra-sre.org)",
        "builder": lambda a: ["ghidraRun", a["target"]] + (a.get("extra", []) or []),
    },
    {
        "key": "jadx",
        "bin": ["jadx", "jadx-gui"],
        "cat": "reverse",
        "desc": "Dex/Android bytecode decompiler",
        "install": "brew install jadx  (atau apt install jadx)",
        "builder": lambda a: ["jadx", a["target"]] + (a.get("extra", []) or []),
    },
]

TOOL_BY_KEY = {t["key"]: t for t in TOOLS}


def detect(name: str):
    t = TOOL_BY_KEY.get(name)
    if not t:
        return None
    for b in t["bin"]:
        p = shutil.which(b)
        if p:
            return p
    return None


def detect_all() -> dict:
    out = {}
    for t in TOOLS:
        out[t["key"]] = detect(t["key"])
    return out


def installed_keys() -> list:
    return [k for k, v in detect_all().items() if v]


def run_tool(name: str, args: dict, run_dir: Path, timeout: int = None) -> dict:
    t = TOOL_BY_KEY.get(name)
    if not t:
        return {"ok": False, "error": f"tool tidak dikenal: {name}"}
    binary = detect(name)
    if not binary:
        # build planned command using first binary name for reference
        try:
            planned = t["builder"](args)
        except Exception as e:
            planned = []
        return {
            "ok": False,
            "status": "not_installed",
            "tool": name,
            "binary": t["bin"][0],
            "planned_cmd": planned,
            "install": t["install"],
            "error": f"{name} tidak terpasang. Pasang: {t['install']}",
        }

    try:
        cmd = t["builder"](args)
    except Exception as e:
        return {"ok": False, "error": f"gagal menyusun perintah: {e}"}

    # swap binary candidate name with detected path for first token if it matches
    if cmd and cmd[0] in t["bin"]:
        cmd[0] = binary

    # isolation checks
    assert_safe_command(cmd)
    for tok in cmd:
        if isinstance(tok, str) and tok.isdigit():
            try:
                assert_safe_port(int(tok))
            except Exception:
                pass

    cfg = load_config()
    to = timeout or int(cfg.get("OTRACE_DEFAULT_TIMEOUT", "300"))
    run_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = run_dir / f"{name}.out"
    stderr_path = run_dir / f"{name}.err"

    start = time.time()
    try:
        with open(stdout_path, "w") as fo, open(stderr_path, "w") as fe:
            proc = subprocess.run(
                cmd, stdout=fo, stderr=fe, timeout=to, text=True,
                env={**dict(__import__("os").environ), "OTRACE_RUN": str(run_dir)},
            )
        rc = proc.returncode
    except subprocess.TimeoutExpired:
        rc = -1
        with open(stderr_path, "a") as fe:
            fe.write(f"\n[otrace] TIMEOUT setelah {to}s\n")
    except Exception as e:
        return {"ok": False, "error": f"gagal menjalankan: {e}", "cmd": cmd}

    dur = round(time.time() - start, 2)
    ok = rc == 0
    return {
        "ok": ok,
        "status": "done" if ok else "failed",
        "tool": name,
        "cmd": cmd,
        "returncode": rc,
        "duration_s": dur,
        "stdout": str(stdout_path),
        "stderr": str(stderr_path),
    }