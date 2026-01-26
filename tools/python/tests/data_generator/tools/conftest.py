"""
Configure pytest for data_generator.tools tests.
"""

import sys
from pathlib import Path

# Add the src directory to the Python path
repo_root = Path(__file__).parents[5]
# Allow `from src...` style imports by adding repo root (PEP 420 namespace package)
sys.path.insert(0, str(repo_root))
# Ensure both `src` and nested Python tools path are available for imports
sys.path.append(str(repo_root / "src"))
sys.path.append(str(repo_root / "src" / "tools" / "python"))