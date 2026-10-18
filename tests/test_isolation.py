import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from otrace.isolation import assert_safe_command, IsolationError, assert_safe_port


def test_safe_command_ok():
    assert_safe_command(["nmap", "-sV", "192.168.1.1"])


def test_blocks_9router_path():
    try:
        assert_safe_command(["cat", "/Users/user/.9router/runtime/mitm/server.js"])
        raise AssertionError("should have blocked")
    except IsolationError:
        pass


def test_blocks_cloudflared():
    try:
        assert_safe_command(["cloudflared", "tunnel", "--url", "http://127.0.0.1:20128"])
        raise AssertionError("should have blocked")
    except IsolationError:
        pass


def test_protected_ports():
    for p in (443, 20128):
        try:
            assert_safe_port(p)
            raise AssertionError(f"port {p} should be blocked")
        except IsolationError:
            pass


def test_safe_port_ok():
    assert_safe_port(18765)


if __name__ == "__main__":
    test_safe_command_ok()
    test_blocks_9router_path()
    test_blocks_cloudflared()
    test_protected_ports()
    test_safe_port_ok()
    print("all isolation tests passed")