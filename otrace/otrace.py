"""Otrace CLI — powerful cybersecurity suite, isolated from 9router."""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

from .config import (
    ensure_dirs, load_config, RUNS_DIR, LOGS_DIR, SCOPE_FILE, OTRACE_HOME,
    is_protected_port, OTRACE_SERVICE_PORT,
)
from .isolation import preflight, postflight, IsolationError, nine_router_health, hosts_file_intact
from .notify import notify, success, error, warn
from .tools import TOOLS, TOOL_BY_KEY, detect, detect_all, run_tool, installed_keys

BANNER = r"""
    ____  _                     
   / __ \| |                    
  | |  | | |_ _ __ __ _  ___ ___ 
  | |  | | __| '__/ _` |/ __/ _ \
  | |__| | |_| | | (_| | (_|  __/
   \____/ \__|_|  \__,_|\___\___|
   Powerful Cybersecurity Suite — 9router-safe
"""


def new_run_id() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def check_scope(target: str) -> bool:
    cfg = load_config()
    if cfg.get("OTRACE_SCOPE_REQUIRED", "1") != "1":
        return True
    if not SCOPE_FILE.exists():
        return False
    allowed = [l.strip() for l in SCOPE_FILE.read_text().splitlines()
               if l.strip() and not l.strip().startswith("#")]
    if "*" in allowed or "any" in allowed or "ANY" in allowed:
        return True
    for a in allowed:
        if a == target or target.startswith(a) or a in target:
            return True
    return False


def protected_target_check(target: str):
    low = target.lower()
    if "9router" in low or "20128" in low:
        raise IsolationError("Target terkait 9router — Otrace menolak (isolasi).")
    for h in ["cloudcode-pa.googleapis.com", "runtime.us-east-1.kiro.dev"]:
        if h in low:
            raise IsolationError(f"Target adalah domain 9router ({h}) — ditolak.")


def cmd_doctor(_args):
    before = preflight()
    print(BANNER)
    print("=== OTRACE DOCTOR ===")
    print(f"Home          : {OTRACE_HOME}")
    print(f"9router app   : {'OK' if before['health']['app_ok'] else 'DOWN'}")
    print(f"9router MITM  : {'OK' if before['health']['mitm_ok'] else 'DOWN'}")
    print(f"/etc/hosts    : {'intact' if before['hosts_intact'] else 'BROKEN'}")
    print(f"port 443      : {'listening' if before['protected_ports_listening'][443] else 'down'}")
    print(f"port 20128    : {'listening' if before['protected_ports_listening'][20128] else 'down'}")
    print()
    print("=== TOOLS ===")
    for t in TOOLS:
        p = detect(t["key"])
        print(f"  {t['key']:<12} {t['cat']:<10} {'OK ' + p if p else 'MISSING'}")
    print()
    print("Terpasang:", sum(1 for t in TOOLS if detect(t["key"])), "/", len(TOOLS))
    print("Scope file   :", SCOPE_FILE)
    ok, problems, after = postflight(before)
    print("Isolasi      :", "AMAN" if ok else "PERINGATAN " + "; ".join(problems))
    return 0


def cmd_tools(_args):
    for t in TOOLS:
        p = detect(t["key"])
        print(f"{t['key']:<12} [{t['cat']}]  {t['desc']}")
        print(f"   bin: {', '.join(t['bin'])}  -> {'OK: ' + p if p else 'MISSING'}")
        if not p:
            print(f"   install: {t['install']}")
    return 0


def _run_one(tool_key, target, run_dir, extra=None, msf_cmd=None):
    args = {"target": target}
    if extra:
        args["extra"] = extra
    if msf_cmd:
        args["msf_cmd"] = msf_cmd
    return run_tool(tool_key, args, run_dir)


def cmd_scan(args):
    before = preflight()
    target = args.target
    protected_target_check(target)
    if not check_scope(target):
        print(f"Target '{target}' tidak ada di scope ({SCOPE_FILE}). Tambahkan dulu atau set OTRACE_SCOPE_REQUIRED=0.")
        return 2
    run_id = new_run_id()
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    notify("Scan Started", f"{run_id} target={target}")
    print(f"[otrace] run {run_id} target={target}")
    results = []

    pipeline = ["nmap", "nikto", "sqlmap"]
    if args.no_web:
        pipeline = ["nmap"]
    for key in pipeline:
        print(f"  -> {key} ...")
        r = _run_one(key, target, run_dir, extra=args.extra.split() if args.extra else None)
        results.append(r)
        print(f"     {r.get('status', r.get('error'))}")

    if args.brute and detect("hydra"):
        print("  -> hydra ...")
        r = _run_one("hydra", target, run_dir, extra=args.brute.split())
        results.append(r)

    report = {
        "run_id": run_id,
        "target": target,
        "started": datetime.now().isoformat(),
        "results": results,
        "nine_router_before": before,
    }
    ok, problems, after = postflight(before)
    report["nine_router_after"] = after
    report["isolation_ok"] = ok
    report["isolation_problems"] = problems
    (run_dir / "report.json").write_text(json.dumps(report, indent=2, default=str))

    md = [f"# Otrace Report — {run_id}", "", f"Target: `{target}`", ""]
    for r in results:
        md.append(f"## {r.get('tool')}")
        md.append(f"- status: {r.get('status', r.get('error'))}")
        if "cmd" in r:
            md.append(f"- cmd: `{' '.join(r['cmd'])}`")
        if "stdout" in r:
            md.append(f"- output: {r['stdout']}")
        md.append("")
    md.append("## Isolasi 9router")
    md.append(f"- sebelum: {before['health']}")
    md.append(f"- sesudah: {after['health']}")
    md.append(f"- hosts intact: {after['hosts_intact']}")
    md.append(f"- hasil: {'AMAN' if ok else 'PERINGATAN: ' + '; '.join(problems)}")
    (run_dir / "report.md").write_text("\n".join(md))

    notify("Scan Complete", f"{run_id} isolation={'SAFE' if ok else 'WARNING'}")
    print(f"\nReport: {run_dir / 'report.md'}")
    print("Isolasi 9router:", "AMAN" if ok else "PERINGATAN")
    if not ok:
        print("  " + "; ".join(problems))
        error(f"Isolation warning: {problems}")
    else:
        success(f"Scan {run_id} complete — isolation safe")
    return 0 if ok else 1


def cmd_recon(args):
    before = preflight()
    target = args.target
    protected_target_check(target)
    if not check_scope(target):
        print("Target tidak dalam scope."); return 2
    run_dir = RUNS_DIR / new_run_id()
    run_dir.mkdir(parents=True, exist_ok=True)
    print(f"[otrace recon] {target}")
    r = _run_one("nmap", target, run_dir, extra=(args.extra.split() if args.extra else None))
    print(r.get("status", r.get("error")))
    if "stdout" in r:
        print("output:", r["stdout"])
    ok, problems, after = postflight(before)
    print("Isolasi:", "AMAN" if ok else problems)
    return 0


def cmd_web(args):
    before = preflight()
    target = args.target
    protected_target_check(target)
    if not check_scope(target):
        print("Target tidak dalam scope."); return 2
    run_dir = RUNS_DIR / new_run_id()
    run_dir.mkdir(parents=True, exist_ok=True)
    print(f"[otrace web] {target}")
    for key in ["nikto", "sqlmap"]:
        print(f"  -> {key} ...")
        r = _run_one(key, target, run_dir)
        print(f"     {r.get('status', r.get('error'))}")
    ok, problems, after = postflight(before)
    print("Isolasi:", "AMAN" if ok else problems)
    return 0


def cmd_crack(args):
    before = preflight()
    run_dir = RUNS_DIR / new_run_id()
    run_dir.mkdir(parents=True, exist_ok=True)
    print(f"[otrace crack] {args.file}")
    r = _run_one("john", args.file, run_dir, extra=(args.extra.split() if args.extra else None))
    print(r.get("status", r.get("error")))
    if "stdout" in r:
        print("output:", r["stdout"])
    ok, problems, after = postflight(before)
    print("Isolasi:", "AMAN" if ok else problems)
    return 0


def cmd_reverse(args):
    before = preflight()
    run_dir = RUNS_DIR / new_run_id()
    run_dir.mkdir(parents=True, exist_ok=True)
    print(f"[otrace reverse] {args.file}")
    for key in ["ghidra", "jadx"]:
        if detect(key):
            print(f"  -> {key} ...")
            r = _run_one(key, args.file, run_dir)
            print(f"     {r.get('status', r.get('error'))}")
        else:
            print(f"  -> {key}: MISSING ({TOOL_BY_KEY[key]['install']})")
    ok, problems, after = postflight(before)
    print("Isolasi:", "AMAN" if ok else problems)
    return 0


def cmd_forensics(args):
    before = preflight()
    run_dir = RUNS_DIR / new_run_id()
    run_dir.mkdir(parents=True, exist_ok=True)
    print(f"[otrace forensics] {args.image}")
    if detect("autopsy"):
        r = _run_one("autopsy", args.image, run_dir)
        print(r.get("status", r.get("error")))
    else:
        print("autopsy MISSING:", TOOL_BY_KEY["autopsy"]["install"])
    if args.pcap and detect("wireshark"):
        r = _run_one("wireshark", args.pcap, run_dir)
        print("wireshark:", r.get("status", r.get("error")))
    ok, problems, after = postflight(before)
    print("Isolasi:", "AMAN" if ok else problems)
    return 0


def cmd_wireless(args):
    before = preflight()
    run_dir = RUNS_DIR / new_run_id()
    run_dir.mkdir(parents=True, exist_ok=True)
    print("[otrace wireless] aircrack-ng suite")
    if not detect("aircrack"):
        print("aircrack-ng MISSING:", TOOL_BY_KEY["aircrack"]["install"])
    else:
        r = _run_one("aircrack", args.capture, run_dir, extra=(args.extra.split() if args.extra else None))
        print(r.get("status", r.get("error")))
    ok, problems, after = postflight(before)
    print("Isolasi:", "AMAN" if ok else problems)
    return 0


def cmd_exploit(args):
    before = preflight()
    run_dir = RUNS_DIR / new_run_id()
    run_dir.mkdir(parents=True, exist_ok=True)
    print("[otrace exploit] metasploit")
    if not detect("metasploit"):
        print("metasploit MISSING:", TOOL_BY_KEY["metasploit"]["install"])
        return 0
    msf_cmd = args.cmd or "version; exit"
    r = _run_one("metasploit", "127.0.0.1", run_dir, msf_cmd=msf_cmd)
    print(r.get("status", r.get("error")))
    if "stdout" in r:
        print("output:", r["stdout"])
    ok, problems, after = postflight(before)
    print("Isolasi:", "AMAN" if ok else problems)
    return 0


def cmd_vuln(args):
    before = preflight()
    target = args.target
    protected_target_check(target)
    if not check_scope(target):
        print("Target tidak dalam scope."); return 2
    run_dir = RUNS_DIR / new_run_id()
    run_dir.mkdir(parents=True, exist_ok=True)
    print(f"[otrace vuln] {target} (openvas/gvm)")
    if detect("openvas") or detect("gvm"):
        key = "openvas" if detect("openvas") else "gvm"
        r = _run_one(key, target, run_dir)
        print(r.get("status", r.get("error")))
    else:
        print("openvas/gvm MISSING:", TOOL_BY_KEY["openvas"]["install"])
    ok, problems, after = postflight(before)
    print("Isolasi:", "AMAN" if ok else problems)
    return 0


def cmd_report(args):
    run_dir = RUNS_DIR / args.run_id
    if not run_dir.exists():
        print("Run tidak ditemukan:", run_dir)
        return 1
    p = run_dir / "report.md"
    if p.exists():
        print(p.read_text())
    else:
        print("Tidak ada report.md; isi folder:")
        for f in run_dir.iterdir():
            print(" ", f.name)
    return 0


def cmd_scope(args):
    ensure_dirs()
    if args.add:
        lines = SCOPE_FILE.read_text().splitlines() if SCOPE_FILE.exists() else []
        if args.add not in lines:
            lines.append(args.add)
        SCOPE_FILE.write_text("\n".join(lines) + "\n")
        print("Ditambahkan ke scope:", args.add)
    else:
        print(SCOPE_FILE.read_text())
    return 0


def cmd_isolate(args):
    before = preflight()
    print(json.dumps(before, indent=2, default=str))
    ok, problems, after = postflight(before)
    print("Hasil:", "AMAN" if ok else problems)
    return 0 if ok else 1


def build_parser():
    p = argparse.ArgumentParser(prog="otrace", description="Otrace powerful cybersecurity suite (9router-safe)")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("doctor", help="Cek environment & isolasi").set_defaults(func=cmd_doctor)
    sub.add_parser("tools", help="Daftar tools terintegrasi").set_defaults(func=cmd_tools)

    s = sub.add_parser("scan", help="Scan pipeline (nmap+nikto+sqlmap)")
    s.add_argument("target")
    s.add_argument("--extra", default=None, help="argumen ekstra untuk nmap")
    s.add_argument("--no-web", action="store_true", help="lewati nikto/sqlmap")
    s.add_argument("--brute", default=None, help="argumen hydra untuk brute force")
    s.set_defaults(func=cmd_scan)

    r = sub.add_parser("recon", help="Reconnaissance (nmap)")
    r.add_argument("target")
    r.add_argument("--extra", default=None)
    r.set_defaults(func=cmd_recon)

    w = sub.add_parser("web", help="Web assessment (nikto+sqlmap)")
    w.add_argument("target")
    w.set_defaults(func=cmd_web)

    c = sub.add_parser("crack", help="Password cracking (john)")
    c.add_argument("file")
    c.add_argument("--extra", default=None)
    c.set_defaults(func=cmd_crack)

    rv = sub.add_parser("reverse", help="Reverse engineering (ghidra+jadx)")
    rv.add_argument("file")
    rv.set_defaults(func=cmd_reverse)

    f = sub.add_parser("forensics", help="Digital forensics (autopsy)")
    f.add_argument("image")
    f.add_argument("--pcap", default=None)
    f.set_defaults(func=cmd_forensics)

    wl = sub.add_parser("wireless", help="Wireless (aircrack-ng)")
    wl.add_argument("capture")
    wl.add_argument("--extra", default=None)
    wl.set_defaults(func=cmd_wireless)

    ex = sub.add_parser("exploit", help="Exploitation (metasploit)")
    ex.add_argument("--cmd", default=None, help="perintah msfconsole")
    ex.set_defaults(func=cmd_exploit)

    v = sub.add_parser("vuln", help="Vulnerability scan (openvas/gvm)")
    v.add_argument("target")
    v.set_defaults(func=cmd_vuln)

    rep = sub.add_parser("report", help="Tampilkan report run")
    rep.add_argument("run_id")
    rep.set_defaults(func=cmd_report)

    sc = sub.add_parser("scope", help="Kelola scope (izin)")
    sc.add_argument("--add", default=None, help="tambah target ke scope")
    sc.set_defaults(func=cmd_scope)

    iso = sub.add_parser("serve", help="Start web dashboard")
    iso.add_argument("--port", type=int, default=8765, help="Port (default 8765)")
    iso.set_defaults(func=cmd_serve)

    iso = sub.add_parser("isolate", help="Cek isolasi 9router")
    iso.set_defaults(func=cmd_isolate)

    return p


def cmd_serve(args):
    from .web import serve
    port = args.port or 8765
    print(f"Starting Otrace web dashboard on http://127.0.0.1:{port}")
    print("Press Ctrl+C to stop")
    serve(port)


def main(argv=None):
    ensure_dirs()
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except IsolationError as e:
        print("ISOLATION BLOCK:", e, file=sys.stderr)
        return 3
    except KeyboardInterrupt:
        print("\n[dibatalkan]")
        return 130
    except Exception as e:
        print("ERROR:", repr(e), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
