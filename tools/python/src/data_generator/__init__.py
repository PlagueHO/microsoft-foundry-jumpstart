"""
data_generator
==============

Reusable, secure generation engine for producing scenario-specific synthetic
datasets with Azure OpenAI & Semantic-Kernel.
"""

from .engine import DataGenerator  # noqa: F401  (re-export)
from .tool import DataGeneratorTool  # NEW export

# ↓ auto-import tools to trigger registry registration
from .tools import (
    retail_product,  # noqa: F401  (import for side-effect)
    tech_support,  # noqa: F401  (import for side-effect)
)

__all__: list[str] = ["DataGenerator", "DataGeneratorTool"]
