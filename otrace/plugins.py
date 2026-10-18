"""Plugin system for custom tool definitions."""

import json
from pathlib import Path

from .config import OTRACE_HOME
from .tools import TOOL_BY_KEY, TOOLS

PLUGIN_DIR = OTRACE_HOME / "plugins"


def ensure_plugin_dir():
    PLUGIN_DIR.mkdir(parents=True, exist_ok=True)


def list_plugins() -> list:
    """List available plugin .json files."""
    ensure_plugin_dir()
    plugins = []
    for f in PLUGIN_DIR.glob("*.json"):
        try:
            data = json.loads(f.read_text())
            plugins.append({"name": f.stem, "file": str(f), "config": data})
        except Exception:
            plugins.append({"name": f.stem, "file": str(f), "error": "invalid json"})
    return plugins


def install_plugin(path: str) -> dict:
    """Install a plugin from a .json file path."""
    ensure_plugin_dir()
    src = Path(path)
    if not src.exists():
        return {"ok": False, "error": f"file not found: {path}"}
    
    dst = PLUGIN_DIR / src.name
    dst.write_text(src.read_text())
    
    try:
        data = json.loads(dst.read_text())
        return {"ok": True, "name": src.stem, "config": data}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def register_plugin(plugin_name: str) -> bool:
    """Register a plugin's tools into the global TOOL_BY_KEY registry."""
    plugin_file = PLUGIN_DIR / f"{plugin_name}.json"
    if not plugin_file.exists():
        return False
    
    try:
        data = json.loads(plugin_file.read_text())
    except Exception:
        return False
    
    tools = data.get("tools", [])
    for t in tools:
        key = t["key"]
        # Convert string builder to actual function if needed
        if isinstance(t.get("builder"), str):
            # Parse simple builder expressions
            t["builder"] = eval(t["builder"])
        TOOL_BY_KEY[key] = t
        TOOLS.append(t)
    
    return True


def reload_plugins():
    """Reload all plugins."""
    for plugin in list_plugins():
        register_plugin(plugin["name"])


def create_example_plugin():
    """Create a sample plugin file for users to edit."""
    ensure_plugin_dir()
    example = PLUGIN_DIR / "example.json"
    if example.exists():
        return str(example)
    example.write_text(json.dumps({
        "name": "example",
        "description": "Contoh plugin kustom - edit sesuai kebutuhan",
        "tools": [
            {
                "key": "mytool",
                "bin": ["mytool"],
                "cat": "custom",
                "desc": "Tool kustom pengguna",
                "install": "pip3 install mytool",
                "builder": "lambda a: ['mytool', a['target']]  # Edit sesuai kebutuhan",
            }
        ]
    }, indent=2))
    return str(example)
