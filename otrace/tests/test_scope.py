"""Tests for scope module with CIDR support."""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from otrace.scope import check_scope, scope_add, scope_remove, scope_list
from otrace.config import SCOPE_FILE
import tempfile
from pathlib import Path


def test_scope_wildcard():
    """Wildcard scope should allow all targets."""
    original = SCOPE_FILE.read_text() if SCOPE_FILE.exists() else ""
    try:
        SCOPE_FILE.write_text("*\n")
        assert check_scope("192.168.1.1") == True
        assert check_scope("example.com") == True
    finally:
        SCOPE_FILE.write_text(original)


def test_scope_exact_match():
    """Exact IP match should work."""
    original = SCOPE_FILE.read_text() if SCOPE_FILE.exists() else ""
    try:
        SCOPE_FILE.write_text("192.168.1.1\n")
        assert check_scope("192.168.1.1") == True
        assert check_scope("192.168.1.2") == False
    finally:
        SCOPE_FILE.write_text(original)


def test_scope_cidr():
    """CIDR notation should work."""
    original = SCOPE_FILE.read_text() if SCOPE_FILE.exists() else ""
    try:
        SCOPE_FILE.write_text("192.168.1.0/24\n")
        assert check_scope("192.168.1.1") == True
        assert check_scope("192.168.1.254") == True
        assert check_scope("192.168.2.1") == False
        assert check_scope("10.0.0.1") == False
    finally:
        SCOPE_FILE.write_text(original)


def test_scope_string_fallback():
    """Plain string matching should still work."""
    original = SCOPE_FILE.read_text() if SCOPE_FILE.exists() else ""
    try:
        SCOPE_FILE.write_text("example.com\n")
        assert check_scope("example.com") == True
        assert check_scope("test.example.com") == True  # substring match
    finally:
        SCOPE_FILE.write_text(original)


def test_scope_empty():
    """Empty scope should deny all."""
    original = SCOPE_FILE.read_text() if SCOPE_FILE.exists() else ""
    try:
        SCOPE_FILE.write_text("# only comments\n")
        assert check_scope("192.168.1.1") == False
    finally:
        SCOPE_FILE.write_text(original)


def test_scope_disabled():
    """Scope checking can be disabled via config."""
    original = SCOPE_FILE.read_text() if SCOPE_FILE.exists() else ""
    try:
        SCOPE_FILE.write_text("")
        os.environ["OTRACE_SCOPE_REQUIRED"] = "0"
        try:
            assert check_scope("anything") == True
        finally:
            del os.environ["OTRACE_SCOPE_REQUIRED"]
    finally:
        SCOPE_FILE.write_text(original)


def test_scope_add():
    """Test adding to scope."""
    original = SCOPE_FILE.read_text() if SCOPE_FILE.exists() else ""
    try:
        SCOPE_FILE.write_text("")
        assert scope_add("10.0.0.0/8") == True
        assert scope_add("10.0.0.0/8") == False  # duplicate
        assert scope_add("172.16.0.0/12") == True
        
        entries = scope_list()
        assert "10.0.0.0/8" in entries
        assert "172.16.0.0/12" in entries
    finally:
        SCOPE_FILE.write_text(original)


def test_scope_remove():
    """Test removing from scope."""
    original = SCOPE_FILE.read_text() if SCOPE_FILE.exists() else ""
    try:
        SCOPE_FILE.write_text("192.168.1.0/24\n10.0.0.1\n")
        assert scope_remove("192.168.1.0/24") == True
        assert scope_remove("192.168.1.0/24") == False  # already removed
        
        entries = scope_list()
        assert all("192.168.1.0/24" not in str(e) for e in entries)
        assert any("10.0.0.1" in str(e) for e in entries)
    finally:
        SCOPE_FILE.write_text(original)


if __name__ == "__main__":
    test_scope_wildcard()
    test_scope_exact_match()
    test_scope_cidr()
    test_scope_string_fallback()
    test_scope_empty()
    test_scope_disabled()
    test_scope_add()
    test_scope_remove()
    print("all scope tests passed")
