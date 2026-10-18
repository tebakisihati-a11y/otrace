"""Tests for tools module."""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from otrace.tools import detect, detect_all, installed_keys, TOOLS, TOOL_BY_KEY
import tempfile
from pathlib import Path


def test_detect_ssh():
    """SSH should be detected on most systems."""
    result = detect("ssh")
    # Just verify it doesn't crash
    assert result is None or isinstance(result, str)


def test_detect_unknown():
    """Unknown tool should return None."""
    assert detect("nonexistent_tool_xyz") is None


def test_detect_all():
    """detect_all should return dict with all keys."""
    result = detect_all()
    assert isinstance(result, dict)
    assert "nmap" in result
    assert "ssh" in result
    assert len(result) == len(TOOLS)


def test_tool_builder_nmap():
    """Test nmap command builder."""
    t = TOOL_BY_KEY["nmap"]
    cmd = t["builder"]({"target": "192.168.1.1"})
    assert cmd[0] == "nmap"
    assert "-sV" in cmd
    assert "-sC" in cmd
    assert "192.168.1.1" in cmd


def test_tool_builder_sqlmap():
    """Test sqlmap command builder."""
    t = TOOL_BY_KEY["sqlmap"]
    cmd = t["builder"]({"target": "http://example.com"})
    assert cmd[0] == "sqlmap"
    assert "-u" in cmd
    assert "http://example.com" in cmd


def test_tool_builder_john():
    """Test john command builder."""
    t = TOOL_BY_KEY["john"]
    cmd = t["builder"]({"target": "/path/to/hash"})
    assert cmd[0] == "john"
    assert "/path/to/hash" in cmd


def test_installed_keys():
    """installed_keys should return list of detected tools."""
    keys = installed_keys()
    assert isinstance(keys, list)
    # ssh is usually installed
    if detect("ssh"):
        assert "ssh" in keys


if __name__ == "__main__":
    test_detect_ssh()
    test_detect_unknown()
    test_detect_all()
    test_tool_builder_nmap()
    test_tool_builder_sqlmap()
    test_tool_builder_john()
    test_installed_keys()
    print("all tool tests passed")
