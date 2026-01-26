# mypy: disable-error-code="import-not-found, misc"
"""
Minimal pytest fixtures for data_generator tests.
"""

from pathlib import Path

import pytest

@pytest.fixture()
def temp_output_dir(tmp_path: Path) -> Path:
    """Return a temporary directory Path for test outputs."""
    return tmp_path / "output"
