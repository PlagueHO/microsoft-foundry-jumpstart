"""
Cosmos DB-backed ChatMessageStore for Microsoft Agent Framework.

This module provides an Azure Cosmos DB implementation of the ChatMessageStore
protocol for persistent chat history storage, following the official Microsoft
Agent Framework documentation pattern:
https://learn.microsoft.com/agent-framework/tutorials/agents/third-party-chat-history-storage

Usage with chat_message_store_factory:
    ```python
    from cosmosdb_chat_message_store import CosmosDBChatMessageStore

    agent = ChatAgent(
        chat_client=chat_client,
        name="MyAgent",
        instructions="You are helpful.",
        chat_message_store_factory=lambda: CosmosDBChatMessageStore(
            connection_string=os.environ["COSMOS_DB_CONNECTION_STRING"]
        )
    )
    ```

Prerequisites:
    pip install azure-cosmos azure-identity pydantic
"""
# pylint: disable=too-many-instance-attributes,too-many-arguments
# pylint: disable=too-many-positional-arguments,duplicate-code
# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false
# pyright: reportUnknownArgumentType=false

import json
import time
from collections.abc import Sequence
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel


class CosmosDBStoreState(BaseModel):
    """State model for serializing/deserializing Cosmos DB chat message store."""

    thread_id: str
    database_name: str = "agent_threads"
    container_name: str = "messages"
    max_messages: int | None = None
    endpoint: str | None = None


class CosmosDBChatMessageStore:
    """
    Cosmos DB-backed implementation of ChatMessageStore.

    Messages are stored as JSON documents with each conversation thread
    isolated by a partition key (thread_id).

    Protocol Methods:
        - add_messages: Add messages to Cosmos DB
        - list_messages: Retrieve messages in chronological order
        - serialize_state: Serialize store config for thread persistence
        - deserialize_state: Restore store config from serialized state
    """

    def __init__(
        self,
        connection_string: Optional[str] = None,
        endpoint: Optional[str] = None,
        database_name: str = "agent_threads",
        container_name: str = "messages",
        thread_id: Optional[str] = None,
        max_messages: Optional[int] = None,
    ) -> None:
        """
        Initialize the Cosmos DB chat message store.

        Args:
            connection_string: Cosmos DB connection string.
            endpoint: Cosmos DB endpoint URL (uses DefaultAzureCredential).
            database_name: Name of the database.
            container_name: Name of the container.
            thread_id: Unique conversation thread ID (auto-generated if None).
            max_messages: Max messages to retain (trims oldest when exceeded).
        """
        self.thread_id = thread_id or f"thread_{uuid4()}"
        self.database_name = database_name
        self.container_name = container_name
        self.max_messages = max_messages
        self._connection_string = connection_string
        self._endpoint = endpoint

        # Lazy initialization
        self._client: Any = None
        self._database: Any = None
        self._container: Any = None
        self._initialized = False

    async def _ensure_initialized(self) -> None:
        """Ensure Cosmos DB client and resources are initialized."""
        if self._initialized:
            return

        # pylint: disable=import-outside-toplevel
        try:
            from azure.cosmos.aio import CosmosClient
            from azure.identity.aio import DefaultAzureCredential
        except ImportError as e:
            raise ImportError(
                "azure-cosmos and azure-identity packages are required. "
                "Install with: pip install azure-cosmos azure-identity"
            ) from e

        # Create client
        if self._connection_string:
            self._client = CosmosClient.from_connection_string(
                self._connection_string
            )
        elif self._endpoint:
            credential = DefaultAzureCredential()
            self._client = CosmosClient(url=self._endpoint, credential=credential)
        else:
            raise ValueError(
                "Either connection_string or endpoint must be provided"
            )

        # Create database and container if needed
        self._database = await self._client.create_database_if_not_exists(
            id=self.database_name
        )
        self._container = await self._database.create_container_if_not_exists(
            id=self.container_name,
            partition_key={"paths": ["/thread_id"], "kind": "Hash"}
        )
        self._initialized = True

    async def add_messages(self, messages: Sequence[Any]) -> None:
        """
        Add messages to the Cosmos DB store.

        Args:
            messages: Sequence of ChatMessage objects to add.
        """
        if not messages:
            return

        await self._ensure_initialized()

        for i, message in enumerate(messages):
            doc = {
                "id": f"{self.thread_id}_{int(time.time() * 1000)}_{i}",
                "thread_id": self.thread_id,
                "timestamp": time.time(),
                "message": self._serialize_message(message)
            }
            await self._container.create_item(body=doc)

        # Apply message limit if configured
        if self.max_messages is not None:
            await self._trim_messages()

    async def _trim_messages(self) -> None:
        """Trim messages to max_messages limit."""
        all_docs = await self._get_all_documents()
        if len(all_docs) > self.max_messages:  # type: ignore[arg-type]
            all_docs.sort(key=lambda x: x.get("timestamp", 0))
            to_delete = all_docs[:-self.max_messages]  # type: ignore[operator]
            for doc in to_delete:
                await self._container.delete_item(
                    item=doc["id"],
                    partition_key=self.thread_id
                )

    async def _get_all_documents(self) -> List[Dict[str, Any]]:
        """Get all documents for this thread."""
        query = (
            "SELECT * FROM c WHERE c.thread_id = @thread_id "
            "ORDER BY c.timestamp"
        )
        parameters = [{"name": "@thread_id", "value": self.thread_id}]

        items = []
        async for item in self._container.query_items(
            query=query,
            parameters=parameters,
            partition_key=self.thread_id
        ):
            items.append(item)
        return items

    async def list_messages(self) -> List[Any]:
        """
        Get all messages from the store in chronological order.

        Returns:
            List of ChatMessage objects (oldest first).
        """
        await self._ensure_initialized()
        documents = await self._get_all_documents()
        return [self._deserialize_message(doc["message"]) for doc in documents]

    async def serialize_state(self, **_kwargs: Any) -> Dict[str, Any]:
        """
        Serialize the store state for persistence.

        Returns:
            Dictionary with store configuration.
        """
        state = CosmosDBStoreState(
            thread_id=self.thread_id,
            database_name=self.database_name,
            container_name=self.container_name,
            max_messages=self.max_messages,
            endpoint=self._endpoint,
        )
        return state.model_dump()

    async def deserialize_state(
        self,
        serialized_store_state: Any,
        **_kwargs: Any
    ) -> None:
        """
        Restore store config from serialized state.

        Args:
            serialized_store_state: Previously serialized state data.
        """
        if serialized_store_state:
            state = CosmosDBStoreState.model_validate(serialized_store_state)
            self.thread_id = state.thread_id
            self.database_name = state.database_name
            self.container_name = state.container_name
            self.max_messages = state.max_messages

            # Reconnect if endpoint changed
            if state.endpoint and state.endpoint != self._endpoint:
                self._endpoint = state.endpoint
                if self._client:
                    await self.aclose()

    # Backward-compatibility aliases for ChatMessageStoreProtocol
    async def serialize(self, **kwargs: Any) -> Dict[str, Any]:
        """Alias for serialize_state (protocol compatibility)."""
        return await self.serialize_state(**kwargs)

    async def update_from_state(
        self,
        serialized_store_state: Any,
        **kwargs: Any
    ) -> None:
        """Alias for deserialize_state (protocol compatibility)."""
        await self.deserialize_state(serialized_store_state, **kwargs)

    @classmethod
    async def deserialize(
        cls,
        serialized_store_state: Any,
        **kwargs: Any
    ) -> "CosmosDBChatMessageStore":
        """Create instance from serialized state (protocol compatibility).

        Args:
            serialized_store_state: Serialized state dictionary.
            **kwargs: Additional args (connection_string supported).

        Returns:
            New CosmosDBChatMessageStore instance.
        """
        conn_str = kwargs.get("connection_string")
        if serialized_store_state:
            return cls(
                connection_string=conn_str,
                endpoint=serialized_store_state.get("endpoint"),
                database_name=serialized_store_state.get(
                    "database_name", "agent_threads"),
                container_name=serialized_store_state.get(
                    "container_name", "messages"),
                thread_id=serialized_store_state.get("thread_id"),
                max_messages=serialized_store_state.get("max_messages"),
            )
        return cls(connection_string=conn_str)

    async def clear(self) -> None:
        """Remove all messages from the store."""
        await self._ensure_initialized()
        documents = await self._get_all_documents()
        for doc in documents:
            await self._container.delete_item(
                item=doc["id"],
                partition_key=self.thread_id
            )

    async def aclose(self) -> None:
        """Close the Cosmos DB client connection."""
        if self._client:
            await self._client.close()
            self._client = None
            self._initialized = False

    def _serialize_message(self, message: Any) -> str:
        """Serialize a ChatMessage to JSON string."""
        if hasattr(message, "model_dump"):
            message_dict = message.model_dump()
        elif hasattr(message, "to_dict"):
            message_dict = message.to_dict()
        elif isinstance(message, dict):
            message_dict = message
        else:
            message_dict = {
                "role": str(getattr(message, "role", "user")),
                "content": str(message)
            }
        return json.dumps(message_dict, separators=(",", ":"))

    def _deserialize_message(self, serialized: str) -> Any:
        """Deserialize a JSON string to ChatMessage."""
        message_dict = json.loads(serialized)
        # pylint: disable=import-outside-toplevel
        try:
            from agent_framework import ChatMessage

            if hasattr(ChatMessage, "model_validate"):
                return ChatMessage.model_validate(message_dict)  # type: ignore[attr-defined]
            if "contents" in message_dict:
                return ChatMessage.from_dict(message_dict)
            return ChatMessage(
                role=message_dict.get("role", "user"),
                text=message_dict.get("content", "")
            )
        except ImportError:
            return message_dict

    def __repr__(self) -> str:
        """String representation of the store."""
        return (
            f"CosmosDBChatMessageStore(thread_id='{self.thread_id}', "
            f"database='{self.database_name}', container='{self.container_name}')"
        )
