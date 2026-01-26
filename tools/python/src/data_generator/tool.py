"""
Data Generator Tool Base Classes.

This module provides abstract base classes and utilities for creating data generation
tools that can produce synthetic data in various formats (JSON, YAML, text).
"""

from __future__ import annotations

import argparse
import json
import logging
import uuid
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any, ClassVar

import yaml

_logger = logging.getLogger(__name__)


class DataGeneratorTool(ABC):
    """
    Contract that every scenario-specific prompt builder must satisfy.

    Sub-classes should *only* embed domain logic (prompt templates, argument
    validation, post-processing) and have zero coupling to Azure / I/O.
    """

    # ------------------------------------------------------------------ #
    # Registry for dynamic discovery                                     #
    # ------------------------------------------------------------------ #
    _REGISTRY: ClassVar[dict[str, type[DataGeneratorTool]]] = {}

    def __init_subclass__(cls, **kwargs: Any) -> None:  # noqa: D401 (pylint)
        """Register every concrete subclass in the internal tool registry.

        This enables dynamic lookup/instantiation via `DataGeneratorTool.from_name`
        without requiring manual imports in the consumer code.
        """
        super().__init_subclass__(**kwargs)
        if not getattr(cls, "name", None):
            raise AttributeError(
                "DataGeneratorTool subclasses must define a unique `name` attribute."
            )
        if cls.name in cls._REGISTRY:
            raise ValueError(f"Duplicate tool registration for name '{cls.name}'.")
        cls._REGISTRY[cls.name] = cls
        _logger.debug("Registered DataGeneratorTool '%s' -> %s", cls.name, cls)

    # ------------------------------------------------------------------ #
    # Mandatory interface                                                #
    # ------------------------------------------------------------------ #
    name: str  # unique identifier (e.g. "tech-support")
    # Semantic Kernel tool name (e.g. "TechSupport"). Match: '^[0-9A-Za-z_]+$'
    toolName: str

    @abstractmethod
    def build_prompt(self, output_format: str, *, unique_id: str | None = None) -> str:
        """Return the full prompt string for the given output format."""

    @abstractmethod
    def cli_arguments(self) -> list[dict[str, Any]]:
        """
        Specification for CLI arguments consumed by this tool.
        Return a list of *argparse.add_argument* keyword-dicts.
        """

    @abstractmethod
    def validate_args(self, ns: argparse.Namespace) -> None:
        """
        Validate CLI args after parsing.  Raise *ValueError* on invalid combos.
        """

    @abstractmethod
    def examples(self) -> list[str]:
        """Return usage snippets for `--help` epilog."""

    @abstractmethod
    def get_system_description(self) -> str:
        """Optional extra context injected via a system-prompt."""

    # ------------------------------------------------------------------ #
    # Optional / overridable                                             #
    # ------------------------------------------------------------------ #
    def get_unique_id(self) -> str:
        """Return a unique identifier for the item. Override to use custom IDs."""
        return str(uuid.uuid4())

    # ------------------------------------------------------------------ #
    # Format helpers                                                     #
    # ------------------------------------------------------------------ #
    _FORMAT_PARSERS: ClassVar[dict[str, Callable[[str], Any]]] = {
        "json": json.loads,
        "yaml": yaml.safe_load,
    }

    def supported_output_formats(self) -> list[str]:
        """Return the list of output formats recognised by ``post_process``."""
        return [*self._FORMAT_PARSERS.keys(), "txt"]

    def post_process(self, raw: str, output_format: str) -> Any:  # noqa: ANN401
        """
        Convert ``raw`` model output into a structured Python object.

        The method relies on the internal ``_FORMAT_PARSERS`` registry to
        dispatch to the correct parser. Unsupported or parsing-error cases
        gracefully fall back to returning the original string.

        Parameters
        ----------
        raw:
            The unprocessed text returned by Azure OpenAI / SK.
        output_format:
            Desired format - e.g. ``json``, ``yaml`` or ``txt``.

        Returns
        -------
        Any
            Parsed object on success, otherwise the original *raw* text.
        """
        fmt = output_format.lower()
        parser = self._FORMAT_PARSERS.get(fmt)
        if parser is None:               # txt / unknown formats
            return raw

        try:
            return parser(raw)
        except Exception:                # noqa: BLE001 (broad but intentional)
            _logger.debug(
                "Failed to parse %s; returning raw string.", fmt, exc_info=True
            )
            return raw

    # ------------------------------------------------------------------ #
    # Helper: factory                                                    #
    # ------------------------------------------------------------------ #
    @classmethod
    def from_name(cls, name: str) -> DataGeneratorTool:
        """Factory helper that returns a new instance of the requested tool.

        Parameters
        ----------
        name: str
            The unique `name` identifier declared on the desired tool class.

        Returns
        -------
        DataGeneratorTool
            A freshly-constructed instance of the matching tool.

        Raises
        ------
        KeyError
            If no tool with the supplied `name` has been registered.
        """
        try:
            tool_cls = cls._REGISTRY[name]
        except KeyError as exc:
            raise KeyError(
                f"No DataGeneratorTool registered with name '{name}'."
            ) from exc
        return tool_cls()
