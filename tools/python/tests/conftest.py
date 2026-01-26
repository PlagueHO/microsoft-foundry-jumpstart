"""
Configure pytest environment.
"""

import sys
from pathlib import Path

# Add the tools/python/src directory to the Python path
tools_python_root = Path(__file__).parent.parent
# Allow imports from tools/python/src
sys.path.insert(0, str(tools_python_root / "src"))