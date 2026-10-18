"""Tests for reports module."""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from otrace.reports import build_report, write_json, write_markdown, write_sarif, write_csv, write_all, list_runs
from otrace.config import RUNS_DIR
import json
from pathlib import Path
import tempfile


def test_build_report():
    """Test report dict building."""
    results = [
        {"tool": "nmap", "status": "done", "ok": True, "duration_s": 12.5},
        {"tool": "nikto", "status": "failed", "ok": False, "error": "not installed"},
    ]
    before = {"health": {"app_ok": True, "mitm_ok": True, "healthy": True}}
    after = {"health": {"app_ok": True, "mitm_ok": True, "healthy": True}}
    
    report = build_report("20261018-120000", "192.168.1.1", results, before, after)
    
    assert report["run_id"] == "20261018-120000"
    assert report["target"] == "192.168.1.1"
    assert report["tool_count"] == 2
    assert report["failed_count"] == 1
    assert report.get("isolation_ok", True) == False  # 有失败的工具


def test_write_json(tmp_path):
    """Test JSON report writing."""
    report = {
        "run_id": "test-001",
        "target": "192.168.1.1",
        "results": [{"tool": "nmap", "ok": True}],
    }
    p = write_json(report, tmp_path)
    assert p.exists()
    
    data = json.loads(p.read_text())
    assert data["run_id"] == "test-001"


def test_write_markdown(tmp_path):
    """Test Markdown report writing."""
    report = {
        "run_id": "test-001",
        "target": "192.168.1.1",
        "started": "2026-10-18T12:00:00",
        "finished": "2026-10-18T12:01:00",
        "results": [{"tool": "nmap", "ok": True, "status": "done"}],
        "tool_count": 1,
        "failed_count": 0,
        "isolation_ok": True,
    }
    p = write_markdown(report, tmp_path)
    assert p.exists()
    
    content = p.read_text()
    assert "# Otrace Report" in content
    assert "192.168.1.1" in content
    assert "AMAN" in content


def test_write_sarif(tmp_path):
    """Test SARIF report writing."""
    report = {
        "run_id": "test-001",
        "target": "192.168.1.1",
        "results": [
            {"tool": "nmap", "ok": True, "status": "done"},
            {"tool": "nikto", "ok": False, "error": "not installed"},
        ],
    }
    p = write_sarif(report, tmp_path)
    assert p.exists()
    
    data = json.loads(p.read_text())
    assert data["version"] == "2.1.0"
    assert len(data["runs"]) == 2


def test_write_csv(tmp_path):
    """Test CSV report writing."""
    report = {
        "run_id": "test-001",
        "target": "192.168.1.1",
        "results": [
            {"tool": "nmap", "ok": True, "status": "done", "duration_s": 10.5},
        ],
    }
    p = write_csv(report, tmp_path)
    assert p.exists()
    
    content = p.read_text()
    assert "run_id" in content
    assert "nmap" in content


def test_write_all(tmp_path):
    """Test writing all formats."""
    report = {
        "run_id": "test-001",
        "target": "192.168.1.1",
        "results": [],
        "isolation_ok": True,
        "started": "2026-10-18T12:00:00",
        "finished": "2026-10-18T12:01:00",
        "tool_count": 0,
        "failed_count": 0,
    }
    paths = write_all(report, tmp_path)
    
    assert paths["json"].exists()
    assert paths["md"].exists()
    assert paths["sarif"].exists()
    assert paths["csv"].exists()


def test_list_runs(tmp_path):
    """Test listing runs."""
    # Create mock run directories
    run1 = tmp_path / "20261018-120000"
    run1.mkdir()
    (run1 / "report.json").write_text(json.dumps({
        "run_id": "20261018-120000",
        "target": "192.168.1.1",
    }))
    
    run2 = tmp_path / "20261018-110000"
    run2.mkdir()
    (run2 / "report.json").write_text(json.dumps({
        "run_id": "20261018-110000",
        "target": "192.168.1.2",
    }))
    
    runs = list_runs(tmp_path)
    assert len(runs) == 2
    assert runs[0]["run_id"] == "20261018-120000"  # newest first


if __name__ == "__main__":
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        test_build_report()
        test_write_json(tmp)
        test_write_markdown(tmp)
        test_write_sarif(tmp)
        test_write_csv(tmp)
        test_write_all(tmp)
        test_list_runs(tmp)
    print("all report tests passed")
