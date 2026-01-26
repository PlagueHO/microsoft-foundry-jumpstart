"""
Command-line interface for the create_ai_search_index package.

Usage (once the project is installed in the active Python environment):

    create_ai_search_index --storage-account mystorage --storage-container docs \
        --search-service mysearch --index-name myindex

This script parses CLI arguments, validates them,
and invokes the CreateSearchIndex engine.
"""

import argparse
import sys

from .engine import CreateAISearchIndex, CreateAISearchIndexConfig


def main(argv: list[str] | None = None):
    """
    Main entry point for the create_ai_search_index CLI.

    Parses command-line arguments, constructs the CreateSearchIndexConfig dataclass,
    and invokes the CreateSearchIndex engine. Exits with code 1 on error.

    Args:
        argv (list, optional): List of arguments to parse. Defaults to sys.argv[1:].
    """
    parser = argparse.ArgumentParser(
        prog="create_ai_search_index",
        description="Azure AI Search index pipeline builder for RAG scenarios.",
    )
    parser.add_argument(
        "--storage-account",
        help=(
            "Azure Storage account name. Required if not using a connection string."
        ),
    )
    parser.add_argument(
        "--storage-account-key",
        help=(
            "Azure Storage account key. Required if not using a connection string."
        ),
    )
    parser.add_argument(
        "--storage-account-connection-string",
        help=(
            "Azure Storage account connection string. If provided, overrides "
            "storage-account and storage-account-key."
        ),
    )
    parser.add_argument(
        "--storage-container",
        required=True,
        help="Blob container with documents."
    )
    parser.add_argument(
        "--search-service", 
        required=True,
        help="Azure AI Search service name."
    )
    parser.add_argument(
        "--index-name",
        required=True,
        help="Name of the search index to create or update.",
    )
    parser.add_argument(
        "--azure-openai-endpoint",
    required=False,
        help="Azure OpenAI endpoint URL."
    )
    parser.add_argument(
        "--embedding-model",
        default="text-embedding-ada-002",
        help="Azure OpenAI embedding model name. Defaults to 'text-embedding-ada-002'."
    )
    parser.add_argument(
        "--embedding-deployment",
        default="text-embedding-ada-002",
        help=(
            "Azure OpenAI embedding deployment name. "
            "Defaults to 'text-embedding-ada-002'."
        ),
    )
    parser.add_argument(
        "--embedding-dimension",
        type=int,
        default=1536,
        help="Embedding vector dimension. Defaults to 1536."
    )
    parser.add_argument(
        "--delete-existing",
        action="store_true",
        help="Delete and re-create pipeline resources if they exist.",
    )
    # ...add more arguments as needed (chunk-size, overlap, etc.)...

    args = parser.parse_args(argv or sys.argv[1:])

    # Validation: If connection string is provided, do not allow storage-account or
    # storage-account-key to be required.
    if args.storage_account_connection_string:
        if args.storage_account or args.storage_account_key:
            parser.error(
                "--storage-account-connection-string cannot be used with "
                "--storage-account or --storage-account-key"
            )
    else:
        if not args.storage_account:
            parser.error(
                "--storage-account is required unless "
                "--storage-account-connection-string is provided"
            )
        if not args.storage_account_key:
            parser.error(
                "--storage-account-key is required unless "
                "--storage-account-connection-string is provided"
            )

    config = CreateAISearchIndexConfig(
        storage_account=args.storage_account,
        storage_account_key=args.storage_account_key,
        storage_account_connection_string=args.storage_account_connection_string,
        storage_container=args.storage_container,
        search_service=args.search_service,
        index_name=args.index_name,
        azure_openai_endpoint=args.azure_openai_endpoint,
        embedding_model=args.embedding_model,
        embedding_deployment=args.embedding_deployment,
        embedding_dimension=args.embedding_dimension,
        delete_existing=args.delete_existing,
    )

    try:
        CreateAISearchIndex(config).run()
    except RuntimeError as ex:  # Changed from general Exception to RuntimeError
        print(f"ERROR: {ex}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
