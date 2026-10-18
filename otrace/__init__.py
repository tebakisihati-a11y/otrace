"""Otrace — powerful, isolated cybersecurity orchestration suite."""

__version__ = "1.0.0"
__app__ = "otrace"

# Expose submodules for direct import
from . import reports
from . import scope
from . import tools
from . import config
from . import isolation
from . import plugins
from . import scheduler