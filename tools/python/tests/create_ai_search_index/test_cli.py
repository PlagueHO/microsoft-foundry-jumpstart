"""
Unit tests for the cli.py module in create_ai_search_index package.
"""

import sys
from unittest.mock import MagicMock, patch

import pytest

# Patch sys.argv and dependencies for CLI tests

@patch("create_ai_search_index.cli.CreateAISearchIndex")
def test_cli_main_success(mock_engine: MagicMock, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test main() runs successfully with required arguments."""
    from create_ai_search_index import cli
    # Prepare mock engine
    mock_instance = MagicMock()
    mock_engine.return_value = mock_instance
    # Prepare arguments
    argv = [
        "--storage-account", "acct",
        "--storage-account-key", "key",
        "--storage-container", "cont",
        "--search-service", "svc",
        "--index-name", "idx"
    ]
    monkeypatch.setattr(sys, "argv", ["prog"] + argv)
    cli.main()
    mock_engine.assert_called_once()
    mock_instance.run.assert_called_once()
    # Check default embedding_model and embedding_dimension
    config = mock_engine.call_args[0][0]
    assert config.embedding_model == "text-embedding-ada-002"
    assert config.embedding_dimension == 1536
    assert config.storage_account_key == "key"
    assert config.storage_account_connection_string is None

@patch("create_ai_search_index.cli.CreateAISearchIndex")
def test_cli_main_with_all_args(mock_engine: MagicMock, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test main() with all optional arguments."""
    from create_ai_search_index import cli
    mock_instance = MagicMock()
    mock_engine.return_value = mock_instance
    argv = [
        "--storage-account", "acct",
        "--storage-account-key", "key",
        "--storage-container", "cont",
        "--search-service", "svc",
        "--index-name", "idx",
        "--azure-openai-endpoint", "https://example.com",
        "--embedding-model", "model",
        "--embedding-deployment", "deploy",
        "--embedding-dimension", "2048",
        "--delete-existing"
    ]
    monkeypatch.setattr(sys, "argv", ["prog"] + argv)
    cli.main()
    mock_engine.assert_called_once()
    mock_instance.run.assert_called_once()
    # Check config values
    config = mock_engine.call_args[0][0]
    assert config.azure_openai_endpoint == "https://example.com"
    assert config.embedding_model == "model"
    assert config.embedding_deployment == "deploy"
    assert config.embedding_dimension == 2048
    assert config.delete_existing is True
    assert config.storage_account_key == "key"
    assert config.storage_account_connection_string is None

@patch("create_ai_search_index.cli.CreateAISearchIndex")
def test_cli_main_with_connection_string(mock_engine: MagicMock, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test main() with storage-account-connection-string only."""
    from create_ai_search_index import cli
    mock_instance = MagicMock()
    mock_engine.return_value = mock_instance
    argv = [
        "--storage-account-connection-string", "connstr",
        "--storage-container", "cont",
        "--search-service", "svc",
        "--index-name", "idx"
    ]
    monkeypatch.setattr(sys, "argv", ["prog"] + argv)
    cli.main()
    mock_engine.assert_called_once()
    mock_instance.run.assert_called_once()
    config = mock_engine.call_args[0][0]
    assert config.storage_account_connection_string == "connstr"
    assert config.storage_account is None or config.storage_account == ""
    assert config.storage_account_key is None

@patch("create_ai_search_index.cli.CreateAISearchIndex")
def test_cli_main_connection_string_and_account_error(
    mock_engine: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test error if both connection string and account/key are provided."""
    from create_ai_search_index import cli
    argv = [
        "--storage-account", "acct",
        "--storage-account-key", "key",
        "--storage-account-connection-string", "connstr",
        "--storage-container", "cont",
        "--search-service", "svc",
        "--index-name", "idx"
    ]
    monkeypatch.setattr(sys, "argv", ["prog"] + argv)
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code != 0

@patch("create_ai_search_index.cli.CreateAISearchIndex")
def test_cli_main_missing_storage_key(
    mock_engine: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test error if storage-account-key is missing and no connection string."""
    from create_ai_search_index import cli
    argv = [
        "--storage-account", "acct",
        "--storage-container", "cont",
        "--search-service", "svc",
        "--index-name", "idx"
    ]
    monkeypatch.setattr(sys, "argv", ["prog"] + argv)
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code != 0

@pytest.mark.parametrize("missing_arg,expected", [
    ("--storage-account", "storage_account"),
    ("--storage-account-key", "storage_account_key"),
    ("--storage-container", "storage_container"),
    ("--search-service", "search_service"),
    ("--index-name", "index_name"),
])
def test_cli_main_missing_required(
    monkeypatch: pytest.MonkeyPatch, missing_arg: str, expected: str
) -> None:
    """Test main() exits with error if required argument is missing."""
    from create_ai_search_index import cli
    argv = [
        "--storage-account", "acct",
        "--storage-account-key", "key",
        "--storage-container", "cont",
        "--search-service", "svc",
        "--index-name", "idx"
    ]
    # Remove the required argument
    idx = argv.index(missing_arg)
    del argv[idx : idx + 2]
    monkeypatch.setattr(sys, "argv", ["prog"] + argv)
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code != 0
