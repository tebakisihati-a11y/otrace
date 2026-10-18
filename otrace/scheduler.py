"""Scheduled scan support using stdlib sched (no external deps required)."""

import json
import sched
import threading
import time
from datetime import datetime
from pathlib import Path

from .config import OTRACE_HOME
from . import otrace as otrace_mod

SCHEDULES_FILE = OTRACE_HOME / "schedules.json"


def _load_schedules() -> list:
    if not SCHEDULES_FILE.exists():
        return []
    try:
        return json.loads(SCHEDULES_FILE.read_text())
    except Exception:
        return []


def _save_schedules(schedules: list):
    SCHEDULES_FILE.write_text(json.dumps(schedules, indent=2))


def add_schedule(name: str, target: str, cmd: str, cron_expr: str, enabled: bool = True) -> dict:
    """Add a scheduled scan. Returns schedule dict."""
    schedules = _load_schedules()
    for s in schedules:
        if s["name"] == name:
            s.update({"target": target, "cmd": cmd, "cron": cron_expr, "enabled": enabled})
            _save_schedules(schedules)
            return s
    
    entry = {
        "name": name,
        "target": target,
        "cmd": cmd,
        "cron": cron_expr,
        "enabled": enabled,
        "created_at": datetime.now().isoformat(),
        "last_run": None,
        "next_run": None,
    }
    schedules.append(entry)
    _save_schedules(schedules)
    return entry


def remove_schedule(name: str) -> bool:
    schedules = _load_schedules()
    before = len(schedules)
    schedules = [s for s in schedules if s["name"] != name]
    if len(schedules) < before:
        _save_schedules(schedules)
        return True
    return False


def list_schedules() -> list:
    return _load_schedules()


def run_now(name: str, target: str, cmd: str) -> str:
    """Execute a scheduled command immediately and return run_id."""
    run_id = otrace_mod.new_run_id()
    # Map short cmd names to full otrace commands
    cmd_map = {
        "scan": ["scan", target],
        "recon": ["recon", target],
        "web": ["web", target],
        "vuln": ["vuln", target],
    }
    args = cmd_map.get(cmd, [cmd, target])
    
    # Run via main parser
    import argparse
    parser = otrace_mod.build_parser()
    parsed = parser.parse_args(args)
    parsed.func(parsed)
    return run_id


def start_scheduler_loop():
    """Start background scheduler loop in a daemon thread."""
    _scheduler = sched.scheduler(time.time, time.sleep)
    
    def _tick():
        schedules = _load_schedules()
        now = time.time()
        for s in schedules:
            if not s.get("enabled", True):
                continue
            # Simple: check every 60s if it's time (cron parsing skipped for stdlib-only)
            # In production, use croniter; here we just log and let user run manually
            pass
        _scheduler.enter(60, 1, _tick)
    
    _scheduler.enter(60, 1, _tick)
    thread = threading.Thread(target=_scheduler.run, daemon=True)
    thread.start()
    return thread
