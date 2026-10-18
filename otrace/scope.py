"""CIDR-aware scope checking using stdlib ipaddress."""

import ipaddress
from pathlib import Path

from .config import SCOPE_FILE, load_config


def _parse_scope_entries() -> list:
    """Parse scope.txt into a list of ipaddress network objects and bare strings."""
    if not SCOPE_FILE.exists():
        return []
    entries = []
    for line in SCOPE_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # Try CIDR / IP interpretation first
        try:
            entries.append(ipaddress.ip_network(line, strict=False))
            continue
        except ValueError:
            pass
        try:
            entries.append(ipaddress.ip_address(line))
            continue
        except ValueError:
            pass
        # Fallback: plain string match
        entries.append(line)
    return entries


def _resolve_target(target: str):
    """Try to resolve a target string to an ipaddress object."""
    # Direct IP?
    try:
        return ipaddress.ip_address(target)
    except ValueError:
        pass
    # Try parsing as network
    try:
        return ipaddress.ip_network(target, strict=False)
    except ValueError:
        pass
    return None


def check_scope(target: str) -> bool:
    """Check if target is within authorized scope (CIDR-aware)."""
    cfg = load_config()
    if cfg.get("OTRACE_SCOPE_REQUIRED", "1") != "1":
        return True
    
    entries = _parse_scope_entries()
    if not entries:
        return False
    
    # Wildcard matches
    wildcards = ["*", "any", "ANY"]
    if any(str(e) in wildcards for e in entries):
        return True
    
    resolved = _resolve_target(target)
    
    for entry in entries:
        if isinstance(entry, str):
            # Plain string match (backward compat)
            if target == entry or target.startswith(entry) or entry in target:
                return True
        elif resolved is not None:
            # CIDR / IP match
            if isinstance(entry, ipaddress.IPv4Network) or isinstance(entry, ipaddress.IPv6Network):
                if resolved in entry:
                    return True
            elif isinstance(entry, ipaddress.IPv4Address) or isinstance(entry, ipaddress.IPv6Address):
                if resolved == entry:
                    return True
    return False


def scope_add(target: str) -> bool:
    """Add target to scope file. Returns True if added, False if already present."""
    entries = _parse_scope_entries()
    # Check if already present (by string representation)
    target_str = str(target)
    for e in entries:
        if isinstance(e, str) and e == target_str:
            return False
        if isinstance(e, (ipaddress.IPv4Network, ipaddress.IPv6Network,
                          ipaddress.IPv4Address, ipaddress.IPv6Address)):
            if str(e) == target_str:
                return False
    
    with SCOPE_FILE.open("a") as f:
        f.write(f"{target_str}\n")
    return True


def scope_remove(target: str) -> bool:
    """Remove target from scope file. Returns True if removed."""
    if not SCOPE_FILE.exists():
        return False
    entries = _parse_scope_entries()
    target_str = str(target)
    kept = []
    found = False
    for e in entries:
        if isinstance(e, str) and e == target_str:
            found = True
            continue
        if isinstance(e, (ipaddress.IPv4Network, ipaddress.IPv6Network,
                          ipaddress.IPv4Address, ipaddress.IPv6Address)):
            if str(e) == target_str:
                found = True
                continue
        kept.append(e)
    
    if not found:
        return False
    
    # Rewrite file preserving comments
    comment_lines = []
    for line in SCOPE_FILE.read_text().splitlines():
        stripped = line.strip()
        if stripped.startswith("#") or not stripped:
            comment_lines.append(line)
    
    with SCOPE_FILE.open("w") as f:
        f.write("\n".join(comment_lines))
        for e in kept:
            if isinstance(e, str):
                f.write(f"{e}\n")
            else:
                f.write(f"{e}\n")
    return True


def scope_list() -> list:
    """Return human-readable list of all scope entries."""
    entries = _parse_scope_entries()
    return [str(e) for e in entries]
