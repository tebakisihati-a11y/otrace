"""Pytest configuration for otrace project."""

import sys
from pathlib import Path

# Add otrace package directory to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
