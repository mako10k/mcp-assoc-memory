#!/usr/bin/env python3
"""
MCP Associative Memory Server Entry Point
Allows the package to be executed as a module: python -m mcp_assoc_memory
"""

import sys
from pathlib import Path

# Add the src directory to the Python path
src_dir = Path(__file__).parent.parent
sys.path.insert(0, str(src_dir))

if __name__ == "__main__":
    from mcp_assoc_memory.server import main

    main()
