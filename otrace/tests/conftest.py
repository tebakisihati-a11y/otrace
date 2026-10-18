"""Pytest configuration for otrace project."""

import sys
from pathlib import Path

# Add project root (parent of otrace/) to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
