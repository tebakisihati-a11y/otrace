"""Report generation, export formats, and summary builders."""

import csv
import io
import json
from datetime import datetime
from pathlib import Path

# SARIF schema constants — minimal but valid
SARIF_SCHEMA = "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json"
SARIF_VERSION = "2.1.0"


def build_report(run_id: str, target: str, results: list, before: dict, after: dict) -> dict:
    """Build unified report dict from run components."""
    started = next((r.get("started") for r in [{}] + results), datetime.now().isoformat())
    if not any(isinstance(r, dict) and "started" in r for r in results):
        started = datetime.now().isoformat()
    
    isolation_ok = all(r.get("ok", True) for r in results if isinstance(r, dict))
    tools_ran = [r.get("tool", "unknown") for r in results if isinstance(r, dict) and "tool" in r]
    tools_failed = [r.get("tool") for r in results if isinstance(r, dict) and not r.get("ok")]
    
    return {
        "run_id": run_id,
        "target": target,
        "started": started,
        "finished": datetime.now().isoformat(),
        "results": results,
        "nine_router_before": before,
        "nine_router_after": after,
        "isolation_ok": isolation_ok,
        "tools_ran": tools_ran,
        "tools_failed": tools_failed,
        "tool_count": len(tools_ran),
        "failed_count": len(tools_failed),
    }


def write_json(report: dict, run_dir: Path) -> Path:
    """Write report.json to run directory."""
    p = run_dir / "report.json"
    p.write_text(json.dumps(report, indent=2, default=str))
    return p


def write_markdown(report: dict, run_dir: Path) -> Path:
    """Write human-readable report.md."""
    lines = [
        f"# Otrace Report — {report['run_id']}",
        "",
        f"**Target:** `{report['target']}`",
        f"**Started:** {report['started']}",
        f"**Finished:** {report['finished']}",
        f"**Tools executed:** {report['tool_count']}",
        f"**Failures:** {report['failed_count']}",
        "",
        "---",
        "",
        "## Tool Results",
        "",
    ]
    
    for r in report.get("results", []):
        if not isinstance(r, dict):
            continue
        tool = r.get("tool", "unknown")
        status = r.get("status", r.get("error", "unknown"))
        duration = r.get("duration_s", "?")
        rc = r.get("returncode", "?")
        
        status_icon = "✓" if r.get("ok") else "✗"
        lines.append(f"### {status_icon} {tool}")
        lines.append(f"- **Status:** {status}")
        lines.append(f"- **Return code:** {rc}")
        lines.append(f"- **Duration:** {duration}s")
        if "cmd" in r:
            lines.append(f"- **Command:** `{ ' '.join(r['cmd']) }`")
        if "stdout" in r and r["stdout"]:
            lines.append(f"- **Output:** [{r['stdout']}]")
        lines.append("")
    
    lines += [
        "## Isolasi 9router",
        "",
        f"- Sebelum: {json.dumps(report.get('nine_router_before', {}).get('health', {}))}",
        f"- Sesudah: {json.dumps(report.get('nine_router_after', {}).get('health', {}))}",
        f"- Hosts intact: {report.get('nine_router_after', {}).get('hosts_intact', False)}",
        f"- Hasil: {'AMAN' if report.get('isolation_ok') else 'PERINGATAN'}",
        "",
        "---",
        f"*Dibuat oleh Otrace pada {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
    ]
    
    p = run_dir / "report.md"
    p.write_text("\n".join(lines))
    return p


def write_sarif(report: dict, run_dir: Path) -> Path:
    """Write SARIF-format report for GitHub Code Scanning integration."""
    runs = []
    for r in report.get("results", []):
        if not isinstance(r, dict):
            continue
        tool = r.get("tool", "unknown")
        level = "error" if not r.get("ok") else "note"
        message = r.get("error", r.get("status", "no message"))
        
        runs.append({
            "tool": {"name": tool},
            "results": [{
                "level": level,
                "message": {"text": message},
                "ruleId": f"OTRACE.{tool}",
            }]
        })
    
    sarif = {
        "$schema": SARIF_SCHEMA,
        "version": SARIF_VERSION,
        "runs": runs,
    }
    
    p = run_dir / "report.sarif.json"
    p.write_text(json.dumps(sarif, indent=2))
    return p


def write_csv(report: dict, run_dir: Path) -> Path:
    """Write CSV summary for spreadsheet analysis."""
    p = run_dir / "report.csv"
    with p.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["run_id", "target", "tool", "status", "returncode", "duration_s", "ok"])
        for r in report.get("results", []):
            if not isinstance(r, dict):
                continue
            writer.writerow([
                report["run_id"],
                report["target"],
                r.get("tool", ""),
                r.get("status", r.get("error", "")),
                r.get("returncode", ""),
                r.get("duration_s", ""),
                r.get("ok", ""),
            ])
    return p


def write_all(report: dict, run_dir: Path) -> dict:
    """Write all export formats. Returns paths."""
    paths = {
        "json": write_json(report, run_dir),
        "md": write_markdown(report, run_dir),
        "sarif": write_sarif(report, run_dir),
        "csv": write_csv(report, run_dir),
    }
    return paths


def list_runs(runs_dir: Path) -> list:
    """List all run directories with metadata."""
    runs = []
    if not runs_dir.exists():
        return runs
    for d in sorted(runs_dir.iterdir(), reverse=True):
        if d.is_dir():
            report_json = d / "report.json"
            if report_json.exists():
                try:
                    data = json.loads(report_json.read_text())
                    data["_path"] = str(d)
                    runs.append(data)
                except Exception:
                    runs.append({"run_id": d.name, "_path": str(d), "error": "parse failed"})
            else:
                runs.append({"run_id": d.name, "_path": str(d), "note": "no report.json"})
    return runs
