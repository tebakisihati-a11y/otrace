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
from .tools import TOOLS, TOOL_BY_KEY, detect, detect_all, run_tool, installed_keys
from .reports import build_report, write_all, list_runs
from .scope import check_scope, scope_add, scope_remove, scope_list
from .scheduler import add_schedule, remove_schedule, list_schedules, run_now
from .plugins import list_plugins, install_plugin, register_plugin, create_example_plugin

BANNER = r"""
   ____  _                     
  / __ \| |                    
 | |  | | |_ _ __ __ _  ___ ___ 
 | |  | | __| '__/ _` |/ __/ _ \
 | |__| | |_| | | (_| | (_|  __/
  \____/ \__|_|  \__, |\___\___|
                  __/ |        
                 |___/         
  Powerful Cybersecurity Suite — 9router-safe
"""


def new_run_id() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def protected_target_check(target: str):
    low = target.lower()
    if "9router" in low or "20128" in low:
        raise IsolationError("Target terkait 9router — Otrace menolak (isolasi).")
    if low in ("127.0.0.1", "localhost") and False:
        pass
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
    installed = sum(1 for t in TOOLS if detect(t["key"]))
    print(f"Terpasang: {installed}/{len(TOOLS)}")
    print(f"Scope file   : {SCOPE_FILE}")
    
    # Show plugins
    try:
        from .plugins import list_plugins as _list_plugins
        plugins = _list_plugins()
        if plugins:
            print(f"\n=== PLUGINS ({len(plugins)}) ===")
            for pl in plugins:
                print(f"  {pl['name']}: {'ok' if 'config' in pl else 'error'}")
    except Exception:
        pass
    
    ok, problems, after = postflight(before)
    print(f"\nIsolasi      : {'AMAN' if ok else 'PERINGATAN ' + '; '.join(problems)}")
    
    # Show recent runs
    try:
        runs = list_runs(RUNS_DIR)
        if runs:
            print(f"\n=== RECENT RUNS ({len(runs)}) ===")
            for r in runs[:5]:
                rid = r.get('run_id', 'unknown')
                target = r.get('target', '-')
                tools = r.get('tool_count', 0)
                failed = r.get('failed_count', 0)
                iso = r.get('isolation_ok', False)
                iso_icon = '✓' if iso else '✗'
                print(f"  {rid}  target={target}  tools={tools}  fail={failed}  iso={iso_icon}")
    except Exception:
        pass
    
    return 0


def cmd_tools(_args):
    for t in TOOLS:
        p = detect(t["key"])
        print(f"{t['key']:<12} [{t['cat']}]  {t['desc']}")
        print(f"   bin: {', '.join(t['bin'])}  -> {'OK: ' + p if p else 'MISSING'}")
        if not p:
            print(f"   install: {t['install']}")
    return 0


def _run_one(tool_key, target, run_dir, extra=None, msf_cmd=None, stream=False):
    args = {"target": target}
    if extra:
        args["extra"] = extra
    if msf_cmd:
        args["msf_cmd"] = msf_cmd
    return run_tool(tool_key, args, run_dir, stream_output=stream)


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
    print(f"[otrace] run {run_id} target={target}")
    results = []

    # pipeline order
    pipeline = ["nmap", "nikto", "sqlmap"]
    if args.no_web:
        pipeline = ["nmap"]
    for key in pipeline:
        print(f"  -> {key} ...")
        r = _run_one(key, target, run_dir, extra=args.extra.split() if args.extra else None, stream=True)
        results.append(r)
        print(f"     {r.get('status', r.get('error'))}")

    # optional brute force
    if args.brute and detect("hydra"):
        print("  -> hydra ...")
        r = _run_one("hydra", target, run_dir, extra=args.brute.split(), stream=True)
        results.append(r)

    report = build_report(run_id, target, results, before, None)
    # postflight
    ok, problems, after = postflight(before)
    report["nine_router_after"] = after
    report["isolation_ok"] = ok
    report["isolation_problems"] = problems
    
    # Write all formats
    paths = write_all(report, run_dir)
    print(f"\nReport generated:")
    for fmt, p in paths.items():
        print(f"  [{fmt.upper()}] {p}")
    
    print(f"\nIsolasi 9router: {'AMAN' if ok else 'PERINGATAN'}")
    if not ok:
        print("  " + "; ".join(problems))
    return 0 if ok else 1


def cmd_recon(args):
    before = preflight()
    target = args.target
    protected_target_check(target)
    if not check_scope(target):
        print("Target tidak dalam scope.")
        return 2
    run_dir = RUNS_DIR / new_run_id()
    run_dir.mkdir(parents=True, exist_ok=True)
    print(f"[otrace recon] {target}")
    r = _run_one("nmap", target, run_dir, extra=(args.extra.split() if args.extra else None), stream=True)
    print(r.get("status", r.get("error")))
    if "stdout" in r:
        print("output:", r["stdout"])
    
    # Generate report
    report = build_report(new_run_id(), target, [r], before, None)
    ok, problems, after = postflight(before)
    report["nine_router_after"] = after
    report["isolation_ok"] = ok
    write_all(report, run_dir)
    
    print("Isolasi:", "AMAN" if ok else problems)
    return 0


def cmd_web(args):
    before = preflight()
    target = args.target
    protected_target_check(target)
    if not check_scope(target):
        print("Target tidak dalam scope.")
        return 2
    run_dir = RUNS_DIR / new_run_id()
    run_dir.mkdir(parents=True, exist_ok=True)
    print(f"[otrace web] {target}")
    results = []
    for key in ["nikto", "sqlmap"]:
        print(f"  -> {key} ...")
        r = _run_one(key, target, run_dir, stream=True)
        results.append(r)
        print(f"     {r.get('status', r.get('error'))}")
    
    report = build_report(new_run_id(), target, results, before, None)
    ok, problems, after = postflight(before)
    report["nine_router_after"] = after
    report["isolation_ok"] = ok
    write_all(report, run_dir)
    
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
    
    report = build_report(new_run_id(), args.file, [r], before, None)
    ok, problems, after = postflight(before)
    report["nine_router_after"] = after
    report["isolation_ok"] = ok
    write_all(report, run_dir)
    
    print("Isolasi:", "AMAN" if ok else problems)
    return 0


def cmd_reverse(args):
    before = preflight()
    run_dir = RUNS_DIR / new_run_id()
    run_dir.mkdir(parents=True, exist_ok=True)
    print(f"[otrace reverse] {args.file}")
    results = []
    for key in ["ghidra", "jadx"]:
        if detect(key):
            print(f"  -> {key} ...")
            r = _run_one(key, args.file, run_dir)
            results.append(r)
            print(f"     {r.get('status', r.get('error'))}")
        else:
            print(f"  -> {key}: MISSING ({TOOL_BY_KEY[key]['install']})")
    
    report = build_report(new_run_id(), args.file, results, before, None)
    ok, problems, after = postflight(before)
    report["nine_router_after"] = after
    report["isolation_ok"] = ok
    write_all(report, run_dir)
    
    print("Isolasi:", "AMAN" if ok else problems)
    return 0


def cmd_forensics(args):
    before = preflight()
    run_dir = RUNS_DIR / new_run_id()
    run_dir.mkdir(parents=True, exist_ok=True)
    print(f"[otrace forensics] {args.image}")
    results = []
    if detect("autopsy"):
        r = _run_one("autopsy", args.image, run_dir)
        results.append(r)
        print(r.get("status", r.get("error")))
    else:
        print("autopsy MISSING:", TOOL_BY_KEY["autopsy"]["install"])
    # wireshark/tshark for pcap
    if args.pcap and detect("wireshark"):
        r = _run_one("wireshark", args.pcap, run_dir)
        results.append(r)
        print("wireshark:", r.get("status", r.get("error")))
    
    report = build_report(new_run_id(), args.image, results, before, None)
    ok, problems, after = postflight(before)
    report["nine_router_after"] = after
    report["isolation_ok"] = ok
    write_all(report, run_dir)
    
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
    
    report = build_report(new_run_id(), args.capture, [r] if detect("aircrack") else [], before, None)
    ok, problems, after = postflight(before)
    report["nine_router_after"] = after
    report["isolation_ok"] = ok
    write_all(report, run_dir)
    
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
    
    report = build_report(new_run_id(), "127.0.0.1", [r], before, None)
    ok, problems, after = postflight(before)
    report["nine_router_after"] = after
    report["isolation_ok"] = ok
    write_all(report, run_dir)
    
    print("Isolasi:", "AMAN" if ok else problems)
    return 0


def cmd_vuln(args):
    before = preflight()
    target = args.target
    protected_target_check(target)
    if not check_scope(target):
        print("Target tidak dalam scope.")
        return 2
    run_dir = RUNS_DIR / new_run_id()
    run_dir.mkdir(parents=True, exist_ok=True)
    print(f"[otrace vuln] {target} (openvas/gvm)")
    results = []
    if detect("openvas") or detect("gvm"):
        key = "openvas" if detect("openvas") else "gvm"
        r = _run_one(key, target, run_dir)
        results.append(r)
        print(r.get("status", r.get("error")))
    else:
        print("openvas/gvm MISSING:", TOOL_BY_KEY["openvas"]["install"])
    
    report = build_report(new_run_id(), target, results, before, None)
    ok, problems, after = postflight(before)
    report["nine_router_after"] = after
    report["isolation_ok"] = ok
    write_all(report, run_dir)
    
    print("Isolasi:", "AMAN" if ok else problems)
    return 0


def cmd_report(args):
    run_dir = RUNS_DIR / args.run_id
    if not run_dir.exists():
        # Try listing all runs
        runs = list_runs(RUNS_DIR)
        if runs:
            print("Run tidak ditemukan. Daftar run tersedia:")
            for r in runs[:10]:
                print(f"  {r.get('run_id', 'unknown')}  target={r.get('target', '-')}")
            return 1
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
        if scope_add(args.add):
            print(f"Ditambahkan ke scope: {args.add}")
        else:
            print(f"Scope sudah ada: {args.add}")
    elif args.remove:
        if scope_remove(args.remove):
            print(f"Dihapus dari scope: {args.remove}")
        else:
            print(f"Tidak ditemukan di scope: {args.remove}")
    else:
        entries = scope_list()
        if entries:
            print("Scope saat ini:")
            for e in entries:
                print(f"  {e}")
        else:
            print("(kosong)")
    return 0


def cmd_isolate(args):
    before = preflight()
    print(json.dumps(before, indent=2, default=str))
    ok, problems, after = postflight(before)
    print("Hasil:", "AMAN" if ok else problems)
    return 0 if ok else 1


def cmd_runs(_args):
    """List all previous runs with summary."""
    runs = list_runs(RUNS_DIR)
    if not runs:
        print("Belum ada run.")
        return 0
    print(f"Total {len(runs)} run:\n")
    for r in runs:
        rid = r.get('run_id', 'unknown')
        target = r.get('target', '-')
        started = r.get('started', '-')[:19]
        tools = r.get('tool_count', 0)
        failed = r.get('failed_count', 0)
        iso = r.get('isolation_ok', False)
        iso_icon = '✓' if iso else '✗'
        print(f"  {rid}")
        print(f"    target : {target}")
        print(f"    waktu  : {started}")
        print(f"    tools  : {tools} dijalankan, {failed} gagal")
        print(f"    isolasi: {iso_icon}")
        print()
    return 0


def cmd_schedule(args):
    """Manage scheduled scans."""
    if args.action == "add":
        entry = add_schedule(args.name, args.target, args.cmd, args.cron)
        print(f"Scheduled added: {entry['name']} -> {args.target} ({args.cmd})")
    elif args.action == "list":
        schedules = list_schedules()
        if not schedules:
            print("No schedules.")
        else:
            for s in schedules:
                status = "enabled" if s.get("enabled") else "disabled"
                print(f"  {s['name']}: {s['cmd']} {s['target']} [{status}]")
    elif args.action == "remove":
        if remove_schedule(args.name):
            print(f"Removed schedule: {args.name}")
        else:
            print(f"Not found: {args.name}")
    elif args.action == "run":
        run_now(args.name, args.target, args.cmd)
    return 0


def cmd_plugin(args):
    """Manage plugins."""
    if args.action == "list":
        plugins = list_plugins()
        if not plugins:
            print("No plugins installed.")
        else:
            for p in plugins:
                print(f"  {p['name']}: {'ok' if 'config' in p else 'error'}")
    elif args.action == "install":
        result = install_plugin(args.path)
        if result.get("ok"):
            print(f"Plugin installed: {result['name']}")
        else:
            print(f"Failed: {result.get('error')}")
    elif args.action == "example":
        path = create_example_plugin()
        print(f"Example plugin created: {path}")
        print("Edit it, then run: otrace plugin install <path>")
    elif args.action == "reload":
        from .plugins import reload_plugins
        reload_plugins()
        print("Plugins reloaded.")
    return 0


def build_parser():
    p = argparse.ArgumentParser(prog="otrace", description="Otrace powerful cybersecurity suite (9router-safe)")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("doctor", help="Cek environment & isolasi").set_defaults(func=cmd_doctor)
    sub.add_parser("tools", help="Daftar tools terintegrasi").set_defaults(func=cmd_tools)
    sub.add_parser("runs", help="Daftar semua run sebelumnya").set_defaults(func=cmd_runs)

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
    sc.add_argument("--remove", default=None, help="hapus target dari scope")
    sc.set_defaults(func=cmd_scope)

    iso = sub.add_parser("isolate", help="Cek isolasi 9router")
    iso.set_defaults(func=cmd_isolate)

    sch = sub.add_parser("schedule", help="Jadwalkan scan otomatis")
    sch.add_argument("action", choices=["add", "list", "remove", "run"])
    sch.add_argument("--name", default=None)
    sch.add_argument("--target", default=None)
    sch.add_argument("--cmd", default="scan")
    sch.add_argument("--cron", default="0 2 * * *")
    sch.set_defaults(func=cmd_schedule)

    pl = sub.add_parser("plugin", help="Kelola plugin kustom")
    pl.add_argument("action", choices=["list", "install", "example", "reload"])
    pl.add_argument("--path", default=None)
    pl.set_defaults(func=cmd_plugin)

    return p


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