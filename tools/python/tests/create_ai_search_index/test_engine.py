"""
Unit tests for the create_ai_search_index.engine module.
"""

from typing import Any

import pytest
from create_ai_search_index.engine import CreateAISearchIndex, CreateAISearchIndexConfig
from pytest import MonkeyPatch


@pytest.fixture
def sample_config() -> CreateAISearchIndexConfig:
    return CreateAISearchIndexConfig(
        storage_account="teststorage",
        storage_account_key="testkey",
        storage_container="testcontainer",
        search_service="testsearch",
        index_name="testindex",
        embedding_model="text-embedding-ada-002",
        embedding_deployment=None,
        embedding_dimension=1536,
        azure_openai_endpoint=None,
        delete_existing=False,
        storage_account_connection_string=None,
    )

@pytest.fixture
def sample_config_with_connstr() -> CreateAISearchIndexConfig:
    # Provide empty strings for required str fields to avoid mypy errors
    return CreateAISearchIndexConfig(
        storage_account="",
        storage_account_key="",
        storage_container="testcontainer",
        search_service="testsearch",
        index_name="testindex",
        embedding_model="text-embedding-ada-002",
        embedding_deployment=None,
        embedding_dimension=1536,
        azure_openai_endpoint=None,
        delete_existing=False,
        storage_account_connection_string="connstr",
    )


@pytest.fixture(name="engine")
def engine_fixture(sample_config: CreateAISearchIndexConfig) -> CreateAISearchIndex:
    return CreateAISearchIndex(sample_config)




def test_config_properties(sample_config: CreateAISearchIndexConfig) -> None:
    """Test CreateAISearchIndexConfig properties."""
    assert sample_config.search_endpoint == "https://testsearch.search.windows.net"
    assert sample_config.embedding_dimension == 1536
    assert sample_config.embedding_model == "text-embedding-ada-002"
    assert sample_config.storage_account_key == "testkey"
    assert sample_config.storage_account_connection_string is None

def test_engine_init(engine: CreateAISearchIndex) -> None:
    """Test CreateAISearchIndex initialization."""
    assert engine.cfg.index_name == "testindex"

def test_engine_run(monkeypatch: MonkeyPatch, engine: CreateAISearchIndex) -> None:
    """Test CreateAISearchIndex.run method with all internals monkeypatched."""
    monkeypatch.setattr(engine, "_teardown_pipeline", lambda: None)
    monkeypatch.setattr(engine, "_ensure_index_schema", lambda: None)
    monkeypatch.setattr(engine, "_ensure_data_source", lambda: None)
    monkeypatch.setattr(engine, "_ensure_skillset", lambda: None)
    monkeypatch.setattr(engine, "_ensure_indexer", lambda: None)
    monkeypatch.setattr(engine, "_run_indexer", lambda: None)
    # Should not raise
    engine.run()

@pytest.mark.parametrize("method_name", [
    "_ensure_index_schema",
    "_ensure_data_source",
    "_ensure_skillset",
    "_ensure_indexer",
    "_run_indexer",
    "_teardown_pipeline",
])
def test_engine_methods_stub(
    monkeypatch: MonkeyPatch, engine: CreateAISearchIndex, method_name: str
) -> None:
    """Test that each internal method can be called without error when stubbed."""
    monkeypatch.setattr(engine, method_name, lambda: None)
    getattr(engine, method_name)()

def test_config_repr(sample_config: CreateAISearchIndexConfig) -> None:
    """Test the __repr__ of the config for coverage."""
    assert "testindex" in repr(sample_config)


def test_data_source_connection_string(
    monkeypatch: MonkeyPatch, sample_config_with_connstr: CreateAISearchIndexConfig
) -> None:
    """Test that _ensure_data_source uses the connection string if provided."""
    engine = CreateAISearchIndex(sample_config_with_connstr)
    called: dict[str, str | None] = {}
    def fake_create_or_update_data_source_connection(ds: Any) -> None:
        value = getattr(ds, 'connection_string', None)
        # mypy: ignore-next-line
        called['conn_str'] = value if value is not None else ''
    monkeypatch.setattr(engine.indexer_client, "create_or_update_data_source_connection", fake_create_or_update_data_source_connection)
    engine._ensure_data_source()  # type: ignore[attr-defined]  # noqa: SLF001
    assert called['conn_str'] == "connstr"

def test_get_storage_account_connection_string_with_connstr(sample_config_with_connstr: CreateAISearchIndexConfig) -> None:
    """Test _get_storage_account_connection_string returns the connection string if provided."""
    engine = CreateAISearchIndex(sample_config_with_connstr)
    assert engine._get_storage_account_connection_string() == "connstr"  # type: ignore[attr-defined]  # noqa: SLF001

def test_get_storage_account_connection_string_with_account_key(sample_config: CreateAISearchIndexConfig) -> None:
    """Test _get_storage_account_connection_string assembles string from account/key."""
    engine = CreateAISearchIndex(sample_config)
    expected = (
        "DefaultEndpointsProtocol=https;AccountName=teststorage;"
        "AccountKey=testkey;EndpointSuffix=core.windows.net"
    )
    assert engine._get_storage_account_connection_string() == expected  # type: ignore[attr-defined]  # noqa: SLF001

def test_get_storage_account_connection_string_missing_key() -> None:
    """Test _get_storage_account_connection_string raises if key missing."""
    config = CreateAISearchIndexConfig(
        storage_account="teststorage",
        storage_account_key=None,
        storage_container="testcontainer",
        search_service="testsearch",
        index_name="testindex",
        embedding_model="text-embedding-ada-002",
        embedding_deployment=None,
        embedding_dimension=1536,
        azure_openai_endpoint=None,
        delete_existing=False,
        storage_account_connection_string=None,
    )
    engine = CreateAISearchIndex(config)
    with pytest.raises(ValueError):
        engine._get_storage_account_connection_string()  # type: ignore[attr-defined]  # noqa: SLF001

def test_get_storage_account_connection_string_missing_account() -> None:
    """Test _get_storage_account_connection_string raises if account missing."""
    config = CreateAISearchIndexConfig(
        storage_account=None,
        storage_account_key="testkey",
        storage_container="testcontainer",
        search_service="testsearch",
        index_name="testindex",
        embedding_model="text-embedding-ada-002",
        embedding_deployment=None,
        embedding_dimension=1536,
        azure_openai_endpoint=None,
        delete_existing=False,
        storage_account_connection_string=None,
    )
    engine = CreateAISearchIndex(config)
    with pytest.raises(ValueError):
        engine._get_storage_account_connection_string()  # type: ignore[attr-defined]  # noqa: SLF001
