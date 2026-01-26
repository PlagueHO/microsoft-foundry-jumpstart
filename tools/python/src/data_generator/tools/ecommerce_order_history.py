"""
E-commerce Order History Prompt Builder
========================================

Concrete :class:`data_generator.tool.DataGeneratorTool` implementation that
creates realistic e-commerce customer order histories with orders, returns,
reviews, and support interactions.
"""

from __future__ import annotations

import argparse
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

import yaml

from ..tool import DataGeneratorTool

_logger = logging.getLogger(__name__)


class EcommerceOrderHistoryTool(DataGeneratorTool):
    """Generate synthetic e-commerce customer order histories."""

    # ------------------------------------------------------------------ #
    # Identification / registry key                                      #
    # ------------------------------------------------------------------ #
    name: str = "ecommerce-order-history"
    toolName: str = "EcommerceOrderHistory"

    # ------------------------------------------------------------------ #
    # CLI contract                                                       #
    # ------------------------------------------------------------------ #
    def __init__(
        self,
        *,
        industry: str | None = None,
        orders_min: int | None = None,
        returns_percent: int | None = None
    ) -> None:
        """Create a new tool instance with optional parameters."""
        super().__init__()
        self.industry = industry or "general retail"
        self.orders_min = orders_min or 3
        self.returns_percent = returns_percent or 10

    def cli_arguments(self) -> list[dict[str, Any]]:
        """Argparse specification consumed by the top-level CLI wrapper."""
        return [
            {
                "flags": ["--industry"],
                "kwargs": {
                    "required": False,
                    "metavar": "TEXT",
                    "default": "general retail",
                    "help": (
                        "Industry context for the order history "
                        "(e.g., electronics, fashion, general retail)."
                    ),
                },
            },
            {
                "flags": ["--orders-min"],
                "kwargs": {
                    "required": False,
                    "type": int,
                    "metavar": "INT",
                    "default": 3,
                    "help": (
                        "Minimum number of orders per customer history. "
                        "Range: 1-50."
                    ),
                },
            },
            {
                "flags": ["--returns-percent"],
                "kwargs": {
                    "required": False,
                    "type": int,
                    "metavar": "INT",
                    "default": 10,
                    "help": (
                        "Percentage chance that an order is returned. "
                        "Range: 0-100."
                    ),
                },
            },
        ]

    def validate_args(self, ns: argparse.Namespace) -> None:
        """Validate and normalize CLI arguments after parsing."""
        # Store validated arguments
        self.industry = getattr(ns, "industry", None) or "general retail"
        
        # Validate and clamp orders_min
        orders_min = getattr(ns, "orders_min", None)
        if orders_min is None:
            orders_min = 3
        if not isinstance(orders_min, int):
            try:
                orders_min = int(orders_min)
            except (ValueError, TypeError):
                orders_min = 3
        # Clamp to valid range [1, 50]
        self.orders_min = max(1, min(50, orders_min))
        
        # Validate and clamp returns_percent
        returns_percent = getattr(ns, "returns_percent", None)
        if returns_percent is None:
            returns_percent = 10
        if not isinstance(returns_percent, int):
            try:
                returns_percent = int(returns_percent)
            except (ValueError, TypeError):
                returns_percent = 10
        # Clamp to valid range [0, 100]
        self.returns_percent = max(0, min(100, returns_percent))

    def examples(self) -> list[str]:
        """Representative usage snippets for `--help` output."""
        return [
            "python -m generate_data "
            "--scenario ecommerce-order-history "
            "--count 40 "
            "--industry electronics "
            "--orders-min 5 "
            "--returns-percent 15 "
            "--output-format yaml"
        ]

    # ------------------------------------------------------------------ #
    # Output formats                                                     #
    # ------------------------------------------------------------------ #
    def supported_output_formats(self) -> list[str]:
        """Return the list of output formats this tool can generate."""
        return ["yaml", "json", "text"]

    # ------------------------------------------------------------------ #
    # Prompt construction                                                #
    # ------------------------------------------------------------------ #
    def _prompt_common(self, *, unique_id: str | None = None) -> str:
        """Shared prompt header including an optional caller-supplied id."""
        customer_id = unique_id or str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        return (
            f"Customer ID (immutable): {customer_id}\n"
            f"Created At: {created_at}\n"
            f"Industry: {self.industry}\n"
            f"Orders Min: {self.orders_min}\n"
            f"Returns Percent: {self.returns_percent}\n\n"
        )

    def build_prompt(self, output_format: str, *, unique_id: str | None = None) -> str:
        """Return the full prompt for the requested *output_format*."""
        base = (
            "You are an e-commerce data specialist producing REALISTIC BUT "
            "ENTIRELY FICTIONAL per-customer order history snapshots.\n\n"
            f"{self._prompt_common(unique_id=unique_id)}"
            "Generate a comprehensive customer order history including orders, "
            "returns, product reviews, and (optionally) support interactions. "
            "All data must be fictional with no real PII. Use ISO timestamps "
            "throughout.\n\n"
            "Always output ONLY the requested data structure – no markdown fences, "
            "no commentary.\n\n"
        )

        if output_format == "yaml":
            return base + self._yaml_skeleton()
        if output_format == "json":
            return base + self._json_skeleton()
        # TEXT
        return base + self._text_skeleton()

    # ------------------------------------------------------------------ #
    # Static prompt fragments                                            #
    # ------------------------------------------------------------------ #
    def _yaml_skeleton(self) -> str:
        """YAML response schema instructing the LLM on the exact shape."""
        return (
            "Return valid YAML ONLY.\n\n"
            "customer_id: (echo above)\n"
            "created_at: (echo above)\n"
            "industry: (echo above)\n"
            "orders:\n"
            "  - order_id: uuid\n"
            "    order_date: ISO timestamp\n"
            "    items:\n"
            "      - sku: text\n"
            "        name: product name\n"
            "        qty: integer\n"
            "        price: decimal\n"
            "        currency: USD\n"
            "    total: decimal\n"
            "    status: placed|shipped|delivered|returned\n"
            f"  # ... generate at least {self.orders_min} orders ...\n"
            "returns:  # optional, based on returns_percent\n"
            "  - order_id: uuid from orders above\n"
            "    return_date: ISO timestamp\n"
            "    reason: descriptive text\n"
            "    status: approved|rejected|pending\n"
            "reviews:  # optional, for some orders\n"
            "  - order_id: uuid from orders above\n"
            "    sku: text from items\n"
            "    rating: 1-5\n"
            "    title: review title\n"
            "    review: review text\n"
            "interactions:  # optional support interactions\n"
            "  - timestamp: ISO timestamp\n"
            "    channel: email|chat|phone\n"
            "    subject: interaction subject\n"
            "    outcome: resolution description\n"
        )

    def _json_skeleton(self) -> str:
        """JSON response schema instructing the LLM on the exact shape."""
        return (
            "Return valid JSON ONLY.\n\n"
            "{\n"
            '  "customer_id": "(echo above)",\n'
            '  "created_at": "(echo above)",\n'
            '  "industry": "(echo above)",\n'
            '  "orders": [\n'
            '    {\n'
            '      "order_id": "uuid",\n'
            '      "order_date": "ISO timestamp",\n'
            '      "items": [\n'
            '        {\n'
            '          "sku": "text",\n'
            '          "name": "product name",\n'
            '          "qty": 1,\n'
            '          "price": 123.45,\n'
            '          "currency": "USD"\n'
            '        }\n'
            '      ],\n'
            '      "total": 123.45,\n'
            '      "status": "placed|shipped|delivered|returned"\n'
            '    }\n'
            f'    // ... generate at least {self.orders_min} orders ...\n'
            '  ],\n'
            '  "returns": [\n'
            '    {\n'
            '      "order_id": "uuid from orders above",\n'
            '      "return_date": "ISO timestamp",\n'
            '      "reason": "descriptive text",\n'
            '      "status": "approved|rejected|pending"\n'
            '    }\n'
            '  ],\n'
            '  "reviews": [\n'
            '    {\n'
            '      "order_id": "uuid from orders above",\n'
            '      "sku": "text from items",\n'
            '      "rating": 5,\n'
            '      "title": "review title",\n'
            '      "review": "review text"\n'
            '    }\n'
            '  ],\n'
            '  "interactions": [\n'
            '    {\n'
            '      "timestamp": "ISO timestamp",\n'
            '      "channel": "email|chat|phone",\n'
            '      "subject": "interaction subject",\n'
            '      "outcome": "resolution description"\n'
            '    }\n'
            '  ]\n'
            "}\n"
        )

    @staticmethod
    def _text_skeleton() -> str:
        """Plain-text layout for tools that prefer unstructured output."""
        return (
            "Return plain text WITHOUT any YAML/JSON formatting markers.\n\n"
            "Customer ID: (echo above)\n"
            "Created At: (echo above)\n"
            "Industry: (echo above)\n\n"
            "ORDERS:\n"
            "Order 1:\n"
            "  Order ID: uuid\n"
            "  Order Date: ISO timestamp\n"
            "  Items:\n"
            "    - SKU: text, Name: product name, Qty: 1, Price: 123.45 USD\n"
            "  Total: 123.45\n"
            "  Status: delivered\n\n"
            "RETURNS:\n"
            "Return 1:\n"
            "  Order ID: uuid from orders\n"
            "  Return Date: ISO timestamp\n"
            "  Reason: descriptive text\n"
            "  Status: approved\n\n"
            "REVIEWS:\n"
            "Review 1:\n"
            "  Order ID: uuid from orders\n"
            "  SKU: text from items\n"
            "  Rating: 5/5\n"
            "  Title: review title\n"
            "  Review: review text\n\n"
            "INTERACTIONS:\n"
            "Interaction 1:\n"
            "  Timestamp: ISO timestamp\n"
            "  Channel: email\n"
            "  Subject: interaction subject\n"
            "  Outcome: resolution description\n"
        )

    # ------------------------------------------------------------------ #
    # Post-processing                                                    #
    # ------------------------------------------------------------------ #
    def post_process(self, raw: str, output_format: str) -> Any:  # noqa: ANN401
        """Deserialize based on output_format and enrich if applicable."""
        fmt = output_format.lower()
        parsed_data: Any

        if fmt == "json":
            try:
                parsed_data = json.loads(raw)
            except json.JSONDecodeError:
                _logger.warning(
                    "Failed to parse raw output as JSON. Returning raw string."
                )
                return raw
        elif fmt == "yaml":
            try:
                parsed_data = yaml.safe_load(raw)
            except yaml.YAMLError:
                _logger.warning(
                    "Failed to parse raw output as YAML. Returning raw string."
                )
                return raw
        # Handle both 'txt' (from CLI) and 'text' (from tool's supported_output_formats)
        elif fmt == "txt" or fmt == "text":
            return raw
        else:
            _logger.warning(
                "Unknown output format '%s' for post-processing. Returning raw string.",
                output_format
            )
            return raw

        return parsed_data

    # ------------------------------------------------------------------ #
    # Misc.                                                              #
    # ------------------------------------------------------------------ #
    def get_system_description(self) -> str:
        """Return a sentence describing the target order history context."""
        return f"E-commerce order histories in {self.industry}"