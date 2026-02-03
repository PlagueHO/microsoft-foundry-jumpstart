"""
Redis-backed ChatMessageStore for Microsoft Agent Framework.

**DEPRECATED**: This custom implementation is deprecated as of the official
agent-framework-redis package release. Use the official package instead:

    pip install agent-framework-redis --pre

    from agent_framework_redis import RedisChatMessageStore

The official implementation provides:
- Better performance and reliability
- Azure AD authentication support for Azure Managed Redis
- Production-ready error handling and connection pooling
- Official support and updates from Microsoft

This file is kept for backward compatibility only and may be removed in future versions.

Documentation: https://learn.microsoft.com/agent-framework/tutorials/agents/third-party-chat-history-storage

Legacy Usage (not recommended):
    ```python
    from redis_chat_message_store import RedisChatMessageStore

    agent = ChatAgent(
        chat_client=chat_client,
        name="MyAgent",
        instructions="You are helpful.",
        chat_message_store_factory=lambda: RedisChatMessageStore(
            redis_url="redis://localhost:6379"
        )
    )
    ```

Prerequisites:
    pip install redis pydantic
"""
# pylint: disable=too-many-instance-attributes,duplicate-code
# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false
# pyright: reportUnknownArgumentType=false

import json
import warnings
from collections.abc import Sequence
from typing import Any, Dict, List
from uuid import uuid4

from pydantic import BaseModel

# Emit deprecation warning when imported
warnings.warn(
    "The custom redis_chat_message_store module is deprecated. "
    "Use the official 'agent-framework-redis' package instead: "
    "pip install agent-framework-redis --pre",
    DeprecationWarning,
    stacklevel=2
)


class RedisStoreState(BaseModel):
    """State model for serializing/deserializing Redis chat message store."""

    thread_id: str
    redis_url: str | None = None
    key_prefix: str = "chat_messages"
    max_messages: int | None = None


class RedisChatMessageStore:
    """
    Redis-backed implementation of ChatMessageStore using Redis Lists.

    Protocol Methods:
        - add_messages: Append messages to the Redis list
        - list_messages: Retrieve messages in chronological order
        - serialize_state: Serialize store config for thread persistence
        - deserialize_state: Restore store config from serialized state
    """

    def __init__(
        self,
        redis_url: str | None = None,
        thread_id: str | None = None,
        key_prefix: str = "chat_messages",
        max_messages: int | None = None,
    ) -> None:
        """
        Initialize the Redis chat message store.

        Args:
            redis_url: Redis connection URL (e.g., "redis://localhost:6379").
            thread_id: Unique conversation thread ID (auto-generated if None).
            key_prefix: Prefix for Redis keys to namespace applications.
            max_messages: Max messages to retain (trims oldest when exceeded).
        """
        if redis_url is None:
            raise ValueError("redis_url is required for Redis connection")

        self.redis_url = redis_url
        self.thread_id = thread_id or f"thread_{uuid4()}"
        self.key_prefix = key_prefix
        self.max_messages = max_messages

        # Lazy initialization
        self._redis_client: Any = None

    async def _ensure_client(self) -> Any:
        """Ensure Redis client is initialized."""
        if self._redis_client is None:
            # pylint: disable=import-outside-toplevel
            try:
                import redis.asyncio as redis
            except ImportError as e:
                raise ImportError(
                    "redis package is required. Install with: pip install redis"
                ) from e
            self._redis_client = redis.from_url(
                self.redis_url, decode_responses=True
            )
        return self._redis_client

    @property
    def redis_key(self) -> str:
        """Get the Redis key for this thread's messages."""
        return f"{self.key_prefix}:{self.thread_id}"

    async def add_messages(self, messages: Sequence[Any]) -> None:
        """
        Add messages to the Redis store.

        Args:
            messages: Sequence of ChatMessage objects to add.
        """
        if not messages:
            return

        client = await self._ensure_client()
        serialized = [self._serialize_message(msg) for msg in messages]
        await client.rpush(self.redis_key, *serialized)

        # Apply message limit if configured
        if self.max_messages is not None:
            current_count = await client.llen(self.redis_key)
            if current_count > self.max_messages:
                await client.ltrim(self.redis_key, -self.max_messages, -1)

    async def list_messages(self) -> List[Any]:
        """
        Get all messages from the store in chronological order.

        Returns:
            List of ChatMessage objects (oldest first).
        """
        client = await self._ensure_client()
        serialized_messages = await client.lrange(self.redis_key, 0, -1)

        messages = []
        for serialized in serialized_messages:
            msg = self._deserialize_message(serialized)
            messages.append(msg)
        return messages

    async def serialize_state(self, **_kwargs: Any) -> Dict[str, Any]:
        """
        Serialize the store state for persistence.

        Returns:
            Dictionary with store configuration.
        """
        state = RedisStoreState(
            thread_id=self.thread_id,
            redis_url=self.redis_url,
            key_prefix=self.key_prefix,
            max_messages=self.max_messages,
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
            state = RedisStoreState.model_validate(serialized_store_state)
            self.thread_id = state.thread_id
            self.key_prefix = state.key_prefix
            self.max_messages = state.max_messages

            # Reconnect if URL changed
            if state.redis_url and state.redis_url != self.redis_url:
                self.redis_url = state.redis_url
                if self._redis_client:
                    await self._redis_client.aclose()
                    self._redis_client = None

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
    ) -> "RedisChatMessageStore":
        """Create instance from serialized state (protocol compatibility).

        Args:
            serialized_store_state: Serialized state dictionary.
            **kwargs: Additional args (redis_url supported).

        Returns:
            New RedisChatMessageStore instance.
        """
        url = kwargs.get("redis_url")
        if serialized_store_state:
            return cls(
                redis_url=url or serialized_store_state.get("redis_url"),
                thread_id=serialized_store_state.get("thread_id"),
                key_prefix=serialized_store_state.get(
                    "key_prefix", "chat_messages"),
                max_messages=serialized_store_state.get("max_messages"),
            )
        if url is None:
            raise ValueError("redis_url is required")
        return cls(redis_url=url)

    async def clear(self) -> None:
        """Remove all messages from the store."""
        client = await self._ensure_client()
        await client.delete(self.redis_key)

    async def aclose(self) -> None:
        """Close the Redis connection."""
        if self._redis_client:
            await self._redis_client.aclose()
            self._redis_client = None

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
            f"RedisChatMessageStore(thread_id='{self.thread_id}', "
            f"key='{self.redis_key}')"
        )
