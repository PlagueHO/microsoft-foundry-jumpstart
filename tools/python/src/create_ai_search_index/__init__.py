"""
create_ai_search_index
======================

Synchronous, secure builder for Azure AI Search indexing pipelines.
"""

from .engine import CreateAISearchIndex, CreateAISearchIndexConfig

__all__: list[str] = ["CreateAISearchIndex", "CreateAISearchIndexConfig"]
