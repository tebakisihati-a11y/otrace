"""Otrace notification system — macOS native notifications."""

import subprocess


def notify(title: str, message: str):
    """Send macOS notification via osascript."""
    try:
        subprocess.run([
            "osascript", "-e",
            f'display notification "{message}" with title "{title}" sound name "Glass"'
        ], check=False, timeout=5)
    except Exception:
        pass


def info(message: str):
    notify("Otrace", message)


def success(message: str):
    notify("Otrace ✓", message)


def error(message: str):
    notify("Otrace ✗", message)


def warn(message: str):
    notify("Otrace ⚠", message)
