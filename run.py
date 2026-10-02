# -*- coding: utf-8 -*-
"""Root entry point for HyperMesh AI Agent CLI application."""

import sys
from pathlib import Path

# Ensure root directory is in sys.path
root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from hm_agent.main import main

if __name__ == "__main__":
    main()
